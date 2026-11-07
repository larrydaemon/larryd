"""THE REVIEWS WAITING (CORE_CLEANUP_IV 23, pf Review Lane): "records": {"*": ["reviews"]} hands the agents waiting for FROST's
review on a CALL, read through wid's reviews door for this member, ONLY when this runtime is LARRYD RUNTIME INTERNAL
(Harness.INTERNAL, from LARRYD_INTERNAL=1 at its start): elsewhere it never asks and hands nothing (fail closed); wid refuses any card that is not internal
and SYSTEM's own (the second guard). Any other shape hands nothing. No network: the door is a stand-in."""
import os
import unittest

import _here  # noqa: F401
from core_engine import harness, member_records

WAITING = {'waiting': [{'agent_key': 'MAGT_000000000001_0001', 'code_sha256': 'a' * 64, 'manifest_sha256': 'b' * 64, 'manifest': {'name': 'pf Scratch'}}]}
WHO = ('ACCT_A', 'SCRATCH', 'MCON_M', 'MAGT_K')
DECLARED = {'records': {'*': ['reviews']}}


class TheReviewsWaiting(unittest.TestCase):
    def test_star_takes_reviews_each_once_beside_the_others(self):
        for words in (['reviews'], ['count', 'reviews'], ['roster', 'reviews', 'count']):
            self.assertTrue(member_records.reviews_declared({'records': {'*': words}}), words)
        for bad in (['reviews', 'reviews'], ['review'], ['REVIEWS'], 'reviews', [], ['reviews', 'read']):
            self.assertFalse(member_records.reviews_declared({'records': {'*': bad}}), bad)
        self.assertEqual(member_records.declared({'records': {'*': ['reviews'], 'opns': ['read']}}), {'opns': ('read',)})   # no right on any species

    def test_the_answer_is_waiting_entries_or_nothing(self):
        self.assertEqual(member_records.reviewed(WAITING), WAITING['waiting'])
        self.assertEqual(member_records.reviewed({'waiting': []}), [])
        for bad in ({'waiting': WAITING['waiting'], 'more': 1}, {'rows': []}, {'waiting': 'all'}, {'waiting': ['MAGT_K']},
                    {'waiting': [{}] * (member_records.MOST_WAITING + 1)}, [], None):
            with self.assertRaises(ValueError, msg=bad):
                member_records.reviewed(bad)

    def test_the_door_is_asked_for_the_member_the_platform_named(self):
        asked = []
        self.assertEqual(member_records.reviews(lambda *a: asked.append(a) or WAITING, *WHO), WAITING['waiting'])
        self.assertEqual(asked, [('wid', 'GET', '/agnt/reviews/waiting', {'account': 'ACCT_A', 'scope': 'SCRATCH', 'member': 'MCON_M', 'agent_key': 'MAGT_K'})])

    def harness_asking(self, answer):
        h = harness.Harness.__new__(harness.Harness)
        h.INTERNAL = True
        asked = []
        h._ask = lambda *a: asked.append(a) or answer
        return h, asked

    def test_the_internal_runtime_hands_them(self):
        h, asked = self.harness_asking(WAITING)
        given = {}
        self.assertEqual((h._reviews(DECLARED, given, *WHO), given), ('', {'reviews': WAITING['waiting']}))
        self.assertEqual(len(asked), 1)

    def test_an_external_runtime_never_asks_and_hands_nothing(self):
        h, asked = self.harness_asking(WAITING)
        given = {}
        h.INTERNAL = False
        self.assertEqual((h._reviews(DECLARED, given, *WHO), given, asked), ('', {}, []))   # the external runtime: nothing asked, nothing handed, nothing said, as it always was
        self.assertIs(harness.Harness.INTERNAL, os.environ.get('LARRYD_INTERNAL') == '1')   # the flag is the start's word, never a card's

    def test_not_declared_asks_nothing_and_a_wrong_shape_or_refusal_hands_nothing(self):
        h, asked = self.harness_asking(WAITING)
        given = {}
        self.assertEqual((h._reviews({'records': {'*': ['roster']}}, given, *WHO), given, asked), ('', {}, []))
        h._ask = lambda *a: {'waiting': 'everything'}
        self.assertEqual((h._reviews(DECLARED, given, *WHO), given), ('reviews not read', {}))

        def refuse(*a):
            raise harness.Refused(403, 'refused by FROST: only an internal agent reads the reviews waiting')
        h._ask = refuse
        self.assertEqual((h._reviews(DECLARED, given, *WHO), given), ('reviews not read', {}))


if __name__ == '__main__':
    unittest.main()
