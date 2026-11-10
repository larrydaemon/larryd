"""THE CLOCK READER (ONE SYSTEM, 2026-11-07): each agent's clock is its own job record's fields in wid (data_job_schedule_type,
data_job_time, data_job_timezone, data_job_day_of_week 0 = Sun .. 6 = Sat, data_job_day_of_month, data_job_month_of_quarter,
data_job_starts_on, data_job_ends_on, and data_job_last_run_at, written by wid as a RUN ends). due() reads them; Clock.tick() asks
for the jobs, and for each one due whose agent the locker holds and FROST approved, asks wid to queue a RUN exactly as the member's
RUN press does, then runs the catch-up so the RUN starts. The same code on both runtimes: on this computer (LARRYD_INTERNAL=1) a
loop ticks it every 60 s in-process; on Cloud Run the signed door POST /api/clock/tick ticks it (Cloud Scheduler).

A missed time (the computer asleep) fires ONCE on wake: only the latest scheduled moment at or before now is ever considered,
and it is due only when nothing ran since it. The runtime's own memory (runtime_clock) holds the moment it last pressed for
each job, so one moment is never pressed twice, even when wid refused the press or the RUN has not ended yet."""
import datetime
import logging
import re
import sqlite3
import threading
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LOG = logging.getLogger('runtime')

NEVER = ('', 'on_demand', 'manual')   # only a press of the member's runs these
EVERY = re.compile(r'^every\s+(\d+)\s+(minute|minutes|hour|hours)$')
HM = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)$')
TICK_SECONDS = 60
FIELDS = ('schedule_type', 'time', 'timezone', 'day_of_week', 'day_of_month', 'month_of_quarter', 'starts_on', 'ends_on')


def _f(job, name):
    return str(job.get(f'data_job_{name}') or '').strip()


def _int(text, low, high):
    return int(text) if text.isdigit() and low <= int(text) <= high else None


def _date(text):
    try:
        return datetime.date.fromisoformat(text[:10]) if text else None
    except ValueError:
        return None


def _at(day, hm, zone):
    """The aware moment of HH:MM on that local day in that zone."""
    return datetime.datetime.combine(day, hm, tzinfo=zone)


