"""THE ONE DATABASE DOOR of the Scrum Master: scrum_master_3_release.db, its schema beside it (instance/scrum_master.json, the
owner 2026-10-21: "put the schema file for the db in the folder"). Nothing else opens it (PLAN.md, 2026-10-21:
"agent/shared_store.py: the only code that touches his data"). Every data statement goes through the FROST SECURITY
LOCK (door_guard.secure_query), and every connection wears its guard.

THE TABLES (the owner 2026-10-21: a database designed for the 45 row agents, not old files poured into tables): real
columns with real SQLite types (STRICT), a UNIQUE key, an index on the row and on the day or start, CHECKs on the
states, no body column; settings (the owner 2026-10-21: settings out of notes); and BUILD ITEMS A AND B (the owner's
spec 2026-10-21, section 2): requests (A, his requests in his exact words), build_items (B, each under one parent
request: a FOREIGN KEY, PRAGMA foreign_keys ON on every connection) and build_turns. Made by Store() when it opens,
through the same lock. work_items and work_turns stay until every reader has moved to requests and build_items (archived
whole to ~/scratch/reports/scrum_master_3/archive/ on 2026-10-21; the main session drops them). One function each:
    st = Store()                                    instance/ beside app/, or $SCRUM_MASTER_INSTANCE
    st.run(row, started, ended, state, text)        a row run, upserted on row + started (a running run later ended)
    st.item(id, row, title, state, found, closed=None)   a work item (work_items), upserted on its id
    st.turn(item_id, turn, result)                  a turn on an item (a second turn n refused: sqlite3.IntegrityError)
    st.finding(row, place, file, line, severity, state)  a finding, upserted on row + place + file + line
    st.lesson(row, lesson, at)                      a lesson (the same lesson twice is kept once) -> True when new
    st.note(day, text)                              the day's note (the standup, the summary), upserted on day
    st.request_add(words, source, ref, asked_at)    a request (A): R-NNNN, state asked, position next; the same line twice: None
    st.request_state(id, state, why=None, ...)      a request's state changed (state_at now), its other columns with it
    st.build_item_add(request_id, found_by, rule, evidence, file=None)   a build item (B) under its request: B-NNNN
    st.build_item_state(id, state, turns=None, approach=None)            a build item's state changed
    st.build_turn(item_id, turn, approach, result, at=None)             a turn on an R or a B (twice: sqlite3.IntegrityError)
    st.requests(state=None) / st.request(id) / st.build_items(request_id=None, state=None) / st.build_turns(item_id=None)
    st.runs(row=None, day=None) / st.items(state=None, row=None) / st.turns(item_id)
    st.findings(row=None, state=None) / st.lessons(row=None) / st.notes(day=None)     the readers: plain dicts
    st.latest_runs(since=None, row=None) / st.open_items(row=None)                    the board, the open work
    st.table_rows(table) / st.replace(table, key, values)                             a whole table; one row changed in place
    st.log_path(*parts)                             a file under the logs folder outside sanity (folders made)
    write_whole(path, obj)                          a file of his own written whole (then one rename), never through a link

    st.setting(name, value, at=None) / st.settings_kept()                          a value changed at run time (settings)

THE DEFAULTS are settings.json (schemas/), read only: nothing writes it at run time (it is LOCKED by the final deploy).
Every value changed at run time (a switch, the worker's session and pause, the rulebook's bump) is kept HERE, in its
own table, settings (name TEXT PRIMARY KEY, value TEXT JSON, at TEXT; STRICT): one row a name, newest wins; a reader
takes the kept value over the default (shared_memory.settings). Notes keep the standup and the summary only: the old
SETTINGS NOTE (the notes row of day SETTINGS_DAY, 0000-00-00) is carried into settings once when the door opens, and
that notes row deleted. History is not data (what was said, told and seen: logs, files under
the logs folder outside ~/virtual_sanity). No secrets (the owner 2026-10-21)."""
import datetime
import hashlib
import json
import os
import sys
import re
import sqlite3

from . import shared_door_guard as door_guard
from . import shared_where as where   # his places (his logs folder: schemas/reports.json)
from .shared_door_guard import FrostLockError, Secured, secure_query   # THE FROST SECURITY LOCK, the door's own  # noqa: F401

SCHEMAS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'instance'))   # EACH DATABASE'S SCHEMA BESIDE IT IN instance/ (the owner 2026-10-21: "put the schema file for the db in the folder")
LOGS = where.LOGS   # his own logs, outside the locked folder: named once, in schemas/reports.json (or $SCRUM_MASTER_LOGS)
INSTANCE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'instance'))   # <office>/scrum_master/instance


def _schema(name):
    with open(os.path.join(SCHEMAS, name), encoding='utf-8') as fh:
        return json.load(fh)


FILES = {'scrum_master': 'scrum_master_3_release.db'}   # no two databases of the system share a file name (owner 2026-09-28)
SETTINGS_TABLE = {   # THE SEVENTH (the owner 2026-10-21: settings out of notes), as instance/scrum_master.json declares it; here too, so the door
    'name': 'settings',   # makes it on open even before that file is copied in by hand (the apply changes app/ only); a check holds the two the same
    'purpose': ('THE VALUES CHANGED AT RUN TIME (the owner 2026-10-21: settings out of notes): one row a setting, its dotted name in settings.json '
                '(switches.worker, develop.worker.session, memory.rulebook), its value as JSON (null: taken away, the default stands again) and when '
                'it was set; newest wins. settings.json keeps the defaults, read only'),
    'columns': ['name', 'value', 'at'], 'types': {'name': 'TEXT', 'value': 'TEXT', 'at': 'TEXT'}, 'required': ['name', 'value', 'at'],
    'primary': ['name'], 'unique': ['name'], 'index': [], 'check': {}, 'iso': {'at': 'time'}, 'json': ['value'], 'one_line': ['name'],
    'max': {'name': 200}, 'order': 'name'}
