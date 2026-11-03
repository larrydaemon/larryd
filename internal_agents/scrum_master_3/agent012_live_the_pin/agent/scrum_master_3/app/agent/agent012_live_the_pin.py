"""AGENT 007 · THE PIN, LIVE (the original's row 020 THE PIN, agent020_checks_the_pin.py, ported whole): a SUB AGENT of the MARK IV
agent (agent001), lower rank, its job in the LIVE slot, LIVE: the page's one watcher (frame/frame_live.py) looks the moment its TRIGGERS
change (the lie detector's report, its configuration), its light kept in the office's live_status, a run written on a flip. One look at the lie detector's own report (cebf
report.json, read only): the Judge's pin (probe A3, the old THE HAMMER IS PINNED) and the core's seal (probes A5 and every B, the old
THE SEAL), said together. It never fixes: a red names the owner's own 3 minute step (PIN AND RESEAL on his page, his fingerprint
once; or the lie detector run again, RERUN), which this program never performs.

THE RULE (the original's, ROW 020 THE PIN rules LEGIT; the rule itself lives in the database): it is red if the report is missing, unreadable, older than its deadman (console.json
cebf deadman, 900 s when none) or over 60 s ahead of the clock; or it has no A3, or no A5 or B probes; or any of them is not PASS for
a real fault. It is green if A3, A5 and every B in a current report say PASS, said with the report's time. HELD (green, said 'held: ...')
when every probe that is not a PASS says only "no pin" or "no baseline": nothing pinned yet, on the owner's word.
SELF-CONTAINED: stdlib only; the original's shared_* modules are read, never imported."""
import datetime
import json
import os
import re
import subprocess
import zoneinfo

KEY = 'the_pin'
SLOT = 'LIVE'   # where it lives: the LIVE slot
ROW = 20   # its row in the original (agent020_checks_the_pin)
NAME = 'The Pin'
CARD_NAME = 'Scrum Master The Pin'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'The Judge and the sealed core still match their pin'   # its card's pitch (the original's row job line)
WHAT = "The Judge's pin and the sealed core's seal, read from the lie detector's report the moment it changes"   # what it does, its one line
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'live', 'timezone': 'America/New_York'}   # LIVE: on every change of its TRIGGERS, never a clock (frame_red.due_at never misses a live job)
LIVE_SAID = 'LIVE · ON EVERY CHANGE'
ROW_FILE = 'agent020_checks_the_pin.py'   # the original's program for this row: its skills index is filed under it

# ITS PLACES, read only: the original's settings.json reads lie_detector and console_json (the lie detector's own report and configuration)
REPORT = os.path.expanduser('~/virtual_workspace/lryllm/lryllm/instance/logs/cebf/report.json')
CONSOLE = os.path.expanduser('~/virtual_workspace/lryllm/lryllm/app/schemas/console.json')
ZONE = zoneinfo.ZoneInfo('America/New_York')   # the original's clock (settings scrum.zone)


def triggers(store=None):
    """ITS TRIGGERS, exactly its inputs: the lie detector's report and its configuration (the deadman)"""
    return [REPORT, CONSOLE]


TRIGGERS = triggers()

PASS = 'PASS'   # the lie detector's own verdict word
DEADMAN = 900   # seconds, when console.json cebf names none
AHEAD = 60   # seconds a report may be dated ahead of this clock (the writer rounding to its minute)
PIN_HELD = "not pinned yet, on the owner's word (the data fields first)"
HAND = 'YOUR 3 MIN: '
MOST = 800   # a run's text is cut to this: the why is cut before his step ever is (800: RERUN, the whole command, is ~300 of it)
RERUN = '''cd ~/virtual_workspace/lryllm/lryllm/app && env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 WID_ENV="${WID_ENV:-localhost.rnd}" ~/virtual_workspace/.venv/bin/python -c "from core_engine import cebf; r = cebf.run(); print(r['at'], r['verdict'], r['pass'], 'pass', r['fail'], 'fail', r['no_data'], 'no data', flush=True)"'''   # the lie detector run again, now: ONE whole run of LARRY LLM's own cebf.run() from its app/ with the workspace's python (about 2 s; never run here)
PIN_AND_RESEAL = ("press PIN AND RESEAL on this page (under the lock), your fingerprint once: it seals the vaults and the core, re-pins, "
                  "waits for FROST's vault check and runs the lie detector itself")
PIN_OF = re.compile(r'pin of (\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})')   # the probe's own words name the pin it differs from


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def seen(report=None, console=None, now=None):
    """THE LIE DETECTOR'S OWN REPORT (the original's shared_work_list.seen): {'report': {at, verdict, rows} or None, 'age', 'silent',
    'deadman'}; a report without rows or without a readable 'at' is None; silent: older than its deadman or over AHEAD s ahead."""
    got = _json(report or REPORT)
    got = got if isinstance(got, dict) and isinstance(got.get('rows'), list) else None
    try:
        deadman = int(((_json(console or CONSOLE) or {}).get('cebf') or {}).get('deadman') or DEADMAN)
    except (TypeError, ValueError, AttributeError):
        deadman = DEADMAN
    age = None
    if got:
        try:
            at = datetime.datetime.fromisoformat(got['at'])
            at = at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc)
            age = int(((now or datetime.datetime.now(datetime.timezone.utc)) - at).total_seconds())
        except (ValueError, KeyError, TypeError):
            got = None
    return {'report': got, 'age': age, 'silent': got is not None and (age > deadman or age < -AHEAD), 'deadman': deadman}


