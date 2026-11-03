"""AGENT 017 · REVIEW (the DAY group, the owner 2026-10-28: "DAY is a group on the top right each should say day / and we should see each /
build each one"; "all of day needs to be rewritten its all hotfix style for the day no judge"): a SUB AGENT of the MARK IV agent (agent001),
lower rank, its own block in the DAY group, its own light and its own run. STEP 7: REVIEW (the original's 014: "was it read or not"): the change still the one proven (its fingerprint found again), a separate Claude Code reader, blind (it never saw the build), reads the whole change from its base, its new files and its tests against his words: LEGIT or STUPID, its verdict the last line it says. Never cut: a change too big to read whole is set aside. A red puts its own change back and sets it aside, stuck today.

THE DAY, STEP BY STEP, each step its own agent (agent011 to agent020; agent021 the backlog): the requests, building now, main first, pick,
build, prove, review, commit (then pick again, one request at a time), the hot fix walk (once for every commit of the day), cleanup. A step
that ends green takes the next step's RUN before it writes its own DONE, and the first run drives the next ones in a loop (the chain the page
hands every run: no agent imports another), so RUN AGENT on THE REQUESTS runs the whole day block by block, and RUN AGENT on any step runs the
day from there. A red step stops there: it is THE RED's, its one step said. ONE DAY AT A TIME: one lock for the whole day, a second press ends
red. ON THE HOT FIX TREE (~/spine_worktrees/hotfix), NO JUDGE, NO SEAL, NO PUBLISH: production takes a change only by his AI ECHO HOTFIX
button, never pressed here. Its requests are this office's own (nothing read from the original). ON RUN AGENT ONLY: never due.

ITS BLOCK, THE ORIGINAL'S ROW 014 (content): Was it read or not (the proven request next, then every request past its read and its verdict,
or no read of its own, or none recorded), WHY IT'S RED while its newest run is red, Refused by the read (each request it set aside, stuck
today, his line and its BACK TO ASKED press); its run line the original's list (report)."""
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
import threading
import time
import traceback
import zoneinfo

KEY = 'review'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
ROW = 14   # the original's row 014
NAME = 'Review'
CARD_NAME = 'Scrum Master Review'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Review: a blind read of the change, LEGIT or STUPID'
WHAT = 'Has a separate Claude Code reader read the whole change blind against his words: LEGIT or STUPID'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due (frame_red.due_at)
ROW_FILE = 'agent017_day_review.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes: in its own thread, the page answers RUN AGENT at once
NEXT = 'commit'   # the step it hands on to when it ends green
PRESSES = ('back',)   # its own button on each request it set aside: BACK TO ASKED (his hand line, pressed; the page's agent_press route runs press for these alone)
ASIDE_TITLE, ASIDE_EMPTY = 'Refused by the read', 'No read refused: nothing Review set aside is stuck today.'
PAST_READ = ('reviewed', 'approved', 'waiting_takein', 'taken_in', 'green', 'shipped')   # the original's row 014: the states after the read

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
SIDE, HIRE_MARK, KEPT = '.day_base', '.day_hire', '.day_reviewed'   # A REQUEST'S SIDE FILES in its tests folder (~/scratch/tests/day/<id>, outside the tree: no commit carries them, never a test, never in its tests' sha): its pick's base and its proof; the pid of the worker hired for it now
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
    """A READ A VERDICT STANDS ON: what git printed, or NotMeasured when it did not answer (an empty read is never an empty change or a HEAD at its base)"""
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


def _ignored(git, tree):
    """THE TREE'S IGNORED FILES, each with its fingerprint (as Build): no commit carries them, so their bytes are the only record that the reader edited one. SQLite's
    own working files are left out, for a plain read moves them and they hold no row: a -shm index, an empty -wal. A -wal with rows in it is compared, as is
    the .db. -> {path: fingerprint}"""
    held = [p for code, p in _status(git, '--untracked-files=all', '--ignored') if code == '!!' and not _cache(p)]
    return {p: _print(os.path.join(tree, p)) for p in held if not p.endswith('-shm') and not (p.endswith('-wal') and not (_bytes(os.path.join(tree, p)) or b''))}


def _head(git):
    return _out(git, 'rev-parse', 'HEAD').strip()


def _print(path):
    """one file's fingerprint: its sha256, a link's target, or its stat when its bytes do not read (a folder, a file gone in between)"""
    if os.path.islink(path):
        return f'link {os.readlink(path)}'
    held = _bytes(path)
    if held is not None:
        return hashlib.sha256(held).hexdigest()
    try:
        seen = os.lstat(path)
    except OSError:
        return 'gone'
    return f'stat {seen.st_mode} {seen.st_size} {seen.st_mtime_ns}'


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


