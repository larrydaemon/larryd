"""THE RED-ROW FIX LOOP (the owner 2026-10-22, his ruling between his two words: "Red rows force their fix"; THE RULE of
2026-10-21 09:10: "a row NOT DONE runs the thing that forces it done, immediately, by itself (never 'nobody is working on
it')"). Row 025 calls force() every round with the day's red rows; each red row is then, in this order:
  fixing    ITS OWN hired fixer (the Developer's own, shared_developer.hire), now: EVERY RED ROW AT ONCE (the owner
            2026-10-22: "when the item is red each one should have its own agent trying to fix it... not one at a time
            all"), each in a tree of its own (a detached worktree of the hot fix tree, red_rows/<NNN> beside it), so no
            fixer ever writes in another's; none starts while the hot fix utility, the night's chain or the cool down
            holds the hot fix tree (shared_developer.clear)
  queued    its fixer not started yet: the next round starts it
  fixed     its fixer's commit applied on the hot fix branch, one at a time under a lock (the take-in carries it); the
            row's own next look says. A native row's words move piece by piece while its proof run goes (the build lands,
            its walk minutes after, then the compare): whether the red is another's is read once the chain at work on its
            piece ended, never in the gap (row 037, 2026-10-24 12:18)
  owner     its fixer found the cause is the owner's hands alone (a pin, a seal, a lock, a ruling): his exact steps kept
  stuck     its fixer could not fix it (or touched outside its ground: the turn undone); tried again after RETRY
A fixer works inside the RED ROW ground (shared_developer CONF ground) and the wall: a test, a check, the sealed core or
the machinery touched, or anything outside the ground, and the whole turn is undone (proven undone). It never changes a
row, a rule or the Judge (~/virtual_sanity is not in its tree). Its record per row and day is a file under his logs
(logs/red_rows/<day>/<NNN>.json), never a row of his database.

    python -m agent.shared_red_rows fix <NNN>      one fixer for one red row (started detached by force())

THE TWO GROUPS (the owner 2026-10-24: "we have two groups and it should be clear. group 1 the thing to fix is in the
virtual_workspace it has access can automatically go fix it. group 2 the agent itself is broken and this should require an
unlock"; "make sure its dynamic and not hard coded because all are changing constantly"): every red row is sorted first,
from the records (group_of), never a list of rows. WORKSPACE: its fixer starts NOW, in a tree of its own, waiting for
nothing (the owner 2026-10-23: NOTHING WAITS FOR A LATER PROCESS TO CLEAR); only a row whose fix is the chain at work
this minute (its plan keys: the nightly container, an app) is held on that chain. AGENT: its record says so (state agent),
no platform fixer is hired; it heals only while the master lock is OPEN by his press (master_open), the healer of step 2.
What forces a red row (forcing): a fixer ALIVE on it, its fix APPLIED and the row's next look pending, or HELD on the chain
running now. Queued, stuck, the owner's hands, an AGENT red: nothing forces them, said as that (row 025 is red)."""
import datetime
import glob
import json
import os
import re
import subprocess
import sys

from agent import shared_developer as developer   # the hire, the wall, the tree, its lock
from agent import shared_schedule as schedule     # the day
from agent import shared_store as store           # the logs folder, written whole
from agent import shared_where as where           # his places as he types them (settings reads)

FOLDER = 'red_rows'
SOURCE = 'RED ROW'                          # the fixer's ground (shared_developer CONF ground 'RED ROW')
APPROACHES = 3                              # a stuck row's approaches on the SAME inputs (the owner 2026-10-22: "keep trying to fix it"); new inputs start again at 1
RETRY = datetime.timedelta(minutes=30)      # a stuck row is hired again after this long (the owner 2026-10-22: "keep trying to fix it")
DONE_WORDS = ('FIXED', 'OWNER', 'STUCK', 'AGENT')   # the fixer's last line begins with one of these (AGENT: the cause is the agent's own, its file and line: GROUP 2)
GROUPS = ('WORKSPACE', 'AGENT')             # THE TWO GROUPS (the owner 2026-10-24); a row's group is read from the records, never from a list


def plan():
    """THE ROWS AS HIS PLAN HAS THEM (schemas/rows.json): {n: its row, with its keys}, read at every call and never kept
    (the owner 2026-10-24: "dynamic and not hard coded because all are changing constantly")."""
    try:
        with open(where.ROWS_FILE, encoding='utf-8') as fh:
            book = json.load(fh)
    except (OSError, ValueError):
        return {}
    return {int(r['n']): r for r in book.get('rows') or [] if str(r.get('n', '')).lstrip('-').isdigit()}


def plan_book(key, default=None):
    """one top key of his plan (groups, containers, x_rule), read now"""
    try:
        with open(where.ROWS_FILE, encoding='utf-8') as fh:
            return json.load(fh).get(key, default)
    except (OSError, ValueError):
        return default


def row_key(n, key, default=None, rows=None):
    """one key of a row in his plan (app, own_fix, stop, measure, chain, rerun, step), or default"""
    return ((rows if rows is not None else plan()).get(int(n)) or {}).get(key, default)


def app_of(n, rows=None):
    """the app a row's facts come from (its key app: iphone, macos; the rows that read a kept build), or ''"""
    return str(row_key(n, 'app', '', rows) or '')


def chain_rows(rows=None):
    """THE ROWS WHOSE RED THE NIGHT'S CHAIN CLEARS BY ITSELF: the nightly container, unless the row says chain false (the
    data sync, 039: the daily schedule's, no piece of the chain). -> set of row numbers"""
    rows = rows if rows is not None else plan()
    return {n for n, r in rows.items() if r.get('container') == 'nightly' and r.get('chain', True) is not False}


def stop_rows(rows=None):
    """a night step's stop (as the rows name it) and the row whose fault that stop is: each row's key stop. -> {word: n}"""
    out = {}
    for n, r in (rows if rows is not None else plan()).items():
        for w in r.get('stop') or []:
            out[str(w)] = int(n)
    return out


def master_open():
    """IS THE MASTER LOCK OPEN, by the owner's press: its mark (settings master.mark) exists and is root's regular file
    (no session can make it). No mark named: closed."""
    import stat
    mark = str((where.SETTINGS.get('master') or {}).get('mark') or '')
    if not mark:
        return False
    try:
        st_ = os.lstat(mark)
    except OSError:
        return False
    return st_.st_uid == 0 and stat.S_ISREG(st_.st_mode)


