"""THE OPERATIONS MANAGER OFFICE, MOVED INTO LARRYD RUNTIME INTERNAL (2026-11-03, the owner: "all virtual sanity agents will use 1 single
internal larryd run"; "rip it out of the virtual sanity"). This folder holds the office's own code, copied whole: operations_manager/app
(its agent programs agent00N_*.py, web/app.py and web/page.py, its schemas, templates and sheet) and the frame it was drawn in (frame/*,
from the replica). Its state lives at ~/larryd/server/runtime/internal/instance/data/operations_manager (the office's instance, copied once).

One agent per card: agent.py names its program (FILE) and hands the CALL or RUN here.
- A CALL is what the office's /internal/view drew for this agent: the office's own page (web/app.py home, answers only, the public agent
  face) draws every canvas from its own store and LARRYD's records, and this agent's canvas is taken from it. The canvas is then made to fit
  LARRYD's view gate (core_engine/view.py): <style> moves to the sheet, elements outside the gate's list become div/span carrying
  data-tag (their table look kept by the sheet), attributes outside it are dropped, links and forms that are not the page's own become text.
- A RUN is what the office's RUN AGENT did for it: its RUN taken on its own shell (store.run: RUN n QUEUED), its own program's run(), the
  MARK IV agent's red round after its run, all synchronous here; the delivery is the run's own LOGS record as the office wrote it.
"""
import html as _html
import html.parser
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, 'operations_manager', 'app')
DATA = os.path.expanduser('~/larryd/server/runtime/internal/instance/data/operations_manager')
OFFICE_PY = os.path.expanduser('~/virtual_workspace/.venv/bin/python')   # the office's own interpreter (flask, jinja2, markupsafe), as its launcher ran it
GATE_APP = os.path.expanduser('~/larryd/server/runtime/app')   # LARRYD's own view gate, read where it is
LAYER = 'agent'   # the public agent face: the canvas exactly as the pf agent mode shows it (no rnd controls: those post to the office's own routes)


def _env():
    os.environ['REPLICA_OFFICE_APP'] = APP
    os.environ['REPLICA_INSTANCE'] = DATA
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.path[:] = [APP] + [p for p in sys.path if os.path.abspath(p or '.') not in (HERE, APP)]   # the office's own packages first (agent/, web/, frame/); this folder's agent.py is not the office's agent package
    sys.modules.pop('agent', None)


def _ensure_interpreter():
    """The office ran on the workspace's interpreter (flask); LARRYD's own has none: hand the same stdin to it once."""
    try:
        import flask  # noqa: F401
        import jinja2  # noqa: F401
        return None
    except ImportError:
        pass
    if os.environ.get('OM_REEXEC') == '1' or not os.path.isfile(OFFICE_PY):
        raise SystemExit('the office needs flask and jinja2, and the workspace interpreter is not there: ' + OFFICE_PY)
    import subprocess
    data = sys.stdin.read()
    env = dict(os.environ, OM_REEXEC='1')
    done = subprocess.run([OFFICE_PY, '-B', os.path.abspath(sys.argv[0])], input=data, text=True, capture_output=True, env=env, cwd=HERE)
    sys.stdout.write(done.stdout)
    sys.stderr.write(done.stderr)
    raise SystemExit(done.returncode)


# ---- the view made to fit LARRYD's gate --------------------------------------------------------------------------------------
KEEP_TAGS = frozenset('div span section article header footer p b strong i em small img button ul ol li h1 h2 h3 h4 h5 h6 br hr figure figcaption a canvas form input'.split())
BLOCKS = {'table': 'div', 'thead': 'div', 'tbody': 'div', 'tfoot': 'div', 'tr': 'div', 'details': 'div', 'summary': 'div', 'pre': 'div',
          'nav': 'div', 'main': 'div', 'aside': 'div', 'dl': 'div', 'dt': 'div', 'dd': 'div', 'blockquote': 'div', 'caption': 'div', 'fieldset': 'div', 'legend': 'div'}
