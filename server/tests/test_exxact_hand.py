"""THE EXXACT HAND (core_engine/exxact_hand.py, CORE_CLEANUP_IV 97): an 'exxact/<type>' ask made through the missions and returns
buckets, never a real bucket, never the network, never the real box. Exxact_Loot's own code is copied unchanged (pinned here by sha256);
the end to end runs this runtime's hand against BucketLanes on Exxact_Loot's own FakeStore, with Exxact_Loot's own Runner on its own
FakeBox (~/virtual_sanity/exxact_loot/tests, read only) answering. The sealing needs `cryptography`: without it those tests are skipped
(run them with ~/larryd/.venv/bin/python)."""
import base64
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from _here import APP
from core_engine import exxact, exxact_hand, exxact_locker, harness, outside
from test_skills import ACCOUNT, JOB, KEY, MEMBER, World

LOOT = pathlib.Path.home() / 'virtual_sanity' / 'exxact_loot'
ORIGINALS = {   # THE PINS: Exxact_Loot's two files as copied (a change on either side is seen here first)
    'exxact.py': 'a631933909fb9e65ee8de914f47781c7c5978de81acbe084ee429472f79f511a',   # Exxact_Loot 1c55069: lanes as bucket/prefix (2538e2b), an unreachable box said (ssh 255)
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
WAV = b'RIFF\x24\x00\x00\x00WAVEfmt ' + b'\x00' * 64
MP4 = b'\x00\x00\x00\x18ftypmp42' + b'\x00' * 64
LIPS = {'model': 'exxact/lips', 'name': 'Lips', 'slots': [1, 2], 'reference': ['DA-M_AAAAAAAAAAAA_0001', 'DA-M_AAAAAAAAAAAA_0002', 'DA-M_AAAAAAAAAAAA_0003']}
SWAP = {'model': 'exxact/face-swap', 'prompt': 'swap the face', 'name': 'Swapped',
        'reference': ['DA-M_AAAAAAAAAAAA_0001', 'DA-M_AAAAAAAAAAAA_0002']}
ASKER = {'card': KEY, 'job_key': JOB, 'member': MEMBER}
MP3 = b'ID3\x04\x00' + b'\x00' * 64
ON = {'vol': 1, 'mute': False, 'solo': False}
SECRET = 'MEMBERS-OWN-WORDS'   # a value no refusal may carry


def _clip(source, track, at, out, gain=1, fade_in=0, fade_out=0, in_=0):
    return {'source': source, 'track': track, 'at': at, 'in': in_, 'out': out, 'gain': gain, 'fade_in': fade_in, 'fade_out': fade_out}


MIX = {'model': 'exxact/mix', 'name': 'Mix', 'tracks': [dict(ON) for _ in range(4)],
       'clips': [_clip(1, 'VOICE A', 0, 1), _clip(2, 'MUSIC', 1.5, 2, gain=0.5, fade_out=0.5), _clip(1, 'SFX', 2.5, 0.5, in_=0.25)],
       'reference': ['DA-M_AAAAAAAAAAAA_0001', 'DA-M_AAAAAAAAAAAA_0002']}


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
        for wrong in ({**SWAP, 'enhance': 'vivid'}, {**SWAP, 'target_box': [1, 2, 3, 4, 5]}, {**SWAP, 'reference': SWAP['reference'] * 2},
                      {**SWAP, 'reference': ['https://example.com/a.png']}, {**SWAP, 'model': 'exxact/lips'}):
            self.assertEqual(ok(wrong)[0], [], wrong)
        self.assertEqual(outside.check([{'model': 'exxact/gpu-status', 'prompt': 'read', 'name': 'Cards', 'reference': 'DA-M_AAAAAAAAAAAA_0001'}],
                                       ('exxact/gpu-status',))[0], [])   # a type with no input slot takes no reference


class TheNumbersAndTheWords(unittest.TestCase):
    """THE LIPS GAPS (2026-11-06): a number field is on the grammar within its range, as exxact.check_fields takes it; an Exxact ask needs
    no words; a refusal never carries the member's value."""
    def test_the_number_fields_are_copied_from_the_types_list(self):
        self.assertEqual(outside.MODELS['exxact/lips']['numbers'], {'slots': {'list_ints': (1, 8), 'most': 8}})
        self.assertEqual(outside.MODELS['exxact/face-swap']['numbers'], {'target_box': {'list_numbers': (0, 20000), 'most': 4, 'optional': True}})
        for name, t in exxact.TYPES.items():
            for field in outside.MODELS[f'exxact/{name}']['numbers']:
                self.assertIn(field, t['fields'])
        self.assertEqual([m for m in ('nano-banana-2', 'seedance-2.5', 'flux-krea', 'kling-2.5') if outside.MODELS[m]['numbers']], [])

    def test_lips_slots_in_range_is_taken_and_off_its_range_refused(self):
        ok = lambda ask: outside.check([ask], ('exxact/lips',))   # noqa: E731
        self.assertEqual(ok(LIPS), ([LIPS], ''))
        self.assertEqual(ok({**LIPS, 'slots': list(range(1, 9))})[1], '')
        for wrong in ([0], [9], [], list(range(1, 9)) + [1], [1.0], [True], ['1'], 1, '1', None, [-1], [10 ** 9], [1, None]):
            asks, why = ok({**LIPS, 'slots': wrong})
            self.assertEqual(asks, [], wrong)
            self.assertEqual(why, "the ask's slots is not a list of at most 8 whole numbers from 1 to 8")   # fixed words, never the value
        self.assertEqual(ok({k: v for k, v in LIPS.items() if k != 'slots'}), ([], 'the ask names no slots'))   # lips needs its slots
        for good in (LIPS, {**LIPS, 'slots': [8, 3]}):   # what the grammar takes, the box's own check takes
            self.assertEqual(exxact.check_fields('lips', {'slots': ok(good)[0][0]['slots']}), {'slots': good['slots']})

    def test_face_swap_target_box_in_range_is_taken_and_off_its_range_refused(self):
        ok = lambda ask: outside.check([ask], ('exxact/face-swap',))   # noqa: E731
        for good in ([0, 0, 20000, 20000], [10.5, 20, 300, 400.25], [1]):
            asks, why = ok({**SWAP, 'target_box': good})
            self.assertEqual((why, asks[0]['target_box']), ('', good))
            self.assertEqual(exxact.check_fields('face-swap', {'enhance': 'natural', 'target_box': good})['target_box'], good)
        self.assertNotIn('target_box', ok(SWAP)[0][0])   # optional: left out, left out
        for wrong in ([1, 2, 3, 4, 5], [], [-1, 0, 0, 0], [0, 0, 0, 20001], ['1', 2, 3, 4], [True, 2, 3, 4], [float('nan')], [float('inf')], (1, 2, 3, 4), '1,2,3,4', {'x': 1}):
            asks, why = ok({**SWAP, 'target_box': wrong})
            self.assertEqual((asks, why), ([], "the ask's target_box is not a list of at most 4 numbers from 0 to 20000"), wrong)

    def test_an_exxact_ask_needs_no_words_and_a_replicate_ask_still_does(self):
        no_words = {k: v for k, v in SWAP.items() if k != 'prompt'}
        asks, why = outside.check([no_words], ('exxact/face-swap',))
        self.assertEqual((why, 'prompt' in asks[0]), ('', False))
        self.assertEqual(outside.check([{'model': 'exxact/gpu-status', 'name': 'Cards'}], ('exxact/gpu-status',))[1], '')
        self.assertEqual(outside.check([{**SWAP, 'prompt': ''}], ('exxact/face-swap',))[0], [])   # words carried are checked the same
        self.assertEqual(outside.check([{'model': 'nano-banana-2', 'name': 'Fox'}], ('nano-banana-2',)), ([], 'the ask carries no words, or more than 4000 characters'))
        self.assertEqual(outside.check([{'model': 'seedance-2.5', 'name': 'Boat'}], ('seedance-2.5',))[0], [])
        self.assertEqual(outside.check([{'model': 'exxact/gpu-status'}], ('exxact/gpu-status',))[0], [])   # the made file's name: every model

    def test_a_number_field_is_a_field_of_its_own_model_only(self):
        self.assertEqual(outside.check([{**LIPS, 'target_box': [1, 2, 3, 4]}], ('exxact/lips',))[0], [])
        self.assertEqual(outside.check([{'model': 'nano-banana-2', 'prompt': 'x', 'name': 'X', 'slots': [1]}], ('nano-banana-2',))[0], [])


class TheMix(unittest.TestCase):
    """ROW 55'S MIX (Exxact_Loot 2bfc275): on the list from TYPES with its 16 source slots; its tracks and clips held to Exxact_Loot's own
    FIELD_CHECKS through the rule {'check': ...}; a refusal in fixed words that never carries the member's value; the made file capped."""
    def ok(self, ask):
        return outside.check([ask], ('exxact/mix',))

    def test_the_mix_is_on_the_list_with_sixteen_source_slots(self):
        spec = outside.MODELS['exxact/mix']
        self.assertEqual(spec['references'], tuple(f'source_{n}' for n in range(1, 17)))
        self.assertEqual(spec['most_references'], 16)
        self.assertEqual(spec['reference_rules'], ((('wav', 'mp3', 'mp4'), outside.MOST_ASK_REFERENCES),) * 16)
        self.assertEqual((spec['checks'], spec['numbers'], spec['choices'], spec['prompt'], spec['kind']),
                         ({'tracks': 'mix_tracks', 'clips': 'mix_clips'}, {}, {}, False, 'audio'))
        self.assertEqual({m: s['checks'] for m, s in outside.MODELS.items() if s['checks']}, {'exxact/mix': spec['checks']})   # no other model's grammar moved
        self.assertTrue(exxact.TYPES['mix']['inputs']['source_1']['need'])

    def test_a_good_mix_is_taken_as_the_box_takes_it(self):
        asks, why = self.ok(MIX)
        self.assertEqual((why, asks), ('', [MIX]))
        fields = {f: asks[0][f] for f in ('tracks', 'clips')}
        self.assertEqual(exxact.check_fields('mix', fields), fields)   # what the grammar takes, the box's own check takes
        sixteen = {**MIX, 'reference': [f'DA-M_AAAAAAAAAAAA_{n:04d}' for n in range(1, 17)], 'clips': [_clip(16, 'SFX', 0, 1)]}
        self.assertEqual(self.ok(sixteen)[1], '')

    def test_a_bad_mix_is_refused_in_fixed_words_without_its_value(self):
        bad = [({**MIX, 'tracks': MIX['tracks'][:3]}, "the ask's tracks is not in the shape Exxact mix takes"),
               ({**MIX, 'tracks': [{**ON, 'vol': SECRET}] * 4}, "the ask's tracks is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': [_clip(1, 'VOICE A', 0, 1, in_=1)]}, "the ask's clips is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': [_clip(1, 'VOICE A', 0, 1, in_=2)]}, "the ask's clips is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': [_clip(1, 'VOICE A', 0, 1, gain=4.5)]}, "the ask's clips is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': [{**_clip(1, 'VOICE A', 0, 1), 'cmd': SECRET}]}, "the ask's clips is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': [_clip(1, SECRET, 0, 1)]}, "the ask's clips is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': [_clip(1, 'VOICE A', 0, 1)] * 65}, "the ask's clips is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': SECRET}, "the ask's clips is not in the shape Exxact mix takes"),
               ({**MIX, 'clips': [_clip(3, 'VOICE A', 0, 1)]}, "the ask's clips name a source it does not send"),
               ({k: v for k, v in MIX.items() if k != 'reference'}, "the ask's clips name a source it does not send"),
               ({k: v for k, v in MIX.items() if k != 'tracks'}, 'the ask names no tracks'),
               ({**MIX, SECRET: 1}, 'the ask holds more than Exxact mix takes')]
        for ask, words in bad:
            with self.subTest(words=words):
                self.assertEqual(self.ok(ask), ([], words))
                self.assertNotIn(SECRET, words)

    def test_the_made_file_is_capped_at_one_asks_most(self):
        spec = outside.MODELS['exxact/mix']
        self.assertGreater(exxact.TYPES['mix']['outputs']['mix']['most'], outside.MOST_ASK_REFERENCES)
        self.assertEqual(spec['most_bytes'], outside.MOST_ASK_REFERENCES)
        self.assertTrue(all(s['most_bytes'] <= outside.MOST_ASK_REFERENCES for m, s in outside.MODELS.items() if m.startswith('exxact/')))
        ask = self.ok(MIX)[0][0]
        for size, want in ((1000, (None, exxact_hand.TOO_LARGE)), (10 ** 6, ({'name': 'Mix.wav', 'kind': 'wav', 'data': WAV + b'\x00' * 999}, ''))):
            hand = exxact_hand.ExxactHand(lanes=object(), keys_dir='k')
            with mock.patch.object(hand, 'set_up', lambda: True), mock.patch.object(hand, '_sweep', lambda: None), \
                    mock.patch.object(exxact, 'ask', lambda *a: 'JOB1') as _a, mock.patch.dict(spec, {'most_bytes': size}), \
                    mock.patch.object(exxact, 'collect', lambda *a, **k: ({'type': 'mix', 'state': 'DONE'}, {'mix': WAV + b'\x00' * 999})):   # collect takes most_bytes since b657a03
                self.assertEqual(hand.make(ask, '', [WAV, MP3], asker=ASKER), want, size)


