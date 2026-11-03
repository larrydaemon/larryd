"""AGENT 011 · THE REQUESTS (the DAY group, the owner 2026-10-28: "DAY is a group on the top right each should say day / and we should see each /
build each one"; "all of day needs to be rewritten its all hotfix style for the day no judge"): a SUB AGENT of the MARK IV agent (agent001),
lower rank, its own block in the DAY group, its own light and its own run. STEP 1: THE REQUESTS (the original's 004: "its storing the requests or its not storing the requests"): this office's own requests read, each one's swear words taken out as it is read (the owner 2026-10-28: "remove the swear word to keep the system clean"), written back only where they change; red only when they do not read (a write that fails is said on its green line).

THE DAY, STEP BY STEP, each step its own agent (agent011 to agent020; agent021 the backlog): the requests, building now, main first, pick,
build, prove, review, commit (then pick again, one request at a time), the hot fix walk (once for every commit of the day), cleanup. A step
that ends green takes the next step's RUN before it writes its own DONE, and the first run drives the next ones in a loop (the chain the page
hands every run: no agent imports another), so RUN AGENT on THE REQUESTS runs the whole day block by block, and RUN AGENT on any step runs the
day from there. A red step stops there: it is THE RED's, its one step said. ONE DAY AT A TIME: one lock for the whole day, a second press reads the
requests (its own light) and runs no day. ON THE HOT FIX TREE (~/spine_worktrees/hotfix), NO JUDGE, NO SEAL, NO PUBLISH: production takes a change only by his AI ECHO HOTFIX
button, never pressed here. Its requests are this office's own (nothing read from the original). ON RUN AGENT ONLY: never due.

ITS BLOCK IS THE ORIGINAL'S ROW 004 (the owner 2026-10-28: "look at each original agent and rebuild it so it looks like the original agent"):
its green run line is the original's ("N request(s): <state counts, most first> · ... · inbox ..."); ADD REQUEST TO BACKLOG stores his words
at once in this office's requests table (asked, the next R-NNNN and position, his ENVIRONMENT boxes in its environment column); TODAY'S NEW
REQUESTS carries REMOVE, UPDATE and APPROVE (in VERIFY) on each; then INCOMPLETE and REMOVED, every request one line. The BACKLOG table is
agent021's, under it."""
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

KEY = 'the_requests'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
INTERFACE = True   # an interface of its own, ADD REQUEST TO BACKLOG: drawn in the original's markup on both faces (the owner 2026-10-28: "if we need an interfact like to add request it needs to look like the original")
ROW = 4   # the original's row 004
NAME = 'The requests'
CARD_NAME = 'Scrum Master The requests'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = "The requests: stored or not, this office's own, its swear words out"
WHAT = "Reads this office's own requests, takes the swear words out of their words, and says what each stage holds"
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due (frame_red.due_at)
ROW_FILE = 'agent011_day_the_requests.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes: in its own thread, the page answers RUN AGENT at once
NEXT = 'building_now'   # the step it hands on to when it ends green

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


def _git(tree, runner=subprocess.run):
    """git in the tree, every path taken as typed (--literal-pathspecs: a file named with * or ? is that file alone), its bytes kept whole"""
    def git(*args):
        return runner(['git', '--literal-pathspecs', *args], cwd=tree, capture_output=True, text=True, errors='surrogateescape')
    return git


def _status(git, *more):
    """the tree's own status, NUL separated (a path with any byte said whole): [(code, path)]"""
    seen = git('status', '--porcelain=v1', '-z', *more)
    if seen.returncode != 0:   # a status that did not read is never a clean tree (its blind rule read 2026-10-31)
        raise RuntimeError(f'not measured: git status failed ({_last(seen.stderr)[:120]})')
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
        return [dict(zip(('id', 'words', 'state', 'position', 'tests', 'tests_sha', 'commits', 'why', 'done_at'), r))
                for r in con.execute('SELECT id, words, state, position, tests, tests_sha, commits, why, done_at FROM requests ORDER BY position, id')]
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