INLINES = {'td': 'span', 'th': 'span', 'code': 'span', 'label': 'span', 'kbd': 'span', 'samp': 'span', 'u': 'span', 's': 'span', 'sup': 'span',
           'sub': 'span', 'mark': 'span', 'abbr': 'span', 'time': 'span', 'tt': 'span', 'var': 'span', 'q': 'span', 'cite': 'span', 'select': 'span', 'option': 'span', 'textarea': 'span'}
DROP_WHOLE = frozenset(('script', 'style', 'svg', 'noscript', 'template', 'iframe', 'object', 'embed', 'audio', 'video', 'math', 'head', 'title', 'link', 'meta'))
VOID = frozenset(('br', 'hr', 'img', 'input', 'meta', 'link', 'col', 'area', 'base', 'wbr', 'source', 'track', 'param'))
ATTRS = frozenset(('class', 'title', 'alt', 'role'))
TABLE_CSS = ('[data-tag="table"] { display: table; border-collapse: collapse } [data-tag="thead"] { display: table-header-group } [data-tag="tbody"] { display: table-row-group } '
             '[data-tag="tfoot"] { display: table-footer-group } [data-tag="tr"] { display: table-row } [data-tag="td"], [data-tag="th"] { display: table-cell } '
             '[data-tag="th"] { font-weight: 700 } [data-tag="pre"] { white-space: pre-wrap } [data-tag="code"] { font-family: ui-monospace, Menlo, monospace }')


_GATE = []


