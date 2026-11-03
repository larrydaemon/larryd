"""AGENT 006 · THE LIE DETECTOR, LIVE (the original's row 019, agent019_checks_lie_detector.py; the owner 2026-10-27: "this one is for
scrum master and should be red if there are any problems this is the real health of the system"): A SUB AGENT of the MARK IV agent
(agent001), lower rank, in the LIVE group. LIVE, ON EVERY CHANGE (the owner 2026-10-27: "not 5 minutes not anything else"): the page's
one watcher (frame/frame_live.py) looks the moment one of its TRIGGERS changes, its light kept in the office's live_status, a run written
on a flip. It reads the lie detector's own report.json, READ ONLY, where the original
reads it (the Scrum Master's settings reads lie_detector), its deadman from LARRY LLM's console.json (cebf.deadman, 900 s when none).

ITS RULE, THE ORIGINAL'S (the owner 2026-10-27: "the other original one used the other lie detector so why are you not doing the same as
the original?"; "12 is fine we can change it later"): the 12 pin and seal probes (S1 S2 S3 A3 A4 A5 B1-B5 G8) and nothing else. GREEN only
when the report is fresh (no older than its deadman, never more than 60 s ahead of the clock) and every pin probe is in it and says PASS.
RED for anything else: a report missing, unreadable or stale; a pin probe missing; a pin probe not PASS (FAIL or NO DATA). Every other
probe (D3, G4 and the rest) is never counted, as the original. Every failing pin probe is named, never one hiding another.

ITS STEP (the owner's 3 minutes, named, NEVER performed here): a pin or seal that differs -> press PIN AND RESEAL on the Scrum
Master's page, his fingerprint once (the original's REPIN); his pin newer than the report, or no fresh/whole report -> the lie
detector run again (RERUN: LARRY LLM's own cebf.run(), about 2 s); a pin probe missing or NO DATA -> the same RERUN. Other probes are
never counted, so no step is ever given for them. It never fixes, never presses, never writes anything but its own run."""
import datetime
import json
import os
import re
import zoneinfo

KEY = 'lie_detector'
SLOT = 'LIVE'   # where it lives: the LIVE group
ROW = 19   # its row in the original (agent019_checks_lie_detector)
NAME = 'Lie Detector'
CARD_NAME = 'Scrum Master Lie Detector'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'The real health of the system: red if there are any problems'   # the owner's own rule for it (2026-10-27)
WHAT = "Reads the lie detector's report the moment it changes: green only when all 12 pin and seal probes pass in a fresh report, red if any of them fails or is missing"
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'live', 'timezone': 'America/New_York'}   # LIVE: on every change of its TRIGGERS, never a clock (frame_red.due_at never misses a live job)
LIVE_SAID = 'LIVE · ON EVERY CHANGE'   # its clock's words
ROW_FILE = 'agent019_checks_lie_detector.py'   # the original's program for this row: its skills index is filed under it

REPORT = '~/virtual_workspace/lryllm/lryllm/instance/logs/cebf/report.json'   # the original's settings reads lie_detector (agent.json facts lie_detector overrides)
CONSOLE = '~/virtual_workspace/lryllm/lryllm/app/schemas/console.json'   # the original's settings reads console_json: cebf.deadman (agent.json facts console_json overrides)
READS = {'lie_detector': REPORT, 'console_json': CONSOLE}   # WHAT IT READS, the inputs of its look (a check points them at scratch)


def triggers(store=None):
    """ITS TRIGGERS, exactly its inputs: the lie detector's report and its configuration (the deadman)"""
    return [os.path.expanduser(READS['lie_detector']), os.path.expanduser(READS['console_json'])]


