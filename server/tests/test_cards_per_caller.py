"""ONE RUNTIME, EVERY PLATFORM ITS OWN CARD (2026-11-11). The one runtime serves several platforms (production B, this Mac), and
each mints its own card key for the same agent. The locker kept ONE card key per agent, so the 2026-11-09 ship, which wrote
production B's card keys beside 133 lockers, took this Mac's away: every page of this Mac that held one of those agents got
404 "no agent that answers here" and drew an empty block. A card is linked per caller now: each platform finds the agent by
its own card, never by another platform's; a locker linked before (no caller named) answers as it did. EACH CALLER ITS OWN
LOCKER since 2026-11-22 (the owner: "there should be zero agents that are on a and b at the same fucking time"): each platform's
card is linked to its own copy of the agent, slot A's the locker of before, slot-b's and proof's copied beside it."""
import json
import pathlib
import shutil
import tempfile
import unittest

from _here import APP
from test_review_fixes import FakeBucket, MARKET, marketplace_package
from core_engine import harness, locker, lockers as bucket_lockers, store

KEY = 'MAGT_AAAAAAAAAAAA_0001'
CARD_B, CARD_MAC, CARD_OLD = 'MAGT_BBBBBBBBBBBB_5600', 'MAGT_BBBBBBBBBBBB_0643', 'MAGT_BBBBBBBBBBBB_0001'
CONF = json.loads((APP / 'schemas' / 'runtime.json').read_text())['intake']


class CardsPerCaller(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.root / 'm', ignore=shutil.ignore_patterns('__pycache__'))
        self.db = store.open_store(self.tmp.name)
        locker.add(self.db, self.root, KEY, 'm')
        for caller in ('slot-b', 'proof'):   # each platform its own copy (the migration's copy, 2026-11-22)
            self.assertEqual(locker.copy(self.db, self.root, caller)['copied'], [KEY])

    def tearDown(self):
        self.tmp.cleanup()

    def test_each_platform_finds_the_agent_by_its_own_card(self):
        self.assertTrue(locker.link(self.db, KEY, CARD_B, 'slot-b'))
        self.assertTrue(locker.link(self.db, KEY, CARD_MAC, 'proof'))   # the second platform's card never takes the first's place
        for caller, card in (('slot-b', CARD_B), ('proof', CARD_MAC)):
            row = locker.held(self.db, card, caller)
            self.assertEqual((row['agent_key'], row['card_key']), (KEY, card))
            self.assertEqual(locker.held(self.db, KEY, caller)['card_key'], card)   # by the runtime's own key: the caller's own card
            self.assertEqual(locker.verify(self.db, locker.root_for(self.root, caller), card, caller), (True, ''))
    def test_a_card_is_found_only_by_its_own_platform(self):
        locker.link(self.db, KEY, CARD_B, 'slot-b')
        self.assertIsNone(locker.held(self.db, CARD_B, 'proof'))
        self.assertIsNone(locker.held(self.db, CARD_B))   # no caller named: another platform's card finds nothing
        self.assertIsNone(locker.held(self.db, '', 'slot-b'))
        self.assertEqual(locker.verify(self.db, locker.root_for(self.root, 'proof'), CARD_B, 'proof'), (False, 'not in the locker'))

    def test_a_locker_linked_before_answers_as_it_did(self):
        self.assertTrue(locker.link(self.db, KEY, CARD_OLD))   # no caller named: the one card of before, in the locker of before
        self.assertEqual(locker.held(self.db, CARD_OLD)['agent_key'], KEY)
        self.assertEqual(locker.held(self.db, CARD_OLD, 'slot-a')['card_key'], CARD_OLD)   # slot A's locker is the locker of before
        self.assertIsNone(locker.held(self.db, CARD_OLD, 'slot-b'))   # never another platform's copy
        self.assertTrue(locker.link(self.db, KEY, CARD_OLD, into='slot-b'))   # slot-b's copy keeps one of its own
        self.assertEqual(locker.held(self.db, CARD_OLD, 'slot-b')['card_key'], CARD_OLD)   # a platform with no card of its own yet
        locker.link(self.db, KEY, CARD_MAC, 'proof')
        self.assertEqual(locker.held(self.db, KEY, 'proof')['card_key'], CARD_MAC)   # its own card, once it has one
        self.assertEqual(locker.held(self.db, KEY, 'slot-b')['card_key'], CARD_OLD)

    def test_a_platform_links_again_and_an_unheld_agent_links_nothing(self):
        locker.link(self.db, KEY, CARD_B, 'slot-b')
        locker.link(self.db, KEY, CARD_OLD, 'slot-b')   # its card named again: one card a platform, the last said
        self.assertIsNone(locker.held(self.db, CARD_B, 'slot-b'))
        self.assertEqual(locker.held(self.db, CARD_OLD, 'slot-b')['agent_key'], KEY)
        self.assertFalse(locker.link(self.db, 'MAGT_CCCCCCCCCCCC_0003', CARD_MAC, 'proof'))
        self.assertIsNone(locker.held(self.db, CARD_MAC, 'proof'))

    def test_removed_with_its_cards(self):
        locker.link(self.db, KEY, CARD_MAC, 'proof')
        locker.link(self.db, KEY, CARD_B, 'slot-b')
        locker.remove(self.db, locker.root_for(self.root, 'proof'), KEY, 'proof')
        self.assertIsNone(locker.held(self.db, CARD_MAC, 'proof'))
        self.assertEqual(locker.held(self.db, CARD_B, 'slot-b')['agent_key'], KEY)   # another platform's copy and card stay
        self.assertEqual(locker.verify(self.db, self.root, KEY), (True, ''))

    def test_the_second_guard_reads_the_callers_own_card(self):
        """The platform's approval names the card it shows; the runtime compares it with THIS caller's card of the agent."""
        locker.link(self.db, KEY, CARD_B, 'slot-b')
        locker.link(self.db, KEY, CARD_MAC, 'proof')
        row = locker.held(self.db, KEY)
        exact = (KEY, row['code_sha256'], row['manifest_sha256'])
        for caller, card, other in (('slot-b', CARD_B, CARD_MAC), ('proof', CARD_MAC, CARD_B)):
            h = harness.Harness(self.db, locker.root_for(self.root, caller), None, caller=caller)
            self.assertEqual(h._verifier({exact: card})(card), (True, ''))
            self.assertEqual(h._verifier({exact: other})(KEY), (False, 'not the card FROST approved'))
            self.assertEqual(h._verifier({exact: other})(other)[0], False)   # the other platform's card: no agent here


