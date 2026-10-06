"""THE BROWSER PROOF of the one card template: ten agents with ten looks on the developer's own shelf, in a real
headless Chromium (off-screen), under the page's strict policy. Checks: each card's computed border colour, radius and
padding are its own record's names resolved by the LIVE variables; no card wears another's; no policy violation; then
the theme's variables change (a second theme, then its dark mode) and every card's colour follows with no change to any
record. Run with a Python that has Playwright: python proofs/card_looks_browser.py"""
import json
import pathlib
import shutil
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / 'server' / 'tests'))
sys.path.insert(0, str(HERE / 'server' / 'hanzo' / 'app'))
import test_card_look as t  # noqa: E402
from test_preview import GOOD_CARD, SECRET, _agent, _zip  # noqa: E402
from web import app as host  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PORT = 18431   # a scratch port, never a live one
tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(t.APP / 'agents' / 'marketplace', tmp / 'agents' / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
app = host.create_app(tmp, secret=SECRET, addresses={}, agents=tmp / 'agents', developer=True)
c = app.test_client()
c.get('/marketplace')
for n, (key, record) in enumerate(zip(t.KEYS, t.LOOKS)):
    files = _agent(f'LOOK {n + 1:02d}', GOOD_CARD)
    m = json.loads(files['agent.json'])
    m['look'] = record
    files['agent.json'] = json.dumps(m).encode()
    assert c.post(f'/marketplace/place?key={key}', data=_zip(files), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'}).status_code in (200, 201)
server = make_server('127.0.0.1', PORT, app, threaded=True)
threading.Thread(target=server.serve_forever, daemon=True).start()

PROBE = """() => [...document.querySelectorAll('[data-agent-card]')].map(h => { const a = h.shadowRoot.querySelector('.agent-card');
  const s = getComputedStyle(a); const n = a.querySelector('[data-part=name]');
  return {key: a.dataset.agent, look: a.dataset.look, border: s.borderTopColor, radius: s.borderTopLeftRadius, padding: s.paddingTop,
          effect: a.dataset.effect || '', name_role: [...n.classList].filter(c => c !== 'mk-name').join(' '), style_attr: a.getAttribute('style') || ''} })"""
THEME_B = {f'--active-color-{n:02d}': f'rgb({(n * 37) % 256}, {(n * 91) % 256}, {(n * 53) % 256})' for n in range(1, 65)}
DARK_B = {k: f'rgb({255 - (n * 37) % 256}, {255 - (n * 91) % 256}, {255 - (n * 53) % 256})' for n, k in enumerate(THEME_B, 1)}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    violations = []
    page.on('console', lambda m: violations.append(m.text) if 'Content Security Policy' in m.text else None)
    page.goto(f'http://127.0.0.1:{PORT}/marketplace')
    page.wait_for_function("() => document.querySelectorAll('[data-agent-card]').length >= 11")
    runs = {}
    for name, theme in (('reference', None), ('theme B', THEME_B), ('theme B dark', DARK_B)):
        if theme:
            page.evaluate("t => { for (const k in t) document.documentElement.style.setProperty(k, t[k]); }", theme)
        runs[name] = {r['key']: r for r in page.evaluate(PROBE)}
    b.close()
server.shutdown()

ok = True
ref = runs['reference']
steps = {f'step-{i}': px for i, px in enumerate((0, 2, 4, 8, 12, 16, 22, 32, 48, 64))}
for key, record in zip(t.KEYS, t.LOOKS):
    r = ref[key]
    want = t.look.clean(record)
    line = f"{key[-4:]} look={r['look']} border={r['border']} radius={r['radius']} padding={r['padding']} effect={r['effect'] or '-'} name={r['name_role']}"
    good = (('radius' not in want or r['radius'] == f"{steps[want['radius']]}px") and ('space' not in want or r['padding'] == f"{steps[want['space']]}px")
            and r['effect'] == (want.get('effect') or '') and r['name_role'] == want.get('text', {}).get('name', 'title'))
    moved = len({runs[n][key]['border'] for n in runs}) == 3 and all(runs[n][key]['look'] == r['look'] for n in runs)
    ok &= good and moved
    print(('PASS ' if good and moved else 'FAIL ') + line + f" | theme B {runs['theme B'][key]['border']} | dark {runs['theme B dark'][key]['border']}")
leak = len({(ref[k]['border'], ref[k]['radius'], ref[k]['padding']) for k in t.KEYS[:9]}) == 9
inline = [r['style_attr'] for r in ref.values() if r['style_attr'] and not all(part.strip().split(':')[0].strip() in ('--accent', '--radius', '--space', '--effect') for part in r['style_attr'].split(';') if part.strip())]
print(f'ten different looks: {leak} · CSP violations: {len(violations)} · style set only as menu properties: {not inline}')
ok &= leak and not violations and not inline
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