def _gate():
    """LARRYD's own view gate (core_engine/view.py), loaded by its file: the office has the platform's core_engine on its path, a different package"""
    if not _GATE:
        import importlib.util
        spec = importlib.util.spec_from_file_location('larryd_view_gate', os.path.join(GATE_APP, 'core_engine', 'view.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _GATE.append(mod)
    return _GATE[0]


class _Fit(html.parser.HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.out, self.path, self.skip, self.stack, self.forms = [], path, 0, [], 0
        self.gate = _gate()

    def _attrs(self, tag, attrs, was):
        had = {}
        for name, value in attrs:
            value = '' if value is None else str(value)
            if name in had:
                continue
            if name.startswith(('data-', 'aria-')) and re.fullmatch(r'(data|aria)-[a-z0-9-]+', name):
                had[name] = value
            elif name in ATTRS:
                had[name] = value
        if was != tag:
            had['data-tag'] = was
        return had

    def _open(self, tag, had, close=False):
        inner = ''.join(f' {k}="{_html.escape(v, quote=True)}"' for k, v in had.items())
        self.out.append(f'<{tag}{inner}{" /" if close else ""}>')

    def handle_starttag(self, tag, attrs, close=False):
        if self.skip:
            if tag in DROP_WHOLE and tag not in VOID and not close:
                self.skip += 1
            return
        if tag in DROP_WHOLE:
            if tag not in VOID and not close:
                self.skip = 1
            return
        raw = dict((k, '' if v is None else v) for k, v in attrs)
        was = tag
        if tag in BLOCKS:
            tag = BLOCKS[tag]
        elif tag in INLINES:
            tag = INLINES[tag]
        elif tag not in KEEP_TAGS:
            tag = 'span'
        had = self._attrs(tag, attrs, was)
        if tag == 'a':
            href = raw.get('href', '')
            if self.gate.link_address(href):
                had.update(href=href, target='_blank', rel='noopener noreferrer')
            elif self.path and self.gate.page_address(href, self.path):
                had['href'] = href
            else:
                tag, had['data-tag'] = 'span', 'a'
        elif tag == 'img':
            if not self.gate.picture_address(raw.get('src', '')):
                if raw.get('alt'):
                    self.out.append(f'<span data-tag="img">{_html.escape(raw["alt"])}</span>')
                return
            had['src'] = raw['src']
            if raw.get('loading') in ('lazy', 'eager'):
                had['loading'] = raw['loading']
        elif tag == 'form':
            if raw.get('method', '').lower() == 'get' and self.path and raw.get('action') == self.path:
                had = {k: v for k, v in had.items() if k == 'class'}
                had.update(method='get', action=self.path)
                self.forms += 1
            else:
                tag, had['data-tag'] = 'div', 'form'
        elif tag == 'input':
            if not (self.forms and raw.get('type') in ('text', 'hidden') and re.fullmatch(r'[a-z_]{1,32}', raw.get('name', ''))):
                return
            had = {k: v for k, v in had.items() if k == 'class'}
            had.update({k: raw[k] for k in ('type', 'name', 'value', 'placeholder') if k in raw})
        elif tag == 'button':
            had['type'] = 'submit' if (self.forms and raw.get('type') == 'submit') else 'button'
        if was in VOID or close:
            self._open(tag, had, close=True)
            return
        self.stack.append((was, tag))
        self._open(tag, had)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, close=True)

    def handle_endtag(self, tag):
        if self.skip:
            if tag in DROP_WHOLE:
                self.skip -= 1
            return
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                while len(self.stack) > i:
                    was, now = self.stack.pop()
                    if now == 'form' and was == 'form':
                        self.forms = max(0, self.forms - 1)
                    self.out.append(f'</{now}>')
                return

    def handle_data(self, data):
        if not self.skip:
            self.out.append(_html.escape(data, quote=False))

    def close(self):
        super().close()
        while self.stack:
            self.out.append(f'</{self.stack.pop()[1]}>')
        return ''.join(self.out)


SELECTOR_TAGS = re.compile(r'(?<![\w\-.#\[:"\'])(' + '|'.join(sorted(set(BLOCKS) | set(INLINES), key=len, reverse=True)) + r')(?![\w\-])')


def _fit_sheet(css):
    gate = _gate()
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S).replace('\\', '')
    css = css.replace('<', '')

    def decl_ok(m):
        d = m.group(0)
        for _q, address in gate._URL.findall(d):
            if not gate.picture_address(address.strip()):
                return ''
        low = re.sub(r'\s+', '', d.lower())
        if any(n in low for n in gate.SHEET_NEVER):
            return ''
        return d
    css = re.sub(r'@import[^;]*;', '', css, flags=re.I)
    css = re.sub(r'[^;{}]*url\([^)]*\)[^;{}]*;?', decl_ok, css)
    css = re.sub(r'@font-face\s*\{[^{}]*\}', '', css, flags=re.I)

    def selectors(m):
        return SELECTOR_TAGS.sub(lambda t: f'[data-tag="{t.group(1)}"]', m.group(1)) + '{'
    css = re.sub(r'([^{}]+)\{', selectors, css)
    for never in gate.SHEET_NEVER:
        css = re.sub(re.escape(never), '', css, flags=re.I)
    return (TABLE_CSS + ' ' + re.sub(r'\s+', ' ', css)).strip()


def fit(view, path):
    """the office's canvas made to fit LARRYD's view gate: -> {html, css}"""
    raw = str(view.get('html') or '')
    sheets = re.findall(r'<style[^>]*>(.*?)</style>', raw, flags=re.S | re.I)
    p = _Fit(path)
    p.feed(raw)
    markup = p.close()
    sheet = _fit_sheet(' '.join([str(view.get('css') or ''), *sheets]))
    out = {'html': markup, 'css': sheet}
    why = _gate().refused(out, path)
    if why:   # never a view the gate drops whole: say why instead
        return {'html': f'<div class="annotation">The canvas could not be made to fit the view gate: {_html.escape(why)}.</div>', 'css': ''}
    return out


def page_path(given):
    """the page this canvas sits on, as LARRYD names it to the gate: /wid/rnd/en/app/<species>/<page>"""
    page = str(given.get('page') or '')
    if isinstance(given.get('page'), dict):
        page = str(given['page'].get('path') or given['page'].get('board') or '')
    if page.startswith('/'):
        return page.split('?')[0]
    parts = [x for x in page.split('/') if x]
    if len(parts) >= 2:
        return f'/wid/rnd/en/app/{parts[-2]}/{parts[-1]}'
    return ''


# ---- the office ---------------------------------------------------------------------------------------------------------------
def office():
    _env()
    import logging
    logging.disable(logging.CRITICAL)
    from web import app as W
    app = W.create(W.PAGE['store'], W.frame.agent())
    return W, app, app.office


def module_of(o, file):
    return next((m for m in o['agents'] if os.path.basename(m.__file__) == file), None)


def say_view(name, words):
    return {'html': f'<div class="replica-canvas"><div class="replica-canvas-content"><div class="title">{_html.escape(name)}</div>'
                    f'<div class="annotation">{_html.escape(words)}</div></div></div>', 'css': ''}


def call(file, given):
    W, app, o = office()
    module = module_of(o, file)
    name = (getattr(module, 'NAME', None) or (o['agent'] or {}).get('name') or file) if module else file
    if module is None:
        return {'view': say_view(file, 'its program is not in this folder: nothing drawn.')}
    from flask import g
    with app.test_request_context('/'):
        g.lang = 'en'
        g.carry = {'agentlayer': LAYER, 'mode': ''}
        g.answers_only = True
        answers = o['home']() or {}
        key = (o['agent'] or {}).get('key') if module is o['MARK_IV'] else o['key_of'](module)
        answer = answers.get(key) if key else None
    if not key:
        return {'view': say_view(name, 'its card is not found in LARRYD by its name: the office draws no canvas without its card key.')}
    if not isinstance(answer, dict) or not (answer.get('view') or {}).get('html'):
        return {'view': say_view(name, 'the office drew no canvas for it on this face.')}
    v = answer['view']
    return {'view': fit({'html': str(v.get('head') or '') + str(v.get('html') or '') + str(v.get('foot') or ''), 'css': str(v.get('css') or '')}, page_path(given))}


def run(file, given):
    W, app, o = office()
    module = module_of(o, file)
    label = (getattr(module, 'NAME', None) or (o['agent'] or {}).get('name') or file) if module else file
    if module is None:
        raise SystemExit(f'{file}: its program is not in this folder')
    store = o['store']
    o['place']()   # every agent in its shell, as the office's page does before any press
    held = o['shell_of'](module)
    if not held:
        raise SystemExit(f'{label}: no shell holds it in the office (its card key not found): nothing run')
    job = held.get('job') or {}
    if job.get('data_job_run_state') in ('QUEUED', 'DROPPED') and str(job.get('data_job_run') or '').isdigit():
        n = int(job['data_job_run'])   # A RUN LEFT QUEUED (the office's page is gone, nothing will take it): run that one, as the office's catch-up at its start ran the RUNs queued while it was away
    else:
        took, word = store.run(held['id'])   # its RUN taken, as the office's RUN AGENT press takes it
        if not took:
            raise SystemExit(f'{label}: RUN refused by the office: {word}')
        n = int(word.split()[1])
    import datetime
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    shells = store.board()
    try:
        module.run(store, held['job_key'], n, o['agent'], shells, chain=o['chain_of'](shells))
    except Exception as fault:   # A RUN THAT CRASHES IS RED, as the office's run_agent writes it
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        store.ran(held['job_key'], n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps({'summary': f'FAILED · {line}'}), 'FAILED')
    if module is o['MARK_IV']:   # THE MARK IV AGENT RUNS THE FRAME'S READS, THE RED AMONG THEM, on its RUN AGENT
        try:
            o['red_round']()
        except Exception as fault:  # noqa: BLE001
            print(f'red round: {type(fault).__name__}: {fault}', file=sys.stderr)
    last = next((r for r in store.runs(held['job_key'], 5) if r['n'] == n), None)
    said = {}
    try:
        said = json.loads((last or {}).get('said') or '{}')
    except ValueError:
        said = {'summary': str((last or {}).get('said') or '')}
    summary = str(said.get('summary') or (last or {}).get('said') or '').strip() or f'RUN {n}: no LOGS record read back'
    if not last or last.get('exit'):
        raise SystemExit(f'{label} RUN {n}: {summary}')
    return {'delivery': f'RUN {n} · {summary}'}


def main(file):
    _ensure_interpreter()
    given = json.load(sys.stdin)
    real, sys.stdout = sys.stdout, sys.stderr   # whatever the office prints goes to the log, never into the one JSON answer
    do = given.get('do')
    if do == 'canvas':
        out = call(file, given)
    elif do == 'run':
        out = run(file, given)
    else:
        raise SystemExit('this agent does: canvas, run')
    real.write(json.dumps(out))
    real.flush()
    os._exit(0)   # the office's timers (daemon threads) never hold the process
