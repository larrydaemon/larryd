"""THE RUN RECORDS (the LARRYD runtime design, 2026-10-06, decisions 2 and 8): one record per call and run, written by
the runtime only (the platform reads them to reconcile; mTok alone charges). On a laptop or a test they live in runtime.db;
on Cloud Run in Firestore (`runs`), because an instance's own disk is gone the moment it stops, and they are kept 13
months (Firestore's own TTL on expire_at). A record holds keys, states, times and counts: never a record value, an
input or a delivery (data stays in wid)."""
import datetime
import re
import secrets
import sqlite3

KEEP_DAYS = 396   # 13 months: past a year of billing disputes
KEY = re.compile(r'^[A-Z]{4}_[0-9A-F]{12}_[0-9A-F]{4}$')   # a platform key, as the platform mints it
LANES = ('call', 'hire', 'job', 'selftest')
STATES = ('DONE', 'FAILED', 'REFUSED', 'ON', 'OFF', 'INTERRUPTED', 'CALLBACK_FAILED')   # CALLBACK_FAILED: the run ended, its result never reached the platform
CALLERS = ('', 'slot-a', 'slot-b', 'proof', 'selftest')
DOMAIN = re.compile(r'^[a-z0-9.-]{1,253}$')


def error_code(reason):
    """An error is a short CODE, never its text (the text may carry what a run was handed or what the platform said):
    the words before the first ':', '·', a bracket or a quote (the runtime's own fixed phrase; what follows may be data), letters and digits only, at most six words,
    upper case. '' stays ''."""
    head = re.split(r'[:\u00b7(\[{"\']', str(reason or ''), maxsplit=1)[0]
    words = [w for w in (re.sub(r'[^A-Za-z0-9]', '', w) for w in head.split()) if w][:6]
    return '_'.join(words)[:64].upper()


def _checked(lane, agent_key, state, job_key, run, charged, caller, account, member, egress_refused):
    """THE ALLOW LIST (the security review, 2026-10-06): a run record holds the design's fields only, each in its own
    form; anything else is refused before it is written."""
    if lane not in LANES or state not in STATES or caller not in CALLERS:
        raise ValueError('not a run record: lane, state or caller')
    for key in (agent_key, job_key, account, member):
        if key and not KEY.fullmatch(str(key)):
            raise ValueError('not a run record: a key is not a platform key')
    if not isinstance(run, int) or not isinstance(charged, int) or run < 0 or charged < 0:
        raise ValueError('not a run record: run and usage are counts')
    domains = list(egress_refused or ())
    if any(not isinstance(d, str) or not DOMAIN.fullmatch(d) for d in domains):
        raise ValueError('not a run record: an egress refusal is a domain')
    return domains


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class SqliteRecords:
    """The laptop's and the tests' records: runtime.db's runtime_runs, as before."""
    def __init__(self, db):
        self.db = db

    def record(self, lane, agent_key, state, reason='', job_key='', run=0, charged=0, caller='', account='', member='',
               egress_refused=(), **extra):
        if extra:
            raise ValueError(f'not a run record field: {sorted(extra)}')
        at = _now().isoformat(timespec='seconds')
        con = sqlite3.connect(self.db)
        try:
            con.execute('INSERT INTO runtime_runs (lane, agent_key, job_key, run, state, reason, started_at, finished_at, charged) VALUES (?,?,?,?,?,?,?,?,?)',
                        (lane, agent_key, job_key, int(run), state, error_code(reason), at, at, int(charged)))
            con.commit()
        finally:
            con.close()

    def count(self, agent_key=None, lane=None, state=None):
        where, args = [], []
        for col, val in (('agent_key', agent_key), ('lane', lane), ('state', state)):
            if val is not None:
                where.append(f'{col} = ?')
                args.append(val)
        con = sqlite3.connect(self.db)
        try:
            return con.execute('SELECT COUNT(*) FROM runtime_runs' + (' WHERE ' + ' AND '.join(where) if where else ''), args).fetchone()[0]
        finally:
            con.close()

    def by_state(self, agent_key, lane):
        con = sqlite3.connect(self.db)
        try:
            return dict(con.execute('SELECT state, COUNT(*) FROM runtime_runs WHERE agent_key = ? AND lane = ? GROUP BY state', (agent_key, lane)).fetchall())
        finally:
            con.close()

    def charged(self, agent_key):
        con = sqlite3.connect(self.db)
        try:
            return con.execute("SELECT COALESCE(SUM(charged), 0) FROM runtime_runs WHERE agent_key = ? AND lane = 'job'", (agent_key,)).fetchone()[0]
        finally:
            con.close()


class FirestoreRecords:
    """Cloud Run's records: Firestore `runs`, one document per call or run, the 13-month expire_at its TTL field. The
    runtime is their only writer. `col` may be given (a test's fake); otherwise the real client."""

    def __init__(self, col=None):
        if col is None:
            from google.cloud import firestore   # only on the server
            col = firestore.Client().collection('runs')
        self.col = col

    FIELDS = ('lane', 'agent_key', 'job_key', 'run', 'state', 'error_code', 'caller', 'account', 'member', 'started_at',
              'finished_at', 'charged', 'egress_refused', 'expire_at')

    def record(self, lane, agent_key, state, reason='', job_key='', run=0, charged=0, caller='', account='', member='',
               egress_refused=(), **extra):
        """The design's fields only, checked (an unknown field, or a value not in its form, is refused before anything is
        written); an error is kept as its code, never its text."""
        if extra:
            raise ValueError(f'not a run record field: {sorted(extra)}')
        domains = _checked(lane, agent_key, state, job_key, int(run), int(charged), caller, account, member, egress_refused)
        at = _now()
        doc = {'lane': lane, 'agent_key': agent_key, 'job_key': job_key, 'run': int(run), 'state': state, 'error_code': error_code(reason),
               'caller': caller, 'account': account, 'member': member, 'started_at': at, 'finished_at': at, 'charged': int(charged),
               'egress_refused': domains, 'expire_at': at + datetime.timedelta(days=KEEP_DAYS)}
        assert tuple(doc) == self.FIELDS
        self.col.document(secrets.token_hex(16)).create(doc)

    def _query(self, agent_key=None, lane=None, state=None):
        q = self.col
        for field, val in (('agent_key', agent_key), ('lane', lane), ('state', state)):
            if val is not None:
                q = q.where(field_path=field, op_string='==', value=val)
        return q

    def count(self, agent_key=None, lane=None, state=None):
        q = self._query(agent_key, lane, state)
        if hasattr(q, 'count'):
            try:
                return int(q.count().get()[0][0].value)
            except (AttributeError, IndexError, TypeError):
                pass
        return sum(1 for _ in q.stream())

    def by_state(self, agent_key, lane):
        out = {}
        for s in STATES:
            n = self.count(agent_key, lane, s)
            if n:
                out[s] = n
        return out

    def charged(self, agent_key):
        return sum(int((d.to_dict() or {}).get('charged') or 0) for d in self._query(agent_key, 'job').stream())
