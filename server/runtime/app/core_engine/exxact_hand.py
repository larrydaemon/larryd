"""THE EXXACT HAND (CORE_CLEANUP_IV 97, Exxact_Loot's spec from frost-88): an 'exxact/<type>' ask made on the Exxact box, the way
outside.Hand makes a Replicate ask, under outside.py's same laws. The box has no door of its own: this hand only writes a sealed job into
the MISSIONS bucket and reads the box's sealed answer from the RETURNS bucket (exxact.py, Exxact_Loot's own code, copied unchanged).
1. THE LIST ONLY: the type is the model's own (outside.MODELS, built from exxact.TYPES); its fields are checked by exxact.check_fields,
   its inputs (the references, the member's DA-M files, read by the harness) put on the type's input slots in order.
2. A FIXED GRAMMAR: the job carries the type's fields and files and the asker (the agent's card, the job, the member), nothing else.
3. THE KEY NEVER TRAVELS: there is no vault key for the box. The buckets are reached with the runtime's own token (a function handed in
   at the runtime's start; on Cloud Run its service account), and the job is sealed with the hand's own locker keys (keys_dir).
4. POLL, NEVER LISTEN: exxact.collect every EVERY_SECONDS until the type's most_seconds are up.
5. WHAT COMES BACK IS NOT TRUSTED: collect has checked the box side's signature, the job it answers and each file's sha256, kind and
   size against the type's outputs; it goes to the member's DA-M through the harness, as a Replicate file does.
Every refusal is LARRYD's own fixed words, NOT_MADE_EXXACT_<WHY>; the box's own 'why' is never carried.
NOTHING IS WIRED IN THIS ROUND: the buckets, the token and the keys are S4. A hand built without them is NOT SET UP and refuses every
ask with NOT_MADE_EXXACT_NOT_SET_UP; it never raises."""
import json
import threading
import time
import urllib.error

from . import exxact, exxact_locker, outside

EVERY_SECONDS = 15
MOST_DROPPED = 200   # jobs whose time was up, kept so their late return is collected and dropped

NOT_SET_UP = 'NOT_MADE_EXXACT_NOT_SET_UP'
NOT_ON_THE_LIST = 'NOT_MADE_EXXACT_NOT_ON_THE_LIST'
REFERENCE_NOT_READ = 'NOT_MADE_EXXACT_REFERENCE_NOT_READ'
TAKEN = 'NOT_MADE_EXXACT_TAKEN'
UNREACHABLE = 'NOT_MADE_EXXACT_UNREACHABLE'
TIME_UP = 'NOT_MADE_EXXACT_TIME_UP'
NOT_TRUSTED = 'NOT_MADE_EXXACT_RETURN_NOT_TRUSTED'
NOTHING_MADE = 'NOT_MADE_EXXACT_NOTHING_MADE'
RED = 'NOT_MADE_EXXACT_RED'   # a RED whose step is not one of exxact.STEPS


def red_words(step):
    """A RED's fixed words, by the step it stopped at: NOT_MADE_EXXACT_TAKEN, _ROOM, _SENT, _RUN, _HOME."""
    return f'NOT_MADE_EXXACT_{step}' if step in exxact.STEPS else RED


