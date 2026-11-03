"""AGENT 016 · PROVE (the DAY group, the owner 2026-10-28: "DAY is a group on the top right each should say day / and we should see each /
build each one"; "all of day needs to be rewritten its all hotfix style for the day no judge"): a SUB AGENT of the MARK IV agent (agent001),
lower rank, its own block in the DAY group, its own light and its own run. STEP 6: PROVE (the original's 013: "proven or not"): on the tree still at its base and changed in its own recorded files alone, the built request's own tests run on the hot fix tree, unchanged since frozen: every one passes, none skipped, the tree the same after; the change's fingerprint (its diff from its base and its new files' bytes) kept in its side file. A red on its tests puts its own change back and sets it aside, stuck today; a press that moved the request during the run ends red with its change put back too, but never stuck: its state stays as he set it (never set aside, see _set_aside).

THE DAY, STEP BY STEP, each step its own agent (agent011 to agent020; agent021 the backlog): the requests, building now, main first, pick,
build, prove, review, commit (then pick again, one request at a time), the hot fix walk (once for every commit of the day), cleanup. A step
that ends green takes the next step's RUN before it writes its own DONE, and the first run drives the next ones in a loop (the chain the page
hands every run: no agent imports another), so RUN AGENT on THE REQUESTS runs the whole day block by block, and RUN AGENT on any step runs the
day from there. A red step stops there: it is THE RED's, its one step said. ONE DAY AT A TIME: one lock for the whole day, a second press ends
red. ON THE HOT FIX TREE (~/spine_worktrees/hotfix), NO JUDGE, NO SEAL, NO PUBLISH: production takes a change only by his AI ECHO HOTFIX
button, never pressed here. Its requests are this office's own (nothing read from the original). ON RUN AGENT ONLY: never due.

ITS BLOCK, THE ORIGINAL'S ROW 013 (content): Proven or not (the built request next, then every request past its build and when its frozen
tests passed, or no proof of its own recorded), WHY IT'S RED while its newest run is red, Not proven: set aside (each request it set aside,
stuck today, his line and its BACK TO ASKED press); its run line the original's list (report)."""
import datetime
import fcntl
import hashlib
import inspect
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import zoneinfo

KEY = 'prove'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
ROW = 13   # the original's row 013
NAME = 'Prove'
CARD_NAME = 'Scrum Master Prove'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Prove: its own tests pass, unchanged since frozen'
WHAT = "Runs the built request's own frozen tests on the hot fix tree: every one passes, none skipped, the change fingerprinted"
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due (frame_red.due_at)
ROW_FILE = 'agent016_day_prove.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes: in its own thread, the page answers RUN AGENT at once
NEXT = 'review'   # the step it hands on to when it ends green
PRESSES = ('back',)   # its own button on each request it set aside: BACK TO ASKED (his hand line, pressed; the page's agent_press route runs press for these alone)
ASIDE_TITLE, ASIDE_EMPTY = 'Not proven: set aside', 'Nothing Prove set aside is stuck today.'
PAST_BUILDING = ('proven', 'reviewed', 'approved', 'waiting_takein', 'taken_in')   # the original's row 013: the states a request holds only with a proven fix

HOME = os.path.expanduser('~')
CONF = {'tree': os.path.join(HOME, 'spine_worktrees', 'hotfix'), 'main': 'main',
        'utility': [os.path.join(HOME, 'virtual_workspace', '.venv', 'bin', 'python'), os.path.join(HOME, 'virtual_workspace', 'utilities', 'build', 'walk', 'hotfix.py')],
        'utility_cwd': os.path.join(HOME, 'virtual_workspace'), 'utility_seconds': 3 * 3600,
        'utility_lock': os.path.join(HOME, 'spine_scratch', 'hotfix_runs', 'running.lock'),   # the hot fix utility's own lock: its pid while it runs
        'writer': os.path.join(HOME, 'scratch', 'reports', 'scrum_master', 'developer.lock'),   # THE OTHER WRITER'S MARK the utility honors (its writer_waits): our pid while a step touches the tree
        'tests': os.path.join(HOME, 'scratch', 'tests', 'day'),   # every request's own tests, outside every virtual folder (his rule: tests live in ~/scratch/tests); the day's lock beside them
        'python': os.path.join(HOME, 'virtual_workspace', '.venv', 'bin', 'python'),
        'write_seconds': 15 * 60, 'build_seconds': 25 * 60, 'review_seconds': 7 * 60, 'prove_seconds': 10 * 60}
WAITING = 'asked'   # the backlog
PICKED, BUILT = 'planned', 'building'   # the table's own states (its CHECK holds them): picked is planned, built is building
IN_HAND = (PICKED, BUILT, 'proven', 'reviewed')   # a request between its pick and its commit: only one at a time, on the tree
COMMITTED, READY, STUCK = 'approved', 'waiting_takein', 'stuck_today'   # committed waits for the walk as approved; walked READY is ready
BEAT = 60   # seconds between two heartbeats of a long step (THE RED's QUIET is 3 minutes)
GIT_SECONDS = 120   # the longest one git call may run: its calls end in seconds, one past this is hung, stopped and red (never RUNNING forever with the day's lock and the writer mark held)
HAND = 'YOUR 3 MIN: '
DAY_EMAIL = 'day@localhost'   # THE DAY's own commits (its merge of main, its commit of a request) carry it
SIDE, HIRE_MARK = '.day_base', '.day_hire'   # A REQUEST'S SIDE FILES in its tests folder (~/scratch/tests/day/<id>, outside the tree: no commit carries them, never a test, never in its tests' sha): its pick's base and its proof; the pid of the worker hired for it now
BUILT_MARK = '.day_built_'   # A REQUEST'S BASE AND BUILT FILES AGAIN (<tests>/.day_built_<id>, Build's), beside its tests folder: read when that folder is gone with its side file
NO_GIT = ('commit', 'push', 'reset', 'checkout', 'switch', 'restore', 'rebase', 'merge', 'branch', 'tag', 'worktree', 'stash', 'add', 'rm', 'clean',
          'update-ref', 'commit-tree', 'cherry-pick', 'revert', 'am', 'notes', 'replace', 'filter-branch', 'config')
NO_BASH = ('git -C', 'git -c', 'git --git-dir', 'git --work-tree', 'gcloud', 'gsutil', 'ssh', 'scp', 'rsync', 'sudo', 'launchctl', 'kill', 'pkill', 'killall',
           'pip', 'pip3', 'python -m pip', 'python3 -m pip', 'uv', 'brew', os.path.join(HOME, 'virtual_workspace', '.venv', 'bin'))
NO_WRITE = tuple(os.path.join(HOME, p) for p in ('virtual_workspace', 'virtual_sanity', 'virtual_sanity_records', 'scratch/reports', 'scratch/requests', 'spine_scratch', '.claude', 'Library')) + (os.path.join(CONF['tree'], '.git'),)


def _denied(*more):
    """A HIRED WORKER'S DENIES, frame_red.FIXER's kind: every git form that moves the tree's git, the commands that reach past this laptop
    or stop a process, and no write outside the tree and its tests folder (the workspace and its .venv, the offices, the reports, his claude)"""
    return ','.join(['Task', 'NotebookEdit'] + [f'Bash(git {g}:*)' for g in NO_GIT] + [f'Bash({c}:*)' for c in NO_BASH]
                    + [f"{tool}(//{p.lstrip('/')}/**)" for p in (*NO_WRITE, *more) for tool in ('Edit', 'Write')])