class TheReferenceKinds(World):
    """THE REFERENCES BY KIND, PER MODEL (2026-11-06): the harness reads each DA-M reference and holds it to its slot's kinds (from its
    first bytes) and most bytes; Replicate's models keep png, jpg, webp within outside.MOST_REFERENCE."""
    def read(self, ask, contents):
        class Dam(Platform):
            def get(self, office, route, data=None, most=None):
                self.said.append((office, route, data))
                return 200, {'dam_key': data['dam_key'], 'content_b64': base64.b64encode(contents[data['dam_key']]).decode()}
        h = harness.Harness(self.db, self.agents, Dam())
        return h._reference(ask, ACCOUNT, '', MEMBER, JOB, 1)

    def refused(self, ask, contents):
        with self.assertRaises(harness._Stop) as stop:
            self.read(ask, contents)
        return stop.exception.reason

    def test_lips_takes_a_wav_and_an_mp4_on_its_slots(self):
        lips = outside.check([LIPS], ('exxact/lips',))[0][0]
        keys = LIPS['reference']
        self.assertEqual(self.read(lips, dict(zip(keys, (WAV, WAV, MP4)))), [WAV, WAV, MP4])
        self.assertIn('reference not a kind its slot takes', self.refused(lips, dict(zip(keys, (WAV, MP4, MP4)))))   # an mp4 on the second wav slot
        self.assertIn('reference not a kind its slot takes', self.refused(lips, dict(zip(keys, (PNG, WAV, MP4)))))
        self.assertEqual(outside.reference_kind(WAV, ('wav',)), 'wav')
        self.assertEqual(outside.reference_kind(WAV, ('png', 'jpg', 'webp')), '')   # wav sniffed only where its slot takes it
        self.assertEqual(outside.kind_of(WAV), '')

    def test_nano_banana_2_refuses_a_wav_and_an_mp4_as_before(self):
        key = 'DA-M_AAAAAAAAAAAA_0001'
        nano = outside.check([{'model': 'nano-banana-2', 'prompt': 'x', 'name': 'X', 'reference': key}], ('nano-banana-2',))[0][0]
        self.assertEqual(self.read(nano, {key: JPEG}), [JPEG])
        for data in (WAV, MP4):
            reason = self.refused(nano, {key: data})
            self.assertEqual(reason, f'not made, reference not a picture: {key}; nothing was sent')

    def test_an_mp3_is_taken_on_a_mix_slot_and_refused_by_nano_banana_2(self):
        mix = outside.check([MIX], ('exxact/mix',))[0][0]
        a, b = MIX['reference']
        self.assertEqual(self.read(mix, {a: MP3, b: WAV}), [MP3, WAV])
        self.assertEqual(self.read(mix, {a: b'\xff\xfb\x90\x00' + b'\x00' * 64, b: MP4})[1], MP4)   # an mp3 frame's sync, no tag; an mp4's sound
        self.assertIn('reference not a kind its slot takes', self.refused(mix, {a: PNG, b: WAV}))
        self.assertEqual((outside.reference_kind(MP3, ('wav', 'mp3', 'mp4')), exxact.kind_of(MP3)), ('mp3', 'mp3'))   # one reading: Exxact_Loot's
        key = 'DA-M_AAAAAAAAAAAA_0001'
        nano = outside.check([{'model': 'nano-banana-2', 'prompt': 'x', 'name': 'X', 'reference': key}], ('nano-banana-2',))[0][0]
        self.assertEqual(self.refused(nano, {key: MP3}), f'not made, reference not a picture: {key}; nothing was sent')

    def test_a_reference_over_its_slots_most_bytes_is_refused(self):
        key = 'DA-M_AAAAAAAAAAAA_0001'
        nano = outside.check([{'model': 'nano-banana-2', 'prompt': 'x', 'name': 'X', 'reference': key}], ('nano-banana-2',))[0][0]
        big = JPEG + b'\x00' * outside.MOST_REFERENCE
        self.assertEqual(self.refused(nano, {key: big}), f'not made, reference too large: {key} is over 10 MB; nothing was sent')
        swap = outside.check([SWAP], ('exxact/face-swap',))[0][0]
        a, b = SWAP['reference']
        fits = JPEG + b'\x00' * (outside.MOST_REFERENCE + 1)   # over Replicate's 10 MB, within face-swap's 20 MB slot
        self.assertEqual(self.read(swap, {a: fits, b: PNG}), [fits, PNG])
        over = JPEG + b'\x00' * (exxact.TYPES['face-swap']['inputs']['source']['most'])
        self.assertIn('reference too large', self.refused(swap, {a: over, b: PNG}))
        self.assertEqual([r for r in outside.MODELS['exxact/face-landmarks']['reference_rules']], [(('png', 'jpg'), 40 * 1024 * 1024)])


