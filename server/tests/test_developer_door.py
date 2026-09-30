"""THE DEVELOPER DOOR: a developer (a HANZO-side name, their own secret) submits the files of an agent that is theirs;
HANZO writes them into its locker (dev/<agent_key>/), then sends that agent to FROST's review as it sends any agent.
Every refusal is planted here. What FROST answers is proven live only; here FROST is either a Recorder (in this process,
it answers nothing for the platform but a receipt) or a silent port."""
import base64
import datetime
import hashlib
import json
import os
import pathlib
import socket
import sqlite3
import stat
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import developers, harness, locker, signing, store
from web import app as host

SECRET = 'scratch-secret-for-the-developer-door'
KEY = 'MAGT_00000000D001_0001'
OTHER = 'MAGT_00000000D002_0002'


def _closed_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Frost:
    """FROST as a receipt: it records what HANZO sends and answers a waiting review. Nothing else answers for the platform."""
    def __init__(self, approved=()):
        self.said, self.approved = [], list(approved)

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return 200, {'id': 1, 'state': 'waiting'}

    def get(self, office, route, data=None):
        return 200, {'approved': self.approved}


def _b64(text):
    return base64.b64encode(text.encode()).decode()


def _agent_files(answer='hello'):
    return {'agent.json': _b64(json.dumps({'name': 'Scratch agent', 'entry': 'agent.py', 'does': ['answer']})),
            'agent.py': _b64(f'import json, sys\njson.load(sys.stdin)\nprint(json.dumps({{"delivery": "{answer}"}}))\n')}