TEST_WRITER = ['claude', '-p', '--model', 'claude-opus-5-5', '--permission-mode', 'acceptEdits', '--allowedTools', 'Read,Edit,Write,Glob,Grep,Bash', '--disallowedTools', _denied()]
DEVELOPER = ['claude', '-p', '--model', 'claude-opus-5-5', '--permission-mode', 'acceptEdits', '--allowedTools', 'Read,Edit,Write,Glob,Grep,Bash', '--disallowedTools', _denied(CONF['tests'])]   # its tests are frozen: no write there either
READER = ['claude', '-p', '--model', 'claude-opus-5-5', '--allowedTools', 'Read,Glob,Grep', '--disallowedTools', 'Edit,Write,Bash,Task,NotebookEdit']
VERDICT = re.compile(r'^\s*VERDICT\s*:\s*(LEGIT|STUPID)\b[\s:,.·-]*(.*?)\s*$', re.I)
CAPS = {'diff': 60000, 'file': 20000, 'tests': 20000}   # the most of a change the blind reader reads whole: a bigger one is never cut


def _now():
    return datetime.datetime.now(zoneinfo.ZoneInfo(SCHEDULE['timezone']))


def _stamp():
    return _now().isoformat(timespec='seconds')


def _line(fault):
    return (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]


def _where(fault):
    """WHERE A CRASH HAPPENED: the last frame in this agent's own file (a library's frame says nothing he can open), else the last frame"""
    frames = traceback.extract_tb(fault.__traceback__) if fault.__traceback__ else []
    own = [f for f in frames if os.path.abspath(f.filename) == os.path.abspath(__file__)]
    at = (own or frames or [None])[-1]
    return f'{os.path.basename(at.filename)} line {at.lineno}' if at else 'its own code'


class NotMeasured(RuntimeError):
    """A READ OF THE TREE THAT FAILED: not measured, never clean; said first, with its file and line, and his step is the tree's, not the code's"""


def _git(tree, runner=subprocess.run):
    """git in the tree, every path taken as typed (--literal-pathspecs: a file named with * or ? is that file alone), its bytes kept whole;
    a call past GIT_SECONDS is stopped and raises subprocess.TimeoutExpired"""
    def git(*args):
        return runner(['git', '--literal-pathspecs', *args], cwd=tree, capture_output=True, text=True, errors='surrogateescape', timeout=GIT_SECONDS)
    return git


def _out(git, *args, codes=(0,)):
    """A READ A GREEN STANDS ON: what git printed, or NotMeasured when it did not answer (an empty read is never an empty change or a HEAD at its base)"""
    try:
        seen = git(*args)
    except OSError as fault:   # no folder to run git in: not measured either
        raise NotMeasured(f'not measured: git {args[0]} failed ({_line(fault)})') from fault
    if seen.returncode not in codes:
        raise NotMeasured(f'not measured: git {args[0]} failed ({_last(seen.stderr)[:120]})')
    return seen.stdout


def _status(git, *more):
    """the tree's own status, NUL separated (a path with any byte said whole): [(code, path)]"""
    try:
        seen = git('status', '--porcelain=v1', '-z', *more)
    except OSError as fault:   # no folder to run git in: not measured either
        raise NotMeasured(f'not measured: git status failed ({_line(fault)})') from fault
    if seen.returncode != 0:   # a status that did not read is never a clean tree (its blind rule read 2026-10-31)
        raise NotMeasured(f'not measured: git status failed ({_last(seen.stderr)[:120]})')
    out = seen.stdout
    items, parts, i = [], out.split('\0'), 0
    while i < len(parts):
        e = parts[i]
        if len(e) > 3:
            items.append((e[:2], e[3:]))
            if e[0] in 'RC':
                i += 1
        i += 1
    return items


def _cache(p):
    return '__pycache__' in p.split('/') or p.endswith('.pyc') or p.endswith('.DS_Store')


def _changed(git):
    return [p for code, p in _status(git, '--untracked-files=all') if code != '!!' and not _cache(p)]


def _watched(git, tree):
    """EVERY IGNORED OR CACHE FILE OF THE TREE, A COMMIT NEVER CARRIES THEM AND THE FINGERPRINT NEVER SEES THEM. -> {its path: its bytes' sha256}"""
    seen = {}
    for code, p in _status(git, '--untracked-files=all', '--ignored'):
        if code == '!!' or _cache(p):
            full = os.path.join(tree, p)
            held = os.readlink(full).encode('utf-8', 'surrogateescape') if os.path.islink(full) else _bytes(full)
            seen[p] = hashlib.sha256(b'<unreadable>' if held is None else held).hexdigest()
    return seen


def _head(git):
    return _out(git, 'rev-parse', 'HEAD').strip()


def _sha(folder):
    """its tests' sha256: every file of the folder but the request's own side files (.day_*)"""
    h = hashlib.sha256()
    for root, dirs, files in sorted(os.walk(folder)):
        dirs[:] = sorted(d for d in dirs if d != '__pycache__')
        for f in sorted(files):
            if f.endswith('.pyc') or (root == folder and f.startswith('.day_')):
                continue
            p = os.path.join(root, f)
            h.update(os.path.relpath(p, folder).encode() + b'\0')
            with open(p, 'rb') as fh:
                h.update(fh.read())
    return h.hexdigest()


def _read(path, most=None):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read() if most is None else fh.read(most + 1)


def _bytes(path):
    try:
        with open(path, 'rb') as fh:
            return fh.read()
    except OSError:
        return None


def _last(said):
    return next((ln.strip() for ln in reversed(str(said or '').splitlines()) if ln.strip()), '')


def _run_line(tree, tests, python):
    return f'cd {tree} && {python} -m unittest discover -s {tests} -t {tests}'


def _tests_of(conf, r):
    return os.path.join(conf['tests'], r['id'])


def _side(conf, r, fresh=False, **more):
    """A REQUEST'S SIDE FILE (<its tests folder>/.day_base, JSON, outside the tree): its pick's base HEAD and that the tree was clean then,
    its built files, its proof, its commit begun. fresh: written anew (its pick); more: written into it. -> what it holds ({} when none)"""
    path = os.path.join(_tests_of(conf, r), SIDE)
    held = {}
    if not fresh:
        try:
            with open(path, encoding='utf-8') as fh:
                held = json.load(fh)
        except (OSError, ValueError):
            held = {}
        held = held if isinstance(held, dict) else {}
    if fresh or more:
        held.update(more)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + '.tmp', 'w', encoding='utf-8') as fh:
            json.dump(held, fh, sort_keys=True)
        os.replace(path + '.tmp', path)
    return held


def _built_kept(conf, r):
    """WHAT BUILD KEPT BESIDE ITS TESTS FOLDER (its base, its clean mark, its built files), for a folder gone with its side file. -> what it holds ({} when none)"""
    try:
        with open(os.path.join(conf['tests'], f"{BUILT_MARK}{r['id']}"), encoding='utf-8') as fh:
            held = json.load(fh)
    except (OSError, ValueError):
        return {}
    return held if isinstance(held, dict) else {}


def _pid_in(path):
    raw = (_bytes(path) or b'').decode(errors='replace').split()
    return int(raw[0]) if raw and raw[0].isdigit() else None


def _alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (TypeError, ValueError, ProcessLookupError):
        return False


def _moved(git, base):
    """what the tree's HEAD holds past a request's pick: [(sha, committer email, parents, subject)]; a base the tree does not hold is one"""
    if not base or git('cat-file', '-e', f'{base}^{{commit}}').returncode != 0:
        return [(str(base or '?'), '', '', 'its base is not a commit of this tree')]
    out = _out(git, 'log', '--format=%H%x00%ce%x00%P%x00%s', f'{base}..HEAD')
    return [tuple(ln.split('\0', 3)) for ln in out.splitlines() if ln.count('\0') >= 3]


def _at_base(git, base):
    """HEAD and a request's base compared, commit to commit, as Build and Review (_moved lists only what sits past the base, so a HEAD reset behind it reads as nothing moved). -> (HEAD's sha, it is the base)"""
    head = _out(git, 'rev-parse', '--verify', 'HEAD^{commit}').strip()   # a commit that did not read is never a tree at its base
    return head, head == _out(git, 'rev-parse', '--verify', f'{base}^{{commit}}').strip()


