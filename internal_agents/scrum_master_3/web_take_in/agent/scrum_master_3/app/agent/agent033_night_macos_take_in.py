"""AGENT 028 · NIGHT · MACOS · TAKE IN (the owner 2026-10-31: "lets focus the night on 3 builds web, iphone, macos / in that order";
"why cant all 3 be broken into 3 parts / take in / build / publish"; "green light comrade build it all for the night"): a SUB AGENT of the
MARK IV agent (agent001), its own block in the NIGHT group, its own light and its own run. The Mac app written from the web code of the night (the write of the iPhone take in serves it)

THE NIGHT, nine agents in three builds, each take in, build, publish: WEB (take in, build, publish), IPHONE (take in, build, publish), MACOS
(take in, build, publish). The web take in starts by itself at 01:00 New York; every other one runs when the step before it ends green (it
takes the next step's RUN before it writes its own DONE, the chain the page hands every run: no agent imports another), so RUN AGENT on any
step runs the night from there. A red step stops the night there, its one step said. ONE NIGHT AT A TIME: one lock for the whole night; the
night never runs while a DAY run or the hot fix utility holds the tree (both use the simulator and the workspace). The tower's own steps
run through the step runner at the end of this file (the night chain's own code, core_engine.auto); nothing goes to live pf, and the A to B swap is the owner's."""
import datetime
import fcntl
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import threading
import time
import traceback
import zoneinfo

KEY = 'night_macos_take_in'
SLOT = 'NIGHT'   # its group: NIGHT, worn at its block's top right
ROW = 30   # the original's row it takes over (0: none)
NAME = 'macOS take in'
CARD_NAME = 'Scrum Master macOS take in'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'macOS take in: the Mac app written from the web code of the night (the write of the iPhone take in serves it)'
WHAT = 'The Mac app written from the web code of the night (the write of the iPhone take in serves it)'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # runs when the step before it ends green, or on RUN AGENT
ROW_FILE = 'agent028_night_macos_take_in.py'   # its program's file: its skills index is filed under it
BACKGROUND = True   # its run (and the steps after it) works for minutes to hours: in its own thread, the page answers RUN AGENT at once
NEXT = 'night_macos_build'   # the step it hands on to when it ends green

HOME = os.path.expanduser('~')
PY = os.path.join(HOME, 'virtual_workspace', '.venv', 'bin', 'python')
CONF = {'night': os.path.join(HOME, 'scratch', 'tests', 'night'),   # the night's lock and its own files, outside every virtual folder
        'workspace': os.path.join(HOME, 'virtual_workspace'),
        'tower_app': os.path.join(HOME, 'virtual_workspace', 'lryllm', 'lryllm', 'app'),   # where the tower's steps run (LARRY LLM's app/)
        'step': os.path.abspath(__file__),   # this very file runs the tower's steps (its own runner at its end)
        'reruns': os.path.join(HOME, 'spine_scratch', 'tower_auto', 'reruns'),   # the step runner's results (auto.reports_dir()/reruns)
        'day_lock': os.path.join(HOME, 'scratch', 'tests', 'day', '.day.lock'),
        'utility_lock': os.path.join(HOME, 'spine_scratch', 'hotfix_runs', 'running.lock'),
        'seconds': 3600}
HAND = 'YOUR 3 MIN: '
BEAT = 60   # seconds between two heartbeats of a working run
TOOK = 'the write about 3 s to minutes'   # its measured or expected time, said on every red (the owner's measured exceptions: the Judge, the native builds, the walks)


# ---- small pieces
def _now():
    return datetime.datetime.now(zoneinfo.ZoneInfo('America/New_York'))


def _line(fault):
    return (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]


def _where(fault):
    tb = traceback.extract_tb(fault.__traceback__)
    mine = [f for f in tb if f.filename == os.path.abspath(__file__)] or tb
    return f'{os.path.basename(mine[-1].filename)} line {mine[-1].lineno}' if mine else os.path.basename(__file__)


def _ok(lines, nxt=NEXT):
    return {'ok': True, 'lines': lines, 'why': '', 'step': '', 'next': nxt}


