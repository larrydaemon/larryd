"""THE MEMBER'S RECORDS (the owner, 2026-10-07: "it's an agent and has access to the database; the core does not do this work"):
an agent whose approved manifest declares "records" is handed the member's records of each declared species on a CALL, read
through wid's own doors for that member; its answer's "writes" are carried to wid's own doors, only what is declared; then the
agent runs once more on the records as they are now, with "written" (what wid said), so the page shows the truth. Nothing is
kept by the runtime. On a developer's runtime the stand-in answers the same doors from one small file."""
import datetime
import json
import pathlib
import shutil
import tempfile
import unittest

from _here import APP
from core_engine import harness, member_records, preview, signing
from test_preview import GOOD_CARD, KEY_A, SECRET, _zip
from web import app as host

PATH = '/wid/pf/en/app/opns/home'
CODE = '''import json, sys
given = json.load(sys.stdin)
rows = given.get("records", {}).get("opns", [])
search = given.get("page", {}).get("search", {})
out = {"seen": [r.get("key") for r in rows], "topics": [r.get("identity_operations_headline") for r in rows], "written": given.get("written"),
       "view": {"html": "<section class=\\"cal\\">" + str(len(rows)) + "</section>", "css": ".cal { color: red }"}}
if "written" not in given and search.get("act") == "book":
    out["writes"] = [{"do": "add", "species": "opns", "values": {"identity_operations_date": search.get("day", ""), "identity_operations_headline": search.get("topic", ""), "data_meeting_time": "14:00"}}]
if "written" not in given and search.get("act") == "change":
    out["writes"] = [{"do": "edit", "species": "opns", "key": search.get("key", ""), "values": {"identity_operations_headline": search.get("topic", "")}}]
if "written" not in given and search.get("act") == "remove":
    out["writes"] = [{"do": "remove", "species": "opns", "key": search.get("key", "")}]
if "written" not in given and search.get("act") == "bad":
    out["writes"] = json.loads(search.get("bad", "[]"))
if "written" in given and search.get("again") == "1":
    out["writes"] = [{"do": "remove", "species": "opns", "key": "MOPN_000000000000_0000"}]
print(json.dumps(out))
'''


def _agent(records, calls=('month',), gives=('seen', 'topics', 'written', 'view', 'writes')):
    manifest = {'name': 'Scratch calendar', 'entry': 'agent.py', 'about': 'a scratch calendar', 'does': ['month'], 'calls': list(calls), 'reads': [],
                'run': {'do': 'month', 'hands': []}, 'gives': list(gives), 'skills': [], 'card': {**GOOD_CARD, 'screen': 'opns/home', 'module': 'Operations'}}
    if records is not None:
        manifest['records'] = records
    return {'agent.json': json.dumps(manifest).encode(), 'agent.py': CODE.encode()}


