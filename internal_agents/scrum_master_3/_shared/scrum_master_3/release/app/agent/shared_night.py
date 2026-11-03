"""THE NIGHT, READ (the owner's order 2026-10-22, THE NIGHTLY BUILD END TO END, items 5 to 7; N5, N6, N9): ONE SMALL
READER of the night's own files, used by rows 017 to 028, by the gate (shared_requests.nightly_green) and by the B rule
(shared_build_items.make). It reads; it never writes, never runs the tower and never imports its code.

    the night     the newest run of the local chain that the nightly member ran, not a dry one: its folder
                  <stamp>_local under the tower's reports (reports.json nightly_result), its result.json (steps: ok,
                  why, seconds, commit), its REPORT.md. A re-run is a new folder: both are kept and both are read (the
                  first one's failure is said, never hidden: N10).
    the Judge     THIS RUN'S OWN REPORT, named by the tower as tower.py step12_preflight names it: the folder 'runs'
                  beside the Judge's report (reports.json judge), file <YYYYMMDDHHMMSS UTC of the Judge's start>_
                  <commit[:12]>_<hex>.json, the start inside the run. It must agree with the rows the Judge printed
                  (result.json judge: its FAIL lines, the seal's row when unsealed).
    step(row)     each of rows 017 to 028 its step(s) of the night: pass or fail, why, the night's commit, the run id.
    gate()        N5: step12 passed with its own report agreeing, the look passed, step13 to step18 on localhost pf
                  passed. Nothing else decides green.
    failures()    N6: every red step, Judge row and native walk of the night with its lines (the files they name are
                  matched by the B rule against each request's commits, shared_build_items).
"""
import datetime
import glob
import json
import os
import re
import subprocess

from agent import shared_native as native       # the tower's one lock: whether a chain runs now
from agent import shared_schedule as schedule   # his local time (R3)
from agent import shared_where as where         # every place he reads, by its name

MEMBER = 'nightly'   # result.json "member" of the 01:00 chain (a button press says another)
CHAIN = 'local'      # the night's chain (auto.py local: localhost pf, then slot B's rnd side, then the apps)
LAPTOP = 'this laptop'   # result.json target of the backups, write the apps and the native steps
JUDGE_STEP = 'step12'
LOOK_STEP = 'look'
PUBLISH_PF = ('step13', 'step14', 'step15', 'step16', 'step17', 'step18')   # the publish steps on localhost pf (N5)
SEAL_ROW = 'THE LOCK'   # the Judge's seal row: counted as printed when result.json says unsealed (tower.SEAL_ROW)
MAX_AGE_HOURS = 30   # a night older than this is not measured (reports.json nightly_result max_age)
RUN_FILE = re.compile(r'^(\d{14})_([0-9a-f]{12})_[0-9a-f]+\.json$')
PRINTED = re.compile(r'^FAIL\s+(.*?)(\s{2}\([^()]*\))?$')

NOT_A_REQUEST = 'not a request'
ALREADY = 'already failing'   # the owner's ruling 2026-10-22 00:23: a failure the night before showed too, never a B
NO_STEP = 'the night has no step for it'
GOES_ON = ('native_generate',)   # a red step the chain goes on past (auto.local: "red or not, the build goes on"): never where it stopped


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError, TypeError):
        return None


def _moment(text):
    try:
        m = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return m if m.tzinfo else m.replace(tzinfo=datetime.timezone.utc)


def _digits(text):
    return re.sub(r'[^0-9]', '', str(text or ''))[:14]


def local_target():
    """The target the night publishes to on this laptop (global_config tower.auto.local), 'localhost_pf' when unread."""
    got = _json(where.path('global_config')) or {}
    return ((got.get('tower') or {}).get('auto') or {}).get('local') or 'localhost_pf'


def top():
    """The tower's reports folder (the parent of every <stamp>_<chain> run), from reports.json nightly_result."""
    return os.path.dirname(os.path.dirname(where.REPORTS['nightly_result']))


def runs(folder=None):
    """Every night of the local chain, newest first: [{'folder', 'run', 'result'}] (dry runs and button presses out)."""
    out = []
    for path in sorted(glob.glob(os.path.join(folder or top(), '*_' + CHAIN)), reverse=True):
        got = _json(os.path.join(path, 'result.json'))
        if isinstance(got, dict) and got.get('member') == MEMBER and got.get('chain', CHAIN) == CHAIN and not got.get('dry'):
            out.append({'folder': path, 'run': os.path.basename(path), 'result': got})
    return out


