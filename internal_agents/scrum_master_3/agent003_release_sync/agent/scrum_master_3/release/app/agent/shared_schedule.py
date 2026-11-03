"""THE SCHEDULE (moved out of shared_where and row 003, 2026-10-21): his clock, the day's step records, and THE DAILY
SCHEDULE (its jobs, its tick, its lane and its cool down). The clock: CONF (settings 'scrum'), ZONE, _now, cycle,
began, due, _in, _clock, _when, said, none, sprint, NO_RUNNER. The step records (files beside the jobs' logs, never
rows): record, records, days, copies, keep, _keep, put_aside, _step, records_home. The daily schedule: DAILY (settings 'daily'), HOLDER, jobs, when, ready, run, tick,
cool, overdue, take_back, sweep, keep_whole_smoke, whole_smoke, log_file, _job, _lane, _holder, home, place.

    python -m agent.shared_schedule tick | list    (settings launch.tick)
"""
import datetime
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import types
import zoneinfo

from agent import shared_where as where
from agent import shared_store as store
from agent import shared_words as words
from agent import shared_native as native   # the night's build as its own files say it (running: its lock file)


# ---------------------------------------------------------------- the clock, a row's word, settings['scrum']

CONF = where.SETTINGS['scrum']   # his own clock's settings: zone, reset, release, version, sprint_days, smoke_rows


ZONE = zoneinfo.ZoneInfo(CONF['zone'])

NO_RUNNER = 'no runner yet'

def _now(now=None):
    return (now or datetime.datetime.now(datetime.timezone.utc)).astimezone(ZONE)

def _reset():
    hour, minute = (int(x) for x in CONF['reset'].split(':'))
    return datetime.timedelta(hours=hour, minutes=minute)

def cycle(now=None):
    """The day a moment belongs to: it starts at conf reset in conf zone and holds the night after it."""
    return (_now(now) - _reset()).date().isoformat()

def began(day):
    """The first moment of a day's cycle."""
    return datetime.datetime.combine(datetime.date.fromisoformat(day), datetime.time(), ZONE) + _reset()

def due(day, at, now=None):
    """A row is looked at from its hour on (an hour before the reset's is the night's: the day after)."""
    hour, minute = (int(x) for x in at.split(':'))
    after = datetime.timedelta(hours=hour, minutes=minute) - _reset()
    return _now(now) >= began(day) + (after if after >= datetime.timedelta(0) else after + datetime.timedelta(days=1))

def _in(day, moment):
    """A runner's own moment (ISO, any zone) lies in this day's cycle."""
    try:
        m = datetime.datetime.fromisoformat(moment)
    except (TypeError, ValueError):
        return False
    m = m if m.tzinfo else m.replace(tzinfo=datetime.timezone.utc)
    return began(day) <= m < began(day) + datetime.timedelta(days=1)

def _clock(moment):
    try:
        m = datetime.datetime.fromisoformat(moment)
    except (TypeError, ValueError):
        return ''
    return (m if m.tzinfo else m.replace(tzinfo=datetime.timezone.utc)).astimezone(ZONE).strftime('%H:%M')

def said(ok, text, start='', end='', held=False):
    """A check's word. ok: True (as it should be), False (an issue), None (nothing to judge yet: the step has not run
    today, or has no runner). start, end: the step's own moments, when its runner left them. held: THE OWNER HOLDS IT
    (2026-10-12: "never a fake green: a red that is truly his act stays, said as that"): not run or not done on his own
    ruling (no pin before the data fields are right; a switch he set off; no sender he named). Never red, never green,
    no ticket; said as his ruling."""
    return {'ok': None if held else ok, 'said': text, 'start': start, 'end': end, 'held': bool(held)}

def sprint(now=None):
    """THE 90 DAY COUNT ("that is the key to the entire flow and goal"): counted back from the release day."""
    left = (datetime.date.fromisoformat(CONF['release']) - _now(now).date()).days
    return {'release': CONF['release'], 'version': CONF['version'], 'left': left, 'of': int(CONF['sprint_days']), 'day': int(CONF['sprint_days']) - left}

