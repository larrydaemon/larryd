"""AGENT 015 · BUILD (the DAY group, the owner 2026-10-28: "DAY is a group on the top right each should say day / and we should see each /
build each one"; "all of day needs to be rewritten its all hotfix style for the day no judge"): a SUB AGENT of the MARK IV agent (agent001),
lower rank, its own block in the DAY group, its own light and its own run. STEP 5: BUILD (the original's 012: "the build went to the end or not"): on the tree still clean at its pick's base, holding the tree's writer mark, a Claude Code test writer writes the picked request's tests (they must fail on the tree as it is, or they prove nothing), frozen by their sha256; then a Claude Code developer (denied every git form, every write outside the tree, its frozen tests too) builds it on the hot fix tree, its changed files recorded. A worker that moves the tree's git (a commit: named, never built on), writes, edits or removes an ignored file or touches the side file is caught. A red puts its own change back and sets it aside, stuck today.

THE DAY, STEP BY STEP, each step its own agent (agent011 to agent020; agent021 the backlog): the requests, building now, main first, pick,
build, prove, review, commit (then pick again, one request at a time), the hot fix walk (once for every commit of the day), cleanup. A step
that ends green takes the next step's RUN before it writes its own DONE, and the first run drives the next ones in a loop (the chain the page
hands every run: no agent imports another), so RUN AGENT on THE REQUESTS runs the whole day block by block, and RUN AGENT on any step runs the
day from there. A red step stops there: it is THE RED's, its one step said. ONE DAY AT A TIME: one lock for the whole day, a second press ends
red. ON THE HOT FIX TREE (~/spine_worktrees/hotfix), NO JUDGE, NO SEAL, NO PUBLISH: production takes a change only by his AI ECHO HOTFIX
button, never pressed here. Its requests are this office's own (nothing read from the original). ON RUN AGENT ONLY: never due.

ITS BLOCK, THE ORIGINAL'S ROW 012 (content): Building now (each request picked or built, his words, since when, where its build stands), WHY
IT'S RED while its newest run is red (red since, ticking; came in; the warning; his one step on the line under), Builds that did not go to
the end (each request it set aside, stuck today, his line and its BACK TO ASKED press); its run line the original's list (report)."""
import datetime
import fcntl
import hashlib
import inspect
import json
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import threading
import time
import traceback
import zoneinfo

KEY = 'build'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
ROW = 12   # the original's row 012
NAME = 'Build'
CARD_NAME = 'Scrum Master Build'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Build: tests first, then the request built on the hot fix tree'
WHAT = 'Has its tests written and failing first, freezes them, then has the request built on the hot fix tree'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due (frame_red.due_at)
ROW_FILE = 'agent015_day_build.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes: in its own thread, the page answers RUN AGENT at once
NEXT = 'prove'   # the step it hands on to when it ends green
PRESSES = ('back',)   # its own button on each request it set aside: BACK TO ASKED (his hand line, pressed; the page's agent_press route runs press for these alone)
ASIDE_TITLE, ASIDE_EMPTY = 'Builds that did not go to the end', 'No build failed: nothing Build set aside is stuck today.'

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
SIDE, HIRE_MARK, WORDS_MARK = '.day_base', '.day_hire', '.day_words'   # A REQUEST'S SIDE FILES in its tests folder (~/scratch/tests/day/<id>, outside the tree: no commit carries them, never a test, never in its tests' sha): its pick's base and its proof; the pid of the worker hired for it now; the sha of the words its tests were frozen for (a pick keeps it)
BUILT_MARK = '.day_built_'   # ITS BASE, FILES AND THEIR PRINTS AGAIN, beside its tests folder: Prove reads it when that folder is gone
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


def _ignored(git, tree):
    """THE TREE'S IGNORED FILES, each with its fingerprint: no commit carries them, so their bytes are the only record that a worker edited one. SQLite's
    own working files are left out, for a plain read moves them and they hold no row: a -shm index, an empty -wal. A -wal with rows in it is compared, as is
    the .db. -> {path: fingerprint}"""
    held = [p for code, p in _status(git, '--untracked-files=all', '--ignored') if code == '!!' and not _cache(p)]
    return {p: _print(os.path.join(tree, p)) for p in held if not p.endswith('-shm') and not (p.endswith('-wal') and not (_bytes(os.path.join(tree, p)) or b''))}


def _head(git):
    return git('rev-parse', 'HEAD').stdout.strip()


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


def _prints(tree, files):
    """EACH BUILT FILE'S OWN sha256 as its build left it (None: its build removed it): {file: sha}"""
    held = {f: _bytes(os.path.join(tree, f)) for f in files}
    return {f: hashlib.sha256(b).hexdigest() if b is not None else None for f, b in held.items()}


