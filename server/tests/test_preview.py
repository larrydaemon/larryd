"""THE DEVELOPER'S MARKETPLACE: the runtime in developer mode, with no platform, answers itself (core_engine/preview.py);
the marketplace runs in the sandbox as it does on the server; a placed agent is a card with a hire toggle that hires and
lets go; a card the gate cannot show says why; a server (no developer mode) has no page at all."""
import io
import json
import pathlib
import re
import shutil
import tempfile
import unittest
import zipfile

from _here import APP
from core_engine import preview
from web import app as host

SECRET = 'scratch-secret-developer'
GOOD_CARD = {'class': 'MARK I AGENT (NORMAL)', 'pitch': 'Says hi.', 'price': '0', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL',
             'screen': 'cont/card', 'product': 'Invoice Maps', 'module': 'CONTACTS', 'developer': 'Scratch Dev', 'sends_to': '', 'data_sent': ''}
KEY_A, KEY_B, KEY_C = 'DAGT_000000000001_0001', 'DAGT_000000000002_0002', 'DAGT_000000000003_0003'


def _zip(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, body in files.items():
            z.writestr(name, body)
    return out.getvalue()


def _agent(name, card=None):
    manifest = {'name': name, 'entry': 'agent.py', 'about': 'a scratch agent', 'does': ['answer'], 'calls': [], 'reads': [],
                'run': {'do': 'answer', 'hands': []}, 'gives': ['delivery'], 'skills': []}
    if card is not None:
        manifest['card'] = card
    return {'agent.json': json.dumps(manifest).encode(), 'agent.py': b'import json, sys\nprint(json.dumps({"delivery": "hi"}))\n'}


class DeveloperMarketplace(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
        self.app = host.create_app(root, secret=SECRET, addresses={}, agents=self.agents, developer=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def page(self):
        r = self.client.get('/marketplace')
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:400])
        return r.get_data(as_text=True)

    def token(self, html):
        return re.search(r'name="token" value="([0-9a-f]+)"', html).group(1)

    def place(self, key, files):
        return self.client.post(f'/marketplace/place?key={key}', data=_zip(files), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})

    def toggle(self, html, key, on):
        r = self.client.post('/marketplace/hire', data={'token': self.token(html), 'key': key, 'value': 'on' if on else 'off'})
        self.assertEqual(r.status_code, 302)
        return r.headers['Location']

    def test_the_first_visit_places_the_marketplace_and_the_page_shows_it_hired(self):
        html = self.page()
        self.assertIn('THE AGENT MARKETPLACE', html)
        self.assertIn('1 total in network · 1 hired', html)
        self.assertIn('aria-pressed="true"', html)
        self.assertIn('No. 000', html)
        j = self.client.get('/marketplace.json').get_json()
        self.assertEqual((j['total'], j['hired'], j['cards'][0]['key'], j['not_shown']), (1, 1, preview.MARKETPLACE_KEY, []))

    def test_a_placed_agent_is_a_card_whose_toggle_hires_and_lets_go(self):
        r = self.place(KEY_A, _agent('Scratch agent', GOOD_CARD))
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True))
        self.assertEqual(r.get_json()['held']['name'], 'Scratch agent')
        html = self.page()
        for said in ('Scratch agent', 'Says hi.', 'Invoice Maps · CONTACTS', 'Developer · Scratch Dev', '▸ OFF-THE-SHELF ▸ INTERNAL', 'No. 001',
                     'lives on cont/card', f'data-agent="{KEY_A}" data-on="0"'):
            self.assertIn(said, html)
        self.assertIn('2 total in network · 1 hired', html)
        self.assertEqual(self.toggle(html, KEY_A, True), '/marketplace')
        j = self.client.get('/marketplace.json').get_json()
        self.assertEqual(j['hired'], 2)
        self.assertTrue(next(c for c in j['cards'] if c['key'] == KEY_A)['hired'])
        self.assertIn(f'data-agent="{KEY_A}" data-on="1"', self.page())
        self.toggle(self.page(), KEY_A, False)
        self.assertEqual(self.client.get('/marketplace.json').get_json()['hired'], 1)

    def test_the_same_agent_placed_again_replaces_itself(self):
        self.place(KEY_A, _agent('Scratch agent', GOOD_CARD))
        self.place(KEY_A, _agent('Scratch agent', {**GOOD_CARD, 'pitch': 'Says hello now.'}))
        j = self.client.get('/marketplace.json').get_json()
        self.assertEqual([c['pitch'] for c in j['cards'] if c['key'] == KEY_A], ['Says hello now.'])
        self.assertEqual(j['total'], 2)

    def test_a_card_the_gate_cannot_show_is_listed_with_why(self):
        self.place(KEY_B, _agent('No card'))
        self.place(KEY_C, _agent('Odd price', {**GOOD_CARD, 'price': '1.5'}))
        j = self.client.get('/marketplace.json').get_json()
        self.assertEqual({n['name']: n['why'] for n in j['not_shown']},
                         {'No card': 'the card names no screen', 'Odd price': 'the price is not a whole mTok rate'})
        self.assertEqual(j['total'], 1)
        html = self.page()
        self.assertIn('Not on the shelf', html)
        self.assertIn('Odd price: the price is not a whole mTok rate', html)

    def test_sends_to_is_on_the_card(self):
        self.place(KEY_A, _agent('Teller', {**GOOD_CARD, 'sends_to': 'An outside model', 'data_sent': 'the contact\'s city'}))
        html = self.page()
        self.assertIn('Sends data to An outside model: the contact&#39;s city', html)
        card = next(c for c in self.client.get('/marketplace.json').get_json()['cards'] if c['key'] == KEY_A)
        self.assertEqual((card['sends_to'], card['data_sent']), ('An outside model', 'the contact\'s city'))

    def test_a_stale_form_is_told_so_and_nothing_changes(self):
        self.page()
        r = self.client.post('/marketplace/hire', data={'token': 'not-the-token', 'key': preview.MARKETPLACE_KEY, 'value': 'off'})
        self.assertEqual(r.status_code, 302)
        self.assertIn('stale', r.headers['Location'])
        self.assertEqual(self.client.get('/marketplace.json').get_json()['hired'], 1)

    def test_a_refused_hire_is_said_on_the_page(self):
        html = self.page()
        where = self.toggle(html, 'DAGT_FFFFFFFFFFFF_FFFF', True)
        self.assertIn('could%20not%20be%20hired', where)
        self.assertIn('The agent could not be hired', self.client.get(where).get_data(as_text=True))

    def test_only_this_computers_browser_and_larryd_place_are_answered(self):
        self.assertEqual(self.client.get('/marketplace', headers={'Host': 'evil.example'}).status_code, 403)
        self.assertEqual(self.client.get('/marketplace.json', headers={'Host': 'evil.example'}).status_code, 403)
        self.assertEqual(self.client.post('/marketplace/hire', data={'token': 'x', 'key': preview.MARKETPLACE_KEY, 'value': 'off'},
                                          headers={'Origin': 'https://evil.example'}).status_code, 403)
        sneaky = _zip(_agent('Sneaky', GOOD_CARD))
        self.assertEqual(self.client.post(f'/marketplace/place?key={KEY_A}', data=sneaky, content_type='text/plain').status_code, 403)
        self.assertEqual(self.client.post(f'/marketplace/place?key={KEY_A}', data=sneaky, content_type='application/octet-stream').status_code, 403)
        self.assertEqual(self.client.get('/marketplace.json').get_json()['total'], 1)

    def test_the_marketplace_let_go_can_be_hired_again_from_the_page(self):
        html = self.page()
        self.toggle(html, preview.MARKETPLACE_KEY, False)
        r = self.client.get('/marketplace')
        self.assertEqual(r.status_code, 403)
        page = r.get_data(as_text=True)
        self.assertIn('Hire the marketplace again', page)
        self.toggle(page, preview.MARKETPLACE_KEY, True)
        self.assertIn('1 hired', self.page())


