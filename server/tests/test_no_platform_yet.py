"""A RUNTIME WITH NO PLATFORM YET (the LARRYD server before the platform has one): no address is declared, so HANZO's
own door answers, and every call that needs the platform is refused in its own plain words; nothing crashes."""
import datetime
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import signing
from web import app as host

SECRET = 'scratch-secret-no-platform'


class NoPlatformYet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = host.create_app(self.tmp.name, secret=SECRET, addresses={})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, method, route, data):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        headers = {'X-Office': signing.sign(SECRET, route, data, at), 'X-Office-At': at}
        r = self.client.get('/api' + route, query_string=data, headers=headers) if method == 'GET' else self.client.post('/api' + route, json=data, headers=headers)
        return r.status_code, r.get_json()

    def test_its_own_door_answers(self):
        self.assertEqual(self.call('GET', '/health', {}), (200, {'office': 'hanzo', 'locker': 0, 'runs': 0}))

    def test_a_call_that_needs_the_platform_says_why_it_cannot(self):
        from core_engine import locker
        locker.add(self.app.config['harness'].db, APP / 'agents', 'MAGT_00000000A001_0001', 'marketplace')
        who = {'account': 'ACCT_' + 'A' * 12 + '_0001', 'scope': 'SCRATCH', 'member': 'MCON_' + 'B' * 12 + '_0002'}
        self.assertEqual(self.call('GET', '/agents/answer', {**who, 'agent_key': 'MAGT_00000000A001_0001'}), (502, {'refused': 'wid has no address here'}))

    def test_the_start_up_catch_up_does_not_crash(self):
        self.assertEqual(host.catch_up(self.app), 0)


if __name__ == '__main__':
    unittest.main()
