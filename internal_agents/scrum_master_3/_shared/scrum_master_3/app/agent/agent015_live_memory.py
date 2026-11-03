"""AGENT 010 · MEMORY, LIVE (the original's row 026, agent026_lists_memory.py, ported into this office): a SUB AGENT of the MARK IV agent
(agent001), lower rank, its job in a LIVE shell, LIVE: the page's one watcher (frame/frame_live.py) looks the moment one of its TRIGGERS
changes (the knowledge store and its -wal, Claude Code's settings, the known-answer questions), its light kept in the office's live_status,
a run written on a flip. THE 3 WAY SWITCH WORKS OR NOT, and whether the memory is
getting its live updates.

THE OWNER'S WORDS (2026-10-27): "this should be baked in to live and combined with live maybe. check on it or it can stay on its own if you
feel it is good as is. in my mind its live data updates to the memory". It stays on its own (one LIVE agent, its own light), and it also says
the memory's live updates, as information: the newest entry, how many entries were added and changed today (New York), the newest route of
the 3 way switch and how many routes today. These numbers are NEVER the light: a quiet hour or a quiet day (the owner asleep, no session
writing) adds nothing and is no fault, so no honest "not updating" line exists for a 5-minute look; the night step's staleness is the
original's row 040, not this row.

ITS RED, AS THE ORIGINAL DECIDES (row 026, the owner 2026-10-23: "it works on a 3 way switch or not"), the first bad thing's step last:
  - the knowledge store is not there, or its entries do not read;
  - Claude Code's settings cannot be read, or the prompt hook (knowledge.hook_prompt on UserPromptSubmit) or the write block
    (knowledge.hook_write on PreToolUse) is not wired, or an old Cortex hook is still wired (UserPromptSubmit or SessionStart);
  - no known-answer questions to ask (settings knowledge known_questions);
  - a known question answered wrong: no position (1 the skills index, 2 the knowledge store, 3 the facts fast search), or the expected
    entry not in its first known_within answers; or the door does not answer (a crash, no JSON, past switch_seconds), said at once and
    the asking stopped.
GREEN "the 3 way switch works: N of N questions answered right, the slowest in M ms (the store: K entries) · the hooks are wired".
A crash of its own run ends FAILED too.

SELF-CONTAINED: stdlib only; it never imports the original's shared_* modules nor the knowledge package. It reads knowledge.db READ ONLY
(file:...?mode=ro), Claude Code's settings READ ONLY, and asks through the knowledge door's read-only ask (bin/knowledge ask: no route
written), never add. It reads and reports, never fixes; the questions' words are never said, only their numbers."""
import datetime
import json
import os
import re
import sqlite3
import subprocess
import time
import zoneinfo

KEY = 'memory'
SLOT = 'LIVE'   # where it lives: a shell of LIVE
ROW = 26   # its row in the original (agent026_lists_memory)
NAME = 'Memory'
CARD_NAME = 'Scrum Master Memory'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'Memory: the 3 way switch works or not, and the memory\'s live updates'
WHAT = 'Proves the 3 way switch is wired to every prompt and answers its known questions right, and shows the memory\'s live updates today'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'live', 'timezone': 'America/New_York'}   # LIVE: on every change of its TRIGGERS, never a clock (frame_red.due_at never misses a live job)
LIVE_SAID = 'LIVE · ON EVERY CHANGE'
ROW_FILE = 'agent026_lists_memory.py'   # the original's program for this row: its skills index is filed under it

# THE ORIGINAL'S settings.json knowledge, by the same names (the replica cannot import the original), READ ONLY
CONF = {'home': os.path.expanduser('~/virtual_sanity/knowledge'),
        'db': os.path.expanduser('~/virtual_sanity/knowledge/instance/knowledge.db'),
        'settings': os.path.expanduser('~/.claude/settings.json'),
        'prompt_hook': '-m knowledge.hook_prompt',
        'write_hook': '-m knowledge.hook_write',
        'known_questions': os.path.expanduser('~/virtual_sanity/knowledge/questions/known.json'),
        'known_within': 3,
        'switch_seconds': 20,
        'python': 'python3'}



