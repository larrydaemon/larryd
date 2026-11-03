"""AGENT 018 · COMMIT (the DAY group, the owner 2026-10-28: "DAY is a group on the top right each should say day / and we should see each /
build each one"; "all of day needs to be rewritten its all hotfix style for the day no judge"): a SUB AGENT of the MARK IV agent (agent001),
lower rank, its own block in the DAY group, its own light and its own run. STEP 8: COMMIT (the original's 015, ready): the reviewed request's own files committed by path on the hot fix tree, its id and his words in the message, only when nothing was committed past its base, its tests are still the frozen ones and its change is still the one proven and read; the request is then written waiting_takein with its commit in commits, ready for tonight's take-in (no day walk: the owner 2026-10-31, "we do a full walk at night with the full build"); then PICK again, the next request of the backlog. A commit that landed before its run stopped is recorded the same way, never made again. Its tests moved since the review: frozen tests that moved are never proven again, so its red gives his one line that stashes its change (git stash push -u, never lost) and sets it back to asked with its tests unfrozen, then RUN AGENT here. Its change moved since the review: its red gives Review's kept patch back, or the sqlite3 line that sets it back to building, then RUN AGENT on Prove.

THE DAY, STEP BY STEP, each step its own agent (agent011 to agent020; agent021 the backlog): the requests, building now, main first, pick,
build, prove, review, commit (then pick again, one request at a time), cleanup; no day walk (the full walk is at night, its take-in). A step
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

KEY = 'commit'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
ROW = 15   # the original's row 015
NAME = 'Commit'
CARD_NAME = 'Scrum Master Commit'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Commit: the reviewed change committed by path'
WHAT = "Commits the reviewed request's files by path, its id and his words in the message, then the next request"
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due (frame_red.due_at)
ROW_FILE = 'agent018_day_commit.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes: in its own thread, the page answers RUN AGENT at once
NEXT = 'pick'   # the step it hands on to when it ends green

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
COMMITTED, READY, STUCK = 'approved', 'waiting_takein', 'stuck_today'   # a commit is READY at once (waiting_takein, for tonight's take-in); approved is only a row from before the day walk was removed
BEAT = 60   # seconds between two heartbeats of a long step (THE RED's QUIET is 3 minutes)
GIT_SECONDS = 120   # the longest one git call may run: its calls end in seconds, one past this is hung, stopped and red (never RUNNING forever with the day's lock and the writer mark held)
HAND = 'YOUR 3 MIN: '
DAY_EMAIL = 'day@localhost'   # THE DAY's own commits (its merge of main, its commit of a request) carry it
SIDE, HIRE_MARK, KEPT = '.day_base', '.day_hire', '.day_reviewed'   # A REQUEST'S SIDE FILES in its tests folder (~/scratch/tests/day/<id>, outside the tree: no commit carries them, never a test, never in its tests' sha): its pick's base and its proof; the pid of the worker hired for it now; Review's patch of the change it read
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


def _ignored(git):
    return {p for code, p in _status(git, '--untracked-files=all', '--ignored') if code == '!!' and not _cache(p)}


def _head(git):
    seen = git('rev-parse', 'HEAD')
    if seen.returncode != 0:   # a HEAD that did not read is never a commit that is not the one
        raise NotMeasured(f'not measured: git rev-parse HEAD failed ({_last(seen.stderr)[:120]})')
    return seen.stdout.strip()


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
    if seen.returncode != 0:   # a log that did not read is never a tree still at its base
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


def _proof(git, tree, base):
    """THE CHANGE'S OWN FINGERPRINT: sha256 of its diff from its base and its new files' bytes (Prove keeps it; Review and Commit find the
    same one, or stop)"""
    diff, new = git('diff', '--binary', base, '--'), git('ls-files', '--others', '--exclude-standard', '-z')
    if diff.returncode != 0 or new.returncode != 0:   # a change that did not read is never a change that moved
        raise NotMeasured(f'not measured: its change did not read ({_last(diff.stderr or new.stderr)[:120]})')
    h = hashlib.sha256(diff.stdout.encode('utf-8', 'surrogateescape'))
    for f in sorted(p for p in new.stdout.split('\0') if p and not _cache(p)):
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
    return {'ok': False, 'lines': [], 'why': f'it crashed at {where} ({_line(fault)})', 'step': f'open app/agent/{where}, fix what the crash names, then RUN AGENT here', 'next': None}


def _hung(tree, fault, staged=False):
    """A GIT THAT DID NOT END: stopped at GIT_SECONDS, its heartbeat, the writer mark and the day's lock let go on the way out; said not measured, with what clears it.
    staged: it stopped inside its add or commit, so what it left staged is unstaged too (paths only, its change stays in the tree, so its proof holds); its commit begun stays marked, so a commit that did land is recorded by the next run, never made again"""
    lock = f'"$(git -C {tree} rev-parse --path-format=absolute --git-path index.lock)"'
    clear = f' && git -C {tree} restore --staged -- .' if staged else ''
    return _no([], f'not measured: a git call hung and was stopped at {_where(fault)} ({_line(fault)})',
               f"ps -axo pid,etime,command | grep '[g]it ' names any git left running: let it end; with none left, rm -f {lock}{clear}, and when git -C {tree} status --porcelain answers at once, RUN AGENT here")


def _fault(fault, conf, db):
    """A STEP THAT BROKE: what did not read (the requests, the tree) is 'not measured', said first with its file and line, and his step is that
    read's, no code to edit (its blind rule read 2026-10-31); a git that hung the same; anything else is its own crash. -> its red"""
    tree = conf['tree']
    if isinstance(fault, subprocess.TimeoutExpired):   # A HUNG GIT ENDS THE RUN RED, with what clears it: never RUNNING forever under its own heartbeat
        return _hung(tree, fault)
    if isinstance(fault, sqlite3.Error):
        return _no([], f'not measured: the requests cannot be read or written ({_line(fault)}) at {_where(fault)}', _read_step(db, fault))
    if isinstance(fault, (FileNotFoundError, NotADirectoryError)) and not os.path.isdir(tree):   # the tree went while the step worked: git could not start in it
        return _no([], f'not measured: there is no hot fix tree at {tree} ({_line(fault)}) at {_where(fault)}', f'{_tree_step(tree)}, then RUN AGENT here')
    if isinstance(fault, NotMeasured):
        return _no([], f'{fault} at {_where(fault)}', f'git -C {tree} status --porcelain prints the error it met; when it still fails, {_tree_step(tree)}, then RUN AGENT here')
    return _crashed(fault)


