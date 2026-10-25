"""THE LARRY DATA FABRIC (the owner, 2026-10-25) as the runtime carries it: custom data only on custom agents (any other agent
is handed rows without their custom field buckets and may not write one); an agent declaring "fabric" is handed, on its
RUN, the newest official files from DA-M, its state from FROST and its modules' records WITH their custom fields; its
answer's fabric writes (custom fields only, declared modules only, at most 5000) are carried through wid's own doors and
its state saved back to FROST with the record each row landed on; on a CALL it is handed its state only. These tests stand
the sandbox in for one that hands back a fixed answer: what the agent itself does is proven by the agent's own walk."""
import json
import pathlib
import sqlite3
import tempfile
import unittest
from unittest import mock

from _here import APP  # noqa: F401
from core_engine import fabric, harness, locker, member_records, store, view

KEY, JOB = 'MAGT_00000000FAB1_0001', 'MJOB_00000000FAB1_0001'
ACCOUNT, SCOPE, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'SCRATCH', 'MCON_' + 'B' * 12 + '_0002'
CARD = {'key': KEY, 'name': 'PF DATA FABRIC', 'screen': 'larry/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents',
        'price': '0', 'status': 'APPROVED', 'authorization': 'PUBLIC', 'account_key': ''}
HIRED = [{'agent_key': KEY, 'board': CARD['screen'], 'shell_id': 1, 'on': True, 'job_key': JOB}]
INVOICE = 'MINV_' + 'C' * 12 + '_0003'
ROW = {'MINV_norm_key': INVOICE, 'identity_invoice_number': 'INV-1', 'custom_0001': 'SO-1', 'custom_0004': '100.00'}
FILE = {'name': 'pf_invoices.csv', 'original_filename': 'PF_Invoices.csv', 'dam_key': 'DA-M_' + 'D' * 12 + '_0001', 'version': 2,
        'made_at': '2026-10-25T10:00:00', 'file_size': '30', 'content': 'id,id_lookup,total\nSO-1,INV-1,100.00\n'}
FABRIC = {'fabric': {'modules': ['invc']}, 'records': {'invc': ['read', 'edit']}}


class Platform:
    """The platform as the runtime hears it: wid's record doors, DA-M's Fabric files, FROST's Fabric state, mTok."""
    def __init__(self, rows=None, state=None, files=None, refuse=()):
        self.rows = rows if rows is not None else [dict(ROW)]
        self.state = state or {'files': [], 'held': [], 'slots': [], 'ids': [], 'apis': [{'api_name': 'VIRTUAL WIRE API', 'api_state': 'live', 'synced_at': ''}]}
        self.files = files if files is not None else [dict(FILE)]
        self.refuse, self.said = refuse, []

    def get(self, office, route, data=None):
        self.said.append(('GET', route, data))
        if route in self.refuse:
            return 403, {'refused': 'not yours'}
        if route == '/agnt/records/list':
            return 200, {'rows': self.rows, 'total': len(self.rows), 'first': []}
        if route == '/dam/fabric':
            return 200, {'files': self.files}
        if route == '/fabric/state':
            return 200, self.state
        return 404, {'refused': route}

    def post(self, office, route, data):
        self.said.append(('POST', route, data))
        if route in self.refuse:
            return 403, {'refused': 'not yours'}
        if route == '/agnt/records/edit':
            return (200, {'key': data['key']}) if data['key'] == INVOICE else (404, {'refused': 'nothing by that key'})
        if route == '/agnt/records/add':
            return 200, {'key': ''}   # custom values alone: the platform keeps the row waiting at its entry (RULE 13)
        if route == '/fabric/state':
            return 200, {'saved': {t: len(data.get(t, [])) for t in fabric.TABLES}}
        if route == '/mtok/use':
            return 200, {'charged': 0, 'free': True}
        return 200, {'saved': True}

    def posted(self, route):
        return [d for m, r, d in self.said if m == 'POST' and r == route]

    def asked(self, route):
        return [d for m, r, d in self.said if m == 'GET' and r == route]