class DeveloperDoor(unittest.TestCase):
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
        self.client = self.app.test_client()
        self.db = self.h.db
        self.secrets = self.instance / 'secrets' / 'developers'
        self.dev_secret = developers.add(self.db, self.secrets, 'ada', KEY)

    def tearDown(self):
        self.tmp.cleanup()

    def _headers(self, route, data, developer='ada', secret=None, at=None):
        at = at or self.now.isoformat(timespec='seconds')
        return {'X-Developer': developer, 'X-Developer-Sig': signing.sign(secret or self.dev_secret, route, data, at), 'X-Office-At': at}

    def submit(self, files, key=KEY, **signed):
        data = {'agent_key': key, 'files': files}
        return self.client.post('/api/developer/submit', json=data, headers=self._headers('/developer/submit', data, **signed))

    def status(self, **signed):
        return self.client.get('/api/developer/status', headers=self._headers('/developer/status', {}, **signed))

    # ---------------------------------------------------------------- the developer
    def test_a_developer_is_made_once_with_a_secret_only_hanzo_keeps(self):
        self.assertEqual(len(self.dev_secret), 64)
        path = self.secrets / 'ada'
        self.assertEqual(path.read_text().strip(), self.dev_secret)
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.secrets).st_mode), 0o700)
        self.assertEqual(developers.add(self.db, self.secrets, 'ada', OTHER), '')   # not shown again
        self.assertEqual(developers.theirs(self.db, 'ada'), [KEY, OTHER])

    def test_an_agent_has_one_developer(self):
        with self.assertRaises(developers.Refused) as no:
            developers.add(self.db, self.secrets, 'bob', KEY)
        self.assertEqual(no.exception.status, 409)
        self.assertEqual(developers.theirs(self.db, 'bob'), [])

    def test_plain_names_and_card_keys_only(self):
        for name, key in (('../x', KEY), ('Ada', KEY), ('ada', 'not-a-key'), ('ada', '../../etc'), ('ada', 'MAGT_SCRATCH00001_0001')):   # not hex: FROST would refuse it
            with self.assertRaises(developers.Refused):
                developers.add(self.db, self.secrets, name, key)
        self.assertEqual(sorted(p.name for p in self.secrets.iterdir()), ['ada'])

    # ---------------------------------------------------------------- the signature
    def test_a_signed_developer_call_answers(self):
        self.assertEqual(self.status().status_code, 200)

    def test_unsigned_wrong_stale_or_unknown_is_refused(self):
        self.assertEqual(self.client.get('/api/developer/status').status_code, 401)
        self.assertEqual(self.status(secret='f' * 64).status_code, 401)
        old = (self.now - datetime.timedelta(seconds=61)).isoformat(timespec='seconds')
        self.assertEqual(self.status(at=old).status_code, 401)
        self.assertEqual(self.status(developer='nobody').status_code, 401)
        self.assertTrue((self.secrets / '..' / 'developers' / 'ada').is_file())   # the plant really reaches ada's secret file
        self.assertEqual(self.status(developer='../developers/ada').status_code, 401)

    def test_the_two_doors_do_not_cross(self):
        self.assertEqual(self.status(secret=SECRET).status_code, 401)   # HANZO's own secret is not a developer's
        at = self.now.isoformat(timespec='seconds')
        r = self.client.get('/api/health', headers={'X-Office': signing.sign(self.dev_secret, '/health', {}, at), 'X-Office-At': at})
        self.assertEqual(r.status_code, 401)   # a developer's secret opens no office route

    def test_the_signature_binds_the_upload(self):
        data = {'agent_key': KEY, 'files': _agent_files()}
        headers = self._headers('/developer/submit', data)
        r = self.client.post('/api/developer/submit', json={**data, 'files': _agent_files('changed')}, headers=headers)
        self.assertEqual(r.status_code, 401)

    # ---------------------------------------------------------------- the upload
    def test_a_submission_is_held_and_sent_to_frost(self):
        r = self.submit(_agent_files())
        self.assertEqual(r.status_code, 200, r.get_json())
        body = r.get_json()
        row = locker.held(self.db, KEY)
        self.assertEqual((body['code_sha256'], body['manifest_sha256']), (row['code_sha256'], row['manifest_sha256']))
        self.assertEqual(row['folder'], f'dev/{KEY}')
        self.assertEqual(locker.verify(self.db, self.agents, KEY), (True, ''))
        code = hashlib.sha256(b'agent.py\0' + base64.b64decode(_agent_files()['agent.py']) + b'\0').hexdigest()
        self.assertEqual(body['code_sha256'], code)   # the locker's recipe over exactly the uploaded bytes
        self.assertEqual(body['review'], {'id': 1, 'state': 'waiting'})
        office, route, sent = self.frost.said[-1]
        self.assertEqual((office, route), ('fs', '/agents/submit'))
        self.assertEqual((sent['agent_key'], sent['code_sha256'], sent['manifest_sha256'], sent['name']), (KEY, code, row['manifest_sha256'], 'Scratch agent'))

    def test_a_changed_agent_replaces_the_old_one(self):
        first = self.submit(_agent_files('one')).get_json()
        second = self.submit(_agent_files('two')).get_json()
        self.assertNotEqual(first['code_sha256'], second['code_sha256'])
        self.assertIn(b'two', (self.agents / 'dev' / KEY / 'agent.py').read_bytes())
        self.assertEqual(sorted(p.name for p in (self.agents / 'dev').iterdir()), [KEY])   # no leftover upload
        self.assertEqual(self.submit(_agent_files('two')).get_json()['code_sha256'], second['code_sha256'])

    def test_not_yours_is_refused(self):
        developers.add(self.db, self.secrets, 'ada', OTHER)
        bob = developers.add(self.db, self.secrets, 'bob', 'MAGT_00000000D003_0003')
        r = self.submit(_agent_files(), key=KEY, developer='bob', secret=bob)
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': 'that agent is not yours'}))
        self.assertIsNone(locker.held(self.db, KEY))

    def _refused(self, files, status=400):
        r = self.submit(files)
        self.assertEqual(r.status_code, status, r.get_json())
        self.assertIn('refused', r.get_json())
        return r.get_json()['refused']

    def test_every_bad_upload_is_refused_and_nothing_is_held(self):
        good = _agent_files()
        plants = {
            'a path up and out': {**good, '../escape.py': _b64('x')},
            'a path up inside': {**good, 'lib/../../escape.py': _b64('x')},
            'an absolute path': {**good, '/tmp/escape.py': _b64('x')},
            'a hidden file': {**good, '.env': _b64('x')},
            'a hidden folder': {**good, 'lib/.cache/x.py': _b64('x')},
            'a backslash path': {**good, 'lib\\x.py': _b64('x')},
            'a link (not a file)': {**good, 'data.txt': {'link': '/etc/hosts'}},
            'not base64': {**good, 'data.txt': 'not base64!!'},
            'no manifest': {'agent.py': good['agent.py']},
            'a manifest with no entry file': {'agent.json': good['agent.json']},
            'a manifest that is not JSON': {**good, 'agent.json': _b64('{')},
            'no files': {},
        }
        for name, files in plants.items():
            with self.subTest(name):
                self._refused(files)
        self.assertIsNone(locker.held(self.db, KEY))
        self.assertFalse((self.agents / 'dev' / KEY).exists())
        self.assertFalse(pathlib.Path('/tmp/escape.py').exists())
        self.assertFalse((self.agents / 'escape.py').exists())

    def test_the_limits(self):
        many = {**_agent_files(), **{f'f{i}.txt': _b64('x') for i in range(200)}}
        self.assertIn('more than 200 files', self._refused(many, 413))
        big = {**_agent_files(), 'big.txt': base64.b64encode(b'x' * 5_000_001).decode()}
        self.assertIn('bytes', self._refused(big, 413))

    def test_a_bad_resubmission_leaves_the_held_agent_as_it_was(self):
        held = self.submit(_agent_files()).get_json()
        self._refused({**_agent_files(), '../escape.py': _b64('x')})
        self._refused({'agent.json': _agent_files()['agent.json']})
        self.assertEqual(locker.held(self.db, KEY)['code_sha256'], held['code_sha256'])
        self.assertEqual(locker.verify(self.db, self.agents, KEY), (True, ''))

    def test_a_silent_frost_is_said_and_the_agent_stays_held(self):
        self.h.client = host.platform.Client({'fs': f'http://127.0.0.1:{_closed_port()}'}, SECRET, timeout=2)
        r = self.submit(_agent_files())
        self.assertEqual(r.status_code, 502)
        self.assertIn('FROST did not take it: fs does not answer; submit again', r.get_json()['refused'])
        self.assertEqual(r.get_json()['code_sha256'], locker.held(self.db, KEY)['code_sha256'])

    # ---------------------------------------------------------------- the status
    def test_the_status_is_counted_from_hanzo_runs(self):
        developers.add(self.db, self.secrets, 'ada', OTHER)
        developers.add(self.db, self.secrets, 'bob', 'MAGT_00000000D003_0003')
        held = self.submit(_agent_files()).get_json()
        for lane, state, charged in (('job', 'DONE', 3), ('job', 'DONE', 2), ('job', 'FAILED', 0), ('call', 'DONE', 0),
                                     ('hire', 'ON', 0), ('hire', 'ON', 0), ('hire', 'OFF', 0)):
            self.h._record(lane, KEY, state, charged=charged)
        self.h._record('job', 'MAGT_00000000D003_0003', 'DONE', charged=99)   # bob's, never in ada's status
        self.frost.approved = [{'agent_key': KEY, 'code_sha256': held['code_sha256'], 'manifest_sha256': held['manifest_sha256']}]
        agents = self.status().get_json()['agents']
        self.assertEqual([a['agent_key'] for a in agents], [KEY, OTHER])
        mine = agents[0]
        self.assertEqual({k: mine[k] for k in ('held', 'review', 'runs', 'calls', 'hires', 'unhires', 'charged')},
                         {'held': True, 'review': 'approved', 'runs': {'DONE': 2, 'FAILED': 1}, 'calls': 1, 'hires': 2, 'unhires': 1, 'charged': 5})
        self.assertEqual(agents[1]['review'], 'not submitted')
        self.frost.approved = []
        self.assertEqual(self.status().get_json()['agents'][0]['review'], 'not approved')
        self.h.client = host.platform.Client({'fs': f'http://127.0.0.1:{_closed_port()}'}, SECRET, timeout=2)
        self.assertEqual(self.status().get_json()['agents'][0]['review'], 'unknown: fs does not answer')

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


if __name__ == '__main__':
    unittest.main()
