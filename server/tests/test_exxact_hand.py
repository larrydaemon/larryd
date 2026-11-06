"""THE EXXACT HAND (core_engine/exxact_hand.py, CORE_CLEANUP_IV 97): an 'exxact/<type>' ask made through the missions and returns
buckets, never a real bucket, never the network, never the real box. Exxact_Loot's own code is copied unchanged (pinned here by sha256);
the end to end runs this runtime's hand against BucketLanes on Exxact_Loot's own FakeStore, with Exxact_Loot's own Runner on its own
FakeBox (~/virtual_sanity/exxact_loot/tests, read only) answering. The sealing needs `cryptography`: without it those tests are skipped
(run them with ~/larryd/.venv/bin/python)."""
import hashlib
import importlib.util
import pathlib
import re
import sys
import tempfile
import unittest

from _here import APP
from core_engine import exxact, exxact_hand, exxact_locker, harness, outside
from test_skills import ACCOUNT, JOB, KEY, MEMBER, World

LOOT = pathlib.Path.home() / 'virtual_sanity' / 'exxact_loot'
ORIGINALS = {   # THE PINS: Exxact_Loot's two files as copied (a change on either side is seen here first)
    'exxact.py': '6e087b084a86749c18532b4cb2f5d66464fbde62e41e22d42c1e4ffe9b9c21e7',   # Exxact_Loot 7ada929: names no address and no user
    'locker.py': '3674a52f362c85ff165fe2c19085c236844c94e80739a4f072bce7cadd65a026',
}
COPIES = {'exxact.py': 'exxact.py', 'locker.py': 'exxact_locker.py'}
# THE ONE CHANGE: the original reaches its locker by putting its own folder on sys.path; here that folder holds the runtime's own
# locker.py (and platform.py), which a sys.path entry would shadow, so the copy imports its neighbour exxact_locker as a package module
THE_IMPORT = ("    if HERE not in sys.path:\n        sys.path.insert(0, HERE)\n    import locker\n",
              "    from . import exxact_locker as locker\n")
try:
    import cryptography  # noqa: F401
    SEALS = True
except ImportError:
    SEALS = False

PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64
JPEG = b'\xff\xd8\xff\xe0' + b'\x00' * 64
SWAP = {'model': 'exxact/face-swap', 'prompt': 'swap the face', 'name': 'Swapped',
        'reference': ['DA-M_AAAAAAAAAAAA_0001', 'DA-M_AAAAAAAAAAAA_0002']}
ASKER = {'card': KEY, 'job_key': JOB, 'member': MEMBER}


def _loot_fakes():
    """Exxact_Loot's FakeStore (tests/test_cloud_lane.py), FakeBox (tests/fake_box.py) and its own exxact module (the box side's Runner),
    loaded from their files, read only; None when that folder is not on this machine."""
    if not (LOOT / 'tests' / 'test_cloud_lane.py').is_file():
        return None
    spec = importlib.util.spec_from_file_location('exxact_loot_test_cloud_lane', LOOT / 'tests' / 'test_cloud_lane.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)   # puts Exxact_Loot's _office and tests on sys.path, as its own tests do
    return module.FakeStore, sys.modules['fake_box'].FakeBox, sys.modules['exxact']


class ThePins(unittest.TestCase):
    @unittest.skipUnless((LOOT / '_office').is_dir(), 'Exxact_Loot is not on this machine')
    def test_the_originals_are_the_pinned_ones_and_the_copies_differ_only_by_the_import(self):
        here = APP / 'core_engine'
        for original, pin in ORIGINALS.items():
            raw = (LOOT / '_office' / original).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), pin, f'Exxact_Loot changed {original}: copy it again and pin it')
            want = raw.decode('utf-8')
            if original == 'exxact.py':
                self.assertEqual(want.count(THE_IMPORT[0]), 1)
                want = want.replace(*THE_IMPORT)
            self.assertEqual((here / COPIES[original]).read_text(encoding='utf-8'), want, COPIES[original])


