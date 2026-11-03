"""AGENT 012 · BUILDING NOW (the DAY group, the owner 2026-10-28: "DAY is a group on the top right each should say day / and we should see each /
build each one"; "all of day needs to be rewritten its all hotfix style for the day no judge"): a SUB AGENT of the MARK IV agent (agent001),
lower rank, its own block in the DAY group, its own light and its own run. STEP 2: BUILDING NOW (the original's 005: "did it start the build or not"): a request left between its pick and its commit by a run that stopped (its page restarted) goes back to the backlog, its own recorded files put back to its base and nothing else; a tree that holds anything else (his own hand edits), a commit past its pick, or a hire still alive stops the day untouched. One whose commit landed before its run stopped is recorded committed, never built again; one committed waits for tonight's take-in.

THE DAY, STEP BY STEP, each step its own agent (agent011 to agent020; agent021 the backlog): the requests, building now, main first, pick,
build, prove, review, commit (then pick again, one request at a time), cleanup (no day walk: the full walk runs at night with the full build). A step
that ends green takes the next step's RUN before it writes its own DONE, and the first run drives the next ones in a loop (the chain the page
hands every run: no agent imports another), so RUN AGENT on THE REQUESTS runs the whole day block by block, and RUN AGENT on any step runs the
day from there. A red step stops there: it is THE RED's, its one step said. ONE DAY AT A TIME: one lock for the whole day, a second press ends
red. ON THE HOT FIX TREE (~/spine_worktrees/hotfix), NO JUDGE, NO SEAL, NO PUBLISH: production takes a change only by his AI ECHO HOTFIX
button, never pressed here. Its requests are this office's own (nothing read from the original). ON RUN AGENT ONLY: never due."""
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
import traceback
import threading
import time
import zoneinfo

KEY = 'building_now'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
ROW = 5   # the original's row 005
NAME = 'Building now'
CARD_NAME = 'Scrum Master Building now'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Building now: what a stopped run left half built goes back'
WHAT = 'The request in hand, its state and whether a worker is on it, and the last build; one a stopped run left half built goes back to the backlog'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due (frame_red.due_at)
ROW_FILE = 'agent012_day_building_now.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes: in its own thread, the page answers RUN AGENT at once
NEXT = 'main_first'   # the step it hands on to when it ends green

