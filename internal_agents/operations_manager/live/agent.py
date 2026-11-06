"""LIVE, the shared block of every MARK IV workflow (owned by Operations Manager), drawn as SCRUM MASTER 2's ACTIVE MONITORING panel
(look.py: SM2's own markup and sheets): the workflow's name, TODAY'S WORK from its X board's last RUN, what runs now (a block whose RUN is
open, else IDLE since the newest RUN), and the TOOL / STATUS NOW table read from the workflow's own blocks; a tool with no source here is a
dash. Its RUN counts the office's live_status rows (written by each LIVE check on its own RUN)."""
import datetime
import html
import re

import look
import office

OPEN = ('QUEUED', 'RUNNING')


def at(text):
    """a stored time (ET without a zone, or ISO with one) as an aware moment, None when it does not read"""
    try:
        got = datetime.datetime.fromisoformat(str(text or '').replace('Z', '+00:00'))
    except ValueError:
        return None
    return got if got.tzinfo else got.replace(tzinfo=office.now().tzinfo)


def ago(text):
    """SM2's own ticking words (its page's ago()), written at CALL time: ' 3 H 5 MIN 2 S'; '' when the time does not read"""
    t = at(text)
    if t is None:
        return ''
    s = max(0, int((office.now() - t).total_seconds()))
    h, m = s // 3600, s % 3600 // 60
    return ' ' + (f'{h} H ' if h else '') + (f'{m} MIN ' if h or m else '') + f'{s % 60} S'


def since(cls, text):
    return f'<span class="scrum-since {cls}">{html.escape(ago(text))}</span>' if ago(text) else ''


def rows(given):
    name = office.page_workflow(given)
    place = (office.fact('offices') or {}).get(name)
    if not place:
        raise ValueError(f'no office for the workflow {name!r}: the offices fact names none' if name else 'no workflow found for this page')
    return name, place, office.live_all(place)


def counted(rs):
    return {s: sum(1 for r in rs if r['state'] == s) for s in ('GREEN', 'RED', 'OFF')}


def named(blocks, key):
    return next((j for j in blocks if j.get('data_full_name') == office.fact(key)), {})


def now_line(blocks):
    """WHAT RUNS NOW: the block whose RUN is open, since its last sign of life; else IDLE since the newest RUN"""
    busy = [j for j in blocks if str(j.get('data_job_run_state') or '').upper() in OPEN]
    if busy:
        j = busy[0]
        doing = ' · '.join(x for x in (str(j.get('data_job_run') or ''), j.get('data_full_name') or '') if x)
        return (f'<span class="hdr-status--success">WORKING ON</span> <span class="scrum-key">"{html.escape(doing)}"</span>'
                + since('hdr-status--success', j.get('system_updated_at') or j.get('data_job_last_run_at')))
    last = max((str(j.get('data_job_last_run_at') or '') for j in blocks), default='')
    return '<span class="scrum-idle">IDLE</span>' + since('scrum-idle', last)


def memory_cell(blocks):
    got = office.data_of(named(blocks, 'memory_name'))
    route = (got.get('updates') or {}).get('newest_route')
    if not got:
        return '<span class="scrum-idle">-</span>'
    if got.get('why'):
        return f'<span class="hdr-status--error">{html.escape(str(got["why"]).upper())}</span>'
    return '<span class="scrum-idle">IDLE</span>' + (f' <span class="scrum-idle scrum-switch-since">{html.escape(ago(route).strip())}</span>' if ago(route) else '')


def offices_cell(blocks):
    """THE OFFICES, as the workflow's Audit last asked them (its third question): N UP, and DOWN when it named any"""
    said = next((str(a.get('said') or '') for a in office.data_of(named(blocks, 'hosts_name')).get('answers') or () if a.get('n') == 3), '')
    up = re.search(r'(\d+) (?:of (\d+) )?hosts online', said)
    if not up:
        return '<span class="scrum-idle">OFFICES · -</span>'
    down = int(up.group(2)) - int(up.group(1)) if up.group(2) else 0
    return f'<span class="{"hdr-status--error" if down else "hdr-status--success"}">OFFICES · {up.group(1)} UP' + (f' · {down} DOWN' if down else '') + '</span>'


def canvas(given):
    name, _place, _rs = rows(given)
    blocks = [j for j in office.workflow(given, name) if j.get('data_job_agentic') != 'WORKFLOW']
    board = office.data_of(named(blocks, 'board_name'))
    work = f"{int(round(board['green'] * 100 / board['total']))}%" if board.get('total') else '-'
    hidden = office.asked(given, 'live') == 'hide'
    path = (given.get('page') or {}).get('path') or ''
    dash = '<span class="scrum-idle">-</span>'
    table = ('<div class="scaf-wrap"><table class="scrum-term" id="scrum-monitor"><thead><tr><th>Tool</th><th>Status now</th></tr></thead><tbody>'
             f'<tr data-tool="rg"><td>1 RIPGREP · FAST SEARCH</td><td id="scrum-rg">{dash}</td></tr>'
             f'<tr data-tool="sse"><td>2 SSE · LIVE STREAMING</td><td id="scrum-sse">{dash}</td></tr>'
             f'<tr data-tool="manifest"><td>3 MANIFEST · MANIFEST.JSON</td><td id="scrum-manifest">{dash}</td></tr>'
             f'<tr data-tool="memory"><td>4 MEMORY · 3 WAY SWITCH</td><td id="scrum-memory-switch">{memory_cell(blocks)}</td></tr>'
             f'<tr data-tool="system"><td>5 SYSTEM</td><td id="scrum-system">{dash}<div class="scrum-offices">{offices_cell(blocks)}</div></td></tr>'
             '</tbody></table></div>')
    hide = (f'<form class="ct-form" method="get" action="{html.escape(path)}"><input type="hidden" name="live" value="{"show" if hidden else "hide"}">'
            f'<button type="submit" class="pfb pfb--small">{"▸ VIEW" if hidden else "▾ HIDE"}</button></form>')
    markup = (f'<div class="replica-live" id="replica-live" aria-label="LIVE"><div class="replica-active-head">'
              f'<div class="title scaf-law-title" id="scrum-active-title">{html.escape(name.upper())} - ACTIVE MONITORING</div>'
              f'<div id="scrum-today" class="subtitle" role="status"><span class="scrum-idle">TODAY\'S WORK {work} DONE</span></div>{hide}</div>'
              + ('' if hidden else f'<div data-live-body><div id="scrum-now" class="subtitle" role="status">{now_line(blocks)}</div>{table}</div>') + '</div>')
    return look.view(markup, path, office.fact('css'))


def run(given):
    name, place, rs = rows(given)
    n = counted(rs)
    red = [r['name'] for r in rs if r['state'] == 'RED']
    return office.done(f"GREEN · {name} live: {n['GREEN']} green, {n['RED']} red, {n['OFF']} off of {len(rs)}" + (f" · red: {', '.join(red)}" if red else ''),
                       'GREEN', {'workflow': name, 'office': place, **n, 'red_names': red, 'at': office.stamp()})


if __name__ == '__main__':
    office.main(canvas, run)
