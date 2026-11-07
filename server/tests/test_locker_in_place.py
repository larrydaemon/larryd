"""THE LOCKER IN PLACE (ONE SYSTEM, the owner 2026-11-07: "1 single locker for all agents internal (sanity_agents/<name>"; "zero agents
should live in the runtime itself"): with LARRYD_INTERNAL=1 and LARRYD_LOCKER the runtime holds each agent where it is,
<LARRYD_LOCKER>/<name>/agent, its kits written into it at place so the folder is self-contained and its hashes cover them; verify()
refuses any change exactly as before; nothing is copied into instance/. Unset, production's place is what it was. Scratch folders only."""
import datetime
import io
import json
import os
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from _here import APP  # noqa: F401
from core_engine import intake, locker, store
from test_intake import Wid
from web import app as host

KEY = 'MAGT_00000000E001_0001'
SECRET = 'scratch-secret-for-the-locker-in-place'


def internal(locker_dir=None, on=True):
    env = {**({'LARRYD_INTERNAL': '1'} if on else {}), **({'LARRYD_LOCKER': str(locker_dir)} if locker_dir else {})}
    patch = mock.patch.dict(os.environ, env, clear=False)
    patch.start()
    for name in ('LARRYD_INTERNAL', 'LARRYD_LOCKER'):
        if name not in env:
            os.environ.pop(name, None)
    return patch


