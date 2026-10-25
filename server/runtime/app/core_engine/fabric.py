"""THE LARRY DATA FABRIC (the owner, 2026-10-25): the account's own business data, dropped as one of sixteen known files
(pf_contacts.csv .. pf_jobs.csv, one per module) into any DA-M drop zone, comes into that module's CUSTOM FIELDS and
nowhere else. The work is the agent's (PF DATA FABRIC): it reads the files, filters the rows, matches each row to a
record and says what to write. The runtime only hands and carries, as for every agent:

  on a RUN of an agent whose approved manifest declares "fabric": {"modules": [...]} (and the records lane for those
  modules: read, edit), it is handed given["fabric"] = {files: the newest official version of each file, from
  DA-M while the RUN is open; state: the account's Fabric state, from FROST's datafabric.db} and the records of those
  modules WITH their custom fields; its answer's "fabric" = {writes, state} is checked whole (one fault refuses it
  all), the writes carried through wid's own record doors for the member, and the state saved back to FROST with the
  record each row landed on. THE FABRIC ONLY EDITS: a row lands on a record that exists; a row that matches none stays in
  its official file (DA-M), tracked in FROST by its id and id_import, until its record exists (wid keeps partial data as
  one waiting entry, RULE 13: an add of custom fields alone would keep the first such row and lose the rest);
  on a CALL (its dashboard view) it is handed given["fabric"] = {state} only.

Nothing is kept here: the files and rows live in the call's memory, the values go to wid, the state to FROST."""
import json
import pathlib
import re

from . import member_records, view

FILES = {'pf_contacts.csv': 'cont', 'pf_invoices.csv': 'invc', 'pf_locations.csv': 'locn', 'pf_operations.csv': 'opns',
         'pf_hierarchies.csv': 'hrcy', 'pf_media.csv': 'mdia', 'pf_brands.csv': 'brnd', 'pf_sprints.csv': 'sprt',
         'pf_images.csv': 'imgs', 'pf_videos.csv': 'vdeo', 'pf_audio.csv': 'audo', 'pf_productions.csv': 'prdn',
         'pf_agents.csv': 'agnt', 'pf_models.csv': 'mdls', 'pf_logs.csv': 'logs', 'pf_jobs.csv': 'jobs'}   # THE SIXTEEN NAMES, one per module (DA-M knows the same list)
MODULES = frozenset(FILES.values())
NEEDS = ('read', 'edit')   # what the records lane must declare on each Fabric module: it reads them and edits their custom fields
MOST_WRITES = 5000                # record writes one RUN may carry
FIELDS, FIELD_BYTES = 100, 48     # THE SIZE LIMIT, BASED ON 100 FIELDS (the owner, 2026-10-25): a row's write names up to 100 custom
                                  # fields, each about 48 bytes as JSON (its name and a typical value)
MOST_ANSWER = MOST_WRITES * FIELDS * FIELD_BYTES + 1_000_000   # a Fabric RUN's answer: its most writes of 100 fields, and 1 MB for the rest (25 MB)
MOST_ROWS = 20000                 # rows one state list may hold
MOST_TEXT = 10_000                # characters in one state value
TABLES = {'files': ('file_name', 'dam_key', 'version', 'imported_at', 'rows_in', 'rows_held', 'rows_waiting', 'held_dam_key', 'preview'),
          'held': ('file_name', 'row_number', 'row_id', 'why', 'row_text', 'held_at'),
          'slots': ('segment', 'slot', 'header'),
          'ids': ('segment', 'row_id', 'id_import', 'id_lookup', 'record_key', 'made_at')}   # FROST's datafabric.db, per account (fabric_<table>)
STATE_DOOR = '/fabric/state'
FILES_DOOR = '/dam/fabric'
ROW_ID = re.compile(r'^[^\x00-\x1f]{1,200}$')


