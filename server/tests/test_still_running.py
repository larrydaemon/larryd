"""A LONG RUN SAYS IT IS ALIVE (the owner 2026-11-10: "fix the scrum master and all agents"): the platform closes a RUN with nothing
written to its job for 20 minutes (wid atom.STALE_SECONDS), and the night's Web build holds the Judge, about 45 minutes. While the agent
works the runtime writes RUNNING again every ALIVE_SECONDS; once the agent answers, the beat stops before the end is written, so no
RUNNING ever lands after it. The agent's own run is stood in for (the sandbox is not what this proves)."""
import json
import pathlib
import shutil
import tempfile
import threading
import time
import unittest

from _here import APP
from core_engine import harness, locker, store

KEY, JOB = 'MAGT_SCRATCH00001_0001', 'MJOB_SCRATCH00001_0001'
ACCOUNT, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'MCON_' + 'B' * 12 + '_0002'


class Recorder:
    def __init__(self):
        self.said, self.lock = [], threading.Lock()

    def post(self, office, route, data):
        with self.lock:
            self.said.append((office, route, dict(data)))
        return (200, {'charged': 0, 'free': True}) if route == '/jobs/charge' else (200, {'saved': True})


class StillRunning(unittest.TestCase):
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

    def run_for(self, seconds, beat):
        card = {'key': KEY, 'number': '1', 'class': 'MARK II SUPER AGENT (HARNESS)', 'name': 'Scratch', 'screen': 'larryd/agnt/home',
                'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents', 'pitch': '', 'developer': '', 'price': '0',
                'image_dam_key': '', 'type': 'OFF-THE-SHELF', 'residency': 'EXTERNAL', 'status': 'APPROVED'}
        hired = [{'agent_key': KEY, 'board': card['screen'], 'shell_id': 1, 'on': True, 'job_key': JOB}]
        client = Recorder()
        h = harness.Harness(self.db, self.agents, client)
        h.ALIVE_SECONDS = beat
        h.facts = lambda account, scope, member: ([card], hired, [], lambda key: (True, ''))

        def slow(folder, manifest, given):
            time.sleep(seconds)
            return 'DONE', {'delivery': 'done'}, ''
        h._run = slow
        state = h.run_job(ACCOUNT, 'SCRATCH', MEMBER, JOB, 1)
        time.sleep(beat * 2)   # a beat that would come late would land here
        return state, [d for _o, route, d in client.said if route == '/jobs/result']

    def test_a_long_run_writes_running_again_and_nothing_after_its_end(self):
        state, results = self.run_for(0.5, 0.1)
        self.assertEqual(state, 'DONE')
        states = [d['state'] for d in results]
        self.assertGreaterEqual(states.count('RUNNING'), 3, states)   # the first, then the beats
        self.assertEqual(states[-1], 'DONE', states)
        self.assertNotIn('RUNNING', states[states.index('DONE'):], states)
        self.assertTrue(any('still working' in d['log'] for d in results if d['state'] == 'RUNNING'))

    def test_a_short_run_writes_running_once(self):
        state, results = self.run_for(0, 1)
        self.assertEqual([d['state'] for d in results], ['RUNNING', 'DONE'])


if __name__ == '__main__':
    unittest.main()
