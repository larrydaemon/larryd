"""HOW AN A GETS IN (the owner's spec 2026-10-21, BUILD ITEMS A AND B, section 3): ONE INBOX outside sanity,
~/scratch/requests/inbox.jsonl (append only, one JSON object a line; $SCRUM_MASTER_INBOX for a check's own). Sessions
cannot write his database (the sandbox denies ~/virtual_sanity), so every request comes through here and only his
round turns the inbox into rows.

    run request "<his exact words>"      (agent/run; python -m agent.shared_requests request "<words>")
        one line {"kind": "request", "words", "asked_at", "session", "cwd", "source": "session"} appended in one write
        (O_APPEND), "recorded: next round takes it in", exit 0. It never opens his database.
    intake(st)                           (the round, before the rows: agent001 round_)
        the inbox read from the offset kept in settings (inbox_offset); each "request" line one row of requests
        (st.request_add: hash unique, a line taken twice writes nothing, state asked, position next); each "heard" line
        (the UserPromptSubmit hook, ~/.claude/hooks/requests_heard.py) kept on the day's heard list (settings
        requests.heard.<YYYYMMDD>), never a request; then the new offset kept. Twice in a row: nothing the second time.
    seed(st)                             (once, at the switch, section 3.5): O-1 -> R-0001; S-04, S-05, S-01, S-07, S-08
        -> R-0002 .. R-0006, their words as his settings.json keeps them. A seed already made writes nothing.
"""
import datetime
import json
import os
import sys

INBOX = os.path.abspath(os.path.expanduser(os.environ.get('SCRUM_MASTER_INBOX') or '~/scratch/requests/inbox.jsonl'))
OFFSET = 'inbox_offset'   # THE ROUND'S PLACE IN THE INBOX (spec 3.4), a row of settings: the bytes taken in so far
HEARD = 'requests.heard.'   # + YYYYMMDD: THE DAY'S HEARD LIST (spec 3.4), a row of settings: what a session heard, never a request
SAID = 'recorded: next round takes it in'
SEED_SPRINT = ('S-04', 'S-05', 'S-01', 'S-07', 'S-08')   # THE ACCEPTED SPRINT ITEMS IN THE OWNER'S ORDER (spec 3.5)
SEED_ORDER = 'O-1'


def now():
    """Now, local, ISO with its offset, to the second."""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec='seconds')


def append(line, inbox=None):
    """ONE LINE ADDED TO THE INBOX, WHOLE: one JSON object and its newline in ONE write on a file opened O_APPEND (two
    writers never mix their bytes), never through a link. -> the inbox's path"""
    path = os.path.abspath(inbox or INBOX)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = (json.dumps(line, ensure_ascii=False) + '\n').encode('utf-8')
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        if os.write(fd, data) != len(data):
            raise OSError('the inbox took part of the line')
    finally:
        os.close(fd)
    return path


def request_line(words, session=None, cwd=None, asked_at=None):
    """The line `run request` appends (spec 3.1)."""
    return {'kind': 'request', 'words': words, 'asked_at': asked_at or now(), 'session': session, 'cwd': cwd, 'source': 'session'}


def record(argv, inbox=None, env=None, out=print):
    """`run request "<words>"`: his words appended as one request line. -> exit code (0 recorded, 2 no words)"""
    env = os.environ if env is None else env
    words = ' '.join(argv) if len(argv) > 1 else (argv[0] if argv else '')
    if not words.strip():
        out('run request "<his exact words>"')
        return 2
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = env.get('PWD')
    append(request_line(words, env.get('CLAUDE_SESSION_ID') or None, env.get('RUN_REQUEST_CWD') or cwd), inbox)
    out(SAID)
    return 0


def _lines(path, offset):
    """The whole lines of the inbox after `offset` (a line not yet ended is left for the next round). A file shorter
    than the offset (made again) is read from its start. -> ([(line bytes)], new offset)"""
    try:
        with open(path, 'rb') as fh:
            size = os.fstat(fh.fileno()).st_size
            offset = offset if 0 <= offset <= size else 0
            fh.seek(offset)
            data = fh.read()
    except FileNotFoundError:
        return [], 0
    end = data.rfind(b'\n') + 1
    return data[:end].splitlines(), offset + end


