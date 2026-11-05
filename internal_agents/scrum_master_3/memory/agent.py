"""MEMORY, Scrum Master 3's LIVE check, on demand: the 3 way switch works or not. Red: the knowledge store not there or its entries
not reading; Claude Code's settings unreadable, the prompt hook or the write block not wired, an old Cortex hook still wired; no
known-answer questions; a known question answered with no position or without its expected entry in the first known_within, or
the door not answering (the asking stops there). The memory's live updates today (entries added and changed, prompts routed) are
information, never the light. The store is opened read only; the door is asked with its read-only ask; questions' words never said."""
import datetime
import html
import json
import os
import sqlite3
import subprocess
import time
import zoneinfo

import look as lookkit
import office

HAND = 'YOUR 3 MIN: '
NOT_WORKING = 'the 3 way switch does not work: '


def store():
    path = office.fact('db')
    if not os.path.exists(path):
        return None
    con = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=5)
    return con


def entries(con):
    try:
        return int(con.execute('SELECT count(*) FROM entries').fetchone()[0]) if con is not None else None
    except (sqlite3.Error, TypeError, IndexError):
        return None


def updates(con):
    zone = zoneinfo.ZoneInfo(office.fact('zone'))
    day = datetime.datetime.now(zone).date()
    since = (day - datetime.timedelta(days=1)).isoformat()

    def local(stamp):
        try:
            t = datetime.datetime.fromisoformat(str(stamp))
        except (TypeError, ValueError):
            return None
        return (t if t.tzinfo else t.replace(tzinfo=zone)).astimezone(zone).date()
    out = {'today': day.isoformat(), 'newest_entry': None, 'newest_change': None, 'added_today': None, 'changed_today': None,
           'newest_route': None, 'routes_today': None}
    if con is None:
        return out
    try:
        rows = con.execute('SELECT created_at, updated_at FROM entries WHERE updated_at >= ? OR created_at >= ?', (since, since)).fetchall()
        out['newest_entry'], out['newest_change'] = con.execute('SELECT max(created_at), max(updated_at) FROM entries').fetchone()
        out['added_today'] = sum(1 for r in rows if local(r[0]) == day)
        out['changed_today'] = sum(1 for r in rows if local(r[1]) == day)
    except sqlite3.Error:
        pass
    try:
        ats = [r[0] for r in con.execute('SELECT at FROM routes WHERE at >= ?', (since,))]
        out['newest_route'] = con.execute('SELECT max(at) FROM routes').fetchone()[0]
        out['routes_today'] = sum(1 for a in ats if local(a) == day)
    except sqlite3.Error:
        pass
    return out


def updates_said(u):
    n = lambda v: '?' if v is None else v  # noqa: E731
    at = lambda v: str(v)[:16].replace('T', ' ') if v else 'none'  # noqa: E731
    return (f"live updates today ({u['today']}): {n(u['added_today'])} entries added, {n(u['changed_today'])} changed, the newest written "
            f"{at(u['newest_entry'])}, changed {at(u['newest_change'])}; {n(u['routes_today'])} prompts routed, the newest {at(u['newest_route'])}")


def hook_step(which):
    cmd = f"env PYTHONPATH={os.path.join(office.fact('home'), 'app')} PYTHONDONTWRITEBYTECODE=1 {office.fact('python')} {office.fact(which + '_hook')}"
    entry = (f'"UserPromptSubmit": [{{"hooks": [{{"type": "command", "command": "{cmd}"}}]}}]' if which == 'prompt' else
             f'"PreToolUse": [{{"matcher": "{office.fact("write_matcher")}", "hooks": [{{"type": "command", "command": "{cmd}"}}]}}]')
    return f"put back in {office.fact('settings')}, under \"hooks\": {entry} (seconds)"


def hooks():
    """-> (what is missing, its step)"""
    try:
        with open(office.fact('settings'), encoding='utf-8') as fh:
            got = json.load(fh).get('hooks') or {}
    except (OSError, ValueError, AttributeError):
        return ["Claude Code's settings cannot be read"], office.fact('settings_step')
    cmds = lambda event: ' '.join(h.get('command', '') for g in got.get(event) or [] for h in g.get('hooks') or [])  # noqa: E731
    out = []
    if office.fact('prompt_hook') not in cmds('UserPromptSubmit'):
        out.append(('the prompt hook does not run the 3 way switch', hook_step('prompt')))
    if office.fact('write_hook') not in cmds('PreToolUse'):
        out.append(('the write block is not on', hook_step('write')))
    if office.fact('old_hook_word') in cmds('UserPromptSubmit') + cmds('SessionStart'):
        out.append(('the old Cortex hooks are still wired', office.fact('old_hook_step')))
    return [w for w, _ in out], (out[0][1] if out else '')


