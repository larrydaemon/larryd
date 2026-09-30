"""THE INTAKE: an agent the owner approved from LARRYD's review queue (one .larryd file, a zip of agent/) goes into HANZO's
locker (dev/<card key>/) with the host's `place`, then to FROST's review as any agent goes. Every refusal is planted
here. The old signed developer door is gone, and its table is dropped from an old database. FROST is a Recorder here (in
this process: a receipt, nothing for the platform) or a silent port; what FROST answers is proven live only."""
import datetime
import hashlib
import io
import json
import pathlib
import socket
import sqlite3
import tempfile
import unittest
import zipfile

from _here import APP  # noqa: F401
from core_engine import harness, intake, locker, signing, store
from web import app as host

SECRET = 'scratch-secret-for-the-intake'
KEY = 'MAGT_00000000D001_0001'
OTHER = 'MAGT_00000000D002_0002'


def _closed_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Frost:
    """FROST as a receipt: it records what HANZO sends and answers a waiting review, and each review's word as the test
    sets it (states: {(key, code, manifest): (state, note)}); older=True is a FROST before its review_state door (404)."""
    def __init__(self, approved=(), states=None, older=False):
        self.said, self.approved, self.states, self.older = [], list(approved), dict(states or {}), older

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return 200, {'id': 1, 'state': 'waiting'}

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        if route == '/agents/review_state':
            if self.older:
                return 404, {'error': 'no route GET /agents/review_state'}
            state, note = self.states.get((data['agent_key'], data['code_sha256'], data['manifest_sha256']), ('not submitted', ''))
            return 200, {'state': state, 'note': note}
        return 200, {'approved': self.approved}


def _agent(answer='hello'):
    return {'agent.json': json.dumps({'name': 'Scratch agent', 'entry': 'agent.py', 'does': ['answer']}).encode(),
            'agent.py': f'import json, sys\njson.load(sys.stdin)\nprint(json.dumps({{"delivery": "{answer}"}}))\n'.encode()}


def _zip(files, links=()):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, body in files.items():
            z.writestr(name, body)
        for name, target in links:
            info = zipfile.ZipInfo(name)
            info.external_attr = 0o120777 << 16
            z.writestr(info, target)
    return out.getvalue()


