"""A FEW RUNS AT A TIME ON THIS COMPUTER (the owner 2026-11-10: "this needs to be automated"; "it starts at 6:50am and all day agents run
then the night starts at 1am"): one slot made every block wait behind a long step and the platform closed the waiting RUNs after 20
minutes. Slots hands as many tokens as it has slots, refuses the next, and a slot given back is free again; Cloud Run keeps one."""
import unittest

from _here import APP  # noqa: F401
from core_engine import slot


class AFewRuns(unittest.TestCase):
    def test_three_at_a_time_then_refused_then_free_again(self):
        s = slot.Slots(3, 60)
        tokens = [s.take() for _ in range(3)]
        self.assertTrue(all(tokens))
        self.assertEqual(len({id(t) for t in tokens}), 3)
        self.assertIsNone(s.take())   # the fourth waits
        s.give_back(tokens[1])
        again = s.take()
        self.assertTrue(again)
        self.assertIsNone(s.take())
        s.give_back(tokens[1])   # twice, or a token no longer its slot's: harmless
        self.assertIsNone(s.take())

    def test_a_token_speaks_to_its_own_slot(self):
        s = slot.Slots(2, 60)
        a, b = s.take(), s.take()
        s.attach(b, 4242)
        self.assertEqual([x.pgid for x in s.slots], [None, 4242])
        s.give_back(a)
        self.assertEqual([x.owner is None for x in s.slots], [True, False])
        self.assertFalse(s.stuck())

    def test_one_slot_is_still_one(self):
        s = slot.Slot(60)
        self.assertTrue(s.take())
        self.assertIsNone(s.take())
