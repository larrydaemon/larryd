"""THE OFFICE LIBRARY: the one program every internal agent of a real workflow stands on (Scrum Master 3, Operations Manager,
CMO, Creative Director; the owner 2026-11-03: "DELETE ALL OLD CRAP it needs a ful conversion not fake lazy copy and paste").

An agent is its own folder: agent.json (its facts, every one data) and agent.py (its own work, short). This file is packed beside
agent.py when the agent is placed in LARRYD RUNTIME INTERNAL (tools/place.sh): one source, never a copy kept in a folder.

THE CONTRACT (LARRYD RUNTIME INTERNAL, server/runtime/app/core_engine/harness.py and sandbox.py):
- stdin: one JSON object. A CALL: {do: "canvas", page: {path, search}, cards, records, who}. A RUN: {do: "run", records, job?}.
- stdout: one JSON object. A CALL: {"view": {"html", "css"}} (view.py's allowlist: no script, style, svg, table, details).
  A RUN: {"delivery": "<its line>", "light": "GREEN" | "RED"}: a RED light ends the RUN red with its own line on its job.
- Its records are what its agent.json declares (agnt, jobs, logs), read through wid's own doors for the member that holds it.
- Its own state lives in the runtime's data, data/<office>/<office>.db (THE OFFICE'S DATABASE: requests and live_status), never
  in ~/virtual_sanity. A process ends when its answer is written: nothing waits, nothing runs on a clock (the owner 2026-11-03:
  "its on demand").
"""
import datetime
import html
import json
import os
import re
import sqlite3
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv and sys.argv[0] else __file__))
HOME = os.path.expanduser('~')
DATA_ROOT = os.environ.get('OFFICE_DATA') or os.path.join(HOME, 'larryd', 'server', 'runtime', 'internal', 'instance', 'data')
ZONE = 'America/New_York'


# ── THE AGENT'S OWN FACTS ────────────────────────────────────────────────────────────────────────────────────────────────

def me():
    """Its agent.json, whole: its name, its office, its group, its number and every fact of its own work."""
    with open(os.path.join(HERE, 'agent.json'), encoding='utf-8') as fh:
        return json.load(fh)


def fact(name, default=None):
    """One fact of its own work (agent.json "facts"), ~ opened to this computer's home."""
    got = (me().get('facts') or {}).get(name, default)
    return os.path.expanduser(got) if isinstance(got, str) and got.startswith('~') else got


# ── THE OFFICE'S DATABASE ───────────────────────────────────────────────────────────────────────────────────────────────

SCHEMA = {
    'requests': '''CREATE TABLE IF NOT EXISTS "requests" ("id" TEXT PRIMARY KEY NOT NULL, "words" TEXT NOT NULL, "hash" TEXT NOT NULL,
        "source" TEXT CHECK ("source" IN ('session', 'sprint', 'order')), "ref" TEXT, "asked_at" TEXT NOT NULL, "position" INTEGER NOT NULL,
        "state" TEXT CHECK ("state" IN ('asked', 'planned', 'building', 'proven', 'reviewed', 'waiting_takein', 'approved', 'taken_in', 'green',
        'shipped', 'stuck_today', 'removed')), "state_at" TEXT NOT NULL, "why" TEXT, "tests" TEXT, "tests_sha" TEXT, "commits" TEXT, "done_at" TEXT,
        environment TEXT CHECK (environment IS NULL OR json_valid(environment)))''',
    'live_status': '''CREATE TABLE IF NOT EXISTS "live_status" ("key" TEXT PRIMARY KEY NOT NULL, "name" TEXT NOT NULL,
        "state" TEXT NOT NULL CHECK ("state" IN ('GREEN', 'RED', 'OFF')), "summary" TEXT, "why" TEXT, "step" TEXT, "changed_at" TEXT NOT NULL,
        "checked_at" TEXT, "trigger" TEXT)''',
}


def office():
    return str(me().get('office') or '')


def data_dir(name=None):
    """The office's own folder in the runtime's data (made when missing)."""
    path = os.path.join(DATA_ROOT, name or office())
    os.makedirs(path, exist_ok=True)
    return path


def db(name=None):
    """The office's own database: its two tables, made when missing, never another."""
    name = name or office()
    con = sqlite3.connect(os.path.join(data_dir(name), f'{name}.db'), timeout=10)
    con.row_factory = sqlite3.Row
    for sql in SCHEMA.values():
        con.execute(sql)
    return con


def now():
    import zoneinfo
    return datetime.datetime.now(zoneinfo.ZoneInfo(ZONE))


def stamp():
    return now().strftime('%Y-%m-%d %H:%M:%S')


