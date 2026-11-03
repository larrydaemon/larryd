"""AGENT 021 · BACKLOG (the owner 2026-10-28: "add one more for backlog on its own"; "for the backlog add a big button to clear all backlog"):
a SUB AGENT of the MARK IV agent (agent001), lower rank, in the DAY group, beside the DAY script and never inside it. THE BACKLOG IS
THIS OFFICE'S OWN (the owner 2026-10-28: "all of everything are in the new one and nothign in the original"): the requests of its own
database (its requests table, declared in instance/<office>.json). A LIST, NEVER RED FOR THE WORK: a backlog is work waiting, not a fault;
red only when its requests cannot be read (its step names it).

THE ORIGINAL'S BACKLOG · N TABLE (row 004, under TODAY'S NEW REQUESTS; the owner 2026-10-28: "look at each original agent and rebuild it so
it looks like the original agent"): every request not done and not removed that was asked before today, and every one stuck today, in build
order (position, then id); each row its Request (id · when it was asked · where the work goes), His words, Status now (WAITING, BUILDING or
VERIFY, the why, its time counting from when that status began; TEST IT in VERIFY), and its presses: REMOVE (marked removed by him, never
deleted), UPDATE (his words added under its words, back to the backlog for the next DAY run; one the DAY holds on the tree keeps its state),
APPROVE in VERIFY (done: green).

CLEAR ALL BACKLOG, ITS ONE BIG BUTTON: every WAITING request of the backlog (asked or stuck today: work not built) marked removed, its
state_at now, its why "cleared by CLEAR ALL BACKLOG", in one write; nothing is deleted. BUILDING and VERIFY ones stay (the DAY holds the
first on the tree, the second is built work waiting for his look): each has its own REMOVE. Only he presses it (the page's guard: a press
from its own page alone); it asks once before it goes."""
import datetime
import json
import os
import re
import sqlite3
import traceback
import zoneinfo

KEY = 'backlog'
SLOT = 'DAY'   # where it lives: a shell of DAY, beside the DAY script
INTERFACE = True   # an interface of its own, the BACKLOG table and its presses: drawn in the original's markup on both faces (the owner 2026-10-28)
ROW = 0   # no row of the original: the owner's own new agent (2026-10-28)
NAME = 'Backlog'
CARD_NAME = 'Scrum Master Backlog'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = 'The backlog: every request waiting to be built, in build order'
WHAT = "Lists the original's BACKLOG table with REMOVE, UPDATE and APPROVE on each request, and clears the waiting ones with one button"
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'daily', 'time': '07:00', 'timezone': 'America/New_York'}   # its count kept once a day and on RUN AGENT; its list is read fresh at every draw
ROW_FILE = 'agent021_day_backlog.py'   # its program's file: its skills index is filed under it
ZONE = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
PRESSES = ('clear', 'remove', 'update', 'approve')   # its own buttons, by name (the page's agent_press route runs press for these alone)
STATUS = (('WAITING', ('asked', 'stuck_today')), ('BUILDING', ('planned', 'building', 'proven', 'reviewed', 'approved')), ('VERIFY', ('waiting_takein',)))   # this office's states: picked (planned) and committed waiting for the walk (approved) are the DAY's hands, walked READY (waiting_takein) is his to look at
WAITING = STATUS[0][1]   # what CLEAR ALL BACKLOG clears: work not built
IN_HAND = STATUS[1][1]   # the DAY holds its change on the tree: an UPDATE keeps its state
ASKED, STUCK, READY = 'asked', 'stuck_today', 'waiting_takein'
CLOSED = ('green', 'shipped', 'taken_in')   # done: never on the work list
GONE = ('removed',)
APPROVED = 'green'   # HIS APPROVE closes it: this office's 'approved' is the DAY's own (committed, waiting for the walk), so his verdict writes green
CLEARED = 'cleared by CLEAR ALL BACKLOG'
BY_HIS_PAGE = 'on his page'
ENVIRONMENTS = (('localhost_rnd', 'localhost', 'rnd'), ('localhost_pf', 'localhost', 'pf'), ('production_rnd', 'production', 'rnd'),
                ('production_pf', 'production', 'pf'), ('agent_larryd', 'agent', 'larryd'), ('native_ios', 'native', 'ios'), ('native_macos', 'native', 'macos'))   # the original's, word for word
