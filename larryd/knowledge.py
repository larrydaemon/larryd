"""A KNOWLEDGE PACK: a folder of plain text files an agent needs (pack.json {"name", "about"} + .md .txt .csv .json),
named by its hash (every file, by the locker's recipe), so a changed pack is a new pack. A member hires a pack like a
theme; no pack is held by PF HANZO yet, so `larryd pack` gives a pack its hash and checks its shape, nothing more."""
import json
import pathlib

from . import hashes, shape


def held():
    """-> {hash: pack}: the packs PF HANZO holds. None yet: PF HANZO has no knowledge door."""
    return {}


def check(folder):
    """-> (the pack's hash or '', [what is wrong · what to do])."""
    folder = pathlib.Path(folder)
    wrong = []
    if folder.is_symlink() or not folder.is_dir() or not (folder / shape.PACK).is_file():
        return '', [f'{folder} is not a knowledge pack (no {shape.PACK}) · make a folder with {shape.PACK} {{"name": ..., "about": ...}} and the text files']
    try:
        card = json.loads((folder / shape.PACK).read_text())
    except (UnicodeDecodeError, ValueError):
        card = None
    if not isinstance(card, dict) or sorted(card) != sorted(shape.PACK_FIELDS) or not all(isinstance(card[k], str) and card[k].strip() for k in card):
        wrong.append(f'{shape.PACK} is not {{"name": ..., "about": ...}} · write exactly those two fields, as plain words')
    for p in sorted(folder.rglob('*')):
        rel = p.relative_to(folder).as_posix()
        if p.is_symlink():
            wrong.append(f'{rel} is a link · put the real file in the pack, or remove it')
        elif any(part.startswith('.') for part in p.relative_to(folder).parts):
            wrong.append(f'{rel} is hidden · remove it; everything in a pack must be visible')
        elif p.is_file():
            if p.suffix not in shape.PACK_KINDS:
                wrong.append(f'{rel} is not a kind a pack holds · keep only {", ".join(sorted(shape.PACK_KINDS))} files')
            else:
                try:
                    p.read_text()
                except UnicodeDecodeError:
                    wrong.append(f'{rel} is not plain UTF-8 text · save it as UTF-8 text')
    return ('' if wrong else hashes.pack(folder)), wrong