def chain_running(n=None, rows=None):
    """THE CHAIN AT WORK ON THIS ROW'S PIECE NOW (its fix, never a fixer beside it): the tower's lock holder for a row of the
    chain (chain_rows), the hot fix utility for a row that reads an app (its key app); '' otherwise, and '' for a row of
    neither. n None: either chain, for anyone."""
    rows = rows if rows is not None else plan()
    if n is None or int(n) in chain_rows(rows):
        try:
            from agent import shared_native as native
            held = native.running()
        except Exception:   # noqa: BLE001  (the lock unreadable: nothing holds it)
            held = ''
        if held:
            return f"the chain holding the tower's lock ({held})"
    if n is None or app_of(n, rows):
        try:
            with open(where.REPORTS['hotfix_lock'], encoding='utf-8') as fh:
                pid = fh.read().strip()
            if pid.isdigit() and developer._alive(int(pid)):
                return f'the hot fix utility (pid {pid})'
        except (OSError, KeyError):
            pass
    return ''


def group_of(n, words, rec=None):
    """WHICH GROUP A RED ROW IS IN, from the records (the owner 2026-10-24: two groups, dynamic): AGENT when the loop's record
    says its fixer read the cause into the agent (state agent), when the row's own first words are the round's for a program
    that failed (his plan's groups.agent_words: "its program wrote no run", "he could not read it: ..."), or when a BROKEN
    file it names lies under ~/virtual_sanity (settings reads.sanity); WORKSPACE otherwise (a BROKEN file under the workspace,
    or no file named: the workspace's until a read says otherwise). -> (group, why)"""
    from agent import shared_chunks as chunks
    words = str(words or '')
    fixer_said = rec and (rec.get('by') == 'its fixer' or (str(rec.get('state') or '') == 'agent' and rec.get('by') != 'the sorting'))
    if fixer_said and (rec.get('cause') or rec.get('said')) and _same_red(str(rec.get('words') or ''), words):
        return 'AGENT', f"its fixer read the cause into the agent: {str(rec.get('cause') or rec['said'])[:160]}"
    head = words.split(' · ')[0].strip().lower()
    for w in (plan_book('groups') or {}).get('agent_words') or []:
        if re.match(r'(?:[^:·]{0,40}(?::| ·) )?' + re.escape(str(w).lower()) + r'(?=[\s:]|$)', head):   # the words whole: "its program's" is a row's own sentence
            return 'AGENT', f"the round's own words: {head[:140]}"
    if chunks.BROKEN in words:
        sanity = os.path.abspath(os.path.expanduser(str(where.path('sanity'))))
        workspace = os.path.abspath(os.path.expanduser(str(where.WORKSPACE)))
        named = [p.strip().split(' ')[0] for p in words.split(chunks.BROKEN, 1)[1].split(' · ') if p.strip()]
        full = [(p, os.path.abspath(os.path.expanduser(p))) for p in named]
        for p, f in full:
            if f == sanity or f.startswith(sanity + os.sep):
                return 'AGENT', f"its broken file is the agent's own: {p}"
        for p, f in full:
            if f == workspace or f.startswith(workspace + os.sep):
                return 'WORKSPACE', f"its broken file is the workspace's: {p}"
    return 'WORKSPACE', "the cause is the workspace's until a read says otherwise"


def agent_broken(st=None, names=None, off=(), day=None, top=None):
    """GROUP 2 NOW: every red row whose cause is the agent's own, as the newest ended runs and the loop's records say it
    (a row of a section he switched off never counts). -> [{'n', 'name', 'why', 'words'}], by number"""
    st = st or store.door()
    rows = plan()
    names = names if names is not None else {n: r.get('name', '') for n, r in rows.items()}
    try:
        runs = st.newest_runs(ended=True)
    except Exception:   # noqa: BLE001  (his records unreadable: no warning made up)
        return []
    out = []
    for n, r in sorted(runs.items()):
        if n not in names or n in set(off) or r.get('state') != 'red':
            continue
        group, why = group_of(n, r.get('text'), read(n, day, top))
        if group == 'AGENT':
            out.append({'n': int(n), 'name': names[n], 'why': why, 'words': str(r.get('text') or '')[:200]})
    return out


def _folder(day=None, top=None):
    day = str(day or schedule.cycle())
    return os.path.join(top, day) if top else os.path.dirname(store.Store().log_path(FOLDER, day, 'x'))


def _path(n, day=None, top=None):
    return os.path.join(_folder(day, top), f'{int(n):03d}.json')


