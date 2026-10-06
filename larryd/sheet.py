"""THE CARD SHEET'S RULES, IN ONE PLACE (the owner, 2026-10-06: "all agents' CSS definitions are IN THE AGENT"; "the doctor
rewrites the CSS for the agent, so it can control what is there and what is allowed or not allowed"; "it's impossible
for the submission to get refused on CSS, because we are writing the CSS").

An agent's card sheet is its own: its layout and its looks stay as the developer wrote them. `rewrite()` writes it in
the platform's form, the same way every time (`larryd doctor --fix` and `larryd submit` both run it; what FROST reviews
is its output). On the platform the sheet is drawn inside each card's own shadow root, under the page's
Content-Security-Policy: that isolation is the second guard, this is the first.

REWRITTEN (the platform's own menu, so agents look native):
  TYPE      font, font-family, font-size, font-weight, font-style, line-height, letter-spacing, word-spacing,
            text-transform: the nearest role of THE GLOBAL FONT CATALOG (that role's own variables)
  COLOUR    a typed colour (#hex, rgb(), hsl(), a colour's name): the theme's perceptually nearest colour variable
            (OKLab distance), var(--active-color-NN); a see-through colour keeps its alpha (color-mix with transparent)
  SPACING   gap, padding, margin, border-radius (and their sides): each length to the nearest step of the scale
REMOVED (each said):
  REACH     @import; url() to another host (a scheme or //, data: included)
  FACES     @font-face (the catalog's faces only), @charset, @namespace, @page, @document
  SCRIPT    expression(), javascript:, behavior, -moz-binding
  PIN       position: fixed or sticky
  PAGE      a selector naming the page outside the card (html, body, :root, :host-context())
  MARKUP    a '<' or a backslash anywhere (the platform would refuse the whole sheet); a comment that names a reach
  SIZE      past CAP characters, the rules at the end
"""
import json
import re
from importlib import resources

CAP = 20000
SPACING = (0, 2, 4, 8, 12, 16, 22, 32, 48, 64)   # px: the platform's spacing scale
TYPE = ('font', 'font-family', 'font-size', 'font-weight', 'font-style', 'line-height', 'letter-spacing', 'word-spacing', 'text-transform')
SPACED = re.compile(r'^(gap|row-gap|column-gap|padding(-(top|right|bottom|left|inline|block)(-(start|end))?)?|margin(-(top|right|bottom|left|inline|block)(-(start|end))?)?|border(-(top|bottom)-(left|right))?-radius)$')
NAMED = {'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0), 'green': (0, 128, 0), 'blue': (0, 0, 255), 'yellow': (255, 255, 0),
         'orange': (255, 165, 0), 'purple': (128, 0, 128), 'pink': (255, 192, 203), 'gray': (128, 128, 128), 'grey': (128, 128, 128),
         'silver': (192, 192, 192), 'navy': (0, 0, 128), 'teal': (0, 128, 128), 'lime': (0, 255, 0), 'cyan': (0, 255, 255),
         'magenta': (255, 0, 255), 'aqua': (0, 255, 255), 'fuchsia': (255, 0, 255), 'maroon': (128, 0, 0), 'olive': (128, 128, 0)}
COLOUR = re.compile(r'#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\([^()]*\)|(?<![\w-])(?:' + '|'.join(NAMED) + r')(?![\w-])', re.I)
OUTSIDE = re.compile(r'''url\(\s*["']?\s*(?:[a-z][a-z0-9+.-]*:|//)''', re.I)
SCRIPT = re.compile(r'expression\s*\(|javascript:|-moz-binding|behaviou?r', re.I)
PAGE = re.compile(r'(^|[\s>+~(,])(html|body|:root)(?![\w-])|:host-context\(', re.I)
DROPPED_AT = ('import', 'font-face', 'charset', 'namespace', 'page', 'document', '-moz-document')
NESTED_AT = ('media', 'supports', 'container', 'layer')
FRAMES_AT = ('keyframes', '-webkit-keyframes')
ELEMENTS = {'h1': 'heading', 'h2': 'title', 'h3': 'subtitle', 'h4': 'subtitle', 'p': 'body', 'small': 'annotation', 'label': 'label',
            'a': 'link', 'nav': 'nav', 'blockquote': 'callout', 'aside': 'callout', 'code': 'notes', 'pre': 'notes'}   # what a developer writes by habit


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