OFF_BY_DEFAULT = ('native_ios', 'native_macos')
HAND = 'YOUR 3 MIN: '
READ_STEP = "see why the office's requests do not read (seconds): sqlite3 ~/larryd/server/runtime/internal/instance/data/scrum_master_3/scrum_master_3.db 'SELECT id, words, state, asked_at, state_at, why, environment, position FROM requests LIMIT 1' (its own read: the error it prints is the one it met), then RUN AGENT"

PLAIN = [   # (pattern, its plain word); in this order: THE REQUESTS' own (agent011), so his UPDATE is stored as every request is kept
    (r"\bmotherfuck\w*", ''), (r"\bwhat the fuck\b", 'what'), (r"\bthe fuck\b", ''), (r"\bfuck(?:ed|ing)? up\b", 'messed up'),
    (r"\bfuck(?:ing|ign|in|en)\b", ''), (r"\bfucked\b", 'messed up'), (r"\bfuck(?:er|ers|s)?\b", ''),
    (r"\bbullshit\b", 'nonsense'), (r"\bshitty\b", 'bad'), (r"\bshit(?:s)?\b", 'junk'), (r"\bcrappy\b", 'bad'), (r"\bcrap\b", 'junk'),
    (r"\bassholes?\b", 'jerk'), (r"\bgoddamn(?:ed)?\b", ''), (r"\bdamn(?:ed|it)?\b", ''), (r"\bwtf\b", ''), (r"\bbitch(?:es|ing)?\b", ''),
]
PLAIN = [(re.compile(p, re.I), w) for p, w in PLAIN]
SWEAR = re.compile(r"\b(?:motherfuck\w*|fuck\w*|bullshit|shit\w*|crap\w*|assholes?|goddamn\w*|damn\w*|wtf|bitch\w*)\b", re.I)


def _where(fault):
    """WHERE A CRASH HAPPENED: the last frame in this agent's own file (a library's frame says nothing he can open), else the last frame"""
    frames = traceback.extract_tb(fault.__traceback__) if fault.__traceback__ else []
    own = [f for f in frames if os.path.abspath(f.filename) == os.path.abspath(__file__)]
    at = (own or frames or [None])[-1]
    return f'{os.path.basename(at.filename)} line {at.lineno}' if at else 'its own code'


def clean(text):
    """only the swear words change (THE REQUESTS' clean): a removed one leaves a mark, and only the space beside a mark is tidied"""
    if not text or not SWEAR.search(text):
        return text
    t = text
    for rx, w in PLAIN:
        t = rx.sub(lambda m, w=w: (w.upper() if w and m.group(0).isupper() and len(m.group(0)) > 1 else w) if w else '\x00', t)
    t = SWEAR.sub('\x00', t)
    t = re.sub(r"[ \t]*\x00[ \t]*(?=[,.;:!?\"')\]]|$)", '', t, flags=re.M)
    t = re.sub(r"(^|(?<=[\"'(\[]))[ \t]*\x00[ \t]*", '', t, flags=re.M)
    t = re.sub(r"[ \t]*\x00[ \t]*", ' ', t)
    return t


def _db(store):
    return store.db_path


def _now():
    return datetime.datetime.now(ZONE)


def _moment(text):
    """an ISO moment with its zone (one with no zone is New York's), or None"""
    try:
        got = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return got if got.tzinfo else got.replace(tzinfo=ZONE)


def backlog(store, now=None):
    """THE BACKLOG NOW, read fresh, the original's requests_pending 'backlog': every request not done and not removed, asked before today or
    stuck today, in build order. -> [{'id', 'words', 'state', 'asked_at', 'state_at', 'why', 'environment', 'position'}]. sqlite3.Error: they do not read."""
    now = now or _now()
    con = sqlite3.connect(f'file:{_db(store)}?mode=ro', uri=True, timeout=10)
    try:
        cols = ('id', 'words', 'state', 'asked_at', 'state_at', 'why', 'environment', 'position')
        rows = [dict(zip(cols, r)) for r in con.execute(f"SELECT {', '.join(cols)} FROM requests ORDER BY position, id")]
    finally:
        con.close()
    out = []
    for r in rows:
        if r['state'] in CLOSED + GONE:
            continue
        at_ = _moment(r['asked_at'])
        if r['state'] == STUCK or not (at_ and at_.astimezone(ZONE).date() == now.astimezone(ZONE).date()):
            out.append(r)
    return out


def waiting(store, now=None):
    """the backlog's WAITING requests (asked, stuck today): what CLEAR ALL BACKLOG clears"""
    return [r for r in backlog(store, now) if r['state'] in WAITING]