class Scratch(unittest.TestCase):
    """A scratch locker (sanity_agents with its _office kits and one agent) and a scratch instance."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        self.lock = base / 'sanity_agents'
        self.instance = base / 'instance'
        self.instance.mkdir()
        (self.lock / '_office').mkdir(parents=True)
        (self.lock / '_office' / 'office.py').write_text('WHO = "office"\n')
        (self.lock / '_office' / 'look.py').write_text('LOOK = "look"\n')
        self.agent = self.agent_folder('pf-scratch', libs=['look'])
        self.db = store.open_store(self.instance)
        self.patch = internal(self.lock)

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def agent_folder(self, name, libs=(), key=KEY):
        folder = self.lock / name / 'agent'
        folder.mkdir(parents=True)
        (folder / 'agent.json').write_text(json.dumps({'key': key, 'name': name, 'entry': 'agent.py', 'libs': list(libs)}))
        (folder / 'agent.py').write_text('import office, look\nprint(office.WHO)\n')
        (self.lock / name / 'samples').mkdir()
        (self.lock / name / 'samples' / 'job.json').write_text('{}')
        return folder

    def hold(self, folder='pf-scratch/agent', kits='default'):
        return intake.hold_in_place(self.db, self.lock, KEY, folder, 200, 5_000_000, kits=self.lock / '_office' if kits == 'default' else kits)


class InPlace(Scratch):
    def test_the_switch_is_only_internal(self):
        self.assertEqual(locker.in_place(), self.lock.resolve())
        self.patch.stop()
        self.patch = internal(self.lock, on=False)
        self.assertIsNone(locker.in_place())   # LARRYD_LOCKER alone switches nothing
        self.patch.stop()
        self.patch = internal(None)
        self.assertIsNone(locker.in_place())

    def test_held_in_place_with_its_kits_inside_and_nothing_copied(self):
        row = self.hold()
        self.assertEqual(row['folder'], 'pf-scratch/agent')
        self.assertEqual(sorted(p.name for p in self.agent.iterdir()), ['agent.json', 'agent.py', 'look.py', 'office.py'])
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (True, ''))
        self.assertEqual(sorted(p.name for p in self.instance.iterdir()), ['runtime.db'])   # instance/ is for the database

    def test_the_hashes_cover_the_kits(self):
        self.hold()
        (self.agent / 'look.py').write_text('LOOK = "changed"\n')
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (False, 'tampered: the code changed'))

    def test_any_change_added_file_or_link_is_tampered(self):
        self.hold()
        (self.agent / 'agent.py').write_text('print("changed")\n')
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (False, 'tampered: the code changed'))
        self.hold()
        (self.agent / 'extra.py').write_text('x = 1\n')
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (False, 'tampered: the code changed'))
        (self.agent / 'extra.py').unlink()
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (True, ''))
        (self.agent / 'out').symlink_to(self.tmp.name)
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (False, 'tampered: a link in the folder'))
        with self.assertRaises(intake.Refused):
            self.hold()

    def test_a_run_s_pycache_is_not_a_change(self):
        self.hold()
        (self.agent / '__pycache__').mkdir()
        (self.agent / '__pycache__' / 'office.cpython-313.pyc').write_bytes(b'x')
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (True, ''))

    def test_a_missing_kit_is_refused_before_anything_is_held(self):
        (self.lock / '_office' / 'look.py').unlink()
        with self.assertRaises(intake.Refused) as no:
            self.hold()
        self.assertIn('look.py', no.exception.reason)
        self.assertIsNone(locker.held(self.db, KEY))

    def test_without_kits_the_folder_is_held_as_it_is(self):
        (self.agent / 'agent.json').write_text(json.dumps({'key': KEY, 'name': 'n', 'entry': 'agent.py'}))
        self.hold(kits=None)
        self.assertEqual(sorted(p.name for p in self.agent.iterdir()), ['agent.json', 'agent.py'])

    def test_refusals(self):
        with self.assertRaises(intake.Refused):
            intake.hold_in_place(self.db, self.lock, 'MAGT_00000000E002_0002', 'pf-scratch/agent', 200, 5_000_000)   # agent.json names another key
        with self.assertRaises(intake.Refused):
            intake.hold_in_place(self.db, self.lock, KEY, '../instance', 200, 5_000_000)   # outside the locker
        with self.assertRaises(intake.Refused):
            intake.hold_in_place(self.db, self.lock, 'not a key', 'pf-scratch/agent', 200, 5_000_000)
        (self.agent / '.hidden').write_text('x')
        with self.assertRaises(intake.Refused):
            self.hold()
        self.assertIsNone(locker.held(self.db, KEY))

    def test_placed_again_replaces_its_row(self):
        first = self.hold()
        (self.agent / 'agent.py').write_text('print("v2")\n')
        second = self.hold()
        self.assertNotEqual(first['code_sha256'], second['code_sha256'])
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (True, ''))

    def test_remove_in_place_takes_the_row_and_keeps_the_folder(self):
        self.hold()
        locker.remove(self.db, self.lock, KEY)
        self.assertIsNone(locker.held(self.db, KEY))
        self.assertTrue((self.agent / 'agent.py').is_file())

    def test_place_command_in_place_then_wid(self):
        app = host.create_app(self.instance, secret=SECRET, agents=self.lock)
        wid = Wid()
        app.config['harness'].client = wid
        got = host.place_in_place(app, KEY, 'pf-scratch')
        self.assertEqual(got['folder'], 'pf-scratch/agent')
        self.assertEqual(got['review'], {'id': 1, 'state': 'waiting'})
        submitted = [d for _o, r, d in wid.said if r == '/agnt/submit'][0]
        self.assertEqual((submitted['code_sha256'], submitted['manifest_sha256']), (got['code_sha256'], got['manifest_sha256']))
        self.assertIn('look.py', os.listdir(self.agent))
        with self.assertRaises(SystemExit):
            host.place_in_place(app, KEY, str(self.instance))   # a folder outside the locker


class Adopt(Scratch):
    """THE ONE-TIME MOVE: an agent placed the old way (a copy in instance/agents/dev/<key>, kits packed in) held in place on the very
    hashes FROST approved."""
    def setUp(self):
        super().setUp()
        self.old = self.instance / 'agents'
        self.old.mkdir()
        files = {'agent.json': (self.agent / 'agent.json').read_bytes(), 'agent.py': (self.agent / 'agent.py').read_bytes(),
                 'office.py': b'WHO = "office as approved"\n', 'look.py': b'LOOK = "look as approved"\n'}
        self.row = intake.receive(self.db, self.old, 'dev', KEY, files)
        locker.link(self.db, KEY, KEY)

    def test_adopted_on_the_approved_hashes_with_the_approved_kits(self):
        (self.lock / '_office' / 'office.py').write_text('WHO = "office, newer"\n')   # the kits moved on since; the approved bytes are kept
        row = locker.adopt(self.db, self.old, self.lock, KEY, 'pf-scratch/agent')
        self.assertEqual((row['folder'], row['code_sha256'], row['manifest_sha256'], row['card_key']),
                         ('pf-scratch/agent', self.row['code_sha256'], self.row['manifest_sha256'], KEY))
        self.assertEqual((self.agent / 'office.py').read_text(), 'WHO = "office as approved"\n')
        self.assertEqual(locker.verify(self.db, self.lock, KEY), (True, ''))

    def test_a_changed_agent_is_not_adopted(self):
        (self.agent / 'agent.py').write_text('print("changed since")\n')
        with self.assertRaises(ValueError):
            locker.adopt(self.db, self.old, self.lock, KEY, 'pf-scratch/agent')
        self.assertEqual(locker.held(self.db, KEY)['folder'], f'dev/{KEY}')

    def test_a_file_the_approved_copy_never_had_is_not_adopted(self):
        (self.agent / 'new.py').write_text('x = 1\n')
        with self.assertRaises(ValueError):
            locker.adopt(self.db, self.old, self.lock, KEY, 'pf-scratch/agent')

    def test_a_tampered_copy_is_not_adopted(self):
        (self.old / 'dev' / KEY / 'office.py').write_text('changed')
        with self.assertRaises(ValueError):
            locker.adopt(self.db, self.old, self.lock, KEY, 'pf-scratch/agent')
        self.assertFalse((self.agent / 'office.py').exists())


class TheStart(unittest.TestCase):
    """main(): the locker the runtime is built on, and place's two roads."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        self.instance, self.lock = base / 'instance', base / 'sanity_agents'
        (self.instance / 'secrets').mkdir(parents=True)
        (self.instance / 'secrets' / host.CONFIG['secret']['name']).write_text(SECRET)
        self.lock.mkdir()
        self.built = {}

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, argv, internal_on, lock):
        real = host.create_app

        def create(*a, **k):
            self.built['agents'] = k.get('agents')
            return real(*a, **k)
        patch = internal(lock, on=internal_on)
        try:
            with mock.patch.object(host, 'INSTANCE', self.instance), mock.patch.object(host, 'create_app', create), \
                    mock.patch.object(host, 'catch_up', lambda app: 0), mock.patch.object(host.Flask, 'run', lambda *a, **k: None), \
                    mock.patch.object(host.clock.Clocks, 'start', lambda self, every=60: None):
                os.environ.pop('LARRYD_KEYS_DIR', None)
                with redirect_stdout(io.StringIO()):
                    host.main(['app.py', *argv])
        finally:
            patch.stop()

    def test_internal_with_a_locker_is_built_on_it(self):
        self.run_main([], True, self.lock)
        self.assertEqual(self.built['agents'], self.lock.resolve())

    def test_without_the_switch_the_locker_is_what_it_was(self):
        self.run_main([], False, self.lock)
        self.assertEqual(self.built['agents'], host.locker_root(self.instance))
        self.run_main([], True, None)
        self.assertEqual(self.built['agents'], host.locker_root(self.instance))

    def test_in_place_a_larryd_file_is_refused(self):
        package = pathlib.Path(self.tmp.name) / 'x.larryd'
        package.write_bytes(b'PK')
        with self.assertRaises(SystemExit) as no:
            self.run_main(['place', KEY, str(package)], True, self.lock)
        self.assertIn('in place', str(no.exception))

    def test_a_locker_that_is_no_folder_stops_the_start(self):
        with self.assertRaises(SystemExit):
            self.run_main([], True, pathlib.Path(self.tmp.name) / 'nowhere')


if __name__ == '__main__':
    unittest.main()