class TheBucketKeepsEveryPlatformsCard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bucket = FakeBucket()
        self.lockers = bucket_lockers.BucketLockers(bucket=self.bucket)
        package, row = marketplace_package()
        self.lockers.publish(MARKET, row, package)

    def tearDown(self):
        self.tmp.cleanup()

    def held(self, callers=('', 'slot-a', 'slot-b', 'proof'), n=1):
        base = pathlib.Path(tempfile.mkdtemp(dir=self.tmp.name))
        db = store.open_store(base)
        (base / 'agents').mkdir()
        self.assertEqual(self.lockers.sync(db, base / 'agents', CONF, callers=callers), n)
        return db

    def test_each_platforms_card_is_kept_beside_the_others(self):
        self.lockers.link(MARKET, CARD_OLD)   # the card file of before: one key, no caller
        self.assertEqual(self.lockers.copy('slot-b')['copied'], [MARKET])   # each platform its own copy (2026-11-22)
        self.assertEqual(self.lockers.copy('proof')['copied'], [MARKET])
        self.lockers.link(MARKET, CARD_B, 'slot-b')
        self.lockers.link(MARKET, CARD_MAC, 'proof')
        self.assertEqual(json.loads(self.bucket.objects[f'{MARKET}/card.json']), {'card_key': CARD_OLD})   # the locker of before: untouched
        self.assertEqual(json.loads(self.bucket.objects[f'slot-b/{MARKET}/card.json']), {'card_key': CARD_OLD, 'cards': {'slot-b': CARD_B}})
        self.assertEqual(json.loads(self.bucket.objects[f'proof/{MARKET}/card.json']), {'card_key': CARD_OLD, 'cards': {'proof': CARD_MAC}})
        db = self.held(n=3)   # a new instance's start: each caller's own copy
        self.assertEqual(locker.held(db, CARD_B, 'slot-b')['agent_key'], MARKET)
        self.assertEqual(locker.held(db, CARD_MAC, 'proof')['agent_key'], MARKET)
        self.assertEqual(locker.held(db, CARD_OLD, 'slot-a')['agent_key'], MARKET)   # a platform with no card of its own: the one of before
        self.assertIsNone(locker.held(db, CARD_MAC, 'slot-b'))

    def test_a_card_file_of_before_is_read_as_before(self):
        self.bucket.objects[f'{MARKET}/card.json'] = json.dumps({'card_key': CARD_OLD}).encode()
        db = self.held(callers=('',))
        self.assertEqual(locker.held(db, CARD_OLD)['agent_key'], MARKET)
        self.assertEqual(locker.held(db, CARD_OLD, 'slot-a')['card_key'], CARD_OLD)
        self.assertIsNone(locker.held(db, CARD_OLD, 'slot-b'))   # slot-b holds no copy until one is copied or placed for it


if __name__ == '__main__':
    unittest.main()
