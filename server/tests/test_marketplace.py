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
            'status': 'APPROVED', 'hired': False, 'hireable': True, 'reason': ''}
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
            'hired': False, 'hireable': True, 'needs': '', 'art': ''}])

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
        self.assertEqual(out.pop('view')['css'], (FOLDER / 'card.css').read_text())
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


class TheAgentsOwnView(unittest.TestCase):
    """The card lives in the agent (the owner, 2026-10-07): the collection carries its own view, the whole panel's markup
    (one card per card handed, every value escaped, a hire button per card, no form) and its own sheet (card.css)."""
    def test_one_card_per_card_handed_and_its_own_sheet(self):
        cards = [card(key='K1', name='Weekly <Summary>', hired=True, price='3'), card(key='K2', number='2', name='Action Items')]
        v = run({'do': 'collection', 'cards': cards})['view']
        self.assertEqual(set(v), {'html', 'css'})
        self.assertEqual(v['css'], (FOLDER / 'card.css').read_text())
        self.assertEqual(v['html'].count('<article class="agent-card'), 2)
        self.assertIn('Weekly &lt;Summary&gt;', v['html'])
        self.assertNotIn('<Summary>', v['html'])
        self.assertIn('data-hire="K1" aria-pressed="true"', v['html'])
        self.assertIn('data-hire="K2" aria-pressed="false"', v['html'])
        self.assertIn('3 mTok', v['html'])
        self.assertNotIn('<form', v['html'])
        self.assertIn('2 total in network · 1 hired', v['html'])

    def test_the_marketplace_never_draws_itself(self):   # the runtime never hands it its own card; what it is handed is all it draws
        v = run({'do': 'collection', 'cards': [card(key='OTHER')]})['view']
        self.assertEqual(re.findall(r'data-agent="([^"]+)"', v['html']), ['OTHER'])

    def test_the_view_passes_the_runtimes_check(self):
        from core_engine import view
        self.assertEqual(view.refused(run({'do': 'collection', 'cards': [card(), card(key='K2')]})['view']), '')

    def test_the_sheet_is_in_the_agents_code_hash(self):   # FROST approves the sheet with the agent: a changed sheet is a changed agent
        import shutil, tempfile, pathlib
        from core_engine import locker
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp) / 'marketplace'
            shutil.copytree(FOLDER, copy, ignore=shutil.ignore_patterns('__pycache__'))
            before = locker._code_sha256(copy)
            (copy / 'card.css').write_text((copy / 'card.css').read_text() + '\n.x { }\n')
            self.assertNotEqual(before, locker._code_sha256(copy))
