"""THE B RULE (the owner's spec 2026-10-21, BUILD ITEMS A AND B, section 5.1): a build item (B) is written under its
parent request (A) ONLY when the relation is a file or a test, never a judgement:
    test      a test in the A's own tests folder fails                (given by the Developer: tests={rid: [(test, line)]})
    takein    the hired read REFUSEs the A's diff                     (given by the Developer: reads={rid: verdict line})
    takein    the take-in refuses the A's branch                      (its own lines, the day's job log TAKE IN THE DAY'S WORK)
    judge     a Judge rule FAILs and its evidence names a file the A's commits touched     (reports.json judge)
    smoke     a smoke rule FAILs and its evidence names a file the A's commits touched     (reports.json smoke)
    look      the nightly's look step fails on a file the A's commits touched              (nightly result.json + REPORT.md)
    native    a nightly native step (write the apps, a native build or walk) fails on a touched file
    security  a security finding (findings, open) names a file the A's commits touched
"The A's commits touched" = git show --name-only of each commit in requests.commits (the workspace's git, read only).
Anything else is NOT a B: it is returned in `not_a_request` (row 021 THE GATE lists it once) and never worked.
THE SAME RULE + EVIDENCE + REQUEST NEVER WRITES TWICE (any state, closed too). A report older than its max_age
(schemas/reports.json) makes no B: it is said "not measured" (R1). Writes go only through shared_store's door
(st.build_item_add); this file reads reports and git, and changes nothing else.

    make(st=None, **sources)        -> {'made': [B ids], 'kept': [B ids already there], 'not_a_request': [...], 'said': [...]}
    from_tests(rid, failures)       the Developer: an A's own tests failed -> [B ids]
    from_read(rid, verdict_line)    the Developer: the hired read's verdict on an A's diff -> [B ids] (CLEAN: [])
    open_items(rid)                 the Developer's reader: the open B items of an A (state not closed), by id
    gate(st=None, ...)              row 021's facts: the Judge's and the smoke test's verdicts, each FAIL with its B ids
    python -m agent.shared_build_items make      one pass over every source, printed"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys

from . import shared_memory as memory   # the one lesson door: a B closed leaves its lesson (row 023 SELF HEALING)
from . import shared_night as night   # the night's own files: its failures, new or already there (N6)
from . import shared_schedule as schedule
from . import shared_store as store
from . import shared_where as where

FOUND_BY = ('test', 'judge', 'smoke', 'security', 'takein', 'look', 'native')   # build_items.found_by (instance/scrum_master.json)
READ_RULE = 'the read'          # spec 5.1: "rule = the read, evidence = its reason line"
TAKEIN_RULE = 'the take-in'     # spec 5.1: "rule = the take-in, evidence = its line"
TAKEIN_JOB = "TAKE IN THE DAY'S WORK"   # the daily schedule's job (agent018 JOB); its lines are its job log
NIGHTLY_MEMBER = 'nightly'      # result.json "member" of the nightly chain run (the 01:00 build), not a button press
CLOSED = 'closed'
LOOK_STEPS = ('look',)          # result.json step names of the nightly's look
NATIVE_STEPS = ('native_', 'hot_fix_utility')   # write the apps (native_generate), native builds (native_iphone, native_macos), walks (native_test_*), both apps built and walked (hot_fix_utility)


# ---- reading ------------------------------------------------------------------------------------------------------
def _max_age(name):
    """A report's max_age in hours, from the manifest (schemas/reports.json), or None."""
    for e in where.REPORTS_BOOK.get('reports', []):
        if e.get('name') == name:
            return e.get('max_age')
    return None


def _moment(text):
    try:
        m = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return m if m.tzinfo else m.replace(tzinfo=datetime.timezone.utc)


def _now(now=None):
    return now or datetime.datetime.now(datetime.timezone.utc)


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def report(name, path=None, now=None):
    """THE JUDGE'S OR THE SMOKE TEST'S OWN REPORT, read where it is. -> {'name', 'path', 'report' (dict or None),
    'when' (aware datetime or None), 'measured' (False: missing, unreadable, no time, or older than its max_age),
    'why' (one line when not measured)}"""
    path = path or where.report(name)
    got = _json(path)
    out = {'name': name, 'path': path, 'report': got if isinstance(got, dict) else None, 'when': None, 'measured': False, 'why': ''}
    if out['report'] is None:
        out['why'] = 'no report to read' if not os.path.exists(path) else 'its report is not readable'
        return out
    when = _moment(out['report'].get('when') or out['report'].get('finished') or out['report'].get('started'))   # the Judge's and smoke's 'when'; a nightly run's own end (or start)
    if when is None:
        try:
            when = datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc)
        except OSError:
            when = None
    out['when'] = when
    age = _max_age(name) if name in ('judge', 'smoke') else _max_age('nightly_result')
    if when is None:
        out['why'] = 'its report says no time'
    elif age is not None and (_now(now) - when).total_seconds() / 3600 > float(age):
        out['why'] = f'its report is from {schedule._when(when.isoformat())}, older than {age} h'
    else:
        out['measured'] = True
    return out


