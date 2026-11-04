"""THE PAGE'S OWN PARTS (as the original's web/page.py): what the page draws beyond the platform's one shell, every word read at
the draw, nothing kept. THE AGENT'S VIEW (its card and its words), THE HERO, THE DATA FABRIC; and the parts of
the frame, drawn on the agent layer in every replica (the owner 2026-10-27: "we can not edit the frame items in the gate view so
why do we need them? they can stay only in the replica"): THE HEADER (the original's status board, first on the page), THE X
BOARD (the MARK IV agent's own summary, agent001), AGENT ACCESS (the real HOME tree, its lock, pin and reseal: the owner's
fingerprint, then his tool), THE SKILLS and THE RULES of the chain, read from each agent's job in LARRYD (jobs species, group
sanity): the page holds no table, no file and no reader of its own (the owner 2026-10-27: "rule are rules in the db not python
code. any code itself needs to be in the agent not as a file in the replica"). THE FRAME'S OWN PARTS LIVE IN app/frame (the owner 2026-10-27: "replica / frame/ / frame_ replica / frame_ skills / _ rules / _ xboard /
_ agent acess / _ live"), one file per frame item; this page draws what they hand it."""
import json
import datetime
import os
import re
import sqlite3
import zoneinfo

from frame import frame_replica as frame
from frame import frame_rules as rules
from frame import frame_skills as skills
from frame import frame_red as red   # THE RED's own measure of a rules red, the board's too

COLUMNS = ('.mk-row { display: flex; flex-wrap: wrap; gap: 44px; align-items: flex-start; padding: 0 4px } .mk-side { flex: none; width: 260px; max-width: 100%; } '
           '.mk-say { flex: 1 1 280px; min-width: 0; padding-top: 4px } .mk-side:has(.pf-card) { width: 360px } '
           '.replica-agent-hero { margin: 4px 0 36px; text-align: center } '
           '.replica-what { margin-top: 26px; padding-top: 20px; border-top: 1px solid color-mix(in srgb, currentColor 25%, transparent) } '
           '.replica-what .notes { font-family: var(--clarity-face-notes, ui-monospace, Menlo, monospace); font-size: .82rem; font-weight: 500; line-height: 1.4; text-transform: none } '
           '.replica-what > .callout, .replica-what > .callout + .notes { color: #ED86FF } .replica-what > .callout + .notes { margin-top: 6px } .replica-what > .notes + .notes { margin-top: 10px; font-style: italic }')   # THE ORIGINAL'S ROADMAP BLOCK, its font, colour and style (scrum.html #scrum-roadmap, scrum_master.css lines 15 and 40: the callout and its first line green, the notes face, the last line italic; the owner 2026-10-27: "i was clear to format the font and color and style like the original")   # WHAT A REPLICA IS, under the agent's words, IN THE SAME STYLE AS THE WORDS ABOVE IT (the owner 2026-10-27: "under the text in the same style as the original"; "i said to format it like the original fonts and style"): the title in the platform's subtitle, every sentence in the platform's body, exactly as the say; nothing of its own but the rule above it


def say(text, **slots):
    """Its page speaks English: a phrase with its slots filled, nothing translated."""
    text = str(text or '')
    try:
        return text.format(**slots) if slots else text
    except (KeyError, IndexError, ValueError):
        return text


# ---- the data fabric ------------------------------------------------------------------------------------------------
def fabric(layer=''):
    """THE DATA FABRIC the shell's VIEW DATA FABRIC draws, in the manifest's own shape (as wid's fabric_of): CSV, the
    Fabric's file names as DA-M keeps them (zones.json data_fabric.names); API and DATABASES, Positive Feedback's own rows
    of FROST's datafabric.db (account PF), read where they are, immutable. FROST's file not there: the files alone."""
    csv = [[name, '', ''] for name in frame.read_json('dam_zones')['data_fabric']['names']]
    apis, dbs, looked = [], [], ''
    try:
        con = sqlite3.connect(f"file:{frame.path('datafabric_db')}?immutable=1", uri=True)
        try:
            apis = [[n, '', s or ''] for n, s in con.execute('SELECT api_name, api_state FROM fabric_apis WHERE account_norm_key = ? ORDER BY id', ('PF',))]   # every API FROST keeps under SYSTEM (the owner 2026-10-27: "every single api should be listed this is a system account")   # our own APIs alone, as the platform's shell
            looked = (con.execute('SELECT MAX(synced_at) FROM fabric_apis WHERE account_norm_key = ?', ('PF',)).fetchone()[0] or '')
            dbs = [[n or o or '', '', ' · '.join(x for x in (o, s) if x)] for o, n, s in
                   con.execute('SELECT db_office, db_name, db_state FROM fabric_databases WHERE account_norm_key = ? ORDER BY id', ('PF',))]
        finally:
            con.close()
    except sqlite3.Error:
        pass
    try:   # WHOSE FABRIC: SYSTEM's own, as FROST holds it (the owner 2026-10-27: "this is the system account it shows it blank"), read where it is, immutable
        account, member, scope = frame.system()
        con = sqlite3.connect(f"file:{frame.path('frost_db')}?immutable=1", uri=True)
        try:
            card = con.execute('SELECT Member_Name, Username, Member_Type FROM users_members WHERE Norm_Key = ?', (member,)).fetchone() or ('', '', '')
        finally:
            con.close()
    except (sqlite3.Error, LookupError, OSError, KeyError):
        account, member, scope, card = '', '', '', ('', '', '')
    who = {'FROST IDENTITY/ACCOUNT': scope or account, 'FROST IDENTITY/NAME': card[0] or card[1], 'FROST IDENTITY/TYPE': (card[2] or '').replace('_', ' ').upper(),
           'FROST IDENTITY/AGENT LAYER': (layer or '').upper(), 'FROST IDENTITY/MEMBER KEY': member,
           'FROST IDENTITY/ENVIRONMENT': 'LOCALHOST', 'FROST IDENTITY/DEVICE': 'WEB BROWSER', 'FROST IDENTITY/LOOKED AT': looked.replace('T', ' ')[:16] + ' UTC' if looked else ''}   # whose fabric: this laptop's; the shell draws every row of it, '—' where REPLICA has none (no member signs in here)
    return {'who': {k: v for k, v in who.items() if v}, 'data': [{'t': 'CSV', 'rows': csv}], 'ai': [{'t': 'API', 'rows': apis}, {'t': 'DATABASES', 'rows': dbs}]}


# ---- the agent's own view -------------------------------------------------------------------------------------------
def agent_view(agent, top=None, shell=None, shell_url='/shell', what=None, module=None, job=None, rows=None, light='', controls=True):
    """A RUN'S AGENT, ITS OWN VIEW (the owner 2026-10-26: "the card on the left ... the text on the right and nothing more"):
    its card (the platform's one embedded card, put in its box), its words beside it; under them WHAT A REPLICA IS (what: the frame's title and note, the owner 2026-10-27), in the same
    style; no list of points (the owner 2026-10-27: "lets remove WHAT IT DOES"). The platform shell's own answer shape (atom.html
    view())."""
    from markupsafe import Markup, escape
    points = ''   # no WHAT IT DOES list (the owner 2026-10-27: "lets remove WHAT IT DOES ... also its not needed and takes up to much space")
    if what:   # WHAT A REPLICA IS, in the owner's words, straight under the agent's own and in their style (the owner 2026-10-27: "under the text in the same style as the original"): the frame's title in the subtitle, each line of its note in the body
        points = (f'<div class="replica-what"><div class="callout">{escape(what.get("title") or "")}</div>'
                  + ''.join(f'<div class="notes">{escape(line)}</div>' for line in what.get('note') or ()) + '</div>')   # the original's markup: the callout, then each line in notes
    card_box = '<div class="replica-cardbox"></div>'   # THE ONE AGENT CARD (the owner 2026-11-03: "full conversion to the embedded"): the platform's embedded card is put here (data-inject), nothing of its own
    head = ''.join(f'<div class="{c}">{escape(line)}</div>' for c, line in zip(('amx-kicker', 'amx-h1', 'amx-sub'), top or ()))
    head = f'<div class="amx-hero replica-agent-hero">{head}</div>' if head else ''   # the platform's hero, above its words (the owner 2026-10-26: "the header text goes above this in the agent")
    words = f'<div class="body">{escape(agent["say"])}</div>{points}'
    html = f'{head}<div class="mk-row"><div class="mk-side">{card_box}</div><div class="mk-say">{words}</div></div>'   # the hero across the top, the card and the words in two columns below (the owner 2026-10-26)
    if module is not None:   # THE MARK IV AGENT ON THE ONE CANVAS TOO (the owner 2026-10-27: "so all the agents use the same style"): THREE DISTINCT SECTIONS (the owner 2026-10-27: "3 DISTINCT CLEAR SECTIONS"): the template's head across the top, then the agent's own middle whole (its hero, its card and its words), then the template's foot across the bottom; never the head or the foot inside the words column beside the card
        parts_ = canvas_html(module, agent, job, html, rows, light, controls)
    else:
        parts_ = {'html': html}
    return {'agent_key': agent['key'], 'hire_keys': [], 'room_at': '', 'room_pass': '',
            'view': {**{k: Markup(v) for k, v in parts_.items()}, 'css': Markup(COLUMNS + ' ' + CANVAS_CSS)}}


# ---- THE CANVAS: one template for every agent ------------------------------------------------------------------------
CANVAS_CSS = ('.replica-canvas { display: block } '
              '.replica-rows td .replica-row-press { margin-top: 8px } .replica-rows td .scrum-update-words { display: block; width: 100%; box-sizing: border-box; margin-bottom: 6px } '   # a press in its cell, under the cell's words; the update box the cell's width, never past it   # each part of the canvas its own block (the shell draws the three groups: atom.html canvas)
              '.replica-canvas-head, .replica-canvas-foot { background-color: var(--active-color-01); color: var(--active-color-09); padding: 14px 18px } '   # THE TEMPLATE'S HEAD AND FOOT SOLID, the top block's own two colours (the owner 2026-10-27: "solid pink like the main top brutalist block"); the middle, the agent's own, stays on the page
              '.replica-canvas-head .body, .replica-canvas-head .annotation { color: inherit } '   # every word of the head in the block's own text colour (the theme's .body and .annotation wear the page's colour, pink on pink here)
              '.replica-canvas-foot .replica-rows, .replica-canvas-foot .replica-rows td, .replica-canvas-foot .replica-rows th { background-color: var(--active-color-09); color: var(--active-color-01) } '   # THE WHOLE ROWS TABLE BLACK WITH PINK TEXT (the owner 2026-10-27: "change it to black background with pink text so its readable"; "make this also black background block with pink text"), both day blocks
              '.replica-canvas-foot .scaf-row-alt td { background-color: var(--active-color-09) } .replica-canvas-foot .replica-rows .caption, .replica-canvas-foot .replica-rows .annotation { color: inherit } '
              '.replica-canvas-foot .replica-rows .scrum-day-head .caption { color: var(--status-ok) } '   # EVERY DAY HEAD IN THE LOOK'S GREEN, the ticks' green (the owner 2026-10-27: "make the titles of these green")
              '.replica-canvas-foot .replica-rows tr.replica-run-said td { background-color: var(--clarity-ground); color: var(--clarity-ink); font-family: var(--clarity-face); font-size: 1.25rem; font-weight: 700; line-height: 1.5 } '   # ONLY THE SUMMARY ROW ON CLARITY'S WHITE, big black type, the template for all (the owner 2026-10-27: "make this row only ... white (clarity) and big black font")   # the alternate day the same black; the lights keep their own colours
              '.replica-canvas-foot .btn { background-color: var(--active-color-09); color: var(--active-color-01); border-color: var(--active-color-09) } '   # A BUTTON ON THE PINK BLOCK READS AS A BUTTON (the owner 2026-10-27: "if its a button its pink on pink so it doesnt look like a button"): black, pink text, the same pair
              '.replica-canvas-head { margin: 0 0 24px } .replica-canvas-foot { overflow-x: auto } .replica-canvas-title { display: flex; align-items: center; gap: 12px; margin: 0 0 6px } '   # the rows table wider than a narrow column scrolls inside the foot, never past it
              '.replica-canvas-name { font-family: var(--clarity-face-heading); font-size: 2rem; font-weight: 900; line-height: 1.15; letter-spacing: .02em; text-transform: uppercase; margin: 0 } '
              '.replica-canvas .scrum-light { display: inline-flex; flex: none } '   # ONE BULB, ONE SIZE (the owner 2026-10-27: "all bulbs have 1 single standard size no huge bulbs"): the platform's .hdr-icon is the size; this only places it
              '.replica-canvas .scrum-light .hdr-status--success { fill: var(--status-ok) } .replica-canvas .scrum-light .hdr-status--error { fill: var(--status-error) } .replica-canvas .scrum-light .hdr-status--warn { fill: var(--status-warn) } '
              '.replica-canvas-what { margin: 0 0 2px } .replica-canvas-file { margin: 0; font-family: ui-monospace, Menlo, monospace; letter-spacing: .02em } '
              '.replica-canvas-content { margin: 0 0 24px } '   # the three sections apart: the head block, a gap, the middle on the page, a gap, the foot block
              '.replica-canvas-foot details { margin-top: 12px } .replica-canvas-foot summary.btn { display: inline-block; list-style: none; cursor: pointer } .replica-canvas-foot summary::-webkit-details-marker { display: none } '
              '.replica-canvas-panel { margin: 8px 0 0; padding: 10px 12px; border: 1px solid currentColor; border-radius: 4px; font: 15px/1.6 ui-monospace, Menlo, monospace; user-select: text; background-color: var(--active-color-09); color: var(--active-color-01) } '   # the panel under SKILLS and under RULES, the same
              '.replica-loop-logo { display: block; width: 240px; max-width: 60%; height: auto; margin: 4px auto 18px } .replica-loop .body { font-size: 1.25rem; line-height: 1.6 } '
              '.scrum-rules-panel.clarity { margin: 10px 0 0; padding: 18px 22px 16px; border: 3px solid var(--clarity-ink); border-radius: 0; text-transform: none; background-color: var(--clarity-ground); color: var(--clarity-ink) } '   # THE RULES IN CLARITY, THE ORIGINAL'S PANEL (the owner 2026-10-27: "the rules inside this black block it needs to be white with clarity big font like the original"; "reformat it like the original"): its scrum_master.css lines 184 to 196, scoped to the panel, on clarity's white ground
              '.scrum-rules-panel .annotation[data-rules-state] { font-family: var(--clarity-face-caption); font-size: .8rem; font-weight: 600; line-height: 1.5; letter-spacing: .06em; text-transform: uppercase; color: var(--clarity-ink); opacity: 1; margin: 0 0 14px } '
              '.scrum-rules-panel .body { font-family: var(--clarity-face); font-size: 1.25rem; font-weight: 400; line-height: 1.5; letter-spacing: normal; text-transform: none; color: var(--clarity-ink); margin: 0 0 10px } '
              '.scrum-rules-panel .body > span:first-child { font-family: var(--clarity-face-heading); font-weight: 900; letter-spacing: .04em; text-transform: uppercase; margin-right: .4em } '
              '.scrum-rules-panel .annotation { font-family: var(--clarity-face); font-size: 1rem; font-weight: 400; line-height: 1.45; text-transform: none; color: var(--clarity-ink-notes); opacity: 1; margin: 0 0 10px } '
              '.scrum-rules-panel .scrum-rules-title { font-family: var(--clarity-face-heading); font-size: 1.3rem; font-weight: 900; line-height: 1.3; letter-spacing: .04em; text-transform: uppercase; color: var(--clarity-ink); margin: 0 0 12px } '
              '.scrum-rules-panel .scrum-rules-big { font-family: var(--clarity-face-heading); font-size: 1.9rem; font-weight: 700; line-height: 1.25; letter-spacing: normal; text-transform: none; color: var(--clarity-ink); margin: 0 0 18px } '
              '.scrum-rules-panel .hdr-status--success { color: var(--clarity-ok) } .scrum-rules-panel .hdr-status--error { color: var(--clarity-bad) } .scrum-rules-panel .scrum-idle { color: var(--clarity-warn) } '
              '.replica-skills { width: 100%; border-collapse: collapse; table-layout: fixed } .replica-skills th, .replica-skills td { padding: 4px 8px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--ui-row-divider) } .replica-skills th:nth-child(1) { width: 34px } .replica-skills th:nth-child(2) { width: 9ch } .replica-skills th:nth-child(3) { width: 10ch } .replica-skills th { font-size: var(--font-label-sz); letter-spacing: var(--font-label-ls) } .replica-skills td:nth-child(4) { overflow-wrap: anywhere } '   # THE SKILLS PANEL A TABLE THAT LINES UP (the owner 2026-10-27: "table is now broken")
              '.replica-canvas-panel .subtitle, .replica-canvas-panel .body, .replica-canvas-panel .annotation { color: inherit } .replica-canvas-panel .replica-rule > div { margin: 0 0 6px } '
              '.replica-canvas .scrum-slot { display: grid; grid-template-columns: 18px minmax(0, 1fr); gap: 0 10px; align-items: start; text-transform: none } .replica-canvas .scrum-slot code { font: inherit; color: inherit; white-space: pre-wrap; word-break: break-word } '
              '.replica-rows { width: 100%; margin: 0; border-collapse: collapse; table-layout: fixed } .replica-rows th, .replica-rows td { padding: 6px 10px; vertical-align: middle; border-bottom: 1px solid var(--ui-row-divider) } '   # FIVE FIXED COLUMNS, ONE PADDING, EVERY CELL ON ITS MIDDLE (the owner 2026-10-27: "make everythign line up"; "now nothing lines up")
              '.replica-rows thead th, .replica-view-all .replica-rows td:not([colspan]) { width: 20% } .replica-view-all > td { padding: 6px 0 } .replica-view-all summary { margin: 0 10px 6px } '   # FIVE EQUAL COLUMNS, no wide one: START END MIN CHECK REPORT each a fifth (the owner 2026-10-27: "you have a wide colmn and everything is smashed to the left and words overlap")
              '.replica-rows th, .replica-rows td { text-align: center } .replica-rows td[colspan] { text-align: left } '   # every header over its own cells, centred, a mark under its own word; the day head and the summary from the left edge
              '.replica-rows thead th { border-bottom-width: 2px } .replica-rows .scrum-day-head td { padding-top: 12px } '
              '.replica-rows thead th, .replica-rows .caption, .replica-rows .smoke-status, .replica-rows .annotation, .replica-rows .larry-up, .replica-rows .hdr-status--error { font-size: var(--font-label-sz); letter-spacing: var(--font-label-ls) } '   # ALL THE REST SMALL: the platform's own label size, nothing invented ("make all the rest small")
              '.replica-rows .scaf-mono { font-size: 1rem; line-height: 1.5 } '
              '.replica-rows .hdr-status--success { color: var(--status-ok); font-weight: 700 } .replica-rows .hdr-status--error { color: var(--status-error); font-weight: 700 } '
              '.replica-copy { display: block; font: 15px/1.6 ui-monospace, Menlo, monospace; user-select: all; white-space: pre-wrap; word-break: break-word } '   # his one step, a line to copy whole
              '.replica-voice { margin: 14px 0 0 } .replica-standup { margin: 0 } .replica-spoken > div { margin: 0 0 8px } '
              '.replica-live-line { margin: 8px 0 0 } .replica-live-line .hdr-status--success { color: var(--status-ok); font-weight: 700 } .replica-live-line .hdr-status--error { color: var(--status-error); font-weight: 700 }')   # THE LIVE LINE on a live agent's head: the platform's own status colours   # THE CANVAS SHEET, once, handed with every canvas: the view sits in the shell's own shadow root under the platform's sheets (core.css, technology.css, the theme), where the office's page sheet never reaches


