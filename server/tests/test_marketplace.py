"""THE AGENT MARKETPLACE, run as it really runs: in the sandbox, from its locker folder."""
import json
import re
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
            'key': 'MAGT_AAAAAAAAAAAA_0001', 'number': 1, 'class': 'MARK I AGENT (NORMAL)', 'name': 'The Agent Marketplace',
            'initials': 'TA', 'image_dam_key': '', 'product': 'LARRYD', 'module': 'AGENT', 'pitch': 'Every agent, one toggle.',
            'developer': 'Positive Feedback', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL',
            'screen': 'larryd/agnt/home', 'sends_to': '', 'data_sent': '', 'rate': 0,
            'hired': False, 'hireable': True, 'needs': ''}])

    def test_counts_and_order_come_from_the_cards(self):
        cards = [card(key='K3', number='3', hired=True), card(key='K1', number='1'), card(key='K2', number='', name='PF Night Watch')]
        out = run({'do': 'collection', 'cards': cards})
        self.assertEqual([c['key'] for c in out['cards']], ['K1', 'K3', 'K2'])   # by number; unnumbered last
        self.assertEqual((out['total'], out['hired']), (3, 1))
        self.assertEqual(out['cards'][2]['number'], None)
        self.assertEqual(out['cards'][2]['initials'], 'NW')

    def test_values_never_words(self):
        paid = run({'do': 'collection', 'cards': [card(price='12', hireable=False, needs='PACE SHIFT')]})['cards'][0]
        self.assertEqual((paid['rate'], paid['hireable'], paid['needs']), (12, False, 'PACE SHIFT'))

    def test_filters_are_the_cards_own_values(self):
        cards = [card(key='A', product='INVOICE MAPS', module='CONTACTS', type='DEVELOPER', residency='EXTERNAL'), card(key='B')]
        f = run({'do': 'collection', 'cards': cards})['filters']
        self.assertEqual(f, {'product': ['INVOICE MAPS', 'LARRYD'], 'module': ['AGENT', 'CONTACTS'], 'type': ['DEVELOPER', 'OFF-THE-SHELF'],
                             'residency': ['EXTERNAL', 'INTERNAL'], 'class': ['MARK I AGENT (NORMAL)']})

    def test_an_empty_collection_is_empty(self):
        out = run({'do': 'collection', 'cards': []})
        self.assertTrue(out.pop('style'))   # the card's own sheet comes with every collection
        self.assertEqual(out, {'cards': [], 'total': 0, 'hired': 0,
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
        self.assertEqual(reason, 'exit 1')   # an agent's own words never reach a reason (data stays in wid)


if __name__ == '__main__':
    unittest.main()


class Gives(unittest.TestCase):
    """The marketplace answers only what its manifest's "gives" names (the runtime refuses anything else)."""
    def test_both_answers_stay_inside_gives(self):
        gives = set(json.loads((FOLDER / 'agent.json').read_text())['gives'])
        cards = [{'key': 'MAGT_1', 'name': 'A', 'hired': True, 'product': 'LARRYD', 'module': 'Agents'}]
        for do in ('collection', 'report'):
            state, answer, reason = sandbox.run(FOLDER, 'agent.py', {'do': do, 'cards': cards})
            self.assertEqual(state, 'DONE', reason)
            self.assertLessEqual(set(answer), gives, do)


class TheCardsOwnLook(unittest.TestCase):
    """The owner, 2026-10-06: "all agents' CSS definitions are IN THE AGENT": the card's frame and class look (Mark I CRT,
    Mark II Wellness, Mark III Glitch) are the agent's own sheet, sent with every collection, already in the doctor's
    form (larryd/sheet.py), drawn by the platform in each card's own shadow root."""
    def test_the_collection_carries_the_agents_own_sheet_with_the_three_marks(self):
        sheet = run({'do': 'collection', 'cards': [card()]})['style']
        for mark in ('.mk-mark-1 ', '.mk-mark-2 ', '.mk-mark-3 '):
            self.assertIn(mark, sheet)

    def test_the_sheet_reaches_nowhere(self):
        sheet = run({'do': 'collection', 'cards': []})['style'].lower()
        for reach in ('url(', '@import', 'expression(', 'javascript:', '<', '\\', 'position: fixed', 'body', 'html', ':root'):
            self.assertNotIn(reach, sheet)