class NoPrivateHost(unittest.TestCase):
    """WHAT SHIPS NAMES NO PRIVATE HOST (frost-05's ruling, 2026-11-06: the runtime's core_engine ships in the public larryd package
    and the Cloud Run image): no private IPv4 address (10/8, 172.16/12, 192.168/16), no box user (exx@) and no user's /home/<name> path in any
    code of the runtime's app or of the larryd package. 127.0.0.1 (this machine's own loopback) is not a private host."""
    PRIVATE = re.compile(r'(?<![\d.])(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})(?![\d.])|exx@|/home/[A-Za-z0-9_]')   # a home folder of a user (the doctor's own list of forbidden paths, '/home/|', is a rule, not a host)

    def test_no_shipped_file_names_a_private_host(self):
        shipped = [APP, APP.parents[2] / 'larryd']   # server/runtime/app and the larryd package
        found = []
        for root in shipped:
            for path in sorted(root.rglob('*.py')):
                if '.venv' in path.parts or '__pycache__' in path.parts:
                    continue
                for n, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
                    if self.PRIVATE.search(line):
                        found.append(f'{path.relative_to(APP.parents[2])}:{n}')
        self.assertEqual(found, [])


class TheList(unittest.TestCase):
    def test_one_model_per_type_built_from_its_list(self):
        self.assertEqual(sorted(m for m in outside.MODELS if m.startswith('exxact/')), sorted(f'exxact/{t}' for t in exxact.TYPES))
        self.assertIn('exxact', outside.PROVIDERS)
        for name, t in exxact.TYPES.items():
            spec = outside.MODELS[f'exxact/{name}']
            self.assertEqual((spec['provider'], spec['path'], spec['most_seconds']), ('exxact', name, t['most_seconds']))
            self.assertEqual(spec['references'], tuple(t['inputs']))
            self.assertEqual(spec['most_references'], len(t['inputs']))
            self.assertEqual(set(spec['first']), set(spec['choices']))
            self.assertTrue(all(spec['first'][f] in v for f, v in spec['choices'].items()))
        self.assertEqual(outside.MODELS['exxact/face-swap']['choices'], {'enhance': ('natural',)})

    def test_the_grammar_takes_a_good_ask_and_refuses_one_off_its_choices(self):
        ok = lambda ask: outside.check([ask], ('exxact/face-swap',))   # noqa: E731
        self.assertEqual(ok(SWAP), ([{**SWAP, 'enhance': 'natural'}], ''))
        for wrong in ({**SWAP, 'enhance': 'vivid'}, {**SWAP, 'target_box': [1, 2, 3, 4]}, {**SWAP, 'reference': SWAP['reference'] * 2},
                      {**SWAP, 'reference': ['https://example.com/a.png']}, {**SWAP, 'model': 'exxact/lips'}):
            self.assertEqual(ok(wrong)[0], [], wrong)
        self.assertEqual(outside.check([{'model': 'exxact/gpu-status', 'prompt': 'read', 'name': 'Cards', 'reference': 'DA-M_AAAAAAAAAAAA_0001'}],
                                       ('exxact/gpu-status',))[0], [])   # a type with no input slot takes no reference


class NotSetUp(unittest.TestCase):
    def test_a_hand_with_no_buckets_or_keys_refuses_in_fixed_words(self):
        ask = outside.check([SWAP], ('exxact/face-swap',))[0][0]
        self.assertEqual(exxact_hand.ExxactHand().make(ask, '', [JPEG, PNG], asker=ASKER), (None, 'NOT_MADE_EXXACT_NOT_SET_UP'))
        with tempfile.TemporaryDirectory() as d:
            no_keys = exxact_hand.ExxactHand(lanes=exxact.BucketLanes(object()), keys_dir=d)
            self.assertEqual(no_keys.make(ask, '', [JPEG, PNG], asker=ASKER), (None, 'NOT_MADE_EXXACT_NOT_SET_UP'))
        self.assertEqual(exxact_hand.ExxactHand().make({**ask, 'model': 'nano-banana-2'}, '', b''), (None, 'NOT_MADE_EXXACT_NOT_ON_THE_LIST'))


