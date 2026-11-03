"""HIS MEMORY AND HIS LAW (the owner 2026-10-16: "a new block for its own memory where it can keep
its own memory like the Transparency page, with its own mini law that is simple").

Three parts, newest first on his page (CONTRACT.md 4 and 5, 2026-10-21: settings are not data, history is not data):
  THE LAW       his rules, numbered (LAW below): the first thing he reads every round. Version 1, never written.
  THE LESSONS   the lessons table (the six, shared_store): a lesson of a row, written by the repair that worked, never by
                hand (law 4). Each is one line: the JSON of its row, repair, why, who taught it, the book's version.
  THE NOTES     his working notes, a log (a file, never a row: one JSON line a note, under his logs folder outside
                sanity): what the round found, what changed since the round before, what waits on Christensen.

THE RULEBOOK   the rules he judges by, each with an id, and ONE version for the book: his setting memory.rulebook
               (settings.json the default, a bump kept in his database's settings table), never a record. Every record he writes carries the version it was made under (stamp);
               a record from an older version is STALE: shown as old, never taken as the truth. The version moves only
               by Christensen's hand (`python -m agent.shared_memory bump "<why>"`): rules do not change all day.

    python -m agent.shared_memory show | law | bump "<why>" | note "<text>"

What is gone is cut from everything written here first (words.clean). A home given to a function here is a check's
own folder: its own database (the lessons, the values changed at run time), its own notes file and its own
settings.json (the defaults, read only); none is his instance's."""
import datetime
import json
import os
import sqlite3
import sys

from . import shared_store as _store
from . import shared_where as where
from . import shared_words as words   # what is gone cut (words.clean), his output cut (words.guard)

# HIS MINI LAW (the owner's three, 2026-10-16, in his words; 4 and 5 mine, agreed the same morning)
LAW = [
    "Don't stop working until healthy, all green.",
    "Don't ask to change rules. Fix the real problem.",
    "This tool is for rapid development: one clear process. Fix, prove with the row's own check, next.",
    "Never fake a green: a lesson is written by the repair that worked, never by hand.",
    "What only Christensen can do goes on one list, once a day, in his words.",
]
MOIRE_RULE = ('MOIRÉ shows the changes made (the owner 2026-10-17): a change that is written in git is development, a yellow report; '
              'only a change nobody wrote (a workspace file not as git has it) is red. Never ask to reset or pin its baseline; '
              'the baseline is only a step of the release.')
RULES = {   # the book's rules; a rule added here joins the live book at Christensen's next bump
    'light': 'A light is the state now: red while its own check finds the failure, green the moment it passes (the owner 2026-10-22: "the red is cleared instantly"); the day\'s record is kept in the words and the marks, never held in the light until a reset.',
    'seal': 'The sealed core changes only by Christensen\'s hand: one batch a day, one GO, one merge, one reseal.',
    'judge': 'The Judge and the smoke are the proofs; neither is edited to fit a change.',
    'real': 'Nothing is marked fixed without its own check passing; a lesson is written by the repair that worked.',
    'places': 'A session writes in git, in an instance folder, or nowhere; anything else is on the radar.',
    'moire': MOIRE_RULE,
    'workspace': 'He works in ~/virtual_workspace only (the owner 2026-10-21: "this agent scrum master has nothing to do with civilization cluster or anything else, just virtual workspace"): every search, count and scan reads that folder and nothing else; a root outside it is refused and said, never searched. Outside it he keeps ONE scratch folder of his own ("it can have its own scratch folder outside that is ok ... but it should have 1 scratch folder not a million"); a scratch folder is where he writes, never what he searches.',
    'tests': 'Tests live outside every virtual folder (the owner 2026-10-21): no tests/ folder inside ~/virtual_workspace or ~/virtual_sanity; every test is in ~/scratch/tests (the workspace\'s in ~/scratch/tests/workspace/<office>/tests, his own in ~/scratch/tests/scrum_master_3/checks) and finds its code through one setting (VIRTUAL_WORKSPACE). A tests/ folder found inside either is red, and is moved out, never kept.',
    'models': 'Web build = Opus 5.5 only; macOS and iOS = Fable 5.1 only (the owner 2026-10-22, his words: "web build = opus 5.5 only", "macos and ios = fable 5.1 only"): every Claude he starts names claude-opus-5-5 on its command; the nightly iPhone and Mac fix turns of the hot fix utility name claude-fable-5-1. Any other model is refused, and checks/test_models.py fails.',
    'speed': 'No change to a speed requirement, ever (the owner 2026-10-15, 2026-10-21): a red speed row is cured in the platform or stays red; a fix that touches a speed requirement is refused, and NO SHORTCUTS turns red.'
}
MOST_NOTES = 4000      # the notes log is trimmed to this many lines (the newest kept)
SHOWN = 12             # notes and lessons shown on his page
LESSON_ROW = 23        # a lesson of a row he cannot name is SELF HEALING's (row 23 keeps the lessons)
NOTES = 'memory_notes.jsonl'   # the notes log's file name (in a home given; his own under his logs folder, memory/)
SETTINGS = 'settings.json'     # a home's own settings file (a check's); his own is schemas/settings.json


