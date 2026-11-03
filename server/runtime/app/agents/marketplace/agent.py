"""THE AGENT MARKETPLACE: a controller at the top and a grid of cards below, nothing more (the owner 2026-11-03: "the marketplace just
makes the marketplace / has a controler at the top and a grid of cards below.. nothing more than that"; "should be simple"). It is handed
the cards the harness shows (each with the member's hired state and whether the member may hire it) and answers them in order, with the
counts and the filters, as data; where each card stands in the grid is a placeholder the platform's host fills with its one agent card
(themes/embedded/agent_cards), every value from the platform's own record of that key ("larryd should just have the agent code and data
to populate the database and our endpoint dynamically generates the card from dynamic data / no other info from larryd"). It never
reaches anything itself. RUN asks for the report."""
import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
FILTERS = ('product', 'module', 'type', 'residency', 'class')
SEARCHED = ('name', 'product', 'module', 'pitch', 'developer', 'class')
ORDERS = (('number', 'Number'), ('name', 'Name'), ('product', 'Product'), ('mark', 'Mark'), ('price', 'Price'))   # number: the collection's own order


def _number(number):
    number = str(number or '').strip()
    return int(number) if number.isdigit() else None


def _rate(price):
    price = str(price or '').strip()
    return int(price) if price.isdigit() else 0


def _slug(v):
    return ''.join(ch for ch in str(v or '').lower() if ch.isalnum())


def _found(card, find):
    """Does the card pass what the controller asks: every word of the search in its name, product, module, pitch, developer or class;
    hired, when only the member's own are asked for; of the picked product, and of its picked module."""
    if find.get('hired') and not card.get('hired'):
        return False
    if find.get('product') and _slug(card.get('product')) != _slug(find['product']):
        return False
    if find.get('module') and _slug(card.get('module')) != _slug(find['module']):
        return False
    text = ' '.join(str(card.get(k) or '') for k in SEARCHED).lower()
    return all(word in text for word in str(find.get('q') or '').lower().split())


def _sorted(cards, sort):
    """The cards in the order asked (name, product, mark, price: lowest first), each tie in the collection's own order (its number)."""
    number = lambda c: (0, _number(c.get('number'))) if _number(c.get('number')) is not None else (1, 0)
    keys = {'name': lambda c: str(c.get('name') or '').lower(), 'product': lambda c: (str(c.get('product') or '').lower(), str(c.get('module') or '').lower()),
            'mark': lambda c: str(c.get('class') or '').upper(), 'price': lambda c: _rate(c.get('price'))}
    cards = sorted(cards, key=number)
    return sorted(cards, key=keys[sort]) if sort in keys else cards


def collection(cards, themes=None, find=None, page=None):
    """-> the cards shown, as data (their keys and the member's hire of each), the counts, the filters and the view. themes: no longer read
    (the card's look is the platform's), kept so an older caller's hand is still taken."""
    find = find if isinstance(find, dict) else {}
    everything, hired = len(cards), sum(1 for c in cards if c.get('hired'))   # the whole collection's counts, whatever is looked for
    shown = _sorted([c for c in cards if isinstance(c, dict) and c.get('key') and _found(c, find)], find.get('sort') or '')
    out = [{'key': c['key'], 'number': _number(c.get('number')), 'name': c.get('name') or '', 'class': c.get('class') or '', 'product': c.get('product') or '',
            'module': c.get('module') or '', 'hired': bool(c.get('hired')), 'hireable': bool(c.get('hireable')), 'offline': c.get('offline') is True}
           for c in shown]
    answer = {'cards': out, 'total': everything, 'hired': hired, 'shown': len(out), 'filters': {f: sorted({str(c[f]) for c in shown if c.get(f)}) for f in FILTERS}}
    return {**answer, 'view': view(answer, orgchart=find.get('orgchart') is True, page=page, find=find)}


def _card(c, orgchart=False):
    """WHERE ONE CARD STANDS IN THE GRID, AND NOTHING MORE: the platform's host puts its one agent card there, full in the CARD view, mini in
    the ORG CHART view (the owner 2026-11-03: "the org chart for now will just be the mini cards")."""
    key = str(c.get('key') or '')
    return f'<div data-inject="agent_card" data-agent="{key}" data-size="{"mini" if orgchart else "full"}"></div>' if re.fullmatch(r'[A-Z0-9_]{8,64}', key) else ''


