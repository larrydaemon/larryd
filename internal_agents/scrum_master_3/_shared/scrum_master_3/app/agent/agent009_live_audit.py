"""AGENT 004 · THE AUDIT, LIVE: a SUB AGENT of the MARK IV agent (agent001), the original Scrum Master's row 017 AUDIT ported
(its rule record: the knowledge store's row-rules-agent017_checks_audit). RED ON THE OWNER'S RULE: any of the three questions failing (the
owner 2026-10-23: the lock half open, The Pin FAILED, an office host down or none listed) is red with its own step; a question that cannot be read is red too, with CRASH_STEP. A crash of the run itself is red with its one step (CRASH_STEP). It never fixes, and it never runs
his hand steps: it names them.
LIVE, ON EVERY CHANGE (the owner 2026-10-27: "not 5 minutes not anything else"): the page's one watcher (frame/frame_live.py) looks the moment
one of its TRIGGERS changes (the lock's sources, The Pin's live_status row, the office hosts answering, global_config.json, this office's
settings), its light kept in the office's live_status, a run written on a flip.
STANDS ALONE (the owner 2026-10-27: "nothing can depend on the orginal. we need to update all"): it reads NOTHING of the original
Scrum Master (no database, no settings or rows file, no manifest, no command of it); only this office's own frame and agents, the
workspace's global_config.json and the system-wide master mark.
1. IS THE AGENT UNLOCKED? The lock the frame's AGENT ACCESS block shows (frame/frame_agent_access.py: lock_state over home_tree of
   sanity_home, read only): the folders' own flags, the sessions' sandbox, the master mark. All three LOCKED: green, locked. MASTER OPEN
   (the database part UNLOCKED: root's mark, his own UNLOCK press) is his state, never a fault: green, what stands open said. Red: the
   master closed while the folders or the sessions stand UNLOCKED (a half lock). A changed locked file is measured by the seal
   (question 2: The Pin's seal probes A5 and B over the sealed core), never counted green here on its own. His step: LOCK AGENT.
2. IS THE PIN AND RESEAL DONE AND IN SYNC? This office's own The Pin, read from its own job's latest run, through the shells and
   the store its run is handed (the shell whose job's data_full_name is 'The Pin'; an agent stands alone: it never imports another
   agent). Its job's RUN STATE DONE and its last run's own seal (A5, B) and pin (A3) both said and passing:
   in sync, its last run's summary quoted (held is not an answer: a pin held and not pinned yet is not in sync). The Pin's switch off:
   red, said as off, with its step (its switch on, then RUN AGENT). FAILED, a seal or pin that is not passing, or one not said: not in sync, red, its own step
   named. No run yet, or no The Pin in this office: a row without its fact, red, with The Pin's own step.
3. ARE ALL OFFICES ONLINE AND NOTHING DOWN? Every host of the workspace's global_config.json offices (each office's rnd port, each
   mini's rnd port, wid's pf port) answers an HTTP GET within 3 s; any HTTP answer, even an error page, is online. His step: the auto
   start, again. No host listed at all (global_config.json offices empty): his step is the file put back from its last commit.
OFF IS NEVER RED: this office's own switch, frame.SETTINGS switches.section_live (its group, LIVE); absent means ON; off makes this
look OFF, green, never red."""
import datetime
import json
import os
import urllib.error
import urllib.request
import zoneinfo

KEY = 'audit'
SLOT = 'LIVE'   # where it lives: the LIVE group
ROW = 17   # its row in the original (agent017_checks_audit): a name only, nothing of the original is read
NAME = 'Audit'
CARD_NAME = 'Scrum Master Audit'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Checks the agent lock is whole or opened by your press, The Pin is in sync, and every office answers; red if any fails'
WHAT = 'Red when the lock is half open, The Pin ended FAILED, an office host does not answer in 3 s, or none is listed'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'live', 'timezone': 'America/New_York'}   # LIVE: on every change of its TRIGGERS, never a clock (frame_red.due_at never misses a live job)
LIVE_SAID = 'LIVE · ON EVERY CHANGE'
ROW_FILE = 'agent017_checks_audit.py'   # the knowledge store files its skills index under this name (a name, never read)

