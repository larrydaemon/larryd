"""THE SKILLS HANZO CARRIES OUT: an agent declares skills by hash (schemas/skills.json, the same definitions as LARRYD's);
a skill with a hand is carried out before the RUN and handed in; a skill HANZO does not have fails the run before
anything is asked. LARRY LLM here is a Recorder (in this process); what LARRY LLM answers is proven live only."""
import json
import pathlib
import socket
import sqlite3
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import harness, locker, platform, store

MTOK = '3c8ad8bf218a8350b26a7fb4b9eb7f6c70073553437aec8d05afee60f9740dcb'       # pinned here and in LARRYD's tests: drift on either side is red
GREETING = '94686bdeef7ebf3df3e52f1a3086f280ee25b1457336b87f5ab39860f7248fa2'
IDENTITY = '4db76a92980ff0a3b4cbe584d0b2de4c9821a5cbf7385c0b062c43f276f0ac0f'
STORE = '1d0eb4d13f8a91b4d0cc67f8b5cb157a4b74ec2c937779d49d4bb80beecc670a'
WHO = {'first_name': 'Ann', 'member_type': 'user', 'account_name': 'Scratch Account'}
KEY, JOB = 'MAGT_00000000D0B2_0001', 'MJOB_00000000D0B2_0001'
ACCOUNT, SCOPE, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'SCRATCH', 'MCON_' + 'B' * 12 + '_0002'
CARD = {'key': KEY, 'name': 'Echo', 'screen': 'larryd/agnt/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents',
        'price': '0', 'status': 'LIVE'}
HIRED = [{'agent_key': KEY, 'board': CARD['screen'], 'shell_id': 1, 'on': True, 'job_key': JOB}]
SAID = {'date': '2026-09-30', 'lang': 'en', 'greetings': {'morning': 'Up with the sun', 'afternoon': 'Good afternoon', 'evening': 'Good evening', 'night': 'Good night'}}


class Platform:
    def __init__(self, status=200, store_status=200):
        self.status, self.store_status, self.said = status, store_status, []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        if self.status != 200:
            return self.status, {'refused': 'sign in first'}
        return 200, {'/larry/greeting': SAID, '/agents/identity': WHO}[route]

    def post(self, office, route, data):
        self.said.append((office, route, data))
        if route == '/dam/upload':
            return (200, {'dam_key': 'DA-M_' + '0' * 12 + '_0001', 'repeat': False}) if self.store_status == 200 else (self.store_status, {'error': 'the zone does not take it'})
        return (200, {'charged': 0, 'free': True}) if route == '/mtok/use' else (200, {'saved': True})


