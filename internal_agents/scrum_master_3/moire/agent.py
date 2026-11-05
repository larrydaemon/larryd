"""MOIRÉ, Scrum Master 3's LIVE check, on demand (the owner: "red is only if its not running. a change is not a red"). Green
whenever the change report runs, whatever it shows: the drift the lie detector's probe D3 counts since the baseline (written
changes) and the workspace's files not as git has them (not committed yet) are information only. Red ONLY when the report is not
running: the lie detector's report missing, unreadable, past its deadman or ahead of the clock, no D3 or no drift count in it, or
git not answering for the workspace. A missing baseline is never red. git is asked with no optional locks (read only)."""
import datetime
import html
import json
import os
import re
import subprocess
import time

import look as lookkit
import office

HAND = 'YOUR 3 MIN: '
NOT_WORKING = 'the report is not working: '


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def drift():
    """(count or None, its words, why the report does not work or '')"""
    path = office.fact('report')
    raw = _json(path)
    if raw is None:
        return None, '', (f'the lie detector has never run (no report at {path})' if not os.path.exists(path) else f"the lie detector's report is unreadable ({path})")
    if not isinstance(raw, dict) or not isinstance(raw.get('rows'), list):
        return None, '', "the lie detector's report is not a whole report (no rows)"
    try:
        deadman = int(((_json(office.fact('console')) or {}).get('cebf') or {}).get('deadman') or office.fact('deadman'))
    except (TypeError, ValueError, AttributeError):
        deadman = office.fact('deadman')
    try:
        at = datetime.datetime.fromisoformat(raw['at'])
        age = int((datetime.datetime.now(datetime.timezone.utc) - (at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc))).total_seconds())
    except (ValueError, KeyError, TypeError):
        return None, '', "the lie detector's report has no readable time (at)"
    of = f"report of {str(raw.get('at', ''))[11:16]} UTC"
    if age > deadman or age < -office.fact('ahead'):
        return None, '', f'the lie detector is silent: its {of} is older than its deadman ({deadman} s; {age} s old)'
    probe = office.fact('probe')
    p = {r.get('id'): r for r in raw['rows'] if isinstance(r, dict)}.get(probe)
    if not p:
        return None, '', f'the lie detector wrote no probe {probe}'
    detail = str(p.get('detail', ''))
    if p.get('verdict') == office.fact('pass'):
        return 0, ' · '.join(x for x in (detail, of) if x), ''
    m = re.match(office.fact('drift_words'), detail)
    if m:
        return int(m.group(1)), f'{detail} · {of}', ''
    if re.search(office.fact('no_baseline_words'), detail):
        return None, f'{detail} · {of}', ''
    return None, '', f"the lie detector's {probe} gave no drift count ({p.get('verdict')}: {detail[:80]}; {of})"


def written():
    """the workspace's files not as committed, asked of git (read only): {read, drift, first}"""
    workspace = office.fact('workspace')
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    ends = time.monotonic() + office.fact('git_seconds')
    git = lambda *a: subprocess.run(['git', '-C', workspace, *a], capture_output=True, encoding='utf-8', errors='replace',  # noqa: E731
                                    timeout=max(1, ends - time.monotonic()), env=env)
    try:
        top, said = git('rev-parse', '--show-toplevel'), git('status', '--porcelain=v1', '-z', '--untracked-files=all')
    except (OSError, subprocess.SubprocessError):
        return {'read': False, 'drift': None, 'first': []}
    if top.returncode or said.returncode or os.path.realpath(top.stdout.strip()) != os.path.realpath(workspace):
        return {'read': False, 'drift': None, 'first': []}
    entries, n, first = said.stdout.split('\0'), 0, []
    while entries:
        entry = entries.pop(0)
        if len(entry) < 4:
            continue
        if ('R' in entry[:2] or 'C' in entry[:2]) and entries:
            entries.pop(0)   # a rename names its old path next: one change
        n += 1
        if len(first) < office.fact('first_files'):
            first.append(entry[3:])
    return {'read': True, 'drift': n, 'first': first}


