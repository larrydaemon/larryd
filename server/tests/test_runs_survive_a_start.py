"""A RUN IN FLIGHT SURVIVES ANOTHER RUNTIME'S START, AND NEVER HANGS (OPERATION BDAY SCRUM MASTER 3 HEALTH, item 1, 2026-11-10 12:08).
A second runtime started on this computer while the first still ran two RUNs (Build, RUN 6, and MJOB_E1526F4436D7_E80C, RUN 4): its
start swept every run folder older than 120 s, the two live runs' output folders among them (an internal RUN writes its answer only at
its end, so its folder looks old), and each run's thread died on FileNotFoundError with nothing written: both RUNs stayed RUNNING.
Now, on this computer, the start spares any run folder younger than the longest a RUN may live (an internal agent's 6 hours plus a
minute), and a RUN whose thread meets any error is ended FAILED with that error, its slot given back."""
import os
import pathlib
import tempfile
import threading
import time
import unittest

from _here import APP  # noqa: F401
from core_engine import sandbox
from web import app as host

SECRET = 'scratch-secret-for-the-sweep-test'
WHO = ('ACCT_000000000001_0001', 'SCRATCH', 'MCON_000000000002_0002')


def folder(age_seconds, instance):
    out = pathlib.Path(instance, 'out')   # the instance's own run folders (since 2026-11-10)
    out.mkdir(exist_ok=True)
    p = pathlib.Path(tempfile.mkdtemp(prefix='runtime_out_s1test_', dir=out))
    (p / 'kept').write_text('a run in flight')
    at = time.time() - age_seconds
    os.utime(p, (at, at))
    return p


class InternalStart(unittest.TestCase):
    def setUp(self):
        self.was = os.environ.get('LARRYD_INTERNAL')
        os.environ['LARRYD_INTERNAL'] = '1'
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()
        if self.was is None:
            os.environ.pop('LARRYD_INTERNAL', None)
        else:
            os.environ['LARRYD_INTERNAL'] = self.was

    def test_a_ten_minute_old_run_folder_survives_a_start(self):
        live = folder(10 * 60, self.tmp.name)
        self.addCleanup(lambda: __import__('shutil').rmtree(live, ignore_errors=True))
        host.create_app(self.tmp.name, secret=SECRET)
        self.assertTrue(live.is_dir(), 'a run in flight lost its folder to another runtime\'s start')

    def test_a_folder_older_than_the_longest_run_is_still_swept(self):
        gone = folder(7 * 3600, self.tmp.name)
        self.addCleanup(lambda: __import__('shutil').rmtree(gone, ignore_errors=True))
        host.create_app(self.tmp.name, secret=SECRET)
        self.assertFalse(gone.exists())

    def test_a_run_that_meets_any_error_is_ended_failed_and_frees_its_slot(self):
        app = host.create_app(self.tmp.name, secret=SECRET)
        h, slots, ended, done = app.config['harness'], app.config['slot'], [], threading.Event()

        def broken(*a):
            raise FileNotFoundError('[Errno 2] No such file or directory: runtime_out_x/out')
        h.run_job = broken
        h._end = lambda *a, **k: (ended.append((a[4], a[5], a[6], a[7])), done.set())
        self.assertIs(app.config['start'](*WHO, 'MJOB_SCRATCH_BROKEN', 4), True)
        self.assertTrue(done.wait(5), 'the RUN was never ended')
        self.assertEqual(ended[0][:3], ('MJOB_SCRATCH_BROKEN', 4, 'FAILED'))
        self.assertIn('FileNotFoundError', ended[0][3])
        until = time.monotonic() + 5
        while time.monotonic() < until and any(s.owner is not None for s in slots.slots):
            time.sleep(0.02)
        self.assertTrue(all(s.owner is None for s in slots.slots), 'the slot was not given back')


class CloudStart(unittest.TestCase):
    def test_the_cloud_keeps_its_short_sweep(self):
        self.assertEqual(sandbox.sweep.__defaults__[0], 120)


if __name__ == '__main__':
    unittest.main()
