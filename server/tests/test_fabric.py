"""THE LARRY DATA FABRIC, ONE SNAPSHOT (the owner 2026-11-04: "it should only use a snapshot from the database so the data
is very fast and no connections / just 1 updated snapshot per day / everything else we need to delete"): an agent declaring
"fabric": {"snapshot": true} is handed, on a CALL, FROST's snapshot (apis, databases) and who looks, from ONE read; nothing
is brought in (no files, no records, no custom fields, nothing saved back). Custom data only on custom agents (an agent
PRIVATE to this account); any other agent is handed rows without their custom field buckets and may not write one. These
tests stand the sandbox in for one that hands back a fixed answer: what the agent itself does is proven by the agent's own walk."""
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
FABRIC = {'fabric': {'snapshot': True}}


class Platform:
    """The platform as the runtime hears it: wid's record doors, DA-M's Fabric files, FROST's Fabric state, mTok."""
    def __init__(self, rows=None, state=None, files=None, refuse=()):
        self.rows = rows if rows is not None else [dict(ROW)]
        self.state = state or {'apis': [{'api_name': 'VIRTUAL WIRE API', 'api_state': 'live', 'synced_at': ''}], 'databases': [{'db_office': 'FS', 'db_name': 'one.db', 'db_state': 'UP'}]}
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
        if route == '/agnt/records/fields':   # the account's own custom fields, every module asked in one answer (EDIT CUSTOM FIELDS)
            return 200, {'fields_by': {g: [{'slot': 'custom_0004', 'name': 'total', 'type': 'text'}, {'slot': 'not_a_bucket', 'name': 'x', 'type': 'text'}] for g in data['segments'].split(',')}}
        if route == '/agnt/fabric':
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
        if route == '/agnt/records/fields':   # pf_mapping.csv: one custom field set (a REMOVEd bucket refused)
            return (400, {'refused': 'custom_0009 is not a free custom bucket of this module'}) if data['slot'] == 'custom_0009' else (200, {'slot': data['slot']})
        if route == '/jobs/charge':
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
        manifest = {'name': 'PF DATA FABRIC', 'entry': 'agent.py', 'run': {'do': 'go', 'hands': []}, 'gives': ['view', 'delivery', 'writes'], 'skills': [], **(extra or {})}
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
    def test_only_the_snapshot_counts(self):
        self.assertTrue(fabric.declared({'fabric': {'snapshot': True}}))
        for asked in ({'fabric': {'modules': ['invc']}, 'records': {'invc': ['read', 'edit']}}, {'fabric': {'snapshot': 'yes'}}, {'fabric': True}, {}, None):
            self.assertFalse(fabric.declared(asked), asked)   # the old import's declaration counts for nothing now

    def test_custom_is_a_private_agent_of_this_account_alone(self):
        self.assertTrue(fabric.custom({**CARD, 'authorization': 'PRIVATE', 'account_key': ACCOUNT}, {}, ACCOUNT))
        self.assertFalse(fabric.custom({**CARD, 'authorization': 'PRIVATE', 'account_key': 'ACCT_' + 'E' * 12 + '_0009'}, {}, ACCOUNT))
        self.assertFalse(fabric.custom(CARD, FABRIC, ACCOUNT))   # the Data Fabric fills no custom field any more


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


class TheRun(World):
    ANSWER = {'delivery': 'done'}

    def test_a_run_of_the_fabric_is_handed_nothing_of_the_old_import(self):
        self.agent(FABRIC)
        p = Platform()
        with self.sandboxed(self.ANSWER):
            self.assertEqual(self.harness(p).run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), 'DONE')
        self.assertNotIn('fabric', self.given[0])
        self.assertEqual(self.most_bytes, harness.sandbox.MOST_BYTES)   # the runtime's own 1 MB, as every agent
        self.assertEqual((p.asked('/dam/fabric'), p.asked('/agnt/records/fields'), p.asked('/agnt/fabric'), p.posted('/agnt/fabric')), ([], [], [], []))


class TheCall(World):
    def test_the_page_is_handed_the_snapshot_from_one_read(self):
        self.agent(FABRIC, calls=['panel'])
        p = Platform()
        with self.sandboxed({'view': {'html': '<section>ok</section>', 'css': ''}}):
            self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY)
        state = self.given[0]['fabric']['state']
        self.assertEqual((sorted(state), state['apis'][0]['api_state'], state['databases'][0]['db_state']), (['apis', 'databases'], 'live', 'UP'))
        self.assertEqual(len(p.asked('/agnt/fabric')), 1)   # ONE read
        self.assertEqual((p.asked('/dam/fabric'), p.asked('/agnt/records/fields'), p.asked('/agnt/records/list')), ([], [], []))   # no files, no fields, no records
        self.assertNotIn('records', self.given[0])
        self.assertEqual(self.given[0]['fabric']['viewer'], {'member_type': ''})   # FROST did not say who looks: the page masks

    def test_the_page_is_told_who_looks_for_its_mask(self):
        self.agent(FABRIC, calls=['panel'])
        p = Platform()
        p.state = {**p.state, 'viewer': {'member_type': 'system_owner', 'first_name': 'never handed'}}   # FROST says who looks with the state
        with self.sandboxed({'view': {'html': '<section>ok</section>', 'css': ''}}):
            self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertEqual(self.given[0]['fabric']['viewer'], {'member_type': 'system_owner'})   # its member type alone, never the name

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
