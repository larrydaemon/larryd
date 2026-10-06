"""ONE RUN PER INSTANCE, THE SLOT (the security reviews, 2026-10-06). take() is atomic; give_back() never fails, even
twice; a slot held longer than a run's own limit plus a margin is reclaimed by the next take() and the reclaim logged
(ids and times only, never a run's data)."""
import logging
import threading
import time

LOG = logging.getLogger('hanzo')


class Slot:
    def __init__(self, most_seconds, clock=time.monotonic):
        self.lock, self.guard, self.clock = threading.Lock(), threading.Lock(), clock
        self.most_seconds, self.taken_at, self.owner = most_seconds, None, None

    def take(self):
        """-> a token (truthy) for the holder, or None when the slot is held. Only the token's holder gives it back."""
        with self.guard:
            if self.lock.acquire(blocking=False):
                self.taken_at, self.owner = self.clock(), object()
                return self.owner
            if self.taken_at is not None and self.clock() - self.taken_at > self.most_seconds:
                LOG.warning('slot reclaimed: held %.0f s, past the limit of %d s', self.clock() - self.taken_at, self.most_seconds)
                self.taken_at, self.owner = self.clock(), object()   # the lock stays held: ownership passes to this caller
                return self.owner
            return None

    def give_back(self, token):
        """A token no longer the owner's (its slot was reclaimed) gives nothing back."""
        with self.guard:
            if token is None or token is not self.owner:
                return
            self.taken_at, self.owner = None, None
            try:
                self.lock.release()
            except RuntimeError:
                pass   # already given back: a second give-back in a finally is harmless
