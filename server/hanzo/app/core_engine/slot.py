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
        """-> a token (truthy) for the holder, or None: the slot is held, OR anything went wrong while taking or
        checking it. It fails CLOSED: an error never lets a run through. The stale reclaim is a compare-and-swap on
        the exact owner seen, under the guard, so two callers can never both reclaim the same stale slot."""
        try:
            with self.guard:
                if self.lock.acquire(blocking=False):
                    try:
                        self.taken_at, self.owner = self.clock(), object()
                    except Exception:
                        self.taken_at, self.owner = None, None
                        self.lock.release()   # never left held with no owner
                        raise
                    return self.owner
                seen_owner, seen_at = self.owner, self.taken_at
                if seen_owner is None or seen_at is None or self.clock() - seen_at <= self.most_seconds:
                    return None
                if self.owner is not seen_owner:   # the compare: still the very stale holder that was seen
                    return None
                LOG.warning('slot reclaimed: held %.0f s, past the limit of %d s', self.clock() - seen_at, self.most_seconds)
                self.taken_at, self.owner = self.clock(), object()   # the swap: the lock stays held, ownership passes here
                return self.owner
        except Exception as error:   # any doubt refuses the run
            LOG.error('slot not taken (refused): %s', type(error).__name__)
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
