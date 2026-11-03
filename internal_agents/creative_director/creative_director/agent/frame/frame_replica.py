"""FRAME · THE FRAME ITSELF (the owner 2026-10-27: "replica / frame/ / frame_ replica"; "the idea is the frame is not an agent / it holds agents / it does nothing on its own without an agent attached"): the root shape and its
slots, the shells store, the LARRYD records, the places. Every other frame file, every agent and the page import it; it imports no frame
file, no agent and nothing of the page. Three parts, each as it was: ITS PLACES (its settings, its routes, its schema, every path it
reads), THE LARRYD RECORDS (its door to the platform's one pipeline: cards, model, jobs and logs under SYSTEM) and THE SHELLS STORE (the
root shape's slots, each shell connected to its records by their keys); then the pieces every frame file draws with: the light, a
block of the frame, the clock's words. It runs nothing of its own."""
import datetime
import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import zoneinfo

# ---- its places: its one settings file, its routes, its schema, every path it reads ----------------------------------
# ITS PLACES: its one settings file (schemas/settings.json), loaded once, and every path it reads, named there (reads). ITS OWN
# NAME (the owner 2026-10-27: "it would have its own css not called replica"): the office's folder names its sheet, its page, its
# database and that database's schema ({office} in settings.json and routes.json: replica/ the template, scrum_master_2/, cmo/).
FRAME_APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # THE FRAME'S ONE HOME: the replica's own app; an office holds no copy of it (the owner 2026-10-27: "no fucking frame in the fucking scrum master")
FRAME = os.path.join(FRAME_APP, 'frame')   # the frame's own folder
APP = FRAME_APP   # LARRYD RUNTIME INTERNAL (2026-11-03): the office's app is this agent's own folder (agent/, web/, schemas/ copied into it)   # THE OFFICE IT SERVES: its app (agent/, web/, static/, schemas/), handed once by the office's own launcher (agent/run); the replica's own when none is handed (the template's page, its checks)
ROOT = OFFICE = os.path.dirname(APP)   # the office: app/ and instance/
NAME = 'creative_director'   # the office's own name, kept: its jobs, its store and its skills are filed under it (the folder LARRYD places it in has another name)   # THIS OFFICE'S OWN NAME: its files carry it (static/css/<name>.css, web/templates/<name>.html, instance/<name>.db and <name>.json)
SCHEMAS = os.path.join(APP, 'schemas')
SETTINGS_FILE = os.path.join(SCHEMAS, 'settings.json')
ROUTES_FILE = os.path.join(SCHEMAS, 'routes.json')
INSTANCE = os.path.abspath(os.path.expanduser(os.environ.get('REPLICA_INSTANCE') or '~/larryd/server/runtime/internal/instance/data/creative_director'))   # its state in LARRYD RUNTIME INTERNAL's own data, never ~/virtual_sanity
with open(SETTINGS_FILE, encoding='utf-8') as _fh:
    _text = _fh.read()


def agent():
    """THIS OFFICE'S OWN AGENT (settings agent: its agent.json in its own app/schemas, as the original keeps its card in its own
    schemas), read once a draw; None for the frame, which has none. Its '{agent}' is its office, its '{app}' its app."""
    import json as _json
    at = SETTINGS.get('agent')
    if not at:
        return None
    with open(os.path.expanduser(at), encoding='utf-8') as fh:
        got = _json.load(fh)
    got.pop('about', None)
    if got.get('art'):
        got['art'] = got['art'].replace('{agent}', OFFICE).replace('{app}', APP)
    return got


for _word, _place in (('{app}', APP), ('{schemas}', SCHEMAS), ('{instance}', INSTANCE)):
    _text = _text.replace('"' + _word, '"' + _place)   # a value that begins with one of its places, filled in
_text = _text.replace('{office}', NAME)   # its own name, wherever a value carries it (the store's file: {instance}/{office}.db)
SETTINGS = json.loads(_text)
PATHS = {k: os.path.expanduser(v) for k, v in SETTINGS['reads'].items() if not k.endswith('about')}
with open(ROUTES_FILE, encoding='utf-8') as _fh:
    ROUTES = {k: v.replace('{office}', NAME) for k, v in json.load(_fh)['routes'].items()}


def path(name, *parts):
    """a place it reads, by its name in settings.json reads (and a file below it)"""
    return os.path.join(PATHS[name], *parts)


def read_json(name):
    """a JSON file it reads, by its name in settings.json reads"""
    with open(path(name), encoding='utf-8') as fh:
        return json.load(fh)


def schema():
    """THE OFFICE'S OWN DATABASE SCHEMA, beside the database in instance/ as the original keeps its own (instance/<name>.json;
    the owner 2026-10-27: "missing the schema"): its tables, each with its columns, their types and what is required."""
    with open(os.path.join(INSTANCE, NAME + '.json'), encoding='utf-8') as fh:
        return json.load(fh)


# ---- the LARRYD records: its door to the platform's one pipeline (cards, model, jobs, logs under SYSTEM) -------------
# THE REPLICA'S RECORDS IN LARRYD (the owner 2026-10-27: "system account"; "add all the data in larryd"; "we are not duplicating
# data tables when they are already setup and running"; "make sure the scrum master itself has a key for agent, model, logs, jobs and
# registered"): its agent cards (agents: the MARK IV agent itself in its own class, and one per sub agent in the species' own class,
# lower rank), its model (models), its jobs (jobs) and every run's log (logs) are records of LARRYD's four modules under the SYSTEM account,
# minted by the one generator through the platform's one pipeline (core_engine verbs), never by this program. One DOOR per
# office: it reads the records where they are (the store's own connections, through the lock's secure_query) and writes them
# through the verbs; a proof hands it a scratch store (Store.copy), the office its live one. SYSTEM and its owner are read from
# FROST's identity database, never typed. `run register` writes the office's cards and model once (the same identity is the
# same record).
LOG_LINE = re.compile(r'^(?P<start>.+?) → (?P<end>.+?) · exit (?P<exit>-?\d+)$')   # a run's log line, as the original's row face writes it
SYSTEM_OWNER = 'system_owner'   # FROST's word for the member who owns SYSTEM (users_members Member_Type)
MODEL = 'LARRY LLM'   # the model's name; its identity carries the platform's one version after it


def platform():
    """THE PLATFORM'S ONE PIPELINE (settings reads wid_app), imported from its app with this office's box and side set for it the way
    the platform's own offices carry theirs (global_config environment_variable; settings page environment). -> (store, verbs)"""
    app = path('wid_app')
    if app not in sys.path:
        sys.path.insert(0, app)
    conf = read_json('global_config')
    os.environ.setdefault(conf['environment_variable'], SETTINGS['root_shape']['page']['environment'])
    from core_engine import store, verbs
    return store, verbs


def system():
    """SYSTEM's account and its owner, as FROST holds them (settings reads frost_db, read where it is), and SYSTEM's scope
    (global_config roles). -> (account, member, scope)"""
    con = sqlite3.connect(f"file:{path('frost_db')}?immutable=1", uri=True)
    try:
        row = con.execute('SELECT Parent_Norm_Key, Norm_Key FROM users_members WHERE Member_Type = ?', (SYSTEM_OWNER,)).fetchone()
    finally:
        con.close()
    if not row:
        raise LookupError('FROST names no system owner')
    return row[0], row[1], read_json('global_config')['roles']['system']['scope']


