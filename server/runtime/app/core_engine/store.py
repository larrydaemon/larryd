"""agents.db, the runtime's only database, created from schemas/store.json and nothing else; a table that differs is refused, and a
table the schema retired is dropped. Its name is the schema's "database", the one place (runtime.db until 2026-11-09, the owner: "we
called the instance agents.db ... make sure its consistent please"; the same code on this Mac and in the cloud, where the file is
made anew on each start)."""
import json
import pathlib
import sqlite3

SCHEMA = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'schemas' / 'store.json').read_text())


def open_store(instance):
    path = str(pathlib.Path(instance) / SCHEMA['database'])
    con = sqlite3.connect(path)
    try:
        for name in SCHEMA.get('retired', {}).get('tables', []):   # a table the runtime no longer keeps goes, with what it held
            if name not in SCHEMA['tables']:
                con.execute(f'DROP TABLE IF EXISTS "{name}"')
        for name, table in SCHEMA['tables'].items():
            con.execute(f'CREATE TABLE IF NOT EXISTS "{name}" ({_body(table)})')
            have = [r[1] for r in con.execute(f'PRAGMA table_info("{name}")')]
            for c, kind in table['columns'][len(have):]:   # a table made before a column the schema added at its end: the column added, empty
                if have == [c0 for c0, _k in table['columns'][:len(have)]]:
                    con.execute(f'ALTER TABLE "{name}" ADD COLUMN "{c}" {kind}')
            have = [r[1] for r in con.execute(f'PRAGMA table_info("{name}")')]
            if have != [c for c, _kind in table['columns']]:
                raise SystemExit(f'agents.db: {name} is not the schema\'s ({have}); the runtime refuses to keep it')
            if _key_of(con, name) != _key(table):   # A KEY THE SCHEMA CHANGED (runtime_locker, 2026-11-22: one row per agent PER CALLER): the table made
                _rebuild(con, name, table)          # anew with the schema's key, every row copied into it exactly as it was, then the old one dropped
        con.commit()
    finally:
        con.close()
    return path


def _key(table):
    """The schema's primary key of a table: its "primary_key" columns, else the one column declared PRIMARY KEY."""
    return list(table.get('primary_key') or [c for c, kind in table['columns'] if 'PRIMARY KEY' in kind.upper()])


def _body(table):
    cols = ', '.join(f'"{c}" {kind}' for c, kind in table['columns'])
    return cols + (', PRIMARY KEY (' + ', '.join(f'"{c}"' for c in table['primary_key']) + ')' if table.get('primary_key') else '')


def _key_of(con, name):
    return [r[1] for r in sorted((r for r in con.execute(f'PRAGMA table_info("{name}")') if r[5]), key=lambda r: r[5])]


def _rebuild(con, name, table):
    """The table under the schema's key, its rows copied as they were (a copy, never an edit): a row the new key cannot hold
    twice refuses the start, nothing dropped."""
    cols = ', '.join(f'"{c}"' for c, _kind in table['columns'])
    con.execute(f'DROP TABLE IF EXISTS "{name}__rekeyed"')
    con.execute(f'CREATE TABLE "{name}__rekeyed" ({_body(table)})')
    try:
        con.execute(f'INSERT INTO "{name}__rekeyed" ({cols}) SELECT {cols} FROM "{name}"')
    except sqlite3.IntegrityError:
        con.rollback()
        raise SystemExit(f'agents.db: {name} holds rows the schema\'s key {_key(table)} cannot hold; the runtime refuses to change it')
    con.execute(f'DROP TABLE "{name}"')
    con.execute(f'ALTER TABLE "{name}__rekeyed" RENAME TO "{name}"')


def counts(path):
    con = sqlite3.connect(path)
    try:
        return {'locker': con.execute('SELECT COUNT(*) FROM runtime_locker').fetchone()[0],
                'runs': con.execute('SELECT COUNT(*) FROM runtime_runs').fetchone()[0]}
    finally:
        con.close()
