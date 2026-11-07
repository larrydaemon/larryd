"""THE HANDOFF (core_engine/handoff.py, frost-05's ruling 2026-11-07): an input above Replicate's data-URL size goes as a signed GET URL
for ONE object under handoff/ in the lockers bucket, valid 60 minutes, deleted when the make ends (made, failed, timed out, broken);
the signed URL is a secret for its hour and is never written to a log, a run record, the hand's trace or a reason. Stand-ins only:
nothing leaves this process."""
import base64
import json
import logging
import re
import sqlite3
import unittest

from _here import APP  # noqa: F401
from core_engine import handoff, harness, outside, records
import test_outside as T
from test_outside import ASK, JPG, PNG, REF, SECRET_KEY, Provider, RefPlatform, hand
from test_skills import ACCOUNT, CARD, HIRED, JOB, MEMBER, SCOPE

World = T.World   # used as a base only: no test of test_outside is collected here

SIGNED = 'https://storage.googleapis.com/larryd-runtime-lockers/handoff/x?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Signature=SIGSECRET0001'
BIG = b'\xff\xd8\xff\xe0' + b'7' * (outside.DATA_URI_MOST)   # a picture whose data: address cannot fit


class Blob:
    def __init__(self, bucket, name):
        self.bucket, self.name = bucket, name

    def upload_from_string(self, data, content_type=None):
        self.bucket.objects[self.name] = (bytes(data), content_type)

    def delete(self):
        if self.bucket.broken:
            raise OSError('the bucket went away')
        self.bucket.objects.pop(self.name)
        self.bucket.deleted.append(self.name)


class Bucket:
    def __init__(self, broken=False):
        self.objects, self.deleted, self.broken = {}, [], broken

    def blob(self, name):
        return Blob(self, name)


def handed(bucket=None):
    return handoff.Handoff(bucket=bucket or Bucket(), signer=lambda blob: SIGNED)


class TheHandoffItself(unittest.TestCase):
    def test_put_writes_one_random_handoff_object_and_signs_it(self):
        b = Bucket()
        url, name = handed(b).put(JPG, 'image/jpeg')
        self.assertEqual(url, SIGNED)
        self.assertRegex(name, r'^handoff/[0-9a-f]{32}$')
        self.assertEqual(b.objects[name], (JPG, 'image/jpeg'))
        self.assertNotEqual(handed(b).put(JPG, 'image/jpeg')[1], name)   # a fresh token every time

    def test_drop_deletes_only_a_handoff_name_and_never_raises(self):
        b = Bucket()
        h = handed(b)
        _url, name = h.put(JPG, 'image/jpeg')
        self.assertTrue(h.drop(name))
        self.assertEqual(b.objects, {})
        for bad in ('agent.larryd', 'MAGT_0123456789AB_0001/locker.json', 'handoff/../x', '', None):
            self.assertFalse(h.drop(bad))
        b2 = Bucket(broken=True)
        h2 = handed(b2)
        _url, name2 = h2.put(JPG, 'image/jpeg')
        with self.assertLogs('runtime', level='WARNING') as logs:
            self.assertFalse(h2.drop(name2))
        self.assertIn(name2, logs.output[0])
        self.assertNotIn('Signature', logs.output[0])

    def test_the_signed_url_lives_60_minutes(self):
        self.assertEqual(handoff.MINUTES, 60)

    def test_a_laptop_or_a_test_has_no_handoff(self):
        self.assertIsNone(handoff.from_environment())