def questions():
    try:
        with open(office.fact('known_questions'), encoding='utf-8') as fh:
            known = json.load(fh)
    except (OSError, ValueError):
        return []
    return [(str(k['question']), {k['expect']} if isinstance(k['expect'], str) else set(k['expect']))
            for k in (known if isinstance(known, list) else []) if isinstance(k, dict) and k.get('question') and k.get('expect')]


def ask(question):
    seconds = office.fact('switch_seconds')
    t0 = time.monotonic()
    try:
        done = subprocess.run([office.fact('door'), 'ask', question], capture_output=True, text=True, timeout=seconds,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        got = json.loads(done.stdout or 'null')
    except subprocess.TimeoutExpired:
        return {'fault': f'did not answer within {seconds} s'}
    except (OSError, subprocess.SubprocessError, ValueError) as no:
        return {'fault': f'did not answer: {type(no).__name__}: {no}'[:160]}
    if not isinstance(got, dict):
        return {'fault': 'gave no answer (no JSON on its stdout)'}
    return {'position': str(got.get('position')), 'keys': [d.get('key') for d in got.get('delivered') or [] if isinstance(d, dict)],
            'ms': got.get('ms') if got.get('ms') is not None else round((time.monotonic() - t0) * 1000)}


def switch(known):
    within, positions = office.fact('known_within'), office.fact('positions')
    right, wrong, slowest, first, door = 0, [], 0.0, 0, False
    for n, (q, want) in enumerate(known, 1):
        got = ask(q)
        if got.get('fault'):
            wrong.append(f"question {n} of {len(known)}: the door {got['fault']}")
            first, door = first or n, not first
            break
        try:
            slowest = max(slowest, float(got['ms'] or 0))
        except (TypeError, ValueError):
            pass
        if got['position'] not in positions:
            wrong.append(f'question {n}: no position answered')
        elif not want & set(got['keys'][:within]):
            wrong.append(f"question {n}: {positions[got['position']]} answered, the right entry not in its first {within}")
        else:
            right += 1
            continue
        first = first or n
    return {'asked': len(known), 'right': right, 'wrong': wrong, 'ms': slowest, 'first': first, 'door': door}


def fit(head, tail):
    most = office.fact('most')
    return head + tail if len(head) + len(tail) <= most else head[:max(0, most - len(tail) - 1)].rstrip() + '...' + tail


def run(given):
    whys, step = [], ''
    con = store()
    try:
        n = entries(con)
        live = updates(con if n is not None else None)
    finally:
        if con is not None:
            con.close()
    if n is None:
        whys.append('the knowledge store is not there' if not os.path.exists(office.fact('db')) else 'the knowledge store does not read')
        step = office.fact('store_step')
    unwired, fix = hooks()
    if unwired:
        whys.append('the hooks are not wired: ' + '; '.join(unwired))
        step = step or fix
    known, got = questions(), None
    if not known:
        whys.append('no known-answer questions to ask it')
        step = step or office.fact('questions_step')
    else:
        got = switch(known)
        if got['wrong']:
            whys.append(f"{len(got['wrong'])} of {got['asked']} questions not answered right ({got['wrong'][0]}"
                        + (f", and {len(got['wrong']) - 1} more" if len(got['wrong']) > 1 else '') + ')')
            step = step or office.fact('door_step' if got['door'] else 'switch_step').format(n=got['first'])
    info = updates_said(live)
    state = 'RED' if whys else 'GREEN'
    if whys:
        line = 'RED · ' + fit(NOT_WORKING + ' · '.join(whys) + ' · ' + info, f' · {HAND}{step}')
    else:
        line = (f"GREEN · the 3 way switch works: {got['right']} of {got['asked']} questions answered right, the slowest in {got['ms']:.0f} ms "
                f"(the store: {n} entries) · the hooks are wired · {info}")
    office.live_set(office.fact('live_key'), office.me()['name'], state, line, ' · '.join(whys), step)
    return office.done(line, state, {'at': office.stamp(), 'why': ' · '.join(whys), 'step': step, 'entries': n, 'updates': live,
                                     'switch': got})


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
