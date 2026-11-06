"""THE MEMBER'S RECORDS ON A RUN (hands ["records"], CORE_CLEANUP_IV 30, the owner's blanket approval 2026-11-06): an agent whose approved
manifest declares records with read and names "records" in run.hands is handed, on a RUN, exactly what a CALL of it is handed: each declared
species read through wid's own list door (/agnt/records/list) for this member, and who they are for. Nothing undeclared is asked; nothing is
kept by the runtime; wid silent or refusing fails the RUN before it starts. An agent without the hand is never handed records.
wid here is a Recorder (this process; it answers only what the test gives it); what wid answers is proven live only."""
import json
import sqlite3
import unittest

from _here import APP  # noqa: F401
from core_engine import harness, locker
from test_job_inputs import ACCOUNT, JOB, KEY, MEMBER, SCOPE, Echo

PLANTED = 'Zanzibar-7731-private-contact'
ROWS = {'cont': [{'MCON_norm_key': 'MCON_' + 'C' * 12 + '_0003', 'data_full_name': PLANTED}], 'invc': [{'MINV_norm_key': 'MINV_' + 'D' * 12 + '_0004', 'data_total': '12'}]}


class Wid:
    """wid as a Recorder: /agnt/records/list answers the rows the test gives each species (or refuses); every call is recorded."""
    def __init__(self, rows, status=200):
        self.rows, self.status, self.said = rows, status, []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        if route == '/agnt/records/list':
            if self.status != 200:
                return self.status, {'refused': 'not hired by that member'}
            got = self.rows.get(data['segment'], [])
            return 200, {'rows': got[int(data['offset']):], 'total': len(got)}
        return 200, {}

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return (200, {'charged': 0, 'free': True}) if route == '/jobs/charge' else (200, {'saved': True})


class RunRecords(Echo):
    def agent(self, records=None, hands=('records',)):
        folder = self.agents / 'echo'
        if folder.exists():
            import shutil
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        manifest = {'name': 'Echo', 'entry': 'agent.py', 'run': {'do': 'answer', 'hands': list(hands)}, 'gives': ['delivery']}
        if records is not None:
            manifest['records'] = records
        (folder / 'agent.json').write_text(json.dumps(manifest))
        (folder / 'agent.py').write_text('import json, sys\ng = json.load(sys.stdin)\nprint(json.dumps({"delivery": json.dumps({"records": g.get("records"), "who": g.get("who")}, sort_keys=True)}))\n')
        con = sqlite3.connect(self.db)
        con.execute('DELETE FROM runtime_locker')
        con.commit()
        con.close()
        locker.add(self.db, self.agents, KEY, 'echo')

    def listed(self, wid):
        return [d['segment'] for _o, route, d in wid.said if route == '/agnt/records/list']

    def test_the_declared_records_are_handed_on_a_run(self):
        self.agent({'cont': ['read'], 'invc': ['read', 'add']})
        wid = Wid(ROWS)
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(sorted(self.listed(wid)), ['cont', 'invc'])
        asked = [d for _o, route, d in wid.said if route == '/agnt/records/list'][0]
        self.assertEqual((asked['account'], asked['scope'], asked['member'], asked['agent_key']), (ACCOUNT, SCOPE, MEMBER, KEY))   # this member, as this agent: wid's own checks
        got = json.loads(self.results(wid)[-1]['delivery'])
        self.assertEqual(got['who'], {'member': MEMBER})
        self.assertEqual([r['data_full_name'] for r in got['records']['cont']], [PLANTED])
        self.assertEqual([r['key'] for r in got['records']['invc']], [ROWS['invc'][0]['MINV_norm_key']])
        for path in self.instance.rglob('*'):
            if path.is_file():
                self.assertNotIn(PLANTED.encode(), path.read_bytes(), f'{path.name} keeps a record')

    def test_a_species_declared_without_read_is_never_asked(self):
        self.agent({'cont': ['read'], 'invc': ['add']})
        wid = Wid(ROWS)
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(self.listed(wid), ['cont'])
        self.assertNotIn('invc', json.loads(self.results(wid)[-1]['delivery'])['records'])

    def test_a_refusing_wid_fails_the_run_before_it_starts(self):
        self.agent({'cont': ['read']})
        wid = Wid(ROWS, status=403)
        self.assertEqual(self.run_with(wid), 'FAILED')
        end = self.results(wid)
        self.assertEqual([r['state'] for r in end], ['FAILED'])   # never RUNNING: the agent did not run
        self.assertEqual(end[0]['log'], 'LARRYD could not read the records: not hired by that member')

    def test_without_the_hand_no_records_are_asked_or_handed(self):
        self.agent({'cont': ['read']}, hands=())
        wid = Wid(ROWS)
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(self.listed(wid), [])
        self.assertEqual(json.loads(self.results(wid)[-1]['delivery']), {'records': None, 'who': None})

    def test_the_hand_with_no_records_declared_hands_none(self):
        self.agent(None)
        wid = Wid(ROWS)
        self.assertEqual(self.run_with(wid), 'DONE')
        self.assertEqual(self.listed(wid), [])
        self.assertEqual(json.loads(self.results(wid)[-1]['delivery'])['records'], {})

    def test_records_is_a_hand_the_runtime_has(self):
        self.assertIn('records', harness.HANDS)


if __name__ == '__main__':
    unittest.main()