def declared(manifest):
    """The Fabric modules the approved manifest declares, each one also declared on the records lane with read, add and
    edit; [] when it declares none (an ill-formed declaration counts for nothing, fail closed)."""
    asked = manifest.get('fabric') if isinstance(manifest, dict) else None
    modules = asked.get('modules') if isinstance(asked, dict) else None
    if not isinstance(modules, list):
        return []
    lane = member_records.declared(manifest)
    return [m for m in dict.fromkeys(modules) if isinstance(m, str) and m in MODULES and all(v in lane.get(m, ()) for v in NEEDS)]


def custom(card, manifest, account):
    """CUSTOM DATA ONLY ON CUSTOM AGENTS (the owner, 2026-10-25: "custom would be meaning we custom build it for that
    customer"): an agent that is PRIVATE to this very account, or THE DATA FABRIC itself (it fills the custom fields)."""
    if declared(manifest):
        return True
    card = card if isinstance(card, dict) else {}
    return str(card.get('authorization') or '').strip().upper() == 'PRIVATE' and bool(account) and card.get('account_key') == account


def state(ask, account, scope, member):
    """The account's Fabric state from FROST: {files, held, slots, ids, apis, databases} (the last two Positive Feedback's own
    look, shown to every account); a refusal propagates."""
    body = ask('fs', 'GET', STATE_DOOR, {'account': account, 'scope': scope, 'member': member})
    return {t: [r for r in (body.get(t) or []) if isinstance(r, dict)] for t in (*TABLES, 'apis', 'databases')}


def files(ask, account, scope, member, job_key, run):
    """The newest official version of each of the sixteen files, with its text, from DA-M (only while this RUN is open:
    DA-M's own rule); a refusal propagates."""
    body = ask('so', 'GET', FILES_DOOR, {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run), 'content': 'yes'})
    return [f for f in (body.get('files') or []) if isinstance(f, dict) and f.get('name') in FILES]


def _rows(rows, columns, table):
    if not (isinstance(rows, list) and len(rows) <= MOST_ROWS):
        return None, f'the state\'s {table} is not a list of at most {MOST_ROWS}'
    out = []
    for n, r in enumerate(rows, 1):
        if not (isinstance(r, dict) and set(r) <= set(columns) and all(isinstance(v, str) and len(v) <= MOST_TEXT for v in r.values())):
            return None, f'the state\'s {table} row {n} is not {{{", ".join(columns)}}} as text'
        out.append({c: r.get(c, '') for c in columns})
    return out, ''


def check(answer, modules):
    """The answer's "fabric" checked whole -> (writes, rows of each write, state, why). writes: records-lane writes, each
    on a declared Fabric module, an edit naming its record, its values custom field buckets alone; each may name
    the row it carries ("row": {segment, row_id}). state: {files, held, slots, ids} of text rows."""
    asked = answer.get('fabric') if isinstance(answer, dict) else None
    if not isinstance(asked, dict) or set(asked) - {'writes', 'state'}:
        return [], [], None, 'the answer\'s fabric is not {writes, state}'
    writes = asked.get('writes', [])
    if not (isinstance(writes, list) and len(writes) <= MOST_WRITES):
        return [], [], None, f'the fabric\'s writes are not a list of at most {MOST_WRITES}'
    plain, rows = [], []
    for n, w in enumerate(writes, 1):
        if not (isinstance(w, dict) and w.get('do') == 'edit' and w.get('species') in modules):
            return [], [], None, f'fabric write {n} is not an edit of a record of a Fabric module the agent declares'
        values = w.get('values')
        if not (isinstance(values, dict) and values and all(isinstance(k, str) and member_records.CUSTOM.fullmatch(k) for k in values)):
            return [], [], None, f'fabric write {n} writes something other than custom fields'
        row = w.get('row') or {}
        if not (isinstance(row, dict) and set(row) <= {'segment', 'row_id'} and (not row or (row.get('segment') == w['species'] and isinstance(row.get('row_id'), str) and ROW_ID.fullmatch(row['row_id'])))):
            return [], [], None, f'fabric write {n} names its row wrongly'
        plain.append({k: w[k] for k in ('do', 'species', 'key', 'values') if k in w})
        rows.append(row.get('row_id', ''))
    checked, why = member_records.check(plain, {m: NEEDS for m in modules}, custom=True, most=MOST_WRITES) if plain else ([], '')   # a RUN's own limit, not a page's
    if why:
        return [], [], None, f'fabric: {why}'
    given = asked.get('state', {})
    if not (isinstance(given, dict) and set(given) <= set(TABLES)):
        return [], [], None, 'the fabric\'s state is not {files, held, slots, ids}'
    saved = {}
    for table, columns in TABLES.items():
        saved[table], why = _rows(given.get(table, []), columns, table)
        if why:
            return [], [], None, why
    return checked, rows, saved, ''