def live_view(L):
    """THE LIVE PANEL, drawn by the replica (the owner 2026-10-27: "next item is the live / we add it to the replica"; "and it is global and universal
    for all agents"): the original's ACTIVE MONITORING (scrum.html) with the frame's own data (frame/frame_live.py panel), in the LIVE slot on both
    faces, moved by this page's own stream (the page's script); no hired line (the frame hires nobody), no reds table (the frame has none). -> Markup"""
    import json as json_
    from markupsafe import Markup, escape
    nd, work, mon = L['now'], L['work'], L['monitor']
    doing_on = ((f"{nd['n']} · " if nd['n'] else '') + nd['name']) if nd['word'] in ('WORKING', 'STUCK') else ''
    cls = 'hdr-status--error' if nd['word'] in ('STUCK', 'OFFLINE') else 'hdr-status--success' if nd['word'] == 'WORKING' else 'scrum-idle'
    now = f'<div id="scrum-now" class="subtitle" role="status"><span class="{cls}">{escape(nd["word"] + " ON" if doing_on else nd["word"])}</span>'
    if doing_on:
        now += f' <span class="scrum-key">"{escape(doing_on)}"</span>'
        now += f'<span class="scrum-since hdr-status--success" data-since="{escape(nd["since"])}"></span>' if nd['since'] else ''
        now += f' <span class="scrum-idle">· {escape(nd["usual"])}</span>' if nd['usual'] else ''
    if nd['word'] == 'IDLE' and nd['since']:
        now += f'<span class="scrum-since scrum-idle" data-since="{escape(nd["since"])}"></span>'
    now += '</div>'
    # no LAST line (the owner 2026-10-28: "LAST SCRUM MASTER · 01:06 · EXIT 0 delete this")
    today = f'<div id="scrum-today" class="subtitle" role="status" data-steps="{work["green"]}/{work["total"]}"><span class="scrum-idle">TODAY\'S WORK {work["percent"]}% DONE</span></div>'   # FIRST UNDER THE TITLE (the owner 2026-10-28: "move TODAY'S WORK 73% DONE after SCRUM MASTER - ACTIVE MONITORING")
    rg, mf, mm, sy = mon['rg'], mon['manifest'], mon['memory'], mon['system']
    rows = [f'<tr data-tool="rg"><td>1 RIPGREP · FAST SEARCH</td><td id="scrum-rg"><span class="{"hdr-status--success" if rg["state"] == "SEARCHING" else "scrum-idle"}">{"SEARCHING NOW" if rg["state"] == "SEARCHING" else "READY"}</span></td></tr>',
            '<tr data-tool="sse"><td>2 SSE · LIVE STREAMING</td><td id="scrum-sse"><span class="hdr-status--success">CONNECTING</span></td></tr>',
            f'<tr data-tool="manifest"><td>3 MANIFEST · {escape(str(mf["file"]).upper())}</td><td id="scrum-manifest"><span class="scrum-idle">{mf["listed"]} GROUPS</span>'
            + ''.join(f' <span class="scrum-idle" data-report="{escape(n)}">"{escape(str(n).upper())}"</span>' for n in mf['names']) + '</td></tr>']
    if not mm.get('wired'):
        cell = f'<span class="hdr-status--error">{escape(str(mm.get("said", "")).upper())}</span>'
    elif mm['state'] == 'IDLE':
        cell = '<span class="scrum-idle" data-switch-state="IDLE">IDLE</span>' + (f' <span class="scrum-idle scrum-switch-since" data-switch-since="{escape(mm["since"])}"></span>' if mm.get('since') else '')
    else:
        cell = (f'<span class="hdr-status--success" data-switch-state="{escape(mm["state"])}">{escape(mm["state"] + (" (SHARED)" if mm["state"] == "KNOWLEDGE STORE" else ""))}</span>'
                f' <span class="scrum-idle">· ROW {escape(mm["row"])}{" · " + escape(str(mm["agent"]).upper()) if mm.get("agent") else ""}</span>'
                + (' <span class="scrum-idle">· SEARCH</span>' + ''.join(f' <span class="scrum-key">"{escape(w)}"</span>' for w in mm['words']) if mm.get('words') else '')
                + ''.join(f'<div class="scrum-idle" data-switch-bullet>- {escape(b)}</div>' for b in mm.get('bullets') or ()))
    rows.append(f'<tr data-tool="memory"><td>4 MEMORY · 3 WAY SWITCH</td><td id="scrum-memory-switch">{cell}</td></tr>')
    if sy['state'] != 'MEASURED':
        machine = '<span class="scrum-idle">MEASURING</span>'
    else:
        c, m, d, n = sy.get('cpu'), sy.get('memory'), sy.get('disk'), sy.get('network')
        pc = lambda v: '?' if v is None else f'{v}%'
        net = f"IN {n['in_percent']}% · OUT {n['out_percent']}%" if n and n.get('in_percent') is not None else 'not measured yet'
        machine = (f'<span class="scrum-idle" data-sys-part="cpu">CPU {pc(c.get("percent") if c else None)}</span> <span class="scrum-idle" data-sys-part="load">· LOAD {pc(c.get("load_percent") if c else None)}</span>'
                   f' <span class="scrum-idle" data-sys-part="memory">· MEMORY {pc(m.get("percent") if m else None)}{" · " + escape(m["pressure"]) if m and m.get("pressure") else ""}</span>'
                   f' <span class="scrum-idle" data-sys-part="disk">· DISK {pc(d.get("percent") if d else None)}</span> <span class="scrum-idle" data-sys-part="net">· NETWORK {net}</span>')
    of = sy.get('offices')
    if not of or of.get('state') == 'MEASURING':
        offices = '<span class="scrum-idle">OFFICES · MEASURING</span>'
    else:
        state = str(of.get('state') or '')
        offices = (f'<span class="{"hdr-status--success" if of["cards"] and not of["down"] else "hdr-status--error"}" data-offices-word>OFFICES · {of["up"]} UP'
                   + (f' · {of["down"]} DOWN' if of['down'] else '') + (f' · {escape(state)}' if state.startswith('NOT MEASURED') or state == 'NO OFFICE' else '') + '</span>')
        for cd in of['cards']:
            offices += (f' <span class="scrum-office" data-office="{escape(cd["name"])}" data-up="{"yes" if cd["up"] else "no"}">{escape(cd["name"])} {cd["port"]} '
                        f'<span class="{"hdr-status--success" if cd["up"] else "hdr-status--error"}">{"UP" if cd["up"] else "DOWN"}</span>{" " + str(cd["answer"]) if cd.get("answer") else ""}'
                        f' · API <span class="{"hdr-status--success" if cd["api_up"] else "hdr-status--error"}">{"UP" if cd["api_up"] else "DOWN"}</span>{" " + str(cd["api_answer"]) if cd.get("api_answer") else ""}'
                        f'{" · PID " + str(cd["pid"]) if cd.get("pid") else ""}</span>')
    rows.append(f'<tr data-tool="system"><td>5 SYSTEM</td><td id="scrum-system">{machine}<div class="scrum-offices" data-offices="{escape(of["state"] if of else "MEASURING")}">{offices}</div></td></tr>')
    table = (f'<div class="scaf-wrap"><table class="scrum-term" id="scrum-monitor" data-rg-since="{escape(rg["since"])}" data-rg-last="{escape(rg["last_at"])}" data-rg-tool="{escape(rg["tool"])}" data-rg-what="{escape(json_.dumps(rg["what"]))}">'
             '<thead><tr><th>Tool</th><th>Status now</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
    return Markup(f'<div class="replica-live" id="replica-live" aria-label="LIVE" data-stream="{escape(L["stream"])}">'
                  f'<div class="replica-active-head"><div class="title scaf-law-title" id="scrum-active-title">{escape(str(L["name"]).upper())} - ACTIVE MONITORING</div>' + today
                  + '<button type="button" class="btn btn--small" data-live-hide onclick="replicaLiveHide(this)">▾ HIDE</button></div>'   # A HIDE (the owner 2026-10-29: "the live data panel for this needs a hide so its not shifting around the page"): its body away, kept so on this browser
                  + '<div data-live-body>' + now   # TODAY'S WORK AFTER THE TITLE, ON ITS LINE (the owner 2026-10-28: "i said move this after not under")
                  + table + '</div></div>')   # no second title over the tools (the owner 2026-10-28: "delete ACTIVE MONITORING - FAST SEARCH AND LIVE STREAMING CURRENT STATUS")


def x_parts(chain, conf, live=''):
    """THE SHAPE'S ITEMS IN THE BUCKETS (the owner 2026-10-27: "reclassify the shape items to fit into the buckets and then include them in the
    xboard / like skills and rules are TOP for example"): for each slot the shape names (settings root_shape parts), each item's state from the
    chain's own records (jobs species, group sanity), in the board's three states: SKILLS green when every agent holds a GREEN skill, never red (knowledge, not a
    fault); RULES red exactly when THE RED has a rules row (a review STUPID, a lie detector DRIFT or TAMPER), green when every review is LEGIT and every
    lie detector CLEAN, else not seen yet (the owner 2026-10-27: "it should be healthy if 0 red"); LIVE (the owner 2026-10-27: "live should be in
    replica not in the agent") green or red as the frame's own look at its stream says (live: frame_live.LOOK state), else not seen yet. A name he has
    not bucketed is not counted (his call). -> [{'name', 'slot', 'green', 'red'}]"""
    jobs = [sh.get('job') or {} for _m, sh in chain]   # each job's own fields

    def skills_held():   # SKILLS DONE WHEN TODAY'S SKILLS READ WORKED (the owner 2026-10-28, "thid is the last time i ask", over TOP 2/3): the MARK IV agent's run, which takes every agent's skills, ran today and ended DONE; never red (knowledge, not a fault)
        return bool(jobs) and frame.light_of(jobs[0], frame.SETTINGS['root_shape']['x_board']) == 'green', False

    def rules_():   # RULES RED EXACTLY AS THE RED COUNTS IT (frame_red.rules_red: the review STUPID, the lie detector DRIFT or TAMPER), so the board and THE RED never disagree
        running = [sh.get('job') or {} for _m, sh in chain if sh.get('on', True)]   # A SHELL SWITCHED OFF IS OFF, as THE RED reads it (frame_red.what_is_red; the owner 2026-10-31: "it should be live data"): the header never counts what the table skips
        bad = [bool(red.rules_red(j)) for j in running]
        ok = [j.get('data_job_rules_review_verdict') == 'LEGIT' and j.get('data_job_lie_detector') == 'CLEAN' for j in running]
        return bool(ok) and all(ok) and not any(bad), any(bad)
    known = {'SKILLS': skills_held, 'RULES': rules_, 'LIVE': lambda: (live == 'green', live == 'red')}
    out = []
    for slot, names in (conf or {}).items():
        for name in names or ():
            if name in known:
                is_green, is_red = known[name]()   # never `red`: that name is THE RED's module here
                out.append({'name': name, 'slot': slot, 'green': bool(is_green), 'red': bool(is_red)})
    return out


def old_rows(facts, row_file, days, zone):
    """THE ORIGINAL'S RUNS OF THE ROW AN AGENT STANDS FOR (the owner 2026-10-27: "load data from yesterday we have the data"): its row
    found in the original's rows list by the program it names (ROW_FILE), its runs of the days asked from the original's row_runs, read
    only (immutable: nothing written, nothing copied into LARRYD). No facts, no ROW_FILE, no row: nothing. -> (row number, {date: runs})"""
    import json
    import sqlite3
    facts = facts or {}
    if not row_file or not facts.get('db') or not facts.get('rows'):
        return None, {}
    try:
        with open(os.path.expanduser(facts['rows']), encoding='utf-8') as fh:
            listed = json.load(fh).get('rows') or []
    except (OSError, ValueError):
        return None, {}
    stem = os.path.splitext(row_file)[0]
    n = next((r['n'] for r in listed if str(r.get('module') or '').rsplit('.', 1)[-1] == stem), None)
    if n is None:
        return None, {}
    near = sorted({(d + datetime.timedelta(days=k)).isoformat() for d in days for k in (-1, 0, 1)})
    try:
        con = sqlite3.connect(f"file:{os.path.expanduser(facts['db'])}?immutable=1", uri=True)
        try:
            got = con.execute(f"SELECT started, ended, state, text FROM row_runs WHERE row = ? AND substr(started, 1, 10) IN ({','.join('?' * len(near))})"
                              ' ORDER BY started DESC', [n, *near]).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return n, {}
    out = {d: [] for d in days}
    zone_ = zoneinfo.ZoneInfo(zone)
    for started, ended, state, text in got:
        try:
            s = datetime.datetime.fromisoformat(started).astimezone(zone_)
            e = datetime.datetime.fromisoformat(ended).astimezone(zone_) if ended else None
        except ValueError:
            continue
        if s.date() in out:
            out[s.date()].append({'start': s.strftime('%H:%M'), 'end': e.strftime('%H:%M') if e else '', 'min': str(int(round((e - s).total_seconds() / 60))) if e else '',
                                  'ok': state == 'green', 'report': bool((text or '').strip()), 'said': text or ''})
    return n, out


FIRST = 5   # A LIST LONGER THAN 5 SHOWS ITS FIRST 5 AND A BUTTON TO VIEW ALL (the owner 2026-10-27: "keep it simple and change from 10 to 5")


def rows_of(store, job, zone, now=None, row_file='', facts=None):
    """THE ROWS OF AN AGENT (the ROWS button; the original's row face, its bottom section): its runs by day (today, yesterday) from its
    own records alone, how long it usually takes and how many past runs, each run's start, end, minutes, its two marks and what it said;
    a day its own records do not cover, from the original's row it stands for (row_file, facts: old_rows), the day head saying so."""
    job_key = store.door.key('jobs', job)
    now = now or datetime.datetime.now(zoneinfo.ZoneInfo(zone))
    today, yesterday = now.date(), now.date() - datetime.timedelta(days=1)
    runs = sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)

    def seconds(r):
        try:
            return (datetime.datetime.fromisoformat(r['ended_at']) - datetime.datetime.fromisoformat(r['started_at'])).total_seconds()
        except ValueError:
            return None
    took = [t for t in (seconds(r) for r in runs) if t is not None]
    if took:
        usual = sorted(took)[len(took) // 2]
        length = 'UNDER 1 SEC' if usual < 1 else f'{int(round(usual))} SEC' if usual < 60 else f'{int(round(usual / 60))} MIN'
        usually = f'USUALLY {length} ({len(took)} past run{"" if len(took) == 1 else "s"})'
    else:
        usually = 'USUALLY: NO PAST RUN TO TIME IT BY'

    did = frame.run_said   # what each run said, the one line the stream says too
    days = []
    row, old = old_rows(facts, row_file, (today, yesterday), zone)
    for day, word in ((today, 'TODAY'), (yesterday, 'YESTERDAY')):
        mine = [r for r in runs if r['started_at'][:10] == day.isoformat()]
        head = f'{day.strftime("%a %b %d").upper()} ({word})' + (f' · {usually}' if word == 'TODAY' else '')
        drawn = [{'start': r['started_at'][11:16], 'end': r['ended_at'][11:16], 'min': str(int(round((seconds(r) or 0) / 60))), 'ok': r['exit'] == 0,
                  'report': bool(str(r['said'] or '').strip()), 'said': did(r)} for r in mine]
        if not mine and old.get(day):   # A DAY ITS OWN LOGS DO NOT COVER: the original's row, read where it is, said where it comes from
            many = len(old[day])
            head = f'{day.strftime("%a %b %d").upper()} ({word}) · FROM THE ORIGINAL\'S ROW {row:03d}' + (f' · {many} RUNS' if many > FIRST else '')
            drawn = old[day]   # every run of the day: the table shows the first FIRST and folds the rest behind its button
        days.append({'head': head, 'runs': drawn})
    return days


def rows_view(days):
    """The rows drawn as the original's row face: the scaffold table in the platform's own classes, FIVE columns (START, END, MIN, CHECK,
    REPORT), its day heads across the five from the START edge, each run's start, end, minutes, TWO marks, each its own fact as the
    original's cells (CHECK a green ✓ when the run ended DONE, a red ✗ when it FAILED or was REFUSED; REPORT a green ✓ when the run wrote
    its report, a red ✗ when it did not; the owner 2026-10-27: "you need two not three"), nothing in a third place, and under the run its
    summary on a row of its own from the START edge at its own size (the owner 2026-10-27: "why do we have 3 check marks and the overall
    look is like dog shit"; "keep the font size for [the summary line] make all the rest small and make everythign line up")."""
    from markupsafe import escape
    rows = []
    for n, d in enumerate(days):
        alt = ' scaf-row-alt' if n % 2 else ''
        rows.append(f'<tr class="scrum-day-head{alt}"><td colspan="5" class="caption">{escape(d["head"])}</td></tr>')
        if not d['runs']:
            rows.append(f'<tr class="{alt.strip()}"><td colspan="5" class="annotation smoke-status">No run.</td></tr>')
        def run_rows(r, alt=alt):
            check = '<span class="larry-up">✓</span>' if r['ok'] else '<span class="hdr-status--error">✗</span>'   # CHECK: the run ended DONE
            report = '<span class="larry-up">✓</span>' if r.get('report') else '<span class="hdr-status--error">✗</span>'   # REPORT: the run wrote its report
            return (f'<tr class="{alt.strip()}" data-light="{"green" if r["ok"] else "red"}"><td class="annotation smoke-status">{escape(r["start"])}</td>'
                    f'<td class="annotation smoke-status">{escape(r["end"])}</td><td class="annotation smoke-status">{escape(r["min"])}</td>'
                    f'<td>{check}</td><td>{report}</td></tr>'
                    f'<tr class="replica-run-said"><td colspan="5" class="scaf-mono clarity">{escape(r["said"])}</td></tr>')   # THE SUMMARY LINE, its own row, on clarity's own ground and ink (the clarity class carries the look's clarity names)
        rows.extend(run_rows(r) for r in d['runs'][:FIRST])
        if len(d['runs']) > FIRST:   # THE REST BEHIND ONE BUTTON (the owner 2026-10-27: "for lists longer than 10 we need a button to view all"): the platform's small button, the same five columns inside
            rest = ''.join(run_rows(r) for r in d['runs'][FIRST:])
            rows.append(f'<tr class="replica-view-all"><td colspan="5"><details><summary class="btn btn--small">▶ View all {len(d["runs"])}</summary>'
                        f'<table class="scaf-table replica-rows"><tbody class="scrum-step-block">{rest}</tbody></table></details></td></tr>')
    return ('<table class="scaf-table replica-rows"><thead><tr><th>Start</th><th>End</th><th>Min</th><th>Check</th><th>Report</th></tr></thead>'
            f'<tbody class="scrum-step-block">{"".join(rows)}</tbody></table>')


def pressable(part, route, agent, back, controls):
    """AN AGENT'S PART MADE PRESSABLE BY THE PAGE: a press or a form names the page's agent_press route, the agent and the face it is on; a table's
    row buttons the same, and none on a face without controls (the public face presses nothing)."""
    if part.get('kind') in ('press', 'form', 'slider', 'marker'):
        return {**part, 'route': route, 'agent': agent, 'back': back, 'controls': bool(controls)}
    if part.get('kind') == 'table':
        rows = [r if controls else {k: v for k, v in r.items() if k != 'presses'} for r in part.get('rows') or ()]
        for r in rows:   # a cell's marker picture gets the page's route too (the owner 2026-10-28: "combine with this table so you have 1 table again")
            for c in r.get('cells') or ():
                if isinstance(c, dict) and isinstance(c.get('marker'), dict):
                    c['marker'] = {**c['marker'], 'route': route, 'agent': agent, 'back': back, 'controls': bool(controls)}
            if isinstance(r.get('wide'), dict) and isinstance(r['wide'].get('marker'), dict):   # the row's full-width picture too
                r['wide'] = {'marker': {**r['wide']['marker'], 'route': route, 'agent': agent, 'back': back, 'controls': bool(controls)}}
        return {**part, 'rows': rows, 'route': route, 'agent': agent, 'back': back}
    return part


def content_view(parts_):
    """AN AGENT'S OWN CONTENT, DRAWN BY THE REPLICA (an agent hands words, never markup): a list of parts, each by its kind: voice (the
    READ button, the browser's own voice reads the lines), html (a block read from elsewhere, as the original's standup, verbatim),
    words (a clarity box: its title, a line under it, its spoken lines each in a class with its part, its detail folded), note (a
    clarity box with one note). A part's title is drawn INSIDE its own box as the original draws its block title, never as a line in the
    head's style or place: the top of every canvas is the head alone (the owner 2026-10-27: "the top need to be 100% the same for all")."""
    from markupsafe import escape
    out = []
    for part in parts_ or ():
        kind = part.get('kind')
        if kind == 'voice':   # THE READ BUTTON, THE PLATFORM'S BIG ONE, INSIDE THE BLOCK (the owner 2026-10-27: "the standup button should be a clarity big black button inside instead of the little pink one on top"): one row at the foot of the block drawn before it, inside its frame; alone only when no block precedes it
            row = (f'<div class="body replica-voice" data-off="" data-making="{escape(part.get("making", ""))}" data-reading="{escape(part.get("reading", ""))}" data-down="{escape(part.get("down", ""))}" data-refused="{escape(part.get("refused", "The browser refused to play the voice"))}">'
                   f'<button type="button" class="btn btn--big" data-read>▶ {escape(part.get("label", "Read"))}</button> <span class="annotation" data-voice-said></span></div>')
            if out and out[-1].endswith('</div>'):
                out[-1] = out[-1][:-len('</div>')] + row + '</div>'
            else:
                out.append(row)
        elif kind == 'press':   # AN AGENT'S OWN BIG BUTTON, INSIDE ITS BLOCK (the owner 2026-10-28: "for the backlog add a big button to clear all backlog"): a form to the page's agent_press route, asked once before it goes
            row = (f'<form method="post" action="{escape(part.get("route", ""))}" class="replica-press-form"'
                   + (f' data-confirm="{escape(part["confirm"])}" onsubmit="return confirm(this.dataset.confirm)"' if part.get('confirm') else '') + '>'
                   f'<input type="hidden" name="agent" value="{escape(part.get("agent", ""))}"><input type="hidden" name="do" value="{escape(part.get("do", ""))}">'
                   f'<input type="hidden" name="back" value="{escape(part.get("back", ""))}"><input type="hidden" name="value" value="{escape(part.get("value", ""))}"><button class="btn btn--big" type="submit">{escape(part.get("label", ""))}</button></form>')
            if out and out[-1].endswith('</div>'):
                out[-1] = out[-1][:-len('</div>')] + row + '</div>'
            else:
                out.append(row)
        elif kind == 'form':   # AN AGENT'S OWN FORM, THE ORIGINAL'S ADD REQUEST TO BACKLOG (the owner 2026-10-28: "look at each original agent and rebuild it so it looks like the original"): its title, its boxes as the original's ENVIRONMENT table, his words in a box that grows, Enter adds, Shift+Enter a new line
            fid = f'replica-form-{part.get("agent", "")}-{part.get("do", "")}'
            boxes = part.get('boxes') or {}
            table = ''
            if boxes.get('rows'):
                table = (f'<div class="scaf-wrap"><table class="scrum-term scrum-env" data-form-boxes="{escape(fid)}"><thead><tr><th colspan="2">{escape(boxes.get("title", ""))}</th></tr></thead><tbody>'
                         + ''.join(f'<tr data-env="{escape(r.get("key", ""))}"><td>{escape(r.get("label", ""))}</td><td>'
                                   + ''.join(f'<label class="scrum-env-box"><input type="checkbox" name="{escape(boxes.get("name", "box"))}" value="{escape(b["value"])}" form="{escape(fid)}"{" checked" if b.get("checked") else ""}> {escape(b.get("label", ""))}</label>' for b in r.get('boxes') or ())
                                   + (f'<span class="annotation scrum-env-note">{escape(r["note"])}</span>' if r.get('note') else '') + '</td></tr>' for r in boxes['rows'])
                         + '</tbody></table></div>')
            out.append(f'<div class="clarity replica-standup replica-form"><div class="subtitle">{escape(part.get("title", ""))}</div>'
                       + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '') + table
                       + f'<form method="post" action="{escape(part.get("route", ""))}" class="sys-form scrum-add-form" id="{escape(fid)}">'
                       f'<input type="hidden" name="agent" value="{escape(part.get("agent", ""))}"><input type="hidden" name="do" value="{escape(part.get("do", ""))}"><input type="hidden" name="back" value="{escape(part.get("back", ""))}">'
                       + (f'<input type="hidden" name="{escape(boxes.get("name", "box"))}_said" value="1">' if boxes.get('rows') else '')
                       + f'<textarea name="{escape(part.get("name", "words"))}" class="pin-box scrum-words" rows="{int(part.get("rows", 8))}" autocomplete="off" aria-label="{escape(part.get("title", ""))}" placeholder="{escape(part.get("placeholder", ""))}" data-enter="adds"></textarea> '
                       f'<button class="btn btn--small" type="submit">{escape(part.get("label", "Add"))}</button></form>'
                       '<script>(() => { const f = document.currentScript.previousElementSibling; const t = f && f.querySelector(\'textarea[data-enter="adds"]\'); if (!t) { return; }'
                       ' const grow = () => { t.style.height = \'auto\'; t.style.height = Math.min(t.scrollHeight + 2, 480) + \'px\'; }; t.addEventListener(\'input\', grow); grow();'
                       ' t.addEventListener(\'keydown\', (ev) => { if (ev.key !== \'Enter\' || ev.isComposing || ev.shiftKey) { return; } ev.preventDefault(); if (t.value.trim()) { if (f.requestSubmit) { f.requestSubmit(); } else { f.submit(); } } }); })();</script></div>')
        elif kind == 'html':
            out.append(str(part.get('html') or '').replace('<div class="clarity" id="scrum-standup"', '<div class="clarity replica-standup" id="scrum-standup"', 1)   # THE ORIGINAL'S BLOCK, 1 TO 1, IN THE SAME PLACE AS THE REPLICA'S OWN BOX (the owner 2026-10-27: "the top need to be 100% the same for all"): its title stays inside it, the block's own
                       .replace('<div id="scrum-spoken">', '<div id="scrum-spoken" class="replica-spoken">'))
        elif kind == 'words':
            lines = ''.join(f'<div class="{cls}" data-say="{escape(text)}"{f" data-part={chr(34)}{escape(tag)}{chr(34)}" if tag else ""}>{escape(text)}</div>' for cls, text, tag in part.get('lines') or ())
            detail = ''.join(f'<div class="scrum-part" data-part="{escape(tag)}"><div class="subtitle">{escape(title)}</div>'
                             + (''.join(f'<div class="body scrum-item">• {escape(it)}</div>' for it in items) or '<div class="body">Nothing.</div>') + '</div>'
                             for tag, title, items in part.get('detail') or ())
            out.append(f'<div class="clarity replica-standup"><div class="title">{escape(part.get("title", ""))}</div>'
                       + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '')
                       + f'<div class="replica-spoken">{lines}</div>'
                       + (f'<details><summary class="annotation">{escape(part.get("detail_title", "The detail"))}</summary>{detail}</details>' if part.get('detail') else '') + '</div>')
        elif kind == 'table':   # A TABLE OF WORDS (THE RED's, the owner 2026-10-27 list 3 item 8: the old WHY IT'S RED made right): its columns, each row's
            # cells (a cell {'text', 'since'} ticks: <text> · D DAYS : HH : MM : SS, moved each second by the page's own script), his one step a copy line under its row
            width = len(part.get('columns') or ()) or 1
            body = []
            for row in part.get('rows') or ():
                cells = []
                for i, cell in enumerate(row.get('cells') or ()):
                    if isinstance(cell, dict) and cell.get('since'):
                        try:
                            s_ = max(0, int((datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(cell['since'])).total_seconds()))
                        except (TypeError, ValueError):
                            s_ = 0
                        tick = f'{s_ // 86400} DAYS : {s_ % 86400 // 3600:02d} : {s_ % 3600 // 60:02d} : {s_ % 60:02d}'
                        cells.append(f'<td data-cell="{i}"><span data-ticking="{escape(cell["since"])}" data-lead="{escape(cell.get("text", ""))}">{escape(cell.get("text", ""))} · {tick}</span></td>')
                    else:
                        cells.append(f'<td data-cell="{i}">{media_html(cell)}{escape(cell.get("text", "") if isinstance(cell, dict) else cell)}</td>')
                def press_html(b, row=row):
                    return (f'<form method="post" action="{escape(part.get("route", ""))}" class="replica-row-press"' + (' data-gather' if b.get('gather') else '') + (f' data-confirm="{escape(b["confirm"])}" onsubmit="return confirm(this.dataset.confirm)"' if b.get('confirm') else '') + '>'
                            f'<input type="hidden" name="agent" value="{escape(part.get("agent", ""))}"><input type="hidden" name="do" value="{escape(b.get("do", ""))}"><input type="hidden" name="back" value="{escape(part.get("back", ""))}">'
                            f'<input type="hidden" name="value" value="{escape(b.get("value", row.get("key", "")))}">'
                            + (f'<textarea name="words" class="pin-box scrum-update-words" rows="2" aria-label="{escape(b.get("label", ""))}" placeholder="{escape(b.get("placeholder", ""))}"></textarea>' if b.get('text') else '')
                            + sliders_html(b)
                            + f'<button class="btn btn--small" type="submit">{escape(b.get("label", ""))}</button></form>')
                presses = row.get('presses') or ()
                for b in presses:   # A PRESS IN ITS OWN CELL, under the cell's words, where the original draws it (the owner 2026-10-28: "rebuild it so it looks like the original agent"): REMOVE under the request, UPDATE under his words, APPROVE under its status
                    if isinstance(b.get('cell'), int) and 0 <= b['cell'] < len(cells):
                        cells[b['cell']] = cells[b['cell']][:-len('</td>')] + press_html(b) + '</td>'
                loose = [b for b in presses if not (isinstance(b.get('cell'), int) and 0 <= b['cell'] < len(cells))]
                if loose:   # ITS ROW'S OWN BUTTONS with no cell named (the original's REMOVE, UPDATE, VERIFY, APPROVE on each request): each a small form to the agent's press, the row's key its value; one with text carries his words
                    cells.append('<td data-cell="presses" class="replica-row-presses">' + ''.join(press_html(b) for b in loose) + '</td>')
                if isinstance(row.get('wide'), dict) and isinstance(row['wide'].get('marker'), dict):   # A FULL-WIDTH PICTURE OVER THE ROW (the owner 2026-10-29: "the fucking images 1 to 8 are the same fucking size"): the row's paint board on its own line, as wide as the window lets it be
                    body.append(f'<tr data-wide="{escape(row.get("key", ""))}"><td colspan="{width}">' + marker_html(row['wide']['marker']) + '</td></tr>')
                body.append(f'<tr data-row="{escape(row.get("key", ""))}"{(' style="background:' + TONES[row['tone']] + '"') if row.get('tone') in TONES else ''}>{"".join(cells)}</tr>')   # a row's tone: 'insert' green (the owner 2026-10-28: "the rows with the inserts should be green")
                if row.get('below'):   # A FULL-WIDTH LINE UNDER THE ROW (the owner 2026-10-28: "The words should be a new row also so its not a tall column")
                    body.append(f'<tr data-below="{escape(row.get("key", ""))}"{(' style="background:' + TONES[row['tone']] + '"') if row.get('tone') in TONES else ''}><td colspan="{width}" class="annotation" style="padding-top:0">{escape(row["below"])}</td></tr>')
                if row.get('copy'):
                    body.append(f'<tr data-copy="{escape(row.get("key", ""))}"><td colspan="{width}"><code class="replica-copy">{escape(row["copy"])}</code></td></tr>')
            if not body:
                body.append(f'<tr><td colspan="{width}" class="annotation">{escape(part.get("empty", ""))}</td></tr>')
            out.append(f'<div class="clarity replica-standup"><div class="title">{escape(part.get("title", ""))}</div>'
                       + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '')
                       + '<div class="scaf-wrap"><table class="scaf-table replica-rows"><thead><tr>' + ''.join(f'<th>{escape(c)}</th>' for c in part.get('columns') or ())
                       + '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div></div>')
        elif kind == 'film':
            out.append(film_html(part))
        elif kind == 'slider':
            out.append(slider_html(part))
        elif kind == 'step':
            out.append(step_html(part))
        elif kind == 'marker':
            out.append(marker_html(part))
        elif kind == 'slideshow':
            out.append(slideshow_html(part))
        elif kind == 'listen':
            out.append(listen_html(part))
        elif kind == 'tracks':
            out.append(tracks_html(part))
        elif kind == 'note':
            out.append(f'<div class="clarity replica-standup"><div class="title">{escape(part.get("title", ""))}</div><div class="notes">{escape(part.get("text", ""))}</div></div>')
    return ''.join(out)