def read(n, day=None, top=None):
    try:
        with open(_path(n, day, top), encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _write(rec, day=None, top=None):
    path = _path(rec['row'], day, top)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    store.write_whole(path, rec)


def _now():
    return schedule._now(None)


def _alive(rec):
    return bool(rec and rec.get('pid') and developer._alive(int(rec['pid'])))


def state(n, day=None, top=None):
    """THIS RED ROW'S PLACE IN THE LOOP TODAY: 'fixing', 'queued', 'fixed', 'owner', 'stuck', 'withdrawn' (its red is another
    red row's stop: force), 'held' (the chain at work on its piece is its fix), 'agent' (GROUP 2: the agent itself, no
    platform fixer) or None (never started). A fixer that died without its last word is 'stuck'."""
    rec = read(n, day, top)
    if not rec:
        return None
    if rec['state'] == 'fixing' and not _alive(rec):
        return 'stuck'
    return rec['state']


def forcing(n, day=None, top=None):
    """WHAT FORCES THIS RED ROW NOW, in the row's words, or '' when nothing does. THE LAW (the owner 2026-10-24, the fix
    loop green on a queue nobody served): a fixer ALIVE on it (its pid), its fix APPLIED and the row's next look pending,
    or HELD on the chain at work on its piece this minute. Queued and not started, stuck (hired again or spent), the
    owner's hands, an AGENT red (no healer yet): nothing forces them, '' here, red on row 025 with the group said."""
    rec, s = read(n, day, top), state(n, day, top)
    healer = (rec or {}).get('group') == 'AGENT'   # GROUP 2 while the lock is open: its healer, said as that
    if s == 'fixing':
        return (f"healing: its healer (pid {rec.get('pid')}) since " if healer else f"fixing: its fixer (pid {rec.get('pid')}) since ") + str(rec.get('at') or '')[11:16]
    if s == 'fixed':
        return f"healed by the agent itself ({rec.get('commit', '')[:9]}), its next look says" if healer else f"fixed by the loop ({rec.get('commit', '')[:9]}), its next look says"
    if s == 'held':
        going = chain_running(n)
        return f'held on {going}' if going else ''
    return ''


def proof(rec, going=None):
    """A FIXED NATIVE ROW'S PROOF (rows 036, 037, 038): its fix on the hot fix branch changes nothing the row reads until
    its app is built from it (remeasure), so a 'fixed' record whose red words have not moved is still forced, by that
    build: its words while the build is asked, refused or going; '' once the build ran and the words stayed (the fix did
    not clear it), and '' for any other row. `going`: the hot fix utility's start when it runs (the page's own check
    when None)."""
    rec = rec or {}
    target = app_of(int(rec.get('row') or 0))
    if not target or rec.get('state') != 'fixed' or not rec.get('commit'):
        return ''
    last = rec.get('rerun') or {}
    if last.get('commit') != rec['commit']:
        return f'its proof build (RUN NOW {target}), asked at the next round'
    if not last.get('started'):
        return f"its proof build (RUN NOW {target}): {last.get('words') or 'not started yet'}"
    if going is None:
        from web import page   # the utility's process, read the way RUN NOW itself refuses a second run
        going = page.run_now_running()
    if going:
        since = going[11:16] if len(going) >= 16 and going[10] == 'T' else going
        return f'its proof build (RUN NOW {target}) runs since {since}'
    return ''


def again_at(rec):
    """WHAT HIRES A STUCK ROW AGAIN (the owner 2026-10-23: "no timed waits either"): a cause, never a time"""
    approach = int((rec or {}).get('approach') or 1)
    if approach < APPROACHES:
        return f'now with approach {approach + 1} of {APPROACHES}'
    return f'the moment what it reads changes (main, the hot fix tree, its code, its words): its {APPROACHES} approaches on these inputs are spent'


def inputs(n, words):
    """WHAT A RED ROW READS, AS ONE FINGERPRINT: main's commit, the hot fix tree's commit, the row's own code and its words
    now (its numbers aside, so a timer is no new input). -> sha256 hex"""
    import hashlib
    h = hashlib.sha256()
    for args in (('-C', developer.WORKSPACE, 'rev-parse', 'main'), ('-C', developer.tree(), 'rev-parse', 'HEAD')):
        try:
            h.update(subprocess.run(['git', *args], capture_output=True, text=True, timeout=20).stdout.strip().encode())
        except (OSError, subprocess.SubprocessError, KeyError):
            h.update(b'?')
        h.update(b'\0')
    mod = _module(n)
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), mod.split('.', 1)[-1] + '.py'), 'rb') as fh:
            h.update(fh.read())
    except OSError:
        h.update(b'?')
    h.update(b'\0' + re.sub(r'\d+', '#', str(words or '')).encode())
    return h.hexdigest()


def stops_on(n, words, rows=None):
    """THE ROW WHOSE FAULT THIS RED IS, when its words name another row's stop ("the night stopped before it at step12 THE
    JUDGE": row 032's; "row 032's step first": 032): its number, or None when the red is the row's own. The stops and
    their rows are each row's key stop in his plan (stop_rows), never a list here. The watch session 2026-10-24 07:08:
    row 034's fixer, hired on a stop that was row 032's, wrote four steps and none of them the look's."""
    stops = stop_rows(rows)
    names = sorted(stops, key=len, reverse=True)
    at = '|'.join(re.escape(w) for w in names) if names else r'(?!x)x'
    m = re.search(r"\bstopped (?:before (?:it|them) )?at (" + at + r")\b|\brow (\d{3})'s step first", str(words or ''))
    if not m:
        return None
    other = int(m.group(2)) if m.group(2) else stops.get(m.group(1))
    return other if other and other != int(n) else None


def force(reds, day=None, top=None, start=None):
    """EVERY RED ROW FORCES ITS FIX, SORTED INTO THE TWO GROUPS FIRST (the owner 2026-10-24): a row with a fix of its own
    runs it; a red that is another red row's stop is withdrawn to that row; an AGENT red is recorded as that (state agent,
    the group and why; no platform fixer, the healer of step 2 while the master lock is open); a row whose piece the chain
    works on this minute is HELD on it; every other red row is queued and gets its own fixer NOW, in a tree of its own,
    waiting for nothing (the owner 2026-10-23: NOTHING WAITS FOR A LATER PROCESS TO CLEAR; only the apply of its commit
    waits, _apply). A stuck one again after RETRY. reds: [(n, name, its words)]. -> {n: its state}"""
    day = day or schedule.cycle()
    now = _now()
    rows = plan()
    own = {int(n) for n, name, words in reds if (OWN.get(int(n)) or (_own_fix if row_key(n, 'own_fix', None, rows) else None) or (lambda *a, **k: False))(n, name, words, day, top)}   # A ROW WITH ITS OWN FIX (its plan key own_fix): run, never a hired fixer
    red = {int(n) for n, _, _ in reds}
    for n, name, words in reds:
        if int(n) in own:
            continue
        rec, s = read(n, day, top), state(n, day, top)
        other = stops_on(n, words, rows)
        if other in red:   # ANOTHER RED ROW'S STOP (the watch session 2026-10-24 07:08): that row's fix is its fix, no fixer of its own; one hired on it before is withdrawn, its word never shown
            if rec and rec.get('state') != 'withdrawn' and s != 'fixing':
                _write({**rec, 'state': 'withdrawn', 'said': f"its red is row {other:03d}'s stop: that row's fix is its fix", 'ended': now.isoformat(timespec='seconds'), 'pid': None}, day, top)
            continue
        same = bool(rec) and _same_red(str(rec.get('words') or ''), words)
        group, why = group_of(n, words, rec)
        if group == 'AGENT' and s != 'fixing':   # GROUP 2: the agent itself; no platform fixer
            by = 'its fixer' if (rec or {}).get('by') == 'its fixer' or (s == 'agent' and (rec or {}).get('by') != 'the sorting') else 'the sorting'
            cause = str((rec or {}).get('cause') or (rec or {}).get('said') or why) if by == 'its fixer' else why
            if not master_open():   # LOCKED: said as that, his one step UNLOCK AGENT
                if s != 'agent' or not same:
                    _write({'row': int(n), 'name': name, 'words': words, 'state': 'agent', 'group': group, 'by': by, 'said': why, 'cause': cause, 'at': now.isoformat(timespec='seconds'),
                            'tries': int((rec or {}).get('tries') or 0)}, day, top)
                continue
            mine = (rec or {}).get('group') == 'AGENT' and same   # OPEN BY HIS PRESS: its healer (shared_healer), started now as a fixer is
            again = s == 'stuck' and rec and now - datetime.datetime.fromisoformat(str(rec.get('ended') or rec['at'])) >= RETRY
            if s in (None, 'agent', 'withdrawn', 'held') or again or not mine:
                _write({'row': int(n), 'name': name, 'words': words, 'state': 'queued', 'group': group, 'by': by, 'cause': cause, 'at': now.isoformat(timespec='seconds'),
                        'tries': int((rec or {}).get('tries') or 0)}, day, top)
            continue
        going = chain_running(n, rows) if s not in ('fixing', 'fixed') else ''
        if going:   # THE CHAIN IS ITS FIX THIS MINUTE: held on it, no fixer beside it
            if s != 'held' or not same:
                _write({'row': int(n), 'name': name, 'words': words, 'state': 'held', 'group': group, 'said': f'held on {going}', 'at': now.isoformat(timespec='seconds'),
                        'tries': int((rec or {}).get('tries') or 0)}, day, top)
            continue
        if s == 'fixed' and not same and chain_running(n, rows):   # A FIXED ROW'S WORDS MOVE WHILE THE CHAIN AT WORK ON ITS PIECE RUNS (row 037, 2026-10-24 12:18: the proof build landed, its walk ten minutes after; in that gap the row said "walk: never ran" and a fixer was hired beside the utility walking it): the run's pieces land one by one, each moving the words; the fixed record stands (proof: the run forces it) and whether the red is ANOTHER is read once the run ends, never a fixer hired in the gap
            continue
        again = s == 'stuck' and rec and now - datetime.datetime.fromisoformat(str(rec.get('ended') or rec['at'])) >= RETRY
        if s is None or again or s in ('withdrawn', 'held', 'agent') or (s == 'fixed' and not same):   # still red with ANOTHER red's words after its fix: once more (the same red with the chain's tail or a new count is not another: its remeasure stands; the chain at work on its piece still running is not the end of its remeasure, above); withdrawn, held or agent no longer so: its own fixer now
            _write({'row': int(n), 'name': name, 'words': words, 'state': 'queued', 'group': group, 'at': now.isoformat(timespec='seconds'),
                    'tries': int((rec or {}).get('tries') or 0)}, day, top)
    for r in sorted((r for r in _all(day, top) if r['state'] == 'queued' and int(r['row']) not in own and int(r['row']) in red), key=lambda r: r['at']):   # EVERY QUEUED RED ROW GETS ITS OWN FIXER NOW
        child = (start or _start)(r['row'], day, top)
        if child is not None and getattr(child, 'pid', None):   # started: fixing from now, by its own pid, so the next round never starts it twice
            _write({**r, 'state': 'fixing', 'pid': child.pid, 'at': _now().isoformat(timespec='seconds')}, day, top)
    remeasure(day, top)   # a native row fixed by the loop builds, walks and pictures its app again now, not at the night
    return {int(n): state(n, day, top) for n, _, _ in reds}


