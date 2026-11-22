"""THE LOCKER: the agents the runtime holds. An agent is a folder inside the locker (its manifest agent.json + its code) and
one runtime_locker row binding the runtime's own key for it (and, once approved, the key of its card on the platform) to that folder and the sha256 of both. Every call and
run verifies the folder against the row first; any change, an added file or a link is TAMPERED and refused."""
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import sqlite3
import sys

MANIFEST = 'agent.json'
NEEDS = ('name', 'entry')


IN_PLACE = 'LARRYD_LOCKER'   # THE LOCKER IN PLACE (LARRYD_INTERNAL=1 only): the one folder holding every internal agent, each at <name>/agent


def in_place():
    """THE LOCKER IN PLACE (ONE SYSTEM, the owner 2026-11-07: "1 single locker for all agents internal (sanity_agents/<name>";
    "zero agents should live in the runtime itself"): with LARRYD_INTERNAL=1 and LARRYD_LOCKER naming a folder, the runtime holds
    each agent where it is, <LARRYD_LOCKER>/<name>/agent, and copies nothing into instance/. -> that folder, or None (every other
    runtime: production's bucket and cache, a laptop's own locker, exactly as before)."""
    root = os.environ.get(IN_PLACE, '')
    if os.environ.get('LARRYD_INTERNAL') != '1' or not root:
        return None
    return pathlib.Path(root).expanduser().resolve()


FIRST = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'schemas' / 'runtime.json').read_text())['lockers']['first']
CALLER = re.compile(r'^[a-z0-9][a-z0-9-]{0,31}$')   # a caller's name as its slot's key id is written (slot-a, slot-b, proof)


def of(caller=''):
    """EACH CALLER ITS OWN LOCKER (the owner 2026-11-22: "there should be zero agents that are on a and b at the same fucking time.
    if so fix that too"): the locker a caller's calls, hires and runs are held to. '' is the locker of before (runtime.json
    lockers.first, slot A's, and a laptop's one platform: its rows and folders exactly as they were); every other caller its own,
    by its name. The locker in place (the one internal locker) is one locker for every caller, as before. -> the locker's name."""
    if in_place() is not None or caller in ('', FIRST):
        return ''
    if not CALLER.match(str(caller)):
        raise ValueError(f'{caller!r} is not a caller')
    return caller


def _of_quiet(caller):
    """of(caller), or None for a name no caller has (a stored row is never a reason to fail)."""
    try:
        return of(caller)
    except ValueError:
        return None


def root_for(agents, caller=''):
    """The folder of a caller's own locker: the locker of before is `agents` itself; another caller's is its sibling
    <agents>.<caller>, never inside another's, so no row of one caller can name a folder of another's."""
    own, agents = of(caller), pathlib.Path(agents)
    return agents if not own else agents.parent / f'{agents.name}.{own}'


def _inside(root, folder):
    root = pathlib.Path(root).resolve()
    path = (root / folder).resolve()
    if root not in path.parents:
        raise ValueError(f'{folder} is not inside the locker')
    return path


def _links(path):
    return any(p.is_symlink() for p in path.rglob('*'))


def _code_sha256(path):
    """Every file but the manifest, by its path inside the folder and its bytes, in a fixed order."""
    h = hashlib.sha256()
    for f in sorted(p for p in path.rglob('*') if p.is_file() and p.name != MANIFEST and '__pycache__' not in p.parts):
        h.update(f.relative_to(path).as_posix().encode('utf-8') + b'\0' + f.read_bytes() + b'\0')
    return h.hexdigest()


def _manifest_sha256(path):
    return hashlib.sha256((path / MANIFEST).read_bytes()).hexdigest()


def manifest(root, folder):
    return json.loads((_inside(root, folder) / MANIFEST).read_text())


def add(db, root, agent_key, folder, caller=''):
    """The agent's row in THE CALLER'S locker (of(caller)); root is that locker's own folder (root_for)."""
    own = of(caller)
    path = _inside(root, folder)
    if _links(path):
        raise ValueError(f'{folder} holds a link; an agent is only its own files')
    card = json.loads((path / MANIFEST).read_text())
    missing = [k for k in NEEDS if not card.get(k)]
    if missing or not (path / card['entry']).is_file():
        raise ValueError(f'{folder}/{MANIFEST} needs {", ".join(NEEDS)} and its entry file')
    con = sqlite3.connect(db)
    try:
        con.execute('INSERT INTO runtime_locker (agent_key, name, folder, code_sha256, manifest_sha256, registered_at, caller) VALUES (?,?,?,?,?,?,?)',
                    (agent_key, card['name'], path.relative_to(pathlib.Path(root).resolve()).as_posix(), _code_sha256(path),
                     _manifest_sha256(path), datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), own))
        con.commit()
    finally:
        con.close()


