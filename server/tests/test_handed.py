"""THE PLATFORM'S ANSWERS HANDED WITH THE CALL (the owner 2026-11-04, "the goal is extremely fast"): a page's CALL may carry
the platform's own answers to the asks the runtime would make back (the cards, the member's hires, the mTok balance, the
records list); the runtime takes those and asks the platform for nothing else it was handed. The approval is never handed
and never asked: it is the runtime's own locker (the core cleanup 2026-11-05), checked afresh at every call, hire and RUN.
After the member's writes are carried, every read asks the platform again (the truth after the act)."""
import json
import pathlib
import sqlite3
import tempfile
import unittest
from unittest import mock

from _here import APP  # noqa: F401
from core_engine import harness, locker, store

KEY = 'MAGT_0000000000AB_0001'
ACCOUNT, SCOPE, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'SCRATCH', 'MCON_' + 'B' * 12 + '_0002'
CARD = {'key': KEY, 'name': 'Scratch meetings', 'screen': 'larry/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents',
        'price': '0', 'status': 'APPROVED', 'authorization': 'PUBLIC', 'account_key': ''}
HIRED = [{'agent_key': KEY, 'board': 'larry/home', 'shell_id': 1, 'on': True, 'job_key': ''}]
ROW = {'MOPN_norm_key': 'MOPN_' + 'C' * 12 + '_0003', 'identity_operations_headline': 'Standup'}
LIST = {'account': ACCOUNT, 'scope': SCOPE, 'member': MEMBER, 'agent_key': KEY, 'segment': 'opns', 'page': 'list', 'limit': '200', 'offset': '0'}


class Platform:
    """The platform as the runtime hears it, every ask counted."""
    def __init__(self):
        self.said = []

    def get(self, office, route, data=None):
        self.said.append((office, route))
        if route == '/agnt/cards':
            return 200, {'cards': [CARD]}
        if route == '/agnt/hired':
            return 200, {'hired': HIRED}
        if route == '/jobs/balance':
            return 200, {'subscriptions': []}
        if route == '/agnt/records/list':
            return 200, {'rows': [dict(ROW)], 'total': 1, 'first': []}
        return 404, {'refused': route}

    def post(self, office, route, data):
        self.said.append((office, route))
        if route == '/agnt/records/add':
            return 200, {'key': 'MOPN_' + 'D' * 12 + '_0004'}
        return 200, {}

    def asked(self, office=None):
        return [r for o, r in self.said if office is None or o == office]


def handed(rows=(ROW,)):
    """The platform's own answers to a CALL's asks, as wid hands them."""
    return [{'office': 'wid', 'method': 'GET', 'route': '/agnt/cards', 'data': {}, 'status': 200, 'body': {'cards': [CARD]}},
            {'office': 'wid', 'method': 'GET', 'route': '/agnt/hired', 'data': {'account': ACCOUNT, 'scope': SCOPE, 'member': MEMBER}, 'status': 200, 'body': {'hired': HIRED}},
            {'office': 'wid', 'method': 'GET', 'route': '/jobs/balance', 'data': {'account': ACCOUNT}, 'status': 200, 'body': {'subscriptions': []}},
            {'office': 'wid', 'method': 'GET', 'route': '/agnt/records/list', 'data': LIST, 'status': 200, 'body': {'rows': [dict(r) for r in rows], 'total': len(rows), 'first': []}}]


