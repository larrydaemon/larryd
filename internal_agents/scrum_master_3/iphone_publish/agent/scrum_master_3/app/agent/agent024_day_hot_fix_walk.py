"""AGENT 019 · HOT FIX WALK (the DAY group, the owner 2026-10-28: "DAY is a group on the top right each should say day / and we should see each /
build each one"; "all of day needs to be rewritten its all hotfix style for the day no judge"): a SUB AGENT of the MARK IV agent (agent001),
lower rank, its own block in the DAY group, its own light and its own run. STEP 9: THE HOT FIX WALK, ONCE FOR THE DAY'S COMMITS (the owner 2026-10-28: "each step should be for rapid development"): THE HOT FIX UTILITY (utilities/build/walk/hotfix.py): both apps built from the tree's commit and walked, a red row fixed and walked again until green, by its own design (it commits its own fixes, and whatever it finds uncommitted). So it runs only on a clean tree, nothing in hand, and nothing on the tree past the day's own commits but THE DAY's merges of main. A busy utility leaves the commits waiting; a red one names them for his hand, never undone here.

THE DAY, STEP BY STEP, each step its own agent (agent011 to agent020; agent021 the backlog): the requests, building now, main first, pick,
build, prove, review, commit (then pick again, one request at a time), the hot fix walk (once for every commit of the day), cleanup. A step
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

KEY = 'hot_fix_walk'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
ROW = 0   # no row of the original: the night's own hot fix utility, once a day run
NAME = 'Hot fix walk'
CARD_NAME = 'Scrum Master Hot fix walk'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Hot fix walk: both apps built and walked once for the day'
WHAT = 'Runs the hot fix utility once for every commit of the day: both apps built from the tree and walked, a red fixed until green'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due (frame_red.due_at)
ROW_FILE = 'agent019_day_hot_fix_walk.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes: in its own thread, the page answers RUN AGENT at once
NEXT = 'cleanup'   # the step it hands on to when it ends green

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
    """git in the tree, every path taken as typed (--literal-pathspecs: a file named with * or ? is that file alone), its bytes kept whole"""
    def git(*args):
        return runner(['git', '--literal-pathspecs', *args], cwd=tree, capture_output=True, text=True, errors='surrogateescape')
    return git


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


def _ignored(git):
    return {p for code, p in _status(git, '--untracked-files=all', '--ignored') if code == '!!' and not _cache(p)}


def _head(git):
    return git('rev-parse', 'HEAD').stdout.strip()


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
    out = git('log', '--format=%H%x00%ce%x00%P%x00%s', f'{base}..HEAD').stdout
    return [tuple(ln.split('\0', 3)) for ln in out.splitlines() if ln.count('\0') >= 3]


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
    olds = [f for f in files if git('cat-file', '-e', f'{base}:{f}').returncode == 0]
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
        return [dict(zip(('id', 'words', 'state', 'position', 'tests', 'tests_sha', 'commits', 'why', 'done_at', 'state_at'), r))
                for r in con.execute('SELECT id, words, state, position, tests, tests_sha, commits, why, done_at, state_at FROM requests ORDER BY position, id')]
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
    this step writes its own end. -> ((its module, its shell, its run), '') or (None, why it was not taken)"""
    nxt = next(((m, sh) for m, sh in (chain or ()) if getattr(m, 'KEY', '') == key), None)
    if nxt is None:
        return None, f'it is not in the chain this run was handed ({key})'
    if not hasattr(store, 'run'):
        return None, 'this store takes no RUN'
    module, sh = nxt
    try:
        job = next((x['job'] for x in store.board() if x['id'] == sh['id']), None) or {}
        ok, text = store.run(sh['id'])
    except Exception as fault:   # noqa: BLE001
        return None, f'its RUN was not taken ({_line(fault)})'
    if not ok:
        return None, f'its RUN was refused ({text})'
    m = re.search(r'RUN (\d+)', str(text))
    n = int(m.group(1)) if m else int(job.get('data_job_run') or 0) + 1
    return (module, sh, n), ''


def _crashed(fault):
    """ITS OWN CODE CRASHED: red, named as a crash, its file and line its step (its blind rule read 2026-10-28; as agent011)"""
    where = _where(fault)
    return {'ok': False, 'lines': [], 'why': f'it crashed at {where} ({_line(fault)})', 'step': f'open app/agent/{where}, fix what the crash names, then RUN AGENT', 'next': None}