def triggers(store=None):
    """ITS TRIGGERS, exactly its inputs: the knowledge store and its -wal (every route and entry written), Claude Code's settings (the hooks),
    the known-answer questions file (a check points CONF at scratch)"""
    return [CONF['db'], CONF['db'] + '-wal', CONF['settings'], CONF['known_questions']]


TRIGGERS = triggers()
POSITIONS = {1: 'the skills index', 2: 'the knowledge store', 3: 'the facts fast search'}   # the three ways of the switch; 0 is none
KNOW = '~/virtual_sanity/knowledge/bin/knowledge'   # the knowledge door from any folder, never imported
NOT_WORKING = 'the 3 way switch does not work: '
HAND = 'YOUR 3 MIN: '   # THE 3 MINUTE RULE: the owner's one step, said last, never cut
MOST = 600   # a run's summary is cut to this: the why is cut before the step ever is
SETTINGS = '~/.claude/settings.json'
HOOK = 'env PYTHONPATH={app} PYTHONDONTWRITEBYTECODE=1 {python} {hook}'
HOOK_LINES = {'prompt': '"UserPromptSubmit": [{{"hooks": [{{"type": "command", "command": "{cmd}"}}]}}]',
              'write': '"PreToolUse": [{{"matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash", "hooks": [{{"type": "command", "command": "{cmd}"}}]}}]'}
CORTEX_STEP = f'take the old Cortex hook out of {SETTINGS}: the UserPromptSubmit or SessionStart entry whose command names cortex (seconds)'
QUESTIONS_STEP = 'write the known-answer questions file (settings knowledge known_questions: question, expect), never from the session that builds the switch'
STORE_STEP = (f'put the store back from the newest backup (seconds): cp "$(ls -d ~/scratch/scrum_master/backups/scrum_master_*/knowledge.db | tail -1)" '
              f'~/virtual_sanity/knowledge/instance/knowledge.db && {KNOW} ask "<a known question>"')
DOOR_STEP = f'see the door\'s fault whole by hand (seconds): {KNOW} ask "<question {{n}}>"; a fault in its code is code work'
SWITCH_STEP = (f'ask question {{n}} alone (seconds): {KNOW} ask "<question {{n}}>"; its right answer turns this row green. '
               f'The switch\'s fix itself is the builder\'s (~/virtual_sanity/knowledge/app/knowledge/switch.py _answer), sent as a request')
SETTINGS_STEP = f'make {SETTINGS} read again (seconds): python3 -m json.tool {SETTINGS} names the broken line; mend that line, then press RUN AGENT'
CRASH_STEP = (f'see the crash whole by hand (seconds): cd {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))} && '
              f'PYTHONDONTWRITEBYTECODE=1 python3 -c "from agent import agent015_live_memory as m; print(m.look()[\'summary\'])"; '
              f'a fault in its code is code work, then press RUN AGENT')


def _conf(conf):
    return {**CONF, **(conf or {})}


