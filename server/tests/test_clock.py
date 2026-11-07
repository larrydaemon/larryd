"""THE CLOCK READER (ONE SYSTEM, 2026-11-07): each job's own clock fields read by due(), and the tick that presses RUN in wid for a
due job whose agent is held and approved, then runs the catch-up. Fake clocks and a fake wid; scratch folders only."""
import datetime
import json
import os
import tempfile
import unittest
from unittest import mock

from _here import APP  # noqa: F401
from core_engine import clock, signing, store
from web import app as host

NY = clock.ZoneInfo('America/New_York')
UTC = datetime.timezone.utc


def ny(y, mo, d, h=0, mi=0):
    return datetime.datetime(y, mo, d, h, mi, tzinfo=NY)


def job(kind, time='06:50', **more):
    return {'data_job_schedule_type': kind, 'data_job_time': time, 'data_job_timezone': 'America/New_York',
            **{f'data_job_{k}': v for k, v in more.items()}}


class Due(unittest.TestCase):
    def test_on_demand_and_manual_never(self):
        for kind in ('on_demand', 'manual', '', 'sometimes'):
            self.assertFalse(clock.due(job(kind), ny(2026, 11, 7, 12), None), kind)

    def test_daily_at_its_time_in_its_zone(self):
        j = job('daily')
        self.assertFalse(clock.due(j, ny(2026, 11, 7, 6, 49), ny(2026, 11, 6, 6, 51)))
        self.assertTrue(clock.due(j, ny(2026, 11, 7, 6, 50), ny(2026, 11, 6, 6, 51)))
        self.assertFalse(clock.due(j, ny(2026, 11, 7, 7, 0), ny(2026, 11, 7, 6, 52)))   # ran since: not again
        utc = datetime.datetime(2026, 11, 7, 11, 50, tzinfo=UTC)   # 06:50 EST is 11:50 UTC
        self.assertTrue(clock.due(j, utc, ny(2026, 11, 6, 7)))
        self.assertFalse(clock.due(j, utc - datetime.timedelta(minutes=1), ny(2026, 11, 6, 7)))

    def test_a_time_missed_while_asleep_fires_once_on_wake(self):
        j = job('daily')
        wake = ny(2026, 11, 9, 10, 0)   # asleep from the 6th at night to the 9th at ten: three 06:50s missed
        self.assertTrue(clock.due(j, wake, ny(2026, 11, 6, 7)))
        self.assertFalse(clock.due(j, wake + datetime.timedelta(minutes=1), wake))   # it ran on wake: the missed ones are not fired again
        self.assertTrue(clock.due(j, ny(2026, 11, 10, 6, 50), wake))

    def test_no_time_never(self):
        self.assertFalse(clock.due(job('daily', time=''), ny(2026, 11, 7, 12), None))
        self.assertFalse(clock.due(job('daily', time='25:00'), ny(2026, 11, 7, 12), None))

    def test_unknown_zone_never(self):
        self.assertFalse(clock.due({**job('daily'), 'data_job_timezone': 'Mars/Olympus'}, ny(2026, 11, 7, 12), None))

    def test_weekly_on_its_day(self):
        j = job('weekly', day_of_week='1')   # 0 = Sunday: 1 = Monday
        self.assertFalse(clock.due(j, ny(2026, 11, 8, 23), ny(2026, 11, 2, 7)))    # Sunday the 8th: last Monday ran
        self.assertTrue(clock.due(j, ny(2026, 11, 9, 6, 50), ny(2026, 11, 2, 7)))  # Monday the 9th
        self.assertFalse(clock.due(j, ny(2026, 11, 12, 9), ny(2026, 11, 9, 7)))
        self.assertEqual(clock.latest(job('weekly', day_of_week='0'), ny(2026, 11, 8, 6, 50)), ny(2026, 11, 8, 6, 50))
        self.assertIsNone(clock.latest(job('weekly', day_of_week=''), ny(2026, 11, 8, 12)))
        self.assertIsNone(clock.latest(job('weekly', day_of_week='7'), ny(2026, 11, 8, 12)))

    def test_monthly_on_its_day_the_last_day_when_shorter(self):
        j = job('monthly', day_of_month='15')
        self.assertTrue(clock.due(j, ny(2026, 11, 15, 6, 50), ny(2026, 10, 15, 7)))
        self.assertFalse(clock.due(j, ny(2026, 11, 14, 23), ny(2026, 10, 15, 7)))
        self.assertEqual(clock.latest(job('monthly', day_of_month='31'), ny(2026, 11, 30, 12)), ny(2026, 11, 30, 6, 50))
        self.assertEqual(clock.latest(job('monthly', day_of_month='31'), ny(2026, 11, 29, 12)), ny(2026, 10, 31, 6, 50))
        self.assertIsNone(clock.latest(job('monthly'), ny(2026, 11, 29, 12)))

    def test_quarterly_on_its_month_and_day(self):
        j = job('quarterly', month_of_quarter='2', day_of_month='10')   # Feb, May, Aug, Nov the 10th
        self.assertEqual(clock.latest(j, ny(2026, 11, 10, 7)), ny(2026, 11, 10, 6, 50))
        self.assertEqual(clock.latest(j, ny(2026, 11, 10, 6)), ny(2026, 8, 10, 6, 50))
        self.assertEqual(clock.latest(j, ny(2026, 12, 31, 23)), ny(2026, 11, 10, 6, 50))
        self.assertEqual(clock.latest(j, ny(2027, 1, 5)), ny(2026, 11, 10, 6, 50))
        self.assertEqual(clock.latest(job('quarterly', month_of_quarter='1', day_of_month='1'), ny(2027, 1, 5)), ny(2027, 1, 1, 6, 50))
        self.assertTrue(clock.due(j, ny(2026, 11, 10, 6, 50), ny(2026, 8, 10, 7)))
        self.assertFalse(clock.due(j, ny(2026, 11, 9, 6, 50), ny(2026, 8, 10, 7)))
        self.assertIsNone(clock.latest(job('quarterly', month_of_quarter='2'), ny(2026, 11, 10, 7)))

    def test_every_n_minutes(self):
        j = job('every 5 minutes', time='')
        self.assertEqual(clock.latest(j, ny(2026, 11, 7, 10, 7)), ny(2026, 11, 7, 10, 5))
        self.assertTrue(clock.due(j, ny(2026, 11, 7, 10, 5), ny(2026, 11, 7, 10, 1)))
        self.assertFalse(clock.due(j, ny(2026, 11, 7, 10, 9), ny(2026, 11, 7, 10, 6)))
        self.assertTrue(clock.due(j, ny(2026, 11, 7, 10, 10), ny(2026, 11, 7, 10, 6)))
        self.assertEqual(clock.latest(job('every 2 hours', time=''), ny(2026, 11, 7, 13, 30)), ny(2026, 11, 7, 12))

    def test_starts_on_and_ends_on(self):
        j = job('daily', starts_on='2026-11-10', ends_on='2026-11-12')
        self.assertFalse(clock.due(j, ny(2026, 11, 9, 12), None))
        self.assertTrue(clock.due(j, ny(2026, 11, 10, 12), None))
        self.assertTrue(clock.due(j, ny(2026, 11, 12, 12), ny(2026, 11, 11, 7)))
        self.assertFalse(clock.due(j, ny(2026, 11, 13, 12), ny(2026, 11, 12, 7)))

    def test_wid_last_run_is_its_own_local_time(self):
        j = {**job('daily'), 'data_job_last_run_at': '2026-11-06 13:46:54'}
        self.assertEqual(clock.last_run_of(j, NY), ny(2026, 11, 6, 13, 46) + datetime.timedelta(seconds=54))
        self.assertIsNone(clock.last_run_of({'data_job_last_run_at': 'not a time'}, NY))


