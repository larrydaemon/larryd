"""THE MENU AND THE MEASURES: the catalog (kit/catalog.json: type roles, the theme's colour variables, the scale's steps,
the card's effects and text parts), a small reader of a designed sheet, and the nearest-match measures look.py uses:
a colour by OKLab distance, a length by the nearest step, written type by the nearest role. Agents ship no CSS: these
turn a sheet written while designing into a look record of names (look.py)."""
import json
import re
from importlib import resources

TYPE = ('font', 'font-family', 'font-size', 'font-weight', 'font-style', 'line-height', 'letter-spacing', 'word-spacing', 'text-transform')
NAMED = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in
         json.loads(resources.files('larryd').joinpath('kit', 'css_colours.json').read_text()).items()}   # every CSS named colour
COLOUR = re.compile(r'#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\([^()]*\)|(?<![\w-])(?:' + '|'.join(sorted(NAMED, key=len, reverse=True)) + r')(?![\w-])', re.I)


def catalog():
    return json.loads(resources.files('larryd').joinpath('kit', 'catalog.json').read_text())


def _skip(text, i, close):
    """The index just past the string or comment that starts at i."""
    j = text.find(close, i + (1 if close in '"\'' else 2))
    return len(text) if j < 0 else j + len(close)


def _blocks(text):
    """The sheet's top level: [('comment', text) | ('at', prelude) | ('block', prelude, body)], strings and comments
    respected; a block that never closes ends the sheet (said)."""
    out, i, start, said = [], 0, 0, []
    while i < len(text):
        ch = text[i]
        if text.startswith('/*', i):
            end = _skip(text, i, '*/')
            if not text[start:i].strip():
                out.append(('comment', text[i:end]))
                start = end
            i = end
        elif ch in '"\'':
            i = _skip(text, i, ch)
        elif ch == ';' and text[start:i].strip().startswith('@'):
            out.append(('at', text[start:i].strip()))
            i = start = i + 1
        elif ch == '{':
            depth, j = 1, i + 1
            while j < len(text) and depth:
                if text.startswith('/*', j):
                    j = _skip(text, j, '*/')
                    continue
                if text[j] in '"\'':
                    j = _skip(text, j, text[j])
                    continue
                depth += {'{': 1, '}': -1}.get(text[j], 0)
                j += 1
            if depth:
                said.append(f'{text[start:i].strip()}: a block that never closes -> removed with the rest of the sheet')
                return out, said
            out.append(('block', text[start:i].strip(), text[i + 1:j - 1]))
            i = start = j
        elif ch == '}':
            said.append('a brace that closes nothing -> removed')
            i = start = i + 1
        else:
            i += 1
    if text[start:].strip():
        said.append(f'{text[start:].strip()[:40]}: not a rule -> removed')
    return out, said


def _split(text, sep):
    """text cut at sep outside parentheses and strings."""
    parts, depth, cur, i = [], 0, '', 0
    while i < len(text):
        ch = text[i]
        if ch in '"\'':
            end = _skip(text, i, ch)
            cur, i = cur + text[i:end], end
            continue
        depth += {'(': 1, ')': -1}.get(ch, 0)
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
        i += 1
    return parts + [cur]


def _px(value):
    m = re.fullmatch(r'\s*(-?[\d.]+)\s*(px|rem|em)?\s*', value or '')
    return float(m.group(1)) * (16 if m.group(2) in ('rem', 'em') else 1) if m else None


def _rgba(token):
    """-> (r, g, b, alpha 0..1) of a typed colour, or None."""
    t = token.lower()
    if t in NAMED:
        return NAMED[t] + (1.0,)
    if t.startswith('#'):
        h = t[1:]
        h = ''.join(c * 2 for c in h) if len(h) in (3, 4) else h
        if len(h) not in (6, 8):
            return None
        return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4)) + ((int(h[6:8], 16) / 255) if len(h) == 8 else 1.0,)
    nums = re.findall(r'[\d.]+%?', t)
    alpha = 1.0
    if len(nums) >= 4:
        a = nums[3]
        alpha = min(1.0, float(a[:-1]) / 100 if a.endswith('%') else float(a))
    if t.startswith('rgb') and len(nums) >= 3:
        return tuple(min(255, int(float(n[:-1]) * 2.55) if n.endswith('%') else int(float(n))) for n in nums[:3]) + (alpha,)
    if t.startswith('hsl') and len(nums) >= 3:
        import colorsys
        h, s, light = float(nums[0].rstrip('%')) / 360, float(nums[1].rstrip('%')) / 100, float(nums[2].rstrip('%')) / 100
        return tuple(int(round(c * 255)) for c in colorsys.hls_to_rgb(h, light, s)) + (alpha,)
    return None


def oklab(rgb):
    """sRGB 0-255 -> OKLab (L, a, b): the space where a distance is what an eye sees (Björn Ottosson, 2020)."""
    def linear(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linear(c) for c in rgb)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def nearest_colour(rgb, cat):
    """-> (the theme's colour variable nearest to rgb by OKLab distance, its hex, the distance); a tie goes to the lowest number."""
    seen = oklab(rgb)
    best = min(cat['colours'].items(), key=lambda kv: sum((x - y) ** 2 for x, y in zip(oklab(tuple(int(kv[1][i:i + 2], 16) for i in (1, 3, 5))), seen)))
    far = sum((x - y) ** 2 for x, y in zip(oklab(tuple(int(best[1][i:i + 2], 16) for i in (1, 3, 5))), seen)) ** 0.5
    return best[0], best[1], far


