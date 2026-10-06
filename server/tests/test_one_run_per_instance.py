"""ONE RUN PER INSTANCE, BY THE RUNTIME ITSELF (the security review, 2026-10-06): every door that runs agent code (the
answer, a job's run, the catch-up at start) takes the one slot atomically BEFORE the work and gives it back in a
finally; a second call while the slot is held is refused 409, never queued behind or run beside. A run's memory, CPU
and output are capped by the runtime's own limits, not only by Cloud Run's settings."""
import datetime
import os
import pathlib
import sys
import tempfile
import threading
import unittest

from _here import APP  # noqa: F401
from core_engine import sandbox, signing
from web import app as host

SECRET = 'scratch-secret-for-the-slot-test'


class OneSlot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = host.create_app(self.tmp.name, secret=SECRET)
        self.client = self.app.test_client()
        self.who = {'account': 'ACCT_000000000001_0001', 'scope': 'SCRATCH', 'member': 'MCON_000000000002_0002'}

    def tearDown(self):
        self.tmp.cleanup()

    def headers(self, route, data):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return {'X-Office': signing.sign(SECRET, route, data, at), 'X-Office-At': at}

    def test_every_door_that_runs_code_is_refused_while_the_slot_is_held(self):
        slot = self.app.config['slot']
        self.assertTrue(slot.acquire(blocking=False))
        try:
            d = {**self.who, 'agent_key': 'AGNT_X'}
            r = self.client.get('/api/agents/answer', query_string=d, headers=self.headers('/agents/answer', d))
            self.assertEqual(r.status_code, 409)
            d = {**self.who, 'job_key': 'JOB_X', 'run': '1'}
            r = self.client.post('/api/jobs/run', json=d, headers=self.headers('/jobs/run', d))
            self.assertEqual(r.status_code, 409)
        finally:
            slot.release()

    def test_the_slot_is_given_back_when_the_work_fails(self):
        d = {**self.who, 'agent_key': 'AGNT_NOT_HELD'}
        self.client.get('/api/agents/answer', query_string=d, headers=self.headers('/agents/answer', d))
        self.assertTrue(self.app.config['slot'].acquire(blocking=False))
        self.app.config['slot'].release()

    def test_a_job_holds_the_slot_until_its_thread_ends(self):
        gate, seen = threading.Event(), {}
        def slow(*_):
            seen['held'] = not self.app.config['slot'].acquire(blocking=False)
            gate.wait(5)
        self.app.config['harness'].run_job = slow
        d = {**self.who, 'job_key': 'JOB_SLOW', 'run': '1'}
        r = self.client.post('/api/jobs/run', json=d, headers=self.headers('/jobs/run', d))
        self.assertEqual(r.status_code, 202)
        d2 = {**self.who, 'job_key': 'JOB_OTHER', 'run': '1'}
        self.assertEqual(self.client.post('/api/jobs/run', json=d2, headers=self.headers('/jobs/run', d2)).status_code, 409)
        gate.set()
        for _ in range(100):
            if self.app.config['slot'].acquire(blocking=False):
                self.app.config['slot'].release()
                break
            threading.Event().wait(0.02)
        else:
            self.fail('the slot was never given back')
        self.assertTrue(seen['held'])


class RunLimits(unittest.TestCase):
    def test_the_runtime_sets_its_own_memory_cpu_and_file_limits(self):
        self.assertTrue(callable(getattr(sandbox, 'limits', None)))
        self.assertGreater(sandbox.MOST_MEMORY, 0)
        self.assertGreater(sandbox.MOST_CPU_SECONDS, 0)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'the limits are applied on Linux (the server)')
    def test_an_answer_past_the_output_limit_is_cut_and_refused(self):
        with tempfile.TemporaryDirectory() as a:
            pathlib.Path(a, 'agent.py').write_text("import sys\nsys.stdout.write('x' * (%d + 10))\n" % sandbox.MOST_BYTES)
            state, answer, why = sandbox.run(a, 'agent.py', {}, seconds=10)
            self.assertEqual(state, 'FAILED')


if __name__ == '__main__':
    unittest.main()
