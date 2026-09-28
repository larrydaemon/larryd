import json
import sqlite3
import tempfile
import unittest

from _here import APP
from core_engine import store


class StoreTest(unittest.TestCase):
    def test_tables_are_exactly_the_schema(self):
        schema = json.loads((APP / 'schemas' / 'store.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            path = store.open_store(d)
            con = sqlite3.connect(path)
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            self.assertEqual(tables, set(schema['tables']))
            for name, table in schema['tables'].items():
                cols = [r[1] for r in con.execute(f'PRAGMA table_info("{name}")')]
                self.assertEqual(cols, [c[0] for c in table['columns']])
            con.close()

    def test_database_name(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(store.open_store(d).endswith('/hanzo.db'))

    def test_counts_are_rows(self):
        with tempfile.TemporaryDirectory() as d:
            path = store.open_store(d)
            self.assertEqual(store.counts(path), {'locker': 0, 'runs': 0})
            con = sqlite3.connect(path)
            con.execute("INSERT INTO hanzo_runs (lane, agent_key, state, started_at) VALUES ('call','K','REFUSED','t')")
            con.commit()
            con.close()
            self.assertEqual(store.counts(path), {'locker': 0, 'runs': 1})


if __name__ == '__main__':
    unittest.main()
