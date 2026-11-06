"""THE JOIN REQUESTS AND THE PAYMENTS (CORE_CLEANUP_IV row 142, pf Alerts): "records": {"*": ["joins"]} / ["payments"] hand, on a CALL,
read only, what wid's /agnt/records/joins and /agnt/records/payments hand for this member, each checked to be exactly its shape;
any other shape, a refusal or the door away hands nothing and says so in fixed words. The words mix with the counts and the roster
under "*", each once (the doctor's own words are held to these by tests/test_makes_match_runtime.py, the runtime never importing the
tool). No network: each door is a stand-in."""
import unittest

import _here  # noqa: F401
from core_engine import harness, member_records

WHO = ('ACCT_A', 'SCRATCH', 'MCON_M', 'MAGT_K')
JOINS = {'requests': [{'name': 'Scratch Person', 'asked_at': '2026-11-06T17:00:00Z'}]}
PAYS = {'payments': [{'kind': 'subscription', 'amount_cents': 4900, 'landed_at': '2026-11-06T17:05:00Z'}]}


class TheWords(unittest.TestCase):
    def test_each_word_once_in_any_mix(self):
        for words in (['joins'], ['payments'], ['joins', 'payments'], ['count', 'joins'], ['roster', 'payments', 'count', 'joins']):
            m = {'records': {'*': words}}
            self.assertEqual((member_records.joins_declared(m), member_records.payments_declared(m)), ('joins' in words, 'payments' in words), words)
            self.assertEqual(member_records.counts_declared(m), 'count' in words, words)
            self.assertEqual(member_records.roster_declared(m), 'roster' in words, words)
        for bad in (['joins', 'joins'], ['payment'], ['JOINS'], 'joins', [], ['payments', 'read']):
            m = {'records': {'*': bad}}
            self.assertFalse(member_records.joins_declared(m) or member_records.payments_declared(m) or member_records.counts_declared(m), bad)

class TheShapes(unittest.TestCase):
    def test_joins_are_exactly_name_and_asked_at(self):
        self.assertEqual(member_records.joined(JOINS), JOINS['requests'])
        one = JOINS['requests'][0]
        for bad in ({'requests': [{**one, 'email': 'a@b.c'}]}, {'requests': [{'name': 'x'}]}, {'requests': [{**one, 'name': 'x' * 201}]},
                    {'requests': [{**one, 'name': 'two\nlines'}]}, {'requests': 'all'}, {'rows': []}, {'requests': [one] * (member_records.MOST_HANDED + 1)}, None):
            with self.assertRaises(ValueError, msg=bad):
                member_records.joined(bad)

    def test_payments_are_exactly_kind_whole_cents_and_landed_at(self):
        self.assertEqual(member_records.paid(PAYS), PAYS['payments'])
        one = PAYS['payments'][0]
        for bad in ({'payments': [{**one, 'amount_cents': 49.0}]}, {'payments': [{**one, 'amount_cents': True}]}, {'payments': [{**one, 'amount_cents': '4900'}]},
                    {'payments': [{**one, 'card': '4242'}]}, {'payments': [{**one, 'amount_cents': 10 ** 12}]}, {'payments': 'all'}, None):
            with self.assertRaises(ValueError, msg=bad):
                member_records.paid(bad)

    def test_each_door_is_asked_for_the_member_the_platform_named(self):
        asked = []
        member_records.joins(lambda *a: asked.append(a) or JOINS, *WHO)
        member_records.payments(lambda *a: asked.append(a) or PAYS, *WHO)
        data = {'account': 'ACCT_A', 'scope': 'SCRATCH', 'member': 'MCON_M', 'agent_key': 'MAGT_K'}
        self.assertEqual(asked, [('wid', 'GET', '/agnt/records/joins', data), ('wid', 'GET', '/agnt/records/payments', data)])


class TheHarness(unittest.TestCase):
    def harness(self, answers):
        h = harness.Harness.__new__(harness.Harness)
        asked = []
        h._ask = lambda office, method, route, data: asked.append(route) or answers[route]
        return h, asked

    def test_handed_on_a_call_when_declared(self):
        h, asked = self.harness({'/agnt/records/joins': JOINS, '/agnt/records/payments': PAYS})
        given = {}
        m = {'records': {'*': ['joins', 'payments']}}
        self.assertEqual((h._joins(m, given, *WHO), h._payments(m, given, *WHO)), ('', ''))
        self.assertEqual(given, {'joins': JOINS['requests'], 'payments': PAYS['payments']})

    def test_not_declared_asks_nothing_and_a_wrong_shape_or_refusal_hands_nothing(self):
        h, asked = self.harness({'/agnt/records/joins': {'requests': 'all'}, '/agnt/records/payments': PAYS})
        given = {}
        self.assertEqual((h._joins({'records': {'*': ['roster']}}, given, *WHO), h._payments({'records': {'*': ['roster']}}, given, *WHO), asked), ('', '', []))
        self.assertEqual((h._joins({'records': {'*': ['joins']}}, given, *WHO), given), ('joins not read', {}))

        def refuse(*a):
            raise harness.Refused(403, 'refused: not declared, approved, hired and switched on')
        h._ask = refuse
        self.assertEqual((h._payments({'records': {'*': ['payments']}}, given, *WHO), given), ('payments not read', {}))


if __name__ == '__main__':
    unittest.main()
