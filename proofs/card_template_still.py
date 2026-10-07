"""THE CARD TEMPLATE IN A STILL (frost-92's rc16 picture): a priced card's price on one line beside wrapping tags, every
art frame the same square, cards in a row the same height, and CRT visible with motion off (reduced motion). Real
headless Chromium, off-screen, on a scratch port; writes card_template_still.png beside this file's run folder.
Run with a Python that has Playwright: python proofs/card_template_still.py <out.png>"""
import json
import pathlib
import shutil
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / 'server' / 'tests'))
sys.path.insert(0, str(HERE / 'server' / 'runtime' / 'app'))
from _here import APP  # noqa: E402
from test_preview import GOOD_CARD, SECRET, _agent, _zip  # noqa: E402
from web import app as host  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PORT = 18433   # a scratch port, never a live one
OUT = sys.argv[1] if len(sys.argv) > 1 else 'card_template_still.png'
tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(APP / 'agents' / 'marketplace', tmp / 'agents' / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
app = host.create_app(tmp, secret=SECRET, addresses={}, agents=tmp / 'agents', developer=True)
c = app.test_client()
c.get('/marketplace')
for n, (name, card, record) in enumerate([
        ('WEEKLY SUMMARY', {**GOOD_CARD, 'price': '3', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL',
                            'pitch': "Your week's wins, blockers and next steps, written up as one clear summary."}, {'effect': 'crt'}),
        ('CALM', {**GOOD_CARD, 'price': '120'}, {'effect': 'wellness'}),
        ('PLAIN', GOOD_CARD, {'effect': 'none'})], 1):
    files = _agent(name, card)
    m = json.loads(files['agent.json'])
    m['look'] = record
    files['agent.json'] = json.dumps(m).encode()
    assert c.post(f'/marketplace/place?key=DAGT_00000000000{n}_000{n}', data=_zip(files), content_type='application/octet-stream',
                  headers={'X-Larryd-Place': '1'}).status_code in (200, 201)
server = make_server('127.0.0.1', PORT, app, threaded=True)
threading.Thread(target=server.serve_forever, daemon=True).start()

PROBE = """() => [...document.querySelectorAll('[data-agent-card]')].map(h => { const a = h.shadowRoot.querySelector('.agent-card');
  const price = a.querySelector('[data-part=price]'), frame = a.querySelector('.mk-frame'), r = frame.getBoundingClientRect();
  const lh = parseFloat(getComputedStyle(price).lineHeight) || price.getBoundingClientRect().height;
  return {name: a.querySelector('[data-part=name]').textContent, effect: a.dataset.effect || '', price: price.textContent,
          price_lines: Math.round(price.getBoundingClientRect().height / lh), frame_w: Math.round(r.width), frame_h: Math.round(r.height),
          card_h: Math.round(h.getBoundingClientRect().height), glow: getComputedStyle(a.querySelector('.mk-glow')).backgroundImage,
          scan: getComputedStyle(a.querySelector('.mk-scan')).backgroundImage, anim: getComputedStyle(a.querySelector('.mk-scan')).animationName} })"""
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={'width': 1300, 'height': 1000}, reduced_motion='reduce')
    page.goto(f'http://127.0.0.1:{PORT}/marketplace')
    page.wait_for_function("() => document.querySelectorAll('[data-agent-card]').length >= 4")
    page.wait_for_timeout(300)
    rows = page.evaluate(PROBE)
    page.screenshot(path=OUT, full_page=True)
    b.close()
server.shutdown()
ok = True
for r in rows:
    print(r['name'], '|', r['effect'] or '-', '|', r['price'], f"({r['price_lines']} line)", '| frame', r['frame_w'], 'x', r['frame_h'], '| card h', r['card_h'], '| still motion:', r['anim'])
crt = next(r for r in rows if r['effect'] == 'crt')
ok &= all(r['price_lines'] == 1 for r in rows)
ok &= all(r['frame_w'] == r['frame_h'] for r in rows) and len({r['frame_h'] for r in rows}) == 1
ok &= len({r['card_h'] for r in rows}) == 1
ok &= crt['anim'] == 'none' and crt['glow'] != 'none' and 'repeating-linear-gradient' in crt['scan']
print('price on one line, one frame shape, one row height, CRT drawn with motion off:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
