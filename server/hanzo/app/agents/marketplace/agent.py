"""THE AGENT MARKETPLACE: the Pokémon-like collection. It is handed the cards the harness shows (each with the member's
hired state, and whether the member may hire it and why not) and lays them out as the original's cards; it never
reaches anything itself. RUN asks for the report."""
import json
import sys

FILTERS = ('product', 'module', 'type', 'residency', 'class')


def _no(number):
    number = str(number or '').strip()
    return f'NO. {int(number):03d}' if number.isdigit() else ''


def _initials(name):
    words = name.removeprefix('PF ').split()
    return ''.join(w[0] for w in words[:2]).upper()


def _price(price):
    price = str(price or '').strip()
    return 'FREE' if price in ('', '0') else f'{int(price)} mTok'


def _order(card):
    number = str(card.get('number') or '').strip()
    return (0, int(number)) if number.isdigit() else (1, 0)


def collection(cards):
    cards = sorted(cards, key=_order)
    out = [{'key': c['key'], 'no': _no(c.get('number')), 'class': c['class'], 'name': c['name'], 'initials': _initials(c['name']),
            'image_dam_key': c.get('image_dam_key') or '', 'place': f"{c['product']} · {c['module']}", 'pitch': c.get('pitch') or '',
            'developer': c.get('developer') or '', 'type': c.get('type') or '', 'residency': c.get('residency') or '',
            'price': _price(c.get('price')), 'hired': bool(c.get('hired')), 'hireable': bool(c.get('hireable')), 'reason': c.get('reason') or ''}
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