NEW = {t['name']: t for t in _schema('scrum_master.json')['new_tables']}   # HIS TABLES (row_runs, work_items, work_turns, findings, lessons, notes, settings, requests, build_items, build_turns): real types, no body
NEW.setdefault('settings', SETTINGS_TABLE)   # an instance schema of before settings: the door's own declaration of it
TABLE = NEW   # every table of his by its name: the ten, and nothing else
ROWS = (1, 45)   # the row agents, 01..45 (schemas/rows.json)
SETTING = 'setting'   # THE OLD SETTINGS NOTE's kind (carried into settings once, on open)
SETTINGS_DAY = '0000-00-00'   # THE OLD SETTINGS NOTE's day (no real day): read once to carry it into settings, then deleted
SETTING_NAME = re.compile(r'[a-z0-9_]+(\.[a-z0-9_]+)*')   # a setting's name: its dotted place in settings.json


def write_whole(path, obj):
    """A FILE OF HIS OWN, WRITTEN WHOLE (a state or a document of his: the work list's, a job's record, the Developer's
    day; never a record of the six): JSON (or a text as it is) written beside it, then one rename, so no reader ever
    sees half of it. A link where it is written is refused, never followed. -> the path"""
    path = os.path.abspath(path)
    for p in (os.path.dirname(path), path):
        if os.path.islink(p):
            raise OSError(f'a link stands where he writes: {p}')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    part = f'{path}.{os.getpid()}.{os.urandom(4).hex()}.part'
    with os.fdopen(os.open(part, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w', encoding='utf-8') as fh:
        fh.write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False))
    os.replace(part, path)
    return path


def instance():
    """His instance folder: $SCRUM_MASTER_INSTANCE (a check's scratch folder), else the office's own."""
    return os.path.abspath(os.environ.get('SCRUM_MASTER_INSTANCE') or INSTANCE)


def _iso(column, kind):
    """A CHECK that a time or day column reads as one (NULL passes: a time not yet known)."""
    day = '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    return f'"{column}" GLOB \'{day}\'' if kind == 'day' else f'"{column}" GLOB \'{day}T[0-9][0-9]:[0-9][0-9]*\''


def new_create_sql(table):
    """One of his tables exactly as its schema says: each column its real type, NOT NULL where required, its DEFAULT,
    its REFERENCES (foreign), its CHECKs (check, iso, rows, one_line, max, json: json_valid, pattern: a GLOB, length,
    min), its PRIMARY KEY (primary) or UNIQUE key (unique, also_unique); STRICT (a wrong type refused); no body column.
    -> (CREATE TABLE, [CREATE INDEX ...])"""
    name, parts = table['name'], []
    for c in table['columns']:
        checks = []
        if c in table.get('check', {}):
            checks.append(f'"{c}" IN (' + ', '.join("'" + v + "'" for v in table['check'][c]) + ')')
        if c in table.get('pattern', {}):
            checks.append(f'"{c}" GLOB \'{table["pattern"][c]}\'')
        if c in table.get('length', {}):
            checks.append(f'length("{c}") = {int(table["length"][c])}')
        if c in table.get('min', {}):
            checks.append(f'"{c}" >= {int(table["min"][c])}')
        if c in table.get('iso', {}):
            checks.append(_iso(c, table['iso'][c]))
        if c == table.get('rows'):
            checks.append(f'"{c}" BETWEEN {ROWS[0]} AND {ROWS[1]}')
        if c in table.get('one_line', ()):
            checks.append(f'instr("{c}", char(10)) = 0 AND instr("{c}", char(13)) = 0')
        if c in table.get('max', {}):
            checks.append(f'length("{c}") <= {int(table["max"][c])}')
        if c in table.get('json', ()):
            checks.append(f'json_valid("{c}")')
        part = f'"{c}" {table["types"][c]}' + (' NOT NULL' if c in table.get('required', ()) else '')
        part += ' PRIMARY KEY' if table.get('primary') == [c] else ''   # settings: name TEXT PRIMARY KEY
        part += f' DEFAULT {int(table["default"][c])}' if c in table.get('default', {}) else ''   # build_items: turns 0, approach 1
        if c in table.get('foreign', {}):   # build_items.request_id REFERENCES requests(id): a B without its A cannot be written
            other, col = re.fullmatch(r'([a-z_]+)\(([a-z_]+)\)', table['foreign'][c]).groups()
            part += f' REFERENCES "{other}" ("{col}")'
        parts.append(part + ''.join(f' CHECK ({x})' for x in checks))
    if table.get('primary') and len(table['primary']) > 1:   # build_turns: PRIMARY KEY (item_id, turn, approach)
        parts.append('PRIMARY KEY (' + ', '.join(f'"{c}"' for c in table['primary']) + ')')
    if table['unique'] != table.get('primary'):   # a PRIMARY KEY is its own unique key
        parts.append('UNIQUE (' + ', '.join(f'"{c}"' for c in table['unique']) + ')')
    for cols in table.get('also_unique', ()):   # requests: hash UNIQUE (one request taken in once)
        parts.append('UNIQUE (' + ', '.join(f'"{c}"' for c in cols) + ')')
    create = f'CREATE TABLE IF NOT EXISTS "{name}" (' + ', '.join(parts) + ') STRICT'
    indexes = [f'CREATE INDEX IF NOT EXISTS "{name}_by_{"_".join(cols)}" ON "{name}" (' + ', '.join(f'"{c}"' for c in cols) + ')'
               for cols in table.get('index', ())]
    return create, indexes


def _in_list(sql, column):
    """The words a table's own SQL allows in a column (its CHECK ("column" IN ('a', 'b'))), or None: no such CHECK."""
    m = re.search(r'"' + re.escape(column) + r'" IN \(([^)]*)\)', str(sql or ''))
    return re.findall(r"'([^']*)'", m.group(1)) if m else None


def one_line(value):
    """A text kept on one line: every run of white space one space, ends trimmed (None stays None)."""
    return None if value is None else ' '.join(str(value).split())


def cut(value):
    """WHAT IS GONE NEVER GOES INTO HIS RECORDS (the owner's O-1, 2026-10-21): every word of every order of kind 'gone'
    cut from a text before the door writes it (shared_words.cut, his order book read at the moment of the write). A
    finding's place and file are never cut: they name real files (row 010's radar is keyed by real paths)."""
    from . import shared_words as words
    return words.cut(value) if isinstance(value, str) else value


STATES_LOG = ('requests', 'states.jsonl')   # under his logs: EVERY STATE CHANGE OF A REQUEST, appended, never rewritten (the owner 2026-10-21: "a reset never erases the day's record")


