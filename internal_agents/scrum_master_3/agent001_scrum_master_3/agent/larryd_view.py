"""THE OFFICE'S CANVAS, CARRIED INTO A LARRYD VIEW (moved 2026-11-03 into LARRYD RUNTIME INTERNAL). The office drew its canvases
for wid's page (tables, details, forms posting to its own port, the light's svg, a <style> inside the markup). LARRYD draws a view
only from its allowlist (core_engine/view.py): this rebuilds the same markup, element for element, in allowed tags, each carrying
lv-<its tag> as a class so the sheet lays it out as before (a table still a table, by display); what cannot be drawn there (a light's
svg, a press to the office's own port, an address that is not the page's or https) is said as plain words, never dropped silently."""
import html
import html.parser
import re

TAGS = frozenset('div span section article header footer p b strong i em small img button ul ol li h1 h2 h3 h4 h5 h6 br hr figure figcaption a canvas'.split())
VOID = frozenset('br hr img input meta link area base col embed param source track wbr'.split())
BLOCK = {'table': 'div', 'thead': 'div', 'tbody': 'div', 'tfoot': 'div', 'tr': 'div', 'td': 'div', 'th': 'div', 'details': 'div',
         'summary': 'div', 'pre': 'div', 'textarea': 'div', 'form': 'div', 'label': 'span', 'code': 'span', 'kbd': 'span', 'samp': 'span',
         'tt': 'span', 'select': 'span', 'option': 'span', 'time': 'span', 'abbr': 'span', 'mark': 'span', 'sup': 'span', 'sub': 'span',
         'u': 'span', 's': 'span', 'q': 'span', 'cite': 'span', 'nav': 'div', 'main': 'div', 'aside': 'div', 'dl': 'div', 'dt': 'div', 'dd': 'div',
         'caption': 'div', 'colgroup': 'span', 'col': 'span', 'fieldset': 'div', 'legend': 'div', 'output': 'span', 'meter': 'span', 'progress': 'span'}
DROP_INSIDE = frozenset(('svg', 'script', 'template', 'noscript', 'iframe', 'object', 'video', 'audio', 'math'))
KEEP = frozenset(('class', 'title', 'alt', 'role'))
SHEET = ('.lv-table { display: table; width: 100%; border-collapse: collapse; table-layout: fixed } .lv-thead { display: table-header-group } '
         '.lv-tbody { display: table-row-group } .lv-tfoot { display: table-footer-group } .lv-tr { display: table-row } '
         '.lv-td, .lv-th { display: table-cell } .lv-th { font-weight: 700 } .lv-caption { display: table-caption } .lv-pre { white-space: pre-wrap } '
         '.lv-code, .lv-kbd, .lv-samp { font-family: ui-monospace, Menlo, monospace } .lv-light { display: inline-block; width: .8em; height: .8em; border-radius: 50%; '
         'background-color: currentColor; vertical-align: middle } .lv-light[data-light="green"] { color: var(--status-ok, #2a2) } '
         '.lv-light[data-light="red"] { color: var(--status-error, #c22) } .lv-summary { font-weight: 700; margin: 6px 0 } .lv-details { margin: 8px 0 }')
SELECTOR_TAGS = re.compile(r'(?<![\w.#:\-\[="\'])(' + '|'.join(sorted(BLOCK, key=len, reverse=True)) + r')(?![\w\-])')


