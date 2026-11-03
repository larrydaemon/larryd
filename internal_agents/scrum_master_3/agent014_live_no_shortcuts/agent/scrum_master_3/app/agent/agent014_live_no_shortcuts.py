"""AGENT 009 · NO SHORTCUTS, LIVE (the original's row 022, agent022_checks_no_shortcuts.py, REDESIGNED; the owner 2026-10-27: "one thing
i could think of is the rule set by the system owner gets changed. this should detect that. also any direct edits to the scratch reports
to change a result. i think this can be simplifed to only the most needed checks"): a SUB AGENT of the MARK IV agent (agent001), lower
rank, its job in a LIVE shell, LIVE: the page's one watcher (frame/frame_live.py) looks the moment one of its TRIGGERS changes (LARRYD's
database and its -wal, the reports it guards, its own baseline, the three speed files and this office's speed_pins.json), its light kept in the
office's live_status, a run written on a flip (its baseline written with that run: record). Three checks, nothing more:

(a) THE OWNER'S RULE CHANGED: every job of this office in LARRYD (records of the SYSTEM account, read only, never edited) has its part 1,
    data_job_rule, the system owner's. Its sha256 per job is kept in a baseline outside sanity (~/scratch/reports/<office>/
    no_shortcuts_baseline.json). Red if a job's rule differs from its baseline (changed or emptied) until the owner accepts it. Not a
    change: a new job (its rule recorded), a job removed (dropped), an EMPTY rule filled once (frame_rules' one allowed write of part 1).
(b) A REPORT EDITED BY HAND, only where an honest signal exists (frame_live.py is the one program that writes the LIVE's reports; launchd
    appends the page's output to logs/page.log): look.json is written at the moment it names (its 'at') together with the same line
    appended to look.log, so red if look.json's 'at' is more than SKEW from its file time, or look.json is not look.log's last line;
    look.log's last line likewise against its file time; an appended log (look.log, page.log) whose lines already seen changed (its writer
    only appends), or look.log cut while its first line is not newer than the last one seen (a log deleted and grown again is self heal,
    not red). NO HONEST SIGNAL, so not checked: panel.json (no moment inside, rewritten at any heal from a held copy); system.json and
    offices.json (measurements, not results, rewritten every 5/15 s, and heal rewrites a held sample so their moment can lag honestly);
    the rest of ~/scratch/reports/replica/ (session logs, shots, verify files: no program of record writes them).
    The baseline itself: each run records its sha256 in its LARRYD log; red if the file differs from the last run's record with no
    accept since; a baseline deleted is rebuilt from the last run's record (self heal), never a silent new baseline.
(c) THE SPEED LOCK (the owner 2026-10-27: "ths speed lock is very important"): the three speed check files the owner pinned, each byte
    for byte as pinned in THIS office's own pin file (app/schemas/speed_pins.json: files, each its path and sha256; nothing of the
    original Scrum Master is read: "nothing can depend on the orginal"). Red if the pin file is missing or unreadable or lists no
    file, or a pinned file changed, is gone or has no pin; his step: put it back exactly as pinned, or his own re-pin in that file when
    he moved the bar himself. Never accepted or re-pinned here: the pin is his alone.

THE OWNER'S 3 MINUTES for (a) and (b), after he has looked: accept, which re-baselines every rule and every log as they are now:
    cd ~/virtual_sanity/scrum_master_3/app && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=".:$HOME/virtual_sanity/replica/app" \\
        REPLICA_OFFICE_APP="$PWD" ~/virtual_workspace/.venv/bin/python -m agent.agent014_live_no_shortcuts accept
    (... -m agent.agent014_live_no_shortcuts look : one look, printed, nothing written.)
It reads and reports, never fixes; it writes only its own run (store.ran) and its own baseline."""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import zoneinfo

KEY = 'no_shortcuts'
SLOT = 'LIVE'   # where it lives: a shell of LIVE
ROW = 22   # its row in the original (agent022_checks_no_shortcuts)
NAME = 'No Shortcuts'
CARD_NAME = 'Scrum Master No Shortcuts'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = "No shortcuts: the owner's rules, the reports and the speed checks are never changed by a tool or a hand"
WHAT = "On every change: red when an owner's job rule changed, a report was edited by hand, or a pinned speed check changed"
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'live', 'timezone': 'America/New_York'}   # LIVE: on every change of its TRIGGERS, never a clock (frame_red.due_at never misses a live job)
LIVE_SAID = 'LIVE · ON EVERY CHANGE'
ROW_FILE = 'agent022_checks_no_shortcuts.py'   # the original's program for this row: its skills index is filed under it

