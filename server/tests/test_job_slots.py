"""THE JOB'S SLOTS (the owner 2026-11-05: "all of the agents need to be updated to use all the new slots we added in the ai atom jobs
view"): an agent's answer may give `job`, an object of its job's slots, when its "gives" names it; the runtime passes it to wid's
/jobs/result beside the delivery (wid keeps only the slots an agent fills), never inside the delivery. The agent's own run is stood in
for (the sandbox is not what this proves)."""
import json
import pathlib
import shutil
import tempfile
import unittest

from _here import APP
from core_engine import harness, locker, store

KEY, JOB = 'MAGT_SCRATCH00001_0001', 'MJOB_SCRATCH00001_0001'
ACCOUNT, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'MCON_' + 'B' * 12 + '_0002'


class Recorder:
    def __init__(self):
        self.said = []

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return (200, {'charged': 0, 'free': True}) if route == '/jobs/charge' else (200, {'saved': True})


class JobSlots(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        (root / 'instance').mkdir()
        self.agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace')
        manifest = self.agents / 'marketplace' / 'agent.json'
        card = json.loads(manifest.read_text())
        card['gives'] = card['gives'] + ['job']
        manifest.write_text(json.dumps(card))
        self.db = store.open_store(root / 'instance')
        locker.add(self.db, self.agents, KEY, 'marketplace')

    def tearDown(self):
        self.tmp.cleanup()

    def run_with(self, answer):
        card = {'key': KEY, 'number': '1', 'class': 'MARK II SUPER AGENT (HARNESS)', 'name': 'Scratch', 'screen': 'larryd/agnt/home',
                'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents', 'pitch': '', 'developer': '', 'price': '0',
                'image_dam_key': '', 'type': 'OFF-THE-SHELF', 'residency': 'EXTERNAL', 'status': 'APPROVED'}
        hired = [{'agent_key': KEY, 'board': card['screen'], 'shell_id': 1, 'on': True, 'job_key': JOB}]
        client = Recorder()
        h = harness.Harness(self.db, self.agents, client)
        h.facts = lambda account, scope, member: ([card], hired, [], lambda key: (True, ''))
        h._run = lambda folder, manifest, given: ('DONE', answer, '')
        state = h.run_job(ACCOUNT, 'SCRATCH', MEMBER, JOB, 1)
        ends = [d for _o, route, d in client.said if route == '/jobs/result' and d['state'] != 'RUNNING']
        return state, ends[-1]

    def test_the_answers_job_goes_to_wid_beside_the_delivery(self):
        slots = {'data_job_lineage': 'MAGT_SCRATCH00001_0001 > report', 'data_job_payload': 'collection of 1'}
        state, said = self.run_with({'delivery': 'one card', 'job': slots})
        self.assertEqual(state, 'DONE')
        self.assertEqual(said['job'], slots)
        self.assertEqual(said['delivery'], 'one card')

    def test_the_job_never_rides_inside_a_made_delivery(self):
        state, said = self.run_with({'total': 1, 'job': {'data_job_payload': 'p'}})
        self.assertEqual(state, 'DONE')
        self.assertEqual(json.loads(said['delivery']), {'total': 1})
        self.assertEqual(said['job'], {'data_job_payload': 'p'})

    def test_an_answer_without_job_sends_none(self):
        state, said = self.run_with({'delivery': 'one card'})
        self.assertEqual(state, 'DONE')
        self.assertNotIn('job', said)

    def test_a_job_that_is_not_an_object_fails_the_run(self):
        state, said = self.run_with({'delivery': 'one card', 'job': ['data_job_payload']})
        self.assertEqual(state, 'FAILED')
        self.assertNotIn('job', said)
        self.assertIn('not an object of slots', said['log'])

    def test_a_job_its_gives_does_not_name_is_refused(self):
        manifest = self.agents / 'marketplace' / 'agent.json'
        card = json.loads(manifest.read_text())
        card['gives'].remove('job')
        manifest.write_text(json.dumps(card))   # the run reads the locker's manifest as it stands
        state, said = self.run_with({'delivery': 'one card', 'job': {'data_job_payload': 'p'}})
        self.assertEqual(state, 'FAILED')
        self.assertNotIn('job', said)


if __name__ == '__main__':
    unittest.main()
