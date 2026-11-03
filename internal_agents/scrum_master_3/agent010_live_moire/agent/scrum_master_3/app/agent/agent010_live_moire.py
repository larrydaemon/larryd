"""AGENT 005 · MOIRÉ, LIVE (the original's row 018, agent018_checks_moire.py, ported whole into this office): a SUB AGENT of the MARK IV
agent (agent001), lower rank, its job in a LIVE shell, LIVE: the page's one watcher (frame/frame_live.py) looks the moment its TRIGGERS change
(the lie detector's report and configuration, MOIRÉ's baseline, git's index and HEAD of the workspace), its light kept in the office's
live_status, a run written on a flip. What changed since MOIRÉ's baseline, shown as a report.

THE OWNER'S RULE FOR IT (his words): "red is only if its not running. a change is not a red." (and 2026-10-23: "any work we do will make
this drift so the red is the report not working and green if working. nothing to do with the data in the report. or we could never build
anything"). So: DONE, exit 0, whenever the change report runs, whatever it shows; the changes are information only: the drift the lie
detector's probe D3 counts since the baseline (WRITTEN changes, said yellow) and the workspace's files not as git has them (UNWRITTEN
changes, not committed yet, said red in the original's wording), never the light. FAILED, exit 1, ONLY when the report is not running:
the lie detector's report is missing, unreadable, older than its deadman (or dated ahead of the clock), wrote no probe D3 or no drift
count, or git does not answer for the workspace; the why first, the owner's one step last (the 3 minute rule). A crash ends FAILED too.
A missing baseline is never red: D3 saying "no baseline" has nothing to count yet, and freezing one is the owner's own act.

SELF-CONTAINED: stdlib only; it never imports the original's shared_* modules. It reads the same files the original reads, READ ONLY
(the original's settings.json reads: workspace, lie_detector, console_json, moire_baseline), and asks git with no optional locks so even
git's index is never touched. It reads and reports, never fixes, and never asks for a new baseline (the baseline is the owner's own act)."""
import datetime
import json
import os
import re
import subprocess
import time
import zoneinfo

KEY = 'moire'
SLOT = 'LIVE'   # where it lives: a shell of LIVE
ROW = 18   # its row in the original (agent018_checks_moire)
NAME = 'Moiré'
CARD_NAME = 'Scrum Master Moiré'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Moiré: what changed, shown; red only when the report is not running'
WHAT = 'What changed since the baseline, shown as information: red only when the change report is not running'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'live', 'timezone': 'America/New_York'}   # LIVE: on every change of its TRIGGERS, never a clock (frame_red.due_at never misses a live job)
LIVE_SAID = 'LIVE · ON EVERY CHANGE'
ROW_FILE = 'agent018_checks_moire.py'   # the original's program for this row: its skills index is filed under it

# THE FILES IT READS, READ ONLY: the original's own settings.json reads, by the same names (the replica cannot import the original)
READS = {'workspace': os.path.expanduser('~/virtual_workspace'),
         'lie_detector': os.path.expanduser('~/virtual_workspace/lryllm/lryllm/instance/logs/cebf/report.json'),
         'console_json': os.path.expanduser('~/virtual_workspace/lryllm/lryllm/app/schemas/console.json'),
         'moire_baseline': os.path.expanduser('~/virtual_workspace/lryllm/lryllm/instance/logs/moire/baseline.json')}


def triggers(store=None):
    """ITS TRIGGERS, exactly its inputs: the lie detector's report and configuration, MOIRÉ's baseline, and what git status reads of the workspace
    that moves the answer (its index and HEAD: a commit, an add, a checkout)"""
    git = os.path.join(READS['workspace'], '.git')
    return [READS['lie_detector'], READS['console_json'], READS['moire_baseline'], os.path.join(git, 'index'), os.path.join(git, 'HEAD')]


TRIGGERS = triggers()

PASS = 'PASS'   # the lie detector's own verdict word, as its report.json writes it
DEADMAN = 900   # the lie detector's deadman when console.json names none (the original's shared_work_list default)
MOIRE_PROBE = 'D3'   # MOIRÉ's own measure in the lie detector: the workspace and the core's tables against its baseline
DRIFT = re.compile(r'^\s*(\d+)\s+drift')   # the probe's own words for a drift: "38 drift: 15 folders · 22 files changed"
NO_BASELINE = re.compile(r'no baseline')   # the probe's own words with nothing frozen: "MOIRÉ has no baseline frozen: nothing to compare with"
NOT_WORKING = 'the report is not working: '   # the one red, said first
HAND = 'YOUR 3 MIN: '   # THE 3 MINUTE RULE: the owner's one step, said last, never cut
RERUN = '''cd ~/virtual_workspace/lryllm/lryllm/app && env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 WID_ENV="${WID_ENV:-localhost.rnd}" ~/virtual_workspace/.venv/bin/python -c "from core_engine import cebf; r = cebf.run(); print(r['at'], r['verdict'], r['pass'], 'pass', r['fail'], 'fail', r['no_data'], 'no data', flush=True)"'''   # the lie detector run again, now: ONE whole run of LARRY LLM's own cebf.run() from its app/ with the workspace's python (about 2 s; never run here)
GIT_STEP = 'git -C ~/virtual_workspace status (the workspace must be a repository\'s own top and git must answer: what it prints is the fault; the lie detector cannot clear this)'
GIT_SECONDS = 90   # git's whole answer, both its calls together: one budget, never 90 s each
MOST = 800   # a run's summary is cut to this: the why is cut before the step ever is (800: RERUN, the whole command, is ~300 of it)


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def baseline(reads=None):
    """MOIRÉ's frozen baseline as its page wrote it, or None (none frozen, or not a whole file)."""
    got = _json((reads or READS)['moire_baseline'])
    return got if isinstance(got, dict) and got else None


