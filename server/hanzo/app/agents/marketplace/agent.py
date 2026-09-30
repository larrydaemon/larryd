"""THE AGENT MARKETPLACE: the Pokémon-like collection. It is handed the cards the harness shows (each with the member's
hired state, whether the member may hire it, and the product whose subscription it needs when not) and answers them
as the original's cards, in order, with the counts and the filters; values only, never words (the platform says them
in the member's language). It never reaches anything itself. RUN asks for the report."""
import json
import sys

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
            'rate': _rate(c.get('price')), 'hired': bool(c.get('hired')), 'hireable': bool(c.get('hireable')), 'needs': c.get('needs') or ''}
           for c in cards]
    return {'cards': out, 'total': len(out), 'hired': sum(1 for c in out if c['hired']),
            'filters': {f: sorted({c[f] for c in cards if c.get(f)}) for f in FILTERS}}


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