def _said_commits(moved):
    return ', '.join(f'{m[0][:12]} "{m[3][:60]}"' for m in moved[:3]) + (f' and {len(moved) - 3} more' if len(moved) > 3 else '')


def _landed(git, r, info):
    """A COMMIT THAT LANDED BEFORE ITS RUN STOPPED (a crash after git commit): the tree clean, its commit begun, and HEAD the one commit past its
    base, THE DAY's, its message starting '<id>:'. -> its sha, or ''"""
    if not info.get('base') or not info.get('committing') or _changed(git):
        return ''
    moved = _moved(git, info['base'])
    if len(moved) == 1 and moved[0][0] == _head(git) and moved[0][1] == DAY_EMAIL and moved[0][3].startswith(f"{r['id']}:"):
        return moved[0][0]
    return ''


def _proof(git, tree, base):
    """THE CHANGE'S OWN FINGERPRINT: sha256 of its diff from its base and its new files' bytes (Prove keeps it; Review and Commit find the
    same one, or stop). A read that failed raises NotMeasured: never a fingerprint of nothing; a link that points nowhere keeps its mark, its own bytes the diff's"""
    h = hashlib.sha256(_out(git, 'diff', '--binary', base, '--').encode('utf-8', 'surrogateescape'))
    for f in sorted(p for p in _out(git, 'ls-files', '--others', '--exclude-standard', '-z').split('\0') if p and not _cache(p)):
        h.update(b'\0' + f.encode('utf-8', 'surrogateescape') + b'\0')
        full, held = os.path.join(tree, f), _bytes(os.path.join(tree, f))
        if held is None and not os.path.islink(full):
            raise NotMeasured(f'not measured: its new file {f[:120]} did not read')
        h.update(held or b'<unreadable>')
    return h.hexdigest()


def put_back(git, tree, base, files):
    """A RED BEFORE THE COMMIT LEAVES NOTHING OF IT BEHIND, AND NOTHING ELSE TOUCHED: only the files changed since its pick (the tree was clean
    then, at its base), each put back to its base: one the base holds checked out from it, a new one removed; never a reset, never a path it
    was not handed. -> (the files put back, the ones that would not go back)"""
    files = sorted(set(files))
    olds = [f for f in files if _out(git, 'ls-tree', '-z', base, '--', f)]   # a read that failed is never a new file to remove
    stuck = []
    if olds and git('checkout', base, '--', *olds).returncode != 0:
        stuck += olds
    for f in files:
        if f in olds:
            continue
        if git('ls-files', '--error-unmatch', '--', f).returncode == 0:
            git('rm', '--cached', '-q', '--', f)
        p = os.path.join(tree, f)
        if os.path.lexists(p) and not os.path.isdir(p):
            try:
                os.remove(p)
            except OSError:
                stuck.append(f)
    still = set(_changed(git))
    return files, sorted(set(stuck) | (still & set(files)))


def requests(db):
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=10)
    try:
        return [dict(zip(('id', 'words', 'state', 'position', 'tests', 'tests_sha', 'commits', 'why', 'done_at', 'state_at', 'source', 'asked_at'), r))
                for r in con.execute('SELECT id, words, state, position, tests, tests_sha, commits, why, done_at, state_at, source, asked_at FROM requests ORDER BY position, id')]
    finally:
        con.close()


def set_state(db, rid, state, why='', when=None, **more):
    """a request's state written; when: the state it must be in now (a press between the read and the write wins). -> True when written"""
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            cols = {'state': state, 'state_at': _stamp(), 'why': why, **more}
            q = f"UPDATE requests SET {', '.join(f'{k} = ?' for k in cols)} WHERE id = ?" + (' AND state = ?' if when else '')
            return con.execute(q, (*cols.values(), rid, *((when,) if when else ()))).rowcount == 1
    finally:
        con.close()


def at(db, *states):
    return [r for r in requests(db) if r['state'] in states]


def said_words(r):
    return f"{r['id']} · {' '.join(str(r['words'] or '').split())[:160]}"


class Beat:
    """A LONG STEP'S HEARTBEAT: its job's RUN written RUNNING again every BEAT seconds, so THE RED never takes a working run for a stuck one;
    joined on its way out, so no late beat ever writes RUNNING after the run's own end."""
    def __init__(self, store, job_key):
        self.store, self.job_key, self.stop, self.thread = store, job_key, threading.Event(), None

    def __enter__(self):
        def beat():
            while not self.stop.wait(BEAT):
                try:
                    self.store._edit(self.job_key, {'run_state': 'RUNNING'}, run=True)
                except Exception:   # noqa: BLE001  (a missed beat is one minute; the run goes on)
                    pass
        if self.job_key and hasattr(self.store, '_edit'):
            self.thread = threading.Thread(target=beat, daemon=True)
            self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        if self.thread:
            self.thread.join()


class Writer:
    """THE HOT FIX TREE'S ONE WRITER MARK (the utility's writer_waits reads it: while its pid lives the utility starts nothing): our pid written
    while a step touches the tree, let go on its way out; refused while the utility runs (its running.lock's pid alive) or another live pid
    holds the mark. The utility writes its own lock first, then reads the mark: so the mark is written first here, then its lock read again."""
    depth = 0   # how many marks this process holds now: a nested take within one step's own mark keeps it

    def __init__(self, conf):
        self.mark, self.utility, self.held, self.why = conf['writer'], conf['utility_lock'], False, ''

    def _busy(self):
        pid = _pid_in(self.utility)
        return f'the hot fix utility is running (pid {pid}): it writes the tree now' if pid and _alive(pid) else ''

    def __enter__(self):
        other = _pid_in(self.mark)
        self.why = self._busy() or (f'another writer of the hot fix tree holds its mark (pid {other}, {self.mark})' if other and other != os.getpid() and _alive(other) else '')
        if self.why:
            return self
        if Writer.depth and other == os.getpid():   # HELD ALREADY BY THIS RUN (its step took the mark first): kept, let go by its first holder alone
            return self
        os.makedirs(os.path.dirname(self.mark), exist_ok=True)
        with open(self.mark, 'w', encoding='utf-8') as fh:
            fh.write(str(os.getpid()))
        self.held = True
        Writer.depth += 1
        self.why = self._busy()
        if self.why:
            Writer.depth -= 1
            self._let_go()
        return self

    def _let_go(self):
        if self.held and _pid_in(self.mark) == os.getpid():
            try:
                os.remove(self.mark)
            except OSError:
                pass
        self.held = False

    def __exit__(self, *exc):
        if self.held:
            Writer.depth -= 1
        self._let_go()


def _lock_path(conf):
    return os.path.join(conf['tests'], '.day.lock')


def _day_lock(conf):
    """THE DAY'S ONE LOCK (two presses never overlap): an fcntl.flock on one file beside the requests' tests, taken without waiting and held
    by the run that drives the day, from its first step to its last. -> its open file, or None when another run holds it"""
    os.makedirs(conf['tests'], exist_ok=True)
    fh = open(_lock_path(conf), 'a+', encoding='utf-8')   # a lock that will not open is its crash, never said as held (run())
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except BlockingIOError:   # only this is another run holding it
        fh.close()
        return None
    except OSError:
        fh.close()
        raise


def _hire():
    from frame import frame_red   # the frame's own hire: one session, its words on stdin, its clock, stopped by its own pid
    if 'started' in inspect.signature(frame_red.hire).parameters:
        return lambda command, words, cwd, seconds, started=None: frame_red.hire(command, words, cwd, seconds, started=started)
    return lambda command, words, cwd, seconds: frame_red.hire(command, words, cwd, seconds)


