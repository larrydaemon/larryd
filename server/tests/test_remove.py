"""THE `remove <key>` COMMAND (frost-05's approval 2026-11-06: revoked leftovers sat in the locker, inert): a placed agent is taken out
(its folder under the locker and its row) ONLY when the platform's word on its exact hashes is revoked (FROST's latest review, through
wid's review_state door); an approved, waiting or unknown one, or a key not held, is refused in words and nothing is touched. On Cloud
Run the command refuses (the lockers bucket keeps the agent too). Scratch folders and a stand-in wid only."""
import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from _here import APP  # noqa: F401
from core_engine import locker
import test_intake
from test_intake import KEY, OTHER, _agent
from web import app as host


class Remove(unittest.TestCase):
    setUp, tearDown, place = test_intake.Intake.setUp, test_intake.Intake.tearDown, test_intake.Intake.place   # its scratch locker and stand-in wid, not its tests

    def word(self, held, state):
        self.wid.states = {(KEY, held['code_sha256'], held['manifest_sha256']): (state, '')}

    def folder(self):
        return self.agents / 'dev' / KEY

    def test_a_revoked_agent_is_removed_folder_and_row(self):
        held = self.place(_agent())
        self.assertTrue(self.folder().is_dir())
        self.word(held, 'revoked')
        with self.assertLogs('runtime', 'WARNING') as said:
            self.assertEqual(self.h.remove(KEY), {'agent_key': KEY, 'removed': f'dev/{KEY}'})
        self.assertIn(f'remove {KEY}: removed dev/{KEY}', said.output[0])   # logged
        self.assertFalse(self.folder().exists())
        self.assertIsNone(locker.held(self.db, KEY))
        self.assertEqual(self.h.remove(KEY)['refused'], 'not in the locker under this key')   # once only

    def test_an_approved_waiting_rejected_or_unknown_agent_is_refused_and_kept(self):
        held = self.place(_agent())
        for state in ('approved', 'waiting', 'rejected', 'not submitted'):
            with self.subTest(state=state):
                self.word(held, state)
                got = self.h.remove(KEY)
                self.assertEqual(got, {'agent_key': KEY, 'refused': f'its review is {state}, not revoked: kept'})
                self.assertTrue(self.folder().is_dir())
                self.assertIsNotNone(locker.held(self.db, KEY))
        self.h.client.get = lambda *a, **k: (503, {'refused': 'away'})   # wid silent: never removed on a guess
        self.assertIn('its review is unknown: away, not revoked', self.h.remove(KEY)['refused'])
        self.assertTrue(self.folder().is_dir())

    def test_an_unknown_key_or_a_card_keys_alias_is_refused(self):
        self.assertEqual(self.h.remove(OTHER), {'agent_key': OTHER, 'refused': 'not in the locker under this key'})
        held = self.place(_agent())
        locker.link(self.db, KEY, OTHER)   # its card's key, linked at approval: the command takes the runtime's own key exactly
        self.word(held, 'revoked')
        self.assertEqual(self.h.remove(OTHER)['refused'], 'not in the locker under this key')
        self.assertTrue(self.folder().is_dir())

    def test_the_command_says_it_and_refuses_on_cloud_run(self):
        held = self.place(_agent())
        self.word(held, 'approved')
        with mock.patch.object(host, 'create_app', return_value=self.app), self.assertRaises(SystemExit) as no:
            host.main(['app.py', 'remove', KEY])
        self.assertEqual(str(no.exception), 'refused: its review is approved, not revoked: kept')
        self.word(held, 'revoked')
        out = io.StringIO()
        with mock.patch.object(host, 'create_app', return_value=self.app), redirect_stdout(out):
            host.main(['app.py', 'remove', KEY])
        self.assertIn('"removed": "dev/', out.getvalue())
        self.app.config['lockers'] = object()
        with mock.patch.object(host, 'create_app', return_value=self.app), self.assertRaises(SystemExit) as no:
            host.main(['app.py', 'remove', KEY])
        self.assertIn('on Cloud Run the lockers bucket keeps the agent too', str(no.exception))


if __name__ == '__main__':
    unittest.main()
