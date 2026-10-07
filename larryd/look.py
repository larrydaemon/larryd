"""AN AGENT'S LOOK: a small record of NAMES in agent.json, never CSS. Agents ship no sheet; the platform's one card
template puts the record on the card element as custom properties (--accent, --radius, --space, --effect) and gives
each text part its role class. Every value is a name from the menu (kit/catalog.json): a theme colour variable, a
scale step, an effect, a type role. Anything else is refused here and dropped by the platform.

    "look": {"accent": "active-color-04", "radius": "step-2", "space": "step-3", "effect": "wellness",
             "text": {"name": "title", "price": "callout"}}

A sheet written while designing (agent/card.css) is converted to the nearest record by `from_sheet` (`larryd doctor
--fix`): colours by OKLab distance, lengths to the nearest step, type to the nearest role."""
import re

from . import sheet

FIELDS = ('accent', 'radius', 'space', 'effect', 'text')
CARD = re.compile(r'\.mk-card\b|\.agent-card\b|:host\b|\.card\b')
EFFECT_WORDS = {   # what a designed sheet says, read as the nearest effect
    'crt': re.compile(r'\bcrt\b|scan|repeating-linear-gradient\(\s*0deg|roll', re.I),
    'wellness': re.compile(r'wellness|blur\(|breathe|drift|radial-gradient', re.I),
    'glitch': re.compile(r'glitch|jitter|foil|flicker|mix-blend-mode|hue-rotate', re.I),
}
PART_WORDS = (   # a selector's words, read as the card's text part they style
    ('price', ('price', 'rate', 'callout', 'cost')),
    ('name', ('name', 'title', 'heading')),
    ('pitch', ('pitch', 'flavour', 'flavor', 'body', 'about', 'desc')),
    ('number', ('number', 'num', 'no')),
    ('class', ('class', 'mark', 'eyebrow')),
    ('developer', ('developer', 'credit', 'author', 'by')),
    ('info', ('info', 'product', 'module')),
    ('facts', ('facts', 'foot', 'footer', 'type', 'residency')),
)


def menu(cat=None):
    cat = cat or sheet.catalog()
    return {'accent': [k.lstrip('-') for k in cat['colours']], 'radius': list(cat['steps']), 'space': list(cat['steps']),
            'effect': list(cat['effects']), 'parts': list(cat['parts']), 'roles': list(cat['roles'])}


def check(look, cat=None):
    """-> [(what is wrong, what to do)] for a look record; [] when every value is a name on the menu."""
    m = menu(cat)
    if not isinstance(look, dict):
        return [('"look" is not an object', 'set "look" to {"accent": ..., "radius": ..., "space": ..., "effect": ..., "text": {...}} or remove it')]
    wrong = []
    for k, v in look.items():
        if k not in FIELDS:
            wrong.append((f'look "{k}" is not a look field', f'remove it; the fields are: {", ".join(FIELDS)}'))
        elif k == 'text':
            if not isinstance(v, dict):
                wrong.append(('look "text" is not an object', 'set it to {"<part>": "<role>"}, e.g. {"name": "title"}'))
                continue
            for part, role in v.items():
                if part not in m['parts']:
                    wrong.append((f'look text part "{part}" is not a part of the card', f'use one of: {", ".join(m["parts"])}'))
                elif role not in m['roles']:
                    wrong.append((f'look text "{part}": "{role}" is not a type role', f'use one of: {", ".join(m["roles"])}'))
        elif v not in m[k]:
            shown = ', '.join(m[k]) if k != 'accent' else 'active-color-01 to active-color-64 (the table in CLAUDE.md)'
            wrong.append((f'look "{k}": {json_text(v)} is not a name on the menu', f'use one of: {shown} (a name, never a raw colour or length)'))
    return wrong


def json_text(v):
    return f'"{v}"' if isinstance(v, str) else repr(v)


def clean(look, cat=None):
    """The record with every value not on the menu dropped (what the platform does at render)."""
    m = menu(cat)
    if not isinstance(look, dict):
        return {}
    out = {k: look[k] for k in ('accent', 'radius', 'space', 'effect') if isinstance(look.get(k), str) and look[k] in m[k]}
    text = look.get('text')
    if isinstance(text, dict):
        kept = {p: r for p, r in text.items() if p in m['parts'] and r in m['roles']}
        if kept:
            out['text'] = kept
    return out


def properties(look, cat=None):
    """-> {custom property: value} for the card element, from the cleaned record only."""
    look = clean(look, cat)
    out = {}
    if 'accent' in look:
        out['--accent'] = f'var(--{look["accent"]})'   # the live variable: the card follows the theme, brand and mode
    for k in ('radius', 'space'):
        if k in look:
            out[f'--{k}'] = f'var(--{look[k]})'
    if 'effect' in look:
        out['--effect'] = look['effect']
    return out