class ExxactHand:
    """buckets: {'missions': name, 'returns': name}; token: a function giving the runtime's bearer token for them; keys_dir: this hand's
    locker keys (exxact_locker.keys / trust, the key ceremony with the box side). lanes replaces the buckets (a test: BucketLanes on a fake
    store). Without lanes or keys the hand is not set up. runtime: 'external' (Cloud Run) or 'internal' (the internal runtime)."""

    def __init__(self, buckets=None, token=None, keys_dir='', lanes=None, runtime='external', sleep=time.sleep, clock=time.monotonic):
        if lanes is None and buckets and token:
            lanes = exxact.BucketLanes(exxact.GcsStore(buckets, token))
        self.lanes, self.keys, self.runtime = lanes, keys_dir, runtime
        self.sleep, self.clock = sleep, clock
        self._dropped, self._lock = [], threading.Lock()

    def set_up(self):
        """-> True when the lanes are given and the key ceremony is done (this side's keys and the box side's publics)."""
        return bool(self.lanes is not None and self.keys and not exxact_locker.ready(self.keys))

    def _sweep(self):
        """A return that came after its time was up is collected and dropped (never made into a file)."""
        with self._lock:
            late, self._dropped = self._dropped, []
        keep = []
        for job in late:
            try:
                if exxact.collect(self.lanes, self.keys, job) is None:
                    keep.append(job)
            except (ValueError, KeyError, TypeError, OSError):
                continue   # a return not trusted, or one that cannot be read: let go
        with self._lock:
            self._dropped = (keep + self._dropped)[-MOST_DROPPED:]

    def _give_up(self, job):
        """Time up: a job still waiting in the missions lane is taken out of it (the box then finds it gone); its return, if one comes, is dropped."""
        try:
            if job in self.lanes.names('missions'):
                self.lanes.remove('missions', job)
        except (ValueError, OSError):
            pass
        with self._lock:
            self._dropped = (self._dropped + [job])[-MOST_DROPPED:]

    def _files(self, ask, kind, picture):
        """the references' bytes on the type's input slots, in order -> ({slot: bytes}, '') or ({}, why)"""
        pictures = [picture] if isinstance(picture, (bytes, bytearray)) else list(picture or ())
        pictures = [bytes(p) for p in pictures if p]
        wanted = ask.get('reference') or []
        wanted = [wanted] if isinstance(wanted, str) else wanted
        if len(pictures) != len(wanted):
            return {}, REFERENCE_NOT_READ
        rules = exxact.TYPES[kind]['inputs']
        if len(pictures) > len(rules):
            return {}, TAKEN
        files = dict(zip(rules, pictures))
        for slot, rule in rules.items():
            if rule.get('need') and slot not in files:
                return {}, TAKEN
        for slot, data in files.items():
            if exxact.kind_of(data) not in rules[slot]['kinds'] or len(data) > rules[slot]['most']:
                return {}, TAKEN
        return files, ''

    def make(self, ask, key, picture=b'', asker=None):
        """The whole errand, the same shape as outside.Hand.make: -> ({'name', 'kind', 'data'}, '') or (None, why). key: unused (the
        box has no vault key; the harness hands ''). picture: the references' bytes in the ask's order. asker: {card, job_key, member},
        the RUN's own (the harness's), never the agent's word."""
        spec = outside.MODELS.get(ask.get('model')) if isinstance(ask, dict) else None
        if not spec or spec['provider'] != 'exxact' or spec['path'] not in exxact.TYPES:
            return None, NOT_ON_THE_LIST
        if not self.set_up():
            return None, NOT_SET_UP
        kind = spec['path']
        self._sweep()
        files, why = self._files(ask, kind, picture)
        if why:
            return None, why
        try:
            fields = exxact.check_fields(kind, {f: ask[f] for f in (*spec['choices'], *spec.get('numbers', {})) if f in ask})
        except exxact.Red:
            return None, TAKEN
        who = asker if isinstance(asker, dict) else {}
        try:
            job = exxact.ask(self.lanes, self.keys, kind, fields, files,
                             {'runtime': self.runtime, **{k: str(who.get(k) or '') for k in ('card', 'job_key', 'member')}})
        except exxact.Red:
            return None, TAKEN
        except ImportError:   # no `cryptography` in this runtime: it cannot seal, so it is not set up
            return None, NOT_SET_UP
        except (OSError, ValueError, urllib.error.URLError):
            return None, UNREACHABLE
        until = self.clock() + spec['most_seconds']
        while True:
            try:
                back = exxact.collect(self.lanes, self.keys, job)
            except (ValueError, KeyError, TypeError):   # a return whose signature, job or files are off: never opened further
                return None, NOT_TRUSTED
            except OSError:
                back = None   # a blip: asked again until the type's time is up
            if back is not None:
                break
            if self.clock() >= until:
                self._give_up(job)
                return None, TIME_UP
            self.sleep(EVERY_SECONDS)
        body, made = back
        if body.get('type') != kind:
            return None, NOT_TRUSTED
        if body.get('state') != 'DONE':
            return None, red_words(body.get('step'))
        outputs = exxact.TYPES[kind]['outputs']
        if not outputs:   # a type that makes no file (gpu-status, face-landmarks): what it said, its numbers, as one JSON file
            data = json.dumps(body.get('said') or {}, sort_keys=True).encode('utf-8')
            if len(data) > spec['most_bytes']:
                return None, NOTHING_MADE
            return {'name': f"{ask['name']}.json", 'kind': 'json', 'data': data}, ''
        # ONE FILE BACK: the harness settles one file per ask (its _made appends one {name, content_b64} per ask), so a type with several
        # outputs (lips: one per ON slot) gives its FIRST output that came home, in the type's order; the others are not kept
        for slot in outputs:
            data = made.get(slot)
            if data:
                ext = outside.kind_of(data) or exxact.kind_of(data)
                return {'name': f"{ask['name']}.{ext}", 'kind': ext, 'data': data}, ''
        return None, NOTHING_MADE