def _keep_built(conf, r, base, files, prints):
    """ITS BASE, BUILT FILES AND THEIR PRINTS ALSO KEPT BESIDE ITS TESTS FOLDER (<tests>/.day_built_<id>, JSON): a folder gone with its side file still names what Prove puts back, each file as its build left it"""
    path = os.path.join(conf['tests'], f"{BUILT_MARK}{r['id']}")
    with open(path + '.tmp', 'w', encoding='utf-8') as fh:
        json.dump({'base': base, 'clean': True, 'files': files, 'prints': prints}, fh, sort_keys=True)
    os.replace(path + '.tmp', path)


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
    if seen.returncode != 0:   # a log that did not read is never a tree still at its base
        raise NotMeasured(f'not measured: git log failed ({_last(seen.stderr)[:120]})')
    return [tuple(ln.split('\0', 3)) for ln in seen.stdout.splitlines() if ln.count('\0') >= 3]


def _at_base(git, base):
    """HEAD and a request's base compared, commit to commit (_moved lists only what sits past the base, so a HEAD reset behind it reads as nothing moved). -> (HEAD's sha, it is the base)"""
    head, at_ = git('rev-parse', '--verify', 'HEAD^{commit}'), git('rev-parse', '--verify', f'{base}^{{commit}}')
    if head.returncode != 0 or at_.returncode != 0:   # a commit that did not read is never a tree at its base
        raise NotMeasured(f'not measured: HEAD or its base did not read ({_last(head.stderr or at_.stderr)[:120]})')
    return head.stdout.strip(), head.stdout.strip() == at_.stdout.strip()


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
               f"ps -axo pid,etime,command | grep '[g]it ' names any git left running: let it end; with none left, rm -f {lock}, and when git -C {tree} status --porcelain answers at once, RUN AGENT here")


def _fault(fault, conf, db):
    """A STEP THAT BROKE: what did not read (the requests, the tree) is 'not measured', said first with its file and line, and his step is that
    read's, no code to edit (its blind rule read 2026-10-31); a git that hung the same (its tests' own clock is caught where they run); anything
    else is its own crash. -> its red"""
    tree = conf['tree']
    if isinstance(fault, subprocess.TimeoutExpired):   # A HUNG GIT ENDS THE RUN RED, with what clears it: never RUNNING forever under its own heartbeat
        return _hung(tree, fault)
    if isinstance(fault, sqlite3.Error):
        return _no([], f'not measured: the requests cannot be read or written ({_line(fault)}) at {_where(fault)}', _read_step(db, fault))
    if isinstance(fault, (FileNotFoundError, NotADirectoryError)) and not os.path.isdir(tree):   # the tree went while the step worked: git or a test could not start in it
        return _no([], f'not measured: there is no hot fix tree at {tree} ({_line(fault)}) at {_where(fault)}', f'{_tree_step(tree)}, then RUN AGENT here')
    if isinstance(fault, NotMeasured):
        return _no([], f'{fault} at {_where(fault)}', f'git -C {tree} status --porcelain prints the error it met; when it still fails, {_tree_step(tree)}, then RUN AGENT here')
    return _crashed(fault)


def _handed_back(name):
    """HIS TWO PRESSES WHEN THE NEXT STEP'S RUN WAS NOT TAKEN: here first, for its request stands built and nothing is picked, so this run ends green and
    hands nothing on; the next step alone never clears this red, for past it Pick hands on to the walk or the cleanup and Build never runs again"""
    return (f'RUN AGENT here, seconds of your hand: its request is built and nothing is picked now, so {NAME} ends green in seconds and hands nothing on, which ends this red; '
            f'then clear what the refusal names (an open run let end) and RUN AGENT on {name}: it takes its own RUN and runs the day on by itself')


def _timed(conf, db, got):
    """A RED WHOSE LAST PRESS IS A RUN OF THIS STEP, A REQUEST STILL PLANNED: that press hires its writer and developer and runs the day on, so the line says so with their clocks;
    nothing planned, the run ends green in seconds, and the line stands as it is. Requests that do not read: said as an if. -> the red"""
    if not got['step'].endswith(('then RUN AGENT here', 'then RUN AGENT')):
        return got
    try:
        rows = at(db, PICKED)
    except sqlite3.Error:
        rows = None
    if rows == []:
        return got
    # A REQUEST STILL PLANNED: a bare RUN AGENT here would hire its workers again and the red would clear only after Build's 50 minutes; so his
    # line first takes it off planned (only while it is still planned: a run that ends in between keeps what it set), and the press here then
    # finds nothing picked and ends green in seconds. Building it again is Pick's run, the day's own, never part of this fix.
    rid = rows[0]['id'] if rows else ''
    keep = bool(rows and rows[0].get('tests_sha'))
    where = f"id='{rid}' AND state='{PICKED}'" if rid else f"state='{PICKED}'"
    back = f"sqlite3 {db} \"UPDATE requests SET state='{WAITING}'{'' if keep or not rid else ', tests_sha=NULL'} WHERE {where}\""
    head = got['step']
    for end in (', then RUN AGENT here', ' then RUN AGENT here', ', then RUN AGENT', ' then RUN AGENT'):
        if head.endswith(end):
            head = head[:-len(end)]
            break
    write, first, build = conf['write_seconds'], conf['prove_seconds'], conf['build_seconds']
    who = f"{rid} is still planned" if rid else 'if a request is still planned'
    return {**got, 'step': (f"{head}, then set it back to asked ({who}: {back}{', its frozen tests kept' if keep else ''}), {NOTHING_PICKED} (seconds of your hand); "
                            f"RUN AGENT on Pick then takes it in its build order as the day's own run, no part of this fix "
                            f"(Build up to {(write + first + build) // 60} minutes: {write // 60} for the test writer, {first // 60} for its tests' failing-first run, {build // 60} for the developer)")}