def _folder(home=None):
    return os.path.abspath(os.path.expanduser(home)) if home else None


def _guard(home=None):
    """A LINK NEVER STANDS WHERE HE WRITES (as scrum._write refused a link where he wrote): the folder, its database and
    its notes log must be real ones. -> the folder (None: his own places)"""
    folder = _folder(home)
    if folder:
        for path in (folder, os.path.join(folder, _store.FILES['scrum_master']), os.path.join(folder, NOTES), os.path.join(folder, SETTINGS)):
            if os.path.islink(path):
                raise OSError(f'a link stands where he writes: {path}')
    return folder


_STORES = {}


def store_at(home=None):
    """HIS DATABASE through the one door (store.Store): his instance's (home None), or the one in the folder a check
    names. A link standing for the folder or the database is refused, never followed."""
    folder = _guard(home) or _store.instance()
    db = os.path.join(folder, _store.FILES['scrum_master'])
    if os.path.islink(folder) or os.path.islink(db):
        raise OSError(f'a link stands where he writes: {db}')
    st = _STORES.get(folder)
    if st is None or not os.path.isfile(db):
        st = _STORES[folder] = _store.Store(folder)
    return st


def _now(now=None):
    return (now or datetime.datetime.now().astimezone()).isoformat(timespec='seconds')


# ---------------------------------------------------------------- his settings: the defaults (one file, read only) and the values changed at run time (his database)
def settings_file(home=None):
    """HIS ONE SETTINGS FILE (schemas/settings.json), or a home's own settings.json (a check's scratch folder): THE
    DEFAULTS, read only (LOCKED by the final deploy: nothing writes it at run time)."""
    folder = _guard(home)
    return os.path.join(folder, SETTINGS) if folder else where.SETTINGS_FILE


def _home_of(home=None, path=None):
    """The home whose database keeps the values changed at run time: the home given; for a settings file named, his own
    (None) when it is his own file, else the folder it stands in (a check's)."""
    if home or not path:
        return home
    path = os.path.abspath(os.path.expanduser(path))
    return None if path == os.path.abspath(where.SETTINGS_FILE) else os.path.dirname(path)


def kept(home=None, path=None):
    """THE VALUES CHANGED AT RUN TIME, {name: value} (shared_store's settings table, one row a name, newest wins): his
    instance's database (home None), or the database in the home a check names. No database there yet, or one that
    cannot be read: none kept (every value its default). A database is never made by a read."""
    home = _home_of(home, path)
    try:
        folder = _guard(home) or _store.instance()
        if not os.path.isfile(os.path.join(folder, _store.FILES['scrum_master'])):
            return {}
        return store_at(home).settings_kept()
    except (OSError, sqlite3.Error, ValueError):
        return {}


def _over(got, values):
    """the defaults with each value kept set at its dotted place (a value kept wins over the default)"""
    for name, value in sorted(values.items()):
        *up, last = name.split('.')
        at = got
        for k in up:
            if not isinstance(at.get(k), dict):
                at[k] = {}
            at = at[k]
        at[last] = value
    return got


def settings(home=None, path=None):
    """his settings now: the defaults as the file says them (read again each time), each value changed at run time
    (kept in his database) over its default; none: {}"""
    try:
        with open(path or settings_file(home), encoding='utf-8') as fh:
            got = json.load(fh)
    except (OSError, ValueError):
        got = {}
    return _over(got if isinstance(got, dict) else {}, kept(home, path))


def setting_put(name, value, home=None, path=None, now=None):
    """ONE VALUE CHANGED AT RUN TIME (a switch, the worker's session or pause, the rulebook): kept in his database under
    its dotted name (shared_store.setting: a row of settings, newest wins), never written into settings.json. value
    None: taken away, the default stands again. -> his settings as they read now"""
    home = _home_of(home, path)
    store_at(home).setting(name, words.clean(value), at=_now(now))
    return settings(home)


SECTIONS = ('day', 'night', 'release')   # the three sections of rows.json, each its switch switches.section_<name>