def failures(rep):
    """A report's FAIL rules: [(rule, [evidence lines])] (INFO and PASS are not failures)."""
    rules = (rep or {}).get('rules') or []
    return [(str(r.get('rule') or ''), [store.one_line(str(e)) for e in (r.get('evidence') or []) if str(e).strip()])
            for r in rules if isinstance(r, dict) and r.get('status') == 'FAIL']


def nightly_run(top=None):
    """THE NEWEST NIGHTLY RUN FOLDER (<stamp>_<chain>, its result.json member 'nightly'). -> folder or None"""
    top = top or os.path.dirname(os.path.dirname(where.REPORTS['nightly_result']))   # ~/spine_scratch/tower_auto
    for folder in sorted(glob.glob(os.path.join(top, '*_*')), reverse=True):
        got = _json(os.path.join(folder, 'result.json'))
        if isinstance(got, dict) and got.get('member') == NIGHTLY_MEMBER:
            return folder
    return None


def _step_kind(step):
    if step in LOOK_STEPS:
        return 'look'
    if any(step == p or (p.endswith('_') and step.startswith(p)) for p in NATIVE_STEPS):
        return 'native'
    return None


def nightly_failures(folder):
    """THE NIGHTLY'S FAILED STEPS: [(found_by look|native|None, step, [evidence lines])]: each failed step's own why,
    and the REPORT.md NOT DONE lines that name it (its title). A step of another kind is found_by None (never a B)."""
    got = _json(os.path.join(folder, 'result.json')) if folder else None
    if not isinstance(got, dict):
        return []
    try:
        with open(os.path.join(folder, 'REPORT.md'), encoding='utf-8') as fh:
            text = fh.read()
    except OSError:
        text = ''
    not_done = []
    if '## NOT DONE' in text:
        for line in text.split('## NOT DONE', 1)[1].splitlines():
            if line.startswith('## '):
                break
            if line.startswith('- ') and line[2:].strip() != 'none':
                not_done.append(store.one_line(line[2:]))
    out = []
    for s in got.get('steps') or []:
        if not isinstance(s, dict) or s.get('ok') is not False:
            continue
        step = str(s.get('step') or '')
        lines = [store.one_line(str(s['why']))] if s.get('why') else []
        lines += [l for l in not_done if str(s.get('why') or '\0') in l and l not in lines]
        out.append((_step_kind(step), step, lines))
    return out


def takein_lines(path=None, day=None):
    """THE TAKE-IN'S OWN REFUSALS of the day: its job log's lines '<branch> REFUSED...' and '<branch> does not fit
    main...'. -> [(branch, line)]"""
    if path is None:
        path = where.report('job_logs', day or schedule.cycle(), schedule._step(TAKEIN_JOB) + '.log')
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        head, _, rest = line.strip().partition(' ')
        if head.startswith('hotfix/') and (rest.startswith('REFUSED') or rest.startswith('does not fit main')):
            out.append((head, store.one_line(line)))
    return out


# ---- git (read only) -------------------------------------------------------------------------------------------------
def _git_at(root):
    return lambda *a: subprocess.run(['git', '-C', root, *a], capture_output=True, text=True, timeout=60)


def commits_of(req):
    try:
        got = json.loads(req.get('commits') or '[]')
    except ValueError:
        return []
    return [str(c) for c in got if isinstance(c, str) and re.fullmatch(r'[0-9a-fA-F]{7,64}', c)] if isinstance(got, list) else []


def touched(req, git):
    """THE FILES AN A'S COMMITS TOUCHED: git show --name-only of each commit in requests.commits. -> set of paths"""
    files = set()
    for c in commits_of(req):
        done = git('show', '--name-only', '--no-renames', '--format=', c)
        if done.returncode == 0:
            files.update(p.strip() for p in done.stdout.splitlines() if p.strip())
    return files


TOKEN = re.compile(r"[A-Za-z0-9_.~/\-]+")