class TheDeclaration(unittest.TestCase):
    def test_only_a_well_formed_declaration_counts(self):
        self.assertEqual(member_records.declared({'records': {'opns': ['read', 'add', 'edit', 'remove']}}), {'opns': ('read', 'add', 'edit', 'remove')})
        self.assertEqual(member_records.declared({'records': {'opns': ['read', 'read']}}), {'opns': ('read',)})
        for bad in ({'records': 'opns'}, {'records': {'OPNS': ['read']}}, {'records': {'opns': []}}, {'records': {'opns': ['delete']}},
                    {'records': {'opns': 'read'}}, {'records': {'../x': ['read']}}, {}, 'junk'):
            self.assertEqual(member_records.declared(bad), {}, bad)

    def test_the_key_is_the_platforms_m_column(self):
        self.assertEqual(member_records.key_of({'MOPN_norm_key': 'MOPN_1_2', 'KOPN_norm_key': 'KOPN_1_2', 'key': 'x'}), 'MOPN_1_2')
        self.assertEqual(member_records.key_of({'key': 'x'}), 'x')
        self.assertEqual(member_records.key_of({'junk': 1}), '')

    def test_the_writes_are_checked_whole(self):
        wanted = {'opns': ('read', 'add', 'edit')}
        ok, why = member_records.check([{'do': 'add', 'species': 'opns', 'values': {'identity_operations_headline': 'x'}},
                                        {'do': 'edit', 'species': 'opns', 'key': 'MOPN_000000000001_0001', 'values': {'a_b': 'y'}}], wanted)
        self.assertEqual(why, '')
        self.assertEqual([w['do'] for w in ok], ['add', 'edit'])
        for bad, said in (([{'do': 'remove', 'species': 'opns', 'key': 'MOPN_000000000001_0001'}], 'does not declare'),
                          ([{'do': 'add', 'species': 'cont', 'values': {'a': 'b'}}], 'does not declare'),
                          ([{'do': 'edit', 'species': 'opns', 'values': {'a': 'b'}}], 'names no record key'),
                          ([{'do': 'edit', 'species': 'opns', 'key': '../x', 'values': {'a': 'b'}}], 'names no record key'),
                          ([{'do': 'add', 'species': 'opns', 'values': {}}], 'carries no values'),
                          ([{'do': 'add', 'species': 'opns', 'values': {'Bad-Name': 'b'}}], 'not a plain field name'),
                          ([{'do': 'add', 'species': 'opns', 'values': {'a': 5}}], 'not text'),
                          ([{'do': 'add', 'species': 'opns', 'values': {'a': 'x' * 10_001}}], 'not text'),
                          (['junk'], 'not an object'), ('junk', 'not a list'),
                          ([{'do': 'add', 'species': 'opns', 'values': {'a': 'b'}}] * 21, 'at most 20')):
            got, why = member_records.check(bad, wanted)
            self.assertEqual(got, [], bad)
            self.assertIn(said, why, bad)