def _hired_by(hire, conf, r, command, words, cwd, seconds):
    """ONE HIRE FOR A REQUEST, its pid kept beside its tests (.day_hire) while it works, so a hire a stopped page left is found by its pid"""
    mark = os.path.join(_tests_of(conf, r), HIRE_MARK)

    def started(pid):
        os.makedirs(os.path.dirname(mark), exist_ok=True)
        with open(mark, 'w', encoding='utf-8') as fh:
            fh.write(f'{pid} {_stamp()}')
    try:
        takes = 'started' in inspect.signature(hire).parameters
    except (TypeError, ValueError):
        takes = False
    try:
        return hire(command, words, cwd, seconds, started=started) if takes else hire(command, words, cwd, seconds)
    finally:
        try:
            os.remove(mark)
        except OSError:
            pass


def _ran(store, job_key, n, started, code, said, state):
    """A RUN'S END WRITTEN, again a moment later while LARRYD says 'database is locked' (a busy store is not a lost run)"""
    for attempt in range(6):
        try:
            return store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code, said, state)
        except sqlite3.OperationalError as busy:
            if 'locked' not in str(busy) or attempt == 5:
                raise
            time.sleep(0.5 * (attempt + 1))


def _close(store, job_key, n, why):
    """A RUN TAKEN AND NEVER RUN, closed FAILED with its line (never left QUEUED)"""
    said = {'summary': f'FAILED · {why} · {HAND}RUN AGENT here', 'ok': False, 'lines': [], 'why': why, 'step': 'RUN AGENT here', 'next': None}
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        _ran(store, job_key, n, now, 1, json.dumps(said), 'FAILED')
    except Exception:   # noqa: BLE001  (its block then says its RUN open: THE RED's)
        pass


def hand_on(store, chain, key):
    """THE NEXT STEP'S RUN, TAKEN NOW as the Run button takes it (the chain the page hands every run: never an import of another agent), before
    this step writes its own end. -> ((its module, its shell, its run), ''), (None, why it was not taken), or (None, '') when the board says its block is switched off (off is never a red)"""
    nxt = next(((m, sh) for m, sh in (chain or ()) if getattr(m, 'KEY', '') == key), None)
    if nxt is None:
        return None, f'it is not in the chain this run was handed ({key})'
    if not hasattr(store, 'run'):
        return None, 'this store takes no RUN'
    module, sh = nxt
    try:
        job = next((x['job'] for x in store.board() if x['id'] == sh['id']), None) or {}
        ok, text = store.run(sh['id'])
        off = not ok and any(x['id'] == sh['id'] and not x.get('on', True) for x in store.board())   # read after the refusal: a block switched off a moment before it is off too
    except Exception as fault:   # noqa: BLE001
        return None, f'its RUN was not taken ({_line(fault)})'
    if off:
        return None, ''
    if not ok:
        return None, f'its RUN was refused ({text})'
    m = re.search(r'RUN (\d+)', str(text))
    n = int(m.group(1)) if m else int(job.get('data_job_run') or 0) + 1
    return (module, sh, n), ''


def _crashed(fault):
    """ITS OWN CODE CRASHED: red, named as a crash, its file and line its step (its blind rule read 2026-10-28; as agent011)"""
    where = _where(fault)
    return {'ok': False, 'lines': [], 'why': f'it crashed at {where} ({_line(fault)})', 'step': f'open app/agent/{where}, fix what the crash names, then RUN AGENT', 'next': None}


def _hung(tree, fault):
    """A GIT THAT DID NOT END: stopped at GIT_SECONDS, its heartbeat, the writer mark and the day's lock let go on the way out; said not measured, with what clears it"""
    lock = f'"$(git -C {tree} rev-parse --git-path index.lock)"'
    return _no([], f'not measured: a git call hung and was stopped at {_where(fault)} ({_line(fault)})',
               f"ps -axo pid,etime,command | grep '[g]it ' names any git left running: let it end; with none left, rm -f {lock}, and when git -C {tree} status --porcelain answers at once, RUN AGENT")


def _handed_back(name):
    """HIS TWO PRESSES WHEN THE NEXT STEP'S RUN WAS NOT TAKEN: here first, for its request stands proven and nothing is built, so this run ends green and
    hands nothing on; the next step alone never clears this red, for past it Pick hands on to the walk or the cleanup and Prove never runs again"""
    return (f'RUN AGENT here, seconds of your hand: its request is proven and nothing is built now, so {NAME} ends green in seconds and hands nothing on, no test run, which ends this red; '
            f'then clear what the refusal names (an open run let end, its agent added) and RUN AGENT on {name}: it takes its own RUN and runs the day on by itself')