HOME = os.path.expanduser('~')
CONF = {'tree': os.path.join(HOME, 'spine_worktrees', 'hotfix'), 'branch': 'hold/20261021', 'main': 'main',   # branch: the hot fix tree's, named in the steps that stand it up again
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
COMMITTED, READY, STUCK = 'approved', 'waiting_takein', 'stuck_today'   # COMMITTED is the old state from before the day walk was removed; a landed day commit is READY, waiting for tonight's take-in
BEAT = 60   # seconds between two heartbeats of a long step (THE RED's QUIET is 3 minutes)
PS_SECONDS, HIRE_GRACE = 10, 2   # the longest one ps may run; a hire's process begins before its mark's stamp, whole seconds both, so 2 s covers the rounding
GIT_SECONDS = 120   # the longest one git call may run: its calls end in seconds, one past this is hung, stopped and red (never RUNNING forever with the day's lock and the writer mark held)
HAND = 'YOUR 3 MIN: '
DAY_EMAIL = 'day@localhost'   # THE DAY's own commits (its merge of main, its commit of a request) carry it
SIDE, HIRE_MARK = '.day_base', '.day_hire'   # A REQUEST'S SIDE FILES in its tests folder (~/scratch/tests/day/<id>, outside the tree: no commit carries them, never a test, never in its tests' sha): its pick's base and its proof; the pid of the worker hired for it now
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


def _out(git, *args):
    """A READ A GREEN STANDS ON: what git printed, or NotMeasured when it did not answer (an empty read is never a new file or a HEAD)"""
    seen = git(*args)
    if seen.returncode != 0:
        raise NotMeasured(f'not measured: git {args[0]} failed ({_last(seen.stderr)[:120]})')
    return seen.stdout


def _status(git, *more):
    """the tree's own status, NUL separated (a path with any byte said whole): [(code, path)]"""
    seen = git('status', '--porcelain=v1', '-z', *more)
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


def _ignored(git):
    return {p for code, p in _status(git, '--untracked-files=all', '--ignored') if code == '!!' and not _cache(p)}


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
    seen = git('log', '--format=%H%x00%ce%x00%P%x00%s', f'{base}..HEAD')
    if seen.returncode != 0:   # a log that did not read is never a HEAD at its base
        raise NotMeasured(f'not measured: git log failed ({_last(seen.stderr)[:120]})')
    return [tuple(ln.split('\0', 3)) for ln in seen.stdout.splitlines() if ln.count('\0') >= 3]


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


def _prints(tree, files):
    """EACH BUILT FILE'S OWN sha256 as its build left it (None: its build removed it): {file: sha}"""
    held = {f: _bytes(os.path.join(tree, f)) for f in files}
    return {f: hashlib.sha256(b).hexdigest() if b is not None else None for f, b in held.items()}


def _hand_edited(tree, info, files):
    """THE RECORDED FILES THAT ARE NOT WHAT ITS BUILD LEFT (his hand edits inside them, never put back). files: the ones still changed, so one already
    back at its base is no edit. -> [file], or None when its build kept no prints: not measured, never passed"""
    kept = info.get('prints')
    if not isinstance(kept, dict) or not set(files) <= set(kept):
        return None
    now = _prints(tree, files)
    return [f for f in files if now[f] != kept[f]]


def _proof(git, tree, base):
    """THE CHANGE'S OWN FINGERPRINT: sha256 of its diff from its base and its new files' bytes (Prove keeps it; Review and Commit find the
    same one, or stop)"""
    h = hashlib.sha256(git('diff', '--binary', base, '--').stdout.encode('utf-8', 'surrogateescape'))
    for f in sorted(p for p in git('ls-files', '--others', '--exclude-standard', '-z').stdout.split('\0') if p and not _cache(p)):
        h.update(b'\0' + f.encode('utf-8', 'surrogateescape') + b'\0')
        h.update(_bytes(os.path.join(tree, f)) or b'<unreadable>')
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
        return [dict(zip(('id', 'words', 'state', 'position', 'tests', 'tests_sha', 'commits', 'why', 'done_at', 'state_at', 'asked_at'), r))
                for r in con.execute('SELECT id, words, state, position, tests, tests_sha, commits, why, done_at, state_at, asked_at FROM requests ORDER BY position, id')]
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


def _wait_step(why):
    """HIS STEP ON A RED THAT SAYS WAIT FOR THE MARK OR THE UTILITY: its pid is in its why, its mark no open file: ps names it where lsof on the day's lock would not"""
    pid = re.search(r'pid (\d+)', why).group(1)
    return f'ps -p {pid} -o command= names that run: let it end, then RUN AGENT here'


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
    """ITS OWN CODE CRASHED: red, named as a crash, its file and line its step"""
    where = _where(fault)
    return {'ok': False, 'lines': [], 'why': f'it crashed at {where} ({_line(fault)})', 'step': f'open app/agent/{where}, fix what the crash names, then RUN AGENT', 'next': None}


def _ended(got):
    return {'summary': ('DONE · ' if got['ok'] else f"FAILED · {got['why']} · {HAND}{got['step']} · ") + ' | '.join(got['lines'][-3:]), **got}


def _hung(tree, fault):
    """A GIT THAT DID NOT END: stopped at GIT_SECONDS, its heartbeat, the writer mark and the day's lock let go on the way out; said not measured, with what clears it"""
    lock = f'"$(git -C {tree} rev-parse --git-path index.lock)"'
    return _no([], f'not measured: a git call hung and was stopped at {_where(fault)} ({_line(fault)})',
               f"ps -axo pid,etime,command | grep '[g]it ' names any git left running: let it end; with none left, rm -f {lock}, and when git -C {tree} status --porcelain answers at once, RUN AGENT here")


def once(store, job_key, n, agent, chain, conf, runner, hire, db, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step); green, the next step's RUN taken first: a next refused or
    missing ends this one FAILED, said; a next switched off is off, never a red: this one ends DONE and hands nothing on. A crash ends FAILED with its line. -> (what it said, the next to run (module, shell, run) or None)"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not locked:
        got = _no([], 'another DAY step is running', f'lsof {_lock_path(conf)} names the run that holds the lock: let it end (its block says RUNNING), then RUN AGENT')
    else:
        try:
            with Beat(store, job_key):
                got = step(store, conf, runner, db, hire)
        except NotMeasured as fault:   # NOT MEASURED SAID FIRST, its file and line beside it: the tree's fault, no code to edit (its blind rule read 2026-10-31)
            got = _no([], f'{fault} at {_where(fault)}', f"git -C {conf['tree']} status prints the error it met; when it still fails, {_stood_up(conf['tree'], conf)} (moved aside, never lost), then RUN AGENT here")
        except subprocess.TimeoutExpired as fault:   # A HUNG GIT ENDS THE RUN RED, with what clears it: never RUNNING forever under its own heartbeat
            got = _hung(conf['tree'], fault)
        except sqlite3.Error as fault:   # A LATER READ OR WRITE OF THE REQUESTS FAILED: not measured with its step, never a crash in his code
            got = _no([], f'not measured: the requests cannot be read ({_line(fault)})', _read_step(db, fault))
        except Exception as fault:   # A CRASH IS RED, NAMED WHERE IT HAPPENED: its own file and line (its blind rule read 2026-10-28)
            got = _crashed(fault)
    nxt = None
    if got['ok'] and got.get('next'):
        nxt, why = hand_on(store, chain, got['next'])
        name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or got['next']
        if nxt is None and why:
            got = {**got, 'ok': False, 'why': f'the day stopped before {name}: {why}', 'step': f'do what that says on the {name} block, then RUN AGENT here (this step takes its RUN again)', 'next': None}
        elif nxt is None:   # OFF IS NEVER A RED: the day rests here by his switch, nothing handed on
            got = {**got, 'lines': got['lines'] + [f'{name} is switched off, its RUN not taken; when you turn it on, RUN AGENT on {name}'], 'next': None}
    said = _ended(got)
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
        said = _ended(_crashed(fault))
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


COLUMNS = {'id': 'TEXT', 'words': "TEXT NOT NULL DEFAULT ''", 'state': 'TEXT', 'position': 'INTEGER NOT NULL DEFAULT 0', 'tests': 'TEXT', 'tests_sha': 'TEXT', 'commits': 'TEXT',
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


BUILD = 'Build'   # THE BUILD STEP'S JOB ON THIS BOARD, by the name the page gives its job (its NAME): the last build is its newest run that worked on a request
WITHIN = 180   # his 3 minute rule: a build within it says "within 3 min", a longer one "OVER 3 min" (words only, never the light)
STAGE = {'planned': 'picked, Build is next', 'building': 'built, Prove is next', 'proven': 'proven, Review is next', 'reviewed': 'reviewed, Commit is next',
         'approved': 'committed before the day walk was removed'}   # what each state of a request in hand means in THE DAY
NAMED = re.compile(r'\bR-\d{4,}\b')   # a request named in a run's line


def _zone():
    return zoneinfo.ZoneInfo(SCHEDULE['timezone'])


def _moment(at):
    """an ISO moment, or LARRYD's 'YYYY-MM-DD HH:MM:SS' (a naive one read in his zone), as a datetime in his zone; None when not kept"""
    try:
        m = datetime.datetime.fromisoformat(str(at or '').strip().replace('Z', '+00:00'))
    except ValueError:
        return None
    return (m if m.tzinfo else m.replace(tzinfo=_zone())).astimezone(_zone())


def _since_word(at):
    """the original's "since" (shared_work_list.since): its date and clock, Oct 28 10:59"""
    m = _moment(at)
    return m.strftime('%b %d %H:%M') if m else 'time not recorded'


def _clock(at):
    """the original's clock (shared_work_list.clock): today's by its clock alone, an earlier one by its date and clock"""
    m = _moment(at)
    if not m:
        return 'time not recorded'
    return m.strftime('%H:%M') if m.date() == _now().date() else m.strftime('%b %d %H:%M')


def cut(text, most):
    """THE ORIGINAL'S CUT (shared_work_list.cut): whole when it fits, else up to the last whole word within most, with an ellipsis"""
    text = ' '.join(str(text or '').split())
    if len(text) <= most:
        return text
    head = text[:most + 1].rsplit(' ', 1)[0].rstrip(' ,;:.')
    return (head or text[:most]) + '...'


def one(r):
    """A REQUEST IN ONE SHORT LINE, the original's (shared_work_list.one): its id, his words cut at 80, its state since when, its why"""
    words = cut(r.get('words'), 80)
    return (f"{r['id']}" + (f' "{words}"' if words else '') + f" {r.get('state')} since {_since_word(r.get('state_at'))}"
            + (f": {r['why']}" if r.get('why') else ''))


def _hire_of(conf, rid):
    """the worker hired for a request: (its pid, since when) from its tests folder's .day_hire, (None, '') when none"""
    raw = (_bytes(os.path.join(conf['tests'], rid, HIRE_MARK)) or b'').decode(errors='replace').split()
    return (int(raw[0]) if raw and raw[0].isdigit() else None), (raw[1] if len(raw) > 1 else '')


def worker_word(conf, rid):
    """WHETHER A WORKER IS ON IT THIS MOMENT, the original's words: "worker alive since HH:MM", or "no worker now" """
    pid, at_ = _hire_of(conf, rid)
    if pid and _alive(pid):
        if _is_worker(pid, at_) is False:
            return f'no worker now (pid {pid} is another process, its hire mark is stale)'
        return f'worker alive since {_clock(at_)} (pid {pid})'
    return f'no worker now (pid {pid} of a stopped run is gone)' if pid else 'no worker now'


def _is_worker(pid, at_):
    """WHETHER A LIVE HIRE PID TRULY IS ITS WORKER, by ps: a hire's pid is written just after its start, so its process began by the mark's stamp
    and its command names claude; a process begun later, or any other command, took a dead worker's pid. -> True, False, or None when ps did not say"""
    try:
        seen = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'command='], capture_output=True, text=True, errors='replace', timeout=PS_SECONDS, env={**os.environ, 'LC_ALL': 'C'})
    except (OSError, subprocess.SubprocessError):
        return None
    parts = seen.stdout.split(None, 5)   # Sat Oct 31 18:37:19 2026 its command
    if len(parts) < 6:
        return None if _alive(pid) else False
    if not re.search(r'\bclaude\b', parts[5], re.I):
        return False
    hired = _moment(at_)
    try:
        began = datetime.datetime.strptime(' '.join(parts[:5]), '%a %b %d %H:%M:%S %Y').astimezone()
    except ValueError:
        return None
    return began <= hired + datetime.timedelta(seconds=HIRE_GRACE) if hired else True


