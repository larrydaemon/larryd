"""EACH CARD WEARS ITS OWN AGENT'S LOOK, AND NOTHING ELSE: agents ship no CSS; the look is a record of names in the
agent's own approved manifest, attached by the runtime, cleaned against the one menu (schemas/look.json), carried on
the card as data-look and set by the card script only after a second check. Ten agents, ten looks, one page: no card
wears another's, no raw value reaches the page, the page carries no inline style at all."""
import json
import re
import shutil
import tempfile
import pathlib
import unittest

from _here import APP
from core_engine import look
from test_preview import GOOD_CARD, SECRET, _agent, _zip
from web import app as host

LOOKS = [
    {'accent': 'active-color-01', 'radius': 'step-0', 'space': 'step-1', 'effect': 'none'},
    {'accent': 'active-color-05', 'radius': 'step-1', 'space': 'step-2', 'effect': 'crt'},
    {'accent': 'active-color-07', 'radius': 'step-2', 'space': 'step-3', 'effect': 'wellness'},
    {'accent': 'active-color-08', 'radius': 'step-3', 'space': 'step-4', 'effect': 'glitch'},
    {'accent': 'active-color-09', 'radius': 'step-4', 'space': 'step-5', 'text': {'name': 'heading'}},
    {'accent': 'active-color-10', 'radius': 'step-5', 'space': 'step-6', 'text': {'price': 'title', 'pitch': 'caption'}},
    {'accent': 'active-color-11', 'radius': 'step-6', 'space': 'step-7'},
    {'accent': 'active-color-19', 'radius': 'step-7', 'space': 'step-8', 'effect': 'crt'},
    {'accent': 'active-color-23', 'radius': 'step-8', 'space': 'step-9', 'effect': 'wellness'},
    # hostile: raw values, markup, an unknown field and part: everything off the menu is dropped
    {'accent': 'red; background: url(//evil.example/x)', 'radius': '20px', 'space': 'step-4', 'effect': "glitch'></article><script>alert(1)</script>",
     'text': {'name': 'title', 'pitch': 'x;y', 'hack': 'body'}, 'shadow': 'step-1'},
]
KEYS = [f'DAGT_00000000{n:04d}_{n:04d}' for n in range(1, 11)]


