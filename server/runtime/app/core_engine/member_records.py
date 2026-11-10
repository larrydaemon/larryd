"""THE MEMBER'S RECORDS (the owner, 2026-10-07: "it's an agent and has access to the database; the core does not do this
work"): an agent whose approved manifest declares "records" ({"opns": ["read", "add", "edit", "remove"]}) is handed, on a
CALL, the member's records of each declared species, read through wid's own record doors for that member, as
records = {species: [rows]} (each row the record's fields, its key as "key"); and its answer may carry
writes = [{do: add | edit | remove, species, key, values}], each carried to wid's own doors for that member, only for a
declared species and verb; anything undeclared or ill-shaped refuses the whole answer, nothing is carried. The runtime
keeps none of it: the rows live in the call's memory, the writes go to wid and are gone. The manifest is in the agent's
hash, so FROST approves what an agent may read and write with the agent itself.
THE COUNTS (2026-10-09): a manifest that declares "records": {"*": ["count"]} is handed, on a CALL and on a RUN, counts =
{scope, modules: {species: how many}, products: {species: product}, ties: [[from, to, how many]]}: the numbers of the
member's own account as their own grid lets them list it, asked of wid's counts door; never a record, never a key."""
import os
import re

VERBS = ('read', 'add', 'edit', 'remove')
DOORS = {'read': ('GET', '/agnt/records/list'), 'add': ('POST', '/agnt/records/add'),
         'edit': ('POST', '/agnt/records/edit'), 'remove': ('POST', '/agnt/records/remove')}
SPECIES = re.compile(r'^[a-z]{4}$')             # a module's code on the platform (opns, cont, ...)
FIELD = re.compile(r'^[a-z][a-z0-9_]{0,63}$')   # a record's field, by the platform's own name
KEY = re.compile(r'^[A-Z0-9_]{1,64}$')          # a record's key, as the platform minted it
MOST_WRITES = 20        # in one answer
MOST_VALUE = 10_000     # characters in one written value
MOST_ROWS = 1000        # rows handed per species
PAGE = 200              # rows asked of wid at a time
_M_KEY = re.compile(r'^M[A-Z]+_norm_key$')      # the record's key column on the platform (M + the module's family + _norm_key)
CUSTOM = re.compile(r'^custom_[0-9]{4}$')        # a member's custom field bucket (custom_0001 .. custom_0100)


def declared(manifest):
    """{species: (verbs)}: what the manifest declares, well formed; an ill-formed declaration counts for nothing (fail closed)."""
    asked = manifest.get('records') if isinstance(manifest, dict) else None
    if not isinstance(asked, dict):
        return {}
    out = {}
    for species, verbs in asked.items():
        if isinstance(species, str) and SPECIES.fullmatch(species) and isinstance(verbs, list) and verbs \
                and all(isinstance(v, str) and v in VERBS for v in verbs):
            out[species] = tuple(dict.fromkeys(verbs))
    return out