def _hires(conf):
    """every live .day_hire pid this moment, whatever its request's state: [(request id, pid, _is_worker's answer)]; no folder holds no worker,
    a folder that will not list raises OSError: not measured, never none"""
    try:
        ids = sorted(d for d in os.listdir(conf['tests']) if os.path.isdir(os.path.join(conf['tests'], d)))
    except FileNotFoundError:
        return []
    return [(d, pid, _is_worker(pid, at_)) for d in ids for pid, at_ in [_hire_of(conf, d)] if pid and _alive(pid)]


def _hired_now(conf):
    """every request id with a live worker this moment, for the words of its line and its table"""
    try:
        return [d for d, _pid, seen in _hires(conf) if seen is not False]
    except OSError:
        return []


def _said(r):
    try:
        got = json.loads(r.get('said') or '')
    except (TypeError, ValueError):
        return {}
    return got if isinstance(got, dict) else {}


def _day_jobs(store):
    """THE DAY GROUP'S JOBS ON THIS BOARD: {its name: its job key}"""
    return {str(sh['job'].get('data_full_name') or ''): sh['job_key'] for sh in store.board() if sh.get('slot') == SLOT and sh.get('job') and sh.get('job_key')}


def last_steps(store):
    """WHAT THE DAY LAST SAID OF EACH REQUEST (the original's "turn N of approach M: result", here THE DAY's own runs in LARRYD): for each request
    id named in a DAY step's run line, the newest such line and the step that said it. -> {id: (moment, step name, line)}"""
    out = {}
    for name, key in _day_jobs(store).items():
        for run_ in store.runs(key, 30):
            for ln in _said(run_).get('lines') or ():
                for rid in set(NAMED.findall(str(ln))):
                    if rid not in out or run_['started_at'] >= out[rid][0]:
                        out[rid] = (run_['started_at'], name, str(ln))
    return out


