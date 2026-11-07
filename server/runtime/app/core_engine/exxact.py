"""EXXACT_LOOT: THE ONE DOOR TO THE EXXACT BOX (CORE_CLEANUP_IV items 86, 87; the owner 2026-11-06: "PF_Loot and Exxact_Loot", "we should
have somethign just for this not mixed", "it seems like a more clean way to have all exxact traffic go through this one point right?").

Every job for the box, from an internal agent or an external one, takes this one road; no agent reaches the box by itself. This file is the
only code that reaches the box (SshBox, LocalBox): a test fails when any agent file elsewhere names it. Where the box is lives only in the
box side's own config (box_config), never here: this file is copied into LARRYD's runtime, which ships in public.

THE LAW (pf Loot's, ~/virtual_sanity/pf_loot/_office/away.py; Exxact_Loot's own locker.py, lanes, keys and types, never mixed with pf Loot's):
- The asker never reaches the box. It SEALS a mission (signed by the asker's side, sealed to the box side) into the MISSIONS lane.
- The box side (box/runner.py) dials OUT to the lanes, never the other way: the box has no inbound door (the owner 2026-10-06).
- A mission names its files by sha256 and carries one random file key; each file travels beside it, encrypted with that key. So a lane
  that is read or changed can neither read nor forge a job.
- Each job is one TYPE on the list below: its fields and their choices, its input slots and their kinds, its GPU lane and the room it needs,
  its one fixed run (an engine call on the box's own 127.0.0.1, or a fixed command: never a string from a mission), its outputs.
- Every step is stamped on the job's label: TAKEN, ROOM, SENT, RUN, HOME, then DONE or RED. A RED stops where it broke, says why in fixed
  words, comes back sealed like a DONE, and the job's folders are wiped on the box and here.

THE JOB SHAPE (the same for an internal asker and an external one, so the cloud half plugs in unchanged):
  {"v": 1, "job": "JOB-<12 hex>-<4 hex>", "type": "<a type>", "asker": {"runtime": "internal" | "external", "card": "MAGT_...", "job_key": "...",
   "member": "..."}, "fields": {...}, "files": [{"slot": "<slot>", "sha256": "...", "bytes": n}], "file_key": "<fernet key>", "asked_at": "<iso>"}
THE RETURN: {"v": 1, "job", "type", "state": "DONE" | "RED", "step": "<where it stopped>", "why": "<fixed words>", "hops": [...], "said": {...},
  "files": [{"slot", "sha256", "bytes", "kind"}], "file_key"}

Stdlib, and `cryptography` through locker.py for the lockers (the runner's python and the asker's hand; the placed Exxact_Loot agent never
seals or opens anything: it reads the labels)."""
import base64
import datetime
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
KITS = os.path.join(REPO, 'box', 'kits')
VERSION = 1
LOCKER_KIND_MISSION, LOCKER_KIND_RETURN = 'exxact-mission', 'exxact-return'
STEPS = ('TAKEN', 'ROOM', 'SENT', 'RUN', 'HOME')
RUNTIMES = ('internal', 'external')


def _away():
    """Exxact_Loot's own locker (_office/locker.py: pf Loot's construction, its own label; never pf Loot's lockers)"""
    from . import exxact_locker as locker
    return locker


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


class Red(Exception):
    """A RED: the step it stopped at and LARRYD's own fixed words (never outside text)."""
    def __init__(self, step, why):
        super().__init__(f'{step}: {why}')
        self.step, self.why = step, why


class Wait(Exception):
    """Not a RED: the box is busy (a lane or its room); the job stays queued with its position."""


# ── THE KINDS (read from a file's first bytes, never its name) ──────────────────────────────────────────────────────

def kind_of(data):
    head = data[:16]
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if head.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    if head[4:8] == b'ftyp':
        return 'mp4'
    if head.startswith(b'RIFF') and head[8:12] == b'WAVE':
        return 'wav'
    if head.startswith(b'ID3') or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE6 in (0xE2, 0xE4, 0xE6)):   # an mp3: its tag, or a frame's sync and layer III
        return 'mp3'
    if head.startswith(b'{') or head.startswith(b'['):
        return 'json'
    return ''


# ── THE LIST: every job type the box takes ───────────────────────────────────────────────────────────────────────────
# Each type: lane (gpu0, gpu1, both, none), room (MiB free it needs on its lane's card; 0 = not measured yet, any free card),
# fields {name: {'choices': (...)} | {'ints': (low, high), 'most': n} | {'list_ints': (low, high), 'most': n}}, inputs {slot: kinds, most bytes,
# need}, kit (box/kits/<name>: files laid in the job's folder), run (one fixed run), outputs, most_seconds.