def once(store, job_key, n, agent, chain, conf, runner, hire, db, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step); green, the next step's RUN taken first: a next refused or
    missing ends this one FAILED, said; a next switched off is off, never a red: this one ends DONE, hands nothing on, and its request stands built. A crash ends FAILED with its line. -> (what it said, the next to run (module, shell, run) or None)"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not locked:
        got = _no([], 'another DAY step is running', f'lsof {_lock_path(conf)} prints the pid N that holds the lock, ps -p N -o command= names that run: let it end (its block says RUNNING), then RUN AGENT here')
    else:
        try:
            with Beat(store, job_key):
                got = step(store, conf, runner, db, hire)
        except Exception as fault:   # A CRASH IS RED, NAMED WHERE IT HAPPENED: the traceback's last frame, its file and line (its blind rule read 2026-10-28; as agent011)
            got = _fault(fault, conf, db)
    if not got['ok']:   # every press that runs this step again: what it starts named, none left unsaid
        got = _timed(conf, db, got)
    nxt = None
    if got['ok'] and got.get('next'):
        nxt, why = hand_on(store, chain, got['next'])
        name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or got['next']
        if nxt is None and why:
            got = {**got, 'ok': False, 'why': f'the day stopped before {name}: {why}', 'step': _handed_back(name), 'next': None}
        elif nxt is None:   # OFF IS NEVER A RED: the day rests here by his switch, its build kept, nothing handed on
            got = {**got, 'lines': got['lines'] + [f'{name} is switched off, its RUN not taken: the request stands built; when you turn it on, RUN AGENT on {name}'], 'next': None}
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
        got = _timed({**CONF, **(conf or {})}, db or store.db_path, _crashed(fault))
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
                     'copy': f"{HAND}{_asked(db, r['id'], keep=bool(a.get('keep_tests')))}, {_row_clears(r['id'])}",
                     'presses': [{'do': 'back', 'label': 'Back to asked', 'confirm': f"Send {r['id']} back to asked? Pick takes it again in its build order."}]})
    return {'kind': 'table', 'title': ASIDE_TITLE, 'under': (f"{len(rows)} stuck today: each one's change was put back; BACK TO ASKED sends it back to the backlog" if rows else 'none stuck today'),
            'columns': ['Request', 'His words', 'Why', 'Set aside', 'Your press'], 'rows': rows, 'empty': ASIDE_EMPTY}


def press(store, job_key, do, fields=None):
    """ITS BUTTON ON A REQUEST IT SET ASIDE: 'back', his hand line pressed: the request stuck today by this step set back to asked (Pick takes it
    again in its build order; after a developer's red its frozen tests are kept, as its line keeps them, so its developer alone runs again; after
    any other red they are cleared, as its line clears them). Any other request, or one moved since, changes nothing, said.
    -> the words said on its shell"""
    if do not in PRESSES:
        raise ValueError(f'not one of its presses: {do!r}')
    db, rid = store.db_path, str((fields or {}).get('value') or '').strip()
    r = next((x for x in requests(db) if x['id'] == rid), None)
    if r is None:
        return f"BACK TO ASKED · no request {rid or 'named'}: nothing changed"
    a = _side(CONF, r).get('aside') or {}
    if r['state'] != STUCK or a.get('step') != KEY:
        return f'BACK TO ASKED · {rid} is {r["state"]}, not set aside by {NAME}: nothing changed'
    keep = bool(a.get('keep_tests'))
    if not set_state(db, rid, WAITING, f'sent back to asked by the owner ({NAME} had set it aside)', when=STUCK, **({} if keep else {'tests_sha': None})):
        return f'BACK TO ASKED · {rid} moved before the write: nothing changed'
    return f"BACK TO ASKED · {rid} is asked again{', its frozen tests kept' if keep else ''}: RUN AGENT here ends this row's red in seconds, Pick takes it in its build order"


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
    """HIS ONE COMMAND WHEN HEAD SITS BEHIND A REQUEST'S BASE: its branch brought forward to the base (nothing lost, never a reset), the request asked again with its tests unfrozen; its new pick records the base"""
    return f"git -C {tree} merge --ff-only {base} && {_asked(db, rid)}"