OFFICE = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))   # this office's own name (scrum_master_3)
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.expanduser('~/scratch/reports')
BASELINE = os.path.join(REPORTS, OFFICE, 'no_shortcuts_baseline.json')   # its one written file, outside sanity
REPORT_ROOTS = [os.path.join(REPORTS, OFFICE), os.path.join(REPORTS, 'replica')]   # this office's reports and the frame's
SPEED_PINS = os.path.join(APP, 'schemas', 'speed_pins.json')   # the owner's pins, this office's own file: files [{path, sha256, what}], read only
SKEW = 120   # seconds a report's own moment may be from its file time (the writer stamps it right before the write)
PAIR = 5   # seconds look.json may stand without its look.log line: frame_live.py writes look.json, then appends that line in a second write
           # (frame_live.look: write_report('look'), then write_report('look_log')); a look woken by the first write may land between the two
COMMITS = 30   # how far back a speed file's own git is searched for the pinned bytes
ACCEPT = (f'look at it, then accept: cd ~/virtual_sanity/{OFFICE}/app && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=".:$HOME/virtual_sanity/replica/app" '
          f'REPLICA_OFFICE_APP="$PWD" ~/virtual_workspace/.venv/bin/python -m agent.agent014_live_no_shortcuts accept')
CRASH_STEP = (f'it crashed before it could look: run its look by hand, it prints the fault and each red with its step and writes nothing: '
              f'cd ~/virtual_sanity/{OFFICE}/app && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=".:$HOME/virtual_sanity/replica/app" '
              f'REPLICA_OFFICE_APP="$PWD" ~/virtual_workspace/.venv/bin/python -m agent.agent014_live_no_shortcuts look; then press RUN AGENT')
PIN_STEP = f'write your speed pins in {SPEED_PINS} (files: each its path and sha256, from shasum -a 256 <file>)'


def larryd_db(store=None):
    """LARRYD's database file where this office's jobs are read (its store's door: the jobs' segment), or '' without a store"""
    door = getattr(store, 'door', None)
    try:
        db = door.st.db_of('jobs')
        return os.path.join(door.s.dirs[db], f'{db}.db')
    except Exception:   # noqa: BLE001  (no door: a proof's fake store)
        return ''


def triggers(store=None):
    """ITS TRIGGERS, exactly its inputs: LARRYD's database and its -wal (the owner's rules, its own last record), the reports it guards
    (each root's live/look.json, live/look.log, logs/page.log), its own baseline, the speed files pinned and the pin file itself"""
    out = []
    db = larryd_db(store)
    if db:
        out += [db, db + '-wal']
    for root in REPORT_ROOTS:
        out += [os.path.join(root, 'live', 'look.json'), os.path.join(root, 'live', 'look.log'), os.path.join(root, 'logs', 'page.log')]
    out.append(BASELINE)
    try:
        with open(SPEED_PINS, encoding='utf-8') as fh:
            out += [os.path.expanduser(str(f.get('path') or '')) for f in json.load(fh).get('files') or [] if f.get('path')]
    except (OSError, ValueError, AttributeError):
        pass
    out.append(SPEED_PINS)
    return out


TRIGGERS = triggers()
REPIN = f' · or, only if you moved the bar yourself: your own re-pin, its new sha256 (shasum -a 256 <file>) written in {SPEED_PINS} (never done by this program)'


def _sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else str(data).encode('utf-8')).hexdigest()


def _bytes(path):
    try:
        with open(path, 'rb') as fh:
            return fh.read()
    except OSError:
        return None


def _now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _moment(text, near=None):
    """a report's moment (ISO with an offset, or this laptop's local time) as epoch seconds; None when it is not one.
    A local time with no offset in the hour the clocks fall back happened twice (01:00:57 EDT, then 01:00:57 EST): of its two
    readings, the one nearest `near` (the file's own time) is taken; anywhere else both readings are the same moment"""
    try:
        m = datetime.datetime.fromisoformat(str(text).strip())
    except (TypeError, ValueError):
        return None
    if m.tzinfo is not None or near is None:
        return m.timestamp()
    return min((m.replace(fold=0).timestamp(), m.replace(fold=1).timestamp()), key=lambda t: abs(t - near))


