"""THE REQUESTS, Scrum Master 3's request inbox (SM2 agent011): every request of the office's own database. Its CALL shows ADD REQUEST
TO BACKLOG with its ENVIRONMENT, TODAY'S NEW REQUESTS with REMOVE, UPDATE and APPROVE (in VERIFY), then INCOMPLETE and REMOVED; a press
is a GET of the page itself, written on the next CALL only when the search carries it. Its RUN takes the swear words out of the stored
words (the owner 2026-10-28: "i dont want the swear words stored in the system") and says what each state holds; red only when the
requests do not read."""
import hashlib
import json
import re
import sqlite3

import look
import office
from day import F, RQ_CSS, approve, clean, day_off, env_keys, env_line, moment, now, off, path_of, pressed_as, remove, request_table, update


def production_name():
    """the production box's name, as SM2's: the sprint slot that is not live (the swap's log names the live one), '' when unsaid"""
    try:
        with open(F('global_config'), encoding='utf-8') as fh:
            tower = json.load(fh).get('tower') or {}
        slots = (tower.get('sprint') or {}).get('slots') or {}
        try:
            with open(F('swaps'), encoding='utf-8') as fh:
                rows = [json.loads(x) for x in fh if x.strip()]
        except FileNotFoundError:
            rows = []
        flips = [r for r in rows if r.get('result') == 'committed' and r.get('to') in slots]
        live = flips[-1]['to'] if flips else (tower.get('swap') or {}).get('start')
        others = [s for s in slots if s != live]
        if live not in slots or len(others) != 1:
            return ''
        sprint = (slots.get(others[0]) or {}).get('name')
        return others[0].split('-')[-1].upper() + (f' · {sprint}' if sprint else '')
    except (OSError, ValueError, AttributeError, TypeError):
        return ''


def add(words, keys):
    """ADD REQUEST TO BACKLOG: his words (the swear words out), the next R-NNNN and position, asked, the boxes he left checked"""
    words = clean(str(words or '').replace('\r\n', '\n'))
    if not words.strip():
        return 'ADD refused · a request is your words: the box was empty'
    if not keys:
        return 'ADD refused · check at least one environment: it is where the work goes'
    at = now().isoformat(timespec='seconds')
    digest = hashlib.sha256(json.dumps([F('source'), words, at], ensure_ascii=False).encode('utf-8')).hexdigest()
    shut = F('closed') + [F('removed')]
    con = office.db()
    try:
        con.execute('BEGIN IMMEDIATE')
        if con.execute(f"SELECT 1 FROM requests WHERE words = ? AND state NOT IN ({','.join('?' * len(shut))})", (words, *shut)).fetchone():
            con.rollback()
            return 'ADD refused · the same request is kept already'
        top = max([int(m.group(1)) for (i,) in con.execute('SELECT id FROM requests') for m in [re.fullmatch(r'R-(\d+)', str(i))] if m] or [0])
        rid = f'R-{top + 1:04d}'
        con.execute('INSERT INTO requests (id, words, hash, source, ref, asked_at, position, state, state_at, environment) '
                    'VALUES (?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(position), 0) + 1 FROM requests), ?, ?, ?)',
                    (rid, words, digest, F('source'), F('ref'), at, F('asked'), at, json.dumps(keys)))
        con.commit()
    finally:
        con.close()
    return f'ADDED · {rid} · asked, in the backlog for the next DAY run · {env_line(keys)}'


def chosen(raw):
    """the ENVIRONMENT boxes as the page holds them: none said is the default, 'none' is every box off"""
    return [] if raw == 'none' else env_keys(raw.replace('+', ' ') or None)


def pressed(given):
    do, value, words = pressed_as(given, F('press'))
    try:
        if do == 'add':
            return add(words, chosen(value))
        if do in ('remove', 'approve'):
            return (remove if do == 'remove' else approve)(value)
        if do == 'update':
            return update(value, words)
    except sqlite3.Error as fault:
        return f'{do.upper()} not written · the requests do not write ({type(fault).__name__}: {fault})'
    return ''