class Intake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.instance = pathlib.Path(self.tmp.name) / 'instance'
        self.instance.mkdir()
        self.agents = pathlib.Path(self.tmp.name) / 'agents'
        self.agents.mkdir()
        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.app = host.create_app(self.instance, secret=SECRET, now=lambda: self.now, agents=self.agents)
        self.h = self.app.config['harness']
        self.frost = Frost()
        self.h.client = self.frost
        self.db = self.h.db

    def tearDown(self):
        self.tmp.cleanup()

    def place(self, files, key=KEY, links=()):
        return host.place(self.app, key, _zip(files, links))

    def refused(self, files, status=400, key=KEY, links=()):
        with self.assertRaises(SystemExit) as no:
            self.place(files, key, links)
        self.assertIn(f'refused ({status})', str(no.exception))
        return str(no.exception)

    # ---------------------------------------------------------------- place
    def test_an_approved_file_is_held_and_sent_to_frost(self):
        body = self.place(_agent())
        row = locker.held(self.db, KEY)
        self.assertEqual((body['code_sha256'], body['manifest_sha256']), (row['code_sha256'], row['manifest_sha256']))
        self.assertEqual(row['folder'], f'dev/{KEY}')
        self.assertEqual(locker.verify(self.db, self.agents, KEY), (True, ''))
        code = hashlib.sha256(b'agent.py\0' + _agent()['agent.py'] + b'\0').hexdigest()
        self.assertEqual(body['code_sha256'], code)   # the locker's recipe over exactly the file's bytes
        self.assertEqual(body['review'], {'id': 1, 'state': 'waiting'})
        office, route, sent = self.frost.said[-1]
        self.assertEqual((office, route), ('fs', '/agents/submit'))
        self.assertEqual((sent['agent_key'], sent['code_sha256'], sent['manifest_sha256'], sent['name']), (KEY, code, row['manifest_sha256'], 'Scratch agent'))

    def test_the_submit_doors_own_file_is_placed(self):
        """The exact shape LARRYD's submit door queues (larryd/bundle.py): fixed times, 0644 file modes."""
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, body in sorted(_agent().items()):
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                z.writestr(info, body)
        self.assertEqual(host.place(self.app, KEY, out.getvalue())['review']['state'], 'waiting')

    def test_a_changed_agent_replaces_the_old_one(self):
        first = self.place(_agent('one'))
        second = self.place(_agent('two'))
        self.assertNotEqual(first['code_sha256'], second['code_sha256'])
        self.assertIn(b'two', (self.agents / 'dev' / KEY / 'agent.py').read_bytes())
        self.assertEqual(sorted(p.name for p in (self.agents / 'dev').iterdir()), [KEY])   # no leftover upload
        self.assertEqual(self.place(_agent('two'))['code_sha256'], second['code_sha256'])

    def test_every_bad_file_is_refused_and_nothing_is_held(self):
        good = _agent()
        plants = {
            'a path up and out': {**good, '../escape.py': b'x'},
            'a path up inside': {**good, 'lib/../../escape.py': b'x'},
            'an absolute path': {**good, '/tmp/escape.py': b'x'},
            'a hidden file': {**good, '.env': b'x'},
            'a hidden folder': {**good, 'lib/.cache/x.py': b'x'},
            'a backslash path': {**good, 'lib\\x.py': b'x'},
            'no manifest': {'agent.py': good['agent.py']},
            'a manifest with no entry file': {'agent.json': good['agent.json']},
            'a manifest that is not JSON': {**good, 'agent.json': b'{'},
            'no files': {},
        }
        for name, files in plants.items():
            with self.subTest(name):
                self.refused(files)
        with self.subTest('a link'):
            self.refused(good, links=[('data.txt', '/etc/hosts')])
        with self.subTest('not a zip'):
            with self.assertRaises(SystemExit) as no:
                host.place(self.app, KEY, b'not a zip')
            self.assertIn('refused (400): not a .larryd file', str(no.exception))
        with self.subTest('not a card key'):
            self.refused(good, key='ada')
        self.assertIsNone(locker.held(self.db, KEY))
        self.assertFalse((self.agents / 'dev' / KEY).exists())
        self.assertFalse(pathlib.Path('/tmp/escape.py').exists())
        self.assertFalse((self.agents / 'escape.py').exists())

    def test_the_limits(self):
        many = {**_agent(), **{f'f{i}.txt': b'x' for i in range(200)}}
        self.assertIn('more than 200 files', self.refused(many, 413))
        big = {**_agent(), 'big.txt': b'x' * 5_000_001}
        self.assertIn('bytes', self.refused(big, 413))

    def test_a_bad_file_again_leaves_the_held_agent_as_it_was(self):
        held = self.place(_agent())
        self.refused({**_agent(), '../escape.py': b'x'})
        self.refused({'agent.json': _agent()['agent.json']})
        self.assertEqual(locker.held(self.db, KEY)['code_sha256'], held['code_sha256'])
        self.assertEqual(locker.verify(self.db, self.agents, KEY), (True, ''))

    def test_a_silent_frost_is_said_and_the_agent_stays_held(self):
        self.h.client = host.platform.Client({'fs': f'http://127.0.0.1:{_closed_port()}'}, SECRET, timeout=2)
        body = self.place(_agent())
        self.assertIn('FROST did not take it: fs does not answer; send it again with submit', body['refused'])
        self.assertEqual(body['code_sha256'], locker.held(self.db, KEY)['code_sha256'])

    # ---------------------------------------------------------------- each layer on its own (two layers each: the zip, the files)
    def test_the_zip_layer_keeps_its_own_limits(self):
        with self.assertRaises(intake.Refused) as no:
            intake.from_zip(b'x' * 101, 5, 100)
        self.assertEqual((no.exception.status, no.exception.reason), (413, 'more than 100 bytes'))
        with self.assertRaises(intake.Refused) as no:
            intake.from_zip(_zip({f'f{i}.txt': b'x' for i in range(6)}), 5, 10_000)
        self.assertEqual((no.exception.status, no.exception.reason), (413, 'more than 5 files'))
        with self.assertRaises(intake.Refused) as no:   # a bomb: small packed, big unpacked
            intake.from_zip(_zip({'big.txt': b'0' * 50_000}), 5, 10_000)
        self.assertEqual((no.exception.status, no.exception.reason), (413, 'more than 10000 bytes'))

    def test_the_file_layer_keeps_its_own_limits(self):
        with self.assertRaises(intake.Refused) as no:
            intake.check({**_agent(), **{f'f{i}.txt': b'x' for i in range(4)}}, 5, 10_000)
        self.assertEqual((no.exception.status, no.exception.reason), (413, 'more than 5 files'))
        with self.assertRaises(intake.Refused) as no:
            intake.check({**_agent(), 'big.txt': b'x' * 10_000}, 5, 10_000)
        self.assertEqual((no.exception.status, no.exception.reason), (413, 'more than 10000 bytes'))

    def test_the_write_layer_keeps_every_file_inside(self):
        with self.assertRaises(intake.Refused) as no:   # past the file layer's plain-path rule, the write itself refuses
            intake.receive(self.db, self.agents, 'dev', KEY, {**_agent(), '../escape.py': b'x'})
        self.assertEqual(no.exception.status, 400)
        self.assertFalse((self.agents / 'escape.py').exists() or (self.agents / 'dev' / 'escape.py').exists())
        self.assertIsNone(locker.held(self.db, KEY))

    # ---------------------------------------------------------------- review: what HANZO records, with FROST's word
    def test_the_review_is_counted_from_hanzo_runs(self):
        held = self.place(_agent())
        for lane, state, charged in (('job', 'DONE', 3), ('job', 'DONE', 2), ('job', 'FAILED', 0), ('call', 'DONE', 0),
                                     ('hire', 'ON', 0), ('hire', 'ON', 0), ('hire', 'OFF', 0)):
            self.h._record(lane, KEY, state, charged=charged)
        self.h._record('job', 'MAGT_00000000D003_0003', 'DONE', charged=99)   # another agent's, never in this one's counts
        self.frost.states = {(KEY, held['code_sha256'], held['manifest_sha256']): ('approved', '')}
        agents = self.h.review_state([KEY, OTHER])['agents']
        self.assertEqual([a['agent_key'] for a in agents], [KEY, OTHER])
        mine = agents[0]
        self.assertEqual({k: mine[k] for k in ('held', 'review', 'runs', 'calls', 'hires', 'unhires', 'charged')},
                         {'held': True, 'review': 'approved', 'runs': {'DONE': 2, 'FAILED': 1}, 'calls': 1, 'hires': 2, 'unhires': 1, 'charged': 5})
        self.assertEqual(agents[1]['review'], 'not submitted')
        self.frost.states = {(KEY, held['code_sha256'], held['manifest_sha256']): ('rejected', 'the manifest names no screen')}
        mine = self.h.review_state([KEY])['agents'][0]
        self.assertEqual((mine['review'], mine['note']), ('rejected', 'the manifest names no screen'))
        self.h.client = host.platform.Client({'fs': f'http://127.0.0.1:{_closed_port()}'}, SECRET, timeout=2)
        self.assertEqual(self.h.review_state([KEY])['agents'][0]['review'], 'unknown: fs does not answer')

    def test_a_frost_before_its_review_state_door_is_read_the_older_way(self):
        held = self.place(_agent())
        self.h.client = Frost(older=True, approved=[{'agent_key': KEY, 'code_sha256': held['code_sha256'], 'manifest_sha256': held['manifest_sha256']}])
        mine = self.h.review_state([KEY])['agents'][0]
        self.assertEqual((mine['review'], mine['note']), ('approved', ''))
        self.h.client = Frost(older=True)
        self.assertEqual(self.h.review_state([KEY])['agents'][0]['review'], 'not approved')

    def test_a_hire_is_a_row_with_the_agents_key_only(self):
        class Hires(harness.Harness):
            """The platform's facts given in this process (what the lanes are proven with live), to see what a hire records."""
            def facts(self, account, scope, member):
                card = {'key': KEY, 'status': 'LIVE', 'screen': 'larryd/agnt/home', 'price': '', 'product': 'LARRYD', 'product_slug': 'larryd',
                        'name': 'M', 'module': 'AGENT'}
                return [card], [], [], lambda key: (True, '')

            def marketplace_key(self):
                return KEY

            def _ask(self, office, method, route, data):
                return {'done': route}
        h = Hires(self.db, self.agents, client=None)
        h.hire('ACCT_000000000001_0001', 'SCRATCH', 'MCON_000000000002_0002', KEY, True)
        h.hire('ACCT_000000000001_0001', 'SCRATCH', 'MCON_000000000002_0002', KEY, False)
        con = sqlite3.connect(self.db)
        rows = con.execute("SELECT * FROM hanzo_runs WHERE lane = 'hire' ORDER BY id").fetchall()
        con.close()
        self.assertEqual([(r[1], r[2], r[5]) for r in rows], [('hire', KEY, 'ON'), ('hire', KEY, 'OFF')])
        self.assertNotIn('ACCT_000000000001_0001', repr(rows))
        self.assertNotIn('MCON_000000000002_0002', repr(rows))

    # ---------------------------------------------------------------- the old door is gone
    def test_the_old_developer_door_is_gone(self):
        c = self.app.test_client()
        data = {'agent_key': KEY, 'files': {}}
        at = self.now.isoformat(timespec='seconds')
        unsigned = c.post('/api/developer/submit', json=data, headers={'X-Developer': 'ada', 'X-Developer-Sig': 'x', 'X-Office-At': at})
        self.assertEqual(unsigned.status_code, 401)   # a developer's own signature opens nothing now
        signed = c.post('/api/developer/submit', json=data, headers={'X-Office': signing.sign(SECRET, '/developer/submit', data, at), 'X-Office-At': at})
        self.assertEqual(signed.status_code, 404)     # and with HANZO's own signature there is no such route
        self.assertFalse((self.instance / 'secrets' / 'developers').exists())

    def test_the_retired_table_is_dropped_from_an_old_database(self):
        old = pathlib.Path(self.tmp.name) / 'old'
        old.mkdir()
        con = sqlite3.connect(old / 'hanzo.db')
        with con:
            con.execute('CREATE TABLE hanzo_developers (agent_key TEXT PRIMARY KEY, developer TEXT NOT NULL, added_at TEXT NOT NULL)')
            con.execute("INSERT INTO hanzo_developers VALUES (?, 'ada', '2026-09-29')", (KEY,))
        con.close()
        store.open_store(old)
        con = sqlite3.connect(old / 'hanzo.db')
        tables = sorted(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"))
        con.close()
        self.assertEqual(tables, ['hanzo_locker', 'hanzo_runs'])


if __name__ == '__main__':
    unittest.main()