def intake(st, inbox=None, day_of=None):
    """THE ROUND'S INTAKE (spec 3.4). -> {'requests': [new ids], 'heard': n new heard lines, 'skipped': n unreadable,
    'offset': the new offset}"""
    kept = st.settings_kept()
    try:
        offset = int(kept.get(OFFSET) or 0)
    except (TypeError, ValueError):
        offset = 0
    lines, new_offset = _lines(inbox or INBOX, offset)
    made, heard, skipped = [], {}, 0
    for raw in lines:
        try:
            got = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            skipped += 1
            continue
        if not isinstance(got, dict) or not isinstance(got.get('words'), str) or not got['words'].strip() or not _iso(got.get('asked_at')):
            skipped += 1
            continue
        if got.get('kind') == 'request':
            rid = st.request_add(got['words'], 'session', got.get('session') or None, got['asked_at'])
            if rid:
                made.append(rid)
        elif got.get('kind') == 'heard':
            one = {k: got.get(k) for k in ('words', 'asked_at', 'session', 'cwd')}
            heard.setdefault((day_of or _day)(got['asked_at']), []).append(one)
        else:
            skipped += 1
    added = 0
    for day, new in sorted(heard.items()):
        name = HEARD + day
        have = list(kept.get(name) or [])
        seen = {(h.get('asked_at'), h.get('session'), h.get('words')) for h in have if isinstance(h, dict)}
        fresh = [h for h in new if (h['asked_at'], h['session'], h['words']) not in seen]
        if fresh:
            st.setting(name, have + fresh)
            added += len(fresh)
    if new_offset != offset:
        st.setting(OFFSET, new_offset)
    return {'requests': made, 'heard': added, 'skipped': skipped, 'offset': new_offset}


def heard(st, day=None):
    """The day's heard list (YYYY-MM-DD, today by default). -> [{words, asked_at, session, cwd}]"""
    day = (day or now()[:10]).replace('-', '')
    return list(st.settings_kept().get(HEARD + day) or [])


def _iso(text):
    try:
        datetime.datetime.fromisoformat(str(text))
        return True
    except ValueError:
        return False


def _day(asked_at):
    """The day a line was asked, as the heard list's name keeps it: YYYYMMDD."""
    return str(asked_at)[:10].replace('-', '')


def seed(st, settings=None, at=None):
    """THE SEED (spec 3.5), once: O-1 -> R-0001 (source order, ref O-1, its words: the order's own "said" in his
    settings.json orders), then S-04, S-05, S-01, S-07, S-08 (source sprint, ref the S id, words: the item's "said") ->
    R-0002 .. R-0006, all asked at one moment, positions 1..6 by that order. Refused when requests already holds a
    row (a seed is the first six, never later ones). -> [the ids made]"""
    if st.requests():
        raise RuntimeError('requests holds rows already: the seed is made once, first')
    if settings is None:
        from . import shared_where as where
        with open(where.SETTINGS_FILE, encoding='utf-8') as fh:
            settings = json.load(fh)
    order = next(o for o in settings['orders'] if o['id'] == SEED_ORDER)
    sprint = {i['id']: i for i in settings['sprint']['items']}
    at = at or now()
    made = [st.request_add(order['said'], 'order', SEED_ORDER, at)]
    for sid in SEED_SPRINT:
        made.append(st.request_add(sprint[sid]['said'], 'sprint', sid, at))
    return made


DONE_WHY = 'a Scrum Master fix, done outside the build: '
DONE_STATE = 'green'   # his table's states have no "done" (schemas: requests.state CHECK); green is its closed state, and the why says how
CLOSED = ('green', 'shipped')   # a request already closed: refused


def done(argv, st=None, out=print):
    """THE CLOSE DOOR (the owner 2026-10-23: "a Scrum Master fix is done at once, never queued"): a request that was a fix of
    the Scrum Master's own page, built outside the build, closed honestly. `done <R-id> -- <words>`: its state done, why
    "a Scrum Master fix, done outside the build: <words>", done_at now, through the store's own request_state. Its state is
    green (DONE_STATE: the table's states have no "done"; a green with no commits is never shipped by the night). An unknown
    id, one already closed (green or shipped), or no words is refused. -> exit code (0 closed, 2 refused)"""
    usage = 'python -m agent.shared_requests done <R-id> -- <words>'
    if len(argv) < 3 or argv[1] != '--' or not ' '.join(argv[2:]).strip():
        out(usage)
        return 2
    rid, words = argv[0].strip(), ' '.join(argv[2:]).strip()
    if st is None:
        from agent import shared_store as his_store
        st = his_store.door()
    got = st.request(rid)
    if got is None:
        out(f'refused: no request {rid}')
        return 2
    proven = str(got.get('why') or '').startswith(('shipped by itself: ', 'in sync on ')) or str(got.get('state') or '') == 'green'   # a shipped request with no proof of its own may be closed with one (frost-c5 2026-10-24)
    if str(got.get('state') or '') in CLOSED and proven:
        out(f'refused: {rid} is done already ({got.get("state")} since {got.get("done_at") or got.get("state_at")})')
        return 2
    at = now()
    if not st.request_state(rid, DONE_STATE, why=DONE_WHY + words, at=at, done_at=at):
        out(f'refused: {rid} was not changed')
        return 2
    out(f'{rid} done: {DONE_WHY}{words}')
    return 0



