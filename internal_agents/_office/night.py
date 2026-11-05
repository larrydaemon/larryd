"""THE NIGHT KIT: what every NIGHT and RELEASE step of a chain shares (packed beside agent.py when its agent.json "libs" names
"night"). A step runs ON DEMAND only: the tree free (its chain's lock, the locks it waits for, the hot fix utility), its own checks
(the agent's own()), then dry (agent.json "dry"): what it would run, or real: its plan (agent.json "plan") under its chain's lock. A red
a code fix can clear becomes a FIX request at the top of DAY's backlog in the office's database (THE RED HEAL, at most heal_most a day).
The step after it is named in its line, never run from here. The agent gives own(given, dry) -> {lines, would, why, step, skip, data}
and ends with night.main(own). Its CALL is SM2's look: one line, and the group's panel on the block whose agent.json names "panel"."""
import datetime
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import look
import office


def F(name, default=None):
    return office.fact(name, default)


def home(p):
    return os.path.expanduser(p) if isinstance(p, str) else p


def tail(text, most=240):
    lines = [x for x in str(text or '').strip().splitlines() if x.strip()]
    return (lines[-1] if lines else '')[:most]


def held(p):
    """another run holds this flock now (tried without waiting, let go at once; a missing file is free)"""
    p = home(p)
    if not p or not os.path.exists(p):
        return False
    with open(p, 'a+', encoding='utf-8') as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fh, fcntl.LOCK_UN)
            return False
        except BlockingIOError:
            return True


def pid_in(p):
    try:
        pid = int(open(home(p)).read().split()[0])
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError, IndexError):
        return 0


def busy():
    """-> (why, his step) when the tree is another run's now, else None: never two writers"""
    if held(F('lock')):
        return f"another {F('chain')} step holds its lock ({F('lock')})", f"lsof {F('lock')} names it: let it end, then RUN here"
    for name, p in (F('waits_for') or {}).items():
        if held(p):
            return f'{name} holds its lock ({p})', f'let {name} end, then RUN here'
    pid = pid_in(F('utility_pid'))
    if pid:
        return f'the hot fix utility is running (pid {pid})', f'let it end (ps -p {pid}), then RUN here'
    return None


def target_of(step, args):
    t = F('targets')
    return t['native'] if step.startswith(tuple(F('native_prefixes'))) else t['rnd'] if '--rnd' in args else t['here']


