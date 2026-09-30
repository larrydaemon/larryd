"""THE JOB'S INPUTS (hands ["job"]): an agent declares its inputs {name: slot 001-015}; on a RUN, HANZO reads that RUN's
inputs from wid (/jobs/inputs), hands them in as job = {name: value}, and keeps none of them (data stays in wid). Refused:
an input the agent does not declare, a value too large or not text; failed: wid silent, inputs not declared right.
wid here is a Recorder (in this process, it answers only what the test gives it); what wid answers is proven live only."""
import json
import pathlib
import shutil
import socket
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import harness, locker, platform, store

KEY = 'MAGT_00000000D0B1_0001'
JOB = 'MJOB_00000000D0B1_0001'
ACCOUNT, SCOPE, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'SCRATCH', 'MCON_' + 'B' * 12 + '_0002'
PLANTED = 'Zanzibar-7731-private-mood'
CARD = {'key': KEY, 'number': '2', 'class': 'MARK I AGENT (NORMAL)', 'name': 'Echo', 'screen': 'larryd/agnt/home', 'product': 'LARRYD',
        'product_slug': 'larryd', 'module': 'Agents', 'pitch': '', 'developer': '', 'price': '0', 'image_dam_key': '', 'type': '',
        'residency': '', 'status': 'LIVE'}
HIRED = [{'agent_key': KEY, 'board': CARD['screen'], 'shell_id': 1, 'on': True, 'job_key': JOB}]


def _closed_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Wid:
    """wid as a Recorder: /jobs/inputs answers what the test gives it; every call is recorded."""
    def __init__(self, inputs, status=200):
        self.inputs, self.status, self.said = inputs, status, []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        return self.status, ({'inputs': self.inputs} if self.status == 200 else {'refused': 'RUN 1 is already DONE'})

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return (200, {'charged': 0, 'free': True}) if route == '/mtok/use' else (200, {'saved': True})


class JobInputs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.instance = pathlib.Path(self.tmp.name) / 'instance'
        self.instance.mkdir()
        self.agents = pathlib.Path(self.tmp.name) / 'agents'
        self.db = store.open_store(self.instance)

    def tearDown(self):
        self.tmp.cleanup()

    def agent(self, inputs=None, hands=('job',)):
        folder = self.agents / 'echo'
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        manifest = {'name': 'Echo', 'entry': 'agent.py', 'run': {'do': 'answer', 'hands': list(hands)}}
        if inputs is not None:
            manifest['inputs'] = inputs
        (folder / 'agent.json').write_text(json.dumps(manifest))
        (folder / 'agent.py').write_text('import json, sys\njob = json.load(sys.stdin)\nprint(json.dumps({"delivery": json.dumps(job.get("job"), sort_keys=True)}))\n')
        con = __import__('sqlite3').connect(self.db)
        con.execute('DELETE FROM hanzo_locker')
        con.commit()
        con.close()
        locker.add(self.db, self.agents, KEY, 'echo')

    def run_with(self, client):
        h = harness.Harness(self.db, self.agents, client)
        h.facts = lambda account, scope, member: ([CARD], HIRED, [], lambda key: (True, ''))   # the platform's word, as it would answer
        return h.run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1)

    @staticmethod
    def results(wid):
        return [d for _o, route, d in wid.said if route == '/jobs/result']

    def test_the_inputs_are_handed_by_name(self):
        self.agent({'name': '001', 'mood': '002', 'seed': '003'})
        wid = Wid({'001': 'Harbor', '002': PLANTED})
        self.assertEqual(self.run_with(wid), 'DONE')
        asked = [d for _o, route, d in wid.said if route == '/jobs/inputs']
        self.assertEqual(asked, [{'account': ACCOUNT, 'scope': SCOPE, 'job_key': JOB, 'run': '1'}])   # this RUN only
        done = self.results(wid)[-1]
        self.assertEqual((done['state'], json.loads(done['delivery'])), ('DONE', {'mood': PLANTED, 'name': 'Harbor'}))   # seed not filled: not handed
        for path in self.instance.rglob('*'):
            if path.is_file():
                self.assertNotIn(PLANTED.encode(), path.read_bytes(), f'{path.name} keeps an input')

    def test_an_input_the_agent_does_not_declare_is_refused(self):
        self.agent({'name': '001'})
        wid = Wid({'001': 'Harbor', '004': PLANTED})
        self.assertEqual(self.run_with(wid), 'REFUSED')
        end = self.results(wid)
        self.assertEqual([r['state'] for r in end], ['REFUSED'])   # never RUNNING: the agent did not run
        self.assertEqual(end[0]['log'], 'the job holds input 004, which the agent does not declare')
        self.assertNotIn(PLANTED, json.dumps(wid.said[-1]))

    def test_a_value_too_large_or_not_text_is_refused(self):
        self.agent({'name': '001'})
        wid = Wid({'001': 'x' * (harness.MOST_INPUT + 1)})
        self.assertEqual(self.run_with(wid), 'REFUSED')
        self.assertEqual(self.results(wid)[-1]['log'], f'input 001 is larger than {harness.MOST_INPUT} characters')
        wid = Wid({'001': 7})
        self.assertEqual(self.run_with(wid), 'REFUSED')
        self.assertEqual(self.results(wid)[-1]['log'], 'input 001 is not text')

    def test_a_silent_or_refusing_wid_fails_the_run(self):
        self.agent({'name': '001'})
        silent = platform.Client({'wid': f'http://127.0.0.1:{_closed_port()}', 'cc': f'http://127.0.0.1:{_closed_port()}'}, 'scratch', timeout=2)
        self.assertEqual(self.run_with(silent), 'FAILED')
        con = __import__('sqlite3').connect(self.db)
        reason = con.execute("SELECT reason FROM hanzo_runs WHERE lane = 'job' ORDER BY id DESC").fetchone()[0]
        con.close()
        self.assertTrue(reason.startswith("HANZO could not read the job's inputs: wid does not answer"), reason)
        wid = Wid({}, status=400)
        self.assertEqual(self.run_with(wid), 'FAILED')
        self.assertIn('RUN 1 is already DONE', self.results(wid)[-1]['log'])

    def test_inputs_not_declared_right_fail_before_wid_is_asked(self):
        for bad in ({}, {'name': '016'}, {'name': '1'}, {'name': '001', 'mood': '001'}, {'not a name': '001'}, ['001'], None):
            with self.subTest(bad):
                self.agent(bad)
                wid = Wid({'001': 'Harbor'})
                self.assertEqual(self.run_with(wid), 'FAILED')
                self.assertFalse([r for _o, r, _d in wid.said if r == '/jobs/inputs'])

    def test_an_agent_without_the_job_hand_never_asks_for_inputs(self):
        self.agent({'name': '001'}, hands=())
        wid = Wid({'001': PLANTED})
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertFalse([r for _o, r, _d in wid.said if r == '/jobs/inputs'])
        self.assertEqual(json.loads(self.results(wid)[-1]['delivery']), None)

    def test_a_hand_hanzo_does_not_have_still_fails(self):
        self.agent({'name': '001'}, hands=('members',))
        wid = Wid({})
        self.assertEqual(self.run_with(wid), 'FAILED')
        self.assertEqual(self.results(wid)[-1]['log'], "HANZO cannot hand ['members'] yet")


if __name__ == '__main__':
    unittest.main()