def card_source(name):
    """an agent card's identity (identity_agent_source): the replica's, by its name"""
    return f'REPLICA {name.upper()} AGENT'


def model_name(version):
    """the model's identity (identity_model_name): LARRY LLM and the platform's one version (engine.json)"""
    return f'{MODEL} {version}'


WRITING = threading.RLock()   # ONE WRITER AT A TIME in this process (the page's own placement, an agent's run in its thread, a RUN taken): the pipeline is one, never two threads inside it at once ("database is locked")


class _Writing:
    """ONE WRITE THROUGH THE DOOR: the door's one writing lock (WRITING), and the page's remembered reads forgotten before and after it."""
    def __enter__(self):
        WRITING.acquire()
        _forget_reads()
        return self

    def __exit__(self, *exc):
        try:
            _forget_reads()
        finally:
            WRITING.release()
        return False


def _page_reads():
    """THE PAGE'S READS, ONCE (the owner's speed rule: a board of 35 blocks asked the same records hundreds of times, each its own
    connection): within ONE GET request of the office's page, each exact read (module, query, values) is asked once and handed again as a
    copy; any write through this door (with WRITING) forgets them at once; nothing outlives the request. None outside a GET request."""
    try:
        from flask import g, has_request_context, request
    except ImportError:
        return None
    if not has_request_context() or request.method != 'GET':
        return None
    return g.setdefault('_frame_reads', {})


def _forget_reads():
    """A write through the door: the page's remembered reads forgotten, so the next read is the record as it now stands."""
    try:
        from flask import g, has_request_context
    except ImportError:
        return
    if has_request_context():
        g.pop('_frame_reads', None)


