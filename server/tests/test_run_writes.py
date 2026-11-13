"""THE WRITES OF A RUN, THE ONE NEW RIGHT (the owner 2026-11-13: "no run is ever pressed"; asked whether an approved internal agent may write the
records its card declares when its RUN is started by a clock or by a member's save: "lets go"). A RUN's answer may carry `writes`, held as a
CALL's are (each a declared verb on a declared species, carried to wid's own doors for this member), ONLY for an internal agent on LARRYD
RUNTIME INTERNAL whose approved manifest says "run": {"writes": true}. Without the word, or on the external runtime, the writes are dropped
and the RUN's line says so; an undeclared species or verb refuses them all; records not read: nothing written; a write wid refuses ends the
RUN FAILED with what was carried. wid here is a Recorder (this process; it answers only what the test gives it)."""
import json
import sqlite3
import unittest

from _here import APP  # noqa: F401
from core_engine import harness, locker
from test_job_inputs import ACCOUNT, CARD, HIRED, JOB, KEY, MEMBER, SCOPE, Echo

ROW = {'MOPN_norm_key': 'MOPN_' + 'A' * 12 + '_0001', 'data_notes': 'as it was'}
ADD = {'do': 'add', 'species': 'opns', 'values': {'data_notes': 'scratch news'}}
EDIT = {'do': 'edit', 'species': 'opns', 'key': ROW['MOPN_norm_key'], 'values': {'data_notes': 'scratch news, again'}}


class Wid:
    """wid as a Recorder: the list door answers one row; the write doors answer a key, or refuse the edit when told to; every call is recorded."""
    def __init__(self, refuse_edit=False, listed=200):
        self.refuse_edit, self.listed, self.said = refuse_edit, listed, []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        if route == '/agnt/records/list':
            return (200, {'rows': [ROW][int(data['offset']):], 'total': 1}) if self.listed == 200 else (self.listed, {'refused': 'not hired by that member'})
        return 200, {}

    def post(self, office, route, data):
        self.said.append((office, route, data))
        if route == '/agnt/records/add':
            return 200, {'key': 'MOPN_' + 'B' * 12 + '_0002'}
        if route == '/agnt/records/edit':
            return (403, {'refused': 'not that member\'s record'}) if self.refuse_edit else (200, {'key': data['key']})
        return (200, {'charged': 0, 'free': True}) if route == '/jobs/charge' else (200, {'saved': True})


