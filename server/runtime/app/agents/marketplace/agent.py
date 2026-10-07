"""THE AGENT MARKETPLACE: the Pokémon-like collection. It is handed the cards the harness shows (each with the member's
hired state, whether the member may hire it, and the product whose subscription it needs when not) and answers them
as the original's cards, in order, with the counts and the filters; values only, never words (the platform says them
in the member's language). It never reaches anything itself. RUN asks for the report."""
import html
import json
import pathlib
import re
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


def _site(address):
    """A developer's website as a link the card may draw: a plain https address, else none (a link is drawn only when it works)."""
    address = str(address or '').strip()
    return address if address.startswith('https://') and not any(ch.isspace() or ch in '"\'<>\\' for ch in address) else ''


def _rating(card):
    """A card's rating as its strip shows it: ('4.8', 212), or none when the card has no rating yet (a score from 0 to 5, a count of at least 1)."""
    try:
        score, count = float(card.get('rating')), int(card.get('reviews'))
    except (TypeError, ValueError):
        return None
    return (f'{score:.1f}', count) if 0 <= score <= 5 and count > 0 else None


def _order(card):
    number = _number(card.get('number'))
    return (0, number) if number is not None else (1, 0)


SORTS = ('', 'name', 'product', 'mark', 'rating', 'price')   # '' = the collection's own order (by number)
SEARCHED = ('name', 'product', 'module', 'pitch', 'developer', 'class')


def _found(card, find):
    """Does the card pass what the controller asks: every word of the search somewhere in its name, product, module, pitch, developer or class;
    when only the member's own are asked for, hired; and, when a product level is picked, of that product."""
    if find.get('hired') and not card.get('hired'):
        return False
    slug = lambda v: ''.join(ch for ch in str(v or '').lower() if ch.isalnum())
    if find.get('product') and slug(card.get('product')) != slug(find['product']):   # the product level: one product's cards only
        return False
    if find.get('module') and slug(card.get('module')) != slug(find['module']):   # the module level, under a picked product: one module's cards only
        return False
    text = ' '.join(str(card.get(k) or '') for k in SEARCHED).lower()
    return all(word in text for word in str(find.get('q') or '').lower().split())


def _sorted(cards, sort):
    """The cards in the order asked (name, product, mark, rating: best first, price: lowest first), each tie in the collection's own order."""
    cards = sorted(cards, key=_order)
    keys = {'name': lambda c: str(c.get('name') or '').lower(), 'product': lambda c: (str(c.get('product') or '').lower(), str(c.get('module') or '').lower()),
            'mark': lambda c: str(c.get('class') or '').upper(), 'rating': lambda c: -float((_rating(c) or ('-1',))[0]), 'price': lambda c: _rate(c.get('price'))}
    return sorted(cards, key=keys[sort]) if sort in keys else cards


def collection(cards, themes=None, find=None, page=None):
    find = find if isinstance(find, dict) else {}
    everything, hired = len(cards), sum(1 for c in cards if c.get('hired'))   # the whole collection's counts, whatever is being looked for
    cards = _sorted([c for c in cards if _found(c, find)], find.get('sort') or '')
    out = [{'key': c['key'], 'number': _number(c.get('number')), 'class': c.get('class') or '', 'name': c['name'], 'initials': _initials(c['name']),
            'image_dam_key': c.get('image_dam_key') or '', 'product': c['product'], 'module': c['module'], 'pitch': c.get('pitch') or '',
            'developer': c.get('developer') or '', 'developer_site': _site(c.get('developer_site')), 'type': c.get('type') or '', 'residency': c.get('residency') or '',
            'screen': c.get('screen') or '', 'sends_to': c.get('sends_to') or '', 'data_sent': c.get('data_sent') or '',
            'rate': _rate(c.get('price')), 'hired': bool(c.get('hired')), 'hireable': bool(c.get('hireable')), 'needs': c.get('needs') or '',
            'art': c.get('art') or '', 'wears': c.get('wears') or '', 'rating': _rating(c), 'offline': c.get('offline') is True}
           for c in cards]
    answer = {'cards': out, 'total': everything, 'hired': hired, 'shown': len(out),
              'filters': {f: sorted({c[f] for c in cards if c.get(f)}) for f in FILTERS}}
    return {**answer, 'view': view(answer, themes, simple=bool(find.get('simple')), page=page, find=find)}


