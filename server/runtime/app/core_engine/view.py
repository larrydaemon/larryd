"""AN AGENT'S OWN VIEW (the owner, 2026-10-07: the card's markup and CSS live in the agent, never in the platform's core):
an answer may carry view = {html, css}, drawn by the platform inside one shadow root on its own host element. The
runtime passes it on only when every element and attribute is on the ALLOWLIST below (parsed, never pattern-matched),
every address is our CDN's, and the sheet holds nothing that loads, runs or escapes; each within its size. Anything
else: the whole view is dropped (the cards stay), never trimmed."""
import html.parser
import posixpath
import re
import urllib.parse

CDN_HOST, CDN_PATH = 'storage.googleapis.com', '/positivefeedback-cdn/'
MAX_HTML, MAX_CSS = 200 * 1024, 100 * 1024
TAGS = frozenset('div span section article header footer p b strong i em small img button ul ol li h1 h2 h3 h4 h5 h6 br hr figure figcaption'.split())
ATTRS = frozenset(('class', 'title', 'alt', 'role', 'type', 'src', 'loading'))
SHEET_NEVER = ('@import', 'expression(', 'image-set(', 'src(', 'behavior', 'javascript:')
_URL = re.compile(r'url\(\s*([\'"]?)(.*?)\1\s*\)', re.I | re.S)


def cdn_address(address):
    """Is this exactly an address on our CDN (https, the one host, under our bucket, nothing that walks or hides)?"""
    if not isinstance(address, str) or not address or '\\' in address or any(c.isspace() or ord(c) < 32 for c in address):
        return False
    low = address.lower()
    if '%2e' in low or '%2f' in low or '%5c' in low:
        return False
    try:
        parts = urllib.parse.urlsplit(address)
    except ValueError:
        return False
    if parts.scheme != 'https' or parts.netloc != CDN_HOST or parts.username or parts.password or parts.port:
        return False
    path = parts.path
    if '..' in path.split('/') or '..' in path or posixpath.normpath(path) != path.rstrip('/') or not path.startswith(CDN_PATH):
        return False
    return True


class _Check(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.why = ''

    def _no(self, why):
        if not self.why:
            self.why = why

    def handle_starttag(self, tag, attrs):
        if tag not in TAGS:
            return self._no(f'the view\'s markup holds a <{tag}> element')
        for name, value in attrs:
            value = value if value is not None else ''
            if name.startswith(('data-', 'aria-')) and re.fullmatch(r'(data|aria)-[a-z0-9-]+', name):
                continue
            if name not in ATTRS:
                return self._no(f'the view\'s markup holds the attribute {name}')
            if name == 'type' and (tag != 'button' or value != 'button'):
                return self._no('a type other than a plain button')
            if name in ('src', 'loading') and tag != 'img':
                return self._no(f'{name} on a <{tag}>')
            if name == 'src' and not cdn_address(value):
                return self._no('the view\'s markup reaches outside our CDN')
            if name == 'loading' and value not in ('lazy', 'eager'):
                return self._no('a loading other than lazy or eager')

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag not in TAGS:
            self._no(f'the view\'s markup holds a </{tag}> element')

    def handle_comment(self, data):
        self._no('the view\'s markup holds a comment')

    def handle_decl(self, decl):
        self._no('the view\'s markup holds a declaration')

    def handle_pi(self, data):
        self._no('the view\'s markup holds a processing instruction')

    def unknown_decl(self, data):
        self._no('the view\'s markup holds a declaration')


def _markup(markup):
    check = _Check()
    try:
        check.feed(markup)
        check.close()
    except Exception:   # noqa: BLE001 - a markup the parser cannot read is no view
        return 'the view\'s markup cannot be read'
    return check.why


def _sheet(sheet):
    if '\\' in sheet:
        return 'the view\'s sheet holds a backslash'
    if '<' in sheet:
        return 'the view\'s sheet holds a <'
    flat = re.sub(r'\s+', '', sheet.lower())
    for never in SHEET_NEVER:
        if never in flat:
            return f'the view\'s sheet holds {never}'
    if flat.count('url(') != len(_URL.findall(sheet)):
        return 'the view\'s sheet holds a url( it cannot read'
    for _q, address in _URL.findall(sheet):
        if not cdn_address(address.strip()):
            return 'the view\'s sheet reaches outside our CDN'
    return ''


def refused(view):
    """Why this view may not be drawn, or '' when it may."""
    if not isinstance(view, dict) or set(view) - {'html', 'css'} or not all(isinstance(view.get(k, ''), str) for k in ('html', 'css')):
        return 'a view is {html, css}, two texts'
    markup, sheet = view.get('html', ''), view.get('css', '')
    if len(markup.encode('utf-8')) > MAX_HTML:
        return 'the view\'s markup is over 200 KB'
    if len(sheet.encode('utf-8')) > MAX_CSS:
        return 'the view\'s sheet is over 100 KB'
    return _markup(markup) or _sheet(sheet)


def checked(answer):
    """The answer with its view passed on, or dropped whole when refused (-> (answer, why))."""
    if not isinstance(answer, dict) or 'view' not in answer:
        return answer, ''
    why = refused(answer['view'])
    if why:
        answer = {k: v for k, v in answer.items() if k != 'view'}
    return answer, why