def _month_day(year, month, dom):
    """Day dom of that month, or its last day when the month is shorter (31 in April: the 30th)."""
    last = (datetime.date(year + (month == 12), month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    return datetime.date(year, month, min(dom, last))


def _back_months(year, month, n):
    month -= n
    while month < 1:
        month, year = month + 12, year - 1
    return year, month


def zone_of(job):
    """The job's time zone, or None when it names none the system knows (then it never fires)."""
    try:
        return ZoneInfo(_f(job, 'timezone') or 'America/New_York')   # the species' own default (jobs.json)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def latest(job, now):
    """The job's latest scheduled moment at or before now (aware), or None: on demand, manual, an unknown kind, a field it needs
    missing or not a value, an unknown zone."""
    kind = _f(job, 'schedule_type').lower()
    if kind in NEVER:
        return None
    zone = zone_of(job)
    if zone is None:
        return None
    here = now.astimezone(zone)
    every = EVERY.match(kind)
    if every:   # every N minutes (or hours): the moments N apart from the local midnight of the day
        step = int(every.group(1)) * (60 if every.group(2).startswith('hour') else 1)
        if step < 1:
            return None
        midnight = datetime.datetime.combine(here.date(), datetime.time(0, 0), tzinfo=zone)
        minutes = int((here - midnight).total_seconds() // 60)
        return midnight + datetime.timedelta(minutes=minutes - minutes % step)
    hm = HM.match(_f(job, 'time'))
    if not hm:
        return None
    hm = datetime.time(int(hm.group(1)), int(hm.group(2)))
    today = here.date()
    if kind == 'daily':
        days = [today, today - datetime.timedelta(days=1)]
    elif kind == 'weekly':
        dow = _int(_f(job, 'day_of_week'), 0, 6)   # 0 = Sunday .. 6 = Saturday (wid's clock_of)
        if dow is None:
            return None
        back = ((today.weekday() + 1) % 7 - dow) % 7
        days = [today - datetime.timedelta(days=back), today - datetime.timedelta(days=back + 7)]
    elif kind == 'monthly':
        dom = _int(_f(job, 'day_of_month'), 1, 31)
        if dom is None:
            return None
        days = [_month_day(*_back_months(today.year, today.month, n), dom) for n in (0, 1)]
    elif kind == 'quarterly':
        moq, dom = _int(_f(job, 'month_of_quarter'), 1, 3), _int(_f(job, 'day_of_month'), 1, 31)
        if moq is None or dom is None:
            return None
        back = (today.month - moq) % 3   # months back to the latest month that is the quarter's moq-th (1: Jan Apr Jul Oct)
        days = [_month_day(*_back_months(today.year, today.month, back + n), dom) for n in (0, 3)]
    else:
        return None
    return next((m for m in (_at(d, hm, zone) for d in days) if m <= now), None)


def due(job, now, last_run):
    """Is the job due now? now: aware. last_run: aware, or None (never ran). Never for on_demand, manual or anything not
    understood; otherwise its latest scheduled moment at or before now, within its starts_on .. ends_on (local dates, both
    days included), with nothing run since it. A moment missed while asleep is that latest one: it fires once, never twice."""
    moment = latest(job, now)
    if moment is None:
        return False
    day = moment.astimezone(zone_of(job)).date()
    starts, ends = _date(_f(job, 'starts_on')), _date(_f(job, 'ends_on'))
    if (starts and day < starts) or (ends and day > ends):
        return False
    return last_run is None or last_run < moment


def last_run_of(job, zone):
    """wid's data_job_last_run_at ('YYYY-MM-DD HH:MM:SS', wid's own local time, naive) as an aware moment, or None."""
    text = str(job.get('data_job_last_run_at') or '').strip()
    try:
        at = datetime.datetime.fromisoformat(text[:19].replace(' ', 'T')) if text else None
    except ValueError:
        return None
    if at is None:
        return None
    return at.replace(tzinfo=zone) if at.tzinfo is None else at


class WidJobs:
    """THE JOBS AS WID HANDS THEM, through two runtime doors wid does not have yet (wid is locked core; see MISSING):
    GET /jobs/scheduled  -> {'jobs': [{account, scope, member, job_key, agent_key, data_job_<each of FIELDS>, data_job_last_run_at,
                             data_job_run_state}]}  every job with a clock this runtime may run (runtime=internal: the INTERNAL-ONLY
                             agents' jobs, else every other), as /jobs/queued splits them
    POST /jobs/press     {account, scope, member, job_key}  -> {ok, text}  the job's own member's RUN press (atom.act 'run' at the
                             job's own board and shell, atom.placed), its every check and refusal; a runtime may press only a job
                             with a clock that is due by wid's own reading, never an on-demand or manual one
    Until wid has them, scheduled() answers nothing (wid's 404, said once in the log) and the clock presses nothing."""
    MISSING = ('GET /jobs/scheduled', 'POST /jobs/press')

    def __init__(self, client, internal=False):
        self.client, self.internal, self.said = client, internal, False

    def scheduled(self):
        status, body = self.client.get('wid', '/jobs/scheduled', {'runtime': 'internal'} if self.internal else None)
        if status != 200:
            if not self.said:
                LOG.warning('clock: wid answered %s for /jobs/scheduled: nothing is pressed', status)
                self.said = True
            return []
        self.said = False
        return [j for j in body.get('jobs') or [] if isinstance(j, dict)]

    def press(self, job):
        body = {k: str(job.get(k) or '') for k in ('account', 'scope', 'member', 'job_key')}
        if self.internal:   # wid has one callback key for both runtimes: the internal one says so, as on /jobs/queued (else 403 "the other runtime's job")
            body['runtime'] = 'internal'
        return self.client.post('wid', '/jobs/press', body)


class Memory:
    """The runtime's own memory of the clock (runtime_clock in agents.db): per job, the moment it first saw the job and the
    moment it last pressed for it. A job first seen after its latest moment waits for its next one (a new runtime never fires
    a moment it was not there for)."""

    def __init__(self, db):
        self.db = db

    def _key(self, job):
        return f"{job.get('account', '')}/{job.get('scope', '')}/{job.get('job_key', '')}"

    def get(self, job):
        con = sqlite3.connect(self.db)
        try:
            row = con.execute('SELECT first_seen, pressed_for FROM runtime_clock WHERE job = ?', (self._key(job),)).fetchone()
        finally:
            con.close()
        return tuple(datetime.datetime.fromisoformat(v) if v else None for v in row) if row else None

    def seen(self, job, now):
        con = sqlite3.connect(self.db)
        try:
            con.execute('INSERT OR IGNORE INTO runtime_clock (job, first_seen, pressed_for) VALUES (?, ?, ?)', (self._key(job), now.isoformat(), ''))
            con.commit()
        finally:
            con.close()

    def pressed(self, job, moment):
        con = sqlite3.connect(self.db)
        try:
            con.execute('UPDATE runtime_clock SET pressed_for = ? WHERE job = ?', (moment.isoformat(), self._key(job)))
            con.commit()
        finally:
            con.close()


class Clock:
    """jobs: scheduled() and press(job) (WidJobs, or a test's fake). held(agent_key) -> (ok, why): the locker holds it and FROST
    approved its exact hashes (Harness.verify_now). then(): run once after any press (the catch-up). wid_zone: the zone wid's
    data_job_last_run_at is written in (wid's own local time; this computer's when not named)."""

    def __init__(self, jobs, held, memory, then=None, wid_zone=None):
        self.jobs, self.held, self.memory, self.then = jobs, held, memory, then
        self.wid_zone = wid_zone or datetime.datetime.now().astimezone().tzinfo

    def tick(self, now):
        """One look at every job. -> [(job key, what happened)], keys and words only, never a job's data."""
        said, pressed = [], 0
        for job in self.jobs.scheduled():
            key = str(job.get('job_key') or '')
            if _f(job, 'schedule_type').lower() in NEVER:
                continue
            moment = latest(job, now)
            if moment is None:
                continue
            mem = self.memory.get(job)
            if mem is None:
                self.memory.seen(job, now)
                mem = (now, None)
            last = [t for t in (last_run_of(job, self.wid_zone), mem[0], mem[1]) if t is not None]
            if not due(job, now, max(last) if last else None):
                continue
            agent = str(job.get('agent_key') or job.get('data_agent_key') or '')
            ok, why = self.held(agent) if agent else (False, 'no agent')
            if not ok:   # this moment is looked at once: skipped, never tried again
                self.memory.pressed(job, moment)
                LOG.warning('clock: %s due, not pressed: its agent %s is not held (%s)', key, agent or '-', why)
                said.append((key, f'skipped: {why}'))
                continue
            status, body = self.jobs.press(job)
            if status != 0:   # wid answered (a RUN queued, or its refusal): this moment is done; no answer: tried on the next tick
                self.memory.pressed(job, moment)
            body = body if isinstance(body, dict) else {}
            queued = status == 200 and body.get('ok') is True
            words = str(body.get('text') or body.get('refused') or '')[:120]
            LOG.warning('clock: %s pressed for %s: wid answered %s', key, moment.isoformat(), status)
            said.append((key, f'queued: {words}' if queued else f'not queued: {status} {words}'.rstrip()))
            pressed += 1 if queued else 0
        if pressed and self.then is not None:
            self.then()
        return said


class Clocks:
    """Every source's clock as one (the catch-up's sources: one per slot on a keyed runtime, else one), the catch-up run once
    after any tick that queued a RUN. tick(now) -> [(job key, what happened)]; loop and start: the in-process tick."""

    def __init__(self, clocks, then=None):
        self.clocks, self.then = list(clocks), then

    def tick(self, now):
        said = [s for c in self.clocks for s in c.tick(now)]
        if self.then is not None and any(w.startswith('queued') for _k, w in said):
            self.then()
        return said

    def loop(self, stop, every=TICK_SECONDS, now=None):
        """Tick every `every` seconds until stop (a threading.Event) is set; a tick that fails is logged by its kind only."""
        now = now or (lambda: datetime.datetime.now(datetime.timezone.utc))
        while not stop.is_set():
            try:
                self.tick(now())
            except Exception as error:   # the clock never stops for one bad tick
                LOG.error('clock: a tick failed: %s', type(error).__name__)
            stop.wait(every)

    def start(self, every=TICK_SECONDS):
        """The loop on its own thread (this computer's runtime). -> the Event that stops it."""
        stop = threading.Event()
        threading.Thread(target=self.loop, args=(stop, every), daemon=True, name='clock').start()
        return stop
