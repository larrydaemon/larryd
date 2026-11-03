"""AGENT 001 · THE MARK IV AGENT ITSELF (the owner 2026-10-27: "the scrum master 2 has 2 agents so far: scrum master 2, standup";
"make sure the scrum master itself has a key for agent, model, logs, jobs and registered and the shell is connected"; "keep in
mind this is the mark IV agent; all agents below it are not mark IV they are sub agents and lower rank"): the office's own agent,
in the AGENT slot of the root shape; its name, class, card, words and facts its own (app/schemas/agent.json); its card, its model,
its job and its logs LARRYD's records under SYSTEM (frame_replica), its shell connected to them by their keys. The file carries the
office's own name (replica/ the template; stamped as agent001_<office>.py); the sub agents follow it (agent002_...), each in its
own slot, found by listing the agent folder, never a kept list.
ITS RUN (at the page's start, daily 06:50 New York, or RUN AGENT; the slow part in its own thread, as a RUN is a request): THE
CHAIN'S SANITY, written into each agent's job in LARRYD (jobs species, group sanity; the owner 2026-10-27: "rule are rules in the db
not python code"; "needs a key and needs to be stored in the job"; 2026-10-26: "a new agent that manages all the rules and is in
the top ... every agent in the frame it will populate the rules"): for every agent of the office, itself and its sub agents, its
skills from the knowledge store's index (frame_skills) and its rule carried once from his record of the original row and judged against
its own program by the reader when the program changed (frame_rules), its lie detector said; then THE SUMMARY, the X board of the day (one line per group of the shape, its
rows that ran today and ended DONE, its reds), HEALTHY or CRITICAL. DONE, exit 0; a read that failed: FAILED, exit 1, the
first fault named (one step: run it again). Its logs are its runs, LARRYD's LOGS."""
import datetime
import json
import os
import re
import zoneinfo

from frame import frame_replica as frame
from frame import frame_rules as rules
from frame import frame_skills as skills
from frame import frame_xboard as xboard

KEY = 'mark_iv'
SLOT = 'AGENT'            # where it lives: the root shape's AGENT slot, the one shell above the groups
NAME = None               # its name the office's own (agent.json name): the card is the office's
BACKGROUND = True         # its run reads programs with the reader (minutes): QUEUED on the press, DONE when the thread ends
WHAT = 'Reads the rules and skills of every agent each morning and keeps the X board'   # what it does, its one line (the canvas)
ROW_FILE = 'agent001_top_summary.py'   # the original's program its skills index is filed under: the summary of the chain (row 001)
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'daily', 'time': '06:50', 'timezone': 'America/New_York'}   # once a day, before the standup's 07:00


def piece_of(last, chain):
    """THE FAILED PIECE ALONE (the owner 2026-10-24: "if any of the 3 fail its red", its step runs that piece alone): when the last run
    ended FAILED and its first fault is a skills or rules read of one agentNNN_*.py of the chain, the next RUN AGENT reads that program's
    skills or that program's rules first: one program's write and its blind review, each read at most 7 min
    (frame_skills/frame_rules SECONDS 420, settings reader minutes 7), the measured piece, written as its own LOGS record at once, so
    the light follows that one piece; the other changed programs are read after it as a record of their own (_run).
    -> (file, 'skills' or 'rules'), or None for a whole run"""
    failed = (last or {}).get('failed') or {}
    if not failed:
        return None
    file, fault = next(iter(failed.items()))
    if file not in {os.path.basename(m.__file__) for m, _ in chain}:
        return None
    return file, 'skills' if str(fault).startswith('skills ') else 'rules'


