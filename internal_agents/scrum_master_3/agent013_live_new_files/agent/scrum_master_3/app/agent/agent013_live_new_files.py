"""AGENT 008 · NEW FILES, LIVE: a SUB AGENT of the MARK IV agent (agent001), the replica's port of the original Scrum Master's row 021 NEW
FILES AND PAGES, STANDING ALONE (the owner 2026-10-27: "nothing can depend on the orginal"): the standard library alone, nothing of the
original read, imported or named as a step. THE RULE (the owner 2026-10-23: "the main thing is a extra file that is unexpected that was the
intention. claude code files are where they are expected and they use hooks. its that simple"): UNEXPECTED EXTRA FILES ONLY. Every file of
the workspace is known by name, size and time against the day's line (the last look before the day's 07:00 reset, New York); what is new,
changed and gone is counted, every new page named, and only an UNEXPECTED new file is red.
EACH RED'S 3-MINUTE STEP, SHORT (each red also ends with its own after "YOUR 3 MIN"):
  past 600000 files (walk stopped): du -sh ~/virtual_workspace/* | sort -h | tail -5, move the biggest folder that does not belong out
    of the workspace, press RUN AGENT (no ledger number: "belongs" never greens it; red on every look until the walk finishes)
  an unexpected file F-nnnn: remove it by hand, or answer belongs on its number (below), press RUN AGENT
  a crash: global_config.json / ledger.json: python -m json.tool on it, fix the line it names; git: git status in the workspace;
    the 60 s timeout: move the slow folder out; the program: press RUN AGENT again
THE UNEXPECTED NEW FILE, by these plain rules:
  a new name at the top of the workspace (a CLAUDE-SECURITY-* scan folder too: no exception, unexpected until the owner says it belongs)
  a new file with a sealed core file's name outside the core
  a new file outside the three places (git, the offices' instance folders, the compilers' folders) that git does not see (ignored)
  a program in a data folder; a kind that is not a compiler's own in its folder
  a new link, or a file that became a link
Claude Code's own files (a .claude folder anywhere, CLAUDE.md, CLAUDE.local.md, .mcp.json) are where they are expected: counted, never red.
A CHANGED FILE IS INFORMATION, NEVER RED (a file that became a link is no longer a changed file: it is a new link, red as a new link is).
PAST 600000 FILES its walk stops early: that is red on every look it happens, its own red OUTSIDE the ledger (never a numbered item, so no
'belongs' answer can ever make it green), with its own 3-minute step (CUT_STEP: move the biggest folder that does not belong out of the
workspace, then press RUN AGENT); no open item is closed as gone by a walk that did not reach it, and a cut walk never becomes the day's line.
A CRASH IS RED with its one fault and its one 3-minute step (global_config.json, ledger.json, git, the 60 s timeout).
ITS OWN LEDGER (ledger.json beside its looks): every unexpected file gets a number (F-0001, ...)
the first time it is seen, never given twice, and stays OPEN (red) until it is gone, seen by git, or the owner says it belongs, by its number:
    python -m agent.agent013_live_new_files belongs F-0001 "<why it belongs>"
A 'belongs' answer stands while the file is there and the question is the same one; removing a file stays his own manual step. The ledger
began once from the original's radar items (copy_new_files_ledger.py, a one-time script outside this office); never read from it again.
LIVE, ON EVERY CHANGE (the owner 2026-10-27: "not 5 minutes not anything else"): the page's one watcher (frame/frame_live.py) looks the
moment its TRIGGER moves (the workspace folder, held whole or its folders alone), its light kept in the office's live_status, a run written on a
flip; its look is pure, its own files (the day's line, last.json, the ledger) kept after each look (keep).
WHAT IT READS, READ ONLY: the workspace (names, sizes, times; nothing opened), git check-ignore, the workspace's global_config.json.
WHAT IT KEEPS: its own files alone, ~/scratch/reports/scrum_master_3/new_files/ (<day>.json, the day's line; last.json, its last look;
ledger.json, its numbered items and the owner's answers). NOT PORTED: the original's temp wipe (destructive)."""
import datetime
import fcntl
import json
import os
import re
import subprocess
import sys
import unicodedata
import zoneinfo