def who():
    """who changed it: $SCRUM_MASTER_BY when a person or a session says so, else the program by its module"""
    if os.environ.get('SCRUM_MASTER_BY'):
        return os.environ['SCRUM_MASTER_BY'][:80]
    prog = ' '.join(sys.argv[:2]) if sys.argv else ''
    return 'the Developer' if 'shared_developer' in prog else 'the round' if 'agent001' in prog else 'the take-in' if 'agent018' in prog else (os.path.basename(prog) or 'a program')[:80]


def state_said(rid, state, why, at, by=None):
    """one line of the state log (a file of his, outside sanity); a log that cannot be written never stops a change. by: who
    changed it when the caller knows (the owner's own press on his page), else who() says"""
    try:
        path = os.path.join(LOGS, *STATES_LOG)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps({'at': at, 'id': rid, 'state': state, 'why': why, 'by': (by or who())[:80]}, ensure_ascii=False) + '\n')
    except OSError:
        pass


CLOSED_BY_HIM = ('approved', 'taken_in', 'green', 'shipped')   # a request the owner approved, or one done after his approval
REOPENS = ('asked', 'planned', 'building', 'proven', 'reviewed', 'waiting_takein', 'stuck_today')   # the states that open it again


class Store:
    def __init__(self, folder=None):
        self.folder = os.path.abspath(folder) if folder else instance()
        os.makedirs(self.folder, exist_ok=True)   # instance/ holds the database only (the owner 2026-10-21: logs outside, "no secrets for agents")
        con = self.connect()
        con.execute('PRAGMA journal_mode=WAL')   # READERS NEVER WAIT FOR A WRITER (as lryllm's door, W18b 2026-10-05)
        con.close()
        self.make_new_tables()   # THE SEVEN, made when the door opens (CREATE ... IF NOT EXISTS, never a drop); the old settings note carried

    @property
    def path(self):
        """The records' database (scrum_master_3_release.db); paths has it by its name."""
        return self.paths['scrum_master']

    @property
    def paths(self):
        return {db: os.path.join(self.folder, name) for db, name in FILES.items()}

    def connect(self, db='scrum_master'):
        if db not in FILES:
            raise ValueError(f"not one of the Scrum Master's databases: {db!r}")
        con = sqlite3.connect(self.paths[db], timeout=30, factory=door_guard.Locked)   # THE LOCK: a data statement runs only through secure_query
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys = ON')   # a build item's request must be there (build_items.request_id REFERENCES requests)
        return door_guard.wear(con)   # THE DOOR'S GUARD: no other database

    # ---- HIS TABLES: real columns, real types, no body (made when the door opens, through the lock) -----------------------
    def make_new_tables(self):
        """His tables and their indexes made (once a door): CREATE ... IF NOT EXISTS, never a drop; then the old
        settings note, when there is one, carried into settings and deleted (_carry_settings_note), in the same step."""
        if getattr(self, '_new_made', False):
            return
        con = self.connect()
        try:
            with con:
                old = {c[1] for c in con.execute('PRAGMA table_info("work_items")')}
                if 'body' in old:   # THE OLD WORK LIST'S TABLE of the same name (an instance from before the six, 2026-10-21): kept whole under its old name, never dropped
                    con.execute('ALTER TABLE "work_items" RENAME TO "old_work_items"')
                for t in NEW.values():
                    create, indexes = new_create_sql(t)
                    con.execute(create)
                    for sql in indexes:
                        con.execute(sql)
                self._carry_settings_note(con)
            self._grow_checks(con)   # a table whose CHECK list grew since it was made: made again as the schema says, its rows copied, the old kept (never a drop)
        finally:
            con.close()
        self._new_made = True

    def _grow_checks(self, con):
        """A TABLE WHOSE CHECK LIST GREW (the owner 2026-10-24, REMOVE under a backlog request: a request's state 'removed'):
        CREATE ... IF NOT EXISTS never changes a table that is there, so a word the schema now allows in a CHECK (requests
        state IN (...)) would still be refused by the live table. Such a table is made again exactly as the schema says it,
        its rows copied over whole, its indexes on the new one; the old table stays beside it as <name>_before_<stamp>,
        never dropped (as old_work_items, 2026-10-21). -> [the tables grown]"""
        grown = []
        for t in NEW.values():
            have = {c[1] for c in con.execute(f'PRAGMA table_info("{t["name"]}")')}
            if have and set(t['columns']) - have:   # A COLUMN THE SCHEMA NOW HAS (the owner 2026-10-24, the ENVIRONMENT boxes: requests.environment): made again the same way, the old rows copied, the new column empty
                self._grow(con, t, None)
                grown.append(t['name'])
                continue
            for col, allowed in (t.get('check') or {}).items():
                row = con.execute('SELECT "sql" FROM sqlite_master WHERE "type" = ? AND "name" = ?', ('table', t['name'])).fetchone()
                live = _in_list(row['sql'], col) if row else None
                if live is not None and not set(allowed) <= set(live):
                    self._grow(con, t, col)
                    grown.append(t['name'])
                    break
        return grown

    def _grow(self, con, t, col):
        """One table made again as its schema says (CHECKs, types, keys), the rows copied whole, proven the same count, the
        children's rows still pointing at it (PRAGMA foreign_key_check), in ONE transaction that rolls back whole on any
        doubt. Foreign keys are off and legacy_alter_table on for the rename alone, so a child's REFERENCES keeps naming
        the table by its name (build_items.request_id REFERENCES requests) instead of following the old one to its
        before-name; both set back after, whatever happened. Two doors at once: the second finds it grown and does nothing."""
        name = t['name']
        before = f'{name}_before_{datetime.datetime.now().strftime("%Y%m%dT%H%M%S")}'
        con.execute('PRAGMA foreign_keys = OFF')   # outside any transaction (inside one the pragma does nothing)
        con.execute('PRAGMA legacy_alter_table = ON')
        try:
            con.execute('BEGIN IMMEDIATE')
            try:
                again = con.execute('SELECT "sql" FROM sqlite_master WHERE "type" = ? AND "name" = ?', ('table', name)).fetchone()
                old_cols = [c[1] for c in con.execute(f'PRAGMA table_info("{name}")')]
                done = (not (set(t['columns']) - set(old_cols))) if col is None else (again is not None and set(t['check'][col]) <= set(_in_list(again['sql'], col) or ()))
                if again is None or done:
                    con.execute('COMMIT')   # grown by another door while this one waited
                    return
                # =============================================================================
                # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
                # =============================================================================
                # Secure count query
                secure_count_query, secure_count_params = secure_query(f'SELECT count(*) FROM "{name}"')
                was = con.execute(secure_count_query, secure_count_params).fetchone()[0]
                # =============================================================================
                # FROST SECURITY LOCK
                # =============================================================================
                for (idx,) in con.execute('SELECT "name" FROM sqlite_master WHERE "type" = ? AND "tbl_name" = ? AND "sql" IS NOT NULL', ('index', name)).fetchall():
                    con.execute(f'DROP INDEX "{idx}"')   # the named indexes go to the new table (a name is one in the file); the kept table is an archive
                con.execute(f'ALTER TABLE "{name}" RENAME TO "{before}"')
                create, indexes = new_create_sql(t)
                con.execute(create)
                for sql in indexes:
                    con.execute(sql)
                cols = ', '.join(f'"{c}"' for c in t['columns'] if c in old_cols)   # a column new to the schema starts empty
                # =============================================================================
                # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
                # =============================================================================
                # Secure count query
                secure_count_query, secure_count_params = secure_query(f'INSERT INTO "{name}" ({cols}) SELECT {cols} FROM "{before}"')
                con.execute(secure_count_query, secure_count_params)
                secure_count_query, secure_count_params = secure_query(f'SELECT count(*) FROM "{name}"')
                now = con.execute(secure_count_query, secure_count_params).fetchone()[0]
                # =============================================================================
                # FROST SECURITY LOCK
                # =============================================================================
                if now != was:
                    raise sqlite3.IntegrityError(f'{name}: {was} rows before, {now} copied: not grown')
                bad = con.execute('PRAGMA foreign_key_check').fetchall()
                if bad:
                    raise sqlite3.IntegrityError(f'{name}: {len(bad)} child row(s) would point nowhere: not grown')
                con.execute('COMMIT')
            except BaseException:
                con.execute('ROLLBACK')
                raise
        finally:
            con.execute('PRAGMA legacy_alter_table = OFF')
            con.execute('PRAGMA foreign_keys = ON')

    @staticmethod
    def _carry_settings_note(con):
        """SETTINGS OUT OF NOTES, ONCE (the owner 2026-10-21): the old settings note (the notes row of day SETTINGS_DAY,
        {"kind": "setting", "values": {name: {"value", "at"}}}) carried into settings, each name kept unless settings
        has it newer, and that notes row deleted, in the caller's one transaction. A note that does not read whole is
        carried as nothing and deleted all the same (a guess is never kept). -> how many names were carried"""
        # =============================================================================
        # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
        # =============================================================================
        # Secure count query
        secure_count_query, secure_count_params = secure_query('SELECT "text" FROM "notes" WHERE "day" = ?', params=(SETTINGS_DAY,))
        found = con.execute(secure_count_query, secure_count_params).fetchall()
        # =============================================================================
        # FROST SECURITY LOCK
        # =============================================================================
        if not found:
            return 0
        try:
            got = json.loads(found[0][0] or '{}')
        except ValueError:
            got = {}
        values = got.get('values') if isinstance(got, dict) and got.get('kind') == SETTING else None
        carried = 0
        for name, one in sorted((values or {}).items()):
            if not (SETTING_NAME.fullmatch(str(name)) and isinstance(one, dict) and one.get('at')):
                continue
            # =============================================================================
            # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
            # =============================================================================
            # Secure count query
            secure_count_query, secure_count_params = secure_query(
                'INSERT INTO "settings" ("name", "value", "at") VALUES (?, ?, ?) ON CONFLICT ("name") DO UPDATE SET '
                '"value" = excluded."value", "at" = excluded."at" WHERE excluded."at" >= "settings"."at"',
                params=(str(name), json.dumps(one.get('value'), ensure_ascii=False), str(one['at'])))
            carried += con.execute(secure_count_query, secure_count_params).rowcount
            # =============================================================================
            # FROST SECURITY LOCK
            # =============================================================================
        # =============================================================================
        # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
        # =============================================================================
        # Secure count query
        secure_count_query, secure_count_params = secure_query('DELETE FROM "notes" WHERE "day" = ?', params=(SETTINGS_DAY,))
        con.execute(secure_count_query, secure_count_params)
        # =============================================================================
        # FROST SECURITY LOCK
        # =============================================================================
        return carried

    def _new_write(self, sql, params):
        self.make_new_tables()
        con = self.connect()
        try:
            with con:
                # =============================================================================
                # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
                # =============================================================================
                # Secure count query
                secure_count_query, secure_count_params = secure_query(sql, params=params)
                return con.execute(secure_count_query, secure_count_params).rowcount
                # =============================================================================
                # FROST SECURITY LOCK
                # =============================================================================
        finally:
            con.close()

    def _new_read(self, table, filters, extra='', extra_params=()):
        self.make_new_tables()
        t = NEW[table]
        where = [f'"{c}" = ?' for c in filters] + ([extra] if extra else [])
        sql = f'SELECT * FROM "{table}"' + (' WHERE ' + ' AND '.join(where) if where else '') + f' ORDER BY "{t["order"]}", rowid'
        con = self.connect()
        try:
            # =============================================================================
            # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
            # =============================================================================
            # Secure count query
            secure_count_query, secure_count_params = secure_query(sql, params=list(filters.values()) + list(extra_params))
            return [dict(r) for r in con.execute(secure_count_query, secure_count_params).fetchall()]
            # =============================================================================
            # FROST SECURITY LOCK
            # =============================================================================
        finally:
            con.close()

    def _upsert(self, table, values):
        """Written, or the row with this key changed in place (INSERT ... ON CONFLICT of its UNIQUE key)."""
        t = NEW[table]
        names = list(values)
        rest = [c for c in names if c not in t['unique']]
        sql = (f'INSERT INTO "{table}" (' + ', '.join(f'"{c}"' for c in names) + ') VALUES (' + ', '.join('?' for _ in names) + ')'
               + ' ON CONFLICT (' + ', '.join(f'"{c}"' for c in t['unique']) + ') DO '
               + ('UPDATE SET ' + ', '.join(f'"{c}" = excluded."{c}"' for c in rest) if rest else 'NOTHING'))
        return self._new_write(sql, [values[c] for c in names])

    def _insert(self, table, values, ignore=False):
        names = list(values)
        sql = (f'INSERT {"OR IGNORE " if ignore else ""}INTO "{table}" (' + ', '.join(f'"{c}"' for c in names) + ') VALUES ('
               + ', '.join('?' for _ in names) + ')')
        return self._new_write(sql, [values[c] for c in names])

    def run(self, row, started, ended, state, text):
        """EVERY ROW: one line per run (green, red or running), upserted on row + started."""
        self._upsert('row_runs', {'row': int(row), 'started': started, 'ended': ended, 'state': state, 'text': one_line(cut(text))})

    def item(self, id, row, title, state, found, closed=None):   # noqa: A002 (the owner's column name)
        """THE FIX ROWS: a work item (open or closed), upserted on its id."""
        self._upsert('work_items', {'id': str(id), 'row': int(row), 'title': one_line(cut(title)), 'state': state, 'found': found, 'closed': closed})

    def turn(self, item_id, turn, result):
        """THE FIX ROWS: turn n on an item, one line (never a transcript). A turn n kept already: sqlite3.IntegrityError."""
        self._insert('work_turns', {'item_id': str(item_id), 'turn': int(turn), 'result': one_line(cut(result))})

    # ---- BUILD ITEMS A AND B (the owner's spec 2026-10-21, section 2) -----------------------------------------------
    def _next_id(self, con, table, prefix):
        """The next id of a table of R-NNNN or B-NNNN ids, in the caller's transaction (never reused: one past the
        highest kept). -> 'R-0007'"""
        # =============================================================================
        # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
        # =============================================================================
        # Secure count query
        secure_count_query, secure_count_params = secure_query(f'SELECT MAX(CAST(substr("id", 3) AS INTEGER)) FROM "{table}"', params=())
        top = con.execute(secure_count_query, secure_count_params).fetchone()[0]
        # =============================================================================
        # FROST SECURITY LOCK
        # =============================================================================
        return f'{prefix}-{int(top or 0) + 1:04d}'

    def request_environment(self, id, where):
        """WHERE THE WORK GOES (the owner 2026-10-24: "Environment / localhost rnd | pf / production rnd | pf / agent larryd
        (if agent) ... this is where the work will go and the agent then knows the environment"): the boxes he left
        checked on his page, a JSON list of their keys, on one request. -> True when a request took it"""
        self.make_new_tables()
        con = self.connect()
        try:
            with con:
                # Secure count query
                secure_count_query, secure_count_params = secure_query('UPDATE "requests" SET "environment" = ? WHERE "id" = ?', params=(json.dumps(list(where)), id))
                return con.execute(secure_count_query, secure_count_params).rowcount == 1
        finally:
            con.close()

    def request_add(self, words, source, ref=None, asked_at=None, state='asked', tests=None):
        """ONE REQUEST (A), TAKEN IN ONCE: his words exactly as given (never edited, never shortened, never cut), its
        hash the sha256 of (source, words, asked_at) (request_hash): a line taken twice writes nothing. Its id the next
        R-NNNN, its position the next (build order: arrival), state `state` (asked) since now, its tests folder
        ~/scratch/tests/requests/<id>/ unless given; tests_sha empty until the freeze. In one transaction.
        -> the new id, or None when the same request is kept already"""
        if not isinstance(words, str) or not words.strip():
            raise ValueError('a request is his words: a text, never empty')
        asked_at = asked_at or stamp()
        digest = request_hash(source, words, asked_at)
        self.make_new_tables()
        con = self.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            # =============================================================================
            # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
            # =============================================================================
            # Secure count query
            secure_count_query, secure_count_params = secure_query('SELECT "id" FROM "requests" WHERE "hash" = ?', params=(digest,))
            kept = con.execute(secure_count_query, secure_count_params).fetchone()
            # =============================================================================
            # FROST SECURITY LOCK
            # =============================================================================
            if kept:
                con.rollback()
                return None
            mine = self._next_id(con, 'requests', 'R')
            # =============================================================================
            # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
            # =============================================================================
            # Secure count query
            secure_count_query, secure_count_params = secure_query(
                'INSERT INTO "requests" ("id", "words", "hash", "source", "ref", "asked_at", "position", "state", "state_at", "tests") '
                'VALUES (?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX("position"), 0) + 1 FROM "requests"), ?, ?, ?)',
                params=(mine, words, digest, source, one_line(ref), asked_at, state, stamp(), one_line(tests) or request_tests(mine)))
            con.execute(secure_count_query, secure_count_params)
            # =============================================================================
            # FROST SECURITY LOCK
            # =============================================================================
            con.commit()
            return mine
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    REQUEST_MORE = ('tests', 'tests_sha', 'commits', 'done_at')

    def request_update(self, id, words, at=None):   # noqa: A002 (the owner's column name)
        """HIS UPDATE TO A REQUEST (the owner 2026-10-24: "a new text input box should be under the description to say
        update if i look and dont see anythign"): his new words exactly as typed, added under the words before them as
        "UPDATE <moment>: <his words>"; the words before are never edited; the hash stays the first ask's.
        -> rows changed (0: no such id, or removed)"""
        if not isinstance(words, str) or not words.strip():
            raise ValueError('an update is his words: a text, never empty')
        moment = (at or stamp())[:16].replace('T', ' ')
        return self._new_write('UPDATE "requests" SET "words" = "words" || ? WHERE "id" = ? AND "state" IS NOT ?',
                               [f'\n\nUPDATE {moment}: {words.strip()}', str(id), 'removed'])

    def request_state(self, id, state, why=None, at=None, by=None, **more):   # noqa: A002 (the owner's column name)
        """A REQUEST'S STATE CHANGED: its state, state_at (now, or at) and why (one line, a machine fact; None clears
        it), and any of tests, tests_sha, commits (a list: kept as JSON), done_at with it; by: who changed it, for the
        state log, when the caller knows (the owner's own press). -> rows changed (0: no such id)"""
        bad = set(more) - set(self.REQUEST_MORE)
        if bad:
            raise ValueError(f'not a column a state change sets: {sorted(bad)}')
        values = {'state': state, 'state_at': at or stamp(), 'why': one_line(why)}
        for k, v in more.items():
            values[k] = json.dumps(list(v), ensure_ascii=False) if k == 'commits' and v is not None else (one_line(v) if k == 'tests' else v)
        sql = 'UPDATE "requests" SET ' + ', '.join(f'"{c}" = ?' for c in values) + ' WHERE "id" = ?'
        params = list(values.values()) + [str(id)]
        if state in REOPENS and not str(by or '').startswith('the owner, '):   # HIS APPROVE IS THE DECISION (the owner approved R-0045 at 20:45 2026-10-24; a session's hired read at 22:53 put it back to building): only his own press on his page (UPDATE, REOPEN, REJECT) opens a request he approved or closed again
            sql += ' AND "state" NOT IN (' + ', '.join('?' for _ in CLOSED_BY_HIM) + ')'
            params.extend(CLOSED_BY_HIM)
        if state != 'removed':   # REMOVED IS FINAL (the owner 2026-10-24, REMOVE on a request being built: "the remove buttons are not working here"): once he removed it, no turn of the Developer, no round, writes a state over it; the write finds no row and says 0
            sql += ' AND "state" IS NOT ?'
            params.append('removed')
        changed = self._new_write(sql, params)
        if changed:
            state_said(str(id), state, values['why'], values['state_at'], by)
        return changed

    def request_first(self, id):   # noqa: A002 (the owner's column name)
        """THE OWNER PUTS A REQUEST FIRST (the owner 2026-10-21: R-0007 first, tonight): its position 1, every other
        request one place down, their order kept. -> rows changed"""
        rows = [r for r in self.requests() if r['id'] != str(id)]
        changed = self._new_write('UPDATE "requests" SET "position" = ? WHERE "id" = ?', [1, str(id)])
        for n, r in enumerate(rows, 2):
            self._new_write('UPDATE "requests" SET "position" = ? WHERE "id" = ?', [n, r['id']])
        return changed

    def requests(self, state=None, source=None):
        """The requests in build order (position). -> [dict]"""
        return self._new_read('requests', {k: v for k, v in (('state', state), ('source', source)) if v is not None})

    def request(self, id):   # noqa: A002
        """One request by its id. -> dict or None"""
        return next(iter(self._new_read('requests', {'id': str(id)})), None)

    def build_item_add(self, request_id, found_by, rule, evidence, file=None, state='open', at=None):
        """ONE BUILD ITEM (B) UNDER ITS REQUEST: the next B-NNNN; a request_id that is no request's is refused
        (sqlite3.IntegrityError: FOREIGN KEY). turns 0, approach 1. In one transaction. -> the new id"""
        self.make_new_tables()
        con = self.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            mine = self._next_id(con, 'build_items', 'B')
            # =============================================================================
            # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
            # =============================================================================
            # Secure count query
            secure_count_query, secure_count_params = secure_query(
                'INSERT INTO "build_items" ("id", "request_id", "found_by", "rule", "evidence", "file", "state", "state_at") VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                params=(mine, str(request_id), found_by, one_line(rule), one_line(evidence), one_line(file), state, at or stamp()))
            con.execute(secure_count_query, secure_count_params)
            # =============================================================================
            # FROST SECURITY LOCK
            # =============================================================================
            con.commit()
            return mine
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def build_item_state(self, id, state, turns=None, approach=None, at=None):   # noqa: A002
        """A BUILD ITEM'S STATE CHANGED (state_at now, or at), its turns and approach with it when given. -> rows changed"""
        values = {'state': state, 'state_at': at or stamp()}
        values.update({k: int(v) for k, v in (('turns', turns), ('approach', approach)) if v is not None})
        sql = 'UPDATE "build_items" SET ' + ', '.join(f'"{c}" = ?' for c in values) + ' WHERE "id" = ?'
        return self._new_write(sql, list(values.values()) + [str(id)])

    def build_items(self, request_id=None, state=None):
        """The build items (of one request, of one state), by id. -> [dict]"""
        return self._new_read('build_items', {k: v for k, v in (('request_id', request_id), ('state', state)) if v is not None})

    def build_turn(self, item_id, turn, approach, result, at=None):
        """A TURN ON AN R OR A B: one line (what changed, what the proof said). The same turn of the same approach
        twice: sqlite3.IntegrityError."""
        self._insert('build_turns', {'item_id': str(item_id), 'turn': int(turn), 'approach': int(approach), 'at': at or stamp(),
                                     'result': one_line(cut(result))})

    def build_close(self, item_id, turn, approach, result, lesson_row, lesson, at=None):
        """A B CLOSED AND ITS LESSON KEPT IN ONE TRANSACTION (row 023 SELF HEALING, law 4): its closing turn (build_turn),
        its state 'closed' (build_item_state) and its lesson (lesson: the same lesson of the same row kept once), all
        three or none: a failed write never leaves a closed B without its lesson. -> True when the lesson is new"""
        when = at or stamp()
        self.make_new_tables()
        con = self.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            # =============================================================================
            # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
            # =============================================================================
            q, a = secure_query('INSERT INTO "build_turns" ("item_id", "turn", "approach", "at", "result") VALUES (?, ?, ?, ?, ?)',
                                params=(str(item_id), int(turn), int(approach), when, one_line(cut(result))))
            con.execute(q, a)
            q, a = secure_query('UPDATE "build_items" SET "state" = ?, "state_at" = ? WHERE "id" = ?', params=('closed', when, str(item_id)))
            if con.execute(q, a).rowcount != 1:
                raise ValueError(f'{item_id}: no such build item (nothing written)')
            q, a = secure_query('INSERT OR IGNORE INTO "lessons" ("row", "lesson", "at") VALUES (?, ?, ?)',
                                params=(int(lesson_row), one_line(cut(lesson)), when))
            fresh = con.execute(q, a).rowcount == 1
            # =============================================================================
            # FROST SECURITY LOCK
            # =============================================================================
            con.commit()
            return fresh
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def build_turns(self, item_id=None):
        """The turns (of one R or B), oldest first. -> [dict]"""
        return self._new_read('build_turns', {} if item_id is None else {'item_id': str(item_id)})

    # ---- A TABLE THAT IS NO LONGER HIS (work_items, work_turns: the owner's spec 2026-10-21, 2.5) ----
    def old_rows(self, table):
        """Every row of a table his schema no longer holds, read whole (for its archive). -> [dict] ([] when gone)"""
        if table in NEW or not re.fullmatch(r'[a-z_]+', table):
            raise ValueError(f'one of his tables, or no table name: {table!r}')
        con = self.connect()
        try:
            if not con.execute('SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?', ('table', table)).fetchone():
                return []
            # =============================================================================
            # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
            # =============================================================================
            # Secure count query
            secure_count_query, secure_count_params = secure_query(f'SELECT * FROM "{table}" ORDER BY rowid', params=())
            return [dict(r) for r in con.execute(secure_count_query, secure_count_params).fetchall()]
            # =============================================================================
            # FROST SECURITY LOCK
            # =============================================================================
        finally:
            con.close()

    def drop_old(self, table):
        """A table his schema no longer holds, dropped (after its archive was read back equal). Never one of his. -> True when it was there"""
        if table in NEW or not re.fullmatch(r'[a-z_]+', table):
            raise ValueError(f'one of his tables, or no table name: {table!r}')
        con = self.connect()
        try:
            with con:
                there = bool(con.execute('SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?', ('table', table)).fetchone())
                con.execute(f'DROP TABLE IF EXISTS "{table}"')
            return there
        finally:
            con.close()

    def finding(self, row, place, file, line, severity, state):
        """THE CHECK ROWS: a finding, upserted on row + place + file + line (its severity and state changed in place)."""
        self._upsert('findings', {'row': int(row), 'place': one_line(place), 'file': one_line(file), 'line': int(line),
                                  'severity': one_line(severity), 'state': state})

    def lesson(self, row, lesson, at):
        """23 SELF HEALING: a lesson learned; the same lesson of the same row kept once. -> True when new."""
        return self._insert('lessons', {'row': int(row), 'lesson': one_line(cut(lesson)), 'at': at}, ignore=True) == 1

    def note(self, day, text):
        """01 SUMMARY, 02 STANDUP: the day's note, upserted on the day (never SETTINGS_DAY: settings have their own table)."""
        if day == SETTINGS_DAY:
            raise ValueError('a setting is a row of settings (st.setting), never a note')
        self._upsert('notes', {'day': day, 'text': cut(text)})

    def runs(self, row=None, day=None):
        """The row runs (of one row, of one day by their start), oldest first."""
        f = {} if row is None else {'row': int(row)}
        if day is None:
            return self._new_read('row_runs', f)
        return self._new_read('row_runs', f, '"started" >= ? AND "started" < ?', (day, day + '~'))   # the day's starts: an index range

    def items(self, state=None, row=None):
        f = {k: v for k, v in (('state', state), ('row', None if row is None else int(row))) if v is not None}
        return self._new_read('work_items', f)

    def turns(self, item_id):
        return self._new_read('work_turns', {'item_id': str(item_id)})

    def findings(self, row=None, state=None):
        f = {k: v for k, v in (('row', None if row is None else int(row)), ('state', state)) if v is not None}
        return self._new_read('findings', f)

    def lessons(self, row=None):
        return self._new_read('lessons', {} if row is None else {'row': int(row)})

    def notes(self, day=None):
        return self._new_read('notes', {} if day is None else {'day': day})

    # ---- SETTINGS: every value changed at run time, one row a name, newest wins (settings.json: the defaults) ----------
    def setting(self, name, value, at=None):
        """ONE VALUE CHANGED AT RUN TIME, kept under its name (a dotted place in settings.json: 'switches.worker',
        'develop.worker.session', 'memory.rulebook') as a row of settings, its value JSON, in one statement (no reader
        sees half, no two writers lose one another's names). value None: taken away (kept as JSON null), the default
        stands again. A value kept with a newer `at` than this one stays (newest wins). -> True when kept"""
        name = str(name)
        if not SETTING_NAME.fullmatch(name):
            raise ValueError(f'not a setting name: {name!r}')
        at = at or stamp()
        sql = ('INSERT INTO "settings" ("name", "value", "at") VALUES (?, ?, ?) ON CONFLICT ("name") DO UPDATE SET '
               '"value" = excluded."value", "at" = excluded."at" WHERE excluded."at" >= "settings"."at"')   # every value a ? parameter (the lock)
        return self._new_write(sql, [name, json.dumps(value, ensure_ascii=False), at]) == 1

    def settings_kept(self):
        """THE VALUES CHANGED AT RUN TIME, {name: value} (a value taken away is not here: its default stands). A value
        that does not read is none kept, never a guess."""
        out = {}
        for r in self._new_read('settings', {}):
            try:
                value = json.loads(r['value'])
            except (TypeError, ValueError):
                continue
            if value is not None:
                out[r['name']] = value
        return out

    def latest_runs(self, since=None, row=None):
        """THE BOARD (row 001's summary, the page): each row's newest run, of those started at or after `since` (an ISO
        time: the day's start; None: ever). -> {row: run}"""
        f = {} if row is None else {'row': int(row)}
        found = self._new_read('row_runs', f) if since is None else self._new_read('row_runs', f, '"started" >= ?', (since,))
        out = {}
        for r in found:   # oldest first: the last one a row has is its newest
            out[r['row']] = r
        return out

    def newest_runs(self, ended=False):
        """EVERY ROW'S NEWEST RUN, ever, in one read (row 025, 2026-10-24: a row with no run since the day began is not yet
        looked at today, never green by that; its newest run overall says its light; never the whole table, 55 000 runs by
        then). ended: the newest of the runs that ended (a 'running' record is not a light). -> {row: run}"""
        if ended:
            found = self._new_read('row_runs', {}, '"state" != ? AND "started" IN (SELECT max("started") FROM "row_runs" WHERE "state" != ? GROUP BY "row")', ('running', 'running'))
        else:
            found = self._new_read('row_runs', {}, '"started" IN (SELECT max("started") FROM "row_runs" GROUP BY "row")')
        out = {}
        for r in found:   # oldest first: the last one a row has is its newest (another row's newest moment may be one of its older starts)
            out[r['row']] = r
        return out

    def red_since(self, row):
        """HOW LONG A ROW HAS BEEN RED (the owner 2026-10-21: "a little timer behind each red"): the start of the first
        red run of its unbroken red streak, its newest runs read back to the last run that was not red ('running' runs
        are passed over). -> an ISO time, or None when its newest ended run is not red"""
        since = None
        for r in reversed(self.runs(row=row)):
            if r.get('state') == 'running':
                continue
            if r.get('state') != 'red':
                break
            since = r.get('started')
        return since

    def open_items(self, row=None):
        """The open work items (of one row). -> [item]"""
        return self.items(state='open', row=row)

    def table_rows(self, table):
        """Every row of one of his tables, in its readers' order (the word pass reads them whole). -> [dict]"""
        if table not in NEW:
            raise ValueError(f"not one of the Scrum Master's tables: {table!r}")
        return self._new_read(table, {})

    def replace(self, table, key, values):
        """ONE ROW OF THE SEVEN CHANGED IN PLACE (the word pass): the row with this whole key gets these values; a value
        that makes its key another row's is refused (sqlite3.IntegrityError), never merged. -> how many rows changed"""
        t = NEW.get(table)
        if t is None:
            raise ValueError(f"not one of the Scrum Master's tables: {table!r}")
        if set(key) != set(t['unique']) or not values or not set(values) <= set(t['columns']):
            raise ValueError(f'{table}: its whole key {t["unique"]} and columns of its own')
        sql = (f'UPDATE "{table}" SET ' + ', '.join(f'"{c}" = ?' for c in values) + ' WHERE ' + ' AND '.join(f'"{c}" = ?' for c in key))
        return self._new_write(sql, [one_line(v) if c in t.get('one_line', ()) else v for c, v in values.items()] + list(key.values()))


    # ---- LOGS: files, never rows, OUTSIDE ~/virtual_sanity (the owner 2026-10-21: "why wouldnt logs be in the reports
    # folder outside this"): reports.json logs, or $SCRUM_MASTER_LOGS for checks. No secrets. ----
    def log_path(self, *parts):
        """A log under the logs folder outside sanity (its folder made): log_path('daily', day, 'AUDIT.log')."""
        return self._under(LOGS, parts, 0o755)

    # ---- THE ONE PATH UNDER HIS LOGS --------------------------------------------------------------------------------
    def _under(self, top, parts, mode):
        base = top if os.path.isabs(top) else os.path.join(self.folder, top)
        path = os.path.abspath(os.path.join(base, *parts))
        if not path.startswith(base + os.sep):
            raise ValueError(f'{path} is not under {base}')
        os.makedirs(os.path.dirname(path), mode=mode, exist_ok=True)
        return path


# ---- THE ROW CONTRACT (CONTRACT.md, 2026-10-21): every row file agentNNN_*.py is its own program -----------------------
#     def check(): -> (state, text)        state green | red | running, text one line (cut to 500)
#     if __name__ == '__main__':
#         sys.exit(store.row_main(NNN, check, sys.argv[1:], more={'run': run}))   # more: the row's other subcommands
# python -m agent.agentNNN_x check runs check() once and writes its run (row_runs) through run_check below.
STATES = ('green', 'red', 'running')


def stamp():
    """Now, as a run's time is kept: local, with its offset, to the second (2026-10-21T08:05:03-04:00)."""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec='seconds')