def _fault(fault, conf, db):
    """A STEP THAT BROKE: what did not read (the requests, the tree) is 'not measured', said first with its file and line, and his step is that
    read's, no code to edit (its blind rule read 2026-10-31); anything else is its own crash. -> its red"""
    tree = conf['tree']
    if isinstance(fault, sqlite3.Error):
        return _no([], f'not measured: the requests cannot be read or written ({_line(fault)}) at {_where(fault)}', f"sqlite3 {db} 'SELECT count(*) FROM requests' prints the error it met; clear it, then RUN AGENT here")
    if isinstance(fault, NotMeasured):
        return _no([], f'{fault} at {_where(fault)}', f'git -C {tree} status --porcelain prints the error it met; when it still fails, {_tree_step(tree)}, then RUN AGENT here')
    return _crashed(fault)


def once(store, job_key, n, agent, chain, conf, runner, hire, db, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step); green, the next step's RUN taken first: a next refused or
    missing ends this one FAILED, said. A crash ends FAILED with its line. -> (what it said, the next to run (module, shell, run) or None)"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not locked:
        got = _no([], 'another DAY step is running', f'lsof {_lock_path(conf)} prints the pid N that holds the lock, ps -p N -o command= names that run: let it end (its block says RUNNING), then RUN AGENT here')
    else:
        try:
            with Beat(store, job_key):
                got = step(store, conf, runner, db, hire)
        except Exception as fault:   # A CRASH IS RED, NAMED WHERE IT HAPPENED: its own file and line (its blind rule read 2026-10-28)
            got = _fault(fault, conf, db)
    nxt = None
    if got['ok'] and got.get('next'):
        nxt, why = hand_on(store, chain, got['next'])
        if nxt is None:
            name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or got['next']
            got = {**got, 'ok': False, 'why': f'the day stopped before {name}: {why}', 'step': f'RUN AGENT on {name}: it takes its own RUN', 'next': None}
    said = {'summary': ('DONE · ' if got['ok'] else f"FAILED · {got['why']} · {HAND}{got['step']} · ") + ' | '.join(got['lines'][-3:]), **got}
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


def _runs(store, job_key):
    """its own runs in LARRYD, newest first ([] when the store does not read)"""
    try:
        return sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)
    except Exception:   # noqa: BLE001  (a store that does not read draws no warning; the head's light is the job's own)
        return []


def _said_of(r):
    try:
        s = json.loads(r.get('said') or '')
    except (TypeError, ValueError):
        return {}
    return s if isinstance(s, dict) else {}


def _local(stamp):
    """a run's start as LARRYD keeps it (this laptop's time, no zone), with its zone. -> aware datetime, or None"""
    try:
        t = datetime.datetime.fromisoformat(str(stamp or '')[:19])
    except ValueError:
        return None
    return t.astimezone() if t.tzinfo is None else t


def red_now(store, job_key):
    """THE ROW'S RED, as the original draws it under a red row: its newest run FAILED. since: the start of the first run of the unbroken
    FAILED runs ending with the newest (the original's "Red since": how long this row has been red). -> {'why', 'step', 'since'} or None"""
    runs = _runs(store, job_key)
    if not runs or runs[0].get('exit') == 0:
        return None
    first = runs[0]
    for r in runs:
        if r.get('exit') == 0:
            break
        first = r
    s = _said_of(runs[0])
    why = s.get('why') or re.sub(r'^FAILED · ', '', str(s.get('summary') or runs[0].get('said') or 'its run ended red'))
    return {'why': str(why), 'step': str(s.get('step') or ('' if HAND in str(why) else 'RUN AGENT here')), 'since': _local(first.get('started_at'))}


def warning(store, job_key):
    """THE ORIGINAL'S WARNING ROW of a red row: its clock (Red since HH:MM: how long this row has been red, ticking), when it came in, Warning ·
    the why, and his one step on its own line under the row (YOUR 3 MIN: ...). -> [the part] or [] when the row is not red"""
    red = red_now(store, job_key)
    if red is None:
        return []
    at = red['since']
    clock = ({'text': f"Red since {at:%H:%M}: how long this row has been red", 'since': at.isoformat(timespec='seconds')} if at
             else 'Red since: its first red run has no time on file')
    row = {'key': 'red', 'cells': [clock, f"Came in {at:%Y-%m-%d %H:%M}" if at else 'Came in: not on file', f"Warning · {red['why']}"]}
    if red['step']:
        row['copy'] = f"{HAND}{red['step']}"
    return [{'kind': 'table', 'title': 'Warning', 'columns': ['Red since', 'Came in', 'Warning'], 'rows': [row], 'empty': ''}]