def loop_view(voiced=False):
    """THE RULE-SKILL-LOOP BUTTON (settings root_shape rule_skill_loop_about): his words as typed, in the clarity panel, black and white, the one red
    Positive Feedback logo above them."""
    from markupsafe import escape
    words = frame.SETTINGS['root_shape'].get('rule_skill_loop') or ''
    voice = ('<div class="body replica-voice" data-off="" data-making="Christensen is getting ready…" data-reading="Christensen is reading the rule-skill-loop" '
             'data-down="The voice is not running (start the script lab&#39;s voice)" data-refused="The browser refused to play">'
             '<button type="button" class="btn btn--big" data-read>▶ Read about</button> <span class="annotation" data-voice-said></span></div>')   # READ IT ALOUD (the owner 2026-10-28: "add a new button to the bottom of ABOUT to read the text with the christensen voice"): the page's own voice, its agent's (Christensen)
    return ('<details class="replica-canvas-loop"><summary class="btn btn--small">▶ About · rule-skill-loop</summary><div class="scrum-rules-panel clarity replica-loop" data-voice-root>'
            '<img class="replica-loop-logo" src="/positive-feedback-logo.png" alt="Positive Feedback" width="240">'
            f'<div class="body" data-say="{escape(words)}">{escape(words)}</div>{voice if voiced else ""}</div></details>')   # the button only where the agent has a voice (the owner 2026-10-28: "only for the scrum master and not for the cmo")