def _kept_aside(tree, db, rid):
    """HIS ONE COMMAND WHEN THE TREE HOLDS WHAT A REQUEST CANNOT CLAIM: stashed, never lost (it may be his own edit), the request asked again"""
    return f"git -C {tree} stash push -u -m day-{rid} && sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


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


def _no(lines, why, step):
    return {'ok': False, 'lines': lines, 'why': why, 'step': step, 'next': None}


def _no_tree(git, tree):
    """THE TREE THERE AND ITS HEAD A COMMIT, read before anything else on it: not measured, said first. The path gone: his command stands it up.
    Something at the path: a worktree add stops on it, so git's own error is said and it is moved aside first. -> a red, or None"""
    if not os.path.lexists(tree):
        return _no([], f'not measured: there is no hot fix tree at {tree}', f'{_tree_step(tree)}, then RUN AGENT here')
    if os.path.isdir(tree):
        head = git('rev-parse', '--verify', 'HEAD^{commit}')
        if head.returncode == 0:
            return None
        error = _last(head.stderr)[:160] or f'git exit {head.returncode}'
    else:
        error = 'it is not a folder'
    return _no([], f'not measured: {tree} is there but its HEAD does not read ({error})', f'{_tree_step(tree)}, then RUN AGENT here')


def _unready(git, tree):
    """THE HOT FIX TREE THERE, ON ITS BRANCH AND CLEAN (nobody's half done work is ever committed or put back for them). -> a red, or None"""
    red = _no_tree(git, tree)
    if red:
        return red
    if git('symbolic-ref', '-q', 'HEAD').returncode != 0:
        return _no([], 'the hot fix tree is on no branch (a detached HEAD)', f'git -C {tree} checkout {BRANCH}, then RUN AGENT')
    dirty = _changed(git)
    if dirty:
        return _no([], f"the hot fix tree holds {len(dirty)} file(s) nobody committed: {', '.join(dirty[:4])}", f'git -C {tree} stash push -u -m day-left (kept in the stash, never lost), then RUN AGENT')
    return None


def _asked(db, rid, state=WAITING, keep=False):
    """HIS ONE LINE that sets a request's state by hand (back to asked: Pick takes it again in its build order; keep: its frozen tests stay)"""
    return f"sqlite3 {db} \"UPDATE requests SET state='{state}'{', tests_sha=NULL' if state == WAITING and not keep else ''} WHERE id='{rid}'\""


def _since_pick(git, tree, r, info, lines, built, db=''):
    """WHAT A STEP ON A PICKED REQUEST STANDS ON: its base recorded at its pick on a clean tree, HEAD still at that base (a commit past it, or
    a HEAD gone back behind it, is never built on), and the tree's change exactly its own recorded files (built), or none (not built yet). -> a red, or None"""
    base = info.get('base')
    if not base or not info.get('clean'):
        return _no(lines, f"{r['id']}: its pick recorded no base", f"{_kept_aside(tree, db, r['id'])}, {_row_clears(r['id'])}")
    moved = _moved(git, base)
    if moved:
        return _no(lines, f"{r['id']}: the tree moved past its pick ({_said_commits(moved)}): never built on, never reviewed",
                   f"{_undone(tree, db, r['id'], base)}, {_row_clears(r['id'])}")
    head, there = _at_base(git, base)
    if not there:   # nothing past its base and not at it: HEAD went back behind it, on older code than its pick
        return _no(lines, f"{r['id']}: the tree went back behind its pick (HEAD {head[:12]}, its base {base[:12]}): never built on, never reviewed",
                   f"{_brought_up(tree, db, r['id'], base)}, {_row_clears(r['id'])}")
    mine = set(info.get('files') or ()) if built else set()
    if built and not mine:
        return _no(lines, f"{r['id']}: its built files were never recorded", f"{_kept_aside(tree, db, r['id'])}, {_row_clears(r['id'])}")
    dirty = set(_changed(git))
    if dirty != mine:
        odd = sorted(dirty ^ mine)
        if dirty - mine:
            return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) changed besides it: {', '.join(odd[:4])})",
                       f'see `git -C {tree} status`: they may be his own hand edits, never put back here; clear them by hand, then RUN AGENT here')
        return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) of it gone: {', '.join(odd[:4])})",
                   f"set {r['id']} back to asked ({_asked(db, r['id'])}), clear the rest of its change by hand (git -C {tree} status), {_row_clears(r['id'])}")
    return None


NOTHING_PICKED = 'then RUN AGENT here: nothing is picked now, so this row ends green in seconds and hands nothing on'


