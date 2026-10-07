"""The lanes' pure part: from the platform's answers (cards, the member's hired shells, the account's groups) to what
the marketplace is handed. The calls themselves are proven live against scratch platform hosts, never a stand-in."""
import unittest

from _here import APP  # noqa: F401
from core_engine import lanes

OK = (True, '')


def card(key, **over):
    base = {'key': key, 'number': '1', 'class': 'MARK I AGENT (NORMAL)', 'name': key, 'screen': 'larryd/agnt/home', 'product': 'LARRYD',
            'product_slug': 'larryd', 'module': 'AGENT', 'pitch': '', 'developer': '', 'price': '0', 'image_dam_key': '',
            'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'status': 'APPROVED'}
    base.update(over)
    return base


class AssembleTest(unittest.TestCase):
    def test_only_shown_cards_with_the_members_state(self):
        cards = [card('FREE'), card('PAID', price='10', product_slug='paceshift', product='PACE SHIFT'), card('DRAFT', status='DRAFT'),
                 card('NOCODE')]
        hired = [{'agent_key': 'FREE', 'on': True}, {'agent_key': 'PAID', 'on': False}]
        verify = {'FREE': OK, 'PAID': OK, 'DRAFT': OK, 'NOCODE': (False, 'not in the locker')}.get
        out = lanes.assemble(cards, hired, [], verify)
        self.assertEqual([(c['key'], c['hired'], c['hireable'], c['reason']) for c in out],
                         [('FREE', True, True, ''), ('PAID', False, True, 'needs the PACE SHIFT subscription')])   # every card can be hired (the owner, 2026-10-06); its run needs the subscription
        self.assertEqual([c['needs'] for c in out], ['', 'PACE SHIFT'])

    def test_an_agent_is_never_handed_its_own_card(self):
        out = lanes.assemble([card('MARKET'), card('WEEKLY')], [], [], lambda k: OK, own='MARKET')
        self.assertEqual([c['key'] for c in out], ['WEEKLY'])

    def test_a_subscription_opens_its_group(self):
        cards = [card('PAID', price='10', product_slug='paceshift', product='PACE SHIFT')]
        self.assertEqual(lanes.assemble(cards, [], ['paceshift'], lambda k: OK)[0]['hireable'], True)

    def test_hired_is_a_shell_that_is_on(self):
        self.assertEqual(lanes.hired_on([{'agent_key': 'A', 'on': False}, {'agent_key': 'A', 'on': True}], 'A'), True)
        self.assertEqual(lanes.hired_on([{'agent_key': 'A', 'on': False}], 'A'), False)
        self.assertEqual(lanes.hired_on([], 'A'), False)

    def test_groups_are_the_subscriptions_agent_groups(self):
        balance = {'subscriptions': [{'agent_group': 'paceshift'}, {'agent_group': 'invoicemaps'}]}
        self.assertEqual(lanes.groups(balance), ['invoicemaps', 'paceshift'])
        self.assertEqual(lanes.groups({}), [])


if __name__ == '__main__':
    unittest.main()


class OfflineIsForTheSubscription(unittest.TestCase):
    """The owner, 2026-10-07: "the offline is for the subscription to work ... this is offline until someone buys a subscription to invoice maps"."""
    def test_a_card_marked_offline_is_offline_only_without_its_products_subscription(self):
        maps = card('MAPS', product='INVOICE MAPS', product_slug='invoicemaps', screen='locn/home', offline=True)
        self.assertIs(lanes.assemble([maps], [], [], lambda k: OK)[0]['offline'], True)                     # no subscription: offline
        self.assertIs(lanes.assemble([maps], [], ['paceshift'], lambda k: OK)[0]['offline'], True)          # another product's: still offline
        self.assertIs(lanes.assemble([maps], [], ['invoicemaps'], lambda k: OK)[0]['offline'], False)       # its own product's: online
        for not_marked in (False, None, 'true', 1):
            self.assertIs(lanes.assemble([card('CAL', offline=not_marked)], [], [], lambda k: OK)[0]['offline'], False)   # never marked: never offline
        self.assertIs(lanes.assemble([card('CAL')], [], [], lambda k: OK)[0]['offline'], False)

    def test_with_the_subscription_the_card_says_subscription_never_without(self):
        maps = card('MAPS', product='INVOICE MAPS', product_slug='invoicemaps', screen='locn/home', offline=True)
        self.assertIs(lanes.assemble([maps], [], ['invoicemaps'], lambda k: OK)[0]['subscription'], True)
        self.assertIs(lanes.assemble([maps], [], [], lambda k: OK)[0]['subscription'], False)       # no subscription: Offline, and the word Subscription is never shown
        self.assertIs(lanes.assemble([card('CAL')], [], ['larryd'], lambda k: OK)[0]['subscription'], False)   # a free agent stays Free

    def test_all_four_products_work_the_same(self):   # the owner, 2026-10-07: "all 4 products work the same"
        products = (('INVOICE MAPS', 'invoicemaps'), ('AGENCY MGMT', 'agencymgmt'), ('PACE SHIFT', 'paceshift'), ('LARRYD', 'larryd'))
        for name, slug in products:
            marked = card('X', product=name, product_slug=slug, offline=True)
            without = lanes.assemble([marked], [], [s for _n, s in products if s != slug], lambda k: OK)[0]   # every OTHER product's subscription
            with_it = lanes.assemble([marked], [], [slug], lambda k: OK)[0]
            self.assertEqual((without['offline'], without['subscription']), (True, False), name)    # no subscription to ITS product: offline and locked
            self.assertEqual((with_it['offline'], with_it['subscription']), (False, True), name)    # its own: Subscription, the toggle works
            free = lanes.assemble([card('F', product=name, product_slug=slug)], [], [], lambda k: OK)[0]
            self.assertEqual((free['offline'], free['subscription'], free['needs']), (False, False, ''), name)   # a free agent: free with no subscription