def _day_lock(conf):
    """THE DAY'S ONE LOCK (two presses never overlap): an fcntl.flock on one file beside the requests' tests, taken without waiting and held
    by the run that drives the day, from its first step to its last. -> its open file, or None when another run holds it"""
    os.makedirs(conf['tests'], exist_ok=True)
    fh = open(os.path.join(conf['tests'], '.day.lock'), 'a+', encoding='utf-8')   # a lock that will not open is its crash, never said as held (run())
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fh.seek(0)
        fh.truncate()
        fh.write(f'{os.getpid()} {_stamp()}')   # the holder named, so a second press says whose day runs
        fh.flush()
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
    until = time.monotonic() + 120   # kept trying for 2 minutes, inside THE RED's 3 minute QUIET (a run left RUNNING past it is red there)
    attempt = 0
    while True:
        try:
            return store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code, said, state)
        except sqlite3.OperationalError as busy:
            if 'locked' not in str(busy) or time.monotonic() >= until:
                raise
            attempt += 1
            time.sleep(min(0.5 * attempt, 5))


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
    """ITS OWN CODE CRASHED: red, named as a crash, its file and line its step"""
    where = _where(fault)
    return {'ok': False, 'lines': [], 'why': f'it crashed at {where} ({_line(fault)})', 'step': f'open app/agent/{where}, fix what the crash names, then RUN AGENT', 'next': None}


def _said(got):
    return {'summary': ('' if got['ok'] else f"FAILED · {got['why']} · {HAND}{got['step']} · ") + ' | '.join(got['lines'][-3:]), **got}   # GREEN SAYS THE ORIGINAL'S RUN LINE AS IT WAS ("670 request(s): ... · inbox ..."), no word before it: the canvas footer draws its DONE


def once(store, job_key, n, agent, chain, conf, runner, hire, db, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step, only when the requests do not read); green, the next step's
    RUN taken first: a next refused or missing is said on its green line, the day stops there. A crash ends FAILED with its line. -> (what it said, the next to run (module, shell, run) or None)"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:   # ITS RULE: green when the requests read, red when they do not (step() says so), and red when its own code crashes, said as a crash
        with Beat(store, job_key):
            got = step(store, conf, runner, db, hire)
    except Exception as fault:   # A CRASH IS RED, NAMED AS ONE: never said as the requests not reading when they did (its blind review 2026-10-28)
        got = _crashed(fault)
    nxt = None
    if got['ok'] and not locked:   # a second press: the requests read (green), the day itself is the other run's, never run twice
        lock = os.path.join(conf['tests'], '.day.lock')
        pid = _pid_in(lock)
        got = {**got, 'next': None, 'lines': got['lines'] + [f"the day not run from here: another DAY run holds its lock (pid {pid or '?'}, `ps -p {pid or '<pid>'} -o command=`)"]}
    if got['ok'] and got.get('next'):   # the next step's RUN, said on this green line when not taken (Building now's own block is its light)
        nxt, why = hand_on(store, chain, got['next'])
        if nxt is None:
            name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or ('Building now' if got['next'] == NEXT else got['next'])
            got = {**got, 'next': None, 'lines': got['lines'] + [f'the day stopped before {name}: {why}']}
    said = _said(got)
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
        said = _said(_crashed(fault))
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


def _ok(lines, nxt=NEXT):
    return {'ok': True, 'lines': lines, 'why': '', 'step': '', 'next': nxt}


BRANCH = 'hold/20261021'   # the hot fix tree's branch, named in the steps that stand it up again


def _rebuilt(tree):
    """HIS ONE COMMAND THAT STANDS THE TREE UP AGAIN"""
    return f'git -C {HOME}/virtual_workspace worktree prune && git -C {HOME}/virtual_workspace worktree add {tree} {BRANCH}'


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

PLAIN = [   # (pattern, its plain word); in this order
    (r"\bmotherfuck\w*", ''), (r"\bwhat the fuck\b", 'what'), (r"\bthe fuck\b", ''), (r"\bfuck(?:ed|ing)? up\b", 'messed up'),
    (r"\bfuck(?:ing|ign|in|en)\b", ''), (r"\bfucked\b", 'messed up'), (r"\bfuck(?:er|ers|s)?\b", ''),
    (r"\bbullshit\b", 'nonsense'), (r"\bshitty\b", 'bad'), (r"\bshit(?:s)?\b", 'junk'), (r"\bcrappy\b", 'bad'), (r"\bcrap\b", 'junk'),
    (r"\bassholes?\b", 'jerk'), (r"\bgoddamn(?:ed)?\b", ''), (r"\bdamn(?:ed|it)?\b", ''), (r"\bwtf\b", ''), (r"\bbitch(?:es|ing)?\b", ''),
]
PLAIN = [(re.compile(p, re.I), w) for p, w in PLAIN]
SWEAR = re.compile(r"\b(?:motherfuck\w*|fuck\w*|bullshit|shit\w*|crap\w*|assholes?|goddamn\w*|damn\w*|wtf|bitch\w*)\b", re.I)