def _ended(got):
    return {'summary': ('DONE · ' if got['ok'] else f"FAILED · {got['why']} · {HAND}{got['step']} · ") + ' | '.join(got['lines'][-3:]), **got}


def _handed_back(name):
    """HIS TWO PRESSES WHEN THE NEXT STEP'S RUN WAS NOT TAKEN: here first, for its request stands committed and nothing is reviewed, so this run ends green and
    hands nothing on; the next step alone never clears this red, for past it Pick hands on to the cleanup and Commit never runs again"""
    return (f'RUN AGENT here, seconds of your hand: its request is committed and nothing is reviewed now, so {NAME} ends green in seconds and hands nothing on, no commit made, which ends this red; '
            f'then clear what the refusal names (an open run let end) and RUN AGENT on {name}: it takes its own RUN and runs the day on by itself')


def once(store, job_key, n, agent, chain, conf, runner, hire, db, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step); green, the next step's RUN taken first: a next refused or
    missing ends this one FAILED, said; a next switched off is off, never a red: this one ends DONE, hands nothing on, its commit recorded. A crash ends FAILED with its line. -> (what it said, the next to run (module, shell, run) or None)"""
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
        name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or got['next'].capitalize()
        if nxt is None and why:
            got = {**got, 'ok': False, 'why': f'the day stopped before {name}: {why}', 'step': _handed_back(name), 'next': None}
        elif nxt is None:   # OFF IS NEVER A RED: the day rests here by his switch, the commit recorded, nothing handed on
            got = {**got, 'lines': got['lines'] + [f'{name} is switched off, its RUN not taken: the commit stands recorded; when you turn it on, RUN AGENT on {name}'], 'next': None}
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


def _not_read(db, e):
    return [{'kind': 'note', 'title': 'The requests', 'text': f'not measured: the requests cannot be read ({_line(e)}) · {HAND}{_read_step(db, e)}'}]


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
    """HIS ONE COMMAND WHEN A COMMIT SITS PAST A REQUEST'S BASE: what the tree holds stashed first, never lost (a reviewed change left dirty stops the revert or Pick's clean tree), reverted, the request asked again with its tests unfrozen; its new pick records the new base"""
    return f"git -C {tree} stash push -u -m day-{rid} && {{ [ -z \"$(git -C {tree} rev-list {base[:12]}..HEAD)\" ] || git -C {tree} revert --no-edit {base[:12]}..HEAD; }} && sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


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


def _reviewed_back(conf, r, info):
    """HIS ONE COMMAND WHEN THE TREE MOVED OFF THE CHANGE REVIEW READ: what moved stashed, never lost, and Review's own patch of that change applied, so its
    fingerprint is the proven one again and Commit needs no new proof. -> the line, or '' when Review kept no patch of this very proof"""
    kept = os.path.join(_tests_of(conf, r), KEPT)
    if not info.get('proof') or info.get('kept') != info['proof'] or not os.path.isfile(kept):
        return ''
    return f"git -C {conf['tree']} stash push -u -m day-{r['id']}-moved && git -C {conf['tree']} apply {kept}"


def _since_pick(git, tree, r, info, lines, built, db='', back=''):
    """WHAT A STEP ON A PICKED REQUEST STANDS ON: its base recorded at its pick on a clean tree, HEAD still at that base (a commit past it is
    never built on), and the tree's change exactly its own recorded files (built), or none (not built yet). -> a red, or None"""
    base = info.get('base')
    if not base or not info.get('clean'):
        return _no(lines, f"{r['id']}: its pick recorded no base", f"{_kept_aside(tree, db, r['id'])}, {_row_clears(r['id'])}")
    moved = _moved(git, base)
    if moved:
        return _no(lines, f"{r['id']}: the tree moved past its pick ({_said_commits(moved)}): never built on, never reviewed",
                   f"{_undone(tree, db, r['id'], base)}, {_row_clears(r['id'])}")
    mine = set(info.get('files') or ()) if built else set()
    if built and not mine:
        return _no(lines, f"{r['id']}: its built files were never recorded", f"{_kept_aside(tree, db, r['id'])}, {_row_clears(r['id'])}")
    dirty = set(_changed(git))
    if dirty != mine:
        odd = sorted(dirty ^ mine)
        if back:
            return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) {'changed besides it' if dirty - mine else 'of it gone'}: {', '.join(odd[:4])})",
                       f"{back} (what moved stays in the stash, the reviewed change is back whole), then RUN AGENT here: it commits in seconds")
        return _no(lines, f"{r['id']}: the tree's change is not its own ({len(odd)} file(s) {'changed besides it' if dirty - mine else 'of it gone'}: {', '.join(odd[:4])})",
                   f"{_kept_aside(tree, db, r['id'])} (they may be his own hand edits: the stash keeps them), {_row_clears(r['id'])}")
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