HAND = 'YOUR 3 MIN: '   # a row's own step follows it
HELD = 'held: '   # a held word is not an answer
SWITCH = 'section_' + SLOT.lower()   # this office's own switch: frame.SETTINGS['switches']['section_live']; absent means ON
LOCK_STEP = 'press LOCK AGENT on your page (the master lock closed, a fresh seal over your changed files)'
PIN_STEP = "press RUN AGENT on The Pin in this office's LIVE group"
PIN_OFF_STEP = "turn The Pin's switch on (its card's toggle in this office's LIVE group), then press RUN AGENT on The Pin"
HOST_SECONDS = 3
HOSTS_STEP = 'launchctl kickstart -k gui/$(id -u)/ai.positivefeedback.spine.autostart   (the auto start: every localhost host not answering is started now, python app.py in its web folder)'
EMPTY_STEP = 'git -C ~/virtual_workspace checkout -- global_config.json   (its offices put back from its last commit), then press RUN AGENT on Audit'
CRASH_STEP = "press RUN AGENT on Audit in this office's LIVE group again; if it fails the same way, send that line to a builder as a request"
FOREIGN = ('scrum_master/app', 'scrum_master' + os.sep + 'app')   # a step that names a program of the original is never his step here


def _frame():
    from frame import frame_replica as frame
    return frame


def places():
    """THE PLACES IT READS: the office's sanity home (the AGENT ACCESS tree), the workspace's global_config.json; from the office's
    frame (settings reads) when it loads, else the same paths the frame's settings name."""
    sanity, config = os.path.expanduser('~/virtual_sanity'), os.path.expanduser('~/virtual_workspace/global_config.json')
    try:
        frame = _frame()
        sanity, config = frame.path('sanity_home'), frame.path('global_config')
    except Exception:   # noqa: BLE001  (no frame on the path: the settings' own paths)
        pass
    return {'sanity': sanity, 'global_config': config}


READS = {}   # a check's own places over places() (sanity, global_config, sessions_sandbox, master_mark, settings): never the real ones in a check


def lock_places():
    """WHERE THE LOCK IS READ (frame_agent_access.lock_state): the sanity home's own folder (its flags: the master lock sets them on the top too),
    the sessions' sandbox file, the master mark; and this office's settings (its switch). -> {name: path}"""
    out = {'sanity': places()['sanity'], 'sessions_sandbox': os.path.expanduser('~/.config/claude/sandbox/virtual_sanity.sb'),
           'master_mark': '/var/run/ai.positivefeedback.master_unlocked', 'settings': ''}
    try:
        frame = _frame()
        out.update(sessions_sandbox=frame.path('sessions_sandbox'), master_mark=frame.path('master_mark'), settings=frame.SETTINGS_FILE)
    except Exception:   # noqa: BLE001
        pass
    return {**out, **{k: v for k, v in READS.items() if k in out}}


def triggers(store=None):
    """ITS TRIGGERS, exactly its inputs: the lock's sources (the sanity home's folder itself, the sandbox file, the master mark), the workspace's
    global_config.json (the hosts listed), this office's settings (its switch), The Pin's live_status row, and the office hosts answering"""
    lp = lock_places()
    return [p for p in (lp['sanity'].rstrip('/'), lp['sessions_sandbox'], lp['master_mark'], {**places(), **READS}['global_config'], lp['settings']) if p] + ['status:the_pin', 'ports']


TRIGGERS = triggers()


def one_line(value):
    return ' '.join(str(value).split())


# ---- OFF IS NEVER RED -----------------------------------------------------------------------------------------------
def switch_on(settings=None):
    """THIS OFFICE'S OWN SWITCH: frame.SETTINGS switches.section_live; True when absent or unreadable; only False is off."""
    if settings is None:   # read where it is, each look (a switch turned is a trigger: the settings file): never the copy loaded at the start
        try:
            with open(lock_places()['settings'], encoding='utf-8') as fh:
                settings = json.load(fh)
        except (OSError, ValueError):
            try:
                settings = _frame().SETTINGS
            except Exception:   # noqa: BLE001
                return True
    return ((settings or {}).get('switches') or {}).get(SWITCH, True) is not False


# ---- 1. IS THE AGENT UNLOCKED? --------------------------------------------------------------------------------------
def lock_now(sanity):
    """THE LOCK AGENT ACCESS SHOWS: its own functions, read only -> {'folders', 'sessions', 'database', 'open'}"""
    from frame import frame_agent_access as access
    return access.lock_state(access.home_tree(sanity))


