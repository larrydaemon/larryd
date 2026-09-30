"""THE HASHES, one recipe each, as PF HANZO's locker computes them (so what larryd prints is what HANZO records).
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
    return _tree(agent, skip=(manifest,))


def manifest(agent, name='agent.json'):
    return hashlib.sha256((pathlib.Path(agent) / name).read_bytes()).hexdigest()


def definition(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def pack(folder):
    return _tree(folder)