def once(store, job_key, n, agent, chain, conf, runner, hire, db, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step); green, the next step's RUN taken first: a next refused or
    missing ends this one FAILED, said; a next switched off is off, never a red: this one ends DONE, hands nothing on, and its request stands proven. A crash ends FAILED with its line. -> (what it said, the next to run (module, shell, run) or None)"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not locked:
        got = _no([], 'another DAY step is running', f'lsof {_lock_path(conf)} names the run that holds the lock: let it end (its block says RUNNING), then RUN AGENT')
    else:
        try:
            with Beat(store, job_key):
                got = step(store, conf, runner, db, hire)
        except NotMeasured as fault:   # NOT MEASURED SAID FIRST, its file and line beside it: the tree's fault, no code to edit (its blind rule read 2026-10-31)
            got = _no([], f'{fault} at {_where(fault)}', f"git -C {conf['tree']} status --porcelain prints the error it met; when it still fails, {_tree_step(conf['tree'])}, then RUN AGENT here")
        except subprocess.TimeoutExpired as fault:   # A HUNG GIT ENDS THE RUN RED, with what clears it: never RUNNING forever under its own heartbeat
            got = _hung(conf['tree'], fault)
        except Exception as fault:   # A CRASH IS RED, NAMED WHERE IT HAPPENED: the traceback's last frame, its file and line (its blind rule read 2026-10-28; as agent011)
            gone = isinstance(fault, (FileNotFoundError, NotADirectoryError)) and not os.path.isdir(conf['tree'])   # the tree went while the step worked: git or a test could not start in it
            got = _no([], f"not measured: there is no hot fix tree at {conf['tree']} ({_line(fault)}) at {_where(fault)}", f"{_tree_step(conf['tree'])}, then RUN AGENT here") if gone else _crashed(fault)
    nxt = None
    if got['ok'] and got.get('next'):
        nxt, why = hand_on(store, chain, got['next'])
        name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or got['next']
        if nxt is None and why:
            got = {**got, 'ok': False, 'why': f'the day stopped before {name}: {why}', 'step': _handed_back(name), 'next': None}
        elif nxt is None:   # OFF IS NEVER A RED: the day rests here by his switch, the proof kept, nothing handed on
            got = {**got, 'lines': got['lines'] + [f'{name} is switched off, its RUN not taken: the request stands proven; when you turn it on, RUN AGENT on {name}'], 'next': None}
    try:   # THE ORIGINAL'S RUN LINE: its list of the requests at its stage, read after the step (report)
        listed = report(db, conf)
    except Exception as fault:   # noqa: BLE001  (a list that does not read is said, the run's own end still written)
        listed = f'its list did not read ({_line(fault)})'
    done = ' | '.join(got['lines'][-3:])
    summary = (f"DONE · {done + ' · ' if done else ''}{listed}" if got['ok'] else f"FAILED · {got['why']} · {done + ' · ' if done else ''}{HAND}{got['step']}")   # a red: why first, his one step last (the original's)
    said = {'summary': summary, 'list': listed, **got}
    try:
        _ran(store, job_key, n, started, 0 if got['ok'] else 1, json.dumps(said), 'DONE' if got['ok'] else 'FAILED')
    except Exception as fault:   # noqa: BLE001  (its own end not written: the next one taken is closed, the day stops)
        if nxt:
            _close(store, nxt[1]['job_key'], nxt[2], f'the day stopped: {NAME} could not write its run ({_line(fault)})')
        return said, None
    return said, nxt


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None, conf=None, runner=subprocess.run, hire=None, db=None):
    """ONE RUN OF THE DAY FROM THIS STEP (RUN AGENT): the day's lock taken, this step, then every next one in a loop (never a recursion: a
    hundred requests are five hundred steps), each its own run written; a next that breaks is closed FAILED with its line. A crash before its
    step (the day's lock not opening, the frame's hire not loading) is its own crash: its run written FAILED here, its file and line its step."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conf = {**CONF, **(conf or {})}
        hire = hire or ((lambda c, w, cwd, s: hire_with(c, w, cwd, s)) if hire_with else _hire())
        db = db or store.db_path
        lock = _day_lock(conf)
    except Exception as fault:
        got = _crashed(fault)
        said = {'summary': f"FAILED · {got['why']} · {HAND}{got['step']}", **got}
        _ran(store, job_key, n, started, 1, json.dumps(said), 'FAILED')
        return said
    try:
        said, nxt = once(store, job_key, n, agent, chain, conf, runner, hire, db, lock is not None)
        while nxt:
            module, sh, m = nxt
            try:
                _s, nxt = module.once(store, sh['job_key'], m, agent, chain, conf, runner, hire, db, True)
            except Exception as fault:   # noqa: BLE001  (its RUN was taken: closed FAILED, never left QUEUED)
                _close(store, sh['job_key'], m, f'it broke before its run was written ({_line(fault)})')
                nxt = None
    finally:
        if lock is not None:
            lock.close()
    return said


def latest(store, job_key):
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except (TypeError, ValueError):
            return None
    return None


def until_next(now=None, schedule=None):
    """ON RUN AGENT ONLY: never due by itself (a year, so the page's timer never fires)"""
    return 365 * 86400


def clock(schedule=None):
    """Its clock in its shell: ON RUN AGENT."""
    schedule = schedule or SCHEDULE
    return {'zone': schedule['location'], 'at': '', 'said': 'ON RUN AGENT', 'when': 'ON RUN AGENT', 'repeat': 'MANUAL', 'hour_deg': 0, 'minute_deg': 0}


def _aware(stamp):
    """a stamp with its zone: a run's naive time (datetime.now()) taken as this machine's own, a request's kept as written. -> iso, or ''"""
    try:
        at_ = datetime.datetime.fromisoformat(str(stamp))
    except (TypeError, ValueError):
        return ''
    return (at_ if at_.tzinfo else at_.astimezone()).isoformat(timespec='seconds')


def _when(stamp, form='%b %d %H:%M'):
    """a stamp said in his zone (Oct 28 10:15), '' when none"""
    a = _aware(stamp)
    return datetime.datetime.fromisoformat(a).astimezone(zoneinfo.ZoneInfo(SCHEDULE['timezone'])).strftime(form) if a else ''


def _cut(text, most=240):
    t = ' '.join(str(text or '').split())
    return t if len(t) <= most else t[:most - 1] + '…'


def _listed(items, most=10):
    return '; '.join(items[:most]) + (f'; and {len(items) - most} more' if len(items) > most else '')


def _last_work(db):
    """THE LAST WORK (the original's 'the last work: ... at ...'): the request whose state moved last, past the backlog. -> words, or ''"""
    moved = sorted((r for r in requests(db) if r['state'] not in (WAITING, 'removed') and _aware(r.get('state_at'))), key=lambda r: _aware(r['state_at']))
    return f"{moved[-1]['id']} {moved[-1]['state']} at {_when(moved[-1]['state_at'])}" if moved else ''


def _red_part(store, job_key):
    """WHY IT'S RED, THE ORIGINAL'S WARNING ROW (scrum.html data-warning, data-terminal-line): while its newest run is red, how long it has been
    red (the first red run of the streak, ticking), when it came in, 'Warning · why · YOUR 3 MIN: the line under this row', and his one step
    on the copy line under it. -> a table part, or None (its newest run green, or no run yet)"""
    streak = []
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True):
        if r['exit'] == 0:
            break
        streak.append(r)
    if not streak:
        return None
    try:
        said = json.loads(streak[0]['said'])
    except (TypeError, ValueError):
        said = {}
    said = said if isinstance(said, dict) else {}
    since = _aware(streak[-1]['started_at'])
    why = said.get('why') or _cut(streak[0]['said'], 300) or 'its run ended red'
    step = said.get('step') or 'see its last run under Rules and Skills, then RUN AGENT here'
    return {'kind': 'table', 'title': "Why it's red", 'under': f"{len(streak)} red run{'' if len(streak) == 1 else 's'} in a row, the newest at {_when(streak[0]['started_at'])}",
            'columns': ['Red since', 'Came in', 'Warning'],
            'rows': [{'key': 'red', 'cells': [{'text': f"Red since {_when(since, '%H:%M')}: how long this row has been red", 'since': since},
                                              f"Came in {_when(since, '%Y-%m-%d %H:%M')}", f'Warning · {why} · {HAND}the line under this row'],
                      'copy': f'{HAND}{step}'}], 'empty': ''}


def _aside_part(db, conf):
    """THE REQUESTS THIS STEP SET ASIDE, STILL STUCK TODAY (the original's red list of the requests sent back to the builder): each with his
    words, why, when, his one line to try it again on the copy line, and its BACK TO ASKED press that does that line."""
    rows = []
    for r in at(db, STUCK):
        a = _side(conf, r).get('aside') or {}
        if a.get('step') != KEY:
            continue
        rows.append({'key': r['id'], 'cells': [r['id'], _cut(r['words']), _cut(a.get('why') or r['why'], 300), _when(a.get('at') or r.get('state_at'))],
                     'copy': f"{HAND}{_again(CONF, db, r)}, then RUN AGENT on Pick",
                     'presses': [{'do': 'back', 'label': 'Back to asked', 'confirm': f"Send {r['id']} back to asked? Pick takes it again in its build order and its tests are written anew from his words."}]})
    return {'kind': 'table', 'title': ASIDE_TITLE, 'under': (f"{len(rows)} stuck today: each one's change was put back; BACK TO ASKED sends it back to the backlog" if rows else 'none stuck today'),
            'columns': ['Request', 'His words', 'Why', 'Set aside', 'Your press'], 'rows': rows, 'empty': ASIDE_EMPTY}


def press(store, job_key, do, fields=None):
    """ITS BUTTON ON A REQUEST IT SET ASIDE: 'back', his hand line pressed: the request stuck today by this step set back to asked (Pick takes it
    again in its build order; its tests unfrozen, as that line does, so Build writes them anew). Any other request, or one moved since, changes nothing, said.
    -> the words said on its shell"""
    if do not in PRESSES:
        raise ValueError(f'not one of its presses: {do!r}')
    db, rid = store.db_path, str((fields or {}).get('value') or '').strip()
    r = next((x for x in requests(db) if x['id'] == rid), None)
    if r is None:
        return f"BACK TO ASKED · no request {rid or 'named'}: nothing changed"
    if r['state'] != STUCK or (_side(CONF, r).get('aside') or {}).get('step') != KEY:
        return f'BACK TO ASKED · {rid} is {r["state"]}, not set aside by {NAME}: nothing changed'
    if not set_state(db, rid, WAITING, f'sent back to asked by the owner ({NAME} had set it aside)', when=STUCK, tests_sha=None):
        return f'BACK TO ASKED · {rid} moved before the write: nothing changed'
    return f'BACK TO ASKED · {rid} is asked again: Pick takes it in its build order'


def _ok(lines, nxt=NEXT):
    return {'ok': True, 'lines': lines, 'why': '', 'step': '', 'next': nxt}


BRANCH = 'hold/20261021'   # the hot fix tree's branch, named in the steps that stand it up again


def _rebuilt(tree):
    """HIS ONE COMMAND THAT STANDS THE TREE UP AGAIN"""
    return f'git -C {HOME}/virtual_workspace worktree prune && git -C {HOME}/virtual_workspace worktree add {tree} {BRANCH}'