def _case(m, w):
    s = m.group(0)
    return w.upper() if w and s.isupper() and len(s) > 1 else w


def clean(text):
    """only the swear words change: a removed one leaves a mark, and only the space beside a mark is tidied; every other byte stays as typed"""
    if not text or not SWEAR.search(text):
        return text
    t = text
    for rx, w in PLAIN:
        t = rx.sub(lambda m, w=w: _case(m, w) if w else '\x00', t)
    t = SWEAR.sub('\x00', t)   # any word SWEAR still finds that PLAIN has no plain word for (shitload): taken out too
    t = re.sub(r"[ \t]*\x00[ \t]*(?=[,.;:!?\"')\]]|$)", '', t, flags=re.M)   # a removed word before a mark or the line's end: no space left
    t = re.sub(r"(^|(?<=[\"'(\[]))[ \t]*\x00[ \t]*", '', t, flags=re.M)   # at a line's or a quote's start: no space left
    t = re.sub(r"[ \t]*\x00[ \t]*", ' ', t)   # between two words: one space
    return t


def _cleaned(db, rows):
    """THE SWEAR WORDS OUT OF HIS STORED REQUESTS (the owner 2026-10-28: "i dont want the swear words stored in the system"): each request's
    words cleaned as they are read, written back only where they change (a press between the read and the write wins). -> how many"""
    con = sqlite3.connect(db, timeout=10)
    n = 0
    try:
        with con:
            for r in rows:
                words = r['words']
                plain = clean(words) if isinstance(words, str) else words
                if plain != words:
                    n += con.execute('UPDATE requests SET words = ? WHERE id = ? AND words = ?', (plain, r['id'], words)).rowcount
                    r['words'] = plain
    finally:
        con.close()
    return n


COLUMNS = {'id': 'TEXT', 'words': "TEXT NOT NULL DEFAULT ''", 'state': 'TEXT', 'position': 'INTEGER NOT NULL DEFAULT 0', 'tests': 'TEXT', 'tests_sha': 'TEXT',
           'commits': 'TEXT', 'why': 'TEXT', 'done_at': 'TEXT'}   # a column its read needs, as ALTER TABLE takes it back: every row kept
TABLE = ("CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY NOT NULL, words TEXT NOT NULL, hash TEXT NOT NULL, source TEXT CHECK (source IN ('session', 'sprint', 'order')), "
         "ref TEXT, asked_at TEXT NOT NULL, position INTEGER NOT NULL, state TEXT CHECK (state IN ('asked', 'planned', 'building', 'proven', 'reviewed', 'waiting_takein', 'approved', "
         "'taken_in', 'green', 'shipped', 'stuck_today', 'removed')), state_at TEXT NOT NULL, why TEXT, tests TEXT, tests_sha TEXT, commits TEXT, done_at TEXT, "
         "environment TEXT CHECK (environment IS NULL OR json_valid(environment)))")   # the table as this office holds it


def _read_step(db, fault):
    """HIS ONE STEP FOR A READ THAT FAILED: its own SELECT, which prints the error it met, then the one line that clears that error"""
    words = str(fault)
    column = re.search(r'no such column: (\w+)', words)
    if 'locked' in words:
        fix = f'database is locked clears when the other writer ends (lsof {db} names it)'
    elif column and column.group(1) in COLUMNS:
        fix = f'no such column: sqlite3 {db} "ALTER TABLE requests ADD COLUMN {column.group(1)} {COLUMNS[column.group(1)]}" (every row kept)'
    elif 'no such table' in words:
        fix = f'no such table: sqlite3 {db} "{TABLE}" (it stands up empty: the rows that went with it are not in it)'
    else:
        fix = 'what it prints is the database file itself: put the last good copy of it back'
    return f"sqlite3 {db} 'SELECT id, words, state, position, tests, tests_sha, commits, why, done_at FROM requests LIMIT 1' (its own read: the error it prints is the one it met); {fix}; then RUN AGENT"