TRIGGERS = triggers()
DEADMAN = 900   # seconds, when console.json names none (the original's)
AHEAD = 60   # seconds a report may be dated ahead of this laptop's clock (the writer rounds to the minute); more is not current
PASS = 'PASS'
PIN_PROBES = ('S1', 'S2', 'S3', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5', 'G8')   # the original's pins and seals: their failing is the owner's re-pin
REPIN = "press PIN AND RESEAL on the Scrum Master's page (under the lock), your fingerprint once: it seals the vaults and the core, re-pins, waits for FROST's vault check and runs the lie detector itself"
RERUN = '''cd ~/virtual_workspace/lryllm/lryllm/app && env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 WID_ENV="${WID_ENV:-localhost.rnd}" ~/virtual_workspace/.venv/bin/python -c "from core_engine import cebf; r = cebf.run(); print(r['at'], r['verdict'], r['pass'], 'pass', r['fail'], 'fail', r['no_data'], 'no data', flush=True)"'''   # the lie detector run again, now: ONE whole run of LARRY LLM's own cebf.run() from its app/ with the workspace's python (about 2 s; never run here)
CEBF = f'run the lie detector again now (about 2 s): {RERUN}'
PIN_OF = re.compile(r'pin of (\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})')   # a probe's words name the pin it differs from


def _json(p):
    try:
        with open(os.path.expanduser(p), encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _local(at):
    """a report's moment (UTC, naive or zoned) said in New York: 'Oct 27 20:37'"""
    try:
        m = datetime.datetime.fromisoformat(at)
    except (TypeError, ValueError):
        return str(at)
    return (m if m.tzinfo else m.replace(tzinfo=datetime.timezone.utc)).astimezone(zoneinfo.ZoneInfo(SCHEDULE['timezone'])).strftime('%b %d %H:%M')


def _line(p):
    return f"{p.get('id')} {p.get('verdict')}: {' '.join(str(p.get('detail') or p.get('says') or '').split())[:100]}"


def judge(report_path=REPORT, console_path=CONSOLE, now=None):
    """THE REAL HEALTH, from the lie detector's report, read only. -> {'ok', 'said', 'failing': [ids], 'pins': [failing pin ids],
    'missing': [ids], 'step', 'at', 'age', 'probes': n, 'lines': [one per failing probe]}"""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    deadman = int(((_json(console_path) or {}).get('cebf') or {}).get('deadman') or DEADMAN)
    out = {'ok': False, 'failing': [], 'pins': [], 'missing': [], 'lines': [], 'at': '', 'age': None, 'probes': 0, 'deadman': deadman,
           'report': os.path.expanduser(report_path)}
    if not os.path.exists(os.path.expanduser(report_path)):
        return {**out, 'said': f'the lie detector did not run: no report at {report_path}', 'step': CEBF}
    report = _json(report_path)
    if not isinstance(report, dict) or not isinstance(report.get('rows'), list):
        return {**out, 'said': f'the lie detector did not run: its report at {report_path} is unreadable', 'step': CEBF}
    try:
        at = datetime.datetime.fromisoformat(str(report.get('at')))
    except ValueError:
        return {**out, 'said': f"the lie detector did not run: its report has no moment ({report.get('at')!r})", 'step': CEBF}
    age = int((now - (at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc))).total_seconds())
    out.update(at=_local(report['at']), age=age)
    if age > deadman:
        return {**out, 'said': f"the lie detector did not run: its report is of {out['at']}, {age // 60} min old, past its deadman of {deadman // 60} min", 'step': CEBF}
    if age < -AHEAD:
        return {**out, 'said': f"the lie detector did not run: its report of {out['at']} is dated ahead of the clock", 'step': CEBF}
    rows = [p for p in report['rows'] if isinstance(p, dict)]
    ids = [str(p.get('id')) for p in rows]
    out['probes'] = len(rows)
    missing = [x for x in PIN_PROBES if x not in ids]
    bad = [p for p in rows if p.get('verdict') != PASS and str(p.get('id')) in PIN_PROBES]   # THE 12 PIN AND SEAL PROBES ALONE (the original's rule)
    pins = [str(p.get('id')) for p in bad if str(p.get('id')) in PIN_PROBES and p.get('verdict') == 'FAIL']   # a pin that differs: his re-pin
    unmeasured = [str(p.get('id')) for p in bad if str(p.get('id')) in PIN_PROBES and p.get('verdict') != 'FAIL']   # a pin probe that could not measure: the detector not run whole (the original's)
    out.update(failing=[str(p.get('id')) for p in bad], pins=pins, missing=missing, lines=[_line(p) for p in bad])
    if not rows:
        return {**out, 'said': f"the lie detector did not run whole: its report of {out['at']} holds no probe", 'step': CEBF}
    if not bad and not missing:
        return {**out, 'ok': True, 'said': f"healthy: all {len(PIN_PROBES)} pin and seal probes pass (report of {out['at']})", 'step': ''}
    parts = []
    if bad:
        parts.append(f"{len(bad)} of {len(PIN_PROBES)} pin and seal probes fail: " + ', '.join(out['failing']))
    if missing:
        parts.append('pin probe(s) not in the report: ' + ', '.join(missing))
    after = ''
    for p in bad:   # his pin already made, the report not yet: the lie detector again, never a second press
        if str(p.get('id')) in PIN_PROBES:
            for m in PIN_OF.finditer(str(p.get('detail') or '')):
                if m.group(1).replace(' ', 'T') > str(report.get('at') or '')[:16]:
                    after = m.group(1).replace('T', ' ')
    steps = []
    if pins and not after:
        steps.append(REPIN)
    if after or missing or unmeasured:
        steps.append(f'run the lie detector again now (about 2 s; your pin of {after} is newer than this report): {RERUN}' if after else CEBF)
    return {**out, 'said': f"not healthy (report of {out['at']}): " + '; '.join(parts), 'step': ' · '.join(steps), 'after_pin': after}


def look(store=None, shells=None, now=None, agent=None):
    """ITS ONE LOOK, PURE (nothing written): the report judged. -> {'state': GREEN|RED, 'summary', 'why', 'step', 'said'} (said: what a run keeps)"""
    facts = (agent or {}).get('facts') or {}
    got = judge(facts.get('lie_detector') or READS['lie_detector'], facts.get('console_json') or READS['console_json'],
                now.astimezone(datetime.timezone.utc) if now else None)
    said = {'summary': ('GREEN · ' if got['ok'] else 'RED · ') + got['said'] + (f" · YOUR 3 MIN: {got['step']}" if got['step'] else ''),
            'looked_at': datetime.datetime.now(zoneinfo.ZoneInfo(SCHEDULE['timezone'])).strftime('%H:%M'), **got}   # 'looked_at', never 'written': the frame's run_said reads a record with 'written' as the standup's and hides this agent's own words
    return {'state': 'GREEN' if got['ok'] else 'RED', 'summary': said['summary'], 'why': '' if got['ok'] else got['said'], 'step': got['step'], 'said': said}


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT by hand; the page writes its live flips itself): one look, then its run written; GREEN DONE exit 0, RED FAILED exit 1
    with every failing probe and his step; a crash ends FAILED with its fault's one line. -> what it wrote."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        got = look(store, shells, now, agent)
        said, ok = got['said'], got['state'] != 'RED'
    except Exception as fault:   # A CRASH IS RED: never no record and no light
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        said, ok = {'summary': f'FAILED · {line}'}, False
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0 if ok else 1, json.dumps(said), 'DONE' if ok else 'FAILED')
    return said