class Door:
    """One office's door to LARRYD under SYSTEM."""

    def __init__(self, office, store=None):
        self.office = office
        self.st, self.verbs = platform()
        self.s = store or self.st.Store.for_offices()
        self.account, self.member, self.scope = system()
        self.screen = SETTINGS['page'].get('screen') or SETTINGS['root_shape']['page']['screen']   # AN OFFICE'S OWN SCREEN when its settings name one (the owner 2026-11-02: "Operations Manager agent belongs on invoice maps operations page"), else the shape's
        engine = read_json('engine')
        self.stages = {x['letter']: x['stage'] for x in engine['keys']['stages']}
        self.version = engine['larry_llm_version']
        from core_engine import larryd_runtime, offices, shells   # THE PLATFORM'S OWN WORDS, read where they are (platform() put its app on the path): a card's names (CARD), where an internal agent runs (INTERNAL, INTERNAL_RUNTIME), every office's api door, a job's schedule and its defaults (the species')
        self.runtime, self.api = larryd_runtime, offices.API
        self.schedule = tuple((n, shells.SCHEDULE_DEFAULTS.get(n, '')) for n in shells.SCHEDULE)

    # ---- where the records are
    def source(self, shell_id):
        """A JOB'S IDENTITY, the platform's own (<member>@<screen>#<shell>): the shell named by its office and its id (ids are never reused)."""
        return f'{self.member}@{self.screen}#{self.office}-{shell_id}'

    def table(self, seg):
        return self.verbs._record_table(self.account, self.scope, seg)

    def key(self, seg, rec):
        """a record's master key (M<family>_norm_key), '' for none"""
        return (rec or {}).get(self.verbs._mcol(seg)) or ''

    def stage(self, key):
        return self.stages.get((key or '')[:1], '')

    def rows(self, seg, tail='', params=()):
        """LARRYD's master records of one module under SYSTEM, every column; none before the first is written (the pipeline makes the table then)."""
        reads, asked = _page_reads(), (self.account, seg, tail, tuple(params))
        if reads is not None and asked in reads:
            return [dict(r) for r in reads[asked]]
        con = self.s.connect(self.st.db_of(seg))
        try:
            t = self.table(seg)
            if not con.execute(*self.st.secure_query('SELECT name FROM sqlite_master WHERE type = ? AND name = ?', params=('table', t))).fetchone():
                got = []
            else:
                got = [dict(r) for r in con.execute(*self.st.secure_query(f'SELECT * FROM "{t}" {tail}', params=params))]
        finally:
            con.close()
        if reads is not None:
            reads[asked] = [dict(r) for r in got]
        return got

    def one(self, seg, field, value):
        got = self.rows(seg, f'WHERE "{field}" = ? ORDER BY id DESC LIMIT 1', (value,))
        return got[0] if got else None

    # ---- the four modules
    def card(self, name):
        return self.one('agnt', 'identity_agent_source', card_source(name))

    def card_key(self, name):
        return self.key('agnt', self.card(name))

    def cards(self):
        """every agent under SYSTEM, (key, name): the agents a shell may hold"""
        return [(self.key('agnt', r), r.get('data_full_name') or '') for r in self.rows('agnt', 'ORDER BY id')]

    def model(self):
        return self.one('mdls', 'identity_model_name', model_name(self.version))

    def model_of(self, key):
        """THE MODELS RECORD A JOB NAMES (data_model_key), as the shell's manifest says it: its key, its name (the record's nickname) and its
        version (the platform's one, when the record is that version's LARRY LLM); no key: nothing (the template's rest)."""
        if not key:
            return {}
        rec = self.one('mdls', self.verbs._mcol('mdls'), key) or {}
        return {'key': key, 'name': rec.get('data_nickname') or rec.get('identity_model_name') or '', 'version': self.version if rec.get('identity_model_name') == model_name(self.version) else ''}

    def workflow_source(self):
        """ITS MANAGER'S WORKFLOW ON ITS OWN SCREEN (the owner 2026-11-02: "wid's workflow job" stays as each agent's ONE job; "DO NOT DUPLICATE
        ANYTHING IN AGENTS, LOGS, JOBS"): a block job there names <member>@<screen>#<the workflow's job key>#<its wid shell>."""
        return f'{self.member}@{self.screen}#MJOB_'

    def jobs(self):
        """this office's jobs by key: its own (the identity names the member, the screen and this office's shell) and its manager's workflow
        blocks on its screen, held by reference (one job per agent, never a copy)"""
        own = self.rows('jobs', 'WHERE identity_job_source LIKE ? ORDER BY id', (f'{self.member}@{self.screen}#%',))   # LARRYD RUNTIME INTERNAL (2026-11-03): its agents' jobs are held in wid's own shells on its screen now (<member>@<screen>#<wid shell>); the office's shells table names which by key
        return {self.key('jobs', r): r for r in own}

    def job(self, shell_id):
        return self.one('jobs', 'identity_job_source', self.source(shell_id))

    def add_job(self, shell_id, values=None):
        with _Writing():
            return self._add_job(shell_id, values)

    def _add_job(self, shell_id, values=None):
        """ADD JOB: a JOBS record minted into the shell (the same identity is the same record: a shell that let go of its key takes it back). -> key"""
        fields = {'identity_job_source': self.source(shell_id), 'data_job_block_type': 'PROCESS', 'data_job_scope': 'member', 'data_model_key': self.key('mdls', self.model()), **(values or {})}   # its schedule's defaults come with its birth (the species', the pipeline's), as every new record's
        return self.verbs.add(self.s, self.account, self.scope, 'jobs', fields, self.member)['key']

    def edit(self, key, changes, run=False):
        with _Writing():
            return self._edit(key, changes, run)

    def _edit(self, key, changes, run=False):
        """a job's fields written (run=True: its RUN's own opening and ending, as the Run button and the result write them)"""
        self.verbs.edit(self.s, self.account, self.scope, 'jobs', key, changes, self.member, run=run)

    def delete_job(self, key):
        with _Writing():
            self._delete_job(key)

    def _delete_job(self, key):
        self.verbs.delete(self.s, self.account, self.scope, 'jobs', key, self.member)

    def logs(self, job_key, limit=None):
        """a job's LOGS records, newest first: one per run; limit: only that many read (the stream asks every shell's newest on each open: never all its rows to keep one)"""
        if _page_reads() is not None:   # ON A PAGE: the LOGS read once, newest first, each job's own taken from it (the same rows, the same order: a board of 35 asked it 200 times)
            mine = [r for r in self.rows('logs', 'ORDER BY identity_log_time DESC, id DESC') if r.get('identity_log_workflow') == job_key]
            return mine[:limit] if limit else mine
        return self.rows('logs', 'WHERE identity_log_workflow = ? ORDER BY identity_log_time DESC, id DESC' + (' LIMIT ?' if limit else ''), (job_key, limit) if limit else (job_key,))

    def add_log(self, job, n, started_at, ended_at, exit_code, said):
        with _Writing():
            return self._add_log(job, n, started_at, ended_at, exit_code, said)

    def _add_log(self, job, n, started_at, ended_at, exit_code, said):
        """A RUN'S LOG: a LOGS record (its workflow the job, its block RUN n, its time the start, its source the agent that ran it,
        its message the run's line, its notes what the run wrote). -> the line"""
        agent = self.one('agnt', self.verbs._mcol('agnt'), job.get('data_agent_key') or '') if job.get('data_agent_key') else None
        line = f'{started_at} → {ended_at} · exit {exit_code}'
        self.verbs.add(self.s, self.account, self.scope, 'logs', {'identity_log_workflow': self.key('jobs', job), 'identity_log_block': f'RUN {n}', 'identity_log_time': started_at,
                                                                  'identity_log_source': (agent or {}).get('identity_agent_source') or card_source(self.office),
                                                                  'data_full_name': f"{job.get('data_full_name') or 'Job'} RUN {n}", 'data_log_message': line, 'data_notes': said}, self.member)
        return line

    def register(self, agent, items=()):
        with _Writing():
            return self._register(agent, items)

    def _register(self, agent, items=()):
        """THE OFFICE REGISTERED (run register): LARRY LLM's model, the MARK IV agent's own card (its class the office's: MARK IV) and one card
        per sub agent (items: the agent programs after the first; no class written: the species' own default, MARK I AGENT (NORMAL), a lower
        rank; the owner 2026-10-27: "all agents below it are not mark IV they are sub agents and lower rank"), each written once, with the
        words settings name (larryd): its authorization and status among them, FROST's word on a card, written as FROST's own doors write
        them (frost=True; the owner 2026-10-27: "fix all of them at once"); never an account. -> {name: key}"""
        out = {}
        name = model_name(self.version)
        if not self.model():
            self.verbs.add(self.s, self.account, self.scope, 'mdls', {'identity_model_name': name, 'data_full_name': f'{name} Model', 'data_nickname': MODEL}, self.member)   # its nickname the model's name, its identity the name and the version
        out[name] = self.key('mdls', self.model())
        if not agent:
            return out
        words = SETTINGS['larryd']
        wanted = [(agent['name'], agent['name'], agent['card_words']['pitch'], agent['class'])] + [(getattr(it, 'CARD_NAME', '') or f"{agent['name']} {it.NAME}", it.NAME, getattr(it, 'PITCH', it.NAME), '') for it in items]   # A MOVED AGENT KEEPS ITS CARD (CARD_NAME): never a second one
        for name, full, pitch, klass in wanted:
            if not self.card(name):
                numbers = [int(r['data_agent_number']) for r in self.rows('agnt') if str(r.get('data_agent_number') or '').isdigit()]
                self.verbs.add(self.s, self.account, self.scope, 'agnt', {'identity_agent_source': card_source(name), 'data_full_name': full, 'data_agent_number': str(max(numbers + [0]) + 1),
                                                                          'data_agent_class': klass, 'data_agent_pitch': pitch, 'data_agent_price': agent['price'],
                                                                          'data_agent_developer': words['developer'], 'data_agent_screen': self.screen, 'data_agent_type': words['type'],
                                                                          'data_agent_residency': words['residency'], 'data_agent_environment': words['environment'],
                                                                          'data_agent_authorization': words['authorization'], 'data_agent_status': words['status']}, self.member, frost=True)
            out[name] = self.card_key(name)
        return out


# ---- the shells store: the root shape's slots, each shell connected to its records by their keys ---------------------
# THE REPLICA SHELL'S OWN HANDS (the owner 2026-10-26: "it needs to look and function identical"): the AI atom shell's
# actions, done the same way (wid core_engine/shells.py). THE SHELLS (their slots, their order, their switch, the job each holds)
# are the one table of this office's own database (instance/<office>.db, declared beside it in instance/<office>.json), as FROST
# holds the platform's; EVERY JOB, ITS RUNS AND THEIR LOGS, every agent's skills, rule and lie detector live in LARRYD under
# SYSTEM (frame_replica.Door), written through the platform's one pipeline and read where they are: nothing here mints a key and
# nothing is kept twice (the owner 2026-10-27: "add all the data in larryd"; "rule are rules in the db not python code"; "all logs
# should be stored in larryd logs"). A RUN's verdict is said once, by the page itself, kept in nobody's browser. A SHELL IS NOT A
# JOB: + / − add or remove a shell; ADD JOB mints a job into the shell, REMOVE JOB deletes it; ▲ ▼ move a shell; the switch is the
# shell's on/off; wires (1)-(3) join jobs on the same board, never a loop; (4) is the NEUTRAL passthrough, never set: a shell
# switched OFF passes straight through it; RUN is a request only.
WIRES = ('wire_1', 'wire_2', 'wire_3')
OPEN_RUN = ('QUEUED', 'DROPPED', 'RUNNING')
FIELD = {'full_name': 'data_full_name', 'agent_key': 'data_agent_key', 'model_key': 'data_model_key'}   # the shell's names for a job's fields; the rest are data_job_<name>
MOVED = ('jobs', 'runs', 'said', 'rules', 'takes', 'skills')   # the tables a store kept before LARRYD held its jobs, runs and logs and every job its own sanity (moved 2026-10-27): gone from a store that still has them

_GROW = threading.Lock()   # the store's table grown by one thread at a time