def _age(asked_at, now):
    at = _moment(asked_at)
    if at is None:
        return ''
    days = (now.date() - at.astimezone(now.tzinfo).date()).days   # calendar days in his zone: asked yesterday is 1 day, whatever the hour
    return 'today' if days <= 0 else 'yesterday' if days == 1 else f'{days} days ago'


def said_now(store, now=None):
    """What the backlog says now: {'ok', 'count', 'waiting', 'oldest', 'summary'} (ok False: its requests do not read)."""
    now = now or _now()
    try:
        rows = backlog(store, now)
    except sqlite3.Error as e:
        why = f'{type(e).__name__}: {e}'.splitlines()[0][:200]
        return {'ok': False, 'count': 0, 'waiting': 0, 'oldest': '', 'summary': f"FAILED · the requests do not read ({why}) · {HAND}{READ_STEP}"}
    if not rows:
        return {'ok': True, 'count': 0, 'waiting': 0, 'oldest': '', 'summary': 'BACKLOG · 0 · the backlog is empty'}
    oldest = min((r['asked_at'] for r in rows if r['asked_at']), default='')
    by = {}
    for r in rows:
        word = status_of(r['state'])
        by[word] = by.get(word, 0) + 1
    n_wait = by.get('WAITING', 0)
    return {'ok': True, 'count': len(rows), 'waiting': n_wait, 'oldest': oldest,
            'summary': f"BACKLOG · {len(rows)} · " + ', '.join(f'{n} {w.lower()}' for w, n in sorted(by.items(), key=lambda kv: (-kv[1], kv[0]))) + f" · the oldest asked {_age(oldest, now)}"}


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (daily 07:00 or RUN AGENT): the backlog counted, its run written; DONE exit 0, or FAILED exit 1 when its requests do not read
    (READ_STEP), or when its own code crashes, named as a crash with its file and line (its blind rule read 2026-10-28: a crash that is no
    sqlite3.Error wrote no run, so its last DONE stayed green)."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        got = said_now(store, now)
    except Exception as fault:   # A CRASH IS RED, NAMED AS ONE, as THE REQUESTS (agent011 once): never no run, never said as the requests not reading
        where = _where(fault)
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        why, step = f'it crashed at {where} ({line})', f'open {where}, fix what the crash names, then RUN AGENT'
        got = {'ok': False, 'count': 0, 'waiting': 0, 'oldest': '', 'why': why, 'step': step, 'summary': f'FAILED · {why} · {HAND}{step}'}
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0 if got['ok'] else 1, json.dumps(got), 'DONE' if got['ok'] else 'FAILED')
    return got


def status_of(state):
    return next((word for word, states in STATUS if state in states), '')


def environment_line(r):
    """one request's places in a few words, as the original's: localhost rnd · pf · production rnd · pf · agent larryd"""
    try:
        got = json.loads(r.get('environment') or 'null')
    except (TypeError, ValueError):
        got = None
    keys = [k for k, _e, _s in ENVIRONMENTS]
    keep = [k for k in keys if k not in OFF_BY_DEFAULT] if not isinstance(got, list) else [k for k in keys if k in got]
    parts = []
    for place in dict.fromkeys(e for _k, e, _s in ENVIRONMENTS):
        sides = [side for k, e, side in ENVIRONMENTS if e == place and k in keep]
        if sides:
            parts.append(f"{place} {' · '.join(sides)}")
    return ' · '.join(parts) or 'none'


def test_url(words):
    """THE LINK TO TEST IT, as the original's: the newest page address in his words that is not production A, or ''"""
    found = [u.rstrip('.,;)') for u in re.findall(r'https?://[^\s<>"\']+', str(words or ''))]
    found = [u for u in found if not re.match(r'https?://(?:www\.)?positivefeedback\.(?:ai|com)(?:[/?#]|$)', u)]
    return found[-1] if found else ''


