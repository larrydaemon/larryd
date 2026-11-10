"""A SLOT HOLDS ITS RUN'S PROCESS, FOR THE RUN'S OWN TIME (OPERATION BDAY SCRUM MASTER 3 HEALTH, item 1, 2026-11-10). On 2026-11-09 the
runtime's log said "slot stuck: held 80 s with no run process to reclaim" 305 times: a RUN's start() took a slot and never told it the
run's process, and the slot's limit was a CALL's (20 s plus a minute) while an internal RUN may work for hours. Now:
- each RUN's process is attached to its own slot (the harness's on_start is the run's own thread's, never another run's or a CALL's);
- a RUN's slot is held for the run's own limit, so three long runs are neither killed nor called stuck after 25 minutes;
- 17 RUNs queued behind them all start once the three end, and none is ended FAILED by the runtime;
- a RUNNING write the platform refuses ends the RUN FAILED with its true reason; the agent never runs; the slot is free again;
- a stuck slot's line says when and which job held it."""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from _here import APP
from _frost import decided
from core_engine import harness, locker, slot as one_slot, store
from web import app as host

SECRET = 'scratch-secret-for-the-slot-held-long-test'
ALLOW = host.CONFIG['access']['grants']
WHO = ('ACCT_000000000001_0001', 'SCRATCH', 'MCON_000000000002_0002')
LONG = 25 * 60


def sleeper(test):
    """A stand-in for a run's own sandboxed process: its own process group, as sandbox.run starts it."""
    proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'], start_new_session=True)
    test.addCleanup(lambda: (proc.poll() is None and proc.kill(), proc.wait()))
    return proc


class ThreeLongRunsSeventeenQueued(unittest.TestCase):
    def setUp(self):
        self.was = os.environ.get('LARRYD_INTERNAL')
        os.environ['LARRYD_INTERNAL'] = '1'   # the runtime on this computer: three slots
        self.tmp = tempfile.TemporaryDirectory()
        self.app = host.create_app(self.tmp.name, secret=SECRET)
        self.h = self.app.config['harness']
        self.slots = self.app.config['slot']
        self.ended, self.started, self.lock = [], [], threading.Lock()
        self.gates, self.procs = {}, {}
        self.h._end = lambda *a, **k: self.ended.append((a[4], a[6], a[7]))   # (job, state, log): a RUN the runtime ends

        def run_job(account, scope, member, job_key, run):
            with self.lock:
                self.started.append(job_key)
            if job_key in self.gates:   # a long run: its process starts (told to the slot as sandbox.run tells it), then it works
                proc = sleeper(self)
                self.procs[job_key] = proc
                self.h.on_start(proc.pid)
                self.gates[job_key].wait(30)
                self.h.on_start(None)
                proc.kill()
                proc.wait()
            return 'DONE'
        self.h.run_job = run_job

    def tearDown(self):
        for g in self.gates.values():
            g.set()
        self.tmp.cleanup()
        if self.was is None:
            os.environ.pop('LARRYD_INTERNAL', None)
        else:
            os.environ['LARRYD_INTERNAL'] = self.was

    def wait_for(self, what, seconds=10):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            if what():
                return True
            time.sleep(0.02)
        return False

    def test_three_long_runs_keep_their_slots_and_the_seventeen_behind_all_run(self):
        self.assertEqual(len(self.slots.slots), 3)
        long_runs = ['LONG_1', 'LONG_2', 'LONG_3']
        for k in long_runs:
            self.gates[k] = threading.Event()
            self.assertIs(self.app.config['start'](*WHO, k, 1), True)
        self.assertTrue(self.wait_for(lambda: all(s.pgid for s in self.slots.slots)),
                        'each long run\'s process is attached to its own slot')
        self.assertEqual(sorted(s.pgid for s in self.slots.slots), sorted(p.pid for p in self.procs.values()))

        for s in self.slots.slots:   # 25 minutes go by
            s.taken_at -= LONG
        self.assertIsNone(self.app.config['start'](*WHO, 'QUEUED_0', 1))   # busy: it waits, nothing is taken from the three
        self.assertFalse(self.slots.stuck(), 'three runs inside their own time are not stuck')
        self.assertTrue(all(p.poll() is None for p in self.procs.values()), 'no long run was killed')

        queue = [{'account': WHO[0], 'scope': WHO[1], 'member': WHO[2], 'job_key': f'QUEUED_{n}', 'run': '1',
                  host.CONFIG['access']['field']: ALLOW, **decided(member=WHO[2])} for n in range(17)]

        class Client:
            def get(self, office, route, data=None):
                return 200, {'jobs': [j for j in queue if j['job_key'] not in started]}
        started = self.started
        self.h.client = Client()

        for g in self.gates.values():   # the three end
            g.set()
        self.assertTrue(self.wait_for(lambda: all(s.owner is None for s in self.slots.slots)), 'the three gave their slots back')
        host.catch_up(self.app, wait=5)
        self.assertTrue(self.wait_for(lambda: all(f'QUEUED_{n}' in self.started for n in range(17))), self.started)
        self.assertEqual(self.ended, [], 'no RUN was ended by the runtime')

    def test_a_stuck_slot_says_when_and_which_job(self):
        s = one_slot.Slots(1, 60)
        t = s.take(label='MJOB_SCRATCH_STUCK#7')
        self.assertTrue(t)
        s.slots[0].taken_at -= 61
        with self.assertLogs('runtime', level='ERROR') as said:
            self.assertIsNone(s.take(label='MJOB_OTHER#1'))
        line = said.output[0]
        self.assertIn('MJOB_SCRATCH_STUCK#7', line)
        self.assertRegex(line, r'20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d')


