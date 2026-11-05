"""NO SHORTCUTS, Scrum Master 3's LIVE check, on demand (the owner: "the rule set by the system owner gets changed. this should
detect that. also any direct edits to the ... reports to change a result"; "ths speed lock is very important"). Three checks:
(a) the owner's rule: every job of this workflow has its part 1 (data_job_rule); its sha256 per job is kept in this agent's own
    RUN data. Red when a job's rule differs from it (changed or emptied) until he accepts (facts accepted_at). A new job, a job
    removed or an empty rule filled once is noted, never red.
(b) a result edited by hand: every LIVE row in the office database (live_status) whose job ran must say what that job's last RUN
    delivered (its light and its line); a row that differs was written by a hand, not its RUN.
(c) the speed lock: each pinned speed check file byte for byte as pinned (facts speed_pins). Never re-pinned here."""
import datetime
import hashlib
import html
import os
import subprocess

import look as lookkit
import office

HAND = 'YOUR 3 MIN: '


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else str(data).encode('utf-8')).hexdigest()


def plain(text):
    return ' '.join(str(text or '').split())[:office.fact('compare_chars')]


def rules(blocks, base):
    reds, notes, kept = [], [], {}
    for j in blocks:
        key, name, rule = j.get('key') or j.get('data_agent_key'), j.get('data_full_name') or '', j.get('data_job_rule') or ''
        cur = {'name': name, 'sha': sha(rule) if rule else ''}
        was = base.get(key)
        if was is None:
            notes.append(f'{name}: a new job, its rule recorded')
            kept[key] = cur
        elif was['sha'] == cur['sha'] or not was['sha']:
            if not was['sha'] and cur['sha']:
                notes.append(f'{name}: its empty rule filled once, recorded')
            kept[key] = cur
        else:
            kept[key] = was
            how = 'emptied' if not cur['sha'] else f"sha256 {was['sha'][:12]} -> {cur['sha'][:12]}"
            reds.append({'kind': 'rule', 'what': f"the owner's rule of {name} ({key}) changed: {how}", 'step': office.fact('accept_step')})
    for key, was in base.items():
        if key not in kept:
            notes.append(f"{was.get('name') or key}: its job is gone, dropped")
    return reds, notes, kept


def results(blocks, own_key):
    """each LIVE row against its own job's last RUN (the newest job by that name)"""
    newest = {}
    for j in blocks:
        if j.get('data_agent_key') != own_key and j.get('data_job_last_run_at') and j.get('data_job_delivery'):
            name = j.get('data_full_name')
            if str(j['data_job_last_run_at']) > str((newest.get(name) or {}).get('data_job_last_run_at') or ''):
                newest[name] = j
    reds, n = [], 0
    for row in office.live_all():
        job = newest.get(row['name'])
        if not job or job.get('data_job_run_state') not in ('DONE', 'FAILED'):
            continue
        n += 1
        line = str(job['data_job_delivery']).split('\n', 1)[0]
        light = office.light_of(job)
        if row['state'] != light or plain(row['summary']) != plain(line):
            what = (f"{row['name']}: its row says {row['state']} '{plain(row['summary'])[:80]}', its last RUN ({job['data_job_last_run_at']}) "
                    f"delivered {light} '{plain(line)[:80]}'")
            reds.append({'kind': 'result', 'what': what, 'step': office.fact('result_step').format(name=row['name'])})
    return reds, n


def git(root, *args, text=True):
    try:
        return subprocess.run(['git', '-C', root, *args], capture_output=True, text=text, timeout=office.fact('git_seconds'),
                              env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
    except (OSError, subprocess.SubprocessError):
        return None


def restore_step(path, pin):
    top = git(os.path.dirname(path), 'rev-parse', '--show-toplevel')
    if top is not None and top.returncode == 0:
        top = top.stdout.strip()
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(top))
        log = git(top, 'log', '--format=%h', '-n', str(office.fact('commits')), '--', rel)
        for h in (log.stdout.split() if log is not None and log.returncode == 0 else []):
            blob = git(top, 'show', f'{h}:{rel}', text=False)
            if blob is not None and blob.returncode == 0 and sha(blob.stdout) == pin:
                return f'put it back exactly as pinned: git -C {top} checkout {h} -- {rel}' + office.fact('repin')
    return f'put it back exactly as pinned (sha256 {pin[:12]}): no commit of its git holds those bytes; from your own copy' + office.fact('repin')


def speed():
    pins = office.fact('speed_pins') or []
    if not pins:
        return [{'kind': 'speed', 'what': 'no speed check is pinned: facts speed_pins lists no file', 'step': office.fact('pin_step')}], 0
    reds = []
    for f in pins:
        path, pin = os.path.expanduser(str(f.get('path') or '')), str(f.get('sha256') or '')
        try:
            with open(path, 'rb') as fh:
                data = fh.read()
        except OSError:
            data = None
        if not pin:
            reds.append({'kind': 'speed', 'what': f'{os.path.basename(path)}: no pin', 'step': office.fact('pin_step')})
        elif data is None:
            reds.append({'kind': 'speed', 'what': f'{os.path.basename(path)}: gone ({path})', 'step': restore_step(path, pin)})
        elif sha(data) != pin:
            reds.append({'kind': 'speed', 'what': f'{os.path.basename(path)}: changed (sha256 {sha(data)[:12]}, pinned {pin[:12]})', 'step': restore_step(path, pin)})
    return reds, len(pins)


def run(given):
    was = office.data_of(office.own_job(given))
    accepted = str(office.fact('accepted_at') or '')
    blocks = office.workflow(given)
    base = {} if accepted != str(was.get('accepted_at') or '') else (was.get('rules') or {})
    r_reds, notes, kept = rules(blocks, base)
    if not was.get('rules'):
        notes = [f'its first RUN: {len(kept)} rule(s) recorded as the baseline']
    elif not base:
        notes = [f'accepted ({accepted}): {len(kept)} rule(s) taken as they are now']
    p_reds, n_rows = results(blocks, office.me()['key'])
    s_reds, n_speed = speed()
    reds = r_reds + p_reds + s_reds
    state = 'RED' if reds else 'GREEN'
    steps = list(dict.fromkeys(r['step'] for r in reds))
    line = (f'GREEN · {len(kept)} owner rule(s) as set, {n_rows} result(s) as their RUN wrote them, {n_speed} speed check(s) as pinned' if not reds
            else 'RED · ' + '; '.join(r['what'] for r in reds)[:400] + f' · {HAND}{steps[0]}')
    office.live_set(office.fact('live_key'), office.me()['name'], state, line, '; '.join(r['what'] for r in reds)[:600], ' · '.join(steps))
    return office.done(line, state, {'at': office.stamp(), 'reds': reds, 'notes': notes, 'rules': kept, 'accepted_at': accepted,
                                     'rules_n': len(kept), 'results_n': n_rows, 'speed_n': n_speed})


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