def last_real(step, args):
    """the newest real result of one tower step, as the step runner wrote it (reruns/<step>@<target>.json), {} when none"""
    try:
        with open(os.path.join(F('reruns'), f'{step}@{target_of(step, args)}.json'), encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def said_real(step, args):
    r = last_real(step, args)
    if not r:
        return f'{step}@{target_of(step, args)} · never run'
    return (f"{step}@{r.get('target')} · {'pass' if r.get('ok') else 'FAIL'} · {str(r.get('finished') or '')[:16]} · "
            f"{str(r.get('commit') or '')[:12]}" + ('' if r.get('ok') else f" · {str(r.get('why') or '')[:120]}"))


def reals(plan):
    return [said_real(s, i['tower']) for i in plan if 'tower' in i for s in i['tower'] if not s.startswith('--')]


def command(item):
    """one item of its plan as the argv, cwd and env it runs with"""
    if 'tower' in item:
        return ([F('python'), os.path.abspath(sys.argv[0]), 'step', *item['tower']], F('tower_app'), {'PYTHONPATH': '.'})
    return [home(a) for a in item['argv']], home(item['cwd']), item.get('env') or {}


def shown(item):
    argv, cwd, env = command(item)
    return f"cd {cwd} && {' '.join(f'{k}={v}' for k, v in env.items())}{' ' if env else ''}{' '.join(argv)}"


def missing(plan):
    need = [F('python'), F('tower_app')] if any('tower' in i for i in plan) else []
    for i in plan:
        need += [home(i.get('cwd'))] + [home(n) for n in i.get('needs') or ()]
    return [n for n in need if n and not os.path.exists(n)]


def ran(item):
    """ITS REAL PATH, one item: -> (ok, lines, why)"""
    argv, cwd, env = command(item)
    if item.get('fresh'):
        shutil.rmtree(home(item['fresh']), ignore_errors=True)
        os.makedirs(home(item['fresh']), exist_ok=True)
    got = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=item.get('seconds') or 3600,
                         env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', **env})
    last = tail((got.stdout or '') + '\n' + (got.stderr or ''))
    if 'tower' in item:
        args = item['tower']
        steps = [s for s in args if not s.startswith('--')]
        lines = [f"{item['say']} · {said_real(s, args)}" for s in steps]
        bad = next((s for s in steps if not last_real(s, args).get('ok')), None)
        codes = {2: 'the tower refused the step', 3: 'the tower is busy'}
        why = codes.get(got.returncode) or (f"{bad} FAILED: {str(last_real(bad, args).get('why') or last)[:200]}" if bad else f'it ended {got.returncode}: {last}')
        return got.returncode == 0, lines, '' if got.returncode == 0 else why
    lines = [f"{item['say']} · exit {got.returncode} · {last[:200]}"]
    if got.returncode == 0 and item.get('result'):
        try:
            with open(home(item['result']), encoding='utf-8') as fh:
                found = json.load(fh).get(item.get('list') or 'items') or []
        except (OSError, ValueError):
            return False, lines, f"its result {item['result']} cannot be read"
        red = [x for x in found if not x.get('ok')]
        if red:
            return False, lines, f'{len(red)} of {len(found)} differ: ' + '; '.join(f"{x.get('id')} {str(x.get('why', ''))[:80]}" for x in red[:4])
        lines.append(f"{item['say']} · all {len(found)} within their line")
    return got.returncode == 0, lines, '' if got.returncode == 0 else f'it ended {got.returncode}: {last}'


def heals_today(con):
    return con.execute('SELECT count(*) FROM requests WHERE why LIKE ? AND substr(asked_at, 1, 10) = ?',
                       (f"heal of the {F('chain')}%", office.now().date().isoformat())).fetchone()[0]


def heal(why, step):
    """THE RED HEAL: a red a code fix can clear becomes a FIX request at the top of DAY's backlog (at most heal_most a day for its
    chain); DAY builds it on its own RUN, never driven from here. -> its line"""
    con = office.db()
    try:
        most, used = int(F('heal_most')), heals_today(con)
        if used >= most:
            return f'not healed: {most} fix requests today already, it stays red for the owner'
        words = (f"FIX · {office.me()['name']} went red in the {F('chain')}: {why} · Its own step: {step} · Find the cause in the code or "
                 f"the data it names and fix it, so {office.me()['name']} passes when it runs again. Heal round {used + 1} of {most}.")
        at = office.now().isoformat(timespec='seconds')
        with con:
            top, first = con.execute('SELECT max(cast(substr(id, 3) AS integer)), min(position) FROM requests').fetchone()
            rid = f'R-{(top or 0) + 1:04d}'
            con.execute('INSERT INTO requests (id, words, hash, source, ref, asked_at, position, state, state_at, why) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (rid, words, hashlib.sha256(words.encode()).hexdigest(), 'order', '', at, (first or 1) - 1, 'asked', at,
                         f"heal of the {F('chain')}: asked by {office.me()['name']}, its run was red"))
        return f'heal · {rid} asked at the top of DAY\'s backlog (round {used + 1} of {most}): DAY builds it on its RUN'
    finally:
        con.close()


HOOK = {}


def next_of():
    return (HOOK.get('next_of') or (lambda: F('next') or ''))()


def answer(lines, would, why='', step='', data=None, healed='', said=''):
    dry = F('dry') is not False
    nxt = '' if why else next_of()
    got = {'at': office.stamp(), 'dry': dry, 'lines': lines, 'would': would, 'why': why, 'step': step, 'next': nxt, 'healed': healed, **(data or {})}
    if why:
        return office.done(f"RED · {why} · YOUR 3 MIN: {step}" + (f' · {healed}' if healed else ''), 'RED', got)
    head = (f"GREEN · DRY · would run {len(would)} command{'s' if len(would) != 1 else ''}" + (f' ({said})' if said else '')) if dry and would else 'GREEN · DRY · nothing to run' if dry else 'GREEN'
    return office.done(' · '.join([head] + lines[-1:] + ([f'next: {nxt}'] if nxt else [])), 'GREEN', got)