KEY, JOB = 'MAGT_SCRATCH00001_0001', 'MJOB_SCRATCH00001_0001'
ACCOUNT, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'MCON_' + 'B' * 12 + '_0002'


class Refuses:
    """wid that does not hear the RUNNING write (as on 2026-11-09 at 14:31: a 400, and 'wid does not answer' at other times)."""
    def __init__(self, status, reason):
        self.status, self.reason, self.said = status, reason, []

    def post(self, office, route, data):
        self.said.append((route, dict(data)))
        if route == '/jobs/result' and data.get('state') == 'RUNNING':
            return self.status, {'refused': self.reason}
        return 200, {'saved': True}


class RunningNotWritten(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        (root / 'instance').mkdir()
        self.agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace')
        self.db = store.open_store(root / 'instance')
        locker.add(self.db, self.agents, KEY, 'marketplace')

    def tearDown(self):
        self.tmp.cleanup()

    def run_with(self, client):
        card = {'key': KEY, 'number': '1', 'class': 'MARK II SUPER AGENT (HARNESS)', 'name': 'Scratch', 'screen': 'larryd/agnt/home',
                'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents', 'pitch': '', 'developer': '', 'price': '0',
                'image_dam_key': '', 'type': 'OFF-THE-SHELF', 'residency': 'EXTERNAL', 'status': 'APPROVED'}
        hired = [{'agent_key': KEY, 'board': card['screen'], 'shell_id': 1, 'on': True, 'job_key': JOB}]
        h = harness.Harness(self.db, self.agents, client)
        h.facts = lambda account, scope, member: ([card], hired, [], lambda key: (True, ''))
        ran = []
        h._run = lambda folder, manifest, given: (ran.append(1), ('DONE', {'delivery': 'done'}, ''))[1]
        return h.run_job(ACCOUNT, 'SCRATCH', MEMBER, JOB, 1), ran

    def test_wid_silent_on_running_ends_the_run_failed_with_its_reason(self):
        client = Refuses(502, 'wid does not answer')
        state, ran = self.run_with(client)
        self.assertEqual(state, 'FAILED')
        self.assertEqual(ran, [], 'the agent never runs')
        ends = [d for route, d in client.said if route == '/jobs/result' and d['state'] != 'RUNNING']
        self.assertEqual([d['state'] for d in ends], ['FAILED'])
        self.assertIn('RUNNING', ends[0]['log'])
        self.assertIn('wid does not answer', ends[0]['log'])

    def test_a_run_wid_already_closed_ends_in_one_line_no_trace(self):
        client = Refuses(400, 'RUN 1 is already FAILED')
        with self.assertLogs('runtime', level='WARNING') as said:
            state, ran = self.run_with(client)
        self.assertEqual(state, 'FAILED')
        self.assertEqual(ran, [])
        self.assertTrue(any(JOB in line and 'already FAILED' in line for line in said.output), said.output)


class OnStartIsTheRunsOwn(unittest.TestCase):
    def test_a_call_setting_on_start_never_takes_a_runs(self):
        h = harness.Harness(None, None, None)
        mine, theirs = [], []
        h.on_start = mine.append
        t = threading.Thread(target=lambda: (setattr(h, 'on_start', theirs.append), h.on_start(2), setattr(h, 'on_start', None)))
        t.start()
        t.join()
        h.on_start(1)
        self.assertEqual((mine, theirs), ([1], [2]))


if __name__ == '__main__':
    unittest.main()