def _row_clears(rid, state=WAITING, press='Pick'):
    """THE END OF HIS LINE THAT TAKES A REQUEST OFF REVIEWED: nothing reviewed is this row's own green, so one press here clears it in seconds; building the request again is the day's next run on its own rows, never what this row waits on. -> one clause"""
    return f"then RUN AGENT here: nothing is reviewed now, so this row ends green in seconds and hands nothing on; {rid} waits {state}, and RUN AGENT on {press} takes it on as the day's own run, no part of this fix"


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
    r, red = _one(db, 'reviewed', lines, 'Commit')
    if red or r is None:
        return {**red, 'lines': red['lines'] + [take_in(requests(db))[2]]} if red['ok'] else red   # row 015's list said on a green run too
    tree, tests = conf['tree'], _tests_of(conf, r)
    git = _git(tree, runner)
    red = _no_tree(git, tree)
    if red:
        return red
    if git('symbolic-ref', '-q', 'HEAD').returncode != 0:   # on no branch: never committed there
        return _no([], 'the hot fix tree is on no branch (a detached HEAD)', f'git -C {tree} checkout {BRANCH}, then RUN AGENT here')
    info = _side(conf, r)
    landed = _landed(git, r, info)
    if landed:   # A CRASH AFTER ITS COMMIT: recorded, never built or committed again
        if not set_state(db, r['id'], READY, "committed before its run stopped: recorded, ready for tonight's take-in", when='reviewed', commits=landed, done_at=_stamp()):
            return _no(lines, f"{r['id']}: its commit {landed[:12]} landed but a press moved it off reviewed: not recorded", f"sqlite3 {db} \"UPDATE requests SET state='waiting_takein', commits='{landed}' WHERE id='{r['id']}'\", then RUN AGENT here, then on Pick")
        return _ok([f"8 commit · {r['id']} · {landed[:12]} · its commit landed before its run stopped: recorded", take_in(requests(db))[2]])
    back = _reviewed_back(conf, r, info)
    red = _since_pick(git, tree, r, info, lines, built=True, db=db, back=back)
    if red:
        return red
    base, files = info['base'], sorted(info['files'])
    try:
        frozen = _sha(tests) if os.path.isdir(tests) else None
    except OSError as fault:   # a test that does not read is not measured, never tests that moved
        return _no(lines, f"not measured: {r['id']}: its tests do not read ({_line(fault)})", f'ls -la {tests} shows the file: chmod u+r it, then RUN AGENT here')
    if frozen is None:   # no tests folder at all is not measured, never tests that moved
        return _no(lines, f"not measured: {r['id']}: its tests folder is not there ({tests})", f"its tests are gone, so it is built anew with new tests: {_kept_aside(tree, db, r['id'])}, {_row_clears(r['id'])}")
    if frozen != r.get('tests_sha'):
        return _no(lines, f"{r['id']}: the tree moved since its review (its tests)", f"see its tests ({tests}): frozen tests that moved are never proven again, so its change goes aside and it goes back to asked, built anew with new tests: {_kept_aside(tree, db, r['id'])}, {_row_clears(r['id'])}")   # never Prove: it refuses tests off their sha (its rule read 2026-10-28)
    if _proof(git, tree, base) != info.get('proof'):
        return _no(lines, f"{r['id']}: its change is not the one proven and read", (f"{back} (what moved stays in the stash, the reviewed change is back whole), then RUN AGENT here: it commits in seconds. Only if what moved must ship: " if back else '') + f"see `git -C {tree} diff {base[:12]}`: the tree moved after its review; to prove and read it again: sqlite3 {db} \"UPDATE requests SET state='{BUILT}' WHERE id='{r['id']}' AND state='reviewed'\", {_row_clears(r['id'], BUILT, 'Prove')}")
    with Writer(conf) as w:
        if w.why:
            return _no(lines, f"{r['id']}: {w.why}", _wait(w.why))
        _side(conf, r, committing=_stamp())
        try:
            added = git('add', '--', *files)
            made = git('-c', 'user.name=THE DAY', '-c', f'user.email={DAY_EMAIL}', 'commit', '-q', '-m',
                       f"{r['id']}: {r['words'] or ''}\n\nBuilt by THE DAY (scrum_master_3's DAY group): tests first {str(r.get('tests_sha') or '')[:12]}, proven, reviewed LEGIT. No Judge, no seal, no publish.") if added.returncode == 0 else added
            if added.returncode != 0 or made.returncode != 0:
                git('restore', '--staged', '--', *files)   # NOTHING LEFT HALF STAGED (its third rule read 2026-10-28): the tree as before its add
                _side(conf, r, committing='')
                return _no(lines, f"{r['id']}: its commit did not land ({_last(added.stderr + made.stderr + made.stdout)[:200]})", f'rm -f "$(git -C {tree} rev-parse --git-dir)/index.lock" (a lock a stopped git left; any other stop is git\'s own words above), then RUN AGENT here')
        except subprocess.TimeoutExpired as fault:   # STOPPED MID COMMIT: it may be staged, it may have landed; his step clears the one, the next run records the other
            return _hung(tree, fault, staged=True)
    commit = _head(git)
    if [m[0] for m in _moved(git, base)] != [commit]:
        return _no(lines, f"{r['id']}: its commit {commit[:12]} is not the one commit past its base", f"{_undone(tree, db, r['id'], base)}, {_row_clears(r['id'])}")
    if not set_state(db, r['id'], READY, "committed, ready for tonight's take-in", when='reviewed', commits=commit, done_at=_stamp()):   # COMMITTED IS READY: ready for tonight's take-in (no day walk: the owner 2026-10-31, "we need to remove it ... we do a full walk at night with the full build")
        return _no(lines, f"{r['id']}: its commit {commit[:12]} landed but a press moved it off reviewed: not recorded", f"sqlite3 {db} \"UPDATE requests SET state='waiting_takein', commits='{commit}' WHERE id='{r['id']}'\", then RUN AGENT here, then on Pick")
    lines.append(f"8 commit · {r['id']} · {commit[:12]} · {len(files)} file(s) by path: {', '.join(files[:4])}" + (f' and {len(files) - 4} more' if len(files) > 4 else ''))
    lines.append(take_in(requests(db))[2])   # THE ORIGINAL ROW 015'S RUN LINE: every request for the take-in with its commit
    return _ok(lines)