def night(folder=None, now=None, run=None):
    """THE NIGHT: the newest night run (or the one in the folder `run`), with what a row needs. -> dict or None:
    {'folder', 'run', 'result', 'commit', 'started', 'finished', 'ok', 'measured', 'why', 'earlier': [the runs of the
    same night before it, each {'run', 'ok', 'stopped'}], 'before': [the nights before this one, newest first, each
    {'folder', 'run', 'result'}: a re-run of the same night is not a night before]}"""
    all_ = runs(folder or (os.path.dirname(os.path.abspath(run)) if run else None))
    if run:
        all_ = all_[[os.path.abspath(e['folder']) for e in all_].index(os.path.abspath(run)):] if os.path.abspath(run) in [os.path.abspath(e['folder']) for e in all_] else []
    if not all_:
        return None
    n = dict(all_[0])
    r = n['result']
    n.update(commit=str(r.get('commit') or ''), started=str(r.get('started') or ''), finished=str(r.get('finished') or ''), ok=r.get('ok'))
    began = _moment(n['started'])
    moment = now or datetime.datetime.now(datetime.timezone.utc)
    if began is None:
        n.update(measured=False, why=f"the night {n['run']} says no start")
    elif (moment - began).total_seconds() / 3600 > MAX_AGE_HOURS:
        n.update(measured=False, why=f"the newest night is {n['run']} ({schedule._when(n['started'])}), older than {MAX_AGE_HOURS} h")
    else:
        n.update(measured=True, why='')
    n['earlier'], n['before'] = [], []
    for e in all_[1:]:
        at = _moment(e['result'].get('started'))
        if began and at and datetime.timedelta(0) <= began - at <= SAME_NIGHT:
            stop = next((s for s in e['result'].get('steps') or [] if isinstance(s, dict) and s.get('ok') is False), None)
            n['earlier'].append({'run': e['run'], 'ok': e['result'].get('ok'), 'stopped': (stop or {}).get('step', '')})
        elif began and at and began - at > SAME_NIGHT:
            n['before'].append(e)
    return n


SAME_NIGHT = datetime.timedelta(hours=12)   # a run this close before another is the same night (a re-run), never "the night before"


RERUN_COMMIT = re.compile(r'^[0-9a-f]{40}$')
ON_ITS_COMMIT = ('look', 'step18')   # a step that measures what the target runs: it stands only on the commit it names


def reruns(names, target=None, after=None, folder=None):
    """THE STEPS RUN AGAIN ON THEIR OWN (agent/rerun_step.py, reports.json step_rerun: reruns/ beside the nights, in the
    folder of the night read, never another), ONE ATTEMPT WHOLE, ON THE CODE IT NAMES: only a record as rerun_step.py
    writes it counts (its file named by its own step and target, by 'rerun', a full commit), started and ended after
    `after` (the night's start: a rerun before the night is older than the night). The newest attempt on the target that
    was asked to run any of `names` stands for every name it was asked to run: a name it ran gives its record; a name
    it did not reach is said so, with where it stopped (never the night's older word, never an older attempt's). A look
    or a restart whose target ran other code than its attempt's (published is not commit) does not stand: said so.
    A record written before attempts were named is an attempt of its own step alone.
    -> {name: step dict, as the night's result has it, with 'finished' and 'commit'}"""
    recs = []
    for path in glob.glob(os.path.join(folder or top(), 'reruns', os.path.basename(where.REPORTS['step_rerun']))):
        got = _json(path)
        if not isinstance(got, dict) or not _moment(got.get('finished')):
            continue
        step, t = str(got.get('step') or ''), str(got.get('target') or '')
        if os.path.basename(path) != f'{step}@{t}.json' or got.get('by') != 'rerun' or not RERUN_COMMIT.match(str(got.get('commit') or '')):
            continue   # not as agent/rerun_step.py writes it: a file of another hand never stands for a step
        if target is not None and not (target(t) if callable(target) else t == target):
            continue
        if after and (_moment(got['finished']) <= after or (_moment(got.get('started')) or after) <= after):
            continue
        got = dict(got, attempt=str(got.get('attempt') or got.get('started') or got['finished']), planned=list(got.get('planned') or [step]))
        recs.append(got)
    asked = [r for r in recs if set(r['planned']) & set(names)]
    if not asked:
        return {}
    newest = max(asked, key=lambda r: (_moment(r['attempt']) or _moment(r['finished']), _moment(r['finished'])))
    mine = sorted((r for r in recs if r['attempt'] == newest['attempt'] and r['target'] == newest['target']), key=lambda r: _moment(r['finished']))
    stop = next((r['step'] for r in mine if r.get('ok') is not True), '')
    out = {}
    for r in mine:
        if r['step'] not in names:
            continue
        if r['step'] in ON_ITS_COMMIT and r.get('published') is not None and str(r.get('published') or '') != r['commit']:
            r = dict(r, ok=False, why=f"it ran on {str(r.get('published') or 'no build')[:12]}, not on its attempt's {r['commit'][:12]}: it does not stand")
        out[r['step']] = r
    for x in newest['planned']:
        if x in names and x not in out:
            out[x] = {'step': x, 'target': newest['target'], 'ok': False, 'by': 'rerun', 'attempt': newest['attempt'], 'commit': newest['commit'],
                      'finished': mine[-1]['finished'], 'why': f"the rerun did not reach it (stopped at {stop})" if stop else 'the rerun has not reached it yet'}
    return out