@unittest.skipUnless(SEALS, 'no `cryptography` in this python: the lockers cannot be sealed')
class TheRoad(unittest.TestCase):
    """the hand on BucketLanes(FakeStore()), Exxact_Loot's Runner on a FakeBox answering between two polls"""
    def setUp(self):
        fakes = _loot_fakes()
        if fakes is None:
            self.skipTest('Exxact_Loot is not on this machine')
        self.FakeStore, self.FakeBox, self.loot = fakes
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = pathlib.Path(d.name)
        self.mine, self.boxkeys = str(self.root / 'hand_keys'), str(self.root / 'box_keys')
        exxact_locker.trust(self.mine, exxact_locker.keys(self.boxkeys))   # the key ceremony, both halves
        exxact_locker.trust(self.boxkeys, exxact_locker.keys(self.mine))
        self.store = self.FakeStore()
        self.lanes = exxact.BucketLanes(self.store)
        self.now, self.slept = [0.0], []

    def hand(self, box=None):
        """box: a FakeBox's faults, its runner taking one pass at each poll's sleep; None: no box looks (the time runs out)"""
        runner = None if box is None else self.loot.Runner(self.lanes, self.boxkeys, str(self.root / 'state'), self.FakeBox(str(self.root / 'box'), **box))
        self.runner = runner

        def sleep(s):
            self.slept.append(s)
            self.now[0] += s
            if runner is not None:
                runner.once()
        return exxact_hand.ExxactHand(lanes=self.lanes, keys_dir=self.mine, sleep=sleep, clock=lambda: self.now[0])

    def swap(self, **more):
        return outside.check([{**SWAP, **more}], ('exxact/face-swap',))[0][0]

    def test_done_a_file_comes_back(self):
        made, why = self.hand({}).make(self.swap(), '', [JPEG, PNG], asker=ASKER)
        self.assertEqual((why, made), ('', {'name': 'Swapped.png', 'kind': 'png', 'data': PNG}))
        self.assertEqual(self.slept, [exxact_hand.EVERY_SECONDS])   # polled, never listened
        label = self.runner.label(next(iter(sorted((self.root / 'state' / 'labels').iterdir()))).stem)
        self.assertEqual((label['status'], label['asker']), ('DONE', {'runtime': 'external', **ASKER}))
        self.assertEqual({k: v for k, v in self.store.lanes['returns'].items() if k != 'heartbeat.json'}, {})   # taken home
        self.assertEqual(self.store.lanes['missions'], {})

    def test_red_comes_back_in_fixed_words(self):
        self.assertEqual(self.hand({'engine_makes_nothing': True}).make(self.swap(), '', [JPEG, PNG], asker=ASKER), (None, 'NOT_MADE_EXXACT_RUN'))
        self.assertEqual(self.hand({'gpus_unreadable': True}).make(self.swap(), '', [JPEG, PNG], asker=ASKER), (None, 'NOT_MADE_EXXACT_ROOM'))

    def test_a_type_with_no_file_gives_its_numbers(self):
        ask = outside.check([{'model': 'exxact/gpu-status', 'prompt': 'read the cards', 'name': 'Cards'}], ('exxact/gpu-status',))[0][0]
        made, why = self.hand({}).make(ask, '', [], asker=ASKER)
        self.assertEqual((why, made['name'], made['kind']), ('', 'Cards.json', 'json'))
        self.assertIn(b'"out"', made['data'])

    def test_time_up_takes_the_job_out_of_its_lane(self):
        made, why = self.hand(None).make(self.swap(), '', [JPEG, PNG], asker=ASKER)
        self.assertEqual((made, why), (None, 'NOT_MADE_EXXACT_TIME_UP'))
        self.assertGreaterEqual(self.now[0], outside.MODELS['exxact/face-swap']['most_seconds'])
        self.assertEqual(set(self.slept), {exxact_hand.EVERY_SECONDS})
        self.assertEqual(self.lanes.names('missions'), [])   # the box will find it gone

    def test_what_the_hand_refuses_before_anything_leaves(self):
        h = self.hand({})
        for picture, said in (([JPEG], 'NOT_MADE_EXXACT_REFERENCE_NOT_READ'),        # the ask names two, one was read
                              ([JPEG, b'<html>'], 'NOT_MADE_EXXACT_TAKEN')):         # not a kind the slot takes
            self.assertEqual(h.make(self.swap(), '', picture, asker=ASKER), (None, said))
        lips = outside.check([{'model': 'exxact/lips', 'prompt': 'lips', 'name': 'Lips', 'reference': 'DA-M_AAAAAAAAAAAA_0001'}], ('exxact/lips',))[0][0]
        self.assertEqual(h.make(lips, '', [b'RIFF\x24\x00\x00\x00WAVEfmt ' + b'\x00' * 64], asker=ASKER), (None, 'NOT_MADE_EXXACT_TAKEN'))   # its slots field is not on the grammar
        self.assertEqual(self.store.lanes['missions'], {})


