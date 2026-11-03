"""THE WORK LIST, NOW THE REQUESTS' READER (the owner's spec 2026-10-21, BUILD ITEMS A AND B): NOTHING HAPPENS WITHOUT A.
The work is only what Christensen asked for: requests (A) and the build items under them (B), in his database through
the one door (shared_store). Nothing here makes work: no red row, no Judge or smoke failure, no finding ever becomes an
item here. The rows of B THE SPRINT and C THE BUILD WORK read the requests through this file, and the round runs the
report scrub from here (R4: housekeeping inside the round, in no row).

    requests_panel(st)   every request in build order, his words (an order's: its id and state only, R6), state, since
                         when, its B items under it; and the day's heard list, "heard, not recorded"
    board(st)            the same requests, each with its B items and its turns, for the rows
    counts(st)           green / total, and how many are open
    idle(st)             THE IDLE ALARM's fact: an asked-for request unfinished and no build, test or commit for 30 min
    scrub(...)           THE REPORT SCRUB (moved here from the old row 010 NEW FILES, R4): one call from the round
    seen(), judged(), smoke_report(), speed_fact()   readers of the platform's own report files, kept for the Developer
"""
import datetime
import fnmatch
import json
import os
import re
import stat
import subprocess

from agent import shared_where as where
from agent import shared_store as store
from agent import shared_schedule as schedule   # the clock


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


PASS, FAIL = 'PASS', 'FAIL'   # the lie detector's own verdict words, as its report.json writes them


def seen():
    """THE LIE DETECTOR'S OWN REPORT (settings reads lie_detector; its deadman from console.json cebf): {'report': {at,
    verdict, rows: [{id, says, verdict, detail}]} or None, 'age': seconds, 'silent': older than its deadman (or dated
    ahead of the clock), 'deadman'}"""
    report = _json(where.path('lie_detector'))
    report = report if isinstance(report, dict) and isinstance(report.get('rows'), list) else None
    deadman = int(((_json(where.path('console_json')) or {}).get('cebf') or {}).get('deadman') or 900)
    age = None
    if report:
        try:
            at = datetime.datetime.fromisoformat(report['at'])
            age = int((datetime.datetime.now(datetime.timezone.utc) - (at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc))).total_seconds())
        except (ValueError, KeyError, TypeError):
            report = None
    return {'report': report, 'age': age, 'silent': report is not None and (age > deadman or age < -60), 'deadman': deadman}   # -60: a minute ahead of this laptop's clock is the writer's own clock rounding to the minute; more is a report from the future, not current


def judged(commit):
    """THE JUDGE's verdict on a commit as a night's build left it on this laptop (preflight_<commit>.json beside each
    laptop target's tree, settings reads preflight_*): the newest of them, or None"""
    found = [x for x in (_json(where.path(k, f'preflight_{commit}.json')) for k in ('preflight_pf', 'preflight_scratch')) if isinstance(x, dict)]
    return max(found, key=lambda m: str(m.get('made_at', ''))) if found else None


def smoke_report():
    """THE SMOKE TEST'S NEWEST REPORT, as it wrote it (reports.json smoke), or None"""
    got = _json(where.report('smoke'))
    return got if isinstance(got, dict) else None


BROKE = 'no check of its own here: the speed row broke before it measured anything'   # nobody is hired while it measures nothing (back() leaves it), never a person's either


def speed_fact(i):
    """What a speed row's item says while no cure is found: the row broke and measured nothing (its own words), or the
    platform has no cure yet (the row's own numbers)."""
    said = ' '.join(str(i.get('evidence', '')).split())
    if said.startswith('THE ROW BROKE'):
        return f'{BROKE}: {said[:220]}; it is worked again when the row measures'
    return f'no platform cure found yet: its row says {said[:200]}'



