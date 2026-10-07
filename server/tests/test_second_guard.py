"""THE SECOND GUARD (the owner's rule: two guards, never one; frost-0d's offline end to end, step 18): the platform decides
a member's access (FROST's grid) and says so in the signed body of every hire and run (schemas/runtime.json "access":
its field and the one value that grants); the runtime refuses a hire or a run whose signed request does not carry that
decision, before it asks the platform anything or records anything. A vendor the platform let through by mistake is still
refused here."""
import datetime
import json
import sqlite3
import tempfile
import time
import unittest

from _here import APP
from core_engine import signing
from web import app as host

SECRET = 'scratch-secret-for-the-second-guard'
CONF = json.loads((APP / 'schemas' / 'runtime.json').read_text())['access']
WHO = {'account': 'ACCT_000000000001_0001', 'scope': 'SCRATCH', 'member': 'MCON_000000000002_0002'}


class SecondGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = host.create_app(self.tmp.name, secret=SECRET, addresses={})
        self.client = self.app.test_client()
        self.db = self.app.config['harness'].db
        self.started = []
        self.app.config['harness'].run_job = lambda *a: self.started.append(a)   # the run itself is not this test's: only whether it starts

    def tearDown(self):
        self.tmp.cleanup()

    def post(self, route, data):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return self.client.post('/api' + route, json=data, headers={'X-Office': signing.sign(SECRET, route, data, at), 'X-Office-At': at})

    def records(self):
        con = sqlite3.connect(self.db)
        n = con.execute('SELECT COUNT(*) FROM runtime_runs').fetchone()[0]
        con.close()
        return n

    def test_the_decision_is_named_in_the_config(self):
        self.assertEqual(sorted(CONF), ['about', 'field', 'grants'])
        self.assertTrue(CONF['field'] and CONF['grants'])

    def test_a_hire_without_the_decision_is_refused_before_anything(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'on'})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': 'the platform did not grant this member access'}))
        self.assertEqual(self.records(), 0)

    def test_a_hire_with_another_decision_is_refused(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'on', CONF['field']: 'deny'})
        self.assertEqual(r.status_code, 403)

    def test_a_hire_with_the_decision_goes_on_to_the_lanes(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'on', CONF['field']: CONF['grants']})
        self.assertEqual((r.status_code, r.get_json()), (503, {'refused': 'the marketplace is not in the locker'}))   # past the guard

    def test_a_run_without_the_decision_is_refused_and_never_started(self):
        r = self.post('/jobs/run', {**WHO, 'job_key': 'MJOB_00000000000A_0001', 'run': '1'})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': 'the platform did not grant this member access'}))
        self.assertEqual(self.started, [])

    def test_a_run_with_the_decision_starts(self):
        r = self.post('/jobs/run', {**WHO, 'job_key': 'MJOB_00000000000A_0001', 'run': '1', CONF['field']: CONF['grants']})
        self.assertEqual(r.status_code, 202)
        for _ in range(50):
            if self.started:
                break
            time.sleep(0.02)
        self.assertEqual(len(self.started), 1)

    def test_the_decision_is_signed_with_the_rest(self):
        """A decision added after signing breaks the signature: it cannot be put in by anyone but the platform."""
        data = {**WHO, 'job_key': 'MJOB_00000000000A_0001', 'run': '1'}
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        sig = signing.sign(SECRET, '/jobs/run', data, at)
        r = self.client.post('/api/jobs/run', json={**data, CONF['field']: CONF['grants']}, headers={'X-Office': sig, 'X-Office-At': at})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.started, [])


if __name__ == '__main__':
    unittest.main()