def trigger_word(trigger):
    """WHAT WOKE A LIVE LOOK, said short: start STARTUP, ports PORTS, status:the_pin THE PIN, a folder its name and /, a file its name (REPORT.JSON)"""
    t = str(trigger or '')
    if t in ('', 'start'):
        return 'STARTUP'
    if t.startswith('status:'):
        return t[7:].replace('_', ' ').upper()
    if t.endswith('/'):
        return os.path.basename(t.rstrip('/')).upper() + '/'
    return (os.path.basename(t) or t).upper()


def live_line(row):
    """THE ONE STATUS LINE OF AN AGENT, three words (the owner 2026-10-31: "we should actually have 3 status / running green idle pink and not running
    (like broken) red"): RUNNING in green while a run is open, IDLE in the page's pink ink when nothing is wrong (a look that passed, or an agent that
    has simply not been run), NOT RUNNING in red when it is broken: its newest run failed, it is stuck, or a live agent has no row at all. Each ticks
    from its changed_at (the page's own scrum-since) when it has one. No LAST line (the owner 2026-10-27: "remove LAST THE PIN · 23:12 · EXIT 0 on all"). -> Markup"""
    from markupsafe import Markup, escape
    key, state = escape(row.get('key') or ''), str(row.get('state') or '')
    word, cls = {'RUNNING': ('RUNNING', 'hdr-status--success'), 'RED': ('NOT RUNNING', 'hdr-status--error'), '': ('NOT RUNNING', 'hdr-status--error')}.get(state, ('IDLE', 'scrum-idle'))
    since = str(row.get('changed_at') or '')
    clock = f'<span class="scrum-since {cls}" data-since="{escape(since)}"></span>' if since else ''
    return Markup(f'<div class="replica-live-line" data-live-key="{key}" data-live-state="{escape(state)}"><div class="subtitle"><span class="{cls}">{word}</span>{clock}</div></div>')


def run_status(job, row):
    """AN OPEN RUN OUTRANKS THE ROW: RUNNING since its last sign of life, RED (NOT RUNNING) when that sign is older than THE RED's own stuck limit. -> row"""
    if (job or {}).get('data_job_run_state') not in frame.OPEN_RUN:
        return row
    life = red._utc(job.get('system_updated_at'))
    stuck = bool(life) and datetime.datetime.now(datetime.timezone.utc) - life > red.QUIET
    return {**row, 'state': 'RED' if stuck else 'RUNNING', 'changed_at': life.isoformat() if life else ''}


LIVE_BLOCK_CSS = ('.replica-live-block { display: flex; align-items: baseline; gap: 12px; margin: 0; padding: 0 4px; text-align: left } '
                  '.replica-live-block .scaf-law-title { font-size: 1.25rem; font-weight: 900; line-height: 1.2; text-transform: uppercase; margin: 0 } '
                  '.replica-live-block .replica-live-line { margin: 0 } .replica-live-block .replica-live-line .subtitle { margin: 0 } '
                  '.replica-group:has(+ .replica-live-block) { margin: 0 0 2px } '
                  '.replica-live-group { position: absolute; top: 0; right: 0; font-family: var(--clarity-face-caption, inherit); font-size: .8rem; font-weight: 700; line-height: 1.2; letter-spacing: .08em; text-transform: uppercase; }')   # LIVE ON THE AGENT LINE, at its right (the owner 2026-10-28: "are all missing the LIVE on the right try to line it up with AGENT so they dont take up too much room"): placed on the shell's own top line, beside the platform's Agent link, never a line of its own   # THE AGENT CLOSE TO ITS LINE (the owner 2026-10-28: "the AGENT is too high it needs to be close"): no 24px gap above a LIVE block's group word   # ONE LINE, COLLAPSED (the owner 2026-10-27: "have the agent closer"; "we want to colapse all of these they are taking up way too much room"): the name, its live status beside it   # THE PUBLIC FACE'S BASIC BLOCK, in its shell's own shadow root (the office's page sheet never reaches it)


def live_block(module, row):
    """A LIVE AGENT ON THE PUBLIC FACE, ONE LINE (the owner 2026-10-27: "have the agent closer"; "we want to colapse all of these they are taking up
    way too much room"): its name, then its live line beside it (live_line, from its row of the one status place, ticking); no head line, no
    summary line (the owner 2026-10-27: "remove 0 live data: ..."), no canvas, no buttons, no rows. data-live-block: the page's stream draws it
    again in place. -> Markup"""
    from markupsafe import Markup, escape
    row = row or {}
    key = escape(getattr(module, 'KEY', '') or row.get('key') or '')
    name = escape(getattr(module, 'NAME', '') or '')
    return Markup(f'<div class="replica-live-block" data-live-block="{key}"><div class="title scaf-law-title">{name}</div>{live_line({**row, "key": getattr(module, "KEY", "") or row.get("key")})}'
                  f'<span class="replica-live-group" aria-label="group">{escape(getattr(module, "SLOT", "") or "LIVE")}</span></div>')


def _scoped_theme(sheet, site, scope):
    """A PRODUCT'S OWN THEME, ON ONE BLOCK ALONE (the owner 2026-10-28: "use the agency mgmt logo and theme for the day block and the night block"):
    its sheet's dark and light values (each set under its own [data-brilliance-hierarchy][data-theme] head) said again under the block's own id,
    its fonts' faces with their addresses made the theme route's, never copied. A sheet that does not read: nothing (the page's own look stays). -> css"""
    import re as re_
    try:
        with open(sheet, encoding='utf-8') as fh:
            text = fh.read()
    except OSError:
        return ''
    fix = lambda css: css.replace('url("../', f'url("{site}/')
    out = []
    for mode in ('dark', 'light'):
        m = re_.search(r'\[data-brilliance-hierarchy="[A-F0-9]+"\]\[data-theme="' + mode + r'"\]\s*\{(.*?)\n\}', text, re_.S)
        if m:
            out.append(f'[data-theme="{mode}"] {scope} {{{fix(m.group(1))}}}')
    out += [fix(f) for f in re_.findall(r'@font-face\s*\{[^}]*\}', text)]
    return '\n'.join(out)


DAY_TITLE = 'Day shift - Hotfix Agent'   # THE DAY BLOCK'S NAME (the owner 2026-10-28: "update the text in the block from Day to Day shift - Hotfix Agent"); the NIGHT block's, kept for later: 'Night Shift - Full Build Agent'
DAY_CSS = ('#replica-day { color: var(--active-color-01); background-color: var(--active-color-09); font-family: var(--font-body); text-align: start; padding: 20px 24px 28px; } '
           '#replica-day .replica-day-mark { display: block; width: 180px; max-width: 100%; height: 77px; margin: 0 auto 16px; background: var(--image-logo_header) center / contain no-repeat; color: transparent; overflow: hidden; } '
           '#replica-day .title { font-family: var(--font-heading); font-size: .9rem; font-weight: 900; letter-spacing: .02em; text-transform: uppercase; margin: 0 0 4px; } '
           '#replica-day .annotation { font-family: var(--font-body); font-size: .75rem; opacity: .85; text-transform: none; } '
           '#replica-day .ct-form { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 10px 0 0; } #replica-day .body { text-transform: none; }')   # its look, the Security block's shape in Agency Mgmt's own values


RELEASE_TITLE = 'Release - Freeze to Swap'   # THE RELEASE BLOCK'S NAME until the owner names it (the plan, 2026-10-31)
NIGHT_TITLE = 'Night Shift - Full Build Agent'   # THE NIGHT BLOCK'S NAME (the owner 2026-10-28, kept for NIGHT; built 2026-10-31)


def day_view(on, total, action, back, sheet, site, slot='DAY', title=None):
    """THE DAY BLOCK, ITS ONE TOGGLE AND NOTHING ELSE (the owner 2026-10-28: "you can have a single day block at the top with a toggle and 1 toggle
    turns off all the day agents ... it does nothign else"; "it can look sorta like the frost identity security block"; "use the agency mgmt logo and
    theme for the day block"): at the top of the DAY group, Agency Mgmt's logo and its own theme on this block alone, its title, how many of the DAY
    agents are on, and the platform's toggle: on turns every DAY agent's shell on, off turns them all off. -> Markup"""
    from markupsafe import Markup, escape
    all_on = bool(total) and on == total
    low, word = slot.lower(), slot.capitalize()   # THE SAME BLOCK FOR NIGHT (the owner 2026-10-28: "the same shape"): its own ids, its own slot on the switch
    toggle = (f'<form method="post" action="{escape(action)}" class="ct-form" id="{low}-switch-form"><input type="hidden" name="to" value="{"off" if all_on else "on"}">'
              f'<input type="hidden" name="slot" value="{escape(slot)}"><input type="hidden" name="back" value="{escape(back)}"><span class="body">{word} agents</span> '
              f'<button class="toggle" type="submit" aria-pressed="{"true" if all_on else "false"}" title="{"On" if all_on else "Off"}"><span class="toggle__knob"></span></button> '
              f'<span class="annotation">{on} of {total} on</span></form>')
    theme_id = site.rstrip('/').rsplit('/', 1)[-1]   # the theme's site (7573b188): its background lives on this laptop's CDN, the page's own /cdn/themes/ door
    ground = ''.join(f'[data-theme="{m}"] #replica-{low} {{ background-image: url("/cdn/themes/{theme_id}/images/{m}/background.webp"); background-size: cover; background-position: center; }} ' for m in ('dark', 'light'))   # ITS BACKGROUND PICTURE (the owner 2026-10-28: "the agency mgmt block needs the background image")
    return Markup(f'<style>{_scoped_theme(sheet, site, "#replica-" + low)}\n{DAY_CSS.replace("#replica-day", "#replica-" + low)}\n{ground}</style>'
                  f'<div class="replica-normal-block replica-frame-part replica-{low}-part" aria-label="{escape(slot)}"><div class="replica-day" id="replica-{low}" data-place="agencymgmt">'
                  '<div class="replica-day-mark" role="img" aria-label="Agency Mgmt">Agency Mgmt</div>'
                  f'<div class="title" id="{low}-name">{escape(title or DAY_TITLE)}</div><div class="annotation">One switch for every {escape(slot)} agent</div>{toggle}</div></div>')


def security_toggle(on, action, back, running=False):
    """THE OWNER'S SECURITY SWITCH (the original's row 16 toggle, scrum.html: its form, its hidden 'to', the platform's toggle button, its words after it
    as the original's: "Off: it never starts (it is slow and spends many tokens). On runs it once, now."; RUNNING while a scan runs): a press writes this
    office's settings security.scan on or off; on starts the scan once, now; the light is the issue list's alone. -> Markup"""
    from markupsafe import Markup, escape
    said = ('<span class="body">RUNNING</span>' if running else 'On: it started when switched on and runs once' if on
            else 'Off: it never starts (it is slow and spends many tokens). On runs it once, now.')
    return Markup(f'<form method="post" action="{escape(action)}" class="ct-form" id="security-switch-form"><input type="hidden" name="to" value="{"off" if on else "on"}">'
                  f'<input type="hidden" name="back" value="{escape(back)}"><span class="body">Security scan</span> '
                  f'<button class="toggle" type="submit" aria-pressed="{"true" if on else "false"}" title="{"On" if on else "Off"}"><span class="toggle__knob"></span></button> '
                  f'<span class="annotation">{said}</span></form>')