# ---- (a) the owner's rule ----------------------------------------------------------------------------------------------------
def office_jobs(store=None):
    """THIS OFFICE'S JOBS IN LARRYD, read only, the office's own way: its store's door, else frame.Door(frame.NAME). -> {key: record}"""
    door = getattr(store, 'door', None)
    if door is None:
        from frame import frame_replica as frame
        door = frame.Door(frame.NAME)
    return door.jobs()


def rule_hashes(jobs):
    """{key: {'name', 'sha'}}: each job's part 1 hashed ('' for an empty rule)"""
    out = {}
    for key, job in (jobs or {}).items():
        rule = (job or {}).get('data_job_rule') or ''
        out[key] = {'name': (job or {}).get('data_full_name') or key, 'sha': _sha(rule) if rule else ''}
    return out


def rules_check(base, jobs):
    """THE OWNER'S RULES against their baseline. -> (reds, notes, new baseline): a changed rule keeps its old sha until accepted"""
    now = rule_hashes(jobs)
    reds, notes, kept = [], [], {}
    for key, cur in now.items():
        was = (base or {}).get(key)
        if was is None:
            kept[key] = cur
            notes.append(f"{cur['name']}: a new job, its rule recorded")
        elif was.get('sha') == cur['sha']:
            kept[key] = cur
        elif not was.get('sha'):   # an empty part 1 filled once: frame_rules' one allowed write
            kept[key] = cur
            notes.append(f"{cur['name']}: its empty rule filled once, recorded")
        else:
            kept[key] = was
            how = 'emptied' if not cur['sha'] else f"sha256 {was['sha'][:12]} -> {cur['sha'][:12]}"
            reds.append({'kind': 'rule', 'what': f"the owner's rule of {cur['name']} ({key}) changed: {how}", 'step': ACCEPT})
    for key, was in (base or {}).items():
        if key not in now:
            notes.append(f"{was.get('name') or key}: its job is gone, dropped from the baseline")
    return reds, notes, kept


# ---- (b) a report edited by hand ---------------------------------------------------------------------------------------------
LOG_LINE = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) · ')


def _appended(roots):
    """the appended logs it watches: each root's live/look.log and logs/page.log that exist"""
    out = []
    for root in roots:
        for rel in ('live/look.log', 'logs/page.log'):
            p = os.path.join(root, rel)
            if os.path.isfile(p):
                out.append(p)
    return out


def reports_check(roots, memory, now=None):
    """THE REPORTS, only where an honest signal exists (module doc, b). -> (reds, notes, new memory of the appended logs)"""
    now = now or datetime.datetime.now().timestamp()
    reds, notes, mem = [], [], {}
    step = 'the report was written by a hand, not its program: delete it (its writer writes it again within 5 minutes, self heal), then ' + ACCEPT
    for root in roots:
        look_p, log_p = os.path.join(root, 'live', 'look.json'), os.path.join(root, 'live', 'look.log')
        look_b, log_b = _bytes(look_p), _bytes(log_p)
        last = (log_b or b'').decode('utf-8', 'replace').rstrip('\n').rsplit('\n', 1)[-1] if log_b else ''
        if look_b is not None:
            try:
                look = json.loads(look_b)
            except ValueError:
                look = None
            mtime = os.path.getmtime(look_p)
            at = _moment((look or {}).get('at'), mtime) if isinstance(look, dict) else None
            if at is None:
                reds.append({'kind': 'report', 'what': f'{look_p}: not as its writer writes it (no moment in it)', 'step': step})
            elif abs(mtime - at) > SKEW:
                reds.append({'kind': 'report', 'what': f"{look_p}: changed at {datetime.datetime.fromtimestamp(mtime):%Y-%m-%d %H:%M:%S}, its writer wrote it at {look['at']}", 'step': step})
            elif last and now - mtime > PAIR and last != f"{look.get('at')} · {look.get('state')} · {look.get('text')}":
                reds.append({'kind': 'report', 'what': f"{look_p}: says {look.get('state')} at {look.get('at')}, its log's last line says otherwise ({last[:80]})", 'step': step})
        if last:
            m = LOG_LINE.match(last)
            mtime = os.path.getmtime(log_p)
            if not m:
                reds.append({'kind': 'report', 'what': f'{log_p}: its last line is not as its writer writes it ({last[:60]})', 'step': step})
            elif abs(mtime - _moment(m.group(1), mtime)) > SKEW:
                reds.append({'kind': 'report', 'what': f"{log_p}: changed at {datetime.datetime.fromtimestamp(mtime):%Y-%m-%d %H:%M:%S}, its last line was written at {m.group(1)}", 'step': step})
    for p in _appended(roots):
        data = _bytes(p) or b''
        was = (memory or {}).get(p)
        first = LOG_LINE.match(data.decode('utf-8', 'replace').split('\n', 1)[0])
        last = [LOG_LINE.match(x) for x in data.decode('utf-8', 'replace').rstrip('\n').split('\n')]
        last = next((x.group(1) for x in reversed(last) if x), '')
        mem[p] = {'size': len(data), 'sha256': _sha(data), 'last_at': last}
        if not was:
            continue
        if len(data) >= was['size']:
            if _sha(data[:was['size']]) != was['sha256']:
                reds.append({'kind': 'report', 'what': f'{p}: lines already written were changed (its writer only appends)', 'step': step})
                mem[p] = was   # remembered as it was: red until put back or accepted
        elif was.get('last_at') and first and first.group(1) <= was['last_at']:
            reds.append({'kind': 'report', 'what': f"{p}: cut from {was['size']} to {len(data)} bytes, its old lines still in it (its writer only appends)", 'step': step})
            mem[p] = was
        else:
            notes.append(f'{p}: started over (deleted and written again: self heal)')
    return reds, notes, mem


