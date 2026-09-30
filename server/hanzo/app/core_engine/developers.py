"""THE DEVELOPER DOOR's logic: who a developer is, which agents are theirs, and how their upload becomes a locker folder.
A developer is a HANZO-side name with their own secret (a file in HANZO's instance, printed once when made) and the card
keys they may submit; never a platform account or member. An upload is plain files (path -> base64), written into the
locker's dev/<agent_key>/ folder only when every path stays inside it; the locker then holds exactly those files."""
import base64
import binascii
import datetime
import json
import os
import pathlib
import re
import secrets
import shutil
import sqlite3

from . import locker

NAME = re.compile(r'^[a-z][a-z0-9-]{1,39}$')
KEY = re.compile(r'^[A-Z]{4}_[0-9A-F]{12}_[0-9A-F]{4}$')   # a card's key, as the platform mints it (FROST's review takes only this)
PART = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.-]*$')        # one part of an uploaded path: no hidden part, no '..'


class Refused(Exception):
    def __init__(self, status, reason):
        super().__init__(reason)
        self.status, self.reason = status, reason


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def secret(secrets_dir, developer):
    """The developer's secret, or '' when there is no such developer."""
    if not NAME.match(developer or ''):
        return ''
    path = pathlib.Path(secrets_dir) / developer
    return path.read_text().strip() if path.is_file() and not path.is_symlink() else ''


def add(db, secrets_dir, developer, agent_key):
    """The developer may submit agent_key. -> their new secret (printed once) when the developer is new, else ''."""
    if not NAME.match(developer or ''):
        raise Refused(400, 'a developer is a plain name: a small letter first, then small letters, digits or -')
    if not KEY.match(agent_key or ''):
        raise Refused(400, 'not a card key')
    con = sqlite3.connect(db)
    try:
        row = con.execute('SELECT developer FROM hanzo_developers WHERE agent_key = ?', (agent_key,)).fetchone()
        if row and row[0] != developer:
            raise Refused(409, 'that agent is another developer\'s')
        made = ''
        folder = pathlib.Path(secrets_dir)
        if not secret(folder, developer):
            folder.mkdir(parents=True, exist_ok=True)
            os.chmod(folder, 0o700)
            made = secrets.token_hex(32)
            path = folder / developer
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(made + '\n')
        if not row:
            con.execute('INSERT INTO hanzo_developers (agent_key, developer, added_at) VALUES (?,?,?)', (agent_key, developer, _now()))
            con.commit()
        return made
    finally:
        con.close()


def theirs(db, developer):
    con = sqlite3.connect(db)
    try:
        return [r[0] for r in con.execute('SELECT agent_key FROM hanzo_developers WHERE developer = ? ORDER BY agent_key', (developer,))]
    finally:
        con.close()


def _files(files, most_files, most_bytes):
    """-> {relative path: bytes}, or Refused: every path plain and inside, every value base64 text, within the limits."""
    if not isinstance(files, dict) or not files:
        raise Refused(400, 'files is {path: base64 of the file}')
    if len(files) > most_files:
        raise Refused(413, f'more than {most_files} files')
    out, total = {}, 0
    for rel, data in files.items():
        parts = str(rel).split('/')
        if not all(PART.match(p) for p in parts):
            raise Refused(400, f'{rel} is not a plain path inside the agent\'s folder')
        if not isinstance(data, str):
            raise Refused(400, f'{rel} is not a file (its value must be base64 text)')
        try:
            raw = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError):
            raise Refused(400, f'{rel} is not base64')
        total += len(raw)
        if total > most_bytes:
            raise Refused(413, f'more than {most_bytes} bytes')
        out['/'.join(parts)] = raw
    try:
        card = json.loads(out[locker.MANIFEST]) if locker.MANIFEST in out else None
    except (UnicodeDecodeError, ValueError):
        card = None
    if not isinstance(card, dict) or not all(isinstance(card.get(k), str) and card[k] for k in locker.NEEDS) or card['entry'] not in out:
        raise Refused(400, f'{locker.MANIFEST} needs {", ".join(locker.NEEDS)} and its entry file')
    return out


def receive(db, agents, folder, agent_key, files, most_files, most_bytes):
    """Write the upload into agents/<folder>/<agent_key>/ and hold it in the locker: a changed agent replaces the old one,
    the same files again give the same hashes (so the same review). Everything is checked before the old one is touched.
    -> the locker row."""
    raw = _files(files, most_files, most_bytes)
    agents = pathlib.Path(agents).resolve()
    home = agents / folder
    home.mkdir(exist_ok=True)
    incoming = home / f'incoming_{secrets.token_hex(8)}'
    try:
        incoming.mkdir()
        for rel, data in raw.items():
            path = (incoming / rel).resolve()
            if incoming.resolve() not in path.parents:
                raise Refused(400, f'{rel} is not inside the agent\'s folder')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        target = home / agent_key
        con = sqlite3.connect(db)
        try:
            con.execute('BEGIN IMMEDIATE')
            con.execute('DELETE FROM hanzo_locker WHERE agent_key = ?', (agent_key,))
            if target.exists():
                shutil.rmtree(target)
            incoming.rename(target)
            con.commit()
        finally:
            con.close()
        locker.add(db, agents, agent_key, f'{folder}/{agent_key}')
        return locker.held(db, agent_key)
    finally:
        shutil.rmtree(incoming, ignore_errors=True)
