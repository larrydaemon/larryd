"""THE INDEPENDENT REVIEW'S FINDINGS, FIXED (frost-58's review of the LARRYD runtime, 2026-10-06):
H1 the run records in Firestore and the lockers from the bucket, nothing that must outlive an instance on its own disk;
H2 the calls back INTO the platform signed in the hardened scheme with the runtime's own key, and no start without it;
H3 no thread after a 202: a long run is claimed once and started as its own Cloud Run job;
H4 the start-up catch-up claims each queued run once across instances;
M1 every mounted version of a caller's key accepted during the overlap; M4 the body cap on the bytes actually read."""
import datetime
import io
import json
import pathlib
import re
import secrets
import shutil
import tempfile
import threading
import unittest
import zipfile

from _here import APP
from core_engine import callers, jobs, locker, lockers as bucket_lockers, platform, records as run_records, signing
from web import app as host


class Exists(Exception):
    pass


class FakeDoc:
    def __init__(self, store, key):
        self.store, self.key = store, key

    def create(self, data):
        with self.store.lock:
            if self.key in self.store.docs:
                raise Exists(self.key)
            self.store.docs[self.key] = dict(data)


class FakeSnap:
    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return dict(self.data)


class FakeCollection:
    """A Firestore collection, as much of it as the runtime uses: document(id).create() refusing an id that exists,
    where(...) and stream()."""
    def __init__(self, docs=None, filters=()):
        self.docs = {} if docs is None else docs
        self.filters, self.lock = filters, threading.Lock()

    def document(self, key):
        return FakeDoc(self, key)

    def where(self, field_path, op_string, value):
        view = FakeCollection(self.docs, self.filters + ((field_path, value),))
        view.lock = self.lock
        return view

    def stream(self):
        return [FakeSnap(d) for d in list(self.docs.values()) if all(d.get(f) == v for f, v in self.filters)]


class FakeBlob:
    def __init__(self, bucket, name):
        self.bucket, self.name = bucket, name

    def upload_from_string(self, data, content_type=None):
        self.bucket.objects[self.name] = data.encode('utf-8') if isinstance(data, str) else data

    def download_as_bytes(self):
        return self.bucket.objects[self.name]


class FakeBucket:
    def __init__(self):
        self.objects = {}

    def blob(self, name):
        return FakeBlob(self, name)

    def list_blobs(self):
        return [FakeBlob(self, n) for n in sorted(self.objects)]


MARKET = 'MAGT_00000000AA01_0001'


def marketplace_package():
    """The image's own marketplace agent as one approved .larryd file, and its locker hashes."""
    folder = APP / 'agents' / 'marketplace'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for f in sorted(folder.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:
                z.write(f, f.relative_to(folder).as_posix())
    tmp = tempfile.TemporaryDirectory()
    root = pathlib.Path(tmp.name)
    shutil.copytree(folder, root / 'm', ignore=shutil.ignore_patterns('__pycache__'))
    row = {'name': json.loads((folder / 'agent.json').read_text())['name'], 'code_sha256': locker._code_sha256(root / 'm'),
           'manifest_sha256': locker._manifest_sha256(root / 'm')}
    tmp.cleanup()
    return buf.getvalue(), row


class CloudApp(unittest.TestCase):
    """A Cloud Run runtime built with fakes for Firestore, the bucket and the job starter."""
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.dir.name)
        self.keys_dir, self.out_dir = base / 'keys', base / 'out'
        self.keys = {}
        for slot in ('slot-a', 'slot-b'):
            (self.keys_dir / slot).mkdir(parents=True)
            self.keys[slot] = secrets.token_hex(32)
            (self.keys_dir / slot / 'v1').write_text(self.keys[slot])
            (self.out_dir / slot).mkdir(parents=True)
            (self.out_dir / slot / 'v1').write_text(secrets.token_hex(32))
        self.runs, self.claims_col, self.bucket, self.started = FakeCollection(), FakeCollection(), FakeBucket(), []
        self.now = datetime.datetime.now(datetime.timezone.utc)

    def tearDown(self):
        self.dir.cleanup()

    def starter(self):
        test = self

        class Starter:
            def start(self, args):
                test.started.append(list(args))
                return True
        return Starter()

    def make(self, name='instance', with_outbound=True):
        inst = pathlib.Path(self.dir.name) / name
        inst.mkdir(exist_ok=True)
        cloud = {'outbound': callers.Outbound(self.out_dir) if with_outbound else None,
                 'records': run_records.FirestoreRecords(col=self.runs), 'lockers': bucket_lockers.BucketLockers(bucket=self.bucket),
                 'claims': jobs.FirestoreClaims(col=self.claims_col, exists=Exists), 'jobs': self.starter()}
        return host.create_app(str(inst), secret='', now=lambda: self.now, keys=callers.Keys(self.keys_dir), nonces=callers.MemoryNonces(),
                               agents=inst / 'agents', cloud=cloud)

    def call(self, app, route, data=None, method='GET', slot='slot-a'):
        data, at = data or {}, self.now.isoformat(timespec='seconds')
        nonce = secrets.token_hex(16)
        headers = {'X-Office-Key': slot, 'X-Office-At': at, 'X-Office-Nonce': nonce,
                   'X-Office': signing.sign_hardened(self.keys[slot], route, data, at, nonce)}
        c = app.test_client()
        return c.get('/api' + route, query_string=data, headers=headers) if method == 'GET' else c.post('/api' + route, json=data, headers=headers)