def held(db, agent_key, caller=''):
    """The locker row of an agent, by the runtime's own key or by the key of its card on the platform (linked at approval).
    ONE RUNTIME, EVERY PLATFORM ITS OWN CARD (2026-11-11: the 2026-11-09 ship wrote production B's card key over this Mac's in
    133 lockers, so this Mac's cards found no agent, 404 on every page): each platform that calls (caller, its slot's key id)
    mints its own card key for the same agent, so a card is linked per caller (runtime_cards) and found only by the caller it
    belongs to. The row's card_key is this caller's card when it has one, else the one linked with no caller named (a laptop's
    one platform; a locker linked before 2026-11-11). EACH CALLER ITS OWN LOCKER (2026-11-22): only the rows of the caller's own
    locker (of(caller)) are ever found; another caller's copy of the same agent never is."""
    own = of(caller)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute('SELECT * FROM runtime_locker WHERE caller = ? AND (agent_key = ? OR (card_key = ? AND card_key != \'\') '
                          'OR agent_key IN (SELECT agent_key FROM runtime_cards WHERE card_key = ? AND card_key != \'\' AND caller = ? AND caller != \'\')) '
                          'ORDER BY agent_key = ? DESC', (own, agent_key, agent_key, agent_key, caller, agent_key)).fetchone()
        if row is None:
            return None
        row = dict(row)
        own = con.execute('SELECT card_key FROM runtime_cards WHERE agent_key = ? AND caller = ? AND caller != \'\'', (row['agent_key'], caller)).fetchone()
        if own:
            row['card_key'] = own[0]
        return row
    finally:
        con.close()


def link(db, agent_key, card_key, caller='', into=''):
    """BOTH KEYS SAVED AND LINKED (the owner, 2026-10-06): the runtime mints its own key for the agent; the platform mints
    its card's key at approval and tells the runtime here. caller: the platform that minted it (its slot's key id); each
    caller's card is kept beside the others', never over them. The agent must be held in that caller's own locker (of(caller)).
    into: with no caller named, the locker whose row keeps the card (a caller's name; '' the locker of before), as before.
    -> True when the agent is held (and now linked)."""
    own = of(caller if caller else into)
    con = sqlite3.connect(db)
    try:
        if caller:
            n = con.execute('SELECT COUNT(*) FROM runtime_locker WHERE agent_key = ? AND caller = ?', (agent_key, own)).fetchone()[0]
            if n == 1:
                con.execute('DELETE FROM runtime_cards WHERE agent_key = ? AND caller = ?', (agent_key, caller))
                con.execute('INSERT INTO runtime_cards (agent_key, caller, card_key) VALUES (?,?,?)', (agent_key, caller, card_key))
        else:
            n = con.execute('UPDATE runtime_locker SET card_key = ? WHERE agent_key = ? AND caller = ?', (card_key, agent_key, own)).rowcount
        con.commit()
    finally:
        con.close()
    return n == 1


def verify(db, root, agent_key, caller=''):
    """(True, '') when the folder is exactly what was registered; (False, the reason) otherwise."""
    row = held(db, agent_key, caller)
    if row is None:
        return False, 'not in the locker'
    try:
        path = _inside(root, row['folder'])
    except ValueError:
        return False, 'tampered: the folder is outside the locker'
    if not path.is_dir() or not (path / MANIFEST).is_file():
        return False, 'tampered: the folder is missing'
    if _links(path):
        return False, 'tampered: a link in the folder'
    if _manifest_sha256(path) != row['manifest_sha256']:
        return False, 'tampered: the manifest changed'
    if _code_sha256(path) != row['code_sha256']:
        return False, 'tampered: the code changed'
    return True, ''


def remove(db, root, agent_key, caller=''):
    """A PLACED AGENT TAKEN OUT (frost-05's approval 2026-11-06, the revoked leftovers): its folder deleted and its row with it, by the
    runtime's own key exactly (never a card key's alias). The caller decides it may go (Harness.remove: FROST's word on its exact hashes
    is revoked). Only THE CALLER'S OWN copy goes, and the cards of the callers held to that locker; another caller's copy stays.
    -> the folder removed; ValueError when it is not held or its folder is not inside the locker."""
    own = of(caller)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute('SELECT * FROM runtime_locker WHERE agent_key = ? AND caller = ?', (agent_key, own)).fetchone()
        if row is None:
            raise ValueError('not in the locker')
        path = _inside(root, row['folder'])
        if (pathlib.Path(root) / row['folder']).is_symlink():
            raise ValueError('the folder is a link')   # never followed out of the locker
        if path.is_dir() and in_place() != pathlib.Path(root).resolve():   # IN PLACE the folder is the agent's own home: only its row goes
            shutil.rmtree(path)
        for (card_caller,) in con.execute('SELECT DISTINCT caller FROM runtime_cards WHERE agent_key = ?', (agent_key,)).fetchall():
            if _of_quiet(card_caller) == own:
                con.execute('DELETE FROM runtime_cards WHERE agent_key = ? AND caller = ?', (agent_key, card_caller))
        con.execute('DELETE FROM runtime_locker WHERE agent_key = ? AND caller = ?', (agent_key, own))
        con.commit()
        return row['folder']
    finally:
        con.close()