def none(why=NO_RUNNER):
    return lambda day: said(None, why)

def _when(moment):
    """A moment as the page says a past one: its date and clock, in his zone."""
    try:
        m = datetime.datetime.fromisoformat(moment)
    except (TypeError, ValueError):
        return ''
    return (m if m.tzinfo else m.replace(tzinfo=datetime.timezone.utc)).astimezone(ZONE).strftime('%b %d %H:%M')


# ---------------------------------------------------------------- the daily schedule's records: files of its own (CONTRACT.md 4, 5)
# A job's record of a day is the clock's own state (when it began, when it ended, its exit, its log), never a row of
# his database: a file beside the job's log, <logs>/daily/<day>/<STEP>.json (written whole, then one rename), and a
# record put aside is <STEP>.json.<HHMMSS>.<copy> beside it. A folder given is a check's own: its records under it.

def _st(folder=None):
    """HIS DATABASE DOOR (agent/shared_store.py): the office's own instance, or a check's scratch one (folder)."""
    from . import shared_store as store
    return store.Store(folder) if folder else store.Store()

def _step(name):
    """A job's step name as its record is named (the old file name: spaces to _, no ')."""
    return name.replace(' ', '_').replace("'", '')

def records_home(folder=None):
    """Where the job records are: <folder>/daily (a check's), else daily/ under his logs folder, outside sanity."""
    return os.path.join(os.path.abspath(os.path.expanduser(folder)), 'daily') if folder else os.path.join(store.LOGS, 'daily')

def _record_file(day, name, folder=None, copy='', at=''):
    base = os.path.join(records_home(folder), day, _step(name) + '.json')
    return f'{base}.{at}.{copy}' if copy else base

def _read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            got = json.load(fh)
    except (OSError, ValueError):
        return {}
    return got if isinstance(got, dict) else {}

def _write(path, rec):
    """a record written whole by the door (store.write_whole: beside it, then one rename), never through a link"""
    store.write_whole(path, rec)

def record(day, name, folder=None):
    """A job's own record of a day ({} when it has not begun): {name, started, ended, exit, log}."""
    return _read(_record_file(day, name, folder))

def days(folder=None):
    """The days that hold a job record, newest first."""
    try:
        found = os.listdir(records_home(folder))
    except OSError:
        return []
    return sorted((d for d in found if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d) and os.path.isdir(os.path.join(records_home(folder), d))), reverse=True)

def records(day, folder=None):
    """Every job's record of a day (not the ones put aside). -> {step: record}"""
    root = os.path.join(records_home(folder), day)
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return {}
    return {n[:-5]: r for n in names if n.endswith('.json') for r in [_read(os.path.join(root, n))] if r}

def copies(day, name, folder=None):
    """A job's records put aside on a day. -> [(copy, HHMMSS, record)], oldest first"""
    root, head = os.path.join(records_home(folder), day), _step(name) + '.json.'
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    out = []
    for n in names:
        m = re.fullmatch(re.escape(head) + r'(\d{6})\.(failed|before)', n)
        if m:
            out.append((m.group(2), m.group(1), _read(os.path.join(root, n))))
    return out

def _keep(day, name, rec, folder=None):
    """The job's record of the day, written whole (what is gone cut from it first)."""
    _write(_record_file(day, name, folder), words.clean(rec))

def keep(day, name, rec, folder=None):
    """A job's record of a day written whole (for another file, or a check planting one)."""
    _keep(day, name, rec, folder)

def put_aside(day, name, copy='failed', folder=None, at=None):
    """A JOB'S RECORD OF TODAY PUT ASIDE (the old <STEP>.json.<HHMMSS>.failed / .before-<HHMMSS>): kept as copy 'failed'
    or 'before' at HHMMSS, and today's own record gone, so its clock starts it again. -> False when there was none."""
    rec = record(day, name, folder)
    if not rec:
        return False
    _write(_record_file(day, name, folder, copy, at or datetime.datetime.now().strftime('%H%M%S')), rec)
    os.remove(_record_file(day, name, folder))
    return True