def canvas_html(module, agent, job, content_html='', rows=None, light='', controls=True, live=None):
    """THE CANVAS, the same for every agent, in three parts never mixed (the owner 2026-10-27: "TOP HEADER CONTROL FOR AGENT (RND FACE ONLY)
    MIDDLE CANVAS (PUBLIC ONLY) BOTTOM CONTROL FOR AGENT (RND FACE ONLY) do not fucking mix them it pisses me off"): the TOP HEADER CONTROL,
    the same for all ("the light goes on the left ... this is the top of the template the same for all"): the light, the name big, one line
    what it does, one line its file ("the style and location of AGENT TOP THE STANDUP the top need to be 100% the same for all": the head alone is
    the top, identical in markup, sheet and place on every canvas; the group word is the shell's line above it, never the canvas's; an agent's
    title lives inside its own box, content_view); the MIDDLE CANVAS, the agent's own content, the one part the public face shows; the BOTTOM CONTROL: the
    rows in the open, the runs table as the original's row face ("ROWS OUTSIDE THE FUCKING DROP DOWN RULE INSIDE": the rule stays inside the JOB
    dropdown, the job's sanity), then the SKILLS button. controls: the rnd face (the gate layer of the rnd side) alone draws the two controls.
    live: a live agent's row of the one status place: its live line on the head (live_line), under its file.
    -> {head, html, foot}: the parts of the agent's answer the shell places in its three groups; the public face the html alone."""
    from markupsafe import escape
    middle = f'<div class="replica-canvas-content">{content_html}</div>'
    if not controls:   # THE PUBLIC FACE: the middle canvas alone
        return {'html': f'<div class="replica-canvas">{middle}</div>'}
    name = getattr(module, 'NAME', None) or (agent or {}).get('name') or ''
    said_index, panel = skills.skills_panel(job or {})
    top = (f'<div class="replica-canvas-head"><div class="replica-canvas-title">{frame.light_view(light)}<div class="replica-canvas-name">{escape(name)}</div></div>'   # ONE PINK BLOCK, the template's (the owner 2026-10-27: "make the headers and footers solid pink like the main top brutalist block so we are clear what is in the template and what is not in the template")
           f'<div class="body replica-canvas-what">{escape(getattr(module, "WHAT", "") or "")}</div>'
           f'<div class="annotation replica-canvas-file">{escape(os.path.basename(module.__file__))}</div>' + (str(live_line(live)) if live is not None else '') + '</div>')
    file = os.path.basename(module.__file__)
    bottom = ('<div class="replica-canvas-foot">' + (rows_view(rows) if rows is not None else '')   # THE BOTTOM CONTROL (the owner 2026-10-27: "the bottom of each has skills button rules button under it"): ROWS in the open, then two real buttons stacked
              + f'<details class="replica-canvas-rules"><summary class="btn btn--small">▶ Rules · {escape(rules.rules_word(job or {}))}</summary><div class="scrum-rules-panel clarity">{rules.rule_block(file, job or {}, fold=False)}</div></details>'
              + f'<details class="replica-canvas-skills"><summary class="btn btn--small">▶ Skills · {escape(said_index)}</summary>{panel}</details>'
              + loop_view(bool((agent or {}).get('voice'))) + '</div>')   # RULES, SKILLS, then the RULE-SKILL-LOOP (the owner 2026-10-27: "Rules (button) / Skills (button) / rule-skill-loop (new button)")
    return {'html': f'<div class="replica-canvas">{middle}</div>'}   # THE ONE AI ATOM SHELL'S HEADER AND FOOTER FOR EVERY AGENT (the owner 2026-11-01: "all ai atom shells need to be updated together and synced ... exactly the same"): the agent hands its canvas alone; the shell draws its own CANVAS HEADER and CANVAS FOOTER (atom.html canvas), the same for every agent, filled by Phase III
    # was: return {'head': f'<div class="replica-canvas">{top}</div>', 'html': f'<div class="replica-canvas">{middle}</div>', 'foot': f'<div class="replica-canvas">{bottom}</div>'}   # THE THREE PARTS, the shell groups them (the owner 2026-10-28: "in the agent block we need a table with borders and 3 groups stacked / CANVAS HEADER / CANVAS / CANVAS FOOTER"; "its fixed like the rest of the shell"): the platform's AI atom shell draws CANVAS HEADER, CANVAS and CANVAS FOOTER (atom.html canvas), each part under its word


ORIGINAL_CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scrum_original.css'), encoding='utf-8').read()   # THE ORIGINAL'S SHEET, the frame's own copy beside this file (web/scrum_original.css): read here into an interface's canvas, never served
INTERFACE_CSS = ('#scrum.replica-interface { display: block; text-align: left } #scrum.replica-interface > * + * { margin-top: 18px } '
                 '#scrum .replica-press-form { margin-top: 12px } '
                 '#scrum .scrum-term td .scrum-remove, #scrum .scrum-term td .scrum-update, #scrum .scrum-term td .scrum-verdict-form { margin-top: 6px }')   # its parts spaced as the original's row lines; a press under its cell's words


def _own(src):
    """an address of this page's own (a path on this host), never another site's"""
    src = str(src or '')
    return src if src.startswith('/') and not src.startswith('//') else ''


TONES = {'insert': 'rgba(46,170,96,.30)', 'two': 'rgba(214,58,58,.28)'}   # a tone's colour: III green, II red (the owner 2026-10-28: "you should color the I II and III with III green and II red")
TONE_STRONG = {'insert': 'rgba(46,170,96,.75)', 'two': 'rgba(214,58,58,.75)'}


def sliders_html(b):
    """A ROW PRESS'S SLIDERS (the owner 2026-10-29: "in the 4 we need side by side original enhanced and controls all in a row", the lab's OPACITY and
    SATURATION): b['sliders'] = [{'name', 'label', 'min', 'max', 'step', 'value', 'unit'}], each a range input sent with the press, its number beside it."""
    from markupsafe import escape
    out = ''
    for x in b.get('sliders') or ():
        name, unit = escape(x.get('name', '')), escape(x.get('unit', ''))
        out += (f'<label class="replica-slider">{escape(x.get("label", ""))} <input type="range" name="{name}" min="{x.get("min", 0)}" max="{x.get("max", 100)}" step="{x.get("step", 1)}" '
                f'value="{x.get("value", 0)}" oninput="this.nextElementSibling.textContent=this.value+\'{unit}\'" aria-label="{escape(x.get("label", ""))}"> <span>{x.get("value", 0)}{unit}</span></label> ')
    return out


def media_html(cell):
    """A CELL'S OWN MEDIA (the owner 2026-10-28, the CMO's one min sm video: "each row can play its own little clip"): an agent hands addresses,
    never markup; a cell {'video', 'poster'} is a small player, {'audio'} a sound player, {'image'} a picture, {'links': [[label, address]]} its
    links; every address this page's own."""
    from markupsafe import escape
    if not isinstance(cell, dict):
        return ''
    out = ''
    live = cell.get('live')
    if isinstance(live, dict) and _own(live.get('src')):   # A LIVE FILTER (the owner 2026-10-29: "can it adjust with the slider so you see the results live? instead of guess and guess"): the picture drawn in the page and filtered as the row's sliders move, the same maths the box saves
        out += (f'<canvas data-live="{escape(_own(live["src"]))}" data-shift="{escape(json.dumps([float(v) for v in live.get("shift") or (0, 0)]))}" '
                f'style="display:block;width:{int(cell.get("width", 420))}px;background:#000"></canvas><div class="annotation">LIVE · moves with the sliders · REPROCESS saves it</div>')
    if _own(cell.get('video')):
        out += (f'<video src="{escape(_own(cell["video"]))}" controls preload="none" playsinline width="{int(cell.get("width", 240))}" style="display:block;background:#000"'
                + (f' poster="{escape(_own(cell.get("poster")))}"' if _own(cell.get('poster')) else '') + '></video>')
    if _own(cell.get('audio')):
        out += f'<audio src="{escape(_own(cell["audio"]))}" controls preload="none" style="display:block;width:{int(cell.get("width", 240))}px"></audio>'
    if _own(cell.get('image')):
        out += f'<img src="{escape(_own(cell["image"]))}" alt="" width="{int(cell.get("width", 120))}" style="display:block;background:#000;object-fit:contain">'
        if cell.get('full'):   # A CLOSE LOOK (the owner 2026-10-28: "add a full screen on the result to see a close of of each"): the picture alone, full screen; Esc closes
            out += ('<button type="button" class="btn btn--small" style="margin-top:4px" onclick="const i=this.previousElementSibling.querySelector(&#39;img&#39;)||this.previousElementSibling; '
                   'if (i.requestFullscreen) { i.requestFullscreen(); } else if (i.webkitRequestFullscreen) { i.webkitRequestFullscreen(); }">⛶ FULL SCREEN</button>')
    if isinstance(cell.get('marker'), dict):   # A PICTURE TO MARK, inside a table cell
        out += marker_html(cell['marker'])
    if cell.get('chips'):   # SMALL COLOURED LABELS, each its tone (III green, II red)
        out += '<span style="display:inline-flex;flex-wrap:wrap;gap:3px">' + ''.join(
            f'<span style="padding:1px 6px;border:1px solid currentColor;border-radius:3px;white-space:nowrap{";background:" + TONE_STRONG[tn] + ";color:#fff" if tn in TONE_STRONG else ""}">{escape(t)}</span>'
            for t, tn in cell['chips']) + '</span>'
    pics = [(_own(h), t) for h, t in cell.get('images') or () if _own(h)]   # A ROW OF SMALL PICTURES (the owner 2026-10-28: generic reference samples for each shot group), each its title on hover
    if pics:
        out += '<div style="display:flex;flex-wrap:wrap;gap:3px;max-width:520px">' + ''.join(f'<a href="{escape(h)}" target="_blank"><img src="{escape(h)}" alt="{escape(t)}" title="{escape(t)}" width="{int(cell.get("thumb", 96))}" style="display:block"></a>' for h, t in pics) + '</div>'
    links = [(t, _own(h)) for t, h in cell.get('links') or () if _own(h)]
    if links:
        out += '<div>' + ' · '.join(f'<a href="{escape(h)}">{escape(t)}</a>' for t, h in links) + '</div>'
    return out


def film_html(part):
    """A FILM WITH ITS NUMBERED TIMELINE (the owner 2026-10-28: "row to see the video with markers for each clip as it plays the markers on a little
    timeline below but keep it simple"; "number the segments 1 to 8"): the agent hands its address and its segments [{'n', 'at', 'end'}] in seconds;
    the player, a bar of numbered segments under it (each as wide as its seconds), the playing one lit, a click jumps to its start. Its handlers
    sit on the elements themselves, so it plays inside any face's own root."""
    from markupsafe import escape
    src, segs = _own(part.get('src')), part.get('segments') or ()
    if not src:
        return f'<div class="replica-iface-note"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div><div class="annotation">{escape(part.get("empty", ""))}</div></div>'
    bar = ''.join(f'<div class="replica-film-seg" data-at="{float(s["at"])}" data-end="{float(s["end"])}" style="flex:{max(0.1, float(s["end"]) - float(s["at"]))} 0 0" title="{escape(str(s["n"]))}"'
                  ' onclick="const v=this.parentElement.previousElementSibling; v.currentTime=+this.dataset.at+0.01; v.play()">' + str(escape(str(s['n']))) + '</div>' for s in segs)
    return (f'<div class="replica-film"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div>'
            '<style>.replica-film-bar{display:flex;gap:2px;max-width:960px;margin-top:6px}.replica-film-seg{border:1px solid currentColor;text-align:center;font-weight:700;'
            'font-size:.8rem;padding:4px 0;cursor:pointer;opacity:.5}.replica-film-seg.replica-film-now{opacity:1;background:var(--status-ok,#2a7);color:#fff}</style>'
            f'<video src="{escape(src)}" controls preload="metadata" playsinline style="display:block;width:100%;max-width:960px;background:#000"'
            ' ontimeupdate="for (const s of this.nextElementSibling.children) { s.classList.toggle(\'replica-film-now\', this.currentTime >= +s.dataset.at &amp;&amp; this.currentTime &lt; +s.dataset.end); }"></video>'
            f'<div class="replica-film-bar">{bar}</div>' + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '') + '</div>')


def _wave_svg(peaks, height=44, cls='replica-wave'):
    """a waveform from its peaks (0..1), as a mirrored bar path in an SVG that stretches to its box"""
    peaks = [max(0.0, min(1.0, float(p))) for p in peaks or ()] or [0.0]
    n = len(peaks)
    d = ''.join(f'M{i} {50 - p * 48:.1f}V{50 + p * 48:.1f}' for i, p in enumerate(peaks))
    return (f'<svg class="{cls}" viewBox="0 0 {n} 100" preserveAspectRatio="none" style="display:block;width:100%;height:{int(height)}px">'
            f'<path d="{d}" stroke="currentColor" stroke-width="0.8" vector-effect="non-scaling-stroke" fill="none"/></svg>')


def slider_html(part):
    """A WINDOW TO SLIDE (the owner 2026-10-28: "a slider for 1 min and you can slide to the min you want"): the whole song's waveform, a window as wide
    as part['window'] seconds over it, a slider for its start (snapped to part['snaps'] when given: the downbeats), its start and end said as it moves,
    a play button that plays the window from its start, and its button posting the start to the agent's press (do, value, name). The agent hands
    numbers and addresses, never markup."""
    from markupsafe import escape
    total = max(1.0, float(part.get('total') or 1))
    win, lo, hi = float(part.get('window') or 60), float(part.get('min') or 0), float(part.get('max') or 0)
    start = max(lo, min(hi, float(part.get('start') or 0)))
    snaps = ','.join(f'{float(x):.3f}' for x in part.get('snaps') or ())
    audio = _own(part.get('audio'))
    move = ("const box=this.closest('.replica-slider'); let t=+this.value; const sn=(box.dataset.snaps||'').split(',').filter(Boolean).map(Number);"
            " if (sn.length) { t=sn.reduce((a,b)=>Math.abs(b-t)<Math.abs(a-t)?b:a, sn[0]); }"
            " const f=x=>Math.floor(x/60)+':'+String(Math.floor(x%60)).padStart(2,'0'); box.querySelector('[data-said]').textContent='start '+f(t)+' · end '+f(t+(+box.dataset.win))+' (est)';"
            " box.querySelector('[data-win]').style.left=(100*t/(+box.dataset.total))+'%'; box.querySelector('input[data-start]').value=t.toFixed(3);")
    play = ("const box=this.closest('.replica-slider'); const a=box.querySelector('audio'); const t=+box.querySelector('input[data-start]').value;"
            " if (!a.paused) { a.pause(); this.textContent='▶ PLAY THE MINUTE'; return; } a.currentTime=t; a.play(); this.textContent='■ STOP';"
            " const b=this; a.ontimeupdate=()=>{ if (a.currentTime>=t+(+box.dataset.win)) { a.pause(); b.textContent='▶ PLAY THE MINUTE'; } };")
    form = ''
    if part.get('controls') and part.get('route'):
        form = (f'<form method="post" action="{escape(part["route"])}" style="display:inline"><input type="hidden" name="agent" value="{escape(part.get("agent", ""))}">'
                f'<input type="hidden" name="do" value="{escape(part.get("do", ""))}"><input type="hidden" name="back" value="{escape(part.get("back", ""))}">'
                f'<input type="hidden" name="value" value="{escape(part.get("value", ""))}"><input type="hidden" data-start name="{escape(part.get("name", "start"))}" value="{start:.3f}">'
                f'<button class="btn btn--small" type="submit">{escape(part.get("label", "SET"))}</button></form>')
    else:
        form = f'<input type="hidden" data-start value="{start:.3f}">'
    f = lambda x: f'{int(x // 60)}:{int(x % 60):02d}'   # noqa: E731
    return (f'<div class="replica-slider" data-total="{total:.3f}" data-win="{win:.3f}" data-snaps="{escape(snaps)}"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div>'
            + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '')
            + '<div style="position:relative;max-width:960px;margin:6px 0">' + _wave_svg(part.get('peaks'), 56)
            + f'<div data-win style="position:absolute;top:0;bottom:0;left:{100 * start / total:.3f}%;width:{100 * win / total:.3f}%;background:rgba(80,180,120,.28);border:2px solid var(--status-ok,#2a7);box-sizing:border-box;pointer-events:none"></div></div>'
            + f'<input type="range" min="{lo:.3f}" max="{hi:.3f}" step="0.01" value="{start:.3f}" oninput="{escape(move)}" style="width:100%;max-width:960px;display:block">'
            + f'<div><span class="annotation" data-said>start {f(start)} · end {f(start + win)} (est)</span> '
            + (f'<audio src="{escape(audio)}" preload="none"></audio><button type="button" class="btn btn--small" onclick="{escape(play)}">▶ PLAY THE MINUTE</button> ' if audio else '')
            + form + '</div></div>')