def run(given):
    """ONE STEP OF THE CHAIN, ON DEMAND: the tree free, its own checks, then (dry) what it would run, or (real) its plan, its lock held"""
    dry = F('dry') is not False
    plan = F('plan') or []
    stop = busy()
    if stop:
        return answer([], [], *stop)
    real = reals(plan)
    lines = [f"last real: {sum(' · pass · ' in x for x in real)} of {len(real)} pass"] if real else []
    gone = missing(plan)
    if gone:
        return answer(lines, [], f"not there: {', '.join(gone[:3])}", 'put back what it names (or set the fact in agent.json), then RUN here')
    mine = HOOK['own'](given, dry)
    lines += mine.get('lines') or []
    plan = [] if mine.get('skip') else plan
    would = (mine.get('would') or []) + [shown(i) for i in plan]
    said = ', '.join(i['say'] for i in plan)
    if mine.get('why') or dry:
        return answer(lines, would, mine.get('why', ''), mine.get('step', ''), mine.get('data'), said=said)
    os.makedirs(os.path.dirname(home(F('lock'))), exist_ok=True)
    with open(home(F('lock')), 'a+', encoding='utf-8') as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return answer(lines, would, f"another {F('chain')} step holds its lock", 'let it end, then RUN here')
        for item in plan:
            try:
                ok, more, why = ran(item)
            except subprocess.TimeoutExpired:
                ok, more, why = False, [], f"it ran past its {item.get('seconds')} s and was stopped"
            lines += more
            if not ok:
                step = f"{shown(item)} ({item['say']} alone; {F('took')}), then RUN here"
                return answer(lines, would, f"{item['say']}: {why}", step, mine.get('data'), heal(why, step) if F('heals') else '')
    return answer(lines, would, data=mine.get('data'), said=said)


# ── THE LOOK: SM2's own (page.py live_block, live_line, day_view), drawn through look ──────────────────────────────────────

def ago(at):
    """SM2's ticking clock, written at CALL time: '44 H 38 MIN 56 S' since a local stamp ('' when none)"""
    try:
        then = datetime.datetime.fromisoformat(str(at or '')[:19].replace('T', ' '))
    except ValueError:
        return ''
    s = max(0, int((office.now().replace(tzinfo=None) - then).total_seconds()))
    h, m = s // 3600, s % 3600 // 60
    return (f'{h} H ' if h else '') + (f'{m} MIN ' if h or m else '') + f'{s % 60} S'


def live_line(job):
    """SM2's three words: RUNNING (green) while a run is open, NOT RUNNING (red) when its last run was red, else IDLE, each with its time since"""
    d = office.data_of(job)
    if str(job.get('data_job_run_state') or '').upper() in ('RUNNING', 'QUEUED'):
        state, word, cls = 'RUNNING', 'RUNNING', 'hdr-status--success'
    elif office.light_of(job) == 'RED':
        state, word, cls = 'RED', 'NOT RUNNING', 'hdr-status--error'
    else:
        state, word, cls = 'GREEN', 'IDLE', 'scrum-idle'
    since = ago(job.get('data_job_last_run_at') or d.get('at'))
    clock = f'<span class="scrum-since {cls}"> {office.e(since)}</span>' if since else ''
    return (f'<div class="replica-live-line" data-live-key="{office.e(job.get("key") or "")}" data-live-state="{state}">'
            f'<div class="subtitle"><span class="{cls}">{word}</span>{clock}</div></div>')


def group_of(job):
    return str(job.get('data_job_group') or (job.get('card') or {}).get('data_agent_group') or '').upper()


