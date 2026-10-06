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


def _rules(text):
    """[(selector, [(prop, value)])] of the sheet's plain rules, nested at-rules opened; keyframes skipped."""
    items, _said = sheet._blocks(text or '')
    out = []
    for item in items:
        if item[0] != 'block':
            continue
        prelude = ' '.join(item[1].split())
        if prelude.startswith('@'):
            name = prelude[1:].split(None, 1)[0].lower()
            if name in ('media', 'supports', 'container', 'layer'):
                out += _rules(item[2])
            continue
        out.append((prelude, _decls(item[2])))
    return out


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
    """-> (the look record nearest to a designed sheet, [what was mapped, each said]). The card's own rule (.mk-card,
    .agent-card, :host) gives the accent (its border, outline or text colour first), the radius and the space; the
    sheet's words give the effect; each rule that sets type on a named part gives that part's role."""
    cat = cat or sheet.catalog()
    rules = _rules(text)
    said, look = [], {}
    card = [r for r in rules if CARD.search(r[0])] + [r for r in rules if not CARD.search(r[0])]

    order = ('border-color', 'border', 'outline', 'outline-color', 'border-top', 'border-bottom', 'color', 'box-shadow', 'background-color', 'background')
    found = None
    for selector, decls in card:
        for want in order:
            for prop, value in decls:
                if prop == want:
                    named, typed = _first_colour(value)
                    if named or typed:
                        found = (selector, prop, named, typed)
                        break
            if found:
                break
        if found:
            break
    if found:
        selector, prop, named, typed = found
        if named:
            look['accent'] = named
            said.append(f'{selector}: {prop} var(--{named}) -> accent {named}')
        else:
            rgba = sheet._rgba(typed)
            if rgba:
                slot, hexa, far = sheet.nearest_colour(rgba[:3], cat)
                look['accent'] = slot.lstrip('-')   # the NAME only: the match is made once, here, against the reference theme
                said.append(f'{selector}: {prop} {typed} -> accent {look["accent"]} (the theme\'s nearest colour, {hexa} in the reference theme, distance {far:.2f})')

    for field, props in (('radius', ('border-radius',)), ('space', ('padding', 'gap', 'margin'))):
        done = False
        for selector, decls in card:
            ranked = sorted(decls, key=lambda d: next((n for n, p in enumerate(props) if d[0] == p or d[0].startswith(p + '-')), len(props)))
            for prop, value in ranked:
                if prop in props or (field == 'radius' and prop.startswith('border-') and prop.endswith('-radius')):
                    step, tie = _step(value, cat)
                    if step:
                        look[field] = step
                        said.append(f'{selector}: {prop} {value} -> {field} {step} ({cat["steps"][step]}px, the nearest step{"; tie: rounds down" if tie else ""})')
                        done = True
                        break
            if done:
                break

    hits = {e: len(w.findall(text or '')) for e, w in EFFECT_WORDS.items()}
    best = max(hits, key=lambda e: hits[e]) if any(hits.values()) else 'none'
    if best != 'none':
        look['effect'] = best
        said.append(f'the sheet\'s animation and layers -> effect {best}')

    text_roles = {}
    for selector, decls in rules:
        written = {p: v for p, v in decls if p in sheet.TYPE and not v.startswith('var(--font-')}
        if not written:
            continue
        part = _part(selector)
        if part is None:
            said.append(f'{selector}: {"; ".join(f"{k}: {v}" for k, v in written.items())} -> dropped (no text part of the card; the parts: {", ".join(cat["parts"])})')
            continue
        role = sheet.nearest_role(written, cat)
        text_roles[part] = role
        said.append(f'{selector}: {"; ".join(f"{k}: {v}" for k, v in written.items())} -> text {part}: the {role} role (its own font, size, weight, case and letter spacing)')
    if text_roles:
        look['text'] = text_roles
    return look, said
