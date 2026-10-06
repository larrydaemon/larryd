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
        self.out_dir = pathlib.Path(self.dir.name) / 'out'
        for slot in ('slot-a', 'slot-b'):   # the runtime's own key back to each slot (it refuses to start without them)
            (self.out_dir / slot).mkdir(parents=True)
            (self.out_dir / slot / 'v1').write_text(secrets.token_hex(32))
        self.client = host.create_app(str(inst), secret='', now=lambda: self.now, keys=self.keys,
                                      nonces=callers.MemoryNonces(), cloud={'outbound': callers.Outbound(self.out_dir)}).test_client()

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

    def test_a_key_mounted_as_a_folder_is_read(self):
        (self.keys_dir / 'slot-c').mkdir()
        c = secrets.token_hex(32)
        (self.keys_dir / 'slot-c' / 'key').write_text(c)
        self.tick[0] += callers.KEY_CACHE_SECONDS
        self.assertEqual(self.call('slot-c', c).status_code, 200)

    def test_a_destroyed_key_stops_within_the_cache(self):
        self.assertEqual(self.call('slot-a', self.a).status_code, 200)
        (self.keys_dir / 'slot-a').unlink()
        self.tick[0] += callers.KEY_CACHE_SECONDS
        self.assertEqual(self.call('slot-a', self.a).status_code, 401)
        self.assertEqual(self.call('slot-b', self.b).status_code, 200)


if __name__ == '__main__':
    unittest.main()


class HeaderValidationTest(HardenedCallTest):
    """The security review (2026-10-06): every header is checked for presence, length and characters before use; a
    malformed or oversize call is refused with 401 before its body is read or any nonce is stored; nothing of an
    exception is echoed."""

    def raw(self, headers, body=None, method='POST', route='/health'):
        return self.client.open('/api' + route, method=method, headers=headers, data=body,
                                content_type='application/json' if body is not None else None)

    def good_headers(self, nonce=None):
        at, nonce = self.now.isoformat(timespec='seconds'), nonce or secrets.token_hex(16)
        return {'X-Office-Key': 'slot-a', 'X-Office-At': at, 'X-Office-Nonce': nonce,
                'X-Office': signing.sign_hardened(self.a, '/health', {}, at, nonce)}

    def test_a_key_id_that_is_a_path_or_unknown_is_refused(self):
        for bad in ('../slot-a', 'slot-a/', 'SLOT-A', 'slot a', 'x' * 64, ''):
            h = self.good_headers(); h['X-Office-Key'] = bad
            self.assertEqual(self.raw(h, method='GET').status_code, 401, bad)

    def test_a_nonce_must_be_32_hex(self):
        for bad in ('g' * 32, 'a' * 31, 'a' * 33, 'A' * 32 + ' ', '00' * 100):
            h = self.good_headers(nonce=bad)
            self.assertEqual(self.raw(h, method='GET').status_code, 401, bad)

    def test_a_signature_must_be_64_hex(self):
        for bad in ('0' * 63, '0' * 65, 'z' * 64, ''):
            h = self.good_headers(); h['X-Office'] = bad
            self.assertEqual(self.raw(h, method='GET').status_code, 401, bad)

    def test_a_timestamp_must_be_the_iso_utc_form(self):
        for bad in ('1791300000', 'yesterday', self.now.isoformat() + 'x', 'x' * 200):
            h = self.good_headers(); h['X-Office-At'] = bad
            self.assertEqual(self.raw(h, method='GET').status_code, 401, bad)

    def test_an_oversize_body_is_refused_before_it_is_read(self):
        h = self.good_headers()
        r = self.raw(h, body='{"x": "' + 'a' * 70000 + '"}')
        self.assertEqual(r.status_code, 401)

    def test_a_malformed_call_stores_no_nonce(self):
        nonce = secrets.token_hex(16)
        h = self.good_headers(nonce=nonce); h['X-Office'] = '0' * 64   # well formed, wrong signature
        self.assertEqual(self.raw(h, method='GET').status_code, 401)
        self.assertEqual(self.raw(self.good_headers(nonce=nonce), method='GET').status_code, 200)   # the nonce was not used up

    def test_a_refusal_says_nothing_more(self):
        h = self.good_headers(); h['X-Office-At'] = 'x' * 200
        r = self.raw(h, method='GET')
        self.assertEqual(r.get_json(), {'refused': 'not a signed call'})