def _ago(at, now=None):
    """how long ago, said short: 'just now', '5 min ago', '3 h ago', '2 days ago'"""
    if at is None:
        return ''
    s = max(0, int(((now or datetime.datetime.now().astimezone()) - at).total_seconds()))
    return 'just now' if s < 60 else f'{s // 60} min ago' if s < 3600 else f'{s // 3600} h ago' if s < 172800 else f'{s // 86400} days ago'


def _words(r, most=120):
    return ' '.join(str(r.get('words') or '').split())[:most]


def _reader(tree):
    """git in the tree for a look on the page: read only, never its index refreshed (GIT_OPTIONAL_LOCKS=0: no index.lock taken while the
    utility or a step writes the tree)"""
    return _git(tree, lambda cmd, **kw: subprocess.run(cmd, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}, **kw))


def _not_read(e):
    return [{'kind': 'note', 'title': 'The requests', 'text': f"The requests do not read ({_line(e)}). {HAND}see why (seconds): sqlite3 ~/larryd/server/runtime/internal/instance/data/scrum_master_3/scrum_master_3.db 'SELECT count(*) FROM requests'"}]


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


def _asked_again(db, rid):
    """HIS ONE COMMAND WHEN A COMMITTED REQUEST'S CHANGE IS NOT ON THE TREE: asked again with its tests unfrozen, Pick and Build take it anew"""
    return f"sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


def _undone(tree, db, rid, base):
    """HIS ONE COMMAND WHEN A COMMIT SITS PAST A REQUEST'S BASE: reverted, the request asked again with its tests unfrozen; its new pick records the new base"""
    return f"[ -z \"$(git -C {tree} rev-list {base[:12]}..HEAD)\" ] || git -C {tree} revert --no-edit {base[:12]}..HEAD; sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


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


def _since_pick(git, tree, r, info, lines, built, db=''):
    """WHAT A STEP ON A PICKED REQUEST STANDS ON: its base recorded at its pick on a clean tree, HEAD still at that base (a commit past it is
    never built on), and the tree's change exactly its own recorded files (built), or none (not built yet). -> a red, or None"""
    base = info.get('base')
    if not base or not info.get('clean'):
        return _no(lines, f"{r['id']}: its pick recorded no base", 'RUN AGENT on Building now (it goes back to the backlog), then the day picks it again')
    moved = _moved(git, base)
    if moved:
        return _no(lines, f"{r['id']}: the tree moved past its pick ({_said_commits(moved)}): never built on, never reviewed",
                   f"{_undone(tree, db, r['id'], base)}, then RUN AGENT on Pick")
    mine = set(info.get('files') or ()) if built else set()
    if built and not mine:
        return _no(lines, f"{r['id']}: its built files were never recorded", f"{_kept_aside(tree, db, r['id'])}, then RUN AGENT on Pick")
    dirty = set(_changed(git))
    if dirty != mine:
        odd = sorted(dirty ^ mine)
        return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) {'changed besides it' if dirty - mine else 'of it gone'}: {', '.join(odd[:4])})",
                   f"{_kept_aside(tree, db, r['id'])} (they may be his own hand edits: the stash keeps them), then RUN AGENT on Pick")
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

UTILITY_FIX = 'Hot fix: the '   # the subject of the hot fix utility's own commit of its fixes (hotfix.py one: "Hot fix: the <target> walk's red rows green ...")
WALK_MINUTES = '101 to 171 minutes for both apps (the utility, 3 nights to 2026-10-31)'
WALKED = ('iphone', 'macos')   # THE TWO APPS EVERY WALK MUST NAME READY (hotfix.py TARGETS, its default when run with no target)
TARGET_LINE = re.compile(r'\b(IPHONE|MACOS) · ([A-Z][A-Z ]*?) · (.*)$', re.M)   # the utility's verdict of each target (hotfix.py main: "IPHONE · READY · <why>")
REPORT_LINE = re.compile(r'THE REPORT · (\S.*?)\s*$', re.M)   # the utility's report (hotfix.py main: "THE REPORT · <its HOTFIX_RUN.md>")
REPORT_TARGET = re.compile(r'^## (iphone|macos): .*$', re.M)   # a target's part of the report (hotfix.py report: "## iphone: READY")
REPORT_KEPT = re.compile(r'^- The build kept: ([0-9a-f]+)', re.M)   # the commit that target's build was walked at
REPORT_PIXEL = re.compile(r'^- PIXEL COMPARE: (GREEN|RED|NOT RUN)', re.M)   # READY names the walk alone: the Mac's pixel compare has its own line