REQUEST_TESTS = os.path.expanduser('~/scratch/tests/requests')   # THE HOME OF EVERY REQUEST'S TESTS (the owner's spec 2026-10-21, 2.1): <here>/<id>/


def request_tests(rid):
    """A request's tests folder: ~/scratch/tests/requests/<id>/ (the spec's own form, a slash at its end)."""
    return os.path.join(REQUEST_TESTS, str(rid)) + os.sep


def request_hash(source, words, asked_at):
    """THE REQUEST'S HASH (the owner's spec 2026-10-21, 2.1): sha256 of (source, words, asked_at), the three as one
    JSON list (UTF-8, as written): one request is taken in once. -> 64 hex"""
    return hashlib.sha256(json.dumps([source, words, asked_at], ensure_ascii=False).encode('utf-8')).hexdigest()


def as_run(got):
    """A check's answer as a run keeps it: (state, text), the state one of STATES, the text one line of at most 500.
    Anything else is red, never a pass. -> (state, text)"""
    try:
        state, said = got
    except (TypeError, ValueError):
        return 'red', one_line(f'the check gave no (state, text): {got!r}')[:500]
    said = one_line(cut(said)) or ''
    if state not in STATES:
        return 'red', (f'the check gave no state of {"/".join(STATES)}: {state!r} · ' + said)[:500]
    return state, (said or state)[:500]


