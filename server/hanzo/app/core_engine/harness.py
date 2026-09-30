"""THE HARNESS: how HANZO answers the platform. Everything it knows about a member comes from the platform over the
one signed client (the cards, the member's hired shells, the account's subscriptions, FROST's approvals); every agent
runs in the sandbox; every call and run is a hanzo_runs row. Nothing is assumed when the platform does not answer.
DATA STAYS IN wid (the owner): what a run is handed lives in memory and its run folder only; its result goes back to wid
and is not kept; hanzo.db never holds a record value, a delivery, an account or a member.
An agent counts as verified only when its folder matches the locker AND FROST approved those exact hashes."""
import base64
import binascii
import datetime
import hashlib
import json
import pathlib
import re
import sqlite3

from . import gate, lanes, locker, sandbox

MARKETPLACE = 'marketplace'   # the one agent's locker folder: it answers the collection, hires, and places defaults
HANDS = ('cards', 'job')      # what a RUN can be handed: the cards the member sees; the job's own inputs (read from wid, kept nowhere)
SLOT = re.compile(r'^0(0[1-9]|1[0-5])$')   # a job's agent input slots, as wid's jobs species holds them: data_job_001 .. data_job_015
MOST_INPUT = 10_000           # characters in one input


def _skills():
    """{hash: definition}: the skills an agent may declare (schemas/skills.json), each by the sha256 of its definition."""
    listed = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'schemas' / 'skills.json').read_text())['skills']
    return {hashlib.sha256(json.dumps(s, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest(): s for s in listed}


SKILLS = _skills()
MOST_FILES = 10   # what the DA-M store keeps from one answer (all of it inside the sandbox's 1 MB answer)
FILE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 ._-]{0,120}$')
HANDED = {   # a skill's hand: the platform's door HANZO asks for the RUN's member and account (signed with hanzo_link)
    'greeting': ('lryllm', '/larry/greeting', "the member's greeting", 'LARRY LLM'),
    'identity': ('fs', '/agents/identity', 'who the agent works for', 'FROST'),
}



def _outside_gives(manifest, answer):
    """What the manifest's "gives" names is all an answer may hold (as `larryd run` holds it on the developer's computer):
    -> '' when it holds nothing else, or why not, in the words the member's job log shows."""
    gives = manifest.get('gives')
    if not (isinstance(gives, list) and all(isinstance(g, str) for g in gives)):
        return 'the agent declares no "gives": nothing it answers can be delivered'
    extra = sorted(set(answer) - set(gives))
    return f'the answer holds {extra}, which "gives" does not name' if extra else ''

class _Stop(Exception):
    def __init__(self, state, reason):
        super().__init__(reason)
        self.state, self.reason = state, reason


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

    def review_state(self, keys):
        """What HANZO records for these agents (the owner's `review` command): held or not, FROST's word on the exact
        hashes, and the counts of hanzo_runs (runs by state, calls, hires, unhires, mTok charged). Only agent keys and
        counts: no account, no member."""
        approved = None   # FROST's approved list, asked only when FROST has no review_state door (a FROST before it)
        con = sqlite3.connect(self.db)
        try:
            out = []
            for key in keys:
                row = locker.held(self.db, key)
                note = ''
                if row is None:
                    review = 'not submitted'
                else:
                    review, note, approved = self._review(key, row, approved)
                runs = dict(con.execute("SELECT state, COUNT(*) FROM hanzo_runs WHERE agent_key = ? AND lane = 'job' GROUP BY state", (key,)).fetchall())
                count = lambda lane, state=None: con.execute(  # noqa: E731
                    'SELECT COUNT(*) FROM hanzo_runs WHERE agent_key = ? AND lane = ?' + (' AND state = ?' if state else ''),
                    (key, lane) + ((state,) if state else ())).fetchone()[0]
                charged = con.execute("SELECT COALESCE(SUM(charged), 0) FROM hanzo_runs WHERE agent_key = ? AND lane = 'job'", (key,)).fetchone()[0]
                out.append({'agent_key': key, 'held': row is not None, 'code_sha256': row['code_sha256'] if row else '',
                            'manifest_sha256': row['manifest_sha256'] if row else '', 'review': review, 'note': note, 'runs': runs,
                            'calls': count('call'), 'hires': count('hire', 'ON'), 'unhires': count('hire', 'OFF'), 'charged': charged})
            return {'agents': out}
        finally:
            con.close()

    def _review(self, key, row, approved):
        """FROST's word on these exact hashes: -> (review, note, approved). waiting · approved · rejected (with FROST's
        reason) · not submitted, from FROST's review_state door; a FROST without that door (404) is read the older way,
        its approved list (approved · not approved); a silent FROST is said as unknown."""
        status, body = self.client.get('fs', '/agents/review_state', {'agent_key': key, 'code_sha256': row['code_sha256'],
                                                                       'manifest_sha256': row['manifest_sha256']})
        if status == 200:
            return body.get('state', 'unknown'), body.get('note', '') if body.get('state') == 'rejected' else '', approved
        if status == 404:
            if approved is None:
                s, listed = self.client.get('fs', '/agents/approved', {})
                if s != 200:
                    return f"unknown: {listed.get('refused') or f'FROST answered {s}'}", '', None
                approved = {(a['agent_key'], a['code_sha256'], a['manifest_sha256']) for a in listed['approved']}
            return ('approved' if (key, row['code_sha256'], row['manifest_sha256']) in approved else 'not approved'), '', approved
        return f"unknown: {body.get('refused') or body.get('error') or f'FROST answered {status}'}", '', approved

    # ---------------------------------------------------------------- the record
    def _record(self, lane, agent_key, state, reason='', job_key='', run=0, charged=0):
        """One row per call and run: the agent's key, the job's, its state, times, charge and a plain reason; never an
        account, a member, an input or a delivery (data stays in wid)."""
        con = sqlite3.connect(self.db)
        try:
            con.execute('INSERT INTO hanzo_runs (lane, agent_key, job_key, run, state, reason, started_at, finished_at, charged) VALUES (?,?,?,?,?,?,?,?,?)',
                        (lane, agent_key, job_key, run, state, reason, _now(), _now(), charged))
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
            self._record('call', agent_key, 'REFUSED', why)
            raise Refused(403, why)
        state, answer, reason = sandbox.run(self.agents / held['folder'], locker.manifest(self.agents, held['folder'])['entry'],
                                            {'do': calls[0], 'cards': lanes.assemble(cards, hired, groups, verify)}, self.seconds)
        outside = _outside_gives(locker.manifest(self.agents, held['folder']), answer) if state == 'DONE' else ''
        if outside:
            state, reason = 'FAILED', outside
        self._record('call', agent_key, state, reason)
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
        done = self._ask('wid', 'POST', '/agnt/hire' if on else '/agnt/unhire', {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key})
        self._record('hire', agent_key, 'ON' if on else 'OFF')   # the agent's key only: who hired it stays in wid
        return done

    def defaults(self, account, scope, member, board):
        """A board's first visit (the platform asks once): the marketplace is placed on its own screen, when it may be shown."""
        key = self.marketplace_key()
        cards, hired, groups, verify = self.facts(account, scope, member)
        card = self._card(lanes.assemble(cards, hired, groups, verify), key)
        if card is None or card['screen'] != board or card['hired'] or not card['hireable']:
            return {'placed': []}
        self._ask('wid', 'POST', '/agnt/hire', {'account': account, 'scope': scope, 'member': member, 'agent_key': key})
        self._record('hire', key, 'ON')
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
        if set(hands) - set(HANDS):
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f"HANZO cannot hand {sorted(set(hands) - set(HANDS))} yet")
        given = {'do': plan.get('do', 'run')}
        try:
            given.update(self._skill_hands(manifest, account, scope, member, job_key, run))
        except _Stop as stop:
            return self._end(account, scope, member, key, job_key, run, stop.state, stop.reason)
        if 'job' in hands:
            try:
                given['job'] = self._job_inputs(manifest, account, scope, job_key, run)
            except _Stop as stop:
                return self._end(account, scope, member, key, job_key, run, stop.state, stop.reason)
        self._result(account, scope, job_key, run, 'RUNNING', f'RUN {run} RUNNING')
        if 'cards' in hands:
            given['cards'] = lanes.assemble(cards, hired, groups, verify)
        state, answer, reason = sandbox.run(self.agents / folder, manifest['entry'], given, self.seconds)
        if state != 'DONE':
            return self._end(account, scope, member, key, job_key, run, 'FAILED', reason)
        outside = _outside_gives(manifest, answer)
        if outside:
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f'{outside}; the delivery is withheld')
        try:
            files = self._files(manifest, answer)
        except _Stop as stop:
            return self._end(account, scope, member, key, job_key, run, stop.state, stop.reason)
        status, body = self.client.post('cc', '/mtok/use', {'account': account, 'member': member, 'agent_key': key,
                                                            'job_key': f'{job_key}#{run}', 'agent_group': card['product_slug'], 'rate': str(gate.rate(card))})
        if status != 200:
            return self._end(account, scope, member, key, job_key, run, 'FAILED',
                             f"not charged: {body.get('refused') or f'mTok answered {status}'}; the delivery is withheld")
        charged = int(body.get('charged') or 0)
        paid = 'free' if body.get('free') else f"{charged} mTok from the {body.get('paid_from')}"
        for f in files:
            status, stored = self.client.post('so', '/dam/upload', {'account': account, 'scope': scope, 'member': member, 'job_key': job_key,
                                                                   'run': str(run), 'name': f['name'], 'content_b64': f['content_b64'], 'source_key': key})
            if status != 200:
                return self._end(account, scope, member, key, job_key, run, 'FAILED',
                                 f"{paid}, but DA-M did not store the files: {stored.get('refused') or stored.get('error') or f'DA-M answered {status}'}", charged=charged)
        kept = {k: v for k, v in answer.items() if k != 'files'}
        delivery = answer.get('delivery') if isinstance(answer.get('delivery'), str) else json.dumps(kept, sort_keys=True)
        stored_note = f" · {len(files)} file{'' if len(files) == 1 else 's'} in DA-M" if files else ''
        return self._end(account, scope, member, key, job_key, run, 'DONE', f'RUN {run} DONE · {paid}{stored_note}', charged=charged, delivery=delivery)

    def _files(self, manifest, answer):
        """The files an answer carries, checked before anything is charged: [] when none; refused when the agent does not
        declare the DA-M store, or they are not [{name, content_b64}] within the limits."""
        files = answer.get('files')
        if files is None:
            return []
        if not any(SKILLS.get(h, {}).get('after') == 'files' for h in manifest.get('skills') or [] if isinstance(h, str)):
            raise _Stop('FAILED', 'the answer carries files, but the agent does not declare the DA-M store; the delivery is withheld')
        if not isinstance(files, list) or len(files) > MOST_FILES:
            raise _Stop('FAILED', f'the answer\'s files are not a list of at most {MOST_FILES}; the delivery is withheld')
        for i, f in enumerate(files, 1):
            if not (isinstance(f, dict) and set(f) == {'name', 'content_b64'} and isinstance(f['name'], str) and FILE_NAME.match(f['name'])
                    and isinstance(f['content_b64'], str)):
                raise _Stop('FAILED', f'file {i} is not {{name, content_b64}} with a plain name; the delivery is withheld')
            try:
                size = len(base64.b64decode(f['content_b64'], validate=True))
            except (binascii.Error, ValueError):
                raise _Stop('FAILED', f'file {i} is not base64; the delivery is withheld')
            if size == 0:
                raise _Stop('FAILED', f'file {i} is empty; the delivery is withheld')
        return files

    def _skill_hands(self, manifest, account, scope, member, job_key, run):
        """The skills the agent declares, carried out before the RUN: -> {hand: what it hands}. A skill HANZO does not have
        fails the run; a skill with no hand (the mTok charge) hands nothing. What is handed is kept nowhere. Each call names
        the RUN it is for (scope, job_key, run): the platform answers only for a member of a RUN that is open now."""
        declared = manifest.get('skills') or []
        if not (isinstance(declared, list) and all(isinstance(h, str) for h in declared)):
            raise _Stop('FAILED', 'the agent\'s skills are not a list of hashes')
        unknown = [h for h in declared if h not in SKILLS]
        if unknown:
            raise _Stop('FAILED', f'the agent declares a skill HANZO does not have: {unknown[0][:12]}')
        out = {}
        for h in declared:
            hand = SKILLS[h].get('hand')
            if hand not in HANDED:
                continue
            office, route, what, who = HANDED[hand]
            status, body = self.client.get(office, route, {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run)})
            if status != 200:
                raise _Stop('FAILED', f"HANZO could not read {what}: {body.get('refused') or body.get('error') or f'{who} answered {status}'}")
            out[hand] = body
        return out

    def _job_inputs(self, manifest, account, scope, job_key, run):
        """The job's own inputs, as the agent declares them ({name: slot}), read from wid for this RUN only: -> {name: value}.
        Held in memory for the run, never kept (data stays in wid); a reason names slots, never a value."""
        declared = manifest.get('inputs')
        if not (isinstance(declared, dict) and declared and all(isinstance(n, str) and n.isidentifier() and isinstance(s, str) and SLOT.match(s)
                                                                for n, s in declared.items()) and len(set(declared.values())) == len(declared)):
            raise _Stop('FAILED', 'the agent hands "job" but its inputs are not {name: slot 001-015}, one slot each')
        status, body = self.client.get('wid', '/jobs/inputs', {'account': account, 'scope': scope, 'job_key': job_key, 'run': str(run)})
        if status != 200:
            raise _Stop('FAILED', f"HANZO could not read the job's inputs: {body.get('refused') or body.get('error') or f'wid answered {status}'}")
        held = body.get('inputs')
        if not isinstance(held, dict):
            raise _Stop('FAILED', "HANZO could not read the job's inputs: not {slot: value}")
        extra = sorted(set(held) - set(declared.values()))
        if extra:
            raise _Stop('REFUSED', f"the job holds input {', '.join(extra)}, which the agent does not declare")
        for slot, value in sorted(held.items()):
            if not isinstance(value, str):
                raise _Stop('REFUSED', f'input {slot} is not text')
            if len(value) > MOST_INPUT:
                raise _Stop('REFUSED', f'input {slot} is larger than {MOST_INPUT} characters')
        return {name: held[slot] for name, slot in declared.items() if slot in held}

    def _end(self, account, scope, member, key, job_key, run, state, log, charged=0, delivery=''):
        reason = '' if state == 'DONE' else log
        try:
            self._result(account, scope, job_key, run, state, log, delivery)
        except Refused as lost:
            reason = f'{reason} · the platform did not take the result: {lost.reason}'.lstrip(' ·')
        self._record('job', key, state, reason, job_key, int(run), charged)
        return state