def _no(lines, why, step):
    return {'ok': False, 'lines': lines, 'why': why, 'step': step, 'next': None}


def _crashed(fault):
    where = _where(fault)
    return _no([], f'it crashed at {where} ({_line(fault)})', f'open {where}, fix what the crash names, then RUN AGENT')


def _ended(got):
    return {'summary': ('DONE · ' if got['ok'] else f"FAILED · {got['why']} · {HAND}{got['step']} · ") + ' | '.join(got['lines'][-3:]), **got}


def _tail(text, most=300):
    lines = [l for l in str(text or '').strip().splitlines() if l.strip()]
    return (lines[-1] if lines else '')[:most]


def _held(path):
    """another run holds this flock now (tried without waiting, let go at once)"""
    if not os.path.exists(path):
        return False
    with open(path, 'a+', encoding='utf-8') as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fh, fcntl.LOCK_UN)
            return False
        except BlockingIOError:
            return True


def _alive_pid(path):
    try:
        pid = int(open(path).read().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return 0


def _busy(conf):
    """THE TREE IS ANOTHER RUN'S NOW: a DAY run (its lock) or the hot fix utility (its pid): the night waits, red, never two writers"""
    if _held(conf['day_lock']):
        return f"a DAY run holds its lock ({conf['day_lock']})", f"let it end (the DAY block says RUNNING), then RUN AGENT here"
    pid = _alive_pid(conf['utility_lock'])
    if pid:
        return f'the hot fix utility is running (pid {pid})', 'let it end (ps -p %d), then RUN AGENT here' % pid
    return None


def tower(conf, runner, *args):
    """ONE OR MORE OF THE NIGHT CHAIN'S OWN STEPS through the step runner at the end of this file, as the chain runs them. -> (exit code, its results by step, its last line)
    exit 0 every step passed; 1 a step red (the chain stops there); 2 refused; 3 busy (the tower's lock or the utility's own run)"""
    done = runner([PY, conf['step'], 'step', *args], cwd=conf['tower_app'], capture_output=True, text=True, timeout=conf['seconds'],
                  env={**os.environ, 'PYTHONPATH': '.', 'PYTHONDONTWRITEBYTECODE': '1'})
    results = {}
    for ln in (done.stdout or '').splitlines():
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get('written'):
            try:
                with open(e['written'], encoding='utf-8') as fh:
                    r = json.load(fh)
                results[r['step']] = r
            except (OSError, ValueError, KeyError):
                pass
    return done.returncode, results, _tail((done.stdout or '') + '\n' + (done.stderr or ''))


def said_steps(results):
    return [f"{s} {'pass' if r.get('ok') else 'FAIL'}" + ('' if r.get('ok') else f": {str(r.get('why') or '')[:160]}") + f" · {str(r.get('commit') or '')[:12]}" for s, r in results.items()]


def tower_red(code, results, last, steps, again):
    """the one red of a tower step: the first step that did not pass, its why, the step that runs it alone"""
    bad = next((s for s in steps if s in results and not results[s].get('ok')), None)
    if code == 3:
        return f'the tower is busy ({last})', f'let that run end, then RUN AGENT here'
    if code == 2:
        return f'the tower refused the step ({last})', f'read its line, clear what it names, then RUN AGENT here'
    if bad:
        return f"{bad} FAILED: {str(results[bad].get('why') or last)[:240]}" + judged(results[bad]), f'{again} (that step alone; {TOOK})'
    return f'it ended {code} with no step result: {last}', f'{again} ({TOOK})'


def judged(r):
    """a red Judge's own words: its failed rules by name, read from its report (the step itself says no reason)"""
    try:
        from glob import glob
        runs = sorted(glob(os.path.join(HOME, 'virtual_sanity_records', 'judge', 'reports', 'runs', f"*_{str(r.get('commit', ''))[:12]}_*.json")))
        with open(runs[-1], encoding='utf-8') as fh:
            rules = json.load(fh).get('rules') or []
        bad = [f"{x.get('rule')}: {'; '.join(x.get('evidence') or [])[:200]}" for x in rules if x.get('status') == 'FAIL']
        return (' · the Judge: ' + ' | '.join(bad)[:400]) if bad else ''
    except (OSError, ValueError, IndexError):
        return ''


def red_heals(got):
    """a red a code fix can clear: handed to the heal"""
    return {**got, 'heal': True}


def again_line(conf, *args):
    return f"cd {conf['tower_app']} && PYTHONPATH=. {PY} {conf['step']} step {' '.join(args)}"


# ---- THE HEAL (the owner 2026-10-31: "if this happens it should use claude code to fix the issue and do it again"): a red that a code fix
# can clear becomes a FIX request at the top of DAY's backlog; DAY builds it with Claude Code (tests first, proven, read blind, committed), then
# the run starts again from its first step, so the fix is taken in and judged. At most HEALS rounds a day; a red that waits is never healed.
HEALS = 2
START = 'night_web_take_in'   # where a healed run starts again


def _heal_file(conf):
    return os.path.join(conf['night'], 'heal.json')


def _heals_today(conf):
    try:
        with open(_heal_file(conf), encoding='utf-8') as fh:
            got = json.load(fh)
    except (OSError, ValueError):
        return 0
    return int(got.get('tries', 0)) if got.get('day') == _now().date().isoformat() else 0


def _heal_count(conf, n):
    os.makedirs(conf['night'], exist_ok=True)
    with open(_heal_file(conf), 'w', encoding='utf-8') as fh:
        json.dump({'day': _now().date().isoformat(), 'tries': n}, fh)


def _ask(db, words):
    """a FIX request at the top of DAY's backlog -> its id"""
    import hashlib
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            top, first = con.execute('SELECT max(cast(substr(id, 3) AS integer)), min(position) FROM requests').fetchone()
            rid, at = f'R-{(top or 0) + 1:04d}', _now().isoformat(timespec='seconds')
            con.execute('INSERT INTO requests (id, words, hash, source, ref, asked_at, position, state, state_at, why) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (rid, words, hashlib.sha256(words.encode()).hexdigest(), 'order', '', at, (first or 1) - 1, 'asked', at, f'asked by {NAME}: its run was red'))
        return rid
    finally:
        con.close()


def _state(db, rid):
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=10)
    try:
        row = con.execute('SELECT state, why FROM requests WHERE id = ?', (rid,)).fetchone()
        return row or ('', '')
    finally:
        con.close()


def heal(store, agent, chain, conf, got):
    """THE RED HANDED TO CLAUDE CODE THROUGH DAY. -> (lines, the step to start again from, or None)"""
    tries = _heals_today(conf)
    if tries >= HEALS:
        return [f'not healed: {HEALS} fix rounds today already, it stays red for the owner'], None
    pick = next(((m, sh) for m, sh in (chain or ()) if getattr(m, 'KEY', '') == 'pick'), None)
    if pick is None or not pick[1].get('on', True):
        return ['not healed: DAY is not on (its Pick is switched off or not in the chain)'], None
    _heal_count(conf, tries + 1)
    db = store.db_path
    words = (f"FIX · {NAME} went red in the {SLOT}: {got['why']} · Its own step: {got['step']} · Find the cause in the code or the data it names and "
             f"fix it, so {NAME} passes when it runs again. Heal round {tries + 1} of {HEALS}.")
    rid = _ask(db, words)
    lines = [f'heal · {rid} asked: DAY builds the fix with Claude Code (round {tries + 1} of {HEALS})']
    module, sh = pick
    try:
        ok, text = store.run(sh['id'])
    except Exception as fault:   # noqa: BLE001
        return lines + [f'not healed: DAY did not take its RUN ({_line(fault)})'], None
    if not ok:
        return lines + [f'not healed: DAY refused its RUN ({text})'], None
    m = re.search(r'RUN (\d+)', str(text))
    module.run(store, sh['job_key'], int(m.group(1)) if m else 0, agent, store.board(), chain=chain)   # DAY, whole: pick, build, prove, review, commit, cleanup
    state, why = _state(db, rid)
    if state not in ('approved', 'waiting_takein'):
        return lines + [f'not healed: DAY left {rid} {state or "unknown"} ({str(why)[:160]})'], None
    return lines + [f'heal · {rid} committed by DAY: the {SLOT} starts again from its first step'], START


# ---- the run
class Beat:
    """A LONG STEP'S HEARTBEAT: its RUN written RUNNING again every BEAT seconds, so THE RED never takes a working run for a stuck one"""
    def __init__(self, store, job_key):
        self.store, self.job_key, self.stop, self.thread = store, job_key, threading.Event(), None

    def __enter__(self):
        def beat():
            while not self.stop.wait(BEAT):
                try:
                    self.store._edit(self.job_key, {'run_state': 'RUNNING'}, run=True)
                except Exception:   # noqa: BLE001  (a missed beat is one minute)
                    pass
        if self.job_key and hasattr(self.store, '_edit'):
            self.thread = threading.Thread(target=beat, daemon=True)
            self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        if self.thread:
            self.thread.join()


def _lock_path(conf):
    return os.path.join(conf['night'], '.night.lock')


def _night_lock(conf):
    """THE NIGHT'S ONE LOCK: taken without waiting by the run that drives the night, held from its first step to its last. -> its file or None"""
    os.makedirs(conf['night'], exist_ok=True)
    fh = open(_lock_path(conf), 'a+', encoding='utf-8')
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except BlockingIOError:
        fh.close()
        return None


def _ran(store, job_key, n, started, code, said, state):
    for attempt in range(6):
        try:
            return store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code, said, state)
        except sqlite3.OperationalError as busy:
            if 'locked' not in str(busy) or attempt == 5:
                raise
            time.sleep(0.5 * (attempt + 1))


