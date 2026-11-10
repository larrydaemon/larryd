"""ONE RUN PER INSTANCE, BY THE RUNTIME ITSELF (the security review, 2026-10-06): every door that runs agent code (the
answer, a job's run, the catch-up at start) takes the one slot atomically BEFORE the work and gives it back in a
finally; a second call while the slot is held is refused 409, never queued behind or run beside. A run's memory, CPU
and output are capped by the runtime's own limits, not only by Cloud Run's settings."""
import datetime
import os
import pathlib
import subprocess
import sys
import shutil
import tempfile
import threading
import unittest

from _here import APP  # noqa: F401
from _frost import decided
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
        t = slot.take()
        self.assertTrue(t)
        try:
            d = {**self.who, 'agent_key': 'AGNT_X'}
            r = self.client.get('/api/agents/answer', query_string=d, headers=self.headers('/agents/answer', d))
            self.assertEqual(r.status_code, 409)
            d = {**self.who, 'job_key': 'JOB_X', 'run': '1', 'access': 'allow', **decided(member=self.who['member'])}
            r = self.client.post('/api/jobs/run', json=d, headers=self.headers('/jobs/run', d))
            self.assertEqual(r.status_code, 409)
        finally:
            slot.give_back(t)

    def test_the_slot_is_given_back_when_the_work_fails(self):
        d = {**self.who, 'agent_key': 'AGNT_NOT_HELD'}
        self.client.get('/api/agents/answer', query_string=d, headers=self.headers('/agents/answer', d))
        t = self.app.config['slot'].take()
        self.assertTrue(t)
        self.app.config['slot'].give_back(t)

    def test_a_job_holds_the_slot_until_its_thread_ends(self):
        gate, seen = threading.Event(), {}
        def slow(*_):
            seen['held'] = self.app.config['slot'].taken_at is not None
            gate.wait(5)
        self.app.config['harness'].run_job = slow
        d = {**self.who, 'job_key': 'JOB_SLOW', 'run': '1', 'access': 'allow', **decided(member=self.who['member'])}
        r = self.client.post('/api/jobs/run', json=d, headers=self.headers('/jobs/run', d))
        self.assertEqual(r.status_code, 202)
        d2 = {**self.who, 'job_key': 'JOB_OTHER', 'run': '1', 'access': 'allow', **decided(member=self.who['member'])}
        self.assertEqual(self.client.post('/api/jobs/run', json=d2, headers=self.headers('/jobs/run', d2)).status_code, 409)
        gate.set()
        for _ in range(100):
            t = self.app.config['slot'].take()
            if t:
                self.app.config['slot'].give_back(t)
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