def step(store, conf, runner, db, hire):
    try:
        rows = requests(db)
    except sqlite3.Error as e:
        return _no([], f"the requests do not read ({type(e).__name__}: {str(e)[:120]})", _read_step(db, e))
    try:
        cleaned = _cleaned(db, rows)
        unwritten = ''
    except sqlite3.Error as e:   # the rule: red only when the requests do not read; a write that fails is said on the green line
        cleaned, unwritten = 0, f" · the swear words could not be written out ({type(e).__name__}: {str(e)[:120]}): sqlite3 {db} 'SELECT count(*) FROM requests', then RUN AGENT"
    try:
        left = sum(1 for r in requests(db) if isinstance(r['words'], str) and SWEAR.search(r['words']))   # read again: what is still stored
    except sqlite3.Error as e:
        left = f'unknown ({type(e).__name__})'
    return _ok([summary(rows) + f" · {cleaned} cleaned of swear words, {left} still holding one" + unwritten])


# ============ THE ORIGINAL'S ROW 004 ON THIS CANVAS (the owner 2026-10-28: "look at each original agent and rebuild it so it looks like the
# original agent but in our new shell frame structure"): its run line, ADD REQUEST TO BACKLOG with its ENVIRONMENT boxes, TODAY'S NEW
# REQUESTS with REMOVE / UPDATE / APPROVE on each, the INCOMPLETE and REMOVED lists; every one read from and written to THIS office's own
# requests table (instance/scrum_master_3.db), never the original's.
ZONE = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
PRESSES = ('add', 'remove', 'update', 'approve')   # its own buttons, by name (the page's agent_press route runs press for these alone)
LISTS = ('environment',)   # a field that always comes as a list: his ENVIRONMENT boxes
FROM_THE_BOX = 'the owner, typed in ADD REQUEST TO BACKLOG'   # a request's ref when it came from his page (its source stays session, as the original's)
ENVIRONMENTS = (('localhost_rnd', 'localhost', 'rnd'), ('localhost_pf', 'localhost', 'pf'), ('production_rnd', 'production', 'rnd'),
                ('production_pf', 'production', 'pf'), ('agent_larryd', 'agent', 'larryd'), ('native_ios', 'native', 'ios'), ('native_macos', 'native', 'macos'))   # the original's shared_developer.ENVIRONMENTS, word for word
OFF_BY_DEFAULT = ('native_ios', 'native_macos')   # the native boxes start unchecked (the owner 2026-10-24: "do not check these automatically")
NOTES = {'agent': '(if agent)', 'native': '(if only that build)'}
GLOBAL_CONFIG = os.path.join(HOME, 'virtual_workspace', 'global_config.json')   # the platform's own file: the sprint slots by name (tower.sprint.slots)
SWAPS = os.path.join(HOME, 'virtual_workspace', 'lryllm', 'lryllm', 'instance', 'tower', 'swaps.jsonl')   # the swap's own log: which slot is live
STATUS = (('WAITING', ('asked', 'stuck_today')), ('BUILDING', ('planned', 'building', 'proven', 'reviewed', 'approved')), ('VERIFY', ('waiting_takein',)))   # HIS STATUSES, this office's states: picked (planned) and committed waiting for the walk (approved) are the DAY's hands, walked READY (waiting_takein) is his to look at
CLOSED = ('green', 'shipped', 'taken_in')   # done: never on the work list
GONE = ('removed',)   # removed by him: its record stays and says so
APPROVED = 'green'   # HIS APPROVE closes it: this office's 'approved' is the DAY's own (committed, waiting for the walk), so his verdict writes green, never approved (the walk would take it again)
BY_HIS_PAGE = 'on his page'


def _moment(text):
    """an ISO moment with its zone (one with no zone is New York's), or None"""
    try:
        got = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return got if got.tzinfo else got.replace(tzinfo=ZONE)


def _all(db):
    """EVERY REQUEST OF THIS OFFICE, in build order, with what the page draws. sqlite3.Error: they do not read."""
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=10)
    try:
        cols = ('id', 'words', 'state', 'asked_at', 'state_at', 'why', 'commits', 'environment', 'position')
        return [dict(zip(cols, r)) for r in con.execute(f"SELECT {', '.join(cols)} FROM requests ORDER BY position, id")]
    finally:
        con.close()