def seen(reads=None, now=None):
    """THE LIE DETECTOR'S OWN REPORT (the original's shared_work_list.seen): {'report' or None, 'age' s, 'silent', 'deadman', 'why_none'}.
    silent: older than its deadman, or more than a minute ahead of this clock."""
    reads = reads or READS
    path = reads['lie_detector']
    raw = _json(path)
    why_none = '' if raw is not None else ('the lie detector has never run (no report at ' + path + ')' if not os.path.exists(path)
                                           else 'the lie detector\'s report is unreadable (' + path + ')')
    report = raw if isinstance(raw, dict) and isinstance(raw.get('rows'), list) else None
    if raw is not None and report is None:
        why_none = 'the lie detector\'s report is not a whole report (no rows)'
    try:
        deadman = int(((_json(reads['console_json']) or {}).get('cebf') or {}).get('deadman') or DEADMAN)
    except (TypeError, ValueError, AttributeError):
        deadman = DEADMAN
    age = None
    if report:
        try:
            at = datetime.datetime.fromisoformat(report['at'])
            now = now or datetime.datetime.now(datetime.timezone.utc)
            age = int((now - (at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc))).total_seconds())
        except (ValueError, KeyError, TypeError):
            report, why_none = None, 'the lie detector\'s report has no readable time (at)'
    return {'report': report, 'age': age, 'silent': report is not None and (age > deadman or age < -60), 'deadman': deadman, 'why_none': why_none}


def drift(reads=None, now=None):
    """The drift as the lie detector's probe D3 wrote it: (count or None, its words with the report's time, why the report does not work or '').
    D3 saying "no baseline" is no fault: no count, its words, no why (the report runs; RERUN could never freeze one)."""
    state = seen(reads, now)
    report = state['report']
    if not report:
        return None, '', state['why_none'] or 'the lie detector has never run'
    of = f"report of {str(report.get('at', ''))[11:16]}"
    if state['silent']:
        return None, '', f"the lie detector is silent: its {of} is older than its deadman ({state['deadman']} s; {state['age']} s old)"
    p = {r.get('id'): r for r in report['rows'] if isinstance(r, dict)}.get(MOIRE_PROBE)
    if not p:
        return None, '', f'the lie detector wrote no probe {MOIRE_PROBE}'
    detail = str(p.get('detail', ''))
    if p.get('verdict') == PASS:
        return 0, ' · '.join(x for x in (detail, of) if x), ''
    m = DRIFT.match(detail)
    if m:
        return int(m.group(1)), f'{detail} · {of}', ''
    if NO_BASELINE.search(detail):
        return None, f'{detail} · {of}', ''
    return None, '', f"the lie detector's {MOIRE_PROBE} gave no drift count ({p.get('verdict')}: {detail[:80]}; {of})"


def written(workspace=None):
    """THE WRITTEN TRUTH, asked of git each time: the workspace's files not as committed (extra, missing, changed; a rename once).
    -> {read, drift, first}; read False when the workspace is no repository's own top or git does not answer within GIT_SECONDS, its two
    calls together. A file name git gives in bytes that are not UTF-8 is a change like any other, never a crash. GIT_OPTIONAL_LOCKS=0:
    git status never rewrites the workspace's index (read only)."""
    workspace = workspace or READS['workspace']
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    ends = time.monotonic() + GIT_SECONDS
    git = lambda *a: subprocess.run(['git', '-C', workspace, *a], capture_output=True, encoding='utf-8', errors='replace', timeout=max(0, ends - time.monotonic()), env=env)
    try:
        top, said = git('rev-parse', '--show-toplevel'), git('status', '--porcelain=v1', '-z', '--untracked-files=all')
    except (OSError, subprocess.SubprocessError):
        return {'read': False, 'drift': None, 'first': []}
    if top.returncode or said.returncode or os.path.realpath(top.stdout.strip()) != os.path.realpath(workspace):
        return {'read': False, 'drift': None, 'first': []}
    entries, n, first = said.stdout.split('\0'), 0, []
    while entries:
        entry = entries.pop(0)
        if len(entry) < 4:
            continue
        if ('R' in entry[:2] or 'C' in entry[:2]) and entries:
            entries.pop(0)   # a rename names its old path next: the same change, said once
        n += 1
        if len(first) < 3:
            first.append(entry[3:])
    return {'read': True, 'drift': n, 'first': first}