class RunWrites(Echo):
    def agent(self, writes, word=True, records=None, internal=True, gives=('delivery', 'writes')):
        folder = self.agents / 'echo'
        if folder.exists():
            import shutil
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        manifest = {'name': 'Echo', 'entry': 'agent.py', 'run': {'do': 'answer', 'hands': [], **({'writes': word} if word is not None else {})}, 'gives': list(gives),
                    'records': {'opns': ['read', 'add', 'edit']} if records is None else records, **({'internal': {'seconds': 30}} if internal else {})}
        if not manifest['records']:
            del manifest['records']
        (folder / 'agent.json').write_text(json.dumps(manifest))
        (folder / 'agent.py').write_text('import json, sys\ng = json.load(sys.stdin)\n'
                                         f'print(json.dumps({{"delivery": "seen " + str(len((g.get("records") or {{}}).get("opns") or [])), "writes": {json.dumps(writes)}}}))\n')
        con = sqlite3.connect(self.db)
        con.execute('DELETE FROM runtime_locker')
        con.commit()
        con.close()
        locker.add(self.db, self.agents, KEY, 'echo')

    def run_with(self, client, internal=True):
        h = harness.Harness(self.db, self.agents, client)
        h.INTERNAL = internal   # LARRYD RUNTIME INTERNAL (its start says so, LARRYD_INTERNAL=1), or the external runtime
        h.facts = lambda account, scope, member: ([CARD], HIRED, [], lambda key: (True, ''))
        return h.run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1)

    @staticmethod
    def written(wid):
        return [(route.rsplit('/', 1)[1], d) for _o, route, d in wid.said if route.startswith('/agnt/records/') and route != '/agnt/records/list']

    def test_an_internal_agent_whose_manifest_says_so_writes_on_a_run(self):
        self.agent([ADD, EDIT])
        wid = Wid()
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual([do for do, _d in self.written(wid)], ['add', 'edit'])
        add = self.written(wid)[0][1]
        self.assertEqual((add['account'], add['scope'], add['member'], add['agent_key'], add['segment'], add['values']), (ACCOUNT, SCOPE, MEMBER, KEY, 'opns', ADD['values']))   # this member, as this agent: wid's own doors decide the rest
        end = self.results(wid)[-1]
        self.assertEqual(end['state'], 'DONE')
        self.assertIn('2 of 2 record writes carried', end['log'])
        self.assertEqual(end['delivery'], 'seen 1')   # the writes are never the delivery

    def test_without_the_word_the_writes_are_dropped_and_the_run_says_so(self):
        for word in (None, False, 'yes', 1):
            with self.subTest(word):
                self.agent([ADD], word=word)
                wid = Wid()
                self.assertEqual(self.run_with(wid), 'DONE')
                self.assertEqual(self.written(wid), [])
                self.assertIn('writes not carried: its approved manifest does not say a RUN of it writes', self.results(wid)[-1]['log'])

    def test_the_external_runtime_and_an_agent_that_is_not_internal_never_write_on_a_run(self):
        self.agent([ADD])
        wid = Wid()
        self.run_with(wid, internal=False)   # the external runtime: the word alone is not enough
        self.assertEqual(self.written(wid), [])
        self.agent([ADD], internal=False, gives=('delivery', 'writes'))
        wid = Wid()
        self.run_with(wid)                   # LARRYD RUNTIME INTERNAL, an agent that does not declare "internal"
        self.assertEqual(self.written(wid), [])

    def test_a_species_or_a_verb_not_declared_refuses_them_all(self):
        for bad, why in (({'do': 'add', 'species': 'cont', 'values': {'data_full_name': 'x'}}, 'names a species the agent does not declare'),
                         ({'do': 'remove', 'species': 'opns', 'key': ROW['MOPN_norm_key']}, 'asks to remove opns, which the agent does not declare')):
            with self.subTest(why):
                self.agent([ADD, bad])
                wid = Wid()
                self.assertEqual(self.run_with(wid), 'FAILED')
                self.assertEqual(self.written(wid), [])   # one fault refuses them all: the good one is not carried either
                self.assertIn(why, self.results(wid)[-1]['log'])
                self.assertIn('nothing was written', self.results(wid)[-1]['log'])

    def test_no_records_declared_or_none_read_writes_nothing(self):
        self.agent([ADD], records={})
        wid = Wid()
        self.run_with(wid)
        self.assertEqual(self.written(wid), [])   # no records declared: none were read, an agent that saw none decided blind
        self.assertIn('writes not carried: the records were not read', self.results(wid)[-1]['log'])
        self.agent([ADD])
        wid = Wid(listed=403)
        self.assertEqual(self.run_with(wid), 'FAILED')   # wid refused the read: the RUN fails before the agent runs
        self.assertEqual(self.written(wid), [])

    def test_a_write_the_platform_refuses_ends_the_run_failed_with_what_was_carried(self):
        self.agent([ADD, EDIT])
        wid = Wid(refuse_edit=True)
        self.assertEqual(self.run_with(wid), 'FAILED')
        end = self.results(wid)[-1]
        self.assertEqual(end['state'], 'FAILED')
        self.assertIn("1 of 2 record writes carried; refused: not that member's record", end['log'])

    def test_a_run_that_asks_no_writes_is_as_it_was(self):
        self.agent([])
        wid = Wid()
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(self.written(wid), [])
        self.assertNotIn('writes', self.results(wid)[-1]['log'])


if __name__ == '__main__':
    unittest.main()