def summary(rows):
    """THE ORIGINAL'S RUN LINE (its agent004 summary + look): how many requests in each state, most first; then what this office keeps
    of the rest: no B items, no heard list and no inbox (a request is stored by ADD REQUEST TO BACKLOG the moment he presses Add)."""
    if not rows:
        return 'asked for nothing: no request yet · no B items kept here · no heard list kept here · inbox: none, ADD REQUEST TO BACKLOG stores each request at its press'
    by = {}
    for r in rows:
        by[r['state']] = by.get(r['state'], 0) + 1
    states = ', '.join(f"{n} {str(s).replace('_', ' ')}" for s, n in sorted(by.items(), key=lambda kv: (-kv[1], str(kv[0]))))
    return (f'{len(rows)} request(s): {states} · no B items kept here · no heard list kept here'
            ' · inbox: none, ADD REQUEST TO BACKLOG stores each request at its press')


def production_name(config=GLOBAL_CONFIG, swaps=SWAPS):
    """THE PRODUCTION BOX'S NAME, as the original's: the sprint slot (the other one of tower.sprint.slots from the live one the swap's log names,
    before any swap tower.swap.start), its letter and its sprint (B · LARRY 6); '' when the platform's files do not say it."""
    try:
        with open(config, encoding='utf-8') as fh:
            tower = json.load(fh).get('tower') or {}
        slots = (tower.get('sprint') or {}).get('slots') or {}
        try:
            with open(swaps, encoding='utf-8') as fh:
                rows = [json.loads(x) for x in fh if x.strip()]
        except FileNotFoundError:
            rows = []
        moved = [r for r in rows if r.get('result') in ('committed', 'rolled back', 'ROLLBACK FAILED')]
        if moved and moved[-1]['result'] == 'ROLLBACK FAILED':
            return ''
        flips = [r for r in rows if r.get('result') == 'committed' and r.get('to') in slots]
        live = flips[-1]['to'] if flips else (tower.get('swap') or {}).get('start')
        others = [s for s in slots if s != live]
        if live not in slots or len(others) != 1:
            return ''
        sprint = (slots.get(others[0]) or {}).get('name')
        return others[0].split('-')[-1].upper() + (f' · {sprint}' if sprint else '')
    except (OSError, ValueError, AttributeError, TypeError):
        return ''


def environment_of(r):
    """THE BOXES HE LEFT CHECKED for one request, in ENVIRONMENTS' order; one with none kept is every box as they stand by default"""
    try:
        got = json.loads(r.get('environment') or 'null')
    except (TypeError, ValueError):
        got = None
    keys = [k for k, _e, _s in ENVIRONMENTS]
    return [k for k in keys if k not in OFF_BY_DEFAULT] if not isinstance(got, list) else [k for k in keys if k in got]


def environment_line(r):
    """one request's places in a few words: localhost rnd · pf · production rnd · pf · agent larryd"""
    keep, parts = environment_of(r), []
    for place in dict.fromkeys(e for _k, e, _s in ENVIRONMENTS):
        sides = [side for k, e, side in ENVIRONMENTS if e == place and k in keep]
        if sides:
            parts.append(f"{place} {' · '.join(sides)}")
    return ' · '.join(parts) or 'none'


def environment_boxes(prod=None):
    """THE ENVIRONMENT BOXES, the form part's rows: one line a place, its boxes, every one checked but the native ones"""
    prod = production_name() if prod is None else prod
    out = []
    for key, place, side in ENVIRONMENTS:
        if not out or out[-1]['key'] != place:
            out.append({'key': place, 'label': f'{place} ({prod})' if place == 'production' and prod else place, 'note': NOTES.get(place, ''), 'boxes': []})
        out[-1]['boxes'].append({'value': key, 'label': side, 'checked': key not in OFF_BY_DEFAULT})
    return out


def status_of(state):
    return next((word for word, states in STATUS if state in states), '')


def test_url(words):
    """THE LINK TO TEST IT, as the original's: the newest page address in his words that is not production A, or ''"""
    found = [u.rstrip('.,;)') for u in re.findall(r'https?://[^\s<>"\']+', str(words or ''))]
    found = [u for u in found if not re.match(r'https?://(?:www\.)?positivefeedback\.(?:ai|com)(?:[/?#]|$)', u)]
    return found[-1] if found else ''