def named_files(line, roots=()):
    """THE FILES A LINE NAMES: each path-like word, its ':<line>' and edge marks cut, a known root (the workspace, the
    hot fix tree) taken off the front. -> set of paths as git names them"""
    out = set()
    for tok in TOKEN.findall(line or ''):
        tok = os.path.expanduser(tok.rstrip('.-/'))
        for root in roots:
            root = root.rstrip('/') + '/'
            if tok.startswith(root):
                tok = tok[len(root):]
                break
        while tok.startswith('./'):
            tok = tok[2:]
        if '/' in tok or '.' in tok:
            out.add(tok)
    return out


def _roots():
    roots = [where.WORKSPACE]
    hot = os.path.expanduser('~/spine_worktrees/hotfix')   # the hot fix tree (spec section 1)
    roots.append(hot)
    return [os.path.realpath(r) for r in roots] + roots


# ---- writing --------------------------------------------------------------------------------------------------------
def _write(st, rid, found_by, rule, evidence, file, made, kept):
    """One B, unless the same rule + evidence + request is kept already (any state)."""
    rule, evidence, file = store.one_line(rule), store.one_line(evidence), store.one_line(file)
    for b in st.build_items(request_id=rid):
        if b['rule'] == rule and b['evidence'] == evidence:
            if b['id'] not in kept and b['id'] not in made:
                kept.append(b['id'])
            return b['id']
    bid = st.build_item_add(rid, found_by, rule, evidence, file=file or None)
    made.append(bid)
    return bid


def write_b(request_id, found_by, rule, evidence, file=None, st=None):
    """ONE B UNDER ITS A, from the Developer or the take-in (the hired read's REFUSE, the take-in's refusal, a failing
    test of the A's own): the same rule + evidence + request is never written twice. -> the B id"""
    st = st or store.door()
    return _write(st, request_id, found_by, rule, evidence, file, [], [])


def make(st=None, *, judge_path=None, smoke_path=None, nightly_dir=None, takein_log=None, day=None, reads=None, tests=None,
         security=True, git=None, now=None, requests=None, close=True):
    """ONE PASS OF THE B RULE over every source (section 5.1). judge_path, smoke_path: the reports (default: where
    reports.json names them); nightly_dir: one nightly run folder (default: the newest nightly); takein_log: the
    take-in's job log (default: the day's); reads {rid: verdict line}, tests {rid: [(test, line)]}: the Developer's;
    security: read open findings (False: not). git: fn(*args) on the workspace (a check's stand-in).
    -> {'made', 'kept', 'not_a_request': [{'found_by', 'rule', 'evidence'}], 'said': [one line a source not measured],
    'already': [{'found_by', 'rule', 'evidence', 'since'}: the night's failures the night before showed too, never a B]}"""
    st = st or store.door()
    git = git or _git_at(where.WORKSPACE)
    reqs = requests if requests is not None else st.requests()
    ids = {r['id'] for r in reqs}
    files = {r['id']: touched(r, git) for r in reqs}
    roots = _roots()
    made, kept, nar, said, already = [], [], [], [], []

    def tie(found_by, rule, lines):
        """A failure's lines against every A's touched files: a B for each line naming one; none: not a request."""
        hit = set()
        for line in lines or ['']:
            names = named_files(line, roots)
            for r in reqs:
                if r['id'] in hit:
                    continue   # ONE B A FAILURE AND A REQUEST: its first line that names a file the request touched
                for f in sorted(names & files[r['id']]):
                    _write(st, r['id'], found_by, rule, line, f, made, kept)
                    hit.add(r['id'])
                    break
        if not hit:
            nar.append({'found_by': found_by, 'rule': store.one_line(rule), 'evidence': store.one_line((lines or [''])[0])})

    # the Developer's: an A's own tests, the hired read of its diff
    for rid, fails in (tests or {}).items():
        if rid in ids:
            for test, line in fails:
                _write(st, rid, 'test', test, line or test, None, made, kept)
    for rid, line in (reads or {}).items():
        reason = read_refusal(line)
        if rid in ids and reason:
            _write(st, rid, 'takein', READ_RULE, reason, None, made, kept)

    # the Judge's and the smoke test's own reports: the Judge's of the NIGHT (this run's own report, read with the night
    # below, shared_night) unless a report is named here; the smoke test's, the day's (its daily run, row 021)
    for name, path in ((('judge', judge_path),) if judge_path else ()) + (('smoke', smoke_path),):
        rep = report(name, path, now)
        if not rep['measured']:
            said.append(f"{name}: not measured: {rep['why']}")
            continue
        day = schedule.cycle(rep['when']) if rep['when'] else None
        for rule, lines in failures(rep['report']):
            since = smoke_since(rule, day) if name == 'smoke' and day else ''
            if since:   # THE OWNER'S RULING 2026-10-22 00:23: an old failure is shown once, never a B
                already.append({'found_by': name, 'rule': store.one_line(rule), 'evidence': store.one_line((lines or [''])[0]), 'lines': [store.one_line(l) for l in lines], 'since': since})
            else:
                tie(name, rule, lines)

    # THE NIGHT (shared_night, N6; the owner's ruling 2026-10-22 00:23): only a NEW failure, one the night before did not
    # show (by step, Judge row, look page), is tied to a request's files; one already there is shown once, "already
    # failing since <night>", never a B. A red step whose kind build_items.found_by does not hold is never a B.
    n = night.night(run=nightly_dir, now=now) if nightly_dir else night.night(now=now)
    if n is None:
        said.append('nightly: not measured: no nightly run to read')
    elif not n['measured']:
        said.append(f"nightly: not measured: {n['why']}")
    else:
        if not judge_path and night.judge(n)['report'] is None:
            said.append(f"judge: not measured: {night.judge(n)['why']}")
        new, old = night.sorted_failures(n)
        for f in new:
            if f['found_by'] in FOUND_BY:
                tie(f['found_by'], f['rule'], f['lines'])
            else:
                nar.append({'found_by': 'nightly', 'rule': store.one_line(f['rule']), 'evidence': store.one_line((f['lines'] or [''])[0])})
        for f in old:
            already.append({'found_by': f['found_by'], 'rule': store.one_line(f['rule']), 'evidence': store.one_line((f['lines'] or [''])[0]), 'lines': [store.one_line(l) for l in f['lines']], 'since': f['since']})

    # the take-in's refusals of a branch holding an A's commits (not yet in main)
    for branch, line in takein_lines(takein_log, day):
        mine = [r for r in reqs if any(git('merge-base', '--is-ancestor', c, branch).returncode == 0
                                        and git('merge-base', '--is-ancestor', c, 'HEAD').returncode != 0 for c in commits_of(r))]
        for r in mine:
            _write(st, r['id'], 'takein', TAKEIN_RULE, line, None, made, kept)
        if not mine:
            nar.append({'found_by': 'takein', 'rule': TAKEIN_RULE, 'evidence': line})

    # the security findings that name a touched file
    if security:
        for f in st.findings(state='open'):
            line = f"{f['file']}:{f['line']}: {f['place']} ({f['severity']})"
            tie('security', f['place'], [line])
    closed = close_old(st, already) if close else []
    return {'made': made, 'kept': kept, 'not_a_request': nar, 'said': said, 'already': already, 'closed': closed}