def merged(handed, saved):
    """The ids the answer names (new, or changed since the state handed) over the ids FROST handed, one per module and row
    id: an answer never carries every id back, only what changed."""
    ids = {(i.get('segment'), i.get('row_id')): i for i in handed.get('ids', [])}
    ids.update({(i['segment'], i['row_id']): i for i in saved['ids']})
    saved['ids'] = sorted(({c: i.get(c, '') for c in TABLES['ids']} for i in ids.values()), key=lambda i: (i['segment'], i['row_id']))
    return saved


def landed(saved, writes, rows, written):
    """The state with each id's record as wid answered its write: an edit wid took names its record; one it refused names
    none (the row waits for its record again)."""
    by_row = {(w['species'], r): out for w, r, out in zip(writes, rows, written) if r}
    for i in saved['ids']:
        out = by_row.get((i['segment'], i['row_id']))
        if out is not None:
            i['record_key'] = out['key'] if out['ok'] else ''
    return saved


def held_name(name):
    """The held rows file of one of the sixteen: pf_invoices.csv -> pf_invoices_held.csv (DA-M keeps it in the DATA FABRIC folder)."""
    return name[:-len('.csv')] + '_held.csv'


def with_held(saved, stored):
    """THE DOWNLOAD (the owner, 2026-10-25: "we can do it without javascript just like any download"): each file's held rows
    file this RUN stored in DA-M, by the key DA-M gave it (stored: {name: dam_key}); a file whose held rows this RUN did not
    store keeps the key the agent handed back. The agent cannot know a key DA-M has not given yet: the runtime fills it."""
    for f in saved['files']:
        key = stored.get(held_name(f['file_name']))
        if key:
            f['held_dam_key'] = key
    return saved


PAGES = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'schemas' / 'runtime.json').read_text()).get('pages', {})   # each caller's page host


def with_downloads(state, path, caller=''):
    """THE PAGE'S DOWNLOADS: each file row of the state handed to a CALL carries "download" (its official CSV) and
    "held_download" (its held rows), DA-M's own download addresses on the caller's page host ('' for none)."""
    origin = PAGES.get(caller, '') if isinstance(PAGES.get(caller, ''), str) else ''
    for f in state.get('files', []):
        f['download'] = view.download_of(path, f.get('dam_key', ''), origin)
        f['held_download'] = view.download_of(path, f.get('held_dam_key', ''), origin)
    return state


def save(post, account, scope, member, held, job_key, run, saved):
    """The state back to FROST's datafabric.db for this account, only while this RUN is open and only for the agent FROST
    approved under exactly these hashes (held: its locker row), as the provider key is asked; -> (ok, why)."""
    status, body = post('fs', STATE_DOOR, {'account': account, 'scope': scope, 'member': member, 'job_key': job_key, 'run': str(run), 'agent_key': held['agent_key'],
                                           'code_sha256': held['code_sha256'], 'manifest_sha256': held['manifest_sha256'], **saved})
    body = body if isinstance(body, dict) else {}
    return status == 200, '' if status == 200 else str(body.get('refused') or body.get('error') or f'FROST answered {status}')[:300]
