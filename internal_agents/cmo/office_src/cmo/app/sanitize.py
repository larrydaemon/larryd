"""THE OFFICE'S CANVAS, MADE TO PASS LARRYD'S VIEW GATE (core_engine/view.py): the same words and blocks, in the elements the gate takes.
A table is drawn as divs wearing the table's own display; a fold (details) stands open; a picture, a video or a sound on this computer
is named by its file (the gate takes pictures from the CDN alone); a script, a style element and a drawing (svg) go (their sheets were
lifted into the css first). THE PRESSES: the office's POST form to its /agent_press becomes a GET to the page itself (the only form the
gate takes), every field renamed p_<name>, its token once; a box to tick or a choice becomes one text word (the values, comma
separated), a box of many lines one line ( || between the lines). bridge.py presses it before it draws (press_of)."""
import html
import html.parser
import re
import secrets

TAGS = set('div span section article header footer p b strong i em small img button ul ol li h1 h2 h3 h4 h5 h6 br hr figure figcaption a form input'.split())
AS = {'table': ('div', 'x-table'), 'thead': ('div', 'x-thead'), 'tbody': ('div', 'x-tbody'), 'tfoot': ('div', 'x-tbody'), 'tr': ('div', 'x-tr'),
      'td': ('div', 'x-td'), 'th': ('div', 'x-th'), 'details': ('div', 'x-details'), 'summary': ('div', 'x-summary'), 'label': ('span', 'x-label'),
      'code': ('span', 'x-code'), 'pre': ('div', 'x-pre'), 's': ('span', 'x-s'), 'u': ('span', 'x-u'), 'nav': ('div', 'x-nav'), 'main': ('div', 'x-main'),
      'aside': ('div', 'x-aside'), 'dl': ('div', 'x-dl'), 'dt': ('div', 'x-dt'), 'dd': ('div', 'x-dd'), 'sup': ('small', 'x-sup'), 'sub': ('small', 'x-sub'),
      'mark': ('span', 'x-mark'), 'kbd': ('span', 'x-code'), 'time': ('span', 'x-time'), 'caption': ('div', 'x-caption'), 'blockquote': ('div', 'x-quote')}
DROP = {'script', 'style', 'svg', 'iframe', 'object', 'embed', 'noscript', 'template', 'math', 'canvas', 'datalist'}   # gone with everything inside
VOID = {'br', 'hr', 'img', 'input', 'source', 'track', 'wbr', 'col', 'meta', 'link', 'area', 'base', 'param'}
KEEP = {'class', 'title', 'alt', 'role'}
NAME = re.compile(r'[a-z_]{1,32}')
DIGITS = 'abcdefghij'
# THE EMBEDDED WIDGETS (the owner 2026-11-04: "make sure all the agents inject the embedded buttons too"): every press, toggle, tag, pill and
# export in a view wears the platform's one set (themes/embedded, embedded.css), written in classes alone since the host takes no data- or aria-
# attribute. This rewrite keeps every class (no class list to pass), so the pfb classes go through as written; an older class still drawn (the office's own .btn, the shell's .toggle) becomes its widget here.
LEGACY = {'btn': 'pfb', 'btn--small': 'pfb--small', 'btn--big': 'pfb--small', 'toggle': 'pfb pfb--toggle', 'toggle__knob': 'pfb__knob'}


def widget(cls, attrs):
    """a class list as the embedded widgets read it: an older button or toggle class turned into its pfb class, a toggle pressed (aria-pressed true,
    which the host drops) marked pfb--on"""
    out = []
    for c in ' '.join(LEGACY.get(c, c) for c in cls.split()).split():
        if c not in out:
            out.append(c)
    if 'pfb--toggle' in out and attrs.get('aria-pressed') == 'true' and 'pfb--on' not in out:
        out.append('pfb--on')
    return ' '.join(out)


def esc(text):
    return html.escape(str(text if text is not None else ''), quote=True)


def enc(name):
    """a field's name as the gate takes it ([a-z_], at most 32): p_ then its letters, a digit as x and a letter"""
    out = ''.join(c if ('a' <= c <= 'z' or c == '_') else ('x' + DIGITS[int(c)] if c.isdigit() else '_') for c in str(name).lower())
    return ('p_' + out)[:32]