class NotSetUp(unittest.TestCase):
    def test_a_hand_with_no_buckets_or_keys_refuses_in_fixed_words(self):
        ask = outside.check([SWAP], ('exxact/face-swap',))[0][0]
        self.assertEqual(exxact_hand.ExxactHand().make(ask, '', [JPEG, PNG], asker=ASKER), (None, 'NOT_MADE_EXXACT_NOT_SET_UP'))
        with tempfile.TemporaryDirectory() as d:
            no_keys = exxact_hand.ExxactHand(lanes=exxact.BucketLanes(object()), keys_dir=d)
            self.assertEqual(no_keys.make(ask, '', [JPEG, PNG], asker=ASKER), (None, 'NOT_MADE_EXXACT_NOT_SET_UP'))
        self.assertEqual(exxact_hand.ExxactHand().make({**ask, 'model': 'nano-banana-2'}, '', b''), (None, 'NOT_MADE_EXXACT_NOT_ON_THE_LIST'))


@unittest.skipUnless(SEALS, 'no `cryptography` in this python: the lockers cannot be sealed')
class TheLanes(unittest.TestCase):
    """EXXACT_LOOT'S LANES INSIDE LARRYD'S OWN BUCKET (the owner 2026-11-06; frost-88 2538e2b): the hand's buckets are LANES, each
    'bucket/prefix'; every object it names is under its lane's prefix, and a name listed back comes without it. With no token the hand is
    still not set up (nothing reaches the cloud without the runtime's own token and the key ceremony)."""
    def test_the_lanes_are_larryds_bucket_under_exxact(self):
        self.assertEqual(exxact_hand.LANES, {'missions': 'larryd-runtime-lockers/exxact/missions', 'returns': 'larryd-runtime-lockers/exxact/returns'})
        store = exxact.GcsStore(exxact_hand.LANES, lambda: 'scratch-token')
        self.assertEqual(store._o('missions', 'J1/mission.json'),
                         exxact.GcsStore.API + 'larryd-runtime-lockers/o/' + 'exxact%2Fmissions%2FJ1%2Fmission.json')
        self.assertEqual(store._o('returns', 'J1/return.json'),
                         exxact.GcsStore.API + 'larryd-runtime-lockers/o/' + 'exxact%2Freturns%2FJ1%2Freturn.json')
        hand = exxact_hand.ExxactHand(token=lambda: 'scratch-token')
        self.assertEqual((hand.lanes.store.buckets, hand.lanes.store.prefix),
                         ({'missions': 'larryd-runtime-lockers', 'returns': 'larryd-runtime-lockers'}, {'missions': 'exxact/missions/', 'returns': 'exxact/returns/'}))
        self.assertFalse(hand.set_up())   # no keys: not set up, whatever the lanes
        self.assertIsNone(exxact_hand.ExxactHand().lanes)   # no token: no lanes at all
        for bad in ({'missions': '/', 'returns': 'b'}, {'missions': 'b/../x', 'returns': 'b'}):
            with self.assertRaises(ValueError):
                exxact.GcsStore(bad, lambda: 'scratch-token')

    def test_an_unreachable_box_is_a_red_of_its_own_step(self):
        self.assertEqual((exxact.UNREACHABLE, exxact.SSH_UNREACHABLE), ('the box could not be reached', 255))
        self.assertEqual((exxact_hand.red_words('ROOM'), exxact_hand.red_words('RUN')), ('NOT_MADE_EXXACT_ROOM', 'NOT_MADE_EXXACT_RUN'))   # the member's words stay by step


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

    def test_lips_its_slots_and_its_wav_and_mp4_reach_the_box_and_a_video_comes_back(self):   # the lips gaps closed (2026-11-06)
        lips = outside.check([LIPS], ('exxact/lips',))[0][0]
        made, why = self.hand({}).make(lips, '', [WAV, WAV, MP4], asker=ASKER)
        self.assertEqual((why, made['name'], made['kind']), ('', 'Lips.mp4', 'mp4'))
        self.assertEqual(made['data'][4:8], b'ftyp')

    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg is not on this computer: the mix kit runs it')
    def test_a_mix_its_sources_in_order_and_its_fields_reach_the_box_and_a_wav_comes_back(self):   # row 55, on Exxact_Loot's FakeBox with a real ffmpeg
        def tone(freq, seconds):
            return subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'sine=frequency={freq}:duration={seconds}:sample_rate=44100',
                                   '-ac', '1', '-c:a', 'pcm_s16le', '-f', 'wav', '-'], capture_output=True, check=True).stdout
        a, b = tone(440, 1), tone(660, 2)
        mix = outside.check([MIX], ('exxact/mix',))[0][0]
        hand, put = self.hand({}), {}
        box_put = self.runner.box.put
        self.runner.box.put = lambda job, rel, data: put.__setitem__(rel, data) or box_put(job, rel, data)   # what reached the box, kept to read
        made, why = hand.make(mix, '', [a, b], asker=ASKER)
        self.assertEqual((why, made['name'], made['kind']), ('', 'Mix.wav', 'wav'))
        self.assertEqual(made['data'][8:12], b'WAVE')
        self.assertGreater(len(made['data']), 3 * 48000 * 4)   # some 3.5 seconds of 48 kHz stereo, the clips laid at their starts
        self.assertEqual((put['in/source_1'], put['in/source_2']), (a, b))   # the references in the ask's order, source_1 first
        self.assertEqual(json.loads(put['mix.json']), {'tracks': MIX['tracks'], 'clips': MIX['clips']})   # the checked fields, as the kit reads them
        label = self.runner.label(next(iter(sorted((self.root / 'state' / 'labels').iterdir()))).stem)
        self.assertEqual(label['status'], 'DONE')

    def test_a_return_bigger_than_the_run_holds_is_refused_before_a_file_is_read(self):   # exxact_loot b657a03: collect(most_bytes)
        with mock.patch.object(outside, 'MOST_ASK_REFERENCES', len(PNG) - 1):   # the box's listed size passes what this RUN takes
            made, why = self.hand({}).make(self.swap(), '', [JPEG, PNG], asker=ASKER)
        self.assertEqual((made, why), (None, exxact_hand.TOO_LARGE))

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
        lips = outside.check([{'model': 'exxact/lips', 'name': 'Lips', 'slots': [1], 'reference': 'DA-M_AAAAAAAAAAAA_0001'}], ('exxact/lips',))[0][0]
        self.assertEqual(h.make(lips, '', [MP4], asker=ASKER), (None, 'NOT_MADE_EXXACT_TAKEN'))   # an mp4 on the vocals' wav slot
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

    def get(self, office, route, data=None, most=None):
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