SMOKE_JOB = 'SMOKE TEST'   # the daily schedule's smoke job: its log is the day's smoke run as the smoke test printed it
PRINTED_ROW = re.compile(r'^FAIL\s+(.*?)(\s{2}\([^()]*\))?$')


def smoke_days(before, most=14, path=None):
    """THE DAYS' SMOKE RUNS BEFORE A DAY, from the daily SMOKE TEST job's own logs (reports.json job_logs): newest first,
    [(day, {the FAIL rules it printed})]; a day with no log is passed over (no run that day). path: a check's own
    folder of days."""
    top = path or os.path.dirname(os.path.dirname(where.REPORTS['job_logs']))
    out = []
    try:
        days = sorted((d for d in os.listdir(top) if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d) and d < before), reverse=True)
    except OSError:
        return []
    for d in days:
        try:
            with open(os.path.join(top, d, schedule._step(SMOKE_JOB) + '.log'), encoding='utf-8', errors='replace') as fh:
                text = fh.read().splitlines()
        except OSError:
            continue
        out.append((d, {m.group(1).strip() for m in (PRINTED_ROW.match(l) for l in text) if m}))
        if len(out) >= most:
            break
    return out


def smoke_since(rule, day, path=None):
    """A smoke FAIL that the day before showed too: the first day of the unbroken line of days that failed it ('' : it
    is new)."""
    since = ''
    for d, fails in smoke_days(day, path=path):
        if store.one_line(rule) not in {store.one_line(f) for f in fails}:
            break
        since = d
    return since


def close_old(st, already):
    """THE OWNER'S RULING 2026-10-22 00:23 OVER THE OPEN B ITEMS: an open B whose failure is an old one (found_by, rule
    and evidence one of `already`) is closed through the store's own state change, its fact one line of build_turns:
    "closed: not a new failure: already failing since <day or night>". -> [B ids closed]"""
    out = []
    for b in st.build_items():
        if b['state'] != 'open':
            continue
        hit = next((a for a in already if a['found_by'] == b['found_by'] and a['rule'] == b['rule'] and b['evidence'] in [a['evidence']] + list(a.get('lines') or [])), None)
        if not hit:
            continue
        turns = st.build_turns(b['id'])
        fact = f"closed: not a new failure: {b['found_by']} {b['rule']} already failing since {hit['since']}"
        memory.close_b(st, b, turns, fact, by='the B closed as an old failure (close_old)')   # its turn, its state 'closed' and its lesson: one transaction
        out.append(b['id'])
    return out