class _Rewrite(html.parser.HTMLParser):
    def __init__(self, path, groups):
        super().__init__(convert_charrefs=True)
        self.path, self.groups, self.out, self.stack, self.drop = path, groups, [], [], 0
        self.form = None   # the press being rebuilt: {names: {enc: orig}, lists, multi, fid}
        self.select = None
        self.textarea = None
        self.forms = 0
        self.js_only, self.pressable = set(), set()   # the presses drawn: the ones a GET can send, the ones only a page script sends

    # --- the press: its fields
    def _field(self, name, value, kind='hidden', placeholder=''):
        e = enc(name)
        if self.form is not None:
            self.form['names'][e] = name
        ph = f' placeholder="{esc(placeholder)}"' if placeholder else ''
        if self.form is not None:
            self.form['pieces'].append(len(self.out))
            if name == 'do':
                self.form['do'] = value
        return f'<input type="{kind}" name="{e}" value="{esc(value)}"{ph}>'

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if self.drop:
            if tag in DROP:
                self.drop += 1
            return
        if tag in DROP:
            self.drop = 1
            return
        if self.textarea is not None or self.select is not None:
            if tag == 'option' and self.select is not None:
                self.select['opts'].append([a.get('value', ''), 'selected' in a, ''])
                self.select['in'] = True
            return
        cls = widget(a.get('class', ''), a)
        if tag == 'form':
            method = a.get('method', 'get').lower()
            fid = a.get('id', '')
            self.form = {'names': {}, 'lists': [], 'multi': [], 'fid': fid, 'post': method == 'post', 'at': len(self.out), 'submit': False, 'pieces': []}
            self.forms += 1
            self.out.append(f'<form method="get" action="{esc(self.path)}"' + (f' class="{esc(cls)}"' if cls else '') + '>')
            self.out.append(f'<input type="hidden" name="p_token" value="{secrets.token_hex(8)}">')
            if a.get('action', '') not in ('', '/agent_press'):
                self.out.append(f'<input type="hidden" name="p_route" value="{esc(a.get("action", ""))}">')   # another of the office's own doors (a shell action, the day toggle)
            self.stack.append('form')
            return
        if tag == 'input':
            kind = a.get('type', 'text').lower()
            if kind in ('checkbox', 'radio'):   # A BOX TO TICK: named by its value, ticked or not; its word is one text field at the form's end
                self.out.append(f'<span class="x-box">{"[x]" if "checked" in a else "[ ]"} <small class="x-box-value">{esc(a.get("value", ""))}</small></span> ')
                return
            if kind in ('submit', 'button', 'image', 'reset', 'file'):
                if kind == 'file':
                    self.out.append('<span class="annotation">(a file to send cannot be chosen here)</span>')
                elif self.forms:
                    if self.form is not None:
                        self.form['submit'] = True
                    self.out.append(f'<button type="submit" class="{esc(cls or "pfb pfb--small")}">{esc(a.get("value", "Go"))}</button>')
                return
            if not self.forms:   # an input outside any form: its value as words
                if a.get('value'):
                    self.out.append(f'<span class="x-input">{esc(a.get("value"))}</span>')
                return
            name = a.get('name', '')
            if not name:
                return
            if kind == 'hidden':
                if name in ('agent', 'back', 'csrf') or (name == 'value' and not a.get('value')):
                    return   # the bridge carries the agent and the face; an empty value is no value
                self.out.append(self._field(name, a.get('value', '')))
            else:   # text, number, range, color, search, date...: one text word, its value as it is
                self.out.append(self._field(name, a.get('value', ''), 'text', a.get('placeholder', '') or (f"{a.get('min', '')} to {a.get('max', '')}" if kind == 'range' else '')))
            return
        if tag == 'textarea':
            self.textarea = {'name': a.get('name', ''), 'text': [], 'ph': a.get('placeholder', '')}
            return
        if tag == 'select':
            self.select = {'name': a.get('name', ''), 'opts': [], 'in': False}
            return
        if tag in ('img', 'video', 'audio', 'source', 'picture'):
            src = a.get('src', '') or a.get('poster', '')
            if src and tag != 'source':
                self.out.append(f'<span class="x-media">[{ {"img": "picture", "video": "video", "audio": "sound", "picture": "picture"}[tag]}: {esc(src)}]</span>')
            elif tag == 'source' and src:
                self.out.append(f'<span class="x-media">[file: {esc(src)}]</span>')
            if tag in ('video', 'audio', 'picture'):
                self.stack.append('')   # its children (sources) named, its own element gone
            return
        if tag == 'a':
            href = a.get('href', '')
            if href.startswith('https://') and not re.search(r'[\s"\'<>\\`]', href):
                self.out.append(f'<a href="{esc(href)}" target="_blank" rel="noopener noreferrer"' + (f' class="{esc(cls)}"' if cls else '') + '>')
                self.stack.append('a')
            else:
                self.out.append('<span class="x-link' + (f' {esc(cls)}' if cls else '') + '">')
                self.stack.append('span')
            return
        if tag == 'button':
            kind = 'submit' if (self.forms and a.get('type', 'submit') == 'submit') else 'button'
            if kind == 'submit' and self.form is not None:
                self.form['submit'] = True
            self.out.append(f'<button type="{kind}"' + (f' class="{esc(cls)}"' if cls else '') + (f' title="{esc(a["title"])}"' if a.get('title') else '') + '>')   # its title kept: a toggle's On or Off (the host takes title)
            self.stack.append('button')
            return
        if tag in AS:
            el, extra = AS[tag]
            cls = (extra + ' ' + cls).strip()
        elif tag in TAGS:
            el = tag
        else:
            el = 'span' if tag in ('font', 'abbr', 'cite', 'q', 'var', 'samp', 'bdi', 'bdo', 'data', 'output', 'meter', 'progress', 'ins', 'del') else 'div'
            cls = (f'x-{tag} ' + cls).strip() if re.fullmatch(r'[a-z0-9]+', tag) else cls
        if a.get('id') and re.fullmatch(r'[A-Za-z0-9_-]{1,60}', a['id']):
            cls = (cls + ' x-id-' + a['id']).strip()   # an id the office's sheet names (#scrum): a class of the same name
        keep = ''.join(f' {k}="{esc(v)}"' for k, v in a.items() if (k in KEEP or (re.fullmatch(r'(data|aria)-[a-z0-9-]+', k) and len(v) <= 120)) and k != 'class')   # a page script's own state (a long data- value: strokes, frames) goes with the script
        self.out.append(f'<{el}' + (f' class="{esc(cls)}"' if cls else '') + keep + ('>' if el not in VOID else '>'))
        if el not in VOID and tag not in VOID:
            self.stack.append(el)

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if self.drop:
            if tag in DROP:
                self.drop -= 1
            return
        if tag == 'textarea' and self.textarea is not None:
            t, self.textarea = self.textarea, None
            if t['name'] and self.forms:
                if self.form is not None:
                    self.form['multi'].append(t['name'])
                self.out.append(self._field(t['name'], ''.join(t['text']).replace('\n', ' || '), 'text', (t['ph'] + ' (lines: put || between them)').strip()))
            return
        if self.textarea is not None:
            return
        if tag == 'select' and self.select is not None:
            s, self.select = self.select, None
            picked = next((o[0] for o in s['opts'] if o[1]), s['opts'][0][0] if s['opts'] else '')
            if s['name'] and self.forms:
                self.out.append('<span class="x-choices">' + ' · '.join(esc(o[2].strip() or o[0]) + (f' ({esc(o[0])})' if o[2].strip() and o[2].strip() != o[0] else '') for o in s['opts']) + '</span> ')
                self.out.append(self._field(s['name'], picked, 'text', 'one of the choices'))
            return
        if self.select is not None:
            if tag == 'option':
                self.select['in'] = False
            return
        if tag in VOID or tag in ('img', 'source'):
            return
        if tag == 'form':
            if self.form is not None and not self.form['submit']:   # A FORM ONLY A PAGE SCRIPT SENDS (a stroke painted, a marker dragged): no script here, so no form; its words stay
                f = self.form
                self.js_only.add(f.get('do') or '?')
                self.out[f['at']] = '<div class="x-form">'
                for i in f['pieces']:
                    self.out[i] = ''
                for i in range(f['at'] + 1, len(self.out)):
                    if self.out[i].startswith('<input type="hidden" name="p_'):
                        self.out[i] = ''
                self.form = None
                self.forms = max(0, self.forms - 1)
                if self.stack:
                    self.stack.pop()
                self.out.append('</div>')
                return
            if self.form is not None:
                f = self.form
                self.pressable.add(f.get('do') or '?')
                for name, opts in self.groups.get(f['fid'], {}).items() if f['fid'] else ():
                    ticked = ', '.join(v for v, on in opts if on)
                    self.out.append(f'<span class="x-tick-word">{esc(name.upper())}: </span>' + self._field(name, ticked, 'text', 'the values above to tick, comma separated'))
                    f['lists'].append(name)
                odd = ','.join(f'{e}={o}' for e, o in f['names'].items() if e != 'p_' + o)
                self.out.append(f'<input type="hidden" name="p_fields" value="{esc(odd or "1")}">')
                if f['lists']:
                    self.out.append(f'<input type="hidden" name="p_lists" value="{esc(",".join(f["lists"]))}">')
                if f['multi']:
                    self.out.append(f'<input type="hidden" name="p_multi" value="{esc(",".join(f["multi"]))}">')
            self.form = None
            self.forms = max(0, self.forms - 1)
        if self.stack:
            el = self.stack.pop()
            if el:
                self.out.append(f'</{el}>')

    def handle_data(self, data):
        if self.drop:
            return
        if self.textarea is not None:
            self.textarea['text'].append(data)
            return
        if self.select is not None:
            if self.select['in'] and self.select['opts']:
                self.select['opts'][-1][2] += data
            return
        self.out.append(esc(data).replace('&#x27;', "'"))

    def handle_comment(self, data):
        return

    def handle_decl(self, decl):
        return

    def unknown_decl(self, data):
        return

    def handle_pi(self, data):
        return

    def close(self):
        super().close()
        while self.stack:
            el = self.stack.pop()
            if el:
                self.out.append(f'</{el}>')