def env_table(path, keys):
    """SM2's ENVIRONMENT table: a row per place, each box a link to the page itself with that box flipped (a view holds no checkbox),
    the native ones off at first"""
    e, prod, rows = office.e, production_name(), []
    for place in dict.fromkeys(pl for _k, pl, _s in F('environments')):
        boxes = ''
        for k, pl, side_ in F('environments'):
            if pl == place:
                flip = [x for x in keys if x != k] if k in keys else keys + [k]
                boxes += (f'<a class="scrum-env-box" href="{e(path)}?{F("press")}_env={"+".join(flip) or "none"}">'
                          f'<span class="scrum-env-tick{" scrum-env-tick--on" if k in keys else ""}"></span> {e(side_)}</a>')
        note = F('notes').get(place, '')
        label = f'{place} ({prod})' if place == 'production' and prod else place
        rows.append(f'<tr data-env="{e(place)}"><td>{e(label)}</td><td>{boxes}' + (f'<span class="annotation scrum-env-note">{e(note)}</span>' if note else '') + '</td></tr>')
    return (f'<div class="scaf-wrap" id="scrum-env-wrap"><table class="scrum-term scrum-env" id="scrum-env"><thead><tr><th colspan="2">{e(F("env_title"))}</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def listed(r):
    """one request as SM2's INCOMPLETE and REMOVED lines say it"""
    e, at = office.e, moment(r['state_at'])
    words = ' '.join(str(r['words'] or '').split())
    cut = words if len(words) <= F('line_cut') else words[:F('line_cut')] + '…'
    return (f'<details class="scrum-request"><summary class="subtitle">{e(r["id"])} · {e(str(r["state"]).upper().replace("_", " "))}'
            + (f' · since {at:%b %d %H:%M}' if at else '') + f' · <span class="annotation">{e(cut)}</span></summary></details>')


def summary(rows):
    if not rows:
        return 'asked for nothing: no request yet'
    by = {}
    for r in rows:
        by[r['state']] = by.get(r['state'], 0) + 1
    return f'{len(rows)} request(s): ' + ', '.join(f"{n} {str(s).replace('_', ' ')}" for s, n in sorted(by.items(), key=lambda kv: (-kv[1], str(kv[0]))))


# SM2's checkbox drawn as a box (the runtime refuses one); its header across both columns (no colspan in a view); SM2's request list folded (no details in a view: its lines alone)
CSS = RQ_CSS + """
.id-scrum .scrum-env-box { color: inherit; text-decoration: none; }
.scrum-env-tick { display: inline-block; box-sizing: border-box; width: 16px; height: 16px; border: 1px solid currentColor; border-radius: 3px; background: transparent; }
.scrum-env-tick--on { background: currentColor; text-align: center; }
.scrum-env-tick--on::after { content: "✓"; display: block; color: var(--active-color-09); font: 700 12px/14px sans-serif; }
.id-scrum .id-scrum-env .t-thead { display: table-caption; }
.id-scrum .id-scrum-env .t-thead .t-tr, .id-scrum .id-scrum-env .t-thead .t-th { display: block; }
.id-scrum .id-scrum-env .t-thead .t-th { border-bottom: 0; }
.id-scrum .id-scrum-env .t-td:first-child { width: 50%; }
.id-scrum .id-scrum-add-request .scrum-words { box-sizing: border-box; height: 12.5em; padding: 8px 10px calc(12.5em - 2.4em); font: inherit; color: inherit; background: transparent; border: 1px solid currentColor; }
.id-scrum .id-scrum-add-request .scrum-words::placeholder { color: inherit; opacity: 1; }
.id-scrum-requests .scrum-request .t-summary::before { content: "▶"; font-size: .7em; margin-right: .5em; }
"""


def canvas(given):
    """SM2's request part (agent011): ADD REQUEST TO BACKLOG with its ENVIRONMENT and box, TODAY'S NEW REQUESTS, then THE REQUESTS"""
    path, p, e = path_of(given), F('press'), office.e
    said_ = pressed(given)
    keys = chosen(office.asked(given, f'{p}_env'))
    try:
        rows = office.requests()
    except sqlite3.Error as fault:
        return office.view(office.head('The requests', 'not measured', 'RED'), office.said(f'the requests cannot be read ({fault})'))
    shut = F('closed') + [F('removed')]
    open_ = [r for r in rows if r['state'] not in shut]
    new = [r for r in open_ if r['state'] != F('stuck') and moment(r['asked_at']) and moment(r['asked_at']).date() == now().date()]
    removed = [r for r in rows if r['state'] == F('removed')]
    add_ = (f'<form class="sys-form scrum-add-form" id="scrum-add-request"><input type="hidden" name="{p}_do" value="add {"+".join(keys) or "none"}">'
            f'<input type="text" name="{p}_words" class="pin-box scrum-words" placeholder="{e(F("box_words"))}"> <button class="pfb pfb--small" type="submit">Add</button></form>')
    return look.view(
        f'<div class="replica-group" aria-label="group">{e(office.me().get("group") or "")}</div><div class="replica-canvas"><div class="replica-canvas-content">'
        f'<div id="scrum" class="replica-interface"><div class="replica-iface-form"><div class="subtitle">ADD REQUEST TO BACKLOG</div>{env_table(path, keys)}{add_}'
        + (f'<div class="annotation">{e(said_)}</div>' if said_ else '') + '</div>'
        f'<div class="clarity scrum-new-clarity" id="scrum-new-clarity"><div class="title scaf-law-title" id="scrum-new-title">'
        f"TODAY'S NEW REQUESTS · THE SCRUM MASTER BUILDS IT FROM HERE · {len(new)}</div> "
        f'<div class="scaf-wrap" id="scrum-new-wrap">{request_table(new, p, "scrum-new", "no new request pending today", today=True)}</div></div>'
        f'<div class="scrum-report" id="scrum-requests"><div class="title scaf-law-title">{e(F("list_title"))}</div>'
        f'<div class="subtitle scrum-requests-list">INCOMPLETE · {len(open_)}</div>{"".join(listed(r) for r in open_)}'
        f'<div class="subtitle scrum-requests-list">REMOVED · {len(removed)}</div>{"".join(listed(r) for r in removed)}</div></div></div></div>',
        path, CSS)


def run(given):
    if day_off():
        return off()
    try:
        rows = office.requests()
    except sqlite3.Error as fault:
        return office.done(f'RED · the requests do not read ({type(fault).__name__}: {fault})', 'RED')
    swear, n, unwritten = re.compile(F('swear'), re.I), 0, ''
    try:
        con = office.db()
        with con:
            for r in rows:
                plain = clean(r['words']) if isinstance(r['words'], str) else r['words']
                if plain != r['words']:
                    n += con.execute('UPDATE requests SET words = ? WHERE id = ? AND words = ?', (plain, r['id'], r['words'])).rowcount
        con.close()
    except sqlite3.Error as fault:
        unwritten = f' · the swear words could not be written out ({type(fault).__name__}: {fault})'
    left = sum(1 for r in office.requests() if isinstance(r['words'], str) and swear.search(r['words']))
    by = {}
    for r in rows:
        by[r['state']] = by.get(r['state'], 0) + 1
    return office.done(f'GREEN · {summary(rows)} · {n} cleaned of swear words, {left} still holding one{unwritten}', 'GREEN',
                       {'count': len(rows), 'states': by, 'cleaned': n, 'left': left})


if __name__ == '__main__':
    office.main(canvas, run)