def create_sql(table):
    """ONE TABLE AS ITS SCHEMA DECLARES IT (instance/<office>.json, the original's way): real columns, real types, NOT NULL where
    required, the primary key, each check's words. -> CREATE TABLE IF NOT EXISTS ..."""
    parts = []
    for c in table['columns']:
        kind = table['types'][c]
        line = f'"{c}" {kind}'
        if c in table.get('primary', []) and len(table['primary']) == 1:
            line += ' PRIMARY KEY' + (' AUTOINCREMENT' if kind == 'INTEGER' else '')
        if c in table.get('required', []):
            line += ' NOT NULL'
        if c in table.get('check', {}):
            line += ' CHECK ("' + c + '" IN (' + ', '.join("'" + w + "'" for w in table['check'][c]) + '))'
        parts.append(line)
    if len(table.get('primary', [])) > 1:
        parts.append('PRIMARY KEY (' + ', '.join(f'"{c}"' for c in table['primary']) + ')')
    return f'CREATE TABLE IF NOT EXISTS "{table["name"]}" (' + ', '.join(parts) + ')'


class Shells:
    def __init__(self, db_path, door, slots=('DAY',), single=(), tables=None):
        self.db_path = db_path
        self.door = door   # THE OFFICE'S DOOR TO LARRYD: every job, run and log of this board
        self.schedule = door.schedule   # THE JOB'S SCHEDULE, the platform's own shape and order, each name with its default (core_engine/shells.py SCHEDULE, the species' defaults; the owner 2026-10-26: "it needs to be exactly like this in the shell")
        self.single = tuple(single)   # a slot that holds its one shell, never a stack (the frame's AGENT slot)
        self.slots = tuple(slots)   # THE ROOT SHAPE's slots, in their fixed order (settings root_shape): each keeps its own stack
        self.schema = tables or schema()   # ITS TABLES, declared beside the database (instance/<office>.json); a check's scratch store is declared by the office's own
        self.table = self.schema['tables'][0]
        self._said = None   # A RUN's verdict or a refusal, said once (the page's own, nobody's browser)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def _con(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        with _GROW:   # one thread grows a store at a time (the page's start reads while its first draw opens the same new store)
            self._grow(con)
        return con

    def _grow(self, con):
        con.execute(create_sql(self.table))   # its one table, made the first time it is missing (a new or emptied store)
        if 'slot' not in {r[1] for r in con.execute('PRAGMA table_info(shells)')}:   # a store made before the shape: its shells go to the first slot, kept
            con.execute(f"ALTER TABLE shells ADD COLUMN slot TEXT NOT NULL DEFAULT '{self.slots[0]}'")
        for t in MOVED:
            con.execute(f'DROP TABLE IF EXISTS {t}')

    @staticmethod
    def _now():
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def say(self, shell, ok, text):
        """A RUN's verdict or a refusal, kept until the page says it once (nothing kept for a browser)."""
        self._said = {'shell': str(shell), 'ok': bool(ok), 'text': text}

    def said(self):
        got, self._said = self._said, None
        return got

    def _rows(self, con, slot=None):
        rows = [dict(r) for r in con.execute(f'SELECT * FROM shells ORDER BY {self.table["order"]}')]
        return rows if slot is None else [r for r in rows if r['slot'] == slot]

    def _slot_of(self, con, shell_id):
        return self._shell(con, shell_id)['slot']

    def root_on(self):
        """THE REPLICA ON OR OFF: its AGENT slot's own switch (the owner 2026-10-26: "off means it all stops"; "the agent block
        might do that already"): the agent off, the whole replica off; no agent slot, on."""
        with self._con() as con:
            rows = [r for s in self.single for r in self._rows(con, s)]
        return all(r['switch'] == 'on' for r in rows)

    @staticmethod
    def _order(con, ids):
        for n, shell_id in enumerate(ids, 1):
            con.execute('UPDATE shells SET position = ? WHERE id = ?', (n, shell_id))

    def source(self, shell_id):
        """The identity a job minted into this shell carries: the platform's own (frame_replica.Door.source)."""
        return self.door.source(shell_id)

    def agents(self):
        """the agents a shell may hold: every card under SYSTEM, (key, name)"""
        return self.door.cards()

    def _job(self, rec):
        """A JOBS RECORD as the shell's hands read it: the record whole, and its parts by the shell's own names."""
        return {**rec, 'job_key': self.door.key('jobs', rec), 'source': rec.get('identity_job_source') or '', 'agent_key': rec.get('data_agent_key') or '',
                'run': rec.get('data_job_run') or '', 'run_state': rec.get('data_job_run_state') or '', 'log': rec.get('data_job_log') or '',
                'full_name': rec.get('data_full_name') or '', 'block_type': rec.get('data_job_block_type') or '',
                **{c: rec.get(f'data_job_{c}') or '' for c in WIRES}, **{n: rec.get(f'data_job_{n}') or '' for n, _d in self.schedule},
                'created_at': rec.get('system_created_at') or '', 'updated_at': rec.get('system_updated_at') or ''}

    def _jobs(self):
        return {k: self._job(r) for k, r in self.door.jobs().items()}

    def board(self):
        """The shells in order, each with the job it holds (or none); the board always has one shell: the first visit places it."""
        with self._con() as con:
            for slot in self.slots:   # every slot of the shape holds its first shell from the first visit
                if not self._rows(con, slot):
                    con.execute("INSERT INTO shells (position, slot, switch, job_key) VALUES (?, ?, 'on', '')", (len(self._rows(con)) + 1, slot))
            rows = self._rows(con)
        jobs = self._jobs()
        held = [j if (j := jobs.get(r['job_key'])) and j['source'].startswith(f'{self.door.member}@{self.door.screen}#') else None for r in rows]   # its own job, or its manager's workflow block held by reference
        cards = {self.door.key('agnt', c): c for c in self.door.rows('agnt')} if any(j and j['agent_key'] for j in held) else {}   # the cards the held jobs name (LARRYD): each shell's agent, its class and where it runs
        targeted = {w for j in held if j for w in (j[c] for c in WIRES) if w}
        live = all(r['switch'] == 'on' for r in rows if r['slot'] in self.single)   # the agent off: every shell in the replica off too
        out = []
        at = {}
        for r, job in zip(rows, held):
            i = at[r['slot']] = at.get(r['slot'], -1) + 1   # its place in its own slot
            wires = [job[c] for c in WIRES] if job else ['', '', '']
            state = 'wired' if any(wires) else ('end' if job and job['job_key'] in targeted else 'unwired')
            out.append({'id': r['id'], 'slot': r['slot'], 'index': i, 'count': sum(1 for x in rows if x['slot'] == r['slot']), 'place': i + 1, 'places': sum(1 for x in rows if x['slot'] == r['slot']), 'on': (live or r['slot'] in self.single) and r['switch'] == 'on', 'job': self.platform_job(job),
                        'job_key': job['job_key'] if job else '', 'agent': (job or {}).get('agent_key') or '', 'wires': wires,
                        'wire': state, 'jobs_here': [j['job_key'] for j in held if j], 'neutral': not live or r['switch'] != 'on',
                        'harness': False, 'sequence': False, 'schedule': {n: job[n] or d for n, d in self.schedule} if job else {},
                        **self.connected(job, cards)})
        return out

    def connected(self, job, cards=None):
        """THE RECORDS A SHELL CONNECTS TO BY THE KEYS ITS JOB HOLDS (the owner 2026-10-27: "the shell needs to automatically connect to them.. its not hard
        wired"; "all shells need to auto connect"): the AGENTS card its agent key names (by the platform's own names, larryd_runtime.CARD, and whether it
        runs inside), the MODELS record its model key names, the LOGS record of its last RUN (its key, when it ran), and its own key's stage; no job: none."""
        if not job:
            return {'card': None, 'model': {}, 'log': {}, 'stage': ''}
        c = (cards if cards is not None else {self.door.key('agnt', x): x for x in self.door.rows('agnt')}).get(job['agent_key']) if job['agent_key'] else None
        last = next((r for r in self.runs(job['job_key']) if r['n']), {})   # its last RUN (n 1 and up), the run its JOB LOG line says; a RUN 0 (the
        # original's standup loaded, its log alone) is never the shell's log (the owner 2026-10-27: "LOG KEY ... JOB LOG ... all wrong")
        return {'card': ({**{n: c.get(f) or '' for n, f in self.door.runtime.CARD.items()}, 'internal': (c.get('data_agent_environment') or '') == self.door.runtime.INTERNAL} if c else None),
                'model': self.door.model_of(job.get('data_model_key') or ''), 'log': {'key': last.get('log_key', ''), 'time': last.get('started_at', '')}, 'stage': self.door.stage(job['job_key'])}

    def platform_job(self, job):
        """The job as the platform's one shell reads a JOBS record (atom.html): the record's own fields, its schedule's defaults where empty."""
        if not job:
            return None
        rec = {k: v for k, v in job.items() if k.startswith(('identity_', 'data_', 'system_', 'tag_')) or k.endswith('_norm_key') or k == 'id'}
        return {**rec, **{f'data_job_{n}': job[n] or d for n, d in self.schedule}}

    def _shell(self, con, shell_id):
        r = con.execute('SELECT * FROM shells WHERE id = ?', (shell_id,)).fetchone()
        if r is None:
            raise KeyError(shell_id)
        return dict(r)

    def _held(self, shell_id):
        shell = next((x for x in self.board() if str(x['id']) == str(shell_id)), None)
        if shell is None:
            raise KeyError(shell_id)
        if not shell['job']:
            raise ValueError('Add job first')
        return shell

    def _edit(self, key, values, run=False):
        """a job's own fields, by the shell's names, written through the pipeline"""
        self.door.edit(key, {FIELD.get(k, f'data_job_{k}'): v for k, v in values.items()}, run=run)

    def add(self, after=None, beside=None):
        """A new shell in the slot of the shell it is added beside (the first slot when none), after its place there."""
        with self._con() as con:
            slot = self._slot_of(con, beside) if beside is not None else self.slots[0]
            ids = [r['id'] for r in self._rows(con, slot)]
            new = con.execute("INSERT INTO shells (position, slot, switch, job_key) VALUES (?, ?, 'on', '')", (len(self._rows(con)) + 1, slot)).lastrowid
            ids.insert(len(ids) if after is None else min(after + 1, len(ids)), new)
            self._order(con, [r['id'] for r in self._rows(con) if r['slot'] != slot] + ids)
        return new

    def remove(self, shell_id):
        with self._con() as con:
            rows = self._rows(con, self._slot_of(con, shell_id))
            if len(rows) <= 1:
                raise ValueError('a slot always keeps one shell')
            con.execute('DELETE FROM shells WHERE id = ?', (shell_id,))
            self._order(con, [r['id'] for r in self._rows(con)])

    def move(self, shell_id, step):
        with self._con() as con:
            slot = self._slot_of(con, shell_id)
            ids = [r['id'] for r in self._rows(con, slot)]   # within its own slot: a shell never leaves the slot it is in
            i = [str(x) for x in ids].index(str(shell_id))
            j = i + step
            if 0 <= j < len(ids):
                ids[i], ids[j] = ids[j], ids[i]
                self._order(con, [r['id'] for r in self._rows(con) if r['slot'] != slot] + ids)

    def switch(self, shell_id, on):
        with self._con() as con:
            self._shell(con, shell_id)
            con.execute('UPDATE shells SET switch = ? WHERE id = ?', ('on' if on else 'off', shell_id))

    def add_job(self, shell_id):
        """ADD JOB: a JOBS record minted into the shell by the pipeline (its identity this shell's); the shell holds its key."""
        with self._con() as con:
            shell = self._shell(con, shell_id)
        job = self._jobs().get(shell['job_key'])
        if job and job['source'] == self.source(shell_id):
            raise ValueError('this shell already holds a job')
        key = self.door.add_job(shell_id)
        with self._con() as con:
            con.execute('UPDATE shells SET job_key = ? WHERE id = ?', (key, shell_id))
        return key

    def remove_job(self, shell_id):
        """REMOVE JOB: the shell's own job is deleted (wires that pointed at it are cut); the shell stays, empty."""
        shell = next((x for x in self.board() if str(x['id']) == str(shell_id)), None)
        if shell is None:
            raise KeyError(shell_id)
        with self._con() as con:
            if not self._shell(con, shell_id)['job_key']:
                raise ValueError('this shell holds no job')
        if shell['job'] and (self._jobs().get(shell['job_key']) or {}).get('source') == self.source(shell_id):   # A WORKFLOW BLOCK'S JOB HELD BY REFERENCE IS NEVER DELETED HERE: the shell lets go of it
            key = shell['job_key']
            for x in self.board():
                cut = {c: '' for c, w in zip(WIRES, x['wires']) if w == key}
                if cut:
                    self._edit(x['job_key'], cut)
            self.door.delete_job(key)
        with self._con() as con:
            con.execute("UPDATE shells SET job_key = '' WHERE id = ?", (shell_id,))

    def wire(self, shell_id, n, target):
        if n not in range(1, len(WIRES) + 1):
            raise ValueError('a member sets wires (1) to (3); (4) is the neutral passthrough')
        shell = self._held(shell_id)
        key, target = shell['job_key'], (target or '').strip().upper()
        if target:
            if target == key or target not in shell['jobs_here']:
                raise ValueError('a wire goes to another job on this board')
            links = {x['job_key']: [w for w in x['wires'] if w] for x in self.board() if x['job']}
            links[key] = [w for i, w in enumerate(shell['wires'], 1) if w and i != n] + [target]
            seen, todo = set(), [target]
            while todo:
                k = todo.pop()
                if k == key:
                    raise ValueError('that wire would make a loop')
                if k not in seen:
                    seen.add(k)
                    todo += links.get(k, [])
        self._edit(key, {WIRES[n - 1]: target})

    def agent(self, shell_id, agent_key, agents=None):
        """ADD AGENT: the job's agent, one of SYSTEM's cards (LARRYD); '' lets go of it."""
        shell = self._held(shell_id)
        agent_key = (agent_key or '').strip()
        if agent_key and agent_key not in dict(agents if agents is not None else self.agents()):
            raise ValueError('not an agent of this account')
        self._edit(shell['job_key'], {'agent_key': agent_key})

    def run(self, shell_id):
        """RUN: a REQUEST. Refused with no job, when the shell is off, with no agent, or while a run is open; otherwise
        RUN = n + 1 and RUN STATE = QUEUED, written as the Run button writes them. Nothing is executed here."""
        shell = next((x for x in self.board() if str(x['id']) == str(shell_id)), None)
        if shell is None:
            raise KeyError(shell_id)
        job = shell['job']
        if not job:
            return False, 'Add job first'
        if not shell['on']:
            return False, 'Switched off: turn the block on first'
        if not job['data_agent_key']:
            return False, 'Add agent first'
        if job['data_job_run_state'] in OPEN_RUN:
            return False, f'RUN {job["data_job_run"]} IS ALREADY {job["data_job_run_state"]}'
        n = int(job['data_job_run'] or 0) + 1
        for attempt in range(6):   # LARRYD BUSY IS NOT A DEAD RUN (the owner 2026-10-27: "and if it has a red an agent should be working on it"; the fixer named it: "database is locked" after the QUEUED write left run 31 stuck)
            try:
                self._edit(shell['job_key'], {'run': str(n), 'run_state': 'QUEUED'}, run=True)
                break
            except sqlite3.OperationalError as busy:
                if 'locked' not in str(busy):
                    raise
                held = self._jobs().get(shell['job_key']) or {}
                if str(held.get('data_job_run')) == str(n) and held.get('data_job_run_state') == 'QUEUED':
                    break   # the write landed, only the report after it was refused: the run is queued
                time.sleep(0.5 * (attempt + 1))
        else:
            return False, 'LARRYD is busy: RUN AGENT again in a moment'
        return True, f'RUN {n} QUEUED'

    def _busy(self, write, landed):
        """ONE WRITE THROUGH A BUSY LARRYD: 'database is locked' tried again up to six times, as run()'s QUEUED, unless it landed (only the report after it was refused)"""
        for attempt in range(6):
            try:
                return write()
            except sqlite3.OperationalError as busy:
                if 'locked' not in str(busy):
                    raise
                if landed():
                    return None
                time.sleep(0.5 * (attempt + 1))
        return write()   # the last try: a fault now is said by its caller

    def ran(self, job_key, n, started_at, ended_at, exit_code, said, state):
        """A RUN ENDED: its LOGS record (one per run, kept), and the job's RUN ended with its state and its line (n 0: a run loaded
        from the original, its log alone)."""
        job = self.door.jobs().get(job_key)
        if job is None:
            raise KeyError(job_key)
        line = f'{started_at} → {ended_at} · exit {exit_code}'
        logged = lambda: any(r.get('identity_log_block') == f'RUN {n}' and r.get('identity_log_time') == started_at for r in self.door.logs(job_key))
        self._busy(lambda: self.door.add_log(job, n, started_at, ended_at, exit_code, said), logged)   # LARRYD BUSY IS NOT A DEAD RUN (the moiré's RUN 13 left QUEUED): its log written once
        if n:
            self._busy(lambda: self._edit(job_key, {'run_state': state, 'log': line}, run=True),
                       lambda: (self._jobs().get(job_key) or {}).get('data_job_run_state') == state)
            word = {SETTINGS['root_shape']['x_board']['done']: 'GREEN', 'FAILED': 'RED'}.get(state)
            if word:   # THE RULES STATUS, the agent's own check, said the moment its run ends: DONE GREEN, FAILED RED (SKILLS_POSITIVE_FEEDBACK_BUILD field 2)
                self._edit(job_key, {'rules_status': word})

    def runs(self, job_key, limit=30):
        """A job's runs, newest first, each from its LOGS record: when it started and ended, its exit, what it wrote, its log key."""
        out = []
        for r in self.door.logs(job_key, limit):
            m = LOG_LINE.match(r.get('data_log_message') or '')
            block = (r.get('identity_log_block') or '').rpartition(' ')[2]
            out.append({'id': r['id'], 'job_key': job_key, 'n': int(block) if block.isdigit() else 0, 'started_at': r.get('identity_log_time') or '',
                        'ended_at': m['end'] if m else '', 'exit': int(m['exit']) if m else 1, 'said': r.get('data_notes') or '', 'log_key': self.door.key('logs', r)})
        return out

    def set_job(self, job_key, values):
        """A job's own fields (its name, its schedule, its sanity: skills_*, rule_*, lie_detector), by its key, through the pipeline."""
        self._edit(job_key, values)

    def act(self, shell_id, do, value='', n=0, index=None, clear=False, agents=None):
        """EVERY SHELL ACTION. -> {} done; {ok, text} a RUN's verdict. KeyError: no such shell; ValueError: refused, and why."""
        held = None
        with self._con() as con:
            if shell_id:
                held = self._shell(con, shell_id)['slot']
        if not self.root_on() and not (do == 'switch' and held in self.single):   # THE REPLICA OFF (its agent off): nothing inside it acts, nothing runs; only the agent's switch turns it back on
            raise ValueError('the replica is off')
        if do == 'add':
            self.add(index, beside=shell_id or None)
        elif do == 'remove':
            self.remove(shell_id)
        elif do in ('up', 'down'):
            self.move(shell_id, -1 if do == 'up' else 1)
        elif do == 'switch':
            self.switch(shell_id, value == 'on')
        elif do == 'add_job':
            self.add_job(shell_id)
        elif do == 'remove_job':
            self.remove_job(shell_id)
        elif do == 'wire':
            self.wire(shell_id, n, '' if clear else value)
        elif do == 'agent':
            self.agent(shell_id, value, agents)
        elif do == 'run':
            ok, text = self.run(shell_id)
            return {'ok': ok, 'text': text}
        else:
            raise ValueError(f'unknown action {do!r}')
        return {}