def said(ok, text, held=False):
    return {'ok': None if held else ok, 'said': text, 'held': bool(held)}


def by_probes(state, what, *ids):
    """ONE PART (the original's _by_probes): the report's rows of these ids (an id ending in * names every id it begins), judged."""
    rows_by = {p['id']: p for p in ((state.get('report') or {}).get('rows') or []) if isinstance(p, dict) and 'id' in p}
    rows = [(i, rows_by[i].get('verdict'), rows_by[i].get('detail', '')) for i in rows_by
            if i in ids or any(i.startswith(x[:-1]) for x in ids if x.endswith('*'))]
    if state.get('silent') or not state.get('report'):
        return said(False, f'the lie detector is silent: {what} cannot be read')
    if not rows:
        return said(False, f"the lie detector's report has no {what} probes ({', '.join(ids)}): {what} cannot be read")
    bad = [f'{i} {v}: {d}'[:120] for i, v, d in rows if v != PASS]
    unpinned = [i for i, v, d in rows if v != PASS and re.search(r'no pin|no baseline', str(d))]
    if bad and len(unpinned) == len(bad):   # every non-pass only because nothing was pinned yet: the owner's ruling, held
        return said(None, f"{PIN_HELD}: {', '.join(unpinned)}", held=True)
    return said(not bad, '; '.join(bad[:3]) + (f' (+{len(bad) - 3} more)' if len(bad) > 3 else '') if bad
                else f"{what}: {', '.join(i for i, _v, _d in rows)} pass")


def pin(parts):
    """THE HAMMER and THE SEAL together: red when either is red; held when every part not red is held; green when both pass."""
    oks = [p['ok'] for _, p in parts]
    ok = False if False in oks else None if None in oks else True
    held = ok is None and all(p.get('held') for _, p in parts if p['ok'] is None)
    return said(ok, ' · '.join(f"{label}: {p['said']}" for label, p in parts), held=held)


def read_at(state):
    """when the lie detector wrote the report, in New York time ('Oct 27 20:37'), or ''"""
    try:
        at = datetime.datetime.fromisoformat(str((state.get('report') or {}).get('at')))
    except (TypeError, ValueError):
        return ''
    at = at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc)
    return at.astimezone(ZONE).strftime('%b %d %H:%M')


def after_his_pin(parts, state):
    """HIS RE-PIN ALREADY MADE, THE REPORT NOT YET: a probe that differs from a pin newer than the report's 'at' (compared as the
    original compares them, text to text). -> the pin's time or ''"""
    at = str((state.get('report') or {}).get('at') or '')
    if not at:
        return ''
    for _label, p in parts:
        for m in PIN_OF.finditer(str(p.get('said') or '')):
            pin_at = m.group(1).replace(' ', 'T')
            if pin_at > at[:16]:
                return pin_at
    return ''


def running(words=r'rerun_lie_detector|cebf\.run\(\)'):
    """the pid of a lie detector run now ('' when none): pgrep, read only, a process-name match (the launchd watcher's, or RERUN's own cebf.run())"""
    try:
        got = subprocess.run(['pgrep', '-f', words], capture_output=True, text=True, timeout=10)
        return next((p for p in str(got.stdout or '').split() if p.isdigit()), '')
    except Exception:   # noqa: BLE001
        return ''


def _fit(head, tail):
    if len(head) + len(tail) <= MOST:
        return head + tail
    return head[:max(0, MOST - len(tail) - 1)].rstrip() + '…' + tail


def chunk(text, waiting='', step=''):
    """A RED UNDER THE 3 MINUTE RULE: why first, what works on it now, his one step last (YOUR 3 MIN: ...), the step never cut."""
    tail = f' · at work on it now: {waiting}' if waiting else ''
    return _fit(text, f'{tail} · {HAND}{step}') if step else (_fit(text, tail) if tail else text)


