"""ONE FILE: the agent as LARRYD reviews it. `<name>.larryd` is a zip of agent/ and nothing else (no project file, no
key, no compiled cache), made the same way every time (sorted names, one fixed time), so its sha256 names it.
open_safely() is what LARRYD does with a file anyone sent: a size cap, at most 200 plain files, no link, no path that
leaves the folder, no file that grows past the cap when unpacked; it unpacks into agent/ and runs nothing."""
import hashlib
import io
import pathlib
import stat
import zipfile

from . import shape

MOST_BYTES = 5_000_000   # packed and unpacked alike (LARRYD's limit for an agent)
MOST_FILES = 200
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def make(root):
    """-> (the file's bytes, its sha256) for the agent project at root."""
    agent = pathlib.Path(root).resolve() / shape.AGENT
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(agent.rglob('*')):
            rel = p.relative_to(agent)
            if p.is_file() and not p.is_symlink() and '__pycache__' not in rel.parts:
                info = zipfile.ZipInfo(rel.as_posix(), FIXED_TIME)
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, p.read_bytes())
    data = out.getvalue()
    return data, hashlib.sha256(data).hexdigest()


def open_safely(data, into):
    """Unpack a sent file into <into>/agent/. -> [what is wrong] (empty: unpacked). Nothing is run, nothing is trusted."""
    if len(data) > MOST_BYTES:
        return [f'the file is larger than {MOST_BYTES} bytes']
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        infos = z.infolist()
    except (zipfile.BadZipFile, ValueError, OSError):
        return ['it is not a .larryd file (a zip of agent/)']
    if not infos or len(infos) > MOST_FILES:
        return [f'it holds {len(infos)} files; an agent holds 1 to {MOST_FILES}']
    total, wrong = 0, []
    for i in infos:
        name = i.filename
        parts = name.split('/')
        mode = i.external_attr >> 16
        if name.startswith('/') or '\\' in name or ':' in name or any(p in ('', '.', '..') for p in parts):
            wrong.append(f'{name[:80]!r} is not a plain path inside agent/')
        elif stat.S_ISLNK(mode) or i.is_dir():
            wrong.append(f'{name[:80]!r} is a link or a folder entry, not a file')
        elif i.flag_bits & 0x1:
            wrong.append(f'{name[:80]!r} is encrypted')
        total += i.file_size
    if total > MOST_BYTES:
        wrong.append(f'it unpacks to more than {MOST_BYTES} bytes')
    if wrong:
        return wrong
    agent = pathlib.Path(into) / shape.AGENT
    agent.mkdir(parents=True)
    for i in infos:
        target = agent / i.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        with z.open(i) as src:
            body = src.read(i.file_size + 1)   # never more than it says (a lying header cannot grow it)
        if len(body) != i.file_size:
            return [f'{i.filename[:80]!r} is not the size it says']
        target.write_bytes(body)
    return []