EVERY, COUNT = '*', 'count'                     # THE COUNTS: "records": {"*": ["count"]}, of no one species
ROSTER = 'roster'                               # THE ROSTER (CORE_CLEANUP_IV 37): "records": {"*": ["roster"]} or {"*": ["count", "roster"]}: the account's members, read only, on a CALL
JOINS, PAYMENTS = 'joins', 'payments'            # THE JOIN REQUESTS and THE PAYMENTS (CORE_CLEANUP_IV row 142, pf Alerts): on a CALL, read only
JOINS_DOOR = ('GET', '/agnt/records/joins')        # wid's (frost-8f, e8e0e77d): {"requests": [{name, asked_at}]}, the roster's refusals
PAYMENTS_DOOR = ('GET', '/agnt/records/payments')  # wid's (frost-8f, e8e0e77d): {"payments": [{kind, amount_cents, landed_at}]}, the same
MOST_HANDED = 1000                                  # the join requests or payments handed at most; more refuses the answer whole
REVIEWS = 'reviews'                             # THE REVIEWS WAITING (CORE_CLEANUP_IV 23, pf Review Lane): "records": {"*": ["reviews"]}: on a CALL, an INTERNAL agent only
REVIEWS_DOOR = ('GET', '/agnt/reviews/waiting')  # wid's (frost-8f, item 23): {"waiting": [...]}; wid refuses any card that is not internal and SYSTEM's own (the second guard)
MOST_WAITING = 500                              # the reviews waiting handed at most; more refuses the answer whole
HISTORY = 'history'                             # THE REVIEW HISTORY (CORE_CLEANUP_IV row 78): "records": {"*": ["history"]}: on a CALL, an INTERNAL agent only
HISTORY_DOOR = ('GET', '/agnt/reviews/history')  # wid's (frost-8f, f9a169b2): {"history": [...]}; wid refuses any card that is not internal and SYSTEM's own (the second guard)
HISTORY_FIELDS = {'id', 'agent_key', 'card_key', 'name', 'code_sha256', 'manifest_sha256', 'state', 'submitted_at', 'decided_at', 'note'}
MOST_HISTORY = 1000                             # the history entries handed at most; more refuses the answer whole
GUARDS = 'guards'                               # THE TWO GUARDS' REPORTS (Agents Security Plan, the Agent Ecosystem agent): "records": {"*": ["guards"]}: on a CALL, an INTERNAL agent only
GUARDS_DOOR = ('GET', '/agnt/guards')           # wid's (060695c4): {"frost": FROST active monitoring's agents_report, "hades": HADES's}; wid refuses any account but SYSTEM's own (the second guard)
GUARDS_PARTS = {'rules', 'agents', 'counts', 'at'}   # each guard's report, as wid hands it
MOST_GUARD_ROWS = 1000                          # the rules or agents of one guard's report handed at most; more refuses the answer whole
INTERNAL_WORDS = (REVIEWS, HISTORY, GUARDS)      # words of "*" on LARRYD RUNTIME INTERNAL only (harness.Harness.INTERNAL decides whether they are ever asked)
INTERNAL = os.environ.get('LARRYD_INTERNAL') == '1'   # LARRYD RUNTIME INTERNAL (its start says so): there "*" may hold INTERNAL_WORDS beside the rest
EVERY_WORDS = (COUNT, ROSTER, JOINS, PAYMENTS)                   # what "*" may hold, each once; anything else under "*" counts for nothing (fail closed)
COUNTS_DOOR = ('GET', '/agnt/records/counts')
ROSTER_DOOR = ('GET', '/agnt/records/roster')   # wid's (frost-8f, 22203d5a): {"members": [{key, name, type, active[, organization]}]}, the same refusals as the counts door
MEMBER_KEY = re.compile(r'^MCON_[0-9A-F]{12}_[0-9A-F]{4}$')
MEMBER_TYPE = re.compile(r'^[a-z][a-z_]{0,39}$')   # owner, user, vendor, partner, system_owner ...
MOST_MEMBERS = 1000
SCOPE = re.compile(r'^[A-Za-z0-9]{1,40}$')      # an account's scope name, as the page shows it to the member (letters and digits alone)
PRODUCT = re.compile(r'^[a-z]{1,24}$')          # a product's slug


def _every(manifest, words=None):
    """What "*" declares, well formed: a list of EVERY_WORDS (and INTERNAL_WORDS on LARRYD RUNTIME INTERNAL; words: the list asked
    of), each once -> their set; anything else -> empty (fail closed)."""
    allowed = words if words is not None else EVERY_WORDS + (INTERNAL_WORDS if INTERNAL else ())
    asked = manifest.get('records') if isinstance(manifest, dict) else None
    words = asked.get(EVERY) if isinstance(asked, dict) else None
    if not (isinstance(words, list) and words and all(isinstance(w, str) and w in allowed for w in words) and len(set(words)) == len(words)):
        return set()
    return set(words)


def counts_declared(manifest):
    """Does the manifest declare THE COUNTS: "records": {"*": ["count"]}, or with the roster ["count", "roster"] (anything else
    under "*" counts for nothing, fail closed)? It is no right on any species: declared() never sees it."""
    return COUNT in _every(manifest)


def roster_declared(manifest):
    """Does the manifest declare THE ROSTER: "*" holds "roster" (alone or with "count")? No right on any species either."""
    return ROSTER in _every(manifest)


ROSTER_FIELDS = frozenset({'key', 'name', 'type', 'active'})   # and "organization" once wid hands it (row 21)


