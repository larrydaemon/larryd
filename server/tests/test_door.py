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