MB = 1024 * 1024
LIPS_SLOTS = range(1, 9)
MIX_SOURCES = range(1, 17)                                  # a mix's sources: up to 16 audio files, named by number in its clips
MIX_TRACKS = ('VOICE A', 'VOICE B', 'MUSIC', 'SFX')         # LARRY 5's four tracks (pf Soundtrack's TRACKS)
MIX_MOST_CLIPS, MIX_MOST_SECONDS = 64, 3600                 # LARRY 5's bounds: 64 clips; a timeline of at most an hour
TYPES = {
    'gpu-status': {
        'about': 'the two GPUs: memory used and free on each card, read once (nvidia-smi); runs nothing',
        'lane': 'none', 'room': 0, 'fields': {}, 'inputs': {}, 'kit': '',
        'run': {'command': ['nvidia-smi', '--query-gpu=index,memory.used,memory.total', '--format=csv,noheader,nounits']},
        'outputs': {}, 'most_seconds': 30,
    },
    'face-swap': {
        'about': 'one face onto one picture: the source face laid on the target face (the box\'s face-swap worker, port 5036)',
        'lane': 'gpu0', 'room': 0,
        'fields': {'enhance': {'choices': ('natural',)}, 'target_box': {'list_numbers': (0, 20000), 'most': 4, 'optional': True}},
        'inputs': {'source': {'kinds': ('png', 'jpeg'), 'most': 20 * MB, 'need': True}, 'target': {'kinds': ('png', 'jpeg'), 'most': 20 * MB, 'need': True}},
        'kit': '', 'run': {'http': 5036, 'path': '/generate'},
        'outputs': {'picture': {'kinds': ('png', 'jpeg'), 'most': 40 * MB}}, 'most_seconds': 600,
    },
    'face-landmarks': {
        'about': 'every face in one picture: its box and its five points, as fractions (the box\'s face-swap worker, port 5036); numbers only come back',
        'lane': 'gpu0', 'room': 0, 'fields': {},
        'inputs': {'image': {'kinds': ('png', 'jpeg'), 'most': 40 * MB, 'need': True}},
        'kit': '', 'run': {'http': 5036, 'path': '/landmarks'}, 'outputs': {}, 'most_seconds': 300,
    },
    'lips': {
        'about': 'the lips on baked movement (F-0004): each ON slot\'s mouth made to the vocals (PF Lip-sync, port 5060) and laid back on its clip',
        'lane': 'gpu1', 'room': 0,
        'fields': {'slots': {'list_ints': (1, 8), 'most': 8}},
        'inputs': {'minute_vocals': {'kinds': ('wav',), 'most': 200 * MB, 'need': True, 'as': 'minute_vocals.wav'},
                   'minute_voice': {'kinds': ('wav',), 'most': 200 * MB, 'need': False, 'as': 'minute_voice.wav'},
                   **{f'move_{n}': {'kinds': ('mp4',), 'most': 1024 * MB, 'need': False, 'as': f'slot_{n}/move.mp4'} for n in LIPS_SLOTS}},
        'kit': 'lips', 'run': {'detached': ['python3', 'lipsrun.py'], 'status': 'status.json', 'done': 'done', 'poll': 30},
        'outputs': {**{f'lips_{n}': {'kinds': ('mp4',), 'most': 1024 * MB, 'from': f'slot_{n}/lips.mp4', 'optional': True} for n in LIPS_SLOTS}},
        'most_seconds': 6 * 3600,
    },
    'mix': {
        'about': 'the mixdown of a soundtrack (row 55, LARRY 5\'s EXPORT): each clip trimmed, its gain and fades, set at its start, the four '
                 'tracks\' volume, mute and solo, mixed to one wav with ffmpeg (box/kits/mix); CPU only',
        'lane': 'none', 'room': 0,
        'fields': {'tracks': {'check': 'mix_tracks'}, 'clips': {'check': 'mix_clips'}},
        'inputs': {f'source_{n}': {'kinds': ('wav', 'mp3', 'mp4'), 'most': 300 * MB, 'need': n == 1} for n in MIX_SOURCES},
        'kit': 'mix', 'fields_as': 'mix.json', 'run': {'command': ['python3', 'mixrun.py']},
        'outputs': {'mix': {'kinds': ('wav',), 'most': 1024 * MB, 'from': 'out/mix.wav'}},
        'most_seconds': 1800,
    },
}


# THE BOX'S ENGINES a type needs up before its run: its port, its folder under the engines' root, its fixed start (agent003's swap_up did this
# for the face-swap worker; now only Exxact_Loot does)
ENGINES = {
    'faceswap': {'port': 5036, 'health': '/health', 'folder': 'faceswap', 'start': ['venv/bin/python', 'worker.py'], 'log': 'logs/worker.log', 'wait': 120},
}
for _t in ('face-swap', 'face-landmarks'):
    TYPES[_t]['engine'] = 'faceswap'


def _n(x, lo, hi):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x and lo <= x <= hi


def _mix_tracks(v):
    """the four tracks, in order: {vol 0..2, mute, solo} each"""
    return (isinstance(v, list) and len(v) == len(MIX_TRACKS)
            and all(isinstance(t, dict) and set(t) == {'vol', 'mute', 'solo'} and _n(t['vol'], 0, 2)
                    and isinstance(t['mute'], bool) and isinstance(t['solo'], bool) for t in v))


def _mix_clips(v):
    """1..64 clips: {source 1..16, track, at, in, out (in < out), gain 0..4, fade_in, fade_out 0..30}, seconds"""
    keys = {'source', 'track', 'at', 'in', 'out', 'gain', 'fade_in', 'fade_out'}
    return (isinstance(v, list) and 0 < len(v) <= MIX_MOST_CLIPS
            and all(isinstance(c, dict) and set(c) == keys and isinstance(c['source'], int) and not isinstance(c['source'], bool)
                    and c['source'] in MIX_SOURCES and c['track'] in MIX_TRACKS and _n(c['at'], 0, MIX_MOST_SECONDS)
                    and _n(c['in'], 0, MIX_MOST_SECONDS) and _n(c['out'], 0, MIX_MOST_SECONDS) and c['in'] < c['out']
                    and _n(c['gain'], 0, 4) and _n(c['fade_in'], 0, 30) and _n(c['fade_out'], 0, 30) for c in v))


FIELD_CHECKS = {'mix_tracks': _mix_tracks, 'mix_clips': _mix_clips}


def check_fields(kind, fields):
    """-> the fields as the type takes them; Red('TAKEN', ...) on anything not on the type's list"""
    t = TYPES[kind]
    if not isinstance(fields, dict):
        raise Red('TAKEN', 'the fields are not an object')
    extra = set(fields) - set(t['fields'])
    if extra:
        raise Red('TAKEN', 'a field the type does not take')
    out = {}
    for name, rule in t['fields'].items():
        if name not in fields:
            if rule.get('optional'):
                continue
            raise Red('TAKEN', f'the field {name} is missing')
        v = fields[name]
        if 'choices' in rule and v not in rule['choices']:
            raise Red('TAKEN', f'the field {name} is not one of its choices')
        if 'list_numbers' in rule:
            lo, hi = rule['list_numbers']
            if not (isinstance(v, list) and 0 < len(v) <= rule['most'] and all(isinstance(x, (int, float)) and not isinstance(x, bool) and lo <= x <= hi for x in v)):
                raise Red('TAKEN', f'the field {name} is not a short list of numbers in range')
        if 'list_ints' in rule:
            lo, hi = rule['list_ints']
            if not (isinstance(v, list) and 0 < len(v) <= rule['most'] and all(isinstance(x, int) and not isinstance(x, bool) and lo <= x <= hi for x in v)):
                raise Red('TAKEN', f'the field {name} is not a short list of whole numbers in range')
        if 'check' in rule and not FIELD_CHECKS[rule['check']](v):
            raise Red('TAKEN', f'the field {name} is not in the shape its type takes')
        out[name] = v
    return out