BACK_STATE, BACK_WHY = 'asked', 'sent back to the builder by the owner: '   # THE SEND BACK (the owner 2026-10-25: "can it be fixed in 3 min or not"): the request goes to the builder again, nothing lost


def back(argv, st=None, out=print):
    """THE SEND BACK DOOR (the owner 2026-10-25): a request whose build failed, whose proof is missing or whose read refused
    goes back to the builder in one step: `back <R-id> -- <words>`, its state asked again, why "sent back to the builder by
    the owner: <words>", through the store's own request_state; the worker builds it again (rows 005 and 007 watch that).
    An unknown id, one already done (green or shipped), or no words is refused. -> exit code (0 sent back, 2 refused)"""
    usage = 'python -m agent.shared_requests back <R-id> -- <words>'
    if len(argv) < 3 or argv[1] != '--' or not ' '.join(argv[2:]).strip():
        out(usage)
        return 2
    rid, words = argv[0].strip(), ' '.join(argv[2:]).strip()
    if st is None:
        from agent import shared_store as his_store
        st = his_store.door()
    got = st.request(rid)
    if got is None:
        out(f'refused: no request {rid}')
        return 2
    if str(got.get('state') or '') in ('green', 'shipped'):
        out(f'refused: {rid} is done already ({got.get("state")})')
        return 2
    if not st.request_state(rid, BACK_STATE, why=BACK_WHY + words, at=now()):
        out(f'refused: {rid} was not changed')
        return 2
    for b in st.build_items(request_id=rid, state='building'):   # its build items go back with it: the builder takes them again, never left building on a failed turn
        st.build_item_state(b['id'], 'open', at=now())
    out(f'{rid} sent back to the builder: {words}')
    return 0


def back_line(ids):
    """HIS ONE STEP for a build, a proof or a read that failed: each request sent back, one line (seconds)."""
    return '; '.join(f'cd ~/virtual_sanity/scrum_master_3/release/app && PYTHONPATH=. WID_ENV=localhost.rnd ~/virtual_workspace/.venv/bin/python -m agent.shared_requests back {rid} -- "<what to fix>"' for rid in ids)


# ---------------------------------------------------------------- GREEN AFTER THE NIGHT (spec 4; the owner 2026-10-21 23:40)

def _in_main(commit, built, workspace):
    """is this commit inside the commit the nightly built (an ancestor of it, or it)"""
    import subprocess
    got = subprocess.run(['git', '-C', workspace, 'merge-base', '--is-ancestor', commit, built], capture_output=True, text=True, timeout=30)
    return got.returncode == 0