class TheHandHandsALargeInputOff(World):
    def hand_with(self, provider, bucket):
        h = hand(provider)
        h.handoff = handed(bucket)
        return h

    def ask(self, model='flux-krea'):
        return {**ASK, 'model': model, 'reference': [REF], 'aspect': '1:1'}

    def test_a_large_picture_goes_as_the_signed_url_and_is_deleted_when_made(self):
        p, b = Provider(), Bucket()
        made, why = self.hand_with(p, b).make(self.ask(), SECRET_KEY, BIG)
        self.assertEqual(why, '')
        self.assertNotIn('https://api.replicate.com/v1/files', [u for _m, u, _h, _d in p.asked])
        body = json.loads(next(d for m, u, _h, d in p.asked if m == 'POST' and u.endswith('/predictions')))
        self.assertEqual(body['input'][outside.MODELS['flux-krea']['reference']], SIGNED)
        self.assertEqual((len(b.deleted), b.objects), (1, {}))

    def test_deleted_when_failed_and_when_timed_out(self):
        for provider, said in ((Provider(state='failed', error='could not download'), 'Replicate failed'), (Provider(state='processing'), 'Replicate timed out')):
            b = Bucket()
            self.assertEqual(self.hand_with(provider, b).make(self.ask(), SECRET_KEY, BIG), (None, said))
            self.assertEqual((len(b.deleted), b.objects), (1, {}), said)

    def test_deleted_when_the_make_breaks(self):
        b = Bucket()
        h = self.hand_with(Provider(), b)
        h.poll = lambda *a: (_ for _ in ()).throw(RuntimeError('broken'))
        with self.assertRaises(RuntimeError):
            h.make(self.ask(), SECRET_KEY, BIG)
        self.assertEqual((len(b.deleted), b.objects), (1, {}))

    def test_an_input_that_cannot_be_handed_sends_nothing(self):
        p = Provider()
        h = hand(p)
        h.handoff = handoff.Handoff(bucket=Bucket(), signer=lambda blob: (_ for _ in ()).throw(OSError('no signing')))
        self.assertEqual(h.make(self.ask(), SECRET_KEY, BIG), (None, 'reference not handed'))
        self.assertEqual(p.asked, [])
        self.assertEqual(h.last['class'], 'unreachable')

    def test_a_small_picture_still_goes_inside_the_ask(self):
        b = Bucket()
        made, why = self.hand_with(Provider(), b).make(self.ask(), SECRET_KEY, PNG)
        self.assertEqual((why, b.objects, b.deleted), ('', {}, []))

    def test_two_references_both_deleted_when_the_second_cannot_go(self):
        b = Bucket()
        h = self.hand_with(Provider(), b)
        two = {**ASK, 'model': 'nano-banana-2', 'reference': [REF, REF]}
        made, why = h.make(two, SECRET_KEY, [BIG, b'<html>not a picture</html>'])
        self.assertTrue(why)
        self.assertEqual((len(b.deleted), b.objects), (1, {}))


class TheSignedUrlIsNeverWritten(World):
    def test_no_log_no_trace_no_reason_holds_it(self):
        b = Bucket()
        h = hand(Provider(state='failed', error='could not download ' + SIGNED))
        h.handoff = handed(b)
        logging.getLogger().setLevel(logging.DEBUG)
        with self.assertLogs(level='DEBUG') as logs:
            logging.getLogger('runtime').debug('a line so the capture is never empty')
            made, why = h.make({**ASK, 'model': 'flux-krea', 'reference': [REF]}, SECRET_KEY, BIG)
        for text in ('\n'.join(logs.output), json.dumps(h.last), why):
            self.assertNotIn('SIGSECRET0001', text)
            self.assertNotIn('X-Goog-Signature', text)

    def test_a_runs_records_never_hold_it(self):
        T.TheRun.placed(self, {**T.TheRun.ANSWER, 'makes': [{**ASK, 'reference': REF}]}, {'makes': ['nano-banana-2'], 'records': {'imgs': ['read', 'add']}},
                      ('makes', 'keeps', 'delivery'))
        b = Bucket()
        p = RefPlatform(content=BIG)
        h = harness.Harness(self.db, self.agents, p, hand=hand(Provider(state='failed', error='download ' + SIGNED)), a_day={'image': 25})
        h.hand.handoff = handed(b)
        h.facts = lambda account, scope, member: ([CARD], HIRED, [], lambda k: (True, ''))
        h.run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1)
        con = sqlite3.connect(self.db)
        rows = con.execute('SELECT * FROM runtime_runs').fetchall()
        con.close()
        self.assertTrue(rows)
        self.assertNotIn('SIGSECRET0001', json.dumps(rows))
        self.assertNotIn('SIGSECRET0001', json.dumps([d for _o, _r, d in p.said], default=str))
        self.assertEqual(b.objects, {})


if __name__ == '__main__':
    unittest.main()
