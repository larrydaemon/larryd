"""A RUN ON A THREAD IN KEYS MODE (frost-0d's final e2e, 2026-10-06): a keys-mode runtime with no job starter (LARRYD_JOB
unset) runs the RUN on a thread here; that thread must run it on THE CALLER's harness (its calls back to that slot,
signed with the runtime's key for it), never the default one, which has no platform and ends CALLBACK_FAILED with the
member's RUN left QUEUED. A caller with no harness is refused before the slot is taken or a thread exists."""
import pathlib
import time
import unittest

from _here import APP  # noqa: F401
from _frost import decided
from core_engine import callers, jobs, records as run_records
from test_review_fixes import CloudApp, Exists
from web import app as host

WHO = {'account': 'ACCT_00000000000A_000A', 'scope': 'S', 'member': 'MCON_00000000000B_000B'}


class ThreadCaller(CloudApp):
    def make_threaded(self):
        """Keys mode, both slots' keys, NO job starter: the run goes on a thread here."""
        cloud = {'outbound': callers.Outbound(self.out_dir), 'records': run_records.FirestoreRecords(col=self.runs),
                 'lockers': None, 'claims': jobs.FirestoreClaims(col=self.claims_col, exists=Exists), 'jobs': None}
        d = pathlib.Path(self.dir.name) / 'threaded'
        d.mkdir()
        app = host.create_app(str(d), secret='', now=lambda: self.now, keys=callers.Keys(self.keys_dir), nonces=callers.MemoryNonces(),
                              agents=d / 'agents', cloud=cloud)
        self.ran = []
        app.config['harness'].run_job = lambda *a: self.ran.append(('default',) + a)
        for caller, h in app.config['harnesses'].items():
            h.run_job = (lambda c: (lambda *a: self.ran.append((c,) + a)))(caller)
        return app

    def wait(self):
        for _ in range(100):
            if self.ran:
                return
            time.sleep(0.02)

    def test_a_threaded_run_goes_on_the_callers_harness(self):
        app = self.make_threaded()
        r = self.call(app, '/jobs/run', {**WHO, 'job_key': 'MJOB_000000000001_0001', 'run': '1', 'access': 'allow', **decided(member=WHO['member'])}, 'POST', slot='slot-b')
        self.assertEqual(r.status_code, 202)
        self.wait()
        self.assertEqual([x[0] for x in self.ran], ['slot-b'])   # never 'default'

    def test_each_slot_its_own(self):
        app = self.make_threaded()
        self.call(app, '/jobs/run', {**WHO, 'job_key': 'MJOB_000000000002_0001', 'run': '1', 'access': 'allow', **decided(member=WHO['member'])}, 'POST', slot='slot-a')
        self.wait()
        self.assertEqual([x[0] for x in self.ran], ['slot-a'])

    def test_a_caller_without_a_harness_is_refused_before_the_slot(self):
        app = self.make_threaded()
        start = app.config['start']
        with self.assertRaises(Exception) as no:
            start(WHO['account'], WHO['scope'], WHO['member'], 'MJOB_000000000003_0001', 1, 'proof')   # no keys for proof here
        self.assertIn('no harness', str(no.exception))
        self.assertTrue(app.config['slot'].take())   # the slot was never taken
        self.assertEqual(self.ran, [])


if __name__ == '__main__':
    unittest.main()
