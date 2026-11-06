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
TAGS = frozenset('div span section article header footer p b strong i em small img button ul ol li h1 h2 h3 h4 h5 h6 br hr figure figcaption a canvas form input'.split())
ATTRS = frozenset(('class', 'title', 'alt', 'role', 'type', 'src', 'loading', 'href', 'target', 'rel', 'method', 'action', 'name', 'value', 'placeholder'))
LINK = {'target': '_blank', 'rel': 'noopener noreferrer'}   # a link out: a new tab that cannot reach back, always both
_HOST = re.compile(r'(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}')
SHEET_NEVER = ('@import', 'expression(', 'image-set(', 'src(', 'behavior', 'javascript:')
_URL = re.compile(r'url\(\s*([\'"]?)(.*?)\1\s*\)', re.I | re.S)


def link_address(address):
    """Is this a plain https address to a NAMED host (a link a card may draw: a developer's website)? No user, no port, no number for a host,
    nothing that hides or breaks out."""
    if not isinstance(address, str) or not address or len(address) > 2048 or any(c.isspace() or ord(c) < 32 or c in '"\'<>\\`' for c in address):
        return False
    try:
        parts = urllib.parse.urlsplit(address)
        port = parts.port
    except ValueError:
        return False
    return parts.scheme == 'https' and not parts.username and not parts.password and port is None and bool(_HOST.fullmatch(parts.netloc.lower()))


_PATH = re.compile(r'/(?!/)[A-Za-z0-9_./~-]*')
_QUERY = re.compile(r'[A-Za-z0-9_.~%+&=-]*')
_THEMES = re.compile(r'/themes/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*\.[A-Za-z0-9]+')


def page_address(address, path):
    """Is this THE PAGE ITSELF, changed only in its query (a controller's link: the page's own path, then at most a plain query)? Never another path,
    another site, a fragment or anything that hides."""
    if not path or not isinstance(path, str) or not _PATH.fullmatch(path) or '..' in path or not isinstance(address, str):
        return False
    if address == path:
        return True
    return address.startswith(path + '?') and bool(_QUERY.fullmatch(address[len(path) + 1:]))


_DAM_DOWNLOAD = re.compile(r'/so/([a-z0-9_-]{1,32})/([a-z]{2}(?:-[a-z]{2,4})?)/app/files/card/DA-M_[0-9A-F]{12}_[0-9A-F]{4}/download')
_PAGE_SIDE = re.compile(r'/[a-z0-9_-]{1,32}/([a-z0-9_-]{1,32})/([a-z]{2}(?:-[a-z]{2,4})?)/app/.*')


def download_address(address, path):
    """Is this DA-M's own DOWNLOAD of one file, on the page's own site, side and language (the owner, 2026-10-25: "we can do
    it without javascript just like any download")? Exactly /so/<side>/<lang>/app/files/card/<DA-M key>/download, nothing
    more: DA-M's own door decides, with the member's own session, whether the file is theirs to have."""
    page = _PAGE_SIDE.fullmatch(path) if isinstance(path, str) else None
    got = _DAM_DOWNLOAD.fullmatch(address) if isinstance(address, str) else None
    return bool(page and got and got.groups() == page.groups())


def download_of(path, dam_key, origin='', local=()):
    """DA-M's own DOWNLOAD address of one file on the page's own side and language, built by the runtime (an agent never
    writes an address of the platform's), as an https address of the caller's page host (origin), opened in a new tab:
    the platform's own view gate takes no other link (found on B, 2026-10-25: a same-site path dropped the whole view).
    '' when the page's path, the key or the host is not plain."""
    page = _PAGE_SIDE.fullmatch(path) if isinstance(path, str) else None
    address = f'/so/{page.group(1)}/{page.group(2)}/app/files/card/{dam_key}/download' if page and isinstance(dam_key, str) else ''
    if not (address and download_address(address, path) and isinstance(origin, str) and (link_address(origin) or origin in (local or ()))):
        return ''
    return _built(origin, address, local)


