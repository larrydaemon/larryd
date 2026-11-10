"""THE TWO GUARDS' REPORTS (Agents Security Plan, the Agent Ecosystem agent): "records": {"*": ["guards"]} hands, on a CALL, the two
guards' reports wid's /agnt/guards hands for this member ({frost: FROST active monitoring's, hades: HADES's}, each {rules, agents,
counts, at}), ONLY when this runtime is LARRYD RUNTIME INTERNAL (Harness.INTERNAL, from LARRYD_INTERNAL=1 at its start): elsewhere it
never asks and hands nothing (fail closed); wid refuses any account but SYSTEM's own (the second guard). Any other shape hands
nothing. No network: the door is a stand-in."""
import os
import unittest

import _here  # noqa: F401
from core_engine import harness, member_records

REPORT = {'rules': [{'id': 'A1', 'verdict': 'Pass', 'findings': []}], 'agents': [{'agent_key': 'MAGT_000000000001_0001', 'code_sha256': 'a' * 64, 'verdict': 'Pass'}],
          'counts': {'Pass': 1, 'Findings': 0, 'findings': 0, 'agents': 1, 'agents_findings': 0}, 'at': '21:30'}
GUARDS = {'frost': REPORT, 'hades': {**REPORT, 'rules': []}}
WHO = ('ACCT_A', 'SCRATCH', 'MCON_M', 'MAGT_K')
DECLARED = {'records': {'*': ['guards']}}


class TheTwoGuards(unittest.TestCase):
    def test_star_takes_guards_each_once_beside_the_others(self):
        for words in (['guards'], ['history', 'guards'], ['count', 'roster', 'reviews', 'history', 'guards']):
            self.assertTrue(member_records.guards_declared({'records': {'*': words}}), words)
        for bad in (['guards', 'guards'], ['guard'], 'guards', [], ['guards', 'read']):
            self.assertFalse(member_records.guards_declared({'records': {'*': bad}}), bad)
        self.assertNotIn('guards', member_records.EVERY_WORDS)   # never a word of the external runtime
        self.assertIn('guards', member_records.INTERNAL_WORDS)

    def test_the_answer_is_exactly_both_reports(self):
        self.assertEqual(member_records.guarded(GUARDS), GUARDS)
        for bad in ({'frost': REPORT}, {**GUARDS, 'more': REPORT}, {**GUARDS, 'hades': {**REPORT, 'pin': 'x'}},
                    {**GUARDS, 'frost': {k: v for k, v in REPORT.items() if k != 'at'}}, {**GUARDS, 'frost': {**REPORT, 'rules': 'all'}},
                    {**GUARDS, 'frost': {**REPORT, 'agents': ['x']}}, {**GUARDS, 'frost': {**REPORT, 'counts': {'Pass': True}}},
                    {**GUARDS, 'frost': {**REPORT, 'at': 'x' * 41}}, {**GUARDS, 'frost': {**REPORT, 'agents': [{}] * (member_records.MOST_GUARD_ROWS + 1)}}, None):
            with self.assertRaises(ValueError, msg=bad):
                member_records.guarded(bad)

    def test_the_door_is_asked_for_the_member_the_platform_named(self):
        asked = []
        member_records.guards(lambda *a: asked.append(a) or GUARDS, *WHO)
        self.assertEqual(asked, [('wid', 'GET', '/agnt/guards', {'account': 'ACCT_A', 'scope': 'SCRATCH', 'member': 'MCON_M', 'agent_key': 'MAGT_K'})])

    def harness(self, answer, internal=True):
        h = harness.Harness.__new__(harness.Harness)
        h.INTERNAL = internal
        asked = []
        h._ask = lambda *a: asked.append(a) or answer
        return h, asked

    def test_the_internal_runtime_hands_it(self):
        h, asked = self.harness(GUARDS)
        given = {}
        self.assertEqual((h._guards(DECLARED, given, *WHO), given, len(asked)), ('', {'guards': GUARDS}, 1))

    def test_elsewhere_it_never_asks_and_hands_nothing(self):
        h, asked = self.harness(GUARDS, internal=False)
        given = {}
        self.assertEqual((h._guards(DECLARED, given, *WHO), given, asked), ('', {}, []))   # the external runtime: nothing asked, nothing handed, nothing said
        self.assertIs(harness.Harness.INTERNAL, os.environ.get('LARRYD_INTERNAL') == '1')   # the flag is the start's word, never a card's

    def test_not_declared_asks_nothing_and_a_wrong_shape_or_refusal_hands_nothing(self):
        h, asked = self.harness({'frost': 'everything'})
        given = {}
        self.assertEqual((h._guards({'records': {'*': ['history']}}, given, *WHO), given, asked), ('', {}, []))
        self.assertEqual((h._guards(DECLARED, given, *WHO), given), ('guards not read', {}))

        def refuse(*a):
            raise harness.Refused(403, 'only SYSTEM asks for the inventory')
        h._ask = refuse
        self.assertEqual((h._guards(DECLARED, given, *WHO), given), ('guards not read', {}))


if __name__ == '__main__':
    unittest.main()