def tracks_html(part):
    """A MULTITRACK (the owner 2026-10-28: "it should have layers like a multitrack with the data ready to go for the end"): lanes over one length
    (part['seconds']), each a waveform with its own player, a row of marks (strong ones bold: the downbeats), or a row of labelled blocks (sections,
    words, slots); one playhead over every lane follows whichever player plays; a click on a lane jumps every player there. The agent hands numbers,
    words and addresses, never markup."""
    from markupsafe import escape
    total = max(0.1, float(part.get('seconds') or 60))
    rows = []
    for lane in part.get('lanes') or ():
        name, body, player = str(escape(lane.get('name', ''))), '', ''
        if lane.get('peaks') is not None:
            body = _wave_svg(lane.get('peaks'), int(lane.get('height', 40)))
        elif lane.get('marks') is not None:
            body = ('<div style="position:relative;height:22px">' + ''.join(
                f'<span style="position:absolute;left:{100 * float(m["t"]) / total:.3f}%;top:{0 if m.get("strong") else 6}px;bottom:0;border-left:{2 if m.get("strong") else 1}px solid currentColor;opacity:{1 if m.get("strong") else .5}"></span>'
                for m in lane['marks'] if 0 <= float(m['t']) <= total) + '</div>')
        else:
            body = ('<div style="position:relative;height:26px">' + ''.join(
                f'<span title="{escape(b.get("label", ""))}" style="position:absolute;left:{100 * float(b["start"]) / total:.3f}%;width:{max(0.2, 100 * (float(b["end"]) - float(b["start"])) / total):.3f}%;'
                f'top:2px;bottom:2px;border:1px solid currentColor;overflow:hidden;white-space:nowrap;font-size:.72rem;line-height:20px;padding:0 2px;box-sizing:border-box{";font-weight:700" if b.get("strong") else ""}">{escape(b.get("label", ""))}</span>'
                for b in lane.get('blocks') or () if float(b['end']) > 0 and float(b['start']) < total) + '</div>')
        if _own(lane.get('audio')):
            player = (f'<audio src="{escape(_own(lane["audio"]))}" preload="none" ontimeupdate="const box=this.closest(\'.replica-tracks\'); box.style.setProperty(\'--t\', String(Math.min(1, this.currentTime / {total})));"></audio>'
                      '<button type="button" class="btn btn--small" style="padding:0 6px" onclick="const box=this.closest(\'.replica-tracks\'); const a=this.previousElementSibling;'
                      ' box.querySelectorAll(\'audio\').forEach(x=>{ if (x!==a) { x.pause(); } }); if (a.paused) { a.currentTime=(+getComputedStyle(box).getPropertyValue(\'--t\')||0)*' + f'{total}' + '; a.play(); } else { a.pause(); }">▶</button>')
        rows.append(f'<div class="replica-lane" style="display:grid;grid-template-columns:120px 1fr;gap:8px;align-items:center"><div class="caption">{player} {name}</div>'
                    f'<div onclick="const box=this.closest(\'.replica-tracks\'); const r=this.getBoundingClientRect(); const f=Math.max(0,Math.min(1,(event.clientX-r.left)/r.width));'
                    f' box.style.setProperty(\'--t\', String(f)); box.querySelectorAll(\'audio\').forEach(x=>{{ x.currentTime=f*{total}; }});" style="cursor:pointer">{body}</div></div>')
    return (f'<div class="replica-tracks" style="--t:0;position:relative"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div>'
            + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '')
            + '<div style="position:relative;max-width:1100px">' + ''.join(rows)
            + '<div style="position:absolute;top:0;bottom:0;left:calc(128px + (100% - 128px) * var(--t));border-left:2px solid var(--status-error,#e33);pointer-events:none"></div></div></div>')


def step_html(part):
    """A STEP'S OWN SECTION HEAD (the owner 2026-10-28: "a big 1 for step 1"; "step 2 will have its own section in the agent"): its number big, its
    title beside it, a line under it; the agent hands the number and the words."""
    from markupsafe import escape
    return (f'<div class="replica-step" style="display:flex;align-items:center;gap:18px;margin:28px 0 8px;border-top:3px solid currentColor;padding-top:12px">'
            f'<div style="font-size:5.5rem;line-height:.9;font-weight:800">{escape(str(part.get("n", "")))}</div>'
            f'<div><div class="title scaf-law-title" style="font-size:1.6rem">{escape(part.get("title", ""))}</div>'
            + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '') + '</div></div>')


def listen_html(part):
    """A BIG BUTTON THAT PLAYS ONE SOUND (the owner 2026-10-28: "a button after this to say play final song"): its label, the sound's own address, a
    line under it; press plays, press again stops. The agent hands the words and the address, never markup."""
    from markupsafe import escape
    audio = _own(part.get('audio'))
    if not audio:
        return f'<div class="replica-iface-note"><div class="annotation">{escape(part.get("empty", ""))}</div></div>'
    play = ("const a=this.nextElementSibling; if (a.paused) { a.currentTime=0; a.play(); this.dataset.label=this.dataset.label||this.textContent; this.textContent='■ STOP'; }"
            " else { a.pause(); this.textContent=this.dataset.label; } a.onended=()=>{ this.textContent=this.dataset.label; };")
    return (f'<div class="replica-listen" style="margin:10px 0"><button type="button" class="btn btn--big" onclick="{escape(play)}">{escape(part.get("label", "▶ PLAY"))}</button>'
            f'<audio src="{escape(audio)}" preload="none"></audio> '
            + ' '.join(f'<a class="btn btn--{"big" if i == 0 else "small"}" href="{escape(_own(h))}" download="{escape(n)}">{escape(t)}</a>' for i, (t, h, n) in enumerate(part.get('download') or ()) if _own(h))   # its downloads (the owner 2026-10-28: "a downlaod song button"): each a link that saves the file under its own name
            + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '') + '</div>')


def slideshow_html(part):
    """PICTURES ON TIME OVER ONE SOUND (the owner 2026-10-28: "it doesnt need to play a movie it can just show the image for that duration"): the sound,
    one picture that changes to the slide whose [at, end) holds the sound's time, a bar of the slides under it (each as wide as its seconds, its
    label), the slide now lit, a click jumps there. The agent hands addresses, seconds and labels, never markup."""
    from markupsafe import escape
    audio, slides = _own(part.get('audio')), [x for x in part.get('slides') or () if x]
    if not audio or not slides:
        return f'<div class="replica-iface-note"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div><div class="annotation">{escape(part.get("empty", ""))}</div></div>'
    first = next((_own(x.get('src')) for x in slides if _own(x.get('src'))), '')
    tick = ("const box=this.closest('.replica-slideshow'); const t=this.currentTime; const img=box.querySelector('img[data-show]');"
            " box.querySelectorAll('.replica-film-seg').forEach(s=>{ const on=t>=+s.dataset.at&&t<+s.dataset.end; s.classList.toggle('replica-film-now', on);"
            " if (on && s.dataset.src && img.getAttribute('src')!==s.dataset.src) { img.setAttribute('src', s.dataset.src); } });")
    jump = ("const box=this.closest('.replica-slideshow'); const a=box.querySelector('audio'); a.currentTime=+this.dataset.at+0.01;"
            " const img=box.querySelector('img[data-show]'); if (this.dataset.src) { img.setAttribute('src', this.dataset.src); } if (a.paused) { a.play(); }")
    bar = ''.join(f'<div class="replica-film-seg" data-at="{float(x["at"])}" data-end="{float(x["end"])}" data-src="{escape(_own(x.get("src")))}" '
                  f'style="flex:{max(0.1, float(x["end"]) - float(x["at"]))} 0 0{(";background:" + TONE_STRONG[x["tone"]] + ";color:#fff") if x.get("tone") in TONE_STRONG else ""}" title="{escape(str(x.get("label", "")))}" '
                  f'onclick="{escape(jump)}">{escape(str(x.get("label", "")))}</div>' for x in slides)
    return (f'<div class="replica-slideshow replica-film"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div>'
            '<style>.replica-film-bar{display:flex;gap:2px;max-width:960px;margin-top:6px}.replica-film-seg{border:1px solid currentColor;text-align:center;font-weight:700;'
            'font-size:.8rem;padding:4px 0;cursor:pointer;opacity:.6}.replica-film-seg.replica-film-now{opacity:1;outline:3px solid var(--status-ok,#2a7)}</style>'
            f'<div style="max-width:960px;aspect-ratio:16/9;background:#000;display:flex;align-items:center;justify-content:center;overflow:hidden">'
            f'<img data-show src="{escape(first)}" alt="" style="max-width:100%;max-height:100%;object-fit:contain"></div>'
            f'<audio src="{escape(audio)}" controls preload="metadata" style="width:100%;max-width:960px;display:block;margin-top:6px" ontimeupdate="{escape(tick)}" onseeked="{escape(tick)}"></audio>'
            f'<div class="replica-film-bar">{bar}</div>' + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '') + '</div>')


PAINT_CSS = '/* THE BOARD\'S ONE TOOL BAR (the owner 2026-10-29: "the controls are confusing and ugly. this needs to be better looking"): the mode, then only that mode\'s tools */\n.rp-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 6px 0; padding: 6px 10px; background: rgba(0, 0, 0, .55); border: 1px solid rgba(255, 255, 255, .16); border-radius: 6px; font-size: .72rem; letter-spacing: .06em; }\n.rp-seg { display: inline-flex; border: 1px solid rgba(255, 255, 255, .35); border-radius: 4px; overflow: hidden; }\n.rp-seg button, .rp-pill { background: transparent; color: inherit; border: 0; padding: 5px 11px; font: inherit; letter-spacing: inherit; cursor: pointer; }\n.rp-seg > * + * { border-left: 1px solid rgba(255, 255, 255, .35); }\n.rp-seg button[aria-pressed="true"], .rp-pill:has(input:checked) { background: #00B140; color: #000; }\n.rp-pill input { display: none; }\n.rp-btn { background: transparent; color: inherit; border: 1px solid rgba(255, 255, 255, .35); border-radius: 4px; padding: 5px 11px; font: inherit; letter-spacing: inherit; cursor: pointer; }\n.rp-btn:hover, .rp-seg button:hover, .rp-pill:hover { border-color: #00B140; }\n.rp-go { background: #00B140; color: #000; border-color: #00B140; font-weight: 700; }\n.rp-group { display: none; flex-wrap: wrap; align-items: center; gap: 10px; }\n.replica-marker[data-mode="mask"] .rp-group[data-for="mask"], .replica-marker[data-mode="grill"] .rp-group[data-for="grill"],\n.replica-marker[data-mode="mask"] .rp-group[data-for="bake"], .replica-marker[data-mode="tune"] .rp-group[data-for="bake"] { display: inline-flex; }\n.rp-range { display: inline-flex; align-items: center; gap: 6px; }\n.rp-range input { width: 92px; accent-color: #00B140; }\n.rp-range b { min-width: 3.2em; font-weight: 400; opacity: .85; }\n.rp-said { margin-left: auto; opacity: .75; }\n'   # the board's own look, carried inside the board: an agent draws in its own shadow root, where the page's styles never reach


