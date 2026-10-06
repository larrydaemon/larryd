import datetime
import json
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import signing
from web import app as host

SECRET = 'scratch-secret-for-the-door-test'


class DoorTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.now = datetime.datetime(2026, 9, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
        self.client = host.create_app(self.dir.name, secret=SECRET, now=lambda: self.now).test_client()

    def tearDown(self):
        self.dir.cleanup()

    def _get(self, route, data, secret=SECRET, at=None):
        """The platform's headers: X-Office = the signature, X-Office-At = the moment it signed (the platform's office scheme)."""
        at = at or self.now.isoformat(timespec='seconds')
        return self.client.get('/api' + route, query_string=data, headers={'X-Office': signing.sign(secret, route, data, at), 'X-Office-At': at})

    def test_signed_call_answers_real_counts(self):
        r = self._get('/health', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {'office': 'hanzo', 'locker': 0, 'runs': 0})

    def test_unsigned_is_refused(self):
        self.assertEqual(self.client.get('/api/health').status_code, 401)

    def test_wrong_secret_is_refused(self):
        self.assertEqual(self._get('/health', {}, secret='another').status_code, 401)

    def test_stale_call_is_refused(self):
        old = (self.now - datetime.timedelta(seconds=61)).isoformat(timespec='seconds')
        self.assertEqual(self._get('/health', {}, at=old).status_code, 401)

    def test_future_call_is_refused(self):
        ahead = (self.now + datetime.timedelta(seconds=61)).isoformat(timespec='seconds')
        self.assertEqual(self._get('/health', {}, at=ahead).status_code, 401)

    def test_signature_binds_the_data(self):
        at = self.now.isoformat(timespec='seconds')
        sig = signing.sign(SECRET, '/health', {}, at)
        r = self.client.get('/api/health', query_string={'account': 'X'}, headers={'X-Office': sig, 'X-Office-At': at})
        self.assertEqual(r.status_code, 401)

    def test_no_secret_no_start(self):
        with self.assertRaises(SystemExit):
            host.create_app(self.dir.name, secret='')


class SigningTest(unittest.TestCase):
    def test_the_platform_scheme(self):
        """route + ' ' + at + ' ' + compact sorted JSON, HMAC-SHA256 hex: the scheme the platform's offices already use."""
        import hashlib
        import hmac
        text = '/x 2026-09-28T12:00:00+00:00 ' + json.dumps({'b': '1', 'a': '2'}, sort_keys=True, separators=(',', ':'))
        self.assertEqual(signing.sign('s', '/x', {'b': '1', 'a': '2'}, '2026-09-28T12:00:00+00:00'),
                         hmac.new(b's', text.encode(), hashlib.sha256).hexdigest())


if __name__ == '__main__':
    unittest.main()


class TheCardKeyDoor(unittest.TestCase):
    """POST /agents/card: the platform, after FROST approved an agent, tells the runtime its card's key (signed)."""
    def setUp(self):
        import pathlib
        from core_engine import locker, store
        self.dir = tempfile.TemporaryDirectory()
        self.now = datetime.datetime(2026, 9, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
        agents = pathlib.Path(self.dir.name) / 'agents'
        (agents / 'echo').mkdir(parents=True)
        (agents / 'echo' / 'agent.json').write_text(json.dumps({'name': 'ECHO', 'entry': 'agent.py'}))
        (agents / 'echo' / 'agent.py').write_text('print(1)\n')
        self.db = store.open_store(self.dir.name)
        locker.add(self.db, agents, 'MAGT_AAAAAAAAAAAA_0001', 'echo')
        self.client = host.create_app(self.dir.name, secret=SECRET, now=lambda: self.now, agents=str(agents)).test_client()

    def tearDown(self):
        self.dir.cleanup()

    def _post(self, data, secret=SECRET):
        at = self.now.isoformat(timespec='seconds')
        return self.client.post('/api/agents/card', json=data, headers={'X-Office': signing.sign(secret, '/agents/card', data, at), 'X-Office-At': at})

    def test_the_card_key_is_linked(self):
        from core_engine import locker
        r = self._post({'agent_key': 'MAGT_AAAAAAAAAAAA_0001', 'card_key': 'MAGT_BBBBBBBBBBBB_0002'})
        self.assertEqual((r.status_code, r.get_json()), (200, {'linked': True}))
        self.assertEqual(locker.held(self.db, 'MAGT_BBBBBBBBBBBB_0002')['agent_key'], 'MAGT_AAAAAAAAAAAA_0001')

    def test_refused(self):
        self.assertEqual(self._post({'agent_key': 'MAGT_AAAAAAAAAAAA_0001', 'card_key': 'MAGT_BBBBBBBBBBBB_0002'}, secret='another').status_code, 401)
        self.assertEqual(self._post({'agent_key': 'MAGT_CCCCCCCCCCCC_0003', 'card_key': 'MAGT_BBBBBBBBBBBB_0002'}).status_code, 404)
        self.assertEqual(self._post({'agent_key': 'MAGT_AAAAAAAAAAAA_0001', 'card_key': 'x; DROP'}).status_code, 400)
