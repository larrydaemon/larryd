"""THE INTAKE: how an approved agent file becomes a locker folder. The file is one `.larryd` (a zip of agent/, as LARRYD's
submit door queued it); it is read with its own guards (no link, no path out, no hidden part, at most so many files and
bytes, the manifest and its entry there), written into the locker's <folder>/<agent_key>/ only when every file passes,
and then held by the locker's recipe. Nothing in it is run here."""
import io
import json
import pathlib
import re
import secrets
import shutil
import sqlite3
import stat
import zipfile

from . import locker

KEY = re.compile(r'^[A-Z]{4}_[0-9A-F]{12}_[0-9A-F]{4}$')   # a card's key, as the platform mints it (FROST's review takes only this)
PART = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.-]*$')        # one part of a path: no hidden part, no '..'


class Refused(Exception):
    def __init__(self, status, reason):
        super().__init__(reason)
        self.status, self.reason = status, reason


def from_zip(data, most_files, most_bytes):
    """-> {relative path: bytes} from a .larryd file, or Refused: a zip of plain files only, within the limits."""
    if len(data) > most_bytes:
        raise Refused(413, f'more than {most_bytes} bytes')
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        infos = [i for i in z.infolist() if not i.is_dir()]
    except (zipfile.BadZipFile, ValueError, OSError):
        raise Refused(400, 'not a .larryd file (a zip of agent/)')
    if len(infos) > most_files:
        raise Refused(413, f'more than {most_files} files')
    if sum(i.file_size for i in infos) > most_bytes:
        raise Refused(413, f'more than {most_bytes} bytes')
    out = {}
    for i in infos:
        if stat.S_ISLNK(i.external_attr >> 16):
            raise Refused(400, f'{i.filename} is a link, not a file')
        with z.open(i) as src:
            body = src.read(i.file_size + 1)
        if len(body) != i.file_size:
            raise Refused(400, f'{i.filename} is not the size it says')
        out[i.filename] = body
    return out


def check(raw, most_files, most_bytes):
    """-> the files, or Refused: every path plain and inside, within the limits, the manifest and its entry there."""
    if not isinstance(raw, dict) or not raw:
        raise Refused(400, 'no files')
    if len(raw) > most_files:
        raise Refused(413, f'more than {most_files} files')
    out, total = {}, 0
    for rel, data in raw.items():
        parts = str(rel).split('/')
        if not all(PART.match(p) for p in parts):
            raise Refused(400, f'{rel} is not a plain path inside the agent\'s folder')
        if not isinstance(data, bytes):
            raise Refused(400, f'{rel} is not a file')
        total += len(data)
        if total > most_bytes:
            raise Refused(413, f'more than {most_bytes} bytes')
        out['/'.join(parts)] = data
    try:
        card = json.loads(out[locker.MANIFEST]) if locker.MANIFEST in out else None
    except (UnicodeDecodeError, ValueError):
        card = None
    if not isinstance(card, dict) or not all(isinstance(card.get(k), str) and card[k] for k in locker.NEEDS) or card['entry'] not in out:
        raise Refused(400, f'{locker.MANIFEST} needs {", ".join(locker.NEEDS)} and its entry file')
    return out


def receive(db, agents, folder, agent_key, files):
    """Write checked files into agents/<folder>/<agent_key>/ and hold them in the locker: a changed agent replaces the old
    one, the same files give the same hashes. Everything is written aside before the old one is touched. -> the locker row."""
    if not KEY.match(agent_key or ''):
        raise Refused(400, 'not a card key')
    agents = pathlib.Path(agents).resolve()
    home = agents / folder
    home.mkdir(exist_ok=True)
    incoming = home / f'incoming_{secrets.token_hex(8)}'
    try:
        incoming.mkdir()
        for rel, data in files.items():
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
        if incoming.exists():
            shutil.rmtree(incoming, ignore_errors=True)