def sections_off(home=None, path=None):
    """THE SECTIONS HE SWITCHED OFF (the owner 2026-10-22: "Day (toggle on off) Night (toggle on off) Release (toggle on
    off)"): the names of the sections whose switch is off now; a switch never flipped is on. -> set"""
    got = settings(home, path).get('switches') or {}
    return {s for s in SECTIONS if got.get(f'section_{s}', True) is False}


def rows_off(plan, home=None, path=None):
    """The rows of rows.json (plan: its whole dict) in a section he switched off. -> set of row numbers"""
    off = sections_off(home, path)
    where_ = {c['container']: c.get('section') for c in plan.get('containers') or []}
    return {int(r['n']) for r in plan.get('rows') or [] if where_.get(r.get('container')) in off}


# ---------------------------------------------------------------- the law and the rulebook
def law(home=None):
    """his rules, numbered: the mini law, version 1 (written in his code, never in a record)"""
    return {'version': 1, 'since': '', 'rules': [{'n': i + 1, 'text': t} for i, t in enumerate(LAW)]}


def rulebook(home=None):
    """the book he judges by: {version, since, why, rules: {id: text}}, as his settings keep it (memory.rulebook);
    none kept: version 1, the rules as they stand today"""
    got = (settings(home).get('memory') or {}).get('rulebook')
    if isinstance(got, dict) and isinstance(got.get('version'), int):
        return {'since': '', 'why': '', **got, 'rules': dict(got['rules']) if isinstance(got.get('rules'), dict) else dict(RULES)}
    return {'version': 1, 'since': '', 'why': 'the book begins: the rules as they stand this morning', 'rules': dict(RULES)}


def version(home=None):
    return int(rulebook(home)['version'])


def stamp(obj, home=None):
    """every record he writes carries the rulebook version it was made under"""
    if isinstance(obj, dict) and 'rules' not in obj:
        obj['rules'] = version(home)
    return obj


def stale(obj, home=None):
    """an old record: made under an earlier version of the book (or none)"""
    return not isinstance(obj, dict) or obj.get('rules') != version(home)


def bump(why, home=None, now=None):
    """Christensen's hand only: the book's version moves (his settings, memory.rulebook); every record of an older
    version is stale from this moment"""
    book = rulebook(home)
    for k, v in RULES.items():   # a rule written or corrected in RULES since the last bump is the book's now, under the new version (a corrected rule never stands behind its old words)
        book.setdefault('rules', {})[k] = v
    book.update(version=int(book['version']) + 1, since=_now(now), why=str(why)[:300])
    setting_put('memory.rulebook', book, home, now=now)   # a value changed at run time: his database, never settings.json
    note('rule', f"the rulebook moved to version {book['version']}: {book['why']}", home=home, now=now)
    return book


# ---------------------------------------------------------------- what he writes
def notes_path(home=None):
    """HIS NOTES LOG: memory/notes.jsonl under his logs folder (outside sanity), or a home's own memory_notes.jsonl."""
    folder = _guard(home)
    if folder:
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, NOTES)
    os.makedirs(os.path.join(_store.LOGS, 'memory'), exist_ok=True)
    return os.path.join(_store.LOGS, 'memory', 'notes.jsonl')


def note(kind, text, home=None, now=None, **slots):
    """one working note: what he found, what changed, what waits, what failed. kind: round, change, waits, failed, rule, worker"""
    row = {'at': _now(now), 'kind': str(kind)[:20], 'text': str(text)[:600], 'rules': version(home)}
    if slots:
        row['slots'] = {k: (v if isinstance(v, (int, float, bool, str, type(None))) else str(v)[:200]) for k, v in slots.items()}
    row = words.clean(row)
    path = notes_path(home)
    if os.path.islink(path):
        raise OSError(f'a link stands where he writes: {path}')
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0), 0o600), 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + '\n')
    _trim(path)
    return row


def _row_number(name):
    """a row named by its name (new or old, schemas/rows.json) -> its number; a name he cannot place is row 23's"""
    try:
        with open(where.ROWS_FILE, encoding='utf-8') as fh:
            plan = json.load(fh)
    except (OSError, ValueError):
        return LESSON_ROW
    name = str(name).strip().upper()
    for r in plan.get('rows') or []:
        if str(r.get('name', '')).upper() == name or str(r.get('n')) == name:
            return int(r['n'])
    old = {o.get('name', '').upper(): o.get('n') for o in plan.get('old_rows') or []}
    for r in plan.get('rows') or []:
        if old.get(name) in (r.get('was') or []):
            return int(r['n'])
    return LESSON_ROW