def rostered(body):
    """The roster door's answer as the agent is handed it, or ValueError: [{key, name, type, active, organization}], each a member's
    own key, a plain name, a type word, a yes or no, and the organization FROST keeps for that member (users_members.Organization,
    as typed: row 21, a vendor told from a partner; '' when it is empty or the platform does not hand it yet). Anything else
    (another field, another type, more than MOST_MEMBERS) refuses it whole."""
    members = body.get('members') if isinstance(body, dict) and set(body) == {'members'} else None
    if not (isinstance(members, list) and len(members) <= MOST_MEMBERS):
        raise ValueError('the roster is not {members: [...]}')
    out = []
    for m in members:
        if not (isinstance(m, dict) and set(m) in (ROSTER_FIELDS, ROSTER_FIELDS | {'organization'}) and isinstance(m['key'], str) and MEMBER_KEY.fullmatch(m['key'])
                and isinstance(m['name'], str) and len(m['name']) <= 200 and isinstance(m['type'], str) and MEMBER_TYPE.fullmatch(m['type'])
                and isinstance(m['active'], bool) and _plain(m.get('organization', ''), 200)):
            raise ValueError('a roster member is not {key, name, type, active, organization}')
        out.append({'key': m['key'], 'name': m['name'], 'type': m['type'], 'active': m['active'], 'organization': m.get('organization', '')})
    return out


def roster(ask, account, scope, member, agent_key=''):
    """THE ROSTER of the account the platform named, through wid's roster door for this member: -> [{key, name, type, active, organization}].
    A refusal propagates; an answer of any other shape is ValueError (nothing is handed)."""
    return rostered(ask('wid', ROSTER_DOOR[0], ROSTER_DOOR[1], {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key}))


def joins_declared(manifest):
    """Does the manifest declare THE JOIN REQUESTS: "*" holds "joins"? No right on any species either."""
    return JOINS in _every(manifest)


def payments_declared(manifest):
    """Does the manifest declare THE PAYMENTS: "*" holds "payments"? No right on any species either."""
    return PAYMENTS in _every(manifest)


def _plain(v, most):
    return isinstance(v, str) and len(v) <= most and v == v.strip() and '\n' not in v


def joined(body):
    """The joins door's answer as the agent is handed it, or ValueError: [{name, asked_at}], a plain name and a plain time; anything
    else (another field, more than MOST_HANDED) refuses it whole."""
    got = body.get('requests') if isinstance(body, dict) and set(body) == {'requests'} else None
    if not (isinstance(got, list) and len(got) <= MOST_HANDED):
        raise ValueError('the join requests are not {requests: [...]}')
    out = []
    for r in got:
        if not (isinstance(r, dict) and set(r) == {'name', 'asked_at'} and _plain(r['name'], 200) and _plain(r['asked_at'], 40)):
            raise ValueError('a join request is not {name, asked_at}')
        out.append({'name': r['name'], 'asked_at': r['asked_at']})
    return out


def paid(body):
    """The payments door's answer as the agent is handed it, or ValueError: [{kind, amount_cents, landed_at}], a plain kind word, a
    whole number of cents and a plain time; anything else (another field, a number that is not whole, more than MOST_HANDED)
    refuses it whole."""
    got = body.get('payments') if isinstance(body, dict) and set(body) == {'payments'} else None
    if not (isinstance(got, list) and len(got) <= MOST_HANDED):
        raise ValueError('the payments are not {payments: [...]}')
    out = []
    for r in got:
        if not (isinstance(r, dict) and set(r) == {'kind', 'amount_cents', 'landed_at'} and _plain(r['kind'], 40)
                and isinstance(r['amount_cents'], int) and not isinstance(r['amount_cents'], bool) and abs(r['amount_cents']) < 10 ** 12
                and _plain(r['landed_at'], 40)):
            raise ValueError('a payment is not {kind, amount_cents, landed_at}')
        out.append({'kind': r['kind'], 'amount_cents': r['amount_cents'], 'landed_at': r['landed_at']})
    return out


def joins(ask, account, scope, member, agent_key=''):
    """THE JOIN REQUESTS through wid's joins door for this member: -> [{name, asked_at}]. A refusal propagates; any other shape is
    ValueError (nothing is handed)."""
    return joined(ask('wid', JOINS_DOOR[0], JOINS_DOOR[1], {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key}))


def payments(ask, account, scope, member, agent_key=''):
    """THE PAYMENTS through wid's payments door for this member: -> [{kind, amount_cents, landed_at}]. A refusal propagates; any
    other shape is ValueError (nothing is handed)."""
    return paid(ask('wid', PAYMENTS_DOOR[0], PAYMENTS_DOOR[1], {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key}))


