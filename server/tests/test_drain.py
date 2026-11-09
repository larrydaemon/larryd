"""THE QUEUE WALKED TO ITS END (2026-11-09): 42 RUNs queued by the clock, one slot: every one starts, one after another,
never two at once; a run queued while the walk is on is not left behind; the plain catch-up (no wait) is unchanged."""
import threading
import unittest

from _here import APP  # noqa: F401
from web import app as host

ALLOW = host.CONFIG['access']['grants']


class Client:
    def __init__(self, queues):
        self.queues = queues   # one list of runs per call to /jobs/queued, the last repeated

    def get(self, office, route, data=None):
        jobs = self.queues.pop(0) if len(self.queues) > 1 else self.queues[0]
        return 200, {'jobs': jobs}


def run(n):
    return {'account': 'A', 'scope': 'S', 'member': 'M', 'job_key': f'J{n}', 'run': '1', host.CONFIG['access']['field']: ALLOW}


class Harness:
    def __init__(self, client):
        self.client = client


class FakeApp:
    """start() as the laptop's: None while the one slot is held; the slot is freed by the fake sleep (a run's end)."""
    def __init__(self, queues):
        self.config = {'harnesses': {}, 'harness': Harness(Client(queues))}
        self.held, self.started, self.most = False, [], 0
        self.config['start'] = self.start

    def start(self, account, scope, member, job_key, run, caller=''):
        if self.held:
            return None
        if job_key in self.started:
            return False
        self.held = True
        self.started.append(job_key)
        return True

    def sleep(self, s):
        self.held = False   # the run in the slot ended


class Drain(unittest.TestCase):
    def test_without_wait_a_busy_slot_leaves_the_rest_queued(self):
        app = FakeApp([[run(n) for n in range(42)]])
        host.catch_up(app)
        self.assertEqual(app.started, ['J0'])

    def test_with_wait_every_queued_run_starts_one_after_another(self):
        app = FakeApp([[run(n) for n in range(42)]])
        host.catch_up(app, wait=60, sleep=app.sleep)
        self.assertEqual(app.started, [f'J{n}' for n in range(42)])

    def test_a_run_queued_during_the_walk_is_read_on_a_second_walk(self):
        app = FakeApp([[run(0), run(1)], [run(2)]])
        walks = []
        real = host.catch_up

        def fake(a, wait=None, sleep=None):
            walks.append(wait)
            real(a, wait=wait, sleep=app.sleep)
            if len(walks) == 1:
                d()   # a tick's press while this walk is on
        threads = []

        class Now:
            def __init__(self, target, daemon):
                self.target = target

            def start(self):
                threads.append(self)
                self.target()
        orig = host.catch_up
        host.catch_up = fake
        try:
            d = host.Drain(app, wait=60, thread=Now)
            self.assertTrue(d())
        finally:
            host.catch_up = orig
        self.assertEqual(walks, [60, 60])
        self.assertEqual(app.started, ['J0', 'J1', 'J2'])
        self.assertEqual(len(threads), 1)
        self.assertFalse(d.busy)

    def test_a_second_call_while_walking_starts_no_second_thread(self):
        app = FakeApp([[]])
        d = host.Drain(app, wait=60, thread=lambda target, daemon: type('T', (), {'start': lambda self: None})())
        self.assertTrue(d())
        self.assertFalse(d())
        self.assertTrue(d.again)


class SlotFreed(unittest.TestCase):
    def test_a_run_ending_walks_the_queue_once_more(self):
        import tempfile, pathlib
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            app = host.create_app(pathlib.Path(d), 's' * 32)
            kicked = []
            app.config['drain'] = lambda: kicked.append(1)
            ended = threading.Event()
            with mock.patch.object(host.lanes_harness.Harness, 'run_job', lambda self, *a: ended.set()):
                self.assertTrue(app.config['start']('A', 'S', 'M', 'J', 1))
                self.assertTrue(ended.wait(5))
                for _ in range(50):
                    if kicked:
                        break
                    threading.Event().wait(0.05)
            self.assertEqual(kicked, [1])


if __name__ == '__main__':
    unittest.main()