def place(path, sanity=None):
    """a settings path that may name a locked piece by its old place (~/smoke, ~/judge): resolved to where the piece is"""
    path = os.path.expanduser(str(path))
    base = os.path.basename(path.rstrip(os.sep))
    return os.path.join(os.path.expanduser(sanity or where.path('sanity')), base) if base in ('judge', 'smoke') else path


# ---------------------------------------------------------------- THE DAILY SCHEDULE (from row 003)

DAILY = where.SETTINGS['daily']   # THE DAILY SCHEDULE's own settings: jobs, lane, cool_down, build_grace
HOLDER = 'the-nightly-build'
NEVER = ('judge.py', 'core_engine.auto', 'core_engine.hotfix')   # never a line of the list: the Judge, LARRY LLM's publish chain, the door onto live (LARRY LLM's real module names, as a command would name them)


def home(folder=None):
    """The schedule's own logs folder (daily.log, each job's lines): outside sanity, through the door's log_path."""
    return folder or os.path.dirname(_st().log_path('daily', 'daily.log'))


def jobs():
    found = DAILY['jobs']
    for j in found:
        if any(word in ' '.join(j['command']) for word in NEVER):
            raise ValueError(f"{j['name']}: the daily schedule never starts the Judge or a publish")
    return found


LANE_ALONE = re.compile(r'judge|quiet|baseline|launch (times|measure)', re.I)


def _lane_dir(base=None):
    """THE LANE'S FOLDER (the heavy slot's: .slot1, .window, HEAVY_SLOT.md), the folder settings.json's daily.lane names."""
    return base or os.path.dirname(os.path.expanduser(DAILY['lane']))


def _held(n, base=None):
    try:
        with open(os.path.join(_lane_dir(base), f'.slot{n}', 'holder'), encoding='utf-8') as fh:
            return fh.read().strip()
    except OSError:
        return ''


def _lane(verb, who, what, base=None, now=None):
    """LANE 1 TAKEN OR FREED BY HIMSELF, with take_slot.sh's own protocol (the owner 2026-10-21: he never runs it):
    take = the 10-minute .window after the last lane-1 job is closed, lane 2 empty for a job that runs alone, then
    mkdir .slot1 (atomic: two can never both hold it), its holder file and a START line in HEAVY_SLOT.md; free = only
    his own hold, the folder removed, .window stamped and an END line. -> (done, what was said)"""
    base = _lane_dir(base)
    stamp = (now or datetime.datetime.now()).strftime('%I:%M %p')
    slot, log = os.path.join(base, '.slot1'), os.path.join(base, 'HEAVY_SLOT.md')
    if verb == 'take':
        try:
            with open(os.path.join(base, '.window'), encoding='utf-8') as fh:
                opened = int(fh.read().strip())
        except (OSError, ValueError):
            opened = 0
        left = 600 - (int((now or datetime.datetime.now()).timestamp()) - opened)
        if left > 0:
            return False, f'WAIT: the 10-minute test window after the last lane-1 job is open; try again after {left} s'
        if LANE_ALONE.search(what) and _held(2, base):
            return False, f'REFUSED: lane 2 must be empty first: {_held(2, base)}'
        try:
            os.mkdir(slot)
        except FileExistsError:
            return False, f'HELD: lane 1: {_held(1, base)}'
        with open(os.path.join(slot, 'holder'), 'w', encoding='utf-8') as fh:
            fh.write(f'{who} {stamp} {what}\n')
        with open(log, 'a', encoding='utf-8') as fh:
            fh.write(f'START {who} {stamp} {what}\n')
        return True, 'lane 1 is yours'
    if verb == 'free':
        held = _held(1, base)
        if not held and not os.path.isdir(slot):
            return True, 'lane 1 was not held'
        if not held.startswith(who + ' '):
            return False, f'REFUSED: lane 1 is held by: {held}'
        shutil.rmtree(slot, ignore_errors=True)
        with open(os.path.join(base, '.window'), 'w', encoding='utf-8') as fh:
            fh.write(f'{int((now or datetime.datetime.now()).timestamp())}\n')
        with open(log, 'a', encoding='utf-8') as fh:
            fh.write(f'END {who} {stamp} {what}\n')
        return True, 'lane 1 released'
    raise ValueError(f'the lane knows take and free, not {verb}')


