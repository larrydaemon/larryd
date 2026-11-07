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
            con.execute('DELETE FROM runtime_locker WHERE agent_key = ?', (agent_key,))
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


KIT = 'office.py'   # the office library every internal agent is packed with (its repo's _office/place.sh), beside the kits agent.json "libs" names


def kits_in(path, kits):
    """THE KITS INSIDE THE AGENT (the locker in place: an agent's folder is self-contained, production's shape): the office library
    and each kit its agent.json "libs" names, <kits>/<lib>.py, written into the agent's own folder, so the folder's hashes cover them
    and the agent finds them beside its entry, as it did in its packed copy. -> the kits written; Refused when one is missing."""
    try:
        libs = json.loads((path / locker.MANIFEST).read_text()).get('libs') or []
    except (OSError, ValueError):
        raise Refused(400, f'{locker.MANIFEST} is not readable')
    if not isinstance(libs, list) or not all(isinstance(lib, str) and PART.match(lib) and '.' not in lib for lib in libs):
        raise Refused(400, '"libs" names kits by their plain names')
    kits = pathlib.Path(kits)
    names = ([KIT] if (kits / KIT).is_file() else []) + [f'{lib}.py' for lib in libs]
    missing = [n for n in names if not (kits / n).is_file() or (kits / n).is_symlink()]
    if missing:
        raise Refused(400, f'no kit {", ".join(missing)} in {kits}')
    for n in names:
        try:
            (path / n).write_bytes((kits / n).read_bytes())
        except OSError:   # a locked folder (virtual_sanity's lock): nothing is held until it is opened
            raise Refused(409, f'{n} could not be written into the agent\'s folder (is the locker locked?)')
    return names


def hold_in_place(db, root, agent_key, folder, most_files, most_bytes, kits=None):
    """THE PLACE, IN PLACE (LARRYD_INTERNAL=1 and LARRYD_LOCKER): the agent is held where it is, <root>/<folder> (<name>/agent),
    nothing copied anywhere. Its kits written in first (kits_in, when a kits folder is named), then the same guards as a .larryd file
    (only plain files and paths, no link, within the limits, the manifest and its entry; agent.json's "key", when it names one, is
    the card key placed), then its row: the folder and the sha256 of its code (kits included) and manifest, which verify() checks
    before every call and run. The same folder placed again replaces its row. -> the locker row."""
    if not KEY.match(agent_key or ''):
        raise Refused(400, 'not a card key')
    root = pathlib.Path(root).resolve()
    try:
        path = locker._inside(root, folder)
    except ValueError:
        raise Refused(400, f'{folder} is not inside the locker {root}')
    if not path.is_dir() or (root / folder).is_symlink():
        raise Refused(400, f'{folder} is not a folder in the locker')
    if locker._links(path):
        raise Refused(400, f'{folder} holds a link; an agent is only its own files')
    if kits is not None:
        kits_in(path, kits)
    files = {p.relative_to(path).as_posix(): p.read_bytes() for p in sorted(path.rglob('*')) if p.is_file() and '__pycache__' not in p.relative_to(path).parts}
    check(files, most_files, most_bytes)
    named = json.loads(files[locker.MANIFEST]).get('key')
    if named not in (None, '', agent_key):
        raise Refused(400, f'{locker.MANIFEST} names the key {named}, not {agent_key}')
    con = sqlite3.connect(db)
    try:
        con.execute('DELETE FROM runtime_locker WHERE agent_key = ?', (agent_key,))
        con.commit()
    finally:
        con.close()
    try:
        locker.add(db, root, agent_key, path.relative_to(root).as_posix())
    except ValueError as why:
        raise Refused(400, str(why))
    return locker.held(db, agent_key)
