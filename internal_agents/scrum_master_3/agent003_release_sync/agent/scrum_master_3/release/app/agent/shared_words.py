"""THE WORDS (moved out of shared_where, 2026-10-21): his order book, and what is gone CUT from all he writes.

orders(): his orders as he wrote them. words(): every word of every order of kind 'gone'. cut(text), clean(obj),
cut_file(path): the text, the record, the log with those words cut. guard(): his own output cut as it is printed.
baseline(path), BASELINES, BASELINE_FOLDERS: his baselines keyed by real paths, written uncut. Collide: two names of one
record that would become one name once cut (the write is refused, never merged)."""
import json
import os
import re
import sys

from agent import shared_where as where


# ---------------------------------------------------------------- his order book (from the old today part)

ORDERS = where.ORDERS_FILE   # his order book: the key 'orders' of his settings, written by his hands alone

def orders(path=ORDERS):
    """His orders as he wrote them. -> list of dicts ([] when the file is missing or unreadable)."""
    try:
        with open(path, encoding='utf-8') as fh:
            return [o for o in json.load(fh).get('orders') or [] if o.get('id')]
    except (OSError, ValueError, AttributeError):
        return []


# ---------------------------------------------------------------- what is gone is cut (from the old gone part)

BASELINES = re.compile(r'files_(\d{4}-\d{2}-\d{2}|last)\.json|radar\.json')   # HIS BASELINES, KEYED BY PATH (the security review, 2026-10-21): the files he knows (files_<day>.json, files_last.json) and the radar's ledger (radar.json) name real files by their real paths; a cut path is another file's name, so they are written as they are, and O-1's count finds such a file itself

BASELINE_FOLDERS = ('files_seen',)   # the same baselines as files under his logs folder (row 010's looks, files_seen/<mark>/<day>.json), and its radar as findings of row 10: written as they are

class Collide(ValueError):
    """Two names of one record would become one name once what is gone is cut: the write is refused, never merged."""

def baseline(path):
    """Is this one of his path-keyed baselines (written uncut)?"""
    return bool(BASELINES.fullmatch(os.path.basename(path)))

_PATTERN = {}   # the order book as last read, (path, changed at, size) -> its pattern: read again only when the book changes

def words(book=None):
    """Every word of every order of kind 'gone', as his book has them now, the longest first. -> list"""
    got = []
    for o in orders(book or ORDERS):
        if o.get('kind') == 'gone':
            got += [str(w) for w in o.get('words') or [] if str(w).strip()]
    return sorted(set(got), key=lambda w: (-len(w), w))

def _pattern(book=None):
    book = book or ORDERS
    try:
        st = os.stat(book)
        key = (book, st.st_mtime_ns, st.st_size)
    except OSError:
        key = (book, None, None)
    if key not in _PATTERN:
        found = words(book)
        _PATTERN.clear()
        _PATTERN[key] = re.compile('( ?)(?:' + '|'.join(re.escape(w) for w in found) + ')( ?)', re.IGNORECASE) if found else None
    return _PATTERN[key]

def _gap(m):
    """what stands where a word was: one space when it stood between two words (or two spaces), else nothing"""
    before, after = m.group(1), m.group(2)
    if before and after:
        return ' '
    if before:
        return ' ' if m.end() < len(m.string) and m.string[m.end()].isalnum() else ''
    if after:
        return ' ' if m.start() > 0 and m.string[m.start() - 1].isalnum() else ''
    return ''

def cut(text, book=None):
    """The text without the words: each one taken out with the space beside it, one space kept between the two halves
    when it stood between two. Anything that is not text comes back as it was."""
    pattern = _pattern(book) if isinstance(text, str) else None
    return pattern.sub(_gap, text) if pattern else text

def clean(obj, book=None):
    """A record (dicts, lists, text) with the words cut from every name and every value in it. Two names of one dict
    that would become the same name raise Collide: one value is never written over another (the security review,
    2026-10-21: a path cut to another file's path took that file's place in his baseline)."""
    if isinstance(obj, str):
        return cut(obj, book)
    if isinstance(obj, dict):
        got = {}
        for k, v in obj.items():
            name = cut(k, book)
            if name in got:
                raise Collide(f'two names of one record become one ({name!r}) once what is gone is cut: not written')
            got[name] = clean(v, book)
        return got
    if isinstance(obj, (list, tuple)):
        return type(obj)(clean(v, book) for v in obj)
    return obj

def cut_file(path, book=None):
    """A file already written by someone else's lines (a job's log as it ran) has the words cut where it stands: the
    same file, written over from its start, so a writer that still holds it open keeps writing into it. A link is
    never followed. -> True when it held a word."""
    try:
        fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    except OSError:
        return False
    with os.fdopen(fd, 'r+b') as fh:
        text = fh.read().decode('utf-8', 'surrogateescape')
        new = cut(text, book)
        if new == text:
            return False
        fh.seek(0)
        fh.write(new.encode('utf-8', 'surrogateescape'))
        fh.truncate()
    return True

class _Cutting:
    """His own output (the round's lines into scrum.log, a runner's into its log) with the words cut as it is written."""
    def __init__(self, stream):
        self._stream = stream

    def write(self, text):
        return self._stream.write(cut(text))

    def writelines(self, lines):
        self._stream.writelines(cut(line) for line in lines)

    def __getattr__(self, name):
        return getattr(self._stream, name)

def guard():
    """From each of his programs' start: what it prints, and what goes wrong in it, is cut before it reaches his log."""
    for name in ('stdout', 'stderr'):
        stream = getattr(sys, name)
        if stream is not None and not isinstance(stream, _Cutting):
            setattr(sys, name, _Cutting(stream))
