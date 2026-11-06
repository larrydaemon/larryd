"""DEFAULT AGENTS (the owner, 2026-10-09: "a few agents will be turned on as default when new users come in so its not
blank and empty"): on a board's first visit the runtime places the marketplace as before AND every card the system owner
marked on by default whose screen is that board, each through the platform's own hire door, each leaving a hire record.
Never by default: a card of another board, an unmarked card, one already hired, an offline one, one the locker or FROST
does not verify, one the platform's door refuses, and one that names an outside AI service (the member's own hire is the
permission for that). The runtime keeps nothing of it: "once" is the platform's, so a let-go agent does not come back
unless the platform asks again (it asks only when a board is born)."""
import pathlib
import sqlite3
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import harness, store

ACCOUNT, MEMBER = 'ACCT_000000000001_0001', 'MCON_000000000002_0002'
MARKET = 'MAGT_00000000CA01_0001'
BOARD, HOME = 'agencymgmt/hrcy/home', 'larryd/agnt/home'


def card(key, screen=BOARD, **more):
    return {'key': key, 'status': 'APPROVED', 'screen': screen, 'price': '', 'product': 'AGENCY MGMT', 'product_slug': 'agencymgmt',
            'name': key, 'module': 'HIERARCHIES', 'sends_to': '', 'offline': False, 'default': False, **more}


