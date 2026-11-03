"""THE BACKLOG'S INTERFACE, drawn for the platform's view gate (core_engine/view.py: no table, no textarea, no label, no id, a form only a GET
to the page itself). The office drew it with web/page.py interface_view (tables, POST forms to its own agent_press route), which the gate
refuses; here the same content, from the office's own agent026_day_backlog.py (backlog(store), request_row(r), press(...)), in plain blocks.
A press is a GET to the page itself carrying act=1 (the member's own act); REMOVE and CLEAR ALL ask once before they go (sure=1)."""
import html as _html

CSS = ('.sm3-backlog { display: block; text-align: left } .sm3-backlog .sm3-title { font-family: var(--clarity-face-heading, inherit); font-size: 1.3rem; font-weight: 900; letter-spacing: .04em; text-transform: uppercase; margin: 0 0 12px } '
       '.sm3-backlog .sm3-req { border-top: 1px solid var(--ui-row-divider, currentColor); padding: 10px 0 } .sm3-backlog .sm3-head { font-weight: 700 } '
       '.sm3-backlog .sm3-note, .sm3-backlog .sm3-why { font-size: .9rem; opacity: .8 } .sm3-backlog .sm3-words { font-family: ui-monospace, Menlo, monospace; white-space: pre-wrap; word-break: break-word; margin: 6px 0 } '
       '.sm3-backlog .sm3-status { font-weight: 700; letter-spacing: .04em } .sm3-backlog .sm3-copy { font-family: ui-monospace, Menlo, monospace; user-select: all; word-break: break-all } '
       '.sm3-backlog form { display: inline-flex; gap: 6px; align-items: center; margin: 6px 8px 0 0 } .sm3-backlog input[type=text] { min-width: 18em } '
       '.sm3-backlog .sm3-said { font-weight: 700; margin: 0 0 12px } .sm3-backlog .sm3-ask { margin: 8px 0; font-weight: 700 } .sm3-backlog .sm3-empty { opacity: .8 }')


def e(v):
    return _html.escape(str(v if v is not None else ''), quote=True)


def form(path, do, value='', label='', words=False, sure=False, placeholder=''):
    """one press: a GET to the page itself, act=1, the press, its request, his words when it takes them, sure=1 when it was asked"""
    return (f'<form method="get" action="{e(path)}"><input type="hidden" name="act" value="1"><input type="hidden" name="do" value="{e(do)}">'
            + (f'<input type="hidden" name="value" value="{e(value)}">' if value else '')
            + ('<input type="hidden" name="sure" value="1">' if sure else '')
            + (f'<input type="text" name="words" value="" placeholder="{e(placeholder)}">' if words else '')
            + f'<button class="btn btn--small" type="submit">{e(label)}</button></form>')


def request_block(row, path, asking):
    c0, c1, st = row['cells']
    presses = []
    for p in row.get('presses') or ():
        if p['do'] == 'remove' and asking == ('remove', row['key']):
            presses.append(f'<div class="sm3-ask">{e(p.get("confirm"))}</div>' + form(path, 'remove', row['key'], 'YES, REMOVE', sure=True) + form(path, '', '', 'NO'))
        else:
            presses.append(form(path, p['do'], row['key'], p['label'], words=bool(p.get('text')), placeholder=p.get('placeholder', '')))
    since = f' · {e(st["label"])} since {e(st["since"][:16].replace("T", " "))}' if st.get('since') else ''
    return (f'<div class="sm3-req" data-request="{e(row["key"])}"><div class="sm3-head">{e(c0["text"])}</div><div class="sm3-note">{e(c0.get("note"))}</div>'
            f'<div class="sm3-words">{e(c1["text"])}</div><div><span class="sm3-status">{e(st["word"])}</span>{since}</div>'
            + (f'<div class="sm3-why">{e(st["text"])}</div>' if st.get('text') else '')
            + (f'<div class="sm3-copy">{e(row["copy"])}</div>' if row.get('copy') else '')
            + f'<div>{"".join(presses)}</div></div>')


def view(module, store, job_key, path, search):
    """-> {'html', 'css'}: the press first (his act), then the backlog read fresh"""
    one = lambda k: str((search or {}).get(k) or '')   # noqa: E731
    said, asking = '', None
    do = one('do')
    if one('act') == '1' and do in module.PRESSES:
        if do in ('remove', 'clear') and one('sure') != '1':
            asking = (do, one('value'))
        else:
            said = module.press(store, job_key, do, fields={'value': one('value'), 'words': one('words')})
    content = module.content(store, job_key)
    out = [f'<div class="sm3-said">{e(said)}</div>'] if said else []
    for part in content:
        if part.get('kind') == 'note':
            out.append(f'<div class="sm3-title">{e(part.get("title"))}</div><div class="body">{e(part.get("text"))}</div>')
        elif part.get('kind') == 'table':
            out.append(f'<div class="sm3-title">{e(part.get("title"))}</div>')
            rows = part.get('rows') or []
            out.extend(request_block(r, path, asking) for r in rows)
            if not rows:
                out.append(f'<div class="sm3-empty">{e(part.get("empty"))}</div>')
        elif part.get('kind') == 'press':
            if asking and asking[0] == part.get('do'):
                out.append(f'<div class="sm3-ask">{e(part.get("confirm"))}</div>' + form(path, part['do'], '', 'YES, ' + part.get('label', '').upper(), sure=True) + form(path, '', '', 'NO'))
            else:
                out.append(form(path, part['do'], '', part.get('label', '')))
    return {'html': '<div class="replica-canvas"><div class="replica-canvas-content"><div class="sm3-backlog">' + ''.join(out) + '</div></div></div>', 'css': CSS}