def reviews_declared(manifest):
    """Does the manifest declare THE REVIEWS WAITING: "*" holds "reviews"? No right on any species either."""
    return REVIEWS in _every(manifest, EVERY_WORDS + INTERNAL_WORDS)


def reviewed(body):
    """The reviews door's answer as the agent is handed it, or ValueError: {"waiting": [objects]}, at most MOST_WAITING; anything else
    (another field, a waiting entry that is not an object) refuses it whole."""
    waiting = body.get('waiting') if isinstance(body, dict) and set(body) == {'waiting'} else None
    if not (isinstance(waiting, list) and len(waiting) <= MOST_WAITING and all(isinstance(w, dict) for w in waiting)):
        raise ValueError('the reviews waiting are not {waiting: [...]}')
    return waiting


def reviews(ask, account, scope, member, agent_key=''):
    """THE REVIEWS WAITING through wid's reviews door for this member: -> [entries]. A refusal propagates; an answer of any other
    shape is ValueError (nothing is handed). Asked only by LARRYD RUNTIME INTERNAL (harness._reviews)."""
    return reviewed(ask('wid', REVIEWS_DOOR[0], REVIEWS_DOOR[1], {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key}))


def history_declared(manifest):
    """Does the manifest declare THE REVIEW HISTORY: "*" holds "history"? No right on any species either."""
    return HISTORY in _every(manifest, EVERY_WORDS + INTERNAL_WORDS)


def historied(body):
    """The history door's answer as the agent is handed it, or ValueError: {"history": [entries]}, each exactly HISTORY_FIELDS, its
    state approved or revoked, its words plain text; at most MOST_HISTORY; anything else refuses it whole."""
    got = body.get('history') if isinstance(body, dict) and set(body) == {'history'} else None
    if not (isinstance(got, list) and len(got) <= MOST_HISTORY):
        raise ValueError('the review history is not {history: [...]}')
    for h in got:
        if not (isinstance(h, dict) and set(h) == HISTORY_FIELDS and h['state'] in ('approved', 'revoked')
                and isinstance(h['id'], (int, str)) and not isinstance(h['id'], bool)
                and all(isinstance(h[f], str) and len(h[f]) <= 4000 for f in HISTORY_FIELDS - {'id'})):
            raise ValueError('a history entry is not its ten fields')
    return got


def history(ask, account, scope, member, agent_key=''):
    """THE REVIEW HISTORY through wid's history door for this member: -> [entries]. A refusal propagates; any other shape is
    ValueError (nothing is handed). Asked only by LARRYD RUNTIME INTERNAL (harness._history)."""
    return historied(ask('wid', HISTORY_DOOR[0], HISTORY_DOOR[1], {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key}))


def guards_declared(manifest):
    """Does the manifest declare THE TWO GUARDS' REPORTS: "*" holds "guards"? No right on any species either."""
    return GUARDS in _every(manifest, EVERY_WORDS + INTERNAL_WORDS)


def guarded(body):
    """The guards door's answer as the agent is handed it, or ValueError: {"frost": report, "hades": report}, each report exactly
    {rules: [objects], agents: [objects], counts: {word: a whole number}, at: plain time}, at most MOST_GUARD_ROWS rules and agents
    each; anything else (another guard, another part, a part of another kind) refuses it whole."""
    if not (isinstance(body, dict) and set(body) == {'frost', 'hades'}):
        raise ValueError('the guards are not {frost, hades}')
    for name in ('frost', 'hades'):
        r = body[name]
        if not (isinstance(r, dict) and set(r) == GUARDS_PARTS
                and all(isinstance(r[p], list) and len(r[p]) <= MOST_GUARD_ROWS and all(isinstance(x, dict) for x in r[p]) for p in ('rules', 'agents'))
                and isinstance(r['counts'], dict) and all(isinstance(k, str) and _whole(n) for k, n in r['counts'].items())
                and _plain(r['at'], 40)):
            raise ValueError(f'the {name} guard\'s report is not {{rules, agents, counts, at}}')
    return {'frost': body['frost'], 'hades': body['hades']}


