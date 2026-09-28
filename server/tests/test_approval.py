"""VERIFIED = the locker's hashes AND FROST's approval of those exact hashes; a changed agent is unapproved at once."""
import pathlib
import shutil
import tempfile
import unittest

from _here import APP
from core_engine import harness, locker, store


class Approval(unittest.TestCase):
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

    def test_approved_by_the_exact_hashes(self):
        exact = {('MAGT_SCRATCH00001_0001', self.row['code_sha256'], self.row['manifest_sha256'])}
        self.assertEqual(self.h._verifier(exact)('MAGT_SCRATCH00001_0001'), (True, ''))
        self.assertEqual(self.h._verifier(set())('MAGT_SCRATCH00001_0001'), (False, 'not approved by FROST'))
        other = {('MAGT_SCRATCH00001_0001', 'f' * 64, self.row['manifest_sha256'])}
        self.assertEqual(self.h._verifier(other)('MAGT_SCRATCH00001_0001'), (False, 'not approved by FROST'))

    def test_the_locker_speaks_first(self):
        exact = {('MAGT_SCRATCH00001_0001', self.row['code_sha256'], self.row['manifest_sha256'])}
        (self.agents / 'marketplace' / 'agent.py').write_text('print("{}")\n')
        self.assertEqual(self.h._verifier(exact)('MAGT_SCRATCH00001_0001'), (False, 'tampered: the code changed'))


if __name__ == '__main__':
    unittest.main()