def _decls(body):
    out = []
    for part in sheet._split(re.sub(r'/\*.*?\*/', ' ', body, flags=re.S), ';'):
        if ':' in part:
            prop, value = (x.strip() for x in part.split(':', 1))
            out.append((prop.lower(), value))
    return out


def _rules(text, within=''):
    """-> ([(selector, [(prop, value)], within)], [(at-rule, why)]): the sheet's plain rules, nested @media and the like
    opened (within names it), and every other at-rule, which never becomes a name."""
    items, _said = sheet._blocks(text or '')
    rules, ats = [], []
    for item in items:
        if item[0] == 'at':
            ats.append((item[1], AT_WHY.get(item[1][1:].split(None, 1)[0].lower(), 'not part of a card\'s look')))
            continue
        if item[0] != 'block':
            continue
        prelude = ' '.join(item[1].split())
        if prelude.startswith('@'):
            name = prelude[1:].split(None, 1)[0].lower()
            if name in ('media', 'supports', 'container', 'layer'):
                more, more_ats = _rules(item[2], prelude)
                rules += more
                ats += more_ats
            else:
                ats.append((prelude, AT_WHY.get(name, 'not part of a card\'s look')))
            continue
        rules.append((prelude, _decls(item[2]), within))
    return rules, ats


AT_WHY = {'import': 'the template loads every file itself', 'font-face': 'the type roles bring their own faces',
          'keyframes': 'the effect brings its own animation', '-webkit-keyframes': 'the effect brings its own animation',
          'charset': 'not part of a card\'s look', 'namespace': 'not part of a card\'s look', 'page': 'not part of a card\'s look'}
STATES = re.compile(r':(hover|focus|focus-visible|focus-within|active|visited|checked|disabled)\b', re.I)
REASONS = (   # (properties, why they never become a name); the first that matches says it
    (re.compile(r'^(position|top|right|bottom|left|inset.*|z-index|float|clear)$'), 'the template places every part'),
    (re.compile(r'^(gap|row-gap|column-gap|margin.*)$'), '"space" is the card\'s padding; the template sets the gaps and margins from it'),
    (re.compile(r'^(display|flex.*|grid.*|order|align.*|justify.*|place.*|aspect-ratio|width|height|min-.*|max-.*|overflow.*|box-sizing|columns?.*)$'),
     'the template lays out the card'),
    (re.compile(r'^(transition.*|animation.*|transform.*|translate|rotate|scale|filter|backdrop-filter|box-shadow|text-shadow|opacity|mix-blend-mode|will-change)$'),
     'the effect brings its own motion, light and shadow'),
    (re.compile(r'^(cursor|pointer-events|user-select|content|outline.*)$'), 'the template draws every state'),
)


def _why(prop, selector, part, card):
    if STATES.search(selector):
        return 'the template draws hover, focus and every other state'
    for props, why in REASONS:
        if props.match(prop):
            return why
    if prop in sheet.TYPE:
        return f'no text part of the card here (the parts: {", ".join(sheet.catalog()["parts"])})' if part is None else 'the role brings its own type'
    if card and re.search(r'colou?r|background|border|fill|stroke', prop):
        return 'one accent per card: the first colour on the card became it; the template draws the border and the ground'
    if re.search(r'colou?r|background|border|fill|stroke', prop):
        if part is None:
            return 'colour is card-wide, the accent only; the effect draws its own layers'
        return 'colour is card-wide, the accent only: a text part takes a role, never a colour'
    return 'not a name on the menu'


def _first_colour(value):
    m = re.search(r'var\(--(active-color-\d\d)\)', value)
    if m:
        return m.group(1), None
    m = sheet.COLOUR.search(value)
    return (None, m.group(0)) if m else (None, None)


def _step(value, cat):
    px = sheet._px((re.search(r'-?\d*\.?\d+(?:px|rem|em)?', value) or [None])[0] or '')
    if px is None:
        return None, None
    best = min(cat['steps'], key=lambda s: (abs(cat['steps'][s] - abs(px)), cat['steps'][s]))   # a tie rounds down
    tie = sum(1 for v in cat['steps'].values() if abs(v - abs(px)) == abs(cat['steps'][best] - abs(px))) > 1
    return best, tie


def _part(selector):
    words = set(re.findall(r'[a-z]+', selector.lower()))
    for part, names in PART_WORDS:
        if words & set(names):
            return part
    return None