def _close(store, job_key, n, why):
    said = {'summary': f'FAILED · {why} · {HAND}RUN AGENT here', 'ok': False, 'lines': [], 'why': why, 'step': 'RUN AGENT here', 'next': None}
    try:
        _ran(store, job_key, n, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps(said), 'FAILED')
    except Exception:   # noqa: BLE001
        pass


def hand_on(store, chain, key):
    """THE NEXT STEP'S RUN, TAKEN NOW as the Run button takes it. -> ((module, shell, run), '') or (None, why)"""
    nxt = next(((m, sh) for m, sh in (chain or ()) if getattr(m, 'KEY', '') == key), None)
    if nxt is None:
        return None, f'it is not in the chain this run was handed ({key})'
    module, sh = nxt
    if not sh.get('on', True):
        return None, 'it is switched off'
    try:
        job = next((x['job'] for x in store.board() if x['id'] == sh['id']), None) or {}
        ok, text = store.run(sh['id'])
    except Exception as fault:   # noqa: BLE001
        return None, f'its RUN was not taken ({_line(fault)})'
    if not ok:
        return None, f'its RUN was refused ({text})'
    m = re.search(r'RUN (\d+)', str(text))
    return (module, sh, int(m.group(1)) if m else int(job.get('data_job_run') or 0) + 1), ''


