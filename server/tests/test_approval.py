"""VERIFIED = the locker's exact hashes, LARRYD's own approval (the core cleanup, the owner 2026-11-05: no agent has
anything to do with FROST; an agent is held in the locker only by `place`, the owner's approved file). A changed agent is
unapproved at once; FROST is never asked."""
import pathlib
import shutil
import tempfile
import unittest

from _here import APP
from core_engine import harness, locker, store


class NoPlatform:
    """A client that fails the test if anything is asked: the approval is the runtime's own word."""
    def get(self, office, route, data=None):
        raise AssertionError(f'the verifier asked {office}{route}')

    post = get


class Held(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.agents = pathlib.Path(self.tmp.name) / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace')
        self.db = store.open_store(self.tmp.name)
        locker.add(self.db, self.agents, 'MAGT_SCRATCH00001_0001', 'marketplace')
        self.row = locker.held(self.db, 'MAGT_SCRATCH00001_0001')
        self.h = harness.Harness(self.db, self.agents, client=NoPlatform())

    def tearDown(self):
        self.tmp.cleanup()


class Approval(Held):
    def test_held_with_its_exact_hashes_is_approved_without_asking_anyone(self):
        self.assertEqual(self.h._verifier()('MAGT_SCRATCH00001_0001'), (True, ''))

    def test_an_agent_not_in_the_locker_is_refused(self):
        self.assertEqual(self.h._verifier()('MAGT_SCRATCH00009_0009'), (False, 'not in the locker'))

    def test_the_locker_speaks_first(self):
        (self.agents / 'marketplace' / 'agent.py').write_text('print("{}")\n')
        self.assertEqual(self.h._verifier()('MAGT_SCRATCH00001_0001'), (False, 'tampered: the code changed'))


class TheSinkByTheCard(Held):
    """THE SINK: at every call, hire and run the agent is verified afresh against the locker, by its own key or by the card
    key linked at placement; a new hash or another card: refused at once, fail closed."""
    CARD = 'MAGT_00000000CA01_0001'

    def setUp(self):
        super().setUp()
        locker.link(self.db, 'MAGT_SCRATCH00001_0001', self.CARD)

    def test_by_the_card_key_while_held(self):
        self.assertEqual(self.h._verifier()(self.CARD), (True, ''))

    def test_a_new_hash_is_refused_until_placed_again(self):
        (self.agents / 'marketplace' / 'notes.txt').write_text('changed after approval\n')   # a file added after approval
        self.assertEqual(self.h._verifier()(self.CARD), (False, 'tampered: the code changed'))

    def test_another_card_is_not_covered(self):
        self.assertEqual(self.h._verifier()('MAGT_00000000CB02_0002'), (False, 'not in the locker'))


if __name__ == '__main__':
    unittest.main()