def last_build(store):
    """THE LAST BUILD ONLY (the original's "it only needs to measure the last build"): the newest run of the Build step that worked on a request,
    its length from its start to its end in LARRYD; within 3 minutes is his 3 minute rule met. -> one sentence"""
    try:
        key = _day_jobs(store).get(BUILD)
        if not key:
            return f'the last build: no {BUILD} job on this board'
        for run_ in sorted(store.runs(key, 1000), key=lambda x: x['started_at'], reverse=True):
            named = sorted({rid for ln in _said(run_).get('lines') or () for rid in NAMED.findall(str(ln))})
            t0, t1 = _moment(run_['started_at']), _moment(run_['ended_at'])
            if named and t0 and t1:
                secs = int((t1 - t0).total_seconds())
                return (f"the last build {secs} s ({', '.join(named)}, {BUILD} run {run_['n']}, {t0:%H:%M:%S} to {t1:%H:%M:%S}"
                        + (f' on {t0:%b %d}' if t0.date() != _now().date() else '') + f", {'DONE' if run_['exit'] == 0 else 'FAILED'}): "
                        + ('within 3 min' if secs <= WITHIN else 'OVER 3 min'))
        return 'the last build: no build run yet'
    except Exception as fault:   # noqa: BLE001  (LARRYD not read: said, never a made-up length)
        return f'the last build: not measured ({_line(fault)})'


def in_building(db, conf):
    """EVERY REQUEST IN HAND OR WITH A WORKER ALIVE NOW, read at this look (the original's row 005 look): [request]"""
    rows = requests(db)
    hired = set(_hired_now(conf))
    return [r for r in rows if r['state'] in IN_HAND or r['id'] in hired]


def look(store, db, conf):
    """THE ORIGINAL'S RUN LINE (row 005): each request in hand, its state since when and why, whether a worker is alive on it; then the last
    build; then the ones committed, waiting for tonight's take-in (the B items' place). "nothing in building" when none."""
    rows = in_building(db, conf)
    said = '; '.join(f"{one(r)} · {worker_word(conf, r['id'])}" for r in rows) if rows else 'nothing in building'
    waiting = at(db, READY, COMMITTED)
    return said + ' · ' + last_build(store) + (f" · {len(waiting)} committed, waiting for tonight's take-in: {', '.join(r['id'] for r in waiting)}" if waiting else '')