def lesson_words(row, repair, why, by='the repair that worked', home=None, now=None):
    """a lesson as lesson() keeps it, not yet written: -> (its row number, its one line (JSON), its time, the item)"""
    item = words.clean({'row': str(row)[:80], 'repair': str(repair)[:200], 'why': str(why)[:400], 'by': str(by)[:80], 'rules': version(home)})
    return _row_number(row), json.dumps(item, ensure_ascii=False), _now(now), item


def lesson(row, repair, why, by='the repair that worked', home=None, now=None, st=None):
    """a repair he learned, written by the repair itself when it worked (law 4: never by hand): one lesson of the row it
    was learned for (the lessons table), the same lesson kept once. st: the door the repair already holds (its database
    is there already: no database is ever made here, the owner 2026-10-23)"""
    n, text, at, item = lesson_words(row, repair, why, by, home, now)
    (st or store_at(home)).lesson(n, text, at)   # the lesson's words alone, its time in its own column: the same lesson is kept once whenever it is learned again
    return {'at': at, **item}


def fix_words(st, fid, title, row, tried, held, by, now=None):
    """THE LESSON OF A FIX, from the fix's own record (its id and words, what each turn that did not hold ran into, the
    turn that held), not yet written. -> (row number, one line, time, item) as lesson_words gives them"""
    folder = getattr(st, 'folder', None)
    home = None if not folder or os.path.abspath(folder) == os.path.abspath(_store.instance()) else folder
    tried = [_store.one_line(str(t)) for t in tried or [] if str(t or '').strip()]
    seen = []
    for t in tried:   # one line per distinct thing it ran into, the newest three
        if t not in seen:
            seen.append(t)
    repair = f"{fid} {_store.one_line(str(title or ''))[:80]}: the turn that held: {_store.one_line(str(held or ''))}"   # its id first: row 023 finds a fix's lesson by its id
    why = (f"{len(tried)} turn(s) did not hold ({'; '.join(x[:120] for x in seen[-3:])})" if tried else 'held on its first turn')
    return lesson_words(row, repair, why, by=by, home=home, now=now)


def fix_closed(st, fid, title, row, tried, held, by, now=None):
    """EVERY FIX LEAVES ITS LESSON, WRITTEN BY THE PATH THAT CLOSED IT (law 4; the owner 2026-10-20, rule 6): called by
    every code path that closes a fix (a request proven, an order green on its count, an old list item closed), the
    moment it closes. A B item closes with its lesson in one transaction instead (close_b). Under the 45 rows the
    resident worker's listener (DONE_HOOKS) did this; it went with the cut of 2026-10-21. Written into the database st
    stands on (his own: home None), never a new one. -> the lesson"""
    n, text, at, item = fix_words(st, fid, title, row, tried, held, by, now)
    st.lesson(n, text, at)
    return {'at': at, **item}


def close_b(st, b, turns, fact, by, now=None):
    """A B ITEM CLOSED AND ITS LESSON KEPT IN ONE TRANSACTION (store.build_close): its closing turn, its state and its
    lesson all land or none does, so a failed write never leaves a closed B without its lesson. -> the lesson"""
    n, text, at, item = fix_words(st, b['id'], b['rule'], LESSON_ROW, [t['result'] for t in turns], fact, by, now)
    st.build_close(b['id'], len(turns) + 1, b['approach'] or 1, _store.one_line(str(fact))[:500], n, text)
    return {'at': at, **item}


def _trim(path):
    """the notes log kept to MOST_NOTES lines, the newest kept: the oldest go (written whole, then one rename)"""
    try:
        with open(path, encoding='utf-8') as fh:
            lines = fh.read().splitlines()
    except OSError:
        return
    if len(lines) <= MOST_NOTES:
        return
    part = f'{path}.{os.getpid()}.part'
    with open(part, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines[-MOST_NOTES:]) + '\n')
    os.replace(part, path)


# ---------------------------------------------------------------- what he reads
def _notes(home=None):
    try:
        with open(notes_path(home), encoding='utf-8') as fh:
            got = [json.loads(line) for line in fh if line.strip()]
    except (OSError, ValueError):
        return []
    return [n for n in got if isinstance(n, dict)]