def request_row(r):
    """ONE REQUEST AS THE ORIGINAL'S BACKLOG ROW: Request (id · when asked · where the work goes), His words, Status now (his status, the why,
    its time counting from when it began), its presses (REMOVE, UPDATE with his words, APPROVE in VERIFY) and TEST IT on its copy line."""
    at_ = _moment(r['asked_at'])
    word = status_of(r['state']) or str(r['state'] or '').upper().replace('_', ' ')
    since = _moment(r['asked_at'] if word == 'WAITING' else r['state_at']) or at_
    why = ' '.join(str(r['why'] or '').split())
    status = {'word': word, 'text': why[:240], 'label': f'{word} TIME:', **({'since': since.isoformat()} if since else {})}   # the original's status cell: its word, its why, its time
    row = {'key': r['id'], 'cells': [{'text': f"{r['id']} · {at_.astimezone(ZONE).strftime('%Y-%m-%d %H:%M') if at_ else ''}", 'note': environment_line(r)}, {'text': str(r['words'] or '').strip(), 'mono': True}, status],
           'presses': [{'do': 'remove', 'label': 'REMOVE', 'cell': 0, 'confirm': f"Remove {r['id']}? It is marked removed by you; its words and history stay."},
                       {'do': 'update', 'label': 'UPDATE', 'cell': 1, 'text': True, 'placeholder': 'update: what you looked for and did not see'}]}
    if word == 'VERIFY':
        url = test_url(r['words'])
        row['copy'] = f'TEST IT: {url}' if url else 'TEST IT: no page named in the request: put its address in an UPDATE'
        row['presses'].append({'do': 'approve', 'label': 'APPROVE', 'cell': 2})
    return row


def _one_request(con, rid):
    got = con.execute('SELECT id, state, state_at FROM requests WHERE id = ?', (rid,)).fetchone()
    return dict(zip(('id', 'state', 'state_at'), got)) if got else None


def remove_request(db, rid, now=None):
    """REMOVE (the original's remove_request): its state removed, its why says he removed it on his page, when, and what it was; never a delete"""
    rid, now = str(rid or '').strip(), now or _now()
    if not re.fullmatch(r'R-\d{4,}', rid):
        return f'REMOVE refused · {rid or "nothing"} is not a request id'
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            r = _one_request(con, rid)
            if not r:
                return f'REMOVE refused · {rid}: no such request'
            if r['state'] in CLOSED + GONE:
                return f"REMOVE refused · {rid} is {r['state'].replace('_', ' ')} already: nothing to remove"
            since = str(r['state_at'] or '')[:16].replace('T', ' ')
            why = (f"REMOVED BY THE OWNER {BY_HIS_PAGE} {now.strftime('%Y-%m-%d %H:%M')}: no longer wanted; it was {r['state'].replace('_', ' ')}"
                   + (f' since {since}' if since else '') + '; its words, commits and history stay')
            con.execute('UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state = ?', ('removed', now.isoformat(timespec='seconds'), why[:500], rid, r['state']))
    finally:
        con.close()
    return f'REMOVED · {rid} · marked removed by you, never deleted'


def update_request(db, rid, words, now=None):
    """HIS UPDATE (the original's update_request): his words added under the request's as "UPDATE <moment>: <words>", and it goes back to the
    backlog (asked) for the next DAY run; one the DAY holds on the tree keeps its state, his words kept under it"""
    rid, now = str(rid or '').strip(), now or _now()
    words = clean(str(words or '').replace('\r\n', '\n').replace('\r', '\n'))
    if not re.fullmatch(r'R-\d{4,}', rid):
        return f'UPDATE refused · {rid or "nothing"} is not a request id'
    if not words.strip():
        return f'UPDATE refused · {rid}: an update needs your words'
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            r = _one_request(con, rid)
            if not r:
                return f'UPDATE refused · {rid}: no such request'
            if r['state'] in GONE:
                return f'UPDATE refused · {rid} was removed by you: removed is final, add it again as a new request'
            moment = now.strftime('%Y-%m-%d %H:%M')
            con.execute('UPDATE requests SET words = words || ? WHERE id = ? AND state IS NOT ?', (f'\n\nUPDATE {moment}: {words.strip()}', rid, 'removed'))
            if r['state'] in IN_HAND:
                return f"UPDATED · {rid} · your words kept under its words; it stays {r['state']}: the DAY holds its change on the tree now"
            con.execute('UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state = ?',
                        (ASKED, now.isoformat(timespec='seconds'), f'UPDATED BY THE OWNER {BY_HIS_PAGE} {moment}: back in the backlog, built again with his update by the next DAY run', rid, r['state']))
    finally:
        con.close()
    return f'UPDATED · {rid} · your words kept under its words; back in the backlog for the next DAY run'


def approve_request(db, rid, now=None):
    """HIS APPROVE IN VERIFY (the original's verdict_request, approve): a request walked READY is done (green), its why says he approved it"""
    rid, now = str(rid or '').strip(), now or _now()
    if not re.fullmatch(r'R-\d{4,}', rid):
        return f'APPROVE refused · {rid or "nothing"} is not a request id'
    con = sqlite3.connect(db, timeout=10)
    try:
        with con:
            r = _one_request(con, rid)
            if not r:
                return f'APPROVE refused · {rid}: no such request'
            if r['state'] != READY:
                return f"APPROVE refused · {rid} is {str(r['state']).replace('_', ' ')}, not in VERIFY: nothing to approve"
            con.execute('UPDATE requests SET state = ?, state_at = ?, why = ?, done_at = COALESCE(done_at, ?) WHERE id = ? AND state = ?',
                        (APPROVED, now.isoformat(timespec='seconds'), f"APPROVED BY THE OWNER {BY_HIS_PAGE} {now.strftime('%Y-%m-%d %H:%M')}: done", now.isoformat(timespec='seconds'), rid, READY))
    finally:
        con.close()
    return f'APPROVED · {rid} · done'


