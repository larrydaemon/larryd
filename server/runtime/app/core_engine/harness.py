"""THE HARNESS: how the runtime answers the platform. Everything it knows about a member comes from the platform over the
one signed client, and only from wid (the core cleanup, the owner 2026-11-05: "no agents should have anything to do with cc,
fs, laryllm, so"): the cards, the member's hired shells, the account's subscriptions, and every service of a RUN (its charge,
its files, the provider key, the greeting, who the agent works for), each through a wid door that asks its office AS wid.
Every agent runs in the sandbox; every call and run is a runtime_runs row. Nothing is assumed when the platform does not answer.
DATA STAYS IN wid (the owner): what a run is handed lives in memory and its run folder only; its result goes back to wid
and is not kept; agents.db never holds a record value, a delivery, an account or a member.
TWO GUARDS, NEVER ONE (the owner's rule, 2026-10-04): an agent counts as verified only when its folder matches the locker
(LARRYD's own: held only by `place`, the owner's approved file) AND the platform approved those exact hashes (FROST's
review, asked through wid's /agnt/approved: the runtime never calls FROST itself)."""
import base64
import binascii
import datetime
import hashlib
import json
import logging
import os
import pathlib
import re
import sqlite3
import threading
import time

from . import exxact_hand, fabric, gate, lanes, live, locker, member_records, outside, records as run_records, sandbox, view

MARKETPLACE = 'marketplace'   # the one agent's locker folder: it answers the collection, hires, and places defaults
BESIDE = ('find', 'themes', 'page')   # what an ANSWER call may hand the agent beside its cards (the page's own: its controller's asks, the themes a card may wear, its loaded logos); each a JSON object
HANDS = ('cards', 'job', 'records', 'files')   # what a RUN can be handed: the cards the member sees; the job's own inputs (read from wid, kept nowhere); the member's records its approved manifest declares (CORE_CLEANUP_IV 30, the owner's blanket approval 2026-11-06: read as a CALL reads them, through wid's own list door, kept nowhere)
SLOT = re.compile(r'^0(0[1-9]|1[0-5])$')   # a job's agent input slots, as wid's jobs species holds them: data_job_001 .. data_job_015
MOST_INPUT = 10_000           # characters in one input
MOST_KEEPS = 10               # records one RUN may add for the files it stored
MOST_RUN_FILES = 3            # files one RUN may be handed (hands ["files"], CORE_CLEANUP_IV 21): the member's own DA-M files, named by the job's inputs the manifest declares as files
MOST_RUN_FILE = 20 * 1024 * 1024   # bytes of one handed file (a picture or a short video: the sandbox's 512 MB holds three, base64 and parsed)
RECORD_KEY = re.compile(r'^M[A-Z]{2,4}_[0-9A-F]{12}_[0-9A-F]{4}$')   # a member's record, as wid names the record a DA-M file belongs to (its source_key)
A_DAY = {'image': 25, 'video': 5, 'data': 25, 'audio': 25, 'text': 25}   # THE OUTSIDE HAND'S DAILY LIMIT, per member and agent (the provider is paid per file made; the runtime's own config may set others). data: an Exxact type that makes numbers, no file (outside.MODELS)
PLATFORM_HANDED = {('wid', 'GET', '/agnt/cards'), ('wid', 'GET', '/agnt/hired'), ('wid', 'GET', '/jobs/balance'), ('wid', 'GET', '/agnt/records/list')}
# THE PLATFORM'S ANSWERS HANDED WITH THE CALL (the owner 2026-11-04, "the goal is extremely fast"): what the platform would answer these
# asks of a CALL, its own doors' answers made at the platform with the same checks, handed in its signed call; nothing else is taken
# that way. The approval is never among them: the platform's approved list is the runtime's own word, asked of wid (APPROVED_KEEP)
HANDED_MOST = 64              # handed answers one call may carry
APPROVED_KEEP = 300           # seconds the platform's approved list is kept; an agent not on it is asked of wid again before it is refused
APPROVED_DOOR = '/agnt/approved'   # wid's: the exact hashes FROST's review approved, as wid reads them (the second guard)
LOCAL_CALLERS = ('proof',)   # THE LOCALHOST BOX: the caller slot of this Mac (runtime.json); only its calls may draw http links, and only to the origins the platform handed (CORE_CLEANUP_IV 20/96, ruling c')
RUNS_HANDED = 5               # the member's last RUNs of an agent that starts RUNs from its page, handed to its CALL (state and the runtime's own code, nothing else)
ZONE = ''                     # a made file goes to the member's DA-M with no zone named (DA-M's own general limit)