def _controller(answer, find, page):
    """THE CONTROLLER AT THE TOP, drawn with the platform's own controller classes (the page's sheets stand inside the shadow root): the
    counts (AGENTS: n hired · n total in network) · All agents / Hired agents · View (Card / Org chart) · Product level, under a picked product its Module level (each group showing its selected one,
    Off first); Quick search · Sort by. EVERY LINK IS THE PAGE'S OWN, AS GIVEN (page.links; none is built here), the search a GET to
    page.links.search with the page's kept words (page.search) and q; the products and their modules the page's lists (page.products,
    page.modules). No links given: no controller. A link not given: its button is left out."""
    links = page.get('links')
    if not isinstance(links, dict) or not isinstance(links.get('search'), str) or not links['search']:
        return ''
    e = lambda v: html.escape(str(v), quote=True).replace('&#x27;', '&#39;')
    of = lambda group, key: (links.get(group) or {}).get(key) if isinstance(links.get(group), dict) else None
    current = ' aria-current="true"'

    def small(word, on, at):
        return f'<a class="btn btn--small" href="{e(at)}"{current if on else ""}>{e(word)}</a>' if isinstance(at, str) and at else ''

    mine, orgchart, sort = bool(find.get('hired')), find.get('orgchart') is True, find.get('sort') if find.get('sort') in dict(ORDERS) else 'number'
    products = [(str(p[0]), str(p[1])) for p in page.get('products') or [] if isinstance(p, (list, tuple)) and len(p) == 2] if isinstance(page.get('products'), list) else []
    product = next((slug for slug, _name in products if _slug(slug) == _slug(find.get('product'))), '') if find.get('product') else ''
    modules = page.get('modules').get(product) if product and isinstance(page.get('modules'), dict) else None
    modules = [str(m) for m in modules] if isinstance(modules, list) else []
    module = next((m for m in modules if _slug(m) == _slug(find.get('module'))), '') if find.get('module') else ''
    level = ('<div class="label wl-label">Product level</div><div class="wl-btnrow">' + small('Off', not product, links.get('product_off'))
             + ''.join(small(name, slug == product, of('product', slug)) for slug, name in products) + '</div>') if products else ''
    if product and modules:
        level += ('<div class="label wl-label">Module level</div><div class="wl-btnrow">' + small('Off', not module, links.get('module_off'))
                  + ''.join(small(m, m == module, of('module', m)) for m in modules) + '</div>')
    sorts = ' · '.join(f'<a class="{"emphasis mk-sorted" if key == sort else "annotation"}" href="{e(of("sort", key))}"{current if key == sort else ""}>{word}</a>'
                       for key, word in ORDERS if isinstance(of('sort', key), str) and of('sort', key))
    kept = page.get('search') if isinstance(page.get('search'), dict) else {}
    kept = ''.join(f'<input type="hidden" name="{e(k)}" value="{e(v)}">' for k, v in kept.items() if re.fullmatch(r'[a-z_]{1,32}', str(k)) and k != 'q' and isinstance(v, (str, int)) and str(v) != '')
    search = str(find.get('q') or '')
    return ('<div class="sub-controller-box wl-glass mk-ctl"><div class="wl-panel"><div class="sub-contacts-header"><div class="sub-controller-box"><div class="sub-controller">'
            '<div class="wl-rule"></div><div class="emphasis">Controller</div><div class="wl-rule"></div><div class="wl-cols">'
            f'<div class="wl-col--1"><div class="subtitle">Agents</div><div class="emphasis">{answer["hired"]} hired · {answer["total"]} total in network</div><div class="wl-rule wl-rule--gap"></div>'
            f'<div class="mk-ctl-row"><div><div class="label wl-label">Hired agents</div><div class="wl-btnrow">{small("All agents", not mine, links.get("mine_off"))}{small("Hired agents", mine, links.get("mine_on"))}</div></div>'
            f'<div><div class="label wl-label">View</div><div class="wl-btnrow">{small("Card", not orgchart, links.get("view_card"))}{small("Org chart", orgchart, links.get("view_orgchart"))}</div></div></div>'
            f'{level}</div><div class="wl-divider"></div>'
            '<div class="wl-col--3"><div class="subtitle">Quick search</div><div class="emphasis">Lookup by</div><div class="wl-rule wl-rule--gap"></div>'
            f'<form method="get" action="{e(links["search"])}" class="sub-search-form">{kept}<div class="sub-search-form-container">'
            f'<input type="text" name="q" class="sub-search-input" placeholder="Find…" value="{e(search)}"><button class="btn btn--small" type="submit">Search</button>'
            + (small('Reset', False, links.get('reset')) if search else '') + '</div></form>'
            + (f'<div class="label wl-label">Sort by</div><div class="annotation">{sorts}</div>' if sorts else '') + '</div>'
            '</div></div></div></div></div></div>')


def view(answer, orgchart=False, page=None, find=None):
    """THE MARKETPLACE: the controller at the top, the grid of cards below; its own sheet (marketplace.css, in its code hash) lays them out."""
    grid = ''.join(_card(c, orgchart) for c in answer['cards'])
    markup = (_controller(answer, find if isinstance(find, dict) else {}, page if isinstance(page, dict) else {})
              + f'<div class="mk-grid{" mk-orgchart" if orgchart else ""}">{grid}</div>')
    path = HERE / 'marketplace.css'
    return {'html': markup, 'css': path.read_text(encoding='utf-8') if path.is_file() else ''}


def report(cards):
    total, hired = len(cards), sum(1 for c in cards if c.get('hired'))
    return {'delivery': f"{total} agent{'' if total == 1 else 's'} in the collection · {hired} hired", 'total': total, 'hired': hired}


def main():
    given = json.load(sys.stdin)
    do = {'collection': collection, 'report': report}.get(given.get('do'))
    if do is None:
        raise SystemExit('the marketplace does: collection, report')
    cards = given.get('cards') or []
    print(json.dumps(collection(cards, given.get('themes'), given.get('find'), given.get('page')) if do is collection else do(cards)))


if __name__ == '__main__':
    main()
