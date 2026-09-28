"""THE HARNESS: how HANZO answers the platform. Everything it knows about a member comes from the platform over the
one signed client (the cards, the member's hired shells, the account's subscriptions, FROST's approvals); every agent
runs in the sandbox; every call and run is a hanzo_runs row. Nothing is assumed when the platform does not answer.
An agent counts as verified only when its folder matches the locker AND FROST approved those exact hashes."""
import datetime
import hashlib
import json
import sqlite3

from . import gate, lanes, locker, sandbox

MARKETPLACE = 'marketplace'   # the one agent's locker folder: it answers the collection, hires, and places defaults


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
        """(cards, hired, groups, verify): the platform's word now; verify(key) -> (ok, why) by the locker and FROST."""
        cards = self._ask('wid', 'GET', '/agnt/cards', {})['cards']
        hired = self._ask('wid', 'GET', '/agnt/hired', {'account': account, 'scope': scope, 'member': member})['hired']
        groups = lanes.groups(self._ask('cc', 'GET', '/mtok/balance', {'account': account}))
        approved = {(a['agent_key'], a['code_sha256'], a['manifest_sha256']) for a in self._ask('fs', 'GET', '/agents/approved', {})['approved']}
        return cards, hired, groups, self._verifier(approved)

    def _verifier(self, approved):
        def verify(agent_key):
            ok, why = locker.verify(self.db, self.agents, agent_key)
            if not ok:
                return ok, why
            row = locker.held(self.db, agent_key)
            if (agent_key, row['code_sha256'], row['manifest_sha256']) not in approved:
                return False, 'not approved by FROST'
            return True, ''
        return verify

    def submit(self, agent_key):
        """HANZO submits an agent it holds to FROST's review: its key, its exact hashes, its manifest."""
        ok, why = locker.verify(self.db, self.agents, agent_key)
        if not ok:
            raise Refused(409, why)
        row = locker.held(self.db, agent_key)
        return self._ask('fs', 'POST', '/agents/submit', {'agent_key': agent_key, 'name': row['name'], 'code_sha256': row['code_sha256'],
                                                          'manifest_sha256': row['manifest_sha256'], 'manifest': locker.manifest(self.agents, row['folder'])})

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

    @staticmethod
    def _card(cards, key):
        return next((c for c in cards if c['key'] == key), None)

    # ---------------------------------------------------------------- the CALL lane: an agent answers now
    def answer(self, account, scope, member, agent_key):
        """An agent's answer for the member's screen: only an agent that answers calls, passing the gate itself."""
        held = locker.held(self.db, agent_key)
        calls = locker.manifest(self.agents, held['folder']).get('calls') if held else None
        if not calls:
            raise Refused(404, 'no agent that answers here')
        cards, hired, groups, verify = self.facts(account, scope, member)
        card = self._card(cards, agent_key)
        if card is None:
            raise Refused(404, 'the agent has no LIVE card')
        ok, why = gate.may_run(card, verify(agent_key), lanes.hired_on(hired, agent_key), groups)
        if not ok:
            self._record('call', account, member, agent_key, 'REFUSED', why)
            raise Refused(403, why)
        state, answer, reason = sandbox.run(self.agents / held['folder'], locker.manifest(self.agents, held['folder'])['entry'],
                                            {'do': calls[0], 'cards': lanes.assemble(cards, hired, groups, verify)}, self.seconds)
        self._record('call', account, member, agent_key, state, reason, delivery=answer)
        if state != 'DONE':
            raise Refused(500, reason)
        return {'agent_key': agent_key, 'title': card['name'], **answer}

    def hire(self, account, scope, member, agent_key, on):
        """THE MARKETPLACE'S HIRE: only a card in the collection the member may hire; the marketplace itself can always be hired again."""
        key = self.marketplace_key()
        cards, hired, groups, verify = self.facts(account, scope, member)
        mcard = self._card(cards, key)
        if mcard is None:
            raise Refused(503, 'the marketplace has no card on the platform')
        ok, why = gate.may_run(mcard, verify(key), lanes.hired_on(hired, key), groups)
        if not ok and agent_key != key:
            raise Refused(403, why)
        card = self._card(lanes.assemble(cards, hired, groups, verify), agent_key)
        if card is None:
            raise Refused(404, 'no such agent in the collection')
        if on and not card['hireable']:
            raise Refused(403, card['reason'])
        return self._ask('wid', 'POST', '/agnt/hire' if on else '/agnt/unhire', {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key})

    def defaults(self, account, scope, member, board):
        """A board's first visit (the platform asks once): the marketplace is placed on its own screen, when it may be shown."""
        key = self.marketplace_key()
        cards, hired, groups, verify = self.facts(account, scope, member)
        card = self._card(lanes.assemble(cards, hired, groups, verify), key)
        if card is None or card['screen'] != board or card['hired'] or not card['hireable']:
            return {'placed': []}
        self._ask('wid', 'POST', '/agnt/hire', {'account': account, 'scope': scope, 'member': member, 'agent_key': key})
        return {'placed': [key]}

    # ---------------------------------------------------------------- the JOB lane: a RUN, pushed by the platform
    def _result(self, account, scope, job_key, run, state, log, delivery=''):
        return self._ask('wid', 'POST', '/jobs/result', {'account': account, 'scope': scope, 'job_key': job_key, 'run': str(run),
                                                        'state': state, 'log': log, 'delivery': delivery})

    def run_job(self, account, scope, member, job_key, run):
        """-> the state it ended in. Refused and failed runs are written back and recorded like done ones."""
        try:
            cards, hired, groups, verify = self.facts(account, scope, member)
        except Refused as silent:
            return self._end(account, scope, member, '', job_key, run, 'FAILED', f'HANZO could not read the platform: {silent.reason}')
        shell = next((h for h in hired if h.get('job_key') == job_key), None)
        if shell is None:
            return self._end(account, scope, member, '', job_key, run, 'REFUSED', 'the job is not in a hired shell')
        key = shell['agent_key']
        card = self._card(cards, key)
        if card is None:
            return self._end(account, scope, member, key, job_key, run, 'REFUSED', 'the agent has no LIVE card')
        ok, why = gate.may_run(card, verify(key), shell.get('on') is True, groups)
        if not ok:
            return self._end(account, scope, member, key, job_key, run, 'REFUSED', why)
        folder = locker.held(self.db, key)['folder']
        manifest = locker.manifest(self.agents, folder)
        plan = manifest.get('run') or {}
        hands = plan.get('hands') or []
        if set(hands) - {'cards'}:
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f"HANZO cannot hand {sorted(set(hands) - {'cards'})} yet")
        self._result(account, scope, job_key, run, 'RUNNING', f'RUN {run} RUNNING')
        given = {'do': plan.get('do', 'run')}
        if 'cards' in hands:
            given['cards'] = lanes.assemble(cards, hired, groups, verify)
        state, answer, reason = sandbox.run(self.agents / folder, manifest['entry'], given, self.seconds)
        if state != 'DONE':
            return self._end(account, scope, member, key, job_key, run, 'FAILED', reason)
        status, body = self.client.post('cc', '/mtok/use', {'account': account, 'member': member, 'agent_key': key,
                                                            'job_key': f'{job_key}#{run}', 'agent_group': card['product_slug'], 'rate': str(gate.rate(card))})
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