# ---- (c) the speed lock --------------------------------------------------------------------------------------------------------
def _git(root, *args, text=True):
    try:
        return subprocess.run(['git', '-C', root, *args], capture_output=True, text=text, timeout=30, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
    except (OSError, subprocess.SubprocessError):
        return None


def restore_step(path, pin):
    """HIS ONE STEP for a changed speed check: from the commit of its own git that holds the pinned bytes, else said plainly"""
    top = _git(os.path.dirname(path), 'rev-parse', '--show-toplevel')
    if top is not None and top.returncode == 0:
        top = top.stdout.strip()
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(top))
        log = _git(top, 'log', '--format=%h', '-n', str(COMMITS), '--', rel)
        for h in (log.stdout.split() if log is not None and log.returncode == 0 else []):
            blob = _git(top, 'show', f'{h}:{rel}', text=False)
            if blob is not None and blob.returncode == 0 and _sha(blob.stdout) == pin:
                return f'put it back exactly as pinned: git -C {top} checkout {h} -- {rel}' + REPIN
    return f'put it back exactly as pinned (sha256 {pin[:12]}): no commit of its git holds those bytes; from your own copy' + REPIN


def speed_check(settings=None):
    """THE SPEED CHECKS, byte for byte as the owner pinned them in this office's pin file. -> (reds, n files)"""
    settings = settings or SPEED_PINS
    try:
        with open(settings, encoding='utf-8') as fh:
            files = json.load(fh).get('files') or []
    except (OSError, ValueError, AttributeError) as e:
        return [{'kind': 'speed', 'what': f'the speed pins cannot be read ({settings}: {type(e).__name__})', 'step': PIN_STEP}], 0
    if not files:
        return [{'kind': 'speed', 'what': f'no speed check is pinned: {os.path.basename(settings)} lists no file', 'step': PIN_STEP}], 0
    reds = []
    for f in files:
        path, pin = os.path.expanduser(str(f.get('path') or '')), str(f.get('sha256') or '')
        data = _bytes(path)
        if not pin:
            reds.append({'kind': 'speed', 'what': f'{os.path.basename(path)}: no pin', 'step': PIN_STEP})
        elif data is None:
            reds.append({'kind': 'speed', 'what': f'{os.path.basename(path)}: gone ({path})', 'step': restore_step(path, pin)})
        elif _sha(data) != pin:
            reds.append({'kind': 'speed', 'what': f'{os.path.basename(path)}: changed (sha256 {_sha(data)[:12]}, pinned {pin[:12]})', 'step': restore_step(path, pin)})
    return reds, len(files)


# ---- the baseline ----------------------------------------------------------------------------------------------------------------
def read_baseline(path=None):
    """-> (baseline dict or None, its sha256 or '')"""
    data = _bytes(path or BASELINE)
    if data is None:
        return None, ''
    try:
        got = json.loads(data)
    except ValueError:
        return {}, _sha(data)
    return (got if isinstance(got, dict) else {}), _sha(data)


def write_baseline(base, path=None):
    """its one written file, replaced whole. -> its sha256"""
    path = path or BASELINE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = json.dumps(base, indent=1, sort_keys=True).encode('utf-8')
    tmp = path + '.writing'
    with open(tmp, 'wb') as fh:
        fh.write(data)
    os.replace(tmp, path)
    return _sha(data)