def marker_html(part):
    """A PICTURE TO MARK (the owner 2026-10-28: "add a tool to tag the face of the guy and it puts a marker on it like the lab has / and it can tag
    person"): the picture, its markers drawn on it (a dot and its kind), a choice of kinds; a click on the picture sends the spot (x, y as fractions)
    and the kind to the agent's press. The agent hands the address, the marks and the kinds, never markup."""
    from markupsafe import escape
    img = _own(part.get('image'))
    if not img:
        return ''
    kinds = list(part.get('kinds') or ['face'])
    colours = {'face': '#ff2d95', 'person': '#16d6e8', 'swap': '#ff2d95'}
    dots = ''.join(f'<span title="{escape(k)}" style="position:absolute;left:{float(x) * 100:.2f}%;top:{float(y) * 100:.2f}%;transform:translate(-50%,-50%);'
                   f'width:22px;height:22px;border-radius:50%;border:3px solid #fff;background:{colours.get(k, "#ffcc00")};box-shadow:0 0 0 2px #000;pointer-events:none"></span>'
                   f'<span style="position:absolute;left:{float(x) * 100:.2f}%;top:calc({float(y) * 100:.2f}% + 14px);transform:translateX(-50%);font:700 11px sans-serif;color:#fff;'
                   f'background:#000;padding:0 4px;pointer-events:none">{escape(k.upper())}</span>' for x, y, k in part.get('marks') or ())
    click = ("const box=this.closest('.replica-marker'); const r=this.getBoundingClientRect(); const f=box.querySelector('form');"
             " f.querySelector('[name=x]').value=((event.clientX-r.left)/r.width).toFixed(4); f.querySelector('[name=y]').value=((event.clientY-r.top)/r.height).toFixed(4);"
             " f.querySelector('[name=words]').value=(box.querySelector('input[type=radio]:checked')||{value:box.dataset.kind||'face'}).value; f.submit();")
    radios = ''.join(f'<label style="margin-right:12px"><input type="radio" name="kind_{escape(part.get("value", ""))}" value="{escape(k)}"{" checked" if i == 0 else ""}> {escape(k.upper())}</label>'
                     for i, k in enumerate(kinds))
    form = (f'<form method="post" action="{escape(part.get("route", ""))}" style="display:none"><input type="hidden" name="agent" value="{escape(part.get("agent", ""))}">'
            f'<input type="hidden" name="do" value="{escape(part.get("do", ""))}"><input type="hidden" name="back" value="{escape(part.get("back", ""))}">'
            f'<input type="hidden" name="value" value="{escape(part.get("value", ""))}"><input type="hidden" name="x"><input type="hidden" name="y"><input type="hidden" name="words"></form>') if part.get('controls') else ''
    paint = part.get('paint') if isinstance(part.get('paint'), dict) and part.get('controls') else None
    if paint:   # A PICTURE TO PAINT (the owner 2026-10-29: "when i click it doesnt brush it moves the image"; "we had this same issue on the originals ... then you found a
        # solution"): the old boards' brush (wid psawp bench: hbDown, hbMove, paintAt), a drag paints the mask on a canvas over the picture at once, ERASE takes it back,
        # RESET clears; the whole stroke list goes to the agent's press in the background on each release (path), the page never reloads under his hand.
        # A LAYER ON IT (the owner 2026-10-29: "it should be able to put a custom overlay layer and move it around ... then when you modify it and like it then you bake
        # it"; "you need the squish"; the PF REFERENCE MATCH stage): GRILL lays paint['grill'] on the picture, seen inside the mask as it bakes; drag it to move, a corner
        # to size, a side to squish, the knob to turn; MATCH, LIGHT, EDGE; BAKE asks the agent for this one picture. One tool bar, its groups shown by the mode
        # (the owner 2026-10-29: "the controls are confusing and ugly. this needs to be better looking")
        form = form.replace('<input type="hidden" name="words"></form>', '<input type="hidden" name="words"><input type="hidden" name="path"><input type="hidden" name="at"></form>')
        result, result_url, grill, refpic = _own(paint.get('result')), _own(paint.get('result_url')), _own(paint.get('grill')), _own(paint.get('reference'))
        tone = paint.get('tone') if isinstance(paint.get('tone'), dict) else {}
        state = {"size": float(paint.get("size", 0.012)), "strokes": paint.get("strokes") or [], "key": str(part.get("value", "")),
                 "layer": paint.get("layer") if isinstance(paint.get("layer"), dict) else None, "band": paint.get("band"), "matte": _own(paint.get("matte")),
                 "tone": dict({k: float(tone.get(k, d)) for k, d in (("match", 60), ("light", 0), ("edge", 2))}, **{k: float(v) for k, v in tone.items()})}
        bake = paint.get('bake') if isinstance(paint.get('bake'), dict) else None   # A BAKE ON THE MASK ITSELF (the hair: no layer to place, the mask is the whole job)
        tune = paint.get('tune') if isinstance(paint.get('tune'), dict) else None   # ITS LIVE PREVIEW: two layers mixed in the page as the sliders move
        if tune:
            state['tune'] = {k: tune.get(k) for k in ('a', 'b', 'by', 'amount', 'feather', 'do', 'made')}
        if bake:
            state['bake'] = str(bake.get('do', ''))
            for x in bake.get('sliders') or ():   # its own saved numbers, never the layer board's first numbers (the owner 2026-10-29: "edge still does nothing")
                state['tone'][str(x.get('name'))] = float(x.get('value', 0))
        view = bool(paint.get('view'))   # A PICTURE ONLY LOOKED AT (the cleanup's proposals, the owner 2026-10-29): BEFORE and AFTER, no brush
        modes = (([('mask', 'BEFORE'), ('result', 'AFTER')] if result_url else [('mask', 'PICTURE')]) if view else
                 [('mask', 'MASK')] + ([('grill', 'GRILL')] if grill else []) + ([('tune', 'TUNE')] if tune else []) + ([('result', 'RESULT')] if result_url else []))
        show = paint.get('show') if paint.get('show') in [m for m, _l in modes] and (paint.get('show') != 'result' or result) else 'mask'   # the mode it opens in
        seg = ('<span class="rp-seg">' + ''.join(f'<button type="button" data-paint-mode="{m}" onclick="replicaPaintMode(this, &#39;{m}&#39;)">{lbl}</button>' for m, lbl in modes)
               + '</span>') if len(modes) > 1 else ''
        rng = lambda name, lbl, lo, hi, val, unit: (f'<label class="rp-range">{lbl} <input type="range" min="{lo}" max="{hi}" step="1" value="{val}" data-paint-{name} '   # noqa: E731
                                                     f'oninput="replicaPaintTone(this, &#39;{name}&#39;)" onchange="replicaPaintToneSend(this)"> <b>{val}{unit}</b></label>')
        pills = ''.join(f'<label class="rp-pill"><input type="radio" name="kind_{escape(part.get("value", ""))}" value="{escape(k)}"{" checked" if i == 0 else ""}>{escape(k.upper())}</label>'
                        for i, k in enumerate(kinds))
        bar = (f'<div class="rp-bar"><button type="button" class="rp-btn" data-paint-big onclick="replicaPaintBig(this)">⛶ BIG</button>'
               '<span class="rp-seg"><button type="button" onclick="replicaPaintZoomBy(this, -1)" aria-label="zoom out">−</button><button type="button" data-paint-zoomlabel disabled>1×</button>'
               '<button type="button" onclick="replicaPaintZoomBy(this, 1)" aria-label="zoom in">+</button></span>'   # ONE ZOOM, IN OR OUT, NEVER MOVED (the owner 2026-10-29: "a zoom just single zoom in or zoom out not move"): held on the mouth
               + ('<button type="button" class="rp-btn" data-paint-refbtn onclick="replicaPaintRef(this)">HIDE REF</button>' if refpic else '')   # (the owner 2026-10-29: "it needs a hide reference button")
               + f'{seg}'
               + ('' if view else f'<span class="rp-group" data-for="mask"><span class="rp-seg">{pills}</span>'
               f'<label class="rp-range">SIZE <input type="range" min="1" max="60" step="1" value="{round(state["size"] * 1000)}" data-paint-size oninput="replicaPaintSize(this)"> <b></b></label>'
               '<button type="button" class="rp-btn" onclick="replicaPaintReset(this)">RESET</button>'
               + (f'<button type="button" class="rp-btn" data-paint-auto="{escape(paint["auto"])}" onclick="replicaPaintAuto(this)">AUTO</button>' if paint.get('auto') else '')   # a first mask from the box's finder
               + '</span>')
               + ('<span class="rp-group" data-for="bake">'
                  + ('<button type="button" class="rp-btn" onclick="replicaTunePreview(this)">MAKE PREVIEW</button>' if tune else '')
                  + ''.join(rng(escape(x['name']), escape(x['label']), x['min'], x['max'], round(float(x['value'])), escape(x.get('unit', ''))) for x in bake.get('sliders') or ())
                  + '<button type="button" class="rp-btn rp-go" onclick="replicaPaintBake(this)">BAKE</button></span>' if bake else '')
               + ('<span class="rp-group" data-for="grill">'
                  + rng('match', 'MATCH', 0, 100, round(state['tone']['match']), '%') + rng('light', 'LIGHT', -50, 50, round(state['tone']['light']), '') + rng('edge', 'EDGE', 0, 10, round(state['tone']['edge']), 'px')
                  + '<button type="button" class="rp-btn" data-paint-boxbtn onclick="replicaLayerBox(this)">HIDE BOX</button>'   # (the owner 2026-10-29: "a button to hide the resize rotate box because its hard to see")
                  '<button type="button" class="rp-btn" onclick="replicaLayerFit(this)">FIT</button>'
                  '<button type="button" class="rp-btn rp-go" onclick="replicaLayerBake(this)">BAKE</button></span>' if grill else '')
               + '<span class="rp-said" data-paint-said></span></div>')
        return (f'<style>{PAINT_CSS}</style><div class="replica-marker"{" data-view" if view else ""} data-kind="{escape(kinds[0] if kinds else "brush")}" data-paint="{escape(json.dumps(state))}" data-mode="{show}" style="margin:10px 0">'
                f'<div class="subtitle">{escape(part.get("title", ""))}</div>' + bar
                + f'<div data-paint-frame style="position:relative;overflow:hidden;max-width:{int(part.get("width", 640))}px;width:100%;background:#000" oncontextmenu="return false">'
                '<div data-paint-zoom style="position:relative;transform-origin:0 0">'
                f'<img src="{escape(img)}" data-mask-src="{escape(img)}" data-result-src="{escape(result_url)}" data-grill-src="{escape(grill)}" alt="" draggable="false" crossorigin="anonymous" '
                'style="display:block;width:100%;user-select:none" onload="replicaPaintWide(this.closest(&#39;.replica-marker&#39;))">'
                '<canvas data-layer style="position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none"></canvas>'
                '<canvas style="position:absolute;left:0;top:0;width:100%;height:100%;opacity:.5;touch-action:none;cursor:none" onpointerdown="replicaPaintDown(event, this)" '
                'onpointermove="replicaPaintRing(event, this)" onpointerleave="replicaPaintRing(null, this)"></canvas></div>'
                '<div data-paint-ring style="position:absolute;left:0;top:0;display:none;border:1.5px solid #fff;box-shadow:0 0 0 1px #000;border-radius:50%;pointer-events:none;transform:translate(-50%,-50%)"></div>'
                # THE ORIGINAL TEETH IN THE CORNER (the owner 2026-10-29: "add an overlay of the original teeth in the top right corner so you can see what the should look like"):
                # the master picture, small, top right, never zoomed, clicks go through it
                + (f'<img src="{escape(refpic)}" alt="the reference" data-paint-ref draggable="false" style="position:absolute;top:8px;right:8px;width:24%;border:2px solid #fff;'
                   'box-shadow:0 0 0 1px #000,0 4px 14px rgba(0,0,0,.6);pointer-events:none;opacity:.95">' if refpic else '') + '</div>'
                + form + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '') + '</div>')
    return (f'<div class="replica-marker" data-kind="{escape(kinds[0])}" style="margin:10px 0"><div class="subtitle">{escape(part.get("title", ""))}</div>'
            + (f'<div style="margin:4px 0">{radios if len(kinds) > 1 else ""}<span class="annotation">click the picture to put the marker</span></div>' if part.get('controls') else '')   # one kind: no choice to make
            + f'<div style="position:relative;display:inline-block;max-width:{int(part.get("width", 640))}px;width:100%">'
            f'<img src="{escape(img)}" alt="" style="display:block;width:100%;cursor:crosshair;background:#000;object-fit:contain" onclick="{escape(click)}">{dots}</div>'
            + (('<button type="button" class="btn btn--small" style="margin-top:4px" onclick="const i=this.previousElementSibling.querySelector(&#39;img&#39;)||this.previousElementSibling; '
                   'if (i.requestFullscreen) { i.requestFullscreen(); } else if (i.webkitRequestFullscreen) { i.webkitRequestFullscreen(); }">⛶ FULL SCREEN</button>') if part.get('full') else '') + form
            + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '') + '</div>')


def interface_view(parts_):
    """AN INTERFACE AGENT'S OWN CONTENT IN THE ORIGINAL'S MARKUP (the owner 2026-10-28: "if we need an interfact like to add request it needs to look like the
    original / but no clock or skills or rules"): the same parts an agent hands (words, never markup), drawn the way the original's row 004 draws them, inside
    one #scrum that wears the original's sheet (ORIGINAL_CSS): form, its subtitle, the ENVIRONMENT term table, his words, ADD; table, its law title (a
    'clarity' table in the original's clarity box, as TODAY'S NEW REQUESTS) and a term table, a cell {'text', 'note', 'word', 'label', 'since', 'mono'}
    as the original's request, words and status cells, each press in its cell in the original's own classes (scrum-<do>, scrum-<do>-btn), its copy line
    the status cell's TEST IT box; list, its law title, each group its subtitle and its requests folded, as INCOMPLETE and REMOVED; note; press."""
    from markupsafe import escape
    out = []

    def press_html(part, row, b):
        do = escape(b.get('do', ''))
        form = (f'<form method="post" action="{escape(part.get("route", ""))}" class="scrum-{do}' + (' scrum-verdict-form' if b.get('do') == 'approve' else '') + '"' + (' data-gather' if b.get('gather') else '')
                + (f' data-confirm="{escape(b["confirm"])}" onsubmit="return confirm(this.dataset.confirm)"' if b.get('confirm') else '') + '>'
                f'<input type="hidden" name="agent" value="{escape(part.get("agent", ""))}"><input type="hidden" name="do" value="{do}"><input type="hidden" name="back" value="{escape(part.get("back", ""))}">'
                f'<input type="hidden" name="value" value="{escape(b.get("value", row.get("key", "")))}">'
                + (f'<textarea name="words" class="pin-box scrum-update-words" rows="2" aria-label="{escape(b.get("label", ""))} {escape(row.get("key", ""))}" placeholder="{escape(b.get("placeholder", ""))}"></textarea>' if b.get('text') else '')
                + sliders_html(b)
                + f'<button class="btn btn--small scrum-{do}-btn" type="submit">{escape(b.get("label", ""))}</button></form>')
        return f'<div class="scrum-verdict">{form}</div>' if b.get('do') == 'approve' else form

    def cell_html(i, cell):
        if not isinstance(cell, dict):
            return str(escape(cell))
        word = cell.get('word')
        cls = {'VERIFY': 'scrum-verify', 'WAITING': 'scrum-idle', 'BUILDING': 'scrum-idle'}.get(str(word or ''), 'scrum-idle')
        body = (f'<span class="{cls}">{escape(word)}</span> ' if word else '')
        body = media_html(cell) + body   # a cell's own media (video, audio, image, links) above its words
        if cell.get('mono'):
            body += f'<div class="scrum-words-text">{escape(cell.get("text", ""))}</div>'
        elif word:
            body += f'<span class="annotation">{escape(cell.get("text", ""))}</span>' if cell.get('text') else ''
        else:
            body += str(escape(cell.get('text', '')))
        if cell.get('note'):
            body += f'<div class="annotation scrum-env-line">{escape(cell["note"])}</div>'
        if cell.get('since'):
            body += (f'<div class="annotation scrum-builder">{escape(cell.get("label", ""))} <span class="scrum-building-clock hdr-status--success">'
                     f'<span class="scrum-since" data-since="{escape(cell["since"])}"></span></span></div>')
        if cell.get('working'):   # A CELL AT WORK (the owner 2026-10-29: "it should say its processing in the box or do somethign or we dont know if its working"): the page looks again every 10 seconds while one is on it
            body += '<span data-working hidden></span>'
        return body

    for part in parts_ or ():
        kind = part.get('kind')
        if kind == 'form':
            fid = 'scrum-add-request' if part.get('do', 'add') == 'add' else f'scrum-add-{part.get("do")}'   # the original's own ids (a second form, another step's, its own id: two never clash), its sheet's rules keyed to them (one interface, one shadow root of its own)
            boxes = part.get('boxes') or {}
            table = ''
            if boxes.get('rows'):
                table = (f'<div class="scaf-wrap" id="scrum-env-wrap"><table class="scrum-term scrum-env" id="scrum-env" data-form-boxes="{escape(fid)}"><thead><tr><th colspan="2">{escape(boxes.get("title", ""))}</th></tr></thead><tbody>'
                         + ''.join(f'<tr data-env="{escape(r.get("key", ""))}"><td>{escape(r.get("label", ""))}</td><td>'
                                   + ''.join(f'<label class="scrum-env-box"><input type="checkbox" name="{escape(boxes.get("name", "box"))}" value="{escape(b["value"])}" form="{escape(fid)}"{" checked" if b.get("checked") else ""}> {escape(b.get("label", ""))}</label>' for b in r.get('boxes') or ())
                                   + (f'<span class="annotation scrum-env-note">{escape(r["note"])}</span>' if r.get('note') else '') + '</td></tr>' for r in boxes['rows'])
                         + '</tbody></table></div>')
            out.append(f'<div class="replica-iface-form"><div class="subtitle">{escape(part.get("title", ""))}</div>' + table
                       + f'<form method="post" action="{escape(part.get("route", ""))}" class="sys-form scrum-add-form" id="{escape(fid)}">'
                       f'<input type="hidden" name="agent" value="{escape(part.get("agent", ""))}"><input type="hidden" name="do" value="{escape(part.get("do", ""))}"><input type="hidden" name="back" value="{escape(part.get("back", ""))}">'
                       + (f'<input type="hidden" name="{escape(boxes.get("name", "box"))}_said" value="1">' if boxes.get('rows') else '')
                       + f'<textarea name="{escape(part.get("name", "words"))}" class="pin-box scrum-words" rows="{int(part.get("rows", 8))}" autocomplete="off" aria-label="{escape(part.get("title", ""))}" placeholder="{escape(part.get("placeholder", ""))}" data-enter="adds"></textarea> '
                       f'<button class="btn btn--small" type="submit">{escape(part.get("label", "Add"))}</button></form>'
                       '<script>(() => { const f = document.currentScript.previousElementSibling; const t = f && f.querySelector(\'textarea[data-enter="adds"]\'); if (!t) { return; }'
                       ' t.addEventListener(\'keydown\', (ev) => { if (ev.key !== \'Enter\' || ev.isComposing || ev.shiftKey) { return; } ev.preventDefault(); if (t.value.trim()) { if (f.requestSubmit) { f.requestSubmit(); } else { f.submit(); } } }); })();</script></div>')
        elif kind == 'table':
            width = len(part.get('columns') or ()) or 1
            body = []
            for row in part.get('rows') or ():
                cells = [cell_html(i, c) for i, c in enumerate(row.get('cells') or ())]
                presses = row.get('presses') or ()
                for b in presses:
                    at = b.get('cell') if isinstance(b.get('cell'), int) and 0 <= b['cell'] < len(cells) else len(cells) - 1
                    cells[at] += press_html(part, row, b)
                if row.get('copy') and cells:
                    cells[-1] += f'<div class="annotation scrum-test-link scrum-test-box">{escape(row["copy"])}</div>'   # TEST IT, in its status cell as the original's
                if isinstance(row.get('wide'), dict) and isinstance(row['wide'].get('marker'), dict):   # A FULL-WIDTH PICTURE OVER THE ROW (the owner 2026-10-29: "the fucking images 1 to 8 are the same fucking size"): the row's paint board on its own line, as wide as the window lets it be
                    body.append(f'<tr data-wide="{escape(row.get("key", ""))}"><td colspan="{width}">' + marker_html(row['wide']['marker']) + '</td></tr>')
                body.append(f'<tr data-row="{escape(row.get("key", ""))}"{(' style="background:' + TONES[row['tone']] + '"') if row.get('tone') in TONES else ''}>' + ''.join(f'<td data-cell="{i}">{c}</td>' for i, c in enumerate(cells)) + '</tr>')   # a row's tone: 'insert' green
                if row.get('below'):   # A FULL-WIDTH LINE UNDER THE ROW (the owner 2026-10-28: "The words should be a new row also so its not a tall column")
                    body.append(f'<tr data-below="{escape(row.get("key", ""))}"{(' style="background:' + TONES[row['tone']] + '"') if row.get('tone') in TONES else ''}><td colspan="{width}" class="annotation" style="padding-top:0">{escape(row["below"])}</td></tr>')
            if not body:
                body.append(f'<tr><td colspan="{width}" class="scrum-idle">{escape(part.get("empty", ""))}</td></tr>')
            cols = list(part.get('columns') or ())
            head = ''.join(f'<th{" class=" + chr(34) + ("scrum-why-row" if i == 0 else "scrum-why-status") + chr(34) if len(cols) == 3 and i != 1 else ""}>{escape(c)}</th>' for i, c in enumerate(cols))   # the original's header classes: its column widths
            name = 'new' if part.get('clarity') else 'backlog'   # the original's ids: TODAY'S NEW REQUESTS (scrum-new) in its clarity box, the BACKLOG (scrum-backlog-old)
            grid = f'<div class="scaf-wrap" id="scrum-{name}-wrap"><table class="scrum-term" id="scrum-{"new" if name == "new" else "backlog-old"}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
            title = f'<div class="title scaf-law-title" id="scrum-{name}-title">{escape(part.get("title", ""))}</div>' + (f'<div class="annotation">{escape(part["under"])}</div>' if part.get('under') else '')
            out.append(f'<div class="clarity scrum-new-clarity" id="scrum-new-clarity">{title} {grid}</div>' if part.get('clarity') else f'<div class="replica-iface-table">{title}{grid}</div>')
        elif kind == 'list':
            groups = ''.join(f'<div class="subtitle scrum-requests-list">{escape(head)}</div>'
                             + (''.join(f'<details class="scrum-request"><summary class="subtitle">{escape(it.get("summary", ""))}' + (f' · <span class="annotation">{escape(it["short"])}</span>' if it.get('short') else '') + '</summary>'
                                        + (f'<div class="body">{escape(it["body"])}</div>' if it.get('body') else '') + (f'<div class="annotation">{escape(it["note"])}</div>' if it.get('note') else '') + '</details>' for it in items)
                                or f'<div class="annotation">{escape(empty)}</div>') for head, items, empty in part.get('groups') or ())
            out.append(f'<div class="scrum-report" id="scrum-requests"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div>{groups}</div>')
        elif kind == 'slider':
            out.append(slider_html(part))
        elif kind == 'step':
            out.append(step_html(part))
        elif kind == 'marker':
            out.append(marker_html(part))
        elif kind == 'slideshow':
            out.append(slideshow_html(part))
        elif kind == 'listen':
            out.append(listen_html(part))
        elif kind == 'tracks':
            out.append(tracks_html(part))
        elif kind == 'film':
            out.append(film_html(part))
        elif kind == 'note':
            out.append(f'<div class="replica-iface-note"><div class="title scaf-law-title">{escape(part.get("title", ""))}</div><div class="annotation scaf-mono">{escape(part.get("text", ""))}</div></div>')
        elif kind == 'press':
            out.append(f'<form method="post" action="{escape(part.get("route", ""))}" class="replica-press-form"'
                       + (f' data-confirm="{escape(part["confirm"])}" onsubmit="return confirm(this.dataset.confirm)"' if part.get('confirm') else '') + '>'
                       f'<input type="hidden" name="agent" value="{escape(part.get("agent", ""))}"><input type="hidden" name="do" value="{escape(part.get("do", ""))}">'
                       f'<input type="hidden" name="back" value="{escape(part.get("back", ""))}"><input type="hidden" name="value" value="{escape(part.get("value", ""))}"><button class="btn btn--big" type="submit">{escape(part.get("label", ""))}</button></form>')
    return f'<div id="scrum" class="replica-interface">{"".join(out)}</div>'