def _sheet():
    path = HERE / 'card.css'
    return path.read_text(encoding='utf-8') if path.is_file() else ''


def _title():
    try:
        return json.loads((HERE / 'agent.json').read_text(encoding='utf-8')).get('name') or ''
    except (OSError, ValueError):
        return ''


def _card(c, simple=False):
    e = lambda v: html.escape(str(v), quote=True).replace('&#x27;', '&#39;')
    # THE BOX'S STRIP: a card not hired shows its rating (a star, the score, how many rated it); a hired card shows its number among the member's
    # hired cards, counted by the sheet (a CSS counter over the hired cards in order), so it is right the moment a card is hired or let go
    rating = f'<span class="mk-rating" data-part="rating">★ {c["rating"][0]} ({c["rating"][1]})</span>' if c['rating'] else ''
    number = f'<span class="mk-caption mk-number">{rating}<span class="mk-count" data-part="number"></span></span>'
    art = ('<span class="mk-back"></span>'   # the cat's own shape, solid, under the cat: the box's animation never shows through it (its picture: _art_rules)
           f'<img class="mk-art" src="{e(c["art"])}" alt="" loading="lazy">') if _css_word(c['art']) and not simple else ''   # a picture is drawn only when its address is plainly an address (the same test its mask's rule takes)
    if simple:
        art = '<span class="mk-logo"></span>'   # SIMPLE: no cat is fetched; in its place the card's own product's logo, one the page has already loaded (the sheet's)
    price = f'{c["rate"]} mTok' if c['rate'] else 'Free'
    # AN OFFLINE CARD (the owner's design, 2026-10-07; the platform says which: card.offline): the toggle stays, dimmed and locked (no data-hire: the platform's
    # hire never reaches it), the word Locked where Hire stood; Offline where the price stood; Informational only where Agent stood; the sheet dims the rest
    kind = 'Agent'
    if c['offline']:
        price, kind = 'Offline', 'Informational only'
    developer = (f'<a class="mk-site" href="{e(c["developer_site"])}" target="_blank" rel="noopener noreferrer">{e(c["developer"])}</a>'   # the developer's name opens the developer's own website
                 if c['developer_site'] else e(c['developer']))
    toggle = (f'<button type="button" class="toggle" data-hire="{e(c["key"])}" aria-pressed="{"true" if c["hired"] else "false"}" title="Hire">'
              '<span class="toggle__knob"></span></button>')
    # THE CARD CARRIES NO LINE THE OWNER DID NOT DESIGN (the owner, 2026-10-07: "these extra little notes ... i never asked for that ever"): no "lives on" and
    # no "needs" on its face. ONE NOTE STAYS, and only on an agent that sends a member's data to an outside service: where it goes and what is sent (the
    # platform's disclosure, held by its own test); an agent that sends nothing out shows nothing.
    extra = (f'<div class="mk-caption mk-sends">Sends data to {e(c["sends_to"])}' + (f': {e(c["data_sent"])}' if c['data_sent'] else '') + '</div>') if c['sends_to'] else ''
    mark = next((n for n, word in ((3, 'MARK III'), (2, 'MARK II'), (1, 'MARK I')) if c['class'].upper().startswith(word)), 0)   # the class picks the box's animation: I CRT, II Wellness, III Glitch
    rain = '<canvas class="mk-rain" aria-hidden="true"></canvas>' if mark == 3 and not simple else ''   # Mark III: the code rain's canvas (card.js), behind the cat; none in the SIMPLE view
    locked = ('<button type="button" class="toggle" aria-disabled="true" aria-pressed="' + ('true' if c['hired'] else 'false') + '" title="Locked"><span class="toggle__knob"></span></button>')
    hire = f'{locked}<span class="mk-annotation">Locked</span>' if c['offline'] else f'{toggle}<span class="mk-annotation">Hire</span>'
    return (f'<article class="agent-card{" mk-on" if c["hired"] else ""}{" mk-offline" if c["offline"] else ""}" data-agent="{e(c["key"])}" data-on="{"1" if c["hired"] else "0"}" data-mark="{mark}" data-wears="{e(c["wears"]) if c["wears"].isalnum() else ""}">'
            f'<div class="mk-head"><div class="mk-id"><span class="mk-caption" data-part="class">{e(c["class"])}</span>'
            f'<div class="mk-heading mk-name" data-part="name">{e(c["name"])}</div></div>'   # the name stands where the number stood: under the class, beside the hire toggle
            f'<div class="mk-hire">{hire}</div></div>'
            f'<div class="mk-frame">{rain}{art}<span class="mk-warm"></span>{number}</div>'
            f'<div class="mk-annotation mk-info" data-part="info">{e(c["product"])} · {e(c["module"])}</div>'
            f'<div class="mk-text mk-flavour" data-part="pitch">{e(c["pitch"])}</div>'
            f'<div class="mk-annotation mk-credit" data-part="developer">Developer · {developer}</div>'
            f'<div class="mk-foot"><span class="mk-annotation mk-kind">{kind}</span><span class="mk-callout mk-price" data-part="price">{price}</span></div>{extra}</article>')