# ---- what every frame file draws with: the light, a block of the frame, the clock's words ---------------------------
LIGHT_SVG = ('<span class="scrum-light" role="img" aria-label="{word}" data-light="{state}"><svg class="hdr-icon" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2" fill="none">'
             '<circle cx="12" cy="12" r="9"/>{dot}</svg></span>')   # the original's light: a ring, its dot green or red, empty when not seen today


def light_of(job, rule, now=None):
    """THE LIGHT OF AN AGENT TODAY, one source for the X board and every canvas (the owner 2026-10-27: "the green red light on the top
    right"): green when its job ran today and ended DONE (rule done), red when it ran today and ended in a red word (rule red), nothing
    when not seen today. A LIVE job (schedule live) runs on a flip alone: its last run is its light now, whatever its day. -> 'green' | 'red' | ''"""
    zone = zoneinfo.ZoneInfo(rule['zone'])
    now = now or datetime.datetime.now(zone)
    job = job or {}
    at = str(job.get('system_updated_at') or '')
    try:   # THE DAY IN THE BOARD'S OWN ZONE: the record's moment is UTC (…Z), so after 8 PM New York its date is already tomorrow's
        day = datetime.datetime.fromisoformat(at.replace('Z', '+00:00')).astimezone(zone).date() if at else None
    except ValueError:
        day = None
    if day != now.date() and str(job.get('data_job_schedule_type') or '').lower() != 'live':
        return ''
    state = job.get('data_job_run_state')
    return 'green' if state == rule['done'] else 'red' if state in (rule.get('red') or ()) else ''