def _unreviewed(git, tree, db, built):
    """WHAT THE TREE HOLDS THAT NO REVIEW READ: every committed request's commit on the tree, and from the oldest of them on nothing but those commits, THE DAY's own
    merges of main and the hot fix utility's own commits of its fixes (a walk that was not READY may leave them: the next walk walks them
    again). Each red's step is the one that clears that red: a revert clears a commit on the tree, never a request's record. -> a red, or None"""
    shas = [str(r.get('commits') or '') for r in built]
    for r, s in zip(built, shas):
        if not s:
            return _no([], f"{r['id']} is committed with no commit recorded: the walk would carry it",
                       f"git -C {tree} log --format='%H %s' --grep='^{r['id']}:' names its commit: sqlite3 {db} \"UPDATE requests SET commits='<its sha>' WHERE id='{r['id']}'\"; when it names none, {_asked_again(db, r['id'])}; then RUN AGENT here")
        if git('merge-base', '--is-ancestor', s, 'HEAD').returncode != 0:
            return _no([], f"{r['id']}'s commit {s[:12]} is not on the tree: the walk would not carry it", f"{_asked_again(db, r['id'])}, then RUN AGENT here")
    oldest = max(shas, key=lambda s: int(git('rev-list', '--count', f'{s}..HEAD').stdout.strip() or 0))   # FROM THE OLDEST, not the newest (its rule read 2026-10-28): a hand commit between two requests' commits is caught too
    seen = git('log', '--first-parent', '--format=%H%x00%ce%x00%P%x00%s', f'{oldest}..HEAD')
    if seen.returncode != 0:   # a log that did not read is never a tree with nothing unreviewed
        raise NotMeasured(f'not measured: git log failed ({_last(seen.stderr)[:120]})')
    after = [tuple(ln.split('\0', 3)) for ln in seen.stdout.splitlines() if ln.count('\0') >= 3]
    full = {git('rev-parse', s).stdout.strip() for s in shas}
    plain = lambda m: m[0] not in full and not (m[1] == DAY_EMAIL and len(m[2].split()) > 1) and not m[3].startswith(UTILITY_FIX)
    subjects = {m[3] for m in after}
    subject_of = {git('log', '-1', '--format=%s', s).stdout.strip(): r['id'] for r, s in zip(built, shas)}
    taken_back = [m for m in after if m[3].startswith('Revert "') and m[3][8:-1] in subject_of]
    if taken_back:   # A REQUEST'S OWN COMMIT REVERTED IS NOT WALKED READY: its change is off the tree
        return _no([], f"the tree reverts a request's commit ({taken_back[0][3][:80]}): it is not on the tree", f"{_asked_again(db, subject_of[taken_back[0][3][8:-1]])}, then RUN AGENT here")
    pair = lambda m: (m[3].startswith('Revert "') and m[3][8:-1] in subjects) or f'Revert "{m[3]}"' in subjects   # an odd commit and its own revert cancel out: his step takes one out this way, nothing else does
    odd = [m for m in after if plain(m) and not pair(m)]
    if not odd:
        return None
    return _no([], f"the tree holds {len(odd)} commit(s) no review read: {_said_commits(odd)}: the walk would carry it",
               ' && '.join(f"git -C {tree} revert{' -m 1' if len(m[2].split()) > 1 else ''} --no-edit {m[0][:12]}" for m in odd) + ', then RUN AGENT here')


def _walk_said(walked):
    """what the utility said of its walk: [(target, verdict, why)] and its report's path ('' when it named none)"""
    targets = [(m.group(1).lower(), m.group(2).strip(), m.group(3).strip()[:200]) for m in TARGET_LINE.finditer(walked or '')]
    rep = REPORT_LINE.findall(walked or '')
    return targets, (rep[-1] if rep else '')


