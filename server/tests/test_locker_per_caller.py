"""EACH CALLER ITS OWN LOCKER (the owner 2026-11-22: "there should be zero agents that are on a and b at the same fucking time. if so
fix that too"). The one runtime is called by slot-a (production A), slot-b (production B) and proof (this Mac). Its cards were already
per caller (2026-11-11), but its LOCKER was one: one row and one folder (agent.json and code, one sha256) per agent, run for every
caller, so a manifest could not change for B without changing it for A (whose FROST approval names the old manifest_sha256). Now the
row and the folder are the caller's: the locker of before stays slot A's exactly as it was, slot-b and proof get their own copies
(a migration that copies, never moves), and every call, run, hire, place and clock path is held to the caller's own copy.

The proofs: (1) A's answer is unchanged after the migration; (2) a change to slot-b's agent.json never changes slot-a's hash or
answer; (3) a caller never reaches another caller's folder."""
import hashlib
import io
import json
import os
import pathlib
import sqlite3
import tempfile
import unittest
import zipfile
from unittest import mock

from _here import APP  # noqa: F401
from test_review_fixes import CloudApp, FakeBucket
from core_engine import harness, intake, locker, lockers as bucket_lockers, store
from web import app as host

KEY = 'MAGT_0000000000C1_0001'
ACCOUNT, SCOPE, MEMBER = 'ACCT_' + 'A' * 12 + '_0001', 'SCRATCH', 'MCON_' + 'B' * 12 + '_0002'
CARD = {'key': KEY, 'name': 'Scratch per caller', 'screen': 'larry/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'Agents',
        'price': '0', 'status': 'APPROVED', 'authorization': 'PUBLIC', 'account_key': ''}
HIRED = [{'agent_key': KEY, 'board': 'larry/home', 'shell_id': 1, 'on': True, 'job_key': ''}]
CONF = json.loads((APP / 'schemas' / 'runtime.json').read_text())['intake']
MANIFEST = {'name': 'Scratch per caller', 'entry': 'agent.py', 'calls': ['panel'], 'gives': ['view'], 'skills': []}
OLD_LOCKER = ('CREATE TABLE runtime_locker (agent_key TEXT PRIMARY KEY, name TEXT NOT NULL, folder TEXT NOT NULL, code_sha256 TEXT NOT NULL, '
              'manifest_sha256 TEXT NOT NULL, registered_at TEXT NOT NULL, card_key TEXT)')   # the table as every runtime held it before 2026-11-22


class Platform:
    """One caller's platform as the runtime hears it: its cards, its hires, and ITS OWN FROST's approval (of its own hashes)."""
    def __init__(self, approved):
        self.approved = approved

    def get(self, office, route, data=None):
        if route == '/agnt/cards':
            return 200, {'cards': [CARD]}
        if route == '/agnt/hired':
            return 200, {'hired': HIRED}
        if route == '/jobs/balance':
            return 200, {'subscriptions': []}
        if route == '/agnt/approved':
            return 200, {'approved': self.approved}
        return 404, {'refused': route}

    def post(self, office, route, data):
        if route == '/agnt/submit':
            return 200, {'id': 1, 'state': 'waiting', 'card_key': ''}
        return 200, {}


def ran(folder, entry, given, seconds=20, on_start=None, most_bytes=None, **kw):
    """The sandbox's stand-in: the answer is drawn from the very folder the runtime ran (its manifest's bytes), so an answer shows
    whose copy was run."""
    body = (pathlib.Path(folder) / 'agent.json').read_bytes()
    name = json.loads(body)['name']
    return 'DONE', {'view': {'html': f'<section>{name} {hashlib.sha256(body).hexdigest()[:16]}</section>', 'css': ''}}, ''


