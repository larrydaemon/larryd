"""THE PLATFORM'S ANSWERS HANDED WITH THE CALL (the owner 2026-11-04, "the goal is extremely fast"): a page's CALL may carry
the platform's own answers to the asks the runtime would make back (the cards, the member's hires, the mTok balance, the
records list); the runtime takes those and asks the platform for nothing else it was handed. FROST is never handed: its
approved list is the runtime's own word, kept a short while for a page's CALL, asked again on a miss; a hire and a RUN ask
FROST every time. After the member's writes are carried, every read asks the platform again (the truth after the act)."""
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
    def __init__(self, approved):
        self.approved, self.said = approved, []

    def get(self, office, route, data=None):
        self.said.append((office, route))
        if route == '/agnt/cards':
            return 200, {'cards': [CARD]}
        if route == '/agnt/hired':
            return 200, {'hired': HIRED}
        if route == '/mtok/balance':
            return 200, {'subscriptions': []}
        if route == '/agents/approved':
            return 200, {'approved': self.approved}
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
            {'office': 'cc', 'method': 'GET', 'route': '/mtok/balance', 'data': {'account': ACCOUNT}, 'status': 200, 'body': {'subscriptions': []}},
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
        row = locker.held(self.db, KEY)
        self.approved = [{'agent_key': row['agent_key'], 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256'], 'card_key': ''}]
        self.given, self.answers = [], []

        def run(folder, entry, given, seconds=20, on_start=None, most_bytes=harness.sandbox.MOST_BYTES, internal=False):
            self.given.append(json.loads(json.dumps(given)))
            return 'DONE', (self.answers.pop(0) if self.answers else {'view': {'html': '<section>ok</section>', 'css': ''}}), ''
        p = mock.patch.object(harness.sandbox, 'run', run)
        p.start()
        self.addCleanup(p.stop)

    def harness(self, platform):
        return harness.Harness(self.db, self.agents, platform)

    def test_a_handed_call_asks_the_platform_for_nothing_but_frost(self):
        p = Platform(self.approved)
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, beside={'page': {'path': '/x'}}, handed=handed())
        self.assertEqual(p.asked(), ['/agents/approved'])                              # FROST, the runtime's own word, and nothing else
        self.assertEqual([r['key'] for r in self.given[0]['records']['opns']], [ROW['MOPN_norm_key']])   # the handed rows, as a read gives them

    def test_frost_kept_for_a_page_and_asked_again_on_a_miss(self):
        p = Platform(self.approved)
        h = self.harness(p)
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        self.assertEqual(p.asked(), ['/agents/approved'])                              # kept: the second page asks nothing
        p.approved = []                                                                # revoked at FROST
        h._approved = (h._approved[0], {})                                             # and the kept list knows it not: a miss
        with self.assertRaises(harness.Refused):
            h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        self.assertEqual(p.asked(), ['/agents/approved', '/agents/approved'])           # asked again before the refusal

    def test_a_hire_and_a_run_ask_frost_every_time(self):
        p = Platform(self.approved)
        h = self.harness(p)
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        h.facts(ACCOUNT, SCOPE, MEMBER)
        h.facts(ACCOUNT, SCOPE, MEMBER)
        self.assertEqual(p.asked('fs'), ['/agents/approved'] * 3)

    def test_only_the_four_answers_are_taken(self):
        p = Platform(self.approved)
        forged = handed() + [{'office': 'fs', 'method': 'GET', 'route': '/agents/approved', 'data': {}, 'status': 200, 'body': {'approved': []}},
                             {'office': 'wid', 'method': 'POST', 'route': '/agnt/records/add', 'data': {}, 'status': 200, 'body': {}},
                             'junk', {'office': 'wid', 'method': 'GET', 'route': '/agnt/cards', 'data': 'x', 'status': 200, 'body': {}}]
        self.assertEqual(self.harness(p).handing(forged), 4)
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=forged)
        self.assertEqual(p.asked(), ['/agents/approved'])                              # FROST asked itself, never the handed word

    def test_a_handed_answer_not_matching_the_ask_is_not_used(self):
        p = Platform(self.approved)
        other = [dict(a, data={**a['data'], 'member': 'MCON_' + 'E' * 12 + '_0009'}) if a['route'] != '/agnt/cards' else a for a in handed()]
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=other)
        self.assertIn('/agnt/hired', p.asked())                                         # another member's answer: this member's is asked
        self.assertIn('/agnt/records/list', p.asked())

    def test_without_handed_answers_the_call_asks_as_before(self):
        p = Platform(self.approved)
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertEqual(sorted(set(p.asked())), ['/agents/approved', '/agnt/cards', '/agnt/hired', '/agnt/records/list', '/mtok/balance'])

    def test_after_the_writes_every_read_asks_the_platform(self):
        p = Platform(self.approved)
        self.answers = [{'writes': [{'do': 'add', 'species': 'opns', 'values': {'identity_operations_headline': 'New'}}], 'view': {'html': '<section>a</section>', 'css': ''}},
                        {'view': {'html': '<section>b</section>', 'css': ''}}]
        self.harness(p).answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed(), act=True)
        self.assertEqual(p.asked('wid'), ['/agnt/records/add', '/agnt/records/list'])    # the write, then the records read again from the platform

    def test_the_handed_answers_do_not_outlive_the_call(self):
        p = Platform(self.approved)
        h = self.harness(p)
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY, handed=handed())
        h.answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertIn('/agnt/records/list', p.asked())


if __name__ == '__main__':
    unittest.main()