def unlocked(lock):
    """-> (ok, said) over the AGENT ACCESS lock's three parts"""
    parts = ', '.join(f'{k} {lock.get(k)}' for k in ('folders', 'sessions', 'database'))
    unmeasured = 'changed locked files measured by the seal (question 2)'
    if lock.get('database') == 'UNLOCKED':   # HIS OWN PRESS: master open, his state, said, never a fault
        return True, f'unlocked by your press (master open): {parts}; {unmeasured}'
    if lock.get('folders') == 'LOCKED' and lock.get('sessions') == 'LOCKED':
        return True, f'locked ({parts}); {unmeasured}'
    return False, f'the agent is unlocked: MASTER CLOSED, but {parts}'


# ---- 2. IS THE PIN AND RESEAL DONE AND IN SYNC? ---------------------------------------------------------------------
PIN_NAME = 'The Pin'   # the full name of The Pin's job (its data_full_name), how its shell is found among the shells a run is handed


def pin_of(store, shells):
    """THIS OFFICE'S OWN THE PIN, AS ITS LAST RUN LEFT IT: the shell whose job's data_full_name is The Pin's, its job's RUN STATE and
    its latest run's record (store.runs), read only, nothing asked of The Pin itself. -> {'state': DONE|FAILED|'', 'summary', 'step',
    'found'}"""
    sh = next((s for s in shells or () if str((s.get('job') or {}).get('data_full_name') or '') == PIN_NAME), None)
    if sh is None:
        return {'state': '', 'summary': '', 'step': '', 'found': False}
    job = sh.get('job') or {}
    state = str(job.get('data_job_run_state') or job.get('run_state') or '').upper()
    last = {}
    key = sh.get('job_key')
    if key and store is not None and hasattr(store, 'runs'):
        for r in sorted(store.runs(key, 1000), key=lambda r: str(r.get('started_at') or ''), reverse=True)[:1]:
            try:
                got = json.loads(r.get('said') or '{}')
            except (TypeError, ValueError):
                got = {}
            last = got if isinstance(got, dict) else {}
    return {'state': state, 'summary': one_line(last.get('summary') or ''), 'step': str(last.get('step') or ''), 'found': True,
            'seal': one_line(last.get('seal') or ''), 'hammer': one_line(last.get('hammer') or ''), 'held': bool(last.get('held'))}


def own_step(step):
    """his step as this office says it: a step naming a program of the original becomes The Pin's own way here"""
    step = str(step or '').strip()
    return PIN_STEP if not step or any(f in step for f in FOREIGN) else step


def pin_seal(got):
    """-> (ok, said, step) over The Pin's own job: DONE with its last run's seal (A5, B) and pin (A3) both said and passing (held is not
    an answer): in sync; its switch off: red, said as off; FAILED, a seal or pin not passing or not said: red (its last summary quoted); no The Pin or no run yet: red, a row without its fact"""
    got = got or {}
    if not got.get('found'):
        return False, 'the pin and reseal cannot be read: no The Pin in this office', PIN_STEP
    summary = str(got.get('summary') or '')
    why = summary.partition(' · ' + HAND)[0].partition(' · at work on it now: ')[0]   # its why alone: The Pin's own wait names the original's command
    if got.get('state') == 'DONE':
        parts = [(label, str(got.get(k) or '')) for label, k in (('the seal', 'seal'), ('the pin', 'hammer'))]
        missing = [label for label, v in parts if not v]
        if missing:   # a row without its fact is red: The Pin's last run never said its seal or its pin
            return False, f"the pin and reseal cannot be compared: The Pin's last run does not say {' or '.join(missing)}", PIN_STEP
        bad = [f'{label}: {v[:120]}' for label, v in parts if not v.endswith(' pass')]   # held is not an answer: a pin held and 'not pinned yet' never proved
        if bad:
            return False, 'the pin and reseal are not in sync: ' + '; '.join(bad), own_step(got.get('step'))
        return True, 'pin and seal in sync' + (f' (the seal: {parts[0][1][:120]}; the pin: {parts[1][1][:80]})'), ''
    if got.get('state') == 'FAILED':
        return False, 'the pin and reseal are not in sync: ' + (f'The Pin: {why[:200]}' if why else 'The Pin ended FAILED'), own_step(got.get('step'))
    if got.get('light') == 'OFF':   # The Pin's own switch is off: said as off, never as not run; still not in sync
        return False, "the pin and reseal are not measured: The Pin's switch is off", PIN_OFF_STEP
    return False, 'the pin and reseal cannot be read: The Pin has not run yet', PIN_STEP