class TheHandedCall(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        instance, self.agents = pathlib.Path(tmp.name) / 'instance', pathlib.Path(tmp.name) / 'agents'
        instance.mkdir()
        self.db = store.open_store(instance)
        folder = self.agents / 'meet'
        folder.mkdir(parents=True)
        manifest = {'name': 'Scratch meetings', 'entry': 'agent.py', 'calls': ['panel'], 'run': {'do': 'go', 'hands': []}, 'gives': ['view', 'writes'],
                    'skills': [], 'records': {'opns': ['read', 'add']}}
        (folder / 'agent.json').write_text(json.dumps(manifest))
        (folder / 'agent.py').write_text('print("{}")\n')
        locker.add(self.db, self.agents, KEY, 'meet')
        self.given, self.answers = [], []

        def run(folder, entry, given, seconds=20, on_start=None, most_bytes=harness.sandbox.MOST_BYTES, internal=False):
            self.given.append(json.loads(json.dumps(given)))
            return 'DONE', (self.answers.pop(0) if self.answers else {'view': {'html': '<section>ok</section>', 'css': ''}}), ''
        p = mock.patch.object(harness.sandbox, 'run', run)
        p.start()
        self.addCleanup(p.stop)

    def harness(self, platform):
        return harness.Harness(self.db, self.agents, platform)

    def test_a_handed_call_asks_the_platform_for_nothing(self):
        p = Platform()
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, beside={'page': {'path': '/x'}}, handed=handed())
        self.assertEqual(p.asked(), [])                                                # the approval is the runtime's own locker: nothing asked
        self.assertEqual([r['key'] for r in self.given[0]['records']['opns']], [ROW['MOPN_norm_key']])   # the handed rows, as a read gives them

    def test_a_changed_agent_is_refused_at_the_next_call_without_asking_anyone(self):
        p = Platform()
        h = self.harness(p)
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        (self.agents / 'meet' / 'agent.py').write_text('print("{ }")\n')             # the folder no longer what was placed
        with self.assertRaises(harness.Refused):
            h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        self.assertEqual(p.asked(), [])

    def test_a_hire_and_a_run_verify_the_locker_every_time_and_never_ask_an_office(self):
        p = Platform()
        h = self.harness(p)
        self.assertEqual(h.facts(ACCOUNT, SCOPE, MEMBER)[3](KEY), (True, ''))
        (self.agents / 'meet' / 'agent.py').write_text('print("{ }")\n')
        self.assertEqual(h.facts(ACCOUNT, SCOPE, MEMBER)[3](KEY), (False, 'tampered: the code changed'))
        self.assertEqual({o for o, _r in p.said}, {'wid'})                             # wid alone, never fs, cc, so or lryllm

    def test_only_the_four_answers_are_taken(self):
        p = Platform()
        forged = handed() + [{'office': 'fs', 'method': 'GET', 'route': '/agents/approved', 'data': {}, 'status': 200, 'body': {'approved': []}},
                             {'office': 'cc', 'method': 'GET', 'route': '/mtok/balance', 'data': {'account': ACCOUNT}, 'status': 200, 'body': {'subscriptions': []}},
                             {'office': 'wid', 'method': 'POST', 'route': '/agnt/records/add', 'data': {}, 'status': 200, 'body': {}},
                             'junk', {'office': 'wid', 'method': 'GET', 'route': '/agnt/cards', 'data': 'x', 'status': 200, 'body': {}}]
        self.assertEqual(self.harness(p).handing(forged), 4)
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=forged)
        self.assertEqual(p.asked(), [])

    def test_a_handed_answer_not_matching_the_ask_is_not_used(self):
        p = Platform()
        other = [dict(a, data={**a['data'], 'member': 'MCON_' + 'E' * 12 + '_0009'}) if a['route'] != '/agnt/cards' else a for a in handed()]
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=other)
        self.assertIn('/agnt/hired', p.asked())                                         # another member's answer: this member's is asked
        self.assertIn('/agnt/records/list', p.asked())

    def test_without_handed_answers_the_call_asks_as_before(self):
        p = Platform()
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertEqual(sorted(set(p.asked())), ['/agnt/cards', '/agnt/hired', '/agnt/records/list', '/jobs/balance'])

    def test_after_the_writes_every_read_asks_the_platform(self):
        p = Platform()
        self.answers = [{'writes': [{'do': 'add', 'species': 'opns', 'values': {'identity_operations_headline': 'New'}}], 'view': {'html': '<section>a</section>', 'css': ''}},
                        {'view': {'html': '<section>b</section>', 'css': ''}}]
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed(), act=True)
        self.assertEqual(p.asked('wid'), ['/agnt/records/add', '/agnt/records/list'])    # the write, then the records read again from the platform

    def test_the_handed_answers_do_not_outlive_the_call(self):
        p = Platform()
        h = self.harness(p)
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertIn('/agnt/records/list', p.asked())


class TheKeepWord(TheHandedCall):
    """STEP E: the runtime says beside every answer how long the platform may draw it again (keep), from the approved manifest,
    never the agent's word."""
    def answer(self, manifest_extra=None, **kw):
        if manifest_extra:
            folder = self.agents / 'meet'
            m = json.loads((folder / 'agent.json').read_text())
            (folder / 'agent.json').write_text(json.dumps({**m, **manifest_extra}))
            con = sqlite3.connect(self.db)
            con.execute('DELETE FROM runtime_locker WHERE agent_key = ?', (KEY,))   # the new version placed in its stead
            con.commit()
            con.close()
            locker.add(self.db, self.agents, KEY, 'meet')
        return self.harness(Platform()).answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed(), **kw)

    def test_a_plain_answer_is_kept_the_minute(self):
        self.assertEqual(self.answer()['keep'], 'minute')

    def test_the_manifest_may_say_day_or_none(self):
        self.assertEqual(self.answer({'keep': 'day'})['keep'], 'day')
        self.assertEqual(self.answer({'keep': 'none'})['keep'], 'none')
        self.assertEqual(self.answer({'keep': 'forever'})['keep'], 'minute')   # anything else: the default

    def test_an_act_is_never_kept(self):
        self.assertEqual(self.answer(act=True)['keep'], 'none')

    def test_records_not_read_are_never_kept(self):
        p = Platform()
        p.get = (lambda get: lambda office, route, data=None: (503, {}) if route == '/agnt/records/list' else get(office, route, data))(p.get)
        out = self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY)   # nothing handed: the records asked back, and refused
        self.assertEqual(out['keep'], 'none')

    def test_an_agent_with_runs_is_never_kept(self):
        self.assertEqual(self.answer({'gives': ['view', 'writes', 'run']})['keep'], 'none')

    def test_the_agent_cannot_say_keep(self):
        self.answers = [{'view': {'html': '<section>a</section>', 'css': ''}, 'keep': 'day'}]
        with self.assertRaises(harness.Refused):
            self.answer({'gives': ['view', 'writes', 'keep']})


if __name__ == '__main__':
    unittest.main()