# THE ROWS THAT READ A KEPT APP (its build, its walk, its picture check, its install): each row's key app in his plan (app_of), never a list here


def remeasure(day=None, top=None, run=None):
    """A FIXED NATIVE ROW RE-MEASURES AT ONCE (the goal: "the red is cleared instantly"; never the 01:00 night): a fix the
    loop applied on the hot fix branch for row 036, 037 or 038 changes nothing those rows read until the app is built
    from it, walked and (the Mac) pictured; so its app's RUN NOW starts now (the page's own button: the hot fix utility,
    for the Mac then the install, then the rows' looks), once for that fix's commit; refused (the night, the cool down,
    a run going), it is asked again next round. Two rows of one app on one commit (037 and 038, the Mac) share the one
    run: the second takes the first's start, never a build of its own. -> {row: what RUN NOW said}"""
    said = {}
    records = _all(day, top)
    rows = plan()
    for r in records:
        target = app_of(int(r['row']), rows)
        if not target or r.get('state') != 'fixed' or not r.get('commit') or r.get('group') == 'AGENT':   # a heal (GROUP 2) lands on the Scrum Master's own repository: no app is built from it, nothing to re-measure
            continue
        last = r.get('rerun') or {}
        if last.get('commit') == r['commit'] and last.get('started'):
            continue
        twin = next((o for o in records if o is not r and app_of(int(o.get('row') or 0), rows) == target
                     and (o.get('rerun') or {}).get('commit') == r['commit'] and (o.get('rerun') or {}).get('started')), None)
        if twin:   # ONE RUN FOR ONE APP (rows 037 and 038 share the Mac's build, pictures and install): the run another row started on this commit is this row's too
            r['rerun'] = {**twin['rerun'], 'words': f"{twin['rerun'].get('words')} (row {int(twin['row']):03d}'s start)"}
            _write(r, day, top)
            said[int(r['row'])] = r['rerun']['words']
            continue
        try:
            if run is None:
                from web import page   # RUN NOW's own start (web/page.py run_now): refused while the night holds the laptop or a run goes
                run = page.run_now
            steps, ref = proof_steps(target, r['commit'])
            started, words = run(target, **({'steps': steps, 'ref': ref} if steps else {}))
        except Exception as e:   # noqa: BLE001  (said in the row's record; asked again next round)
            started, words = False, f'{type(e).__name__}: {e}'
        r['rerun'] = {'commit': r['commit'], 'target': target, 'started': bool(started), 'words': words, 'at': _now().isoformat(timespec='seconds')}
        _write(r, day, top)
        said[int(r['row'])] = words
    return said


NATIVE_MODEL = 'claude-fable-5-1'   # THE OWNER'S RULE (2026-10-20): the web is built by Opus 5.5 only, macOS and iOS by Fable 5.1 only


def fixer_command(n, command):
    """the fixer's command for a row: the native rows' fixer (036 iPhone, 037 and 038 Mac) is Fable 5.1, every other row's the
    page's own (Opus 5.5); the model is the word after --model. -> [args]"""
    command = list(command)
    if app_of(n) and '--model' in command:
        command[command.index('--model') + 1] = NATIVE_MODEL
    return command


COMPARE_FILES = ('utilities/build/walk/pixel.py', 'utilities/build/walk/display.py', 'utilities/build/walk/pixel_rows.json')   # the pixel compare's own files: a fix inside them changes no app
COMPARE_STEPS = {'macos': ('compare', 'install')}   # the apps whose rows read the compare (037, 038): the compare alone on the kept build, then the Mac's install