def pending(rows, now=None):
    """THE DAY'S NEW REQUESTS AND THE BACKLOG, the original's requests_pending: every request not done and not removed, asked today ('today')
    or before ('backlog'); stuck today goes down to the backlog; build order kept."""
    now = now or _now()
    out = {'today': [], 'backlog': []}
    for r in rows:
        if r['state'] in CLOSED + GONE:
            continue
        at_ = _moment(r['asked_at'])
        today = bool(at_ and at_.astimezone(ZONE).date() == now.astimezone(ZONE).date())
        out['today' if today and r['state'] != STUCK else 'backlog'].append({**r, 'today': today})
    return out


def request_row(r, presses=True):
    """ONE REQUEST AS THE ORIGINAL'S TABLE ROW: Request (id · when, where the work goes), His words, Status now (his status, the why, its
    time counting from when it began), and its presses: REMOVE, UPDATE with his words, APPROVE in VERIFY; TEST IT on its copy line."""
    at_ = _moment(r['asked_at'])
    when = at_.astimezone(ZONE).strftime('%H:%M' if r.get('today') else '%Y-%m-%d %H:%M') if at_ else ''
    word = status_of(r['state']) or str(r['state'] or '').upper().replace('_', ' ')
    since = _moment(r['asked_at'] if word == 'WAITING' else r['state_at']) or at_
    why = ' '.join(str(r['why'] or '').split())
    status = {'word': word, 'text': why[:240], 'label': f'{word} TIME:', **({'since': since.isoformat()} if since else {})}   # the original's status cell: its word, its why, its time
    row = {'key': r['id'], 'cells': [{'text': f"{r['id']} · {when}", 'note': environment_line(r)}, {'text': str(r['words'] or '').strip(), 'mono': True}, status]}
    if word == 'VERIFY':
        url = test_url(r['words'])
        row['copy'] = f'TEST IT: {url}' if url else 'TEST IT: no page named in the request: put its address in an UPDATE'
    if presses:
        row['presses'] = [{'do': 'remove', 'label': 'REMOVE', 'cell': 0, 'confirm': f"Remove {r['id']}? It is marked removed by you; its words and history stay."},
                          {'do': 'update', 'label': 'UPDATE', 'cell': 1, 'text': True, 'placeholder': 'update: what you looked for and did not see'}]
        if word == 'VERIFY':
            row['presses'].append({'do': 'approve', 'label': 'APPROVE', 'cell': 2})
    return row


def _one_request(con, rid):
    got = con.execute('SELECT id, words, state, state_at, done_at FROM requests WHERE id = ?', (rid,)).fetchone()
    return dict(zip(('id', 'words', 'state', 'state_at', 'done_at'), got)) if got else None


def remove_request(db, rid, now=None):
    """REMOVE (the original's remove_request): its state removed, its why says he removed it on his page, when, and what it was until then;
    its words and history stay. Never a delete. -> the line said on its shell"""
    rid, now = str(rid or '').strip(), now or _now()
    if not re.fullmatch(r'R-\d{4,}', rid):
        return f'REMOVE refused · {rid or "nothing"} is not a request id'
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            r = _one_request(con, rid)
            if not r:
                return f'REMOVE refused · {rid}: no such request'
            if r['state'] in CLOSED + GONE:
                return f"REMOVE refused · {rid} is {r['state'].replace('_', ' ')} already: nothing to remove"
            since = str(r['state_at'] or '')[:16].replace('T', ' ')
            why = (f"REMOVED BY THE OWNER {BY_HIS_PAGE} {now.strftime('%Y-%m-%d %H:%M')}: no longer wanted; it was {r['state'].replace('_', ' ')}"
                   + (f' since {since}' if since else '') + '; its words, commits and history stay')
            con.execute('UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state = ?', ('removed', now.isoformat(timespec='seconds'), why[:500], rid, r['state']))
    finally:
        con.close()
    return f'REMOVED · {rid} · marked removed by you, never deleted'