def _rgb(token, cat=None):
    rgba = _rgba(token)
    return rgba[:3] if rgba else None


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


def _colours(value, cat, said, where):
    def nearest(m):
        rgba = _rgba(m.group(0))
        if rgba is None:
            return m.group(0)
        slot, hexa, far = nearest_colour(rgba[:3], cat)
        alpha = round(rgba[3] * 100)
        new = f'var({slot})' if alpha >= 100 else f'color-mix(in srgb, var({slot}) {alpha}%, transparent)'
        said.append(f'{where}: {m.group(0)} -> {new} (the theme\'s nearest colour, {hexa} in the reference theme, distance {far:.2f})')
        return new
    return COLOUR.sub(nearest, value)


def _spacing(prop, value, said, where):
    def step(m):
        px = _px(m.group(0))
        if px is None:
            return m.group(0)
        to = min(SPACING, key=lambda s: (abs(s - abs(px)), s))
        new = f'{"-" if px < 0 and to else ""}{to}px'
        if new != m.group(0):
            said.append(f'{where}: {prop} {m.group(0)} -> {new} (the spacing scale)')
        return new
    return re.sub(r'-?\d*\.?\d+(?:px|rem|em)\b', step, value)


def _type(written, cat, said, where):
    roles = cat['roles']
    size, wt, case = _px(written.get('font-size')), written.get('font-weight', '400'), written.get('text-transform', 'none')   # unwritten: CSS's own defaults
    wt = {'bold': 700, 'bolder': 800, 'normal': 400, 'lighter': 300}.get(wt, int(wt) if wt.isdigit() else 400)
    role = min(roles, key=lambda r: (abs(roles[r]['size'] - size) if size is not None else 0) + abs(roles[r]['weight'] - wt) / 50
               + (6 if case != roles[r]['case'] else 0))
    said.append(f'{where}: {"; ".join(f"{k}: {v}" for k, v in written.items())} -> the {role} role (its own font, size, weight, case and letter spacing)')
    return [f'font-family: var(--font-{role})', f'font-size: var(--font-{role}-sz)', f'font-weight: var(--font-{role}-wt)', f'text-transform: var(--font-{role}-tt)']


def _declarations(body, cat, said, where):
    out, written = [], {}
    for part in _split(re.sub(r'/\*.*?\*/', ' ', body, flags=re.S), ';'):
        if ':' not in part:
            if part.strip():
                said.append(f'{where}: {part.strip()[:40]} -> removed (not a declaration)')
            continue
        prop, value = (x.strip() for x in part.split(':', 1))
        prop = prop.lower()
        decl = f'{prop}: {value}'
        if '<' in decl or '\\' in decl:
            said.append(f'{where}: {decl[:60]} -> removed (markup or an escape)')
        elif OUTSIDE.search(value):
            said.append(f'{where}: {decl[:60]} -> removed (it reaches another host)')
        elif SCRIPT.search(decl):
            said.append(f'{where}: {decl[:60]} -> removed (a script in CSS)')
        elif prop == 'position' and value.lower().split('!')[0].strip() in ('fixed', 'sticky'):
            said.append(f'{where}: {decl} -> removed (pinned to the screen, outside the card)')
        elif prop in TYPE:
            if not value.startswith('var(--font-'):
                written[prop] = value
            else:
                out.append(decl)
        else:
            value = _colours(value, cat, said, where)
            if SPACED.match(prop):
                value = _spacing(prop, value, said, where)
            out.append(f'{prop}: {value}')
    if written:
        out += [d for d in _type(written, cat, said, where) if d not in out]
    return '; '.join(out)


