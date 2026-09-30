"""THE LOCKER: the agents HANZO holds. An agent is a folder inside the locker (its manifest agent.json + its code) and
one hanzo_locker row binding the key of its card on the platform to that folder and the sha256 of both. Every call and
run verifies the folder against the row first; any change, an added file or a link is TAMPERED and refused."""
import datetime
import hashlib
import json
import pathlib
import sqlite3
import sys

MANIFEST = 'agent.json'
NEEDS = ('name', 'entry')


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


def add(db, root, agent_key, folder):
    path = _inside(root, folder)
    if _links(path):
        raise ValueError(f'{folder} holds a link; an agent is only its own files')
    card = json.loads((path / MANIFEST).read_text())
    missing = [k for k in NEEDS if not card.get(k)]
    if missing or not (path / card['entry']).is_file():
        raise ValueError(f'{folder}/{MANIFEST} needs {", ".join(NEEDS)} and its entry file')
    con = sqlite3.connect(db)
    try:
        con.execute('INSERT INTO hanzo_locker (agent_key, name, folder, code_sha256, manifest_sha256, registered_at) VALUES (?,?,?,?,?,?)',
                    (agent_key, card['name'], path.relative_to(pathlib.Path(root).resolve()).as_posix(), _code_sha256(path),
                     _manifest_sha256(path), datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')))
        con.commit()
    finally:
        con.close()


def held(db, agent_key):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute('SELECT * FROM hanzo_locker WHERE agent_key = ?', (agent_key,)).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def verify(db, root, agent_key):
    """(True, '') when the folder is exactly what was registered; (False, the reason) otherwise."""
    row = held(db, agent_key)
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


def main(argv):
    """python hanzo/app/core_engine/locker.py add <agent_key> <folder inside hanzo/app/agents>"""
    from store import open_store
    app = pathlib.Path(__file__).resolve().parent.parent
    if len(argv) != 4 or argv[1] != 'add':
        raise SystemExit(main.__doc__)
    db = open_store(app.parent / 'instance')
    add(db, app / 'agents', argv[2], argv[3])
    print(argv[2], verify(db, app / 'agents', argv[2]))


if __name__ == '__main__':
    main(sys.argv)