def _row_clears(rid):
    """THE END OF HIS LINE THAT TAKES A REQUEST OFF PICKED: nothing picked is this row's own green, so one press here clears it in seconds; building the request again is the day's next run on its own rows, never what this row waits on. -> one clause"""
    return f"{NOTHING_PICKED}; {rid} waits asked, and RUN AGENT on Pick takes it on as the day's own run, no part of this fix"


def _set_aside(db, git, tree, base, r, files, why, step, lines, conf=None, keep=False):
    """A RED OF BUILD: its change put back (its own files alone), it stuck today, the day stops here. His one step, every red the same: what the
    red names fixed (a file that would not go back cleared by hand first), its one line that sets it back to asked, then RUN AGENT here: nothing is
    picked then, so this row ends green in seconds with no worker hired and no next step run. conf: the step that set it aside, why and when, kept
    in its side file (its block lists it with its BACK TO ASKED press). keep: a developer's red, its frozen tests sound: his line and his press
    leave them, so its developer alone runs when the day picks it again."""
    back, kept = put_back(git, tree, base, files)
    first = f"clear {', '.join(kept[:4])} by hand (git -C {tree} status), then " if kept else ''
    if not set_state(db, r['id'], STUCK, why[:300], when=r['state']):   # A PRESS DURING THE RUN WINS (its blind rule reads 2026-10-28): its change put back, its state left as he set it, never said stuck
        lines.append(f"{r['id']}: a press moved it during the run: its state is left as he set it")
        lines.append(f"{r['id']}: its {len(back)} changed file(s) put back" + (f", {len(kept)} would not go back: {', '.join(kept[:4])}" if kept else ''))
        return _no(lines, f"{r['id']}: {why}; not set aside, a press moved it", f'{step}; {first}{NOTHING_PICKED}')
    if conf:
        _side(conf, r, aside={'step': KEY, 'why': why[:300], 'at': _stamp(), 'keep_tests': keep})
    lines.append(f"{r['id']} set aside: stuck today, its {len(back)} changed file(s) put back" + (f", {len(kept)} would not go back: {', '.join(kept[:4])}" if kept else ''))
    tests_word = ('its frozen tests are kept and its developer alone runs when Pick takes it (words changed by UPDATE have new tests written first)' if keep
                  else 'its tests are written anew from his words when Pick takes it')
    return _no(lines, f"{r['id']}: {why}", f"{step}; {first}{_asked(db, r['id'], keep=keep)}, {_row_clears(r['id'])}; {tests_word}")


def _elsewhere(git):
    """THE BRANCHES ANOTHER WORKTREE HAS CHECKED OUT (the repo's refs are shared: another session's merge there moves them while a worker works
    here, never the worker's move, as main). -> their refs, this tree's own branch never one"""
    held = {ln[len('branch '):] for ln in git('worktree', 'list', '--porcelain').stdout.splitlines() if ln.startswith('branch ')}
    return held - {git('symbolic-ref', '-q', 'HEAD').stdout.strip()}


def _snap(git, tree, side):
    """THE TREE'S GIT AND THE REQUEST'S SIDE FILE before a hire: every local ref (git for-each-ref), the branches other worktrees hold, HEAD, the ignored files with their fingerprints, the side file's bytes"""
    seen, head = git('for-each-ref', '--format=%(refname) %(objectname)'), git('rev-parse', 'HEAD')
    if seen.returncode != 0 or head.returncode != 0:   # a ref that did not read is never a worker's move
        raise NotMeasured(f'not measured: the refs did not read ({_last(seen.stderr or head.stderr)[:120]})')
    refs = seen.stdout.splitlines()
    return {'refs': {ln.split(' ', 1)[0]: ln.split(' ', 1)[1] for ln in refs if ' ' in ln and not ln.startswith(('refs/remotes/', 'refs/heads/main '))},
            'elsewhere': _elsewhere(git), 'head': head.stdout.strip(), 'sym': git('symbolic-ref', '-q', 'HEAD').stdout.strip(), 'ignored': _ignored(git, tree), 'side': _bytes(side)}


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
        top = git('log', '-1', '--format=%h "%s"', after['head']).stdout.strip() if after['head'] != before['head'] else ''
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