def light_view(state):
    dot = {'green': '<circle class="hdr-status--success" cx="12" cy="12" r="4.5" stroke="none"/>', 'red': '<circle class="hdr-status--error" cx="12" cy="12" r="4.5" stroke="none"/>'}.get(state, '')
    return LIGHT_SVG.format(word={'green': 'green', 'red': 'red'}.get(state, 'not seen yet'), state=state or 'none', dot=dot)


def run_said(r):
    """WHAT A RUN SAID, in one line (the ROWS table's last column, the stream's line): its summary, or the standup's word."""
    try:
        said_ = json.loads(r['said'])
    except (TypeError, ValueError):
        return str(r['said'])[:120]
    if not isinstance(said_, dict):
        return str(r['said'])[:120]
    if said_.get('loaded'):
        return "the original's standup of that day, loaded"
    if 'written' in said_:
        return f"updated: the standup of today, three lines, written at {said_.get('written', '')}"
    return said_.get('summary') or said_.get('word') or ' · '.join(f'{k} {v}' for k, v in list(said_.items())[:4])


GROUP_CSS = '.replica-group { text-align: right; margin: 24px 0 6px; font-family: var(--clarity-face-caption, inherit); font-size: .8rem; font-weight: 700; line-height: 1.2; letter-spacing: .08em; text-transform: uppercase; } .replica-group + * { margin-top: 0 !important; }'   # THE GROUP WORD'S STYLE, the standup's TOP exactly (the owner 2026-10-27 13:27: "do you see how top is pink and on the outside? all blocks need to be exactly like this")


