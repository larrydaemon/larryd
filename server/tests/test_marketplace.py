"""THE AGENT MARKETPLACE, run as it really runs: in the sandbox, from its locker folder."""
import unittest

from _here import APP
from core_engine import sandbox

FOLDER = APP / 'agents' / 'marketplace'


def card(**over):
    base = {'key': 'MAGT_AAAAAAAAAAAA_0001', 'number': '1', 'class': 'MARK I AGENT (NORMAL)', 'name': 'The Agent Marketplace',
            'screen': 'larryd/agnt/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'AGENT', 'pitch': 'Every agent, one toggle.',
            'developer': 'Positive Feedback', 'price': '0', 'image_dam_key': '', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL',
            'status': 'LIVE', 'hired': False, 'hireable': True, 'reason': ''}
    base.update(over)
    return base


def run(given):
    state, answer, reason = sandbox.run(FOLDER, 'agent.py', given)
    assert state == 'DONE', reason
    return answer


class CollectionTest(unittest.TestCase):
    def test_one_card_as_the_original_lays_it_out(self):
        out = run({'do': 'collection', 'cards': [card()]})
        self.assertEqual(out['total'], 1)
        self.assertEqual(out['hired'], 0)
        self.assertEqual(out['cards'], [{
            'key': 'MAGT_AAAAAAAAAAAA_0001', 'no': 'NO. 001', 'class': 'MARK I AGENT (NORMAL)', 'name': 'The Agent Marketplace',
            'initials': 'TA', 'image_dam_key': '', 'place': 'LARRYD · AGENT', 'pitch': 'Every agent, one toggle.',
            'developer': 'Positive Feedback', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'price': 'FREE',
            'hired': False, 'hireable': True, 'reason': ''}])

    def test_counts_and_order_come_from_the_cards(self):
        cards = [card(key='K3', number='3', hired=True), card(key='K1', number='1'), card(key='K2', number='', name='PF Night Watch')]
        out = run({'do': 'collection', 'cards': cards})
        self.assertEqual([c['key'] for c in out['cards']], ['K1', 'K3', 'K2'])   # by number; unnumbered last
        self.assertEqual((out['total'], out['hired']), (3, 1))
        self.assertEqual(out['cards'][2]['no'], '')
        self.assertEqual(out['cards'][2]['initials'], 'NW')

    def test_a_rate_is_shown_as_mtok(self):
        self.assertEqual(run({'do': 'collection', 'cards': [card(price='12')]})['cards'][0]['price'], '12 mTok')

    def test_filters_are_the_cards_own_values(self):
        cards = [card(key='A', product='INVOICE MAPS', module='CONTACTS', type='DEVELOPER', residency='EXTERNAL'), card(key='B')]
        f = run({'do': 'collection', 'cards': cards})['filters']
        self.assertEqual(f, {'product': ['INVOICE MAPS', 'LARRYD'], 'module': ['AGENT', 'CONTACTS'], 'type': ['DEVELOPER', 'OFF-THE-SHELF'],
                             'residency': ['EXTERNAL', 'INTERNAL'], 'class': ['MARK I AGENT (NORMAL)']})

    def test_an_empty_collection_is_empty(self):
        self.assertEqual(run({'do': 'collection', 'cards': []}), {'cards': [], 'total': 0, 'hired': 0,
                         'filters': {'product': [], 'module': [], 'type': [], 'residency': [], 'class': []}})


class ReportTest(unittest.TestCase):
    def test_the_run_delivers_the_collection_report(self):
        out = run({'do': 'report', 'cards': [card(hired=True), card(key='K2')]})
        self.assertEqual(out, {'delivery': '2 agents in the collection · 1 hired', 'total': 2, 'hired': 1})
        self.assertEqual(run({'do': 'report', 'cards': [card()]})['delivery'], '1 agent in the collection · 0 hired')


class RefusesTest(unittest.TestCase):
    def test_an_unknown_ask_fails(self):
        state, _answer, reason = sandbox.run(FOLDER, 'agent.py', {'do': 'anything'})
        self.assertEqual(state, 'FAILED')
        self.assertIn('the marketplace does: collection, report', reason)


if __name__ == '__main__':
    unittest.main()