def _stood_up(tree):
    """HIS ONE COMMAND WHEN SOMETHING SITS AT THE TREE'S PATH THAT IS NO WORKING TREE: moved aside whole, never deleted (a worktree add stops on 'already exists'), then the tree stood up again"""
    return f'mv {tree} {tree}.broken-$(date +%Y%m%d%H%M%S) && {_rebuilt(tree)}'


def _tree_step(tree):
    """HIS ONE COMMAND FOR A TREE THAT DOES NOT READ: nothing at its path, stood up; something there, moved aside first"""
    return f'{_stood_up(tree)} (moved aside, never lost)' if os.path.lexists(tree) else _rebuilt(tree)


def _undone(tree, db, rid, base):
    """HIS ONE COMMAND WHEN A COMMIT SITS PAST A REQUEST'S BASE: reverted, the request asked again with its tests unfrozen; its new pick records the new base"""
    return f"[ -z \"$(git -C {tree} rev-list {base[:12]}..HEAD)\" ] || git -C {tree} revert --no-edit {base[:12]}..HEAD; sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


def _brought_up(tree, db, rid, base):
    """HIS ONE COMMAND WHEN HEAD SITS BEHIND A REQUEST'S BASE: what the tree holds stashed, never lost (its build stood on the base, never on this older code, and a tree that holds it stops a fast-forward), its branch brought
    forward to the base (never a reset), the request asked again with its tests unfrozen; its new pick records the base"""
    return f"git -C {tree} stash push -u -m day-{rid} && git -C {tree} merge --ff-only {base} && {_asked(db, rid)}"


def _kept_aside(tree, db, rid):
    """HIS ONE COMMAND WHEN THE TREE HOLDS WHAT A REQUEST CANNOT CLAIM: stashed, never lost (it may be his own edit), the request asked again"""
    return f"git -C {tree} stash push -u -m day-{rid} && sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


def _no(lines, why, step):
    return {'ok': False, 'lines': lines, 'why': why, 'step': step, 'next': None}


def _unready(git, tree):
    """THE HOT FIX TREE THERE, ON ITS BRANCH AND CLEAN (nobody's half done work is ever committed or put back for them). -> a red, or None"""
    if not os.path.isdir(tree) or git('rev-parse', '--verify', '-q', 'HEAD^{commit}').returncode != 0:
        return _no([], f'there is no hot fix tree at {tree}', f'{_rebuilt(tree)}, then RUN AGENT')
    if git('symbolic-ref', '-q', 'HEAD').returncode != 0:
        return _no([], 'the hot fix tree is on no branch (a detached HEAD)', f'git -C {tree} checkout {BRANCH}, then RUN AGENT')
    dirty = _changed(git)
    if dirty:
        return _no([], f"the hot fix tree holds {len(dirty)} file(s) nobody committed: {', '.join(dirty[:4])}", f'git -C {tree} stash push -u -m day-left (kept in the stash, never lost), then RUN AGENT')
    return None


def _asked(db, rid, state=WAITING):
    """HIS ONE LINE that sets a request's state by hand (back to asked: Pick takes it again in its build order)"""
    return f"sqlite3 {db} \"UPDATE requests SET state='{state}'{', tests_sha=NULL' if state == WAITING else ''} WHERE id='{rid}'\""


def _has_tests(tests):
    return os.path.isdir(tests) and any(not f.startswith('.day_') for f in os.listdir(tests))


def _frozen_again(conf, db, rid):
    """HIS ONE LINE THAT KEEPS ITS TESTS AS THEY STAND NOW: Build reuses a folder only at its kept sha and clears it when that sha is NULL, so a hand mend lives only by freezing its new bytes; this program prints their sha, and no sha sets nothing"""
    return f"S=$({conf['python']} {os.path.abspath(__file__)} {os.path.join(conf['tests'], rid)}) && sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha='$S' WHERE id='{rid}'\""


def _again(conf, db, r):
    """HIS ONE LINE THAT SETS IT BACK, the one that fits what he fixed, each saying what Build then does: no tests left in its folder, the one line there is"""
    rid, tests = r['id'], _tests_of(conf, r)
    anew = f"{_asked(db, rid)} (Build clears {tests} and writes its tests anew from his words)"
    if not _has_tests(tests):
        return anew
    return (f"when its tests are sound or you mended them in {tests}: {_frozen_again(conf, db, rid)} (they stay as they stand now and its developer alone runs again); "
            f"when a test asks what his words never asked, or you changed his words by UPDATE: {anew}")


def _since_pick(git, tree, r, info, lines, built, db=''):
    """WHAT A STEP ON A PICKED REQUEST STANDS ON: its base recorded at its pick on a clean tree, HEAD still at that base (a commit past it, or
    a HEAD gone back behind it, is never built on), and the tree's change exactly its own recorded files (built), or none (not built yet). -> a red, or None"""
    base = info.get('base')
    if not base or not info.get('clean'):
        return _no(lines, f"{r['id']}: its pick recorded no base", 'RUN AGENT on Building now (it goes back to the backlog), then the day picks it again')
    dirty = set(_changed(git))   # first: a tree that does not read is not measured, never a tree that moved
    moved = _moved(git, base)
    if moved:
        return _no(lines, f"{r['id']}: the tree moved past its pick ({_said_commits(moved)}): never built on, never reviewed",
                   f"{_undone(tree, db, r['id'], base)}, then RUN AGENT on Pick")
    head, there = _at_base(git, base)
    if not there:   # nothing past its base and not at it: HEAD went back behind it, on older code than its pick
        return _no(lines, f"{r['id']}: the tree went back behind its pick (HEAD {head[:12]}, its base {base[:12]}): never proven on older code",
                   f"{_brought_up(tree, db, r['id'], base)}, then RUN AGENT on Pick")
    mine = set(info.get('files') or ()) if built else set()
    if built and not mine:
        return _no(lines, f"{r['id']}: its built files were never recorded", f"{_kept_aside(tree, db, r['id'])}, then RUN AGENT on Pick")
    if dirty != mine:
        odd = sorted(dirty ^ mine)
        if dirty - mine:
            return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) changed besides it: {', '.join(odd[:4])})",
                       f'see `git -C {tree} status`: they may be his own hand edits, never put back here; clear them by hand, then RUN AGENT here')
        return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) of it gone: {', '.join(odd[:4])})",
                   f"set {r['id']} back to asked ({_asked(db, r['id'])}), clear the rest of its change by hand (git -C {tree} status), then RUN AGENT on Pick")
    return None


def _goes_on(db):
    """HIS LAST PRESS WHEN A PRESS MOVED THE REQUEST DURING THE RUN (a test run that failed or one that passed, its change put back either way), read now: with a request asked, Pick, so Build and Prove run again; with none, Pick would hand on to the walk or the cleanup and Prove would stay red, so here, seconds"""
    if at(db, WAITING):
        return 'RUN AGENT on Pick: the day goes on with the next request'
    return 'RUN AGENT here: nothing is asked or building, it ends green in seconds and hands nothing on'