_DAM_ADD = re.compile(r'/so/([a-z0-9_-]{1,32})/([a-z]{2}(?:-[a-z]{2,4})?)/app/files/add(?:\?zone=[a-z0-9_-]{1,32})?')
_FROST_PAGE = re.compile(r'/fs/([a-z0-9_-]{1,32})/([a-z]{2}(?:-[a-z]{2,4})?)/[a-z0-9_-]{1,32}(?:/[a-z0-9_-]{1,32}){0,2}')
_ZONE = re.compile(r'[a-z0-9_-]{1,32}')
_PAGE_NAME = re.compile(r'[a-z0-9_-]{1,32}(?:/[a-z0-9_-]{1,32}){0,2}')
_LOCAL_ORIGIN = re.compile(r'http://(?:127\.0\.0\.1|localhost):[0-9]{2,5}')
SERVES = {'upload': 'so', 'download': 'so', 'frost': 'fs'}   # which office serves each marker's page (DA-M: so; FROST: fs): only to pick its origin from page.origins
MARKER = re.compile(r'href="larryd:(upload|download|frost)/([^"<>\s]{0,80})"')   # an agent's own word for a platform page it may link: the runtime builds the address


def local_link(address, origins):
    """A LINK ON A LOCALHOST BOX (CORE_CLEANUP_IV 20/96, ruling c'): plain http to EXACTLY one of the origins the platform handed for this
    page (wid, DA-M, FROST, each its own port on this Mac), then a plain path; nothing else (another host, another port, any user,
    query beyond plain words). origins is empty on any box that is not localhost, so this is never true there."""
    if not (isinstance(address, str) and origins) or any(c.isspace() or ord(c) < 32 or c in '"\'<>\\`' for c in address) or '..' in address:
        return False
    for origin in origins:
        if isinstance(origin, str) and _LOCAL_ORIGIN.fullmatch(origin) and address.startswith(origin + '/'):
            rest = address[len(origin):]
            return bool(re.fullmatch(r'/[A-Za-z0-9_./-]{1,300}(?:\?[a-z_]{1,32}=[A-Za-z0-9_-]{1,64})?', rest))
    return False


def _built(origin, address, local):
    """origin + address when the whole is a link the gate takes: https to a named host, or (local origins only) http to that origin."""
    if not (isinstance(origin, str) and address):
        return ''
    whole = origin.rstrip('/') + address
    if link_address(whole):
        return whole
    return whole if origin in (local or ()) and local_link(whole, local) else ''


def upload_of(path, zone, origin='', local=()):
    """DA-M's own ADD FILES page (its drop zone and uploader: the file goes from the member's browser to DA-M with the member's own session,
    never through the agent), on the page's own side and language: /so/<side>/<lang>/app/files/add[?zone=<zone>], on DA-M's origin.
    zone: plain, or '' for none. '' when the page's path, the zone or the origin is not plain (CORE_CLEANUP_IV 20)."""
    page = _PAGE_SIDE.fullmatch(path) if isinstance(path, str) else None
    if not (page and isinstance(zone, str) and (zone == '' or _ZONE.fullmatch(zone))):
        return ''
    address = f'/so/{page.group(1)}/{page.group(2)}/app/files/add' + (f'?zone={zone}' if zone else '')
    return _built(origin, address, local) if _DAM_ADD.fullmatch(address) else ''


def frost_of(path, name, origin='', local=()):
    """One of FROST's own pages, on the page's own side and language: /fs/<side>/<lang>/<name> on FROST's origin (CORE_CLEANUP_IV 96: pf
    Access, pf The Vault). '' when the page's path, the name or the origin is not plain."""
    page = _PAGE_SIDE.fullmatch(path) if isinstance(path, str) else None
    if not (page and isinstance(name, str) and _PAGE_NAME.fullmatch(name)):
        return ''
    address = f'/fs/{page.group(1)}/{page.group(2)}/{name}'
    return _built(origin, address, local) if _FROST_PAGE.fullmatch(address) else ''