def _report_said(report):
    """what the utility's report keeps of each target: {target: (the commit its build was walked at, its pixel compare)}; {} when it does not read"""
    try:
        text = _read(report)
    except (OSError, TypeError):
        return {}
    parts = list(REPORT_TARGET.finditer(text))
    said = {}
    for m, nxt in zip(parts, [*parts[1:], None]):
        part = text[m.end():nxt.start() if nxt else len(text)]
        kept, pixel = REPORT_KEPT.search(part), REPORT_PIXEL.search(part)
        said[m.group(1)] = (kept.group(1) if kept else '', pixel.group(1) if pixel else '')
    return said


def _proven(targets, report, before, after, done):
    """THE APPS PROVEN READY AT THE FINAL HEAD, every path one rule: a READY said with its pixel compare RED or NOT RUN proves nothing. The tree
    still at its start: each app READY here, with the ones kept READY at it. The tree moved by a fix commit: an app walked before that commit
    is not proven at the new one, so only the last app walked (it ended at the final HEAD, the utility walks whole after its own commit), or
    an app whose report names its build at the final HEAD; READY kept at the old commit proves nothing. -> {target}"""
    if not after:
        return set()
    said = _report_said(report)
    ready = {t for t, v, _w in targets if v == 'READY' and said.get(t, ('', ''))[1] not in ('RED', 'NOT RUN')}
    if after == before:
        return ready | set(done)
    last = targets[-1][0] if targets else ''
    return {t for t in ready if t == last or (said.get(t, ('', ''))[0] and after.startswith(said[t][0]))}


def _wait_step(conf):
    """HIS STEP WHILE ANOTHER RUN HOLDS THE TREE: that run's own pid, to look at"""
    pid = _pid_in(conf['utility_lock']) or _pid_in(conf['writer'])
    return (f'ps -p {pid} -o command= names that run: let it end' if pid else 'wait for that run to end') + ', then RUN AGENT here: it walks them'