def steps_of(n, names, target=None):
    """The night's steps by name (and target: a name, or a function of the target), in their order. -> [step dicts]"""
    out = []
    for s in (n or {}).get('result', {}).get('steps') or []:
        if not isinstance(s, dict) or s.get('step') not in names:
            continue
        t = str(s.get('target') or '')
        if target is None or (target(t) if callable(target) else t == target):
            out.append(s)
    return out


# ---- the Judge's own report of the night's run ------------------------------------------------------------------
def judge_runs_dir():
    """The folder the tower names the Judge's own run reports in: 'runs' beside the Judge's report (tower.py)."""
    return os.path.join(os.path.dirname(where.REPORTS['judge']), 'runs')


def judge_file(n):
    """THIS RUN'S OWN REPORT of the Judge: the file of the night's commit whose start lies inside the run (the first
    such: the laptop's step12 comes before any other). -> path or ''"""
    if not n or not n.get('commit'):
        return ''
    lo, hi = _digits(n.get('started')), _digits(n.get('finished')) or '9' * 14
    found = []
    for path in glob.glob(os.path.join(judge_runs_dir(), '*.json')):
        m = RUN_FILE.match(os.path.basename(path))
        if m and m.group(2) == n['commit'][:12] and lo <= m.group(1) <= hi:
            found.append((m.group(1), path))
    return min(found)[1] if found else ''


def report_fails(rep):
    """A report's FAIL rules: [(rule, [evidence lines])]."""
    return [(str(r.get('rule') or ''), [' '.join(str(e).split()) for e in (r.get('evidence') or []) if str(e).strip()])
            for r in (rep or {}).get('rules') or [] if isinstance(r, dict) and r.get('status') == 'FAIL']


def printed_rows(n):
    """The FAIL rows the Judge printed in the night's run, as result.json keeps them (judge red, native; the seal's row
    when unsealed). -> set of rule names"""
    j = (n or {}).get('result', {}).get('judge') or {}
    out = set()
    for text in list(j.get('red') or []) + list(j.get('native') or []):
        m = PRINTED.match(str(text).strip())
        if m:
            out.add(m.group(1).strip())
    if j.get('unsealed'):
        out.add(SEAL_ROW)
    return out


def judge(n):
    """THE JUDGE OF THE NIGHT. -> {'path', 'report', 'verdict', 'fails', 'printed', 'agrees', 'ok', 'why'}: ok only when
    this run's own report is there, says PASS, and agrees with the rows it printed."""
    path = judge_file(n)
    out = {'path': path, 'report': None, 'verdict': None, 'fails': [], 'printed': printed_rows(n), 'agrees': False, 'ok': False, 'why': ''}
    if not path:
        out['why'] = f"no report of this run in {judge_runs_dir()} (commit {(n or {}).get('commit', '')[:12]})"
        return out
    rep = _json(path)
    if not isinstance(rep, dict):
        out['why'] = f'its report {os.path.basename(path)} is not readable'
        return out
    out.update(report=rep, verdict=rep.get('verdict'), fails=report_fails(rep))
    mine = {r for r, _ in out['fails']}
    out['agrees'] = (rep.get('verdict') == 'FAIL') == bool(out['printed']) and mine == out['printed']
    if not out['agrees']:
        out['why'] = (f"its report {os.path.basename(path)} says {rep.get('verdict')} ({', '.join(sorted(mine)) or 'no FAIL'}) "
                      f"but its printed rows say {', '.join(sorted(out['printed'])) or 'no FAIL'}")
    elif rep.get('verdict') != 'PASS':
        out['why'] = f"its report {os.path.basename(path)} says {rep.get('verdict')}, {len(mine)} row(s) failed (each said once, on row 032)"
    else:
        out['ok'] = True
    return out


