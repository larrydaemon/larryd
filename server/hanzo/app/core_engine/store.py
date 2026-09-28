"""hanzo.db, HANZO's only database, created from schemas/store.json and nothing else; a table that differs is refused."""
import json
import pathlib
import sqlite3

SCHEMA = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'schemas' / 'store.json').read_text())


def open_store(instance):
    path = str(pathlib.Path(instance) / SCHEMA['database'])
    con = sqlite3.connect(path)
    try:
        for name, table in SCHEMA['tables'].items():
            con.execute(f'CREATE TABLE IF NOT EXISTS "{name}" (' + ', '.join(f'"{c}" {kind}' for c, kind in table['columns']) + ')')
            have = [r[1] for r in con.execute(f'PRAGMA table_info("{name}")')]
            if have != [c for c, _kind in table['columns']]:
                raise SystemExit(f'hanzo.db: {name} is not the schema\'s ({have}); HANZO refuses to keep it')
        con.commit()
    finally:
        con.close()
    return path


def counts(path):
    con = sqlite3.connect(path)
    try:
        return {'locker': con.execute('SELECT COUNT(*) FROM hanzo_locker').fetchone()[0],
                'runs': con.execute('SELECT COUNT(*) FROM hanzo_runs').fetchone()[0]}
    finally:
        con.close()