def guards(ask, account, scope, member, agent_key=''):
    """THE TWO GUARDS' REPORTS through wid's guards door for this member: -> {frost, hades}. A refusal propagates; any other shape is
    ValueError (nothing is handed). Asked only by LARRYD RUNTIME INTERNAL (harness._guards)."""
    return guarded(ask('wid', GUARDS_DOOR[0], GUARDS_DOOR[1], {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key}))


def _whole(n):
    return isinstance(n, int) and not isinstance(n, bool) and 0 <= n < 10 ** 12


def counted(body):
    """The counts door's answer as the agent is handed it, or ValueError: {scope, modules: {species: how many},
    products: {species: its product's slug}, ties: [[from, to, how many]]}. Numbers, module codes, product slugs and the
    scope's name alone: anything else in the answer (a key, a word, a part the runtime does not know) refuses it whole."""
    if not isinstance(body, dict) or set(body) - {'scope', 'modules', 'products', 'ties'}:
        raise ValueError('the counts are not {scope, modules, products, ties}')
    scope, modules, products, ties = body.get('scope'), body.get('modules'), body.get('products', {}), body.get('ties')
    if not (isinstance(scope, str) and SCOPE.fullmatch(scope)):
        raise ValueError('the counts name no scope')
    if not (isinstance(modules, dict) and len(modules) <= 64 and all(isinstance(k, str) and SPECIES.fullmatch(k) and _whole(n) for k, n in modules.items())):
        raise ValueError('the counts\' modules are not {species: a whole number}')
    if not (isinstance(products, dict) and all(k in modules and isinstance(v, str) and PRODUCT.fullmatch(v) for k, v in products.items())):
        raise ValueError('the counts\' products are not {species: a product}')
    if not (isinstance(ties, list) and len(ties) <= 64 * 64 and all(
            isinstance(t, list) and len(t) == 3 and isinstance(t[0], str) and isinstance(t[1], str) and t[0] in modules and t[1] in modules and _whole(t[2]) for t in ties)):
        raise ValueError('the counts\' ties are not [[from, to, a whole number]] between counted modules')
    return {'scope': scope, 'modules': dict(modules), 'products': dict(products), 'ties': [list(t) for t in ties]}


def counts(ask, account, scope, member, agent_key=''):
    """THE COUNTS of the member the platform named, through wid's counts door: how many records they may list in each
    module and how many ties between two of them; never a record. A refusal propagates; an answer that is not numbers
    and codes alone is ValueError (nothing is handed)."""
    return counted(ask('wid', COUNTS_DOOR[0], COUNTS_DOOR[1], {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key}))


def key_of(row):
    """A record's key: its M key column as the platform's list gives it, else its own "key"."""
    for name, value in row.items():
        if isinstance(name, str) and _M_KEY.fullmatch(name) and isinstance(value, str) and value:
            return value
    return row.get('key') if isinstance(row.get('key'), str) else ''


# WHY THE RECORDS WERE NOT HANDED, IN ONE WORD (frost-05 2026-11-06, frost-99's and frost-e4's finding: an agent handed nothing could not
# tell "the member has not pressed Allow" from any other failure): given['records_refused'] is one of these, never more. Read from wid's
# own fixed refusal sentences (larryd_runtime.records_right), exactly; anything else, wid away or a shape it never says: 'failed'.
REFUSED_WORDS = (("refused by FROST: not allowed to send this member's data out", 'no_allowance'),
                 ('refused by FROST: not in the records that agent declares', 'not_declared'))


def refused_word(status, reason):
    """-> 'no_allowance' | 'not_declared' | 'failed': the one word an agent is handed when its records were not."""
    if status == 403 and isinstance(reason, str):
        for said, word in REFUSED_WORDS:
            if reason == said:
                return word
    return 'failed'