def _selectors(prelude, said):
    keep = []
    for part in _split(prelude, ','):
        sel = ' '.join(part.split())
        if not sel:
            continue
        if '<' in sel or '\\' in sel or ';' in sel:
            said.append(f'{sel[:40]}: removed (markup, an escape or not a selector)')
        elif PAGE.search(sel):
            said.append(f'{sel}: removed (it names the page outside the card)')
        else:
            habit = re.sub(r'(?<![\w.#:-])(h1|h2|h3|h4|p|small|label|a|nav|blockquote|aside|code|pre)(?![\w-])', lambda m: '.' + ELEMENTS[m.group(1)], sel)
            if habit != sel:
                said.append(f'{sel} -> {habit} (the catalog\'s roles)')
            keep.append(habit)
    return ', '.join(keep)


def _items(items, cat, said, frames=False):
    out = []
    for item in items:
        if item[0] == 'comment':
            if '<' in item[1] or '\\' in item[1] or '@import' in item[1].lower() or OUTSIDE.search(item[1]):
                said.append('a comment naming markup, an escape or a reach -> removed (the platform reads the whole sheet)')
            else:
                out.append(item[1])
            continue
        prelude = item[1]
        name = prelude[1:].split(None, 1)[0].lower() if prelude.startswith('@') else ''
        if item[0] == 'at' or name in DROPPED_AT:
            said.append(f'{prelude.split("{")[0].strip()[:60]} -> removed')
            continue
        if name in NESTED_AT or name in FRAMES_AT:
            if '<' in prelude or '\\' in prelude or OUTSIDE.search(prelude):
                said.append(f'{prelude[:40]} -> removed (markup, an escape or a reach)')
                continue
            inner, more = _blocks(item[2])
            said += more
            body = _items(inner, cat, said, frames=name in FRAMES_AT)
            if body:
                out.append(f'{" ".join(prelude.split())} {{ ' + ' '.join(body) + ' }')
            continue
        if name:
            said.append(f'{prelude[:60]} -> removed (not an at-rule a card uses)')
            continue
        selectors = ' '.join(prelude.split()) if frames else _selectors(prelude, said)
        decls = _declarations(item[2], cat, said, selectors or prelude)
        if selectors and decls:
            out.append(f'{selectors} {{ {decls} }}')
    return out


def rewrite(text, cat=None):
    """-> (the sheet in the platform's form, [what was rewritten or removed]). The same text always gives the same result;
    its own result is already in form (rewrite(rewrite(x)) == rewrite(x))."""
    cat = cat or catalog()
    items, said = _blocks(text or '')
    out = _items(items, cat, said)
    while out and len('\n'.join(out)) + 1 > CAP:
        said.append(f'{out.pop()[:40]}: removed (the sheet is over {CAP} characters)')
    return ('\n'.join(out) + '\n') if out else '', said


def table(cat=None):
    """THE MENU as Markdown, one text for the guide and every project's CLAUDE.md: the type roles, the theme's colour
    variables and the spacing scale, the values a sheet is converted to."""
    cat = cat or catalog()
    roles = ['| Role | Class | Size | Weight | Case | For |', '|---|---|---|---|---|---|'] + [
        f'| {r.capitalize()} | `.{v["class"]}` | {v["size"]:g}px | {v["weight"]} | {v["case"]} | {cat["for"].get(r, "")} |' for r, v in cat['roles'].items()]
    shades = {}
    for name, hexa in cat['colours'].items():
        shades.setdefault(hexa.upper(), []).append(name.rsplit('-', 1)[1])
    colours = ['| Colour (reference theme) | Variables `--active-color-NN` |', '|---|---|'] + [
        f'| `{hexa}` | {", ".join(nums)} |' for hexa, nums in shades.items()]
    return '\n'.join(['Type roles (a written font, size, weight, case or letter spacing becomes the nearest role by size, weight and case):', '']
                     + roles + ['', 'Colours (a typed colour becomes the variable nearest to it as the eye sees it; each brand\'s theme sets its own values):', '']
                     + colours + ['', f'Spacing scale (gap, padding, margin, border-radius go to the nearest step): {", ".join(str(x) for x in SPACING)} px.'])