class _Rebuild(html.parser.HTMLParser):
    def __init__(self, path, picture):
        super().__init__(convert_charrefs=True)
        self.out, self.css, self.path, self.picture = [], [], path, picture
        self.stack, self.drop, self.in_style, self.in_head = [], 0, False, 0

    def _attrs(self, attrs, extra=''):
        got, cls = [], extra
        for name, value in attrs:
            value = '' if value is None else str(value)
            if name == 'class':
                cls = (cls + ' ' + value).strip()
            elif name in KEEP or re.fullmatch(r'(data|aria)-[a-z0-9-]+', name or ''):
                got.append(f' {name}="{html.escape(value, quote=True)}"')
        return (f' class="{html.escape(cls, quote=True)}"' if cls else '') + ''.join(got)

    def handle_starttag(self, tag, attrs, closed=False):
        tag = tag.lower()
        if self.drop:
            if tag not in VOID and not closed:
                self.drop += 1
            return
        if tag == 'style':
            self.in_style = True
            return
        if tag in ('head', 'title'):
            self.in_head += 1
            return
        if tag in DROP_INSIDE:
            if tag == 'svg':   # THE LIGHT'S DRAWING: its colour said by the light's own data-light around it
                self.out.append('<span class="lv-light" aria-hidden="true"></span>')
            if not closed:
                self.drop = 1
            return
        had = {k: (v or '') for k, v in attrs}
        if tag == 'a':
            href = had.get('href', '')
            same = href == self.path or (self.path and href.startswith(self.path + '?') and re.fullmatch(r'[A-Za-z0-9_.~%+&=-]*', href[len(self.path) + 1:] or ''))
            out = re.fullmatch(r'https://[a-z0-9.-]+\.[a-z]{2,63}(/[^\s"\'<>\\`]*)?', href or '')
            if same:
                self._open('a', f' href="{html.escape(href, quote=True)}"' + self._attrs(attrs), closed)
            elif out:
                self._open('a', f' href="{html.escape(href, quote=True)}" target="_blank" rel="noopener noreferrer"' + self._attrs(attrs), closed)
            else:
                self._open('span', self._attrs(attrs, 'lv-a'), closed, real='a')
            return
        if tag == 'img':
            src = had.get('src', '')
            if self.picture(src):
                self.out.append(f'<img src="{html.escape(src, quote=True)}"{self._attrs(attrs)}>')
            elif had.get('alt'):
                self.out.append(f'<span class="lv-img">{html.escape(had["alt"])}</span>')
            return
        if tag == 'input':
            kind = had.get('type', 'text')
            if kind == 'hidden':
                return
            if kind in ('submit', 'button'):
                self.out.append(f'<button type="button"{self._attrs(attrs, "lv-input")}>{html.escape(had.get("value", ""))}</button>')
            elif had.get('value') or had.get('placeholder'):
                self.out.append(f'<span{self._attrs(attrs, "lv-input")}>{html.escape(had.get("value") or had.get("placeholder"))}</span>')
            return
        if tag == 'button':
            self._open('button', ' type="button"' + self._attrs(attrs), closed)
            return
        if tag in TAGS:
            self._open(tag, self._attrs(attrs), closed)
            return
        self._open(BLOCK.get(tag, 'span'), self._attrs(attrs, f'lv-{tag}'), closed, real=tag)

    def _open(self, tag, attrs, closed, real=None):
        self.out.append(f'<{tag}{attrs}>')
        if tag in VOID:
            return
        if closed:
            self.out.append(f'</{tag}>')
        else:
            self.stack.append((real or tag, tag))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.drop:
            self.drop -= 1
            return
        if tag == 'style':
            self.in_style = False
            return
        if tag in ('head', 'title'):
            self.in_head = max(0, self.in_head - 1)
            return
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                while len(self.stack) > i:
                    self.out.append(f'</{self.stack.pop()[1]}>')
                return

    def handle_data(self, data):
        if self.drop or self.in_head:
            return
        if self.in_style:
            self.css.append(data)
            return
        self.out.append(html.escape(data, quote=False))

    def close(self):
        super().close()
        while self.stack:
            self.out.append(f'</{self.stack.pop()[1]}>')


def _sheet(css, picture):
    """The office's sheet, carried: element selectors renamed to the classes the markup now wears; what view.py refuses taken out."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S).replace('\\', '').replace('<', '')
    css = re.sub(r'@import[^;]*;', '', css, flags=re.I)

    def url_ok(m):
        return m.group(0) if picture(m.group(2).strip()) else 'none'
    css = re.sub(r'url\(\s*([\'"]?)(.*?)\1\s*\)', url_ok, css, flags=re.I | re.S)
    for never in ('expression(', 'image-set(', 'behavior', 'javascript:'):
        css = re.sub(re.escape(never), '', css, flags=re.I)
    out, depth, buf = [], 0, ''
    for ch in css:   # selectors only (before each {), never inside a declaration block
        if ch == '{':
            if not buf.strip().startswith('@'):   # text before a { is a selector or an @rule, never a declaration
                buf = SELECTOR_TAGS.sub(lambda m: '.lv-' + m.group(1), buf)
            out.append(buf + ch)
            buf, depth = '', depth + 1
        elif ch == '}':
            out.append(buf + ch)
            buf, depth = '', max(0, depth - 1)
        else:
            buf += ch
    out.append(buf)
    return ''.join(out)


def carried(view, path):
    """{html, css} of the office -> {html, css} LARRYD draws (view.py refused(...) == '')."""
    import sys
    sys.path.insert(0, '/Users/frost/larryd/server/runtime/app')
    try:
        from core_engine.view import picture_address as picture
    except Exception:   # noqa: BLE001  the runtime's own check unreadable: no picture passes
        def picture(_):
            return False
    finally:
        sys.path.remove('/Users/frost/larryd/server/runtime/app')
    r = _Rebuild(path, picture)
    r.feed(str((view or {}).get('html') or ''))
    r.close()
    css = _sheet(' '.join([str((view or {}).get('css') or ''), *r.css]), picture) + ' ' + SHEET
    return {'html': ''.join(r.out), 'css': css[:100 * 1024 - 1]}