# ── THE LANES: missions and returns. Here two folders; in Google Cloud two buckets with one-way rights (the cloud half, same four calls) ──

class FolderLanes:
    def __init__(self, root):
        self.root = root
        for lane in ('missions', 'returns'):
            os.makedirs(os.path.join(root, lane), exist_ok=True)

    def _dir(self, lane, job):
        if lane not in ('missions', 'returns') or not _away().NAME.match(job or ''):
            raise ValueError('no such lane or job')
        return os.path.join(self.root, lane, job)

    def put(self, lane, job, locker, blobs):
        """one job's locker and its encrypted files, written whole before its name appears (a .part folder renamed)"""
        final = self._dir(lane, job)
        part = final + '.part'
        shutil.rmtree(part, ignore_errors=True)
        os.makedirs(part)
        for sha, data in blobs.items():
            with open(os.path.join(part, sha + '.bin'), 'wb') as fh:
                fh.write(data)
        with open(os.path.join(part, 'locker.json'), 'w') as fh:
            json.dump(locker, fh)
        os.replace(part, final)

    def names(self, lane):
        """the jobs waiting in a lane, oldest first"""
        d = os.path.join(self.root, lane)
        found = [n for n in os.listdir(d) if not n.endswith('.part') and os.path.isfile(os.path.join(d, n, 'locker.json'))]
        return sorted(found, key=lambda n: (os.path.getmtime(os.path.join(d, n, 'locker.json')), n))

    def locker(self, lane, job):
        with open(os.path.join(self._dir(lane, job), 'locker.json')) as fh:
            return json.load(fh)

    def blob(self, lane, job, sha):
        p = os.path.join(self._dir(lane, job), sha + '.bin')
        if len(sha) != 64 or not os.path.isfile(p):
            return None
        with open(p, 'rb') as fh:
            return fh.read()

    def remove(self, lane, job):
        shutil.rmtree(self._dir(lane, job), ignore_errors=True)

    def claim(self, lane, job):
        """take a job out of its lane -> True for the ONE side that takes it (a rename succeeds once), False when it was already gone"""
        d = self._dir(lane, job)
        gone = d + '.claimed-' + str(os.getpid())
        try:
            os.rename(d, gone)
        except (FileNotFoundError, OSError):
            return False
        shutil.rmtree(gone, ignore_errors=True)
        return True

    def beat(self, beat):
        """the runner's heartbeat, where the asking side reads it"""
        tmp = os.path.join(self.root, 'heartbeat.json.tmp')
        with open(tmp, 'w') as fh:
            json.dump(beat, fh)
        os.replace(tmp, os.path.join(self.root, 'heartbeat.json'))

    def last_beat(self):
        try:
            with open(os.path.join(self.root, 'heartbeat.json')) as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}


class BucketLanes:
    """THE CLOUD LANES (CORE_CLEANUP_IV 97, LARRY 5's shape: a cloud queue the box dials out to): two Cloud Storage buckets, the same calls
    as FolderLanes. A job is <JOB>/<sha>.bin (its encrypted files, written first) and <JOB>/locker.json (written LAST: a job is there only
    when its locker is); a claim is the locker's delete on its generation, so one side alone takes it. store: GcsStore (the real one) or a
    fake in the tests."""
    def __init__(self, store):
        self.store = store
        self._gen = {}

    def _check(self, lane, job):
        if lane not in ('missions', 'returns') or not _away().NAME.match(job or ''):
            raise ValueError('no such lane or job')

    def put(self, lane, job, locker, blobs):
        self._check(lane, job)
        for sha, data in blobs.items():
            self.store.write(lane, f'{job}/{sha}.bin', data)
        self.store.write(lane, f'{job}/locker.json', json.dumps(locker).encode())

    def names(self, lane):
        found = [(o['created'], o['name'][:-len('/locker.json')]) for o in self.store.list(lane, '')
                 if o['name'].endswith('/locker.json') and _away().NAME.match(o['name'][:-len('/locker.json')])]
        return [job for _c, job in sorted(found)]

    def locker(self, lane, job):
        self._check(lane, job)
        data, gen = self.store.read(lane, f'{job}/locker.json')
        if data is None:
            raise ValueError('the job is not in its lane')
        self._gen[(lane, job)] = gen
        return json.loads(data)

    def blob(self, lane, job, sha):
        self._check(lane, job)
        if len(sha) != 64:
            return None
        return self.store.read(lane, f'{job}/{sha}.bin')[0]

    def claim(self, lane, job):
        self._check(lane, job)
        gen = self._gen.pop((lane, job), None)
        if gen is None or not self.store.delete(lane, f'{job}/locker.json', gen):
            return False
        for o in self.store.list(lane, f'{job}/'):
            self.store.delete(lane, o['name'])
        return True

    def remove(self, lane, job):
        self._check(lane, job)
        for o in self.store.list(lane, f'{job}/'):
            self.store.delete(lane, o['name'])

    def beat(self, beat):
        self.store.write('returns', 'heartbeat.json', json.dumps(beat).encode())

    def last_beat(self):
        data, _ = self.store.read('returns', 'heartbeat.json')
        try:
            return json.loads(data) if data else {}
        except ValueError:
            return {}