# ---------------------------------------------------------------- THE REQUESTS (A) AND THEIR BUILD ITEMS (B)
DONE = ('green', 'shipped')   # a request finished: the nightly is green with it in (shipped: on B rnd too)
OPEN = ('asked', 'planned', 'building', 'proven', 'reviewed', 'waiting_takein', 'approved', 'taken_in', 'stuck_today')   # still being worked (approved: by the owner on his page, waits for the take-in)
STATUS = (('WAITING', ('asked', 'planned', 'stuck_today')), ('BUILDING', ('building', 'proven', 'reviewed')), ('VERIFY', ('waiting_takein',)), ('APPROVED', ('approved',)))   # HIS STATUSES (the owner 2026-10-24: "3 status here: waiting - time, building - time, verify - time approve or reject with a button to approve"); APPROVED waits for the take-in
GONE = ('removed',)   # REMOVED BY THE OWNER on his page (2026-10-24): closed by his hand, never built
CLOSED = DONE + GONE   # the closed list of row 004 (the owner 2026-10-24: "split the closed and incomplete list so we have two lists")
ORDER = 'order'   # a request of source order: its words are an order's (R6), shown by its id and state only
IDLE_MINUTES = int(((where.SETTINGS.get('sprint') or {}).get('no_loops') or {}).get('idle_minutes') or 30)   # settings sprint.no_loops.idle_minutes
HOTFIX_TREE = os.path.expanduser('~/spine_worktrees/hotfix')   # the Developer's hot fix tree: its newest commit is a build's sign of life
SPRINT_END = '2026-12-13'   # the swap from A to B (settings scrum.release)


def _st(st=None):
    return st or store.door()


def shown(r):
    """A request's words as the page may show them: an order's are never shown (R6: its id and state only)."""
    return '' if r.get('source') == ORDER else str(r.get('words') or '')


def since(at):
    """A moment as the page says it: today's by its clock, an earlier day's by its date and clock (local time, R3)."""
    try:
        return schedule._when(at)
    except Exception:   # noqa: BLE001  (never a made up time)
        return str(at or '')


def board(st=None):
    """EVERY REQUEST, in build order (position), each with its B items (oldest first) and its turns. -> [dict]"""
    st = _st(st)
    items = {}
    for b in st.build_items():
        items.setdefault(b['request_id'], []).append(b)
    out = []
    for r in sorted(st.requests(), key=lambda r: (int(r.get('position') or 0), r['id'])):
        out.append({**r, 'shown': shown(r), 'items': items.get(r['id'], []), 'turns': st.build_turns(item_id=r['id'])})
    return out


LOADED = ('order', 'sprint')   # requests loaded from his orders and sprint files: recorded when loaded, asked before that


def cycle_clock(sec):
    """A count of seconds as the cycle clock shows it (web/page.took's form): 0d 04:22:23."""
    sec = max(0, int(sec))
    return f"{sec // 86400}d {sec % 86400 // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def cycle(r, now=None):
    """A REQUEST'S CYCLE TIME (the owner 2026-10-24: "add a cycle time after each one so we know how long it took to build /
    if you dont know the past info make a guess and populate it"): from asked_at to done_at (green, shipped), to its
    removal (removed), or to now (still open, running). A moment the record does not hold is guessed and marked ~: a
    done request without done_at ends at its state_at; a request loaded from his orders or sprint file starts at the
    moment it was loaded. -> {'cycle': words, 'cycle_seconds': n or None, 'cycle_guessed': bool}"""
    start, state, guessed = _moment(r.get('asked_at')), r.get('state'), r.get('source') in LOADED
    if state in DONE:
        end = _moment(r.get('done_at'))
        if end is None:
            end, guessed = _moment(r.get('state_at')), True
        word = 'took'
    elif state in GONE:
        end, word = _moment(r.get('state_at')), 'removed after'
    else:
        end, word = now or datetime.datetime.now().astimezone(), 'running'
    if start is None or end is None:
        return {'cycle': '', 'cycle_seconds': None, 'cycle_guessed': False}
    sec = max(0, int((end - start).total_seconds()))
    return {'cycle': f"{'~' if guessed else ''}{word} {cycle_clock(sec)}", 'cycle_seconds': sec, 'cycle_guessed': guessed}