def red_box(store, job_key):
    """THE ORIGINAL'S RED ROW (scrum.html, the owner 2026-10-12: "if the light is red add a WARNING on a new row stating what the problem is"): while
    its last run ended red, how long it has been red (its clock, from the first run of this red run of runs), when it came in, the Warning with its
    why, and his one step on its own line under it. [] when its last run is green or it never ran."""
    runs = sorted(store.runs(job_key, 1000), key=lambda x: x['started_at'], reverse=True) if job_key else []
    if not runs or runs[0]['exit'] == 0:
        return []
    streak = []
    for run_ in runs:
        if run_['exit'] == 0:
            break
        streak.append(run_)
    came = _moment(streak[-1]['started_at']) or _now()
    said = _said(runs[0])
    why = said.get('why') or str(said.get('summary') or 'its last run ended FAILED').removeprefix('FAILED · ')
    return [{'kind': 'table', 'title': 'Why it is red', 'under': f"Its last {len(streak)} run{'' if len(streak) == 1 else 's'} ended red",
             'columns': ['Red since', 'Came in', 'Warning'],
             'rows': [{'key': 'red', 'cells': [{'text': f'Red since {came:%H:%M}: how long this row has been red', 'since': came.isoformat()},
                                               f'Came in {came:%Y-%m-%d %H:%M}', f'Warning · {why}'],
                       'copy': f"{HAND}{said.get('step') or 'RUN AGENT here'}"}]}]


def _ok(lines, nxt=NEXT):
    return {'ok': True, 'lines': lines, 'why': '', 'step': '', 'next': nxt}


BRANCH = CONF['branch']


def _rebuilt(tree, conf=CONF):
    """HIS ONE COMMAND THAT STANDS THE TREE UP AGAIN"""
    return f"git -C {conf['utility_cwd']} worktree prune && git -C {conf['utility_cwd']} worktree add {tree} {conf.get('branch', BRANCH)}"


def _stood_up(tree, conf=CONF):
    """HIS ONE COMMAND WHEN SOMETHING SITS AT THE TREE'S PATH THAT IS NO WORKING TREE: moved aside whole, never deleted (a worktree add stops on 'already exists'), then the tree stood up again"""
    return f'mv {tree} {tree}.broken-$(date +%Y%m%d%H%M%S) && {_rebuilt(tree, conf)}'


def _no_tree(git, tree, conf=CONF):
    """THE TREE THERE AND ITS HEAD A COMMIT (its blind rule read 2026-10-31). The path gone: his command stands it up. Something at the path: a
    worktree add stops on it, so git's own error is said and it is moved aside first. -> (why, his step), or None"""
    if not os.path.lexists(tree):
        return f'there is no hot fix tree at {tree}: nothing can be seen or put back', f'{_rebuilt(tree, conf)}, then RUN AGENT here'
    if os.path.isdir(tree):
        head = git('rev-parse', '--verify', 'HEAD^{commit}')
        if head.returncode == 0:
            return None
        error = _last(head.stderr)[:160] or f'git exit {head.returncode}'
    else:
        error = 'it is not a folder'
    return f'there is no hot fix tree at {tree}: something is there but its HEAD does not read ({error}): nothing can be seen or put back', f'{_stood_up(tree, conf)} (moved aside, never lost), then RUN AGENT here'


def _undone(tree, db, rid, base):
    """HIS ONE COMMAND WHEN A COMMIT SITS PAST A REQUEST'S BASE: any dirt stashed first (a revert refuses a dirty tree, and it may be his own edit), the commit reverted, the request asked again with its tests unfrozen; its new pick records the new base"""
    return (f"git -C {tree} stash push -u -m day-{rid} && {{ [ -z \"$(git -C {tree} rev-list {base[:12]}..HEAD)\" ] || git -C {tree} revert --no-edit {base[:12]}..HEAD; }}"
            f" && sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\"")


def _kept_aside(tree, db, rid):
    """HIS ONE COMMAND WHEN THE TREE HOLDS WHAT A REQUEST CANNOT CLAIM: stashed, never lost (it may be his own edit), the request asked again"""
    return f"git -C {tree} stash push -u -m day-{rid} && sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


def _no(lines, why, step):
    return {'ok': False, 'lines': lines, 'why': why, 'step': step, 'next': None}


def _unready(git, tree):
    """THE HOT FIX TREE THERE, ON ITS BRANCH AND CLEAN (nobody's half done work is ever committed or put back for them). -> a red, or None"""
    missing = _no_tree(git, tree)
    if missing:
        return _no([], *missing)
    if git('symbolic-ref', '-q', 'HEAD').returncode != 0:
        return _no([], 'the hot fix tree is on no branch (a detached HEAD)', f'git -C {tree} checkout {BRANCH}, then RUN AGENT')
    dirty = _changed(git)
    if dirty:
        return _no([], f"the hot fix tree holds {len(dirty)} file(s) nobody committed: {', '.join(dirty[:4])}", f'git -C {tree} stash push -u -m day-left (kept in the stash, never lost), then RUN AGENT')
    return None