def live_set(key, name, state, summary, why='', step='', trigger='run', office_name=None):
    """THE ONE LIVE STATUS PLACE: this check's row, written on its own RUN (its state changed: changed_at moves)."""
    con = db(office_name)
    with con:
        was = con.execute('SELECT state, changed_at FROM live_status WHERE key = ?', (key,)).fetchone()
        changed = stamp() if not was or was['state'] != state else was['changed_at']
        con.execute('INSERT OR REPLACE INTO live_status (key, name, state, summary, why, step, changed_at, checked_at, trigger) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (key, name, state, summary, why, step, changed, stamp(), trigger))
    con.close()


def live_all(office_name=None):
    con = db(office_name)
    rows = [dict(r) for r in con.execute('SELECT * FROM live_status ORDER BY key')]
    con.close()
    return rows


def requests(states=None, office_name=None):
    con = db(office_name)
    sql, args = 'SELECT * FROM requests', ()
    if states:
        sql += f' WHERE state IN ({",".join("?" * len(states))})'
        args = tuple(states)
    rows = [dict(r) for r in con.execute(sql + ' ORDER BY position, asked_at', args)]
    con.close()
    return rows


# ── THE RECORDS IT WAS HANDED ───────────────────────────────────────────────────────────────────────────────────────────

def records(given, species):
    got = (given.get('records') or {}).get(species)
    return [r for r in got if isinstance(r, dict)] if isinstance(got, list) else []


def workflow(given, name=None):
    """THE BLOCKS OF ITS WORKFLOW, from the jobs records alone: every job whose workflow name is its office's workflow
    (data_job_workflow_name), the workflow's own job first, each with its card (agnt) when the records hold it."""
    name = name or str(me().get('workflow') or '')
    cards = {c.get('key'): c for c in records(given, 'agnt')}
    jobs = [j for j in records(given, 'jobs') if (j.get('data_job_workflow_name') or '') == name]
    own = [j for j in jobs if (j.get('data_job_agentic') or '') == 'WORKFLOW']
    blocks = [j for j in jobs if j not in own]
    number = lambda j: str((cards.get(j.get('data_agent_key')) or {}).get('data_agent_number') or '')  # noqa: E731
    blocks.sort(key=lambda j: (number(j) or '~', j.get('data_full_name') or ''))
    return [{**j, 'card': cards.get(j.get('data_agent_key')) or {}} for j in own + blocks]


def light_of(job):
    """A job's light as its record says it: GREEN, RED, or '' (idle)."""
    return (job.get('data_job_light') or '').upper()


def logs_of(given, job_key, most=30):
    """Its job's LARRYD logs (the logs records whose block is that job), newest first."""
    rows = [r for r in records(given, 'logs') if (r.get('identity_log_block') or '') == job_key]
    return sorted(rows, key=lambda r: str(r.get('identity_log_time') or ''), reverse=True)[:most]


# ── THE VIEW KIT: view.py's allowlist only; type, sizes and colours the page's theme (inherit, currentColor, em) ────────

def e(text):
    return html.escape('' if text is None else str(text), quote=True)


CSS = """
:host, .of { font: inherit; color: inherit; }
.of { display: flex; flex-direction: column; gap: .6em; }
.of-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1em; border-bottom: 2px solid; padding-bottom: .3em; }
.of-title { font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
.of-small { font-size: .78em; opacity: .75; }
.of-row { display: flex; justify-content: space-between; gap: 1em; border-bottom: 1px solid color-mix(in srgb, currentColor 18%, transparent); padding: .25em 0; }
.of-row > span:first-child { text-transform: uppercase; font-size: .78em; letter-spacing: .04em; }
.of-row > span:last-child { text-align: right; overflow-wrap: anywhere; }
.of-light { display: inline-block; width: .7em; height: .7em; border-radius: 50%; border: 1px solid; margin-right: .45em; vertical-align: -.05em; }
.of-light--GREEN { background: var(--status-ok, #1fb954); border-color: var(--status-ok, #1fb954); }
.of-light--RED { background: var(--status-error, #e5322d); border-color: var(--status-error, #e5322d); }
.of-light--OFF { background: transparent; }
.of-list { margin: 0; padding-left: 1.2em; }
.of-list li { padding: .12em 0; overflow-wrap: anywhere; }
.of-said { white-space: pre-wrap; overflow-wrap: anywhere; }
.of-red { color: #e5322d; }
.of-big { font-size: 2.2em; font-weight: 800; line-height: 1; letter-spacing: -.01em; }
.of-form { display: flex; flex-wrap: wrap; gap: .5em; align-items: center; }
.of-form input[type=text] { flex: 1 1 18em; font: inherit; padding: .35em .5em; border: 1px solid; background: transparent; color: inherit; }
"""


def light(state):
    state = (state or '').upper()
    state = state if state in ('GREEN', 'RED') else 'OFF'
    return f'<span class="of-light of-light--{state}" role="img" title="{state}"></span>'


def row(label, value):
    return f'<div class="of-row"><span>{e(label)}</span><span>{e(value if value not in (None, "") else "-")}</span></div>'


def head(title, right='', state=None):
    lit = light(state) if state is not None else ''
    return f'<div class="of-head"><span class="of-title">{lit}{e(title)}</span><span class="of-small">{e(right)}</span></div>'


def items(lines):
    lines = [x for x in lines if x not in (None, '')]
    return '<ul class="of-list">' + ''.join(f'<li>{e(x)}</li>' for x in lines) + '</ul>' if lines else '<div class="of-small">none</div>'


def said(text):
    return f'<div class="of-said">{e(text)}</div>'


def view(*parts, css=''):
    return {'html': '<div class="of">' + ''.join(parts) + '</div>', 'css': CSS + css}


def press(path, name, value, words, field=None):
    """A FORM THAT MAY ONLY GET THE PAGE ITSELF (view.py): one button, its name and value; field: a text box named so."""
    box = f'<input type="text" name="{e(field)}" placeholder="{e(words)}">' if field else ''
    return (f'<form class="of-form" method="get" action="{e(path)}"><input type="hidden" name="{e(name)}" value="{e(value)}">{box}'
            f'<button type="submit" class="pfb pfb--small">{e(words)}</button></form>')   # the embedded small button (the owner 2026-11-04: "make sure all the agents inject the embedded buttons too")


def asked(given, name):
    """What the member's press sent in the page's own query (page.search), '' when none."""
    search = (given.get('page') or {}).get('search')
    return str(search.get(name) or '') if isinstance(search, dict) else ''


# ── ITS ANSWER ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def done(line, light_state='GREEN', data=None):
    """A RUN's answer: its one line (its job's TODAY), its light (RED: the RUN ends red with this line on its job), and what it
    found as data on the delivery's second line, read back by data_of on the next CALL."""
    text = ' '.join(str(line).split())[:600] + ('\n' + json.dumps(data, sort_keys=True) if data is not None else '')
    return {'delivery': text, 'light': 'RED' if str(light_state).upper() == 'RED' else 'GREEN'}


def page_workflow(given):
    """the workflow the page shows: the WORKFLOW job whose source is the page's <species>/<page> (its shell when the path names one,
    else the newest), else the workflow of this card's own running job (a RUN)"""
    jobs = records(given, 'jobs')
    m = re.search(r'/app/([^/?#]+)/([^/?#]+)(?:#(\d+))?', str((given.get('page') or {}).get('path') or ''))
    if m:
        def at(j):
            screen, _, shell = str(j.get('identity_job_source') or '').split('@', 1)[-1].partition('#')
            return screen.endswith(f'/{m.group(1)}/{m.group(2)}') and (not m.group(3) or shell == m.group(3)), int(shell) if shell.isdigit() else 0
        wf = [j for j in jobs if j.get('data_job_agentic') == 'WORKFLOW' and j.get('data_job_workflow_name') and at(j)[0]]
        if wf:
            return max(wf, key=lambda j: at(j)[1])['data_job_workflow_name']
    mine = [j for j in jobs if j.get('data_agent_key') == me()['key'] and j.get('data_job_workflow_name')]
    busy = [j for j in mine if str(j.get('data_job_run_state') or '').upper() in ('RUNNING', 'QUEUED')] or mine
    names = {j['data_job_workflow_name'] for j in busy}
    return names.pop() if len(names) == 1 else ''



def own_job(given, key=None):
    """Its own job, as the jobs records hold it ({} when none)."""
    key = key or me()['key']
    return next((j for j in records(given, 'jobs') if j.get('data_agent_key') == key), {})


def data_of(job):
    """What a job's last RUN found (its delivery's second line), {} when none."""
    lines = str((job or {}).get('data_job_delivery') or '').split('\n', 1)
    try:
        got = json.loads(lines[1]) if len(lines) > 1 else {}
    except ValueError:
        return {}
    return got if isinstance(got, dict) else {}


GIVEN = {}


def main(canvas, run=None):
    """Read what the runtime hands, answer once, end. A fault is a red RUN with its own line (never a silent exit)."""
    given = json.loads(sys.stdin.read() or '{}')
    GIVEN.clear()
    GIVEN.update(given)   # what this one answer was handed (the look carries its page's own query on a press)
    real_out, sys.stdout = sys.stdout, sys.stderr   # what its work prints goes to stderr: stdout is its one answer
    do = given.get('do')
    try:
        if do == 'canvas':
            answer = {'view': canvas(given)}
        elif do == 'run' and run is not None:
            answer = run(given)
        else:
            raise SystemExit(f'this agent does not do {do!r}')
    except Exception as fault:   # noqa: BLE001  ITS OWN FAULT: said, red, never hidden
        traceback.print_exc()
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:300]
        answer = {'view': view(head(me().get('name', ''), 'fault', 'RED'), said(line))} if do == 'canvas' else done(f'FAULT · {line}', 'RED')
    sys.stdout = real_out
    sys.stdout.write(json.dumps(answer))
    sys.stdout.flush()