KEY = 'new_files'
SLOT = 'LIVE'   # where it lives: a shell of LIVE
ROW = 21   # its row in the original (agent021_checks_new_files): a name only, nothing read from there
NAME = 'New Files'
CARD_NAME = 'Scrum Master New Files'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Every new file known; an unexpected one is red'
WHAT = 'Every file new, changed or gone in the workspace; red only while an unexpected new file is open and unanswered'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'live', 'timezone': 'America/New_York'}   # LIVE: on every change of its TRIGGERS, never a clock (frame_red.due_at never misses a live job)
LIVE_SAID = 'LIVE · ON EVERY CHANGE'
ROW_FILE = 'agent021_checks_new_files.py'   # the original's program for this row: its skills index is filed under it

H = os.path.expanduser('~')
WORKSPACE = os.path.join(H, 'virtual_workspace')
STATE = os.path.join(H, 'scratch', 'reports', 'scrum_master_3', 'new_files')   # this agent's own looks and ledger, nowhere else (a check points WORKSPACE and STATE at scratch)


def triggers(store=None):
    """ITS TRIGGER, exactly its input: the workspace folder (a folder trigger: a file added, removed or replaced anywhere below it)"""
    return [os.path.join(WORKSPACE, '')]


TRIGGERS = triggers()
RESET = (7, 0)   # the day's line moves at 07:00 New York
KEEP = 3   # days of lines kept
HIS_OWN = '/SCRUM MASTER/'   # the original's own files in an older line: row 017's question, set aside
CLAUDE_NAMES = ('claude.md', 'claude.local.md', '.mcp.json')
MANY = 600000   # the most files one look walks
# THE WATCH RULES, ITS OWN (copied once 2026-10-27 from the original's settings scrum.watch_*; the office's settings have no fitting key)
WATCH_SKIP = frozenset({'.git'})   # folders never walked
WATCH_PROGRAMS = ('.py', '.pyc', '.pyo', '.pyw', '.pyx', '.pyd', '.pth', '.sh', '.zsh', '.bash', '.command', '.swift', '.js', '.mjs', '.cjs',
                  '.ts', '.html', '.htm', '.plist', '.dylib', '.so', '.bundle', '.app', '.bin', '.exe', '.dll', '.jar', '.wasm', '.node',
                  '.rb', '.pl', '.php', '.lua', '.applescript', '.scpt')   # a program's kinds: one in a data folder is red
WATCH_COMPILERS = {'__pycache__': ('.pyc',), '.pytest_cache': None, '.build': None, 'DerivedData': None, 'ios/build': None,
                   'macos/build': None}   # the compilers' folders: their own kinds (None: any)
CUT = '(more files than it walks)'   # the walk's own mark when it stops early: never a path, never a ledger item
CUT_STEP = ('du -sh ~/virtual_workspace/* | sort -h | tail -5 (it names the biggest folders): move the one that does not belong out of '
            'the workspace, then press RUN AGENT')   # the 600000-file red's own step: red again on every look until the walk finishes
RUN = 'then press RUN AGENT'
FAULT_STEPS = {
    'global_config.json': ('~/virtual_workspace/.venv/bin/python -m json.tool ~/virtual_workspace/global_config.json > /dev/null '
                           '(it names the broken line: put it right, or ask Claude Code to show it to you), ' + RUN),
    'ledger.json': ('~/virtual_workspace/.venv/bin/python -m json.tool ~/scratch/reports/scrum_master_3/new_files/ledger.json > /dev/null '
                    '(it names the broken line: put it right; or mv it to ledger.bad.json and every unexpected file is asked again from F-next), ' + RUN),
    'git check-ignore': ('cd ~/virtual_workspace && git status (it names what git refuses, e.g. a stale .git/index.lock: rm .git/index.lock '
                         'only when no git is running), ' + RUN),
    'the 60 s timeout': ('cd ~/virtual_workspace && time git check-ignore -v global_config.json (over a few seconds: git status names the '
                         'folder it is slow on; move that folder out of the workspace or into .gitignore), ' + RUN),
    'the program': 'press RUN AGENT once more; if the same line comes back, ask Claude Code to show you this line in app/agent/agent013_live_new_files.py',
}


