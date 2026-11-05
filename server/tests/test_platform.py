"""THE ONLY WAY OUT, proven against a real signed door on a real port (the runtime's own host): no stand-in for the platform."""
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
        self.assertEqual(self._client().get('wid', '/health'), (200, {'office': 'runtime', 'locker': 0, 'runs': 0}))

    def test_a_wrong_secret_is_refused(self):
        self.assertEqual(self._client(secret='another').get('wid', '/health'), (401, {'refused': 'not a signed call'}))

    def test_query_values_are_signed_as_strings(self):
        """The platform signs a GET's query values as strings; an int given here must still verify there."""
        self.assertEqual(self._client().get('wid', '/health', {'n': 3})[0], 200)

    def test_an_undeclared_office_is_never_called(self):
        self.assertEqual(self._client().get('lryllm', '/health'), (0, {'refused': 'lryllm has no address here'}))
        self.assertEqual(platform.Client({}, 'scratch').post('wid', '/jobs/result', {}), (0, {'refused': 'wid has no address here'}))

    def test_a_silent_platform(self):
        status, body = self._client(port=_free_port()).get('wid', '/health')
        self.assertEqual((status, body), (0, {'refused': 'wid does not answer'}))

    def test_addresses_come_from_config(self):
        cfg = json.loads((APP / 'schemas' / 'runtime.json').read_text())
        self.assertEqual(platform.addresses(cfg, 'rnd', None), {'wid': 'http://127.0.0.1:5004'})   # wid alone (the core cleanup 2026-11-05)

    def test_scratch_addresses_replace_them(self):
        cfg = json.loads((APP / 'schemas' / 'runtime.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / 'platform.json').write_text(json.dumps({'wid': 'http://127.0.0.1:1', 'cc': 'http://127.0.0.1:2'}))
            self.assertEqual(platform.addresses(cfg, 'rnd', d), {'wid': 'http://127.0.0.1:1', 'cc': 'http://127.0.0.1:2'})



class WidAlone(unittest.TestCase):
    """THE RUNTIME REACHES wid ALONE (the core cleanup, the owner 2026-11-05: "no agents should have anything to do with cc, fs,
    laryllm, so"): no address of another office in its config, no other office among the asks a call may be handed or a
    skill's hands, and no call to another office anywhere in its code."""
    OTHERS = ('fs', 'cc', 'so', 'lryllm')

    def test_the_config_names_wid_alone(self):
        cfg = json.loads((APP / 'schemas' / 'runtime.json').read_text())
        self.assertEqual(sorted(k for k in cfg['platform'] if k != 'about'), ['wid'])
        self.assertEqual(cfg['slots']['offices'], ['wid'])

    def test_every_ask_handed_or_carried_is_wids(self):
        from core_engine import harness
        self.assertEqual({o for o, _m, _r in harness.PLATFORM_HANDED}, {'wid'})
        self.assertEqual({office for office, _r, _w, _who in harness.HANDED.values()}, {'wid'})

    def test_no_code_calls_another_office(self):
        import re
        call = re.compile(r"""(?:get|post|_ask|ask|_send)\(\s*'(%s)'""" % '|'.join(self.OTHERS))
        for f in sorted((APP / 'core_engine').glob('*.py')) + sorted((APP / 'web').glob('*.py')):
            self.assertIsNone(call.search(f.read_text()), f.name)


if __name__ == '__main__':
    unittest.main()