def last_record(store, job_key):
    """the newest run of its own that recorded the baseline: (its said, its start) or (None, '')"""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True):
        try:
            said = json.loads(r['said'])
        except (TypeError, ValueError):
            continue
        if isinstance(said, dict) and said.get('baseline_sha'):
            return said, str(r['started_at'])
    return None, ''


def judge(jobs, record=None, record_at='', baseline=None, roots=None, settings=None):
    """ONE JUDGEMENT, all three checks. -> (said, new baseline): said has ok, reds, notes; nothing written here"""
    roots = REPORT_ROOTS if roots is None else roots
    base, base_sha = read_baseline(baseline)
    reds, notes = [], []
    if record and base is None:   # deleted: rebuilt from its last run's own record (self heal), never a silent new baseline
        base = {'rules': record.get('rules') or {}, 'appended': record.get('appended') or {}, 'accepted_at': record.get('accepted_at') or ''}
        notes.append('the baseline was gone: rebuilt from its last run, recorded in LARRYD')
    elif record and base_sha != record.get('baseline_sha') and str(base.get('accepted_at') or '') <= record_at:
        reds.append({'kind': 'report', 'what': f'{baseline or BASELINE}: edited by hand (it is not what its last run wrote, and no accept since)', 'step': ACCEPT})
        base = {'rules': record.get('rules') or {}, 'appended': record.get('appended') or {}, 'accepted_at': record.get('accepted_at') or ''}
    first = base is None
    base = base or {}
    r_reds, r_notes, rules = rules_check(base.get('rules') or {}, jobs)
    if first:
        r_notes = [f'its first run: {len(rules)} rule(s) recorded as the baseline']
    p_reds, p_notes, appended = reports_check(roots, base.get('appended') or {})
    s_reds, n_speed = speed_check(settings)
    reds += r_reds + p_reds + s_reds
    notes += r_notes + p_notes
    new = {'rules': rules, 'appended': appended, 'accepted_at': base.get('accepted_at') or ''}
    said = {'ok': not reds, 'reds': reds, 'notes': notes, 'rules_n': len(rules), 'logs_n': len(appended), 'speed_n': n_speed,
            'summary': ('GREEN · ' if not reds else 'RED · ') + (f'{len(rules)} owner rule(s) as set, {len(appended)} log(s) as written, {n_speed} speed check(s) as pinned'
                                                                   if not reds else '; '.join(r['what'] for r in reds)[:400])}
    return said, new


def job_of(shells):
    """its own job's key among the shells it is handed (the shell whose job's data_full_name is its NAME), '' when none"""
    return next((str(sh.get('job_key') or '') for sh in shells or () if str((sh.get('job') or {}).get('data_full_name') or '') == NAME), '')


def look(store=None, shells=None, now=None, job_key=None):
    """ITS ONE LOOK, PURE (nothing written; its baseline only read): the three checks against its baseline and its own last record in LARRYD.
    -> {'state': GREEN|RED, 'summary', 'why', 'step', 'said', '_new'} (said: what a run keeps; _new: the baseline record() writes with a run)"""
    job_key = job_key or job_of(shells)
    record, record_at = last_record(store, job_key) if (store is not None and job_key) else (None, '')
    said, new = judge(office_jobs(store), record, record_at)
    steps = list(dict.fromkeys(r['step'] for r in said['reds']))
    return {'state': 'GREEN' if said['ok'] else 'RED', 'summary': said['summary'], 'why': '' if said['ok'] else '; '.join(r['what'] for r in said['reds'])[:600],
            'step': ' · '.join(steps), 'said': said, '_new': new}


def record(got):
    """WITH A RUN (RUN AGENT, or the page's flip): its baseline written as the look found it, its record for the run. -> the fields the run keeps"""
    new = got['_new']
    return {'baseline_sha': write_baseline(new), 'rules': new['rules'], 'appended': new['appended'], 'accepted_at': new['accepted_at'],
            'looked_at': datetime.datetime.now(zoneinfo.ZoneInfo(SCHEDULE['timezone'])).strftime('%H:%M')}   # kept as 'looked_at', never 'written': the frame's run_said reads a record with 'written' as the standup's and hides this agent's own words


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT by hand; the page writes its live flips itself): one look, its baseline kept, its record in LARRYD; GREEN DONE exit 0,
    RED FAILED exit 1 with every red named and its step; a crash ends FAILED with its fault's one line. -> what it wrote."""
    started = _now()
    try:
        got = look(store, shells, now, job_key)
        said = {**got['said'], **record(got)}
        ok = said['ok']
    except Exception as fault:   # A CRASH IS RED: never no record and no light
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        said, ok = {'summary': f'FAILED · {line}', 'step': CRASH_STEP}, False
    store.ran(job_key, n, started, _now(), 0 if ok else 1, json.dumps(said), 'DONE' if ok else 'FAILED')
    return said