def requests_panel(st=None, day=None):
    """ROW 005's PANEL: every request (id, his words or for an order only its id, state, since when) and its B items
    under it; then the day's heard list, minus what was recorded as a request (heard, not recorded)."""
    st = _st(st)
    reqs = [{'id': r['id'], 'words': r['shown'], 'source': r.get('source'), 'ref': r.get('ref'), 'state': r.get('state'), 'state_at': r.get('state_at'),
             'since': since(r.get('state_at')), 'why': r.get('why') or '', **cycle(r),
             'items': [{'id': b['id'], 'found_by': b.get('found_by'), 'rule': b.get('rule'), 'state': b.get('state'), 'state_at': b.get('state_at')} for b in r['items']]}
            for r in board(st)]
    return {'requests': reqs, 'incomplete': [q for q in reqs if q['state'] not in CLOSED], 'closed': [q for q in reqs if q['state'] in CLOSED], 'heard': heard_not_recorded(st, day)}   # TWO LISTS (the owner 2026-10-24): the incomplete first, then the closed (green, shipped, removed), each in build order


def heard_not_recorded(st=None, day=None):
    """THE DAY'S HEARD LIST (shared_requests.heard: what a session heard, never a request), minus every line whose words
    a request holds. -> [{words, asked_at, session}]"""
    from agent import shared_requests as requests
    st = _st(st)
    asked = {str(r.get('words') or '').strip() for r in st.requests()}
    return [{'words': h.get('words'), 'asked_at': h.get('asked_at'), 'session': h.get('session')}
            for h in requests.heard(st, day) if str(h.get('words') or '').strip() not in asked]


def counts(st=None):
    """{'total', 'green', 'open', 'stuck', 'building'} over every request."""
    reqs = _st(st).requests()
    return {'total': len(reqs), 'green': sum(1 for r in reqs if r.get('state') in DONE), 'open': sum(1 for r in reqs if r.get('state') in OPEN),
            'stuck': sum(1 for r in reqs if r.get('state') == 'stuck_today'), 'building': sum(1 for r in reqs if r.get('state') == 'building')}


def _moment(text):
    try:
        got = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return got if got.tzinfo else got.replace(tzinfo=schedule.ZONE)