class SlotNeverLeaks(unittest.TestCase):
    """The third review (2026-10-06): the slot is given back on every exit, and a slot held past a run's own limit plus
    a margin is reclaimed (and logged); a run's files live only in its own private folder, removed on every exit and
    swept when the instance starts."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = host.create_app(self.tmp.name, secret=SECRET)

    def tearDown(self):
        self.tmp.cleanup()

    def _old_run(self, slot, token):
        """A stand-in for a hung sandboxed run: its own process group, attached to the slot as a real run is."""
        proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
        self.addCleanup(lambda: (proc.poll() is None and proc.kill(), proc.wait()))
        threading.Thread(target=proc.wait, daemon=True).start()   # as a real run's own thread waits on its sandbox
        slot.attach(token, proc.pid)
        return proc

    def test_a_slot_held_past_its_limit_is_reclaimed_and_logged(self):
        slot = self.app.config['slot']
        old = slot.take()
        self.assertTrue(old)
        proc = self._old_run(slot, old)
        slot.taken_at -= slot.most_seconds + 1   # held long past the run's own limit plus the margin
        with self.assertLogs('runtime', level='WARNING') as said:
            new = slot.take()
        self.assertTrue(new)
        self.assertTrue(any('reclaimed' in line and 'confirmed gone' in line for line in said.output))
        proc.wait(5)
        self.assertIsNotNone(proc.returncode)    # the old run was killed BEFORE the slot was handed over
        slot.give_back(old)                      # the late run's give-back gives nothing back
        self.assertIsNone(slot.take())           # the new owner still holds it
        slot.give_back(new)
        self.assertTrue(slot.take())

    def test_a_stale_slot_with_no_run_process_is_never_handed_over(self):
        """H4 (the independent review, 2026-10-06): a holder that is the runtime's own code (no process to kill) may still
        be alive, so the slot is refused, not reclaimed, and the instance reports itself stuck for the health check."""
        slot = self.app.config['slot']
        old = slot.take()
        slot.taken_at -= slot.most_seconds + 1
        with self.assertLogs('runtime', level='ERROR'):
            self.assertIsNone(slot.take())
        self.assertTrue(slot.stuck())
        r = self.app.test_client().get('/api/health', headers=self._health_headers())
        self.assertEqual(r.status_code, 503)
        slot.give_back(old)
        self.assertFalse(slot.stuck())

    def _health_headers(self):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return {'X-Office': signing.sign(SECRET, '/health', {}, at), 'X-Office-At': at}

    def test_the_reclaim_limit_sits_above_the_runs_own_hard_limit(self):
        self.assertGreater(self.app.config['slot'].most_seconds, host.CONFIG['run']['seconds'])

    def test_giving_back_twice_never_fails(self):
        slot = self.app.config['slot']
        t = slot.take()
        slot.give_back(t)
        slot.give_back(t)   # a second give-back in a finally must not raise
        t2 = slot.take()
        self.assertTrue(t2)
        slot.give_back(t2)

    def test_a_timed_out_run_leaves_no_folder_behind(self):
        before = {p.name for p in pathlib.Path(sandbox.home()).glob('runtime_*')}   # where this instance makes its run folders (its out/ since 2026-11-10)
        with tempfile.TemporaryDirectory() as a:
            pathlib.Path(a, 'agent.py').write_text('while True:\n    pass\n')
            sandbox.run(a, 'agent.py', {}, seconds=1)
        after = {p.name for p in pathlib.Path(sandbox.home()).glob('runtime_*')}
        self.assertEqual(after - before, set())

    def test_leftover_run_folders_are_swept_at_start(self):
        """A leftover is OLD (a run cut off long ago); a folder made just now is a run in flight on this computer (another
        instance's, a thread's) and the start of an instance never pulls it from under that run."""
        import os, time
        with tempfile.TemporaryDirectory() as t:
            out = pathlib.Path(t, 'out')   # the instance's own run folders (since 2026-11-10)
            out.mkdir()
            old = pathlib.Path(tempfile.mkdtemp(prefix='runtime_run_', dir=out))
            (old / 'input.json').write_text('{"left": "behind"}')
            os.utime(old, (time.time() - 600, time.time() - 600))
            fresh = pathlib.Path(tempfile.mkdtemp(prefix='runtime_run_', dir=out))
            host.create_app(t, secret=SECRET)
            self.assertFalse(old.exists())
            self.assertTrue(fresh.exists())

    def test_a_run_folder_is_private(self):
        made = []
        real = tempfile.mkdtemp
        def watch(*a, **k):
            p = real(*a, **k); made.append(p); return p
        tempfile.mkdtemp = watch
        try:
            with tempfile.TemporaryDirectory() as a:
                pathlib.Path(a, 'agent.py').write_text('import os, sys\nsys.stdout.write("{}")\n')
                sandbox.run(a, 'agent.py', {}, seconds=5)
        finally:
            tempfile.mkdtemp = real
        self.assertTrue(made)
        # every folder a run makes is mkdtemp's: created 0o700 (owner only); none survives the run
        self.assertTrue(all(not os.path.exists(p) for p in made))


class SlotFailsClosed(unittest.TestCase):
    """The fourth review (2026-10-06): any error or doubt while taking the slot refuses the run (409), never runs it;
    two takers at once get one token; two reclaimers of the same stale slot get one token (a compare-and-swap)."""

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

    def test_an_error_reading_the_slot_refuses_the_run(self):
        slot = self.app.config['slot']
        def broken():
            raise OSError('the clock could not be read')
        slot.clock = broken
        self.assertIsNone(slot.take())
        d = {**self.who, 'agent_key': 'AGNT_X'}
        r = self.client.get('/api/agents/answer', query_string=d, headers=self.headers('/agents/answer', d))
        self.assertEqual(r.status_code, 409)
        d = {**self.who, 'job_key': 'JOB_X', 'run': '1', 'access': 'allow', **decided(member=self.who['member'])}
        self.assertEqual(self.client.post('/api/jobs/run', json=d, headers=self.headers('/jobs/run', d)).status_code, 409)
        slot.clock = __import__('time').monotonic   # the clock back: the slot was never left held
        t = slot.take()
        self.assertTrue(t)
        slot.give_back(t)

    def test_two_takers_at_once_get_one_token(self):
        slot, tokens, go = self.app.config['slot'], [], threading.Barrier(8)
        def taker():
            go.wait()
            tokens.append(slot.take())
        threads = [threading.Thread(target=taker) for _ in range(8)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(len([t for t in tokens if t]), 1)

    def test_two_reclaimers_of_one_stale_slot_get_one_token(self):
        slot = self.app.config['slot']
        t = slot.take()
        self.assertTrue(t)
        proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
        self.addCleanup(lambda: (proc.poll() is None and proc.kill(), proc.wait()))
        threading.Thread(target=proc.wait, daemon=True).start()
        slot.attach(t, proc.pid)
        slot.taken_at -= slot.most_seconds + 1
        tokens, go = [], threading.Barrier(8)
        def reclaimer():
            go.wait()
            tokens.append(slot.take())
        threads = [threading.Thread(target=reclaimer) for _ in range(8)]
        with self.assertLogs('runtime', level='WARNING'):
            [t.start() for t in threads]
            [t.join() for t in threads]
        self.assertEqual(len([t for t in tokens if t]), 1)