def scoped_theme(sheet, site, scope):
    """SM2's _scoped_theme: a product's dark and light values said again under the block's own id, its addresses the theme's package path"""
    try:
        with open(home(sheet), encoding='utf-8') as fh:
            text = fh.read()
    except OSError:
        return ''
    out = []
    for mode in ('dark', 'light'):
        m = re.search(r'\[data-brilliance-hierarchy="[A-F0-9]+"\]\[data-theme="' + mode + r'"\]\s*\{(.*?)\n\}', text, re.S)
        if m:
            values = m.group(1).replace('url("../', f'url("{site}/')
            out.append(f'[data-theme="{mode}"] {scope} {{{values}}}')
            out.append(f'[data-theme="{mode}"] {scope} {{ background-image: url("{site}/images/{mode}/background.webp"); background-size: cover; background-position: center; }}')
    return '\n'.join(out)


def panel(given, p):
    """SM2's NIGHT / RELEASE block (day_view), its one switch: a press only answers what it would switch (the shells' switches are the board's)"""
    slot, low = p['slot'], p['slot'].lower()
    total = sum(1 for j in office.workflow(given) if group_of(j) == slot)
    pressed = office.asked(given, 'slot') == slot
    said = (f'<div class="annotation">Pressed: it would switch {office.e(office.asked(given, "to") or "off")} the {total} {slot} agents. '
            "Their on and off is each shell's own switch on the board (the owner's): nothing was changed.</div>") if pressed else ''
    form = (f'<form method="post" action="/day_switch" class="ct-form" id="{low}-switch-form"><input type="hidden" name="to" value="off">'
            f'<input type="hidden" name="slot" value="{slot}"><input type="hidden" name="back" value="agent"><span class="body">{slot.capitalize()} agents</span> '
            '<button class="pfb pfb--toggle pfb--on" type="submit" aria-pressed="true" title="On"><span class="pfb__knob"></span></button> '
            f'<span class="annotation">{total} {slot} agents on the board</span></form>')
    html_ = (f'<div class="replica-normal-block replica-frame-part replica-{low}-part" aria-label="{slot}"><div class="replica-day" id="replica-{low}" data-place="agencymgmt">'
             '<div class="replica-day-mark" role="img" aria-label="Agency Mgmt">Agency Mgmt</div>'
             f'<div class="title" id="{low}-name">{office.e(p["title"])}</div><div class="annotation">One switch for every {slot} agent</div>{form}{said}</div></div>')
    day = '\n'.join(dict.fromkeys(re.findall(r'#replica-day[^{]*\{[^}]*\}', look.SHEET)))
    return html_, scoped_theme(F('agency_sheet'), F('agency_site'), f'#replica-{low}') + '\n' + day.replace('#replica-day', f'#replica-{low}')


def canvas(given):
    """SM2's public face of a NIGHT or RELEASE agent: one line (its name, its live line, its group at the right); the first asked block of its
    group carries the group's panel above it (agent.json "panel")"""
    job, me = office.own_job(given), office.me()
    top, css = panel(given, F('panel')) if F('panel') else ('', '')
    line = (f'<div class="replica-live-block" data-live-block="{office.e(job.get("key") or me["key"])}"><div class="title scaf-law-title">{office.e(me["name"])}</div>'
            f'{live_line(job)}<span class="replica-live-group" aria-label="group">{office.e(me.get("group") or "")}</span></div>')
    got = look.view(top + line, str((given.get('page') or {}).get('path') or ''), ':host { display: block }\n' + css)
    return got


def ready(target):
    """the kept build of a target and why it is not ready ('' when ready: its own commit walked green)"""
    try:
        with open(os.path.join(F('builds'), target, 'build.json'), encoding='utf-8') as fh:
            k = json.load(fh)
    except (OSError, ValueError):
        return {}, 'no build is kept'
    try:
        with open(os.path.join(F('builds'), target, 'test.json'), encoding='utf-8') as fh:
            t = json.load(fh)
    except (OSError, ValueError):
        return k, 'the kept build was never walked'
    if not os.path.isdir(k.get('bundle', '')):
        return k, 'its bundle is gone'
    if t.get('commit') != k.get('commit'):
        return k, 'the walk on record is of another build'
    if t.get('verdict') != 'green':
        return k, f"its walk is red ({t.get('red', '?')} red row(s)): hot fix it first"
    return k, ''


