"""SCRUM MASTER 3, the MARK IV agent of its workflow: the day of every block it holds, read from the jobs records alone (each job's
group, light and today's date), group by group in its own order (agent.json groups): what ran green today, what is red, and one
word, HEALTHY when nothing is red, else CRITICAL. A CALL draws the big header from the records as they are now; a RUN says it as the
job's line."""
import json

import look
import office



def day(given):
    today = office.now().date().isoformat()
    me = office.me()['key']
    blocks = [j for j in office.workflow(given) if j.get('data_job_agentic') != 'WORKFLOW' and j.get('data_agent_key') != me]
    groups = []
    for g in office.fact('groups'):
        held = [j for j in blocks if (j.get('data_job_group') or '').upper() == g]
        green = [j['data_full_name'] for j in held if office.light_of(j) == 'GREEN' and (j.get('data_job_today_date') or '') == today]
        red = [j['data_full_name'] for j in held if office.light_of(j) == 'RED']
        groups.append({'group': g, 'total': len(held), 'green': green, 'red': red})
    red = [n for g in groups for n in g['red']]
    word = office.fact('critical') if red else office.fact('healthy')
    return {'day': today, 'word': word, 'blocks': len(blocks), 'green': sum(len(g['green']) for g in groups), 'red': red, 'groups': groups}


def run(given):
    d = day(given)
    line = f"{d['word']} · {d['green']} green today, {len(d['red'])} red of {d['blocks']} blocks" + (f" · red: {', '.join(d['red'][:6])}" if d['red'] else '')
    return office.done(line, 'RED' if d['red'] else 'GREEN', d)


def canvas(given):
    """SM2's MARK IV view (its .mk-row under the hero words): the card, the platform's own one injected where SM2 held its iframe,
    beside its own words (its agnt record's notes) and what its class is (the card manifest's classes)"""
    me = office.me()
    rec = next((r for r in office.records(given, 'agnt') if r.get('key') == me['key']), {})
    try:
        with open(office.fact('card_manifest'), encoding='utf-8') as fh:
            classes = json.load(fh).get('classes') or {}
    except (OSError, ValueError):
        classes = {}
    klass = str(rec.get('data_agent_class') or me['card']['class']).upper()
    what = next((w for k, w in classes.items() if klass.startswith(k.upper())), None) or {}
    hero, e = office.fact('hero'), office.e
    words = (f'<div class="body">{e(rec.get("data_notes"))}</div>' if rec.get('data_notes') else '') + (
        f'<div class="replica-what"><div class="callout">{e(what.get("title"))}</div>' + ''.join(f'<div class="notes">{e(n)}</div>' for n in what.get('notes') or ()) + '</div>'
        if what else '')
    text = ('<div class="replica-canvas"><div class="replica-canvas-content"><div class="amx-hero replica-agent-hero">'
            f'<div class="amx-kicker">{e(hero["kicker"])}</div><div class="amx-h1">{e(hero["title"])}</div><div class="amx-sub">{e(hero["sub"])}</div></div>'
            f'<div class="mk-row"><div class="mk-side"><div data-inject="agent_card" data-agent="{e(me["key"])}" data-size="full"></div></div>'
            f'<div class="mk-say">{words}</div></div></div></div>')
    # the card draws itself card_drawn px wide (card.css); SM2's box was card_box px; the ink SM2's host gave it, here the theme's own
    drawn, box = office.fact('card_drawn'), office.fact('card_box')
    css = (f'.mk-side {{ width: {drawn}px; zoom: {round(box / drawn, 4)}; }} .replica-canvas {{ color: var(--active-color-01); }} '
           '.replica-what > .callout, .replica-what > .callout + .notes { color: var(--active-color-01); }')
    return look.view(text, str((given.get('page') or {}).get('path') or ''), css)


if __name__ == '__main__':
    office.main(canvas, run)