def once(store, job_key, n, agent, chain, conf, runner, locked):
    """ONE STEP, ITS RUN WRITTEN (DONE exit 0, FAILED exit 1 with his one step); green, the next step's RUN taken first. -> (said, next or None)"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not locked and SCHEDULE.get('schedule_type') == 'daily':   # THE NIGHT'S OWN START WHILE A NIGHT RUNS (one started by hand before its hour): that night is the night, green, nothing run twice
        got = _ok(['the night is running already (started by hand before its hour): this start is not needed'], None)
    elif not locked:
        got = _no([], 'another NIGHT step is running', f'lsof {_lock_path(conf)} names the run that holds the lock: let it end, then RUN AGENT')
    else:
        busy = _busy(conf)
        if busy:
            got = _no([], *busy)
        else:
            try:
                with Beat(store, job_key):
                    got = step(store, conf, runner)
            except subprocess.TimeoutExpired as fault:
                got = _no([], f'it ran past its {conf["seconds"]} s and was stopped ({_line(fault)})', f'RUN AGENT here ({TOOK})')
            except Exception as fault:   # A CRASH IS RED, NAMED WHERE IT HAPPENED
                got = _crashed(fault)
    if not got['ok'] and got.get('heal'):
        with Beat(store, job_key):   # THE HEAL WORKS FOR MINUTES (DAY builds the fix with Claude Code): its RUN beats on, never taken for a stuck one
            more, again = heal(store, agent, chain, conf, got)
        got = {**got, 'lines': got['lines'] + more}
        if again:
            got = {**got, 'ok': True, 'why': '', 'step': '', 'next': again, 'lines': got['lines'] + [f"healed red: {got['why']}"]}
    nxt = None
    if got['ok'] and got.get('next'):
        nxt, why = hand_on(store, chain, got['next'])
        if nxt is None:
            name = next((getattr(m, 'NAME', '') for m, _sh in (chain or ()) if getattr(m, 'KEY', '') == got['next']), '') or got['next']
            if why == 'it is switched off':
                got = {**got, 'next': None, 'lines': got['lines'] + [f'the night ends here: {name} is switched off']}
            else:
                got = {**got, 'ok': False, 'why': f'the night stopped before {name}: {why}', 'step': f'RUN AGENT on {name}: it takes its own RUN', 'next': None}
    said = _ended(got)
    try:
        _ran(store, job_key, n, started, 0 if got['ok'] else 1, json.dumps(said), 'DONE' if got['ok'] else 'FAILED')
    except Exception as fault:   # noqa: BLE001
        if nxt:
            _close(store, nxt[1]['job_key'], nxt[2], f'the night stopped: {NAME} could not write its run ({_line(fault)})')
        return said, None
    return said, nxt


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None, conf=None, runner=subprocess.run):
    """ONE RUN OF THE NIGHT FROM THIS STEP: the night's lock taken, this step, then every next one in a loop, each its own run written"""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conf = {**CONF, **(conf or {})}
        lock = _night_lock(conf)
    except Exception as fault:   # noqa: BLE001
        said = _ended(_crashed(fault))
        _ran(store, job_key, n, started, 1, json.dumps(said), 'FAILED')
        return said
    try:
        said, nxt = once(store, job_key, n, agent, chain, conf, runner, lock is not None)
        while nxt:
            module, sh, m = nxt
            try:
                _s, nxt = module.once(store, sh['job_key'], m, agent, chain, {**module.CONF, **{k: v for k, v in conf.items() if k != 'seconds'}}, runner, True)
            except Exception as fault:   # noqa: BLE001
                _close(store, sh['job_key'], m, f'it broke before its run was written ({_line(fault)})')
                nxt = None
    finally:
        if lock is not None:
            lock.close()
    return said