CASE_COST = 6   # px: what a case that differs from the written one (unwritten = none, as in CSS) adds to a role's distance
ROLE_RULE_CASED = 'nearest by size and weight, a different case costing 6px'
ROLE_RULE = 'nearest by size and weight, a different case costing 6px (an unwritten case is none, as in CSS)'   # the menu's words; a part with no case written


def nearest_role(written, cat, selector=''):
    """The type role nearest to written type ({property: value}), as the eye sees it: size and weight lead (an unwritten
    weight counts as 400; 50 of weight count as 1px), and a case other than the written one (unwritten = none, CSS's own
    default) adds CASE_COST, so a 40px black name is still a heading but small text never turns uppercase unasked. A
    role made for one purpose (navigation, a link, a field's label) is chosen only for text whose selector says it is
    that. A tie goes to the earlier role."""
    roles, only = cat['roles'], cat.get('only_for', {})
    words = set(re.findall(r'[a-z]+', selector.lower()))
    allowed = [r for r in roles if r not in only or words & set(only[r])]
    size, wt = _px(written.get('font-size')), written.get('font-weight', '400')
    wt = {'bold': 700, 'bolder': 800, 'normal': 400, 'lighter': 300}.get(wt, int(wt) if wt.isdigit() else 400)
    case = written.get('text-transform', 'none')
    return min(allowed, key=lambda r: (abs(roles[r]['size'] - size) if size is not None else 0) + abs(roles[r]['weight'] - wt) / 50
               + (CASE_COST if case != roles[r]['case'] else 0))


def table(cat=None):
    """THE MENU as Markdown, one text for the guide and every project's CLAUDE.md: every name a look record may hold."""
    cat = cat or catalog()
    shades = {}
    for name, hexa in cat['colours'].items():
        shades.setdefault(hexa.upper(), []).append(name.rsplit('-', 1)[1])
    lines = ['"accent": a theme colour variable, `active-color-01` to `active-color-64`. The number names a slot that every theme fills',
             'with its own colour, in each brand and in light and dark: the same number is the same slot everywhere, so the card follows',
             'the live theme. The colours below are the reference theme\'s only; a designed colour goes to the nearest as the eye sees it.', '',
             '| Colour (reference theme) | active-color-NN |', '|---|---|']
    lines += [f'| `{hexa}` | {", ".join(nums)} |' for hexa, nums in shades.items()]
    lines += ['', '"radius" is the card\'s corner, "space" its padding (the template sets the gaps inside from it); each is a step of the scale (a designed length goes to the nearest step; a tie rounds down):', '',
              '| Step | ' + ' | '.join(cat['steps']) + ' |', '|---|' + '---|' * len(cat['steps']),
              '| px | ' + ' | '.join(f'{v:g}' for v in cat['steps'].values()) + ' |', '',
              f'"effect": {", ".join(cat["effects"])}.', '',
              '"text": a part of the card and its type role (each part has a default; name only the ones you change). A part takes a role, never a colour: colour is card-wide, the accent only.', '',
              '| Part | Default role | What it is |', '|---|---|---|']
    lines += [f'| {p} | {r} | {cat["part_for"][p]} |' for p, r in cat['parts'].items()]
    lines += ['', 'The type roles (designed type on a part goes to the nearest role, ' + ROLE_RULE + '; the role brings its own font, style and letter spacing):', '',
              '| Role | Size | Weight | Case | For |', '|---|---|---|---|---|']
    only = cat.get('only_for', {})
    lines += [f'| {r} | {v["size"]:g}px | {v["weight"]} | {v["case"]} | {cat["for"].get(r, "")}'
              f'{" (chosen only for a selector naming " + ", ".join(only[r]) + ")" if r in only else ""} |' for r, v in cat['roles'].items()]
    import textwrap   # prose re-flowed by whole paragraph like the rest of the guide; a table row stays one line
    out, para = [], []
    for line in lines + ['']:
        if line and not line.startswith('|'):
            para.append(line)
            continue
        if para:
            out.append(textwrap.fill(' '.join(para), 118))
            para = []
        out.append(line)
    return '\n'.join(out[:-1])


def card_table(cat=None):
    """THE CARD'S ALLOWED VALUES as Markdown (the platform's own fixed lists), one text for the guide and every CLAUDE.md."""
    import textwrap
    card = (cat or catalog())['card']
    by = {}
    for screen, where in card['screens'].items():
        by.setdefault((where['product'], where['module']), []).append(screen)
    lines = ['| Field | Allowed values |', '|---|---|',
             '| class | ' + '; '.join(f'{k} (effect {v})' for k, v in card['class'].items()) + ' |',
             '| type | ' + ', '.join(card['type']) + ' |',
             '| residency | ' + ', '.join(card['residency']) + ' (where it runs) |',
             '| authorization | ' + ', '.join(card['authorization']) + ' (who may hire it: your starting setting; the platform\'s authorize '
             'panel can change it at any time after, and a PRIVATE agent\'s owning account is entered there) |',
             '| product | ' + ', '.join(card['products']) + ' |',
             '| price | a whole number of mTok per run: 3 or "3"; "0" is free |', '',
             '| Screen (<species>/<page>, at app/<species>/<page>) | Product | Module |', '|---|---|---|']
    lines += [f'| {", ".join(screens)} | {product} | {module} |' for (product, module), screens in by.items()]
    note = ('The class picks the card\'s effect: Mark I crt, Mark II wellness, Mark III glitch. `larryd doctor --fix` sets the look\'s '
            '"effect" from the class, and `larryd doctor` fails when they differ. A value off these lists fails with the ones to use.')
    return '\n'.join(lines) + '\n\n' + textwrap.fill(note, 118)