def group_line(word):
    """A BLOCK'S GROUP WORD (the owner 2026-10-27 13:27: "all blocks need to be exactly like this ... same rule for all"): its own line ABOVE the block,
    right-aligned, in the page's own pink ink, outside it, the standup's markup exactly; no word, nothing. -> Markup"""
    from markupsafe import Markup, escape
    return Markup(f'<div class="replica-group" aria-label="group">{escape(word)}</div>') if word else Markup('')


def block(name, head, body, group=''):
    """A BLOCK OF THE FRAME (as the X board and AGENT ACCESS are drawn): its group word on its own line above it, outside (group_line; the owner
    2026-10-27 13:27: "should not be shape and not inside"), its head with its words, its body. -> {html, css}"""
    from markupsafe import Markup, escape
    html = (str(group_line(group)) + f'<div class="replica-normal-block replica-frame-part" aria-label="{name}"><div class="title scaf-law-title">{name}</div>'   # A NORMAL BLOCK LIKE THE LIVE (the owner 2026-10-27 13:30: "these sections dont need the clarity white they can look like a normal block like live")
            + (f'<div class="subtitle replica-normal-line">{escape(head)}</div>' if head else '') + f'<div class="replica-normal-body">{body}</div></div>')   # no head: no empty line
    return {'html': Markup(html), 'css': Markup('')}


def when(schedule):
    """An hour, said as the shell's clock says it: NEW YORK · 6:50 AM · DAILY; none (the frame holding no agent) says nothing."""
    if not schedule:
        return ''
    if str(schedule.get('schedule_type') or '').lower() == 'manual':   # ON RUN AGENT ONLY (the DAY script, the owner 2026-10-28: "RUN AGENT only until proven"): never due by itself
        return f"{schedule['location']} · ON RUN AGENT"
    if str(schedule.get('schedule_type') or '').lower() == 'live' or not schedule.get('time'):   # A LIVE AGENT: no hour, it looks on every change of its triggers
        return f"{schedule['location']} · LIVE · ON EVERY CHANGE"
    h, m = (int(x) for x in schedule['time'].split(':'))
    return f"{schedule['location']} · {datetime.time(h, m).strftime('%I:%M %p').lstrip('0')} · {schedule['schedule_type'].upper()}"


def idle_after(last, running=False, zone='America/New_York'):
    """THE GREEN IDLE AFTER A ONE-LINE BLOCK (the owner 2026-10-28: "place in green IDLE time after the rules and skills"): READING while the
    MARK IV agent reads, else IDLE ticking from its last run's end (the page's own scrum-since); nothing before a first run. -> markup"""
    from markupsafe import escape
    if running:
        return '<span class="replica-idle"><span class="hdr-status--success">READING</span></span>'
    if not last:
        return ''
    since = ''
    for at in (last.get('ended_at'), last.get('started_at')):
        try:
            m = datetime.datetime.fromisoformat(str(at))
        except (TypeError, ValueError):
            continue
        since = (m if m.tzinfo else m.replace(tzinfo=zoneinfo.ZoneInfo(zone))).isoformat()
        break
    if not since:
        return ''
    return (f'<span class="replica-idle"><span class="hdr-status--success">IDLE</span>'
            f'<span class="scrum-since hdr-status--success" data-since="{escape(since)}"></span></span>')


def last_said(last):
    """The MARK IV agent's last run, in a few words: LAST OCT 27 09:12 · 2 AGENTS · HEALTHY; nothing before a first run."""
    if not last:
        return ''
    import json
    try:
        at = datetime.datetime.fromisoformat(last['started_at']).strftime('%b %d %H:%M').upper()
        got = json.loads(last['said'] or '{}')
    except (TypeError, ValueError):
        return ''
    return f"LAST {at} · {got.get('agents', 0)} AGENTS · {got.get('word', '')}".rstrip(' ·') if got else f'LAST {at}'


# ---- THE SANITY'S SHARED PIECES (frame_skills, frame_rules and frame_red each import this file alone): the knowledge store's index, a job's
# ten skills, the program's hash as its job keeps it, and the one reader (SKILLS_POSITIVE_FEEDBACK_BUILD 3.1 to 3.3)
TEN = 10   # THE SKILLS ARE TEN (the owner 2026-10-27: "a list of 10 skills"; "populates to the max each time to 10")
POINTER = 'pointer:'   # the night's note of a log (the knowledge store's night), never a skill: left out of every index
FIXED_TAIL = ' · what makes it green or red, how to run and read it'   # the rules' titles in the store all end so; not said
CODE = re.compile(r'^(?P<file>[\w.-]+\.py) · (?P<sha>[0-9a-f]{64})$')   # data_job_rule_code: the program file and the sha256 its rule parts were read against