MARKER_LINK = re.compile(r'<a\b([^>]*?)\shref="larryd:(upload|download|frost)/([^"<>\s]{0,80})"([^>]*)>(.*?)</a>', re.S)   # a whole link that carries a marker
_LINK_ONLY = re.compile(r'\s(?:target|rel)="[^"]*"')   # what makes an <a> a link out: taken off when the link goes and its words stay


def resolve(markup, path, origins, local=False):
    """THE MARKERS (CORE_CLEANUP_IV 20/96, ruling b): an agent never writes an address of the platform's. It writes href="larryd:upload/<zone>",
    href="larryd:download/<DA-M key>" or href="larryd:frost/<page>"; this builds each address on the origin of the office that serves it
    (origins: the platform's own word for this page, {wid, so, fs}). When none can be built (no origins handed, a box that may not take
    http, a word that is not plain), THE LINK ALONE GOES: the <a> becomes a <span> with its own words and class, never a bare <a> the gate
    would refuse (frost-d7's finding, frost-05's order 2026-11-06: an unbuildable marker dropped the agent's WHOLE view).
    local: a localhost box, where the handed origins are plain http (each office its own port)."""
    if not isinstance(markup, str) or 'larryd:' not in markup:
        return markup
    origins = origins if isinstance(origins, dict) else {}
    allowed = tuple(v for v in origins.values() if isinstance(v, str)) if local else ()

    def one(m):
        before, kind, word, after, words = m.groups()
        origin = origins[SERVES[kind]] if isinstance(origins.get(SERVES[kind]), str) else ''   # the origin wid handed for the office that serves this page (a lookup in wid's own word; no office is called)
        build = {'upload': upload_of, 'frost': frost_of, 'download': download_of}[kind]
        address = build(path, word, origin, allowed)
        if address:
            return f'<a{before} href="{address}"{after}>{words}</a>'
        return f'<span{_LINK_ONLY.sub("", before + after)}>{words}</span>'   # the link goes, its words and class stay
    out = MARKER_LINK.sub(one, markup)
    return MARKER.sub('', out)   # a marker outside a plain <a>...</a> (an odd shape): its href goes, as before


def package_address(address):
    """Is this a file of the look's own package, served by the page's own site (/themes/<plain path>: the dock's logos are package files, not the
    CDN's)? Plain names and one extension: no "..", no "%", no query, nothing that walks or hides."""
    return isinstance(address, str) and bool(_THEMES.fullmatch(address))