def last_commit(tree=None):
    """The newest commit's moment on the hot fix tree (git), or None when git does not say."""
    try:
        got = subprocess.run(['git', '-C', tree or HOTFIX_TREE, 'log', '-1', '--format=%cI'], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return _moment(got.stdout.strip()) if got.returncode == 0 else None


def last_work(st=None, tree=None):
    """THE NEWEST SIGN OF BUILD WORK: a turn (build_turns), a request's or a B item's state moved by the work (not 'asked',
    not 'open': those are intake), or a commit on the hot fix tree. -> (moment or None, what)"""
    st = _st(st)
    signs = [(_moment(t.get('at')), f"turn {t.get('turn')} on {t.get('item_id')}") for t in st.build_turns()]
    signs += [(_moment(r.get('state_at')), f"{r['id']} {r.get('state')}") for r in st.requests() if r.get('state') not in ('asked',)]
    signs += [(_moment(b.get('state_at')), f"{b['id']} {b.get('state')}") for b in st.build_items() if b.get('state') not in ('open',)]
    signs.append((last_commit(tree), 'a commit on the hot fix tree'))
    signs = [s for s in signs if s[0] is not None]
    return max(signs, key=lambda s: s[0]) if signs else (None, '')


def idle(st=None, now=None, minutes=None, tree=None):
    """THE IDLE ALARM (the owner 2026-10-21): an asked-for request unfinished (not green, shipped or stuck today) and no
    build, test or commit for `minutes` (settings sprint.no_loops.idle_minutes, 30). Asked for nothing is never idle.
    -> (idle: bool, waiting: n, the newest work's moment or None, what it was)"""
    st = _st(st)
    minutes = IDLE_MINUTES if minutes is None else minutes
    waiting = [r for r in st.requests() if r.get('state') in OPEN and r.get('state') != 'stuck_today']
    if not waiting:
        return False, 0, None, ''
    at, what = last_work(st, tree)
    moment = schedule._now(now)
    quiet = at is None or (moment - at).total_seconds() > minutes * 60
    return quiet, len(waiting), at, what


def pace(st=None, now=None, end=SPRINT_END):
    """PACE: requests green per day so far (since the first request was asked) vs what the swap day needs for the rest.
    -> {'green', 'total', 'left', 'days_gone', 'days_left', 'per_day', 'needed', 'on_pace'}"""
    st = _st(st)
    reqs = st.requests()
    moment = schedule._now(now)
    first = min((_moment(r.get('asked_at')) for r in reqs if _moment(r.get('asked_at'))), default=None)
    green = sum(1 for r in reqs if r.get('state') in DONE)
    left = len(reqs) - green
    days_gone = max(1.0, (moment - first).total_seconds() / 86400) if first else 0.0
    days_left = max(0.0, (datetime.datetime.fromisoformat(end).replace(tzinfo=schedule.ZONE) - moment).total_seconds() / 86400)
    per_day = green / days_gone if days_gone else 0.0
    needed = (left / days_left) if days_left else float(left)
    return {'green': green, 'total': len(reqs), 'left': left, 'days_gone': round(days_gone, 1), 'days_left': round(days_left, 1),
            'per_day': round(per_day, 2), 'needed': round(needed, 2), 'on_pace': left == 0 or per_day >= needed}


def cut(text, most):
    """TEXT SHORTENED AT A WORD, NEVER INSIDE ONE (the owner 2026-10-21): whole when it fits, else up to the last whole
    word within most, with an ellipsis."""
    text = ' '.join(str(text or '').split())
    if len(text) <= most:
        return text
    head = text[:most + 1].rsplit(' ', 1)[0].rstrip(' ,;:.')
    return (head or text[:most]) + '...'


def one(r):
    """A request in one short line: its id, its words (an order's: none), its state since when, its why."""
    words = shown(r)
    return (f"{r['id']}" + (f' "{cut(words, 80)}"' if words else f" ({r.get('ref') or r.get('source')})") + f" {r.get('state')} since {since(r.get('state_at'))}"
            + (f": {r['why']}" if r.get('why') else ''))


def unreadable(e):
    """R1: a table that cannot be read is not measured: said first, red, never work."""
    return 'red', f'not measured: the requests cannot be read ({type(e).__name__}: {e})'


# ---------------------------------------------------------------- THE TURNS' LOOP RULE (rows 6 and 8 share it; rows never import rows)
UNDONE = ('undone', 'put back', 'changed nothing', 'refused')   # a turn that left nothing of its work: its result says so


def undone(result):
    """a turn that left nothing of its work (its result says so)"""
    return any(w in str(result or '').lower() for w in UNDONE)


def reason(result):
    """a turn's reason, the part of its result that names why (said the same way turn after turn)"""
    return str(result or '').split(':', 1)[0].strip()


def in_order(turns):
    """turns oldest first: by their moment, then approach, then turn"""
    return sorted(turns, key=lambda t: (str(t.get('at') or ''), int(t.get('approach') or 0), int(t.get('turn') or 0)))


def same_undone(turns):
    """THE LOOP COUNT: how many of the newest turns in a row were undone for the newest turn's reason. -> (n, reason)
    (0, '') when the newest turn was kept or there is none"""
    turns = in_order(turns)
    if not turns or not undone(turns[-1].get('result')):
        return 0, ''
    why = reason(turns[-1].get('result'))
    n = 0
    for t in reversed(turns):
        if not (undone(t.get('result')) and reason(t.get('result')) == why):
            break
        n += 1
    return n, why


LOOP = 2   # the same reason undid 2 or more turns in a row: a loop (a new approach will not help: the rule in the way)


# ---------------------------------------------------------------- THE STATE LOG (shared_store.state_said: one line per state change)

def state_log(path=None):
    """EVERY STATE CHANGE OF A REQUEST as the log holds it, in file order (a line that does not read is passed over).
    -> [{at, id, state, why, by, from?}] (at may be None: its time was not recorded)"""
    path = path or os.path.join(store.LOGS, *store.STATES_LOG)
    out = []
    try:
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                try:
                    got = json.loads(line)
                except ValueError:
                    continue
                if isinstance(got, dict) and got.get('id'):
                    out.append(got)
    except OSError:
        return []
    return out


def status_of(state):
    """His status for a request's state (STATUS): WAITING, BUILDING, VERIFY, APPROVED; '' for a closed or unknown one."""
    for word, states in STATUS:
        if state in states:
            return word
    return ''


def status_since(rid, state, state_at=None, asked_at=None, log=None):
    """THE MOMENT THE REQUEST'S STATUS BEGAN (the owner 2026-10-24: a time per status): the first line of the latest
    stretch of the same status in the state log (shared_store.state_said); without one, asked_at for WAITING, else
    state_at. log: the log's lines (state_log), read once by the caller for many requests."""
    want, since = status_of(state), None
    for line in (state_log() if log is None else log):
        if line.get('id') != rid:
            continue
        if status_of(line.get('state')) == want:
            since = since or line.get('at')
        else:
            since = None
    return since or (asked_at if want == 'WAITING' else state_at) or asked_at or ''


def moment(text):
    """an ISO moment as a datetime in his zone's sense (a naive one read as his zone), or None"""
    return _moment(text) if text else None


def clock(at, now=None):
    """a log line's moment as the page says it (R3, local): today's (since the day's start) by its clock alone, an
    earlier one by its date and clock; "time not recorded" when its time was not kept"""
    got = moment(at)
    if not got:
        return 'time not recorded'
    return got.astimezone(schedule.ZONE).strftime('%H:%M') if got >= day_start(now) else since(at)


def day_start(now=None):
    """the day's start (settings scrum.reset, 07:00, in his zone) of the day `now` belongs to"""
    return schedule.began(schedule.cycle(now))


def tilde(path):
    """a path as the page says it: ~ for his home"""
    home = os.path.expanduser('~')
    path = str(path or '')
    return '~' + path[len(home):] if path == home or path.startswith(home + os.sep) else path


def freeze():
    """THE FREEZE as row 003 tells it (settings scrum.release, the release day's start in his zone, minus
    scrum.freeze_weeks weeks). -> a moment; raises ValueError when it cannot be told"""
    conf = schedule.CONF
    release = datetime.datetime.fromisoformat(str(conf['release'])).replace(tzinfo=schedule.ZONE)
    weeks = int(conf.get('freeze_weeks') or 0)
    if weeks <= 0:
        raise ValueError(f"no freeze weeks are set: {conf.get('freeze_weeks')!r} (settings scrum.freeze_weeks)")
    return release - datetime.timedelta(weeks=weeks)


NIGHTLY = re.compile(r'the nightly (\S+) built ([0-9a-fA-F]{7,64}) with its commits ([0-9a-fA-F, ]+)')   # shared_requests.nightly_green's why


def nightly_of(why):
    """THE NIGHTLY THAT MADE A REQUEST GREEN, from its why. -> {'run', 'built', 'commits': [..]} or None"""
    got = NIGHTLY.search(str(why or ''))
    if not got:
        return None
    return {'run': got.group(1), 'built': got.group(2), 'commits': [c for c in re.split(r'[, ]+', got.group(3)) if c]}


ORDERS_ROW = 10   # YOUR ORDERS: each order counted by a machine every round


def order_count(st, ref, row=ORDERS_ROW):
    """AN ORDER'S NEWEST COUNT, as row 011's newest ended run says it ("O-1 holds: 0 files in ~/virtual_workspace
    · counted 23:23, next about 23:38", or "O-1 NOT DONE in ...: 3 file(s) still hold it"). -> {'count', 'scope', 'counted',
    'started'} or None when row 011 has no count of it"""
    runs = [r for r in st.runs(row=row) if r.get('state') in ('green', 'red') and r.get('ended')]
    if not runs:
        return None
    text = str(runs[-1].get('text') or '')
    got = re.search(re.escape(str(ref)) + r' NOT DONE in (\S+): (\d+) file', text)
    holds = re.search(re.escape(str(ref)) + r' holds: (\d+) files? in (\S+)', text)
    if holds:
        got = {1: holds.group(2), 2: holds.group(1)}
    elif got:
        got = {1: got.group(1), 2: got.group(2)}
    else:
        return None
    when = re.search(r'counted (\d{1,2}:\d{2}(?: New York time)?)', text)
    return {'count': int(got[2]), 'scope': got[1].rstrip(':'), 'counted': when.group(1) if when else 'at a time it does not say',
            'started': runs[-1].get('started')}


def no_count_why(st, ref, row=ORDERS_ROW):
    """WHY THERE IS NO COUNT (row 006, 2026-10-23 22:31 and 22:47: a one-round "no count of it yet" while row 010 was
    counting, its cause unread): what row 010's newest ended run said, so the red explains itself. -> words"""
    runs = [r for r in st.runs(row=row) if r.get('state') in ('green', 'red') and r.get('ended')]
    if not runs:
        return 'no ended run of it'
    r = runs[-1]
    return f"its newest run ({schedule._clock(r.get('started'))}, {r.get('state')}) says: {str(r.get('text') or '')[:90]}"


# ---------------------------------------------------------------- THE REPORT SCRUB (moved from the old row 010 NEW FILES, R4: the round runs it)
SCRUB_ROW = 1   # the round's own row: each deletion one finding of row 001, place scrub
# (the owner 2026-10-21: a report manifest)
# Every round he scrubs THE REPORT FOLDERS: the parent folders of the reports schemas/reports.json lists, derived from that
# file alone (a pattern entry's folder part matched component by component, through no link). In each report folder:
#   a file not in reports.json: deleted, one line on the page (what, when)
#   a program, a script, an executable, a link or a hidden file: deleted (a link is unlinked, its target never touched), red
#   a listed report older than its max_age: kept, red "the writer stopped"; a listed report missing: red "not written"
# ITS BOUNDS: it deletes only inside a report folder, never above it; never in ~/virtual_sanity, ~/virtual_workspace, an
# instance folder or the office (a report folder inside or above one of them is refused, and said); a folder reached
# through a link is refused; a folder he cannot write is skipped and said. SUBFOLDERS: a subfolder of a report folder is
# never entered and never deleted unless it is itself a report folder (a dated folder of logs is one only through a
# pattern entry, e.g. daily/*/*.log); a hidden subfolder is not entered either, and is red (a person removes it).
# A CHECK'S OWN RUN (an instance that is not the office's own) never deletes a real file: without its own reports.json
# ($SCRUM_MASTER_REPORTS) the scrub only looks (a dry run), so no check can touch a real report folder.
SCRUB = 'scrub'   # the findings' place of a deletion: file = what, line = when (epoch seconds), severity = one line of JSON {why, at}, closed
GLOB = '*?['
MAGIC = (b'#!', b'\x7fELF', b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'MZ')   # a script, ELF, Mach-O (both ends, fat), a Windows program
RED_WHY = ('a link', 'a hidden file', 'a program', 'not a file')


def _globbed(part):
    return any(c in part for c in GLOB)


def _entries():
    """reports.json's entries, each with its path filled in (his logs folder) and expanded."""
    return [{**r, 'path': where.REPORTS[r['name']]} for r in where.REPORTS_BOOK['reports']]


def _expand(pattern):
    """The existing folders a folder pattern names, a glob part matched against real folders only (never a link, never a
    hidden one). -> ([folders], [why one was refused])"""
    parts = os.path.abspath(pattern).split(os.sep)
    at = next((i for i, p in enumerate(parts) if _globbed(p)), len(parts))
    probe = os.sep
    for part in parts[1:at]:   # the fixed part: every step a real folder, never a link
        probe = os.path.join(probe, part)
        try:
            st = os.lstat(probe)
        except OSError:
            return [], []
        if stat.S_ISLNK(st.st_mode):
            return [], [f'a link stands on the way to a report folder, never followed: {probe}']
        if not stat.S_ISDIR(st.st_mode):
            return [], []
    found = [probe]
    for part in parts[at:]:
        step = []
        for f in found:
            try:
                with os.scandir(f) as it:
                    step += sorted(os.path.join(f, e.name) for e in it if e.is_dir(follow_symlinks=False) and not e.name.startswith('.') and fnmatch.fnmatchcase(e.name, part))
            except OSError:
                continue
        found = step
    return found, []


def _forbidden(folder):
    """A folder the scrub never works in: one reached through a link, the top or the home, or one inside or above
    ~/virtual_sanity, ~/virtual_workspace, an instance folder or his office."""
    real = os.path.realpath(folder)
    if real != os.path.abspath(folder) or real in (os.sep, os.path.realpath(os.path.expanduser('~'))):
        return True
    for top in (where.path('sanity'), where.WORKSPACE, where.OFFICE, where.INSTANCE, store.INSTANCE, store.instance()):
        t = os.path.realpath(os.path.expanduser(top))
        if real == t or real.startswith(t + os.sep) or t.startswith(real + os.sep):
            return True
    return False


def report_folders(entries=None):
    """THE REPORT FOLDERS, from reports.json alone. -> ({folder: [its entries]}, [why a folder was refused])"""
    folders, refused = {}, []
    for e in entries or _entries():
        got, why = _expand(os.path.dirname(e['path']))
        refused += why
        for f in got:
            if _forbidden(f):
                refused.append(f'not a folder he may scrub: {f}')
            else:
                folders.setdefault(f, []).append(e)
    return folders, sorted(set(refused))


def _program(name, st, fd):
    """a program, a script or an executable: its kind (settings watch_programs), an executable bit, or its first bytes."""
    if os.path.splitext(re.sub(r'\.\d+$', '', name))[1].lower() in {k.lower() for k in schedule.CONF['watch_programs']} or st.st_mode & 0o111:
        return True
    try:
        f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except OSError:
        return False
    try:
        return stat.S_ISREG(os.fstat(f).st_mode) and os.read(f, 4).startswith(MAGIC)
    except OSError:
        return False
    finally:
        os.close(f)


def _scrub_folder(folder, entries, dry):
    """One report folder, held open by its descriptor (every step by name against it, never through a link).
    -> ([(path, why)] taken (or, dry, to be taken), [what he could not do or would not enter])"""
    taken, said = [], []
    if not os.access(folder, os.W_OK):
        return taken, [f'a report folder he cannot write, not scrubbed: {folder}']
    try:
        fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as e:
        return taken, [f'a report folder he could not open ({type(e).__name__}): {folder}']
    try:
        for name in sorted(os.listdir(fd)):
            try:
                st = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except OSError:
                continue
            path = os.path.join(folder, name)
            if stat.S_ISDIR(st.st_mode):
                if name.startswith('.'):
                    said.append(f'a hidden folder, not entered (a person removes it): {path}')
                continue   # a report folder of its own, or no report folder: never entered here
            why = ('a link' if stat.S_ISLNK(st.st_mode) else 'a hidden file' if name.startswith('.') else 'not a file' if not stat.S_ISREG(st.st_mode)
                   else 'a program' if _program(name, st, fd) else '' if any(fnmatch.fnmatchcase(name, os.path.basename(e['path'])) for e in entries) else 'not in reports.json')
            if not why:
                continue
            if not dry:
                try:
                    os.unlink(name, dir_fd=fd)   # a file, or a link itself: never what a link points at
                except OSError as e:
                    said.append(f'he could not delete ({type(e).__name__}): {path}')
                    continue
            taken.append((path, why))
    finally:
        os.close(fd)
    return taken, said


def _may_delete():
    """A real deletion only for the office's own instance, or a check that brings its own reports.json."""
    return os.path.abspath(store.instance()) == os.path.abspath(store.INSTANCE) or bool(os.environ.get('SCRUM_MASTER_REPORTS'))


def scrub(now=None, dry=None, st=None):
    """ONE SCRUB OF THE REPORT FOLDERS (the owner 2026-10-21). Each deletion one line in his findings (row 1, the round's own, place
    scrub). -> {'ok', 'said', 'taken': [(path, why)], 'red': [...], 'notes': [...], 'dry'}"""
    moment = schedule._now(now)
    dry = (not _may_delete()) if dry is None else dry
    entries = _entries()
    folders, notes = report_folders(entries)
    taken, red = [], []
    for folder in sorted(folders):
        got, said = _scrub_folder(folder, folders[folder], dry)
        taken += got
        notes += said
    red += [n for n in notes if n.startswith('a hidden folder')]
    for e in entries:   # every listed report: there, and written within its max_age
        base, newest = os.path.basename(e['path']), None
        for folder in [f for f, es in folders.items() if e in es]:
            try:
                with os.scandir(folder) as it:
                    for d in it:
                        if not d.name.startswith('.') and fnmatch.fnmatchcase(d.name, base) and d.is_file(follow_symlinks=False):
                            newest = max(newest or 0, d.stat(follow_symlinks=False).st_mtime)
            except OSError:
                continue
        if newest is None and not e.get('transient'):   # a transient file (a lock) is there only while its job runs
            red.append(f"not written: {e['name']} ({e['path']})")
        elif e.get('max_age') is not None and (moment.timestamp() - newest) / 3600 > float(e['max_age']):
            red.append(f"the writer stopped: {e['name']}, newest {schedule._when(datetime.datetime.fromtimestamp(newest, datetime.timezone.utc).isoformat())}, max {e['max_age']} h ({e['writer'].split(':')[0]})")
    red += [f'{why}, deleted: {p}' for p, why in taken if why in RED_WHY]
    if not dry and taken:
        st = st or store.door()
        for i, (p, why) in enumerate(taken):
            st.finding(SCRUB_ROW, SCRUB, p, int(moment.timestamp()) + i, json.dumps({'why': why, 'at': moment.isoformat(timespec='seconds')}, ensure_ascii=False), 'closed')
    plain = sum(1 for _, why in taken if why not in RED_WHY)
    said = (f"reports: {'would delete' if dry else 'deleted'} {len(taken)} ({plain} not in reports.json, {len(taken) - plain} red)" if taken else 'reports: nothing to delete') \
        + (f' · red: ' + '; '.join(red[:4]) + (f' (+{len(red) - 4} more)' if len(red) > 4 else '') if red else '') \
        + (' · ' + '; '.join(n for n in notes if not n.startswith('a hidden folder'))[:200] if any(not n.startswith('a hidden folder') for n in notes) else '')
    return {'ok': not red, 'said': said, 'taken': taken, 'red': red, 'notes': notes, 'dry': dry}


def scrub_lines(st=None, since=None):
    """THE SCRUB'S LINES for the page: one a deletion (what, when), newest first, of those at or after `since` (a moment)."""
    out = []
    for r in (st or store.door()).findings(row=SCRUB_ROW):
        if r['place'] != SCRUB:
            continue
        try:
            got = json.loads(r['severity'])
            at = datetime.datetime.fromisoformat(got['at'])
        except (TypeError, ValueError, KeyError):
            continue
        if since is None or at >= since:
            out.append((at, f"{schedule._when(got['at'])} · deleted {r['file']} · {got.get('why', '')}"))
    return [line for _, line in sorted(out, key=lambda x: x[0], reverse=True)]


