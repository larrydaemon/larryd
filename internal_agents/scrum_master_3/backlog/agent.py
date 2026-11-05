"""BACKLOG, Scrum Master 3's backlog (SM2 agent021; the owner 2026-10-28: "add one more for backlog on its own"; "for the backlog add a
big button to clear all backlog"): every request of the office's own database not done and not removed, asked before today or stuck
today, in build order, each with REMOVE, UPDATE and APPROVE (in VERIFY); CLEAR ALL BACKLOG marks every WAITING one removed (never a
delete), asked once more before it goes. A press is a GET of the page itself, written on the next CALL only when the search carries it.
Its RUN counts the backlog and writes nothing; red only when the requests do not read."""
import sqlite3

import look
import office
from day import F, RQ_CSS, approve, form, moment, now, path_of, pressed_as, remove, request_table, status_of, update


def backlog(rows, today):
    return [r for r in rows if r['state'] not in F('closed') + [F('removed')]
            and (r['state'] == F('stuck') or not (moment(r['asked_at']) and moment(r['asked_at']).date() == today))]


def clear_all():
    rows = [r for r in backlog(office.requests(), now().date()) if r['state'] in F('waiting')]
    con, at = office.db(), now().isoformat(timespec='seconds')
    with con:
        n = sum(con.execute(f"UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state IN ({','.join('?' * len(F('waiting')))})",
                            (F('removed'), at, F('cleared'), r['id'], *F('waiting'))).rowcount for r in rows)
    con.close()
    return f'CLEAR ALL BACKLOG · {n} request{"" if n == 1 else "s"} marked removed, none deleted'


def pressed(given):
    do, value, words = pressed_as(given, F('press'))
    try:
        if do == 'clear_yes':
            return clear_all()
        if do in ('remove', 'approve'):
            return (remove if do == 'remove' else approve)(value)
        if do == 'update':
            return update(value, words)
    except sqlite3.Error as fault:
        return f'{do.upper()} not written · the requests do not write ({type(fault).__name__}: {fault})'
    return ''


def age(at, today):
    days = (today - at.date()).days if at else None
    return '' if days is None else 'today' if days <= 0 else 'yesterday' if days == 1 else f'{days} days ago'


def said_now(rows, today):
    if not rows:
        return 'BACKLOG · 0 · the backlog is empty'
    by = {}
    for r in rows:
        by[status_of(r['state'])] = by.get(status_of(r['state']), 0) + 1
    oldest = min((moment(r['asked_at']) for r in rows if moment(r['asked_at'])), default=None)
    return (f'BACKLOG · {len(rows)} · ' + ', '.join(f'{n} {w.lower()}' for w, n in sorted(by.items(), key=lambda kv: (-kv[1], kv[0])))
            + f' · the oldest asked {age(oldest, today)}')


def canvas(given):
    """SM2's BACKLOG · n (agent021): its table, then CLEAR ALL BACKLOG (n), asked once more before it goes"""
    p, e = F('press'), office.e
    said_ = pressed(given)
    try:
        rows = backlog(office.requests(), now().date())
    except sqlite3.Error as fault:
        return office.view(office.head('Backlog', 'not measured', 'RED'), office.said(f'the requests cannot be read ({fault})'))
    n = sum(1 for r in rows if r['state'] in F('waiting'))
    clear = ''
    if pressed_as(given, p)[0] == 'clear' and n:
        clear = (f'<div class="annotation">Clear all {n} waiting requests from the backlog? Each is marked removed and kept, never deleted. BUILDING and VERIFY ones stay.</div>'
                 + form(p, 'clear_yes', f'Yes, clear all {n}', 'replica-press-form', 'pfb pfb--clarity'))
    elif n:
        clear = form(p, 'clear', f'Clear all backlog ({n})', 'replica-press-form', 'pfb pfb--clarity')
    return look.view(
        f'<div class="replica-group" aria-label="group">{e(office.me().get("group") or "")}</div><div class="replica-canvas"><div class="replica-canvas-content">'
        f'<div id="scrum" class="replica-interface"><div class="replica-iface-table"><div class="title scaf-law-title" id="scrum-backlog-title">BACKLOG · {len(rows)}</div>'
        + (f'<div class="annotation">{e(said_)}</div>' if said_ else '')
        + f'<div class="scaf-wrap" id="scrum-backlog-wrap">{request_table(rows, p, "scrum-backlog-old", "no older request pending")}</div></div>'
        f'{clear}</div></div></div>', path_of(given), RQ_CSS)


def run(given):
    try:
        rows = backlog(office.requests(), now().date())
    except sqlite3.Error as fault:
        return office.done(f'RED · the requests do not read ({type(fault).__name__}: {fault})', 'RED')
    return office.done(f'GREEN · {said_now(rows, now().date())}', 'GREEN',
                       {'count': len(rows), 'waiting': sum(1 for r in rows if r['state'] in F('waiting')), 'ids': [r['id'] for r in rows]})


if __name__ == '__main__':
    office.main(canvas, run)