def _hire_undone(git, tree, db, rid, base, before, side, keep):
    """HIS ONE LINE AFTER A HIRED WORKER'S MOVE: everything it left, in the order git takes it: every ref put back, its uncommitted change stashed
    (never lost), its branch checked out again, its commits reverted (a new commit, never a reset) or HEAD brought back, its new ignored files
    removed, the request asked again (keep: its frozen tests stay); its new pick writes the side file anew. An ignored file it edited has no old
    bytes to go back to: its red names it, this line leaves it"""
    after = _snap(git, tree, side)
    g, branch = f'git -C {shlex.quote(tree)}', before['sym']
    theirs = before['elsewhere'] | after['elsewhere'] | {branch}
    moved = sorted(ref for ref in set(before['refs']) | set(after['refs']) if ref not in theirs and before['refs'].get(ref) != after['refs'].get(ref))
    steps = [f"{g} update-ref {shlex.quote(ref)} {before['refs'][ref]}" if ref in before['refs'] else f'{g} update-ref -d {shlex.quote(ref)}' for ref in moved]
    if _changed(git):
        steps.append(f'{g} stash push -u -m day-{rid}')
    if branch and after['sym'] != branch:
        steps.append(f"{g} checkout {shlex.quote(branch.removeprefix('refs/heads/'))}")
    tip = after['refs'].get(branch) or after['head']
    if tip != before['head']:
        back = git('merge-base', '--is-ancestor', tip, before['head']).returncode == 0
        steps.append(f"{g} merge --ff-only {before['head']}" if back else f'{g} revert --no-edit {base[:12]}..HEAD')
    new = sorted(set(after['ignored']) - set(before['ignored']))
    if new:
        steps.append('rm -f -- ' + ' '.join(shlex.quote(os.path.join(tree, f)) for f in new))
    return ' && '.join([*steps, _asked(db, rid, keep=keep)])


def _unloaded(out):
    """THE TEST FILES unittest could not load (a broken file, an import that stops it at its top: said as unittest.loader._FailedTest, one 'test' that
    failed for no reason of the request's): such a run never counts as failing first. -> their names"""
    return re.findall(r'^ERROR: (\S+) \(unittest\.loader\._FailedTest', out, re.M)


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

def _words_write(r, tests, tree, python):
    return (f"You are THE DAY's test writer for one request of the owner's, on the hot fix tree (your working folder).\n\n"
            f"THE REQUEST {r['id']}, his own words:\n{r['words']}\n\n"
            f"Write ONLY its tests, before anything is built: Python unittest files named test_*.py in {tests} (create the folder). "
            "They must fail on the tree as it is now and pass once the request is done; they call the real thing (the real code, page or file), "
            "never a document's words. Each file must load on the tree as it is: a module the request adds is imported inside its test, never at the file's top. "
            f"THE TREE IS {tree} and the tests are run from it exactly as: {_run_line(tree, tests, python)} . So the tree is the current folder when they "
            "run: import its modules by name, and never find the tree by a path relative to the tests folder (TREE_DIR holds the tree too). "
            f"Do not edit any file of the tree, nor the .day_* files of {tests}. Your last line: WROTE: <the test files>, or STUCK: <why>.")


def _words_build(r, tests, tree, python):
    return (f"You are THE DAY's developer for one request of the owner's, on the hot fix tree (your working folder).\n\n"
            f"THE REQUEST {r['id']}, his own words:\n{r['words']}\n\n"
            f"Its tests are written and FROZEN in {tests}: never change them. They are run as: {_run_line(tree, tests, python)} . Make them pass by building the request in this tree, the smallest "
            "change that does what he asked, in the tree's own style. Never commit (THE DAY commits by path after its review), never any git command that moves "
            "the tree's git, never write outside this tree. Never touch the Judge, a seal, production, slot B or the core's sealed files. "
            "Your last line: BUILT: <the files you changed>, or STUCK: <why>.")


def _wipe(tests):
    """an unfrozen tests folder cleared for a new writer, its side files (.day_*) kept"""
    for f in os.listdir(tests) if os.path.isdir(tests) else ():
        if f.startswith('.day_'):
            continue
        p = os.path.join(tests, f)
        shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) and not os.path.islink(p) else os.remove(p)


def _has_tests(tests):
    return os.path.isdir(tests) and any(not f.startswith('.day_') for f in os.listdir(tests))


def _words_sha(r):
    return hashlib.sha256(str(r['words'] or '').encode('utf-8', 'surrogateescape')).hexdigest()


def _words_moved(tests, r):
    """HIS WORDS CHANGED SINCE ITS TESTS WERE FROZEN (his UPDATE): those tests prove the old words. No mark (frozen before it was kept): not said moved"""
    held = _bytes(os.path.join(tests, WORDS_MARK))
    return held is not None and held.decode(errors='replace') != _words_sha(r)