def proof_steps(target, commit, changed=None, kept=None, tested=None):
    """THE PROOF THE SIZE OF THE FIX (the owner 2026-10-24 09:11: "why is this taking more than 3 min each"): a fix that
    touched only the pixel compare's own files (COMPARE_FILES) since the kept build's commit changes no app, so its proof
    is the compare alone on that build (pixel.py --ref=<kept commit>, about 3 min, the record rows 037 and 038 read),
    never a rebuild and walk of the same app (17 min). Anything else (an app source, a build file, no kept build, a kept
    build whose walk is not green, a target whose rows read no compare) keeps the page's own steps.
    -> (steps, ref) or (None, '') for the page's own"""
    steps = COMPARE_STEPS.get(target)
    if not steps:
        return None, ''
    from agent import shared_native as native
    kept = kept if kept is not None else native.kept(target) or {}
    tested = tested if tested is not None else native.tested(target) or {}
    base = str(kept.get('commit') or '')
    if not base or tested.get('verdict') != 'green' or str(tested.get('commit') or '') != base:
        return None, ''
    if str(commit or '').startswith(base[:12]) or base.startswith(str(commit or '')[:12]) and len(str(commit or '')) >= 7:
        return steps, base   # the kept build IS this commit (nothing to rebuild): its pictures taken again, as 2026-10-24 09:34 (the CDN's pictures had not arrived in time)
    if changed is None:
        try:
            got = subprocess.run(['git', '-C', developer.tree(), 'diff', '--name-only', f'{base}..{commit}'], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError, KeyError):
            return None, ''
        if got.returncode != 0:
            return None, ''
        changed = [l.strip() for l in got.stdout.splitlines() if l.strip()]
    if not changed or any(f not in COMPARE_FILES for f in changed):
        return None, ''
    return steps, base


def _own_fix(n, name, words, day=None, top=None, start=None):
    """A ROW'S OWN FIX (its plan key own_fix: a subcommand of the row's own program, run before any hired fixer; 038's
    install: when the kept Mac build IS the tested Mac app and only its install is missing, the row's own install runs now,
    never a hired fixer and never the 06:15 clock): the row's program says ready() -> (kept, why); ready and nothing of
    its own alive, the subcommand runs detached and the record says so. Any other cause is the hired fixer's. -> True
    when the row's own fix took it"""
    import importlib
    rows = plan()
    what, module = row_key(n, 'own_fix', None, rows), str((rows.get(int(n)) or {}).get('module') or '')
    if not what or not module:
        return False
    try:
        kept, why = importlib.import_module(module).ready()
    except Exception:   # noqa: BLE001  (a row with no ready(): no fix of its own)
        return False
    if not kept or why:
        return False
    rec = read(n, day, top) or {}
    if _alive(rec):
        return True   # its own fix runs now
    app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    child = (start or subprocess.Popen)([sys.executable, '-m', module, str(what)], cwd=app,
                                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
                                        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    _write({'row': int(n), 'name': name, 'words': words, 'state': 'fixing', 'pid': getattr(child, 'pid', None),
            'said': f"its own {what} of {str(kept.get('commit') if isinstance(kept, dict) else kept)[:12]}", 'at': _now().isoformat(timespec='seconds'),
            'tries': int(rec.get('tries') or 0) + 1}, day, top)
    return True


OWN = {}   # a check's own fix for a row, in place of its plan key (the plan's own_fix is the rule; nothing is listed here)

def _all(day=None, top=None):
    out = []
    for path in sorted(glob.glob(os.path.join(_folder(day, top), '[0-9][0-9][0-9].json'))):
        try:
            with open(path, encoding='utf-8') as fh:
                out.append(json.load(fh))
        except (OSError, ValueError):
            continue
    return out


def _start(n, day=None, top=None):
    """one fixer, detached (its own session: a round that ends never takes it down)"""
    app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args = [sys.executable, '-m', 'agent.shared_red_rows', 'fix', f'{int(n):03d}', str(day or schedule.cycle())] + ([top] if top else [])
    return subprocess.Popen(args, cwd=app, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})


def words_for(rec, agent_file, root=None):
    return (f"RED ROW {rec['row']:03d} {rec['name']} of the Scrum Master is red. Its own words now:\n\n{rec['words']}\n\n"
            f"The row's code (read it, never change it): {agent_file}\n"
            f"You are in {root or developer.tree()}, this row's own copy of the platform's hot fix tree. FIX THE CAUSE the row names, here, "
            "in plain code. Never change a test, a check, the sealed core (wid, global_config.json) or anything outside the "
            "platform's offices, minis, utilities/build and plans: such a change is undone whole. Never change the row or "
            "its rule; never make a red row green by hiding what it measures.\n"
            "When the cause is only the owner's hands (a pin, a seal, a lock, a password, a ruling between his words), change "
            "nothing and say his exact steps.\n"
            "Say only what the row's words carry: never a count, a file or a fault they do not name. A step of yours is never "
            "his written GO, a merge, a branch move, a push or a sudo install (his hand lines, not a fix), nor a lock or unlock "
            "the words do not name as the cause. When the words say the night stopped before this row at another step (THE "
            "JUDGE: row 032, THE LOOK: row 034), that row owns the fault: say OWNER: row NNN's step first, then <this row's own "
            "YOUR 3 MIN line>, nothing more.\n"
            "THE TWO GROUPS (the owner): the workspace is yours to fix here; the agent itself (~/virtual_sanity: the Scrum Master, "
            "the Judge, the smoke test, the knowledge store) you may read and never change: when the cause lies there, change "
            "nothing and name its file and line.\n"
            "Your LAST line is exactly one of:\nFIXED: <what you changed, one line>\nOWNER: <his exact steps, one line>\n"
            "AGENT: <the agent's own file and line that is the cause, one line>\nSTUCK: <why, one line>\n")


def _last_word(said):
    for line in reversed([l.strip() for l in str(said or '').splitlines() if l.strip()]):
        for w in DONE_WORDS:
            if line.upper().startswith(w + ':'):
                return w.lower(), line.split(':', 1)[1].strip()
    return 'stuck', 'its fixer gave no last word'


def own_tree(n, root):
    """THIS RED ROW'S OWN TREE: red_rows/<NNN> beside the hot fix tree (a detached worktree: no branch is made)"""
    return os.path.join(os.path.dirname(os.path.abspath(root)), FOLDER, f'{int(n):03d}')


APPLY_WAIT = 15 * 60   # seconds a fixed row waits for the hot fix tree to hold no change of another's before its commit is applied