def _held(path, most):
    """a file the blind read must read whole: its text, or NotMeasured when it did not read (never a file left out of the read)"""
    try:
        return _read(path, most)
    except OSError as fault:
        raise NotMeasured(f'not measured: {os.path.basename(path)[:120]} did not read ({_line(fault)})') from fault


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
        _head(git)   # a git that does not answer is not measured, never a base the tree lost
        return [(str(base or '?'), '', '', 'its base is not a commit of this tree')]
    out = _out(git, 'log', '--format=%H%x00%ce%x00%P%x00%s', f'{base}..HEAD')
    return [tuple(ln.split('\0', 3)) for ln in out.splitlines() if ln.count('\0') >= 3]


def _at_base(git, base):
    """HEAD and a request's base compared, commit to commit, as Build (_moved lists only what sits past the base, so a HEAD reset behind it reads as nothing moved). -> (HEAD's sha, it is the base)"""
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


def _tracked(git, f):
    """git holds this path (--error-unmatch's own exit 1: an answer, any other a read that failed)"""
    return bool(_out(git, 'ls-files', '--error-unmatch', '--', f, codes=(0, 1)))


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
        if _tracked(git, f):
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


def _fault(fault, conf, db):
    """A STEP THAT BROKE: what did not read (the requests, the tree) is 'not measured', said first with its file and line, and his step is that
    read's, no code to edit (its blind rule read 2026-10-31, as Pick, Building now and Commit); a git that hung the same; anything else is its own crash. -> its red"""
    tree = conf['tree']
    if isinstance(fault, subprocess.TimeoutExpired):   # A HUNG GIT ENDS THE RUN RED, with what clears it: never RUNNING forever under its own heartbeat
        return _hung(tree, fault)
    if isinstance(fault, sqlite3.Error):
        return _no([], f'not measured: the requests cannot be read or written ({_line(fault)}) at {_where(fault)}', _read_step(db, fault))
    if isinstance(fault, (FileNotFoundError, NotADirectoryError)) and not os.path.isdir(tree):   # the tree went while the step worked: git could not start in it
        return _no([], f'not measured: there is no hot fix tree at {tree} ({_line(fault)}) at {_where(fault)}', f'{_tree_step(tree)}, then RUN AGENT here')
    if isinstance(fault, NotMeasured):   # NOT MEASURED SAID FIRST, its file and line beside it: the tree's fault, no code to edit
        return _no([], f'{fault} at {_where(fault)}', f'git -C {tree} status --porcelain prints the error it met; when it still fails, {_tree_step(tree)}, then RUN AGENT here')
    return _crashed(fault)


def _handed_back(name):
    """HIS TWO PRESSES WHEN THE NEXT STEP'S RUN WAS NOT TAKEN: here first, for its request stands reviewed and nothing is proven, so this run ends green and
    hands nothing on; the next step alone never clears this red, for past it Pick hands on to the walk or the cleanup and Review never runs again"""
    return (f'RUN AGENT here, seconds of your hand: its request is reviewed and nothing is proven now, so {NAME} ends green in seconds and hands nothing on, no read, which ends this red; '
            f'then clear what the refusal names (an open run let end, its agent added) and RUN AGENT on {name}: it takes its own RUN and runs the day on by itself')


def _pressed_back(db, rid):
    """HIS TWO PRESSES WHEN A PRESS MOVED THE REQUEST BETWEEN THE READ AND THE WRITE: here first, for nothing is proven now, so this run ends green and hands
    nothing on; Building now alone never clears this red when nothing is asked, for past it Pick hands on to the walk or the cleanup and Review never runs again"""
    return (f"sqlite3 {db} \"SELECT state, why FROM requests WHERE id='{rid}'\" shows what the press set; RUN AGENT here, seconds of your hand: nothing is proven now, so {NAME} ends green in seconds and hands nothing on, no read, "
            f"which ends this red; then RUN AGENT on Building now: its change is still on the tree, and Building now puts it back or prints its own line for it, then runs the day on by itself")