def latest(store, job_key):
    """What its last run wrote, or None before a first run."""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except (TypeError, ValueError):
            return None
    return None


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS: words, never markup (web/page.py content_view): the health its last run read, every failing probe
    folded under it, his step last; else that nothing is read yet."""
    s = latest(store, job_key)
    if s is None:
        return [{'kind': 'note', 'title': 'The lie detector', 'text': 'Not read yet: its first look reads it (live, on every change, or RUN AGENT).'}]
    if 'said' not in s:
        return [{'kind': 'note', 'title': 'The lie detector', 'text': f"Not read: its last run {s.get('summary') or 'FAILED'}."}]
    lines = [('body', ('Healthy. ' if s.get('ok') else 'Not healthy. ') + s['said'], '')]
    if s.get('step'):
        lines.append(('subtitle', s['step'], 'your 3 min'))
    return [{'kind': 'words', 'title': 'The lie detector', 'under': f"Read at {s.get('looked_at') or s.get('written', '')}, by its run",
             'lines': lines, 'detail': [('failing', 'Failing probes', s.get('lines') or []), ('missing', 'Missing pin probes', s.get('missing') or [])]}]


def until_next(now=None, schedule=None):
    """LIVE: no next time (it looks on every change of its triggers): None"""
    return None


def clock(schedule=None):
    """Its clock in its shell: NEW YORK · LIVE · ON EVERY CHANGE (no hands: no hour it waits for)."""
    schedule = schedule or SCHEDULE
    return {'zone': schedule['location'], 'at': '', 'said': LIVE_SAID, 'when': LIVE_SAID, 'repeat': LIVE_SAID, 'hour_deg': 0, 'minute_deg': 0}