# ---- 3. ARE ALL OFFICES ONLINE AND NOTHING DOWN? --------------------------------------------------------------------
def hosts(config):
    out = []
    for office, o in (config.get('offices') or {}).items():
        out.append((office, int(o['ports']['rnd'])))
        if isinstance(o.get('mini'), dict) and o['mini'].get('ports'):
            out.append((f'{office}-mini', int(o['mini']['ports']['rnd'])))
    wid = (config.get('offices') or {}).get('wid') or {}
    if (wid.get('ports') or {}).get('pf') and wid['ports']['pf'] != wid['ports'].get('rnd'):
        out.append(('wid pf', int(wid['ports']['pf'])))
    return out


def answers(port, opener=urllib.request.urlopen, seconds=HOST_SECONDS):
    try:
        with opener(f'http://127.0.0.1:{port}/', timeout=seconds):
            return True
    except urllib.error.HTTPError as e:   # an answer in the 400s or 500s is still an answer
        e.close()
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def online(config, opener=urllib.request.urlopen):
    listed = hosts(config)
    down = [(n, p) for n, p in listed if not answers(p, opener)]
    if not listed:
        return False, 'no office is listed (global_config.json offices is empty)', EMPTY_STEP
    if down:
        return False, 'down: ' + ', '.join(f'{n} (port {p})' for n, p in down) + f' · {len(listed) - len(down)} of {len(listed)} hosts online'
    minis = sum(1 for n, _ in listed if n.endswith('-mini'))
    wid_pf = any(n == 'wid pf' for n, _ in listed)
    return True, f'{len(listed)} hosts online ({len(listed) - minis - (1 if wid_pf else 0)} offices, {minis} minis' + (', wid pf' if wid_pf else '') + ')'


# ---- THE THREE QUESTIONS --------------------------------------------------------------------------------------------
def audit(where=None, opener=urllib.request.urlopen, config=None, lock=None, pin=None, settings=None):
    """THE THREE QUESTIONS, answered now -> {'ok', 'off', 'said', 'step', 'answers'}: the bad answers first, then the good ones;
    the step is the first bad answer's. This office's switch off: OFF, ok, nothing asked (off is never red). pin: The Pin's job as
    its last run left it (pin_of; none: not measured yet). lock, settings: a proof's fake inputs (the lock's three parts, the office's settings)."""
    where = {**places(), **READS, **(where or {})}
    if not switch_on(settings):
        return {'ok': True, 'off': True, 'said': f'OFF: your switch is off (switches.{SWITCH} of this office): nothing asked, never red', 'step': '', 'answers': []}
    answered = []   # THE OWNER'S RULE: the lock, The Pin, the hosts; any of the three failing is red, with its own step

    def info(n, ask, step):
        try:
            got = ask()
            ok, said = got[0], got[1]
            step = (got[2] if len(got) > 2 else step) if not ok else ''
        except Exception as fault:   # noqa: BLE001  (a question that can't be read is not a pass: red, with the crash step)
            ok, said, step = False, f'could not be read ({type(fault).__name__}: {one_line(fault)[:120]})', CRASH_STEP
        answered.append({'n': n, 'ok': bool(ok), 'step': step, 'said': said})

    def config_now():
        if config is not None:
            return config
        with open(where['global_config'], encoding='utf-8') as fh:
            return json.load(fh)
    info(1, lambda: unlocked(lock_now(where['sanity']) if lock is None else lock), LOCK_STEP)
    info(2, lambda: pin_seal(pin), '')
    info(3, lambda: online(config_now(), opener), HOSTS_STEP)
    asked = answered
    bad = [a for a in asked if not a['ok']]
    said = ' · '.join(f"{a['n']} {a['said']}" for a in bad + [a for a in asked if a['ok']])   # the bad answers first
    return {'ok': not bad, 'off': False, 'said': one_line(said)[:500], 'step': bad[0]['step'] if bad else '',
            'answers': answered}


