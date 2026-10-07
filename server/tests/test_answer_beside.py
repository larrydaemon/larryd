"""THE ANSWER DOOR TAKES THE PAGE'S OWN, BESIDE THE CARDS (the owner's final card, 2026-10-07): a signed POST to /api/agents/answer may hand the agent find
(the controller's asks), themes (each theme a card may wear) and page (its path and its own links, its loaded logos, which theme each product wears, each theme's
picture); the harness dresses each card on that one call (wears, art, the agent's own manifest's developer_site) and keeps nothing. A GET still answers."""
import datetime
import json
import pathlib
import shutil
import tempfile
import unittest

from _here import APP
from core_engine import preview, signing, view
from test_preview import GOOD_CARD, KEY_A, KEY_B, SECRET, _agent, _zip
from web import app as host

CDN = 'https://storage.googleapis.com/positivefeedback-cdn/themes'
PATH = '/larryd/int/en/app/agnt/home'
THEME = 'A37089573E6F'


class TheAnswerDoor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', agents / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
        self.app = host.create_app(root, secret=SECRET, addresses={}, agents=agents, developer=True)
        self.client = self.app.test_client()
        self.client.get('/marketplace')
        for key, name, site in ((KEY_A, 'Scratch agent', 'https://positivefeedback.ai'), (KEY_B, 'Other agent', 'javascript:alert(1)')):
            r = self.client.post(f'/marketplace/place?key={key}', data=_zip(_agent(name, {**GOOD_CARD, 'developer_site': site})),
                                 content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
            self.assertIn(r.status_code, (200, 201), r.get_data(as_text=True)[:300])
        self.who = {'account': preview.ACCOUNT, 'scope': preview.SCOPE, 'member': preview.MEMBER, 'agent_key': preview.MARKETPLACE_KEY}

    def tearDown(self):
        self.tmp.cleanup()

    def headers(self, data):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return {'X-Office': signing.sign(SECRET, '/agents/answer', data, at), 'X-Office-At': at}

    def post(self, body, signed=None):
        return self.client.post('/api/agents/answer', json=body, headers=self.headers(body if signed is None else signed))

    def body(self, **more):
        return {**self.who, 'find': {'q': '', 'sort': 'name'}, 'themes': {THEME: {'ground': f'{CDN}/0dd98026/images/dark/background.webp', 'values': {'--active-color-01': '#76AAD9'}}},
                'page': {'path': PATH, 'links': {'search': PATH, 'mine_on': PATH + '?mine=1', 'mine_off': PATH, 'sort': {'name': PATH + '?sort=name', 'number': PATH}}, 'search': {'sort': 'name'}, 'wears': {'Invoice Maps': THEME}, 'arts': {THEME: f'{CDN}/0dd98026/images/agent_card_larry.png'},
                         'logos': {THEME: '/themes/9b7c7c13/images/dark/logo_dock_01.png'}}, **more}

    def test_a_get_still_answers_the_cards(self):
        r = self.client.get('/api/agents/answer', query_string=self.who, headers=self.headers(self.who))
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:300])
        out = r.get_json()
        self.assertEqual((out['total'], out['shown']), (2, 2))
        self.assertNotIn('mk-ctl', out['view']['html'])
        self.assertNotIn('data-wears="A', out['view']['html'])

    def test_a_signed_post_hands_find_themes_and_page_and_the_view_passes(self):
        r = self.post(self.body())
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:300])
        out = r.get_json()
        self.assertIn('view', out)   # passed the runtime's own check, with the page's path told
        self.assertEqual(view.refused(out['view'], PATH), '')
        h, css = out['view']['html'], out['view']['css']
        self.assertTrue(css.startswith((APP / 'agents' / 'marketplace' / 'card.css').read_text()))   # view.css = the final sheet, then the call's own rules
        self.assertIn('mk-ctl', h)
        self.assertEqual([c['name'] for c in out['cards']], ['Other agent', 'Scratch agent'])        # find.sort = name
        self.assertEqual(h.count(f'data-wears="{THEME}"'), 2)                                         # page.wears by the card's product
        self.assertIn(f'<img class="mk-art" src="{CDN}/0dd98026/images/agent_card_larry.png" alt="" loading="lazy">', h)   # page.arts by the theme worn
        self.assertIn(f'.agent-card[data-wears="{THEME}"] .mk-frame, .agent-card[data-wears="{THEME}"].mk-on {{ --active-color-01: #76AAD9; }}', css)
        self.assertEqual(h.count('<a class="mk-site" href="https://positivefeedback.ai" target="_blank" rel="noopener noreferrer">Scratch Dev</a>'), 1)   # the agent's own manifest's site
        self.assertNotIn('javascript:', h)                                                            # a site that is not plain https is no link
        self.assertEqual(h.count('<span class="mk-rating" data-part="rating">★ 4.8 (212)</span>'), 2)     # the design's sample on every card, until a rating system exists

    def test_the_body_is_signed_whole(self):
        body = self.body()
        tampered = {**body, 'find': {'q': 'x'}}
        self.assertEqual(self.post(tampered, signed=body).status_code, 401)
        self.assertEqual(self.client.post('/api/agents/answer', json=body).status_code, 401)

    def test_a_wrong_shape_is_left_out_never_a_crash(self):
        r = self.post(self.body(find='junk', themes=['junk'], page='junk'))
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:300])
        self.assertNotIn('mk-ctl', r.get_json()['view']['html'])
        r = self.post({**self.who, 'page': {'path': PATH, 'wears': 'junk', 'arts': 5, 'links': 'junk', 'search': 5, 'products': 'x', 'modules': []}})
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:300])

    def test_a_card_may_not_name_its_own_rating_theme_or_picture(self):   # only the page dresses a card; nothing is kept
        out = self.post(self.body()).get_json()
        for c in out['cards']:
            self.assertEqual((c['wears'], c['rating']), (THEME, ['4.8', 212]))   # the harness's one sample, whatever a card's own manifest says

    def test_the_simple_view_through_the_door(self):
        body = self.body()
        body['find'] = {'simple': True}
        out = self.post(body).get_json()
        self.assertIn('mk-simple', out['view']['html'])
        self.assertNotIn('<img', out['view']['html'])
        self.assertIn(f'.mk-simple .agent-card[data-wears="{THEME}"] {{ --mk-logo: url("/themes/9b7c7c13/images/dark/logo_dock_01.png") }}', out['view']['css'])


if __name__ == '__main__':
    unittest.main()


class AlwaysOn(TheAnswerDoor):
    """THE MARKETPLACE IS ALWAYS ON (the owner, 2026-10-07: "all people will get this turned on and no option to turn this agent off")."""
    def hire(self, key, on):
        return self.app.config['harness'].hire(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, key, on)

    def test_the_marketplace_cannot_be_let_go_and_another_agent_can(self):
        from core_engine import harness
        with self.assertRaises(harness.Refused) as no:
            self.hire(preview.MARKETPLACE_KEY, False)
        self.assertEqual((no.exception.status, no.exception.reason), (403, 'the marketplace is always on'))
        self.hire(KEY_A, True)
        self.hire(KEY_A, False)
        self.hire(preview.MARKETPLACE_KEY, True)   # hiring it (again) is never refused
        self.assertNotIn(f'data-agent="{preview.MARKETPLACE_KEY}"', self.post(self.body()).get_json()['view']['html'])   # and it never lists itself