class H1RecordsAndLockers(CloudApp):
    def test_a_runs_record_is_in_firestore_and_survives_a_fresh_instance(self):
        app = self.make('one')
        app.config['harnesses']['slot-a']._record('call', 'AGNT_000000000001_0001', 'REFUSED', 'scratch', account='ACCT_00000000000A_000A', member='MCON_00000000000B_000B')
        fresh = self.make('two')   # another instance: nothing of the first one's disk
        self.assertEqual(fresh.config['records'].count('AGNT_000000000001_0001', 'call'), 1)
        doc = next(iter(self.runs.docs.values()))
        self.assertEqual((doc['caller'], doc['account'], doc['member'], doc['state']), ('slot-a', 'ACCT_00000000000A_000A', 'MCON_00000000000B_000B', 'REFUSED'))
        self.assertGreater(doc['expire_at'] - doc['started_at'], datetime.timedelta(days=390))   # kept 13 months

    def test_a_record_with_any_other_field_is_refused(self):
        """The security review (2026-10-06): the design's fields only, an allow list on write."""
        records = run_records.FirestoreRecords(col=self.runs)
        for extra in ({'input': 'what the run was handed'}, {'output': 'x'}, {'nonce': 'n'}, {'headers': {}}):
            with self.assertRaises(ValueError):
                records.record('call', 'AGNT_000000000001_0001', 'DONE', **extra)
        for bad in ({'account': 'jane@example.com'}, {'member': 'Jane Doe'}, {'caller': 'evil'}, {'egress_refused': ['http://x/y?q=1']}):
            with self.assertRaises(ValueError):
                records.record('call', 'AGNT_000000000001_0001', 'DONE', **bad)
        self.assertEqual(self.runs.docs, {})
        records.record('call', 'AGNT_000000000001_0001', 'REFUSED', egress_refused=['example.com'])
        self.assertEqual(tuple(next(iter(self.runs.docs.values()))), run_records.FirestoreRecords.FIELDS)

    def test_an_error_carrying_data_is_kept_as_its_code_only(self):
        records = run_records.FirestoreRecords(col=self.runs)
        records.record('job', 'AGNT_000000000001_0001', 'FAILED', "LARRYD could not read the platform: the member's notes say 'secret plan'")
        doc = next(iter(self.runs.docs.values()))
        self.assertEqual(doc['error_code'], 'LARRYD_COULD_NOT_READ_THE_PLATFORM')
        self.assertNotIn('secret', json.dumps(doc, default=str))

    def test_the_lockers_come_from_the_bucket_verified(self):
        package, row = marketplace_package()
        bucket_lockers.BucketLockers(bucket=self.bucket).publish(MARKET, row, package, role='marketplace')
        app = self.make()
        self.assertEqual(app.config['held_from_bucket'], 1)
        health = json.loads(self.call(app, '/health').data)
        self.assertEqual((health['locker'], health['runs']), (1, 'firestore'))
        self.assertEqual(app.config['harness'].marketplace_key(), MARKET)

    def test_a_locker_whose_files_are_not_what_was_approved_is_not_held(self):
        package, row = marketplace_package()
        bucket_lockers.BucketLockers(bucket=self.bucket).publish(MARKET, {**row, 'code_sha256': '0' * 64}, package, role='marketplace')
        with self.assertLogs('runtime', level='ERROR'):
            app = self.make()
        self.assertEqual(app.config['held_from_bucket'], 0)
        self.assertEqual(json.loads(self.call(app, '/health').data)['locker'], 0)


