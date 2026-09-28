"""The lanes at HANZO's door, where no platform is needed to prove them: the refusals, and a RUN whose platform is
silent (a real closed port) ending FAILED with its reason, recorded. What the platform answers is proven live only."""
import datetime
import socket
import sqlite3
import tempfile
import time
import unittest

from _here import APP
from core_engine import locker, signing
from web import app as host

SECRET = 'scratch-secret-for-the-lanes-test'


def _closed_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class HostLanes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        silent = f'http://127.0.0.1:{_closed_port()}'
        self.app = host.create_app(self.tmp.name, secret=SECRET, addresses={'wid': silent, 'cc': silent})
        self.client = self.app.test_client()
        self.db = self.app.config['harness'].db
        self.who = {'account': 'ACCT_000000000001_0001', 'scope': 'SCRATCH', 'member': 'MCON_000000000002_0002'}

    def tearDown(self):
        self.tmp.cleanup()

    def _headers(self, route, data):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return {'X-Office': signing.sign(SECRET, route, data, at), 'X-Office-At': at}

    def get(self, route, data):
        return self.client.get('/api' + route, query_string=data, headers=self._headers(route, data))

    def post(self, route, data):
        return self.client.post('/api' + route, json=data, headers=self._headers(route, data))

    def test_an_agent_not_in_the_locker_answers_nothing(self):
        r = self.get('/agents/answer', {**self.who, 'agent_key': 'MAGT_SCRATCH00001_0001'})
        self.assertEqual((r.status_code, r.get_json()), (404, {'refused': 'no agent that answers here'}))

    def test_a_silent_platform_is_said(self):
        locker.add(self.db, APP / 'agents', 'MAGT_SCRATCH00001_0001', 'marketplace')
        r = self.get('/agents/answer', {**self.who, 'agent_key': 'MAGT_SCRATCH00001_0001'})
        self.assertEqual((r.status_code, r.get_json()), (502, {'refused': 'wid does not answer'}))

    def test_hire_and_defaults_need_the_marketplace_and_the_platform(self):
        r = self.post('/agents/defaults', {**self.who, 'board': 'larryd/agnt/home'})
        self.assertEqual((r.status_code, r.get_json()), (503, {'refused': 'the marketplace is not in the locker'}))
        r = self.post('/agents/hire', {**self.who, 'agent_key': 'K', 'on': 'on'})
        self.assertEqual((r.status_code, r.get_json()), (503, {'refused': 'the marketplace is not in the locker'}))
        locker.add(self.db, APP / 'agents', 'MAGT_SCRATCH00001_0001', 'marketplace')
        r = self.post('/agents/defaults', {**self.who, 'board': 'larryd/agnt/home'})
        self.assertEqual((r.status_code, r.get_json()), (502, {'refused': 'wid does not answer'}))

    def test_what_a_call_must_carry(self):
        r = self.get('/agents/answer', {'account': 'A'})
        self.assertEqual((r.status_code, r.get_json()), (400, {'refused': 'missing: scope, member, agent_key'}))
        r = self.post('/agents/hire', {**self.who, 'agent_key': 'K', 'on': 'yes'})
        self.assertEqual((r.status_code, r.get_json()), (400, {'refused': 'on is "on" or "off"'}))
        r = self.post('/agents/defaults', self.who)
        self.assertEqual((r.status_code, r.get_json()), (400, {'refused': 'missing: board'}))
        r = self.post('/jobs/run', {**self.who, 'job_key': 'J', 'run': 'one'})
        self.assertEqual((r.status_code, r.get_json()), (400, {'refused': 'run is the RUN number'}))

    def test_a_run_with_a_silent_platform_fails_and_is_recorded(self):
        r = self.post('/jobs/run', {**self.who, 'job_key': 'MJOB_000000000009_0009', 'run': '1'})
        self.assertEqual((r.status_code, r.get_json()), (202, {'accepted': 'MJOB_000000000009_0009', 'run': 1, 'already': False}))
        for _ in range(100):
            con = sqlite3.connect(self.db)
            row = con.execute('SELECT lane, job_key, run, state, reason FROM hanzo_runs').fetchone()
            con.close()
            if row:
                break
            time.sleep(0.05)
        self.assertEqual(row, ('job', 'MJOB_000000000009_0009', 1, 'FAILED',
                               'HANZO could not read the platform: wid does not answer · the platform did not take the result: wid does not answer'))


if __name__ == '__main__':
    unittest.main()