SAFE = re.compile(r'[A-Za-z0-9_./:~%?=&+,@-]+')   # an address's own characters (our CDN's carry ?v=...); never a quote, a bracket, a space, a backslash or a <


def _css_word(v):
    """A value written inside a quoted CSS string (a key, an address): itself when every character is plainly safe, else nothing (the runtime's check
    refuses a sheet with a backslash, so nothing is escaped: a value that would need it is left out, and its rule with it)."""
    v = str(v or '')
    return v if SAFE.fullmatch(v) else ''


def _art_rules(cards):
    """Each card's own picture, as a rule of this sheet (the page allows no style attribute): the cat's shape under the cat."""
    return ''.join(f'.agent-card[data-agent="{_css_word(c["key"])}"] .mk-back {{ --mk-art: url("{_css_word(c["art"])}") }}\n'
                   for c in cards if _css_word(c['art']) and _css_word(c['key']))


NAME, UNSAFE = re.compile(r'--[a-z0-9-]+'), re.compile(r'[{};<>@\\]|url\(|expression\(|/\*', re.I)


def _theme_rules(themes, simple=False):
    """THE CARD'S OWN THEME (the owner, 2026-10-07: the box wears its card's theme, never the page's; a hired card wears it whole). The platform
    hands each theme a card may wear ({key: {'ground': its background picture, 'values': {its colour variables of the page's mode}}}); a card says
    which one it wears (data-wears). One rule per theme: its values on that card's box always, and on the whole card once hired; its picture in the
    box. A name or value that is not plainly a custom property's is left out."""
    out = []
    for key, theme in sorted((themes if isinstance(themes, dict) else {}).items()):   # a shape that is not the door's is no theme at all, never a crash
        if not str(key).isalnum() or not isinstance(theme, dict) or not isinstance(theme.get('values') or {}, dict):
            continue
        values = ' '.join(f'{n}: {v};' for n, v in (theme.get('values') or {}).items() if NAME.fullmatch(str(n)) and not UNSAFE.search(str(v)))
        wears = f'.agent-card[data-wears="{key}"]'
        if values:
            out.append(f'{wears} .mk-frame, {wears}.mk-on {{ {values} }}\n')
        if _css_word(theme.get('ground')) and not simple:   # the SIMPLE view fetches no background picture: the box stands on its theme's ground colour
            out.append(f'{wears} {{ --agent-ground: url("{_css_word(theme["ground"])}") }}\n')
    return ''.join(out)


ORDERS = (('number', 'Number'), ('name', 'Name'), ('product', 'Product'), ('mark', 'Mark'), ('rating', 'Rating'), ('price', 'Price'))
_slug = lambda v: ''.join(ch for ch in str(v or '').lower() if ch.isalnum())


