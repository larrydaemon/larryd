"""THE CALLERS' KEYS AND THE NONCES SEEN (the LARRYD runtime design, 2026-10-06).

Keys: one secret per caller (slot A, slot B), each a file in LARRYD_KEYS_DIR named by its key id (on Cloud Run, Secret
Manager versions mounted there). Read again at most every 60 seconds, so a destroyed or disabled version stops working
everywhere within a minute with nothing to restart.

Nonces: each accepted once. On Cloud Run instances come and go, so the record is kept outside the instance (Firestore,
LARRYD_NONCES=firestore, each nonce a document that expires after five minutes by Firestore's own TTL on expire_at);
on a laptop or a test, in memory."""
import datetime
import os
import pathlib
import threading
import time

KEY_CACHE_SECONDS = 60
NONCE_SECONDS = 300


class Keys:
    """{key id: [every enabled version's secret]}. A key is a file named by its id, or (Cloud Run: one secret per
    folder) a folder named by its id holding one file per mounted VERSION: during a rotation's 7-day overlap both the
    current and the previous version are mounted, and a call signed with either is accepted; once the old version is
    destroyed it is no longer mounted, and within a minute it is no longer accepted."""
    def __init__(self, folder, clock=time.monotonic):
        self.folder, self.clock, self.read_at, self.keys, self.lock = pathlib.Path(folder), clock, None, {}, threading.Lock()

    def now(self):
        with self.lock:
            if self.read_at is None or self.clock() - self.read_at >= KEY_CACHE_SECONDS:
                self.keys, self.read_at = read_versions(self.folder), self.clock()
            return {k: list(v) for k, v in self.keys.items()}


def read_versions(folder):
    found = {}
    folder = pathlib.Path(folder)
    if folder.is_dir():
        for f in sorted(folder.iterdir()):
            if f.name.startswith('.'):
                continue
            inner = [g for g in sorted(f.iterdir()) if g.is_file() and not g.name.startswith('.')] if f.is_dir() else [f]
            secrets = [g.read_text().strip() for g in inner]
            secrets = [x for x in secrets if x]
            if secrets:
                found[f.name] = secrets
    return found


class Outbound:
    """THE RUNTIME'S OWN KEYS, for its calls back INTO the platform (the owner's "API only, both ways"): one per slot, a
    folder named by the caller ('slot-a', 'slot-b', 'proof': the same names as the inbound keys) holding its mounted
    versions; a call to it is signed with its NEWEST version (the last file by name) under the key id 'runtime-to-<caller>'
    (the platform's offices accept only those ids, 2026-10-06).
    The runtime refuses to start on Cloud Run without them (no call is ever signed with an empty key)."""
    def __init__(self, folder):
        self.folder = pathlib.Path(folder)

    def key(self, slot):
        versions = read_versions(self.folder).get(slot) or []
        if not versions:
            raise LookupError(f'no outbound key for {slot}')
        return RUNTIME_KEY_PREFIX + slot, versions[-1]

    def slots(self):
        return sorted(read_versions(self.folder))


RUNTIME_KEY_PREFIX = 'runtime-to-'


class MemoryNonces:
    def __init__(self, clock=time.monotonic):
        self.clock, self.seen, self.lock = clock, {}, threading.Lock()

    def fresh(self, nonce):
        with self.lock:
            now = self.clock()
            self.seen = {n: t for n, t in self.seen.items() if now - t < NONCE_SECONDS}
            if nonce in self.seen:
                return False
            self.seen[nonce] = now
            return True


class FirestoreNonces:
    """A nonce is a document id in the collection; create() refuses an id that exists, across every instance."""
    def __init__(self, collection='nonces'):
        from google.cloud import firestore   # only on the server
        from google.api_core.exceptions import AlreadyExists
        self.col, self.exists = firestore.Client().collection(collection), AlreadyExists

    def fresh(self, nonce):
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=NONCE_SECONDS)
        try:
            self.col.document(nonce).create({'expire_at': expire})
            return True
        except self.exists:
            return False


def nonces():
    return FirestoreNonces() if os.environ.get('LARRYD_NONCES') == 'firestore' else MemoryNonces()