def accept(jobs=None, baseline=None, roots=None):
    """THE OWNER'S ACCEPT (his 3 minutes, after he has looked): every rule and every log re-baselined as it is now. -> the new baseline"""
    roots = REPORT_ROOTS if roots is None else roots
    jobs = office_jobs() if jobs is None else jobs
    _r, _n, appended = reports_check(roots, {})
    new = {'rules': rule_hashes(jobs), 'appended': appended, 'accepted_at': _now()}
    write_baseline(new, baseline)
    return new


def latest(store, job_key):
    """What its last run wrote, or None before a first run."""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except (TypeError, ValueError):
            return None
    return None


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS: words, never markup: its last look, every red with its step folded under it; else nothing yet."""
    s = latest(store, job_key)
    if s is None:
        return [{'kind': 'note', 'title': 'No shortcuts', 'text': 'Not looked yet: its first look records the baseline (live, on every change, or RUN AGENT).'}]
    if 'reds' not in s:
        return [{'kind': 'note', 'title': 'No shortcuts', 'text': f"Not looked: its last run {s.get('summary') or 'FAILED'}. Your 3 min: {s.get('step') or CRASH_STEP}"}]
    lines = [('body', s['summary'], '')]
    steps = list(dict.fromkeys(r['step'] for r in s['reds']))
    for st in steps:
        lines.append(('subtitle', st, 'your 3 min'))
    return [{'kind': 'words', 'title': 'No shortcuts', 'under': f"Looked at {s.get('looked_at') or s.get('written', '')}, by its run", 'lines': lines,
             'detail': [('red', 'Red', [r['what'] for r in s['reds']]), ('notes', 'Noted', s.get('notes') or [])]}]


def until_next(now=None, schedule=None):
    """LIVE: no next time (it looks on every change of its triggers): None"""
    return None


def clock(schedule=None):
    """Its clock in its shell: NEW YORK · LIVE · ON EVERY CHANGE (no hands: no hour it waits for)."""
    schedule = schedule or SCHEDULE
    return {'zone': schedule['location'], 'at': '', 'said': LIVE_SAID, 'when': LIVE_SAID, 'repeat': LIVE_SAID, 'hour_deg': 0, 'minute_deg': 0}


class _CliStore:
    """the look command's read-only view of LARRYD: the office's door, and its runs read as the page's store reads them (frame Shells.runs)"""
    def __init__(self):
        from frame import frame_replica as frame
        self.door = frame.Door(frame.NAME)

    def runs(self, job_key, limit=30):
        return [{'started_at': r.get('identity_log_time') or '', 'said': r.get('data_notes') or ''} for r in self.door.logs(job_key)[:limit]]


def main(argv):
    """accept: the owner's re-baseline · look: one look printed, nothing written"""
    if argv[:1] == ['accept']:
        new = accept()
        print(f"accepted at {new['accepted_at']}: {len(new['rules'])} rule(s), {len(new['appended'])} log(s) re-baselined in {BASELINE}")
        return 0
    if argv[:1] == ['look']:   # the same judgement as a run: against its own last record in LARRYD (a hand edit or a deletion of the baseline shows here too)
        try:
            store = _CliStore()
            job_key = next((k for k, j in store.door.jobs().items() if str((j or {}).get('data_full_name') or '') == NAME), '')
            record, record_at = last_record(store, job_key) if job_key else (None, '')
            said, _new = judge(office_jobs(store), record, record_at)
        except Exception as fault:   # noqa: BLE001  (a crash printed with its fault, never a silent green)
            print(f"FAILED · {(f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]}")
            return 1
        if not job_key:
            print(f'NOTE  no job named {NAME} in LARRYD: judged without its last record')
        print(said['summary'])
        for r in said['reds']:
            print(f"RED   {r['what']}\n      step: {r['step']}")
        for x in said['notes']:
            print(f'NOTE  {x}')
        return 0 if said['ok'] else 1
    print(__doc__.split('THE OWNER\'S 3 MINUTES')[1])
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
