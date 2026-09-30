"""THE ONLY WAY OUT, proven against a real signed door on a real port (HANZO's own host): no stand-in for the platform."""
import json
import pathlib
import socket
import tempfile
import threading
import unittest

from werkzeug.serving import make_server

from _here import APP
from core_engine import platform
from web import app as host

SECRET = 'scratch-secret-for-the-client-test'


def _free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.server = make_server('127.0.0.1', 0, host.create_app(cls.tmp.name, secret=SECRET))
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.tmp.cleanup()

    def _client(self, secret=SECRET, port=None):
        return platform.Client({'wid': f'http://127.0.0.1:{port or self.port}'}, secret)

    def test_a_signed_get_is_answered(self):
        self.assertEqual(self._client().get('wid', '/health'), (200, {'office': 'hanzo', 'locker': 0, 'runs': 0}))

    def test_a_wrong_secret_is_refused(self):
        self.assertEqual(self._client(secret='another').get('wid', '/health'), (401, {'refused': 'not a signed call'}))

    def test_query_values_are_signed_as_strings(self):
        """The platform signs a GET's query values as strings; an int given here must still verify there."""
        self.assertEqual(self._client().get('wid', '/health', {'n': 3})[0], 200)

    def test_an_undeclared_office_is_never_called(self):
        with self.assertRaises(KeyError):
            self._client().get('lryllm', '/health')

    def test_a_silent_platform(self):
        status, body = self._client(port=_free_port()).get('wid', '/health')
        self.assertEqual((status, body), (0, {'refused': 'wid does not answer'}))

    def test_addresses_come_from_config(self):
        cfg = json.loads((APP / 'schemas' / 'hanzo.json').read_text())
        self.assertEqual(platform.addresses(cfg, 'rnd', None), {'wid': 'http://127.0.0.1:5004', 'cc': 'http://127.0.0.1:5007', 'fs': 'http://127.0.0.1:5008', 'lryllm': 'http://127.0.0.1:5009'})

    def test_scratch_addresses_replace_them(self):
        cfg = json.loads((APP / 'schemas' / 'hanzo.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / 'platform.json').write_text(json.dumps({'wid': 'http://127.0.0.1:1', 'cc': 'http://127.0.0.1:2'}))
            self.assertEqual(platform.addresses(cfg, 'rnd', d), {'wid': 'http://127.0.0.1:1', 'cc': 'http://127.0.0.1:2'})


if __name__ == '__main__':
    unittest.main()
