"""The lanes' pure part: from the platform's answers (cards, the member's hired shells, the account's groups) to what
the marketplace is handed. The calls themselves are proven live against scratch platform hosts, never a stand-in."""
import unittest

from _here import APP  # noqa: F401
from core_engine import lanes

OK = (True, '')


def card(key, **over):
    base = {'key': key, 'number': '1', 'class': 'MARK I AGENT (NORMAL)', 'name': key, 'screen': 'larryd/agnt/home', 'product': 'LARRYD',
            'product_slug': 'larryd', 'module': 'AGENT', 'pitch': '', 'developer': '', 'price': '0', 'image_dam_key': '',
            'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'status': 'LIVE'}
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
                         [('FREE', True, True, ''), ('PAID', False, False, 'needs the PACE SHIFT subscription')])

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