def clear_all(store, now=None):
    """CLEAR ALL BACKLOG: every WAITING request of the backlog marked removed with its why, in one write; nothing deleted"""
    now = now or _now()
    ids = [r['id'] for r in waiting(store, now)]
    con = sqlite3.connect(_db(store), timeout=10)
    try:
        with con:
            n = sum(con.execute(f"UPDATE requests SET state = 'removed', state_at = ?, why = ? WHERE id = ? AND state IN ({','.join('?' * len(WAITING))})",
                                (now.isoformat(timespec='seconds'), CLEARED, rid, *WAITING)).rowcount for rid in ids)
    finally:
        con.close()
    return f'CLEAR ALL BACKLOG · {n} request{"" if n == 1 else "s"} marked removed, none deleted'


def press(store, job_key, do, fields=None, now=None):
    """ITS BUTTONS: clear (CLEAR ALL BACKLOG), remove, update (words), approve (each the request's id as value). -> the words said on its shell"""
    if do not in PRESSES:
        raise ValueError(f'not one of its presses: {do!r}')
    fields = fields or {}
    one = lambda k: (fields.get(k) or [''])[0] if isinstance(fields.get(k), list) else (fields.get(k) or '')   # noqa: E731
    try:
        if do == 'clear':
            return clear_all(store, now)
        if do == 'remove':
            return remove_request(_db(store), one('value'), now)
        if do == 'update':
            return update_request(_db(store), one('value'), one('words'), now)
        return approve_request(_db(store), one('value'), now)
    except sqlite3.Error as e:
        return f"{do.upper()} not written · the requests do not write ({type(e).__name__}) · {HAND}{READ_STEP}"


def latest(store, job_key):
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except (TypeError, ValueError):
            return None
    return None


def until_next(now=None, schedule=None):
    """Seconds to its next daily run (07:00 New York)."""
    schedule = schedule or SCHEDULE
    zone = zoneinfo.ZoneInfo(schedule['timezone'])
    now = now or datetime.datetime.now(zone)
    h, m = (int(x) for x in schedule['time'].split(':'))
    nxt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if nxt <= now:
        nxt += datetime.timedelta(days=1)
    return (nxt - now).total_seconds()


def clock(schedule=None):
    """Its clock in its shell: NEW YORK · 7:00 AM · DAILY."""
    schedule = schedule or SCHEDULE
    h, m = (int(x) for x in schedule['time'].split(':'))
    when = datetime.time(h, m).strftime('%I:%M %p').lstrip('0')
    return {'zone': schedule['location'], 'at': schedule['time'], 'said': f"{when} · {schedule['schedule_type'].upper()}", 'when': when,
            'repeat': schedule['schedule_type'].upper(), 'hour_deg': (h % 12) * 30 + m * 0.5, 'minute_deg': m * 6}


def content(store, job_key, block=None):
    """ITS CONTENT ON THE ONE CANVAS, words never markup (web/page.py content_view): the original's BACKLOG · N table read fresh, each request
    with REMOVE, UPDATE and APPROVE in VERIFY, then the big CLEAR ALL BACKLOG button for its waiting ones (none waiting: no button)."""
    try:
        rows = backlog(store)
    except sqlite3.Error as e:
        return [{'kind': 'note', 'title': 'BACKLOG', 'text': f"the requests cannot be read ({type(e).__name__}) · {HAND}{READ_STEP}"}]
    table = {'kind': 'table', 'title': f'BACKLOG · {len(rows)}', 'columns': ['Request', 'His words', 'Status now'],
             'rows': [request_row(r) for r in rows], 'empty': 'no older request pending'}
    n = sum(1 for r in rows if r['state'] in WAITING)
    if not n:
        return [table]
    return [table, {'kind': 'press', 'label': f'Clear all backlog ({n})', 'do': 'clear',
                    'confirm': f"Clear all {n} waiting requests from the backlog? Each is marked removed and kept, never deleted. BUILDING and VERIFY ones stay."}]