def from_sheet(text, cat=None):
    """-> (the look record nearest to a designed sheet, [what was mapped], [what was dropped]): every declaration of the
    sheet is said once, as a name it became or as dropped with why. The card's own rule (.mk-card, .agent-card, :host,
    no state) gives the accent (its border, outline or text colour first), the radius and the space (its padding); the
    sheet's animation words give the effect; type on a named part gives that part's role."""
    cat = cat or sheet.catalog()
    rules, ats = _rules(text)
    said, look, used = [], {}, set()
    card = [n for n, r in enumerate(rules) if CARD.search(r[0]) and not STATES.search(r[0])]

    order = ('border-color', 'border', 'outline', 'outline-color', 'border-top', 'border-bottom', 'color', 'box-shadow', 'background-color', 'background')
    found = None
    for n in card:
        for want in order:
            for k, (prop, value) in enumerate(rules[n][1]):
                if prop == want:
                    named, typed = _first_colour(value)
                    if named or typed:
                        found = (n, k, prop, named, typed)
                        break
            if found:
                break
        if found:
            break
    if found:
        n, k, prop, named, typed = found
        selector = rules[n][0]
        if named:
            look['accent'] = named
            used.add((n, k))
            said.append(f'{selector}: {prop} var(--{named}) -> accent {named}')
        else:
            rgba = sheet._rgba(typed)
            if rgba:
                slot, hexa, far = sheet.nearest_colour(rgba[:3], cat)
                look['accent'] = slot.lstrip('-')   # the NAME only: the match is made once, here, against the reference theme
                used.add((n, k))
                said.append(f'{selector}: {prop} {typed} -> accent {look["accent"]} (the theme\'s nearest colour, {hexa} in the reference theme, distance {far:.2f})')

    for field, test in (('radius', lambda p: p == 'border-radius' or (p.startswith('border-') and p.endswith('-radius'))),
                        ('space', lambda p: p == 'padding' or p.startswith('padding-'))):
        done = False
        for n in card:
            for k, (prop, value) in enumerate(rules[n][1]):
                if test(prop):
                    step, tie = _step(value, cat)
                    if step:
                        look[field] = step
                        used.add((n, k))
                        said.append(f'{rules[n][0]}: {prop} {value} -> {field} {step} ({cat["steps"][step]}px, the nearest step{"; tie: rounds down" if tie else ""})')
                        done = True
                        break
            if done:
                break

    hits = {e: len(w.findall(text or '')) for e, w in EFFECT_WORDS.items()}
    best = max(hits, key=lambda e: hits[e]) if any(hits.values()) else 'none'
    if best != 'none':
        look['effect'] = best
        said.append(f'the sheet\'s animation and layers -> effect {best} (read from its words: {", ".join(sorted(set(m.group(0).lower() for m in EFFECT_WORDS[best].finditer(text))))})')

    text_roles, merged = {}, {}   # per part: its type as the browser cascades it (source order, the later wins per property)
    for n, (selector, decls, _within) in enumerate(rules):
        part = _part(selector)
        if STATES.search(selector) or part is None:
            continue
        written = [(k, p, v) for k, (p, v) in enumerate(decls) if p in sheet.TYPE and not v.startswith('var(--font-')]
        if not written:
            continue
        mine = merged.setdefault(part, {'selectors': [], 'type': {}})
        if selector not in mine['selectors']:
            mine['selectors'].append(selector)
        mine['rules'] = mine.get('rules', 0) + 1
        for k, p, v in written:
            mine['type'].pop(p, None)   # re-inserted: the declaration order shows what the browser keeps
            mine['type'][p] = v
            used.add((n, k))
    for part, mine in merged.items():
        selectors = ', '.join(mine['selectors'])
        role = sheet.nearest_role(mine['type'], cat, selectors)
        text_roles[part] = role
        cascade = f' ({mine["rules"]} rules merged as the browser cascades them, the later wins)' if mine['rules'] > 1 else ''
        said.append(f'{selectors}{cascade}: {"; ".join(f"{k}: {v}" for k, v in mine["type"].items())} -> text {part}: the {role} role '
                    f'({sheet.ROLE_RULE_CASED if "text-transform" in mine["type"] else sheet.ROLE_RULE}; the role brings its own font, size, weight, style, case and letter spacing)')
    if text_roles:
        look['text'] = text_roles

    dropped = [f'{at} -> no name on the menu ({why})' for at, why in ats]
    for n, (selector, decls, within) in enumerate(rules):
        groups = {}
        for k, (prop, value) in enumerate(decls):
            if (n, k) not in used:
                groups.setdefault(_why(prop, selector, _part(selector), n in card), []).append(prop)
        where = f'{within} {selector}' if within else selector
        for why, props in groups.items():
            dropped.append(f'{where}: {", ".join(props)} -> no name on the menu ({why})')
    return look, said, dropped