class FakeWid:
    def __init__(self, jobs, answer=(200, {'ok': True, 'text': 'RUN 1 QUEUED'})):
        self.jobs, self.answer, self.pressed = jobs, answer, []

    def scheduled(self):
        return self.jobs

    def press(self, j):
        self.pressed.append(j['job_key'])
        return self.answer


class Tick(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = store.open_store(self.dir.name)
        self.held = {'MAGT_AAAAAAAAAAAA_0001'}
        self.then = []

    def tearDown(self):
        self.dir.cleanup()

    def make(self, wid):
        return clock.Clock(wid, lambda key: (key in self.held, '' if key in self.held else 'not in the locker'), clock.Memory(self.db),
                           then=lambda: self.then.append(1), wid_zone=NY)

    def sm3(self, **more):
        return {'account': 'ACCT', 'scope': 'SYSTEM', 'member': 'MCON', 'job_key': 'scrum_master_3-6', 'agent_key': 'MAGT_AAAAAAAAAAAA_0001',
                **job('daily'), 'data_job_last_run_at': '2026-11-06 07:10:00', **more}

    def test_a_due_job_is_pressed_once_then_the_catch_up(self):
        wid = FakeWid([self.sm3()])
        c = self.make(wid)
        c.memory.seen(self.sm3(), ny(2026, 11, 1))   # the runtime has known this clock since the 1st
        self.assertEqual(c.tick(ny(2026, 11, 7, 6, 49)), [])
        self.assertEqual(c.tick(ny(2026, 11, 7, 6, 50)), [('scrum_master_3-6', 'queued: RUN 1 QUEUED')])
        self.assertEqual(self.then, [1])
        self.assertEqual(c.tick(ny(2026, 11, 7, 6, 51)), [])   # wid's last run is still yesterday's (the RUN is open): never pressed twice
        self.assertEqual(wid.pressed, ['scrum_master_3-6'])
        self.assertEqual(self.then, [1])

    def test_asleep_through_three_moments_one_press_on_wake(self):
        wid = FakeWid([self.sm3()])
        c = self.make(wid)
        c.memory.seen(self.sm3(), ny(2026, 11, 1))
        for minute in range(5):
            c.tick(ny(2026, 11, 9, 10, minute))
        self.assertEqual(wid.pressed, ['scrum_master_3-6'])

    def test_a_job_first_seen_after_its_moment_waits_for_the_next(self):
        wid = FakeWid([self.sm3()])
        c = self.make(wid)
        self.assertEqual(c.tick(ny(2026, 11, 7, 10)), [])
        self.assertEqual(c.tick(ny(2026, 11, 8, 6, 50)), [('scrum_master_3-6', 'queued: RUN 1 QUEUED')])

    def test_an_agent_not_held_is_skipped_by_key_once(self):
        gone = self.sm3(job_key='operations_manager-6', agent_key='MAGT_BBBBBBBBBBBB_0002')
        wid = FakeWid([gone])
        c = self.make(wid)
        c.memory.seen(gone, ny(2026, 11, 1))
        with self.assertLogs('runtime', 'WARNING') as logs:
            self.assertEqual(c.tick(ny(2026, 11, 7, 7)), [('operations_manager-6', 'skipped: not in the locker')])
        self.assertIn('MAGT_BBBBBBBBBBBB_0002', logs.output[0])
        self.assertNotIn('America', logs.output[0])
        self.assertEqual(c.tick(ny(2026, 11, 7, 7, 1)), [])
        self.assertEqual(wid.pressed, [])
        self.assertEqual(self.then, [])

    def test_a_job_with_no_agent_is_skipped(self):
        wid = FakeWid([self.sm3(agent_key='')])
        c = self.make(wid)
        c.memory.seen(self.sm3(), ny(2026, 11, 1))
        self.assertEqual(c.tick(ny(2026, 11, 7, 7)), [('scrum_master_3-6', 'skipped: no agent')])

    def test_on_demand_and_manual_are_never_pressed(self):
        wid = FakeWid([self.sm3(data_job_schedule_type='on_demand'), self.sm3(job_key='m', data_job_schedule_type='manual')])
        c = self.make(wid)
        self.assertEqual(c.tick(ny(2026, 11, 7, 7)), [])
        self.assertEqual(wid.pressed, [])

    def test_wid_refusing_is_one_answer_for_that_moment(self):
        wid = FakeWid([self.sm3()], answer=(200, {'ok': False, 'text': 'RUN 4 IS ALREADY RUNNING'}))
        c = self.make(wid)
        c.memory.seen(self.sm3(), ny(2026, 11, 1))
        self.assertEqual(c.tick(ny(2026, 11, 7, 7)), [('scrum_master_3-6', 'not queued: 200 RUN 4 IS ALREADY RUNNING')])
        c.tick(ny(2026, 11, 7, 7, 1))
        self.assertEqual(wid.pressed, ['scrum_master_3-6'])
        self.assertEqual(self.then, [])

    def test_wid_silent_is_tried_again_next_tick(self):
        wid = FakeWid([self.sm3()], answer=(0, {'refused': 'wid does not answer'}))
        c = self.make(wid)
        c.memory.seen(self.sm3(), ny(2026, 11, 1))
        c.tick(ny(2026, 11, 7, 7))
        wid.answer = (200, {'ok': True, 'text': 'RUN 1 QUEUED'})
        self.assertEqual(c.tick(ny(2026, 11, 7, 7, 1)), [('scrum_master_3-6', 'queued: RUN 1 QUEUED')])
        self.assertEqual(wid.pressed, ['scrum_master_3-6'] * 2)

    def test_the_loop_ticks_until_stopped(self):
        wid = FakeWid([])
        calls = []
        wid.scheduled = lambda: calls.append(1) or []
        stop = clock.threading.Event()
        clocks = clock.Clocks([self.make(wid)])
        ticks = iter(range(3))
        real_wait = stop.wait
        stop.wait = lambda s: (next(ticks, None) is None and stop.set()) or real_wait(0)
        clocks.loop(stop, every=60, now=lambda: ny(2026, 11, 7))
        self.assertEqual(len(calls), 4)

    def test_the_clocks_run_the_catch_up_once_after_a_queued_run(self):
        a, b = FakeWid([self.sm3()]), FakeWid([self.sm3(job_key='other')])
        ca, cb = self.make(a), self.make(b)
        for c, j in ((ca, self.sm3()), (cb, self.sm3(job_key='other'))):
            c.memory.seen(j, ny(2026, 11, 1))
            c.then = None
        caught = []
        said = clock.Clocks([ca, cb], then=lambda: caught.append(1)).tick(ny(2026, 11, 7, 7))
        self.assertEqual(len(said), 2)
        self.assertEqual(caught, [1])


class WidDoors(unittest.TestCase):
    """wid has no door yet that hands the jobs with their clocks: the clock asks, hears the refusal, presses nothing."""
    def test_no_door_no_press(self):
        asked = []

        class Client:
            def get(self, office, route, data=None):
                asked.append((office, route, data))
                return 404, {'refused': 'nothing by that key'}

            def post(self, *a):
                raise AssertionError('nothing is pressed')
        jobs = clock.WidJobs(Client(), internal=True)
        self.assertEqual(jobs.scheduled(), [])
        self.assertEqual(asked, [('wid', '/jobs/scheduled', {'runtime': 'internal'})])
        self.assertEqual(clock.WidJobs(Client()).scheduled(), [])
        self.assertEqual(asked[-1], ('wid', '/jobs/scheduled', None))

    def test_the_press_carries_only_who_and_which_job(self):
        sent = []

        class Client:
            def post(self, office, route, data):
                sent.append((office, route, data))
                return 200, {'ok': True, 'text': 'RUN 2 QUEUED'}
        clock.WidJobs(Client()).press({'account': 'A', 'scope': 'S', 'member': 'M', 'job_key': 'J', 'data_job_time': '06:50', 'agent_key': 'K'})
        self.assertEqual(sent, [('wid', '/jobs/press', {'account': 'A', 'scope': 'S', 'member': 'M', 'job_key': 'J'})])


SECRET = 'scratch-secret-for-the-clock-test'


class TheDoor(unittest.TestCase):
    """POST /api/clock/tick: signed like every call (Cloud Run's Cloud Scheduler), the same clocks the in-process loop ticks."""
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.now = datetime.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
        self.app = host.create_app(self.dir.name, secret=SECRET, now=lambda: self.now)

    def tearDown(self):
        self.dir.cleanup()

    def post(self, data, secret=SECRET):
        at = self.now.isoformat(timespec='seconds')
        return self.app.test_client().post('/api/clock/tick', data=json.dumps(data), content_type='application/json',
                                           headers={'X-Office': signing.sign(secret, '/clock/tick', data, at), 'X-Office-At': at})

    def test_unsigned_is_refused(self):
        self.assertEqual(self.app.test_client().post('/api/clock/tick').status_code, 401)
        self.assertEqual(self.post({}, secret='another').status_code, 401)

    def test_a_signed_tick_with_no_wid_door_presses_nothing(self):
        r = self.post({})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {'ticked': []})

    def test_a_signed_tick_presses_a_due_job_then_catches_up(self):
        wid = FakeWid([{'account': 'A', 'scope': 'S', 'member': 'M', 'job_key': 'J', 'agent_key': 'K', **job('daily', time='06:00')}])
        c = self.app.config['clocks'].clocks[0]
        c.jobs, c.held = wid, (lambda key: (True, ''))
        c.memory.seen({'account': 'A', 'scope': 'S', 'job_key': 'J'}, self.now - datetime.timedelta(days=2))
        caught = []
        self.app.config['clocks'].then = lambda: caught.append(1)
        r = self.post({})
        self.assertEqual(r.get_json(), {'ticked': [{'job_key': 'J', 'said': 'queued: RUN 1 QUEUED'}]})
        self.assertEqual(caught, [1])

    def test_the_loop_starts_in_process_only_on_the_internal_runtime(self):
        started = []
        for internal in (False, True):
            with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(clock.Clocks, 'start', lambda self, every=60: started.append(internal)), \
                    mock.patch.object(host, 'catch_up', lambda app: 0), mock.patch.object(host.Flask, 'run', lambda *a, **k: None), \
                    mock.patch.object(host, 'INSTANCE', __import__('pathlib').Path(self.dir.name)):
                os.environ.pop('LARRYD_INTERNAL', None)
                os.environ.pop('LARRYD_KEYS_DIR', None)
                if internal:
                    os.environ['LARRYD_INTERNAL'] = '1'
                (__import__('pathlib').Path(self.dir.name) / 'secrets').mkdir(exist_ok=True)
                (__import__('pathlib').Path(self.dir.name) / 'secrets' / host.CONFIG['secret']['name']).write_text(SECRET)
                host.main(['app.py'])
        self.assertEqual(started, [True])


if __name__ == '__main__':
    unittest.main()