TESTS_PASSED = ('proven', 'reviewed', 'waiting_takein', 'approved', 'taken_in', 'green', 'shipped')   # its own tests passed
READ_PASSED = ('reviewed', 'waiting_takein', 'approved', 'taken_in', 'green', 'shipped')               # the hired read said CLEAN
TAKEN_PASSED = ('taken_in', 'green', 'shipped')                                            # the take-in merged it
NIGHT_LINKS = ('judge', 'look', 'native')   # links of the night: passed by a later night that holds the request's commits


def _passed_by_state(b, req):
    """The link of a B passed by its request's own state, after the B: tests (test), the hired read (takein, the read),
    the take-in (takein, the take-in). -> the fact, or ''"""
    states = TESTS_PASSED if b['found_by'] == 'test' else TAKEN_PASSED if b['rule'] == TAKEIN_RULE else READ_PASSED if b['found_by'] == 'takein' else ()
    passed, made = _moment(req['state_at']), _moment(b.get('found_at') or b['state_at'])
    if req['state'] in states and passed and made and passed > made:
        link = 'its tests' if b['found_by'] == 'test' else 'the take-in' if b['rule'] == TAKEIN_RULE else 'the hired read'
        return f"{req['id']} passed {link}: {req['state']} since {req['state_at']}"
    return ''


def _passed_by_night(b, req, n, inside):
    """The link of a night B (judge, look, native) passed by a night begun after the B whose commit holds every commit
    of its request: the Judge (step12 and this run's own report), the look, or the very native step or walk that
    failed. -> the fact, or ''"""
    from agent import shared_night as night
    began, made = _moment((n or {}).get('started')), _moment(b.get('found_at') or b['state_at'])
    commits = commits_of(req)
    if not n or not n.get('measured') or not n.get('commit') or not began or not made or began <= made or not commits \
            or not all(inside(c, n['commit']) for c in commits):
        return ''
    if b['found_by'] == 'judge':
        here = night.steps_of(n, (night.JUDGE_STEP,), night.local_target())
        ok = bool(here) and all(s.get('ok') is True for s in here) and night.judge(n)['ok']
    elif b['found_by'] == 'look':
        here = night.steps_of(n, (night.LOOK_STEP,), night.local_target())
        ok = bool(here) and all(s.get('ok') is True and s.get('looked') is not False for s in here)
    else:
        here = night.steps_of(n, (b['rule'],))
        ok = bool(here) and all(s.get('ok') is True for s in here) and not any(f['rule'] == b['rule'] for f in night.failures(n))
    return f"{req['id']} passed {b['found_by']} ({b['rule']}) in the night {n['run']} at {n['commit'][:12]}" if ok else ''


def _passed_smoke(b, req, days):
    """A smoke B passed by a later day's smoke run that ran and no longer printed its rule. -> the fact, or ''"""
    made = _moment(b.get('found_at') or b['state_at'])
    if not days or not made:
        return ''
    d, fails = days[0]   # the newest smoke run only: an older pass that failed again since never closes it
    if d > made.astimezone(schedule.ZONE).strftime('%Y-%m-%d') and store.one_line(b['rule']) not in {store.one_line(f) for f in fails}:
        return f"{req['id']} passed the smoke test ({b['rule']}) on {d}"
    return ''


def _found(st, b):
    """WHEN THE B WAS FOUND: the earliest moment its record holds, its state_at or its first turn (a reopen moves state_at
    past the finding; its turns keep the older moment). Never earlier than the finding: a turn is written after it."""
    moments = [m for m in [str(b['state_at'])] + [str(t.get('at') or '') for t in st.build_turns(b['id'])] if _moment(m)]
    return min(moments, key=_moment) if moments else b['state_at']