# ---- its block
def _runs(store, job_key):
    return sorted(store.runs(job_key, 200), key=lambda r: r['started_at'], reverse=True)


def _said_of(r):
    try:
        return json.loads(r.get('said') or '{}')
    except (TypeError, ValueError):
        return {}


def latest(store, job_key):
    runs = _runs(store, job_key)
    return _said_of(runs[0]) if runs else None


def _local(stamp):
    try:
        return datetime.datetime.fromisoformat(str(stamp).replace(' ', 'T')).replace(tzinfo=zoneinfo.ZoneInfo('America/New_York'))
    except (TypeError, ValueError):
        return None


def red_now(store, job_key):
    runs = _runs(store, job_key)
    if not runs or runs[0].get('exit') == 0:
        return None
    first = runs[0]
    for r in runs:
        if r.get('exit') == 0:
            break
        first = r
    s = _said_of(runs[0])
    return {'why': str(s.get('why') or 'its run ended red'), 'step': str(s.get('step') or 'RUN AGENT here'), 'since': _local(first.get('started_at'))}


def warning(store, job_key):
    red = red_now(store, job_key)
    if red is None:
        return []
    at = red['since']
    row = {'key': 'red', 'cells': [{'text': f"Red since {at:%H:%M}", 'since': at.isoformat(timespec='seconds')} if at else 'Red since: not on file',
                                   f"Came in {at:%Y-%m-%d %H:%M}" if at else 'Came in: not on file', f"Warning · {red['why']}"], 'copy': f"{HAND}{red['step']}"}
    return [{'kind': 'table', 'title': 'Warning', 'columns': ['Red since', 'Came in', 'Warning'], 'rows': [row], 'empty': ''}]


