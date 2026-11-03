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
first fault named with its one step (RUN AGENT again; a fault that comes back, that agent's program fixed); a run that crashes anywhere is
FAILED too, never no record. Its logs are its runs, LARRYD's LOGS."""
import datetime
import json
import sqlite3
import time
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
NEW_YORK = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
DUE = '07:00'             # its rule: no run started by 07:00 New York is red, 'not measured'
PIECE = 180               # the owner's 3 minutes: RUN AGENT after a failed run reads again one piece, its reads given 180 seconds in all
LOCKED_TRIES = 3          # "database is locked" (another writer held LARRYD past the store's 5 s wait): the rules read tried at most 3 times, then FAILED as before
LOCKED_WAIT = 5           # seconds between those tries
FLOOR = 30                # the frame's hire never runs a read shorter than 30 seconds: less left than that, the read is not started


def ny_day(now=None):
    """The New York day (YYYY-MM-DD) of now, or of this moment: the day a run is stamped with and judged by."""
    return (now.astimezone(NEW_YORK) if now and now.tzinfo else datetime.datetime.now(NEW_YORK)).strftime('%Y-%m-%d')


def sanity(store, agent, chain, settings=None, app=None, hire_with=None, force=False):
    """THE CHAIN'S SANITY INTO EACH AGENT'S JOB: every agent of the office (itself first, then its sub agents; chain: (module, shell)
    pairs, each shell holding a job): its skills from the index, written where they changed; its rule carried from his record and judged against its program by the
    reader where the program changed (frame_rules.read_chain), its lie detector; one read at a time in this office. A read that fails, the
    skills' or the rules', is a fault named under its agent's file, never lost. -> what it did."""
    entries, failed = 0, {}
    for module, shell in chain:   # THE SKILLS OF THE CHAIN, each agent's into its job (frame_skills), one agent at a time so a failed read names its agent
        try:
            entries += skills.read_chain(store, agent, [(module, shell)], settings or frame.SETTINGS, app or frame.APP, hire_with, force)
        except Exception as fault:
            failed.setdefault(file_of(module), f'skills not read: {line_of(fault)}')
    try:
        with rules.BUSY:
            for attempt in range(LOCKED_TRIES):   # LARRYD held by another writer past the store's own wait: the read again after a pause, its programs already read cost no read
                try:
                    got = rules.read_chain(store, agent, settings or frame.SETTINGS, app or frame.APP, chain, hire_with, force)
                    break
                except sqlite3.OperationalError as fault:
                    if 'locked' not in str(fault) or attempt == LOCKED_TRIES - 1:
                        raise
                    time.sleep(LOCKED_WAIT)
    except Exception as fault:
        got = {'read': [], 'failed': {'frame_rules.py': f'rules not read: {line_of(fault)}'}, 'unchanged': 0, 'seeded': [], 'none': [], 'lines': []}
    for file, why in got['failed'].items():
        failed.setdefault(file, why)
    return {'agents': len(chain), 'skills': entries, **{k: v for k, v in got.items() if k not in ('lines', 'failed')}, 'failed': failed, 'lines': got['lines']}


def file_of(module):
    """An agent's program file, the name its fault is filed under."""
    return (getattr(module, '__file__', '') or getattr(module, '__name__', '') or '?').rpartition('/')[2]


def line_of(fault):
    """A fault's one line: its kind and its first words."""
    return (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]


def step(file, fault):
    """THE ONE STEP A RED NAMES (its rule's FIX): RUN AGENT reads again only the first file today's failed run named (retry_of), every other
    agent left as it was, its reads within one 3 minute piece (within); a fault that comes back is in that agent's own program, named. How long
    the read took is measured, never guessed: each run keeps its seconds on its line."""
    return f'{file}: {fault} · step: RUN AGENT again; if it comes back, fix {file}'


def retry_of(store, job_key, chain):
    """THE ONE FAILED PIECE AGAIN: when this job's latest run today (New York day) ended FAILED naming agent files, only the first of them is read
    again (one piece, the one its summary names); a crash or a whole rules read that failed (frame_rules.py): the whole chain, where every program
    unchanged since its last read costs no read. No failed run today: the whole chain, not a retry. The X board's fault (frame_xboard.py) reads
    no agent again: the board is built anew every run. Every other agent file the failed run named and this piece does not read again stays
    FAILED with its own fault (kept), never a green over an agent not read again. -> (the chain to read, a retry or not, the faults kept)."""
    last = latest(store, job_key) or {}
    failed = last.get('failed') or {}
    named = list(failed)
    if not named or last.get('not_measured'):
        return chain, False, {}
    if set(named) & {'run', 'frame_rules.py'}:
        return chain, True, {}
    again = [(m, sh) for m, sh in chain if file_of(m) == named[0]]
    if not again and named[0] != 'frame_xboard.py':
        return chain, True, {}
    agents = {file_of(m) for m, sh in chain}
    kept = {f: why for f, why in failed.items() if f != named[0] and f in agents}
    return again, True, kept


def within(hire_with, seconds):
    """THE 3 MINUTE PIECE: every read of a retry shares one clock of seconds; a read gets what is left (never more than the frame's own cap), and
    none is started with less than the frame's floor left, so the press ends within 3 minutes and a read that does not fit fails, named."""
    end = time.monotonic() + seconds

    def hire(cmd, words, cwd, cap, job_path=''):
        left = end - time.monotonic()
        if left < FLOOR:
            return None, f'the {seconds} second piece ran out before this read'
        return (hire_with or frame.hire)(cmd, words, cwd, min(cap, int(left)), job_path)
    return hire


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (its job's RUN, at the page's start, daily 06:50, or by hand): the chain's sanity written, then the summary of the day;
    kept with the run (its LOGS record). DONE exit 0; a read that failed, or a run that crashed anywhere: FAILED exit 1, the first fault
    and its one step on the line, so a red is never no record and no light. -> what it wrote."""
    started, clock, day = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time.monotonic(), ny_day()
    try:
        shape = frame.SETTINGS['root_shape']
        again, retry, kept = retry_of(store, job_key, chain)
        piece = retry and len(again) < len(chain)   # one named file again (an agent's, or the X board's with no agent read): the 3 minute piece; the whole chain again (a crash, a whole rules read): its own measured time (74 to 250 s), never cut by the piece
        if again:
            said = sanity(store, agent, again, hire_with=within(hire_with, PIECE) if piece else hire_with)
        else:   # the X board's fault again: no agent read, only the board built anew below
            said = {'agents': len(chain), 'skills': 0, 'read': [], 'unchanged': 0, 'seeded': [], 'none': [], 'failed': {}, 'lines': []}
        for file, why in kept.items():   # the failed run's other agents, not read again by this piece: still FAILED, each next on RUN AGENT
            said['failed'].setdefault(file, why)
        x = xboard.x_board(shells, shape['slots'], shape['x_board'], now, groups=xboard.x_groups(agent, shape['slots']))
        green, red, total = (sum(line[k] for line in x['lines']) for k in ('green', 'red', 'total'))
        said.update({'day': x['day'], 'green': green, 'red': red, 'total': total, 'word': 'CRITICAL' if red else 'HEALTHY'})
        today = (now.astimezone(NEW_YORK) if now and now.tzinfo else datetime.datetime.now(NEW_YORK)).strftime('%a %b %d').upper() + ' (TODAY)'
        if x.get('day') != today:   # ITS RULE: red if the X board is not today's (New York day)
            said['failed'].setdefault('frame_xboard.py', f"the X board is not today's: it says {x.get('day')!r}, today is {today!r} New York")
        if not x.get('lines'):      # ITS RULE: red if the summary does not show: an X board with no line shows nothing
            said['failed'].setdefault('frame_xboard.py', 'the summary does not show: the X board has no line')
        fault = next((step(f, why) for f, why in said['failed'].items()), '')
        said['summary'] = (f"{said['agents']} agents · {said['skills']} skills entries · {len(said['read'])} rules read · {said['unchanged']} unchanged · "
                           f"{green} green · {red} red of {total} rows today · {said['word']} · run {day} New York, "
                           f"{round(time.monotonic() - clock)} s" + (f' · FAILED: {fault}' if fault else ''))
        if not fault and not (day in said['summary'] and said['word'] in said['summary']):   # the summary line names today and its word, or it is red
            fault = step(__file__.rpartition('/')[2], 'the summary does not show today and HEALTHY or CRITICAL')
            said['failed']['run'] = fault
            said['summary'] += f' · FAILED: {fault}'
    except Exception as crash:   # A RUN THAT CRASHES IS RED: FAILED, exit 1, its fault on the line
        fault = step(__file__.rpartition('/')[2], f'the run crashed: {line_of(crash)}')
        said = {'failed': {'run': fault}, 'summary': f'FAILED: {fault} · run {day} New York, {round(time.monotonic() - clock)} s'}
    said.update({'ny_day': day, 'seconds': round(time.monotonic() - clock)})   # WHEN IT RAN AND HOW LONG, kept with the run: a run of another day is never today's
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1 if fault else 0, json.dumps(said), 'FAILED' if fault else 'DONE')
    return said


def latest(store, job_key, now=None):
    """What its last run TODAY (New York day) wrote. No run today: before 07:00 New York None (not due yet); from 07:00 on a red, 'not measured',
    its step RUN AGENT, as its rule says (no run started by 07:00 is red) and never a green."""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            said = json.loads(r['said'])
        except (TypeError, ValueError):
            said = None
        if isinstance(said, dict) and said.get('ny_day') == ny_day(now):
            return said
    clock = (now.astimezone(NEW_YORK) if now and now.tzinfo else datetime.datetime.now(NEW_YORK)).strftime('%H:%M')
    if clock < DUE:
        return None
    why = f'not measured: no run started today ({ny_day(now)}) by {DUE} New York · step: RUN AGENT'
    return {'not_measured': True, 'failed': {'run': why}, 'ny_day': ny_day(now), 'summary': f'FAILED: {why}'}
