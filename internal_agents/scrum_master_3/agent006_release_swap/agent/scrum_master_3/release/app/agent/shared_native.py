"""THE NIGHT'S BUILD AND THE NATIVE BUILDS, AS THEIR OWN FILES SAY THEM (moved out of row 031, 2026-10-21). He reads
the files the tower writes (reports.json: nightly_latest, nightly_lock; settings reads: native_builds, global_config); he never
imports or runs the tower's code.

latest(chain): the newest run of a chain (latest_<chain>.json), {} before its first. labels(run): each step's name as
the run's own REPORT.md says it. label(run, step): one of them. running(): who holds the tower's one lock ('' when
nobody). targets(): the native targets (global_config tower.native.targets). kept(target), tested(target): the kept
build of a target and its test (build.json, test.json), or None. night(day): the night's build of this day, or None.
steps(what, *names): a row's check made of these steps of the night's chain."""
import datetime
import json
import os
import re

from agent import shared_where as where
from agent import shared_schedule as schedule   # the clock (_in) and a row's word (said)


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def latest(chain):
    """The newest report of a chain, as the tower left it beside its runs ({} before its first run)."""
    got = _json(where.report('nightly_latest', f'latest_{chain}.json'))
    return got if isinstance(got, dict) else {}


def labels(run):
    """THE STEPS' OWN NAMES, as the run's REPORT.md writes them (its table '| Step | Target | ...', one line a step, in
    the order of run['steps']). -> {step key: its name}; a run with no readable report: {} (the key is said as itself)."""
    try:
        with open(run.get('report') or '', encoding='utf-8') as fh:
            lines = fh.read().splitlines()
    except (OSError, TypeError):
        return {}
    try:
        at = lines.index('| Step | Target | Result | Seconds | Why |') + 2
    except ValueError:
        return {}
    names = [line.split('|')[1].strip() for line in lines[at:at + len(run.get('steps') or [])] if line.startswith('|')]
    return {s['step']: n for s, n in zip(run.get('steps') or [], names)}


def label(run, step):
    return labels(run).get(step, step)


def running():
    """Who holds the tower's one lock now ('' when nobody): the lock file says 'pid N since ...' while a chain runs and is
    emptied when it ends; a holder whose process is gone holds nothing."""
    try:
        with open(where.report('nightly_lock'), encoding='utf-8') as fh:
            said = fh.read().strip()
    except OSError:
        return ''
    try:
        os.kill(int(said.split()[1]), 0)
    except (IndexError, ValueError):
        return said
    except ProcessLookupError:
        return ''
    except PermissionError:
        pass
    return said


def targets():
    """The native targets, as global_config.json names them (tower.native.targets): {name: its output folder}."""
    got = _json(where.path('global_config')) or {}
    return ((got.get('tower') or {}).get('native') or {}).get('targets') or {}


def kept(target):
    """The kept build of a target: {target, commit, made_at, bundle, environment[, transferred_at]}, or None."""
    return _json(where.path('native_builds', target, 'build.json'))


def tested(target):
    """The test of the kept build: {commit, verdict, made_at, walked, red, known, folder[, hotfixes][, report]}, or None."""
    return _json(where.path('native_builds', target, 'test.json'))


def night(day):
    """The night's build of this day, as its own chain left it (None before it began)."""
    last = latest('local')
    return last if last and schedule._in(day, last.get('started')) else None


def steps(what, *names):
    """A row of the night's build: these steps of the chain, their own seconds made into its start and end."""
    def check(day, folder=None):
        run = night(day)
        if not run:
            return schedule.said(None, "not yet: the night's build has not begun")
        at, start, end, mine = datetime.datetime.fromisoformat(run['started']), '', '', []
        for s in run['steps']:
            after = at + datetime.timedelta(seconds=float(s.get('seconds') or 0))
            if s['step'] in names:
                start, end = start or at.isoformat(), after.isoformat()
                mine.append(s)
            at = after
        if len(mine) < len(names):
            return schedule.said(None if run.get('ok') is None else False, f"the night's build did not reach it ({len(mine)} of {len(names)} step(s) ran)", start, end)
        said = labels(run)
        bad = [f"{said.get(s['step'], s['step'])}: {s.get('why', 'red')}"[:140] for s in mine if not s.get('ok')]
        return schedule.said(not bad, '; '.join(bad) if bad else what(mine), start, end)
    return check


def screen_files(tree, device, ids, most=4):
    """THE FILES THAT DRAW A SCREEN (the owner 2026-10-24 08:46: the broken script named, with COPY, never a rerun line): the
    generated app's Swift sources under <tree>/<macos|ios>/Sources that carry the screen's own id (its last part:
    'walk/sign_in/dashboard_links' -> dashboard_links), found by grep; at most `most` paths; none found: []."""
    import subprocess
    folder = os.path.join(str(tree or ''), 'ios' if device == 'iphone' else 'macos', 'Sources')
    out = []
    if not os.path.isdir(folder):
        return out
    for i in ids or ():
        token = str(i or '').strip().rstrip('/').split('/')[-1]
        if not token:
            continue
        try:
            got = subprocess.run(['grep', '-rlF', '--include=*.swift', token, folder], capture_output=True, text=True, timeout=20).stdout.split()
        except (OSError, subprocess.SubprocessError):
            got = []
        for path in sorted(got):
            if path not in out:
                out.append(path)
    return out[:most]


def swift_in(words):
    """the Swift files a build's words name (the compiler's "<path>.swift:12:3: error"), each once"""
    out = []
    for m in re.finditer(r'(/[^\s:\'"]+\.swift)', str(words or '')):
        if m.group(1) not in out:
            out.append(m.group(1))
    return out