def content(store, job_key, block=None):
    """ITS BLOCK: the warning row while its newest run is red, then what its newest run did, line by line"""
    last = latest(store, job_key) or {}
    rows = [{'key': str(i), 'cells': [str(l)]} for i, l in enumerate(last.get('lines') or [])]
    return warning(store, job_key) + [{'kind': 'table', 'title': 'MACOS · TAKE IN', 'under': WHAT, 'columns': ['Its last run'], 'rows': rows,
                                       'empty': 'Not run yet.'}] + more_content(store, job_key)


def until_next(now=None, schedule=None):
    schedule = schedule or SCHEDULE
    if schedule.get('schedule_type') != 'daily':
        return 365 * 86400   # ON RUN AGENT ONLY: never due by itself
    zone = zoneinfo.ZoneInfo(schedule['timezone'])
    now = now or datetime.datetime.now(zone)
    h, m = (int(x) for x in schedule['time'].split(':'))
    nxt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if nxt <= now:
        nxt += datetime.timedelta(days=1)
    return max(1, int((nxt - now).total_seconds()))


def clock(schedule=None):
    schedule = schedule or SCHEDULE
    if schedule.get('schedule_type') != 'daily':
        return {'zone': schedule['location'], 'at': '', 'said': 'AFTER THE STEP BEFORE IT', 'when': 'AFTER THE STEP BEFORE IT', 'repeat': 'CHAIN', 'hour_deg': 0, 'minute_deg': 0}
    h, m = (int(x) for x in schedule['time'].split(':'))
    when = datetime.time(h, m).strftime('%I:%M %p').lstrip('0')
    return {'zone': schedule['location'], 'at': schedule['time'], 'said': f'{when} · DAILY', 'when': when, 'repeat': 'DAILY', 'hour_deg': (h % 12) * 30 + m * 0.5, 'minute_deg': m * 6}


# ---- ITS OWN STEP

def written_tonight(conf, hours=12):
    """the native write passed in the last hours, on the commit the workspace holds now -> its record or None"""
    try:
        with open(os.path.join(conf['reruns'], 'native_generate@localhost_pf.json'), encoding='utf-8') as fh:
            r = json.load(fh)
    except (OSError, ValueError):
        return None
    at = datetime.datetime.fromisoformat(str(r.get('finished') or '1970-01-01T00:00:00+00:00'))
    return r if r.get('ok') and datetime.datetime.now(datetime.timezone.utc) - at < datetime.timedelta(hours=hours) else None


def step(store, conf, runner):
    """MACOS · TAKE IN: the Mac app written from tonight's web code (native_generate, the night chain's own write; it commits the
    written apps to the workspace). The Mac take in reuses the iPhone take in's write when it passed in the last 12 hours."""
    had = written_tonight(conf) if True else None
    if had:
        return _ok([f"macos · take in · written tonight already ({str(had.get('finished'))[:16]}, {str(had.get('commit') or '')[:12]}): the same write serves both apps"])
    code, results, last = tower(conf, runner, 'native_generate')
    lines = [f'macos · take in · {l}' for l in said_steps(results)]
    if code != 0:
        why, again = tower_red(code, results, last, ('native_generate',), again_line(conf, 'native_generate'))
        return red_heals(_no(lines, why, again))
    return _ok(lines)


def more_content(store, job_key):
    return []