class Fault(Exception):
    """A CRASH, NAMED: its one fault (a key of FAULT_STEPS) and the owner's one step, both in its one line"""
    def __init__(self, where, line):
        self.where, self.step = where, FAULT_STEPS[where]
        super().__init__(f'{where}: {line} · YOUR 3 MIN: {self.step}')


def fault_of(fault):
    """any crash as a Fault (never a red without its step)"""
    if isinstance(fault, Fault):
        return fault
    if isinstance(fault, subprocess.TimeoutExpired):
        return Fault('the 60 s timeout', 'git check-ignore did not answer in 60 s')
    line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
    return Fault('the program', line)


STEP = ('cd ~/larryd/internal_agents/scrum_master_3/agent013_live_new_files/agent/scrum_master_3/app && PYTHONDONTWRITEBYTECODE=1 REPLICA_OFFICE_APP="$PWD" '   # MOVED 2026-11-03: its own folder in LARRYD RUNTIME INTERNAL, its data there
        'REPLICA_INSTANCE=~/larryd/server/runtime/internal/instance/data/scrum_master_3 PYTHONPATH=. ~/virtual_workspace/.venv/bin/python '
        '-m agent.agent013_live_new_files belongs {n} "<why it belongs>"')


def day_of(now):
    """the day a moment belongs to: it starts at the reset, New York"""
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    return (now.astimezone(zone) - datetime.timedelta(hours=RESET[0], minutes=RESET[1])).date().isoformat()


def settings():
    """its own watch rules: {'skip', 'programs', 'compilers'}"""
    return {'skip': set(WATCH_SKIP), 'programs': tuple(k.lower() for k in WATCH_PROGRAMS), 'compilers': dict(WATCH_COMPILERS)}


def files(top, skip):
    """every file of the workspace by its path: [size, changed at(, 'l')]; nothing opened, no link followed, a linked folder an entry"""
    found = {}
    for root, dirs, names in os.walk(top):
        if len(found) > MANY:   # checked again at the end: the last folder walked can pass it too
            break
        links = [d for d in dirs if os.path.islink(os.path.join(root, d))]
        dirs[:] = [d for d in dirs if d not in skip and d not in links]
        for name in names + links:
            path = os.path.join(root, name)
            try:
                st = os.lstat(path)
            except OSError:
                continue
            found[os.path.relpath(path, top)] = [st.st_size, int(st.st_mtime)] + (['l'] if os.path.islink(path) else [])
    if len(found) > MANY:
        found[CUT] = [0, 0]
    return found


def claudes(p):
    """Claude Code's own files, wherever it puts them: never unexpected"""
    parts = unicodedata.normalize('NFC', p).lower().rstrip(os.sep).split(os.sep)
    return '.claude' in parts[:-1] or (parts[0] == '.claude' and p.endswith(os.sep)) or parts[-1] in CLAUDE_NAMES