def once(store, job_key, n, agent, chain, conf, runner, hire, db, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step); green, the next step's RUN taken first: a next refused or
    missing ends this one FAILED, said; a next switched off is off, never a red: this one ends DONE, hands nothing on, and its request stands reviewed. A crash ends FAILED with its line. -> (what it said, the next to run (module, shell, run) or None)"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not locked:
        got = _no([], 'another DAY step is running', f'lsof {_lock_path(conf)} names the run that holds the lock: let it end (its block says RUNNING), then RUN AGENT')
    else:
        try:
            with Beat(store, job_key):
                got = step(store, conf, runner, db, hire)
        except Exception as fault:   # A CRASH IS RED, NAMED WHERE IT HAPPENED: the traceback's last frame, its file and line (its blind rule read 2026-10-28; as agent011)
            got = _fault(fault, conf, db)
    if not got['ok']:   # every press that ends a red: the longer pieces it starts named, none left unsaid
        got = {**got, 'step': _timed(conf, got['step'])}
    nxt = None
    if got['ok'] and got.get('next'):
        nxt, why = hand_on(store, chain, got['next'])
        name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or got['next']
        if nxt is None and why:
            got = {**got, 'ok': False, 'why': f'the day stopped before {name}: {why}', 'step': _timed(conf, _handed_back(name)), 'next': None}
        elif nxt is None:   # OFF IS NEVER A RED: the day rests here by his switch, the read kept, nothing handed on
            got = {**got, 'lines': got['lines'] + [f'{name} is switched off, its RUN not taken: the request stands reviewed; when you turn it on, RUN AGENT on {name}'], 'next': None}
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
        got = {**got, 'step': _timed({**CONF, **(conf or {})}, got['step'])}
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
                     'copy': f"{HAND}{_timed(conf, _asked(db, r['id']) + ', then RUN AGENT on Pick')}",
                     'presses': [{'do': 'back', 'label': 'Back to asked', 'confirm': f"Send {r['id']} back to asked? Pick takes it again in its build order."}]})
    return {'kind': 'table', 'title': ASIDE_TITLE, 'under': (f"{len(rows)} stuck today: each one's change was put back; BACK TO ASKED sends it back to the backlog" if rows else 'none stuck today'),
            'columns': ['Request', 'His words', 'Why', 'Set aside', 'Your press'], 'rows': rows, 'empty': ASIDE_EMPTY}


def press(store, job_key, do, fields=None):
    """ITS BUTTON ON A REQUEST IT SET ASIDE: 'back', his hand line pressed: the request stuck today by this step set back to asked (Pick takes it
    again in its build order; its tests unfrozen, as the line unfreezes them: Build writes them anew from his words). Any other request, or one moved since, changes nothing, said.
    -> the words said on its shell"""
    if do not in PRESSES:
        raise ValueError(f'not one of its presses: {do!r}')
    db, rid = store.db_path, str((fields or {}).get('value') or '').strip()
    try:
        r = next((x for x in requests(db) if x['id'] == rid), None)
        if r is None:
            return f"BACK TO ASKED · no request {rid or 'named'}: nothing changed"
        if r['state'] != STUCK or (_side(CONF, r).get('aside') or {}).get('step') != KEY:
            return f'BACK TO ASKED · {rid} is {r["state"]}, not set aside by {NAME}: nothing changed'
        if not set_state(db, rid, WAITING, f'sent back to asked by the owner ({NAME} had set it aside)', when=STUCK, tests_sha=None):
            return f'BACK TO ASKED · {rid} moved before the write: nothing changed'
    except sqlite3.Error as fault:   # as Pick and Building now: requests that do not read are not measured, said with his step
        return f'BACK TO ASKED · not measured: the requests cannot be read or written ({_line(fault)}): nothing changed · {HAND}{_timed(CONF, _read_step(db, fault))}'
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


COLUMNS = {'id': 'TEXT', 'words': "TEXT NOT NULL DEFAULT ''", 'state': 'TEXT', 'source': 'TEXT', 'position': 'INTEGER NOT NULL DEFAULT 0', 'tests': 'TEXT', 'tests_sha': 'TEXT', 'commits': 'TEXT',
           'why': 'TEXT', 'done_at': 'TEXT', 'state_at': "TEXT NOT NULL DEFAULT ''", 'asked_at': "TEXT NOT NULL DEFAULT ''"}   # a column its read needs, as ALTER TABLE takes it back: every row kept
TABLE = ("CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY NOT NULL, words TEXT NOT NULL, hash TEXT NOT NULL, source TEXT CHECK (source IN ('session', 'sprint', 'order')), "
         "ref TEXT, asked_at TEXT NOT NULL, position INTEGER NOT NULL, state TEXT CHECK (state IN ('asked', 'planned', 'building', 'proven', 'reviewed', 'waiting_takein', 'approved', "
         "'taken_in', 'green', 'shipped', 'stuck_today', 'removed')), state_at TEXT NOT NULL, why TEXT, tests TEXT, tests_sha TEXT, commits TEXT, done_at TEXT, "
         "environment TEXT CHECK (environment IS NULL OR json_valid(environment)))")   # the table as this office holds it


