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
    def __init__(self, folder, clock=time.monotonic):
        self.folder, self.clock, self.read_at, self.keys, self.lock = pathlib.Path(folder), clock, None, {}, threading.Lock()

    def now(self):
        with self.lock:
            if self.read_at is None or self.clock() - self.read_at >= KEY_CACHE_SECONDS:
                found = {}
                if self.folder.is_dir():
                    for f in sorted(self.folder.iterdir()):
                        if f.name.startswith('.'):
                            continue
                        # a key is a file named by its id, or (Cloud Run: one secret per folder) a folder named by its id
                        # holding the secret's one file
                        inner = [g for g in sorted(f.iterdir()) if g.is_file() and not g.name.startswith('.')] if f.is_dir() else [f]
                        secret = inner[0].read_text().strip() if inner else ''
                        if secret:
                            found[f.name] = secret
                self.keys, self.read_at = found, self.clock()
            return dict(self.keys)


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
