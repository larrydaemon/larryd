"""LIE DETECTOR, Scrum Master 3's LIVE check, on demand: the real health of the system, from the lie detector's own report (read
only). Green only when the report is fresh (within its deadman, never more than a minute ahead of the clock) and every one of the
12 pin and seal probes is in it and says PASS. Red for anything else, every failing probe named. Other probes are never counted.
Its step, never performed here: a pin that differs is the owner's PIN AND RESEAL; no fresh whole report, a probe missing or not
measured, or his pin newer than the report, is the lie detector run again."""
import datetime
import html
import json
import os
import re
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


def judge():
    path, rerun = office.fact('report'), 'run the lie detector again now (about 2 s): ' + office.fact('rerun')
    try:
        deadman = int(((_json(office.fact('console')) or {}).get('cebf') or {}).get('deadman') or office.fact('deadman'))
    except (TypeError, ValueError, AttributeError):
        deadman = office.fact('deadman')
    probes = office.fact('pin_probes')
    out = {'ok': False, 'failing': [], 'pins': [], 'missing': [], 'lines': [], 'at': '', 'age': None, 'probes': 0, 'deadman': deadman, 'step': rerun}
    if not os.path.exists(path):
        return {**out, 'said': f'the lie detector did not run: no report at {path}'}
    report = _json(path)
    if not isinstance(report, dict) or not isinstance(report.get('rows'), list):
        return {**out, 'said': f'the lie detector did not run: its report at {path} is unreadable'}
    try:
        at = datetime.datetime.fromisoformat(str(report.get('at')))
    except ValueError:
        return {**out, 'said': f"the lie detector did not run: its report has no moment ({report.get('at')!r})"}
    at = at if at.tzinfo else at.replace(tzinfo=datetime.timezone.utc)
    age = int((datetime.datetime.now(datetime.timezone.utc) - at).total_seconds())
    out.update(at=at.astimezone(zoneinfo.ZoneInfo(office.fact('zone'))).strftime('%b %d %H:%M'), age=age)
    if age > deadman:
        return {**out, 'said': f"the lie detector did not run: its report is of {out['at']}, {age // 60} min old, past its deadman of {deadman // 60} min"}
    if age < -office.fact('ahead'):
        return {**out, 'said': f"the lie detector did not run: its report of {out['at']} is dated ahead of the clock"}
    rows = [p for p in report['rows'] if isinstance(p, dict)]
    out['probes'] = len(rows)
    if not rows:
        return {**out, 'said': f"the lie detector did not run whole: its report of {out['at']} holds no probe"}
    ids = {str(p.get('id')) for p in rows}
    bad = [p for p in rows if str(p.get('id')) in probes and p.get('verdict') != office.fact('pass')]
    missing = [x for x in probes if x not in ids]
    pins = [str(p.get('id')) for p in bad if p.get('verdict') == office.fact('fail')]
    unmeasured = [str(p.get('id')) for p in bad if p.get('verdict') != office.fact('fail')]
    out.update(failing=[str(p.get('id')) for p in bad], pins=pins, missing=missing,
               lines=[f"{p.get('id')} {p.get('verdict')}: {' '.join(str(p.get('detail') or '').split())[:100]}" for p in bad])
    if not bad and not missing:
        return {**out, 'ok': True, 'step': '', 'said': f"healthy: all {len(probes)} pin and seal probes pass (report of {out['at']})"}
    parts = ([f"{len(bad)} of {len(probes)} pin and seal probes fail: " + ', '.join(out['failing'])] if bad else []) + \
            (['pin probe(s) not in the report: ' + ', '.join(missing)] if missing else [])
    after = max((m.group(1).replace('T', ' ') for p in bad for m in PIN_OF.finditer(str(p.get('detail') or ''))
                 if m.group(1).replace(' ', 'T') > str(report.get('at') or '')[:16]), default='')
    steps = ([office.fact('repin')] if pins and not after else []) + \
            ([f"run the lie detector again now (about 2 s; your pin of {after} is newer than this report): {office.fact('rerun')}" if after else rerun]
             if after or missing or unmeasured else [])
    return {**out, 'said': f"not healthy (report of {out['at']}): " + '; '.join(parts), 'step': ' · '.join(steps), 'after_pin': after}


def run(given):
    got = judge()
    state = 'GREEN' if got['ok'] else 'RED'
    line = f"{state} · {got['said']}" + (f" · {HAND}{got['step']}" if got['step'] else '')
    office.live_set(office.fact('live_key'), office.me()['name'], state, line, '' if got['ok'] else got['said'], got['step'])
    return office.done(line, state, {**got, 'checked': office.stamp()})


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
