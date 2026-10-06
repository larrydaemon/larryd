"""THE LOCKERS ON CLOUD STORAGE (the LARRYD runtime design, decision 2): an approved agent's package is kept in the
lockers bucket, written once at approval and read at every instance's start; an instance's own disk is only a cache.

In the bucket, per agent: `<agent_key>/agent.larryd` (the zip of agent/, as it was approved) and `<agent_key>/locker.json`
(its name and the sha256 of its code and manifest, as approved). At an instance's start every agent is fetched, unpacked
through the intake's own guards into the instance's locker folder, and held ONLY when its files hash to exactly what
locker.json says; anything else is skipped and logged (ids only). `bucket` may be given (a test's fake)."""
import json
import logging
import sqlite3

from . import intake, locker

LOG = logging.getLogger('hanzo')


class BucketLockers:
    def __init__(self, bucket_name=None, bucket=None):
        if bucket is None:
            from google.cloud import storage   # only on the server
            bucket = storage.Client().bucket(bucket_name)
        self.bucket = bucket

    def keys(self):
        return sorted({b.name.split('/', 1)[0] for b in self.bucket.list_blobs() if b.name.endswith('/locker.json')})

    def publish(self, agent_key, row, package, role=''):
        """An approved agent into the bucket: its package, then its locker.json (written last, so a half-written agent is
        never listed)."""
        self.bucket.blob(f'{agent_key}/agent.larryd').upload_from_string(package, content_type='application/octet-stream')
        self.bucket.blob(f'{agent_key}/locker.json').upload_from_string(
            json.dumps({**{k: row[k] for k in ('name', 'code_sha256', 'manifest_sha256')}, **({'role': role} if role else {})}),
            content_type='application/json')

    def link(self, agent_key, card_key):
        """The card's key the platform minted at approval, kept beside the agent in the bucket, so every instance links it."""
        self.bucket.blob(f'{agent_key}/card.json').upload_from_string(json.dumps({'card_key': card_key}), content_type='application/json')

    def sync(self, db, agents, conf):
        """Every agent in the bucket into this instance's locker, verified. -> the number held."""
        held = 0
        for key in self.keys():
            try:
                want = json.loads(self.bucket.blob(f'{key}/locker.json').download_as_bytes())
                files = intake.check(intake.from_zip(self.bucket.blob(f'{key}/agent.larryd').download_as_bytes(),
                                                     conf['most_files'], conf['most_bytes']), conf['most_files'], conf['most_bytes'])
                group = 'marketplace' if want.get('role') == 'marketplace' else conf['folder']   # the marketplace keeps its own folder
                row = intake.receive(db, agents, group, key, files)
            except Exception as error:
                LOG.error('locker %s not held: %s', key, type(error).__name__)
                continue
            if (row['code_sha256'], row['manifest_sha256']) != (want.get('code_sha256'), want.get('manifest_sha256')):
                LOG.error('locker %s not held: its files are not what was approved', key)
                con = sqlite3.connect(db)
                try:
                    con.execute('DELETE FROM hanzo_locker WHERE agent_key = ?', (key,))
                    con.commit()
                finally:
                    con.close()
                continue
            card = self.bucket.blob(f'{key}/card.json')
            if card.exists():
                locker.link(db, key, json.loads(card.download_as_bytes()).get('card_key', ''))
            ok, _why = locker.verify(db, agents, key)
            held += 1 if ok else 0
        return held