def _read_step(db, fault):
    """HIS ONE STEP FOR A READ THAT FAILED, as The requests' (its blind rule read 2026-10-31): the one line that clears the error its read met"""
    words = str(fault)
    column = re.search(r'no such column: (\w+)', words)
    if 'locked' in words:
        return f'lsof {db} names the other writer: database is locked clears when it ends, then RUN AGENT here'
    if column and column.group(1) in COLUMNS:
        return f'sqlite3 {db} "ALTER TABLE requests ADD COLUMN {column.group(1)} {COLUMNS[column.group(1)]}" (every row kept), then RUN AGENT here'
    if 'no such table' in words or 'unable to open' in words:
        return f'mkdir -p {os.path.dirname(db)} && sqlite3 {db} "{TABLE}" (it stands up empty: the rows that went with it are not in it), then RUN AGENT here'
    return f'B={db}.broken-$(date +%Y%m%d%H%M%S); mv {db} $B && sqlite3 $B .recover | sqlite3 {db} (every row that still reads kept, the broken file beside it), then RUN AGENT here'


def _read_piece(conf, secs=None):
    """THE ONE NAMED EXCEPTION TO HIS 3 MINUTES ON A RERUN OF THIS STEP (his rule: the read takes at most 7 minutes): a press that finds a request proven reads it
    anew, stopped by its clock; his hand is seconds. A LEGIT read's run goes on past that piece into Commit and the day, by itself: none of it this red's work.
    secs: the read this red measured. -> words"""
    ran = f', this read ran {secs} s, measured' if secs is not None else ''
    return (f"seconds of your hand; the one piece past 3 minutes, named: a new blind read of a proven request, at most {conf['review_seconds'] // 60} minutes by his rule, its clock stops it at {conf['review_seconds']} s{ran}; "
            "this red ends with that read, and on LEGIT the same run goes on past it into Commit and the rest of the day by itself, nothing more from you, each later red says its own line")


def _prove_piece(conf):
    """THE PIECES PAST HIS 3 MINUTES WHEN HIS PRESS IS ON PROVE (a change not the one proven, proven again): its tests, stopped by their clock, then the read they hand on to. -> words"""
    tests, read = conf['prove_seconds'], conf['review_seconds']
    return (f"seconds of your hand; the two pieces past 3 minutes, named: Prove runs its tests, their clock stops them at {tests} s, and when they pass a new blind read here, at most {read // 60} minutes by his rule, "
            f"its clock stops it at {read} s, so at most {(tests + read) // 60} minutes together, by themselves; on LEGIT the same run goes on past them into Commit and the rest of the day, nothing more from you, each later red says its own line")


def _day_piece(conf):
    """THE PIECES PAST HIS 3 MINUTES WHEN HIS PRESS RUNS THE DAY ON (Pick, Building now or the next step): the next request's Build, its tests and its read, each stopped by its own clock. -> words"""
    write, first, build = conf['write_seconds'], conf['prove_seconds'], conf['build_seconds']
    return (f"seconds of your hand; that press runs the day on by itself, the pieces past 3 minutes named: Build up to {(write + first + build) // 60} minutes ({write // 60} for the test writer, {first // 60} for its tests' failing-first run, "
            f"{build // 60} for the developer), Prove's tests stopped at {conf['prove_seconds']} s, a new blind read stopped at {conf['review_seconds']} s, nothing more from you, each later red says its own line")


def _timed(conf, step):
    """A RED'S STEP WITH WHAT ITS LAST PRESS STARTS: a rerun here its read, a press on Prove its tests and its read, a press that runs the day on the day's own pieces; a step that says its own, or starts none, as it is. -> the step"""
    if step.endswith(('RUN AGENT', 'RUN AGENT here')):
        return f'{step} ({_read_piece(conf)})'
    if step.endswith('RUN AGENT on Prove'):
        return f'{step} ({_prove_piece(conf)})'
    if step.endswith(('RUN AGENT on Pick', 'then the day picks it again', 'the day goes on with the next request', 'runs the day on by itself')):
        return f'{step} ({_day_piece(conf)})'
    return step