def take_in(rows):
    """THE ORIGINAL'S ROW 015 READY LOOK, on this office's own requests: the requests for tonight's take-in (waiting_takein,
    or an approved row from before the day walk was removed), each with its commit; READY MEANS COMMITTED: one with no commit is named, never counted ready. -> (ready, bare, line)"""
    ready = [r for r in rows if r['state'] in (COMMITTED, READY)]
    bare = [r['id'] for r in ready if not str(r.get('commits') or '').strip()]
    line = (f"{len(ready)} for the take-in: " + '; '.join(f"{r['id']} commits {str(r.get('commits') or '').strip()[:12] or 'NONE'}" for r in ready)) if ready else 'a list: nothing waiting for the take-in'
    return ready, bare, (f"not ready: {', '.join(bare)} wait(s) for the take-in with no commit to take in · " if bare else '') + line


def content(store, job_key, block=None):
    """ITS BLOCK, THE ORIGINAL'S ROW 015 READY (words, never markup): the warning row while its newest run is red (the clock, Warning ·, his
    step under it); the request reviewed and waiting for its commit (its built files, its frozen tests, its proof, as its side file holds
    them); then row 015's own list, every request for the take-in with its commit (NONE named: ready means committed)."""
    try:
        rows = requests(store.db_path)
    except sqlite3.Error as e:
        return _not_read(store.db_path, e) + warning(store, job_key)
    reviewed = [r for r in rows if r['state'] == 'reviewed']
    mine = []
    for r in reviewed:
        info = _side(CONF, r)
        files = sorted(info.get('files') or ())
        mine.append({'key': r['id'], 'cells': [r['id'], _words(r), f"{len(files)}: {', '.join(files[:6])}" + (f" and {len(files) - 6} more" if len(files) > 6 else '') if files else 'none recorded',
                                               str(r.get('tests_sha') or '')[:12] or 'none', str(info.get('proof') or '')[:12] or 'none kept', str(r.get('state_at') or '')[:16].replace('T', ' ')]})
    ready, bare, line = take_in(rows)
    walk = {COMMITTED: "committed before the day walk was removed: set it to waiting_takein", READY: "committed, ready for tonight's take-in"}
    listed = [{'key': r['id'], 'cells': [r['id'], _words(r), walk[r['state']], str(r.get('commits') or '').strip()[:12] or 'NONE', str(r.get('done_at') or r.get('state_at') or '')[:16].replace('T', ' ')]} for r in ready]
    return warning(store, job_key) + [
        {'kind': 'table', 'title': 'Reviewed, to commit', 'under': f"{len(reviewed)} reviewed: committed by path on the hot fix tree, only when its tests and its change are still the ones proven and read" if reviewed else 'nothing reviewed: nothing to commit now',
         'columns': ['Request', 'His words', 'Its files', 'Its tests (sha256)', 'Its proof', 'Reviewed'], 'rows': mine, 'empty': 'Nothing to commit now.'},
        {'kind': 'table', 'title': 'For the take-in', 'under': line if bare else (f"{len(ready)} for the take-in" if ready else line),
         'columns': ['Request', 'His words', 'Where it is', 'Commit', 'Since'], 'rows': listed, 'empty': 'a list: nothing waiting for the take-in'}]