class H2Outbound(CloudApp):
    def test_the_runtime_does_not_start_without_its_outbound_key(self):
        with self.assertRaises(SystemExit):
            self.make(with_outbound=False)

    def test_a_call_back_to_a_slot_is_signed_in_the_hardened_scheme(self):
        sent = []

        class Answer:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self, *a):
                return b'{}'

        def opener(req, timeout=None):
            sent.append(req)
            return Answer()
        client = platform.Client({'wid': 'https://slot.example/wid'}, '', outbound=callers.Outbound(self.out_dir), slot='slot-a')
        orig = platform.urllib.request.urlopen
        platform.urllib.request.urlopen = opener
        try:
            client.post('wid', '/jobs/result', {'a': 1})
            client.post('wid', '/jobs/result', {'a': 1})
        finally:
            platform.urllib.request.urlopen = orig
        h = [dict(r.header_items()) for r in sent]
        get = lambda d, k: next(v for kk, v in d.items() if kk.lower() == k.lower())  # noqa: E731
        key = (self.out_dir / 'slot-a' / 'v1').read_text()
        for d in h:
            self.assertEqual(get(d, 'X-Office-Key'), 'runtime-to-slot-a')
            self.assertRegex(get(d, 'X-Office-Nonce'), r'^[0-9a-f]{32}$')
            self.assertEqual(get(d, 'X-Office'), signing.sign_hardened(key, '/jobs/result', {'a': 1}, get(d, 'X-Office-At'), get(d, 'X-Office-Nonce')))
        self.assertNotEqual(get(h[0], 'X-Office-Nonce'), get(h[1], 'X-Office-Nonce'))

    def test_nothing_is_ever_signed_with_an_empty_key(self):
        with self.assertRaises(ValueError):
            signing.sign('', '/x', {}, 'at')
        status, body = platform.Client({'wid': 'https://slot.example/wid'}, '').get('wid', '/agnt/cards')
        self.assertEqual(status, 0)
        self.assertIn('no key', body['refused'])


class H3H4Jobs(CloudApp):
    def test_a_long_run_is_claimed_once_and_started_as_a_job_never_a_thread(self):
        app = self.make()
        before = threading.active_count()
        d = {'account': 'ACCT_00000000000A_000A', 'scope': 'S', 'member': 'MCON_00000000000B_000B', 'job_key': 'MJOB_000000000001_0001', 'run': '3'}
        r = self.call(app, '/jobs/run', d, 'POST')
        self.assertEqual((r.status_code, json.loads(r.data)['already']), (202, False))
        self.assertEqual(self.started, [['job', 'slot-a', 'ACCT_00000000000A_000A', 'S', 'MCON_00000000000B_000B', 'MJOB_000000000001_0001', '3']])
        self.assertEqual(threading.active_count(), before)              # nothing runs here after the answer
        self.assertIsNotNone(app.config['slot'].take())                 # and the slot is free
        r = self.call(self.make('another'), '/jobs/run', d, 'POST')    # the same run, sent to another instance
        self.assertTrue(json.loads(r.data)['already'])
        self.assertEqual(len(self.started), 1)

    def test_the_catch_up_on_two_new_instances_starts_a_queued_run_once(self):
        queued = {'jobs': [{'account': 'ACCT_00000000000A_000A', 'scope': 'S', 'member': 'MCON_00000000000B_000B', 'job_key': 'MJOB_00000000000A_000A', 'run': 1}]}
        for name in ('one', 'two'):
            app = self.make(name)
            for h in app.config['harnesses'].values():
                h.client.get = lambda office, route, data=None: (200, queued)
            host.catch_up(app)
        self.assertEqual(len(self.started), 1)


class M1Versions(CloudApp):
    def test_both_versions_are_accepted_during_the_overlap_and_the_old_one_stops_after(self):
        tick = [0.0]
        keys = callers.Keys(self.keys_dir, clock=lambda: tick[0])
        old = self.keys['slot-a']
        new = secrets.token_hex(32)
        (self.keys_dir / 'slot-a' / 'v2').write_text(new)
        known = keys.now()
        at = self.now.isoformat(timespec='seconds')
        for secret in (old, new):
            nonce = secrets.token_hex(16)
            self.assertTrue(signing.good_hardened(known, 'slot-a', '/health', {}, at, nonce,
                                                  signing.sign_hardened(secret, '/health', {}, at, nonce), self.now, 60, lambda n: True))
        (self.keys_dir / 'slot-a' / 'v1').unlink()   # the old version destroyed: no longer mounted
        tick[0] += 61
        nonce = secrets.token_hex(16)
        self.assertFalse(signing.good_hardened(keys.now(), 'slot-a', '/health', {}, at, nonce,
                                               signing.sign_hardened(old, '/health', {}, at, nonce), self.now, 60, lambda n: True))


class M4ChunkedCap(CloudApp):
    def test_an_oversize_chunked_body_is_refused_on_the_bytes_read(self):
        app = self.make()
        at, nonce = self.now.isoformat(timespec='seconds'), secrets.token_hex(16)
        big = b'{"pad": "' + b'x' * (host.MAX_BODY + 10) + b'"}'
        headers = {'X-Office-Key': 'slot-a', 'X-Office-At': at, 'X-Office-Nonce': nonce, 'X-Office': '0' * 64,
                   'Content-Type': 'application/json', 'Transfer-Encoding': 'chunked'}
        r = app.test_client().open('/api/jobs/run', method='POST', input_stream=io.BytesIO(big), headers=headers,
                                   environ_overrides={'wsgi.input_terminated': True})
        self.assertEqual(r.status_code, 413)


if __name__ == '__main__':
    unittest.main()