def _build(conf, runner, db, hire, r, tree, tests, base, git, lines):
    side = os.path.join(tests, SIDE)
    aside = lambda why, step_, keep=False: _set_aside(db, git, tree, base, r, _changed(git), why, step_, lines, conf, keep)   # the tree was clean at its base when this step began: every change is its own
    stop = lambda bad, before, keep=False: _no(lines, f"{r['id']}: {bad}", f"{_hire_undone(git, tree, db, r['id'], base, before, side, keep)}, {_row_clears(r['id'])}")
    if r.get('tests_sha') and _words_moved(tests, r):   # HIS UPDATE MOVED THE WORDS: its tests written again, never reused
        lines.append(f"5 build · {r['id']} · his words changed since its tests were frozen: new tests are written")
        r = {**r, 'tests_sha': None}
    if _has_tests(tests) and r.get('tests_sha') and _sha(tests) == r['tests_sha']:   # FROZEN ONCE: an earlier run's tests reused only at their kept sha
        frozen = r['tests_sha']
        lines.append(f'5 build · {r["id"]} · its tests frozen before ({frozen[:12]}), the same bytes')
    else:
        if _has_tests(tests):
            if r.get('tests_sha'):
                return aside('its frozen tests changed since they were frozen', f'its tests ({tests}) differ from their sha {r["tests_sha"][:12]} and no copy of them is kept, so its line below unfreezes them and new tests are written')
            _wipe(tests)   # an unfrozen folder (a writer that stopped half way) is written again whole
        os.makedirs(tests, exist_ok=True)
        snap = _snap(git, tree, side)
        took = time.monotonic()
        code, said = _hired_by(hire, conf, r, TEST_WRITER, _words_write(r, tests, tree, conf['python']), tree, conf['write_seconds'])
        lines.append(f"5 build · {r['id']} · its test writer ended exit {code} in {round(time.monotonic() - took)} s (at most {conf['write_seconds']} s)")
        bad = _hired(git, tree, snap, side)
        if bad:
            return stop(bad, snap)
        if code != 0 or _last(said).upper().startswith('STUCK') or not any(f.startswith('test_') and f.endswith('.py') for _rt, _d, fs in os.walk(tests) for f in fs):
            _wipe(tests)
            return aside(f'its tests were not written ({_last(said)[:200]})', "the writer's last words are in this red")
        if _changed(git):
            _wipe(tests)
            return aside('the test writer changed the tree', 'the tree is put back')
        try:   # THE TESTS FAIL FIRST, or they prove nothing
            took = time.monotonic()
            code, out, ran, skipped = _tests_run(conf, tree, tests, runner)
        except subprocess.TimeoutExpired:
            _wipe(tests)
            return aside(f"its new tests did not end on the tree as it is (stopped at {conf['prove_seconds']} s)", 'its tests are cleared')
        lines.append(f"5 build · {r['id']} · its new tests ran on the tree as it is in {round(time.monotonic() - took)} s: exit {code}, {ran} test(s)")
        if _changed(git):   # its tests' run left the tree changed: red, never measured green (its blind review 2026-10-28)
            _wipe(tests)
            return aside('its new tests changed the tree while they ran', 'its tests are cleared and the tree is put back')
        broken = _unloaded(out)
        if broken:   # A FILE THAT DID NOT LOAD FAILS FOR ITS OWN REASON, not the request's: never its failing first
            _wipe(tests)
            return aside(f"its tests did not load on the tree as it is ({', '.join(broken[:4])}): they prove nothing", 'its tests are cleared')
        if code == 0 or ran == 0:
            _wipe(tests)
            return aside('its tests do not fail before the build: they prove nothing', 'its tests are cleared')
        frozen = _sha(tests)
        if not set_state(db, r['id'], PICKED, 'its tests frozen', when=PICKED, tests=tests, tests_sha=frozen):
            return aside(f'it is no longer {PICKED}: a press between the read and the write wins', f"see its state (sqlite3 {db} \"SELECT state, why FROM requests WHERE id='{r['id']}'\")")
        with open(os.path.join(tests, WORDS_MARK), 'w', encoding='utf-8') as fh:
            fh.write(_words_sha(r))
        _side(conf, r, frozen_at=_stamp(), failed_first=ran)   # when its tests were frozen and how many failed first: its block says it
        lines.append(f'5 build · {r["id"]} · its tests fail first ({ran} test(s)), frozen · {frozen[:12]}')
    snap = _snap(git, tree, side)
    took = time.monotonic()
    code, said = _hired_by(hire, conf, r, DEVELOPER, _words_build(r, tests, tree, conf['python']), tree, conf['build_seconds'])
    lines.append(f"5 build · {r['id']} · its developer ended exit {code} in {round(time.monotonic() - took)} s (at most {conf['build_seconds']} s)")
    bad = _hired(git, tree, snap, side)
    if bad:
        return stop(bad, snap, keep=_sha(tests) == frozen)
    if _sha(tests) != frozen:   # first: a developer's other red keeps its tests for a rerun, these no longer are the frozen ones
        return aside('its frozen tests were changed by its build', f"no copy of its tests ({tests}) at their sha {frozen[:12]} is kept, so its line below unfreezes them and new tests are written")
    if code != 0 or _last(said).upper().startswith('STUCK'):
        return aside(f'its build did not go to the end ({_last(said)[:200]})', "the developer's last words are in this red; its change is put back", keep=True)
    files = _changed(git)
    if not files:
        return aside('its build changed nothing in the tree', 'nothing was built', keep=True)
    prints = _prints(tree, files)
    _side(conf, r, files=files, prints=prints, built_at=_stamp())   # each file as it left it: Building now tells a hand edit from its build by these
    _keep_built(conf, r, base, files, prints)
    if not set_state(db, r['id'], BUILT, f"built: {len(files)} file(s) changed", when=PICKED):
        return aside(f'it is no longer {PICKED}: a press between the read and the write wins', f"see its state (sqlite3 {db} \"SELECT state, why FROM requests WHERE id='{r['id']}'\")")
    lines.append(f"5 build · {r['id']} · {len(files)} file(s) changed: {', '.join(files[:6])}{' ...' if len(files) > 6 else ''}")
    return _ok(lines)