# ---- N5: the gate -------------------------------------------------------------------------------------------------
def gate(n):
    """THE OWNER'S GATE (N5). -> {'ok', 'parts': [(name, ok, why)], 'run', 'commit', 'judge': judge(n)}"""
    if not n:
        return {'ok': False, 'parts': [('the night', False, 'no night to read')], 'run': '', 'commit': '', 'judge': None}
    here = local_target()
    parts = []
    if not n.get('measured'):
        parts.append(('the night', False, n.get('why') or 'not measured'))
    s12 = steps_of(n, (JUDGE_STEP,), here)
    j = judge(n)
    ok12 = bool(s12) and all(s.get('ok') is True for s in s12)
    parts.append(('step12 THE JUDGE', ok12 and j['ok'], ('' if ok12 else (s12[0].get('why') or 'red') if s12 else 'it did not run')
                  + ('' if j['ok'] else ('; ' if not ok12 else '') + j['why'])))
    look = steps_of(n, (LOOK_STEP,), here)
    okl = bool(look) and all(s.get('ok') is True and s.get('looked') is not False for s in look)
    parts.append(('THE LOOK', okl, '' if okl else (look[0].get('why') or 'no page was looked at') if look else 'it did not run'))
    pf = {s['step']: s for s in steps_of(n, PUBLISH_PF, here)}
    bad = [f"{p}: {'did not run' if p not in pf else pf[p].get('why') or 'red'}" for p in PUBLISH_PF if p not in pf or pf[p].get('ok') is not True]
    parts.append(('step13 to step18 on ' + here, not bad, '; '.join(bad)))
    return {'ok': all(p[1] for p in parts), 'parts': parts, 'run': n['run'], 'commit': n.get('commit', ''), 'judge': j}


def gate_said(g):
    """The gate in one line: each part pass or FAIL, why."""
    return ' · '.join(f"{name}: {'pass' if ok else 'FAIL'}" + (f': {why}' if why and not ok else '') for name, ok, why in g['parts'])


# ---- N6: the failures, with their lines ---------------------------------------------------------------------------
def _not_done(folder):
    try:
        with open(os.path.join(folder, 'REPORT.md'), encoding='utf-8') as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    if '## NOT DONE' in text:
        for line in text.split('## NOT DONE', 1)[1].splitlines():
            if line.startswith('## '):
                break
            if line.startswith('- ') and line[2:].strip() != 'none':
                out.append(' '.join(line[2:].split()))
    return out


def kind(step):
    """What found a failed step (build_items.found_by): look, native (write the apps, a native build or walk, the hot
    fix utility), judge (step12), else None (another publish step: build_items.found_by holds no value for it, so it
    is shown once on its row and makes no B)."""
    if step == LOOK_STEP:
        return 'look'
    if step == JUDGE_STEP:
        return 'judge'   # the Judge's own step (red with a reason the tower gave: its disk, a copy not whole, the structure)
    if step.startswith('native_') or step == 'hot_fix_utility':
        return 'native'
    return None


def failures(n):
    """EVERY FAILURE OF THE NIGHT WITH ITS LINES (N6): [{'found_by', 'rule', 'lines', 'target'}]: each red step (its
    why and the REPORT.md NOT DONE lines that carry it; found_by look, native or 'nightly'), each FAIL row of the
    Judge's own report of this run (found_by judge, its evidence), each native walk of the night (test.json, made in
    the run, red: found_by native, its why)."""
    if not n:
        return []
    out = []
    not_done = _not_done(n['folder'])
    for s in n['result'].get('steps') or []:
        if not isinstance(s, dict) or s.get('ok') is not False:
            continue
        step = str(s.get('step') or '')
        lines = [' '.join(str(s['why']).split())] if s.get('why') else []
        lines += [l for l in not_done if str(s.get('why') or '\0') in l and l not in lines]
        out.append({'found_by': kind(step) or 'nightly', 'rule': step, 'lines': lines, 'target': str(s.get('target') or '')})
    for rule, lines in judge(n)['fails']:
        out.append({'found_by': 'judge', 'rule': rule, 'lines': lines, 'target': local_target()})
    lo, hi = _moment(n.get('started')), _moment(n.get('finished'))
    for name in _targets():
        t = _json(where.path('native_builds', name, 'test.json')) or {}
        at = _moment(t.get('made_at'))
        if t.get('verdict') not in (None, 'green') and at and lo and lo <= at <= (hi or at):
            out.append({'found_by': 'native', 'rule': f'native_test_{name}', 'lines': [' '.join(str(t.get('why') or t.get('verdict')).split())], 'target': LAPTOP})
    return out


def _targets():
    got = _json(where.path('global_config')) or {}
    return list((((got.get('tower') or {}).get('native') or {}).get('targets') or {}))


# ---- N9: each row its step ----------------------------------------------------------------------------------------
def _rnd(target):
    return target.endswith('.rnd')


STEP_NAMES = {'step5': 'the apps written', 'step6': 'the apps checked', JUDGE_STEP: 'THE JUDGE', LOOK_STEP: 'THE LOOK', 'backups': 'BACKUPS', 'slot_born': 'the slot born',
              'hot_fix_utility': 'THE HOT FIX UTILITY'}   # a step's name beside its number, where a row says the night stopped