def _set_aside(db, git, tree, base, r, files, why, step, lines, conf=None):
    """A RED OF PROVE: its change put back (its own files alone), it stuck today, the day stops here, unless a press moved it during the run: then this red
    is no set-aside: its state stays as he set it, never stuck, so it has no row in Not proven: set aside, BACK TO ASKED refuses it, no line sets it back, and his
    last step is _goes_on's. On every other red his one step is the same: what the red names fixed (a file that would not go back cleared by hand first), its one line that sets it back to asked, then RUN AGENT on Pick: never
    Pick alone, for with nothing asked Pick hands on to the walk or the cleanup, Prove never runs and this red stays; set back, a request is always
    there to pick, so Build and Prove run and end this red, even on the last request. conf: the step that set it aside, why and when, kept in its
    side file (its block lists it with its BACK TO ASKED press)."""
    conf = conf or CONF
    back, kept = put_back(git, tree, base, files)
    if not set_state(db, r['id'], STUCK, why[:300], when=r['state']):   # A PRESS DURING THE RUN WINS (its blind rule reads 2026-10-28): its change put back, its state left as he set it, never stuck, not set aside: no aside kept, so no row and no BACK TO ASKED
        lines.append(f"{r['id']}: a press moved it during the run: its state is left as he set it")
        lines.append(f"{r['id']}: its {len(back)} changed file(s) put back" + (f", {len(kept)} would not go back: {', '.join(kept[:4])}" if kept else ''))
        first = f"clear {', '.join(kept[:4])} by hand (git -C {tree} status), then " if kept else ''
        return _no(lines, f"{r['id']}: {why}; not set aside, a press moved it", f"{step}; {first}{_goes_on(db)}")
    _side(conf, r, aside={'step': KEY, 'why': why[:300], 'at': _stamp()})
    lines.append(f"{r['id']} set aside: stuck today, its {len(back)} changed file(s) put back" + (f", {len(kept)} would not go back: {', '.join(kept[:4])}" if kept else ''))
    first = f"clear {', '.join(kept[:4])} by hand (git -C {tree} status), then " if kept else ''
    took = (conf['write_seconds'] + conf['prove_seconds'] + conf['build_seconds']) // 60
    return _no(lines, f"{r['id']}: {why}", f"{step}; {first}{_again(conf, db, r)}; then RUN AGENT on Pick, seconds of your hand: {r['id']} is asked again, so Pick always has a request and Build and Prove "
               f"run and end this red, even when it is the last; that press runs the whole day from Pick by itself (Build alone up to {took} minutes), each later red says its own line")


def _on(git):
    """the branch HEAD is on, '' on a detached HEAD (symbolic-ref's own exit 1: an answer, any other a read that failed)"""
    return _out(git, 'symbolic-ref', '-q', 'HEAD', codes=(0, 1)).strip()


def _elsewhere(git):
    """THE BRANCHES ANOTHER WORKTREE HAS CHECKED OUT (the repo's refs are shared: another session's merge there moves them while its tests run
    here, never its tests' move, as main). -> their refs, this tree's own branch never one"""
    held = {ln[len('branch '):] for ln in _out(git, 'worktree', 'list', '--porcelain').splitlines() if ln.startswith('branch ')}
    return held - {_on(git)}


def _snap(git, tree, tests, base):
    """ALL ITS TESTS COULD CHANGE, before and after they run: the change's fingerprint and files, every local ref, HEAD, the ignored and cache
    files, the tests' folder and the request's side file"""
    refs = _out(git, 'for-each-ref', '--format=%(refname) %(objectname)').splitlines()
    return {'proof': _proof(git, tree, base), 'changed': set(_changed(git)), 'refs': {ln.split(' ', 1)[0]: ln.split(' ', 1)[1] for ln in refs if ' ' in ln and not ln.startswith(('refs/remotes/', 'refs/heads/main '))},
            'elsewhere': _elsewhere(git), 'head': _head(git), 'sym': _on(git), 'kept': _watched(git, tree),
            'tests': _sha(tests), 'side': _bytes(os.path.join(tests, SIDE))}


def _during(git, tree, tests, base, before):
    """WHAT ITS TESTS CHANGED WHILE THEY RAN, seen after they end (any end). -> (why, the new ignored or cache files, the ones changed or gone), '' when nothing"""
    after, said = _snap(git, tree, tests, base), []
    if after['proof'] != before['proof'] or after['changed'] != before['changed']:
        odd = sorted(after['changed'] ^ before['changed'])
        said.append('its fingerprint or changed files differ' + (f": {', '.join(odd[:4])}" if odd else ''))
    theirs = before['elsewhere'] | after['elsewhere']
    moved = sorted(ref for ref in set(before['refs']) | set(after['refs']) if ref not in theirs and before['refs'].get(ref) != after['refs'].get(ref))
    if after['head'] != before['head'] or after['sym'] != before['sym'] or moved:
        named = [f"HEAD {before['head'][:12]} became {after['head'][:12]}"] if after['head'] != before['head'] else []
        named += [f"{ref} {str(before['refs'].get(ref) or 'none')[:12]} became {str(after['refs'].get(ref) or 'none')[:12]}" for ref in moved if not (ref == after['sym'] and named)]
        top = _out(git, 'log', '-1', '--format=%h "%s"', after['head']).strip() if after['head'] != before['head'] else ''
        said.append(f"the tree's git moved ({'; '.join(named[:3]) or 'its branch changed'}" + (f'; its commit {top}' if top else '') + ')')
    new = sorted(set(after['kept']) - set(before['kept']))
    odd = sorted(p for p in before['kept'] if after['kept'].get(p) != before['kept'][p])
    if new:
        said.append(f"new ignored or cache file(s): {', '.join(new[:4])}")
    if odd:
        said.append(f"ignored or cache file(s) changed or gone: {', '.join(odd[:4])}")
    if after['tests'] != before['tests']:
        said.append('its tests\' folder changed')
    if after['side'] != before['side']:
        said.append('its side file (its base and proof) changed')
    return '; '.join(said), new, odd


def _failed_tests(out):
    """each failing test named by unittest: its lines starting FAIL: or ERROR:, each cut to 200 characters"""
    return [ln.strip()[:200] for ln in str(out or '').splitlines() if ln.startswith(('FAIL:', 'ERROR:'))]


def _tests_run(conf, tree, tests, runner):
    """its tests run as the workers were told. -> (code, its output, tests ran, skipped) or raises subprocess.TimeoutExpired"""
    proved = runner([conf['python'], '-m', 'unittest', 'discover', '-s', tests, '-t', tests], cwd=tree, capture_output=True, text=True,
                    timeout=conf['prove_seconds'], env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'TREE_DIR': tree})
    out = (proved.stdout or '') + (proved.stderr or '')
    ran = re.search(r'^Ran (\d+) tests?', out, re.M)
    return proved.returncode, out, int(ran.group(1)) if ran else 0, bool(re.search(r'skipped=\d+|expected failures=\d+', out))


def _one(db, state, lines, name):
    """the one request at a stage (one at a time on the tree). -> (request or None, red or None)"""
    rows = at(db, state)
    if not rows:
        return None, _ok(lines + [f'nothing {state}: nothing for {name} to do'], None)
    if len(rows) > 1:
        return None, _no(lines, f"{len(rows)} requests are {state} at once: {', '.join(r['id'] for r in rows[:4])}", f"sqlite3 {db} \"UPDATE requests SET state='asked' WHERE state='{state}' AND id<>'{rows[0]['id']}'\", then RUN AGENT")
    return rows[0], None

def _wait(why):
    """HIS STEP WHILE THE TREE IS ANOTHER'S: its pid is in its why, its mark no open file, so ps names it where lsof on the day's lock would not"""
    pid = re.search(r'pid (\d+)', why).group(1)
    return f'ps -p {pid} -o command= names that run: let it end, then RUN AGENT here'


def step(store, conf, runner, db, hire):
    """THE TREE'S WRITER MARK FIRST, every check under it (its blind rule read 2026-10-28, as Main first and Cleanup): a running hot fix
    utility or another writer is said as itself, never as files nobody committed or a tree that moved"""
    with Writer(conf) as w:
        if w.why:
            return _no([], w.why, _wait(w.why))
        return _step(store, conf, runner, db, hire)


