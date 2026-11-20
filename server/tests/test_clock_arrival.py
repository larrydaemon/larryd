"""ON ARRIVAL (core_engine/clock.py; THE PUSH STANDARD, the owner 2026-11-20): a job whose schedule type is `on arrival <name>` is
pressed when its mark in the runtime's data was touched, once, and never by the time of day; nothing arrived, nothing pressed.
Fake wid, scratch folders only."""
import datetime
import os
import tempfile
import threading
import time
import unittest
from unittest import mock

from _here import APP  # noqa: F401
from core_engine import clock

UTC = datetime.timezone.utc
JOB = {'account': 'ACCT_SCRATCH', 'scope': 'SCRATCH', 'member': 'MCON_SCRATCH', 'job_key': 'MJOB_SCRATCH_PUSH', 'agent_key': 'MAGT_BD6B28F6EE0A_F74E',
       'data_job_schedule_type': 'on arrival push', 'data_job_timezone': 'America/New_York'}


class Wid:
    def __init__(self, jobs):
        self.jobs, self.pressed = jobs, []

    def scheduled(self):
        return self.jobs

    def press(self, job):
        self.pressed.append(job['job_key'])
        return 200, {'ok': True, 'text': 'queued'}


class Memory:
    def __init__(self):
        self.held = {}

    def get(self, job):
        return self.held.get(job['job_key'])

    def seen(self, job, now):
        self.held[job['job_key']] = (now, None)

    def pressed(self, job, moment):
        self.held[job['job_key']] = (self.held[job['job_key']][0], moment)


class OnArrival(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = mock.patch.dict(os.environ, {'OFFICE_DATA': self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.wid, self.ran = Wid([dict(JOB)]), []
        self.clock = clock.Clock(self.wid, lambda agent: (True, ''), Memory(), then=lambda: self.ran.append(1))
        self.at = datetime.datetime(2026, 11, 20, 18, 0, tzinfo=UTC)

    def touch(self, name, at):
        os.makedirs(os.path.join(self.tmp.name, 'arrivals'), exist_ok=True)
        path = os.path.join(self.tmp.name, 'arrivals', name)
        open(path, 'a').close()
        os.utime(path, (at.timestamp(), at.timestamp()))

    def minutes(self, n):
        return self.at + datetime.timedelta(minutes=n)

    def test_nothing_arrived_nothing_is_pressed_however_long(self):
        for n in (0, 1, 60, 60 * 24 * 90):   # a quiet account for months
            self.assertEqual(self.clock.tick(self.minutes(n)), [])
        self.assertEqual((self.wid.pressed, self.ran), ([], []))

    def test_an_arrival_is_pressed_once_and_the_next_one_again(self):
        self.clock.tick(self.at)                                  # the job is seen
        self.touch('push', self.minutes(5))
        self.assertEqual(self.clock.tick(self.minutes(5)), [('MJOB_SCRATCH_PUSH', 'queued: queued')])
        self.assertEqual(self.clock.tick(self.minutes(6)), [])    # the same arrival is never pressed twice
        self.assertEqual(self.clock.tick(self.minutes(600)), [])
        self.touch('push', self.minutes(700))
        self.assertEqual(len(self.clock.tick(self.minutes(700))), 1)
        self.assertEqual((self.wid.pressed, len(self.ran)), (['MJOB_SCRATCH_PUSH'] * 2, 2))

    def test_an_arrival_before_the_runtime_first_saw_the_job_waits_for_the_next(self):
        self.touch('push', self.minutes(-30))
        self.assertEqual(self.clock.tick(self.at), [])
        self.touch('push', self.minutes(1))
        self.assertEqual(len(self.clock.tick(self.minutes(1))), 1)

    def test_a_run_since_the_arrival_means_it_is_done(self):
        self.clock.tick(self.at)
        self.touch('push', self.minutes(5))
        ran = self.minutes(6).astimezone(self.clock.wid_zone).strftime('%Y-%m-%d %H:%M:%S')   # the member pressed RUN themselves meanwhile
        self.wid.jobs[0]['data_job_last_run_at'] = ran
        self.assertEqual(self.clock.tick(self.minutes(7)), [])

    def test_only_its_own_mark_and_only_a_plain_name(self):
        self.clock.tick(self.at)
        self.touch('mail', self.minutes(5))
        self.assertEqual(self.clock.tick(self.minutes(5)), [])
        for kind in ('on arrival', 'on arrival ../push', 'on arrival Push', 'on arrival push now', 'on arrival /etc/passwd'):
            self.assertIsNone(clock.latest({**JOB, 'data_job_schedule_type': kind}, self.minutes(9)), kind)

    def test_its_dates_still_hold(self):
        self.clock.tick(self.at)
        self.wid.jobs[0]['data_job_ends_on'] = '2026-11-19'
        self.touch('push', self.minutes(5))
        self.assertEqual(self.clock.tick(self.minutes(5)), [])

    def test_a_runtime_with_no_data_folder_never_fires_one(self):
        with mock.patch.dict(os.environ, {'OFFICE_DATA': '', 'LARRYD_INSTANCE': ''}):
            self.assertEqual((clock.arrivals(), clock.arrived('push'), clock.changed()), ('', None, ()))
            self.assertIsNone(clock.latest(JOB, self.at))

    def test_the_other_kinds_are_as_before(self):
        every = {'data_job_schedule_type': 'every 5 minutes', 'data_job_timezone': 'America/New_York'}
        self.assertIsNotNone(clock.latest(every, self.at))
        self.assertIsNone(clock.latest({'data_job_schedule_type': 'on_demand'}, self.at))

    def test_the_loop_ticks_at_once_when_a_mark_is_touched(self):
        ticks = []

        class Counting:
            def tick(_self, now):
                ticks.append(time.monotonic())
                return []
        stop = threading.Event()
        thread = threading.Thread(target=clock.Clocks([Counting()]).loop, args=(stop, 60), daemon=True)
        began = time.monotonic()
        thread.start()
        time.sleep(0.3)
        self.touch('push', datetime.datetime.now(UTC))
        for _ in range(40):
            if len(ticks) >= 2:
                break
            time.sleep(0.1)
        stop.set()
        thread.join(5)
        self.assertGreaterEqual(len(ticks), 2)
        self.assertLess(ticks[1] - began, 4)   # not the 60 s wait: within seconds of the arrival


if __name__ == '__main__':
    unittest.main()
