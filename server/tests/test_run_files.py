"""THE MEMBER'S FILES ON A RUN (hands ["job", "files"], CORE_CLEANUP_IV 21, the owner's blanket approval 2026-11-06): an agent names
which of its job inputs carry a DA-M key ("files": [name, ...]); on a RUN each one the member filled is read through wid's job file door
(/jobs/file) for this member while the RUN is open and handed as files = {name: {dam_key, kind, bytes, content_b64}}; an empty input is
not handed; nothing is kept. Stopped before the agent runs: files not declared right, an input that is not a DA-M key, a file wid does
not hand, a file over the limit. wid here is a Recorder (this process); what wid and DA-M answer is proven live only."""
import base64
import json
import shutil
import sqlite3
import unittest

from _here import APP  # noqa: F401
from core_engine import harness, locker
from test_job_inputs import ACCOUNT, JOB, KEY, MEMBER, SCOPE, Echo

PNG = b'\x89PNG\r\n\x1a\n' + b'Zanzibar-7731-private-picture' * 10
PIC = 'DA-M_' + 'E' * 12 + '_0005'


class Wid:
    """wid as a Recorder: /jobs/inputs and /jobs/file answer what the test gives them; every call is recorded."""
    def __init__(self, inputs, files, status=200):
        self.inputs, self.files, self.status, self.said = inputs, files, status, []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        if route == '/jobs/inputs':
            return 200, {'inputs': self.inputs}
        if route == '/jobs/file':
            if self.status != 200 or data['dam_key'] not in self.files:
                return 404, {'refused': 'not a file of this member'}
            return 200, {'content_b64': base64.b64encode(self.files[data['dam_key']]).decode()}
        return 200, {}

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return (200, {'charged': 0, 'free': True}) if route == '/jobs/charge' else (200, {'saved': True})


class RunFiles(Echo):
    def agent(self, files=('picture',), hands=('job', 'files'), inputs=None):
        folder = self.agents / 'echo'
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        manifest = {'name': 'Echo', 'entry': 'agent.py', 'run': {'do': 'answer', 'hands': list(hands)}, 'gives': ['delivery'],
                    'inputs': inputs or {'picture': '001', 'task': '002'}}
        if files is not None:
            manifest['files'] = list(files)
        (folder / 'agent.json').write_text(json.dumps(manifest))
        (folder / 'agent.py').write_text('import base64, json, sys\ng = json.load(sys.stdin)\nf = g.get("files")\n'
                                         'out = None if f is None else {n: {**v, "same": base64.b64decode(v["content_b64"])[:8].hex()} for n, v in f.items()}\n'
                                         'print(json.dumps({"delivery": json.dumps(out, sort_keys=True)}))\n')
        con = sqlite3.connect(self.db)
        con.execute('DELETE FROM runtime_locker')
        con.commit()
        con.close()
        locker.add(self.db, self.agents, KEY, 'echo')

    def asked(self, wid):
        return [d for _o, route, d in wid.said if route == '/jobs/file']

    def test_the_picked_file_is_handed_as_bytes(self):
        self.agent()
        wid = Wid({'001': PIC, '002': 'make it brighter'}, {PIC: PNG})
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(self.asked(wid), [{'account': ACCOUNT, 'scope': SCOPE, 'member': MEMBER, 'job_key': JOB, 'run': '1', 'dam_key': PIC}])   # this member, this open RUN
        got = json.loads(self.results(wid)[-1]['delivery'])['picture']
        self.assertEqual((got['dam_key'], got['kind'], got['bytes'], got['same']), (PIC, 'png', len(PNG), PNG[:8].hex()))
        self.assertEqual(base64.b64decode(got['content_b64']), PNG)
        for path in self.instance.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'Zanzibar-7731', path.read_bytes(), f'{path.name} keeps a file')

    def test_an_empty_input_hands_no_file(self):
        self.agent()
        wid = Wid({'002': 'no picture'}, {PIC: PNG})
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(self.asked(wid), [])
        self.assertEqual(json.loads(self.results(wid)[-1]['delivery']), {})

    def test_an_input_that_is_not_a_dam_key_is_refused(self):
        self.agent()
        wid = Wid({'001': '../../etc/passwd'}, {})
        self.assertEqual(self.run_with(wid), 'REFUSED')
        self.assertEqual(self.results(wid)[-1]['log'], 'input 001 is not a DA-M key')
        self.assertEqual(self.asked(wid), [])

    def test_a_file_wid_does_not_hand_fails_before_the_agent_runs(self):
        self.agent()
        wid = Wid({'001': PIC}, {})
        self.assertEqual(self.run_with(wid), 'FAILED')
        end = self.results(wid)
        self.assertEqual([r['state'] for r in end], ['FAILED'])   # never RUNNING
        self.assertEqual(end[0]['log'], f'LARRYD could not read the file of input 001: DA-M did not hand {PIC} (not a file of this member)')

    def test_a_file_over_the_limit_fails(self):
        self.agent()
        big = PNG + b'0' * harness.MOST_RUN_FILE
        wid = Wid({'001': PIC}, {PIC: big})
        self.assertEqual(self.run_with(wid), 'FAILED')
        self.assertEqual(self.results(wid)[-1]['log'], f'the file of input 001 is over {harness.MOST_RUN_FILE // (1024 * 1024)} MB: {PIC}')

    def test_files_not_declared_right_fail_before_wid_is_asked_for_a_file(self):
        for files, hands in ((None, ('job', 'files')), (['nope'], ('job', 'files')), ([], ('job', 'files')),
                             (['picture', 'task', 'picture'], ('job', 'files')), (['picture'], ('files',))):
            with self.subTest(files=files, hands=hands):
                self.agent(files=files, hands=hands)
                wid = Wid({'001': PIC}, {PIC: PNG})
                self.assertEqual(self.run_with(wid), 'FAILED')
                self.assertEqual(self.asked(wid), [])

    def test_without_the_hand_no_file_is_read(self):
        self.agent(hands=('job',))
        wid = Wid({'001': PIC}, {PIC: PNG})
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(self.asked(wid), [])
        self.assertIsNone(json.loads(self.results(wid)[-1]['delivery']))


if __name__ == '__main__':
    unittest.main()