def update_request(db, rid, words, now=None):
    """HIS UPDATE (the original's update_request): his words added under the request's as "UPDATE <moment>: <words>" (the words before never
    edited, the swear words out as THE REQUESTS keeps every request), and it goes back to the backlog to be built again by the next DAY run.
    One the DAY holds on the tree right now keeps its state (its change is on the tree): his words are kept under it. -> the line said"""
    rid, now = str(rid or '').strip(), now or _now()
    words = clean(str(words or '').replace('\r\n', '\n').replace('\r', '\n'))
    if not re.fullmatch(r'R-\d{4,}', rid):
        return f'UPDATE refused · {rid or "nothing"} is not a request id'
    if not words.strip():
        return f'UPDATE refused · {rid}: an update needs your words'
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            r = _one_request(con, rid)
            if not r:
                return f'UPDATE refused · {rid}: no such request'
            if r['state'] in GONE:
                return f'UPDATE refused · {rid} was removed by you: removed is final, add it again as a new request'
            moment = now.strftime('%Y-%m-%d %H:%M')
            con.execute('UPDATE requests SET words = words || ? WHERE id = ? AND state IS NOT ?', (f'\n\nUPDATE {moment}: {words.strip()}', rid, 'removed'))
            if r['state'] in IN_HAND + (COMMITTED,):
                return f"UPDATED · {rid} · your words kept under its words; it stays {r['state']}: the DAY holds its change on the tree now"
            con.execute('UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state = ?',
                        (WAITING, now.isoformat(timespec='seconds'), f'UPDATED BY THE OWNER {BY_HIS_PAGE} {moment}: back in the backlog, built again with his update by the next DAY run', rid, r['state']))
    finally:
        con.close()
    return f'UPDATED · {rid} · your words kept under its words; back in the backlog for the next DAY run'


def approve_request(db, rid, now=None):
    """HIS APPROVE IN VERIFY (the original's verdict_request, approve): a request walked READY (waiting_takein) is done: green, its why says
    he approved it on his page and when. Refused: not an id, no such request, not in VERIFY. -> the line said"""
    rid, now = str(rid or '').strip(), now or _now()
    if not re.fullmatch(r'R-\d{4,}', rid):
        return f'APPROVE refused · {rid or "nothing"} is not a request id'
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            r = _one_request(con, rid)
            if not r:
                return f'APPROVE refused · {rid}: no such request'
            if r['state'] != READY:
                return f"APPROVE refused · {rid} is {str(r['state']).replace('_', ' ')}, not in VERIFY: nothing to approve"
            con.execute('UPDATE requests SET state = ?, state_at = ?, why = ?, done_at = COALESCE(done_at, ?) WHERE id = ? AND state = ?',
                        (APPROVED, now.isoformat(timespec='seconds'), f"APPROVED BY THE OWNER {BY_HIS_PAGE} {now.strftime('%Y-%m-%d %H:%M')}: done", now.isoformat(timespec='seconds'), rid, READY))
    finally:
        con.close()
    return f'APPROVED · {rid} · done'


def add_request(db, words, environment=None, now=None):
    """ADD REQUEST TO BACKLOG (the original's add_request): his words (the swear words out, the owner 2026-10-28: "i dont want the swear words
    stored in the system"), stored at once in this office's own requests table: the next R-NNNN, the next position, asked, where the work goes
    (the boxes he left checked, a JSON list). Refused: no words, or every box unchecked. -> the line said"""
    now = now or _now()
    words = clean(str(words or '').replace('\r\n', '\n').replace('\r', '\n'))
    if not words.strip():
        return 'ADD refused · a request is your words: the box was empty'
    keys = None
    if environment is not None:
        keys = [k for k, _e, _s in ENVIRONMENTS if k in environment]
        if not keys:
            return 'ADD refused · check at least one environment: it is where the work goes'
    asked = now.isoformat(timespec='seconds')
    digest = hashlib.sha256(json.dumps(['session', words, asked], ensure_ascii=False).encode('utf-8')).hexdigest()   # the original's request_hash
    con = sqlite3.connect(db, timeout=10)
    try:
        con.execute('BEGIN IMMEDIATE')
        if con.execute('SELECT 1 FROM requests WHERE hash = ?', (digest,)).fetchone():
            con.rollback()
            return 'ADD refused · the same request is kept already'
        top = max([int(m.group(1)) for (i,) in con.execute('SELECT id FROM requests') for m in [re.fullmatch(r'R-(\d+)', str(i))] if m] or [0])
        rid = f'R-{top + 1:04d}'
        con.execute('INSERT INTO requests (id, words, hash, source, ref, asked_at, position, state, state_at, environment) '
                    'VALUES (?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(position), 0) + 1 FROM requests), ?, ?, ?)',
                    (rid, words, digest, 'session', FROM_THE_BOX, asked, WAITING, asked, json.dumps(keys) if keys is not None else None))
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()
    return f"ADDED · {rid} · asked, in the backlog for the next DAY run · {environment_line({'environment': json.dumps(keys) if keys is not None else None})}"