def step(store, conf, runner, db, hire):
    """THE DAY'S ONE WALK, PUBLISHED OR NOT (the original's row 031 ECHO: green or red, nothing more): every committed request walked by the
    hot fix utility in one run; READY turns each READY (waiting for the take-in), its walk recorded; a walk not READY is red and its requests
    stay committed (approved), so the next RUN AGENT walks them again and only a READY walk turns it green (never a green on nothing to walk
    while they sit on the tree unwalked). Nothing committed is green only past the same checks: in hand or a bad tree is red there too."""
    with Writer(conf) as w:   # THE TREE'S WRITER MARK FIRST, every check under it (its blind rule read 2026-10-28); let go before the
        if w.why:              # utility starts, since the utility itself waits while any live pid holds the mark
            return _no([], w.why, _wait_step(conf))
        built = at(db, COMMITTED)
        red, git = _walkable(conf, runner, db, built)
        if red:
            return red
    if not built:
        return _ok(['9 hot fix walk · nothing committed to walk'])
    tree = conf['tree']
    ids = [r['id'] for r in built]
    shas = ' '.join(str(r.get('commits') or '')[:12] for r in built)
    branch = git('symbolic-ref', '-q', '--short', 'HEAD').stdout.strip() or 'no branch'
    before, began = _head(git), _now()
    done = _ready_at(conf, before)   # ONE PIECE AT A TIME: an app already READY at this very commit is not walked again (his step runs the failed piece alone)
    wanted = [t for t in WALKED if t not in done]
    try:
        walk = runner([*conf['utility'], *wanted], cwd=conf['utility_cwd'], capture_output=True, text=True, timeout=conf['utility_seconds'], env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        code, walked = walk.returncode, (walk.stdout or '') + (walk.stderr or '')
    except (subprocess.TimeoutExpired, OSError) as e:
        code, walked = 1, f'{type(e).__name__}: {e}'
    if code == 2:
        return _no([], f'a run of the hot fix utility is going already: {len(built)} commit(s) wait for the next walk', _wait_step(conf))
    targets, report = _walk_said(walked)
    after = _head(git)
    when = f"the walk of {began:%b %d %H:%M}"
    said_targets = ', '.join(f'{t} {v}' for t, v, _w in targets) or 'no target said'
    record = {'at': began.isoformat(timespec='seconds'), 'minutes': int((_now() - began).total_seconds() // 60), 'apps': wanted or list(WALKED), 'code': code, 'ready': code == 0, 'branch': branch, 'from': before, 'to': after,
              'targets': [list(t) for t in targets], 'report': report, 'requests': ids, 'last': _last(walked)[:200]}
    missing = [t for t in (wanted or WALKED) if t not in {t_ for t_, _v, _w in targets}]   # no target wanted: the utility walks both, so both must be named
    proven = _proven(targets, report, before, after, done)
    _keep_ready(conf, after, proven)
    if code == 0 and (missing or any(v != 'READY' for _t, v, _w in targets)):   # an exit 0 is not READY on its own: both apps must be named, each READY (its third rule read 2026-10-28)
        code = 1
        record['code'], record['ready'] = 1, False
        walked += f"\nthe utility ended 0 but named no verdict for {', '.join(t.upper() for t in missing)}" if missing else '\nthe utility ended 0 but did not say READY for every target'
    stale = [t for t in WALKED if t not in proven]
    if code == 0 and stale:   # A FIX COMMIT MOVED THE TREE: the app READY before it is not READY at the new commit, on one app's walk or both (its blind rule read 2026-10-31)
        code = 1
        record['code'], record['ready'] = 1, False
        walked += f"\nthe tree moved to {after[:12]}: {', '.join(t.upper() for t in stale)} not proven walked at it"
    if code != 0:
        bad = '; '.join(f'{t} {v}: {w}' for t, v, w in targets if v != 'READY') or _last(walked)[:200] or f'it ended {code}'
        got = _no([f"not READY: {when}: {said_targets} on {branch} · commit {after[:12]} · {len(built)} request(s) wait: {', '.join(ids)}"],
                  f"not READY: {when}: {bad}",
                  (f"read its report ({report}) and clear what it names, " if report else "read the hot fix utility's last lines (this row's run), clear what they name, ")
                  + f"then RUN AGENT here: it walks only what is not READY yet ({', '.join(stale)}; {WALK_MINUTES} measured, one app alone not measured, this run's minutes are on its walk; a clean fix build keeps its folder), the {len(built)} commit(s) stay on the tree ({shas}); revert one only if it must not ship (git -C {tree} revert <sha>)")
        return {**got, 'walk': record}
    moved = [r['id'] for r in built if not set_state(db, r['id'], READY, 'built, proven, reviewed, committed and walked READY by THE DAY', when=COMMITTED, done_at=_stamp())]
    said = [f"walked READY: {when}: {said_targets} on {branch} · commit {after[:12]} · {len(built)} request(s): {', '.join(ids)}"]
    if moved:   # A PRESS DURING THE WALK WINS, said as it is (its rule read 2026-10-28): never a green line that claims them ready
        return {**_no(said, f"walked READY, but a press moved {', '.join(moved)} off approved during the walk: not made ready",
                      f"see their state (sqlite3 {db} \"SELECT id, state FROM requests WHERE id IN ({', '.join(repr(m) for m in moved)})\"); set them to waiting_takein by hand if they must ship, then RUN AGENT on Cleanup"), 'walk': record}
    return {**_ok(said), 'walk': record}


def _ready_at(conf, head):
    """the apps already READY at this commit (a walk not READY keeps what it proved, for this commit alone) -> {target}"""
    try:
        with open(os.path.join(conf['tests'], '.walk_ready.json'), encoding='utf-8') as fh:
            kept = json.load(fh)
    except (OSError, ValueError):
        return set()
    return set(kept.get('targets') or ()) & set(WALKED) if kept.get('head') == head else set()


def _keep_ready(conf, head, targets):
    """the apps READY at this commit, kept for the next RUN AGENT"""
    os.makedirs(conf['tests'], exist_ok=True)
    with open(os.path.join(conf['tests'], '.walk_ready.json'), 'w', encoding='utf-8') as fh:
        json.dump({'head': head, 'targets': sorted(targets)}, fh)


def _no_tree(git, tree):
    """THE TREE THERE AND ITS HEAD A COMMIT, read before anything else on it: not measured, said first. The path gone: his command stands it up.
    Something at the path: a worktree add stops on it, so git's own error is said and it is moved aside first. -> a red, or None"""
    if not os.path.lexists(tree):
        return _no([], f'not measured: there is no hot fix tree at {tree}: its commits cannot be walked', f'{_tree_step(tree)}, then RUN AGENT here')
    if os.path.isdir(tree):
        head = git('rev-parse', '--verify', 'HEAD^{commit}')
        if head.returncode == 0:
            return None
        error = _last(head.stderr)[:160] or f'git exit {head.returncode}'
    else:
        error = 'it is not a folder'
    return _no([], f'not measured: {tree} is there but its HEAD does not read ({error})', f'tell him that error, or {_tree_step(tree)}, then RUN AGENT here')


def _walkable(conf, runner, db, built):
    """THE TREE READY TO WALK, read under the writer mark: no request in hand, the tree there and readable, nothing uncommitted, no commit
    no review read (with nothing committed, no commit to read from). -> (red or None, git)"""
    hand = at(db, *IN_HAND)
    if hand:
        return _no([], f"{hand[0]['id']} is {hand[0]['state']}: the walk never runs with a request in hand (the utility commits whatever it finds uncommitted)", 'RUN AGENT on Building now, then the day goes on'), None
    tree = conf['tree']
    git = _git(tree, runner)
    red = _no_tree(git, tree)
    if red:
        return red, None
    dirty = _changed(git)
    if dirty:
        return _no([], f"the tree holds {len(dirty)} file(s) nobody committed: {', '.join(dirty[:4])}: the utility would commit them unreviewed", f'git -C {tree} stash push -u -m day-left (kept in the stash, never lost), then RUN AGENT'), None
    return (_unreviewed(git, tree, db, built) if built else None), git


def last_walk(store, job_key):
    """its newest run that walked (its said holds the walk): {'at', 'code', 'ready', 'branch', 'from', 'to', 'targets', 'report', 'requests'} or None"""
    for r in _runs(store, job_key):
        w = _said_of(r).get('walk')
        if isinstance(w, dict):
            return w
    return None


def content(store, job_key, block=None):
    """ITS BLOCK, IN THE STYLE OF THE ORIGINAL'S ROW 031 ECHO (published or not, green or red, nothing more): the warning row while its newest
    run is red (the clock, Warning ·, his step under it); the commits waiting for the day's one walk, each found on the tree or not; then the
    last walk, READY or not, its targets, the tree it walked from and to, and its report (the original's View full page: its path, to open)."""
    try:
        built = at(store.db_path, COMMITTED)
    except sqlite3.Error as e:
        return warning(store, job_key) + _not_read(e)
    git = _reader(CONF['tree'])
    there = os.path.isdir(CONF['tree']) and git('rev-parse', '--verify', '-q', 'HEAD^{commit}').returncode == 0

    def on_tree(sha):
        if not sha:
            return 'no commit recorded'
        if not there:
            return 'no hot fix tree to look in'
        return 'yes' if git('merge-base', '--is-ancestor', sha, 'HEAD').returncode == 0 else 'no: not on the tree'
    waiting = [{'key': r['id'], 'cells': [r['id'], _words(r), str(r.get('commits') or '')[:12] or 'NONE', on_tree(str(r.get('commits') or '').strip())]} for r in built]
    w = last_walk(store, job_key)
    walks = []
    if w:
        at_ = _local(w.get('at'))
        walk_row = {'key': 'walk', 'cells': [f"{at_:%b %d %H:%M}, {_ago(at_)}" if at_ else str(w.get('at')), 'READY' if w.get('ready') else 'not READY',
                                              '; '.join(f'{t} {v}' + (f': {why}' if v != 'READY' and why else '') for t, v, why in (w.get('targets') or ())) or str(w.get('last') or 'no target said'),
                                              f"{w.get('branch')} {str(w.get('from') or '')[:12]} to {str(w.get('to') or '')[:12]}", ', '.join(w.get('requests') or ()) or 'none']}
        if w.get('report'):
            walk_row['copy'] = f"open {w['report']}"
        walks.append(walk_row)
    return warning(store, job_key) + [
        {'kind': 'table', 'title': 'Waiting for the walk', 'under': f"{len(built)} commit(s) for the day's one walk: both apps built from the tree and walked, no Judge" if built else 'nothing committed to walk',
         'columns': ['Request', 'His words', 'Commit', 'On the tree'], 'rows': waiting, 'empty': 'Nothing to walk now.'},
        {'kind': 'table', 'title': 'The last walk', 'under': 'READY or not: the hot fix utility, once for the day, its report under it',
         'columns': ['Walked', 'Verdict', 'Targets', 'The tree', 'Requests'], 'rows': walks, 'empty': 'no walk on file: it walks once a request is committed'}]
