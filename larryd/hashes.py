"""THE HASHES, one recipe each, as the LARRYD runtime's locker computes them (so what larryd prints is what the runtime records).
- the code: every file of the folder but the manifest, by its path inside the folder and its bytes, in a fixed order
  (compiled caches are not the code);
- the manifest: its bytes;
- a skill: its definition as compact sorted JSON;
- a knowledge pack: every file of the pack, its pack.json too, by the same recipe as the code."""
import hashlib
import json
import pathlib


def _files(folder, skip=()):
    folder = pathlib.Path(folder)
    return sorted(p for p in folder.rglob('*') if p.is_file() and p.name not in skip and '__pycache__' not in p.relative_to(folder).parts)


def _tree(folder, skip=()):
    folder = pathlib.Path(folder)
    h = hashlib.sha256()
    for f in _files(folder, skip):
        h.update(f.relative_to(folder).as_posix().encode('utf-8') + b'\0' + f.read_bytes() + b'\0')
    return h.hexdigest()


def code(agent, manifest='agent.json'):
    """The code's hash as the runtime's locker computes it. The live half of an agent that declares a live page (live/ beside
    agent/) counts as `live/<file>`: it sits in the locker's folder that way, and is approved with the agent by this one hash."""
    agent = pathlib.Path(agent)
    listed = [(f.relative_to(agent).as_posix(), f) for f in _files(agent, skip=(manifest,))]
    half = agent.parent / 'live'
    try:
        declares = isinstance(json.loads((agent / manifest).read_text()).get('live'), dict)
    except (OSError, ValueError, AttributeError):
        declares = False
    if declares and half.is_dir() and not (agent / 'live').exists():
        listed += [(f'live/{f.name}', f) for f in sorted(half.iterdir()) if f.is_file() and f.name in ('live.json', 'page.html', 'page.js', 'room.py', 'page.css', 'rain.js')]
    h = hashlib.sha256()
    for rel, f in sorted(listed, key=lambda x: pathlib.PurePosixPath(x[0])):
        h.update(rel.encode('utf-8') + b'\0' + f.read_bytes() + b'\0')
    return h.hexdigest()


def manifest(agent, name='agent.json'):
    return hashlib.sha256((pathlib.Path(agent) / name).read_bytes()).hexdigest()


def definition(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def pack(folder):
    return _tree(folder)