def press(store, job_key, do, fields=None, now=None):
    """ITS BUTTONS: add (ADD REQUEST TO BACKLOG: words, environment, environment_said), remove, update (words), approve (each the request's id
    as value). -> the one line said on its shell"""
    if do not in PRESSES:
        raise ValueError(f'not one of its presses: {do!r}')
    fields = fields or {}
    one = lambda k: (fields.get(k) or [''])[0] if isinstance(fields.get(k), list) else (fields.get(k) or '')   # noqa: E731
    try:
        if do == 'add':
            env = fields.get('environment') or []
            env = [env] if isinstance(env, str) else list(env)
            return add_request(store.db_path, one('words'), env if one('environment_said') else None, now)
        if do == 'remove':
            return remove_request(store.db_path, one('value'), now)
        if do == 'update':
            return update_request(store.db_path, one('value'), one('words'), now)
        return approve_request(store.db_path, one('value'), now)
    except sqlite3.Error as e:
        return f"{do.upper()} not written · the requests do not write ({_line(e)}) · {HAND}sqlite3 {store.db_path} 'SELECT count(*) FROM requests'"


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS, the original's row 004 below its run line (the run line is its run's summary, drawn by the canvas foot):
    ADD REQUEST TO BACKLOG (his words, the ENVIRONMENT boxes), TODAY'S NEW REQUESTS · THE SCRUM MASTER BUILDS IT FROM HERE · N (each with REMOVE,
    UPDATE, APPROVE in VERIFY), then INCOMPLETE · N and REMOVED · N, every request one line, in build order. Words, never markup."""
    form = {'kind': 'form', 'title': 'ADD REQUEST TO BACKLOG', 'do': 'add', 'name': 'words', 'rows': 8, 'label': 'Add',
            'placeholder': 'your request, in your words · Enter adds it · Shift+Enter starts a new line',
            'boxes': {'title': 'ENVIRONMENT · WHERE THE WORK GOES · A HOT FIX, A DIRECT EDIT', 'name': 'environment', 'rows': environment_boxes()}}
    try:
        rows = _all(store.db_path)
    except sqlite3.Error as e:
        return [form, {'kind': 'note', 'title': "TODAY'S NEW REQUESTS · THE SCRUM MASTER BUILDS IT FROM HERE",
                       'text': f"the requests cannot be read ({type(e).__name__}) · {HAND}sqlite3 {store.db_path} 'SELECT count(*) FROM requests'"}]
    nr = pending(rows)
    today = {'kind': 'table', 'clarity': True, 'title': f"TODAY'S NEW REQUESTS · THE SCRUM MASTER BUILDS IT FROM HERE · {len(nr['today'])}",
             'columns': ['Request', 'His words', 'Status now'], 'rows': [request_row(r) for r in nr['today']], 'empty': 'no new request pending today'}
    incomplete = [r for r in rows if r['state'] not in CLOSED + GONE]
    removed = [r for r in rows if r['state'] in GONE]

    def item(r):   # one request as the original's folded line: its id, state and since, his words cut short; open: his words whole and the why
        at_ = _moment(r['state_at'])
        words = ' '.join(str(r['words'] or '').split())
        return {'summary': f"{r['id']} · {str(r['state'] or '').upper().replace('_', ' ')}" + (f" · since {at_.astimezone(ZONE).strftime('%b %d %H:%M')}" if at_ else ''),
                'short': f"{words[:70]}{'…' if len(words) > 70 else ''}", 'body': str(r['words'] or '').strip(), 'note': ' '.join(str(r['why'] or '').split())}
    lists = {'kind': 'list', 'title': '4 · THE REQUESTS',
             'groups': [(f'INCOMPLETE · {len(incomplete)}', [item(r) for r in incomplete], 'every request is closed'),
                        (f'REMOVED · {len(removed)}', [item(r) for r in removed], 'nothing removed')]}
    return [form, today, lists]
