"""THE CALLBACK'S COLD START (the infra lane's finding, 2026-10-06): a fresh Cloud Run instance behind Cloud NAT loses
the slot's answers for its first 15 to 35 s. Closed in code: the warm-up (three handshakes in a row or 60 s) before
/ready answers and before a job execution's run; every call back retried with backoff, a fresh nonce each try; a result
that still does not reach the platform recorded as CALLBACK_FAILED, never silent."""
import pathlib
import socket
import tempfile
import unittest
import urllib.error

from _here import APP  # noqa: F401
from core_engine import callers, harness as lanes_harness, platform, records as run_records, store, warmup
from test_review_fixes import CloudApp, FakeCollection
from web import app as host


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


class Answer:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, *a):
        return b'{"ok": true}'


class WarmUp(unittest.TestCase):
    def test_ready_only_after_three_handshakes_in_a_row(self):
        clock, seen = Clock(), []
        answers = iter([False, True, True, False, True, True, True])   # lost, two, lost again, then three in a row

        def shake(host, port):
            clock.t += 0.1
            seen.append((host, port))
            if not next(answers):
                raise socket.timeout('lost')
        r = warmup.warm([('frost-b.positivefeedback.ai', 443)], shake=shake, clock=clock, sleep=clock.sleep)
        self.assertTrue(r['ready'])
        self.assertEqual(r['tries'], 7)

    def test_past_sixty_seconds_it_is_ready_anyway_and_says_not_warm(self):
        clock = Clock()

        def shake(host, port):
            clock.t += 3
            raise socket.timeout('lost')
        with self.assertLogs('runtime', 'ERROR'):
            r = warmup.warm([('frost-b.positivefeedback.ai', 443)], shake=shake, clock=clock, sleep=clock.sleep)
        self.assertFalse(r['ready'])
        self.assertGreaterEqual(r['seconds'], 60)
        self.assertLess(r['seconds'], 65)

    def test_only_slots_with_an_address_are_warmed(self):
        self.assertEqual(warmup.hosts({'slot-a': '', 'slot-b': 'https://frost-b.positivefeedback.ai', 'proof': '',
                                       'offices': ['wid']}), [('frost-b.positivefeedback.ai', 443)])

    def test_a_handshake_sends_nothing(self):
        sent = []

        class Raw:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def sendall(self, *a):
                sent.append(a)
        wrapped = []

        class Ctx:
            def wrap_socket(self, raw, server_hostname):
                wrapped.append(server_hostname)
                return Raw()
        orig_conn, orig_ctx = warmup.socket.create_connection, warmup.ssl.create_default_context
        warmup.socket.create_connection = lambda addr, timeout: Raw()
        warmup.ssl.create_default_context = lambda: Ctx()
        try:
            self.assertTrue(warmup.handshake('frost-b.positivefeedback.ai'))
        finally:
            warmup.socket.create_connection, warmup.ssl.create_default_context = orig_conn, orig_ctx
        self.assertEqual(wrapped, ['frost-b.positivefeedback.ai'])
        self.assertEqual(sent, [])


class Ready(CloudApp):
    def test_ready_answers_503_until_the_warm_up_then_200_unsigned(self):
        app = self.make()
        c = app.test_client()
        self.assertEqual(c.get('/ready').status_code, 503)
        clock, shakes = Clock(), []
        host.warm_up(app, shake=lambda h, p: shakes.append(h), sleep=clock.sleep)
        r = c.get('/ready')
        self.assertEqual((r.status_code, r.get_json()), (200, {'ready': True}))
        self.assertEqual(shakes, ['frost-b.positivefeedback.ai'] * 3)
        self.assertEqual(c.get('/api/health').status_code, 401)   # every other door is still signed only
        self.assertEqual(c.post('/ready').status_code, 401)

    def test_the_catch_up_runs_before_ready(self):
        app, order = self.make(), []
        host.warm_up(app, shake=lambda h, p: None, then=lambda a: order.append(a.config['ready'].is_set()))
        self.assertEqual(order, [False])
        self.assertTrue(app.config['ready'].is_set())