def _controller(answer, find, page):
    """THE CONTROLLER, ABOVE THE CARDS, THE AGENT'S OWN (the owner, 2026-10-07: "keep it all in the agent, outside the core"), drawn with the
    platform's own controller classes and its one small button (the page's sheets stand inside the shadow root, so nothing of them is copied):
    the wide column (the total · All agents / My agents · View · Product level, and under a picked product its Module level; every group always
    shows its selected one, Off first) and the narrow one (Quick search · Sort by, as little links). EVERY LINK IS THE PAGE'S OWN, AS GIVEN
    (page.links; none is built here), the search a GET to page.links.search with the page's kept words (page.search) and q; the products and
    their modules are the page's lists (page.products, page.modules). No links given: no controller. A link not given: its button is left out."""
    links = page.get('links')
    if not isinstance(links, dict) or not isinstance(links.get('search'), str) or not links['search']:
        return ''
    e = lambda v: html.escape(str(v), quote=True).replace('&#x27;', '&#39;')
    of = lambda group, key: (links.get(group) or {}).get(key) if isinstance(links.get(group), dict) else None
    current = ' aria-current="true"'

    def small(word, on, at):
        return f'<a class="btn btn--small" href="{e(at)}"{current if on else ""}>{e(word)}</a>' if isinstance(at, str) and at else ''

    mine, simple, sort = bool(find.get('hired')), bool(find.get('simple')), find.get('sort') if find.get('sort') in dict(ORDERS) else 'number'
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
            f'<div class="wl-col--1"><div class="subtitle">Agents</div><div class="emphasis">{answer["total"]} total in network</div><div class="wl-rule wl-rule--gap"></div>'
            f'<div class="mk-ctl-row"><div><div class="label wl-label">My agents ({answer["hired"]})</div><div class="wl-btnrow">{small("All agents", not mine, links.get("mine_off"))}{small("My agents", mine, links.get("mine_on"))}</div></div>'
            f'<div><div class="label wl-label">View</div><div class="wl-btnrow">{small("Animated", not simple, links.get("view_animated"))}{small("Simple", simple, links.get("view_simple"))}</div></div></div>'
            f'{level}</div><div class="wl-divider"></div>'
            '<div class="wl-col--3"><div class="subtitle">Quick search</div><div class="emphasis">Lookup by</div><div class="wl-rule wl-rule--gap"></div>'
            f'<form method="get" action="{e(links["search"])}" class="sub-search-form">{kept}<div class="sub-search-form-container">'
            f'<input type="text" name="q" class="sub-search-input" placeholder="Find…" value="{e(search)}"><button class="btn btn--small" type="submit">Search</button>'
            + (small('Reset', False, links.get('reset')) if search else '') + '</div></form>'
            + (f'<div class="label wl-label">Sort by</div><div class="annotation">{sorts}</div>' if sorts else '') + '</div>'
            '</div></div></div></div></div></div>')


def view(answer, themes=None, simple=False, page=None, find=None):
    """THE MARKETPLACE'S OWN VIEW (the owner, 2026-10-07: the card lives in the agent, never in the platform's core): the
    whole panel's markup, every value escaped, each card's hire control a button the platform's host turns into its own
    signed hire (data-hire, aria-pressed), and this agent's own sheet (card.css, in its code hash)."""
    cards = ''.join(_card(c, simple) for c in answer['cards'])
    controller = _controller(answer, find if isinstance(find, dict) else {}, page if isinstance(page, dict) else {})
    markup = (controller + f'<section class="mk-panel{" mk-simple" if simple else ""}"><div class="mk-controller"><div class="mk-title">{html.escape(_title())}</div>'
              '<div class="mk-caption">Hire an agent with the hire toggle on its card. Once hired, it is ready to view or hide in your settings.</div></div>'
              f'<div class="mk-grid">{cards}</div></section>')
    # SIMPLE: in the cat's place stands each card's OWN PRODUCT'S LOGO, from the pictures every page has already loaded (the dock's five product logos):
    # the page hands their addresses by the theme a card wears ({theme key: address}); one rule per theme
    logos = (page or {}).get('logos') if simple and isinstance(page, dict) else None
    logo = ''.join(f'.mk-simple .agent-card[data-wears="{key}"] {{ --mk-logo: url("{_css_word(at)}") }}\n' for key, at in sorted((logos if isinstance(logos, dict) else {}).items()) if str(key).isalnum() and _css_word(at))
    # a logo that is a finished picture in its own colours (a header logo, e.g. Positive Feedback's red one) is shown as it is, never tinted: page.pictures
    pictures = (page or {}).get('pictures') if simple and isinstance(page, dict) else None
    logo += ''.join(f'.mk-simple .agent-card[data-wears="{key}"] .mk-logo {{ background: url("{_css_word(at)}") center calc(50% - 8px) / 70% auto no-repeat; -webkit-mask: none; mask: none }}\n'
                    for key, at in sorted((pictures if isinstance(pictures, dict) else {}).items()) if str(key).isalnum() and _css_word(at))
    return {'html': markup, 'css': _sheet() + ('' if simple else _art_rules(answer['cards'])) + _theme_rules(themes, simple) + logo}


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
