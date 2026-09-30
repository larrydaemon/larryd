"""DATA STAYS IN wid, NEVER BACK TO PF HANZO (the owner, 2026-09-28). hanzo.db holds only what HANZO itself needs: the
locker (key, hashes, manifest's name, folder), hanzo_runs (lane, the agent's key, job key, run, state, times, charged,
a plain reason) and hanzo_developers (a developer's HANZO-side name and the card keys they may submit). The inputs of a run live in memory and in its run folder (removed after); its result goes back to wid
and is not kept. A failed agent's words never reach a reason: only the kind of failure."""
import json
import pathlib
import shutil
import sqlite3
import tempfile
import unittest

from _here import APP
from core_engine import harness, locker, sandbox, store

ALLOWED = {'hanzo_locker': ['agent_key', 'name', 'folder', 'code_sha256', 'manifest_sha256', 'registered_at'],
           'hanzo_runs': ['id', 'lane', 'agent_key', 'job_key', 'run', 'state', 'reason', 'started_at', 'finished_at', 'charged'],
           'hanzo_developers': ['agent_key', 'developer', 'added_at']}   # a developer's HANZO-side name and the card keys they may submit
PLANTED = 'Zanzibar-7731-private-pitch'   # a value only the input records carry


class Recorder:
    """What the platform is told (in this process, never a server): the results, the charge. Nothing answers for the platform here."""
    def __init__(self):
        self.said = []

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return (200, {'charged': 0, 'free': True}) if route == '/mtok/use' else (200, {'saved': True})


class NoDataKept(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.instance = pathlib.Path(self.tmp.name) / 'instance'
        self.instance.mkdir()
        self.agents = pathlib.Path(self.tmp.name) / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace')
        self.db = store.open_store(self.instance)
        locker.add(self.db, self.agents, 'MAGT_SCRATCH00001_0001', 'marketplace')

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_tables_hold_only_what_hanzo_needs(self):
        con = sqlite3.connect(self.db)
        got = {t: [r[1] for r in con.execute(f'PRAGMA table_info("{t}")')] for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        con.close()
        self.assertEqual(got, ALLOWED)

    def test_an_older_table_is_refused_not_kept(self):
        with tempfile.TemporaryDirectory() as d:
            con = sqlite3.connect(pathlib.Path(d) / 'hanzo.db')
            con.execute('CREATE TABLE hanzo_runs (id INTEGER PRIMARY KEY, lane TEXT, account TEXT, member TEXT, delivery_sha256 TEXT)')
            con.close()
            with self.assertRaises(SystemExit):
                store.open_store(d)

    def test_a_full_run_keeps_no_input_value(self):
        card = {'key': 'MAGT_SCRATCH00001_0001', 'number': '1', 'class': 'MARK II SUPER AGENT (HARNESS)', 'name': 'Planted Name ' + PLANTED,
                'screen': 'larryd/agnt/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents', 'pitch': PLANTED,
                'developer': PLANTED, 'price': '0', 'image_dam_key': '', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'status': 'LIVE'}
        hired = [{'agent_key': card['key'], 'board': card['screen'], 'shell_id': 1, 'on': True, 'job_key': 'MJOB_SCRATCH00001_0001'}]
        client = Recorder()
        h = harness.Harness(self.db, self.agents, client)
        h.facts = lambda account, scope, member: ([card], hired, [], lambda key: (True, ''))   # the platform's word, as it would answer
        self.assertEqual(h.run_job('ACCT_' + 'A' * 12 + '_0001', 'SCRATCH', 'MCON_' + 'B' * 12 + '_0002', 'MJOB_SCRATCH00001_0001', 1), 'DONE')
        delivered = [d for _o, route, d in client.said if route == '/jobs/result' and d['state'] == 'DONE'][0]['delivery']
        self.assertEqual(delivered, '1 agent in the collection · 1 hired')   # the result went back to wid
        for path in pathlib.Path(self.tmp.name, 'instance').rglob('*'):
            if path.is_file():
                body = path.read_bytes()
                for value in (PLANTED, 'agent in the collection', 'ACCT_' + 'A' * 12, 'MCON_' + 'B' * 12):
                    self.assertNotIn(value.encode(), body, f'{path.name} keeps {value!r}')
        self.assertEqual(list(pathlib.Path(tempfile.gettempdir()).glob('hanzo_run_*')), [])   # the run's folder is gone

    def test_a_failed_agents_words_never_reach_a_reason(self):
        folder = self.agents / 'talker'
        folder.mkdir()
        (folder / 'agent.py').write_text('import json, sys\nraise ValueError("leaked " + json.load(sys.stdin)["secret"])\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {'secret': PLANTED})
        self.assertEqual((state, reason), ('FAILED', 'ValueError'))
        folder2 = self.agents / 'reader'
        folder2.mkdir()
        (folder2 / 'agent.py').write_text(f'open("/Users/{PLANTED}.txt")\n')
        reason = sandbox.run(folder2, 'agent.py', {})[2]
        self.assertEqual(reason, 'FileNotFoundError: [Errno 2] No such file or directory')   # the system's fixed words; the path (the value) never
        self.assertNotIn(PLANTED, reason)


if __name__ == '__main__':
    unittest.main()