def index(conf):
    """THE SKILLS INDEX of the knowledge store, every row whole (read where it is, read only): {row: [entries in rank order]}, each its state, kind,
    key and line; a pointer: entry is never a skill; none for an office that names no knowledge store."""
    if not conf or not conf.get('knowledge'):
        return {}
    con = sqlite3.connect(f"file:{os.path.expanduser(conf['knowledge'])}?mode=ro", uri=True, timeout=2)
    try:
        got = con.execute('SELECT s.row, s.rank, s.why, e.key, e.title, e.summary, e.state FROM skills s JOIN entries e ON e.id = s.entry_id ORDER BY s.row, s.rank').fetchall()
    finally:
        con.close()
    rows = {}
    for file, rank, why, key, title, summary, state in got:
        if str(key or '').startswith(POINTER):
            continue
        line = ' · '.join(x for x in (str(title or '').strip().replace(FIXED_TAIL, ''), str(summary or '').strip()) if x)
        rows.setdefault(file, []).append({'rank': int(rank or 0), 'kind': str(why or ''), 'line': line[:240], 'key': str(key or ''), 'state': str(state or '').lower()})
    return rows


def knowledge(agent, module):
    """AN AGENT'S KNOWLEDGE ENTRIES: those filed under the original's row it stands for (its ROW_FILE, only in an office that names the original)
    and under this office's own row (<office>/<file>), each once, in the store's rank order."""
    facts = (agent or {}).get('facts') or {}
    by_file = index(facts)
    stood = by_file.get(getattr(module, 'ROW_FILE', '') or '', []) if facts.get('db') else []
    own = by_file.get(f"{NAME}/{os.path.basename(module.__file__)}", [])
    return stood + [e for e in own if e['key'] not in {x['key'] for x in stood}]


def lessons(agent, module):
    """AN AGENT'S REAL FIXES (the owner 2026-10-27: "if we do real fixes and then they are in the knowledge base too at least that gives us a correct
    baseline"): the knowledge store's lessons filed under its row (<office>/<file>), newest first, read only; each {key, title, summary, commit}."""
    db = os.path.expanduser(str(((agent or {}).get('facts') or {}).get('knowledge') or ''))
    if not db or not os.path.isfile(db):
        return []
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=2)
    try:
        row = f"{NAME}/{os.path.basename(module.__file__)}"
        first = getattr(module, 'ROW_FILE', '') or ''   # A MOVED AGENT'S ORIGINAL ROW (ROW_FILE: the program its lessons, rules and skills were filed under, in whichever office it was born)
        got = con.execute("SELECT key, title, summary, text FROM entries WHERE kind = 'lesson' AND (row = ? OR row LIKE ? OR (? != '' AND (row LIKE ? OR row LIKE ?))) ORDER BY created_at DESC, id DESC",
                          (row, f'%"{row}"%', first, f'%/{first}', f'%/{first}"%')).fetchall()   # the store keeps an entry's rows as a list (["office/file.py"]), a check's scratch one the row alone
    finally:
        con.close()
    out = []
    for key, title, summary, text in got:
        m = re.search(r'\bCOMMIT ([0-9a-f]{7,40})\b', str(text or '')) or re.search(r'\bFIX ([0-9a-f]{7,40})\b', str(summary or ''))
        out.append({'key': str(key), 'title': str(title or ''), 'summary': str(summary or ''), 'text': str(text or '')[:1500], 'commit': m.group(1)[:7] if m else ''})
    return out


def history(agent, module):
    """WHAT HAS BROKEN BEFORE (the owner 2026-10-27: "you can look back in the history too not just tonight"; "our original has evolved over time"): the
    knowledge store's facts of the original's red runs filed under the row the agent stands for (its ROW_FILE), most often first, read only."""
    db = os.path.expanduser(str(((agent or {}).get('facts') or {}).get('knowledge') or ''))
    row = getattr(module, 'ROW_FILE', '') or ''
    if not db or not row or not os.path.isfile(db):
        return []
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=2)
    try:
        return [str(t) for (t,) in con.execute("SELECT title FROM entries WHERE (row = ? OR row LIKE ?) AND key LIKE 'history-%' ORDER BY id", (row, f'%"{row}"%')).fetchall()]
    finally:
        con.close()


def job_skills(job):
    """A JOB'S SKILLS READ BACK FROM ITS RECORD: the filled slots of data_job_skill_1..10, each {state, kind, key, line}, in their order."""
    job = job or {}
    return [{'state': str(job.get(f'data_job_skill_{i}_status') or '').lower(), 'kind': str(job.get(f'data_job_skill_{i}_type') or '').lower(),
             'key': '', 'line': str(job.get(f'data_job_skill_{i}_description') or '')} for i in range(1, TEN + 1) if job.get(f'data_job_skill_{i}_description')]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def code_of(job):
    """THE CODE A JOB'S RULE PARTS WERE READ AGAINST (data_job_rule_code): {'file', 'sha'}, or None before a first read."""
    m = CODE.match(str((job or {}).get('data_job_rule_code') or ''))
    return m.groupdict() if m else None


def reader_command(settings):
    """The reader's command (settings reader: the original's, read only), on the web model (settings models.web: Opus 5.5)."""
    cmd = list(settings['reader']['command'])
    model = settings['models']['web']
    if '--model' in cmd:
        cmd[cmd.index('--model') + 1] = model
    else:
        cmd[1:1] = ['--model', model]
    return cmd


def hire(cmd, words, cwd, seconds, job_path=''):
    """ONE HIRED READ, its words on stdin, a clock on it, a group of its own, stopped whole when its clock runs out (as the original's hire): the
    few words a program needs of this laptop's environment and nothing else. -> (exit code, or None when its clock ran out or it could not be
    started; what it said)."""
    env = {k: os.environ[k] for k in ('HOME', 'USER', 'LOGNAME', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ}
    env.update({'PATH': (job_path + ':' if job_path else '') + os.environ.get('PATH', '/usr/bin:/bin'), 'PYTHONDONTWRITEBYTECODE': '1'})
    try:
        child = subprocess.Popen([os.path.expanduser(x) for x in cmd], cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, start_new_session=True, env=env)
    except OSError as e:
        return None, f'no reader could be started ({type(e).__name__}: {e})'
    try:
        said, _ = child.communicate(words, timeout=max(30, int(seconds)))
        code = child.returncode
    except subprocess.TimeoutExpired:
        said, code = '', None
    finally:
        for sig in (signal.SIGTERM, signal.SIGKILL):   # nothing of it outlives it
            try:
                os.killpg(child.pid, sig)
            except (ProcessLookupError, PermissionError):
                break
    return code, said


def remember(key, kind, title, summary, row, by, text=''):
    """ONE ENTRY INTO THE KNOWLEDGE STORE through its one door (bin/knowledge add; REPLICA_KNOWLEDGE_DOOR names another, a check's /usr/bin/true):
    a RED skill's reason (frame_skills), a cleared red's lesson (frame_red). A door that does not answer loses the entry, never the run."""
    door = os.path.expanduser(os.environ.get('REPLICA_KNOWLEDGE_DOOR') or '~/virtual_sanity/knowledge/bin/knowledge')
    try:
        subprocess.run([door, 'add', '--key', key, '--kind', kind, '--title', title[:300], '--summary', summary[:2000], '--row', row, '--by', by],
                       input=text or summary, capture_output=True, text=True, timeout=60)   # its text on stdin, as the door reads it
    except (OSError, subprocess.SubprocessError):
        pass