def db(conf=None):
    """The knowledge store, read only; None when it is not there."""
    f = _conf(conf)['db']
    if not f or not os.path.exists(f):
        return None
    con = sqlite3.connect(f'file:{f}?mode=ro', uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def entries(con):
    """HOW MANY ENTRIES THE KNOWLEDGE STORE HOLDS. -> int, or None when the store is not there or does not read"""
    if con is None:
        return None
    try:
        return int(con.execute('SELECT count(*) FROM entries').fetchone()[0])
    except (sqlite3.Error, TypeError, IndexError):
        return None


def _ny(stamp, zone):
    try:
        t = datetime.datetime.fromisoformat(str(stamp))
    except (TypeError, ValueError):
        return None
    return (t if t.tzinfo else t.replace(tzinfo=zone)).astimezone(zone)


def updates(con, now=None):
    """THE MEMORY'S LIVE UPDATES, information only (never the light): the newest entry written, the newest change, entries added and changed
    today (New York), the switch's newest route and its routes today. -> dict, its numbers None where a table does not read"""
    zone = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
    now = (now or datetime.datetime.now(zone)).astimezone(zone)
    out = {'newest_entry': None, 'newest_change': None, 'added_today': None, 'changed_today': None, 'newest_route': None, 'routes_today': None,
           'today': now.date().isoformat()}
    if con is None:
        return out
    since = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)   # a day's margin for any offset; counted exactly below
    day = now.date()
    try:
        rows = con.execute('SELECT created_at, updated_at FROM entries WHERE updated_at >= ? OR created_at >= ?', (since.date().isoformat(), since.date().isoformat())).fetchall()
        out['newest_entry'] = con.execute('SELECT max(created_at) FROM entries').fetchone()[0]
        out['newest_change'] = con.execute('SELECT max(updated_at) FROM entries').fetchone()[0]
        out['added_today'] = sum(1 for r in rows if _ny(r[0], zone) and _ny(r[0], zone).date() == day)
        out['changed_today'] = sum(1 for r in rows if _ny(r[1], zone) and _ny(r[1], zone).date() == day)
    except sqlite3.Error:
        pass
    try:
        ats = [r[0] for r in con.execute('SELECT at FROM routes WHERE at >= ?', (since.date().isoformat(),))]
        out['newest_route'] = con.execute('SELECT max(at) FROM routes').fetchone()[0]
        out['routes_today'] = sum(1 for a in ats if _ny(a, zone) and _ny(a, zone).date() == day)
    except sqlite3.Error:
        pass
    return out


def updates_said(u):
    def ago(stamp):
        return str(stamp)[:16].replace('T', ' ') if stamp else 'none'
    return (f"live updates today ({u['today']}): {u['added_today'] if u['added_today'] is not None else '?'} entries added, "
            f"{u['changed_today'] if u['changed_today'] is not None else '?'} changed, the newest written {ago(u['newest_entry'])}, "
            f"changed {ago(u['newest_change'])}; {u['routes_today'] if u['routes_today'] is not None else '?'} prompts routed, the newest {ago(u['newest_route'])}")


def hook_step(which, conf=None):
    """THE MISSING HOOK PUT BACK, its own lines. -> one step, seconds"""
    c = _conf(conf)
    cmd = HOOK.format(app=os.path.join(c['home'], 'app'), python=c.get('python') or 'python3', hook=c[f'{which}_hook'])
    return f'put back in {SETTINGS}, under "hooks": ' + HOOK_LINES[which].format(cmd=cmd) + ' (seconds)'


def hooks_wired(conf=None):
    """THE HOOKS: Claude Code's own settings run the 3 way switch on every prompt and the write block on every write (the wiring, not a
    proof of each prompt's route). -> [what is missing], [] when wired"""
    c = _conf(conf)
    try:
        with open(c['settings'], encoding='utf-8') as fh:
            got = json.load(fh).get('hooks') or {}
    except (OSError, ValueError, AttributeError):
        return ["Claude Code's settings cannot be read"]
    cmds = lambda event: ' '.join(h.get('command', '') for g in got.get(event) or [] for h in g.get('hooks') or [])   # noqa: E731
    out = []
    if c['prompt_hook'] not in cmds('UserPromptSubmit'):
        out.append('the prompt hook does not run the 3 way switch')
    if c['write_hook'] not in cmds('PreToolUse'):
        out.append('the write block is not on')
    if 'cortex' in cmds('UserPromptSubmit') + cmds('SessionStart'):
        out.append('the old Cortex hooks are still wired')
    return out


def hooks_fix(unwired, conf=None):
    first = unwired[0] if unwired else ''
    if 'prompt hook' in first:
        return hook_step('prompt', conf)
    if 'write block' in first:
        return hook_step('write', conf)
    if 'Cortex' in first:
        return CORTEX_STEP
    return SETTINGS_STEP