def _skills():
    """{hash: definition}: the skills an agent may declare (schemas/skills.json), each by the sha256 of its definition."""
    listed = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'schemas' / 'skills.json').read_text())['skills']
    return {hashlib.sha256(json.dumps(s, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest(): s for s in listed}


SKILLS = _skills()
MOST_FILES = 10   # what the DA-M store keeps from one answer (all of it inside the answer's own most, below)
STORE_ANSWER_MOST = 34 * 1024 * 1024   # THE ANSWER'S MOST for an agent that declares the DA-M store (frost-05 2026-11-06, row 92 pf fal): one
                                       # file up to DA-M's 25 MB as base64 and its words; every other agent keeps sandbox.MOST_BYTES (1 MB)


def answer_most(manifest):
    """How many bytes this agent's answer may be: STORE_ANSWER_MOST when its manifest declares the DA-M store skill (the very test _files
    makes), else the sandbox's own 1 MB. The sandbox reads at most this + 2 bytes and refuses past it: never held whole."""
    skills = manifest.get('skills') if isinstance(manifest, dict) else None
    stores = any(SKILLS.get(h, {}).get('after') == 'files' for h in (skills or []) if isinstance(h, str))
    return STORE_ANSWER_MOST if stores else sandbox.MOST_BYTES
FILE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 ._-]{0,120}$')
HANDED = {   # a skill's hand: the wid door the runtime asks for the RUN's member and account (wid asks LARRY LLM or FROST as itself)
    'greeting': ('wid', '/jobs/greeting', "the member's greeting", 'wid'),
    'identity': ('wid', '/jobs/identity', 'who the agent works for', 'wid'),
}



def _product(card):
    """The card's product as the page names its themes (INVOICE MAPS -> invoicemaps)."""
    product = card.get('product') if isinstance(card, dict) else ''
    return ''.join(c for c in product.lower() if c.isalnum()) if isinstance(product, str) else ''


RUNTIME_OWN = frozenset(('room', 'frame', 'keep'))   # THE RUNTIME'S OWN FIELDS OF AN ANSWER (the security review of the room rule, 2026-10-08): never an agent's word, whatever its "gives" names: an answer that holds one is refused whole


KEEPS = ('none', 'minute', 'day')


def _keep(manifest, given, not_read, act):
    """HOW LONG THE PLATFORM MAY DRAW THIS ANSWER AGAIN WITHOUT ASKING (the owner 2026-11-04, "the goal is extremely fast"; step E):
    the runtime's own word, from the approved manifest, never the agent's answer. 'none' whenever the view may hang on anything
    the platform did not hand (the runtime's own RUNs, a live room, the counts, records it could not read) or on the member's
    act; else what the manifest declares ("keep": "none" | "minute" | "day"), 'minute' when it declares nothing (an agent may
    say "in 15 minutes")."""
    if act or not_read or any(k in given for k in ('runs', 'running', 'live', 'counts')):
        return 'none'
    declared = manifest.get('keep')
    return declared if declared in KEEPS else 'minute'


def _outside_gives(manifest, answer):
    """What the manifest's "gives" names is all an answer may hold (as `larryd run` holds it on the developer's computer):
    -> '' when it holds nothing else, or why not, in the words the member's job log shows."""
    gives = manifest.get('gives')
    if not (isinstance(gives, list) and all(isinstance(g, str) for g in gives)):
        return 'the agent declares no "gives": nothing it answers can be delivered'
    extra = sorted(set(answer) - (set(gives) - RUNTIME_OWN))
    return f'the answer holds {extra}, which "gives" does not name' if extra else ''


def _first_line(text):
    """An internal agent's delivery, its first line alone, plain and short (its job's TODAY line)."""
    return ((text if isinstance(text, str) else '').strip().splitlines() or [''])[0][:280]


FILE_SLOTS = {'image': 'data_image_key', 'video': 'data_video_key', 'audio': 'data_audio_key'}   # THE STORED FILES' SLOTS (the owner 2026-11-05): the runtime's own word, never an agent's


def file_kind(data):
    """What a stored file IS, read from its first bytes (never its name): image, video, audio, or ''."""
    if data[:8] == b'\x89PNG\r\n\x1a\n' or data[:3] == b'\xff\xd8\xff' or (data[:4] == b'RIFF' and data[8:12] == b'WEBP') or data[:6] in (b'GIF87a', b'GIF89a'):
        return 'image'
    if (data[:4] == b'RIFF' and data[8:12] == b'WAVE') or data[:3] == b'ID3' or data[:4] in (b'OggS', b'fLaC') or (len(data) > 1 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return 'audio'
    if data[4:8] == b'ftyp':
        return 'audio' if data[8:12] in (b'M4A ', b'M4B ') else 'video'
    return ''


def stored_slots(slots, files, stored_keys):
    """THE JOB'S SLOTS AS THE RUNTIME SENDS THEM (the owner 2026-11-05): the agent's own, without the stored files' slots (those are
    the runtime's word: an agent's image, video or sound key is never kept); then, for each kind this RUN actually stored, the FIRST
    stored file's DA-M key in its slot, and every stored file's key listed in the payload. A RUN that stored nothing leaves them empty."""
    out = {k: v for k, v in (slots or {}).items() if k not in FILE_SLOTS.values()}
    listed = []
    for f in files:
        key = stored_keys.get(f['name'])
        if not key:
            continue
        kind = file_kind(base64.b64decode(f['content_b64']))
        if kind:
            out.setdefault(FILE_SLOTS[kind], key)
        listed.append(f"{kind or 'file'} {key}")
    if listed:
        said = str(out.get('data_job_payload') or '')
        out['data_job_payload'] = (said + '\n' if said else '') + 'stored in DA-M: ' + ', '.join(listed)
    return out or None


class _Stop(Exception):
    def __init__(self, state, reason):
        super().__init__(reason)
        self.state, self.reason = state, reason


class Refused(Exception):
    def __init__(self, status, reason):
        super().__init__(reason)
        self.status, self.reason = status, reason


LOG = logging.getLogger('runtime')
ANSWER_ROOM = 64 * 1024   # the words around a file's base64 in wid's /jobs/file answer (its key, name and kind), at most


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


class Harness:
    def __init__(self, db, agents, client, seconds=20, records=None, caller='', on_start=None, hand=None, a_day=None, exxact=None):
        """records: where every call and run is recorded (agents.db by default; Firestore on Cloud Run). caller: the key id
        of the office that called (a run record names it). on_start(pid): told each sandboxed run's process (the slot).
        hand: THE OUTSIDE HAND (core_engine/outside.py). a_day: {kind: files a member may have made in a day}.
        THE RUNTIME HOLDS NO PROVIDER KEY (the owner, 2026-10-08: "a single source setup"): the key's one home is the platform's
        vault (FROST's); each errand asks wid for it (_provider_key), wid reads the vault at that moment and hands it on the
        signed answer; the runtime uses it once and forgets it.
        exxact: THE EXXACT HAND (core_engine/exxact_hand.py), for an 'exxact/<type>' ask; none given, it is one NOT SET UP (the buckets
        and its keys are S4, later), so such an ask fails in fixed words. THE HAND IS CHOSEN BY THE MODEL'S PROVIDER (self.hands)."""
        self.db, self.agents, self.client, self.seconds = db, agents, client, seconds
        self.records = records if records is not None else run_records.SqliteRecords(db)
        self._here, self._on_start = threading.local(), on_start   # on_start: told per thread (the on_start property)
        self.caller = caller
        self.hand = hand if hand is not None else outside.Hand()
        self.hands = {'replicate': self.hand, 'exxact': exxact if exxact is not None else exxact_hand.ExxactHand()}
        self.a_day = {**A_DAY, **(a_day or {})}
        self._handed = threading.local()   # this request's handed answers (a call's own thread: pages answered at once never mix)
        self._approved = (0.0, None)       # the platform's approved list as last asked (monotonic time, the list)

    # ---------------------------------------------------------------- what the platform says
    @staticmethod
    def _handed_key(office, method, route, data):
        return office, method, route, json.dumps(data or {}, sort_keys=True)

    def handing(self, answers):
        """THE PLATFORM'S ANSWERS FOR THIS CALL: [{office, method, route, data, status, body}], each one of PLATFORM_HANDED (anything else,
        or a malformed one, is not taken: that ask goes to the platform as before). -> the number taken."""
        taken = {}
        for a in (answers if isinstance(answers, list) else [])[:HANDED_MOST]:
            if not isinstance(a, dict) or (a.get('office'), a.get('method'), a.get('route')) not in PLATFORM_HANDED:
                continue
            if not isinstance(a.get('data'), dict) or not isinstance(a.get('body'), dict) or not isinstance(a.get('status'), int):
                continue
            taken[self._handed_key(a['office'], a['method'], a['route'], a['data'])] = (a['status'], a['body'])
        self._handed.answers = taken
        return len(taken)

    def _ask(self, office, method, route, data):
        handed = getattr(self._handed, 'answers', None) or {}
        got = handed.get(self._handed_key(office, method, route, data))
        status, body = got if got is not None else (self.client.get if method == 'GET' else self.client.post)(office, route, data)
        if status != 200:
            raise Refused(502 if status in (0, 500) else status, body.get('refused') or body.get('error') or f'{office} answered {status}')
        return body

    def facts(self, account, scope, member):
        """(cards, hired, groups, verify): the platform's word now (wid's); verify(key) -> (ok, why) by the locker and the platform's
        approval. A page's CALL (answer) may use the approved list as kept (APPROVED_KEEP; a miss asks wid again); a hire and a RUN
        ask now."""
        kept = bool(getattr(self._handed, 'call', False))
        cards = self._ask('wid', 'GET', '/agnt/cards', {})['cards']
        hired = self._ask('wid', 'GET', '/agnt/hired', {'account': account, 'scope': scope, 'member': member})['hired']
        groups = lanes.groups(self._ask('wid', 'GET', '/jobs/balance', {'account': account}))
        return cards, hired, groups, self._verifier(self._approved_now(fresh=not kept), refetch=kept)

    def forget_approved(self):
        """The kept approved list dropped: the next call asks again (the developer's own runtime, after `larryd place`: there the
        locker IS the approval, so a placed agent shows at once, never after APPROVED_KEEP)."""
        self._approved = (0.0, None)

    def verify_now(self, agent_key):
        """THE CLOCK'S CHECK before it presses RUN (core_engine/clock.py): the locker holds the agent by either key and FROST approved
        its exact hashes, the same two guards as every call and run. -> (ok, why); a silent platform is a no."""
        try:
            return self._verifier(self._approved_now())(agent_key)
        except Refused as silent:
            return False, f'the platform did not answer: {silent.reason}'

    def _approved_now(self, fresh=False):
        """The platform's approved list (FROST's review, through wid), the runtime's own word: kept APPROVED_KEEP seconds (fresh:
        asked again now)."""
        at, kept = self._approved
        if fresh or kept is None or time.monotonic() - at > APPROVED_KEEP:
            kept = {(a['agent_key'], a['code_sha256'], a['manifest_sha256']): a.get('card_key') or '' for a in self._ask('wid', 'GET', APPROVED_DOOR, {})['approved']}
            self._approved = (time.monotonic(), kept)
        return kept

    def _verifier(self, approved, refetch=False):
        again = [refetch]   # the platform asked again at most ONCE for one call, and only for the agent the call is for (every card is verified: another card's miss is
        own = getattr(self._handed, 'agent', '')   # only that card unavailable, never a reason to ask again)

        def verify(agent_key):
            nonlocal approved
            ok, why = locker.verify(self.db, self.agents, agent_key, self.caller)   # THE FIRST GUARD: the locker's exact hashes
            if not ok:
                return ok, why
            row = locker.held(self.db, agent_key, self.caller)   # by its card's key too: the review approved the runtime's own key
            exact = (row['agent_key'], row['code_sha256'], row['manifest_sha256'])
            if exact not in approved and again[0] and agent_key == own:   # a kept list without it: asked again now, once, before any refusal (a new approval is seen at once)
                again[0] = False
                approved = self._approved_now(fresh=True)
            if exact not in approved:   # THE SECOND GUARD, at every call, hire and run: the platform's approval of exactly these hashes, fail closed
                return False, 'not approved by FROST'
            if (row.get('card_key') or approved[exact]) and approved[exact] != (row.get('card_key') or ''):
                return False, 'not the card FROST approved'   # the approval names the card it shows; another card is not covered
            return True, ''
        return verify

    def submit(self, agent_key):
        """The runtime sends an agent it holds to the platform: wid writes its card (PENDING until the platform's own review
        shows it) and answers the card's key. Its key, its exact hashes, its manifest."""
        ok, why = locker.verify(self.db, self.agents, agent_key, self.caller)
        if not ok:
            raise Refused(409, why)
        row = locker.held(self.db, agent_key, self.caller)
        inside = os.environ.get('LARRYD_INTERNAL') == '1'   # LARRYD RUNTIME INTERNAL NAMES ITSELF (the owner 2026-11-10: "make sure all use the new runtime"): wid writes FROST's review row with THE TAG from this word (wid larryd_runtime.submit: INTERNAL when runtime=internal, else EXTERNAL), as the queue and the clock name it (/jobs/queued, /jobs/scheduled); without it every internal agent was tagged EXTERNAL and handed to the outside runtime
        return self._ask('wid', 'POST', '/agnt/submit', {'agent_key': agent_key, 'name': row['name'], 'code_sha256': row['code_sha256'],
                                                           'manifest_sha256': row['manifest_sha256'], 'manifest': locker.manifest(self.agents, row['folder']),
                                                           **({'runtime': 'internal'} if inside else {})})

    def marketplace_key(self):
        """The marketplace's key ON THE PLATFORM: the card key wid minted when one is linked (the platform's cards are
        keyed by it), else the runtime's own. A placed or bucket marketplace (marketplace/<key>) comes before the image's own
        (marketplace/), and a linked one before both."""
        con = sqlite3.connect(self.db)
        try:
            row = con.execute("SELECT agent_key, COALESCE(card_key, '') FROM runtime_locker WHERE folder = ? OR folder LIKE ? "
                              "ORDER BY COALESCE(card_key, '') != '' DESC, folder != ? DESC, registered_at DESC",
                              (MARKETPLACE, MARKETPLACE + '/%', MARKETPLACE)).fetchone()
        finally:
            con.close()
        if row is None:
            raise Refused(503, 'the marketplace is not in the locker')
        return (locker.held(self.db, row[0], self.caller) or {}).get('card_key') or row[1] or row[0]   # this caller's own card of it, when it has one

    def review_state(self, keys):
        """What the runtime records for these agents (the owner's `review` command): held or not, the platform's word on its
        card (wid's), and the counts of runtime_runs (runs by state, calls, hires, unhires, mTok charged). Only agent keys and
        counts: no account, no member."""
        out, rec = [], self.records
        for key in keys:
            row = locker.held(self.db, key, self.caller)
            note = ''
            if row is None:
                review = 'not submitted'
            else:
                review, note = self._review(key, row)
            out.append({'agent_key': key, 'held': row is not None, 'code_sha256': row['code_sha256'] if row else '',
                        'manifest_sha256': row['manifest_sha256'] if row else '', 'review': review, 'note': note,
                        'runs': rec.by_state(key, 'job'), 'calls': rec.count(key, 'call'), 'hires': rec.count(key, 'hire', 'ON'),
                        'unhires': rec.count(key, 'hire', 'OFF'), 'charged': rec.charged(key)})
        return {'agents': out}

    def remove(self, key):
        """THE `remove <key>` COMMAND (frost-05's approval 2026-11-06: revoked leftovers sat in the locker, inert): the agent held under
        exactly this key is taken out (its folder and its row) ONLY when the platform's word on its exact hashes is revoked (FROST's
        latest review, through wid's review_state door); anything else is refused in words and nothing is touched. Logged either way.
        -> {agent_key, removed: its folder} or {agent_key, refused: why}."""
        row = locker.held(self.db, key, self.caller)
        if row is None or row['agent_key'] != key:
            out = {'agent_key': key, 'refused': 'not in the locker under this key'}
        else:
            review, _note = self._review(key, row)
            home = locker.in_place()
            stranded = review == 'not submitted' and home is not None and not (home / row['folder']).is_dir()   # THE LOCKER IN PLACE: a row whose
            # folder is not in the one locker (a copy left in instance/ by the old runtime) can never run again and was never submitted under this
            # key (the owner 2026-11-07, the retired CMO, Creative Director and Operations Manager rows): only its row goes, nothing is deleted
            if review != 'revoked' and not stranded:
                out = {'agent_key': key, 'refused': f'its review is {review}, not revoked: kept'}
            else:
                try:
                    out = {'agent_key': key, 'removed': locker.remove(self.db, self.agents, key)}
                except ValueError as why:
                    out = {'agent_key': key, 'refused': str(why)}
        LOG.warning('remove %s: %s', key, out.get('removed') and f"removed {out['removed']}" or f"refused: {out['refused']}")
        return out

    def _review(self, key, row):
        """The platform's word on these exact hashes: -> (review, note). waiting · approved · rejected · revoked · not submitted,
        from wid's review_state door (approved only when FROST's review approved exactly these hashes); a silent platform is
        said as unknown."""
        status, body = self.client.get('wid', '/agnt/review_state', {'agent_key': key, 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']})
        if status == 200:
            return body.get('state', 'unknown'), body.get('note', '') if body.get('state') == 'rejected' else ''
        return f"unknown: {body.get('refused') or body.get('error') or f'wid answered {status}'}", ''

    # ---------------------------------------------------------------- the record
    def _record(self, lane, agent_key, state, reason='', job_key='', run=0, charged=0, account='', member=''):
        """One record per call and run: the agent's key, the job's, its state, times, charge, a plain reason, the caller and
        the account and member keys as the platform gave them; never an input or a delivery (data stays in wid)."""
        self.records.record(lane, agent_key, state, reason, job_key, run, charged, caller=self.caller, account=account, member=member)

    @staticmethod
    def _card(cards, key):
        return next((c for c in cards if c['key'] == key), None)

    def _counts(self, manifest, given, account, scope, member, agent_key):
        """THE COUNTS (2026-10-09): an agent whose APPROVED manifest declares "records": {"*": ["count"]} is handed
        given['counts'], the numbers of the member the platform named (how many records they may list in each module, how
        many ties between two), asked of the platform's counts door for that member and checked to be numbers and codes
        alone; never a record. The platform did not hand them (refused, away, an answer that is more than numbers): the
        agent is handed none and the runtime says so in its own fixed words -> 'counts not read', else ''."""
        if not member_records.counts_declared(manifest):
            return ''
        try:
            given['counts'] = member_records.counts(self._ask, account, scope, member, agent_key)
            return ''
        except Refused as no:
            LOG.warning('counts not read for %s: %s', agent_key, no.reason)   # the platform's words go to the log, never into the audit row
        except ValueError as no:
            LOG.warning('counts not read for %s: %s', agent_key, no)
        return 'counts not read'

    def _roster(self, manifest, given, account, scope, member, agent_key):
        """THE ROSTER (CORE_CLEANUP_IV 37): an agent whose APPROVED manifest declares "records": {"*": [... "roster"]} is handed
        given['roster'] on a CALL, the account's members (key, name, type, active, organization) as wid's roster door hands them for that member,
        checked to be exactly that shape. Not handed (refused, away, any other shape): the agent is handed none and the runtime says
        so in its own fixed words -> 'roster not read', else ''."""
        if not member_records.roster_declared(manifest):
            return ''
        try:
            given['roster'] = member_records.roster(self._ask, account, scope, member, agent_key)
            return ''
        except Refused as no:
            LOG.warning('roster not read for %s: %s', agent_key, no.reason)
        except ValueError as no:
            LOG.warning('roster not read for %s: %s', agent_key, no)
        return 'roster not read'

    def _hand_of(self, word, declared, read, manifest, given, account, scope, member, agent_key):
        """ONE MORE HAND OF THE ROSTER'S KIND: when the APPROVED manifest declares "*": [... word], given[word] is what wid's door hands
        for that member, checked to be exactly its shape; not handed (refused, away, any other shape): none, and the runtime says so in
        its own fixed words -> '<word> not read', else ''."""
        if not declared(manifest):
            return ''
        try:
            given[word] = read(self._ask, account, scope, member, agent_key)
            return ''
        except Refused as no:
            LOG.warning('%s not read for %s: %s', word, agent_key, no.reason)
        except ValueError as no:
            LOG.warning('%s not read for %s: %s', word, agent_key, no)
        return f'{word} not read'

    def _joins(self, manifest, given, account, scope, member, agent_key):
        """THE JOIN REQUESTS (CORE_CLEANUP_IV row 142, pf Alerts): given['joins'] = [{name, asked_at}] on a CALL."""
        return self._hand_of('joins', member_records.joins_declared, member_records.joins, manifest, given, account, scope, member, agent_key)

    def _payments(self, manifest, given, account, scope, member, agent_key):
        """THE PAYMENTS (CORE_CLEANUP_IV row 142, pf Alerts): given['payments'] = [{kind, amount_cents, landed_at}] on a CALL."""
        return self._hand_of('payments', member_records.payments_declared, member_records.payments, manifest, given, account, scope, member, agent_key)

    def _internal_hand_of(self, word, declared, read, manifest, given, account, scope, member, agent_key):
        """A HAND FOR AN INTERNAL AGENT ONLY (the reviews waiting, the review history, the two guards' reports): as _hand_of, but ONLY when this runtime is
        LARRYD RUNTIME INTERNAL (INTERNAL); elsewhere it never asks, hands nothing and says nothing, exactly as the external runtime
        always did (fail closed); wid refuses any card that is not internal and SYSTEM's own (two guards)."""
        if not self.INTERNAL:
            return ''
        return self._hand_of(word, declared, read, manifest, given, account, scope, member, agent_key)

    def _reviews(self, manifest, given, account, scope, member, agent_key):
        """THE REVIEWS WAITING (CORE_CLEANUP_IV 23, pf Review Lane): "records": {"*": [... "reviews"]} hands given['reviews'] on a CALL,
        the agents waiting for FROST's review as wid's reviews door hands them; LARRYD RUNTIME INTERNAL only."""
        return self._internal_hand_of('reviews', member_records.reviews_declared, member_records.reviews, manifest, given, account, scope, member, agent_key)

    def _history(self, manifest, given, account, scope, member, agent_key):
        """THE REVIEW HISTORY (CORE_CLEANUP_IV row 78): "records": {"*": [... "history"]} hands given['history'] on a CALL, as wid's
        history door hands it; LARRYD RUNTIME INTERNAL only."""
        return self._internal_hand_of('history', member_records.history_declared, member_records.history, manifest, given, account, scope, member, agent_key)

    def _guards(self, manifest, given, account, scope, member, agent_key):
        """THE TWO GUARDS' REPORTS (Agents Security Plan, the Agent Ecosystem agent): "records": {"*": [... "guards"]} hands
        given['guards'] on a CALL, FROST active monitoring's and HADES's reports as wid's guards door hands them; LARRYD RUNTIME INTERNAL only."""
        return self._internal_hand_of('guards', member_records.guards_declared, member_records.guards, manifest, given, account, scope, member, agent_key)

    # ---------------------------------------------------------------- the CALL lane: an agent answers now
    def answer(self, account, scope, member, agent_key, beside=None, act=False, handed=None):
        """An agent's answer for the member's screen: only an agent that answers calls, passing the gate itself. handed: the
        platform's own answers to this call's asks (handing), so the runtime need not ask them back."""
        self.handing(handed)
        self._handed.call, self._handed.agent = True, agent_key   # a page's CALL: the approved list may be the kept one (facts); asked again only for this agent
        try:
            return self._answer(account, scope, member, agent_key, beside, act)
        finally:
            self._handed.answers, self._handed.call, self._handed.agent = {}, False, ''


    def _answer(self, account, scope, member, agent_key, beside=None, act=False):
        held = locker.held(self.db, agent_key, self.caller)
        calls = locker.manifest(self.agents, held['folder']).get('calls') if held else None
        if not calls:
            raise Refused(404, 'no agent that answers here')
        cards, hired, groups, verify = self.facts(account, scope, member)
        card = self._card(cards, agent_key)
        if card is None:
            raise Refused(404, 'the agent has no APPROVED card')
        ok, why = gate.may_run(card, verify(agent_key), lanes.hired_on(hired, agent_key), groups)
        if not ok:
            self._record('call', agent_key, 'REFUSED', why, account=account, member=member)
            raise Refused(403, why)
        beside = {k: v for k, v in (beside or {}).items() if k in BESIDE and isinstance(v, dict)}   # the page's own, beside the cards; never over them
        handed = lanes.assemble(cards, hired, groups, verify, own=agent_key)   # the cards as data alone: the platform draws each card from its own record (the owner 2026-11-03: "larryd should just have the agent code and data")
        manifest = locker.manifest(self.agents, held['folder'])
        wanted = member_records.declared(manifest)   # THE MEMBER'S RECORDS: only what the approved manifest declares, read and written through wid's own doors
        custom = fabric.custom(card, manifest, account)   # CUSTOM DATA ONLY ON CUSTOM AGENTS (the owner, 2026-10-25): any other agent never sees nor writes a custom field
        given = {**beside, 'do': calls[0], 'cards': handed}
        if live.declared(manifest) and live.settings()[1]:
            # THE AGENT IS TOLD ONLY THAT ITS ROOM IS THERE (the security review of the room rule, 2026-10-08): never the room's address and never
            # the member's pass. An agent's markup is not trusted with a credential: it draws one empty placeholder, and the address and the pass
            # go to the platform in the runtime's own field beside the view (room, below), which no agent can write
            given['live'] = {'room': True}
        starts = 'run' in (manifest.get('gives') or [])   # AN AGENT THAT STARTS ITS OWN RUN FROM ITS PAGE (the member's Generate): it names "run" in gives
        if starts and hasattr(self.records, 'recent'):
            given['runs'] = self.records.recent(agent_key, member, RUNS_HANDED)   # what became of the member's last RUNs of it: the run's number, its state, the runtime's own code and the time; never an input or a delivery
            given['running'] = self.records.in_flight(agent_key, member) if hasattr(self.records, 'in_flight') else []   # and the ones still IN FLIGHT ([{run, at}]): a page merely opened can say a RUN is being made (found on B, 2026-10-09: a plain load said "No generations yet" while one rendered)
        not_read = ''
        try:
            if wanted:
                given['records'] = member_records.read(self._ask, wanted, account, scope, member, agent_key, custom=custom)
                given['who'] = {'member': member}   # WHO THE RECORDS ARE FOR: the member's own key, so an agent can tell their own rows (system_member_roles) from the account's; nothing else of them
                if live.declared(manifest):
                    # AN AGENT WITH A LIVE PAGE IS HANDED THE FIRST NAME ITS OWN PASS ALREADY CARRIES (PF Virtual Wire, 2026-10-08: the messenger
                    # is inside the page now, and a message written there wears the same name as one written on the live page): the platform's own
                    # word (wid's), plain, or none; an agent without a live page is handed the key alone, as before
                    name = live._plain(self._identity(account, scope, member).get('first_name'), 40)
                    if name:
                        given['who']['name'] = name
        except Refused as no:   # THE PLATFORM DID NOT HAND THEM (a slot without the record doors yet, a member not allowed, wid away): the agent is handed none
            not_read = 'records not read'   # and says so on its page; nothing is guessed, nothing is written without them. THE RECORD KEEPS THE RUNTIME'S OWN WORDS ONLY:
            given['records_refused'] = member_records.refused_word(no.status, no.reason)   # and the agent is told why in ONE word, never the platform's text
            LOG.warning('records not read for %s: %s', agent_key, no.reason)   # the platform's refusal text goes to the log, never into the audit row (fixed words, never cut, nothing written by another)
        not_read = '; '.join(r for r in (not_read, self._counts(manifest, given, account, scope, member, agent_key),
                                         self._roster(manifest, given, account, scope, member, agent_key),
                                         self._joins(manifest, given, account, scope, member, agent_key),
                                         self._payments(manifest, given, account, scope, member, agent_key),
                                         self._reviews(manifest, given, account, scope, member, agent_key),
                                         self._history(manifest, given, account, scope, member, agent_key),
                                         self._guards(manifest, given, account, scope, member, agent_key)) if r)   # THE COUNTS, THE ROSTER, the joins, the payments, and (LARRYD RUNTIME INTERNAL only) the reviews waiting, their history and the two guards' reports, when the approved manifest declares them
        if fabric.declared(manifest):   # THE DATA FABRIC'S ONE SNAPSHOT (the owner 2026-11-04: "no connections / just 1 updated snapshot per day"): one read through wid (FROST's store)
            try:
                state, who = fabric.viewer(self._ask, account, scope, member)
                given['fabric'] = {'state': state, 'viewer': who}   # who looks: the page's mask (the owner, 2026-10-25, UI only)
            except Refused as no:
                not_read = '; '.join(r for r in (not_read, 'fabric state not read') if r)
                LOG.warning('fabric state not read for %s: %s', agent_key, no.reason)
        state, answer, reason = self._run(held['folder'], manifest, given)
        outside = _outside_gives(manifest, answer) if state == 'DONE' else ''
        if outside:
            state, reason = 'FAILED', outside
        if state == 'DONE' and answer.get('writes') and 'records not read' in not_read:   # an agent that saw no records decided blind: its writes go nowhere
            answer = {k: v for k, v in answer.items() if k != 'writes'}
            reason = 'writes not carried: the records were not read'
        if state == 'DONE' and answer.get('writes') and not act:
            # A WRITE IS CARRIED ONLY ON THE MEMBER'S OWN CONFIRMED ACT (the review, 2026-10-07): the platform marks the call (act: true, on a POST it
            # checked with the member's own token); a page merely opened, by any address or link, never writes, changes or removes a record
            answer = {k: v for k, v in answer.items() if k != 'writes'}
            reason = 'writes not carried: the call is not the member\'s confirmed act'
        if state == 'DONE' and answer.get('writes'):
            state, answer, reason = self._written(held, manifest, wanted, given, answer, account, scope, member, agent_key, custom=custom)
        if state == 'DONE' and 'run' in answer:
            # A RUN ASKED FROM THE PAGE: only on the member's own confirmed act, only the inputs the manifest declares, each on its slot, and EACH ONE A
            # WORD OF THAT ACT ITSELF (what the member typed or picked in the form they sent: the platform hands those words in page.search). An agent
            # cannot put anything else into a RUN: not a record it was handed, not words of its own; the act confirms what the member saw and sent,
            # nothing more. The runtime starts nothing itself: it answers the platform {"run": {"inputs": {slot: text}}}, and the platform starts the
            # RUN as its own Run button does
            asked, why = self._run_asked(manifest, answer['run'], (beside.get('page') or {}).get('search')) if act else (None, 'run not asked: the call is not the member\'s confirmed act')
            answer = {k: v for k, v in answer.items() if k != 'run'}
            if asked is not None:
                answer['run'] = asked
            reason = '; '.join(r for r in (reason, why) if r)
        self._record('call', agent_key, state, '; '.join(r for r in (not_read, reason) if r), account=account, member=member)   # the records not read first: the fact that explains the rest
        if state != 'DONE':
            raise Refused(500, reason)
        answer.pop('writes', None)
        path = (beside.get('page') or {}).get('path')
        origins = (beside.get('page') or {}).get('origins')   # THE PLATFORM'S OWN WORD for this page's offices ({wid, so, fs}: CORE_CLEANUP_IV 20/96): the markers' addresses are built on them
        answer, why = view.checked(answer, path if isinstance(path, str) else '', origins if isinstance(origins, dict) else None, self.caller in LOCAL_CALLERS)   # the agent's own view, passed on only when it holds nothing that runs or reaches out
        if why:
            LOG.warning('view dropped for %s: %s', agent_key, why)
        answer.pop('frame', None)   # the field's first name (the frame attempt, 2026-10-08): never an agent's word either, whatever an old host reads
        answer.pop('room', None)   # never an agent's word (an answer that held one was refused above: RUNTIME_OWN); the runtime's own, below
        out = {'agent_key': agent_key, 'title': card['name'], **answer, 'keep': _keep(manifest, given, not_read, act)}   # the runtime's own field: how long the platform may draw this answer again (step E)
        if live.declared(manifest):
            # THE ROOM INSIDE THE PLATFORM'S PAGE (the owner, 2026-10-08: "inside the page but as a regular inject like all the other agents"): the
            # runtime's OWN field beside the view, "<the room program's address>/#<the member's pass>", signed here for the member the platform named,
            # each pass good once. The platform checks the address against its own list and hands both to its own script (wid: THE HOST'S ROOM RULE);
            # the agent's view holds only an empty placeholder and never sees either. No page frames anything
            room = live.link(account, member, agent_key, page=beside.get('page'), product=_product(card), who=self._identity(account, scope, member), scope=scope, via=self.caller)
            if room:
                out['room'] = room
        return out

    def _written(self, held, manifest, wanted, given, answer, account, scope, member, agent_key='', custom=False):
        """THE WRITES AN ANSWER ASKS FOR: checked against the declaration (one fault refuses them all), carried to wid's own
        doors for this member, then the agent runs ONCE MORE on the same page with the records as they are now and
        written = what wid said of each, so the page shows the truth (a new record with its key, a refused write said);
        writes on that second run are ignored, but for edits of a record this same act just added (one round more, below).
        -> (state, answer, reason)."""
        if not wanted:
            return 'FAILED', None, 'the answer carries writes, but the manifest declares no records'
        writes, why = member_records.check(answer['writes'], wanted, custom=custom)
        if why:
            return 'FAILED', None, why
        written = member_records.carry(self.client.post, writes, account, scope, member, agent_key)
        if getattr(self, '_handed', None) is not None:
            self._handed.answers = {}   # WRITTEN: the platform's answers handed before the writes are no longer the truth; every read from here asks the platform
        carried = f'{sum(1 for w in written if w["ok"])} of {len(written)} record write{"" if len(written) == 1 else "s"} carried'   # THE RECORD SAYS WHAT WAS WRITTEN, whatever happens after: the writes are on the platform now
        try:
            given = {**given, 'records': member_records.read(self._ask, wanted, account, scope, member, agent_key, custom=custom), 'written': written}
        except Refused as no:
            LOG.warning('records not read back: %s', no.reason)
            return 'FAILED', None, f'{carried}; the records could not be read back'
        state, answer, reason = self._run(held['folder'], manifest, given)
        outside = _outside_gives(manifest, answer) if state == 'DONE' else ''
        if outside:
            return 'FAILED', None, f'{carried}; the second run: {outside}'
        if state != 'DONE':
            return state, None, f'{carried}; the second run: {reason}'
        # ONE ROUND MORE, FOR A RECORD THIS ACT ITSELF JUST ADDED (PF Virtual Wire, 2026-10-08: the thread's record is added by its
        # identity only, the member's own list is read back, and only then is the first message written into it): the second run may
        # ask for EDITS OF A RECORD WHOSE ADD THIS SAME ACT CARRIED (its key as wid answered it), nothing else. They are checked and
        # carried as the first were, and the agent runs a third and last time on the records as they are now, with written = all of
        # them. Any other write on the second run is ignored as before, and every write on the third.
        made = {w['key'] for w in written if w['do'] == 'add' and w['ok'] and w['key']}
        more = answer.get('writes')
        if not (made and isinstance(more, list) and more and all(isinstance(w, dict) and w.get('do') == 'edit' and w.get('key') in made for w in more)):
            return 'DONE', answer, carried
        writes, why = member_records.check(more, wanted, custom=custom)
        if why:
            return 'FAILED', None, f'{carried}; the second run: {why}'
        try:   # THE RECORD SAYS WHAT WAS WRITTEN, whatever happens in this round (the commit's security review, 2026-10-08): the first writes are on the platform now, so a fault carrying the second never leaves the run without its word
            written = written + member_records.carry(self.client.post, writes, account, scope, member, agent_key)
        except (OSError, ValueError, KeyError, Refused) as no:
            LOG.warning('the second round of writes was not carried: %s', no)
            return 'FAILED', None, f'{carried}; the second round of writes could not be carried'
        carried = f'{sum(1 for w in written if w["ok"])} of {len(written)} record write{"" if len(written) == 1 else "s"} carried'
        try:
            given = {**given, 'records': member_records.read(self._ask, wanted, account, scope, member, agent_key, custom=custom), 'written': written}
        except Refused as no:
            LOG.warning('records not read back: %s', no.reason)
            return 'FAILED', None, f'{carried}; the records could not be read back'
        state, answer, reason = self._run(held['folder'], manifest, given)
        outside = _outside_gives(manifest, answer) if state == 'DONE' else ''
        if outside:
            return 'FAILED', None, f'{carried}; the third run: {outside}'
        if state != 'DONE':
            return state, None, f'{carried}; the third run: {reason}'
        return 'DONE', answer, carried

    @staticmethod
    def _run_asked(manifest, asked, sent=None):
        """-> ({'inputs': {slot: text}}, '') or (None, why): the words of a RUN the page asks for, by the names the manifest's
        "inputs" gives them, each text within the job's own limit, and each EXACTLY a word of the member's act (sent: the words of
        the form the member sent, as the platform hands them). An undeclared name, or a word the member did not send, refuses the
        ask whole."""
        declared = manifest.get('inputs')
        if not (isinstance(declared, dict) and 'job' in ((manifest.get('run') or {}).get('hands') or [])):
            return None, 'run not asked: the agent declares no job inputs'
        if not (isinstance(asked, dict) and asked and all(isinstance(n, str) and n in declared and isinstance(v, str) and len(v) <= MOST_INPUT for n, v in asked.items())):
            return None, 'run not asked: its words are not the declared inputs, each a text'
        own = {v for v in (sent or {}).values() if isinstance(v, str)} if isinstance(sent, dict) else set()
        if any(v != '' and v not in own for v in asked.values()):
            return None, 'run not asked: it carries a word the member did not send'
        return {'inputs': {declared[n]: v for n, v in asked.items() if v != ''}}, ''

    INTERNAL = os.environ.get('LARRYD_INTERNAL') == '1'   # LARRYD RUNTIME INTERNAL: this runtime runs on this computer for internal agents (its start says so); the external one never
    MOST_INTERNAL_SECONDS = 6 * 3600   # an internal agent's own limit at most (the night's Web build and Test each hold the smoke test, up to 4 hours, after the Judge)
    INTERNAL_HANDS = ('service_key',)  # what a RUN can be handed on LARRYD RUNTIME INTERNAL only, beside HANDS

    def internal_for(self, manifest):
        """Does this agent run with this computer's reach? Only on LARRYD RUNTIME INTERNAL, and only when its approved manifest declares
        "internal" (the owner 2026-11-03: "all virtual sanity agents will use 1 single internal larryd run")."""
        return self.INTERNAL and isinstance(manifest.get('internal'), dict)

    def _run(self, folder, manifest, given, **kw):
        """ONE RUN OF AN AGENT: in the sandbox (every external agent, and any agent on the external runtime); an internal agent on
        LARRYD RUNTIME INTERNAL as this computer's own process, its time limit its manifest's own (internal.seconds, at most 6 hours)."""
        kw.setdefault('most_bytes', answer_most(manifest))   # an agent that declares the DA-M store may answer a file up to DA-M's 25 MB
        if self.internal_for(manifest):
            seconds = manifest['internal'].get('seconds')
            seconds = min(int(seconds), self.MOST_INTERNAL_SECONDS) if isinstance(seconds, int) and seconds > 0 else self.seconds
            return sandbox.run(self.agents / folder, manifest['entry'], given, seconds, on_start=self.on_start, internal=True, **kw)
        return sandbox.run(self.agents / folder, manifest['entry'], given, self.seconds, on_start=self.on_start, **kw)

    def hire(self, account, scope, member, agent_key, on):
        """THE MARKETPLACE'S HIRE: only a card in the collection the member may hire; the marketplace itself can always be hired again."""
        key = self.marketplace_key()
        if agent_key == key and not on:   # THE MARKETPLACE IS ALWAYS ON (the owner, 2026-10-07: "all people will get this turned on and no option to turn this agent off")
            raise Refused(403, 'the marketplace is always on')
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
        if on and card.get('offline') is True:   # AN OFFLINE AGENT IS NEVER HIRED, whatever a page draws or a caller sends: refused here, before the platform is asked (its own sink refuses it too)
            raise Refused(403, 'offline')
        if on and not card['hireable']:
            raise Refused(403, card['reason'])
        done = self._ask('wid', 'POST', '/agnt/hire' if on else '/agnt/unhire', {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key})
        self._record('hire', agent_key, 'ON' if on else 'OFF', account=account, member=member)
        return done

    def defaults(self, account, scope, member, board):
        """A board's first visit (the platform asks once, when the member's board is born): the marketplace is placed on its
        own screen, as before, AND EVERY DEFAULT AGENT OF THIS BOARD (the owner, 2026-10-09: "a few agents will be turned on as
        default when new users come in so its not blank and empty"): a card the system owner marked on by default (the card's
        own default, the platform's word, never the agent's manifest) whose screen is this board, shown (APPROVED, in the
        locker, its exact hashes), not offline for this account, hireable and not hired. Each goes through the platform's
        same hire door (its own decision for this member stands: a refusal there skips the card, nothing else) and leaves the
        same hire record. A CARD THAT NAMES AN OUTSIDE AI SERVICE IS NEVER PLACED BY DEFAULT: the member's own hire is the
        permission for that. TWO CHECKS: this runtime skips it from the facts it read, and the platform's door, told the ask is
        a default placement, refuses it on its own card (the one that counts).
        Nothing is kept here: "once" is the platform's (a board is born once), so an agent a member
        let go does not come back. -> {placed: [keys], skipped: [{agent_key, why}]}."""
        key = self.marketplace_key()
        cards, hired, groups, verify = self.facts(account, scope, member)
        placed, skipped, refused = [], [], None
        for card in lanes.assemble(cards, hired, groups, verify):
            mine = card['key'] == key
            if card['screen'] != board or not (mine or card.get('default') is True):
                continue
            if card['hired']:
                continue   # theirs already: nothing to place, nothing to say
            if not card['hireable']:
                skipped.append({'agent_key': card['key'], 'why': card['reason'] or 'not hireable'})
                continue
            if not mine and card.get('offline') is True:   # an offline agent is never hired (hire, above)
                skipped.append({'agent_key': card['key'], 'why': 'offline'})
                continue
            if not mine and str(card.get('sends_to') or '').strip():
                skipped.append({'agent_key': card['key'], 'why': 'it names an outside AI service: the member hires it themselves'})
                continue
            try:
                # THE PLACEMENT SAYS WHAT IT IS (the security review of c78af5d, 2026-10-09): default and the board ride in the signed ask, so THE
                # PLATFORM decides on ITS OWN card as it stands (marked by the owner, approved, on this board, naming no outside AI service) and
                # refuses otherwise; the skips above are this runtime's own reading of the facts and never the check that counts. A member's own
                # hire (hire, above) never carries the mark
                self._ask('wid', 'POST', '/agnt/hire', {'account': account, 'scope': scope, 'member': member, 'agent_key': card['key'], 'default': '1', 'board': board})
            except Refused as no:
                if mine:
                    refused = no   # the marketplace as before: its refusal is the answer, said once the board's other defaults are placed (a board is born once)
                    continue
                skipped.append({'agent_key': card['key'], 'why': no.reason})
                continue
            self._record('hire', card['key'], 'ON', account=account, member=member)
            placed.append(card['key'])
        if refused is not None:
            raise refused
        return {'placed': placed, 'skipped': skipped}

    # ---------------------------------------------------------------- the JOB lane: a RUN, pushed by the platform
    def _result(self, account, scope, job_key, run, state, log, delivery='', job=None):
        """job: the agent's own answer for its job's slots (wid keeps only the slots an agent fills, larryd_runtime.AGENT_FILLS); sent only when given."""
        said = {'account': account, 'scope': scope, 'job_key': job_key, 'run': str(run), 'state': state, 'log': log, 'delivery': delivery}
        if job:
            said['job'] = job
        return self._ask('wid', 'POST', '/jobs/result', said)

    ALIVE_SECONDS = 5 * 60   # how often a RUN still working writes RUNNING again: well inside the platform's 20 minutes, so only a RUN nobody answers is closed

    def _still_running(self, account, scope, job_key, run):
        """While the agent works, RUNNING is written to its RUN again every ALIVE_SECONDS (wid takes RUNNING while the RUN is open),
        so the platform's stale close (no write for 20 minutes) never closes a RUN that is only long. -> stop(): no write after it returns."""
        stop, began = threading.Event(), time.monotonic()

        def beat():
            while not stop.wait(self.ALIVE_SECONDS):
                try:
                    self._result(account, scope, job_key, run, 'RUNNING', f'RUN {run} RUNNING · still working after {int(time.monotonic() - began) // 60} min')
                except Exception as failed:   # noqa: BLE001  a beat not heard is said in the log; the RUN goes on
                    LOG.warning('RUN %s of %s: still running, not heard by wid (%s)', run, job_key, failed)
        beater = threading.Thread(target=beat, name=f'alive {job_key}#{run}', daemon=True)
        beater.start()

        def done():
            stop.set()
            beater.join(timeout=60)
        return done

    _UNSET = object()

    @property
    def on_start(self):
        """THE RUN'S OWN on_start (OPERATION BDAY item 1, 2026-11-10): three RUNs and the page's CALLs share one harness, each on its
        own thread, so each sets and reads its own; a thread that set none reads the one the harness was made with."""
        mine = getattr(self._local(), 'on_start', self._UNSET)
        return self.__dict__.get('_on_start') if mine is self._UNSET else mine

    @on_start.setter
    def on_start(self, told):
        self._local().on_start = told

    def _local(self):
        here = self.__dict__.get('_here')
        if here is None:   # a harness made without __init__ (a test's stand-in) still keeps each thread's own
            here = self.__dict__.setdefault('_here', threading.local())
        return here

    def run_job(self, account, scope, member, job_key, run):
        """-> the state it ended in. Refused and failed runs are written back and recorded like done ones."""
        try:
            cards, hired, groups, verify = self.facts(account, scope, member)
        except Refused as silent:
            return self._end(account, scope, member, '', job_key, run, 'FAILED', f'LARRYD could not read the platform: {silent.reason}')
        shell = next((h for h in hired if h.get('job_key') == job_key), None)
        if shell is None:
            return self._end(account, scope, member, '', job_key, run, 'REFUSED', 'the job is not in a hired shell')
        key = shell['agent_key']
        card = self._card(cards, key)
        if card is None:
            return self._end(account, scope, member, key, job_key, run, 'REFUSED', 'the agent has no APPROVED card')
        ok, why = gate.may_run(card, verify(key), shell.get('on') is True, groups)
        if not ok:
            return self._end(account, scope, member, key, job_key, run, 'REFUSED', why)
        folder = locker.held(self.db, key, self.caller)['folder']
        manifest = locker.manifest(self.agents, folder)
        plan = manifest.get('run') or {}
        hands = plan.get('hands') or []
        may_hand = set(HANDS) | (set(self.INTERNAL_HANDS) if self.INTERNAL else set())
        if set(hands) - may_hand:
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f"LARRYD cannot hand {sorted(set(hands) - may_hand)} yet")
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
        if 'service_key' in hands:   # THE MEMBER'S OWN KEY FOR THE SERVICE ITS CARD NAMES FIRST (CORE_CLEANUP_IV 50, 53, 100: a connector of PF_Loot's), for this RUN only; LARRYD RUNTIME INTERNAL only (the hands check above)
            try:
                given['service_key'] = self._service_key(card, key, job_key, run, account, scope, member)
            except _Stop as stop:
                return self._end(account, scope, member, key, job_key, run, stop.state, stop.reason)
        if 'files' in hands:   # THE MEMBER'S FILES ON A RUN (CORE_CLEANUP_IV 21, the owner's blanket approval 2026-11-06): the files the member named in this RUN's own inputs, each read through wid's job file door for this member while the RUN is open (wid decides and asks DA-M as itself, as a reference picture is read), handed as bytes, kept nowhere
            try:
                given['files'] = self._run_files(manifest, given.get('job'), account, scope, member, job_key, run)
            except _Stop as stop:
                return self._end(account, scope, member, key, job_key, run, stop.state, stop.reason)
        if 'records' in hands:   # THE MEMBER'S RECORDS ON A RUN (CORE_CLEANUP_IV 30): exactly what a CALL of this agent is handed (answer): only the species its approved manifest declares with read, through wid's list door for this member (wid's own permission checks), custom fields only for a custom agent, and who they are for; wid silent or refusing: the RUN fails before it starts, nothing is guessed
            wanted = member_records.declared(manifest)
            try:
                given['records'] = member_records.read(self._ask, wanted, account, scope, member, key, custom=fabric.custom(card, manifest, account)) if wanted else {}
            except Refused as no:
                return self._end(account, scope, member, key, job_key, run, 'FAILED', f'LARRYD could not read the records: {no.reason}')
            given['who'] = {'member': member}
        self.started(key, job_key, run, account, member)
        try:
            self._result(account, scope, job_key, run, 'RUNNING', f'RUN {run} RUNNING')
        except Refused as no:   # THE PLATFORM DID NOT TAKE RUNNING (OPERATION BDAY item 1): the agent never runs, the slot is given back by its caller
            if no.status != 502:   # wid answered and refused: the RUN is no longer open (a second start of a RUN already ended): nothing more is written or recorded
                LOG.warning('RUN %s of %s: RUNNING refused by the platform (%s); the agent does not run', run, job_key, no.reason)
                return 'FAILED'
            LOG.warning('RUN %s of %s: RUNNING not written (%s); the agent does not run, the RUN is ended FAILED', run, job_key, no.reason)
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f'LARRYD could not write RUNNING to the platform: {no.reason}')
        if 'cards' in hands:
            given['cards'] = lanes.assemble(cards, hired, groups, verify, own=key)
        self._counts(manifest, given, account, scope, member, key)   # THE COUNTS, when the approved manifest declares them: handed on a RUN as on a CALL; not handed, the agent runs without
        self._guards(manifest, given, account, scope, member, key)   # THE TWO GUARDS' REPORTS, the same: on a RUN as on a CALL (LARRYD RUNTIME INTERNAL only; OPERATION BDAY 2026-11-10: Agent Ecosystem's every RUN read "the guards' door did not answer" while wid answered 200)
        if self.internal_for(manifest) and 'records' not in hands:   # RECORDS ON A RUN, internal agents (the owner 2026-11-03): what its manifest declares, read as a CALL reads them, without the "records" hand
            wanted = member_records.declared(manifest)
            if wanted:
                try:
                    given['records'] = member_records.read(self._ask, wanted, account, scope, member, key, custom=False)
                except Refused as no:
                    return self._end(account, scope, member, key, job_key, run, 'FAILED', f'the records could not be read: {no.reason}')
        alive = self._still_running(account, scope, job_key, run)   # A LONG RUN SAYS IT IS ALIVE (the owner 2026-11-10: "fix the scrum master and all agents"): the platform closes a RUN with nothing written for 20 minutes (wid atom.STALE_SECONDS), and the night's Web build holds the Judge, about 45
        try:
            state, answer, reason = self._run(folder, manifest, given)
        finally:
            alive()
        if state != 'DONE':
            return self._end(account, scope, member, key, job_key, run, 'FAILED', reason)
        outside = _outside_gives(manifest, answer)
        if outside:
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f'{outside}; the delivery is withheld')
        slots = answer.get('job') if isinstance(answer.get('job'), dict) else None   # THE JOB'S SLOTS (the owner 2026-11-05: "all of the agents need to be updated to use all the new slots we added in the ai atom jobs view"): the agent's `job`, named in its "gives", passed on to wid as it is; wid keeps only the slots an agent fills
        if 'job' in answer and slots is None:
            return self._end(account, scope, member, key, job_key, run, 'FAILED', 'the answer\'s job is not an object of slots; the delivery is withheld')
        slots = stored_slots(slots, [], {})   # an agent's own image, video or sound key is never kept: those slots are the runtime's
        inside = self.internal_for(manifest)
        said = _first_line(answer.get('delivery')) if inside else ''   # AN INTERNAL AGENT'S OWN WORDS ON ITS JOB (the owner 2026-11-03, Scrum Master 3: every value from the database): its delivery's first line is its log, so its job's TODAY says what it found
        wrote, stop = self._run_writes(manifest, given, answer, account, scope, member, key)   # THE WRITES OF A RUN (the one new right, below): carried, or dropped and said
        if stop:
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f'RUN {run} FAILED · {stop}', delivery=answer.get('delivery') if isinstance(answer.get('delivery'), str) else '', job=slots)
        if inside and answer.get('light') == 'RED':   # AN INTERNAL CHECK THAT FOUND A RED (Lie Detector, New Files ...): the RUN ran, what it found is red; its light RED and its own words, never just an exit code
            return self._end(account, scope, member, key, job_key, run, 'FAILED', f'RUN {run} RED · {said or "red"}{wrote}', delivery=answer.get('delivery') if isinstance(answer.get('delivery'), str) else '', job=slots)
        try:
            files = self._files(manifest, answer)
            beside = self._companions(files, given.get('files'), given.get('records'))   # {a file's place: the record it is stored beside}: checked before anything is charged
            asks = self._asks(manifest, answer, key, member)
            keeps = self._keeps(manifest, answer, files, asks, custom=fabric.custom(card, manifest, account))
            if {files[n]['name'] for n in beside} & {k['file'] for k in keeps}:   # one file, one place: beside the member's record OR its own new record, never both
                raise _Stop('FAILED', 'a file is both a companion and kept as a new record; nothing was sent')
            if any(a.get('companion_of') for a in asks) and {a['name'] for a in asks if a.get('companion_of')} & {k['file'] for k in keeps}:   # one file, one place (94 b)
                raise _Stop('FAILED', 'a file is both a companion and kept as a new record; nothing was sent')
            files = files + self._made(asks, key, job_key, run, account, member, scope)   # THE ERRAND, before anything is charged or stored: a file that was not made costs the member nothing and leaves nothing behind
            beside.update({n: f['beside'] for n, f in enumerate(files) if f.get('beside')})   # a made file beside its reference's record (94 b)
            if len({f['name'] for f in files}) != len(files):   # a made file's own name is its ask's plus the kind that came back: it may not land on a carried file's name
                raise _Stop('FAILED', 'two files of this run would be stored under one name; nothing was stored')
        except _Stop as stop:
            return self._end(account, scope, member, key, job_key, run, stop.state, stop.reason)
        if gate.rate(card) == 0 and not gate.group_of(card):   # A FREE AGENT OF NO PLAN (a LARRYD agent: found on B, 2026-10-25, PF DATA FABRIC): it costs nothing and mTok keeps no line for a free one, but refuses a charge naming no group
            status, body = 200, {'charged': 0, 'free': True}
        else:   # THE JOB'S BILL, wid's (the core cleanup 2026-11-05): wid charges this open RUN by its own card, asking mTok as itself
            status, body = self.client.post('wid', '/jobs/charge', {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run)})
        if status != 200:
            return self._end(account, scope, member, key, job_key, run, 'FAILED',
                             f"not charged: {body.get('refused') or f'wid answered {status}'}; the delivery is withheld")
        charged = int(body.get('charged') or 0)
        paid = 'free' if body.get('free') else f"{charged} mTok from the {body.get('paid_from')}"
        # A STORED FILE BECOMES THE MEMBER'S RECORD, AND THE RECORD COMES FIRST (found on B, 2026-10-08: a made picture's card showed no picture). On the
        # platform a record's card shows the files TIED TO THAT RECORD in DA-M (the look book reads them by the record's own key), so a kept file is stored
        # tied to its record, never to the agent. The record's identity is the DA-M file's companion, DA-M_<the content's hash> (the platform's own recipe:
        # sha256 of the bytes, its first twelve, never the token), which the runtime knows before DA-M has seen the file. So: the records are added through
        # wid's own door for this member (as a CALL's write is carried; the identity is the runtime's to fill, never the agent's), then each file is stored
        # under its record's key. A record the platform refuses: nothing is stored.
        record_of, kept_note = {}, ''
        if keeps:
            by_name = {(f.get('asked_as') or f['name']): n for n, f in enumerate(files)}   # WHICH FILE A KEEP MEANS, by its place in this RUN's files, never by a name looked up twice: a made file by the name its ask gave it (the agent cannot know which kind of picture came back), a carried one by its own; _keeps held them one to one
            companion = lambda f: 'DA-M_' + hashlib.sha256(base64.b64decode(f['content_b64'])).hexdigest().upper()[:12]
            writes = [{'do': 'add', 'species': k['species'], 'key': '', 'values': {**k['values'], 'identity_dam_file': companion(files[by_name[k['file']]])}} for k in keeps]
            written = member_records.carry(self.client.post, writes, account, scope, member, key)
            good = sum(1 for w in written if w['ok'])
            kept_note = f" · {good} of {len(written)} record{'' if len(written) == 1 else 's'} added"
            if good != len(written):
                return self._end(account, scope, member, key, job_key, run, 'FAILED', f"{paid}, but not every record was added{kept_note}; no file was stored", charged=charged)
            record_of = {by_name[k['file']]: (w['key'], k['species']) for k, w in zip(keeps, written)}   # {the file's place: (its record's key, its species)}
        stored_keys = {}   # {a stored file's name: the key DA-M gave it}
        for n, f in enumerate(files):
            status, stored = self.client.post('wid', '/jobs/upload', {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run), 'name': f['name'],
                                                                     'content_b64': f['content_b64'], 'source_key': record_of[n][0] if n in record_of else beside.get(n, key)})   # its record's key; a file no record keeps: the agent's card, as before (wid stores it in DA-M)
            if status != 200:
                # A RECORD WHOSE FILE DID NOT ARRIVE IS TAKEN BACK when the platform lets the agent (its card declares remove); either way the RUN says
                # plainly what stands: never a record left behind in silence
                left = ''
                if n in record_of:
                    back = member_records.carry(self.client.post, [{'do': 'remove', 'species': record_of[n][1], 'key': record_of[n][0], 'values': {}}], account, scope, member, key)
                    left = '; its record was taken back' if back and back[0]['ok'] else f"; ITS RECORD {record_of[n][0]} STANDS WITHOUT ITS FILE"
                return self._end(account, scope, member, key, job_key, run, 'FAILED',
                                 f"{paid}{kept_note}, but DA-M did not store the files{left}: {stored.get('refused') or stored.get('error') or f'wid answered {status}'}", charged=charged)
            stored_keys[f['name']] = str(stored.get('dam_key') or '')
        slots = stored_slots(slots, files, stored_keys)   # the stored files' keys, the runtime's own
        kept = {k: v for k, v in answer.items() if k not in ('files', 'makes', 'keeps', 'job', 'writes')}   # job: its own slots, never the delivery; writes: carried or dropped above, never the delivery
        delivery = answer.get('delivery') if isinstance(answer.get('delivery'), str) else json.dumps(kept, sort_keys=True)
        stored_note = f" · {len(files)} file{'' if len(files) == 1 else 's'} in DA-M" if files else ''
        return self._end(account, scope, member, key, job_key, run, 'DONE', f'RUN {run} DONE · {said}{wrote}' if said else f'RUN {run} DONE · {paid}{stored_note}{kept_note}{wrote}', charged=charged, delivery=delivery, job=slots)

    RUN_WRITES_NOT_SAID = 'writes not carried: its approved manifest does not say a RUN of it writes ("run": {"writes": true}, an internal agent\'s alone)'

    def _run_writes(self, manifest, given, answer, account, scope, member, agent_key):
        """THE WRITES OF A RUN, THE ONE NEW RIGHT (the owner 2026-11-13, of the news nobody presses for: "no run is ever pressed"; "you would
        need to tie save to run"; asked whether an approved internal agent may write the records its card declares when its RUN is started
        by a clock or by a member's save: "lets go"). Until now a record was written only on a member's own confirmed act (a CALL with act:
        the review, 2026-10-07), so nothing a clock or a chain started could put news on a day. A RUN's answer may carry `writes`, held
        exactly as a CALL's are: the RUN itself is only ever started for an agent the locker holds verified, its card APPROVED and hired by
        this member (gate.may_run, before the agent ran); each write is a verb its approved manifest declares on a species it declares
        (member_records.check: one fault refuses them all), carried to wid's own doors for this member, where the platform decides the
        rest. AND ONLY WHEN BOTH HOLD: (1) the agent is an INTERNAL one on LARRYD RUNTIME INTERNAL (internal_for: this computer's own
        runtime and a manifest that declares "internal"; the external runtime never carries a RUN's write), and (2) its approved manifest
        says so in one explicit word, "run": {"writes": true}, inside the hashes FROST approved, so no agent gains the right silently.
        Without both, the writes are dropped and the RUN's own line says so; the RUN goes on as before. Records not read on this RUN: an
        agent that saw none decided blind, its writes go nowhere (as a CALL's). A write the platform refuses, or writes that are not well
        formed: the RUN ends FAILED and its line says what was carried. A CALL is untouched: a page merely opened never writes.
        -> (what to say on the RUN's line, '' when nothing was asked; why the RUN must end FAILED, '' when it goes on)."""
        if 'writes' not in answer:
            return '', ''
        asked = answer.get('writes')
        if not (self.internal_for(manifest) and (manifest.get('run') or {}).get('writes') is True):
            return (f' · {self.RUN_WRITES_NOT_SAID}' if asked else ''), ''
        if not asked:
            return '', ''
        if not isinstance(given.get('records'), dict):
            return ' · writes not carried: the records were not read', ''
        wanted = member_records.declared(manifest)
        if not wanted:
            return '', 'the answer carries writes, but the manifest declares no records'
        writes, why = member_records.check(asked, wanted, custom=False)   # custom fields are a custom agent's on a CALL alone
        if why:
            return '', f'{why}; nothing was written'
        try:
            written = member_records.carry(self.client.post, writes, account, scope, member, agent_key)
        except (OSError, ValueError, KeyError, Refused) as no:
            LOG.warning('the writes of a RUN were not carried: %s', no)
            return '', 'the writes could not be carried to the platform'
        good = sum(1 for w in written if w['ok'])
        carried = f'{good} of {len(written)} record write{"" if len(written) == 1 else "s"} carried'
        if good != len(written):
            return '', f"{carried}; refused: {next(w['why'] for w in written if not w['ok'])}"
        return f' · {carried}', ''

    def started(self, agent_key, job_key, run, account, member):
        """A RUN the runtime took is written down as STARTED, once (at the door when the platform names the agent, else here as it
        begins): its agent, its job, its number, the member; nothing of its inputs. Its end is the RUN's own record; a page of
        its agent is told of it meanwhile (records.in_flight). A record that cannot be written stops nothing."""
        try:
            if not self.records.has_start(job_key, int(run)):
                self._record('job', agent_key, 'STARTED', '', job_key, int(run), account=account, member=member)
        except Exception:   # noqa: BLE001 - the RUN itself matters more than this note of it
            LOG.warning('a start could not be recorded for %s', agent_key)

    def _asks(self, manifest, answer, key, member):
        """What the answer asks THE OUTSIDE HAND to make, checked before anything leaves: [] when nothing; refused when the
        manifest declares no such model, the ask is not the model's own grammar, or the member's day is full."""
        makes = answer.get('makes')
        if makes is None:
            return []
        allowed = outside.declared(manifest)
        if not allowed:
            raise _Stop('FAILED', 'the answer asks for something to be made, but the agent declares no "makes"; nothing was sent')
        asks, why = outside.check(makes, allowed)
        if why:
            raise _Stop('FAILED', f'not made, bad ask: {why}; nothing was sent')
        return asks

    def _provider_key(self, provider, agent_key, job_key, run, account, scope, member, whose='platform'):
        """THE KEY FOR ONE ERRAND, FROM ITS ONE HOME (the owner, 2026-10-08: "the replicate token is on production and should point
        to that directly always its a single source setup"): asked of wid for this open RUN of this member; wid reads the
        platform's vault at that moment, for the agent the RUN's own job holds, and decides. -> the key, or '' when wid hands
        none. It lives in this call's memory only: never kept, never written, never in a reason or a log."""
        if locker.held(self.db, agent_key, self.caller) is None:
            return ''
        asked = {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run), 'provider': provider}
        if whose == 'member':   # the RUN's own member's key (row 92 b); the platform's is asked exactly as before
            asked['whose'] = 'member'
        status, body = self.client.post('wid', '/jobs/provider_key', asked)
        held = body.get('key') if status == 200 and isinstance(body, dict) else ''
        return held if isinstance(held, str) else ''

    def _made(self, asks, agent_key, job_key, run, account, member, scope=''):
        """The errand itself: each ask made by the outside hand with the platform's own key for that provider, asked of wid
        (the platform's vault) for this one errand and passed nowhere else. -> the files, as the DA-M store takes them. What a provider says is never carried: the
        reason is the hand's own fixed words.
        THE DAILY LIMIT IS THE BILL'S GUARD, AND IT FAILS CLOSED: every errand is written down BEFORE it leaves (a 'make' record: the
        agent, the member, the job) and then counted with the others of the member's day; over the limit, a limit that is not a
        whole number, a member the platform did not name, or records that cannot be written or counted: nothing is sent. An
        errand counts whatever becomes of it after (a provider that was paid and a DA-M that then refused is still a paid errand)."""
        out = []
        for ask in asks:
            provider = outside.MODELS[ask['model']]['provider']
            hand, more = self.hands[provider], {}
            if provider == 'exxact':   # NO VAULT KEY: the box is reached through the buckets with the runtime's own token; wid is not asked for a key
                provider_key, more = '', {'asker': {'card': agent_key, 'job_key': job_key, 'member': member}}
            else:
                mine = ask.get('key') == 'mine'   # THE MEMBER'S OWN KEY (row 92 b): theirs or nothing, never the platform's in its place
                provider_key = self._provider_key(provider, agent_key, job_key, run, account, scope, member, **({'whose': 'member'} if mine else {}))   # the platform's: asked exactly as before
                if not provider_key and mine:
                    raise _Stop('FAILED', f'not made, no {outside.PROVIDERS[provider]["name"]} key of your own: keep one on your member card (YOUR KEYS), or make it with the platform\'s; nothing was sent')
                if not provider_key:
                    raise _Stop('FAILED', f'not made, no {outside.PROVIDERS[provider]["name"]} key: the platform\'s vault handed none; nothing was sent')
            records = []
            picture = self._reference(ask, account, scope, member, job_key, run, records)   # read before the day is counted: a reference that cannot be read sends nothing and costs nothing
            if ask.get('companion_of') == 'reference' and not (records and records[0]):   # BESIDE ITS REFERENCE'S RECORD (94 b): the record wid names for the first reference, or nothing is sent
                raise _Stop('FAILED', f"not made, the made file is the companion of its reference, whose record the platform did not name: {(ask.get('reference') or [''])[0]}; nothing was sent")
            most = self.a_day.get(outside.MODELS[ask['model']]['kind'])
            if not (isinstance(most, int) and not isinstance(most, bool) and most >= 0 and member and agent_key):
                raise _Stop('REFUSED', 'the day is not counted: no limit is set for this kind, or the member is not named; nothing was sent')
            try:
                self.records.record('make', agent_key, 'SENT', '', job_key, int(run), 0, caller=self.caller, account=account, member=member)
                sent = self.records.sent_today(agent_key, member)
            except Exception:   # noqa: BLE001 - whatever kept the day from being written or counted, nothing leaves
                LOG.error('the day could not be counted for %s: nothing was sent', agent_key)
                raise _Stop('REFUSED', 'the day is not counted: LARRYD could not write or read its own record; nothing was sent')
            if sent > most:
                raise _Stop('REFUSED', f'the day is full: {most} a day; nothing was sent')
            made, why = hand.make(ask, provider_key, picture, **more)
            trace = getattr(hand, 'last', None) or {}   # THE MAKE'S TRACE (frost-05 2026-11-07): the provider's own id and, failed, our word for why
            try:
                self.records.record('made', agent_key, 'FAILED' if why else 'DONE', f'not made, {why}' if why else '', job_key, int(run), 0,
                                    caller=self.caller, account=account, member=member,
                                    provider_ref=str(trace.get('ref') or ''), error_class=(str(trace.get('class') or 'other') if why else ''))
            except Exception:   # noqa: BLE001 - the trace is for finding a make at the provider; a record that cannot be written never stops the RUN
                LOG.error('the make trace could not be written for %s', agent_key)
            if why:
                raise _Stop('FAILED', f'not made, {why}')
            out.append({'name': made['name'], 'content_b64': base64.b64encode(made['data']).decode('ascii'), 'asked_as': ask['name'],
                        **({'beside': records[0]} if ask.get('companion_of') == 'reference' else {})})   # stored with its reference's record as its source (94 b)
        return out

    def _reference(self, ask, account, scope, member, job_key, run, records=None):
        """THE REFERENCE PICTURES (R-0040 / R-0041, the owner 2026-10-24; up to two: CORE_CLEANUP_IV 18): when the ask names them (DA-M
        keys the member typed or picked on the agent's page, checked by outside.check), each one's bytes are read through wid's job
        file door FOR THIS MEMBER, while their RUN is open (wid decides and asks DA-M as itself).
        -> [bytes, ...] in the ask's order, [] when the ask names none. They live in this call's memory only and go to the provider's
        file door and nowhere else: never to the agent, never kept. Any key that cannot be read stops the errand before anything is sent.
        BY KIND, PER MODEL (the lips gaps closed, 2026-11-06): the n-th reference must be a kind the model's n-th reference slot takes,
        read from its first bytes (outside.reference_kind), within that slot's most bytes (outside.MODELS[model]['reference_rules']: a
        picture within MOST_REFERENCE for Replicate's models, as before; an Exxact type's own input slots, its wav and mp4 among them)."""
        wanted = ask.get('reference') or []
        rules = outside.MODELS[ask['model']]['reference_rules']
        pictures_only = all(set(kinds) <= set(outside.REFERENCE_KINDS) for kinds, _most in rules)
        out = []
        for n, dam_key in enumerate([wanted] if isinstance(wanted, str) else wanted):
            _kinds, slot_most = rules[n] if n < len(rules) else ((), 0)
            slot_most = min(slot_most, outside.MOST_ASK_REFERENCES - sum(len(x) for x in out))   # THE ASK'S OWN MOST: what is left of it for this reference
            status, body = self.client.get('wid', '/jobs/file', {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run), 'dam_key': dam_key},
                                           most=-(-slot_most // 3) * 4 + ANSWER_ROOM)   # THE SIZE FIRST: never read past this slot's most bytes (as base64) and the answer's few words (the lips gaps, 2026-11-06)
            if status == 413:
                raise _Stop('FAILED', f'not made, reference too large: {dam_key} is over {slot_most // (1024 * 1024)} MB; nothing was sent')
            raw = body.get('content_b64') if status == 200 and isinstance(body, dict) else None
            try:
                picture = base64.b64decode(raw, validate=True) if isinstance(raw, str) else b''
            except (binascii.Error, ValueError):
                picture = b''
            if not picture:
                said = (body.get('refused') or body.get('error')) if isinstance(body, dict) else ''
                raise _Stop('FAILED', f"not made, reference unreadable: DA-M did not hand {dam_key} ({said if isinstance(said, str) and said else f'wid answered {status}'}); nothing was sent")
            kinds, most = rules[n] if n < len(rules) else ((), 0)   # outside.check keeps the count within the model's most: no slot, no kind
            if not outside.reference_kind(picture, kinds):
                raise _Stop('FAILED', f'not made, reference not {"a picture" if pictures_only else "a kind its slot takes"}: {dam_key}; nothing was sent')
            if len(picture) > slot_most:   # its slot within what is left of the ask
                raise _Stop('FAILED', f'not made, reference too large: {dam_key} is over {slot_most // (1024 * 1024)} MB; nothing was sent')
            if records is not None:   # THE RECORD EACH REFERENCE BELONGS TO, as wid names it (its DA-M source_key, a member's record key), else ''
                record = body.get('source_key') if isinstance(body, dict) else None
                records.append(record if isinstance(record, str) and RECORD_KEY.fullmatch(record) else '')
            out.append(picture)
        return out

    def _keeps(self, manifest, answer, files, asks, custom=False):
        """The records the answer asks for, one per stored file: keeps = [{species, values, file}], each an ADD the manifest
        declares on that species (checked as a CALL's writes are), each naming a file this RUN stores (a file the answer
        carries, by its name; a made one, by the ask's name). -> [{species, values, file: the stored file's name}]."""
        keeps = answer.get('keeps')
        if keeps is None:
            return []
        wanted = member_records.declared(manifest)
        if not (isinstance(keeps, list) and keeps and len(keeps) <= MOST_KEEPS and all(isinstance(k, dict) and set(k) == {'species', 'values', 'file'} for k in keeps)):
            raise _Stop('FAILED', f'the answer\'s keeps are not a list of at most {MOST_KEEPS} of {{species, values, file}}; nothing was sent')
        _writes, why = member_records.check([{'do': 'add', 'species': k['species'], 'values': k['values']} for k in keeps], wanted, custom=custom)
        if why:
            raise _Stop('FAILED', f'not kept: {why}; nothing was sent')
        names = [f['name'] for f in files] + [a['name'] for a in asks]   # a carried file by its own name, a made one by its ask's name
        if len(set(names)) != len(names):
            raise _Stop('FAILED', 'two files of this run share one name: a record could not tell which is its own; nothing was sent')   # ONE NAME, ONE FILE: a keep never lands on another file than the one it names
        out, kept = [], set()
        for n, k in enumerate(keeps, 1):
            if 'identity_dam_file' in k['values']:
                raise _Stop('FAILED', f'keep {n} names the file\'s own key, which is LARRYD\'s to fill; nothing was sent')
            if not (isinstance(k['file'], str) and k['file'] in names):
                raise _Stop('FAILED', f'keep {n} names a file this run does not store; nothing was sent')
            if k['file'] in kept:
                raise _Stop('FAILED', f'keep {n} names a file another keep already holds: one file, one record; nothing was sent')
            kept.add(k['file'])
            out.append({'species': k['species'], 'values': k['values'], 'file': k['file']})
        return out

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
            if not (isinstance(f, dict) and set(f) in ({'name', 'content_b64'}, {'name', 'content_b64', 'companion_of'}) and isinstance(f['name'], str)
                    and FILE_NAME.match(f['name']) and isinstance(f['content_b64'], str) and isinstance(f.get('companion_of', ''), str)):
                raise _Stop('FAILED', f'file {i} is not {{name, content_b64}} (and an optional companion_of) with a plain name; the delivery is withheld')
            try:
                size = len(base64.b64decode(f['content_b64'], validate=True))
            except (binascii.Error, ValueError):
                raise _Stop('FAILED', f'file {i} is not base64; the delivery is withheld')
            if size == 0:
                raise _Stop('FAILED', f'file {i} is empty; the delivery is withheld')
        return files

    @staticmethod
    def _companions(files, handed, records=None):
        """A FILE STORED BESIDE THE MEMBER'S OWN (CORE_CLEANUP_IV 94; rows 260 and 9, frost-05 2026-11-06): an answer file may carry
        "companion_of": <one of this RUN's handed file inputs> (stored with that input file's own record as its source: a picture's
        preview beside the picture), or <the key of a record this RUN was handed in its records> (stored with that record as its
        source: an invoice's PDF beside its invoice). -> {the file's place in files: the record key}. Refused, nothing charged or
        stored: a name that is neither, or a handed file whose record wid did not name. A record key is taken only as handed here:
        the platform read those records for this RUN's member."""
        own = {r['key'] for rows in (records.values() if isinstance(records, dict) else []) if isinstance(rows, list)
               for r in rows if isinstance(r, dict) and isinstance(r.get('key'), str) and r['key']}
        out = {}
        for n, f in enumerate(files):
            name = f.get('companion_of')
            if name is None:
                continue
            got = (handed or {}).get(name) if isinstance(handed, dict) else None
            if isinstance(got, dict):
                if not got.get('record_key'):
                    raise _Stop('FAILED', f'file {n + 1} is the companion of "{name}", whose record the platform did not name; the delivery is withheld')
                out[n] = got['record_key']
            elif name in own:
                out[n] = name
            else:
                raise _Stop('FAILED', f'file {n + 1} is the companion of "{name}", which is neither a file nor a record this RUN was handed; the delivery is withheld')
        return out

    def _skill_hands(self, manifest, account, scope, member, job_key, run):
        """The skills the agent declares, carried out before the RUN: -> {hand: what it hands}. A skill LARRYD does not have
        fails the run; a skill with no hand (the mTok charge) hands nothing. What is handed is kept nowhere. Each call names
        the RUN it is for (scope, job_key, run): the platform answers only for a member of a RUN that is open now."""
        declared = manifest.get('skills') or []
        if not (isinstance(declared, list) and all(isinstance(h, str) for h in declared)):
            raise _Stop('FAILED', 'the agent\'s skills are not a list of hashes')
        unknown = [h for h in declared if h not in SKILLS]
        if unknown:
            raise _Stop('FAILED', f'the agent declares a skill LARRYD does not have: {unknown[0][:12]}')
        out = {}
        for h in declared:
            hand = SKILLS[h].get('hand')
            if hand not in HANDED:
                continue
            office, route, what, who = HANDED[hand]
            status, body = self.client.get(office, route, {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run)})
            if status != 200:
                raise _Stop('FAILED', f"LARRYD could not read {what}: {body.get('refused') or body.get('error') or f'{who} answered {status}'}")
            out[hand] = body
        return out

    def live_records(self, agent_key, account, scope, member, do, species, key='', values=None):
        """THE ROOM PROGRAM'S ASK OF THE MEMBER'S RECORDS (the owner, 2026-10-08: "this data needs to be stored in the sprint module"):
        an agent's live page keeps what its members write in the member's own records on the platform, never in a store of
        its own. The ask is held exactly as a CALL's records are: the agent is in the locker, its APPROVED manifest declares a
        live page AND this species with this verb, its card is approved and hired by that member (the gate), and the platform's
        own doors for agents decide the rest (FROST's scope). The member's act is the send on their own live page, which only
        their pass opened. -> {'rows': [...]} for list; {'ok', 'key', 'why'} for add and edit. Nothing is kept."""
        held = locker.held(self.db, agent_key, self.caller)
        manifest = locker.manifest(self.agents, held['folder']) if held else None
        wanted = member_records.declared(manifest) if manifest and live.declared(manifest) else {}
        verb = live.DOES.get(do)
        if not verb or species not in wanted or verb not in wanted[species]:
            raise Refused(403, 'the agent does not declare it')
        ok, why = locker.verify(self.db, self.agents, held['agent_key'], self.caller)
        if not ok:
            raise Refused(403, why)
        cards, hired, groups, verify = self.facts(account, scope, member)
        card = self._card(cards, agent_key)
        if card is None:
            raise Refused(404, 'the agent has no APPROVED card')
        ok, why = gate.may_run(card, verify(agent_key), lanes.hired_on(hired, agent_key), groups)
        if not ok:
            self._record('live', agent_key, 'REFUSED', why, account=account, member=member)
            raise Refused(403, why)
        custom = fabric.custom(card, manifest, account)
        if do == 'list':
            return {'rows': member_records.read(self._ask, {species: ('read',)}, account, scope, member, agent_key, custom=custom).get(species, [])}
        writes, why = member_records.check([{'do': do, 'species': species, 'key': key, 'values': values}], wanted, custom=custom)
        if why:
            raise Refused(400, why)
        written = member_records.carry(self.client.post, writes, account, scope, member, agent_key)[0]
        return {'ok': written['ok'], 'key': written['key'], 'why': written['why']}

    def _identity(self, account, scope, member):
        """Who the member is, for a live page's pass, from wid's identity door (wid asks FROST as itself): {first_name,
        account_name, ...} as wid hands it; {} when wid does not answer a CALL with it (the page then says Member): never
        guessed, never read from anywhere else."""
        office, route, _what, _who = HANDED['identity']
        try:
            status, body = self.client.get(office, route, {'account': account, 'scope': scope, 'member': member})
        except Exception:   # the platform away: the pass goes without them
            return {}
        return body if status == 200 and isinstance(body, dict) else {}

    def _service_key(self, card, agent_key, job_key, run, account, scope, member):
        """THE SERVICE KEY OF A CONNECTOR (CORE_CLEANUP_IV 50, 53; frost-07's shape, 100): the service is the first plain word of the
        card's sends_to ("monday.com (...)" -> monday), asked of wid's /jobs/provider_key for this open RUN of this member; wid decides
        (an internal agent's approved card naming it first, the member's own Allow) and reads THE MEMBER'S OWN key from FROST's vault.
        -> {service, key}; {service, key: '', why: 'not allowed' | 'none stored'} when wid refuses for those reasons (the agent then
        draws its step and sends nothing); any other answer stops the RUN before it starts. The key lives in this RUN's memory only:
        never kept, never written, never in a reason or a log."""
        found = re.match(r'\s*([A-Za-z0-9_-]{1,32})', str((card or {}).get('sends_to') or ''))
        if not found:
            raise _Stop('FAILED', 'the agent hands "service_key" but its card names no service first in sends_to')
        service = found.group(1).lower()
        status, body = self.client.post('wid', '/jobs/provider_key', {'account': account, 'scope': scope, 'member': member, 'job_key': job_key,
                                                                     'run': str(run), 'provider': service})
        held = body.get('key') if status == 200 and isinstance(body, dict) else None
        if isinstance(held, str) and held:
            return {'service': service, 'key': held}
        said = str(body.get('refused') or '') if isinstance(body, dict) else ''
        if status == 403 and said.startswith('not allowed'):
            return {'service': service, 'key': '', 'why': 'not allowed'}
        if status == 404:
            return {'service': service, 'key': '', 'why': 'none stored'}
        raise _Stop('FAILED', f"LARRYD could not read the service key: {said or f'wid answered {status}'}")

    def _run_files(self, manifest, job, account, scope, member, job_key, run):
        """THE MEMBER'S FILES ON A RUN: the manifest's "files" names which of its job inputs carry a DA-M key ([name, ...], each a
        name in "inputs", at most MOST_RUN_FILES; the hand "files" needs the hand "job"). Each such input the member filled is read
        through wid's /jobs/file for THIS member while the RUN is open: -> {name: {dam_key, kind, bytes, content_b64}}; an input left
        empty is not handed. Held in this RUN's memory only, never kept. Stops before the agent runs: files not declared right
        (FAILED), an input that is not a DA-M key (REFUSED), a file wid or DA-M does not hand, or one over MOST_RUN_FILE (FAILED)."""
        names, declared = manifest.get('files'), manifest.get('inputs')
        if not isinstance(job, dict):
            raise _Stop('FAILED', 'the agent hands "files" but not "job": its files are named by its job inputs')
        if not (isinstance(names, list) and names and len(names) <= MOST_RUN_FILES and len(set(names)) == len(names)
                and all(isinstance(n, str) and isinstance(declared, dict) and n in declared for n in names)):
            raise _Stop('FAILED', f'the agent hands "files" but its "files" is not a list of at most {MOST_RUN_FILES} of its own inputs')
        out = {}
        for name in names:
            dam_key = job.get(name) or ''
            if not dam_key:
                continue
            if not outside.DAM_KEY.fullmatch(dam_key):
                raise _Stop('REFUSED', f'input {declared[name]} is not a DA-M key')
            status, body = self.client.get('wid', '/jobs/file', {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run), 'dam_key': dam_key},
                                           most=-(-MOST_RUN_FILE // 3) * 4 + ANSWER_ROOM)   # THE SIZE FIRST (as _reference, 44830a7): never read past MOST_RUN_FILE as base64 and the answer's few words
            if status == 413:
                raise _Stop('FAILED', f'the file of input {declared[name]} is over {MOST_RUN_FILE // (1024 * 1024)} MB: {dam_key}')
            raw = body.get('content_b64') if status == 200 and isinstance(body, dict) else None
            try:
                data = base64.b64decode(raw, validate=True) if isinstance(raw, str) else b''
            except (binascii.Error, ValueError):
                data = b''
            if not data:
                said = (body.get('refused') or body.get('error')) if isinstance(body, dict) else ''
                raise _Stop('FAILED', f"LARRYD could not read the file of input {declared[name]}: DA-M did not hand {dam_key} ({said if isinstance(said, str) and said else f'wid answered {status}'})")
            if len(data) > MOST_RUN_FILE:
                raise _Stop('FAILED', f'the file of input {declared[name]} is over {MOST_RUN_FILE // (1024 * 1024)} MB: {dam_key}')
            out[name] = {'dam_key': dam_key, 'kind': outside.kind_of(data), 'bytes': len(data), 'content_b64': base64.b64encode(data).decode('ascii')}
            record = body.get('source_key') if isinstance(body, dict) else None
            if isinstance(record, str) and RECORD_KEY.fullmatch(record):   # THE RECORD THE FILE BELONGS TO, when wid names it (CORE_CLEANUP_IV 94): an answer file may be stored as its companion
                out[name]['record_key'] = record
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
            raise _Stop('FAILED', f"LARRYD could not read the job's inputs: {body.get('refused') or body.get('error') or f'wid answered {status}'}")
        held = body.get('inputs')
        if not isinstance(held, dict):
            raise _Stop('FAILED', "LARRYD could not read the job's inputs: not {slot: value}")
        extra = sorted(set(held) - set(declared.values()))
        if extra:
            raise _Stop('REFUSED', f"the job holds input {', '.join(extra)}, which the agent does not declare")
        for slot, value in sorted(held.items()):
            if not isinstance(value, str):
                raise _Stop('REFUSED', f'input {slot} is not text')
            if len(value) > MOST_INPUT:
                raise _Stop('REFUSED', f'input {slot} is larger than {MOST_INPUT} characters')
        return {name: held[slot] for name, slot in declared.items() if slot in held}

    def _end(self, account, scope, member, key, job_key, run, state, log, charged=0, delivery='', job=None):
        """-> the state the run ended in. Its result goes back to the platform; when it never reaches it (after the
        client's retries) the record says so: state CALLBACK_FAILED, the error code the run's own (RUN_DONE for a done
        run), and a log line with the ids; never silent."""
        recorded, reason = state, ('' if state == 'DONE' else log)
        try:
            self._result(account, scope, job_key, run, state, log, delivery, job)
        except Refused:
            recorded, reason = 'CALLBACK_FAILED', (reason or 'RUN DONE')
            LOG.error('callback failed: job %s run %s ended %s, its result did not reach the platform', job_key, int(run), state)
        self._record('job', key, recorded, reason, job_key, int(run), charged, account=account, member=member)
        return state