def stopped_at(n, brief=False):
    """WHERE THE NIGHT STOPPED, said whole (2026-10-24 01:00: "stopped at step12" told no one that THE JUDGE failed PARTIAL
    DATA and FOLDER LOCK on localhost pf): the first red step the chain does not go on past, its name, its target and its
    own why; at the Judge, the Judge's own FAIL rows (brief: their names alone). -> (step, words) or ('', '') when no step stopped it"""
    steps = [s for s in (n or {}).get('result', {}).get('steps') or [] if isinstance(s, dict)]
    stop = next((s for s in steps if s.get('ok') is False and s.get('step') not in GOES_ON), None)
    if not stop:
        return '', ''
    step = str(stop.get('step') or '')
    name = STEP_NAMES.get(step, '')
    where = f"{step}{' ' + name if name else ''}" + (f" on {stop.get('target')}" if stop.get('target') and not brief else '')   # brief: the rows' names alone, no target, no words of theirs (a row's text has the sync's words to carry too)
    if step == JUDGE_STEP:
        fails = judge(n).get('fails') or []
        why = ', '.join(f"FAIL {rule} ({(lines or [''])[0][:90]})" if lines and not brief else rule if brief else f'FAIL {rule}' for rule, lines in fails)
    else:
        why = str(stop.get('why') or '')
    return step, where + (f": {why}" if why else '')


def row_steps(row):
    """Row -> (the step names it shows, its target): rows 028 to 039 (028 is the take-in, on change and at 00:10: its own job log;
    038 and 039 have no step of their own in the night's result)."""
    here = local_target()
    return {29: (('backups',), LAPTOP),
            30: (('native_generate',), LAPTOP),
            31: (('step5', 'step6'), here),
            32: ((JUDGE_STEP,), here),
            34: ((LOOK_STEP,), here),
            33: (PUBLISH_PF, here),
            35: (('backups', 'slot_born', 'step5', 'step6', JUDGE_STEP) + PUBLISH_PF + (LOOK_STEP,), _rnd),
            36: (('native_iphone', 'native_test_iphone', 'hot_fix_utility'), LAPTOP),
            37: (('native_macos', 'native_test_macos', 'hot_fix_utility'), LAPTOP),
            38: ((), None),
            39: ((), None)}.get(row, ((), None))


def _b_of(failure, items):
    """The B items a failure made (found_by and rule the same, the evidence one of its lines). -> [(B id, R id)]"""
    lines = set(failure['lines'])
    fb = failure['found_by']
    return [(b['id'], b['request_id']) for b in items
            if b.get('rule') == ' '.join(failure['rule'].split()) and b.get('evidence') in lines and (fb == 'nightly' or b.get('found_by') == fb)]


def step(row, n=None, items=None):
    """ROW <row>'s STEP OF THE NIGHT. -> {'row', 'names', 'steps', 'ok' (True pass, False fail, None not in the night),
    'why', 'run', 'commit', 'said'}: said is the row's line: '<steps>: pass|FAIL: why · <request B or not a request> ·
    run <id> (<local time>) · commit <12>'. items: the B items (store.build_items()) to show a failure's request."""
    names, target = row_steps(row)
    out = {'row': row, 'names': names, 'steps': [], 'ok': None, 'why': '', 'run': (n or {}).get('run', ''), 'commit': (n or {}).get('commit', ''), 'said': ''}
    if not n:
        out['why'] = out['said'] = 'not measured: no night to read'
        return out
    tail = f" · run {n['run']} ({ago(n['started'])}) · commit {n['commit'][:12] or 'none'}"   # its time and its age, live (ago)
    if not n.get('measured'):
        out['why'] = f"not measured: {n['why']}"
        out['said'] = out['why'] + tail
        return out
    mine = steps_of(n, names, target) if names else []
    again_ = reruns(names, target, _moment(n.get('started')), os.path.dirname(os.path.abspath(n['folder'])) if n.get('folder') else None) if names else {}   # a step run again since the night: its newer result stands
    if again_:
        mine = [again_.get(s.get('step'), s) for s in mine] + [again_[x] for x in names if x in again_ and x not in {s.get('step') for s in mine}]
        mine.sort(key=lambda s: names.index(s.get('step')))
    out['steps'] = mine
    if not names:
        out['why'] = NO_STEP
    elif not mine:
        out['why'] = (f"the night stopped before it at {stopped_at(n, brief=True)[1]}" if stopped_at(n)[0] else 'the night did not reach it') if n.get('ok') is False else 'the night did not run it'
    else:
        bad = [s for s in mine if s.get('ok') is not True]
        never = [x for x in names if x not in {s.get('step') for s in mine}]   # EVERY STEP OF THE ROW OR NO PASS (the reader 2026-10-23): a night that ran one of six is no green
        out['ok'] = not bad and not never
        out['why'] = '; '.join([f"{s.get('step')}: {s.get('why') or 'red'}" for s in bad] + ([f"{', '.join(never)} never ran in the night"] if never else []))
    word = 'pass' if out['ok'] else 'FAIL' if out['ok'] is False else 'not in the night'
    served = ''
    if out['ok'] is False:
        new, old = sorted_failures(n)
        mine_ = lambda f: f['rule'] in {x.get('step') for x in mine} and f['target'] in {str(x.get('target') or '') for x in mine}
        tied = sorted({x for f in new if mine_(f) for x in _b_of(f, items or [])})
        since = sorted({f['since'] for f in old if mine_(f)})
        served = ' · ' + ('; '.join(([', '.join(f'{b} ({r})' for b, r in tied)] if tied else [NOT_A_REQUEST] if any(mine_(f) for f in new) else [])
                                     + ([f'{ALREADY} since {since[0]}'] if since else [])) or NOT_A_REQUEST)
    earlier = [e for e in n.get('earlier') or [] if e.get('ok') is False]
    again = f" · a re-run: the first run {earlier[-1]['run']} stopped at {earlier[-1]['stopped'] or 'a red step'}" if earlier else ''
    shown = 'its step' if not names else ', '.join(names) if len(names) <= 3 else f'{names[0]} to {names[-1]}'
    if again_:
        newest = max(again_.values(), key=lambda s: _moment(s['finished']))
        tail += f" · run again {ago(newest['finished'])} · commit {str(newest.get('commit') or '')[:12] or 'none'}"
    out['said'] = f"{shown}: {word}" + (f": {out['why']}" if out['why'] and out['ok'] is not True else '') + served + tail + again
    return out