def _holder(base=None):
    """Who holds lane 1 ('' when free), read from its holder file."""
    return _held(1, base)


ABOUT = re.compile(r'about (\d+) min')
AT_MOST = re.compile(r'(\d+) min at most')
DAILY_HOLD = re.compile(r'daily \d{1,2}:\d{2} [AP]M (.+?) \(the daily schedule')   # the tick's own hold: "daily 12:29 PM SMOKE TEST (the daily schedule, about 240 min at most)"


def _alive(job):
    """IS THE JOB'S OWN PROGRAM RUNNING ON THIS LAPTOP (read only: ps, nothing stopped): a process whose arguments end
    with the job's command after its interpreter (SMOKE TEST: `smoke.py` alone; `smoke.py <row>` is a row run, not
    the job). -> True / False"""
    cmd = [os.path.basename(os.path.expanduser(x)) for x in job.get('command') or []]
    want = cmd[1:] if cmd and re.match(r'python', cmd[0], re.I) else cmd
    if not want:
        return False
    try:
        out = subprocess.run(['ps', '-axww', '-o', 'command='], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return True   # ps does not answer: never take a lane back on a guess
    for line in out.splitlines():
        got = [os.path.basename(x) for x in line.split()]
        if len(got) >= len(want) and got[-len(want):] == want:
            return True
    return False


def _job_running(line, taken, now, alive=_alive, folder=None):
    """A DAILY HOLD'S JOB IS RUNNING when its own record of the day (the day it was taken, or now's) has begun and not
    ended AND its program is alive (alive(job)). A job no list names, or one with no running record, is not running.
    -> True / False"""
    m = DAILY_HOLD.match(line)
    job = next((j for j in DAILY['jobs'] if m and j['name'] == m.group(1)), None)
    if job is None:
        return False
    days = {cycle(datetime.datetime.fromtimestamp(t, datetime.timezone.utc)) for t in (taken, now)}
    running = any((lambda r: bool(r.get('started')) and not r.get('ended'))(record(d, job['name'], folder)) for d in days)
    return running and bool(alive(job))


def overdue(slot=None, now=None, most=240, building=None, alive=_alive, folder=None):
    """HE WAITS FOR NO PERSON OR AGENT (the owner 2026-10-13, his role: "He waits for no person. One check at a time"):
    a hold of the lane is given up when it is held past one and a half times its own word ("about N min", else "N min
    at most"; none said: most minutes), counted from when it was taken (its holder file). THE TICK'S OWN DAILY HOLD
    (the owner 2026-10-21, POINT 12: "daily 12:29 PM SMOKE TEST" held 8 h after the switch with no smoke running) is
    given up the same way, but only when its job is not running (_job_running: no running record, or no live program).
    THE NIGHTLY BUILD'S hold (HOLDER) only when the build is not running (native.running(), or building) and its cool
    down is over (past build_grace). -> the holder's line when overdue, else ''."""
    slot = slot or os.path.join(os.path.dirname(os.path.expanduser(DAILY['lane'])), '.slot1')
    try:
        with open(os.path.join(slot, 'holder'), encoding='utf-8') as fh:
            line = fh.read().strip()
        taken = os.path.getmtime(os.path.join(slot, 'holder'))
    except OSError:
        return ''
    now = now if now is not None else datetime.datetime.now().timestamp()
    if line.startswith(HOLDER):
        moment = datetime.datetime.fromtimestamp(now, datetime.timezone.utc)
        running = bool(native.running() if building is None else building)
        return '' if running or cool(moment, False) else line   # running, or still before its build_grace: its own
    said = ABOUT.search(line) or AT_MOST.search(line)
    limit = (int(said.group(1)) if said else most) * 1.5 * 60
    if now - taken <= limit:
        return ''
    if line.startswith('daily ') and _job_running(line, taken, now, alive, folder):
        return ''   # his own job, still at work: never given up
    return line


def take_back(line, slot=None, log=None, why='held past its own time'):
    """The overdue hold given up, in the lane's own log (one END line), so whoever held it reads why."""
    base = os.path.dirname(os.path.expanduser(DAILY['lane']))
    slot, log = slot or os.path.join(base, '.slot1'), log or os.path.join(base, 'HEAVY_SLOT.md')
    who = line.split(' ', 1)[0]
    shutil.rmtree(slot, ignore_errors=True)
    with open(log, 'a', encoding='utf-8') as fh:
        fh.write(words.cut(f"END {who} {datetime.datetime.now().strftime('%I:%M %p')} taken back by the Scrum Master: {why} ({line[len(who):].strip()[:120]})\n"))


def sweep(stale=overdue, back=take_back):
    """THE TICK'S OWN HOLDS TAKEN BACK (POINT 12): a daily hold past its limit whose job is not running, or the nightly
    build's hold once that build is over, is given up at the start of every tick, with its one END line (take_back).
    Anyone else's hold is still taken back only when a heavy job needs the lane (tick). -> what was said, or ''"""
    late = stale()
    if not late or not (late.startswith('daily ') or late.startswith(HOLDER)):
        return ''
    why = ('the nightly build is over and not running' if late.startswith(HOLDER)
           else 'held past its own time and its job is not running')
    back(late, why=why)
    return f'the lane was taken back ({why}): {late[:120]}'


NIGHT_STAMP = re.compile(r'(\d{8}T\d{6})_local')   # the tower's own run folder: <UTC stamp>_local (20261021T050001_local)


def night_report(day, top=None):
    """THE NIGHT'S REPORT WRITTEN (N2, the owner's order 2026-10-22: "the request workers pause at 00:30 and resume
    after the report"): the result.json of a nightly run (member 'nightly', not dry) of the local chain whose folder
    is stamped at or after this day's cool down, before its cycle ends. -> its path, or '' while the night has written none."""
    top = top or os.path.dirname(os.path.dirname(os.path.expanduser(where.REPORTS['nightly_result'])))   # ~/spine_scratch/tower_auto
    hour, minute = (int(x) for x in DAILY['cool_down'].split(':'))
    after = datetime.timedelta(hours=hour, minutes=minute) - _reset()
    start = began(day) + (after if after >= datetime.timedelta(0) else after + datetime.timedelta(days=1))
    try:
        names = sorted(os.listdir(top), reverse=True)
    except OSError:
        return ''
    for name in names:
        m = NIGHT_STAMP.fullmatch(name)
        if not m:
            continue
        stamp = datetime.datetime.strptime(m.group(1), '%Y%m%dT%H%M%S').replace(tzinfo=datetime.timezone.utc)
        if stamp >= began(day) + datetime.timedelta(days=1):   # a later day's night: not this one's
            continue
        if stamp < start:
            break
        path = os.path.join(top, name, 'result.json')
        got = _read(path) if os.path.isfile(path) else None
        if got and got.get('member', 'nightly') == 'nightly' and not got.get('dry'):
            return path
    return ''


def cool(now=None, building=None, report=None, quiet=None):
    """THE COOL DOWN is on: from its hour (00:30) until the night's report is written (night_report) and no chain of
    the tower runs (N2; never past the day's reset: a new day's cycle starts its own count). report: a stand-in for
    night_report (a check's).
    A NIGHT THAT IS OVER HOLDS NOTHING (the owner 2026-10-23: "NOTHING WAITS FOR A LATER PROCESS TO CLEAR"): past its
    build_grace (the build starts before it), with no chain of the tower running and the tower's lock untouched for
    QUIET, a night that wrote no report is over (it ended red, or never began): the cool down ends then, never kept to
    the day's reset. quiet: a stand-in for that look (a check's)."""
    now = _now(now)
    day = cycle(now)
    if not due(day, DAILY['cool_down'], now):
        return False
    if native.running() if building is None else building:
        return True
    if night_report(day) if report is None else report:
        return False
    return not (_night_over(day, now) if quiet is None else quiet)


QUIET = datetime.timedelta(minutes=10)   # the tower's lock untouched this long past build_grace, no chain running: the night is over


def _night_over(day, now):
    """past build_grace and the tower's lock (its file) untouched for QUIET: no build runs and none is coming tonight"""
    if not due(day, DAILY.get('build_grace') or '01:10', now):
        return False
    try:
        touched = datetime.datetime.fromtimestamp(os.path.getmtime(where.report('nightly_lock')), datetime.timezone.utc)
    except OSError:
        touched = None   # no lock file: no chain has run
    return touched is None or now - touched >= QUIET


def _started(cmd, timeout, **more):
    """A job as a group of its own, stopped WHOLE when its minutes run out (2026-10-12: the smoke test was stopped at its
    limit; a plain stop ends the first program alone and leaves what it started)."""
    with subprocess.Popen(cmd, start_new_session=True, **more) as child:
        try:
            return types.SimpleNamespace(returncode=child.wait(timeout=timeout))
        except subprocess.TimeoutExpired:
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(child.pid, sig)
                    child.wait(timeout=20)
                    break
                except (ProcessLookupError, PermissionError):
                    break
                except subprocess.TimeoutExpired:
                    continue
            raise


def run(job, day, folder=None, runner=_started, now=None):
    """One job, start to end, its lines in its own log AS THEY COME; its record is written when it begins and when it ends."""
    log = _st(folder).log_path('daily', day, _step(job['name']) + '.log')   # its lines are a log, outside sanity; its record a file beside it
    rec = {'name': job['name'], 'started': _now(now).astimezone(datetime.timezone.utc).isoformat(), 'ended': '', 'exit': None, 'log': log}
    _keep(day, job['name'], rec, folder)
    try:
        if os.path.islink(log) or os.path.islink(os.path.dirname(log)):
            raise OSError(f'a link stands where its lines are written: {log}')
        with os.fdopen(os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600), 'w', encoding='utf-8') as fh:
            done = runner([os.path.expanduser(x) for x in job['command']], cwd=place(job.get('cwd') or where.WORKSPACE), stdout=fh, stderr=subprocess.STDOUT,
                          timeout=float(job.get('minutes', 60)) * 60, env={**os.environ, 'PATH': where.path('job_path') + ':' + os.environ.get('PATH', ''), 'PYTHONUNBUFFERED': '1'})
        rec['exit'] = done.returncode
    except subprocess.TimeoutExpired:
        rec['exit'] = 124   # it ran past its minutes and was stopped, with everything it started
    except OSError as e:
        rec['exit'] = 127
        rec['why'] = f'{type(e).__name__}: {e}'
    rec['ended'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    words.cut_file(log)   # the job's own lines, written as they came, with what is gone cut once it ended
    _keep(day, job['name'], rec, folder)
    if job['name'] == 'SMOKE TEST':
        keep_whole_smoke(folder=folder)   # a check's folder keeps its own copy, never the logs' one
    return rec


def keep_whole_smoke(source=None, folder=None):
    """THE DAY'S WHOLE SMOKE RUN IS KEPT HERE (2026-10-12: a run of one row alone, by a person or by the Developer's
    proof, writes the smoke test's own report over the day's whole one, and the work list then read one row): after the
    daily schedule's run, its report is kept when it holds every row (a file of his, smoke/whole.json under his logs). The work list reads this copy."""
    source = source or where.report('smoke')   # the smoke test, wherever the owner keeps it
    try:
        with open(source, encoding='utf-8') as fh:
            report = json.load(fh)
    except (OSError, ValueError):
        return False
    if len(report.get('rules') or []) < int(CONF['smoke_rows']):
        return False
    _write(_whole_file(folder), words.clean(report))   # his copy of the whole run, a file (CONTRACT.md 5: never a row)
    return True


def _whole_file(folder=None):
    return os.path.join(os.path.abspath(os.path.expanduser(folder)) if folder else store.LOGS, 'smoke', 'whole.json')


def whole_smoke(folder=None):
    """The day's whole smoke run as kept (smoke/whole.json under his logs folder), or None."""
    return _read(_whole_file(folder)) or None


def ready(day, job, now=None, folder=None):
    """IS IT ITS TURN (the owner 2026-10-13: "it should have a starting point and work like a chain"; "a human if they
    finish something early they do not sit in a chair for an hour and look out the window"): a job with an hour (at) is
    a starting point, its turn from that hour on; a job that comes after another (after) has its turn the moment that
    one ended today, however it ended (a red is reported, the day goes on). Begun today already: never again, except a
    job that comes back (again: minutes; the owner 2026-10-13, 12 RED and IDLE: "this should keep you busy"): once it
    has ended, it has its turn again that many minutes after it last began, all day; it says by itself when it has
    nothing to do."""
    rec = record(day, job['name'], folder)
    if rec and rec.get('by') == 'change' and job.get('at') and not job.get('again'):   # A RUN ON CHANGE NEVER TAKES THE HOUR'S TURN (rows9_28, 2026-10-23: the take in runs the moment its inputs change; the 00:10 run still runs)
        try:
            ran = datetime.datetime.fromisoformat(rec['started'])
        except (KeyError, TypeError, ValueError):
            ran = None
        if ran is not None and not due(day, job['at'], ran):   # it began before the hour: the hour's turn is still open
            return bool(rec.get('ended')) and due(day, job['at'], now)
    if rec:
        if not (job.get('again') and rec.get('ended')):
            return False
        try:
            began = datetime.datetime.fromisoformat(rec['started'])
        except (KeyError, ValueError):
            return False
        return (_now(now) - began).total_seconds() >= int(job['again']) * 60
    if job.get('after'):
        before = record(day, job['after'], folder)
        return bool(before.get('ended'))
    return due(day, job['at'], now)


def tick(now=None, folder=None, runner=_started, lane=_lane, holder=_holder, building=None, stale=overdue, back=None):
    """ONE TICK: its own stale holds taken back first (sweep: a daily hold past its limit whose job is not running, the
    nightly build's once over); then the cool down; else every job whose turn has come (ready), one at a time. A job
    that ends gives the next in its chain its turn AT ONCE, in this same tick: nobody waits for the next tick of the clock."""
    fixed, said = now, []
    back = back or take_back
    swept = sweep(stale, back)
    if swept:
        said.append(swept)
    if folder is None and runner is _started:   # THE TAKE IN ON CHANGE (rows9_28, 2026-10-23): looked at each tick, started as a process of its own, never waited for (a check's tick never starts it)
        try:
            from agent import agent028_nightly_take_in as takein_row
            started, line = takein_row.on_change(now=fixed)
            if started:
                said.append(f'TAKE IN ON CHANGE · {line}')
        except Exception as e:   # noqa: BLE001  (said, never a stop of the day's chain)
            said.append(f'the take in on change could not look: {type(e).__name__}: {e}'[:200])
    while True:
        now = _now(fixed)
        day = cycle(now)
        if cool(now, building):
            if holder() == '' and lane('take', HOLDER, 'the nightly build: the full build with the Judge, alone')[0]:
                said.append('the cool down: the lane is held for the nightly build')
            return said or ['the cool down: nothing starts']
        if holder().startswith(HOLDER):
            lane('free', HOLDER, 'the nightly build ended')
            said.append('the nightly build ended: the lane is free')
        started = False
        for job in jobs():
            if not ready(day, job, now, folder):
                continue
            if job.get('heavy'):
                got, why = lane('take', 'daily', f"{job['name']} (the daily schedule, about {job.get('minutes', 60)} min at most)")
                late = '' if got else stale()
                if late:   # held past its own time by a person or an agent that is gone: he takes the lane back and goes on
                    back(late)
                    said.append(f"the lane was taken back: {late[:120]}")
                    got, why = lane('take', 'daily', f"{job['name']} (the daily schedule, about {job.get('minutes', 60)} min at most)")
                if not got:
                    if f"{job['name']} waits: {why}" not in said:
                        said.append(f"{job['name']} waits: {why}")
                    continue
            try:
                rec = run(job, day, folder, runner, now)
            finally:
                if job.get('heavy'):
                    lane('free', 'daily', job['name'])
            said.append(f"{job['name']} · exit {rec['exit']}")
            started = True
        if not started:
            return said


def when(job):
    """A job's turn in words: its hour, or after the job before it."""
    return f"after {job['after']}" if job.get('after') else job['at']


def main(argv):
    if argv[:1] == ['tick']:
        for text in tick():
            print(f"{_now().strftime('%Y-%m-%d %H:%M')} · {text}", flush=True)
        return 0
    if argv[:1] == ['list']:
        day = cycle()
        for j in jobs():
            rec = record(day, j['name'])
            print(f"{when(j):22}  {j['name']:26} {'heavy' if j.get('heavy') else '     '}  {'exit ' + str(rec.get('exit')) if rec.get('ended') else 'running' if rec else 'not yet today'}")
        return 0
    if argv[:1] == ['run'] and argv[1:]:   # ONE JOB NOW, as the tick runs it (its log, its record), never waiting for its turn (the owner 2026-10-23: "DIRECT FIX AND CLEAR NOW")
        name = ' '.join(argv[1:])
        job = next((j for j in jobs() if j['name'] == name), None)
        if job is None:
            print(f'no job named {name!r}: python -m agent.shared_schedule list')
            return 2
        rec = run(job, cycle(), now=_now())
        print(f"{job['name']} · exit {rec['exit']} · {rec['log']}", flush=True)
        return 0 if rec['exit'] == 0 else 1
    print('usage: python -m agent.shared_schedule tick | list | run <job name>')
    return 2


def log_file(log):
    """A job's log as its record names it: a whole path, or 'logs/<parts>' under the logs folder outside sanity (store.LOGS)."""
    log = str(log or '')
    return os.path.join(store.LOGS, *log.split('/')[1:]) if log.startswith('logs/') else os.path.expanduser(log)


def _job(name, good=lambda rec: 'ended well', held=()):
    """A row whose step is a line of THE DAILY SCHEDULE: read from that job's own record of the day. held: the exits
    by which the job says the owner holds it (his design, not a fault): said as his, never red."""
    def check(day):
        rec = record(day, name)
        if not rec:
            return said(None, 'not yet today')
        if not rec.get('ended'):
            return said(None, 'running', rec['started'])
        why = '' if rec['exit'] == 0 else 'it ran past its minutes and was stopped' if rec['exit'] == 124 else f"it ended with exit {rec['exit']}"
        try:
            with open(log_file(rec['log']), encoding='utf-8', errors='replace') as fh:
                last = (fh.read().strip().splitlines() or [''])[-1][:160]
        except OSError:
            last = ''
        if rec['exit'] in held:
            return said(None, f'the owner holds it · {last}' if last else 'the owner holds it', rec['started'], rec['ended'], held=True)
        return said(rec['exit'] == 0, (good(rec) if rec['exit'] == 0 else why) + (f' · {last}' if last else ''), rec['started'], rec['ended'])
    return check


if __name__ == '__main__':
    words.guard()
    sys.exit(main(sys.argv[1:]))