class Fake:
    def __init__(self):
        self.asked = []

    def make(self, ask, key, picture=b'', **more):
        self.asked.append((ask['model'], key, more))
        return {'name': f"{ask['name']}.png", 'kind': 'png', 'data': PNG}, ''


class Platform:
    def __init__(self):
        self.said = []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        return 404, {'refused': 'no'}

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return 200, {'key': 'r8_vault_key'}


class TheDispatch(World):
    def test_the_hand_is_chosen_by_the_models_provider(self):
        replicate, box, p = Fake(), Fake(), Platform()
        h = harness.Harness(self.db, self.agents, p, hand=replicate, exxact=box)
        keyed = []
        h._provider_key = lambda provider, *a: keyed.append(provider) or 'r8_vault_key'
        exx = outside.check([{'model': 'exxact/face-swap', 'prompt': 'x', 'name': 'Swapped'}], ('exxact/face-swap',))[0][0]
        nano = outside.check([{'model': 'nano-banana-2', 'prompt': 'x', 'name': 'Fox'}], ('nano-banana-2',))[0][0]
        self.assertEqual([f['name'] for f in h._made([exx], KEY, JOB, 1, ACCOUNT, MEMBER)], ['Swapped.png'])
        self.assertEqual((box.asked, replicate.asked, keyed), ([('exxact/face-swap', '', {'asker': ASKER})], [], []))   # no vault key asked for the box
        self.assertEqual([f['name'] for f in h._made([nano], KEY, JOB, 1, ACCOUNT, MEMBER)], ['Fox.png'])
        self.assertEqual((replicate.asked, keyed), ([('nano-banana-2', 'r8_vault_key', {})], ['replicate']))
        self.assertEqual(h.records.sent_today(KEY, MEMBER), 2)   # each written down before it left

    def test_the_runtime_as_built_has_an_exxact_hand_not_set_up(self):
        p = Platform()
        h = harness.Harness(self.db, self.agents, p)
        self.assertIsInstance(h.hands['replicate'], outside.Hand)
        self.assertFalse(h.hands['exxact'].set_up())
        exx = outside.check([{'model': 'exxact/face-swap', 'prompt': 'x', 'name': 'Swapped'}], ('exxact/face-swap',))[0][0]
        with self.assertRaises(harness._Stop) as stop:
            h._made([exx], KEY, JOB, 1, ACCOUNT, MEMBER)
        self.assertEqual((stop.exception.state, stop.exception.reason), ('FAILED', 'not made, NOT_MADE_EXXACT_NOT_SET_UP'))
        self.assertNotIn('/jobs/provider_key', [r for _o, r, _d in p.said])


if __name__ == '__main__':
    unittest.main()