def nightly_green(st, top=None, workspace=None, make=None, now=None):
    """A REQUEST GOES GREEN FROM THE GATE (the owner's order 2026-10-22, N5): each request taken in whose commits are all
    inside the night's commit (shared_night: the newest night, measured, begun after it was taken in) goes green only
    when the night's gate passed: step12 (THE JUDGE, this run's own report, agreeing with the rows it printed), THE LOOK,
    and step13 to step18 on localhost pf. Before that, the B rule reads the night (shared_build_items.make, N6: a NEW
    failure naming a file its commits touched is a B under it; the smoke test's, the day's, read by row 021). Its proof:
    the run id, the commit, its commits. top: the tower's reports folder (a check's own). -> the ids made green"""
    from agent import shared_build_items as build_items
    from agent import shared_night as night
    from agent import shared_where as where
    if top is None and make is None:   # THE ROUND'S OWN CALL (a check's stand-in passes top or make): a request in main is measured NOW, never held for the night
        start_green_now(st, workspace)
    n = night.night(top, now=now)
    if not n or not n['measured'] or not n.get('commit'):
        return []
    began = datetime.datetime.fromisoformat(n['started']) if n['started'] else None
    workspace = workspace or where.WORKSPACE
    waiting = [r for r in st.requests(state='taken_in') if build_items.commits_of(r)]
    if not waiting or began is None:
        return []
    (make or build_items.make)(st, nightly_dir=n['folder'])   # the night's new failures tied to a request's own files become its B items first (N6)
    g = night.gate(n)
    if not g['ok']:
        return []
    report = os.path.basename(g['judge']['path'])
    made = []
    for r in waiting:
        try:
            taken = datetime.datetime.fromisoformat(str(r.get('state_at')))
        except ValueError:
            continue
        commits = build_items.commits_of(r)
        if began < taken or not all(_in_main(c, n['commit'], workspace) for c in commits):
            continue
        st.request_state(r['id'], 'green', why=f"the nightly {n['run']} built {n['commit'][:12]} with its commits {', '.join(c[:12] for c in commits)}: step12 THE JUDGE passed (its own report {report} agrees with its printed rows), THE LOOK passed, step13 to step18 on localhost pf passed", done_at=now_iso())
        made.append(r['id'])
    return made


def shipped(st, n, workspace=None):
    """SHIPPED FROM ROW 028 IN SYNC (item 6; N7, N8): when this laptop, slot B's rnd side and both apps are on the night's
    commit, each request green whose commits are all inside it is shipped. n: the night (shared_night.night()).
    -> the ids made shipped"""
    from agent import shared_build_items as build_items
    from agent import shared_where as where
    if not n or not n.get('commit'):
        return []
    workspace = workspace or where.WORKSPACE
    made = []
    for r in st.requests(state='green'):
        commits = build_items.commits_of(r)
        if commits and all(_in_main(c, n['commit'], workspace) for c in commits):
            st.request_state(r['id'], 'shipped', why=f"in sync on {n['commit'][:12]} (the nightly {n['run']}): localhost pf, slot B rnd and both apps", done_at=r.get('done_at'))
            made.append(r['id'])
    return made


def now_iso():
    return now()


# ---------------------------------------------------------------- GREEN NOW (the owner 2026-10-23: "NOTHING WAITS FOR A LATER PROCESS TO CLEAR")
# A request taken into main never waits for the night to go green: the moment its commits are all on main and the
# workspace is main as it stands (HEAD on main, nothing uncommitted), its OWN frozen tests (tests_sha unchanged: never
# a test moved after the freeze) run on that tree, in the box, as the Developer runs them; passed is green now, said
# with its proof (the main commit, its commits). A red stays red: a request whose tests fail is tried again only when
# main moves or its tests do. The round never waits on it: one detached process (green-now), one at a time.
NOW_PROOF = 'its own tests passed now on main'   # the why's words (agent006 built: a green made now, its proof)
NOW_FILE, NOW_PID = 'green_now.json', 'green_now.pid'   # under his logs' requests/: what was tried at which main, and the one running


def _now_dir():
    from agent import shared_store as his_store
    folder = os.path.join(his_store.LOGS, 'requests')
    os.makedirs(folder, exist_ok=True)
    return folder


def _now_tried():
    try:
        with open(os.path.join(_now_dir(), NOW_FILE), encoding='utf-8') as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def _git(workspace, *args):
    import subprocess
    return subprocess.run(['git', '-C', workspace, *args], capture_output=True, text=True, timeout=60)


def _main_now(workspace):
    """main's commit when the workspace IS main (HEAD on main, no tracked file changed), else None and why. -> (commit, why)"""
    head, main = _git(workspace, 'rev-parse', 'HEAD').stdout.strip(), _git(workspace, 'rev-parse', 'main').stdout.strip()
    if not main or head != main:
        return None, 'the workspace is not on main as it stands'
    if _git(workspace, 'status', '--porcelain', '--untracked-files=no').stdout.strip():
        return None, 'the workspace has changes not committed'
    return main, ''