class Proof(CloudApp):
    def test_the_callback_proof_warms_up_then_reports_statuses_and_times_only(self):
        app = self.make()
        h = app.config['harnesses']['slot-b']
        h.client.get = lambda office, route, data=None: (200, {'jobs': [{'job_key': 'secret data'}]})
        orig = host.warmup.handshake
        host.warmup.handshake = lambda host_, port=443: True
        try:
            app.config['ready'].clear()
            out = host.callbacks(app, 'slot-b', 20)
        finally:
            host.warmup.handshake = orig
        self.assertTrue(out['warm_up']['ready'])
        self.assertEqual(out['first_call_back']['status'], 200)
        self.assertEqual((out['steady']['answered'], out['steady']['of'], out['steady']['statuses']), (20, 20, [200]))
        self.assertNotIn('secret data', repr(out))
        with self.assertRaises(SystemExit):
            host.callbacks(app, 'slot-c', 1)


class Retries(CloudApp):
    def client(self, retry=60):
        self.clock = Clock()
        return platform.Client({'wid': 'https://frost-b.positivefeedback.ai/wid'}, '', outbound=callers.Outbound(self.out_dir),
                               slot='slot-b', retry_seconds=retry, clock=self.clock, sleep=self.clock.sleep)

    def patched(self, answers):
        sent, it = [], iter(answers)

        def opener(req, timeout=None):
            sent.append((self.clock.t, dict((k.lower(), v) for k, v in req.header_items())))
            a = next(it)
            if isinstance(a, BaseException):
                raise a
            return Answer()
        orig = platform.urllib.request.urlopen
        platform.urllib.request.urlopen = opener
        self.addCleanup(setattr, platform.urllib.request, 'urlopen', orig)
        return sent

    def test_a_lost_call_back_is_retried_with_backoff_and_a_fresh_nonce_each_time(self):
        client = self.client()
        lost = urllib.error.URLError(socket.timeout('lost'))
        sent = self.patched([lost, lost, lost, Answer()])
        status, body = client.post('wid', '/jobs/result', {'a': 1})
        self.assertEqual((status, body), (200, {'ok': True}))
        self.assertEqual([t for t, _ in sent], [0, 0.5, 1.5, 3.5])
        self.assertEqual(len({h['x-office-nonce'] for _, h in sent}), 4)

    def test_retries_stop_at_sixty_seconds(self):
        client = self.client()
        sent = self.patched([urllib.error.URLError(socket.timeout('lost'))] * 20)
        status, body = client.get('wid', '/jobs/queued')
        self.assertEqual(status, 0)
        self.assertLessEqual(sent[-1][0], 60)
        self.assertEqual([t for t, _ in sent], [0, 0.5, 1.5, 3.5, 7.5, 15.5, 31.5])

    def test_a_post_that_left_is_never_sent_twice(self):
        client = self.client()
        sent = self.patched([socket.timeout('no answer after sending')] * 5)
        status, _ = client.post('wid', '/jobs/result', {'a': 1})
        self.assertEqual((status, len(sent)), (0, 1))

    def test_an_answer_is_never_retried(self):
        client = self.client()
        sent = self.patched([urllib.error.HTTPError('u', 401, 'no', {}, None)])
        status, _ = client.post('wid', '/jobs/result', {'a': 1})
        self.assertEqual((status, len(sent)), (401, 1))


class CallbackFailed(unittest.TestCase):
    def test_a_result_that_never_reaches_the_platform_is_recorded_callback_failed(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = store.open_store(tmp.name)
        col = FakeCollection()

        class Lost:
            def post(self, office, route, data):
                return 0, {'refused': 'wid does not answer'}
        h = lanes_harness.Harness(db, pathlib.Path(tmp.name), Lost(), records=run_records.FirestoreRecords(col=col), caller='slot-b')
        with self.assertLogs('runtime', 'ERROR'):
            h._end('ACCT_0123456789AB_0001', 'scope', 'MEMB_0123456789AB_0001', '', 'JOBS_0123456789AB_0001', 7, 'DONE', 'RUN 7 DONE')
        with self.assertLogs('runtime', 'ERROR'):
            state = h._end('ACCT_0123456789AB_0001', 'scope', 'MEMB_0123456789AB_0001', '', 'JOBS_0123456789AB_0002', 8, 'FAILED', 'the agent stopped: x')
        (done, failed) = sorted(col.docs.values(), key=lambda d: d['run'])
        self.assertEqual((done['state'], done['error_code']), ('CALLBACK_FAILED', 'RUN_DONE'))
        self.assertEqual((failed['state'], failed['error_code'], state), ('CALLBACK_FAILED', 'THE_AGENT_STOPPED', 'FAILED'))


if __name__ == '__main__':
    unittest.main()
