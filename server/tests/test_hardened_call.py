"""THE HARDENED CALL (the LARRYD runtime design, 2026-10-06): on Cloud Run the runtime takes a key per caller (slot A,
slot B) and a nonce signed with the call; a replayed nonce, an unknown key id, a destroyed key, the old shared-secret
form and a call with no nonce are all refused."""
import datetime
import pathlib
import secrets
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import callers, signing
from web import app as host


class HardenedCallTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.keys_dir = pathlib.Path(self.dir.name) / 'keys'
        self.keys_dir.mkdir()
        self.a, self.b = secrets.token_hex(32), secrets.token_hex(32)
        (self.keys_dir / 'slot-a').write_text(self.a)
        (self.keys_dir / 'slot-b').write_text(self.b)
        self.tick = [0.0]
        self.keys = callers.Keys(self.keys_dir, clock=lambda: self.tick[0])
        self.now = datetime.datetime(2026, 10, 6, 12, 0, 0, tzinfo=datetime.timezone.utc)
        inst = pathlib.Path(self.dir.name) / 'instance'
        inst.mkdir()
        self.client = host.create_app(str(inst), secret='', now=lambda: self.now, keys=self.keys,
                                      nonces=callers.MemoryNonces()).test_client()

    def tearDown(self):
        self.dir.cleanup()

    def call(self, key_id, secret, nonce=None, route='/health', data=None):
        data, at = data or {}, self.now.isoformat(timespec='seconds')
        nonce = secrets.token_hex(16) if nonce is None else nonce
        headers = {'X-Office-Key': key_id, 'X-Office-At': at, 'X-Office-Nonce': nonce,
                   'X-Office': signing.sign_hardened(secret, route, data, at, nonce)}
        return self.client.get('/api' + route, query_string=data, headers=headers)

    def test_each_slot_signs_with_its_own_key(self):
        self.assertEqual(self.call('slot-a', self.a).status_code, 200)
        self.assertEqual(self.call('slot-b', self.b).status_code, 200)

    def test_a_key_under_another_id_is_refused(self):
        self.assertEqual(self.call('slot-a', self.b).status_code, 401)
        self.assertEqual(self.call('slot-c', self.a).status_code, 401)

    def test_a_replayed_nonce_is_refused(self):
        nonce = secrets.token_hex(16)
        self.assertEqual(self.call('slot-a', self.a, nonce).status_code, 200)
        self.assertEqual(self.call('slot-a', self.a, nonce).status_code, 401)

    def test_no_nonce_or_a_short_one_is_refused(self):
        self.assertEqual(self.call('slot-a', self.a, nonce='').status_code, 401)
        self.assertEqual(self.call('slot-a', self.a, nonce='abc').status_code, 401)

    def test_the_old_shared_secret_form_is_refused(self):
        at = self.now.isoformat(timespec='seconds')
        r = self.client.get('/api/health', headers={'X-Office': signing.sign(self.a, '/health', {}, at), 'X-Office-At': at})
        self.assertEqual(r.status_code, 401)

    def test_a_destroyed_key_stops_within_the_cache(self):
        self.assertEqual(self.call('slot-a', self.a).status_code, 200)
        (self.keys_dir / 'slot-a').unlink()
        self.tick[0] += callers.KEY_CACHE_SECONDS
        self.assertEqual(self.call('slot-a', self.a).status_code, 401)
        self.assertEqual(self.call('slot-b', self.b).status_code, 200)


if __name__ == '__main__':
    unittest.main()
