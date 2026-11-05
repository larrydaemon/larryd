"""THE PIN, Scrum Master 3's LIVE check, on demand: the lie detector's own report (read only), the Judge's pin (A3, the hammer)
and the core's seal (A5 and every B) said together. Red: the report missing, unreadable, past its deadman or dated ahead of the
clock; the probes not in it; any of them not PASS for a real fault. Green: all PASS in a current report. Held (green, 'held: ...'):
every probe that is not a PASS says only no pin or no baseline, nothing pinned yet on the owner's word."""
import datetime
import html
import json
import re
import subprocess
import zoneinfo

import look as lookkit
import office

HAND = 'YOUR 3 MIN: '
PIN_OF = re.compile(r'pin of (\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})')


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def seen():
    """the report ({at, rows} or None), its age and whether it is silent (past its deadman or ahead of the clock)"""
    got = _json(office.fact('report'))
    got = got if isinstance(got, dict) and isinstance(got.get('rows'), list) else None
    try:
        deadman = int(((_json(office.fact('console')) or {}).get('cebf') or {}).get('deadman') or office.fact('deadman'))
    except (TypeError, ValueError, AttributeError):
        deadman = office.fact('deadman')
    age = None
    if got:
        try:
            at = datetime.datetime.fromisoformat(got['at'])
            age = int((datetime.datetime.now(datetime.timezone.utc) - (at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc))).total_seconds())
        except (ValueError, KeyError, TypeError):
            got = None
    return {'report': got, 'age': age, 'deadman': deadman, 'silent': got is not None and (age > deadman or age < -office.fact('ahead'))}


def part(state, what, ids):
    """-> {'ok': True|False|None (held), 'said'}"""
    rows_by = {p['id']: p for p in ((state['report'] or {}).get('rows') or []) if isinstance(p, dict) and 'id' in p}
    rows = [(i, p.get('verdict'), str(p.get('detail', ''))) for i, p in rows_by.items()
            if i in ids or any(x.endswith('*') and i.startswith(x[:-1]) for x in ids)]
    if state['silent'] or not state['report']:
        return {'ok': False, 'said': f'the lie detector is silent: {what} cannot be read'}
    if not rows:
        return {'ok': False, 'said': f"the lie detector's report has no {what} probes ({', '.join(ids)}): {what} cannot be read"}
    bad = [f'{i} {v}: {d}'[:120] for i, v, d in rows if v != office.fact('pass')]
    held = [i for i, v, d in rows if v != office.fact('pass') and re.search(office.fact('held_words'), d)]
    if bad and len(held) == len(bad):
        return {'ok': None, 'said': f"not pinned yet, on the owner's word: {', '.join(held)}"}
    if bad:
        return {'ok': False, 'said': '; '.join(bad[:3]) + (f' (+{len(bad) - 3} more)' if len(bad) > 3 else '')}
    return {'ok': True, 'said': f"{what}: {', '.join(i for i, _, _ in rows)} pass"}


def running():
    try:
        got = subprocess.run(['pgrep', '-f', office.fact('running')], capture_output=True, text=True, timeout=10)
        return next((p for p in got.stdout.split() if p.isdigit()), '')
    except (OSError, subprocess.SubprocessError):
        return ''


def fit(head, tail):
    most = office.fact('most')
    return head + tail if len(head) + len(tail) <= most else head[:max(0, most - len(tail) - 1)].rstrip() + '...' + tail


def judge():
    state = seen()
    hammer, seal = part(state, 'the Judge', office.fact('hammer_probes')), part(state, 'the core', office.fact('seal_probes'))
    oks = (hammer['ok'], seal['ok'])
    try:
        at = datetime.datetime.fromisoformat(str(state['report']['at']))
        at = (at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc)).astimezone(zoneinfo.ZoneInfo(office.fact('zone'))).strftime('%b %d %H:%M')
    except (TypeError, ValueError, KeyError):
        at = ''
    text = f"the hammer: {hammer['said']} · the seal: {seal['said']}" + (f' · the lie detector of {at}' if at else '')
    out = {'hammer': hammer['said'], 'seal': seal['said'], 'report_at': at, 'age': state['age'], 'deadman': state['deadman'],
           'held': False, 'step': '', 'waiting': ''}
    if False not in oks and None in oks:
        return {**out, 'state': 'GREEN', 'held': True, 'text': 'held: ' + text}
    if False not in oks:
        return {**out, 'state': 'GREEN', 'text': text}
    saids = (hammer['said'], seal['said'])
    pid = running()
    rerun = office.fact('rerun')
    if any('has no' in s and 'probes' in s for s in saids):
        out['step'] = f"these probes are not in the lie detector's report: put them back in its configuration ({office.fact('console')}, the cebf entry), then run it: {rerun}"
    elif any('cannot be read' in s for s in saids):
        out['step'] = rerun
    else:
        newer = [m.group(1) for s in saids for m in PIN_OF.finditer(s) if m.group(1).replace(' ', 'T') > str(state['report'].get('at') or '')[:16]]
        if newer:
            out['waiting'] = f"the lie detector's next run (its report is older than your pin of {newer[0].replace('T', ' ')}; run it now: {rerun})"
        else:
            out['step'] = office.fact('pin_and_reseal')
    if pid and not out['waiting']:
        out['waiting'] = f'the lie detector running now (pid {pid})'
    tail = (f" · at work on it now: {out['waiting']}" if out['waiting'] else '') + (f" · {HAND}{out['step']}" if out['step'] else '')
    return {**out, 'state': 'RED', 'text': fit(text, tail)}


def run(given):
    got = judge()
    line = f"{got['state']} · {got['text']}"
    office.live_set(office.fact('live_key'), office.me()['name'], got['state'], line,
                    '' if got['state'] == 'GREEN' else f"{got['hammer']} · {got['seal']}", got['step'])
    return office.done(line, got['state'], {**got, 'at': office.stamp()})


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