def close_passed(st, n=None, inside=None, days=None):
    """A B CLOSES WHEN ITS REQUEST PASSES THE LINK IT WAS FOUND AT (the owner 2026-10-22 00:40): its own tests (test),
    the hired read (takein, the read), the take-in (takein, the take-in), the Judge, the look or the native step of a
    later night that holds its commits (judge, look, native), a later day's smoke run (smoke). Closed through the
    store's own state change, the fact one line of build_turns. n: the night (shared_night.night()); inside(commit,
    built): is the commit in the night's commit; days: the smoke days, newest first. -> [B ids closed]"""
    out = []
    for b in st.build_items():
        if b['state'] == 'open':
            req = st.request(b['request_id'])
            if not req:
                continue
            b = {**b, 'found_at': _found(st, b)}
            if b['found_by'] in ('test', 'takein'):
                fact = _passed_by_state(b, req)
            elif b['found_by'] in NIGHT_LINKS:
                if n is None:
                    from agent import shared_night as night
                    n = night.night() or {}
                if inside is None:
                    from agent import shared_requests as requests
                    inside = lambda c, built: requests._in_main(c, built, where.WORKSPACE)   # noqa: E731
                fact = _passed_by_night(b, req, n, inside)
            elif b['found_by'] == 'smoke':
                if days is None:
                    days = smoke_days('9999-12-31', most=1)
                fact = _passed_smoke(b, req, days)
            else:
                fact = ''   # security: no link it passes on its own
            if not fact:
                continue
            turns = st.build_turns(b['id'])
            memory.close_b(st, b, turns, f'closed: {fact}', by='the B closed when its request passed (close_passed)')   # its turn, its state 'closed' and its lesson: one transaction
            out.append(b['id'])
    return out


def read_refusal(line):
    """The reason of a hired read's REFUSE ('VERDICT <nonce>: REFUSE: <reason>'), or '' (CLEAN, or no verdict)."""
    m = re.search(r'VERDICT\b[^:]*:\s*REFUSE:\s*(.*)$', str(line or '').strip())
    return store.one_line(m.group(1).strip() or 'REFUSE') if m else ''


def from_tests(rid, fails, st=None):
    """THE DEVELOPER: the A's own tests failed ([(test name, its error line)]). -> [B ids] (made or kept)"""
    st = st or store.door()
    if not st.request(rid):
        raise ValueError(f'no such request: {rid}')
    made, kept = [], []
    for test, line in fails:
        _write(st, rid, 'test', test, line or test, None, made, kept)
    return made + kept


def from_read(rid, line, st=None):
    """THE DEVELOPER: the hired read's verdict line on the A's diff; a REFUSE makes one B (rule 'the read', evidence
    its reason). -> [B ids] ([] for CLEAN)"""
    st = st or store.door()
    reason = read_refusal(line)
    if not reason:
        return []
    if not st.request(rid):
        raise ValueError(f'no such request: {rid}')
    made, kept = [], []
    _write(st, rid, 'takein', READ_RULE, reason, None, made, kept)
    return made + kept


def open_items(rid, st=None):
    """THE DEVELOPER'S READER: the open B items of one A (every state but closed), by id. -> [dict]"""
    return [b for b in (st or store.door()).build_items(request_id=rid) if b['state'] != CLOSED]


def gate(st=None, judge_path=None, smoke_path=None, now=None, nightly_dir=None):
    """ROW 021's FACTS: for the Judge (THE NIGHT'S OWN RUN REPORT, shared_night, unless judge_path names a report) and
    the smoke test (the day's, its own report): measured or not (why), when, the verdict, the rules counted, and each
    FAIL rule with the B ids that serve a request (found_by the same source, the same rule, its evidence one of the
    rule's lines), or none: 'not a request'; a Judge row the night before failed too: 'since' its first night.
    -> [{'name', 'measured', 'why', 'when', 'verdict', 'rules', 'fails': [{'rule', 'b': [(B id, R id)], 'lines': [the rule's first evidence lines], 'since'}],
    'run', 'agrees'}]"""
    st = st or store.door()
    items = st.build_items()
    out = []
    for name, path in (('judge', judge_path), ('smoke', smoke_path)):
        if name == 'judge' and not path:
            out.append(_night_judge(items, now, nightly_dir))
            continue
        rep = report(name, path, now)
        entry = {'name': name, 'measured': rep['measured'], 'why': rep['why'], 'when': rep['when'], 'verdict': None, 'rules': 0, 'fails': [], 'run': '', 'agrees': None}
        if rep['report'] is not None and rep['measured'] and not path:   # the live report: of THE workspace, its verdict its rows' own
            other = _other_workspace(rep['report'])
            if other:
                entry.update(measured=False, why=other)
            else:
                said = _rows_disagree(rep['report']) or _smoke_changed_since(rep['when'])
                if said:
                    entry.update(agrees=False, why=said)
        if rep['report'] is not None:
            entry['verdict'] = rep['report'].get('verdict')
            entry['rules'] = len(rep['report'].get('rules') or [])
            for rule, lines in failures(rep['report']):
                rl = store.one_line(rule)
                b = [(i['id'], i['request_id']) for i in items if i['found_by'] == name and i['rule'] == rl and i['evidence'] in lines]
                entry['fails'].append({'rule': rl, 'b': b, 'lines': lines[:2], 'since': smoke_since(rule, schedule.cycle(rep['when'])) if name == 'smoke' and rep['when'] and not b else ''})   # lines: the rule's own fault, the first two of its evidence (row 032's step names it, 2026-10-23)
        out.append(entry)
    return out