def _apply(commit, git_main, lock_path, wait=None, sleep=None):
    """ITS COMMIT ON THE HOT FIX BRANCH, one fixer at a time (a lock), only on a tree holding no change of another's (the
    Developer's work waits for nothing: the commit waits up to wait seconds). -> ('fixed', its new head) or ('stuck', why)"""
    import fcntl
    import time
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    with open(lock_path, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        wait = APPLY_WAIT if wait is None else wait
        until = time.monotonic() + wait
        while developer._differs(git_main, ('.',)):
            if time.monotonic() >= until:
                return 'stuck', f'the hot fix tree held changes not committed for {wait // 60} minutes: its fix {commit[:9]} was not applied'
            (sleep or time.sleep)(20)
        if git_main('cherry-pick', commit).returncode != 0:
            git_main('cherry-pick', '--abort')
            return 'stuck', f'its fix {commit[:9]} meets another change on the hot fix branch: not applied'
        return 'fixed', git_main('rev-parse', 'HEAD').stdout.strip()


def fix(n, day=None, top=None, hire=None, tree=None):
    """ONE FIXER FOR ONE RED ROW, in its own tree (a detached worktree of the hot fix tree), inside the RED ROW ground and
    the wall; its change committed there, then applied on the hot fix branch (_apply). -> its record"""
    day = day or schedule.cycle()
    rec = read(n, day, top)
    if not rec or not (rec['state'] == 'queued' or (rec['state'] == 'fixing' and rec.get('pid') == os.getpid())):
        return rec
    if rec.get('group') == 'AGENT':   # GROUP 2: the agent's own; its healer, never a platform fixer (shared_healer)
        return _heal(n, rec, day, top, hire)
    root = tree or developer.tree()
    git_main = lambda *a: subprocess.run(['git', '-C', root, *a], capture_output=True, text=True)
    mine = own_tree(n, root)
    git = lambda *a: subprocess.run(['git', '-C', mine, *a], capture_output=True, text=True)
    rec.update(state='fixing', pid=os.getpid(), at=_now().isoformat(timespec='seconds'), tries=int(rec.get('tries') or 0) + 1)
    _write(rec, day, top)
    git_main('worktree', 'remove', '--force', mine)   # an old one of this row's, left by a fixer that died
    git_main('worktree', 'prune')
    made = git_main('worktree', 'add', '--detach', mine, 'HEAD')
    if made.returncode != 0:
        rec.update(state='stuck', said=f'its own tree could not be made: {made.stderr.strip()[-160:]}', ended=_now().isoformat(timespec='seconds'), pid=None)
        _write(rec, day, top)
        return rec
    try:
        agent_file = next(iter(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"agent{int(n):03d}_*.py"))), '')
        item = {'title': f"red row {int(n):03d} {rec['name']}", 'evidence': rec['words']}   # the 3 way switch's question (shared_developer._caller)
        links = developer._links(git)
        conf = developer.CONF['fixer']
        code, said = (hire or developer.hire)(fixer_command(n, conf['command']), words_for(rec, agent_file, mine), mine, int(conf['minutes']) * 60)
        word, line = _last_word(said)
        if developer.wall(git, SOURCE, links) == 'outside':
            word, line = 'stuck', 'its change touched outside the RED ROW ground (a test, a check, the sealed core or the machinery): undone whole'
        elif developer._differs(git, ('.',)):
            if word == 'fixed':
                git('add', '-A')
                done = git('commit', '-q', '-m', f"RED ROW {int(n):03d} {rec['name']}: {line}"[:300])
                if done.returncode == 0:
                    word, head = _apply(git('rev-parse', 'HEAD').stdout.strip(), git_main, os.path.join(_folder(day, top), 'apply.lock'))
                    if word == 'fixed':
                        rec['commit'] = head
                    else:
                        line = head
                else:
                    word, line = 'stuck', 'its change could not be committed: undone'
            # a change without FIXED is never kept: its tree goes whole below
        elif word == 'fixed':
            word, line = 'stuck', 'it said FIXED but changed nothing'
        del item
    finally:
        git_main('worktree', 'remove', '--force', mine)
    rec.update(state=word, said=line, code=code, ended=_now().isoformat(timespec='seconds'), pid=None)
    if word == 'agent':   # ITS FIXER READ THE CAUSE INTO THE AGENT: group 2 from now, its words the cause (group_of)
        rec.update(group='AGENT', by='its fixer', cause=line)
    _write(rec, day, top)
    if word == 'fixed' and app_of(n):
        remeasure(day, top)   # its app built, walked and pictured again at once, not at the next round
    measure = MEASURES.get(str(row_key(n, 'measure', '') or ''))
    if measure and top is None:   # its measure taken again now, never at the detector's next tick: the row's next look is of this moment
        measure()
    return rec


def _heal(n, rec, day=None, top=None, hire=None, **more):
    """ONE HEALER FOR ONE AGENT RED (shared_healer.heal), its record kept as a fixer's is: fixing with its pid, then its
    word."""
    from agent import shared_healer as healer
    rec.update(state='fixing', pid=os.getpid(), at=_now().isoformat(timespec='seconds'), tries=int(rec.get('tries') or 0) + 1)
    _write(rec, day, top)
    try:
        word, line, extra = healer.heal(rec, _folder(day, top), hire=hire, **more)
    except Exception as e:   # noqa: BLE001  (a healer that breaks is stuck, said; never a silent record)
        word, line, extra = 'stuck', f'its healer broke: {type(e).__name__}: {e}'[:200], {}
    rec.update(state=word, said=line, ended=_now().isoformat(timespec='seconds'), pid=None, **{k: v for k, v in extra.items() if k in ('commit', 'base', 'code', 'files')})
    _write(rec, day, top)
    return rec


def _detector_again():
    """the lie detector run again now, detached (agent/rerun_lie_detector.py: one whole run, about 2 s; its report
    written starts rows 018-020 again, ai.positivefeedback.spine.cebf.rows)"""
    app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return subprocess.Popen([sys.executable, '-m', 'agent.rerun_lie_detector'], cwd=app, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True, env={**os.environ, 'PYTHONPATH': app, 'PYTHONDONTWRITEBYTECODE': '1'})


MEASURES = {'cebf': _detector_again}   # WHAT A MEASURE IS, by name (the rows that take one again when a fixer's turn ends: each row's key measure in his plan)