def kept_line(target):
    k, why = ready(target)
    return f"{str(k.get('commit', ''))[:12]} made {str(k.get('made_at', ''))[:16]} · {why or 'ready'}" if k else why


# ── THE TOWER'S STEP RUNNER (its real path only: python agent.py step [--rnd] [--clean] <step> ..., run from LARRY LLM's app/, as
# the night chain runs each step, core_engine.auto); its result written beside the night's (reruns/<step>@<target>.json) ──────

def tower_one(auto, native, native_test, tower, step, t, commit, planned):
    results, began = [], datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    if step == 'native_generate':
        events = auto._native(step, results, native.generate(tower.source(t)))
    elif step in ('native_iphone', 'native_macos'):   # THE NIGHT BUILDS CLEAN: no kept fix folder
        events = auto._native(step, results, native.build(step[len('native_'):], commit, '', tower.source(t)))
    elif step.startswith('native_test_'):
        events = auto._native(step, results, native_test.test(step[len('native_test_'):], tower.source(t)))
    else:
        events = auto._steps(t, (step,), results, commit=commit, member='night')
    for e in events:
        print(json.dumps(e, default=str), flush=True)
    got = results[-1] if results else {'step': step, 'target': t['name'], 'ok': False, 'why': 'the step wrote no result'}
    ran_on = (tower.resolve(t, 'HEAD') if step == 'native_generate' else (native.kept(step.rsplit('_', 1)[1]) or {}).get('commit', '')
              if step.startswith('native_') else commit)
    record = {**got, 'step': step, 'target': str(got.get('target') or t['name']), 'commit': ran_on, 'published': tower._current(t) or '',
              'planned': list(planned), 'started': began, 'finished': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'by': 'night'}
    folder = os.path.join(auto.reports_dir(), 'reruns')
    os.makedirs(folder, exist_ok=True)
    out = os.path.join(folder, f"{step}@{record['target']}.json")
    with open(out + '.tmp', 'w', encoding='utf-8') as fh:
        json.dump(record, fh, indent=1, default=str)
    os.replace(out + '.tmp', out)
    print(json.dumps({'written': out, 'ok': record.get('ok')}), flush=True)
    return record


def tower_main(argv):
    """-> 0 every step passed; 1 a step red (it stops there); 2 refused; 3 busy"""
    from core_engine import auto, native, native_test, tower   # LARRY LLM's own, from its app/
    rnd, clean = '--rnd' in argv, '--clean' in argv
    names = [a for a in argv if a not in ('--rnd', '--clean')]
    allowed = tuple(auto.PUBLISH) + (() if rnd else tuple(F('native_steps')))
    if not names or any(n not in allowed for n in names) or (clean and rnd):
        print(json.dumps({'refused': f"not a step: {', '.join(n for n in names if n not in allowed) or 'none named'}"}), flush=True)
        return 2
    try:
        with auto.Lock():
            here = tower.target(auto.AUTO['local'])
            if rnd:
                way = auto.lane('current')
                if way['frozen']:
                    raise ValueError(f"{way['name']} is frozen: its rnd side takes no build")
                t, commit = tower.target(way['rnd']), tower._current(here) or ''
            else:
                t, commit = here, tower.resolve(here, 'HEAD')   # THE NIGHT'S COMMIT IS MAIN'S HEAD for every step
            for n in names:
                if not tower_one(auto, native, native_test, tower, n, t, commit, names).get('ok'):
                    return 1
    except auto.Busy as e:
        print(json.dumps({'busy': str(e)}), flush=True)
        return 3
    except ValueError as e:
        print(json.dumps({'refused': str(e)}), flush=True)
        return 2
    return 0


def main(own=None, next_step=None):
    """the agent's one entry: python agent.py step ... runs tower steps (its real path), else the runtime's CALL or RUN"""
    HOOK.update(own=own or (lambda given, dry: {}), next_of=next_step)
    if sys.argv[1:2] == ['step']:
        sys.exit(tower_main(sys.argv[2:]))
    office.main(canvas, run)
