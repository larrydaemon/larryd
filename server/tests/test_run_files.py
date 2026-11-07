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
from test_job_inputs import ACCOUNT, CARD, HIRED, JOB, KEY, MEMBER, SCOPE, Echo

PNG = b'\x89PNG\r\n\x1a\n' + b'Zanzibar-7731-private-picture' * 10
PIC = 'DA-M_' + 'E' * 12 + '_0005'


class Wid:
    """wid as a Recorder: /jobs/inputs and /jobs/file answer what the test gives them; every call is recorded."""
    def __init__(self, inputs, files, status=200):
        self.inputs, self.files, self.status, self.said = inputs, files, status, []

    def get(self, office, route, data=None, most=None):
        self.said.append((office, route, data))
        if route == '/jobs/file':
            self.most = most
        if route == '/jobs/inputs':
            return 200, {'inputs': self.inputs}
        if route == '/jobs/file':
            if self.status != 200 or data['dam_key'] not in self.files:
                return 404, {'refused': 'not a file of this member'}
            b64 = base64.b64encode(self.files[data['dam_key']]).decode()
            if most is not None and len(b64) > most:   # as platform.Client: over its most, refused before it is read whole
                return 413, {'refused': 'the answer is larger than asked'}
            return 200, {'content_b64': b64}
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
        self.assertEqual(wid.most, -(-harness.MOST_RUN_FILE // 3) * 4 + harness.ANSWER_ROOM)   # the size asked first: never read whole
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


class Companion(Echo):
    """A FILE STORED BESIDE THE MEMBER'S OWN (CORE_CLEANUP_IV 94): "companion_of": <a handed file input> stores the answer's file with
    that input file's own record as its source; refused before anything is charged when the input was not handed or wid named no record."""
    RECORD = 'MIMG_' + 'A' * 12 + '_0007'
    agent = RunFiles.agent   # the same echo agent as RunFiles, without running RunFiles' own tests again

    def stored(self, answer, source_key=RECORD, records=None):
        self.agent()
        manifest = self.agents / 'echo' / 'agent.json'
        card = json.loads(manifest.read_text())
        card['skills'] = [next(h for h, s in harness.SKILLS.items() if s.get('after') == 'files')]   # the DA-M store
        card['gives'] = card['gives'] + ['files']
        manifest.write_text(json.dumps(card))
        wid = Wid({'001': PIC}, {PIC: PNG})
        got = wid.get

        def get(office, route, data=None, most=None):
            status, body = got(office, route, data, most)
            if route == '/jobs/file' and status == 200 and source_key:
                body = {**body, 'source_key': source_key}   # wid naming the record the file belongs to
            return status, body
        wid.get = get
        h = harness.Harness(self.db, self.agents, wid)
        h.facts = lambda account, scope, member: ([CARD], HIRED, [], lambda key: (True, ''))
        h._skill_hands = lambda *a, **k: {}
        seen = {}
        h._run = lambda folder, manifest, given: (given.update({'records': records}) if records is not None else None,
                                                  seen.update(given) or 'DONE', answer, '')[1:]   # records: as wid's records hand gives them
        return h.run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), wid, seen

    @staticmethod
    def file(name, companion=None):
        return {'name': name, 'content_b64': base64.b64encode(PNG).decode('ascii'), **({'companion_of': companion} if companion else {})}

    def uploads(self, wid):
        return [d for _o, route, d in wid.said if route == '/jobs/upload']

    def test_a_companion_is_stored_with_the_input_files_own_record(self):
        state, wid, seen = self.stored({'delivery': 'a preview', 'files': [self.file('preview.png', 'picture'), self.file('other.png')]})
        self.assertEqual(state, 'DONE')
        self.assertEqual(seen['files']['picture']['record_key'], self.RECORD)   # the agent is told the record too
        self.assertEqual([(u['name'], u['source_key']) for u in self.uploads(wid)], [('preview.png', self.RECORD), ('other.png', KEY)])   # the other: the agent's card, as before

    def test_a_companion_of_an_input_not_handed_or_with_no_record_is_refused_before_anything_is_stored(self):
        for answer, source_key, said in (({'delivery': 'x', 'files': [self.file('p.png', 'mood')]}, self.RECORD, 'which is neither a file nor a record this RUN was handed'),
                                         ({'delivery': 'x', 'files': [self.file('p.png', 'picture')]}, '', 'whose record the platform did not name'),
                                         ({'delivery': 'x', 'files': [self.file('p.png', 'picture')]}, 'not a key', 'whose record the platform did not name')):
            with self.subTest(said=said, source_key=source_key):
                state, wid, _seen = self.stored(answer, source_key)
                self.assertEqual(state, 'FAILED')
                self.assertIn(said, self.results(wid)[-1]['log'])
                self.assertEqual(self.uploads(wid), [])
                self.assertFalse([r for _o, r, _d in wid.said if r == '/jobs/charge'])   # nothing charged

    INVOICE = 'MINV_' + 'B' * 12 + '_0003'

    def test_a_companion_of_a_handed_record_is_stored_with_that_record(self):
        """Rows 260 and 9 (frost-05 2026-11-06): companion_of may name a record this RUN was handed: an invoice's PDF beside its invoice."""
        records = {'invc': [{'key': self.INVOICE, 'data_amount': '10'}], 'cont': [{'key': 'MCON_' + 'C' * 12 + '_0001'}]}
        state, wid, _seen = self.stored({'delivery': 'x', 'files': [self.file('invoice.png', self.INVOICE)]}, records=records)
        self.assertEqual(state, 'DONE')
        self.assertEqual([(u['name'], u['source_key']) for u in self.uploads(wid)], [('invoice.png', self.INVOICE)])

    def test_a_companion_of_a_record_not_handed_is_refused_before_anything_is_charged(self):
        records = {'invc': [{'key': self.INVOICE}], 'odd': 'not rows', 'bad': [7, {'key': 9}, {'key': ''}]}
        for name in ('MINV_' + 'D' * 12 + '_0009', '', 9):
            if name == 9:
                continue   # a companion that is not text is refused by the files' own shape (the test below)
            with self.subTest(name=name):
                state, wid, _seen = self.stored({'delivery': 'x', 'files': [self.file('p.png', name or None) | ({'companion_of': ''} if name == '' else {})]}, records=records)
                self.assertEqual(state, 'FAILED')
                self.assertIn('which is neither a file nor a record this RUN was handed', self.results(wid)[-1]['log'])
                self.assertEqual(self.uploads(wid), [])
                self.assertFalse([r for _o, r, _d in wid.said if r == '/jobs/charge'])

    def test_a_companion_must_be_text_and_files_keep_their_shape(self):
        state, wid, _seen = self.stored({'delivery': 'x', 'files': [{**self.file('p.png'), 'companion_of': 7}]})
        self.assertEqual(state, 'FAILED')
        self.assertIn('an optional companion_of', self.results(wid)[-1]['log'])