def _step(store, conf, runner, db, hire):
    lines = []
    r, red = _one(db, BUILT, lines, 'Prove')
    if red or r is None:
        return red
    tree, tests = conf['tree'], _tests_of(conf, r)
    if not os.path.isdir(tree):   # FIRST: no step below it can run, each stands on git in that tree; stood up, its next run says what is left of the change
        return _no(lines, f'not measured: there is no hot fix tree at {tree}', f'{_tree_step(tree)}, then RUN AGENT here')
    git = _git(tree, runner)
    gone = not os.path.isdir(tests)   # ITS SIDE FILE LIVES IN THAT FOLDER: gone with it, its base and files are read from what Build kept beside it
    info = _built_kept(conf, r) if gone else _side(conf, r)
    if gone and not info.get('base'):   # NOTHING SAYS WHAT IS ITS OWN: its files never guessed at, nothing removed
        return _no(lines, f"{r['id']}: its tests folder ({tests}) is gone and no base or built files of it are kept: nothing set aside, nothing put back", f"{_kept_aside(tree, db, r['id'])}, then RUN AGENT on Pick")
    red = _since_pick(git, tree, r, info, lines, built=True, db=db)
    if red:
        return red
    base, mine = info['base'], info['files']
    with Writer(conf) as w:
        if w.why:
            return _no(lines, f"{r['id']}: {w.why}", _wait(w.why))

        def aside(why, step_, seen=('', (), ())):
            """ITS OWN FILES PUT BACK, AND ANY ITS TESTS LEFT (a new ignored file a new one, removed); a commit that landed goes back by his revert line, its files left to that line; an ignored file they changed has no copy here"""
            bad, new, odd = seen
            moved = _moved(git, base)
            committed = set(_out(git, 'diff', '--name-only', '-z', base, 'HEAD').split('\0')) if moved else set()
            if moved:
                step_ = f"{_undone(tree, db, r['id'], base)} (a commit past its base goes back by this line); {step_}"
            elif not _at_base(git, base)[1]:
                step_ = f"{_brought_up(tree, db, r['id'], base)} (a HEAD gone back behind its base comes forward by this line); {step_}"
            if odd:
                step_ = f"{step_}; no copy of the ignored or cache file(s) it changed is kept: see `git -C {tree} status --ignored` and put them back by hand"
            return _set_aside(db, git, tree, base, r, sorted((set(mine) | set(_changed(git)) | set(new)) - committed), f'{why}; {bad}' if bad else why, step_, lines, conf)
        if gone:
            return aside(f'its tests folder is gone ({tests})', 'its tests are written anew when it is tried again')
        if _sha(tests) != r.get('tests_sha'):
            return aside('its tests are not the ones frozen', f"its tests ({tests}) differ from their sha {str(r.get('tests_sha') or 'none')[:12]} and no copy of them is kept")
        before = _snap(git, tree, tests, base)
        proof = before['proof']
        try:
            took = time.monotonic()
            code, out, ran, skipped = _tests_run(conf, tree, tests, runner)
        except subprocess.TimeoutExpired as late:   # WHAT IT SAID BEFORE IT WAS STOPPED, kept (its blind rule read 2026-10-28): its last 5 lines
            said_ = [ln.strip()[:200] for s in (late.stdout, late.stderr) for ln in (s.decode('utf-8', 'replace') if isinstance(s, bytes) else str(s or '')).splitlines() if ln.strip()][-5:]
            lines.extend(f"6 prove · {r['id']} · before it was stopped: {ln}" for ln in said_)
            return aside(f"its tests did not end in time (stopped at {conf['prove_seconds']} s)" + (f"; its last output: {' | '.join(said_)}" if said_ else '; no output before it was stopped'), 'its change is put back', _during(git, tree, tests, base, before))
        secs = round(time.monotonic() - took)
        lines.append(f"6 prove · {r['id']} · its tests ran in {secs} s: exit {code}, {ran} test(s){', some skipped' if skipped else ''}")
        seen = _during(git, tree, tests, base, before)   # EVERY END MEASURED: a commit or an ignored file is said on a red too, never left behind unsaid
        if code != 0 or ran == 0 or skipped:
            failed = _failed_tests(out)   # THE FAILING TESTS BY NAME (its blind rule read 2026-10-28): never the last line alone
            lines.extend(f"6 prove · {r['id']} · {ln}" for ln in failed)
            why = 'a test was skipped' if skipped and code == 0 else f"its tests did not pass ({_last(out)[:200]}{': ' + '; '.join(failed) if failed else ''})"
            return aside(why, f"its run line: {_run_line(tree, tests, conf['python'])}; its change is put back", seen)
        if seen[0]:
            return aside('its tests changed the tree while they ran', 'its change is put back', seen)
        _side(conf, r, proof=proof, proven_at=_stamp(), proven_tests=ran, proven_seconds=secs)   # its proof, when, how many and how long (a rerun's measured time): its block says it
        if not set_state(db, r['id'], 'proven', f'proven: {ran} of {ran} tests pass', when=BUILT):
            return aside(f'it is no longer {BUILT}: a press between the read and the write wins, its tests passed and it is not proven', f"see its state (sqlite3 {db} \"SELECT state, why FROM requests WHERE id='{r['id']}'\")")   # AS A PRESS ON ANY OTHER END: its change put back, its state left as he set it, his last press _goes_on's, so a passing run's red ends too
    lines.append(f"6 prove · {r['id']} · {ran} of {ran} tests pass, none skipped · its change {proof[:12]}")
    return _ok(lines)


def _no_proof_of_its_own(r):
    """why a request has no proof of its own (the original's order or Scrum Master fix), or ''"""
    if r.get('source') == 'order':
        return 'an order'
    if str(r.get('why') or '').startswith('a Scrum Master fix'):
        return 'a Scrum Master fix'
    return ''


def _proof_word(conf, r):
    """PROVEN OR NOT, one request (the original's 'its tests passed <when> (turn ...)'), from its side file: when its frozen tests passed and how
    many, its change's fingerprint; built and waiting: its tests run next; none recorded: said so"""
    if r['state'] == BUILT:
        return 'built: its frozen tests run next'
    s = _side(conf, r)
    if s.get('proven_at'):
        n = s.get('proven_tests')
        took = s.get('proven_seconds')
        return f"its tests passed {_when(s['proven_at'])}" + (f' ({n} of {n}, none skipped)' if n else '') + (f' in {took} s' if took is not None else '') + (f" · its change {str(s['proof'])[:12]}" if s.get('proof') else '')
    other = _no_proof_of_its_own(r)
    return f'no proof of its own ({other})' if other else 'no passing test run of its own recorded'


def report(db, conf):
    """THE ORIGINAL'S RUN LINE (row 013): a list of every request past its build and when its tests passed, or none past its build yet"""
    rows = at(db, *PAST_BUILDING)
    if not rows:
        return 'a list: no request past its build yet'
    return 'a list · ' + _listed([f"{r['id']} {r['state']}: {_proof_word(conf, r)}" for r in rows])


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS, words never markup (web/page.py content_view), the original's row 013 PROVE: the built request its tests
    run on next, then every request past its build and when its own tests passed (or that no proof of its own is recorded), WHY IT'S RED while
    its newest run is red, then the requests it could not prove (each set aside today, its BACK TO ASKED press)."""
    db = store.db_path
    rows = at(db, BUILT) + at(db, *PAST_BUILDING)
    past = [r for r in rows if r['state'] != BUILT]
    parts = [{'kind': 'table', 'title': 'Proven or not', 'under': (f'a list · {len(past)} past its build' if past else 'a list: no request past its build yet'),
              'columns': ['Request', 'His words', 'State', 'Since', 'Its tests'],
              'rows': [{'key': r['id'], 'cells': [r['id'], _cut(r['words']), r['state'], _when(r.get('state_at')), _proof_word(CONF, r)]} for r in rows],
              'empty': 'Nothing built or proven yet: Build hands the next one.'}]
    red = _red_part(store, job_key)
    return parts + ([red] if red else []) + [_aside_part(db, CONF)]


if __name__ == '__main__':   # HIS LINE AFTER HE MENDS ITS TESTS (_frozen_again): the sha of a tests folder, printed; none when it holds no tests
    if len(sys.argv) != 2 or not _has_tests(sys.argv[1]):
        sys.exit(f"no tests in {' '.join(sys.argv[1:])}")
    print(_sha(sys.argv[1]))