def fit(head, tail):
    most = office.fact('most')
    return head + tail if len(head) + len(tail) <= most else head[:max(0, most - len(tail) - 1)].rstrip() + '...' + tail


def run(given):
    frozen = _json(office.fact('baseline'))
    count, detail, why = drift()
    wrote = written()
    broken = ([why] if why else []) + ([] if wrote['read'] else ['git did not answer for the workspace (not a repository top, or git silent)'])
    loose = wrote['drift'] or 0
    if not (isinstance(frozen, dict) and frozen):
        base = office.fact('no_baseline_said')
    elif count is None:
        base = detail or f"the lie detector's {office.fact('probe')} not read"
    else:
        base = f"{count} drifted since the baseline (the lie detector, {office.fact('probe')})" + (f': {detail}' if detail else '')
    files = (f'{loose} file(s) not committed yet' + (f" ({', '.join(wrote['first'])}{', ...' if loose > len(wrote['first']) else ''})" if loose else '')
             if wrote['read'] else 'files not committed: not read (git did not answer)')
    changes = {'written': {'count': count, 'said': base}, 'unwritten': {'count': wrote['drift'], 'first': wrote['first'], 'said': files}}
    if broken:
        step = office.fact('rerun') if why else office.fact('git_step')
        line = 'RED · ' + fit(NOT_WORKING + '; '.join(broken) + f' · {base} · {files}', f' · {HAND}{step}')
        office.live_set(office.fact('live_key'), office.me()['name'], 'RED', line, '; '.join(broken), step)
        return office.done(line, 'RED', {'at': office.stamp(), 'why': '; '.join(broken), 'step': step, 'changes': changes})
    line = f'GREEN · working · {base} · {files}'
    office.live_set(office.fact('live_key'), office.me()['name'], 'GREEN', line)
    return office.done(line, 'GREEN', {'at': office.stamp(), 'why': '', 'step': '', 'changes': changes})


def canvas(given):
    """SM2's LIVE BLOCK, one line (page.py live_block): the name as a title, the state word in its colour and the time since that state
    began (RUNNING while its RUN is open, IDLE when its light is GREEN, NOT RUNNING when it is RED or it never ran), the group on the right"""
    job = office.own_job(given)
    light = office.light_of(job)
    row = next((r for r in office.live_all() if r['key'] == office.fact('live_key')), {})
    if str(job.get('data_job_run_state') or '').upper() in ('QUEUED', 'RUNNING'):
        word, cls, began = 'RUNNING', 'hdr-status--success', job.get('system_updated_at')
    else:
        word, cls = ('IDLE', 'scrum-idle') if light == 'GREEN' else ('NOT RUNNING', 'hdr-status--error')
        began = row.get('changed_at') if row.get('state') == light else job.get('data_job_last_run_at')
    try:
        t = datetime.datetime.fromisoformat(str(began or '').replace('Z', '+00:00'))
        s = max(0, int((office.now() - (t if t.tzinfo else t.replace(tzinfo=office.now().tzinfo))).total_seconds()))
        clock = f'<span class="scrum-since {cls}"> ' + (f'{s // 3600} H ' if s >= 3600 else '') + (f'{s % 3600 // 60} MIN ' if s >= 60 else '') + f'{s % 60} S</span>'
    except ValueError:
        clock = ''
    key, e = office.fact('live_key'), html.escape
    return lookkit.view(f'<div class="replica-live-block" data-live-block="{e(key)}"><div class="title scaf-law-title">{e(office.me()["name"])}</div>'
                        f'<div class="replica-live-line" data-live-key="{e(key)}" data-live-state="{e(light)}"><div class="subtitle"><span class="{cls}">{word}</span>{clock}</div></div>'
                        f'<span class="replica-live-group" aria-label="group">{e(office.me().get("group") or "LIVE")}</span></div>',
                        (given.get('page') or {}).get('path') or '', office.fact('css') or '')


if __name__ == '__main__':
    office.main(canvas, run)