def _wait(why):
    """HIS STEP ON A WRITER MARK OR THE UTILITY HELD: its pid is in its why, ps names that run; a dead pid frees the mark by itself"""
    pid = re.search(r'pid (\d+)', why).group(1)
    return f'ps -p {pid} -o command= names that run: let it end, never delete a live mark, then RUN AGENT here'


def step(store, conf, runner, db, hire):
    """THE TREE'S WRITER MARK FIRST, every check under it (its blind rule read 2026-10-28, as Main first and Cleanup): a running hot fix
    utility or another writer is said as itself, never as files nobody committed or a tree that moved"""
    with Writer(conf) as w:
        if w.why:
            return _no([], w.why, _wait(w.why))
        return _step(store, conf, runner, db, hire)


def _step(store, conf, runner, db, hire):
    lines = []
    r, red = _one(db, PICKED, lines, 'Build')
    if red or r is None:
        return red
    tree, tests = conf['tree'], _tests_of(conf, r)
    git = _git(tree, runner)
    red = _no_tree(git, tree)
    if red:
        return red
    info = _side(conf, r)
    red = _since_pick(git, tree, r, info, lines, built=False, db=db)
    if red:
        return red
    with Writer(conf) as w:
        if w.why:
            return _no(lines, f"{r['id']}: {w.why}", _wait(w.why))
        return _build(conf, runner, db, hire, r, tree, tests, info['base'], git, lines)


def _build_word(conf, r):
    """WHERE ITS BUILD STANDS (the original's newest turn of each request in building), from its side file: built and its files, or its tests
    frozen and the build next, or its tests not written yet"""
    s = _side(conf, r)
    if r['state'] == BUILT:
        files = s.get('files') or []
        return (f"built{' ' + _when(s['built_at']) if s.get('built_at') else ''}: {len(files)} file(s) changed"
                + (f": {', '.join(files[:4])}{' ...' if len(files) > 4 else ''}" if files else '') + '; Prove runs its tests next')
    if r.get('tests_sha'):
        return (f"its tests written{' ' + _when(s['frozen_at']) if s.get('frozen_at') else ''}, failing first"
                + (f" ({s['failed_first']} test(s))" if s.get('failed_first') else '') + f" and frozen ({r['tests_sha'][:12]}); its developer builds it next")
    return 'picked: its tests are written first'


def report(db, conf):
    """THE ORIGINAL'S RUN LINE (row 012): a list of every request in its build (picked or built) and where its build stands, or 'a list:
    nothing building' and the last work."""
    rows = at(db, PICKED, BUILT)
    if rows:
        return 'a list · ' + _listed([f"{r['id']} {r['state']}: {_build_word(conf, r)}" for r in rows])
    last = _last_work(db)
    return 'a list: nothing building' + (f' · the last work: {last}' if last else '')


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS, words never markup (web/page.py content_view), the original's row 012 BUILD: the requests in their build
    (picked or built: his words, since when, where the build stands), WHY IT'S RED while its newest run is red (red since, ticking, the warning,
    his one step on the line under it), then the builds that did not go to the end (each set aside today, its BACK TO ASKED press)."""
    db = store.db_path
    red = _red_part(store, job_key)
    try:
        rows = at(db, PICKED, BUILT)
        last = _last_work(db)
        aside = _aside_part(db, CONF)
    except sqlite3.Error as fault:   # as Pick and Building now: requests that do not read are not measured, said with his step
        return [{'kind': 'note', 'title': 'Building now', 'text': f'not measured: the requests cannot be read ({_line(fault)}) · {HAND}{_read_step(db, fault)}'}] + ([red] if red else [])
    parts = [{'kind': 'table', 'title': 'Building now', 'under': (f"a list · {len(rows)} in its build" if rows else 'a list: nothing building' + (f' · the last work: {last}' if last else '')),
              'columns': ['Request', 'His words', 'State', 'Since', 'Its build'],
              'rows': [{'key': r['id'], 'cells': [r['id'], _cut(r['words']), r['state'], _when(r.get('state_at')), _build_word(CONF, r)]} for r in rows],
              'empty': 'Nothing building: Pick hands the next request in build order.'}]
    return parts + ([red] if red else []) + [aside]