class _Groups(html.parser.HTMLParser):
    """THE BOXES TO TICK, by their form: {form id: {name: [(value, ticked)]}} (a box names its form by form=, or sits inside it)"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.groups, self.inside = {}, []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if tag == 'form':
            self.inside.append(a.get('id', ''))
        if tag == 'input' and a.get('type', '').lower() in ('checkbox', 'radio') and a.get('name'):
            fid = a.get('form') or (self.inside[-1] if self.inside else '')
            if fid:
                self.groups.setdefault(fid, {}).setdefault(a['name'], []).append((a.get('value', 'on'), 'checked' in a))

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == 'form' and self.inside:
            self.inside.pop()


# ---- the sheet: the office's own, its element names turned to the classes they became; anything the gate refuses dropped
_SELECTOR_TAG = re.compile(r'(^|[\s>+~,(])(' + '|'.join(sorted(AS, key=len, reverse=True)) + r')(?=$|[\s.:#\[>+~,)])')


def _selector(sel):
    sel = _SELECTOR_TAG.sub(lambda m: m.group(1) + '.' + AS[m.group(2)][1], sel)
    sel = re.sub(r'(^|[\s>+~,(])(textarea|select|video|audio|canvas|svg|img)(?=$|[\s.:#\[>+~,)])', lambda m: m.group(1) + ('input' if m.group(2) in ('textarea', 'select') else '.x-media'), sel)
    sel = re.sub(r'#([A-Za-z0-9_-]+)', r'.x-id-\1', sel)
    sel = sel.replace('[open]', '').replace('::-webkit-details-marker', '::after')
    return sel


def _declarations(body):
    keep = []
    for d in body.split(';'):
        low = d.lower()
        if '\\' in d or '<' in d or any(w in re.sub(r'\s+', '', low) for w in ('@import', 'expression(', 'image-set(', 'src(', 'behavior', 'javascript:')):
            continue
        if 'url(' in low:
            ok = all(u.strip().startswith(('/themes/', 'https://storage.googleapis.com/positivefeedback-cdn/')) and '..' not in u and '%' not in u
                     for _q, u in re.findall(r'url\(\s*([\'"]?)(.*?)\1\s*\)', d, re.I | re.S))
            if not ok:
                continue
        keep.append(d)
    return ';'.join(keep)


def sheet(css, drawn=None):
    css = re.sub(r'/\*.*?\*/', '', css or '', flags=re.S)
    out, i, depth = [], 0, 0
    buf = ''
    while i < len(css):   # selectors { declarations } and @media/@supports { ... } blocks, one level deep
        j = css.find('{', i)
        if j < 0:
            break
        head = css[i:j].strip()
        if head.startswith('@'):
            if head.lower().startswith(('@media', '@supports', '@container')):
                out.append(head + '{')
                depth += 1
                i = j + 1
                continue
            k, level = j + 1, 1   # @font-face, @keyframes...: kept when clean, whole
            while k < len(css) and level:
                level += {'{': 1, '}': -1}.get(css[k], 0)
                k += 1
            block = css[i:k]
            if head.lower().startswith('@keyframes') or head.lower().startswith('@font-face'):
                inner = re.sub(r'\{([^{}]*)\}', lambda m: '{' + _declarations(m.group(1)) + '}', block)
                out.append(inner)
            i = k
            continue
        k = css.find('}', j)
        if k < 0:
            break
        body = _declarations(css[j + 1:k])
        sels = ','.join(x for x in (_selector(s) for s in head.split(',')) if drawn is None or set(re.findall(r'\.([A-Za-z0-9_-]+)', x)) <= drawn)
        if body.strip() and sels.strip():
            out.append(sels + '{' + body + '}')
        i = k + 1
        while depth and css[i:].lstrip().startswith('}'):
            i = css.index('}', i) + 1
            out.append('}')
            depth -= 1
    out.extend('}' * depth)
    buf = ''.join(out)
    return buf.replace('<', '').replace('\\', '')


BASE = ('.x-table{display:table;width:100%;border-collapse:collapse}.x-thead{display:table-header-group}.x-tbody{display:table-row-group}'
        '.x-tr{display:table-row}.x-td,.x-th{display:table-cell;padding:4px 8px;vertical-align:top}.x-th{font-weight:700}'
        '.x-pre{white-space:pre-wrap;font-family:var(--font-notes)}.x-code{font-family:var(--font-notes)}.x-s{text-decoration:line-through}'
        '.x-summary{font-weight:700;margin:6px 0}.x-media{display:inline-block;font-family:var(--font-notes);font-size:.8rem;opacity:.8;word-break:break-all}'
        '.x-box{display:inline-block;margin-right:6px}.x-box-value{opacity:.7}.x-said{margin:0 0 10px;font-weight:700}'
        'form input[type=text]{min-width:12ch;max-width:100%}')


def view(markup, css, path, key='', said=''):
    """-> {html, css} for LARRYD's view gate: the office's canvas, its sheets lifted out of the markup, rewritten (see the head)."""
    lifted = re.findall(r'<style[^>]*>(.*?)</style>', markup, re.S | re.I)
    groups = _Groups()
    try:
        groups.feed(markup)
        groups.close()
    except Exception:   # noqa: BLE001
        pass
    r = _Rewrite(path, groups.groups)
    r.feed(markup)
    r.close()
    out = ''.join(r.out)
    if said:
        out = f'<div class="clarity x-said">{esc(said)}</div>' + out
    drawn = {c for v in re.findall(r' class="([^"]*)"', out) for c in v.split()}
    PRESSES['js_only'] |= r.js_only
    PRESSES['get'] |= r.pressable
    return {'html': out, 'css': BASE + sheet(' '.join([css, *lifted]), drawn)}


PRESSES = {'js_only': set(), 'get': set()}   # every press drawn in this process (a check reads it)


def press_of(search, agent='', back=''):
    """THE PRESS A GET CARRIES (the office's POST form rebuilt above): its token and the office's own fields, as its /agent_press reads
    them (agent, do, back, value, his words, the boxes ticked as lists). None when the address carries no press."""
    if not isinstance(search, dict) or not search.get('p_token') or not search.get('p_fields'):
        return None
    names = {k: k[2:] for k in search if isinstance(k, str) and k.startswith('p_') and k not in ('p_token', 'p_fields', 'p_lists', 'p_multi', 'p_route')}
    names.update(dict(pair.split('=', 1) for pair in str(search['p_fields']).split(',') if '=' in pair))
    lists = {x for x in str(search.get('p_lists') or '').split(',') if x}
    multi = {x for x in str(search.get('p_multi') or '').split(',') if x}
    fields = []
    for e, orig in names.items():
        v = search.get(e, '')
        v = v[0] if isinstance(v, list) and v else v
        v = str(v if v is not None else '')
        if orig in multi:
            v = v.replace(' || ', '\n').replace('||', '\n')
        if orig in lists:
            for item in [x.strip() for x in v.split(',') if x.strip()]:
                fields.append((orig, item))
            continue
        fields.append((orig, v))
    if not any(k == 'do' for k, _v in fields) and not search.get('p_route'):
        return None
    if not any(k == 'agent' for k, _v in fields):
        fields.append(('agent', agent))
    fields.append(('back', back))
    from werkzeug.datastructures import MultiDict
    return {'token': str(search['p_token']), 'fields': MultiDict(fields), 'route': str(search.get('p_route') or '/agent_press')}