# ---- THE NIGHT CHAIN'S OWN STEP RUNNER, IN THIS FILE (the owner 2026-10-27: "agent folder NONE shared"): the tower runs this file as a
# process of its own, from LARRY LLM's app/ with that app/ on PYTHONPATH: python <this file> step [--rnd] [--clean] <step> ...
# Each step runs exactly as the night chain runs it (core_engine.auto), its result written beside the night's (<reports>/reruns/<step>@<target>.json).
def _t_one(auto, native, native_test, tower, step, t, commit, attempt, planned, clean):
    results, began = [], datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    if step == 'native_generate':
        events = auto._native(step, results, native.generate(tower.source(t)))
    elif step in ('native_iphone', 'native_macos'):   # THE NIGHT BUILDS CLEAN (the owner 2026-10-23 22:40): no kept fix folder
        target = step[len('native_'):]
        keep = {} if clean or not hasattr(native, 'fix_keep') else {'keep': native.fix_keep(target, os.path.join(HOME, 'spine_worktrees', 'hotfix'))}
        events = auto._native(step, results, native.build(target, commit, '', tower.source(t), **keep))
    elif step in ('native_test_iphone', 'native_test_macos'):
        events = auto._native(step, results, native_test.test(step[len('native_test_'):], tower.source(t)))
    else:
        events = auto._steps(t, (step,), results, commit=commit, member='night')
    for e in events:
        print(json.dumps(e, default=str), flush=True)
    got = results[-1] if results else {'step': step, 'target': t['name'], 'ok': False, 'why': 'the step wrote no result'}
    ran_on = (tower.resolve(t, 'HEAD') if step == 'native_generate' else (native.kept(step.rsplit('_', 1)[1]) or {}).get('commit', '') if step.startswith('native_') else commit)
    record = {**got, 'step': step, 'target': str(got.get('target') or t['name']), 'commit': ran_on, 'published': tower._current(t) or '',
              'attempt': attempt, 'planned': list(planned), 'started': began, 'finished': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'by': 'night'}
    folder = os.path.join(auto.reports_dir(), 'reruns')
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{step}@{record['target']}.json")
    with open(path + '.tmp', 'w', encoding='utf-8') as fh:
        json.dump(record, fh, indent=1, default=str)
    os.replace(path + '.tmp', path)
    print(json.dumps({'written': path, 'ok': record.get('ok')}), flush=True)
    return record


def _t_main(argv):
    """-> 0 every step passed; 1 a step red (it stops there, as the chain stops); 2 refused; 3 busy"""
    from core_engine import auto, native, native_test, tower   # LARRY LLM's own, from its app/ (never imported by the page)
    rnd, clean = '--rnd' in argv, '--clean' in argv
    names = [a for a in argv if a not in ('--rnd', '--clean')]
    allowed = auto.PUBLISH if rnd else ('native_generate', 'native_iphone', 'native_test_iphone', 'native_macos', 'native_test_macos') + auto.PUBLISH
    if not names or any(n not in allowed for n in names):
        print(json.dumps({'refused': f"not a step: {', '.join(n for n in names if n not in allowed) or 'none named'}"}), flush=True)
        return 2
    try:
        with auto.Lock():
            here = tower.target(auto.AUTO['local'])
            if rnd:
                way = auto.lane('current')
                if way['frozen']:
                    raise ValueError(f"{way['name']} is frozen: its rnd side takes no build")
                t, commit = tower.target(way['rnd']), tower._current(here) or ''
            else:
                t, commit = here, tower.resolve(here, 'HEAD')   # THE NIGHT'S COMMIT IS MAIN'S HEAD for every step, as the night chain takes it (auto.local), never what this laptop ran before
            attempt = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
            for n in names:
                if not _t_one(auto, native, native_test, tower, n, t, commit, attempt, names, clean).get('ok'):
                    return 1
    except auto.Busy as e:
        print(json.dumps({'busy': str(e)}), flush=True)
        return 3
    except ValueError as e:
        print(json.dumps({'refused': str(e)}), flush=True)
        return 2
    return 0


if __name__ == '__main__':
    import sys
    if sys.argv[1:2] == ['step']:
        sys.exit(_t_main(sys.argv[2:]))
    sys.exit(2)

