"""X BOARD, the shared block of every MARK IV workflow (owned by Operations Manager): the page workflow's blocks counted by group,
a block green when its job's light is GREEN; a group's X when green equals total (0 of 0 too); HEALTHY or CRITICAL (a red block).
The groups and their words are the card manifest's (read where it lives; SM2's own words over them), then any other a block names;
the MARK IV's own slot (agent_slot) is never a row, as on SM2."""
import json

import look
import office



def board(given):
    name = office.page_workflow(given)
    if not name:
        raise ValueError('no workflow found for this page: no WORKFLOW job holds its screen')
    try:
        with open(office.fact('card_manifest'), encoding='utf-8') as fh:
            manifest = json.load(fh)
    except (OSError, ValueError):
        manifest = {}
    says = {str(k).upper(): v for k, v in {**(manifest.get('says') or {}), **(office.fact('says') or {})}.items()}   # the manifest's words, SM2's own over them
    got = {str(g).upper(): [] for g in manifest.get('groups') or []}
    own = str(office.fact('agent_slot') or '').upper()   # THE MARK IV'S OWN SLOT (SM2's root shape agent_slot): the board's own agent, never a row of it
    for j in office.workflow(given, name):
        group = str(j.get('data_job_group') or j['card'].get('data_agent_group') or '').upper()
        if j.get('data_job_agentic') == 'WORKFLOW' or not j.get('data_agent_key') or not group or group == own:
            continue
        got.setdefault(group, []).append({'name': j.get('data_full_name') or j['card'].get('data_full_name') or j['data_agent_key'],
                                          'green': office.light_of(j) == office.fact('green'), 'red': office.light_of(j) == office.fact('red')})
    lines = [{'group': g, 'green': sum(x['green'] for x in xs), 'total': len(xs), 'crossed': sum(x['green'] for x in xs) == len(xs),
              'names': xs, 'says': says.get(g, '')} for g, xs in got.items() if xs]   # only the groups this workflow holds (a shared board serves every MARK IV)
    red = sum(x['red'] for xs in got.values() for x in xs)
    return {'workflow': name, 'day': office.now().strftime('%a %b %d').upper() + ' (TODAY)', 'lines': lines, 'red': red,
            'green': sum(x['green'] for x in lines), 'total': sum(x['total'] for x in lines), 'word': 'CRITICAL' if red else 'HEALTHY'}


# SM2's X: its svg drawn as two strokes of the box's own ink (look drops svg)
CSS = """
.replica-xline[data-crossed="yes"] > .replica-xbox {
  background: linear-gradient(to top right, transparent calc(50% - 2.5px), var(--clarity-ink) calc(50% - 2.5px), var(--clarity-ink) calc(50% + 2.5px), transparent calc(50% + 2.5px)),
              linear-gradient(to bottom right, transparent calc(50% - 2.5px), var(--clarity-ink) calc(50% - 2.5px), var(--clarity-ink) calc(50% + 2.5px), transparent calc(50% + 2.5px)); }
"""


def canvas(given):
    """SM2's X board (its frame's replica-xboard-agent), its own markup and classes; the counting is this board's"""
    b = board(given)
    e = office.e
    rows = ''.join(
        f'<div class="replica-xline" role="row" data-x-group="{e(x["group"])}" data-crossed="{"yes" if x["crossed"] else "no"}">'
        f'<span class="replica-xgroup" role="cell"><span>{e(x["group"])}</span><span class="replica-xcount">{x["green"]}/{x["total"]}</span></span>'
        f'<span class="replica-xbox" role="cell" aria-label="{"done" if x["crossed"] else "not done"}"></span>'
        '<span class="replica-xwhat" role="cell"><span class="replica-xlist">'
        + ', '.join(e(n['name'].lower()) if n['green'] else f'<span class="replica-xopen">{e(n["name"].lower())}</span>' for n in x['names'])
        + '</span>' + (f'<span class="replica-xsays">{e(x["says"])}</span>' if x['says'] else '') + '</span></div>' for x in b['lines'])
    text = ('<div class="replica-xboard-agent"><div class="replica-group" aria-label="group">TOP</div>'
            '<div class="clarity replica-xboard" role="table" aria-label="X BOARD">'
            f'<div class="replica-xboard-head" role="row"><span class="replica-xboard-title">X BOARD</span><span class="replica-xboard-day">{e(b["day"])}</span></div>'
            '<div class="replica-xline replica-xcols" role="row"><span role="columnheader">GROUP STATUS</span><span role="columnheader">COMPLETE</span>'
            f'<span role="columnheader">WHAT MAKES THE X</span></div>{rows}</div></div>')
    return look.view(text, str((given.get('page') or {}).get('path') or ''), CSS)


def run(given):
    b = board(given)
    xs = ' · '.join(f"{x['group']} {x['green']}/{x['total']}{' X' if x['crossed'] else ''}" for x in b['lines'])
    return office.done(f"{b['word']} · {b['workflow']}: {b['green']} green, {b['red']} red of {b['total']} · {xs}", 'GREEN',
                       {k: b[k] for k in ('workflow', 'word', 'green', 'red', 'total')})

if __name__ == '__main__':
    office.main(canvas, run)