# ---- THE OWNER'S HANDS (the owner 2026-10-23: "make green and add the copy button anything that needs me / with a short
# summary of what it does under it"): every red row of the day that only his hands clear, each with the exact lines he
# types (the copy button's), a short plain summary under them, and the whole text it came from. Two sources, read only:
#   the loop's word       a red row whose fixer said OWNER: his exact steps (its record under logs/red_rows/<day>)
#   the row's own words   a red row that says TO CLEAR: / the one action left: (row 017's audit)
# A line is a command only when the text names it (in backticks, or a hand line: lock all, unlock sanity); a step with
# no line of its own (review, look over, a named branch, a named setting) gets a line that only SHOWS what to look at
# (git log, grep), never one that changes anything the text did not name.
OWNER_ROW = re.compile(r'(?:TO CLEAR|the one action left):\s*(.+?)(?:\s+·\s+|$)')
SPAN = re.compile(r'`([^`]+)`')
HAND_LINES = ('unlock sanity', 'lock all', 'lock sanity')   # his lock tool's own lines, typed bare
COMMAND_WORDS = ('git', 'python', 'python3', 'cd', 'lock', 'unlock', 'grep')
PLACE = r'(~/[\w./-]*\w)'
CHANGED_SINCE_SEAL = re.compile(r'since your seal of (\d{4}-\d{2}-\d{2}): \d+ files \(([^)]*)\)')   # row 017's own words (agent017 _vaults)
SINCE_PIN = re.compile(r'since the (\d\d:\d\d) pin')
BRANCH = re.compile(r'\b(hotfix/[\w.-]*\w)')
SETTING_KEY = re.compile(r'(?<![\w/.~])([a-z_]+(?:\.[a-z_]+)+)(?![\w/])')
BY_HAND = re.compile(r'\b(PIN|your key|GO|rule whether|console|tell the Scrum Master|withdraw|compile|review|look over|read|set |add its|remove|declare)', re.I)


HIS_ALONE = re.compile(r'(?:^|&& )(?:un)?lock \w|judge\.py seal|take_in takein(?!.*--hired)|git (?:commit|merge|branch -[mdD]|push)\b')   # his password, his key, his GO: nothing else is his box
ONLY_SHOWS = re.compile(r'^(?:cd \S+ && )?(?:git(?: -C \S+)? (?:log|diff|show|status)\b|grep )')


def _home(key):
    """a place of his as he types it (~/...): settings reads, never expanded"""
    return where.SETTINGS['reads'][key]


def _is_command(line):
    first = line.split()[0] if line.split() else ''
    return first in COMMAND_WORDS or first.startswith(('~/', '/')) or line in HAND_LINES


def _in_place(text, start, end, line):
    """the folder a span is typed in, when the text names one ('... `x` from ~/a', 'in ~/a run `x`'): cd there first;
    a git line with no folder of its own reads the platform (settings reads workspace)"""
    if line.startswith('cd ') or ' -C ' in f' {line}' or line in HAND_LINES:
        return line
    after = re.match(r'\s*(?:\([^)]*\)\s*)?(?:from|in) ' + PLACE, text[end:])
    before = re.findall(r'\bin ' + PLACE, re.split(r'`[^`]*`|[.;]\s|\bthen\b', text[:start])[-1])
    place = (after and after.group(1)) or (before and before[-1])
    if place:
        return f'cd {place} && {line}'
    return f"git -C {_home('workspace')} {line[4:]}" if line.startswith('git ') else line


def commands(text, row_text='', day=None):
    """THE LINES HE TYPES for one hand step, in the text's order: each named line, then the lines that only show what the
    text asks him to look at. -> [line]"""
    out = []
    for m in SPAN.finditer(text):
        line = m.group(1).strip()
        if _is_command(line):
            out.append(_in_place(text, m.start(), m.end(), line))
    bare = SPAN.sub(' ', text)
    out += [h for h in HAND_LINES if re.search(rf'\b{h}\b', bare) and h not in out]
    shows = []
    seal = CHANGED_SINCE_SEAL.search(row_text) or CHANGED_SINCE_SEAL.search(text)
    if seal and not any(' log' in c for c in out):   # REVIEW THOSE COMMITS: row 017's own measure, as agent017 counts them
        offices = re.findall(r'([a-z][\w-]*) \d+', seal.group(2))
        shows.append(f"git -C {_home('workspace')} log --stat --no-merges --since={seal.group(1)}T00:00:00+00:00 main -- {' '.join(offices)}")
    pin = SINCE_PIN.search(text)
    if pin and not any(' log' in c for c in out):   # WHAT CHANGED SINCE THE PIN: the Judge's and the smoke test's own repositories
        for word, key in (('judge', 'judge_settings'), ('smoke', 'smoke_settings')):
            if word in text.lower():
                shows.append(f"git -C {os.path.dirname(_home(key))} log --stat --since=\"{day} {pin.group(1)}\"")
    if not out and not shows:   # A NAMED BRANCH: what it holds that main has not
        shows += [f"git -C {_home('workspace')} log --oneline --stat main..{b}" for b in dict.fromkeys(BRANCH.findall(text))]
    path = re.search(PLACE, bare)
    if path and path.group(1).endswith('.json'):
        keys = [k for k in SETTING_KEY.findall(bare) if not re.search(r'\.(json|py|pyc|db|sha256)$', k)]
        if keys:   # A NAMED SETTING: where it stands now
            shows.append(f"grep -n '{keys[0].split('.')[-1]}' {path.group(1)}")
    return [s for s in shows if s not in out] + out   # look first, then type


def _does(line):
    """what one line does, in a few plain words"""
    if line in HAND_LINES or re.search(r'(^|/|&& )(un)?lock \w', line):
        what = re.search(r'(?:^|/|&& )((?:un)?lock) ([\w-]+)', line)
        verb, thing = what.group(1), what.group(2)
        said = 'locks every office again (each seal written anew in ~/virtual_sanity/locks, FROST\'s at its top)' if thing == 'all' else f'{verb}s {thing} (asks your password)'
        return said + (' and runs the smoke test' if 'smoke.py' in line else '')
    if ' log' in line and line.startswith('git'):
        return 'shows the commits to review (changes nothing)'
    if line.startswith('grep '):
        return 'shows the setting as it stands (changes nothing)'
    if 'judge.py seal' in line:
        return 'reseals the spine with your key'
    if 'git commit' in line:
        return 'commits the change on main'
    if 'take_in takein' in line:
        return 'takes the hot fix tree into main'
    if 'hotfix.py' in line:
        return 'builds and walks the apps'
    own = re.search(r'agent\.agent(\d{3})_', line)
    return f'runs row {own.group(1)}\'s own step' if own else f'runs {line.split("&&")[-1].strip()}'