class LocalAnswers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
        from core_engine import store
        self.db = store.open_store(root)
        preview.hold_marketplace(self.db, self.agents)
        self.local = preview.Local(self.db, self.agents, root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_platforms_doors_in_the_platforms_shapes(self):
        status, cards = self.local.get('wid', '/agnt/cards', {})
        self.assertEqual(status, 200)
        (card,) = cards['cards']
        self.assertEqual((card['key'], card['status'], card['screen'], card['product_slug'], card['number']), (preview.MARKETPLACE_KEY, 'APPROVED', 'agnt/home', 'larryd', '0'))
        self.assertEqual(self.local.get('wid', '/agnt/hired', {'account': 'developer'}), (200, {'hired': []}))
        self.assertEqual(self.local.post('wid', '/agnt/hire', {'agent_key': preview.MARKETPLACE_KEY})[1]['already'], False)
        self.assertEqual(self.local.get('wid', '/agnt/hired', {})[1]['hired'][0]['on'], True)
        self.assertEqual(self.local.post('wid', '/agnt/unhire', {'agent_key': preview.MARKETPLACE_KEY}), (200, {'removed': 1}))
        self.assertEqual(self.local.get('cc', '/mtok/balance', {})[1]['subscriptions'], [{'agent_group': 'larryd'}])
        approved = self.local.get('fs', '/agents/approved', {})[1]['approved']
        self.assertEqual([a['agent_key'] for a in approved], [preview.MARKETPLACE_KEY])
        self.assertEqual(self.local.get('wid', '/jobs/queued', {}), (200, {'jobs': []}))
        self.assertEqual(self.local.get('so', '/dam/upload', {})[0], 404)

    def test_holding_the_marketplace_again_is_idempotent_and_survives_a_fresh_copy(self):
        self.assertEqual(preview.hold_marketplace(self.db, self.agents), preview.MARKETPLACE_KEY)
        (self.agents / 'marketplace' / 'agent.py').write_text((self.agents / 'marketplace' / 'agent.py').read_text() + '\n# a new release\n')
        self.assertEqual(preview.hold_marketplace(self.db, self.agents), preview.MARKETPLACE_KEY)
        from core_engine import locker
        self.assertEqual(locker.verify(self.db, self.agents, preview.MARKETPLACE_KEY), (True, ''))


class NoPageOnAServer(unittest.TestCase):
    def test_without_developer_mode_the_page_is_a_signed_door_like_any_other(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = host.create_app(tmp, secret=SECRET, addresses={})
            self.assertEqual(app.test_client().get('/marketplace').status_code, 401)
            self.assertEqual(app.test_client().post('/marketplace/place?key=' + KEY_A, data=b'x').status_code, 401)


if __name__ == '__main__':
    unittest.main()