def too_old(n, steps, now=None):
    """A PASS OLDER THAN THE NIGHT READER'S OWN LIMIT IS NO PASS (the owner 2026-10-23: "never a fake green kept forever";
    2026-10-25: "does it work or not?"): the newest proof of a row's steps (the night's start, or a step run alone since,
    its finished) against MAX_AGE_HOURS. -> '' when fresh, else the words of its age"""
    proofs = [_moment((n or {}).get('started'))] + [_moment(s.get('finished')) for s in steps or () if s.get('by') == 'rerun']
    newest = max((p for p in proofs if p), default=None)
    if newest is None:
        return 'not measured: no time to its pass'
    hours = ((now or datetime.datetime.now(datetime.timezone.utc)) - newest).total_seconds() / 3600
    return '' if hours <= MAX_AGE_HOURS else f'not measured: the newest pass is {hours:.0f} h old, over {MAX_AGE_HOURS} h'


def ago(moment, now=None):
    """A PAST MOMENT AS A LIVE ROW SAYS IT (the owner 2026-10-22: "not daily and not hourly only live current data.. that
    is what active monitoring means"): its date and clock in his zone, and how long ago, 'Oct 22 01:12, 17 h ago'. A
    moment that does not read is said as it is."""
    m = _moment(moment)
    if m is None:
        return str(moment or 'no time')
    mins = max(0, int(((now or datetime.datetime.now(datetime.timezone.utc)) - m).total_seconds() // 60))
    age = f'{mins} min ago' if mins < 60 else f'{mins // 60} h ago' if mins < 48 * 60 else f'{mins // 1440} days ago'
    return f"{schedule._when(m.isoformat())}, {age}"


def state(s, running=''):
    """A row's state from its step: pass green; fail red; not in the night red too (R1: never green, never grey, never
    'running'). A chain running now changes nothing here: the newest finished night is the one judged (look)."""
    if s['ok'] is True:
        return 'green'
    return 'red'


def look(row, folder=None, now=None, st=None):
    """ROW <row>'s ONE LOOK AT THE NIGHT, LIVE (the owner 2026-10-22: "do a full sweep... zero once per day rules.. its
    all live data only for active monitoring"). -> (state, text). The newest night there is, judged and said with its
    time and age, however old it is (older than MAX_AGE_HOURS: still the newest fact, judged, its age said; the gate
    keeps its own rule in night()). While a chain holds the tower's lock and began after that night, "the night runs
    now since ..." is said first and the newest finished night is still the one judged: its pass green, its fail red.
    No night at all: red, said so."""
    n = night(folder, now)
    if n and not n.get('measured') and _moment(n.get('started')):   # only its age kept it from being measured: the newest fact there is
        n = dict(n, measured=True, why='')
    try:
        items = (st or _door()).build_items()
    except Exception:   # noqa: BLE001  (the B ids are a help: the step is said all the same)
        items = []
    s = step(row, n, items)
    held = native.running()
    since = _moment(held.split(' since ', 1)[1]) if ' since ' in held else None
    if held and (not n or (since and _moment(n['started']) and since > _moment(n['started']))):
        return state(s, held), (f"the night runs now since {ago(since.isoformat())}" if since else f"the night runs now ({held})") + f"; the newest finished night: {s['said']}"
    return state(s, held), s['said']


def _door():
    from agent import shared_store as store
    return store.door()


def day_of(n=None):
    """THE DAY OF THE NIGHT (his cycle, 07:00 to 07:00, that the night began in): the morning after reads the night
    before, never "not yet today". -> YYYY-MM-DD (today's cycle when there is no night)"""
    began = _moment((n or {}).get('started'))
    return schedule.cycle(began) if began else schedule.cycle()


RANK = {'red': 0, 'running': 1, 'green': 2}


def worst(*parts):
    """The worst of (state, text) parts, their texts joined. -> (state, text)"""
    return min((p[0] for p in parts), key=lambda x: RANK.get(x, 0)), ' · '.join(p[1] for p in parts if p[1])


# ---- THE OWNER'S RULING 2026-10-22 00:23: a B only for a NEW failure ------------------------------------------------
def key(f):
    """What makes two nights' failures the same one: a step by its name and target; a Judge row by its rule; a look
    page by the look's line naming it; a native walk by its target."""
    if f['found_by'] == 'judge':
        return ('judge', f['rule'])
    if f['found_by'] == 'look':
        return ('look', f['rule'], f['target'], tuple(sorted(f['lines'])))
    return (f['found_by'], f['rule'], f['target'])


def _night_of(entry, now=None):
    return night(run=entry['folder'], now=now)


def previous(n):
    """The night before this one (a re-run of the same night is not it). -> night dict or None"""
    before = (n or {}).get('before') or []
    return night(run=before[0]['folder']) if before else None


PATH_RE = re.compile(r"(?<![\w.])(?:~/|/)[\w./@+-]*\w")   # a path in a FAIL row's words: /usr/local/bin/lock, ~/virtual_sanity/judge/bin/lock


def paths_in(lines):
    """the paths the Judge's FAIL rows name, each once, in order"""
    out = []
    for line in lines or []:
        for p in PATH_RE.findall(str(line)):
            if p not in out:
                out.append(p)
    return out


JUDGE_HOME = os.path.expanduser('~/virtual_sanity/judge')   # the Judge's folder, a git repository: the chain runs it AS COMMITTED (tower.step12_preflight)
LOCK_BIN = '/usr/local/bin'                                   # where the owner installs lock and unlock (judge.py LOCK_BIN)


def judge_uncommitted(home=None, installed=None):
    """THE JUDGE RUNS AS COMMITTED (tower.step12_preflight: a clone of the Judge's folder at HEAD), so FOLDER LOCK compares
    the installed lock commands with the COMMITTED bin/lock. When they equal the working copy but not HEAD, the broken
    file is the Judge's own: changed and not committed (2026-10-24 12:56: "differs from the Judge's bin/lock" while cmp
    by hand said identical). -> ({installed path: the Judge's own path} for lock and unlock so placed, HEAD's short hash);
    ({}, '') otherwise, or when the folder is no repository."""
    home, installed = home or JUDGE_HOME, installed or LOCK_BIN
    try:
        with open(os.path.join(home, 'bin', 'lock'), 'rb') as fh:
            work = fh.read()
        got = subprocess.run(['git', '-C', home, 'show', 'HEAD:bin/lock'], capture_output=True, timeout=20)
        head = subprocess.run(['git', '-C', home, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return {}, ''
    if got.returncode or not got.stdout or got.stdout == work:
        return {}, ''
    out = {}
    for cmd in ('lock', 'unlock'):
        theirs = os.path.join(installed, cmd)
        try:
            with open(theirs, 'rb') as fh:
                if fh.read() == work:
                    out[theirs] = os.path.join(home, 'bin', cmd)
        except OSError:
            continue
    return (out, head) if out else ({}, '')


def broken_files(n, lines=None):
    """THE BROKEN FILES OF THE NIGHT'S JUDGE (the owner 2026-10-24 08:46: "the name of the file that is broken and a copy
    link", never a command that runs the check again): the paths its FAIL rows name (lines: one rule's rows; else every
    failed rule's), an installed lock command that equals the Judge's uncommitted copy named as that copy (the truly
    broken file: judge_uncommitted), then its own report. [] with no report."""
    j = judge(n)
    if lines is None:
        lines = [line for _, rows in j.get('fails') or [] for line in rows or []]
    found = paths_in(lines)
    swap = judge_uncommitted()[0] if any(p.startswith(LOCK_BIN + '/') for p in found) else {}
    out = []
    for p in found:
        p = swap.get(p, p)
        if p not in out:
            out.append(p)
    if j.get('path') and j['path'] not in out:
        out.append(j['path'])
    return out


def judged_rows(n):
    """A night's Judge FAIL rows: its own run report's when there is one, else the rows it printed (result.json judge),
    for a night whose Judge wrote no report of its own (before 2026-10-22). -> set of rules"""
    j = judge(n)
    return {r for r, _ in j['fails']} if j['report'] is not None else printed_rows(n)


def _keys(n):
    """A night's failure keys, its Judge rows counted as judged_rows says them."""
    out = {key(f) for f in failures(n) if f['found_by'] != 'judge'}
    return out | {('judge', r) for r in judged_rows(n)}


def sorted_failures(n, most=14):
    """THE NIGHT'S FAILURES, NEW OR ALREADY THERE. -> (new: [failure], old: [failure + 'since': the run id of the first
    night of the unbroken line of nights it failed in]). Compared with the nights before (re-runs of one night are
    one night): a failure the night before also showed is old. No night before: every failure is new."""
    fails = failures(n)
    if not fails:
        return [], []
    nights, seen = [], []
    for e in ((n or {}).get('before') or [])[:most * 3]:
        at = _moment(e['result'].get('started'))
        if seen and at and _moment(seen[-1]['result'].get('started')) - at <= SAME_NIGHT:
            continue   # a run of a night already counted: its newest run stands for it
        seen.append(e)
        if len(seen) >= most:
            break
    nights = [(e['run'], _keys(night(run=e['folder']))) for e in seen]
    new, old = [], []
    for f in fails:
        k = key(f)
        since = ''
        for run, ks in nights:
            if k not in ks:
                break
            since = run
        (old if since else new).append({**f, 'since': since} if since else f)
    return new, old


# ---- N9: the morning, read --------------------------------------------------------------------------------------
def morning(st, n=None):
    """WHAT THE NIGHT DID FOR THE REQUESTS, READ (rows 001 and 002): -> {'run', 'commit', 'started', 'gate', 'green':
    [ids whose green (or shipped) names this run], 'waiting': [ids still taken in], 'bs': [(B id, R id) made from this
    night's failures]} or None (no night). Every id is traceable: its why names the run; the gate is result.json's and
    the Judge's own run report's."""
    n = n if n is not None else night()
    if not n:
        return None
    reqs = st.requests()
    green = [r['id'] for r in reqs if r.get('state') in ('green', 'shipped') and n['run'] in str(r.get('why') or '')]
    waiting = [r['id'] for r in reqs if r.get('state') == 'taken_in']
    fails = failures(n)
    bs = sorted({x for f in fails for x in _b_of(f, st.build_items())})
    return {'run': n['run'], 'commit': n.get('commit', ''), 'started': n.get('started', ''), 'measured': n.get('measured'), 'why': n.get('why', ''),
            'gate': gate(n), 'green': green, 'waiting': waiting, 'bs': bs}


def morning_said(m):
    """Row 001's line of the night: which requests went green last night, with the night's run id."""
    if not m:
        return 'last night: not measured: no night to read'
    head = f"last night (run {m['run']}, {schedule._when(m['started'])}, commit {m['commit'][:12] or 'none'})"
    if not m['measured']:
        return f"{head}: not measured: {m['why']}"
    out = head + (f": green {', '.join(m['green'])}" if m['green'] else ': no request went green')
    if not m['gate']['ok']:
        out += f" · the gate: FAIL: {gate_said(m['gate'])}"
    if m['waiting']:
        out += f" · still taken in: {', '.join(m['waiting'])}"
    if m['bs']:
        out += f" · B from the night: {', '.join(f'{b} ({r})' for b, r in m['bs'])}"
    return out


def morning_spoken(m):
    """The standup's sentence of the night, in plain words (no codes but the request ids, no paths)."""
    if not m or not m['measured']:
        return 'I have no nightly build from last night to read.'
    names = lambda xs: (', '.join(xs[:-1]) + ' and ' + xs[-1]) if len(xs) > 1 else xs[0]
    if m['green']:
        said = f"Last night's build passed the Judge, the look and the publish, and {names(m['green'])} went green."
    elif m['gate']['ok']:
        said = "Last night's build passed the Judge, the look and the publish, and no request was waiting for it."
    else:
        bad = [p[0].split(' ')[0].lower() if p[0].startswith('step') else p[0].lower() for p in m['gate']['parts'] if not p[1]]
        said = f"Last night's build did not pass {names(bad)}, so no request went green."
    if m['waiting']:
        said += f" Taken in and not green yet: {names(m['waiting'])}."
    return said