def pin_live(store):
    """THE PIN'S LIGHT FROM THE ONE STATUS PLACE (the office's live_status row 'the_pin', frame_live.status), read only; None when there is no row
    (no watcher yet, no store): then its job's last run (pin_of). -> pin_of's shape or None"""
    path = getattr(store, 'db_path', None)
    if not path:
        return None
    try:
        from frame import frame_live
        row = frame_live.status(path, 'the_pin')
    except Exception:   # noqa: BLE001  (no frame, no table yet)
        return None
    if not row:
        return None
    state = {'RED': 'FAILED', 'GREEN': 'DONE'}.get(str(row.get('state') or '').upper(), '')   # OFF or anything else: not measured, never "in sync"
    return {'state': state, 'summary': one_line(row.get('summary') or ''), 'step': str(row.get('step') or ''), 'found': True,
            'light': str(row.get('state') or '').upper()}


def look(store=None, shells=None, now=None, word=None):
    """ITS ONE LOOK, PURE (nothing written): the three questions. -> {'state': GREEN|RED|OFF, 'summary', 'why', 'step', 'said'} (said: what a run keeps).
    word: a check's own audit (the proof's fake inputs)."""
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    if word is None:
        ran = pin_of(store, shells)   # the seal and the pin as The Pin's last run said them: compared, never taken on its light alone
        light = pin_live(store)
        pin = {**ran, **light, 'seal': ran.get('seal', ''), 'hammer': ran.get('hammer', ''), 'held': ran.get('held', False)} if light else ran
        word = audit(pin=pin)
    written = (now or datetime.datetime.now(zone)).strftime('%H:%M')   # kept as 'looked_at', never 'written': the frame's run_said reads a record with 'written' as the standup's and hides this red's own words
    if word['ok']:
        said = {'summary': word['said'], 'state': 'off' if word.get('off') else 'green', 'answers': word['answers'], 'step': '', 'looked_at': written}
        return {'state': 'OFF' if word.get('off') else 'GREEN', 'summary': word['said'], 'why': '', 'step': '', 'said': said}
    said = {'summary': f"FAILED · {word['said']} · {HAND}{word['step']}", 'state': 'red', 'answers': word['answers'], 'step': word['step'], 'looked_at': written}
    return {'state': 'RED', 'summary': said['summary'], 'why': word['said'], 'step': word['step'], 'said': said}


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None, look=None):
    """ONE RUN (RUN AGENT; the page writes its live flips itself): the three questions; green: DONE, exit 0; red: FAILED, exit 1, the bad
    answer first and his one step last (YOUR 3 MIN); a crash: FAILED, exit 1, naming what broke, never no record. look: a check's own
    audit (the proof's fake inputs). -> what it wrote."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    try:
        said = _look(store, shells, now, look() if look else None)['said']
    except Exception as fault:   # noqa: BLE001  (A ROW NEVER DIES SILENTLY: what broke is its red line)
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        step = CRASH_STEP
        said = {'summary': f'FAILED · he could not read it: {line} · {HAND}{step}', 'state': 'red', 'answers': [], 'step': step, 'looked_at': datetime.datetime.now(zone).strftime('%H:%M')}
    ok = said['state'] in ('green', 'off')
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0 if ok else 1, json.dumps(said), 'DONE' if ok else 'FAILED')
    return said


_look = look   # run's own name for it (its argument 'look' is a check's audit)


def latest(store, job_key):
    """What its last run wrote, or None before a first run."""
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except ValueError:
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
    """ITS OWN CONTENT ON THE ONE CANVAS: words, never markup: its last summary, each of the three answers on its line, his step last
    when red; else that nothing is written yet."""
    s = latest(store, job_key)
    if s is None:
        return [{'kind': 'note', 'title': 'The audit', 'text': 'Not looked yet: its first look comes on the page\'s start (live, on every change, or RUN AGENT).'}]
    if not s.get('answers'):
        return [{'kind': 'note', 'title': 'The audit', 'text': s.get('summary') or 'FAILED'}]
    lines = [('subtitle', ('INFO · ' if a.get('info') else 'OK · ' if a['ok'] else 'RED · ') + a['said'], f"q{a['n']}") for a in s['answers']]
    if s.get('step'):
        lines.append(('body', HAND + s['step'], 'step'))
    return [{'kind': 'words', 'title': 'The audit', 'under': f"Looked at {s.get('looked_at') or s.get('written', '')}, by its run · {({'green': 'GREEN', 'off': 'OFF'}).get(s.get('state'), 'RED')}", 'lines': lines}]