def _now_due(st, workspace):
    """The requests taken in whose commits are all on main and that were not yet measured at this main with these
    tests. -> (main, [(request, key)], why)"""
    from agent import shared_build_items as build_items
    from agent import shared_developer as dev
    main, why = _main_now(workspace)
    if not main:
        return None, [], why
    tried, due = _now_tried(), []
    for r in st.requests(state='taken_in'):
        commits = build_items.commits_of(r)
        if not commits or not r.get('tests') or not r.get('tests_sha'):
            continue
        key = f"{main} {dev.tests_sha(r['tests'])}"
        if (tried.get(r['id']) or {}).get('key') != key and all(_in_main(c, main, workspace) for c in commits):
            due.append((r, key))
    return main, due, ''


def _alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def start_green_now(st, workspace=None, spawn=None):
    """From the round: start the one green-now process when a request in main is due and none runs. Never waited for.
    -> True when one was started"""
    import subprocess
    from agent import shared_where as where
    workspace = workspace or where.WORKSPACE
    pid_file = os.path.join(_now_dir(), NOW_PID)
    try:
        with open(pid_file, encoding='utf-8') as fh:
            if _alive(fh.read().strip()):
                return False
    except OSError:
        pass
    if not _now_due(st, workspace)[1]:
        return False
    app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    child = (spawn or subprocess.Popen)([sys.executable, '-m', 'agent.shared_requests', 'green-now'], cwd=app, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
                                        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    with open(pid_file, 'w', encoding='utf-8') as fh:
        fh.write(str(getattr(child, 'pid', '')))
    return True


def green_now(st, workspace=None, run=None):
    """EACH REQUEST IN MAIN MEASURED NOW: its own frozen tests on main; passed is green at once, failed stays taken in
    (tried again when main or its tests move), its tests moved since the freeze is never green. -> [(id, word)]"""
    from agent import shared_build_items as build_items
    from agent import shared_developer as dev
    from agent import shared_where as where
    workspace = workspace or where.WORKSPACE
    main, due, why = _now_due(st, workspace)
    if not main:
        return [('-', f'not measured: {why}')]
    tried, out = _now_tried(), []
    for r, key in due:
        fresh = st.request(r['id']) or {}
        if fresh.get('state') != 'taken_in':
            continue
        commits = build_items.commits_of(fresh)
        if dev.tests_sha(fresh['tests']) != fresh.get('tests_sha'):
            word = 'not measured: its tests moved since the freeze (never green)'
        else:
            ok, said = (run or dev.run_tests)(fresh, workspace)
            if ok and _main_now(workspace)[0] == main:   # main did not move under the run
                st.request_state(r['id'], 'green', why=f"{NOW_PROOF} {main[:12]} with its commits {', '.join(c[:12] for c in commits)}: measured the moment it was in main, never waiting for the night (the owner 2026-10-23)", done_at=now_iso())
                word = 'green'
            else:
                word = 'red: its own tests on main: ' + ' '.join(str(said).split())[-300:] if not ok else 'main moved under the run: measured again'
                key = key if ok is False else ''
        tried[r['id']] = {'key': key, 'word': word, 'at': now_iso()}
        out.append((r['id'], word))
    with open(os.path.join(_now_dir(), NOW_FILE), 'w', encoding='utf-8') as fh:
        json.dump(tried, fh, ensure_ascii=False, indent=1)
    return out


def green_now_main():
    """`python -m agent.shared_requests green-now`: the one process; its words one line a request. -> the list or None"""
    from agent import shared_store as his_store
    try:
        got = green_now(his_store.door())
    except Exception as e:   # noqa: BLE001  (said, red)
        print(f'green now broke: {type(e).__name__}: {e}', flush=True)
        return None
    finally:
        try:
            os.remove(os.path.join(_now_dir(), NOW_PID))
        except OSError:
            pass
    for rid, word in got:
        print(f'{now_iso()} · green now · {rid} · {word}', flush=True)
    return got


if __name__ == '__main__':
    if sys.argv[1:2] == ['request']:
        sys.exit(record(sys.argv[2:]))
    if sys.argv[1:2] == ['done']:
        sys.exit(done(sys.argv[2:]))
    if sys.argv[1:2] == ['back']:
        sys.exit(back(sys.argv[2:]))
    if sys.argv[1:2] == ['green-now']:
        sys.exit(0 if green_now_main() is not None else 1)
    print('python -m agent.shared_requests request "<his exact words>"')
    print('python -m agent.shared_requests done <R-id> -- <words>')
    print('python -m agent.shared_requests back <R-id> -- <words>')
    print('python -m agent.shared_requests green-now')
    sys.exit(2)