class TheSizeFirst(unittest.TestCase):
    """THE SIZE FIRST (frost-05's ruling with the lips gaps, 2026-11-06): a reference file is never read whole before its size is
    known: wid's answer whose length says it is over the slot's most bytes is refused before a byte of it is read, and one that turns
    out over is refused at most + 1 bytes; the reference reader asks with exactly its slot's most (as base64, and the answer's words)."""
    class Answer:
        def __init__(self, body, length=None):
            self.status, self.body, self.reads = 200, body, []
            self.headers = {'Content-Length': str(length)} if length is not None else {}

        def read(self, n=-1):
            self.reads.append(n)
            return self.body if n < 0 else self.body[:n]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def client_answering(self, answer):
        from core_engine import platform
        c = platform.Client({'wid': 'http://wid.scratch'}, b'scratch-secret' * 3)
        c._headers = lambda route, data, at: {}
        return c, mock.patch('urllib.request.urlopen', lambda *a, **k: answer)

    def test_a_length_over_most_is_refused_before_a_byte_is_read(self):
        from core_engine import platform
        answer = self.Answer(b'{"content_b64": "' + b'A' * 4000 + b'"}', length=4020)
        c, patched = self.client_answering(answer)
        with patched:
            self.assertEqual(c.get('wid', '/jobs/file', {'dam_key': 'DA-M_000000000001_0001'}, most=1000), (413, {'refused': platform.TOO_LARGE}))
        self.assertEqual(answer.reads, [])   # not one byte read

    def test_an_answer_with_no_length_stops_at_most_plus_one(self):
        from core_engine import platform
        answer = self.Answer(b'{"content_b64": "' + b'A' * 4000 + b'"}')
        c, patched = self.client_answering(answer)
        with patched:
            self.assertEqual(c.get('wid', '/jobs/file', {}, most=1000), (413, {'refused': platform.TOO_LARGE}))
        self.assertEqual(answer.reads, [1001])   # never held whole
        small = self.Answer(b'{"content_b64": "QUJD"}', length=23)
        c, patched = self.client_answering(small)
        with patched:
            self.assertEqual(c.get('wid', '/jobs/file', {}, most=1000), (200, {'content_b64': 'QUJD'}))

    def test_the_reader_asks_with_its_slots_most_and_refuses_on_413(self):
        rules = outside.MODELS['exxact/lips']['reference_rules']
        asked = []

        class Client:
            def get(self, office, route, data=None, most=None):
                asked.append(most)
                return 413, {'refused': 'the answer is larger than this call may hold'}
        h = harness.Harness.__new__(harness.Harness)
        h.client = Client()
        with self.assertRaises(harness._Stop) as stopped:
            h._reference({'model': 'exxact/lips', 'reference': ['DA-M_000000000001_0001']}, 'ACCT_A', 'SCRATCH', 'MCON_M', 'MJOB_J', 1)
        self.assertIn('reference too large', str(stopped.exception.args))
        self.assertEqual(asked, [-(-rules[0][1] // 3) * 4 + harness.ANSWER_ROOM])


class TheAsksOwnMost(unittest.TestCase):
    """ONE ASK HOLDS AT MOST outside.MOST_ASK_REFERENCES of references together (a quarter of the RUN's 1 GiB, read as base64 and
    decoded): every Exxact slot is capped to it, and each next reference is asked only for what is left of it."""
    def test_every_exxact_slot_is_within_the_asks_most(self):
        for name, spec in outside.MODELS.items():
            for _kinds, most in spec['reference_rules']:
                self.assertLessEqual(most, max(outside.MOST_ASK_REFERENCES, outside.MOST_REFERENCE), name)

    def test_the_next_reference_is_asked_only_for_what_is_left(self):
        import base64 as b64
        asked = []
        first = b'RIFF' + b'\0' * 4 + b'WAVE' + b'\0' * 100   # a wav, 112 bytes

        class Client:
            def get(self, office, route, data=None, most=None):
                asked.append(most)
                return (200, {'content_b64': b64.b64encode(first).decode()}) if len(asked) == 1 else (413, {'refused': 'too large'})
        h = harness.Harness.__new__(harness.Harness)
        h.client = Client()
        with mock.patch.object(outside, 'MOST_ASK_REFERENCES', 1000):
            with self.assertRaises(harness._Stop):
                h._reference({'model': 'exxact/lips', 'reference': ['DA-M_000000000001_0001', 'DA-M_000000000002_0002']}, 'ACCT_A', 'SCRATCH', 'MCON_M', 'MJOB_J', 1)
        left = 1000 - len(first)
        self.assertEqual(asked[1], -(-left // 3) * 4 + harness.ANSWER_ROOM)   # only what is left of the ask