FILLER = re.compile(r'^(?:(?:in a terminal|in ~/\S+(?: on \w+)?(?: "\w+",?)?|under \S+)\s*)*(?:run(?: your own)?\s+)?', re.I)
DOES = re.compile(r'(^|\band )(un)?(lock|run|show|reseal|commit|take|build)s\b')
LOOSE_END = ('that', 'its', 'the', 'and', 'to', 'in', 'of', 'on', 'a', 'with', 'for')   # a cut title never ends on one


def _title(text):
    """a short plain title: the first step, its filler gone; a step that is only a line says what the line does"""
    text = FILLER.sub('', text.strip())
    cut = re.search(r'[,;]\s|\.\s|\bthen\b|\(', SPAN.sub(lambda m: '_' * len(m.group(0)), text))   # never inside a line
    first = (text[:cut.start()] if cut else text).strip(' .:')
    if first.startswith('`') and SPAN.match(first):
        first = re.sub(r'\s*\([^)]*\)', '', _does(SPAN.match(first).group(1)))
        first = DOES.sub(lambda m: m.group(1) + (m.group(2) or '') + m.group(3), first)   # what it does -> do it
    first = re.sub(PLACE, lambda m: os.path.basename(m.group(1)), SPAN.sub(lambda m: m.group(1), first))
    if len(first) > 64:
        first = first[:64].rsplit(' ', 1)[0]
        while first.rsplit(' ', 1)[-1].lower() in LOOSE_END and ' ' in first:
            first = first.rsplit(' ', 1)[0]
    return first[:1].upper() + first[1:]


HAND = 'YOUR 3 MIN: '   # THE 3 MINUTE RULE (the owner 2026-10-23, shared_chunks): a red's first part is his step; the red itself follows


def _bare(w):
    """a row's words without his step in front (shared_chunks.HAND), so two reds compare as reds"""
    w = str(w or '')
    return w.split(' · ', 1)[1] if w.startswith(HAND) and ' · ' in w else '' if w.startswith(HAND) else w


def spent(row, rec, day=None, st=None):
    """THE LOOP'S WORD IS FOR ITS OWN RED, NEVER A LATER ONE (row 006, 2026-10-23 22:47: the morning's "lock scrum_master"
    step came back on a red of the same first words and another cause). Once the row went green after the record ended,
    that red is over; a later red is a new red with a cause of its own, so the row's own step stands. -> True when the
    row had a green run after the record (its day's runs); False when it did not, or nothing can be read."""
    ended = str(rec.get('ended') or rec.get('at') or '')
    if not ended:
        return False
    try:
        when = datetime.datetime.fromisoformat(ended)
        when = when if when.tzinfo else when.replace(tzinfo=schedule.ZONE)
        for r in (st or store.door()).runs(row=int(row), day=str(day or schedule.cycle())):
            if r.get('state') != 'green' or not r.get('started'):
                continue
            at = datetime.datetime.fromisoformat(str(r['started']))
            if (at if at.tzinfo else at.replace(tzinfo=schedule.ZONE)) > when:
                return True
    except (OSError, ValueError, TypeError, AttributeError):
        return False
    return False


def _same_red(then, now):
    """the loop's word still about this red: the row's first part (his step in front aside), its numbers and times aside.
    A first part cut by the step's length (shared_chunks._fit: "FA…" one round, "FAI…" the next, when the step changed by
    a letter) is the same red as far as both go (2026-10-24 07:59: row 032's fixer word dropped as "for an earlier red")."""
    first = lambda w: re.sub(r'\d+', '#', _bare(w).split(' · ')[0]).strip()
    a, b = first(then), first(now)
    if a.endswith('…') or b.endswith('…'):
        n = min(len(a.rstrip('…')), len(b.rstrip('…')))
        return n >= 40 and a[:n] == b[:n]
    return a == b


def hands(st, day=None, top=None, names=None):
    """ANYTHING THAT NEEDS THE OWNER, in page order: one per red row of the day that only his hands clear.
    -> [{'row': 'NNN', 'title', 'commands': [line], 'summary', 'text', 'stale': False}]. The loop's word said for an
    EARLIER red of the row (its words then not its words now, or spent by a green since) is never shown (the owner
    2026-10-23 23:27, on row 032's 08:07 box: "it has a prompt that would never fix this so it should not be there"):
    the row's own words stand if they carry his line, else the row has no box."""
    day = str(day or schedule.cycle())
    if names is None:
        with open(where.ROWS_FILE, encoding='utf-8') as fh:
            names = {int(r['n']): r['name'] for r in json.load(fh)['rows']}
    top = top or os.path.dirname(os.path.dirname(st.log_path(FOLDER, day, 'x')))
    runs = st.latest_runs(since=schedule.began(day).isoformat(timespec='seconds'))
    out = []
    for n, run in sorted(runs.items()):
        if run.get('state') != 'red' or n not in names:
            continue
        now, rec = str(run.get('text') or ''), read(n, day, top) or {}
        stale = False
        if rec.get('state') == 'owner' and rec.get('said') and _same_red(rec.get('words'), now) and not spent(n, rec, day, st):
            text = str(rec['said'])
        elif OWNER_ROW.search(now):   # the loop's word is for an earlier red, or there is none: the row's own words, when they carry his line
            text = now
        else:
            continue
        lines = [c for c in commands(text, now, str(rec.get('ended') or day)[:10]) if HIS_ALONE.search(c)]
        if not lines:   # ONLY WHAT HE ALONE CAN DO (the owner 2026-10-23: "the copy commands are only ones you absolutely need me to do otherwise you do it yourself"): a line that only shows (git log, grep) is the session's to read, never his box
            continue
        said = '; '.join(dict.fromkeys(_does(c) for c in lines))
        summary = (said[:1].upper() + said[1:] + '. ' if lines else 'No line to type: the steps below are by hand. ')
        summary += (f"Once its other steps (in the text) are done too, row {n:03d} {names[n]} turns green at its next look."
                    if lines and BY_HAND.search(SPAN.sub(' ', text)) else f"Then row {n:03d} {names[n]} turns green at its next look.")
        out.append({'row': f'{n:03d}', 'title': _title(OWNER_ROW.search(text).group(1) if text is now else text),
                    'commands': lines, 'summary': summary, 'text': text, 'stale': stale})
    return out


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'fix':
        fix(int(sys.argv[2]), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        sys.exit('usage: python -m agent.shared_red_rows fix <NNN> <day> [folder]')