def questions(conf=None):
    """THE KNOWN-ANSWER QUESTIONS, their words never said. -> [(question, {expected keys})], [] when none"""
    try:
        with open(_conf(conf)['known_questions'], encoding='utf-8') as fh:
            known = json.load(fh)
    except (OSError, ValueError):
        return []
    out = []
    for k in known if isinstance(known, list) else []:
        if isinstance(k, dict) and k.get('question') and k.get('expect'):
            out.append((str(k['question']), {k['expect']} if isinstance(k['expect'], str) else set(k['expect'])))
    return out


def ask(question, conf=None, runner=subprocess.run):
    """ONE QUESTION THROUGH THE 3 WAY SWITCH NOW: the knowledge door's read-only ask (bin/knowledge ask, its own process, no route written).
    -> {'position', 'name', 'keys', 'ms'}, or {'fault': why}"""
    c = _conf(conf)
    timeout = int(c.get('switch_seconds') or 20)
    t0 = time.monotonic()
    try:
        done = runner([os.path.join(c['home'], 'bin', 'knowledge'), 'ask', question], capture_output=True, text=True, timeout=timeout,
                      env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        got = json.loads(done.stdout or 'null')
    except subprocess.TimeoutExpired:
        return {'fault': f'did not answer within {timeout} s'}
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return {'fault': f'did not answer: {type(e).__name__}: {e}'[:160]}
    if not isinstance(got, dict):
        return {'fault': 'gave no answer (no JSON on its stdout)'}
    ms = got.get('ms')
    if ms is None:
        ms = round((time.monotonic() - t0) * 1000)
    return {'position': got.get('position'), 'name': str(got.get('name') or ''),
            'keys': [d.get('key') for d in got.get('delivered') or [] if isinstance(d, dict)], 'ms': ms}


def switch(known, conf=None, runner=subprocess.run):
    """THE SWITCH ASKED EVERY KNOWN QUESTION in turn; a door that does not answer stops the asking. -> {'asked', 'right', 'wrong',
    'ms', 'first', 'door'}"""
    within = int(_conf(conf).get('known_within') or 3)
    right, wrong, slowest, first, door = 0, [], 0.0, 0, False
    for n, (q, want) in enumerate(known, 1):
        got = ask(q, conf, runner)
        if got is None or got.get('fault'):
            wrong.append(f"question {n} of {len(known)}: the door {(got or {}).get('fault') or 'gave no answer'}")
            first, door = first or n, not first
            break
        try:
            slowest = max(slowest, float(got.get('ms') or 0))
        except (TypeError, ValueError):
            pass
        if got['position'] not in POSITIONS:
            wrong.append(f'question {n}: no position answered')
            first = first or n
        elif not want & set(got['keys'][:within]):
            wrong.append(f"question {n}: {POSITIONS[got['position']]} answered, the right entry not in its first {within}")
            first = first or n
        else:
            right += 1
    return {'asked': len(known), 'right': right, 'wrong': wrong, 'ms': slowest, 'first': first, 'door': door}


def _fit(head, tail):
    if len(head) + len(tail) <= MOST:
        return head + tail
    return head[:max(0, MOST - len(tail) - 1)].rstrip() + '…' + tail


def check(conf=None, known=None, runner=subprocess.run, now=None):
    """ONE LOOK: THE 3 WAY SWITCH WORKS OR NOT, now. -> {'state', 'summary', 'why', 'step', 'switch', 'entries', 'updates'}"""
    c = _conf(conf)
    whys, step = [], ''
    con = db(c)
    try:
        n = entries(con)
        live = updates(con if n is not None else None, now)
    finally:
        if con is not None:
            con.close()
    if n is None:
        whys.append('the knowledge store is not there' if not os.path.exists(c['db']) else 'the knowledge store does not read')
        step = step or STORE_STEP
    unwired = hooks_wired(c)
    if unwired:
        whys.append('the hooks are not wired: ' + '; '.join(unwired))
        step = step or hooks_fix(unwired, c)
    known = questions(c) if known is None else known
    got = None
    if not known:
        whys.append('no known-answer questions to ask it')
        step = step or QUESTIONS_STEP
    else:
        got = switch(known, c, runner)
        if got['wrong']:
            whys.append(f"{len(got['wrong'])} of {got['asked']} questions not answered right ({got['wrong'][0]}"
                        + (f", and {len(got['wrong']) - 1} more" if len(got['wrong']) > 1 else '') + ')')
            step = step or (DOOR_STEP if got['door'] else SWITCH_STEP).format(n=got['first'])
    info = updates_said(live)
    if whys:
        return {'state': 'red', 'why': ' · '.join(whys), 'step': step, 'switch': got, 'entries': n, 'updates': live,
                'summary': _fit(NOT_WORKING + ' · '.join(whys) + ' · ' + info, f' · {HAND}{step}')}
    return {'state': 'green', 'why': '', 'step': '', 'switch': got, 'entries': n, 'updates': live,
            'summary': (f"the 3 way switch works: {got['right']} of {got['asked']} questions answered right, the slowest in {got['ms']:.0f} ms "
                        f"(the store: {n} entries) · the hooks are wired · {info}")}


def look(store=None, shells=None, now=None, conf=None, known=None, runner=subprocess.run):
    """ITS ONE LOOK, PURE (nothing written: the store read only, the door's read-only ask). -> {'state': GREEN|RED, 'summary', 'why', 'step', 'said'}
    (said: what a run keeps); conf, known and runner: a proof's own."""
    got = check(conf, known, runner, now)
    said = {'summary': ('DONE · ' if got['state'] == 'green' else 'FAILED · ') + got['summary'], 'state': got['state'],
            'why': got['why'], 'step': got['step'], 'entries': got['entries'], 'updates': got['updates'],
            'switch': {k: got['switch'][k] for k in ('asked', 'right', 'wrong', 'ms')} if got['switch'] else None,
            'written': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
    return {'state': 'GREEN' if got['state'] == 'green' else 'RED', 'summary': said['summary'], 'why': got['why'], 'step': got['step'], 'said': said}


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None, conf=None, known=None, runner=subprocess.run):
    """ONE RUN (RUN AGENT; the page writes its live flips itself): the switch looked at once, kept with the run. DONE, exit 0, when it works;
    FAILED, exit 1, on the original's reds (the why first, the owner's step last) or when this run itself crashes. chain and hire_with:
    the MARK IV agent's, not this sub agent's; conf, known and runner: a proof's own. -> what it wrote."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        said = look(store, shells, now, conf, known, runner)['said']
    except Exception as fault:   # noqa: BLE001  (A CRASH IS RED: never no record and no light)
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        said = {'summary': f'FAILED · {NOT_WORKING}its own run crashed ({line}) · {HAND}{CRASH_STEP}', 'state': 'red', 'why': line, 'step': CRASH_STEP}
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
    """ITS OWN CONTENT ON THE ONE CANVAS: words, never markup: its last run's summary, the switch's count, the memory's live updates."""
    s = latest(store, job_key)
    if s is None:
        return [{'kind': 'note', 'title': 'Memory', 'text': 'Not looked yet: its first look asks the 3 way switch (live, on every change, or RUN AGENT).'}]
    if 'updates' not in s:
        return [{'kind': 'note', 'title': 'Memory', 'text': f"Not read: its last run {s.get('summary') or 'FAILED'}."}]
    lines = [('body', s['summary'], '')]
    if s.get('state') == 'red':
        lines.append(('subtitle', f"{s.get('why')} · {HAND}{s.get('step')}", 'not working'))
    sw = s.get('switch')
    if sw:
        lines.append(('subtitle', f"{sw['right']} of {sw['asked']} known questions answered right, the slowest in {float(sw['ms'] or 0):.0f} ms", 'the switch'))
    lines.append(('subtitle', updates_said(s['updates']), 'live updates'))
    return [{'kind': 'words', 'title': 'Memory', 'under': f"Written at {s.get('written', '')}, by its run", 'lines': lines}]
