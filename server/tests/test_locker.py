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


class BothKeysLinked(unittest.TestCase):
    """THE OWNER, 2026-10-06: the runtime mints its OWN key for the agent; the platform mints the card's key at approval and
    tells the runtime; BOTH are saved and linked: the agent is found by either, its stylesheet is in the approved hash."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / 'agents'
        self.root.mkdir()
        self.db = store.open_store(self.tmp.name)
        _agent(self.root)
        locker.add(self.db, self.root, 'MAGT_AAAAAAAAAAAA_0001', 'echo')

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_card_key_finds_the_runtimes_agent(self):
        self.assertIsNone(locker.held(self.db, 'MAGT_BBBBBBBBBBBB_0002'))
        self.assertTrue(locker.link(self.db, 'MAGT_AAAAAAAAAAAA_0001', 'MAGT_BBBBBBBBBBBB_0002'))
        row = locker.held(self.db, 'MAGT_BBBBBBBBBBBB_0002')
        self.assertEqual((row['agent_key'], row['card_key']), ('MAGT_AAAAAAAAAAAA_0001', 'MAGT_BBBBBBBBBBBB_0002'))
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_BBBBBBBBBBBB_0002'), (True, ''))
        self.assertFalse(locker.link(self.db, 'MAGT_CCCCCCCCCCCC_0003', 'MAGT_BBBBBBBBBBBB_0002'))   # not held: nothing linked
        self.assertIsNone(locker.held(self.db, ''))   # an empty card key finds nothing

    def test_the_approved_hash_covers_the_stylesheet(self):
        before = locker.held(self.db, 'MAGT_AAAAAAAAAAAA_0001')['code_sha256']
        (self.root / 'echo' / 'card.css').write_text('.mk-card { border: 1px solid var(--active-color-01) }\n')
        self.assertEqual(locker.verify(self.db, self.root, 'MAGT_AAAAAAAAAAAA_0001'), (False, 'tampered: the code changed'))   # a sheet added after approval
        self.assertNotEqual(locker._code_sha256(self.root / 'echo'), before)

    def test_an_old_locker_gets_the_column(self):
        con = sqlite3.connect(self.db)
        con.execute('DROP TABLE hanzo_locker')
        con.execute('CREATE TABLE hanzo_locker ("agent_key" TEXT PRIMARY KEY, "name" TEXT NOT NULL, "folder" TEXT NOT NULL, "code_sha256" TEXT NOT NULL, '
                    '"manifest_sha256" TEXT NOT NULL, "registered_at" TEXT NOT NULL)')
        con.execute("INSERT INTO hanzo_locker VALUES ('MAGT_AAAAAAAAAAAA_0001', 'ECHO', 'echo', 'x', 'y', 'now')")
        con.commit()
        con.close()
        store.open_store(self.tmp.name)   # the schema's new column added, the row kept
        self.assertEqual(locker.held(self.db, 'MAGT_AAAAAAAAAAAA_0001')['card_key'], None)
