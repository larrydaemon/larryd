"""THE HARNESS: how HANZO answers the platform. Everything it knows about a member comes from the platform over the
one signed client (the cards, the member's hired shells, the account's subscriptions); every agent runs in the
sandbox; every call and run is a hanzo_runs row. Nothing is assumed when the platform does not answer."""
import datetime
import hashlib
import json
import sqlite3

from . import gate, lanes, locker, sandbox

MARKETPLACE = 'marketplace'   # the one agent's locker folder


class Refused(Exception):
    def __init__(self, status, reason):
        super().__init__(reason)
        self.status, self.reason = status, reason


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


class Harness:
    def __init__(self, db, agents, client, seconds=20):
        self.db, self.agents, self.client, self.seconds = db, agents, client, seconds

    # ---------------------------------------------------------------- what the platform says
    def _ask(self, office, method, route, data):
        status, body = (self.client.get if method == 'GET' else self.client.post)(office, route, data)
        if status != 200:
            raise Refused(502 if status in (0, 500) else status, body.get('refused') or body.get('error') or f'{office} answered {status}')
        return body

    def facts(self, account, scope, member):
        cards = self._ask('wid', 'GET', '/agnt/cards', {})['cards']
        hired = self._ask('wid', 'GET', '/agnt/hired', {'account': account, 'scope': scope, 'member': member})['hired']
        groups = lanes.groups(self._ask('cc', 'GET', '/mtok/balance', {'account': account}))
        return cards, hired, groups

    def verify(self, agent_key):
        return locker.verify(self.db, self.agents, agent_key)

    def marketplace_key(self):
        con = sqlite3.connect(self.db)
        try:
            row = con.execute('SELECT agent_key FROM hanzo_locker WHERE folder = ?', (MARKETPLACE,)).fetchone()
        finally:
            con.close()
        if row is None:
            raise Refused(503, 'the marketplace is not in the locker')
        return row[0]

    # ---------------------------------------------------------------- the record
    def _record(self, lane, account, member, agent_key, state, reason='', job_key='', run=0, charged=0, delivery=None):
        con = sqlite3.connect(self.db)
        try:
            con.execute('INSERT INTO hanzo_runs (lane, account, member, agent_key, job_key, run, state, reason, started_at, finished_at, charged, delivery_sha256) '
                        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        (lane, account, member, agent_key, job_key, run, state, reason, _now(), _now(), charged,
                         '' if delivery is None else hashlib.sha256(json.dumps(delivery, sort_keys=True).encode('utf-8')).hexdigest()))
            con.commit()
        finally:
            con.close()

    def _card(self, cards, key):
        return next((c for c in cards if c['key'] == key), None)

    def _the_marketplace_may_answer(self, key, cards, hired, groups):
        card = self._card(cards, key)
        if card is None:
            raise Refused(503, 'the marketplace has no card on the platform')
        ok, why = gate.may_run(card, self.verify(key), lanes.hired_on(hired, key), groups)
        return ok, why

    # ---------------------------------------------------------------- the CALL lane: the marketplace answers now
    def collection(self, account, scope, member):
        key = self.marketplace_key()
        cards, hired, groups = self.facts(account, scope, member)
        ok, why = self._the_marketplace_may_answer(key, cards, hired, groups)
        if not ok:
            self._record('call', account, member, key, 'REFUSED', why)
            raise Refused(403, why)
        state, answer, reason = sandbox.run(self.agents / MARKETPLACE, 'agent.py',
                                            {'do': 'collection', 'cards': lanes.assemble(cards, hired, groups, self.verify)}, self.seconds)
        self._record('call', account, member, key, state, reason, delivery=answer)
        if state != 'DONE':
            raise Refused(500, reason)
        return answer

    def hire(self, account, scope, member, agent_key, on):
        key = self.marketplace_key()
        cards, hired, groups = self.facts(account, scope, member)
        ok, why = self._the_marketplace_may_answer(key, cards, hired, groups)
        if not ok and agent_key != key:   # the marketplace itself can always be hired again
            raise Refused(403, why)
        card = self._card(lanes.assemble(cards, hired, groups, self.verify), agent_key)
        if card is None:
            raise Refused(404, 'no such agent in the collection')
        if on and not card['hireable']:
            raise Refused(403, card['reason'])
        route = '/agnt/hire' if on else '/agnt/unhire'
        return self._ask('wid', 'POST', route, {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key})

    # ---------------------------------------------------------------- the JOB lane: a RUN, pushed by the platform
    def _result(self, account, scope, job_key, run, state, log, delivery=''):
        return self._ask('wid', 'POST', '/jobs/result', {'account': account, 'scope': scope, 'job_key': job_key, 'run': str(run),
                                                        'state': state, 'log': log, 'delivery': delivery})

    def run_job(self, account, scope, member, job_key, run):
        """-> the state it ended in. Refused and failed runs are written back and recorded like done ones."""
        try:
            cards, hired, groups = self.facts(account, scope, member)
        except Refused as silent:
            return self._end(account, scope, member, '', job_key, run, 'FAILED', f'HANZO could not read the platform: {silent.reason}')
        shell = next((h for h in hired if h.get('job_key') == job_key), None)
        if shell is None:
            return self._end(account, scope, member, '', job_key, run, 'REFUSED', 'the job is not in a hired shell')
        key = shell['agent_key']
        card = self._card(cards, key)
        if card is None:
            return self._end(account, scope, member, key, job_key, run, 'REFUSED', 'the agent has no LIVE card')
        ok, why = gate.may_run(card, self.verify(key), shell.get('on') is True, groups)
        if not ok:
            return self._end(account, scope, member, key, job_key, run, 'REFUSED', why)
        folder = locker.held(self.db, key)['folder']
        plan = locker.manifest(self.agents, folder).get('run') or {}
        hands = plan.get('hands') or []
        if set(hands) - {'cards'}:
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f"HANZO cannot hand {sorted(set(hands) - {'cards'})} yet")
        self._result(account, scope, job_key, run, 'RUNNING', f'RUN {run} RUNNING')
        given = {'do': plan.get('do', 'run')}
        if 'cards' in hands:
            given['cards'] = lanes.assemble(cards, hired, groups, self.verify)
        state, answer, reason = sandbox.run(self.agents / folder, locker.manifest(self.agents, folder)['entry'], given, self.seconds)
        if state != 'DONE':
            return self._end(account, scope, member, key, job_key, run, 'FAILED', reason)
        rate = gate.rate(card)
        status, body = self.client.post('cc', '/mtok/use', {'account': account, 'member': member, 'agent_key': key,
                                                            'job_key': f'{job_key}#{run}', 'agent_group': card['product_slug'], 'rate': str(rate)})
        if status != 200:
            return self._end(account, scope, member, key, job_key, run, 'FAILED',
                             f"not charged: {body.get('refused') or f'mTok answered {status}'}; the delivery is withheld")
        charged = int(body.get('charged') or 0)
        paid = 'free' if body.get('free') else f"{charged} mTok from the {body.get('paid_from')}"
        delivery = answer.get('delivery') if isinstance(answer.get('delivery'), str) else json.dumps(answer, sort_keys=True)
        return self._end(account, scope, member, key, job_key, run, 'DONE', f'RUN {run} DONE · {paid}', charged=charged, delivery=delivery)

    def _end(self, account, scope, member, key, job_key, run, state, log, charged=0, delivery=''):
        reason = '' if state == 'DONE' else log
        try:
            self._result(account, scope, job_key, run, state, log, delivery)
        except Refused as lost:
            reason = f'{reason} · the platform did not take the result: {lost.reason}'.lstrip(' ·')
        self._record('job', account, member, key, state, reason, job_key, int(run), charged, delivery or None)
        return state
