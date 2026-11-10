"""ONE RUN PER INSTANCE, THE SLOT (the security reviews, 2026-10-06). take() is atomic; give_back() never fails, even
twice. A slot held longer than a run's own hard limit plus a margin is reclaimed by the next take() ONLY when the old
run can be proven gone: the holder's sandboxed process group (attached as the run starts) is killed and confirmed dead
first. A holder with no process attached (code of the runtime itself, never an agent's) is never reclaimed: the slot
stays held, take() refuses, and stuck() tells the health check, so Cloud Run replaces the instance. The reclaim is
logged (ids and times only, never a run's data)."""
import datetime
import logging
import os
import signal
import threading
import time

LOG = logging.getLogger('runtime')
CONFIRM_SECONDS = 5   # how long a reclaim waits to see the old process group gone


def _alive(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True   # it exists, whoever owns it: never assumed gone


def _kill_and_confirm(pgid, clock, sleep):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    until = clock() + CONFIRM_SECONDS
    while clock() < until:
        if not _alive(pgid):
            return True
        sleep(0.05)
    return not _alive(pgid)


def _now():
    """The time on a slot's line (the runtime's log has no time of its own)."""
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


class Slot:
    def __init__(self, most_seconds, clock=time.monotonic, sleep=time.sleep):
        self.lock, self.guard, self.clock, self.sleep = threading.Lock(), threading.Lock(), clock, sleep
        self.most_seconds, self.taken_at, self.owner, self.pgid = most_seconds, None, None, None
        self.label, self.most = '', most_seconds   # the holder's own: which run (a job key and RUN, for the log) and its own limit

    def attach(self, token, pgid):
        """The holder's run started (its process group) or ended (None)."""
        with self.guard:
            if token is not None and token is self.owner:
                self.pgid = pgid

    def take(self, label='', most=None):
        """label: which run holds it (said in the log, never a run's data). most: the holder's own limit in seconds (a RUN of
        an internal agent may work for hours; a CALL keeps the slot's own); past it, and only then, the slot may be reclaimed.
        -> a token (truthy) for the holder, or None: the slot is held, OR anything went wrong while taking or checking
        it (it fails CLOSED: an error never lets a run through). The stale reclaim is a compare-and-swap on the exact owner
        seen, under the guard, and happens only after the old run's process group is confirmed dead."""
        try:
            with self.guard:
                if self.lock.acquire(blocking=False):
                    try:
                        self.taken_at, self.owner, self.pgid = self.clock(), object(), None
                        self.label, self.most = str(label or ''), (most if most else self.most_seconds)
                    except Exception:
                        self.taken_at, self.owner, self.pgid = None, None, None
                        self.lock.release()   # never left held with no owner
                        raise
                    return self.owner
                seen_owner, seen_at, seen_pgid = self.owner, self.taken_at, self.pgid
                if seen_owner is None or seen_at is None or self.clock() - seen_at <= self.most:
                    return None
                if seen_pgid is None:   # no process to kill: the old holder may still be alive, so never hand it over
                    LOG.error('slot stuck at %s: %s held %.0f s (its limit %d s) with no run process to reclaim; refused',
                              _now(), self.label or 'a holder with no name', self.clock() - seen_at, self.most)
                    return None
                if not _kill_and_confirm(seen_pgid, self.clock, self.sleep):
                    LOG.error('slot not reclaimed: the old run could not be confirmed gone; refused')
                    return None
                if self.owner is not seen_owner:   # the compare: still the very stale holder that was seen
                    return None
                LOG.warning('slot reclaimed at %s: %s held %.0f s, past its limit of %d s; the old run killed and confirmed gone',
                            _now(), self.label or 'a holder with no name', self.clock() - seen_at, self.most)
                self.taken_at, self.owner, self.pgid = self.clock(), object(), None   # the swap: the lock stays held
                self.label, self.most = str(label or ''), (most if most else self.most_seconds)
                return self.owner
        except Exception as error:   # any doubt refuses the run
            LOG.error('slot not taken (refused): %s', type(error).__name__)
            return None

    def stuck(self):
        """True when the slot has been held past the limit with nothing that can be reclaimed: the instance is unhealthy."""
        with self.guard:
            return self.owner is not None and self.taken_at is not None and self.pgid is None and self.clock() - self.taken_at > self.most

    def give_back(self, token):
        """A token no longer the owner's (its slot was reclaimed) gives nothing back."""
        with self.guard:
            if token is None or token is not self.owner:
                return
            self.taken_at, self.owner, self.pgid = None, None, None
            self.label, self.most = '', self.most_seconds
            try:
                self.lock.release()
            except RuntimeError:
                pass   # already given back: a second give-back in a finally is harmless


class Slots:
    """A FEW RUNS AT A TIME, THE RUNTIME ON THIS COMPUTER ONLY (the owner 2026-11-10: "nobody is going to press run on any of them ever ...
    this needs to be automated"; "it starts at 6:50am and all day agents run then the night starts at 1am"): with one slot a long step (the
    night's Web build holds the Judge, about 45 minutes; the day's Build) made every other block's RUN wait, and the platform closes a RUN
    left QUEUED 20 minutes as FAILED. n Slots, each exactly a Slot (its own take, reclaim and give back): take() hands the first free one's
    token; attach, give_back and stuck speak to the slot that token belongs to. Cloud Run keeps ONE RUN PER INSTANCE (Slot)."""

    def __init__(self, n, most_seconds, clock=time.monotonic, sleep=time.sleep):
        self.slots = [Slot(most_seconds, clock, sleep) for _ in range(int(n))]

    def _of(self, token):
        return next((s for s in self.slots if token is not None and s.owner is token), None)

    def take(self, label='', most=None):
        for s in self.slots:
            token = s.take(label, most)
            if token:
                return token
        return None

    def attach(self, token, pgid):
        s = self._of(token)
        if s is not None:
            s.attach(token, pgid)

    def give_back(self, token):
        s = self._of(token)
        if s is not None:
            s.give_back(token)

    def stuck(self):
        return all(s.stuck() for s in self.slots)