def package(manifest=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('agent.json', json.dumps(manifest or MANIFEST))
        z.writestr('agent.py', 'print("{}")\n')
    return buf.getvalue()


def answer_of(h, row):
    """The caller's answer, its own FROST approving exactly its own row's hashes."""
    h.client = Platform([{'agent_key': row['agent_key'], 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256'], 'card_key': ''}])
    h.forget_approved()
    return json.dumps(h.answer(ACCOUNT, SCOPE, MEMBER, KEY), sort_keys=True)


class Patched(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(harness.sandbox, 'run', ran)
        p.start()
        self.addCleanup(p.stop)
        os.environ.pop('LARRYD_INTERNAL', None)


class TheMigration(Patched):
    """A runtime of before: the old table (agent_key the one key), one row, one folder, slot A's and slot-b's cards beside it."""
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = pathlib.Path(tmp.name)
        self.instance, self.agents = self.base / 'instance', self.base / 'agents'
        self.instance.mkdir()
        folder = self.agents / 'dev' / KEY
        folder.mkdir(parents=True)
        (folder / 'agent.json').write_text(json.dumps(MANIFEST))
        (folder / 'agent.py').write_text('print("{}")\n')
        con = sqlite3.connect(self.instance / 'agents.db')
        con.execute(OLD_LOCKER)
        con.execute('CREATE TABLE runtime_cards (agent_key TEXT NOT NULL, caller TEXT NOT NULL, card_key TEXT NOT NULL)')
        con.execute('INSERT INTO runtime_locker VALUES (?,?,?,?,?,?,?)', (KEY, MANIFEST['name'], f'dev/{KEY}', locker._code_sha256(folder),
                                                                           locker._manifest_sha256(folder), '2026-11-01T00:00:00+00:00', ''))
        con.commit()
        self.before = con.execute('SELECT * FROM runtime_locker').fetchall()
        con.close()
        self.files = {p.relative_to(self.agents).as_posix(): p.read_bytes() for p in sorted(self.agents.rglob('*')) if p.is_file()}

    def a(self, db):
        return harness.Harness(db, locker.root_for(self.agents, 'slot-a'), None, caller='slot-a')

    def test_the_rows_of_before_become_slot_a_s_exactly_as_they_are(self):
        db = store.open_store(self.instance)   # the start that rekeys the table
        con = sqlite3.connect(db)
        after = con.execute('SELECT agent_key, name, folder, code_sha256, manifest_sha256, registered_at, card_key, caller FROM runtime_locker').fetchall()
        key = [r[1] for r in sorted((r for r in con.execute('PRAGMA table_info(runtime_locker)') if r[5]), key=lambda r: r[5])]
        con.close()
        self.assertEqual(after, [tuple(self.before[0]) + ('',)])   # every column as it was, the locker of before ('')
        self.assertEqual(key, ['agent_key', 'caller'])
        self.assertEqual(store.open_store(self.instance), db)   # a second start changes nothing
        self.assertEqual(locker.held(db, KEY, 'slot-a')['manifest_sha256'], self.before[0][4])

    def test_1_a_s_answer_is_unchanged_after_the_migration(self):
        db = store.open_store(self.instance)
        row = locker.held(db, KEY, 'slot-a')
        first = answer_of(self.a(db), row)
        self.assertIn(MANIFEST['name'], first)
        for to in ('slot-b', 'proof'):
            self.assertEqual(locker.copy(db, self.agents, to), {'copied': [KEY], 'kept': [], 'refused': {}})
            self.assertEqual(locker.copy(db, self.agents, to), {'copied': [], 'kept': [KEY], 'refused': {}})   # run again: nothing more
        self.assertEqual(answer_of(self.a(db), locker.held(db, KEY, 'slot-a')), first)   # byte for byte
        self.assertEqual(locker.held(db, KEY, 'slot-a'), row)
        self.assertEqual({p.relative_to(self.agents).as_posix(): p.read_bytes() for p in sorted(self.agents.rglob('*')) if p.is_file()}, self.files)   # A's folder untouched
        for to in ('slot-b', 'proof'):   # each copy is its own, at the same place in its own locker, on the same hashes
            mine = locker.held(db, KEY, to)
            self.assertEqual({k: mine[k] for k in ('folder', 'code_sha256', 'manifest_sha256', 'registered_at')},
                             {k: row[k] for k in ('folder', 'code_sha256', 'manifest_sha256', 'registered_at')})
            self.assertEqual(mine['caller'], to)
            self.assertTrue((self.base / f'agents.{to}' / 'dev' / KEY / 'agent.json').is_file())
            h = harness.Harness(db, locker.root_for(self.agents, to), None, caller=to)
            self.assertEqual(answer_of(h, mine), first)   # the copy answers as A's did, until its own platform changes it

    def test_2_slot_b_s_agent_json_changed_never_changes_slot_a(self):
        db = store.open_store(self.instance)
        a_row = locker.held(db, KEY, 'slot-a')
        a_answer = answer_of(self.a(db), a_row)
        locker.copy(db, self.agents, 'slot-b')
        b_root = locker.root_for(self.agents, 'slot-b')
        (b_root / 'dev' / KEY / 'agent.json').write_text(json.dumps({**MANIFEST, 'name': 'Scratch per caller, B only'}))
        self.assertEqual(locker.verify(db, b_root, KEY, 'slot-b'), (False, 'tampered: the manifest changed'))   # B's copy changed by hand: B refuses it
        self.assertEqual(locker.verify(db, self.agents, KEY, 'slot-a'), (True, ''))   # A never sees it
        b_row = intake.receive(db, b_root, 'dev', KEY, {'agent.json': json.dumps({**MANIFEST, 'name': 'Scratch per caller, B only'}).encode(),
                                                        'agent.py': b'print("{}")\n'}, 'slot-b')   # placed again for slot-b: its own new hashes
        self.assertNotEqual(b_row['manifest_sha256'], a_row['manifest_sha256'])
        self.assertEqual(locker.held(db, KEY, 'slot-a'), a_row)   # A's hash: unchanged
        self.assertEqual(locker.held(db, KEY, 'slot-b')['manifest_sha256'], b_row['manifest_sha256'])
        self.assertEqual(answer_of(self.a(db), a_row), a_answer)   # A's answer: unchanged
        b = harness.Harness(db, b_root, None, caller='slot-b')
        self.assertIn('B only', answer_of(b, b_row))
        b.client = Platform([{'agent_key': KEY, 'code_sha256': a_row['code_sha256'], 'manifest_sha256': a_row['manifest_sha256'], 'card_key': ''}])
        b.forget_approved()
        with self.assertRaises(harness.Refused):   # B's new manifest needs B's own approval: A's approval never covers it
            b.answer(ACCOUNT, SCOPE, MEMBER, KEY)

    def test_3_a_caller_never_reaches_another_caller_s_folder(self):
        db = store.open_store(self.instance)
        b_root = locker.root_for(self.agents, 'slot-b')
        b = harness.Harness(db, b_root, Platform([]), caller='slot-b')
        self.assertIsNone(locker.held(db, KEY, 'slot-b'))   # A holds it; B holds no copy yet: B finds nothing
        with self.assertRaises(harness.Refused) as no:
            b.answer(ACCOUNT, SCOPE, MEMBER, KEY)
        self.assertEqual((no.exception.status, no.exception.reason), (404, 'no agent that answers here'))
        self.assertEqual(locker.verify(db, b_root, KEY, 'slot-b'), (False, 'not in the locker'))
        locker.copy(db, self.agents, 'slot-b')
        for one, other in ((self.agents, b_root), (b_root, self.agents)):   # neither locker's folder is inside the other's
            self.assertNotIn(one.resolve(), other.resolve().parents)
            self.assertNotEqual(one.resolve(), other.resolve())
        con = sqlite3.connect(db)   # a row of B's that names A's folder
        con.execute("UPDATE runtime_locker SET folder = ? WHERE caller = 'slot-b'", (f'../agents/dev/{KEY}',))
        con.commit()
        con.close()
        self.assertEqual(locker.verify(db, b_root, KEY, 'slot-b'), (False, 'tampered: the folder is outside the locker'))
        self.assertEqual(locker.verify(db, self.agents, KEY, 'slot-a'), (True, ''))
        locker.link(db, KEY, 'MAGT_0000000000A1_0001', 'slot-a')   # A's card is never B's way in
        self.assertIsNone(locker.held(db, 'MAGT_0000000000A1_0001', 'slot-b'))
        with self.assertRaises(ValueError):
            locker.of('../slot-a')   # a caller's name is never a path

    def test_a_caller_s_copy_removed_leaves_the_others(self):
        db = store.open_store(self.instance)
        locker.copy(db, self.agents, 'slot-b')
        b_root = locker.root_for(self.agents, 'slot-b')
        locker.remove(db, b_root, KEY, 'slot-b')
        self.assertFalse((b_root / 'dev' / KEY).exists())
        self.assertIsNone(locker.held(db, KEY, 'slot-b'))
        self.assertEqual(locker.verify(db, self.agents, KEY, 'slot-a'), (True, ''))

    def test_the_locker_in_place_stays_one_locker(self):
        """THE INTERNAL RUNTIME (LARRYD_INTERNAL=1 and LARRYD_LOCKER, the one internal locker): keeps working as it does, one locker for
        every caller, the folder where it is."""
        with mock.patch.dict(os.environ, {'LARRYD_INTERNAL': '1', 'LARRYD_LOCKER': str(self.agents)}):
            db = store.open_store(self.instance)
            for caller in ('', 'slot-a', 'slot-b', 'proof'):
                self.assertEqual(locker.of(caller), '')
                self.assertEqual(locker.root_for(self.agents, caller), self.agents)
                self.assertEqual(locker.verify(db, self.agents, KEY, caller), (True, ''))
            with self.assertRaises(ValueError):
                locker.copy(db, self.agents, 'proof')


class TheBucket(unittest.TestCase):
    """Cloud Run: the lockers bucket keeps the locker of before at its top (slot A's, untouched) and each other caller's under its name."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bucket = FakeBucket()
        self.lockers = bucket_lockers.BucketLockers(bucket=self.bucket)
        db, root = self.instance()
        row = intake.receive(db, root, 'dev', KEY, intake.check(intake.from_zip(package(), CONF['most_files'], CONF['most_bytes']), CONF['most_files'], CONF['most_bytes']))
        self.lockers.publish(KEY, row, package())
        self.lockers.link(KEY, 'MAGT_0000000000A1_0001', 'slot-a')
        self.top = dict(self.bucket.objects)

    def instance(self):
        base = pathlib.Path(tempfile.mkdtemp(dir=self.tmp.name))
        return store.open_store(base), base / 'agents'

    def test_the_copy_leaves_the_top_untouched_and_runs_once(self):
        self.assertEqual(self.lockers.copy('slot-b'), {'copied': [KEY], 'kept': []})
        self.assertEqual(self.lockers.copy('slot-b'), {'copied': [], 'kept': [KEY]})
        self.assertEqual({k: v for k, v in self.bucket.objects.items() if not k.startswith('slot-b/')}, self.top)
        self.assertEqual({k.removeprefix('slot-b/'): v for k, v in self.bucket.objects.items() if k.startswith('slot-b/')}, self.top)
        self.assertEqual(self.lockers.keys(), [KEY])
        self.assertEqual(self.lockers.keys('slot-a'), [KEY])
        self.assertEqual(self.lockers.keys('slot-b'), [KEY])
        self.assertEqual(self.lockers.keys('proof'), [])

    def test_slot_b_placed_anew_leaves_slot_a_s_locker_json(self):
        self.lockers.copy('slot-b')
        db, root = self.instance()
        changed = package({**MANIFEST, 'name': 'Scratch per caller, B only'})
        files = intake.check(intake.from_zip(changed, CONF['most_files'], CONF['most_bytes']), CONF['most_files'], CONF['most_bytes'])
        row = intake.receive(db, locker.root_for(root, 'slot-b'), 'dev', KEY, files, 'slot-b')
        self.lockers.publish(KEY, row, changed, caller='slot-b')
        self.assertEqual(self.bucket.objects[f'{KEY}/locker.json'], self.top[f'{KEY}/locker.json'])
        self.assertEqual(json.loads(self.bucket.objects[f'slot-b/{KEY}/locker.json'])['manifest_sha256'], row['manifest_sha256'])
        db, root = self.instance()   # a new instance's start: each caller its own copy
        self.assertEqual(self.lockers.sync(db, root, CONF, callers=['', 'slot-a', 'slot-b', 'proof']), 2)
        self.assertNotEqual(locker.held(db, KEY, 'slot-a')['manifest_sha256'], locker.held(db, KEY, 'slot-b')['manifest_sha256'])
        self.assertEqual(json.loads(self.bucket.objects[f'{KEY}/locker.json'])['manifest_sha256'], locker.held(db, KEY, 'slot-a')['manifest_sha256'])
        self.assertIsNone(locker.held(db, KEY, 'proof'))   # proof holds no copy of its own: it never runs slot A's
        self.assertEqual(locker.held(db, 'MAGT_0000000000A1_0001', 'slot-a')['agent_key'], KEY)
        self.assertIsNone(locker.held(db, 'MAGT_0000000000A1_0001', 'slot-b'))


class OnCloudRun(Patched, CloudApp):
    """The host as Cloud Run builds it: each slot's harness on its own locker; place --slot writes that slot's locker alone."""
    def setUp(self):
        Patched.setUp(self)
        CloudApp.setUp(self)

    def test_each_slot_s_harness_holds_its_own_locker_and_place_writes_only_it(self):
        app = self.make()
        hs = app.config['harnesses']
        self.assertEqual(hs['slot-a'].agents, pathlib.Path(self.dir.name) / 'instance' / 'agents')
        self.assertEqual(hs['slot-b'].agents, pathlib.Path(self.dir.name) / 'instance' / 'agents.slot-b')
        for h in hs.values():
            h.client = Platform([])
        out = host.place(app, KEY, package(), slot='slot-a')
        self.assertIsNone(locker.held(hs['slot-b'].db, KEY, 'slot-b'))   # placed for slot-a: slot-b holds nothing
        self.assertNotIn(f'slot-b/{KEY}/locker.json', self.bucket.objects)
        changed = package({**MANIFEST, 'name': 'Scratch per caller, B only'})
        out_b = host.place(app, KEY, changed, slot='slot-b')
        self.assertNotEqual(out_b['manifest_sha256'], out['manifest_sha256'])
        self.assertEqual(locker.held(hs['slot-a'].db, KEY, 'slot-a')['manifest_sha256'], out['manifest_sha256'])
        self.assertEqual(json.loads(self.bucket.objects[f'{KEY}/locker.json'])['manifest_sha256'], out['manifest_sha256'])
        self.assertEqual(json.loads(self.bucket.objects[f'slot-b/{KEY}/locker.json'])['manifest_sha256'], out_b['manifest_sha256'])
        fresh = self.make('fresh')   # another instance: each slot's copy from the bucket
        a, b = fresh.config['harnesses']['slot-a'], fresh.config['harnesses']['slot-b']
        self.assertEqual(fresh.config['held_from_bucket'], 2)
        self.assertNotIn('B only', answer_of(a, locker.held(a.db, KEY, 'slot-a')))
        self.assertIn('B only', answer_of(b, locker.held(b.db, KEY, 'slot-b')))

    def test_the_migration_command_copies_into_the_bucket(self):
        app = self.make()
        for h in app.config['harnesses'].values():
            h.client = Platform([])
        host.place(app, KEY, package(), slot='slot-a')
        top = dict(self.bucket.objects)
        got = host.lockers_copy(app, 'slot-b')
        self.assertEqual(got['bucket'], {'copied': [KEY], 'kept': []})
        self.assertEqual({k: v for k, v in self.bucket.objects.items() if not k.startswith('slot-b/')}, top)
        with self.assertRaises(SystemExit):
            host.lockers_copy(app, 'slot-a')   # the locker of before itself
        with self.assertRaises(SystemExit):
            host.lockers_copy(app, 'proof')   # no such slot here
        fresh = self.make('fresh')
        self.assertEqual(fresh.config['held_from_bucket'], 2)

    def test_the_night_s_check_says_every_caller_its_own_locker(self):
        """THE NIGHT'S CHECK (the owner 2026-11-22: "add ... the agent problem to the smoke test so this runs each night and wont happen
        again"): `lockers check` passes on the runtime as built, and fails the moment two callers share one locker or one folder."""
        app = self.make()
        for h in app.config['harnesses'].values():
            h.client = Platform([])
        host.place(app, KEY, package(), slot='slot-a')
        host.lockers_copy(app, 'slot-b')
        got = host.lockers_check(app)
        self.assertEqual((got['ok'], got['shared']), (True, []), got)
        self.assertEqual({c: v['held'] for c, v in got['lockers'].items()}, {'slot-a': 1, 'slot-b': 1})
        app.config['harnesses']['slot-b'].agents = app.config['harnesses']['slot-a'].agents   # as before 2026-11-22: one locker for both
        with mock.patch.object(locker, 'of', lambda caller='': ''):
            got = host.lockers_check(app)
        self.assertFalse(got['ok'])
        self.assertIn('slot-a, slot-b share one locker', got['shared'])
        self.assertIn('one folder held for slot-a, slot-b', got['shared'])

    def test_the_night_s_check_on_the_command_line(self):
        app = self.make()
        with mock.patch.object(host, 'create_app', lambda *a, **k: app), mock.patch.object(host, 'cloud_parts', lambda: None), \
                mock.patch('builtins.print') as said:
            host.main(['app.py', 'lockers', 'check'])
        self.assertTrue(json.loads(said.call_args[0][0])['ok'])
        app.config['harnesses']['slot-b'].agents = app.config['harnesses']['slot-a'].agents / 'inside'
        with mock.patch.object(host, 'create_app', lambda *a, **k: app), mock.patch.object(host, 'cloud_parts', lambda: None), \
                mock.patch('builtins.print'), self.assertRaises(SystemExit) as no:
            host.main(['app.py', 'lockers', 'check'])
        self.assertEqual(no.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
