"""THE AGENT MARKETPLACE: the Pokémon-like collection. It is handed the cards the harness shows (each with the member's
hired state, whether the member may hire it, and the product whose subscription it needs when not) and answers them
as the original's cards, in order, with the counts and the filters; values only, never words (the platform says them
in the member's language). It never reaches anything itself. RUN asks for the report."""
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

FILTERS = ('product', 'module', 'type', 'residency', 'class')
def _number(number):
    number = str(number or '').strip()
    return int(number) if number.isdigit() else None


def _initials(name):
    words = name.removeprefix('PF ').split()
    return ''.join(w[0] for w in words[:2]).upper()


def _rate(price):
    price = str(price or '').strip()
    return int(price) if price.isdigit() else 0


def _order(card):
    number = _number(card.get('number'))
    return (0, number) if number is not None else (1, 0)


def collection(cards):
    cards = sorted(cards, key=_order)
    out = [{'key': c['key'], 'number': _number(c.get('number')), 'class': c.get('class') or '', 'name': c['name'], 'initials': _initials(c['name']),
            'image_dam_key': c.get('image_dam_key') or '', 'product': c['product'], 'module': c['module'], 'pitch': c.get('pitch') or '',
            'developer': c.get('developer') or '', 'type': c.get('type') or '', 'residency': c.get('residency') or '',
            'screen': c.get('screen') or '', 'sends_to': c.get('sends_to') or '', 'data_sent': c.get('data_sent') or '',
            'rate': _rate(c.get('price')), 'hired': bool(c.get('hired')), 'hireable': bool(c.get('hireable')), 'needs': c.get('needs') or '',
            'art': c.get('art') or ''}
           for c in cards]
    answer = {'cards': out, 'total': len(out), 'hired': sum(1 for c in out if c['hired']),
              'filters': {f: sorted({c[f] for c in cards if c.get(f)}) for f in FILTERS}}
    return {**answer, 'view': view(answer)}


def _sheet():
    path = HERE / 'card.css'
    return path.read_text(encoding='utf-8') if path.is_file() else ''


def _title():
    try:
        return json.loads((HERE / 'agent.json').read_text(encoding='utf-8')).get('name') or ''
    except (OSError, ValueError):
        return ''


def _card(c):
    e = lambda v: html.escape(str(v), quote=True).replace('&#x27;', '&#39;')
    number = f'<span class="caption" data-part="number">No. {c["number"]:03d}</span>' if c['number'] is not None else ''
    art = f'<img class="mk-art" src="{e(c["art"])}" alt="" loading="lazy">' if c['art'] else f'<span class="title mk-initials">{e(c["initials"])}</span>'
    price = f'{c["rate"]} mTok' if c['rate'] else 'Free'
    toggle = (f'<button type="button" class="toggle" data-hire="{e(c["key"])}" aria-pressed="{"true" if c["hired"] else "false"}" title="Hire">'
              '<span class="toggle__knob"></span></button>')
    extra = ''.join([
        f'<div class="caption mk-needs">Needs the {e(c["needs"])} subscription</div>' if c['needs'] else '',
        (f'<div class="caption mk-sends">Sends data to {e(c["sends_to"])}' + (f': {e(c["data_sent"])}' if c['data_sent'] else '') + '</div>') if c['sends_to'] else '',
        f'<div class="annotation mk-home">lives on {e(c["screen"])}</div>' if c['screen'] else ''])
    return (f'<article class="agent-card{" mk-on" if c["hired"] else ""}" data-agent="{e(c["key"])}" data-on="{"1" if c["hired"] else "0"}">'
            f'<div class="mk-head"><div class="mk-id">{number}<span class="caption" data-part="class">{e(c["class"])}</span></div>'
            f'<div class="mk-hire">{toggle}<span class="annotation">Hire</span></div></div>'
            f'<div class="title mk-name" data-part="name">{e(c["name"])}</div>'
            f'<div class="mk-frame">{art}</div>'
            f'<div class="annotation mk-info" data-part="info">{e(c["product"])} · {e(c["module"])}</div>'
            f'<div class="body mk-flavour" data-part="pitch">{e(c["pitch"])}</div>'
            f'<div class="annotation mk-credit" data-part="developer">Developer · {e(c["developer"])}</div>'
            f'<div class="mk-foot"><span class="annotation" data-part="facts">▸ {e(c["type"])} ▸ {e(c["residency"])}</span>'
            f'<span class="callout mk-price" data-part="price">{price}</span></div>{extra}</article>')


def view(answer):
    """THE MARKETPLACE'S OWN VIEW (the owner, 2026-10-07: the card lives in the agent, never in the platform's core): the
    whole panel's markup, every value escaped, each card's hire control a button the platform's host turns into its own
    signed hire (data-hire, aria-pressed), and this agent's own sheet (card.css, in its code hash)."""
    cards = ''.join(_card(c) for c in answer['cards'])
    markup = (f'<section class="mk-panel"><div class="mk-controller"><div class="mk-title">{html.escape(_title())}</div>'
              f'<div class="caption">{answer["total"]} total in network · {answer["hired"]} hired</div>'
              '<div class="caption">Hire an agent with the hire toggle on its card. Once hired, it is ready to switch on in your settings.</div></div>'
              f'<div class="mk-grid">{cards}</div></section>')
    return {'html': markup, 'css': _sheet()}


def report(cards):
    total, hired = len(cards), sum(1 for c in cards if c.get('hired'))
    return {'delivery': f"{total} agent{'' if total == 1 else 's'} in the collection · {hired} hired", 'total': total, 'hired': hired}


def main():
    given = json.load(sys.stdin)
    do = {'collection': collection, 'report': report}.get(given.get('do'))
    if do is None:
        raise SystemExit('the marketplace does: collection, report')
    print(json.dumps(do(given.get('cards') or [])))


if __name__ == '__main__':
    main()