def unseen(top, paths):
    """which of these git does not see (ignored), asked of git itself; git refusing is a fault, never every file counted as seen"""
    if not paths:
        return set()
    try:
        got = subprocess.run(['git', '-C', top, 'check-ignore', '-z', '--stdin'], input='\0'.join(paths), capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise Fault('the 60 s timeout', 'git check-ignore did not answer in 60 s') from None
    except OSError as e:
        raise Fault('git check-ignore', f'git would not start: {e}') from None
    if got.returncode not in (0, 1):
        raise Fault('git check-ignore', f"git refused (exit {got.returncode}): {' '.join((got.stderr or '').split())[:160]}")
    return {p for p in got.stdout.split('\0') if p}


def ledger_path():
    return os.path.join(STATE, 'ledger.json')


class _held:
    """the ledger held alone while it is read and written (a run and the owner's answer never write over each other)"""
    def __enter__(self):
        os.makedirs(STATE, exist_ok=True)
        self.fh = open(os.path.join(STATE, 'ledger.lock'), 'a')
        fcntl.flock(self.fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *_):
        fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()


def load():
    """ITS OWN LEDGER: {'next', 'items': {path: {'n', 'why', 'first', 'state', 'closed'[, 'how']}}}; none yet: empty, numbering from 1.
    A ledger it cannot read is a fault (never every answer silently forgotten)."""
    try:
        with open(ledger_path(), encoding='utf-8') as fh:
            book = json.load(fh)
    except FileNotFoundError:
        return {'next': 1, 'items': {}}
    except (OSError, ValueError) as e:
        raise Fault('ledger.json', f"unreadable: {' '.join(str(e).split())[:160]}") from None
    if not isinstance(book, dict) or not isinstance(book.get('items'), dict):
        raise Fault('ledger.json', f'it is not a ledger: {ledger_path()}')
    try:
        top = max([int(str(i.get('n', 'F-0'))[2:] or 0) for i in book['items'].values()] + [0])
    except (AttributeError, ValueError) as e:
        raise Fault('ledger.json', f'an item without a number F-<n>: {e}') from None
    book['next'] = max(int(book.get('next') or 1), top + 1)   # a number is never given twice
    return book


def save(book):
    os.makedirs(STATE, exist_ok=True)
    path = ledger_path()
    tmp = f'{path}.{os.urandom(6).hex()}.new'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(book, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def update(now, found, present, seen_by_git, write=True, cut=False):
    """ONE ROUND OF THE LEDGER: found = {path: why} unexpected now; present = the paths there now; seen_by_git(paths) -> those git sees.
    A new question gets the next number; an open item not found now is closed 'gone' (not there) or 'in git' (git sees it), else stays
    open; a 'belongs' answer stands while the file is there and the question is the same, its file gone it is closed 'gone'.
    write False: the same round on a copy, nothing saved (the pure look). -> the open items, by number, each {'n', 'why', 'first', 'path'}."""
    if not write:
        return _round(load(), now, found, present, seen_by_git, cut)
    with _held():
        book = load()
        out = _round(book, now, found, present, seen_by_git, cut)
        save(book)
    return out


def _round(book, now, found, present, seen_by_git, cut=False):
    """one round of the ledger over book (changed in place). cut: the walk stopped early, so a path it did not reach is not gone (nothing
    is closed 'gone' by it). -> the open items"""
    items, stamp = book['items'], now.isoformat()
    for path, item in items.items():
        if item.get('state') == 'belongs' and path not in present and not cut:
            item.update(state='gone', closed=stamp)   # if it ever comes back it is a new question
    for path, why in found.items():
        mine = items.get(path)
        if mine and mine.get('state') == 'open':
            mine['why'] = why   # the question as it stands now
            continue
        if mine and mine.get('state') == 'belongs' and mine.get('why') == why:
            continue   # the owner's word stands
        items[path] = {'n': f"F-{book['next']:04d}", 'why': why, 'first': stamp, 'state': 'open', 'closed': None}
        book['next'] += 1
    waiting = [p for p, i in items.items() if i.get('state') == 'open' and p not in found]
    seen = set(seen_by_git([p for p in waiting if p in present]))
    for p in waiting:
        if p not in present and not cut:
            items[p].update(state='gone', closed=stamp)
        elif p in seen:
            items[p].update(state='in git', closed=stamp)
    return sorted(({'path': p, **i} for p, i in items.items() if i.get('state') == 'open'), key=lambda i: i['n'])


def belongs(number, words, now=None):
    """THE OWNER'S ANSWER: the open item by its number belongs, in his words. -> the item, or None (no open item by that number)."""
    if not str(words or '').strip():
        raise ValueError('an answer says why it belongs, in words')
    now = now or datetime.datetime.now(zoneinfo.ZoneInfo(SCHEDULE['timezone']))
    with _held():
        book = load()
        for path, item in book['items'].items():
            if item.get('n') == str(number).upper() and item.get('state') == 'open':
                item.update(state='belongs', closed=now.isoformat(), how=str(words).strip()[:300])
                save(book)
                return {'path': path, **item}
    return None


def _read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) and isinstance(got.get('files'), dict) else None
    except (OSError, ValueError):
        return None


def _write(name, look):
    os.makedirs(STATE, exist_ok=True)
    path = os.path.join(STATE, f'{name}.json')
    tmp = f'{path}.{os.urandom(6).hex()}.new'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(look, fh, ensure_ascii=False)
    os.replace(tmp, path)


def line_of(day, have, moment, write=True):
    """THE DAY'S LINE: its own <day>.json; at a new day its last look before (last.json); its very first look ever: the workspace as it
    stands (its own baseline, nothing seeded from elsewhere). Older days pruned past KEEP. write False: the line as it would be, nothing written."""
    base = _read(os.path.join(STATE, f'{day}.json'))
    if not write:
        return base or _read(os.path.join(STATE, 'last.json')) or {'at': moment.isoformat(), 'files': have}
    if base is None:
        base = _read(os.path.join(STATE, 'last.json')) or {'at': moment.isoformat(), 'files': have}
        _write(day, base)
        old = sorted(n[:-5] for n in os.listdir(STATE) if re.fullmatch(r'\d{4}-\d\d-\d\d\.json', n) and n[:-5] != day)
        for d in old[:max(0, len(old) - (KEEP - 1))]:
            try:
                os.remove(os.path.join(STATE, f'{d}.json'))
            except OSError:
                pass
    _write('last', {'at': moment.isoformat(), 'files': have})
    return base


def judge(now=None):
    """ONE LOOK, NOTHING WRITTEN: -> {'summary', 'ok', 'unexpected': [{'n', 'why', 'path'}], 'new', 'changed', 'gone', 'pages', 'claude', 'since',
    '_keep'} (_keep: what keep() writes after it, never kept in a run)"""
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    moment = (now or datetime.datetime.now(zone)).astimezone(zone)
    day, conf = day_of(moment), settings()
    try:
        with open(os.path.join(WORKSPACE, 'global_config.json'), encoding='utf-8') as fh:
            gc = json.load(fh)
        gc['offices'].values(), gc['databases']['products']
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        raise Fault('global_config.json', f"unreadable: {type(e).__name__}: {' '.join(str(e).split())[:160]}") from None
    have = files(WORKSPACE, conf['skip'])
    cut = have.pop(CUT, None) is not None   # the mark is no file: never new, never a name at the top, never a ledger item
    whole = have
    base = line_of(day, have, moment, write=False)
    have = {p: v for p, v in have.items() if not p.startswith(HIS_OWN)}
    was = {p: v for p, v in base['files'].items() if not p.startswith(HIS_OWN)}

    instances = tuple(os.path.join(o['instance'], '') for o in gc['offices'].values() if o.get('instance')) + tuple(
        os.path.join(f'{n}-mini', f'{n}-mini', 'instance', '') for n in gc['offices'] if os.path.isdir(os.path.join(WORKSPACE, f'{n}-mini', f'{n}-mini', 'instance')))
    compilers = conf['compilers']

    def place(p):
        if p.startswith(instances):
            return 'data'
        parts = p.split(os.sep)
        for key in compilers:
            if p.startswith(os.path.join(key, '')) if os.sep in key else key in parts[:-1]:
                return key
        return ''
    kind = lambda p: os.path.splitext(re.sub(r'\.\d+$', '', p))[1].lower()
    home = lambda p: p.lower().startswith('.claude' + os.sep)

    new = sorted(p for p in have if p not in was)
    outside = [p for p in new if not place(p) and not home(p)]
    gone = sorted(p for p in was if p not in have and not place(p) and not home(p))
    changed = sorted(p for p in have if p in was and have[p] != was[p] and not place(p) and not claudes(p))
    core = os.path.join(gc['databases']['products'], '')
    sealed = {os.path.basename(p).lower() for p in was if p.startswith(core) and (f'{os.sep}core_engine{os.sep}' in p or f'{os.sep}schemas{os.sep}' in p)} | {'global_config.json'}
    hidden = unseen(WORKSPACE, outside)
    tops = {q.split(os.sep)[0].lower() for q in was}
    at_top = [p for p in new if (p.split(os.sep)[0].lower() not in tops or os.sep not in p) and not claudes(p)]
    found = [('a new name at the top', t) for t in sorted({p.split(os.sep)[0] + os.sep if os.sep in p else p for p in at_top})]
    found += [("a new file with a sealed core file's name outside the core", p) for p in new if os.path.basename(p).lower() in sealed and not p.lower().startswith(core.lower())]
    found += [('a new file git does not see', p) for p in outside if p in hidden and p not in set(at_top)]
    found += [('a program in a data folder', p) for p in new if place(p) == 'data' and kind(p) in conf['programs']]
    found += [(f"not a compiler's own kind in {place(p)}", p) for p in new if place(p) in compilers and compilers[place(p)] is not None and kind(p) not in tuple(compilers[place(p)])]
    found += [('a link', p) for p in new if len(have[p]) > 2]
    found += [('a file became a link', p) for p in have if p in was and len(have[p]) > 2 and len(was[p]) < 3]
    tracked = {}
    for why, p in found:
        if not claudes(p):
            tracked.setdefault(p, why)
    present = set(have) | {q.split(os.sep)[0] + os.sep for q in have if os.sep in q}
    # ITS OWN LEDGER: each unexpected file its number; an open one red until gone, seen by git (a folder only by going), or said to belong
    seen_by_git = lambda paths: set(p for p in paths if not p.endswith(os.sep)) - unseen(WORKSPACE, [p for p in paths if not p.endswith(os.sep)])
    items = [{'n': i['n'], 'why': i['why'], 'path': i['path']} for i in update(moment, tracked, present, seen_by_git, write=False, cut=cut)
             if not claudes(i['path']) and i['path'] != CUT]   # an old ledger's CUT item is no item: the cut red stands on its own below
    pages = [p for p in outside if p.endswith('.html')]
    claude = sum(1 for p in set(new) | set(q for q in was if q not in have) | {q for q in have if q in was and have[q] != was[q]} if claudes(p) or home(p))
    try:
        since = datetime.datetime.fromisoformat(str(base.get('at'))).astimezone(zone).strftime('%H:%M')
    except ValueError:
        since = '?'
    word = f"since {since}: {len(outside)} new, {len(changed)} changed, {len(gone)} gone" + (f" · new page(s): {', '.join(os.path.basename(p) for p in pages[:6])}" if pages else '')
    word += f" · Claude Code's home: {claude} files" if claude else ''
    heads, steps = [], []
    if cut:   # red on every look it stops early, whatever the ledger or the line holds: never a green from a walk that did not finish
        heads.append(f'more than {MANY} files: its walk stopped early')
        steps.append(CUT_STEP)
    if items:
        heads.append(f"{len(items)} unexpected file(s): " + '; '.join(f"{i['n']} {i['why']}: {i['path']}" for i in items[:4]) + (f' (+{len(items) - 4} more)' if len(items) > 4 else ''))
        steps.append('remove it, or say it belongs by its number: ' + STEP.format(n=items[0]['n']))
    head = '; '.join(heads) or 'nothing unexpected'
    step = (' · YOUR 3 MIN: ' + '; and '.join(steps)) if steps else ''
    return {'summary': f'{head} · {word}{step}', 'ok': not items and not cut, 'cut': cut, 'unexpected': items, 'new': len(outside), 'changed': len(changed), 'gone': len(gone),
            'pages': pages, 'claude': claude, 'since': since, 'at': moment.strftime('%H:%M'), 'lists': {'new': outside[:200], 'changed': changed[:200], 'gone': gone[:200]},
            '_keep': {'day': day, 'have': whole, 'moment': moment, 'tracked': tracked, 'present': present, 'cut': cut}}


def look(store=None, shells=None, now=None):
    """ITS ONE LOOK, PURE (nothing written). -> {'state': GREEN|RED, 'summary', 'why', 'step', 'said', '_keep'} (said: what a run keeps)"""
    try:
        got = judge(now)
    except Exception as fault:   # a crash, named, with its step, to whoever looks
        raise fault_of(fault) from fault
    keep_ = got.pop('_keep')
    head, _, step = got['summary'].partition(' · YOUR 3 MIN: ')
    return {'state': 'GREEN' if got['ok'] else 'RED', 'summary': got['summary'], 'why': '' if got['ok'] else head, 'step': step, 'said': got, '_keep': keep_}


def keep(got):
    """ITS OWN FILES AFTER A LOOK (the day's line, last.json, the ledger's numbers and closings): the same round the look counted, written; its
    own folder alone (STATE), never the workspace"""
    k = (got or {}).get('_keep')
    if not k:
        return
    if not k.get('cut'):   # a walk that stopped early is never the day's line nor the last look (its unreached files would come back as new)
        line_of(k['day'], k['have'], k['moment'])
    seen_by_git = lambda paths: set(p for p in paths if not p.endswith(os.sep)) - unseen(WORKSPACE, [p for p in paths if not p.endswith(os.sep)])
    update(k['moment'], k['tracked'], k['present'], seen_by_git, cut=k.get('cut', False))


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT; the page writes its live flips itself): one look, its own files kept. Nothing unexpected: DONE, exit 0. An unexpected
    new file open and unanswered: FAILED, exit 1, each by its number in its own ledger, the owner's one step last. A walk past 600000 files:
    FAILED, exit 1, on every look it happens (no ledger item, no answer greens it), CUT_STEP its step. A crash (a record it cannot
    read, git refusing, the 60 s timeout): FAILED, exit 1, its one fault named and its one 3-minute step. -> what it wrote."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        got = look(store, shells, now)
        keep(got)
        said = got['said']
    except Exception as fault:   # ANY CRASH IS RED: never no record and no light, and never without its one step
        f = fault_of(fault)
        said = {'summary': f'FAILED · {f}', 'fault': f.where, 'step': f.step}
        store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps(said), 'FAILED')
        return said
    ok = said['ok']
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0 if ok else 1, json.dumps(said), 'DONE' if ok else 'FAILED')
    return said