def run_check(row, check, st=None, now=stamp):
    """ONE RUN OF A ROW: 'running' written at its start, then its answer (a check that raises is red: he could not read
    it). -> (state, text) as kept"""
    st = st or door()
    started = now()
    st.run(row, started, None, 'running', 'running')
    try:
        state, said = as_run(check())
    except Exception as e:   # a row never dies silently: what broke is its red line
        state, said = 'red', one_line(f'he could not read it: {type(e).__name__}: {e}')[:500]
    st.run(row, started, now() if state != 'running' else None, state, said)
    return state, said


def row_main(row, check, argv, more=None):
    """A ROW'S MAIN: `check` runs check() once and writes its run; `more` names the row's other subcommands
    ({name: fn(argv) -> exit code}). -> the exit code (0 green or running, 1 red, 2 no such subcommand)"""
    if argv[:1] == ['check']:
        from agent import shared_chunks as chunks   # THE 3 MINUTE RULE (the owner 2026-10-23): every row's red says his step, or is held while a run clears it
        state, said = run_check(row, chunks.wrap(row, check))
        print(f'{stamp()[:16]} · row {int(row):03d} · {state} · {said}', flush=True)
        return 1 if state == 'red' else 0
    if more and argv[:1] and argv[0] in more:
        return more[argv[0]](argv[1:])
    print(f'usage: python -m <row module> check' + ''.join(f' | {n}' for n in (more or {})))
    return 2


_DOORS = {}   # one door a database file: Store() makes its tables once, not at every read


def door():
    """THE ONE DATABASE DOOR (moved here from shared_where, 2026-10-21): one Store a database file, the office's own
    instance ($SCRUM_MASTER_INSTANCE: a check's scratch instance), made again when its file is gone."""
    st = _DOORS.get(instance())
    if st is None or not os.path.isfile(st.path):
        st = _DOORS[instance()] = Store()
    return st
