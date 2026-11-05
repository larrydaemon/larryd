"""AUDIT, Scrum Master 3's LIVE check, on demand: three questions, any one failing is red with the owner's one step.
1 the agent lock: ~/virtual_sanity's own flags, the sessions' sandbox, the master mark. All locked, or the master open by his own
  press, is green; the master closed while the folders or the sessions stand unlocked (a half lock) is red.
2 The Pin and its reseal: The Pin's own job in this workflow, its last RUN's seal (A5, B) and pin (A3) both said and passing.
3 every office host of global_config.json (each office's rnd port, each mini's, wid's pf) answers an HTTP GET in time."""
import datetime
import html
import json
import os
import stat
import urllib.error
import urllib.request

import look as lookkit
import office

HAND = 'YOUR 3 MIN: '
FLAGS = stat.SF_IMMUTABLE | stat.UF_IMMUTABLE


def flagged(path):
    try:
        return bool(os.lstat(path).st_flags & FLAGS)
    except OSError:
        return False


def folders_lock(top):
    """LOCKED when the top and every file under it carry the immutable flag (stops at the first that does not)"""
    if not flagged(top):
        return 'UNLOCKED'
    skip, seen = set(office.fact('never_counted')), 0
    for root, dirs, names in os.walk(top):
        dirs[:] = [d for d in dirs if d not in skip]
        for n in names:
            if n in skip:
                continue
            seen += 1
            if not flagged(os.path.join(root, n)):
                return 'UNLOCKED'
    return 'LOCKED' if seen else 'UNLOCKED'


def lock_now():
    sanity = office.fact('sanity').rstrip('/')
    try:
        with open(office.fact('sessions_sandbox'), encoding='utf-8') as fh:
            sessions = 'LOCKED' if f'(subpath "{sanity}")' in fh.read() else 'UNLOCKED'
    except OSError:
        sessions = 'LOCKED'
    try:
        database = 'UNLOCKED' if os.stat(office.fact('master_mark')).st_uid == 0 else 'LOCKED'
    except OSError:
        database = 'LOCKED'
    return {'folders': folders_lock(sanity), 'sessions': sessions, 'database': database}


def unlocked():
    lock = lock_now()
    parts = ', '.join(f'{k} {lock[k]}' for k in ('folders', 'sessions', 'database'))
    if lock['database'] == 'UNLOCKED':
        return True, f'unlocked by your press (master open): {parts}', ''
    if lock['folders'] == lock['sessions'] == 'LOCKED':
        return True, f'locked ({parts})', ''
    return False, f'the agent is half locked: MASTER CLOSED, but {parts}', office.fact('lock_step')


def pin_sync(given):
    name, step = office.fact('pin_name'), office.fact('pin_step')
    jobs = [j for j in office.workflow(given) if j.get('data_full_name') == name]
    if not jobs:
        return False, f'the pin and reseal cannot be read: no {name} in this workflow', step
    job = max(jobs, key=lambda j: str(j.get('data_job_last_run_at') or ''))
    light, got = office.light_of(job), office.data_of(job)
    if not job.get('data_job_last_run_at'):
        return False, f'the pin and reseal cannot be read: {name} has not run yet', step
    if light == 'RED':
        why = got.get('text') or str(job.get('data_job_today_said') or '').split('\n')[0] or f'{name} ended red'
        return False, f'the pin and reseal are not in sync: {why[:200]}', got.get('step') or step
    seal, hammer = str(got.get('seal') or ''), str(got.get('hammer') or '')
    if not seal or not hammer:
        return False, f"the pin and reseal cannot be compared: {name}'s last run does not say {'the seal' if not seal else 'the pin'}", step
    bad = [f'{label}: {v[:120]}' for label, v in (('the seal', seal), ('the pin', hammer)) if not v.endswith(' pass')]
    if bad or got.get('held'):
        return False, 'the pin and reseal are not in sync: ' + ('; '.join(bad) or 'held, not pinned yet'), got.get('step') or step
    return True, f'pin and seal in sync (the seal: {seal[:120]}; the pin: {hammer[:80]}; {name} at {job.get("data_job_last_run_at")})', ''


def hosts(config):
    out, offices = [], config.get('offices') or {}
    for name, o in offices.items():
        out.append((name, int(o['ports']['rnd'])))
        if isinstance(o.get('mini'), dict) and (o['mini'].get('ports') or {}).get('rnd'):
            out.append((f'{name}-mini', int(o['mini']['ports']['rnd'])))
    wid = (offices.get('wid') or {}).get('ports') or {}
    if wid.get('pf') and wid['pf'] != wid.get('rnd'):
        out.append(('wid pf', int(wid['pf'])))
    return out


def answers(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=office.fact('host_seconds')):
            return True
    except urllib.error.HTTPError as no:   # any HTTP answer, even an error page, is online
        no.close()
        return True
    except (OSError, ValueError):
        return False


def online():
    with open(office.fact('global_config'), encoding='utf-8') as fh:
        listed = hosts(json.load(fh))
    if not listed:
        return False, 'no office is listed (global_config.json offices is empty)', office.fact('empty_step')
    down = [(n, p) for n, p in listed if not answers(p)]
    if down:
        return False, 'down: ' + ', '.join(f'{n} (port {p})' for n, p in down) + f' · {len(listed) - len(down)} of {len(listed)} hosts online', office.fact('hosts_step')
    return True, f'{len(listed)} hosts online', ''


def run(given):
    answered = []
    for n, ask in ((1, unlocked), (2, lambda: pin_sync(given)), (3, online)):
        try:
            ok, said, step = ask()
        except Exception as fault:   # noqa: BLE001  a question that cannot be read is red
            ok, said, step = False, f"could not be read ({type(fault).__name__}: {' '.join(str(fault).split())[:120]})", office.fact('crash_step')
        answered.append({'n': n, 'ok': ok, 'said': said, 'step': step})
    bad = [a for a in answered if not a['ok']]
    words = ' · '.join(f"{a['n']} {a['said']}" for a in bad + [a for a in answered if a['ok']])
    step = bad[0]['step'] if bad else ''
    state = 'RED' if bad else 'GREEN'
    line = f'{state} · {words}' + (f' · {HAND}{step}' if step else '')
    office.live_set(office.fact('live_key'), office.me()['name'], state, line, '' if not bad else bad[0]['said'], step)
    return office.done(line, state, {'at': office.stamp(), 'answers': answered, 'step': step})


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