class OnTheDevelopersRuntime(unittest.TestCase):
    """The whole lane through the developer's runtime: the stand-in's doors, the harness, the sandbox, the second run."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
        self.app = host.create_app(root, secret=SECRET, addresses={}, agents=self.agents, developer=True)
        self.client = self.app.test_client()
        self.client.get('/marketplace')
        self.records = root / 'preview' / 'records_opns.json'   # the instance is the root here (the stand-in's one small file)
        self.who = {'account': preview.ACCOUNT, 'scope': preview.SCOPE, 'member': preview.MEMBER, 'agent_key': KEY_A}

    def tearDown(self):
        self.tmp.cleanup()

    def place(self, records):
        r = self.client.post(f'/marketplace/place?key={KEY_A}', data=_zip(_agent(records)), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
        self.assertIn(r.status_code, (200, 201), r.get_data(as_text=True)[:300])
        self.app.config['harness'].hire(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, True)

    def seed(self, rows):
        self.records.parent.mkdir(parents=True, exist_ok=True)
        self.records.write_text(json.dumps(rows))

    def ask(self, confirmed=True, **search):   # act: the platform's mark that this call is the member's own confirmed act (a POST it checked); only then is a write carried
        body = {**self.who, 'page': {'path': PATH, 'search': search}, **({'act': True} if confirmed else {})}
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return self.client.post('/api/agents/answer', json=body, headers={'X-Office': signing.sign(SECRET, '/agents/answer', body, at), 'X-Office-At': at})

    def rows(self):
        return json.loads(self.records.read_text())

    def test_the_declared_records_are_handed_with_their_keys_and_nothing_is_kept(self):
        self.place({'opns': ['read']})
        self.seed([{'MOPN_norm_key': 'MOPN_000000000001_0001', 'identity_operations_headline': 'Partners'}, {'MOPN_norm_key': 'MOPN_000000000002_0002', 'identity_operations_headline': 'Demo'}])
        out = self.ask().get_json()
        self.assertEqual(out['seen'], ['MOPN_000000000001_0001', 'MOPN_000000000002_0002'])
        self.assertEqual(out['topics'], ['Partners', 'Demo'])
        self.assertIsNone(out['written'])
        self.assertIn('view', out)
        self.assertNotIn('writes', out)
        db = next(pathlib.Path(self.tmp.name).glob('*.db')).read_bytes()
        self.assertNotIn(b'Partners', db)   # no record value in the runtime's own database

    def test_an_agent_that_declares_no_records_is_handed_none(self):
        self.place(None)
        self.seed([{'MOPN_norm_key': 'MOPN_000000000001_0001', 'identity_operations_headline': 'Partners'}])
        out = self.ask().get_json()
        self.assertEqual(out['seen'], [])

    def test_a_booking_is_carried_then_the_agent_sees_it_with_its_key(self):
        self.place({'opns': ['read', 'add', 'edit', 'remove']})
        self.seed([])
        out = self.ask(act='book', day='2026-10-07', topic='Partners Meeting').get_json()
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]['identity_operations_date'], rows[0]['identity_operations_headline'], rows[0]['data_meeting_time']), ('2026-10-07', 'Partners Meeting', '14:00'))
        key = rows[0]['MOPN_norm_key']
        self.assertEqual(out['written'], [{'do': 'add', 'species': 'opns', 'key': key, 'ok': True, 'why': ''}])   # the second run: wid's word
        self.assertEqual(out['seen'], [key])                                                                      # and the records as they are now
        self.assertEqual(out['view']['html'], '<section class="cal">1</section>')
        self.assertNotIn('writes', out)

    def test_a_change_and_a_removal_are_carried(self):
        self.place({'opns': ['read', 'add', 'edit', 'remove']})
        self.seed([{'MOPN_norm_key': 'MOPN_000000000001_0001', 'identity_operations_headline': 'Partners'}])
        out = self.ask(act='change', key='MOPN_000000000001_0001', topic='Partner Meeting').get_json()
        self.assertEqual(out['topics'], ['Partner Meeting'])
        self.assertEqual(out['written'][0]['ok'], True)
        out = self.ask(act='remove', key='MOPN_000000000001_0001').get_json()
        self.assertEqual(out['seen'], [])
        self.assertEqual(self.rows(), [])
        out = self.ask(act='remove', key='MOPN_000000000001_0001').get_json()   # gone already: wid's refusal, said, nothing crashes
        self.assertEqual(out['written'], [{'do': 'remove', 'species': 'opns', 'key': 'MOPN_000000000001_0001', 'ok': False, 'why': 'nothing by that key'}])

    def test_an_undeclared_write_refuses_the_whole_answer_and_writes_nothing(self):
        self.place({'opns': ['read', 'add']})
        self.seed([{'MOPN_norm_key': 'MOPN_000000000001_0001', 'identity_operations_headline': 'Partners'}])
        r = self.ask(act='remove', key='MOPN_000000000001_0001')
        self.assertEqual(r.status_code, 500, r.get_data(as_text=True)[:300])
        self.assertIn('does not declare', r.get_json()['refused'])
        self.assertEqual(len(self.rows()), 1)
        r = self.ask(act='bad', bad=json.dumps([{'do': 'add', 'species': 'cont', 'values': {'identity_first_name': 'x'}}]))
        self.assertEqual(r.status_code, 500)
        self.assertFalse((self.records.parent / 'records_cont.json').exists())

    def test_writes_from_an_agent_without_a_declaration_are_refused(self):
        self.place(None)
        self.seed([])
        r = self.ask(act='book', day='2026-10-07', topic='x')
        self.assertEqual(r.status_code, 500)
        self.assertIn('declares no records', r.get_json()['refused'])
        self.assertEqual(self.rows(), [])

    def test_a_page_merely_opened_never_writes(self):   # the review, 2026-10-07: a link or an address is not the member's act
        self.place({'opns': ['read', 'add', 'edit', 'remove']})
        self.seed([{'MOPN_norm_key': 'MOPN_000000000001_0001', 'identity_operations_headline': 'Kept'}])
        before = self.rows()
        for call in (lambda: self.ask(confirmed=False, act='book', day='2026-11-03', topic='Forged'), lambda: self.ask(confirmed=False, act='remove', key='MOPN_000000000001_0001')):
            r = call()
            self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:200])
            self.assertNotIn('writes', r.get_json())
            self.assertIsNone(r.get_json().get('written'))   # nothing was carried, so nothing is said of a write
        self.assertEqual(self.rows(), before)
        who = self.who
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        for act in ('true', 1, 'yes', {'x': 1}):   # only a JSON true, only on the POST
            body = {**who, 'page': {'path': PATH, 'search': {'act': 'book', 'day': '2026-11-03', 'topic': 'Forged'}}, 'act': act}
            self.client.post('/api/agents/answer', json=body, headers={'X-Office': signing.sign(SECRET, '/agents/answer', body, at), 'X-Office-At': at})
        self.assertEqual(self.rows(), before)

    def test_writes_on_the_second_run_are_ignored(self):
        self.place({'opns': ['read', 'add', 'edit', 'remove']})
        self.seed([{'MOPN_norm_key': 'MOPN_000000000000_0000', 'identity_operations_headline': 'Kept'}])
        out = self.ask(act='book', day='2026-10-07', topic='New', again='1').get_json()
        self.assertEqual(len(self.rows()), 2)   # the booking, and Kept still there: the second run's remove went nowhere
        self.assertNotIn('writes', out)

    def test_the_call_is_recorded_with_the_writes_carried_and_no_data(self):
        self.place({'opns': ['read', 'add']})
        self.seed([])
        self.ask(act='book', day='2026-10-07', topic='Secret topic')
        import sqlite3
        con = sqlite3.connect(next(pathlib.Path(self.tmp.name).glob('*.db')))
        rows = con.execute("SELECT state, reason FROM runtime_runs WHERE lane = 'call' AND agent_key = ?", (KEY_A,)).fetchall()
        con.close()
        self.assertEqual(rows, [('DONE', '1_OF_1_RECORD_WRITE_CARRIED')])   # the reason, as every run record keeps it


class TheRead(unittest.TestCase):
    def test_the_rows_are_read_page_by_page_up_to_the_most(self):
        asked = []

        def ask(office, method, route, data):
            asked.append((route, data['offset']))
            n = int(data['offset'])
            return {'total': 450, 'rows': [{'MOPN_norm_key': f'MOPN_{i:012d}_0000'} for i in range(n, min(n + 200, 450))]}
        out = member_records.read(ask, {'opns': ('read', 'add'), 'cont': ('add',)}, 'A', 'S', 'M')
        self.assertEqual(list(out), ['opns'])   # cont: no read declared, nothing asked
        self.assertEqual(len(out['opns']), 450)
        self.assertEqual([o for _r, o in asked], ['0', '200', '400'])
        self.assertEqual(out['opns'][0]['key'], 'MOPN_000000000000_0000')

    def test_a_refusing_wid_fails_the_call_honestly(self):
        def ask(office, method, route, data):
            raise harness.Refused(401, 'not the runtime')
        with self.assertRaises(harness.Refused):
            member_records.read(ask, {'opns': ('read',)}, 'A', 'S', 'M')


if __name__ == '__main__':
    unittest.main()


class WhatTheRecordSays(unittest.TestCase):
    """A write is on the platform the moment it is carried: whatever happens after (the read back refused, the second run
    failing), the run record says how many were carried; and a key wid answers is a plain key or nothing."""
    def test_an_add_that_minted_no_record_is_not_claimed(self):
        post = lambda office, route, data: (200, {'key': ''})
        out = member_records.carry(post, [{'do': 'add', 'species': 'opns', 'key': '', 'values': {'a': 'b'}}], 'A', 'S', 'M')
        self.assertEqual(out, [{'do': 'add', 'species': 'opns', 'key': '', 'ok': False, 'why': 'no record was made'}])
        post = lambda office, route, data: (200, {'key': '../x'})
        out = member_records.carry(post, [{'do': 'add', 'species': 'opns', 'key': '', 'values': {'a': 'b'}}], 'A', 'S', 'M')
        self.assertEqual((out[0]['ok'], out[0]['key']), (False, ''))

    def test_a_failed_second_run_still_records_the_writes_carried(self):
        class Client:
            def post(self, office, route, data):
                return 200, {'key': 'MOPN_000000000009_0009'}
        h = harness.Harness.__new__(harness.Harness)
        h.client, h.seconds, h.on_start, h.agents = Client(), 20, None, pathlib.Path('/nonexistent')
        h._ask = lambda *a: (_ for _ in ()).throw(harness.Refused(503, 'wid is away'))
        state, answer, reason = h._written({'folder': 'x'}, {'entry': 'agent.py', 'gives': []}, {'opns': ('read', 'add')}, {}, {'writes': [{'do': 'add', 'species': 'opns', 'values': {'a': 'b'}}]}, 'A', 'S', 'M')
        self.assertEqual((state, answer), ('FAILED', None))
        self.assertEqual(reason, '1 of 1 record write carried; the records could not be read back: wid is away')


class EveryRecordCallNamesItsAgent(unittest.TestCase):
    """wid's record doors let through only an approved agent the member hired, for what its card declares: every call names the agent's card key."""
    def test_the_read_and_every_write_carry_the_agents_key(self):
        seen = []
        def ask(office, method, route, data):
            seen.append((route, data.get('agent_key'))); return {'rows': [], 'total': 0}
        def post(office, route, data):
            seen.append((route, data.get('agent_key'))); return 200, {'key': 'MOPN_000000000001_0001'}
        member_records.read(ask, {'opns': ('read',)}, 'A', 'S', 'M', 'MAGT_EB3A10BE9600_1266')
        member_records.carry(post, [{'do': 'add', 'species': 'opns', 'key': '', 'values': {'a': 'b'}}, {'do': 'edit', 'species': 'opns', 'key': 'K', 'values': {'a': 'b'}},
                                    {'do': 'remove', 'species': 'opns', 'key': 'K', 'values': {}}], 'A', 'S', 'M', 'MAGT_EB3A10BE9600_1266')
        self.assertEqual([r for r, _k in seen], ['/agnt/records/list', '/agnt/records/add', '/agnt/records/edit', '/agnt/records/remove'])
        self.assertEqual({k for _r, k in seen}, {'MAGT_EB3A10BE9600_1266'})


class WhenThePlatformDoesNotHandThem(OnTheDevelopersRuntime):
    """A slot without the record doors yet, a member FROST does not allow, wid away: the agent is handed no records, its view still
    draws (it says the platform handed none), nothing is written, and the call's record says why."""
    def test_a_refused_read_still_draws_and_is_recorded(self):
        self.place({'opns': ['read', 'add']})
        self.seed([{'MOPN_norm_key': 'MOPN_000000000001_0001', 'identity_operations_headline': 'Partners'}])
        real = preview.Local._records_door
        preview.Local._records_door = lambda self, method, route, data: (404, {'refused': 'nothing by that key'})
        try:
            out = self.ask(act='book', day='2026-10-07', topic='x').get_json()
        finally:
            preview.Local._records_door = real
        self.assertEqual(out['seen'], [])                       # handed none: the agent's own words say so on its page
        self.assertIn('view', out)
        self.assertEqual(len(self.rows()), 1)                   # nothing written
        import sqlite3
        con = sqlite3.connect(next(pathlib.Path(self.tmp.name).glob('*.db')))
        reason = con.execute("SELECT reason FROM runtime_runs WHERE lane = 'call' AND agent_key = ? ORDER BY rowid DESC", (KEY_A,)).fetchone()[0]
        con.close()
        self.assertIn('RECORDS_NOT_READ', reason)