def _lessons(home=None):
    """the lessons as rows of the lessons table, oldest first, each read as the JSON it was written as (a lesson of plain
    words, row 023's own, is its repair)"""
    try:
        kept = store_at(home).lessons()
    except (OSError, ValueError, sqlite3.Error):
        return []
    out = []
    for l in kept:
        try:
            got = json.loads(l['lesson'])
        except ValueError:
            got = None
        if not isinstance(got, dict):
            got = {'at': l['at'], 'row': str(l['row']), 'repair': l['lesson'][:200], 'why': '', 'by': 'the repair that worked'}
        out.append({'at': l['at'], **got, 'n': l['row']})   # its time from its own column (a lesson kept before 2026-10-21 carries its own)
    return sorted(out, key=lambda x: str(x.get('at', '')))


def _lines(home, kind, most=None):
    """the notes ('notes') or the lessons ('lessons'), oldest first (the newest most of them when most is given)"""
    got = _notes(home) if kind == 'notes' else _lessons(home) if kind == 'lessons' else []
    return got[-most:] if most else got


def recall(home=None, shown=SHOWN):
    """the memory as his page shows it: the law, the book's version, the newest lessons and notes (newest first)"""
    book = rulebook(home)
    notes = _lines(home, 'notes', shown)[::-1]
    lessons = _lines(home, 'lessons', shown)[::-1]
    for r in notes + lessons:
        r['old'] = r.get('rules') != book['version']
    return {'law': law(home), 'version': book['version'], 'since': book.get('since', ''), 'why': book.get('why', ''),
            'lessons': lessons, 'notes': notes, 'written_at': _now()}


def round_note(rec, now=None, home=None):
    """the end of a round: one note of what he found and what changed since his last round note (the reds that came and
    went); stale rows (made under an older book) are named so, never taken as the truth"""
    rows = rec.get('rows') or {}
    reds = sorted(n for n, r in rows.items() if r.get('ok') is False)
    old = sorted(n for n, r in rows.items() if isinstance(r, dict) and r.get('rules') not in (None, version(home)))
    last = [r for r in _lines(home, 'notes', 200)[::-1] if r.get('kind') == 'round']
    before = set((last[0].get('slots') or {}).get('reds', '').split(', ')) - {''} if last else set()
    came, went = sorted(set(reds) - before), sorted(before - set(reds))
    text = f"round done: {len(reds)} red" + (f" ({', '.join(reds)})" if reds else ", all green")
    if came:
        text += f"; new since my last round: {', '.join(came)}"
    if went:
        text += f"; cleared since my last round: {', '.join(went)}"
    if old:
        text += f"; made under an older book, to recompute: {', '.join(old)}"
    return note('round', text, home=home, now=now, reds=', '.join(reds), came=', '.join(came), went=', '.join(went), stale=', '.join(old))


# ---------------------------------------------------------------- the resident worker's switch (his settings: switches.worker)

SWITCHES = None         # where his switches are read: None = his settings file; a folder (a check's) = its own settings.json

WORKER_SWITCH = SWITCH = 'worker'   # the resident worker's key in his switches (settings.json switches)


def switch_on(path=None):
    """THE OWNER'S SWITCH for the resident worker: switches.worker is true (as flipped, kept in his database; else the
    settings.json default). Absent, anything else, nothing that can be read: OFF. path: a folder (its own settings.json
    and database) or None (SWITCHES, else his own)."""
    try:
        return (settings(path or SWITCHES).get('switches') or {}).get(SWITCH) is True
    except (OSError, ValueError, TypeError):
        return False


def main(argv):
    if argv[:1] == ['law']:
        for r in law()['rules']:
            print(f"{r['n']}. {r['text']}")
        return 0
    if argv[:1] == ['bump'] and len(argv) > 1:
        book = bump(' '.join(argv[1:]))
        print(f"rulebook version {book['version']} since {book['since']}: {book['why']}")
        return 0
    if argv[:1] == ['note'] and len(argv) > 1:
        print(json.dumps(note('hand', ' '.join(argv[1:])), ensure_ascii=False))
        return 0
    got = recall()
    print(f"THE LAW (version {got['law']['version']})")
    for r in got['law']['rules']:
        print(f"  {r['n']}. {r['text']}")
    print(f"THE RULEBOOK version {got['version']} since {got['since']}: {got['why']}")
    print(f"LESSONS ({len(got['lessons'])} newest)")
    for l in got['lessons']:
        print(f"  {str(l.get('at', ''))[:16]} {l.get('row', '')}: {l.get('repair', '')} ({l.get('why', '')})")
    print(f"NOTES ({len(got['notes'])} newest)")
    for n in got['notes']:
        print(f"  {n['at'][:16]} [{n['kind']}] {n['text']}")
    return 0


if __name__ == '__main__':
    words.guard()
    sys.exit(main(sys.argv[1:]))