def _since_pick(git, tree, r, info, lines, built, back=False, db=''):
    """WHAT A STEP ON A PICKED REQUEST STANDS ON: its base recorded at its pick on a clean tree, HEAD still at that base (a commit past it is
    never built on), and the tree's change exactly its own recorded files (built), or none (not built yet). -> a red, or None"""
    base = info.get('base')
    if not base or not info.get('clean'):
        return _no(lines, f"{r['id']}: its pick recorded no base", 'RUN AGENT here (it goes back to the backlog), then the day picks it again')
    moved = _moved(git, base)
    if moved:
        return _no(lines, f"{r['id']}: the tree moved past its pick ({_said_commits(moved)}): never built on, never reviewed",
                   f"{_undone(tree, db, r['id'], base)}, then RUN AGENT here")
    mine = set(info.get('files') or ()) if built else set()
    if built and not mine:
        return _no(lines, f"{r['id']}: its built files were never recorded", f"{_kept_aside(tree, db, r['id'])}, then RUN AGENT here")
    dirty = set(_changed(git))
    if (dirty - mine) if back else (dirty != mine):   # back (Building now putting it back): files of it already at its base are no red, so a half put back clears (its rule read 2026-10-28)
        odd = sorted(dirty ^ mine)
        return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) {'changed besides it' if dirty - mine else 'of it gone'}: {', '.join(odd[:4])})",
                   f"{_kept_aside(tree, db, r['id'])} (they may be his own hand edits: the stash keeps them), then RUN AGENT here")
    return None


def _set_aside(db, git, tree, base, r, files, why, step, lines):
    """A RED OF BUILD, PROVE OR REVIEW: its change put back (its own files alone), it stuck today, the day stops here."""
    back, kept = put_back(git, tree, base, files)
    if not set_state(db, r['id'], STUCK, why[:300], when=r['state']):   # A PRESS DURING THE RUN WINS (its blind rule read 2026-10-28): its change put back, its state left as he set it
        lines.append(f"{r['id']}: a press moved it during the run: its state is left as he set it")
    lines.append(f"{r['id']} set aside: stuck today, its {len(back)} changed file(s) put back" + (f", {len(kept)} would not go back: {', '.join(kept[:4])}" if kept else ''))
    return _no(lines, f"{r['id']}: {why}", step)


def _snap(git, side):
    """THE TREE'S GIT AND THE REQUEST'S SIDE FILE before a hire: every local ref (git for-each-ref), HEAD, the ignored files, the side file's bytes"""
    refs = git('for-each-ref', '--format=%(refname) %(objectname)').stdout.splitlines()
    return {'refs': {ln.split(' ', 1)[0]: ln.split(' ', 1)[1] for ln in refs if ' ' in ln and not ln.startswith(('refs/remotes/', 'refs/heads/main '))},
            'head': _head(git), 'sym': git('symbolic-ref', '-q', 'HEAD').stdout.strip(), 'ignored': _ignored(git), 'side': _bytes(side)}


def _hired(git, before, side):
    """WHAT A HIRED WORKER MAY NEVER DO, seen after it ends: move the tree's git (a commit, a branch, a tag, a stash: any ref, any git form),
    write into an ignored file, or touch the request's side file. -> why, the commit named, or ''"""
    after = _snap(git, side)
    if after['head'] != before['head'] or after['sym'] != before['sym'] or after['refs'] != before['refs']:
        named = [f"HEAD {before['head'][:12]} became {after['head'][:12]}"] if after['head'] != before['head'] else []
        for ref in sorted(set(before['refs']) | set(after['refs'])):
            if before['refs'].get(ref) != after['refs'].get(ref) and not (ref == after['sym'] and named):
                named.append(f"{ref} {str(before['refs'].get(ref) or 'none')[:12]} became {str(after['refs'].get(ref) or 'none')[:12]}")
        top = git('log', '-1', '--format=%h "%s"', after['head']).stdout.strip() if after['head'] != before['head'] else ''
        return (f"a hired worker moved the tree's git on its own ({'; '.join(named[:3])}" + (f'; its commit {top}' if top else '')
                + '): that commit is not reviewed and is never built on')
    new = sorted(after['ignored'] - before['ignored'])
    if new:
        return f"a hired worker wrote into ignored file(s) a commit never carries: {', '.join(new[:4])}"
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
        return None, _no(lines, f"{len(rows)} requests are {state} at once: {', '.join(r['id'] for r in rows[:4])}", f"sqlite3 {db} \"UPDATE requests SET state='asked' WHERE state='{state}' AND id<>'{rows[0]['id']}'\", then RUN AGENT")
    return rows[0], None


def step(store, conf, runner, db, hire):
    """THE TREE'S WRITER MARK FIRST, every check under it (its blind rule read 2026-10-28, as Main first and Cleanup): a running hot fix
    utility or another writer is said as itself, never as files nobody committed or a tree that moved"""
    with Writer(conf) as w:
        if w.why:
            return _no([], w.why, _wait_step(w.why))
        return _step(store, conf, runner, db, hire)