class World(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.instance = pathlib.Path(self.tmp.name) / 'instance'
        self.instance.mkdir()
        self.agents = pathlib.Path(self.tmp.name) / 'agents'
        self.db = store.open_store(self.instance)

    def tearDown(self):
        self.tmp.cleanup()

    def agent(self, extra=None, calls=None):
        folder = self.agents / 'fabric'
        folder.mkdir(parents=True, exist_ok=True)
        manifest = {'name': 'PF DATA FABRIC', 'entry': 'agent.py', 'run': {'do': 'import', 'hands': []}, 'gives': ['view', 'delivery', 'fabric', 'writes'], 'skills': [], **(extra or {})}
        if calls:
            manifest['calls'] = calls
        (folder / 'agent.json').write_text(json.dumps(manifest))
        (folder / 'agent.py').write_text('print("{}")\n')
        con = sqlite3.connect(self.db)
        con.execute('DELETE FROM runtime_locker')
        con.commit()
        con.close()
        locker.add(self.db, self.agents, KEY, 'fabric')

    def harness(self, client, card=None):
        h = harness.Harness(self.db, self.agents, client)
        h.facts = lambda account, scope, member: ([card or CARD], HIRED, [], lambda key: (True, ''))
        return h

    def sandboxed(self, *answers):
        """The sandbox's stand-in: each run hands back the next answer and keeps what it was given."""
        self.given, queue = [], list(answers)

        def run(folder, entry, given, seconds=20, on_start=None, most_bytes=harness.sandbox.MOST_BYTES):
            self.given.append(json.loads(json.dumps(given)))
            self.most_bytes = most_bytes
            return 'DONE', queue.pop(0) if queue else {}, ''
        return mock.patch.object(harness.sandbox, 'run', run)

    @staticmethod
    def result(p):
        return [d for d in p.posted('/jobs/result') if d['state'] != 'RUNNING'][-1]


class TheDeclaration(unittest.TestCase):
    def test_the_modules_count_only_with_the_records_lane(self):
        self.assertEqual(fabric.declared(FABRIC), ['invc'])
        self.assertEqual(fabric.declared({'fabric': {'modules': ['invc']}, 'records': {'invc': ['read']}}), [])        # no edit: nothing
        self.assertEqual(fabric.declared({'fabric': {'modules': ['invc', 'zzzz', 'invc']}, 'records': {'invc': ['read', 'edit']}}), ['invc'])
        for bad in ({}, {'fabric': 'invc'}, {'fabric': {'modules': 'invc'}}, 'junk'):
            self.assertEqual(fabric.declared(bad), [], bad)

    def test_the_sixteen_names_are_one_per_module(self):
        self.assertEqual(len(fabric.FILES), 16)
        self.assertEqual(len(fabric.MODULES), 16)
        self.assertTrue(all(n.startswith('pf_') and n.endswith('.csv') for n in fabric.FILES))

    def test_custom_is_a_private_agent_of_this_account_or_the_fabric(self):
        self.assertTrue(fabric.custom({'authorization': 'PRIVATE', 'account_key': ACCOUNT}, {}, ACCOUNT))
        self.assertTrue(fabric.custom({'authorization': 'private ', 'account_key': ACCOUNT}, {}, ACCOUNT))
        self.assertFalse(fabric.custom({'authorization': 'PRIVATE', 'account_key': 'ACCT_' + 'Z' * 12 + '_0009'}, {}, ACCOUNT))   # another account's own agent
        self.assertFalse(fabric.custom({'authorization': 'PRIVATE', 'account_key': ''}, {}, ''))
        self.assertFalse(fabric.custom({'authorization': 'PUBLIC', 'account_key': ACCOUNT}, {}, ACCOUNT))
        self.assertFalse(fabric.custom(None, {}, ACCOUNT))
        self.assertTrue(fabric.custom(CARD, FABRIC, ACCOUNT))


class TheGuard(unittest.TestCase):
    def test_an_agent_that_is_not_custom_never_sees_a_custom_field(self):
        ask = lambda office, method, route, data: {'rows': [dict(ROW)], 'total': 1}
        plain = member_records.read(ask, {'invc': ('read',)}, ACCOUNT, SCOPE, MEMBER)['invc'][0]
        self.assertEqual(sorted(plain), ['MINV_norm_key', 'identity_invoice_number', 'key'])
        whole = member_records.read(ask, {'invc': ('read',)}, ACCOUNT, SCOPE, MEMBER, custom=True)['invc'][0]
        self.assertEqual(whole['custom_0004'], '100.00')

    def test_an_agent_that_is_not_custom_may_not_write_one(self):
        writes = [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_0004': '9'}}]
        got, why = member_records.check(writes, {'invc': ('edit',)})
        self.assertEqual((got, why), ([], 'write 1 names a custom field, which only a custom agent may write'))
        got, why = member_records.check(writes, {'invc': ('edit',)}, custom=True)
        self.assertEqual((len(got), why), (1, ''))
        got, why = member_records.check([{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_notes': '9'}}], {'invc': ('edit',)})
        self.assertEqual(why, '')   # a default field that merely starts with the word is not a bucket


class TheCheck(unittest.TestCase):
    def good(self, **more):
        return {'fabric': {'writes': [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_0004': '1'}, 'row': {'segment': 'invc', 'row_id': 'SO-1'}}],
                           'state': {'files': [{'file_name': 'pf_invoices.csv', 'version': '2'}], 'ids': [{'segment': 'invc', 'row_id': 'SO-1'}]}, **more}}

    def test_a_good_answer(self):
        writes, rows, saved, why = fabric.check(self.good(), ['invc'])
        self.assertEqual((len(writes), rows, why), (1, ['SO-1'], ''))
        self.assertEqual(saved['files'][0]['rows_in'], '')        # every column of its table, the missing ones empty
        self.assertEqual(saved['held'], [])

    def test_a_run_carries_more_than_a_page_may(self):
        many = [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_0001': f'SO-{n}'}, 'row': {'segment': 'invc', 'row_id': f'SO-{n}'}} for n in range(fabric.MOST_WRITES)]
        writes, rows, saved, why = fabric.check({'fabric': {'writes': many}}, ['invc'])
        self.assertEqual((len(writes), why), (fabric.MOST_WRITES, ''))   # a page's answer carries at most 20 (member_records.MOST_WRITES); a RUN of the Fabric 5000

    def test_one_fault_refuses_it_all(self):
        bad = [({'fabric': 'x'}, 'not {writes, state}'),
               ({'fabric': {'writes': [], 'more': 1}}, 'not {writes, state}'),
               ({'fabric': {'writes': [{'do': 'remove', 'species': 'invc', 'key': INVOICE}]}}, 'not an edit of a record'),
               ({'fabric': {'writes': [{'do': 'add', 'species': 'invc', 'values': {'custom_0001': 'x'}}]}}, 'not an edit of a record'),   # a row with no record waits in its file: never an add
               ({'fabric': {'writes': [{'do': 'edit', 'species': 'cont', 'key': INVOICE, 'values': {'custom_0001': 'x'}}]}}, 'not an edit of a record'),
               ({'fabric': {'writes': [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'identity_invoice_number': 'x'}}]}}, 'other than custom fields'),
               ({'fabric': {'writes': [{'do': 'edit', 'species': 'invc', 'key': '../x', 'values': {'custom_0001': 'x'}}]}}, 'names no record key'),
               ({'fabric': {'writes': [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_0001': 'x'}, 'row': {'segment': 'cont', 'row_id': 'a'}}]}}, 'names its row wrongly'),
               ({'fabric': {'writes': [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_0001': 'x'}}] * 5001}}, 'at most 5000'),
               ({'fabric': {'state': {'files': [{'file_name': 1}]}}}, 'files row 1'),
               ({'fabric': {'state': {'files': [{'unknown': 'x'}]}}}, 'files row 1'),
               ({'fabric': {'state': {'apis': []}}}, 'not {files, held, slots, ids}')]
        for answer, said in bad:
            writes, rows, saved, why = fabric.check(answer, ['invc'])
            self.assertIn(said, why, answer if len(str(answer)) < 300 else said)
            self.assertEqual((writes, saved), ([], None))

    def test_each_id_names_the_record_it_landed_on(self):
        writes = [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {}}, {'do': 'edit', 'species': 'invc', 'key': 'MINV_' + 'E' * 12 + '_0005', 'values': {}}]
        saved = {'ids': [{'segment': 'invc', 'row_id': 'SO-1', 'record_key': ''}, {'segment': 'invc', 'row_id': 'SO-2', 'record_key': 'old'},
                         {'segment': 'invc', 'row_id': 'SO-3', 'record_key': 'kept'}]}
        written = [{'ok': True, 'key': INVOICE}, {'ok': False, 'key': ''}]
        out = fabric.landed(saved, writes, ['SO-1', 'SO-2'], written)
        self.assertEqual([i['record_key'] for i in out['ids']], [INVOICE, '', 'kept'])   # taken; refused by wid (it waits again); not written this RUN


class TheDownload(unittest.TestCase):
    """THE DOWNLOAD (the owner, 2026-10-25: "we can do it without javascript just like any download"): DA-M's own download of a
    file, on the page's own site, side and language, built by the runtime; the held rows file's key filled once DA-M gave it."""
    PAGE = '/wid/pf/en/app/larry/home'
    KEY = 'DA-M_0123456789AB_C0DE'

    def test_the_address_is_dam_own_download_on_the_pages_side_and_language(self):
        self.assertEqual(view.download_of(self.PAGE, self.KEY), f'/so/pf/en/app/files/card/{self.KEY}/download')
        self.assertEqual([view.download_of(p, k) for p, k in ((self.PAGE, ''), (self.PAGE, 'DA-M_0123456789ab_C0DE'), (self.PAGE, self.KEY + '/../x'), ('', self.KEY), ('/x', self.KEY))],
                         ['', '', '', '', ''])

    def test_the_gate_lets_that_link_through_and_nothing_like_it(self):
        good = f'/so/pf/en/app/files/card/{self.KEY}/download'
        self.assertEqual(view.checked({'view': {'html': f'<a href="{good}">get</a>', 'css': ''}}, self.PAGE)[1], '')
        for bad in (f'/so/rnd/en/app/files/card/{self.KEY}/download',     # another side
                    f'/so/pf/fr/app/files/card/{self.KEY}/download',      # another language
                    f'/so/pf/en/app/files/card/{self.KEY}/raw',           # not the download
                    f'/wid/pf/en/app/files/card/{self.KEY}/download',     # not DA-M
                    f'https://evil.example/so/pf/en/app/files/card/{self.KEY}/download'):
            self.assertNotEqual(view.checked({'view': {'html': f'<a href="{bad}">get</a>', 'css': ''}}, self.PAGE)[1], '', bad)
        self.assertNotEqual(view.checked({'view': {'html': f'<a href="{good}" target="_blank" rel="noopener noreferrer">get</a>', 'css': ''}}, self.PAGE)[1], '')

    def test_the_page_is_handed_each_files_downloads(self):
        state = {'files': [{'file_name': 'pf_invoices.csv', 'dam_key': self.KEY, 'held_dam_key': ''}]}
        got = fabric.with_downloads(state, self.PAGE)['files'][0]
        self.assertEqual((got['download'], got['held_download']), (f'/so/pf/en/app/files/card/{self.KEY}/download', ''))

    def test_the_held_file_key_is_the_one_dam_gave(self):
        saved = {'files': [{'file_name': 'pf_invoices.csv', 'held_dam_key': ''}, {'file_name': 'pf_jobs.csv', 'held_dam_key': 'DA-M_AAAAAAAAAAAA_0001'}]}
        got = fabric.with_held(saved, {'pf_invoices_held.csv': self.KEY})['files']
        self.assertEqual([f['held_dam_key'] for f in got], [self.KEY, 'DA-M_AAAAAAAAAAAA_0001'])


class TheSizeLimit(unittest.TestCase):
    """THE SIZE LIMIT, BASED ON 100 FIELDS (the owner, 2026-10-25): a Fabric RUN's answer may hold its most writes of 100
    custom fields each (25 MB); an answer names only the ids that changed, the runtime keeps the rest."""
    def test_the_limit_is_its_most_writes_of_100_fields(self):
        self.assertEqual((fabric.FIELDS, fabric.MOST_ANSWER), (100, 25_000_000))
        self.assertGreater(fabric.MOST_ANSWER, harness.sandbox.MOST_BYTES)

    def test_the_ids_named_over_the_ids_handed(self):
        handed = {'ids': [{'segment': 'invc', 'row_id': 'SO-1', 'id_import': 'IMP-1', 'id_lookup': 'INV-1', 'record_key': '', 'made_at': 'a'},
                          {'segment': 'invc', 'row_id': 'SO-2', 'id_import': 'IMP-2', 'id_lookup': '', 'record_key': '', 'made_at': 'a'}]}
        saved = {'ids': [{'segment': 'invc', 'row_id': 'SO-1', 'id_import': 'IMP-1', 'id_lookup': 'INV-1', 'record_key': INVOICE, 'made_at': 'a'},
                         {'segment': 'invc', 'row_id': 'SO-3', 'id_import': 'IMP-3', 'id_lookup': '', 'record_key': '', 'made_at': 'b'}]}
        got = fabric.merged(handed, saved)['ids']
        self.assertEqual([(i['row_id'], i['record_key']) for i in got], [('SO-1', INVOICE), ('SO-2', ''), ('SO-3', '')])


class TheRun(World):
    ANSWER = {'fabric': {'writes': [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_0001': 'SO-1', 'custom_0004': '100.00'}, 'row': {'segment': 'invc', 'row_id': 'SO-1'}},
                                    {'do': 'edit', 'species': 'invc', 'key': 'MINV_' + 'E' * 12 + '_0005', 'values': {'custom_0001': 'SO-2'}, 'row': {'segment': 'invc', 'row_id': 'SO-2'}}],
                         'state': {'files': [{'file_name': 'pf_invoices.csv', 'dam_key': FILE['dam_key'], 'version': '2', 'rows_in': '2'}],
                                   'ids': [{'segment': 'invc', 'row_id': 'SO-1', 'id_import': 'FAB_1'}, {'segment': 'invc', 'row_id': 'SO-2', 'id_import': 'FAB_2'}]}},
              'delivery': 'pf_invoices.csv: 2 rows'}

    def test_the_run_is_handed_files_state_and_records_with_their_custom_fields(self):
        self.agent(FABRIC)
        p = Platform()
        with self.sandboxed(self.ANSWER):
            self.assertEqual(self.harness(p).run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), 'DONE')
        given = self.given[0]
        self.assertEqual(given['fabric']['files'][0]['content'], FILE['content'])
        self.assertEqual(given['fabric']['state']['apis'][0]['api_name'], 'VIRTUAL WIRE API')
        self.assertEqual(given['records']['invc'][0]['custom_0004'], '100.00')
        self.assertEqual(self.most_bytes, fabric.MOST_ANSWER)   # its own answer limit, based on 100 fields
        self.assertEqual(p.asked('/dam/fabric')[0], {'account': ACCOUNT, 'scope': SCOPE, 'member': MEMBER, 'job_key': JOB, 'run': '1', 'content': 'yes'})

    def test_the_writes_are_carried_and_the_state_saved_with_where_each_row_landed(self):
        self.agent(FABRIC)
        p = Platform()
        with self.sandboxed(self.ANSWER):
            self.harness(p).run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1)
        self.assertEqual(p.posted('/agnt/records/edit')[0]['values'], {'custom_0001': 'SO-1', 'custom_0004': '100.00'})
        self.assertEqual(p.posted('/agnt/records/edit')[1]['values'], {'custom_0001': 'SO-2'})
        self.assertEqual(p.posted('/agnt/records/add'), [])   # the Fabric never adds
        saved = p.posted('/fabric/state')[0]
        held = locker.held(self.db, KEY)
        self.assertEqual((saved['job_key'], saved['run'], saved['agent_key'], saved['code_sha256'], saved['manifest_sha256']),
                         (JOB, '1', KEY, held['code_sha256'], held['manifest_sha256']))   # FROST keeps it only for the agent it approved under these hashes
        self.assertEqual([(i['row_id'], i['record_key']) for i in saved['ids']], [('SO-1', INVOICE), ('SO-2', '')])
        self.assertIn('1 of 2 record writes carried', self.result(p)['log'])
        self.assertNotIn('fabric', self.result(p)['delivery'])   # the delivery is the agent's words, never the whole answer

    def test_a_bad_fabric_answer_writes_nothing(self):
        self.agent(FABRIC)
        p = Platform()
        bad = {'fabric': {'writes': [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'identity_invoice_number': 'x'}}]}}
        with self.sandboxed(bad):
            self.assertEqual(self.harness(p).run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), 'FAILED')
        self.assertEqual((p.posted('/agnt/records/edit'), p.posted('/fabric/state')), ([], []))
        self.assertIn('other than custom fields', self.result(p)['log'])

    def test_files_not_handed_nothing_runs(self):
        self.agent(FABRIC)
        p = Platform(refuse=('/dam/fabric',))
        with self.sandboxed(self.ANSWER):
            self.assertEqual(self.harness(p).run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), 'FAILED')
        self.assertEqual(self.given, [])
        self.assertIn('the Data Fabric could not read the platform', self.result(p)['log'])

    def test_frost_not_keeping_the_state_is_said(self):
        self.agent(FABRIC)
        p = Platform()
        original = p.post
        p.post = lambda office, route, data: (403, {'refused': 'no open run'}) if route == '/fabric/state' else original(office, route, data)   # FROST reads the state, but will not keep it
        with self.sandboxed(self.ANSWER):
            self.assertEqual(self.harness(p).run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), 'FAILED')
        self.assertIn('FROST did not keep the Data Fabric state: no open run', self.result(p)['log'])

    def test_an_agent_without_fabric_gets_none_of_it(self):
        self.agent({'records': {'invc': ['read', 'edit']}})
        p = Platform()
        with self.sandboxed(self.ANSWER):
            self.assertEqual(self.harness(p).run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), 'DONE')
        self.assertNotIn('fabric', self.given[0])
        self.assertEqual(self.most_bytes, harness.sandbox.MOST_BYTES)   # every other agent: the runtime's own 1 MB
        self.assertEqual((p.asked('/dam/fabric'), p.posted('/agnt/records/edit'), p.posted('/fabric/state')), ([], [], []))


class TheCall(World):
    def test_the_page_is_handed_its_state_only(self):
        self.agent(FABRIC, calls=['panel'])
        p = Platform()
        with self.sandboxed({'view': {'html': '<section>ok</section>', 'css': ''}}):
            self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertEqual(self.given[0]['fabric']['state']['apis'][0]['api_state'], 'live')
        self.assertNotIn('records', self.given[0])                 # its modules are read on its RUN, not on every page
        self.assertEqual(p.asked('/dam/fabric'), [])

    def test_a_public_agent_reading_records_is_handed_no_custom_field(self):
        self.agent({'records': {'invc': ['read']}}, calls=['panel'])
        p = Platform()
        with self.sandboxed({'view': {'html': '<section>ok</section>', 'css': ''}}):
            self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertEqual(sorted(self.given[0]['records']['invc'][0]), ['MINV_norm_key', 'identity_invoice_number', 'key'])

    def test_a_private_agent_of_this_account_is_handed_them(self):
        self.agent({'records': {'invc': ['read']}}, calls=['panel'])
        p = Platform()
        with self.sandboxed({'view': {'html': '<section>ok</section>', 'css': ''}}):
            self.harness(p, card={**CARD, 'authorization': 'PRIVATE', 'account_key': ACCOUNT}).answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertEqual(self.given[0]['records']['invc'][0]['custom_0004'], '100.00')

    def test_a_public_agent_asking_to_write_a_custom_field_is_refused(self):
        self.agent({'records': {'invc': ['read', 'edit']}}, calls=['panel'])
        p = Platform()
        asks = {'writes': [{'do': 'edit', 'species': 'invc', 'key': INVOICE, 'values': {'custom_0004': '9'}}], 'view': {'html': '<section>x</section>', 'css': ''}}
        with self.sandboxed(asks):
            with self.assertRaises(harness.Refused) as no:
                self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, act=True)
        self.assertIn('only a custom agent may write', no.exception.reason)
        self.assertEqual(p.posted('/agnt/records/edit'), [])


if __name__ == '__main__':
    unittest.main()
