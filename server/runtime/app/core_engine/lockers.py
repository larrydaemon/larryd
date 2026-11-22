"""THE LOCKERS ON CLOUD STORAGE (the LARRYD runtime design, decision 2): an approved agent's package is kept in the
lockers bucket, written once at approval and read at every instance's start; an instance's own disk is only a cache.

In the bucket, per agent and per caller's locker (2026-11-22; the locker of before at the top, every other caller's under
`<caller>/`): `<agent_key>/agent.larryd` (the zip of agent/, as it was approved) and `<agent_key>/locker.json`
(its name and the sha256 of its code and manifest, as approved). At an instance's start every agent is fetched, unpacked
through the intake's own guards into the instance's locker folder, and held ONLY when its files hash to exactly what
locker.json says; anything else is skipped and logged (ids only). `bucket` may be given (a test's fake)."""
import json
import logging
import pathlib
import sqlite3

from . import intake, locker

LOG = logging.getLogger('runtime')


class BucketLockers:
    def __init__(self, bucket_name=None, bucket=None):
        if bucket is None:
            from google.cloud import storage   # only on the server
            bucket = storage.Client().bucket(bucket_name)
        self.bucket = bucket

    @staticmethod
    def _at(caller=''):
        """EACH CALLER ITS OWN LOCKER (the owner 2026-11-22: "there should be zero agents that are on a and b at the same fucking
        time"): the locker of before is the bucket's top, <agent_key>/... exactly as it was (slot A's); another caller's is its own
        copy under <caller>/<agent_key>/... -> the prefix."""
        own = locker.of(caller)
        return f'{own}/' if own else ''

    def keys(self, caller=''):
        """The agents of one caller's locker: the keys with a locker.json directly under its prefix (never another caller's)."""
        at, found = self._at(caller), set()
        for b in self.bucket.list_blobs():
            if not b.name.startswith(at):
                continue
            parts = b.name[len(at):].split('/')
            if len(parts) == 2 and parts[1] == 'locker.json' and intake.KEY.match(parts[0]):
                found.add(parts[0])
        return sorted(found)

    def publish(self, agent_key, row, package, role='', caller=''):
        """An approved agent into THE CALLER'S locker in the bucket: its package, then its locker.json (written last, so a
        half-written agent is never listed)."""
        at = self._at(caller)
        self.bucket.blob(f'{at}{agent_key}/agent.larryd').upload_from_string(package, content_type='application/octet-stream')
        self.bucket.blob(f'{at}{agent_key}/locker.json').upload_from_string(
            json.dumps({**{k: row[k] for k in ('name', 'code_sha256', 'manifest_sha256')}, **({'role': role} if role else {})}),
            content_type='application/json')

    def link(self, agent_key, card_key, caller=''):
        """The card's key the platform minted at approval, kept beside the agent in the bucket, so every instance links it.
        caller: the platform that minted it (its slot's key id): card.json keeps each caller's card under "cards", beside the
        others' (one runtime, every platform its own card: 2026-11-11); no caller named: "card_key", as before. The card.json
        is the one of THE CALLER'S OWN locker (2026-11-22)."""
        blob = self.bucket.blob(f'{self._at(caller)}{agent_key}/card.json')
        try:
            kept = json.loads(blob.download_as_bytes()) if blob.exists() else {}
        except ValueError:
            kept = {}
        kept = kept if isinstance(kept, dict) else {}
        if caller:
            kept['cards'] = {**(kept.get('cards') if isinstance(kept.get('cards'), dict) else {}), caller: card_key}
        else:
            kept['card_key'] = card_key
        blob.upload_from_string(json.dumps(kept), content_type='application/json')

    def copy(self, to, keys=None):
        """THE MIGRATION TO A LOCKER PER CALLER (2026-11-22), in the bucket: a copy, never a move. Every agent of the locker of
        before (<key>/agent.larryd, locker.json, card.json, as they are: slot A's untouched) copied to caller `to`'s own locker
        (<to>/<key>/...), locker.json last; an agent `to` already holds is left as it is (run it again: nothing more happens).
        keys: only these (None: every one). -> {'copied': [keys], 'kept': [keys]}."""
        at = self._at(to)
        if not at:
            raise ValueError(f'{to!r} is the locker of before itself: nothing to copy into')
        have, out = set(self.keys(to)), {'copied': [], 'kept': []}
        for key in self.keys():
            if keys is not None and key not in keys:
                continue
            if key in have:
                out['kept'].append(key)
                continue
            for name, kind in (('agent.larryd', 'application/octet-stream'), ('card.json', 'application/json'), ('locker.json', 'application/json')):
                src = self.bucket.blob(f'{key}/{name}')
                if src.exists():
                    self.bucket.blob(f'{at}{key}/{name}').upload_from_string(src.download_as_bytes(), content_type=kind)
            out['copied'].append(key)
        return out

    def sync(self, db, agents, conf, callers=('',)):
        """Every agent of each caller's locker in the bucket into that caller's own locker on this instance (locker.root_for),
        verified. callers: the callers this instance answers (each locker once). -> the number held."""
        held, done = 0, set()
        for caller in callers:
            own = locker.of(caller)
            if own in done:
                continue
            done.add(own)
            held += self._sync(db, locker.root_for(agents, caller), conf, caller)
        return held

    def _sync(self, db, agents, conf, caller):
        held, at = 0, self._at(caller)
        pathlib.Path(agents).mkdir(parents=True, exist_ok=True)
        for key in self.keys(caller):
            try:
                want = json.loads(self.bucket.blob(f'{at}{key}/locker.json').download_as_bytes())
                files = intake.check(intake.from_zip(self.bucket.blob(f'{at}{key}/agent.larryd').download_as_bytes(),
                                                     conf['most_files'], conf['most_bytes']), conf['most_files'], conf['most_bytes'])
                group = 'marketplace' if want.get('role') == 'marketplace' else conf['folder']   # the marketplace keeps its own folder
                row = intake.receive(db, agents, group, key, files, caller)
            except Exception as error:
                LOG.error('locker %s%s not held: %s', at, key, type(error).__name__)
                continue
            if (row['code_sha256'], row['manifest_sha256']) != (want.get('code_sha256'), want.get('manifest_sha256')):
                LOG.error('locker %s%s not held: its files are not what was approved', at, key)
                con = sqlite3.connect(db)
                try:
                    con.execute('DELETE FROM runtime_locker WHERE agent_key = ? AND caller = ?', (key, locker.of(caller)))
                    con.commit()
                finally:
                    con.close()
                continue
            card = self.bucket.blob(f'{at}{key}/card.json')
            if card.exists():
                said = json.loads(card.download_as_bytes())
                if said.get('card_key'):
                    locker.link(db, key, said['card_key'], into=caller)
                for who, card_key in (said.get('cards') if isinstance(said.get('cards'), dict) else {}).items():   # each platform's own card of it
                    if isinstance(who, str) and who and isinstance(card_key, str) and card_key and locker._of_quiet(who) == locker.of(caller):
                        locker.link(db, key, card_key, who)   # only the cards of the callers held to THIS locker
            ok, _why = locker.verify(db, agents, key, caller)
            held += 1 if ok else 0
        return held