def sanity(store, agent, chain, settings=None, app=None, hire_with=None, force=False, piece=None):
    """THE CHAIN'S SANITY INTO EACH AGENT'S JOB: every agent of the office (itself first, then its sub agents; chain: (module, shell)
    pairs, each shell holding a job): its skills from the index, written where they changed; its rule carried from his record and judged against its program by the
    reader where the program changed (frame_rules.read_chain), its lie detector; one read at a time in this office. A piece (piece_of):
    that one program's skills or rules alone. -> what it did."""
    if piece:
        chain = [(m, sh) for m, sh in chain if os.path.basename(m.__file__) == piece[0]]
    fell, seen = {}, {}   # THE SKILLS READ'S OWN FAULTS: a read that did not answer, or a write that is not ten skills, or a review that does not mark all ten
    files = [os.path.basename(m.__file__) for m, _ in chain]
    hire = hire_with or frame.hire

    def watched(cmd, words, cwd, seconds, job_path=''):
        rc, said = hire(cmd, words, cwd, seconds, job_path)
        file = next((f for f in files if f'PROGRAM agent/{f}.' in str(words)), 'a program of the chain')
        step = 'review' if str(words).startswith('You are the REVIEWER') else 'write'   # the step its own words name (a held skill is reviewed before any write)
        seen[file] = True
        asked = re.search(r'(?:Write|Answer with) exactly (\d+) lines', str(words))   # THE LINES ASKED: one a real fix (frame_skills), up to the ten slots
        want = int(asked.group(1)) if asked else skills.TEN
        lines = skills.numbered_lines(said, want) if rc == 0 else {}
        if rc != 0:
            fell.setdefault(file, f'skills {step} of {file} ended {"out of time" if rc is None else f"exit {rc}"}: {skills.one_line(said)[:160]}')
        elif len(lines) != want:
            fell.setdefault(file, f'skills {step} of {file} answered {len(lines)} of {want} lines')
        elif step == 'review' and any(m[0].upper() not in ('GREEN', 'RED') for m in lines.values()):
            fell.setdefault(file, f'skills review of {file} did not mark all {want} GREEN or RED')
        return rc, said
    entries = 0
    if not piece or piece[1] == 'skills':
        entries = skills.read_chain(store, agent, chain, settings or frame.SETTINGS, app or frame.APP, watched, force)   # THE SKILLS OF THE CHAIN, each agent's into its job (frame_skills)
    got = {'read': [], 'failed': {}, 'unchanged': 0, 'lines': []}
    if not piece or piece[1] == 'rules':
        with rules.BUSY:
            got = rules.read_chain(store, agent, settings or frame.SETTINGS, app or frame.APP, chain, hire_with, force)
    failed = {**fell, **got['failed']}   # a failed skills read makes the run FAILED as a failed rules read does
    return {'agents': len(chain), 'skills': entries, **{k: v for k, v in got.items() if k not in ('lines', 'failed')}, 'failed': failed, 'lines': got['lines']}


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (its job's RUN, at the page's start, daily 06:50, or by hand): the chain's sanity written, then the summary of the day;
    kept with the run (its LOGS record). After a FAILED run whose first fault is one program's skills or rules read, that piece is read alone (piece_of) and its own LOGS record written at once; after a FAILED run whose fault is no read (the day, a crash, a summary not shown) the
    piece reads nothing, only the board and its record; when that piece's record is DONE, every other changed program is read next and written as its own record a second later
    (DONE, or FAILED naming its read). A missed 07:00 (its record's only fault 'today') is such a fault: the board alone, its own record. A run still reading
    counts as started today (RUNNING), so the 07:00:05 watch never calls a 06:50 run missed.
    DONE exit 0; a read that failed, a board not of today, or a summary that does not read back from its LOGS record: FAILED exit 1; past 07:00 New York with no run started today: FAILED exit 1
    as well (missed, by its own watch at 07:00:05, or, when the watch was unarmed by a host restart, written as that same FAILED record by the first run started past 07:00, before that run's own record, so one press fixes it either way).
    STARTED BY 07:00 means a run of its own started today before the missed check: a run started past 07:00 is green only after the
    day's missed FAILED record stands in LOGS before it (the day's red is kept, never hidden), and its DONE then says the chain was read.
    ITS MEASURED TIME: every run's summary says 'ran N s' (every read in it, each read at most 7 min, reader minutes 7, so a run is at most
    7 min a changed program's read); a piece's record says 'alone in N s', its own measured total, and the rest's record says
    'every other changed program read in M s', so the press's step (one piece) is measured and lit apart from the reads after it. -> what it wrote."""
    clock = datetime.datetime.now(zoneinfo.ZoneInfo(SCHEDULE['timezone']))
    started = clock.strftime('%Y-%m-%d %H:%M:%S')   # New York time, as the 06:50 schedule
    RUNNING[job_key] = clock.date().isoformat()   # STARTED TODAY: the 07:00:05 watch sees this run while it still reads
    end = lambda: None
    try:
        watch(store, job_key)   # NO RUN TODAY IS RED, measured by itself from here on (missed)
        RUNNING.pop(job_key, None)
        if missed(store, job_key):   # A MISSED 07:00 THE WATCH DID NOT SEE (a host restarted, its timer unarmed): its own FAILED record, as the watch writes it, before this run's record
            import time
            time.sleep(1.01)   # this run's record starts a second after it, so its read back (mine) is never the missed record
            clock = datetime.datetime.now(clock.tzinfo)
            started = clock.strftime('%Y-%m-%d %H:%M:%S')
        RUNNING[job_key] = clock.date().isoformat()
        late_fault = None   # this run is the one press that fixes the missed day, as after the watch's red: never a second press
        shape = frame.SETTINGS['root_shape']
        zone = zoneinfo.ZoneInfo(shape['x_board']['zone'])
        end = alive(store, job_key)   # ITS SIGN OF LIFE while it reads (minutes): RUNNING, written again every BEAT, so a live run is never called stuck
        return _run(store, job_key, n, agent, shells, chain, hire_with, now, shape, zone, clock, started, late_fault, end)
    except Exception as fault:   # noqa: BLE001  A CRASH IS RED: one FAILED record naming it and its one step, never an earlier DONE left standing as green
        end()
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        crash = f'its own run crashed ({line})'
        said = {'summary': f'FAILED: {crash} · {CRASH_STEP}', 'failed': {'crash': crash}, 'step': CRASH_STEP}
        store.ran(job_key, n, started, datetime.datetime.now(clock.tzinfo).strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps(said), 'FAILED')
        return said
    finally:
        end()
        RUNNING.pop(job_key, None)


CRASH_STEP = 'press RUN AGENT on the Scrum Master card once more; if it crashes the same way, send that line to a builder as a request'


BEAT = 60   # seconds between a reading run's signs of life (the frame calls an open RUN stuck after 3 minutes of none)


def alive(store, job_key):
    """A RUN THAT READS FOR MINUTES SAYS IT IS ALIVE: its job's RUN STATE RUNNING, written as its run's own step (run=True) at once and
    again every BEAT seconds while this run's thread lives; a run whose thread died writes none, so it is still called stuck. -> end(),
    which stops the beats before the run writes its end (never a RUNNING after its DONE or FAILED)."""
    import threading
    stop, lock = threading.Event(), threading.Lock()
    edit = getattr(store, '_edit', None)

    def beat():
        while True:
            with lock:
                if stop.is_set():
                    return
                try:
                    edit(job_key, {'run_state': 'RUNNING'}, run=True)
                except Exception:   # LARRYD busy for one beat: the next beat says it
                    pass
            if stop.wait(BEAT):
                return

    def end():
        with lock:
            stop.set()
    if callable(edit):
        threading.Thread(target=beat, daemon=True).start()
    return end


def _run(store, job_key, n, agent, shells, chain, hire_with, now, shape, zone, clock, started, late_fault, end=lambda: None):
    piece = piece_of(last_read(store, job_key), chain)   # after a skills or rules fault of one program: that piece first, past a missed 07:00's record
    last = latest(store, job_key) or {}
    if not piece and last.get('failed'):   # A FAULT THAT IS NO READ (a day, a missed 07:00, a crash, a summary not shown): its piece reads nothing
        piece = ('', 'none')
    said = sanity(store, agent, chain, hire_with=hire_with, piece=piece)
    if not piece:
        return _close(store, job_key, n, agent, shells, now, shape, zone, clock, started, late_fault, end, said, None)
    first = _close(store, job_key, n, agent, shells, now, shape, zone, clock, started, late_fault, end, said, piece)   # THE PIECE'S OWN RECORD: the light follows the one piece, never the rest
    if first['failed']:
        return first
    import time   # THE REST, its own record a second later: every other changed program read, a fault there red as any read
    time.sleep(1.01)
    clock = datetime.datetime.now(clock.tzinfo)
    started = clock.strftime('%Y-%m-%d %H:%M:%S')
    rest = sanity(store, agent, chain, hire_with=hire_with)
    return _close(store, job_key, n, agent, shells, now, shape, zone, clock, started, None, lambda: None, rest, None, after=piece)


def _close(store, job_key, n, agent, shells, now, shape, zone, clock, started, late_fault, end, said, piece, after=None):
    """ONE LOGS RECORD: the summary of the day over what was read (said), measured from clock; a piece's record names the piece alone
    and its measured seconds; the rest's record (after) names the piece it followed. -> what it wrote."""
    if late_fault:
        said['failed']['today'] = late_fault
    x = xboard.x_board(shells, shape['slots'], shape['x_board'], now, groups=xboard.x_groups(agent, shape['slots']))
    green, red, total = (sum(line[k] for line in x['lines']) for k in ('green', 'red', 'total'))
    said.update({'day': x['day'], 'green': green, 'red': red, 'total': total, 'word': 'CRITICAL' if red else 'HEALTHY'})
    today = datetime.datetime.now(zone).strftime('%a %b %d').upper() + ' (TODAY)'
    if x['day'] != today:   # TODAY'S RUN FED THE SUMMARY: a board of another New York day is a fault, never a green
        said['failed']['day'] = f"the summary is of {x['day'].replace(' (TODAY)', '')}, not today {today.replace(' (TODAY)', '')} in New York"
    ended = datetime.datetime.now(zone)
    said['seconds'] = round((ended - clock).total_seconds())   # THE MEASURED TIME of this record, every read in it
    if piece:
        said['piece'] = (f'{piece[1]} of {piece[0]} alone in {said["seconds"]} s' if piece[0] else f'no read, the board alone in {said["seconds"]} s') + ', every other changed program read next as its own record'
    elif after:
        said['piece'] = f'every other changed program read in {said["seconds"]} s, after ' + (f'{after[1]} of {after[0]}' if after[0] else 'the board alone')
    fault = next(iter(said['failed'].values()), '')

    def line(fault):
        return (f"{said['agents']} agents · {said['skills']} skills entries · {len(said['read'])} rules read · {said['unchanged']} unchanged · "
                f"{green} green · {red} red of {total} rows today · {said['word']} · ran {said['seconds']} s" + (f" · {said['piece']}" if said.get('piece') else '') + (f' · FAILED: {fault}' if fault else ''))
    said['summary'] = line(fault)
    end()   # the beats stop before its end is written
    store.ran(job_key, n, started, ended.strftime('%Y-%m-%d %H:%M:%S'), 1 if fault else 0, json.dumps(said), 'FAILED' if fault else 'DONE')
    own = mine(store, job_key, n, started)   # THE SUMMARY SHOWS: this run's own LOGS record read back (frame.run_said), never a later record of another run
    shown = said_of(own)
    if not shown or shown.get('summary') != said['summary'] or not str(frame.run_said(own)).strip():
        fault = fault or 'the summary does not show: its LOGS record read back is not what this run wrote'
        said['failed'].setdefault('shown', fault)
        said['summary'] = line(fault)
        store.ran(job_key, n, started, datetime.datetime.now(zone).strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps(said), 'FAILED')
    return said


RUNNING = {}   # job_key -> the New York day of its run still reading (started, its LOGS record not yet written)
LATE = '07:00'   # New York: today's run (06:50, the page's start, or RUN AGENT) must have started by the standup's 07:00


def late(store, job_key, now=None):
    """NO RUN STARTED TODAY BY 07:00 NEW YORK: past 07:00 with no record of its own (RUN 1 and up) started today. Writes nothing.
    -> the fault, or None"""
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    now = now or datetime.datetime.now(zone)
    h, m = (int(x) for x in LATE.split(':'))
    if now < now.replace(hour=h, minute=m, second=0, microsecond=0):
        return None
    today = now.date().isoformat()
    if RUNNING.get(job_key) == today:   # a run started today is still reading: its LOGS record is written when it ends
        return None
    if any(str(r['started_at'])[:10] == today for r in store.runs(job_key, 1000) if r['n'] >= 1):
        return None
    return f"no run of {KEY} started today ({today}) in New York by {LATE}: the summary is not of today's run"


def missed(store, job_key, now=None):
    """TODAY'S RUN OR RED, MEASURED: past 07:00 New York with no run of its own (RUN 1 and up) started today, its job's RUN ends
    FAILED, exit 1, naming the missing run, so a DONE run of another day never stands green for today's. -> the fault, or None"""
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    now = now or datetime.datetime.now(zone)
    fault = late(store, job_key, now)
    if not fault:
        return None
    today = now.date().isoformat()
    job = next((sh['job'] for sh in store.board() if sh.get('job_key') == job_key and sh.get('job')), None) or {}
    at = now.strftime('%Y-%m-%d %H:%M:%S')
    store.ran(job_key, max(int(job.get('data_job_run') or 0), 1), at, at, 1, json.dumps({'summary': f'FAILED: {fault}', 'failed': {'today': fault}}), 'FAILED')
    return fault


WATCHED = {}   # job_key -> its armed 07:00 timer: the missing run measured by itself, never only when a run happens


def watch(store, job_key):
    """THE MISSING RUN BY ITSELF: once the job runs, a timer wakes at 07:00 New York each day and runs missed(); armed once per
    job, then again for the next day."""
    import threading
    if job_key in WATCHED:
        return

    def wake():
        try:
            missed(store, job_key)
        except Exception:   # a check that crashed is retried the next morning, never a dead watch
            pass
        WATCHED.pop(job_key, None)
        watch(store, job_key)
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    now = datetime.datetime.now(zone)
    h, m = (int(x) for x in LATE.split(':'))
    at = now.replace(hour=h, minute=m, second=5, microsecond=0)
    if at <= now:
        at += datetime.timedelta(days=1)
    t = threading.Timer((at - now).total_seconds(), wake)
    t.daemon = True
    WATCHED[job_key] = t
    t.start()


def latest(store, job_key):
    """What its last run wrote, or None before a first run."""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        return faulted(r)
    return None


def faulted(r):
    """What a LOGS record says, its faults named: a FAILED record (exit not 0) the page wrote with no faults of its own (a run open
    when the page restarted, closed FAILED with that page) is a fault that is no read, 'page', so the next press builds the board
    alone in seconds, as after a crash, never a whole read taken as no fault. -> or None"""
    s = said_of(r)
    if r and int(r.get('exit') or 0) != 0 and not (s or {}).get('failed'):
        s = {**(s or {}), 'failed': {'page': (s or {}).get('summary') or 'FAILED'}}
    return s


def last_read(store, job_key):
    """What its last run that read wrote: the latest LOGS record past any missed 07:00's FAILED record (missed, its only fault
    'today', written by the watch or the press) and any run the page's restart ended (its only fault 'page'), so a program read
    that failed before a missed day or a restart is still read first. -> or None"""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True):
        s = faulted(r)
        failed = set(((s or {}).get('failed') or {}))
        if not failed or not failed <= {'today', 'page'}:
            return s
    return None


def mine(store, job_key, n, started):
    """The LOGS record one run wrote: its RUN number and its start, or None."""
    return next((r for r in store.runs(job_key, 1000) if int(r['n']) == int(n) and str(r['started_at'])[:19] == started), None)


def said_of(r):
    """What a LOGS record says, or None."""
    try:
        return json.loads(r['said']) if r else None
    except (ValueError, TypeError):
        return None
