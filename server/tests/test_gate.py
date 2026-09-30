import unittest

from _here import APP  # noqa: F401
from core_engine import gate


def card(**over):
    base = {'key': 'MAGT_AAAAAAAAAAAA_0001', 'number': '1', 'class': 'MARK I AGENT (NORMAL)', 'name': 'THE AGENT MARKETPLACE',
            'screen': 'larryd/agnt/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'AGENT', 'pitch': 'p',
            'developer': 'd', 'price': '0', 'image_dam_key': '', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'status': 'LIVE'}
    base.update(over)
    return base


class RateTest(unittest.TestCase):
    def test_whole_mtok_only(self):
        self.assertEqual(gate.rate(card(price='0')), 0)
        self.assertEqual(gate.rate(card(price='')), 0)
        self.assertEqual(gate.rate(card(price='12')), 12)
        for bad in ('$1/run', '1.5', '-3', 'ten', ' 7x'):
            self.assertIsNone(gate.rate(card(price=bad)), bad)


class ShownTest(unittest.TestCase):
    def test_a_live_verified_card_with_a_screen_and_a_rate_is_shown(self):
        self.assertEqual(gate.shown(card(), (True, '')), (True, ''))

    def test_what_is_not_shown(self):
        self.assertEqual(gate.shown(card(status='DRAFT'), (True, '')), (False, 'the card is not LIVE'))
        self.assertEqual(gate.shown(card(screen=''), (True, '')), (False, 'the card names no screen'))
        self.assertEqual(gate.shown(card(price='$1/run'), (True, '')), (False, 'the price is not a whole mTok rate'))
        self.assertEqual(gate.shown(card(), (False, 'not in the locker')), (False, 'not in the locker'))
        self.assertEqual(gate.shown(card(), (False, 'tampered: the code changed')), (False, 'tampered: the code changed'))


class EntitledTest(unittest.TestCase):
    def test_free_is_for_everyone(self):
        self.assertEqual(gate.entitled(card(price='0'), []), (True, ''))

    def test_paid_needs_its_group(self):
        paid = card(price='10', product_slug='invoicemaps', product='INVOICE MAPS')
        self.assertEqual(gate.entitled(paid, ['invoicemaps']), (True, ''))
        self.assertEqual(gate.entitled(paid, ['paceshift']), (False, 'needs the INVOICE MAPS subscription'))


class MayRunTest(unittest.TestCase):
    def test_every_condition(self):
        ok = (True, '')
        self.assertEqual(gate.may_run(card(), ok, hired_on=True, groups=[]), (True, ''))
        self.assertEqual(gate.may_run(card(), ok, hired_on=False, groups=[]), (False, 'not hired, or switched off'))
        self.assertEqual(gate.may_run(card(status='SUSPENDED'), ok, hired_on=True, groups=[]), (False, 'the card is not LIVE'))
        self.assertEqual(gate.may_run(card(), (False, 'tampered: the code changed'), hired_on=True, groups=[]), (False, 'tampered: the code changed'))
        self.assertEqual(gate.may_run(card(price='5', product_slug='paceshift', product='PACE SHIFT'), ok, hired_on=True, groups=[]),
                         (False, 'needs the PACE SHIFT subscription'))


if __name__ == '__main__':
    unittest.main()