def _undone(tree, db, rid, base):
    """HIS ONE COMMAND WHEN A COMMIT SITS PAST A REQUEST'S BASE: what the tree holds stashed first, never lost (a proven change left dirty stops the revert or Pick's clean tree), reverted, the request asked again with its tests unfrozen; its new pick records the new base"""
    return f"git -C {tree} stash push -u -m day-{rid} && {{ [ -z \"$(git -C {tree} rev-list {base[:12]}..HEAD)\" ] || git -C {tree} revert --no-edit {base[:12]}..HEAD; }} && sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


def _brought_up(tree, db, rid, base):
    """HIS ONE COMMAND WHEN HEAD SITS BEHIND A REQUEST'S BASE: what the tree holds stashed, never lost (its proof stood on the base, never on this older code, and a tree that holds it stops a fast-forward), its branch brought
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
    """HIS ONE LINE that sets a request's state by hand (back to asked: Pick takes it again in its build order, its tests unfrozen: Build's writer writes them anew from his words, the same as Build's own line; never set back with a sha kept, its fixed tests would be refused as changed and its unfixed ones return frozen)"""
    return f"sqlite3 {db} \"UPDATE requests SET state='{state}'{', tests_sha=NULL' if state == WAITING else ''} WHERE id='{rid}'\""


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
        return _no(lines, f"{r['id']}: the tree went back behind its pick (HEAD {head[:12]}, its base {base[:12]}): never built on, never reviewed",
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
    """HIS LAST PRESS WHEN A PRESS MOVED THE REQUEST, read now: with a request asked, Pick, so Review runs again; with none, Pick would hand on to the walk or the cleanup and Review would stay red, so here"""
    if at(db, WAITING):
        return 'RUN AGENT on Pick: the day goes on with the next request'
    return 'RUN AGENT here: with nothing proven it ends green in seconds and hands nothing on'


def _set_aside(db, git, tree, base, r, files, why, step, lines, conf=None):
    """A RED OF REVIEW: its change put back (its own files alone), it stuck today, the day stops here. His one step, every red the same (as Build and
    Prove): what the red names fixed (a file that would not go back cleared by hand first), its one line that sets it back to asked, then RUN AGENT
    on Pick: never Pick alone, for with nothing asked Pick hands on to the walk or the cleanup, Review never runs and this red stays; set back, a
    request is always there to pick, so Review runs again and ends this red, even on the last request.
    conf: the step that set it aside, why and when, kept in its side file (its block lists it with its BACK TO ASKED press)."""
    back, kept = put_back(git, tree, base, files)
    if not set_state(db, r['id'], STUCK, why[:300], when=r['state']):   # A PRESS DURING THE RUN WINS (its blind rule reads 2026-10-28): its change put back, its state left as he set it, never said stuck
        lines.append(f"{r['id']}: a press moved it during the run: its state is left as he set it")
        lines.append(f"{r['id']}: its {len(back)} changed file(s) put back" + (f", {len(kept)} would not go back: {', '.join(kept[:4])}" if kept else ''))
        first = f"clear {', '.join(kept[:4])} by hand (git -C {tree} status), then " if kept else ''
        return _no(lines, f"{r['id']}: {why}; not set aside, a press moved it", f"{step}; {first}{_goes_on(db)}")
    if conf:
        _side(conf, r, aside={'step': KEY, 'why': why[:300], 'at': _stamp()})
    lines.append(f"{r['id']} set aside: stuck today, its {len(back)} changed file(s) put back" + (f", {len(kept)} would not go back: {', '.join(kept[:4])}" if kept else ''))
    first = f"clear {', '.join(kept[:4])} by hand (git -C {tree} status), then " if kept else ''
    return _no(lines, f"{r['id']}: {why}", f"{step}; {first}{_asked(db, r['id'])} (it unfreezes its tests so Build writes them anew from his words; {r['id']} is asked again, "
               f"so Pick always has a request and Review runs and ends this red, even when it is the last), then RUN AGENT on Pick")   # once() adds what that press starts (_timed): Build's minutes, Prove's 600 s, the read's 420 s


def _on(git):
    """the branch HEAD is on, '' on a detached HEAD (symbolic-ref's own exit 1: an answer, any other a read that failed)"""
    return _out(git, 'symbolic-ref', '-q', 'HEAD', codes=(0, 1)).strip()


def _elsewhere(git):
    """THE BRANCHES ANOTHER WORKTREE HAS CHECKED OUT (the repo's refs are shared: another session's merge there moves them while a worker works
    here, never the worker's move, as main). -> their refs, this tree's own branch never one"""
    held = {ln[len('branch '):] for ln in _out(git, 'worktree', 'list', '--porcelain').splitlines() if ln.startswith('branch ')}
    return held - {_on(git)}


def _snap(git, tree, side):
    """THE TREE'S GIT AND THE REQUEST'S SIDE FILE before a hire: every local ref (git for-each-ref), the branches other worktrees hold, HEAD, the ignored files with their fingerprints, the side file's bytes"""
    refs = _out(git, 'for-each-ref', '--format=%(refname) %(objectname)').splitlines()
    return {'refs': {ln.split(' ', 1)[0]: ln.split(' ', 1)[1] for ln in refs if ' ' in ln and not ln.startswith(('refs/remotes/', 'refs/heads/main '))},
            'elsewhere': _elsewhere(git), 'head': _head(git), 'sym': _on(git), 'ignored': _ignored(git, tree), 'side': _bytes(side)}


def _hired(git, tree, before, side):
    """WHAT A HIRED WORKER MAY NEVER DO, seen after it ends: move the tree's git (a commit, a branch, a tag, a stash: any ref but a branch another
    worktree holds, any git form), write, edit or remove an ignored file, or touch the request's side file. -> why, the commit named, or ''"""
    after = _snap(git, tree, side)
    theirs = before['elsewhere'] | after['elsewhere']
    moved = sorted(ref for ref in set(before['refs']) | set(after['refs']) if ref not in theirs and before['refs'].get(ref) != after['refs'].get(ref))
    if after['head'] != before['head'] or after['sym'] != before['sym'] or moved:
        named = [f"HEAD {before['head'][:12]} became {after['head'][:12]}"] if after['head'] != before['head'] else []
        for ref in moved:
            if not (ref == after['sym'] and named):
                named.append(f"{ref} {str(before['refs'].get(ref) or 'none')[:12]} became {str(after['refs'].get(ref) or 'none')[:12]}")
        top = _out(git, 'log', '-1', '--format=%h "%s"', after['head']).strip() if after['head'] != before['head'] else ''
        return (f"a hired worker moved the tree's git on its own ({'; '.join(named[:3])}" + (f'; its commit {top}' if top else '')
                + '): that commit is not reviewed and is never built on')
    new = sorted(set(after['ignored']) - set(before['ignored']))
    edited = sorted(p for p, was in before['ignored'].items() if after['ignored'].get(p) != was)
    if new or edited:
        said = [f"wrote new ignored file(s) a commit never carries: {', '.join(new[:4])}"] if new else []
        if edited:   # no commit and no copy holds their old bytes: never put back by a line
            said.append(f"edited or removed existing ignored file(s), their old bytes kept nowhere, so see them by hand: {', '.join(edited[:4])}")
        return f"a hired worker {'; '.join(said)}"
    return 'a hired worker changed its side file (its base and proof)' if after['side'] != before['side'] else ''


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
        return None, _no(lines, f"{len(rows)} requests are {state} at once: {', '.join(r['id'] for r in rows[:4])}", f"sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE state='{state}' AND id<>'{rows[0]['id']}'\", then RUN AGENT")
    return rows[0], None


def _wait(why):
    """HIS STEP WHILE THE TREE IS ANOTHER'S: its pid is in its why, its mark no open file, so ps names it where lsof on the day's lock would not"""
    pid = re.search(r'pid (\d+)', why).group(1)
    return f'ps -p {pid} -o command= names that run: let it end (never delete the mark while it lives), then RUN AGENT here'


def _words_review(r, diff, tests_text):
    return (f"You are THE DAY's reviewer, BLIND: you never saw the build. Read the change against the owner's own words and decide.\n\n"
            f"THE REQUEST {r['id']}, his words:\n{r['words']}\n\nITS TESTS:\n{tests_text}\n\nTHE CHANGE (git diff):\n{diff}\n\n"
            "LEGIT when the change does what he asked, no more, honestly (no test cheated, no shortcut, nothing faked). STUPID otherwise. "
            "Your last line exactly: VERDICT: LEGIT <one line why> or VERDICT: STUPID <one line why>.")


def step(store, conf, runner, db, hire):
    """THE TREE'S WRITER MARK FIRST, every check under it (its blind rule read 2026-10-28, as Main first and Cleanup): a running hot fix
    utility or another writer is said as itself, never as files nobody committed or a tree that moved"""
    with Writer(conf) as w:
        if w.why:
            return _no([], w.why, _wait(w.why))
        return _step(store, conf, runner, db, hire)


def _step(store, conf, runner, db, hire):
    lines = []
    tree = conf['tree']
    git = _git(tree, runner)
    _changed(git)   # GIT STATUS READ FIRST, on every way through (its blind rule read 2026-10-31): a tree that does not read is not measured before nothing proven, two proven or no base is said
    r, red = _one(db, 'proven', lines, 'Review')
    if red or r is None:
        return red
    tests = _tests_of(conf, r)
    info = _side(conf, r)
    red = _since_pick(git, tree, r, info, lines, built=True, db=db)
    if red:
        return red
    base, files, side = info['base'], sorted(info['files']), os.path.join(tests, SIDE)
    proof = _proof(git, tree, base)
    if proof != info.get('proof'):
        return _no(lines, f"{r['id']}: its change is not the one proven (its fingerprint {proof[:12]}, proven {str(info.get('proof') or 'none')[:12]})", f"see `git -C {tree} diff {base[:12]}`: the tree moved after its proof; to prove it again set {r['id']} back to building ({_asked(db, r['id'], BUILT)}), then RUN AGENT on Prove")
    with Writer(conf) as w:
        if w.why:
            return _no(lines, f"{r['id']}: {w.why}", _wait(w.why))
        aside = lambda why, step_: _set_aside(db, git, tree, base, r, files, why, step_, lines, conf)
        diff = _out(git, 'diff', base, '--', *files)
        news = [f for f in files if not _tracked(git, f) and os.path.isfile(os.path.join(tree, f))]
        new_texts = {f: _held(os.path.join(tree, f), CAPS['file']) for f in news}
        test_files = sorted(os.path.join(rt, f) for rt, _d, fs in os.walk(tests) for f in fs if f.endswith('.py'))
        tests_text = ''.join(f'\n# {os.path.relpath(f, tests)}\n' + _held(f, CAPS['tests']) for f in test_files)
        over = ([f"its diff is past {CAPS['diff']} characters"] if len(diff) > CAPS['diff'] else []) + [f"new file {f} is past {CAPS['file']} characters" for f, t in new_texts.items() if len(t) > CAPS['file']][:3] + ([f"its tests are past {CAPS['tests']} characters"] if len(tests_text) > CAPS['tests'] else [])
        if over:
            return aside(f"the change is too big for the blind reader to read whole ({'; '.join(over)})", 'its change is put back; a smaller request of his words is his to ask (UPDATE on Backlog), or its tests written anew when they are the big part')
        diff += ''.join(f'\n+++ new file {f}\n{t}' for f, t in new_texts.items())
        snap = _snap(git, tree, side)
        took = time.monotonic()
        code, said = _hired_by(hire, conf, r, READER, _words_review(r, diff, tests_text), tree, conf['review_seconds'])
        secs = round(time.monotonic() - took)
        lines.append(f"7 review · {r['id']} · its blind read ended exit {code} in {secs} s (at most {conf['review_seconds']} s)")
        bad = _hired(git, tree, snap, side)
        if bad:
            return _no(lines, f"{r['id']}: {bad}", f"see `git -C {tree} log -3`, status and the files this red names: take it out by hand (back to {base[:12]}), set {r['id']} back to asked ({_asked(db, r['id'])}), then RUN AGENT on Pick")
        if _proof(git, tree, base) != proof:
            return aside('its change moved while it was read', 'its change is put back')
        m = VERDICT.match(_last(said)) if code == 0 else None   # THE VERDICT IS ITS LAST LINE of a read that ended (exit 0): a VERDICT quoted earlier, or a read stopped by its clock or broken, never counts
        if m and not m.group(2).strip():
            m = None   # a verdict with no why is never kept half said (as frame_rules.answer)
        if not m:   # THE READER'S OWN FAULT (broken, stopped by its clock, no verdict): never blamed on his words, the request stays proven (its rule read 2026-10-28)
            ended = '' if code == 0 else f", stopped by its clock at {secs} s" if code is None else f', its read ended exit {code}'
            return _no(lines, f"{r['id']}: its blind read gave no verdict (no VERDICT and why as its last line{ended}): it stays proven, its change kept",
                       f"RUN AGENT here, one press ({_read_piece(conf, secs)})")
        if m.group(1).upper() != 'LEGIT':
            return aside(f"its review said STUPID: {m.group(2)[:200]}", 'its change is put back')
        _keep_read(git, conf, r, base, proof)
        _side(conf, r, read={'verdict': 'LEGIT', 'why': m.group(2)[:200], 'at': _stamp(), 'seconds': secs})   # its verdict and its measured time kept beside its proof: its block says it after Commit writes its own why
        if not set_state(db, r['id'], 'reviewed', f'reviewed LEGIT: {m.group(2)[:200]}', when='proven'):
            return _no(lines, f"{r['id']} is no longer proven: a press between the read and the write wins", _pressed_back(db, r['id']))
    lines.append(f"7 review · {r['id']} · LEGIT · {m.group(2)[:160]}")
    return _ok(lines)


def _keep_read(git, conf, r, base, proof):
    """THE CHANGE IT READ, KEPT WHOLE BESIDE ITS PROOF (<its tests folder>/.day_reviewed, a patch from its base, new files in it): a tree that moves after
    this read is put back to these very bytes by Commit's one line, in seconds, with no new proof"""
    path = os.path.join(_tests_of(conf, r), KEPT)
    part = path + '.part'   # git itself writes each part: its bytes kept whole (a CRLF line never goes through text)
    new = _out(git, 'ls-files', '--others', '--exclude-standard', '-z')
    _out(git, 'diff', '--binary', f'--output={part}', base, '--')
    with open(path + '.tmp', 'wb') as fh:
        fh.write(_bytes(part) or b'')
        for f in sorted(p for p in new.split('\0') if p and not _cache(p)):
            _out(git, 'diff', '--binary', '--no-index', f'--output={part}', '--', '/dev/null', f, codes=(0, 1))   # --no-index exits 1 when the two differ
            fh.write(_bytes(part) or b'')
    os.remove(part)
    os.replace(path + '.tmp', path)
    _side(conf, r, kept=proof)


def _no_read_of_its_own(r):
    """why a request has no read of its own (the original's: an order, a Scrum Master fix), or ''"""
    if r.get('source') == 'order':
        return 'an order'
    if str(r.get('why') or '').startswith('a Scrum Master fix'):
        return 'a Scrum Master fix'
    return ''


def _read_word(conf, r):
    """WAS IT READ OR NOT, one request (the original's 'read CLEAN, <state> since <when>'), from its side file: its blind read's verdict, when
    and why; proven and waiting: the read next; none recorded: said so"""
    if r['state'] == 'proven':
        return 'proven: the blind read is next'
    read = _side(conf, r).get('read') or {}
    if read.get('verdict') == 'LEGIT':
        took = read.get('seconds')
        return f"read LEGIT {_when(read.get('at'))}" + (f' in {took} s' if took is not None else '') + f": {_cut(read.get('why'), 200)}"
    other = _no_read_of_its_own(r)
    return f'no read of its own ({other})' if other else 'no read recorded'


def report(db, conf):
    """THE ORIGINAL'S RUN LINE (row 014): every request past its read, read LEGIT and since when, no read of its own, or no read recorded"""
    rows = at(db, *PAST_READ)
    if not rows:
        return 'nothing past its read yet'
    said = []
    for r in rows:
        w = _read_word(conf, r)
        said.append(f"{r['id']} read LEGIT, {r['state']} since {_when(r.get('state_at'))}" if w.startswith('read LEGIT') else f"{r['id']} {r['state']}: {w}")
    return _listed(said)


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS, words never markup (web/page.py content_view), the original's row 014 REVIEW: the proven request the blind
    read takes next, then every request past its read and its verdict (or no read of its own, or none recorded), WHY IT'S RED while its newest
    run is red, then the reads that refused (each set aside today, its BACK TO ASKED press)."""
    db = store.db_path
    red = _red_part(store, job_key)
    try:
        rows = at(db, 'proven') + at(db, *PAST_READ)
        aside = _aside_part(db, CONF)
    except sqlite3.Error as fault:   # as Pick and Building now: requests that do not read are not measured, said with his step
        return [{'kind': 'note', 'title': 'Was it read or not', 'text': f'not measured: the requests cannot be read ({_line(fault)}) · {HAND}{_timed(CONF, _read_step(db, fault))}'}] + ([red] if red else [])
    past = [r for r in rows if r['state'] != 'proven']
    parts = [{'kind': 'table', 'title': 'Was it read or not', 'under': (f'{len(past)} past its read' if past else 'nothing past its read yet'),
              'columns': ['Request', 'His words', 'State', 'Since', 'Its read'],
              'rows': [{'key': r['id'], 'cells': [r['id'], _cut(r['words']), r['state'], _when(r.get('state_at')), _read_word(CONF, r)]} for r in rows],
              'empty': 'Nothing proven or read yet: Prove hands the next one.'}]
    return parts + ([red] if red else []) + [aside]