def read(ask, wanted, account, scope, member, agent_key='', custom=False, most=MOST_ROWS):
    """{species: [rows]} for every species declared with read, through wid's list door for this member, page by page
    up to MOST_ROWS; a refusal propagates (nothing is guessed when wid does not answer). CUSTOM DATA ONLY ON CUSTOM
    AGENTS (the owner, 2026-10-25): unless custom, every row is handed without its custom field buckets. most: the rows
    handed per species (THE DATA FABRIC's RUN matches against more than a page shows)."""
    out = {}
    for species, verbs in wanted.items():
        if 'read' not in verbs:
            continue
        rows, offset, first = [], 0, []
        while True:
            body = ask('wid', 'GET', '/agnt/records/list', {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key, 'segment': species,
                                                             'page': 'list', 'limit': str(PAGE), 'offset': str(offset)})
            got = [r for r in (body.get('rows') or []) if isinstance(r, dict)]
            rows += [{**(r if custom else plain(r)), 'key': key_of(r)} for r in got]
            first = first or [k for k in (body.get('first') or []) if isinstance(k, str)]   # the member's BY PRIORITY keys in rank order (the platform's one priority)
            offset += len(got)
            if not got or offset >= int(body.get('total') or 0) or offset >= most:
                break
        rank = {k: n for n, k in enumerate(first, 1)}
        for r in rows:   # the rank rides on the row as 'priority' (1..n), like 'key'; a row off the list carries none
            if r['key'] in rank:
                r['priority'] = rank[r['key']]
            else:
                r.pop('priority', None)
        out[species] = rows[:most]
    return out


def plain(row):
    """A row without the members' custom field buckets: what an agent that is not custom is handed."""
    return {k: v for k, v in row.items() if not (isinstance(k, str) and CUSTOM.fullmatch(k))}


def check(writes, wanted, custom=False, most=MOST_WRITES):
    """-> (writes as the doors take them, '') or ([], why): every write a declared verb on a declared species, a plain key
    where one is needed, values a flat {field: text}; the first fault refuses them all."""
    if not isinstance(writes, list):
        return [], 'the answer\'s writes are not a list'
    if len(writes) > most:
        return [], f'the answer carries {len(writes)} writes; at most {most}'
    out = []
    for n, w in enumerate(writes, 1):
        if not isinstance(w, dict):
            return [], f'write {n} is not an object'
        do, species = w.get('do'), w.get('species')
        if not (isinstance(species, str) and species in wanted):
            return [], f'write {n} names a species the agent does not declare'
        if not (isinstance(do, str) and do in ('add', 'edit', 'remove') and do in wanted[species]):
            return [], f'write {n} asks to {do if isinstance(do, str) else "?"} {species}, which the agent does not declare'
        key = w.get('key', '')
        if do != 'add' and not (isinstance(key, str) and KEY.fullmatch(key)):
            return [], f'write {n} ({do}) names no record key'
        values = w.get('values', {}) if do != 'remove' else {}
        if do != 'remove':
            if not (isinstance(values, dict) and values):
                return [], f'write {n} ({do}) carries no values'
            for name, value in values.items():
                if not (isinstance(name, str) and FIELD.fullmatch(name)):
                    return [], f'write {n} names a field that is not a plain field name'
                if CUSTOM.fullmatch(name) and not custom:
                    return [], f'write {n} names a custom field, which only a custom agent may write'
                if not (isinstance(value, str) and len(value) <= MOST_VALUE):
                    return [], f'write {n}: "{name}" is not text of at most {MOST_VALUE} characters'
        out.append({'do': do, 'species': species, 'key': key if do != 'add' else '', 'values': values})
    return out, ''


def carry(post, writes, account, scope, member, agent_key=''):
    """Each checked write to wid's own door for this member, in order; -> written = [{do, species, key, ok, why}], a
    refused write said as wid said it, the next still carried (each is the member's own ask)."""
    written = []
    for w in writes:
        method, route = DOORS[w['do']]
        data = {'account': account, 'scope': scope, 'member': member, 'agent_key': agent_key, 'segment': w['species']}   # the agent's own card key: wid lets through only an approved agent the member hired, for what its card declares
        if w['do'] != 'add':
            data['key'] = w['key']
        if w['do'] != 'remove':
            data['values'] = w['values']
        status, body = post('wid', route, data)
        body = body if isinstance(body, dict) else {}
        ok = status == 200
        key = body.get('key') if ok and w['do'] == 'add' else w['key']
        key = key if isinstance(key, str) and (not key or KEY.fullmatch(key)) else ''   # a key wid answers is a plain key or nothing
        if ok and w['do'] == 'add' and not key:   # the platform took it but minted no record yet (partial data waits at its entry): said, never claimed
            ok = False
        written.append({'do': w['do'], 'species': w['species'], 'key': key, 'ok': ok,
                        'why': '' if ok else str(body.get('refused') or body.get('error') or ('no record was made' if status == 200 else f'wid answered {status}'))[:300]})
    return written
