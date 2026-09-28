import json
import os
import pathlib
import sqlite3
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import locker, store


def _agent(root, name='echo', code='import sys, json\nprint(json.dumps(json.load(sys.stdin)))\n'):
    folder = pathlib.Path(root) / name
    folder.mkdir()
    (folder / 'agent.json').write_text(json.dumps({'name': name.upper(), 'entry': 'agent.py'}))
    (folder / 'agent.py').write_text(code)
    return folder


class LockerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / 'agents'
        self.root.mkdir()
        self.db = store.open_store(self.tmp.name)
        _agent(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_then_verify(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_TEST_0001'), (True, ''))
        self.assertEqual(store.counts(self.db)['locker'], 1)

    def test_not_in_the_locker(self):
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_NONE_0000'), (False, 'not in the locker'))

    def test_edited_code_is_tampered(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        (self.root / 'echo' / 'agent.py').write_text('print("changed")\n')
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_TEST_0001'), (False, 'tampered: the code changed'))

    def test_added_file_is_tampered(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        (self.root / 'echo' / 'extra.py').write_text('x = 1\n')
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_TEST_0001'), (False, 'tampered: the code changed'))

    def test_edited_manifest_is_tampered(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        (self.root / 'echo' / 'agent.json').write_text(json.dumps({'name': 'OTHER', 'entry': 'agent.py'}))
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_TEST_0001'), (False, 'tampered: the manifest changed'))

    def test_missing_folder(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        (self.root / 'echo').rename(self.root / 'gone')
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_TEST_0001'), (False, 'tampered: the folder is missing'))

    def test_folder_must_be_inside_the_locker(self):
        _agent(self.tmp.name, 'outside')
        with self.assertRaises(ValueError):
            locker.add(self.db, self.root, 'MAGT_TEST_0002', '../outside')

    def test_row_pointing_outside_is_refused(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        _agent(self.tmp.name, 'outside')
        con = sqlite3.connect(self.db)
        con.execute("UPDATE hanzo_locker SET folder = '../outside'")
        con.commit()
        con.close()
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_TEST_0001'), (False, 'tampered: the folder is outside the locker'))

    def test_no_symlink_in_an_agent(self):
        os.symlink('/etc/hosts', self.root / 'echo' / 'hosts')
        with self.assertRaises(ValueError):
            locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')

    def test_symlink_planted_after_is_tampered(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        os.symlink('/etc/hosts', self.root / 'echo' / 'hosts')
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_TEST_0001'), (False, 'tampered: a link in the folder'))

    def test_manifest_needs_name_and_entry(self):
        (self.root / 'echo' / 'agent.json').write_text(json.dumps({'name': 'ECHO'}))
        with self.assertRaises(ValueError):
            locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')

    def test_key_is_held_once(self):
        locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')
        with self.assertRaises(sqlite3.IntegrityError):
            locker.add(self.db, self.root, 'MAGT_TEST_0001', 'echo')


if __name__ == '__main__':
    unittest.main()