def picture_address(address):
    return cdn_address(address) or package_address(address)


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
    def __init__(self, path='', local=()):
        super().__init__(convert_charrefs=True)
        self.why, self.path, self.forms, self.local = '', path, 0, tuple(local or ())

    def _no(self, why):
        if not self.why:
            self.why = why

    def handle_starttag(self, tag, attrs):
        if tag not in TAGS:
            return self._no(f'the view\'s markup holds a <{tag}> element')
        had = {name: (value or '') for name, value in attrs}
        if len(had) != len(attrs):
            return self._no('an attribute written twice')
        if tag == 'a':   # A LINK: either THE PAGE ITSELF with its query changed (no target, no rel), or A LINK OUT (href, target and rel all three, exactly)
            same = (page_address(had.get('href'), self.path) or download_address(had.get('href'), self.path)) and 'target' not in had and 'rel' not in had
            out = (link_address(had.get('href')) or local_link(had.get('href'), self.local)) and all(had.get(k) == v for k, v in LINK.items())
            if not (same or out):
                return self._no('a link that is neither the page itself, DA-M\'s own download of a file, nor https to a named host in a new tab, noopener noreferrer')
        if tag == 'form':   # A SEARCH: a GET to the page itself, nothing else
            if had.get('method') != 'get' or not self.path or had.get('action') != self.path or set(had) - {'method', 'action', 'class'}:
                return self._no('a form that is not a GET to the page itself')
            self.forms += 1
        if tag == 'input':   # a search's word, or a kept one: inside a form, text or hidden, a plain name
            if not self.forms or had.get('type') not in ('text', 'hidden') or not re.fullmatch(r'[a-z_]{1,32}', had.get('name', '')) \
                    or set(had) - {'type', 'name', 'value', 'placeholder', 'class'}:
                return self._no('an input that is not a plain text or hidden word of a search')
        for name, value in attrs:
            value = value if value is not None else ''
            if name.startswith(('data-', 'aria-')) and re.fullmatch(r'(data|aria)-[a-z0-9-]+', name):
                continue
            if name not in ATTRS:
                return self._no(f'the view\'s markup holds the attribute {name}')
            if name == 'type' and tag == 'input':
                continue
            if name == 'type' and (tag != 'button' or value not in ('button', 'submit') or (value == 'submit' and not self.forms)):
                return self._no('a type other than a plain button, or a search\'s own submit')
            if name in ('method', 'action') and tag != 'form':
                return self._no(f'{name} on a <{tag}>')
            if name in ('name', 'value', 'placeholder') and tag != 'input':
                return self._no(f'{name} on a <{tag}>')
            if name in ('src', 'loading') and tag != 'img':
                return self._no(f'{name} on a <{tag}>')
            if name in ('href', 'target', 'rel') and tag != 'a':
                return self._no(f'{name} on a <{tag}>')
            if name == 'src' and not picture_address(value):
                return self._no('the view\'s markup reaches outside our CDN')
            if name == 'loading' and value not in ('lazy', 'eager'):
                return self._no('a loading other than lazy or eager')

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag not in TAGS:
            self._no(f'the view\'s markup holds a </{tag}> element')
        if tag == 'form':
            self.forms = max(0, self.forms - 1)

    def handle_comment(self, data):
        self._no('the view\'s markup holds a comment')

    def handle_decl(self, decl):
        self._no('the view\'s markup holds a declaration')

    def handle_pi(self, data):
        self._no('the view\'s markup holds a processing instruction')

    def unknown_decl(self, data):
        self._no('the view\'s markup holds a declaration')


def _markup(markup, path='', local=()):
    check = _Check(path, local)
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
        if not picture_address(address.strip()):
            return 'the view\'s sheet reaches outside our CDN'
    return ''


def refused(view, path='', local=()):
    """Why this view may not be drawn, or '' when it may. path: the page's own path (the one address a controller's links and search may name)."""
    if not isinstance(view, dict) or set(view) - {'html', 'css'} or not all(isinstance(view.get(k, ''), str) for k in ('html', 'css')):
        return 'a view is {html, css}, two texts'
    markup, sheet = view.get('html', ''), view.get('css', '')
    if len(markup.encode('utf-8')) > MAX_HTML:
        return 'the view\'s markup is over 200 KB'
    if len(sheet.encode('utf-8')) > MAX_CSS:
        return 'the view\'s sheet is over 100 KB'
    return _markup(markup, path, local) or _sheet(sheet)


def checked(answer, path='', origins=None, local=False):
    """The answer with its view passed on, or dropped whole when refused (-> (answer, why)). origins: the platform's own word for this page's
    offices ({wid, so, fs}); its markers are resolved first; on a localhost box (local) the gate takes http for exactly those origins."""
    if not isinstance(answer, dict) or 'view' not in answer:
        return answer, ''
    if isinstance(answer['view'], dict) and isinstance(answer['view'].get('html'), str):
        answer = {**answer, 'view': {**answer['view'], 'html': resolve(answer['view']['html'], path, origins, local)}}
    allowed = tuple(v for v in (origins or {}).values() if isinstance(v, str)) if local and isinstance(origins, dict) else ()
    why = refused(answer['view'], path, allowed)
    if why:
        answer = {k: v for k, v in answer.items() if k != 'view'}
    else:   # PASSED ON WHOLE, both texts always there (PF Virtual Wire, 2026-10-08: its door handed markup and no sheet, the platform's own gate reads a view as {html, css} and placed nothing)
        answer = {**answer, 'view': {'html': answer['view'].get('html', ''), 'css': answer['view'].get('css', '')}}
    return answer, why