def latest(store, job_key):
    """What its last run wrote, or None before a first run."""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except ValueError:
            return None
    return None


def until_next(now=None, schedule=None):
    """LIVE: no next time (it looks on every change of its triggers): None"""
    return None


def clock(schedule=None):
    """Its clock in its shell: NEW YORK · LIVE · ON EVERY CHANGE (no hands: no hour it waits for)."""
    schedule = schedule or SCHEDULE
    return {'zone': schedule['location'], 'at': '', 'said': LIVE_SAID, 'when': LIVE_SAID, 'repeat': LIVE_SAID, 'hour_deg': 0, 'minute_deg': 0}


def content(store, job_key, block=None):
    """ITS OWN CONTENT ON THE ONE CANVAS: words, never markup: its last look (the line, each unexpected file, the lists folded); else
    that nothing is looked at yet."""
    s = latest(store, job_key)
    if s is None:
        return [{'kind': 'note', 'title': 'New files', 'text': 'Not looked yet: its first look comes on the page\'s start (live, on every change, or RUN AGENT).'}]
    if 'ok' not in s:
        return [{'kind': 'note', 'title': 'New files', 'text': f"Not looked: its last run {s.get('summary') or 'FAILED'}."}]
    lines = [('subtitle', 'Nothing unexpected' if s['ok'] else (f'More than {MANY} files: its walk stopped early; ' if s.get('cut') else '') + f"{len(s['unexpected'])} unexpected file(s)", 'radar'),
             ('body', f"Since {s['since']}: {s['new']} new, {s['changed']} changed, {s['gone']} gone" + (f", Claude Code's home {s['claude']}" if s.get('claude') else ''), '')]
    lines += [('body', f"{i['n']} · {i['why']}: {i['path']}", 'unexpected') for i in s['unexpected']]
    if s.get('pages'):
        lines.append(('body', 'New page(s): ' + ', '.join(os.path.basename(p) for p in s['pages']), ''))
    lists = s.get('lists') or {}
    return [{'kind': 'words', 'title': 'New files', 'under': f"Looked at {s.get('at', '')}, by its run", 'lines': lines,
             'detail': [('new', 'New', lists.get('new', [])), ('changed', 'Changed', lists.get('changed', [])), ('gone', 'Gone', lists.get('gone', []))]}]


def main(argv):
    """THE OWNER'S ANSWER, by hand: python -m agent.agent013_live_new_files belongs F-0001 "<why it belongs>"; open: the open items."""
    if argv[:1] == ['belongs'] and len(argv) >= 3:
        got = belongs(argv[1], ' '.join(argv[2:]))
        print(f"{got['n']} · belongs · {got['path']} · {got['how']}" if got else f'no open item by that number: {argv[1]}')
        return 0 if got else 1
    if argv[:1] == ['open']:
        for p, i in sorted(load()['items'].items(), key=lambda kv: kv[1]['n']):
            if i.get('state') == 'open':
                print(f"{i['n']} · since {i.get('first', '')[:16]} · {i['why']}: {p}")
        return 0
    print('usage: python -m agent.agent013_live_new_files belongs F-0001 "<why it belongs>"\n       python -m agent.agent013_live_new_files open')
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