def _closed_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class World(unittest.TestCase):
    """A scratch HANZO: its store, a locker with one agent, the platform's facts as it would answer them."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.instance = pathlib.Path(self.tmp.name) / 'instance'
        self.instance.mkdir()
        self.agents = pathlib.Path(self.tmp.name) / 'agents'
        self.db = store.open_store(self.instance)

    def tearDown(self):
        self.tmp.cleanup()

    def agent(self, skills, answer=None):
        folder = self.agents / 'echo'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'agent.json').write_text(json.dumps({'name': 'Echo', 'entry': 'agent.py', 'run': {'do': 'answer', 'hands': []}, 'skills': skills}))
        if answer is not None:
            (folder / 'agent.py').write_text(f'import json, sys\njson.load(sys.stdin)\nprint(json.dumps({answer!r}))\n')
        else:
            (folder / 'agent.py').write_text('import json, sys\njob = json.load(sys.stdin)\nprint(json.dumps({"delivery": json.dumps({k: job.get(k) for k in ("greeting", "identity") if k in job} or None, sort_keys=True)}))\n')
        con = sqlite3.connect(self.db)
        con.execute('DELETE FROM hanzo_locker')
        con.commit()
        con.close()
        locker.add(self.db, self.agents, KEY, 'echo')

    def run_with(self, client):
        h = harness.Harness(self.db, self.agents, client)
        h.facts = lambda account, scope, member: ([CARD], HIRED, [], lambda key: (True, ''))
        return h.run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1)

    @staticmethod
    def results(p):
        return [d for _o, route, d in p.said if route == '/jobs/result']


class Skills(World):
    def test_the_hashes_are_the_definitions(self):
        self.assertEqual({h: s['name'] for h, s in harness.SKILLS.items()}, {MTOK: 'mTok charge', GREETING: 'LARRY LLM greeting', IDENTITY: 'FROST identity', STORE: 'DA-M store'})

    def test_the_greeting_is_asked_for_the_runs_member_and_handed_in(self):
        self.agent([GREETING])
        p = Platform()
        self.assertEqual(self.run_with(p), 'DONE')
        self.assertIn(('lryllm', '/larry/greeting', {'account': ACCOUNT, 'member': MEMBER}), p.said)
        self.assertEqual(json.loads(self.results(p)[-1]['delivery']), {'greeting': SAID})
        for path in self.instance.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'Up with the sun', path.read_bytes())

    def test_who_the_agent_works_for_is_asked_of_frost_and_handed_in(self):
        self.agent([IDENTITY, GREETING])
        p = Platform()
        self.assertEqual(self.run_with(p), 'DONE')
        self.assertIn(('fs', '/agents/identity', {'account': ACCOUNT, 'member': MEMBER}), p.said)
        self.assertEqual(json.loads(self.results(p)[-1]['delivery']), {'greeting': SAID, 'identity': WHO})
        for path in self.instance.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'Scratch Account', path.read_bytes())

    def test_a_refusing_frost_fails_the_run(self):
        self.agent([IDENTITY])
        p = Platform(status=401)
        self.assertEqual(self.run_with(p), 'FAILED')
        self.assertEqual(self.results(p)[-1]['log'], 'HANZO could not read who the agent works for: sign in first')

    def test_a_silent_or_refusing_larry_llm_fails_the_run(self):
        self.agent([GREETING])
        p = Platform(status=401)
        self.assertEqual(self.run_with(p), 'FAILED')
        self.assertEqual(self.results(p)[-1]['log'], "HANZO could not read the member's greeting: sign in first")
        silent = platform.Client({'lryllm': f'http://127.0.0.1:{_closed_port()}', 'wid': f'http://127.0.0.1:{_closed_port()}'}, 'scratch', timeout=2)
        self.assertEqual(self.run_with(silent), 'FAILED')

    def test_a_skill_hanzo_does_not_have_fails_before_anything_is_asked(self):
        self.agent(['0' * 64])
        p = Platform()
        self.assertEqual(self.run_with(p), 'FAILED')
        self.assertEqual([r for _o, r, _d in p.said if r != '/jobs/result'], [])
        self.assertEqual(self.results(p)[-1]['log'], 'the agent declares a skill HANZO does not have: 000000000000')

    def test_the_mtok_charge_hands_nothing_and_asks_nothing(self):
        self.agent([MTOK])
        p = Platform()
        self.assertEqual(self.run_with(p), 'DONE')
        self.assertFalse([r for _o, r, _d in p.said if r == '/larry/greeting'])
        self.assertEqual(json.loads(self.results(p)[-1]['delivery']), None)

    def test_no_skill_asks_nothing(self):
        self.agent([])
        p = Platform()
        self.assertEqual(self.run_with(p), 'DONE')
        self.assertFalse([r for _o, r, _d in p.said if r == '/larry/greeting'])


class Store(World):
    FILE = {'name': 'Harbor theme.json', 'content_b64': 'eyJ0aGVtZSI6IDF9'}   # {"theme": 1}

    def test_the_files_are_stored_after_the_charge_for_the_runs_member(self):
        self.agent([STORE], {'delivery': 'one theme', 'files': [self.FILE]})
        p = Platform()
        self.assertEqual(self.run_with(p), 'DONE')
        routes = [r for _o, r, _d in p.said if r in ('/mtok/use', '/dam/upload')]
        self.assertEqual(routes, ['/mtok/use', '/dam/upload'])   # paid first: files are part of the delivery
        stored = next(d for o, r, d in p.said if r == '/dam/upload')
        self.assertEqual(stored, {'account': ACCOUNT, 'member': MEMBER, 'source_key': KEY, **self.FILE})
        self.assertIn(('so', '/dam/upload', stored), p.said)
        end = self.results(p)[-1]
        self.assertEqual((end['log'], end['delivery']), ('RUN 1 DONE · free · 1 file in DA-M', 'one theme'))
        for path in self.instance.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'eyJ0aGVtZSI6IDF9', path.read_bytes())

    def test_a_delivery_that_is_not_text_never_carries_the_files(self):
        self.agent([STORE], {'themes': ['Harbor'], 'files': [self.FILE]})
        p = Platform()
        self.assertEqual(self.run_with(p), 'DONE')
        self.assertEqual(json.loads(self.results(p)[-1]['delivery']), {'themes': ['Harbor']})

    def test_refused_before_anything_is_charged(self):
        cases = {
            'files without the skill': ([], {'delivery': 'x', 'files': [self.FILE]}, 'does not declare the DA-M store'),
            'not a list': ([STORE], {'files': 'x'}, 'not a list of at most 10'),
            'eleven files': ([STORE], {'files': [dict(self.FILE, name=f'f{i}.json') for i in range(11)]}, 'not a list of at most 10'),
            'a path for a name': ([STORE], {'files': [dict(self.FILE, name='../escape.json')]}, 'plain name'),
            'more than name and content': ([STORE], {'files': [dict(self.FILE, folder='x')]}, 'plain name'),
            'not base64': ([STORE], {'files': [dict(self.FILE, content_b64='not base64!')]}, 'not base64'),
            'empty': ([STORE], {'files': [dict(self.FILE, content_b64='')]}, 'is empty'),
        }
        for name, (skills, answer, words) in cases.items():
            with self.subTest(name):
                self.agent(skills, answer)
                p = Platform()
                self.assertEqual(self.run_with(p), 'FAILED')
                self.assertIn(words, self.results(p)[-1]['log'])
                self.assertFalse([r for _o, r, _d in p.said if r in ('/mtok/use', '/dam/upload')])

    def test_a_refusing_da_m_fails_the_run_and_says_it_was_charged(self):
        self.agent([STORE], {'delivery': 'x', 'files': [self.FILE]})
        p = Platform(store_status=400)
        self.assertEqual(self.run_with(p), 'FAILED')
        self.assertEqual(self.results(p)[-1]['log'], 'free, but DA-M did not store the files: the zone does not take it')

    def test_no_files_no_store(self):
        self.agent([STORE], {'delivery': 'nothing to keep'})
        p = Platform()
        self.assertEqual(self.run_with(p), 'DONE')
        self.assertFalse([r for _o, r, _d in p.said if r == '/dam/upload'])


if __name__ == '__main__':
    unittest.main()
