"""THE MEMBER'S RECORDS (the owner, 2026-10-07: "it's an agent and has access to the database; the core does not do this
work"): an agent whose approved manifest declares "records" ({"opns": ["read", "add", "edit", "remove"]}) is handed, on a
CALL, the member's records of each declared species, read through wid's own record doors for that member, as
records = {species: [rows]} (each row the record's fields, its key as "key"); and its answer may carry
writes = [{do: add | edit | remove, species, key, values}], each carried to wid's own doors for that member, only for a
declared species and verb; anything undeclared or ill-shaped refuses the whole answer, nothing is carried. The runtime
keeps none of it: the rows live in the call's memory, the writes go to wid and are gone. The manifest is in the agent's
hash, so FROST approves what an agent may read and write with the agent itself."""
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


def key_of(row):
    """A record's key: its M key column as the platform's list gives it, else its own "key"."""
    for name, value in row.items():
        if isinstance(name, str) and _M_KEY.fullmatch(name) and isinstance(value, str) and value:
            return value
    return row.get('key') if isinstance(row.get('key'), str) else ''


def read(ask, wanted, account, scope, member):
    """{species: [rows]} for every species declared with read, through wid's list door for this member, page by page
    up to MOST_ROWS; a refusal propagates (nothing is guessed when wid does not answer)."""
    out = {}
    for species, verbs in wanted.items():
        if 'read' not in verbs:
            continue
        rows, offset = [], 0
        while True:
            body = ask('wid', 'GET', '/agnt/records/list', {'account': account, 'scope': scope, 'member': member, 'segment': species,
                                                             'page': 'list', 'limit': str(PAGE), 'offset': str(offset)})
            got = [r for r in (body.get('rows') or []) if isinstance(r, dict)]
            rows += [{**r, 'key': key_of(r)} for r in got]
            offset += len(got)
            if not got or offset >= int(body.get('total') or 0) or offset >= MOST_ROWS:
                break
        out[species] = rows[:MOST_ROWS]
    return out


def check(writes, wanted):
    """-> (writes as the doors take them, '') or ([], why): every write a declared verb on a declared species, a plain key
    where one is needed, values a flat {field: text}; the first fault refuses them all."""
    if not isinstance(writes, list):
        return [], 'the answer\'s writes are not a list'
    if len(writes) > MOST_WRITES:
        return [], f'the answer carries {len(writes)} writes; at most {MOST_WRITES}'
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
                if not (isinstance(value, str) and len(value) <= MOST_VALUE):
                    return [], f'write {n}: "{name}" is not text of at most {MOST_VALUE} characters'
        out.append({'do': do, 'species': species, 'key': key if do != 'add' else '', 'values': values})
    return out, ''


def carry(post, writes, account, scope, member):
    """Each checked write to wid's own door for this member, in order; -> written = [{do, species, key, ok, why}], a
    refused write said as wid said it, the next still carried (each is the member's own ask)."""
    written = []
    for w in writes:
        method, route = DOORS[w['do']]
        data = {'account': account, 'scope': scope, 'member': member, 'segment': w['species']}
        if w['do'] != 'add':
            data['key'] = w['key']
        if w['do'] != 'remove':
            data['values'] = w['values']
        status, body = post('wid', route, data)
        body = body if isinstance(body, dict) else {}
        ok = status == 200
        key = (body.get('key') if ok and w['do'] == 'add' else w['key']) or ''
        written.append({'do': w['do'], 'species': w['species'], 'key': key if isinstance(key, str) else '', 'ok': ok,
                        'why': '' if ok else str(body.get('refused') or body.get('error') or f'wid answered {status}')[:300]})
    return written