class TenLooksOnePage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', agents / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
        self.client = host.create_app(root, secret=SECRET, addresses={}, agents=agents, developer=True).test_client()
        self.client.get('/marketplace')
        for n, (key, record) in enumerate(zip(KEYS, LOOKS)):
            files = _agent(f'LOOK {n + 1:02d}', GOOD_CARD)
            manifest = json.loads(files['agent.json'])
            manifest['look'] = record
            files['agent.json'] = json.dumps(manifest).encode()
            r = self.client.post(f'/marketplace/place?key={key}', data=_zip(files), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
            self.assertIn(r.status_code, (200, 201), r.get_data(as_text=True)[:300])
        r = self.client.get('/marketplace')
        self.assertEqual(r.status_code, 200)
        self.html, self.headers = r.get_data(as_text=True), r.headers

    def tearDown(self):
        self.tmp.cleanup()

    def cards(self):
        return dict(re.findall(r'<article class="agent-card[^"]*" data-agent="([^"]+)"[^>]*data-look=\'([^\']*)\'', self.html))

    def test_each_card_wears_its_own_agents_record(self):
        cards = self.cards()
        for key, record in zip(KEYS, LOOKS):
            self.assertEqual(json.loads(cards[key]), look.clean(record), key)
        self.assertEqual(len({cards[k] for k in KEYS}), 10)   # ten different looks

    def test_the_hostile_record_keeps_only_menu_names(self):
        self.assertEqual(json.loads(self.cards()[KEYS[9]]), {'space': 'step-4', 'text': {'name': 'title'}})
        for raw in ('evil.example', '20px', '<script>alert', 'alert(', 'x;y', 'hack', '"shadow"'):
            self.assertNotIn(raw, self.html)

    def test_no_inline_style_anywhere_and_a_strict_policy(self):
        self.assertNotIn('style=', self.html)
        self.assertNotIn('<style', self.html)
        self.assertIn("style-src 'self'", self.headers['Content-Security-Policy'])
        self.assertNotIn('unsafe-inline', self.headers['Content-Security-Policy'])

    def test_every_card_is_in_its_own_shadow_root_with_the_template_sheet(self):
        self.assertEqual(self.html.count('<template shadowrootmode="open">'), self.html.count('<article class="agent-card'))
        self.assertEqual(self.html.count('href="/marketplace/agent_card.css"'), 10)   # the ten placed agents; the marketplace is the page, never a card inside itself

    def test_the_card_files_are_served_and_nothing_else(self):
        for name in ('agent_card.css', 'agent_card.js', 'page.css', 'reference_theme.css'):
            self.assertEqual(self.client.get(f'/marketplace/{name}').status_code, 200, name)
        self.assertEqual(self.client.get('/marketplace/app.py').status_code, 403)


class ALookIsNeverResolved(unittest.TestCase):
    def test_the_template_sheet_points_at_live_variables_only(self):
        sheet = (APP / 'web' / 'agent_card.css').read_text()
        self.assertNotRegex(sheet, r'#[0-9a-fA-F]{3,8}\b')   # no colour of its own: the theme's variables only
        self.assertIn('--accent: var(--active-color-01)', sheet)

    def test_the_script_sets_names_only_after_the_menu_check(self):
        js = (APP / 'web' / 'agent_card.js').read_text()
        self.assertIn("setProperty('--accent', 'var(--' + look.accent + ')')", js)
        self.assertNotIn('innerHTML', js)
        self.assertNotIn('cssText', js)
        self.assertNotIn('setAttribute(\'style\'', js)


class AnAgentNeverSpeaksForAnothersCard(unittest.TestCase):
    def test_a_look_the_answer_wrote_is_dropped(self):
        from core_engine import harness
        h = harness.Harness.__new__(harness.Harness)
        h.db, h.agents = None, None
        answer = {'cards': [{'key': 'K1', 'look': {'accent': 'active-color-08'}}, 'not a card']}
        import unittest.mock as m
        with m.patch.object(harness.locker, 'held', return_value=None):
            h._looks(answer, lambda key: (True, ''))
        self.assertEqual(answer['cards'][0], {'key': 'K1'})

    def test_an_unapproved_agents_look_is_not_shown(self):
        from core_engine import harness
        h = harness.Harness.__new__(harness.Harness)
        h.db, h.agents = None, None
        answer = {'cards': [{'key': 'K1'}]}
        import unittest.mock as m
        with m.patch.object(harness.locker, 'held', return_value={'folder': 'x'}), \
             m.patch.object(harness.locker, 'manifest', return_value={'look': {'accent': 'active-color-08'}}):
            h._looks(answer, lambda key: (False, 'not approved by FROST'))
            self.assertEqual(answer['cards'][0], {'key': 'K1'})
            h._looks(answer, lambda key: (True, ''))
            self.assertEqual(answer['cards'][0], {'key': 'K1', 'look': {'accent': 'active-color-08'}})


if __name__ == '__main__':
    unittest.main()


class TheTemplatesShape(unittest.TestCase):
    """frost-92's rc16 picture: the price wrapped beside the tags, CRT was invisible in a still, the frames differed."""
    sheet = (APP / 'web' / 'agent_card.css').read_text()

    def test_the_price_never_wraps_the_tags_do(self):
        self.assertIn('.mk-foot > [data-part="price"] { flex: none; white-space: nowrap }', self.sheet)
        self.assertIn('.mk-foot > [data-part="facts"] { flex: 1 1 auto; min-width: 0 }', self.sheet)

    def test_the_frame_is_one_fixed_shape(self):
        self.assertIn('.mk-frame { flex: none; width: 100%; aspect-ratio: 1 / 1;', self.sheet)

    def test_crt_shows_without_motion(self):
        self.assertIn('.agent-card[data-effect="crt"] .mk-glow { background: radial-gradient(', self.sheet)
        self.assertNotIn('var(--active-color-09) 28%', self.sheet)   # scanlines in the accent, seen on a dark frame