class GcsStore:
    """Cloud Storage over its JSON API, stdlib only. buckets: {'missions': where, 'returns': where}, each a bucket or 'bucket/prefix' (the
    owner 2026-11-06: Exxact_Loot lives inside LARRYD's existing bucket, larryd-runtime-lockers/exxact/missions and .../exxact/returns, never
    beside the code lockers). token: a function giving a bearer token. Every call names its bucket and an object under its lane's prefix only;
    the names it lists come back without the prefix."""
    API = 'https://storage.googleapis.com/storage/v1/b/'
    UPLOAD = 'https://storage.googleapis.com/upload/storage/v1/b/'

    def __init__(self, buckets, token, urlopen=None):
        self.token = token
        self.buckets, self.prefix = {}, {}
        for lane, where in buckets.items():
            bucket, _, prefix = where.strip('/').partition('/')
            if not bucket or '..' in prefix.split('/'):
                raise ValueError('a lane is a bucket or bucket/prefix')
            self.buckets[lane], self.prefix[lane] = bucket, (prefix.strip('/') + '/' if prefix.strip('/') else '')
        self.urlopen = urlopen or urllib.request.urlopen

    def _ask(self, method, url, data=None, ok=(200,), missing=(404,)):
        req = urllib.request.Request(url, data=data, method=method, headers={'Authorization': f'Bearer {self.token()}',
                                                                              **({'Content-Type': 'application/octet-stream'} if data is not None else {})})
        try:
            with self.urlopen(req, timeout=120) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code in missing:
                return e.code, b'', {}
            raise

    def _o(self, lane, name):
        return self.API + urllib.parse.quote(self.buckets[lane], safe='') + '/o/' + urllib.parse.quote(self.prefix[lane] + name, safe='')

    def list(self, lane, prefix):
        out, page = [], ''
        while True:
            q = {'prefix': self.prefix[lane] + prefix, 'fields': 'items(name,generation,timeCreated),nextPageToken'}
            if page:
                q['pageToken'] = page
            _s, body, _h = self._ask('GET', self.API + urllib.parse.quote(self.buckets[lane], safe='') + '/o?' + urllib.parse.urlencode(q))
            got = json.loads(body or b'{}')
            out += [{'name': i['name'][len(self.prefix[lane]):], 'generation': i.get('generation'), 'created': i.get('timeCreated', '')} for i in got.get('items', [])]
            page = got.get('nextPageToken')
            if not page:
                return out

    def read(self, lane, name):
        status, body, headers = self._ask('GET', self._o(lane, name) + '?alt=media')
        if status == 404:
            return None, None
        return body, headers.get('x-goog-generation') or headers.get('X-Goog-Generation')

    def write(self, lane, name, data):
        self._ask('POST', self.UPLOAD + urllib.parse.quote(self.buckets[lane], safe='') + '/o?' + urllib.parse.urlencode({'uploadType': 'media', 'name': self.prefix[lane] + name}), data)

    def delete(self, lane, name, generation=None):
        url = self._o(lane, name) + (f'?ifGenerationMatch={generation}' if generation else '')
        status, _b, _h = self._ask('DELETE', url, missing=(404, 412))
        return status in (200, 204)


def token_command(argv, life=3000):
    """a bearer token from a command (S4 chooses which), kept for life seconds"""
    held = {'at': 0.0, 'token': ''}

    def token():
        if time.time() - held['at'] > life:
            held['token'] = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=True).stdout.strip()
            held['at'] = time.time()
        return held['token']
    return token


# ── SEALING: a payload and its files ─────────────────────────────────────────────────────────────────────────────────

def _fernet(key):
    from cryptography.fernet import Fernet
    return Fernet(key)


def _pack(payload, files, keys_dir, kind, sender):
    """payload (dict, without its file list) + files {slot: bytes} -> (job, locker, blobs)"""
    away = _away()
    from cryptography.fernet import Fernet
    file_key = Fernet.generate_key()
    f = _fernet(file_key)
    listed, blobs = [], {}
    for slot, data in sorted(files.items()):
        sha = hashlib.sha256(data).hexdigest()
        listed.append({'slot': slot, 'sha256': sha, 'bytes': len(data), 'kind': kind_of(data)})
        blobs[sha] = f.encrypt(data)
    body = {**payload, 'files': listed, 'file_key': file_key.decode()}
    raw = json.dumps(body, sort_keys=True).encode()
    job = payload.get('job') or away.job_key(raw)
    body['job'] = job
    raw = json.dumps(body, sort_keys=True).encode()
    return job, away.seal(raw, job, kind, sender, keys_dir), blobs


def _unpack(lanes, lane, job, keys_dir, kind, most_bytes=None):
    """-> (payload, {slot: bytes}); ValueError on anything off: a locker not the trusted peer's, a file missing or changed, or (most_bytes)
    files whose signed sizes add up past it, refused before one of them is read"""
    away = _away()
    locker = lanes.locker(lane, job)
    if locker.get('job') != job:
        raise ValueError('the locker names another job')
    body = json.loads(away.unseal(locker, keys_dir, kind=kind))
    if body.get('v') != VERSION or body.get('job') != job:
        raise ValueError('not a job of this version')
    try:
        f = _fernet(str(body.get('file_key') or '').encode())
    except Exception as no:   # noqa: BLE001
        raise ValueError('the job carries no file key') from no
    listed = body.get('files') or []
    if not isinstance(listed, list) or not all(isinstance(i, dict) and isinstance(i.get('bytes'), int) and not isinstance(i.get('bytes'), bool)
                                               and i['bytes'] >= 0 for i in listed):
        raise ValueError('the job lists its files wrong')
    if most_bytes is not None and sum(i['bytes'] for i in listed) > most_bytes:
        raise ValueError('the files are bigger than the asker takes')
    files = {}
    for item in body.get('files') or []:
        sealed = lanes.blob(lane, job, str(item.get('sha256') or ''))
        if sealed is None:
            raise ValueError('a file of the job is missing from the lane')
        try:
            data = f.decrypt(sealed)
        except Exception as no:   # noqa: BLE001  cryptography's InvalidToken: a file that was changed is never opened
            raise ValueError('a file of the job was changed') from no
        if hashlib.sha256(data).hexdigest() != item['sha256'] or len(data) != item.get('bytes'):
            raise ValueError('a file of the job was changed')
        files[item['slot']] = data
    return body, files


# ── THE ASKER'S HAND (the internal runtime's and, later, the cloud half's: one shape for both) ─────────────────────────