def _fit(head, tail):
    """the why, then the step, within MOST: the why is cut (…) before the step ever is"""
    if len(head) + len(tail) <= MOST:
        return head + tail
    return head[:max(0, MOST - len(tail) - 1)].rstrip() + '…' + tail


def check(reads=None, now=None, wrote=None):
    """ONE LOOK: DOES THE MOIRÉ REPORT RUN? -> {'state': 'green'|'red', 'summary', 'why', 'step', 'changes'}. green whenever the lie
    detector's report reads, is current, has its D3 drift count (or D3 says no baseline), and git answers; red ONLY when one of those is not running. The changes
    (written: D3's drift since the baseline, yellow; unwritten: files not committed yet, red in the original's wording) are information only."""
    reads = reads or READS
    frozen = baseline(reads)
    count, detail, why = drift(reads, now)
    wrote = written(reads['workspace']) if wrote is None else wrote
    broken = ([why] if why else []) + ([] if wrote.get('read') else ['git did not answer for the workspace (not a repository top, or git silent)'])
    loose = int(wrote.get('drift') or 0)
    if not frozen:
        base = "no baseline frozen yet (freezing one is your own act on MOIRÉ's page)"
    elif count is None:
        base = detail or f"the lie detector's {MOIRE_PROBE} not read"
    else:
        base = f'{count} drifted since the baseline (the lie detector, {MOIRE_PROBE})' + (f': {detail}' if detail else '')
    files = (f'{loose} file(s) not committed yet' + (f" ({', '.join(wrote.get('first') or [])}{', ...' if loose > 3 else ''})" if loose else '')
             if wrote.get('read') else 'files not committed: not read (git did not answer)')
    changes = {'baseline': bool(frozen),
               'written': {'tone': 'yellow', 'count': count, 'said': base},
               'unwritten': {'tone': 'red', 'count': loose if wrote.get('read') else None, 'first': wrote.get('first') or [], 'said': files}}
    data = base + ' · ' + files
    if broken:
        step = RERUN if why else GIT_STEP
        return {'state': 'red', 'why': '; '.join(broken), 'step': step, 'changes': changes,
                'summary': _fit(NOT_WORKING + '; '.join(broken) + ' · ' + data, f' · {HAND}{step}')}
    return {'state': 'green', 'why': '', 'step': '', 'changes': changes, 'summary': 'working · ' + data}


def look(store=None, shells=None, now=None):
    """ITS ONE LOOK, PURE (nothing written): does the MOIRÉ report run? -> {'state': GREEN|RED, 'summary', 'why', 'step', 'said'} (said: what a run keeps)"""
    got = check(now=now)
    said = {'summary': ('DONE · ' if got['state'] == 'green' else 'FAILED · ') + got['summary'], 'state': got['state'],
            'why': got['why'], 'step': got['step'], 'changes': got['changes'],
            'looked_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}   # 'looked_at', never 'written': the frame's run_said reads a record with 'written' as the standup's and hides this run's own words
    return {'state': 'GREEN' if got['state'] == 'green' else 'RED', 'summary': said['summary'], 'why': got['why'], 'step': got['step'], 'said': said}


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT; the page writes its live flips itself): the change report looked at once, kept with the run. DONE, exit 0, when the
    report runs, whatever it shows (a change is never red); FAILED, exit 1, only when the report is not running (its fault and the owner's
    3-minute step in the summary), or when this run itself crashes. chain and hire_with: the MARK IV agent's, not this sub agent's. -> what it wrote."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        said = look(store, shells, now)['said']
    except Exception as fault:   # noqa: BLE001  (A CRASH IS RED: never no record and no light)
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        said = {'summary': f'FAILED · {NOT_WORKING}its own run crashed ({line}) · {HAND}{RERUN}', 'state': 'red', 'why': line, 'step': RERUN}
    ok = said['state'] == 'green'
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0 if ok else 1, json.dumps(said), 'DONE' if ok else 'FAILED')
    return said


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
    """ITS OWN CONTENT ON THE ONE CANVAS: words, never markup: its last run's summary, then the changes it saw (written, unwritten)."""
    s = latest(store, job_key)
    if s is None:
        return [{'kind': 'note', 'title': 'Moiré', 'text': 'Not looked yet: its first look reads the change report (live, on every change, or RUN AGENT).'}]
    if 'changes' not in s:
        return [{'kind': 'note', 'title': 'Moiré', 'text': f"Not read: its last run {s.get('summary') or 'FAILED'}."}]
    c = s['changes']
    lines = [('body', s['summary'], '')]
    if s.get('state') == 'red':
        lines.append(('subtitle', f"{s.get('why')} · {HAND}{s.get('step')}", 'not running'))
    lines += [('subtitle', c['written']['said'], 'written'), ('subtitle', c['unwritten']['said'], 'not committed')]
    return [{'kind': 'words', 'title': 'Moiré', 'under': f"Written at {s.get('looked_at') or s.get('written', '')}, by its run", 'lines': lines}]
