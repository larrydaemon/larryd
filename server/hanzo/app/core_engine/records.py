"""THE RUN RECORDS (the LARRYD runtime design, 2026-10-06, decisions 2 and 8): one record per call and run, written by
the runtime only (the platform reads them to reconcile; mTok alone charges). On a laptop or a test they live in hanzo.db;
on Cloud Run in Firestore (`runs`), because an instance's own disk is gone the moment it stops, and they are kept 13
months (Firestore's own TTL on expire_at). A record holds keys, states, times and counts: never a record value, an
input or a delivery (data stays in wid)."""
import datetime
import secrets
import sqlite3

KEEP_DAYS = 396   # 13 months: past a year of billing disputes


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class SqliteRecords:
    """The laptop's and the tests' records: hanzo.db's hanzo_runs, as before."""
    def __init__(self, db):
        self.db = db

    def record(self, lane, agent_key, state, reason='', job_key='', run=0, charged=0, caller='', account='', member=''):
        at = _now().isoformat(timespec='seconds')
        con = sqlite3.connect(self.db)
        try:
            con.execute('INSERT INTO hanzo_runs (lane, agent_key, job_key, run, state, reason, started_at, finished_at, charged) VALUES (?,?,?,?,?,?,?,?,?)',
                        (lane, agent_key, job_key, run, state, reason, at, at, charged))
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
            return con.execute('SELECT COUNT(*) FROM hanzo_runs' + (' WHERE ' + ' AND '.join(where) if where else ''), args).fetchone()[0]
        finally:
            con.close()

    def by_state(self, agent_key, lane):
        con = sqlite3.connect(self.db)
        try:
            return dict(con.execute('SELECT state, COUNT(*) FROM hanzo_runs WHERE agent_key = ? AND lane = ? GROUP BY state', (agent_key, lane)).fetchall())
        finally:
            con.close()

    def charged(self, agent_key):
        con = sqlite3.connect(self.db)
        try:
            return con.execute("SELECT COALESCE(SUM(charged), 0) FROM hanzo_runs WHERE agent_key = ? AND lane = 'job'", (agent_key,)).fetchone()[0]
        finally:
            con.close()


class FirestoreRecords:
    """Cloud Run's records: Firestore `runs`, one document per call or run, the 13-month expire_at its TTL field. The
    runtime is their only writer. `col` may be given (a test's fake); otherwise the real client."""
    STATES = ('DONE', 'FAILED', 'REFUSED', 'ON', 'OFF', 'INTERRUPTED')

    def __init__(self, col=None):
        if col is None:
            from google.cloud import firestore   # only on the server
            col = firestore.Client().collection('runs')
        self.col = col

    def record(self, lane, agent_key, state, reason='', job_key='', run=0, charged=0, caller='', account='', member=''):
        at = _now()
        self.col.document(secrets.token_hex(16)).create({
            'lane': lane, 'agent_key': agent_key, 'job_key': job_key, 'run': int(run), 'state': state, 'reason': reason,
            'caller': caller, 'account': account, 'member': member, 'started_at': at, 'finished_at': at, 'charged': int(charged),
            'expire_at': at + datetime.timedelta(days=KEEP_DAYS)})

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
        for s in self.STATES:
            n = self.count(agent_key, lane, s)
            if n:
                out[s] = n
        return out

    def charged(self, agent_key):
        return sum(int((d.to_dict() or {}).get('charged') or 0) for d in self._query(agent_key, 'job').stream())