def ask(lanes, keys_dir, kind, fields, files, asker):
    """seal one job of a type into the missions lane -> its job name. files: {slot: bytes}. asker: {runtime, card, job_key, member}."""
    if kind not in TYPES:
        raise Red('ASKED', 'not a type on the list')
    if asker.get('runtime') not in RUNTIMES or not all(isinstance(asker.get(k), str) and asker.get(k) for k in ('card', 'job_key')):
        raise Red('ASKED', 'the asker is not whole')
    payload = {'v': VERSION, 'type': kind, 'asker': {k: asker.get(k, '') for k in ('runtime', 'card', 'job_key', 'member')},
               'fields': fields, 'asked_at': now()}
    job, locker, blobs = _pack(payload, files, keys_dir, LOCKER_KIND_MISSION, 'asker')
    lanes.put('missions', job, locker, blobs)
    return job


def collect(lanes, keys_dir, job, most_bytes=None):
    """the asker takes its return home -> (return, {slot: bytes}) or None while it is not back; the return is removed from the lane.
    most_bytes: the most the asker can hold of the return's files together (LARRYD's runtime: its memory per RUN); past it, ValueError
    before a file is read"""
    if job not in lanes.names('returns'):
        return None
    body, files = _unpack(lanes, 'returns', job, keys_dir, LOCKER_KIND_RETURN, most_bytes)
    for item in body.get('files') or []:
        rule = TYPES.get(body.get('type'), {}).get('outputs', {}).get(item['slot'])
        data = files[item['slot']]
        if rule is None or kind_of(data) not in rule['kinds'] or len(data) > rule['most']:
            raise ValueError('a returned file is not what its type makes')
    if not lanes.claim('returns', job):
        return None
    return body, files


# ── THE BOX DOORS: the only code that reaches the box ────────────────────────────────────────────────────────────────
# WHERE the box is (its address, its user, its home) is never in this file: this file is copied unchanged into LARRYD's runtime, which
# ships in a public package. The box side reads it from its OWN config, outside every repository (box_config: a JSON file the runner is
# given, e.g. ~/virtual_sanity/runtime_internal/instance/data/exxact_loot/box.json, never committed, never copied):
#   {"address": "<the box's address on the home network>", "user": "<the box's user>", "home": "<that user's home on the box>"}

SSH_UNREACHABLE = 255                              # ssh's own exit when it never reached the box (down, asleep, off the network)
UNREACHABLE = 'the box could not be reached'
BOX_ROOT = 'frost/virtual_workspace/exxact_loot'   # its own folder under the box user's home, beside amLLM, never inside it
ENGINES_ROOT = 'frost/virtual_workspace'           # the engines' folder under the box user's home


def box_config(path):
    """the box side's own config -> {address, user, home}; Red when it is missing or not whole"""
    try:
        with open(os.path.expanduser(path or '')) as fh:
            got = json.load(fh)
    except (OSError, ValueError):
        raise Red('SENT', 'the box side has no config of where the box is') from None
    if not (isinstance(got, dict) and all(isinstance(got.get(k), str) and got[k] and all(c.isalnum() or c in '._-/' for c in got[k])
                                          for k in ('address', 'user', 'home'))):
        raise Red('SENT', 'the box side\'s config is not whole')
    return got