def _step(store, conf, runner, db, hire):
    lines = []
    try:
        left = at(db, *IN_HAND)
    except sqlite3.Error as fault:   # R1, the original's: a table that cannot be read is not measured, said first, red
        return _no(lines, f'not measured: the requests cannot be read ({_line(fault)})', _read_step(db, fault))
    tree = conf['tree']
    git = _git(tree, runner)
    missing = _no_tree(git, tree, conf)   # NO TREE IS RED: nothing is put back or set back unseen
    if missing:
        return _no(lines, *missing)
    try:
        hires = _hires(conf)   # WHATEVER ITS REQUEST'S STATE: under the day's lock no live hire is this run's, so every worker is a stopped run's
    except OSError as fault:
        return _no(lines, f"not measured: the requests' tests folder cannot be read ({_line(fault)})", f"ls -ld {conf['tests']} prints what stops the read; chmod u+rwx {conf['tests']}, then RUN AGENT here")
    workers = [(rid, pid) for rid, pid, seen in hires if seen]
    if workers:
        pids = [str(pid) for _rid, pid in workers]
        return _no(lines, '; '.join(f'{rid}: a worker hired by a run that stopped still works on it (pid {pid}: ps shows claude, begun by its hire)' for rid, pid in workers[:4]),
                   f"ps -p {','.join(pids)} -o command= still names claude: kill {' '.join(pids)} (only that pid; kill -9 when ps still names it), then RUN AGENT here")
    for rid, pid, seen in hires:
        if seen is None:   # NOT MEASURED, NEVER PASSED: put back under a live worker's feet, or a kill of what may be another process
            mark = os.path.join(conf['tests'], rid, HIRE_MARK)
            return _no(lines, f"not measured: ps did not say what pid {pid} of {rid}'s hire mark is, a worker or another process",
                       f"ps -p {pid} -o lstart= -o command= names it: claude begun at the stamp in {mark} is the worker, kill {pid}; anything else is not, rm {mark} and leave it running; then RUN AGENT here")
    lines += [f"{rid}: its hire mark's pid {pid} is no worker (ps shows another process, or one begun after its hire): that pid took a dead worker's number, it is left alone" for rid, pid, seen in hires if seen is False]
    if len(left) > 1:
        keep = max(left, key=lambda r: IN_HAND.index(r['state']))   # THE ONE FURTHEST ON stays; the others' ids named, so a press since this read is never overwritten by state
        ids = ', '.join(f"'{r['id']}'" for r in left if r is not keep)
        return _no(lines, f"{len(left)} requests are in hand at once: {', '.join(r['id'] for r in left[:4])}",
                   f"sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id IN ({ids})\" (one request at a time on the tree: this keeps {keep['id']}, furthest on), then RUN AGENT here")
    for r in left:
        info = _side(conf, r)
        landed = _landed(git, r, info)
        if landed:
            if not set_state(db, r['id'], READY, "committed before its run stopped: recorded, ready for tonight's take-in", when=r['state'], commits=landed, done_at=_stamp()):   # A PRESS WINS, said as it is (its rule read 2026-10-28)
                return _no(lines, f"{r['id']}: its commit {landed[:12]} landed but a press moved it off {r['state']}: not recorded", f"sqlite3 {db} \"UPDATE requests SET state='waiting_takein', commits='{landed}' WHERE id='{r['id']}'\", then RUN AGENT here")
            lines.append(f"{r['id']} · its commit {landed[:12]} landed before its run stopped: recorded committed, never built again")
            continue
        back = []
        if not info.get('base'):   # PICKED BEFORE ITS BASE WAS KEPT: back only on a clean tree, its dirt never guessed at
            side = os.path.join(_tests_of(conf, r), SIDE)
            try:   # A SIDE FILE MISSING OR NOT READING IS NOT MEASURED, NEVER A NO-BASE PICK (its rule read 2026-10-31): whether its commit landed cannot be known
                with open(side, encoding='utf-8') as fh:
                    if not isinstance(json.load(fh), dict):
                        raise ValueError('not a JSON object')
            except (OSError, ValueError) as fault:
                return _no(lines, f"not measured: {r['id']}: its side file {side} is missing or does not read ({_line(fault)}), so whether its commit landed cannot be known: never set back unseen",
                           f"git -C {tree} log -1 --format='%H %ce %s' names its commit when it is {DAY_EMAIL} and starts '{r['id']}:': then sqlite3 {db} \"UPDATE requests SET state='waiting_takein', commits='<that sha>' WHERE id='{r['id']}'\", else sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{r['id']}'\"; then RUN AGENT here")
            top = _out(git, 'log', '-1', '--format=%H%x00%ce%x00%s').strip().split('\0', 2)
            if len(top) == 3 and top[1] == DAY_EMAIL and top[2].startswith(f"{r['id']}:"):   # ITS COMMIT ON HEAD with no base to prove it the one past its pick: never set back, never built again
                return _no(lines, f"{r['id']}: its pick recorded no base but HEAD {top[0][:12]} is its day commit \"{top[2][:60]}\": never set back to be built again",
                           f"sqlite3 {db} \"UPDATE requests SET state='waiting_takein', commits='{top[0]}' WHERE id='{r['id']}'\", then RUN AGENT here")
            dirty = _changed(git)
            if dirty:
                return _no(lines, f"{r['id']}: its pick recorded no base and the tree holds {len(dirty)} file(s): {', '.join(dirty[:4])}", f"{_kept_aside(tree, db, r['id'])} (they may be his own hand edits: the stash keeps them), then RUN AGENT here")
        elif not info.get('clean'):   # A BASE WITH NO CLEAN MARK: its tree at the pick is unknown, so nothing is put back here; his hand step, never this same red again
            return _no(lines, f"{r['id']}: its pick recorded a base but no clean mark: what the tree held at its pick is unknown, so nothing is put back here",
                       f"{_kept_aside(tree, db, r['id'])}, then RUN AGENT here")
        else:
            red = _since_pick(git, tree, r, info, lines, built=bool(info.get('files')), back=True, db=db)
            if red:
                return red
            mine = sorted(info.get('files') or ())
            if mine:
                edited = _hand_edited(tree, info, sorted(set(mine) & set(_changed(git))))
                if edited is None:
                    return _no(lines, f"not measured: {r['id']}: its build kept no prints of its files, so a hand edit inside them cannot be seen: nothing is put back here", f"{_kept_aside(tree, db, r['id'])} (they may be his own hand edits: the stash keeps them), then RUN AGENT here")
                if edited:
                    return _no(lines, f"{r['id']}: {len(edited)} of its recorded file(s) are not what its build left: {', '.join(edited[:4])}: hand edits are never put back", f"{_kept_aside(tree, db, r['id'])} (his own hand edits: the stash keeps them), then RUN AGENT here")
                with Writer(conf) as w:
                    if w.why:
                        return _no(lines, f"{r['id']}: {w.why}", _wait_step(w.why))
                    back, kept = put_back(git, tree, info['base'], mine)
                if kept:
                    return _no(lines, f"the tree holds {len(kept)} file(s) that would not go back: {', '.join(kept[:4])}", f"{_kept_aside(tree, db, r['id'])} (they may be his own hand edits: the stash keeps them), then RUN AGENT here")
        if set_state(db, r['id'], WAITING, 'its build stopped with its run: back in the backlog, it starts again', when=r['state'], tests_sha=None):
            lines.append(f"{r['id']} left half built by a run that stopped: back in the backlog, its {len(back)} file(s) put back")
        else:   # A PRESS DURING THE RUN WINS (its rule read 2026-10-28): its files put back, its state left as he set it, said as it is
            lines.append(f"{r['id']} left half built by a run that stopped: its {len(back)} file(s) put back; a press moved it off {r['state']}, so its state is left as he set it")
    if not left:
        dirty = _changed(git)
        if dirty:
            return _no(lines, f"the hot fix tree holds {len(dirty)} file(s) no request recorded: {', '.join(dirty[:4])}", f'git -C {tree} stash push -u -m day-left (they may be his own hand edits, never put back here: the stash keeps them), then RUN AGENT here')
    lines.append(look(store, db, conf))   # THE ORIGINAL'S RUN LINE LAST: what is in building now, the last build, the ones waiting for tonight's take-in
    return _ok(lines)


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS, words never markup (web/page.py content_view), the original's row 005 read fresh at every draw: BUILDING NOW,
    a table of every request in hand or with a worker alive (his words, its state since when and why, what THE DAY last said of it, whether a
    worker is alive on it now), then the last build and the ones committed waiting for tonight's take-in; while its last run is red, the red row (Red
    since, its clock, Came in, Warning, his one step under it). Requests that do not read: not measured, his step."""
    red = red_box(store, job_key)
    try:
        rows, waiting = in_building(store.db_path, CONF), at(store.db_path, READY, COMMITTED)
    except sqlite3.Error as fault:
        return [{'kind': 'note', 'title': 'Building now', 'text': f'not measured: the requests cannot be read ({_line(fault)}) · {HAND}{_read_step(store.db_path, fault)}'}] + red
    said = last_steps(store) if rows else {}
    table = {'kind': 'table', 'title': 'Building now', 'under': 'The request in hand (one at a time on the hot fix tree): its state since when, what the day last said of it, whether a worker is alive on it now',
             'columns': ['Request', 'His words', 'State', 'Its last step', 'Worker'], 'empty': 'nothing in building',
             'rows': [{'key': r['id'], 'cells': [r['id'], cut(r['words'], 80),
                                                f"{r['state']} since {_since_word(r.get('state_at'))}" + (f" ({STAGE[r['state']]})" if r['state'] in STAGE else '') + (f": {r['why']}" if r.get('why') else ''),
                                                (f"{said[r['id']][1]} · {said[r['id']][0][11:16]} · {said[r['id']][2]}" if r['id'] in said else 'no step of the day named it yet'),
                                                worker_word(CONF, r['id'])]} for r in rows]}
    after = {'kind': 'words', 'title': 'The last build', 'under': 'Its length, his 3 minute rule beside it', 'lines': [('body', last_build(store), 'last-build')]
             + [('body', (f"{len(waiting)} committed, waiting for tonight's take-in: {', '.join(r['id'] for r in waiting)}" if waiting else "nothing committed is waiting for tonight's take-in"), 'walk')]}
    return red + [table, after]