def copy(db, agents, to, keys=None):
    """THE MIGRATION TO A LOCKER PER CALLER (2026-11-22), a copy, never a move: every agent of the locker of before (its rows,
    caller '', and its folders under `agents`, exactly as they are: slot A's answers unchanged) copied into caller `to`'s own
    locker: its folder byte for byte into root_for(agents, to) at the same place, its row with the same hashes, card and time.
    Nothing is copied that does not verify where it is; an agent `to` already holds is left as it is (run it again: nothing more
    happens). keys: only these runtime keys (None: every one). -> {'copied': [keys], 'kept': [keys], 'refused': {key: why}}."""
    own = of(to)
    if not own:
        raise ValueError(f'{to!r} is the locker of before itself: nothing to copy into')
    agents = pathlib.Path(agents).resolve()
    into = root_for(agents, to)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in con.execute("SELECT * FROM runtime_locker WHERE caller = '' ORDER BY agent_key")]
        have = {r[0] for r in con.execute('SELECT agent_key FROM runtime_locker WHERE caller = ?', (own,))}
    finally:
        con.close()
    out = {'copied': [], 'kept': [], 'refused': {}}
    for row in rows:
        key = row['agent_key']
        if keys is not None and key not in keys:
            continue
        if key in have:
            out['kept'].append(key)
            continue
        ok, why = verify(db, agents, key)
        if not ok:
            out['refused'][key] = why
            continue
        into.mkdir(parents=True, exist_ok=True)
        src, dst = _inside(agents, row['folder']), _inside(into, row['folder'])
        if dst.exists():
            shutil.rmtree(dst)   # a half copy of an earlier run that never got its row
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
        if (_code_sha256(dst), _manifest_sha256(dst)) != (row['code_sha256'], row['manifest_sha256']):
            shutil.rmtree(dst)
            out['refused'][key] = 'the copy does not hash to the held hashes'
            continue
        con = sqlite3.connect(db)
        try:
            con.execute('INSERT INTO runtime_locker (agent_key, name, folder, code_sha256, manifest_sha256, registered_at, card_key, caller) VALUES (?,?,?,?,?,?,?,?)',
                        (key, row['name'], row['folder'], row['code_sha256'], row['manifest_sha256'], row['registered_at'], row['card_key'], own))
            con.commit()
        finally:
            con.close()
        out['copied'].append(key)
    return out


def adopt(db, old_root, root, agent_key, folder):
    """THE ONE-TIME MOVE INTO THE LOCKER IN PLACE: an agent already held (its row and its copy under old_root, instance/agents) is held
    at <root>/<folder> instead, ON THE SAME APPROVED HASHES. The copy's files the folder lacks (the kits packed at its place: office.py,
    look.py ...) are written into the folder from the copy, byte for byte as approved; a file the folder has with other bytes, or a file
    the copy never had, refuses it (the agent changed since its approval: place it again, for a new review). Nothing is written unless
    the copy still verifies; the row moves only when the folder hashes to exactly the approved hashes. The copy is left where it was.
    -> the row; ValueError and why otherwise."""
    ok, why = verify(db, old_root, agent_key)
    if not ok:
        raise ValueError(f'the held copy does not verify: {why}')
    row = held(db, agent_key)
    if row['agent_key'] != agent_key:
        raise ValueError('held under another key: adopt it by its own key')
    old, path = _inside(old_root, row['folder']), _inside(root, folder)
    if not (path / MANIFEST).is_file() or _links(path):
        raise ValueError(f'{folder} is not an agent folder of plain files')
    have = {p.relative_to(old).as_posix() for p in old.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    mine = {p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if mine - have:
        raise ValueError(f'{folder} holds files the approved copy never had: {", ".join(sorted(mine - have))}')
    changed = sorted(f for f in mine if (path / f).read_bytes() != (old / f).read_bytes())
    if changed:
        raise ValueError(f'{folder} changed since its approval: {", ".join(changed)}')
    for f in sorted(have - mine):
        (path / f).parent.mkdir(parents=True, exist_ok=True)
        (path / f).write_bytes((old / f).read_bytes())
    if (_code_sha256(path), _manifest_sha256(path)) != (row['code_sha256'], row['manifest_sha256']):
        raise ValueError(f'{folder} does not hash to the approved hashes')
    con = sqlite3.connect(db)
    try:
        con.execute("UPDATE runtime_locker SET folder = ? WHERE agent_key = ? AND caller = ''", (path.relative_to(pathlib.Path(root).resolve()).as_posix(), agent_key))
        con.commit()
    finally:
        con.close()
    return held(db, agent_key)


def main(argv):
    """python runtime/app/core_engine/locker.py add <agent_key> <folder inside runtime/app/agents>"""
    from store import open_store
    app = pathlib.Path(__file__).resolve().parent.parent
    if len(argv) != 4 or argv[1] != 'add':
        raise SystemExit(main.__doc__)
    db = open_store(app.parent / 'instance')
    add(db, app / 'agents', argv[2], argv[3])
    print(argv[2], verify(db, app / 'agents', argv[2]))


if __name__ == '__main__':
    main(sys.argv)
