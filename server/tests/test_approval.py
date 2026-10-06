"""VERIFIED = the locker's hashes AND FROST's approval of those exact hashes; a changed agent is unapproved at once."""
import pathlib
import shutil
import tempfile
import unittest

from _here import APP
from core_engine import harness, locker, store


class Held(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.agents = pathlib.Path(self.tmp.name) / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace')
        self.db = store.open_store(self.tmp.name)
        locker.add(self.db, self.agents, 'MAGT_SCRATCH00001_0001', 'marketplace')
        self.row = locker.held(self.db, 'MAGT_SCRATCH00001_0001')
        self.h = harness.Harness(self.db, self.agents, client=None)

    def tearDown(self):
        self.tmp.cleanup()


class Approval(Held):
    def test_approved_by_the_exact_hashes(self):
        exact = {('MAGT_SCRATCH00001_0001', self.row['code_sha256'], self.row['manifest_sha256']): ''}
        self.assertEqual(self.h._verifier(exact)('MAGT_SCRATCH00001_0001'), (True, ''))
        self.assertEqual(self.h._verifier({})('MAGT_SCRATCH00001_0001'), (False, 'not approved by FROST'))
        other = {('MAGT_SCRATCH00001_0001', 'f' * 64, self.row['manifest_sha256']): ''}
        self.assertEqual(self.h._verifier(other)('MAGT_SCRATCH00001_0001'), (False, 'not approved by FROST'))

    def test_the_locker_speaks_first(self):
        exact = {('MAGT_SCRATCH00001_0001', self.row['code_sha256'], self.row['manifest_sha256']): ''}
        (self.agents / 'marketplace' / 'agent.py').write_text('print("{}")\n')
        self.assertEqual(self.h._verifier(exact)('MAGT_SCRATCH00001_0001'), (False, 'tampered: the code changed'))


class TheSinkByTheCard(Held):
    """THE SINK (the security review and the owner, 2026-10-06): at every call, hire and run the runtime asks FROST's approved
    list afresh; the agent is shown by its card's key only while FROST approved exactly its hashes FOR THAT CARD. A
    revocation (gone from the list), a new hash, or another card: refused at once, fail closed."""
    CARD = 'MAGT_00000000CA01_0001'

    def setUp(self):
        super().setUp()
        locker.link(self.db, 'MAGT_SCRATCH00001_0001', self.CARD)
        self.exact = ('MAGT_SCRATCH00001_0001', self.row['code_sha256'], self.row['manifest_sha256'])

    def test_by_the_card_key_while_approved(self):
        self.assertEqual(self.h._verifier({self.exact: self.CARD})(self.CARD), (True, ''))

    def test_approved_then_revoked_is_refused(self):
        self.assertEqual(self.h._verifier({})(self.CARD), (False, 'not approved by FROST'))

    def test_a_new_hash_needs_a_new_review(self):
        (self.agents / 'marketplace' / 'notes.txt').write_text('changed after approval\n')   # a file added after approval
        self.assertEqual(self.h._verifier({self.exact: self.CARD})(self.CARD), (False, 'tampered: the code changed'))

    def test_another_card_is_not_covered(self):
        self.assertEqual(self.h._verifier({self.exact: 'MAGT_00000000CB02_0002'})(self.CARD), (False, 'not the card FROST approved'))


if __name__ == '__main__':
    unittest.main()