def _standing_judge(night_report):
    """The Judge's own latest.json (reports.json judge) when it is newer than the night's run report: a `judge.py changed`
    run after a fix wrote it, every rule in it judged then or carried with its inputs unchanged. None when the night's is
    the newest, or it cannot be read."""
    rep = where.load_json(where.REPORTS['judge']) if hasattr(where, 'load_json') else None
    if rep is None:
        try:
            with open(where.REPORTS['judge'], encoding='utf-8') as fh:
                rep = json.load(fh)
        except (OSError, ValueError):
            return None
    if not isinstance(rep, dict) or not rep.get('rules'):
        return None
    mine, theirs = _moment(rep.get('when')), _moment((night_report or {}).get('when'))
    return rep if mine and (theirs is None or mine > theirs) else None


def _workspace():
    return os.path.realpath(os.path.expanduser(where.WORKSPACE))


def _other_workspace(rep):
    """'' when the report judged THE workspace (where.WORKSPACE), else the line that says which tree it judged: a run on a
    frozen copy or a throwaway (JUDGE_WORKSPACE) writes the same latest.json and must never stand for the workspace."""
    ws = rep.get('workspace')
    if not ws or os.path.realpath(os.path.expanduser(str(ws))) == _workspace():
        return ''
    return f'its report judged {ws}, not the workspace {where.WORKSPACE}'


def _rows_disagree(rep):
    """'' when the report's verdict is its own rows' (FAIL: a row failed; INCOMPLETE: a row skipped; else PASS) and its
    counts add up, else the line that says how it does not."""
    rows = [r for r in rep.get('rules') or [] if isinstance(r, dict)]
    st = [r.get('status') for r in rows]
    own = 'FAIL' if 'FAIL' in st else ('INCOMPLETE' if 'SKIP' in st else 'PASS')
    if rep.get('verdict') != own:
        return f"its report says {rep.get('verdict')} but its own rows say {own}"
    if rep.get('judged') is not None and int(rep.get('judged') or 0) + int(rep.get('carried') or 0) != len(rows):
        return f"its report counts {rep.get('judged')} judged and {rep.get('carried')} carried, but holds {len(rows)} rows"
    return ''


def _smoke_changed_since(when, home=None):
    """'' when no file of the smoke test's own (its rows, its parity/ measurers and probes, its bars) is newer than its
    report, else the line naming the newest: a verdict of checks that have changed since is not the checks' as they are
    (a stale result carried past a changed input)."""
    home = home or os.path.expanduser(where.SETTINGS.get('develop', {}).get('smoke') or '~/virtual_sanity/smoke')
    if when is None or not os.path.isdir(home):
        return ''
    newest = (0.0, '')
    for d, dirs, files in os.walk(home):
        dirs[:] = [x for x in dirs if x not in ('.git', '__pycache__', 'reports')]
        for f in files:
            if f.endswith(('.py', '.json', '.swift')):
                try:
                    newest = max(newest, (os.path.getmtime(os.path.join(d, f)), os.path.relpath(os.path.join(d, f), home)))
                except OSError:
                    continue
    if newest[0] > when.timestamp():
        return f"the smoke test's own {newest[1]} changed {schedule._when(datetime.datetime.fromtimestamp(newest[0], datetime.timezone.utc).isoformat())}, after this report: its rows are not the checks as they are now"
    return ''


PRINTED_FAIL = re.compile(r'^FAIL  (.+?)(?:  \((?:planted violation caught|PLANTED VIOLATION MISSED)\))?$')
LOG_TAIL = 4 << 20   # the last 4 MB of the log: hours of runs


def _printed_for(when, log=None):
    """THE ROWS THE RUN PRINTED for the report written at `when`: the FAIL lines of the log block that ends with its
    VERDICT line ('... · report <when>', judge.py since row 032's fix), the block beginning after the VERDICT or 'nothing to
    judge' line before it. -> set of rule names, or None when the log holds no block for it"""
    log = log or where.REPORTS.get('judge_changed_log', '')
    try:
        with open(log, 'rb') as fh:
            fh.seek(max(0, os.path.getsize(log) - LOG_TAIL))
            lines = fh.read().decode('utf-8', 'replace').splitlines()
    except OSError:
        return None
    found, block = None, set()
    for line in lines:
        if line.startswith('VERDICT: '):
            if line.rstrip().endswith(f'· report {when}'):
                found = set(block)
            block = set()
            continue
        if line.startswith('nothing to judge'):
            block = set()
            continue
        m = PRINTED_FAIL.match(line.rstrip())
        if m:
            block.add(m.group(1).strip())
    return found


