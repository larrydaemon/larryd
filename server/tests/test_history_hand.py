"""THE REVIEW HISTORY (CORE_CLEANUP_IV row 78): "records": {"*": ["history"]} hands, on a CALL, the review history wid's
/agnt/reviews/history hands for this member, each entry exactly its ten fields, ONLY when this runtime is LARRYD RUNTIME INTERNAL
(Harness.INTERNAL, from LARRYD_INTERNAL=1 at its start): elsewhere it never asks and hands nothing (fail closed); wid refuses any
card that is not internal and SYSTEM's own (the second guard). Any other shape hands nothing. No network: the door is a stand-in."""
import os
import unittest

import _here  # noqa: F401
from core_engine import harness, member_records

ONE = {'id': 7, 'agent_key': 'MAGT_000000000001_0001', 'card_key': 'MAGT_000000000002_0002', 'name': 'pf Scratch', 'code_sha256': 'a' * 64,
       'manifest_sha256': 'b' * 64, 'state': 'approved', 'submitted_at': '2026-11-06T16:00:00Z', 'decided_at': '2026-11-06T16:30:00Z', 'note': 'scratch'}
HISTORY = {'history': [ONE, {**ONE, 'id': 8, 'state': 'revoked'}]}
WHO = ('ACCT_A', 'SCRATCH', 'MCON_M', 'MAGT_K')
DECLARED = {'records': {'*': ['history']}}


class TheReviewHistory(unittest.TestCase):
    def test_star_takes_history_each_once_beside_the_others(self):
        for words in (['history'], ['reviews', 'history'], ['count', 'roster', 'reviews', 'history']):
            self.assertTrue(member_records.history_declared({'records': {'*': words}}), words)
        for bad in (['history', 'history'], ['histories'], 'history', [], ['history', 'read']):
            self.assertFalse(member_records.history_declared({'records': {'*': bad}}), bad)

    def test_each_entry_is_exactly_its_ten_fields(self):
        self.assertEqual(member_records.historied(HISTORY), HISTORY['history'])
        for bad in ({**ONE, 'state': 'waiting'}, {**ONE, 'pin': 'x'}, {k: v for k, v in ONE.items() if k != 'note'}, {**ONE, 'id': True},
                    {**ONE, 'name': 7}, {**ONE, 'note': 'x' * 4001}):
            with self.assertRaises(ValueError, msg=bad):
                member_records.historied({'history': [bad]})
        for bad in ({'history': HISTORY['history'], 'more': 1}, {'history': 'all'}, {'history': [ONE] * (member_records.MOST_HISTORY + 1)}, None):
            with self.assertRaises(ValueError, msg=bad):
                member_records.historied(bad)

    def test_the_door_is_asked_for_the_member_the_platform_named(self):
        asked = []
        member_records.history(lambda *a: asked.append(a) or HISTORY, *WHO)
        self.assertEqual(asked, [('wid', 'GET', '/agnt/reviews/history', {'account': 'ACCT_A', 'scope': 'SCRATCH', 'member': 'MCON_M', 'agent_key': 'MAGT_K'})])

    def harness(self, answer, internal=True):
        h = harness.Harness.__new__(harness.Harness)
        h.INTERNAL = internal
        asked = []
        h._ask = lambda *a: asked.append(a) or answer
        return h, asked

    def test_the_internal_runtime_hands_it(self):
        h, asked = self.harness(HISTORY)
        given = {}
        self.assertEqual((h._history(DECLARED, given, *WHO), given, len(asked)), ('', {'history': HISTORY['history']}, 1))

    def test_elsewhere_it_never_asks_and_hands_nothing(self):
        h, asked = self.harness(HISTORY, internal=False)
        given = {}
        self.assertEqual((h._history(DECLARED, given, *WHO), given, asked), ('', {}, []))   # the external runtime: nothing asked, nothing handed, nothing said, as it always was
        self.assertIs(harness.Harness.INTERNAL, os.environ.get('LARRYD_INTERNAL') == '1')   # the flag is the start's word, never a card's

    def test_not_declared_asks_nothing_and_a_wrong_shape_or_refusal_hands_nothing(self):
        h, asked = self.harness({'history': 'everything'})
        given = {}
        self.assertEqual((h._history({'records': {'*': ['reviews']}}, given, *WHO), given, asked), ('', {}, []))
        self.assertEqual((h._history(DECLARED, given, *WHO), given), ('history not read', {}))

        def refuse(*a):
            raise harness.Refused(403, 'refused by FROST: only an internal agent reads the review history')
        h._ask = refuse
        self.assertEqual((h._history(DECLARED, given, *WHO), given), ('history not read', {}))


if __name__ == '__main__':
    unittest.main()