class Platform(harness.Harness):
    """The platform's facts given in this process, and its hire door: what it was asked, what it refuses."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.cards, self.hired, self.groups, self.unverified, self.asked, self.refuses = [], [], [], set(), [], {}
        self.core_names_a_service = set()   # THE PLATFORM'S OWN CARD names an outside AI service, whatever the facts this runtime read say

    def marketplace_key(self):
        return MARKET

    def facts(self, account, scope, member):
        return self.cards, self.hired, self.groups, lambda key: (False, 'not approved by FROST') if key in self.unverified else (True, '')

    def _ask(self, office, method, route, data):
        self.asked.append((office, method, route, dict(data)))
        if data['agent_key'] in self.refuses:
            raise harness.Refused(403, self.refuses[data['agent_key']])
        if 'default' in data and data['agent_key'] in self.core_names_a_service:   # the platform's door, told it is a default placement, decides on its own card
            raise harness.Refused(403, 'not placed by default: it names an outside AI service, the member hires it themselves')
        self.hired.append({'agent_key': data['agent_key'], 'on': True})   # the platform's hire: a shell holding it, switched on
        return {'board': BOARD}


class DefaultAgents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = pathlib.Path(self.tmp.name)
        self.p = Platform(store.open_store(base), base / 'agents', client=None, caller='scratch')
        self.p.cards = [card(MARKET, HOME, product='LARRYD', product_slug='larryd')]

    def first(self, board=BOARD):
        return self.p.defaults(ACCOUNT, 'SCRATCH', MEMBER, board)

    def hires(self):
        con = sqlite3.connect(self.p.db)
        rows = con.execute("SELECT agent_key, state, account, member FROM runtime_runs WHERE lane = 'hire' ORDER BY id").fetchall()
        con.close()
        return rows

    def test_the_marketplace_as_before_on_its_own_screen_only(self):
        self.assertEqual(self.first(), {'placed': [], 'skipped': []})
        self.assertEqual(self.first(HOME), {'placed': [MARKET], 'skipped': []})
        self.assertEqual(self.p.asked, [('wid', 'POST', '/agnt/hire', {'account': ACCOUNT, 'scope': 'SCRATCH', 'member': MEMBER, 'agent_key': MARKET, 'default': '1', 'board': HOME})])
        self.assertEqual(self.hires(), [(MARKET, 'ON', ACCOUNT, MEMBER)])
        self.assertEqual(self.first(HOME), {'placed': [], 'skipped': []})   # hired: nothing more

    def test_a_marked_card_is_placed_on_its_own_board_through_the_same_door(self):
        self.p.cards += [card('ATOM', default=True), card('PLAIN'), card('ELSEWHERE', 'agencymgmt/mdia/home', default=True)]
        self.assertEqual(self.first(), {'placed': ['ATOM'], 'skipped': []})
        self.assertEqual(self.p.asked, [('wid', 'POST', '/agnt/hire', {'account': ACCOUNT, 'scope': 'SCRATCH', 'member': MEMBER, 'agent_key': 'ATOM', 'default': '1', 'board': BOARD})])   # the placement says what it is, and for which board
        self.assertEqual(self.hires(), [('ATOM', 'ON', ACCOUNT, MEMBER)])   # the same hire record a member's own hire leaves

    def test_only_the_platforms_true_marks_a_card(self):
        self.p.cards += [card('WORD', default='ON'), card('ONE', default=1), card('NONE')]
        del self.p.cards[-1]['default']   # a platform before the field: no card is a default
        self.assertEqual(self.first(), {'placed': [], 'skipped': []})
        self.assertEqual(self.p.asked, [])

    def test_a_card_that_names_an_outside_ai_service_is_never_placed_by_default_and_it_is_said(self):
        self.p.cards += [card('OUT', default=True, sends_to='an outside AI service'), card('ATOM', default=True)]
        got = self.first()
        self.assertEqual(got['placed'], ['ATOM'])
        self.assertEqual(got['skipped'], [{'agent_key': 'OUT', 'why': 'it names an outside AI service: the member hires it themselves'}])
        self.assertNotIn('OUT', [a[3]['agent_key'] for a in self.p.asked])   # the platform was never asked

    def test_the_mismatch_this_runtimes_fact_says_no_service_and_the_platforms_card_names_one(self):
        """THE SECURITY REVIEW OF c78af5d: this runtime's own skip reads the facts it was handed; empty or stale, it does not
        fire. The ask says it is a default placement, the platform refuses it on its own card, and the runtime lists it as
        skipped: not placed, no hire record. The other default of the board is placed all the same."""
        self.p.cards += [card('STALE', default=True, sends_to=''), card('ATOM', default=True)]
        self.p.core_names_a_service = {'STALE'}
        got = self.first()
        self.assertEqual(got, {'placed': ['ATOM'], 'skipped': [{'agent_key': 'STALE', 'why': 'not placed by default: it names an outside AI service, the member hires it themselves'}]})
        self.assertEqual(self.hires(), [('ATOM', 'ON', ACCOUNT, MEMBER)])
        self.assertTrue(all(a[3].get('default') == '1' and a[3].get('board') == BOARD for a in self.p.asked))   # every default placement carries the mark

    def test_a_members_own_hire_never_carries_the_mark(self):
        self.p.cards += [card('ATOM', default=True)]
        self.p.hired = [{'agent_key': MARKET, 'on': True}]   # the marketplace is theirs: they hire through it
        self.p.hire(ACCOUNT, 'SCRATCH', MEMBER, 'ATOM', True)
        self.p.hire(ACCOUNT, 'SCRATCH', MEMBER, 'ATOM', False)
        self.assertEqual([(a[2], sorted(a[3])) for a in self.p.asked], [('/agnt/hire', ['account', 'agent_key', 'member', 'scope']), ('/agnt/unhire', ['account', 'agent_key', 'member', 'scope'])])

    def test_an_offline_card_is_skipped_until_the_account_holds_its_subscription(self):
        self.p.cards += [card('OFF', default=True, offline=True)]
        self.assertEqual(self.first(), {'placed': [], 'skipped': [{'agent_key': 'OFF', 'why': 'offline'}]})
        self.assertEqual(self.p.asked, [])
        self.p.groups = ['manage']   # the product's plan: the card is online for this account
        self.assertEqual(self.first(), {'placed': ['OFF'], 'skipped': []})

    def test_a_card_not_shown_is_not_placed(self):
        self.p.cards += [card('PENDING', default=True, status='PENDING'), card('UNHELD', default=True), card('ODD', default=True, price='three')]
        self.p.unverified = {'UNHELD'}
        self.assertEqual(self.first(), {'placed': [], 'skipped': []})
        self.assertEqual(self.p.asked, [])

    def test_a_card_the_platform_refuses_is_skipped_and_the_others_are_placed(self):
        self.p.cards += [card('NO', default=True), card('ATOM', default=True)]
        self.p.refuses = {'NO': 'refused by FROST: no_right'}
        self.assertEqual(self.first(), {'placed': ['ATOM'], 'skipped': [{'agent_key': 'NO', 'why': 'refused by FROST: no_right'}]})
        self.assertEqual(self.hires(), [('ATOM', 'ON', ACCOUNT, MEMBER)])   # no record of a hire that did not happen

    def test_an_already_hired_card_is_left_alone(self):
        self.p.cards += [card('ATOM', default=True)]
        self.p.hired = [{'agent_key': 'ATOM', 'on': True}]
        self.assertEqual(self.first(), {'placed': [], 'skipped': []})
        self.assertEqual((self.p.asked, self.hires()), ([], []))

    def test_the_marketplace_and_a_marked_card_on_one_board(self):
        self.p.cards += [card('ATOM', HOME, default=True)]
        self.assertEqual(self.first(HOME), {'placed': [MARKET, 'ATOM'], 'skipped': []})
        self.p.hired, self.p.refuses = [], {MARKET: 'refused by FROST: no_right'}
        with self.assertRaises(harness.Refused):   # the marketplace's refusal is the answer, as before
            self.first(HOME)
        self.assertEqual([a[3]['agent_key'] for a in self.p.asked][-2:], [MARKET, 'ATOM'])   # and the board's other default was placed first

    def test_the_runtime_keeps_no_once_of_its_own(self):
        """ONCE IS THE PLATFORM'S: it asks only when a board is born (wid: shells.board). Asked again for a member who let
        the agent go, the runtime would place it again, so nothing but a board's birth may ask (wid's own test holds that)."""
        self.p.cards += [card('ATOM', default=True)]
        self.assertEqual(self.first()['placed'], ['ATOM'])
        self.p.hired = []   # the member let it go
        self.assertEqual(self.first()['placed'], ['ATOM'])


if __name__ == '__main__':
    unittest.main()