def judge(report=None, console=None, now=None, pid=None):
    """ROW 020's ONE JUDGEMENT. -> {'state': green|red, 'held', 'text', 'step', 'waiting', 'hammer', 'seal', 'report_at', 'age', 'deadman'}"""
    state = seen(report, console, now)
    parts = [('the hammer', by_probes(state, 'the Judge', 'A3')), ('the seal', by_probes(state, 'the core', 'A5', 'B*'))]
    word = pin(parts)
    at = read_at(state)
    tail = f' · the lie detector of {at}' if at else ''
    out = {'held': bool(word.get('held')), 'hammer': parts[0][1]['said'], 'seal': parts[1][1]['said'], 'report_at': at,
           'age': state['age'], 'deadman': state['deadman'], 'step': '', 'waiting': ''}
    if word.get('held'):
        return {**out, 'state': 'green', 'text': f"held: {word['said']}{tail}"}
    text = word['said'] + tail
    if word['ok'] is True:
        return {**out, 'state': 'green', 'text': text}
    pid = running() if pid is None else pid
    if any('has no' in p['said'] and 'probes' in p['said'] for _, p in parts):
        out['waiting'] = f'the lie detector running now (pid {pid})' if pid else ''
        out['step'] = f"these probes are not in the lie detector's report: put them back in its configuration ({CONSOLE}, the cebf entry), then run it: {RERUN}"
    elif any('cannot be read' in p['said'] for _, p in parts):
        out['waiting'] = f'the lie detector running now (pid {pid})' if pid else ''
        out['step'] = RERUN
    elif (pinned := after_his_pin(parts, state)):
        out['waiting'] = f"the lie detector's next run (its report is older than your pin of {pinned.replace('T', ' ')}; run it now: {RERUN})"
    else:
        out['step'] = PIN_AND_RESEAL   # the hammer off its pin (re-pin) or the seal broken (reseal): his one press, his fingerprint
    return {**out, 'state': 'red', 'text': chunk(text, out['waiting'], out['step'])}


def look(store=None, shells=None, now=None):
    """ITS ONE LOOK, PURE (nothing written). -> {'state': GREEN|RED, 'summary', 'why', 'step', 'said'} (said: what a run keeps; held is GREEN)"""
    got = judge(now=now)
    said = {'summary': ('GREEN · ' if got['state'] == 'green' else 'RED · ') + got['text'], 'looked_at': datetime.datetime.now(ZONE).strftime('%H:%M'), **got}   # 'looked_at', never 'written': the frame's run_said reads a record with 'written' as the standup's and hides this agent's own words
    green = got['state'] == 'green'
    return {'state': 'GREEN' if green else 'RED', 'summary': said['summary'], 'why': '' if green else (got['hammer'] + ' · ' + got['seal']), 'step': got['step'], 'said': said}


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT; the page writes its live flips itself): one look, kept with the run. Green (or held): DONE, exit 0; red: FAILED, exit 1,
    its why and the owner's 3 minute step; a crash: FAILED, exit 1, its one line. -> what it wrote."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        got = look(store, shells, now)
        said_ = got['said']
        end, code = ('DONE', 0) if got['state'] == 'GREEN' else ('FAILED', 1)
    except Exception as fault:   # noqa: BLE001  a crash is red, never no record
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        said_, end, code = {'summary': f'FAILED · {line}'}, 'FAILED', 1
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code, json.dumps(said_), end)
    return said_


def latest(store, job_key):
    """What its last run wrote, or None before a first run."""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except (ValueError, TypeError):
            return None
    return None


def until_next(now=None, schedule=None):
    """LIVE: no next time (it looks on every change of its triggers): None"""
    return None


def clock(schedule=None):
    """Its clock in its shell: NEW YORK · LIVE · ON EVERY CHANGE (no hands: no hour it waits for)."""
    schedule = schedule or SCHEDULE
    return {'zone': schedule['location'], 'at': '', 'said': LIVE_SAID, 'when': LIVE_SAID, 'repeat': LIVE_SAID, 'hour_deg': 0, 'minute_deg': 0}


def content(store, job_key, block=None):
    """ITS OWN CONTENT ON THE ONE CANVAS: words, never markup: its last look (the hammer, the seal, the report's time, the owner's step
    when red); else that nothing is looked at yet; a crashed run says its fault."""
    s = latest(store, job_key)
    if s is None:
        return [{'kind': 'note', 'title': 'The pin', 'text': 'Not looked at yet: its first look comes on the page\'s start (live, on every change, or RUN AGENT).'}]
    if 'state' not in s:
        return [{'kind': 'note', 'title': 'The pin', 'text': f"Not looked at: its last run {s.get('summary') or 'FAILED'}."}]
    head = 'GREEN, held on your word: nothing pinned yet' if s.get('held') else ('GREEN: the Judge and the core match their pin' if s['state'] == 'green' else 'RED: the pin or the seal does not hold')
    lines = [('body', head, ''), ('subtitle', f"The hammer (A3): {s['hammer']}", 'hammer'), ('subtitle', f"The seal (A5, B): {s['seal']}", 'seal')]
    if s.get('waiting'):
        lines.append(('body', f"At work on it now: {s['waiting']}", 'waiting'))
    if s.get('step'):
        lines.append(('body', f"{HAND}{s['step']}", 'step'))
    return [{'kind': 'words', 'title': 'The pin', 'under': f"Looked at {s.get('looked_at') or s.get('written', '')}, the lie detector's report of {s.get('report_at') or 'no time'}",
             'lines': lines, 'detail': [('report', 'The report', [f"age {s.get('age')} s, deadman {s.get('deadman')} s", s['text']])]}]