class Box:
    """What the runner needs of the box. LocalBox: the runner runs ON the box. SshBox: the runner runs on this laptop and reaches the box
    by its own key. Tests use a fake box (tests/fake_box.py)."""
    host = '127.0.0.1'
    engines = ''   # where the box's own engines may write what they make (an engine's answer naming a file elsewhere is refused)

    def __init__(self, root):
        self.root = root

    def folder(self, job):
        return os.path.join(self.root, 'jobs', job)

    # each door below: one fixed thing; argv lists only, never a shell string from a mission
    def free_mib(self):
        code, out, _ = self.command('', TYPES['gpu-status']['run']['command'], 30)
        if code != 0:
            raise Red('ROOM', UNREACHABLE if code == SSH_UNREACHABLE else 'the GPUs could not be read')
        cards = {}
        for line in out.strip().splitlines():
            idx, used, total = (int(x.strip()) for x in line.split(','))
            cards[idx] = {'used': used, 'total': total, 'free': total - used}
        return cards

    def http(self, port, path, body, timeout):
        req = urllib.request.Request(f'http://{self.host}:{port}{path}', data=json.dumps(body).encode(), method='POST',
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def healthy(self, engine):
        e = ENGINES[engine]
        try:
            with urllib.request.urlopen(f'http://{self.host}:{e["port"]}{e["health"]}', timeout=5):
                return True
        except (OSError, ValueError):
            return False

    def engine_up(self, engine, sleep=time.sleep):
        """the engine answering, started once by its fixed command when it does not -> True when it answers"""
        if self.healthy(engine):
            return True
        self.start_engine(engine)
        e = ENGINES[engine]
        for _ in range(max(1, e['wait'] // 3)):
            sleep(3)
            if self.healthy(engine):
                return True
        return False


class LocalBox(Box):
    """The runner ON the box: the engines on its own 127.0.0.1, its folder under its own home."""
    def __init__(self, root=None):
        super().__init__(root or os.path.join(os.path.expanduser('~'), BOX_ROOT))
        self.engines = os.path.join(os.path.expanduser('~'), ENGINES_ROOT)

    def put(self, job, rel, data):
        p = os.path.join(self.folder(job), rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as fh:
            fh.write(data)

    def get(self, job, rel):
        p = os.path.join(self.folder(job), rel)
        if not os.path.isfile(p):
            return None
        with open(p, 'rb') as fh:
            return fh.read()

    def path(self, job, rel):
        return os.path.join(self.folder(job), rel)

    def command(self, job, argv, timeout):
        if job:
            os.makedirs(self.folder(job), exist_ok=True)
        p = subprocess.run(argv, cwd=self.folder(job) if job else None, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr

    def detach(self, job, argv):
        with open(os.path.join(self.folder(job), 'run.log'), 'ab') as log:
            subprocess.Popen(argv, cwd=self.folder(job), stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)

    def wipe(self, job):
        shutil.rmtree(self.folder(job), ignore_errors=True)

    def start_engine(self, engine):
        e = ENGINES[engine]
        folder = os.path.join(self.engines, e['folder'])
        os.makedirs(os.path.join(folder, os.path.dirname(e['log'])), exist_ok=True)
        with open(os.path.join(folder, e['log']), 'ab') as log:
            subprocess.Popen(e['start'], cwd=folder, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)


class SshBox(Box):
    """The runner on this laptop: the box reached by Exxact_Loot's OWN key only (never this Mac's default identity), BatchMode, and only
    after the owner's key step: the key file and the go mark must both exist, else every door refuses."""
    def __init__(self, identity, go_mark, config=''):
        super().__init__(BOX_ROOT)
        self.identity, self.go_mark, self.config = identity, go_mark, config
        self.host, self.engines, self.target = '', '', ''

    def _where(self):
        """where the box is, from the box side's own config (read when first needed)"""
        if not self.target:
            got = box_config(self.config)
            self.host, self.target = got['address'], f"{got['user']}@{got['address']}"
            self.engines = f"{got['home'].rstrip('/')}/{ENGINES_ROOT}"
            self.home = got['home'].rstrip('/')

    def _ready(self):
        if not (self.identity and os.path.isfile(self.identity)):
            raise Red('SENT', 'Exxact_Loot has no key of its own yet (the owner\'s key step)')
        if not os.path.isfile(self.go_mark):
            raise Red('SENT', 'no go for the real box yet')
        self._where()

    def _ssh(self, remote_argv, timeout, data=None):
        self._ready()
        line = ' '.join(shlex.quote(a) for a in remote_argv)
        p = subprocess.run(['ssh', '-i', self.identity, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', self.target, line],
                           capture_output=True, timeout=timeout, input=data)
        return p.returncode, p.stdout, p.stderr

    def put(self, job, rel, data):
        target = f'{self.folder(job)}/{rel}'
        code, _, _ = self._ssh(['sh', '-c', 'mkdir -p "$(dirname "$1")" && cat > "$1"', '-', target], 900, data)
        if code != 0:
            raise Red('SENT', 'a file did not reach the box')

    def get(self, job, rel):
        code, out, _ = self._ssh(['cat', f'{self.folder(job)}/{rel}'], 900)
        return out if code == 0 else None

    def path(self, job, rel):
        self._where()
        return f'{self.home}/{self.folder(job)}/{rel}'

    def command(self, job, argv, timeout):
        full = ['sh', '-c', 'mkdir -p "$1" && cd "$1" && shift && exec "$@"', '-', self.folder(job)] + list(argv) if job else list(argv)
        code, out, err = self._ssh(full, timeout)
        return code, out.decode(errors='replace'), err.decode(errors='replace')

    def detach(self, job, argv):
        code, _, _ = self._ssh(['sh', '-c', 'cd "$1" && shift && (nohup "$@" > run.log 2>&1 < /dev/null &)', '-', self.folder(job)] + list(argv), 60)
        if code != 0:
            raise Red('RUN', 'the run did not start on the box')

    def wipe(self, job):
        self._ssh(['rm', '-rf', '--', self.folder(job)], 60)

    def http(self, port, path, body, timeout):
        self._ready()
        return super().http(port, path, body, timeout)

    def healthy(self, engine):
        self._ready()
        return super().healthy(engine)

    def start_engine(self, engine):
        e = ENGINES[engine]
        self._ready()
        self._ssh(['sh', '-c', 'cd "$1" && shift && log="$1" && shift && (nohup "$@" >> "$log" 2>&1 < /dev/null &)', '-',
                   f'{self.engines}/{e["folder"]}', e['log']] + e['start'], 60)


# ── THE BOX SIDE: one pass of the runner over the lanes ───────────────────────────────────────────────────────────────

class Runner:
    """The box side. keys: its locker keys (the key ceremony); state: its own folder here (labels, work); box: the door it runs through."""
    def __init__(self, lanes, keys_dir, state_dir, box, clock=time.time, sleep=time.sleep):
        self.lanes, self.keys, self.state, self.box = lanes, keys_dir, state_dir, box
        self.clock, self.sleep = clock, sleep
        for d in ('labels', 'work'):
            os.makedirs(os.path.join(state_dir, d), exist_ok=True)

    # the label: every hop stamped, read by the Exxact_Loot agent
    def _label_path(self, job):
        return os.path.join(self.state, 'labels', job + '.json')

    def label(self, job):
        try:
            with open(self._label_path(job)) as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {'job': job, 'status': 'QUEUED', 'hops': []}

    def stamp(self, job, stage, note='', **more):
        lab = self.label(job)
        lab.update(more)
        lab['hops'] = lab.get('hops', []) + [{'stage': stage, 'at': now(), 'note': note}]
        lab['status'] = stage
        tmp = self._label_path(job) + '.tmp'
        with open(tmp, 'w') as fh:
            json.dump(lab, fh)
        os.replace(tmp, self._label_path(job))
        return lab

    def _work(self, job):
        return os.path.join(self.state, 'work', job)

    def heartbeat(self):
        """THE HEARTBEAT: when the runner last looked, and each card's free memory (or why the box could not be read)"""
        beat = {'at': now(), 'door': type(self.box).__name__, 'cards': None, 'why': ''}
        try:
            beat['cards'] = {str(i): c for i, c in self.box.free_mib().items()}
        except Red as red:
            beat['why'] = red.why
        except (OSError, ValueError, subprocess.TimeoutExpired):
            beat['why'] = 'the GPUs could not be read'
        tmp = os.path.join(self.state, 'heartbeat.json.tmp')
        with open(tmp, 'w') as fh:
            json.dump(beat, fh)
        os.replace(tmp, os.path.join(self.state, 'heartbeat.json'))
        try:
            self.lanes.beat(beat)   # where the asking side sees the box is up (LARRY 5's heartbeat)
        except (OSError, ValueError, urllib.error.URLError):
            pass
        return beat

    def once(self):
        """take every new mission (TAKEN), then carry every taken job as far as it goes -> {job: its status}"""
        self.heartbeat()
        seen = {}
        for job in self.lanes.names('missions'):
            seen[job] = self.take(job)
        for job in sorted(os.listdir(os.path.join(self.state, 'work'))):
            if os.path.isfile(os.path.join(self._work(job), 'job.json')):
                seen[job] = self.carry(job)
        return seen

    def take(self, job):
        """TAKEN: the locker opened only after its signature is the trusted asker's; the type, the asker, the fields and every file checked;
        then the job leaves the lane and waits here."""
        ctx = {'type': '', 'asker': {}}
        claimed = False
        try:
            try:
                body, files = _unpack(self.lanes, 'missions', job, self.keys, LOCKER_KIND_MISSION)
            except ValueError as no:
                raise Red('TAKEN', 'the mission could not be verified') from no
            finally:
                claimed = self.lanes.claim('missions', job)   # the ONE runner that takes it goes on; another one finds it gone
            if not claimed:
                return 'GONE'
            kind = body.get('type')
            asker = body.get('asker') or {}
            ctx = {'type': kind if kind in TYPES else '', 'asker': asker if isinstance(asker, dict) else {}}
            if kind not in TYPES:
                raise Red('TAKEN', 'not a type on the list')
            if asker.get('runtime') not in RUNTIMES or not asker.get('card') or not asker.get('job_key'):
                raise Red('TAKEN', 'the asker is not whole')
            fields = check_fields(kind, body.get('fields'))
            rules = TYPES[kind]['inputs']
            if set(files) - set(rules):
                raise Red('TAKEN', 'a file in a slot the type does not take')
            for slot, rule in rules.items():
                if rule.get('need') and slot not in files:
                    raise Red('TAKEN', f'the file {slot} is missing')
            for slot, data in files.items():
                if kind_of(data) not in rules[slot]['kinds'] or len(data) > rules[slot]['most']:
                    raise Red('TAKEN', f'the file {slot} is not what the type takes')
            if kind == 'mix' and any(f"source_{c['source']}" not in files for c in fields['clips']):
                raise Red('TAKEN', 'a clip names a source that was not sent')
            work = self._work(job)
            os.makedirs(os.path.join(work, 'in'), exist_ok=True)
            for slot, data in files.items():
                with open(os.path.join(work, 'in', slot), 'wb') as fh:
                    fh.write(data)
            with open(os.path.join(work, 'job.json'), 'w') as fh:
                json.dump({'job': job, 'type': kind, 'asker': asker, 'fields': fields, 'slots': sorted(files), 'taken': self.clock()}, fh)
            self.stamp(job, 'TAKEN', f'{kind} for {asker["runtime"]} {asker["card"]}', type=kind, asker=asker, lane=TYPES[kind]['lane'])
            return 'TAKEN'
        except Red as red:
            if not claimed:
                return 'GONE'
            return self.red(job, red, ctx)

    def carry(self, job):
        with open(os.path.join(self._work(job), 'job.json')) as fh:
            j = json.load(fh)
        t = TYPES[j['type']]
        try:
            self.room(job, t)
            self.send(job, j, t)
            said = self.run(job, j, t)
            outputs = self.home(job, t)
            return self.done(job, j, said, outputs)
        except Wait as w:
            if self.label(job).get('status') != 'WAITING':
                self.stamp(job, 'WAITING', str(w))
            return 'WAITING'
        except Red as red:
            return self.red(job, red, j)

    def room(self, job, t):
        """ROOM: the type's lane must be free (one job per card; a both-card job alone) and its card must hold the room it needs"""
        if t['lane'] == 'none':
            self.stamp(job, 'ROOM', 'no card needed')
            return
        busy = self._busy_lanes(job)
        want = {'gpu0': {0}, 'gpu1': {1}, 'both': {0, 1}}[t['lane']]
        if busy & want:
            raise Wait(f'{t["lane"]} is busy with another job')
        cards = self.box.free_mib()
        if any(i not in cards for i in want):
            raise Red('ROOM', 'the card this type runs on is not on the box')
        if any(cards[i]['total'] < t['room'] for i in want):
            raise Red('ROOM', 'no card on the box is big enough for this type')
        if any(cards[i]['free'] < t['room'] for i in want):
            raise Wait('not enough free memory on its card yet')
        self.stamp(job, 'ROOM', ' · '.join(f'gpu{i} {cards[i]["free"]} MiB free' for i in sorted(want)))

    def _busy_lanes(self, job):
        busy = set()
        for other in os.listdir(os.path.join(self.state, 'work')):
            if other == job:
                continue
            lab = self.label(other)
            if lab.get('status') in ('ROOM', 'SENT', 'RUN'):
                busy |= {'gpu0': {0}, 'gpu1': {1}, 'both': {0, 1}}.get(lab.get('lane'), set())
        return busy

    def send(self, job, j, t):
        """SENT: the job's files and its type's kit into its own folder on the box"""
        rules = t['inputs']
        for slot in j['slots']:
            with open(os.path.join(self._work(job), 'in', slot), 'rb') as fh:
                self.box.put(job, rules[slot].get('as') or f'in/{slot}', fh.read())
        if t['kit']:
            kit = os.path.join(KITS, t['kit'])
            for name in sorted(os.listdir(kit)):
                if name.endswith('.py'):
                    with open(os.path.join(kit, name), 'rb') as fh:
                        self.box.put(job, name, fh.read())
        if j['type'] == 'lips':
            self.box.put(job, 'slots.txt', ' '.join(str(n) for n in j['fields']['slots']).encode())
        if t.get('fields_as'):   # the checked fields, as the kit reads them (never a command line)
            self.box.put(job, t['fields_as'], json.dumps(j['fields'], sort_keys=True).encode())
        self.stamp(job, 'SENT', f'{len(j["slots"])} files')

    def run(self, job, j, t):
        """RUN: the type's one fixed run -> what it said (small JSON)"""
        r = t['run']
        start = self.clock()
        try:
            if 'command' in r:
                code, out, _err = self.box.command(job, r['command'], t['most_seconds'])
                if code != 0:
                    raise Red('RUN', UNREACHABLE if code == SSH_UNREACHABLE else 'the command did not finish well')
                said = {'out': out.strip()[:4000]}
            elif 'http' in r:
                said = self._run_http(job, j, t)
            else:
                said = self._run_detached(job, t, start)
        except (OSError, ValueError, subprocess.TimeoutExpired) as no:
            raise Red('RUN', 'the box did not answer the run') from no
        self.stamp(job, 'RUN', f'{int(self.clock() - start)} s')
        return said

    def _run_http(self, job, j, t):
        if t.get('engine') and not self.box.engine_up(t['engine'], sleep=self.sleep):
            raise Red('RUN', 'the engine on the box did not start')
        if j['type'] == 'face-landmarks':
            got = self.box.http(t['run']['http'], t['run']['path'], {'image': self.box.path(job, 'in/image')}, t['most_seconds'])
            faces = got.get('faces') if isinstance(got, dict) else None
            if not isinstance(faces, list):
                raise Red('RUN', 'the engine gave no list of faces')
            return {'faces': [f for f in (_face(x) for x in faces[:50]) if f]}
        if j['type'] == 'face-swap':
            body = {'source_image': self.box.path(job, 'in/source'), 'target_image': self.box.path(job, 'in/target'), 'enhance': j['fields']['enhance']}
            if 'target_box' in j['fields']:
                body['target_box'] = j['fields']['target_box']
            got = self.box.http(t['run']['http'], t['run']['path'], body, t['most_seconds'])
            made = str(got.get('file') or '')
            if not made:
                raise Red('RUN', 'the engine made nothing')
            if hasattr(self.box, '_where'):
                self.box._where()
            root = self.box.engines.rstrip('/') + '/'
            if not made.startswith(root) or '..' in made.split('/') or not all(c.isalnum() or c in '_./-' for c in made):
                raise Red('RUN', 'the engine named a file outside its own folder')
            code, _o, _e = self.box.command(job, ['mkdir', '-p', 'out'], 30)
            code = code or self.box.command(job, ['cp', '--', made, 'out/picture'], 300)[0]
            if code != 0:
                raise Red('RUN', 'what the engine made could not be taken')
            return {'made': os.path.basename(made)}
        raise Red('RUN', 'no run for this type')

    def _run_detached(self, job, t, start):
        r = t['run']
        self.box.detach(job, r['detached'])
        while True:
            raw = self.box.get(job, r['status'])
            try:
                s = json.loads(raw) if raw else {}
            except ValueError:
                s = {}
            if s.get('state') == r['done']:
                return {'status': s}
            if s.get('state') in ('failed', 'error'):
                raise Red('RUN', 'the run said it failed')
            if self.clock() - start > t['most_seconds']:
                raise Red('RUN', 'the run took longer than its type allows')
            self.sleep(r['poll'])

    def home(self, job, t):
        """HOME: each output fetched, its kind read from its first bytes, its size checked"""
        got = {}
        for slot, rule in t['outputs'].items():
            rel = rule.get('from') or f'out/{slot}'
            data = self.box.get(job, rel)
            if data is None:
                if rule.get('optional'):
                    continue
                raise Red('HOME', f'the output {slot} did not come home')
            if kind_of(data) not in rule['kinds'] or len(data) > rule['most']:
                raise Red('HOME', f'the output {slot} is not what the type makes')
            got[slot] = data
        self.stamp(job, 'HOME', f'{len(got)} files')
        return got

    def done(self, job, j, said, outputs):
        self._return(job, j, 'DONE', 'HOME', '', said, outputs)
        return 'DONE'

    def red(self, job, red, j):
        self._return(job, j, 'RED', red.step, red.why, {}, {})
        return 'RED'

    def _return(self, job, j, state, step, why, said, outputs):
        more = {k: j[k] for k in ('type', 'asker') if j.get(k)}
        lab = self.stamp(job, state, why or 'made', step=step, why=why, **more)
        payload = {'v': VERSION, 'job': job, 'type': j.get('type', ''), 'state': state, 'step': step, 'why': why,
                   'hops': lab['hops'], 'said': said}
        try:
            _, locker, blobs = _pack(payload, outputs, self.keys, LOCKER_KIND_RETURN, 'exxact')
            self.lanes.put('returns', job, locker, blobs)
        finally:
            try:
                self.box.wipe(job)
            except Red:
                pass
            shutil.rmtree(self._work(job), ignore_errors=True)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x and abs(x) < 1e7


def _face(x):
    """one face from the engine, numbers only: bbox (4), kps (up to 10 points), score; anything else dropped"""
    if not isinstance(x, dict) or not (isinstance(x.get('bbox'), list) and len(x['bbox']) == 4 and all(_num(v) for v in x['bbox'])):
        return None
    face = {'bbox': [float(v) for v in x['bbox']]}
    kps = x.get('kps')
    if isinstance(kps, list):
        face['kps'] = [[float(a), float(b)] for a, b in (k for k in kps[:10] if isinstance(k, list) and len(k) == 2 and _num(k[0]) and _num(k[1]))]
    if _num(x.get('score')):
        face['score'] = float(x['score'])
    return face


def labels(state_dir, most=50):
    """the Exxact_Loot agent's read: the newest labels first"""
    d = os.path.join(state_dir, 'labels')
    if not os.path.isdir(d):
        return []
    out = []
    for name in os.listdir(d):
        if name.endswith('.json'):
            try:
                with open(os.path.join(d, name)) as fh:
                    out.append(json.load(fh))
            except (OSError, ValueError):
                continue
    out.sort(key=lambda lab: (lab.get('hops') or [{}])[-1].get('at', ''), reverse=True)
    return out[:most]


def board(state_dir, lanes_root, most=50):
    """everything the Exxact_Loot agent shows, read from plain files only (no key, no locker opened)"""
    try:
        with open(os.path.join(state_dir, 'heartbeat.json')) as fh:
            beat = json.load(fh)
    except (OSError, ValueError):
        beat = {}
    waiting = {}
    for lane in ('missions', 'returns'):
        d = os.path.join(lanes_root, lane)
        waiting[lane] = len([n for n in os.listdir(d) if not n.endswith('.part')]) if os.path.isdir(d) else 0
    return {'heartbeat': beat, 'waiting': waiting, 'labels': labels(state_dir, most)}