def day_status(store, job, key):
    """A DAY AGENT RUNNING IN THE BACKGROUND, ITS ONE LINE (the owner 2026-10-28: "if something is just running in the background it should look like
    AGENT / AUDIT / RED 19 S / LIVE"): the one status row live_block reads, from its own runs in LARRYD: RED since the first run of its red streak when
    its newest run failed, IDLE since its newest run ended when it passed; never run: IDLE with no clock (a day agent runs on RUN AGENT alone, waiting is
    not broken: the owner 2026-10-31); a run open now: RUNNING (run_status). -> {'key', 'state', 'changed_at'}"""
    row = {'key': key, 'state': 'IDLE', 'changed_at': ''}
    if (job or {}).get('data_job_run_state') in frame.OPEN_RUN:
        return run_status(job, row)
    runs = sorted(store.runs(store.door.key('jobs', job), 200), key=lambda r: r['started_at'], reverse=True) if job else []
    if not runs:
        return row
    if runs[0]['exit'] != 0:
        streak = runs[0]
        for r in runs:
            if r['exit'] == 0:
                break
            streak = r
        return {'key': key, 'state': 'RED', 'changed_at': streak['started_at']}
    return {'key': key, 'state': 'GREEN', 'changed_at': runs[0]['ended_at'] or runs[0]['started_at']}


def canvas(module, agent, key, job, content=(), rows=None, light='', controls=True, live=None, interface=False):
    """ONE AGENT'S VIEW IN ITS SHELL, drawn on the one canvas: the platform shell's own answer shape (atom.html view()). interface: its content in the
    original's markup and sheet (interface_view), an agent with an interface of its own (the owner 2026-10-28)."""
    from markupsafe import Markup
    parts_ = canvas_html(module, agent, job, interface_view(content) if interface else content_view(content), rows, light, controls, live)
    return {'agent_key': key, 'hire_keys': [], 'room_at': '', 'room_pass': '', 'view': {**{k: Markup(v) for k, v in parts_.items()}, 'css': Markup(CANVAS_CSS + (' ' + ORIGINAL_CSS + ' ' + INTERFACE_CSS if interface else ''))}}

def hero(screen):
    """THE PAGE'S HERO, the platform's own three lines for a screen (wid config.json, read where it is): [eyebrow, title, sub]."""
    tables = frame.read_json('wid_config')['tables']
    return next(t['rows']['screen'][screen] for t in tables if isinstance(t.get('rows'), dict) and screen in (t['rows'].get('screen') or {}))


# ---- the header: the original's status board -------------------------------------------------------------------------
def header_board(product, name, klass, x, zone, now=None, reds=None):
    """THE HEADER'S WORDS (the owner 2026-10-27: "please add this to the top of the page and make it dynamic"; "just add it to the top
    of the replica so all have it globally"): the mast (the product and the name), the stamp (now, in the board's zone), the report
    tag, the counts of the X BOARD's rows today (one source: green = ran today and ended DONE, red = ran today and ended in a red word,
    not seen yet = the rest), who (the name and its class), the one word and its state: CRITICAL when any row is red today, else
    HEALTHY. -> dict"""
    now = now or datetime.datetime.now(zoneinfo.ZoneInfo(zone))
    green, red, total = (sum(line[k] for line in x['lines']) for k in ('green', 'red', 'total'))
    if reds is not None:   # THE RED'S COUNT (the owner 2026-10-28: "11 RED ... 6 GREEN · 4 RED / the header and data still do not work.. it should be live data from the same source"): THE RED's own rows, the count its block says, never fewer than the X board's own reds (a frame look gone dark is red there and no row of THE RED: hidden, it would be a fake HEALTHY)
        red = max(red, reds)
    word = 'Critical' if red else 'Healthy'
    return {'mast': f'{product} · {name}', 'stamp': now.strftime('%Y-%m-%d'), 'tag': f'{product} report',
            'counts': f'{green} green · {red} red', 'green': green, 'red': red,   # RED AND GREEN ONLY (the owner 2026-10-28: "can be simplired also / red green only")
            'who': ' · '.join(w for w in (name, klass) if w), 'word': word, 'state': word.lower()}


def header_view(h):
    """The board drawn as the original's (the platform's own classes: console-report-panel, lrp-inner, lsb: LARRY LLM's core.css for
    its lines, technology.css for its colours, both read where they are, never copied: web/app.py board_css): the mast and the stamp
    on one row, the rule, the hero with its three tags and the word."""
    from markupsafe import Markup, escape
    html = ('<div class="console-report-panel replica-header"><div class="lrp-inner"><div class="lsb" aria-label="HEADER">'
            f'<div class="lsb-row"><div class="lsb-mast">{escape(h["mast"])}</div><div class="lsb-stamp">{escape(h["stamp"])}</div></div>'
            '<div class="lsb-rule"></div>'
            f'<div class="lsb-hero lsb-hero--{h["state"]}"><div class="lsb-tag lsb-tag--tl">{escape(h["tag"])}</div>'
            f'<div class="lsb-tag lsb-tag--tr"><span class="replica-count-green">{h.get("green", 0)} green</span> · <span class="replica-count-red">{h.get("red", 0)} red</span></div><div class="lsb-tag lsb-tag--br">{escape(h["who"])}</div>'
            f'<div class="lsb-big">{escape(h["word"])}</div></div></div></div></div>')
    return {'html': Markup(html), 'css': Markup('')}


def listed(text, cls):
    """A LINE THAT LISTS MORE THAN 10 (items between commas): its first 10, then the platform's small button holding the rest (the owner 2026-10-27:
    "its showing way more than 10 rows"; "for lists longer than 10 we need a button to view all"). -> markup"""
    from markupsafe import escape
    items = str(text or '').split(', ')
    if len(items) <= FIRST or any(len(i.split()) > 3 for i in items):   # a list of names (R-0234, R-0325 ...), never a sentence cut at its commas (the owner 2026-10-27: "and what the fuck is this / ▶ VIEW ALL 6")
        return f'<div class="{cls}">{escape(text)}</div>'
    return (f'<div class="{cls}">{escape(", ".join(items[:FIRST]))}</div><details class="replica-view-more"><summary class="btn btn--small">▶ View all {len(items)}</summary>'
            f'<div class="{cls}">{escape(", ".join(items[FIRST:]))}</div></details>')


def why_row(w, job, rule_block):
    """ONE ROW OF WHY IT'S RED, the original's markup (scrum.html line 127): the name and OWNER on the left, the one plain sentence that fixes it,
    the why and the full rules folded under it (the rule from the agent's own job, never in the open), and the status now with its ticking red time."""
    from markupsafe import escape
    owner = ' class="scrum-why-owner" data-owner="{0}"'.format(escape(w['name'])) if w['owner'] else ''
    status = ('<span class="scrum-key">"' + str(escape(w['doing'])) + '"</span>') if w['working'] else '<span class="scrum-idle">IDLE</span>'
    since = f' <span class="hdr-status--error scrum-red-for" data-red-since="{escape(w["red_since"])}"></span>' if w['red_since'] else ''
    return (f'<tr data-why="{escape(w["key"])}" data-fixed="no"{owner}><td>{escape(w["name"])}{" · OWNER" if w["owner"] else ""}</td>'
            f'<td>{listed(w["fix"], "scrum-why-fix")}<details class="scrum-why-rules" data-why-rules="{escape(w["key"])}"><summary class="annotation">▶ why it is red, and the full rules</summary>'
            f'<div class="clarity scrum-rules-panel scrum-why-rules-body">{rule_block(w["file"], job, fold=False)}</div></details></td>'
            f'<td data-status="{escape(w["key"])}"{" class=\"scrum-why-working\"" if w["working"] else ""}>{status}{since}</td></tr>')   # a fixer at work: its status green (the owner 2026-10-28: "green when fixing it")


def why_body(rows, jobs, rule_block):
    """WHY IT'S RED's rows: EVERY red, no limit and no View all button (the owner 2026-10-27: "▶ VIEW ALL 7 / no limit on the reds / dont do this"). -> markup"""
    if not rows:
        return '<tr class="replica-why-none"><td colspan="3">Nothing is red.</td></tr>'
    return ''.join(why_row(w, jobs.get(w.get('job_key') or w['key']) or {}, rule_block) for w in rows)


def why_head(rows, now=None):
    """THE TOP OF THE RED, the original's (scrum.html line 113): the count in big type with its small timer after it, and under it the status line,
    IDLE with its cycle time, WORKING ON "<the red>" while a fixer works, STUCK ON when its fixer is stuck (the owner 2026-10-27: "where is the count
    on the top for the red in big font?"; "missing IDLE under it and cycle time"). -> markup"""
    from markupsafe import escape
    now = now or {'word': 'IDLE', 'name': '', 'since': ''}
    sinces = sorted(w['red_since'] for w in rows if w.get('red_since'))
    reds = (f'<div id="scrum-reds" class="title" role="status"><span id="scrum-reds-count" class="{"hdr-status--error" if rows else "scrum-idle"}">{len(rows)} RED</span>'
            f' <span id="scrum-reds-since" class="caption hdr-status--error scrum-reds-since" data-red-since="{escape(sinces[0]) if sinces else ""}" data-red-plain="for"{"" if sinces else " hidden"}></span></div>')
    word = now['word']
    cls = 'hdr-status--error' if word == 'STUCK' else 'hdr-status--success' if word == 'WORKING' else 'scrum-idle'
    line = (f'<span class="{cls}">{escape(word)} ON</span> <span class="scrum-key">"{escape(now["name"])}"</span>' if word in ('WORKING', 'STUCK') and now['name']
            else f'<span class="scrum-idle">{escape(word)}</span>')
    since = f'<span class="scrum-since {cls}" data-since="{escape(now["since"])}"></span>' if now.get('since') else ''
    from markupsafe import Markup
    return Markup(f'<div id="scrum-red-head">{reds}<div id="scrum-red-now" class="subtitle" role="status">{line}{since}</div></div>')


def why_view(rows, jobs, rule_block, now=None):
    """WHY IT'S RED inside the LIVE panel, under the monitor table, the original's title and table (scrum.html lines 125 to 128): three columns, Row,
    Why it's red, Status now; a block like every other, never hidden (the owner 2026-10-27: "its a fucking block like any other block ... there are no
    hidden blocks"); the page's stream fills the rows in place. -> markup"""
    reds = str(why_head(rows, now))   # THE COUNT ON TOP IN BIG TYPE, its small timer after it, the original's (scrum.html line 113; the owner 2026-10-27: "where is the count on the top for the red in big font?")
    return (reds +   # no WHY IT'S RED title over the table (the owner 2026-10-28: "delte WHY IT'S RED above the table")
            f'<div class="scaf-wrap" id="scrum-why-wrap"><table class="scrum-term" id="scrum-why"><thead><tr><th class="scrum-why-row">Row</th><th>Why it\'s red</th>'
            f'<th class="scrum-why-status">Status now</th></tr></thead><tbody>{why_body(rows, jobs, rule_block)}</tbody></table></div>')


def canvas_fields(sh, logs, card, light):
    """WHAT THE ONE SHELL'S CANVAS HEADER AND FOOTER SAY OF AN AGENT, EVERY FIELD AS ITS RECORD HOLDS IT (the owner 2026-11-01: "all data in
    the shell needs to be 100% from the database with zero hard coded"): its agnt record (data_agent_number, data_full_name,
    data_agent_pitch), its shell's slot on this office's board, its job (data_job_run_state as written; data_job_time, data_job_location and
    data_job_schedule_type as written), its LOGS (each run's identity_log_time and data_log_message as written, its notes' summary when it
    wrote one), its rules' review (data_job_rules_review_description, its first two parts: who, when), and its light (frame light_of of its
    job). Nothing typed, nothing translated: a field with no record behind it is left out and the shell says its dash. -> dict"""
    import json
    job = sh.get('job') or {}
    out = {'name': card.get('data_full_name') or '', 'about': card.get('data_agent_pitch') or '', 'light': light or '', 'group': sh.get('slot') or '',
           'status': job.get('data_job_run_state') or '',
           'runs': ' '.join(str(job.get(k) or '') for k in ('data_job_time', 'data_job_location', 'data_job_schedule_type')).strip().upper()}
    if card.get('data_agent_number'):
        out['number'] = str(card['data_agent_number'])
    review = [p.strip() for p in str(job.get('data_job_rules_review_description') or '').split(' · ')]
    if len(review) >= 3:
        out['rules_by'], out['rules_at'] = review[0], review[1]
    if logs:
        out['idle'] = str(logs[0].get('data_log_message') or '').split(' → ')[-1].split(' · ')[0]   # its newest run's end, as its LOGS record wrote it
    days = []
    for r in logs:   # newest first: the newest run of each of the two newest days its LOGS hold
        day = str(r.get('identity_log_time') or '')[:10]
        if day and day not in [d for d, _r in days]:
            days.append((day, r))
        if len(days) == 2:
            break
    for word, (day, r) in zip(('today', 'yesterday'), days):
        try:
            summary = json.loads(r.get('data_notes') or '{}').get('summary') or ''
        except (ValueError, AttributeError):
            summary = ''
        out[word] = {'date': day, 'said': summary or str(r.get('data_log_message') or '')}
    return out


def with_reds(x, shells, reds, red_group):
    """THE X BOARD WITH THE RED (the owner 2026-10-28: "why x if red"; "the count was never updated for the x board"; "should be no x"), one
    function for the page (web/app.py x_now) and the X Board agent's run alike, so the run says what the board shows: an agent in the red is
    not done (off its group's count, open, its red counted, no X); THE RED is its group's own row when it is not a shell already (open, never
    one more red). -> x"""
    red_jobs = {str(w.get('job_key') or w.get('key') or '').split('#')[0] for w in reds}
    red_names = {str((sh['job'] or {}).get('data_full_name') or '').lower() for sh in shells if sh.get('job_key') and sh['job_key'] in red_jobs} - {''}
    for line in x['lines']:
        hit = [n for n in line['names'] if n in red_names and n not in line['open']]
        if hit:
            line['green'] -= len(hit)
            line['red'] += len(hit)
            line['open'] = line['open'] + hit
            line['crossed'] = False
        if reds and line['slot'] == red_group and 'the red' not in line['names']:
            line['total'] += 1
            line['names'] = line['names'] + ['the red']
            line['open'] = line['open'] + ['the red']
            line['crossed'] = False
    return x