def _standing_agrees(rep):
    """THE STANDING REPORT AGREES WITH ITS PRINTED ROWS (what the night's own report is held to, shared_night.judge): its
    verdict is its rows' own, and its FAIL rows are exactly the FAIL rows its `judge.py changed` run printed in the job's log
    (reports.json judge_changed_log). A report the night's chain wrote (its twin in runs/, the same 'when') is the night's own:
    its printed rows are checked when the night ends (None). -> (agrees: True, False or None, why)"""
    said = _rows_disagree(rep)
    if said:
        return False, said
    for path in glob.glob(os.path.join(night.judge_runs_dir(), '*.json')):
        twin = _json(path)
        if isinstance(twin, dict) and twin.get('when') == rep.get('when'):
            return None, ''
    printed = _printed_for(rep.get('when'))
    if printed is None:
        return False, f"no printed rows of the run that wrote it ({rep.get('when')}) in {where.REPORTS.get('judge_changed_log', 'the job log')}"
    mine = {r for r, _ in night.report_fails(rep)}
    if mine != printed:
        return False, f"it says {', '.join(sorted(mine)) or 'no FAIL'} but its run printed {', '.join(sorted(printed)) or 'no FAIL'}"
    return True, ''

def _night_judge(items, now=None, nightly_dir=None):
    """The Judge's entry of row 021 from the night: this run's own report, agreeing with its printed rows."""
    n = night.night(run=nightly_dir, now=now) if nightly_dir else night.night(now=now)
    entry = {'name': 'judge', 'measured': False, 'why': '', 'when': None, 'verdict': None, 'rules': 0, 'fails': [], 'run': (n or {}).get('run', ''), 'agrees': None}
    if n is None:
        entry['why'] = 'no night to read'
        return entry
    if not n['measured']:
        entry['why'] = n['why']
        return entry
    j = night.judge(n)
    standing = _standing_judge(j['report'])   # THE JUDGE'S STANDING REPORT when it is newer than the night's (chunk 4, the owner 2026-10-22: "fixed in minutes")
    if standing is None and j['report'] is None:
        entry['why'] = f"the night {n['run']}: {j['why']}"
        return entry
    if standing is not None and _other_workspace(standing):   # a frozen copy's or a throwaway's run never stands for the workspace
        entry['why'] = _other_workspace(standing)
        if j['report'] is None:
            return entry
        standing = None
    rep = standing or j['report']
    if standing:
        fails = night.report_fails(rep)
        agrees, why = _standing_agrees(rep)
        entry['night'] = ({'verdict': (j['report'] or {}).get('verdict'), 'fails': len(j['fails']), 'agrees': j['agrees'], 'when': _moment((j['report'] or {}).get('when')),
                           'rules': len((j['report'] or {}).get('rules') or []), 'target': night.local_target(),
                           'rows': [{'rule': store.one_line(rule), 'lines': lines[:2]} for rule, lines in j['fails']]}   # THE NIGHT'S OWN FAIL ROWS, whole (2026-10-24 01:00: row 032 read the standing report's PASS, carried from the day before, over the night's own FAIL)
                          if j['report'] is not None else None)   # the night's own Judge, kept: the standing report is today's word, not the night's
        entry.update(measured=True, when=_moment(rep.get('when')), verdict=rep.get('verdict'), rules=len(rep.get('rules') or []), agrees=agrees,
                     run='the standing report, ' + (f"{rep.get('judged')} judged then, {rep.get('carried', 0)} carried" if rep.get('judged') is not None else str(rep.get('made', 'every rule'))))
        if why:
            entry['why'] = why
    else:
        fails = j['fails']
        entry.update(measured=True, when=_moment(rep.get('when')), verdict=rep.get('verdict'), rules=len(rep.get('rules') or []), agrees=j['agrees'])
        if not j['agrees']:
            entry['why'] = j['why']
    _new, old = night.sorted_failures(n)
    since = {f['rule']: f['since'] for f in old if f['found_by'] == 'judge'}
    for rule, lines in fails:
        rl = store.one_line(rule)
        b = [(i['id'], i['request_id']) for i in items if i['found_by'] == 'judge' and i['rule'] == rl and i['evidence'] in lines]
        entry['fails'].append({'rule': rl, 'b': b, 'lines': lines[:2], 'since': since.get(rule, '')})
    return entry


def _main(argv):
    if argv[:1] != ['make']:
        print('usage: python -m agent.shared_build_items make')
        return 2
    got = make()
    print(json.dumps(got, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(_main(sys.argv[1:]))
