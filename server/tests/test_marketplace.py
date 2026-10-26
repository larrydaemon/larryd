"""THE AGENT MARKETPLACE, run as it really runs: in the sandbox, from its locker folder."""
import json
import re
import unittest

from _here import APP
from core_engine import sandbox

FOLDER = APP / 'agents' / 'marketplace'


def card(**over):
    base = {'key': 'MAGT_AAAAAAAAAAAA_0001', 'number': '1', 'class': 'MARK I AGENT (NORMAL)', 'name': 'The Agent Marketplace',
            'screen': 'larryd/agnt/home', 'product': 'LARRYD', 'product_slug': 'larryd', 'module': 'AGENT', 'pitch': 'Every agent, one toggle.',
            'developer': 'Positive Feedback', 'price': '0', 'image_dam_key': '', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL',
            'status': 'APPROVED', 'hired': False, 'hireable': True, 'reason': ''}
    base.update(over)
    return base


def run(given):
    state, answer, reason = sandbox.run(FOLDER, 'agent.py', given)
    assert state == 'DONE', reason
    return answer


class CollectionTest(unittest.TestCase):
    def test_one_card_as_the_original_lays_it_out(self):
        out = run({'do': 'collection', 'cards': [card()]})
        self.assertEqual(out['total'], 1)
        self.assertEqual(out['hired'], 0)
        self.assertEqual(out['cards'], [{
            'key': 'MAGT_AAAAAAAAAAAA_0001', 'number': 1, 'class': 'MARK I AGENT (NORMAL)', 'name': 'The Agent Marketplace',
            'initials': 'TA', 'image_dam_key': '', 'product': 'LARRYD', 'module': 'AGENT', 'pitch': 'Every agent, one toggle.',
            'developer': 'Positive Feedback', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL',
            'screen': 'larryd/agnt/home', 'sends_to': '', 'data_sent': '', 'rate': 0,
            'hired': False, 'hireable': True, 'needs': '', 'art': '', 'wears': '', 'rating': None, 'developer_site': '', 'offline': False, 'subscription': False}])

    def test_counts_and_order_come_from_the_cards(self):
        cards = [card(key='K3', number='3', hired=True), card(key='K1', number='1'), card(key='K2', number='', name='PF Night Watch')]
        out = run({'do': 'collection', 'cards': cards})
        self.assertEqual([c['key'] for c in out['cards']], ['K1', 'K3', 'K2'])   # by number; unnumbered last
        self.assertEqual((out['total'], out['hired']), (3, 1))
        self.assertEqual(out['cards'][2]['number'], None)
        self.assertEqual(out['cards'][2]['initials'], 'NW')

    def test_values_never_words(self):
        paid = run({'do': 'collection', 'cards': [card(price='12', hireable=False, needs='PACE SHIFT')]})['cards'][0]
        self.assertEqual((paid['rate'], paid['hireable'], paid['needs']), (12, False, 'PACE SHIFT'))

    def test_filters_are_the_cards_own_values(self):
        cards = [card(key='A', product='INVOICE MAPS', module='CONTACTS', type='DEVELOPER', residency='EXTERNAL'), card(key='B')]
        f = run({'do': 'collection', 'cards': cards})['filters']
        self.assertEqual(f, {'product': ['INVOICE MAPS', 'LARRYD'], 'module': ['AGENT', 'CONTACTS'], 'type': ['DEVELOPER', 'OFF-THE-SHELF'],
                             'residency': ['EXTERNAL', 'INTERNAL'], 'class': ['MARK I AGENT (NORMAL)']})

    def test_an_empty_collection_is_empty(self):
        out = run({'do': 'collection', 'cards': []})
        self.assertEqual(out.pop('view')['css'], (FOLDER / 'card.css').read_text())
        self.assertEqual(out, {'cards': [], 'total': 0, 'hired': 0, 'shown': 0,
                         'filters': {'product': [], 'module': [], 'type': [], 'residency': [], 'class': []}})


class ReportTest(unittest.TestCase):
    def test_the_run_delivers_the_collection_report(self):
        out = run({'do': 'report', 'cards': [card(hired=True), card(key='K2')]})
        self.assertEqual(out, {'delivery': '2 agents in the collection · 1 hired', 'total': 2, 'hired': 1})
        self.assertEqual(run({'do': 'report', 'cards': [card()]})['delivery'], '1 agent in the collection · 0 hired')


class RefusesTest(unittest.TestCase):
    def test_an_unknown_ask_fails(self):
        state, _answer, reason = sandbox.run(FOLDER, 'agent.py', {'do': 'anything'})
        self.assertEqual(state, 'FAILED')
        self.assertEqual(reason, 'exit 1')   # an agent's own words never reach a reason (data stays in wid)


if __name__ == '__main__':
    unittest.main()


class Gives(unittest.TestCase):
    """The marketplace answers only what its manifest's "gives" names (the runtime refuses anything else)."""
    def test_both_answers_stay_inside_gives(self):
        gives = set(json.loads((FOLDER / 'agent.json').read_text())['gives'])
        cards = [{'key': 'MAGT_1', 'name': 'A', 'hired': True, 'product': 'LARRYD', 'module': 'Agents'}]
        for do in ('collection', 'report'):
            state, answer, reason = sandbox.run(FOLDER, 'agent.py', {'do': do, 'cards': cards})
            self.assertEqual(state, 'DONE', reason)
            self.assertLessEqual(set(answer), gives, do)


class TheAgentsOwnView(unittest.TestCase):
    """The card lives in the agent (the owner, 2026-10-07): the collection carries its own view, the whole panel's markup
    (one card per card handed, every value escaped, a hire button per card, no form) and its own sheet (card.css)."""
    def test_one_card_per_card_handed_and_its_own_sheet(self):
        cards = [card(key='K1', name='Weekly <Summary>', hired=True, price='3'), card(key='K2', number='2', name='Action Items')]
        v = run({'do': 'collection', 'cards': cards})['view']
        self.assertEqual(set(v), {'html', 'css'})
        self.assertEqual(v['css'], (FOLDER / 'card.css').read_text())
        self.assertEqual(v['html'].count('<article class="agent-card'), 2)
        self.assertIn('Weekly &lt;Summary&gt;', v['html'])
        self.assertNotIn('<Summary>', v['html'])
        self.assertIn('data-hire="K1" aria-pressed="true"', v['html'])
        self.assertIn('data-hire="K2" aria-pressed="false"', v['html'])
        self.assertIn('3 mTok', v['html'])
        self.assertNotIn('<form', v['html'])
        self.assertNotIn('total in network', v['html'])   # the platform's controller says the totals (the owner's final card, 2026-10-07)

    def test_the_marketplace_never_draws_itself(self):   # the runtime never hands it its own card; what it is handed is all it draws
        v = run({'do': 'collection', 'cards': [card(key='OTHER')]})['view']
        self.assertEqual(re.findall(r'data-agent="([^"]+)"', v['html']), ['OTHER'])

    def test_the_view_passes_the_runtimes_check(self):
        from core_engine import view
        self.assertEqual(view.refused(run({'do': 'collection', 'cards': [card(), card(key='K2')]})['view']), '')

    def test_the_sheet_is_in_the_agents_code_hash(self):   # FROST approves the sheet with the agent: a changed sheet is a changed agent
        import shutil, tempfile, pathlib
        from core_engine import locker
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp) / 'marketplace'
            shutil.copytree(FOLDER, copy, ignore=shutil.ignore_patterns('__pycache__'))
            before = locker._code_sha256(copy)
            (copy / 'card.css').write_text((copy / 'card.css').read_text() + '\n.x { }\n')
            self.assertNotEqual(before, locker._code_sha256(copy))


CDN = 'https://storage.googleapis.com/positivefeedback-cdn/themes'
THEMES = {'A37089573E6F': {'ground': f'{CDN}/0dd98026/images/dark/background.webp?v=1a2b3c4d',
                           'values': {'--active-color-01': '#76AAD9', '--active-color-09': '#041320', '--dock-glass': 'var(--glass)',
                                      '--glass': 'linear-gradient(135deg, color-mix(in srgb, var(--active-color-01) 18%, transparent) 0%, transparent 100%)',
                                      '--glass-filter': 'blur(16px)'}}}


def final(**over):
    return card(**{'key': 'K1', 'class': 'Mark III', 'wears': 'A37089573E6F', 'art': f'{CDN}/0dd98026/images/agent_card_larry.png?v=9f8e7d6c',
                   'developer_site': 'https://positivefeedback.ai', 'rating': '4.8', 'reviews': '212', **over})


class TheFinalCard(unittest.TestCase):
    """The card the owner approved in the lab (2026-10-07): each card in its own theme, its box's animation by its Mark, a star rating
    or a live hired count in its strip, a link to its developer, a still Simple view; found and sorted by the agent itself."""
    def view(self, cards, **given):
        return run({'do': 'collection', 'cards': cards, **given})

    def test_the_final_sheet_passes_the_runtimes_check_whole(self):   # @keyframes, animation, mask, color-mix, border-image, backdrop-filter, filter, @counter-style, counter()
        from core_engine import view
        sheet = (FOLDER / 'card.css').read_text()
        for must in ('@keyframes', 'animation:', 'mask:', 'color-mix(', 'border-image:', 'backdrop-filter:', 'filter: blur(', '@counter-style', 'counter('):
            self.assertIn(must, sheet)
        self.assertEqual(view.refused({'html': '', 'css': sheet}), '')
        self.assertNotIn('\\', sheet)
        self.assertNotIn('<', sheet)

    def test_a_dressed_collection_passes_the_runtimes_check(self):
        from core_engine import view
        for find in ({}, {'simple': True}):
            out = self.view([final(), final(key='K2', hired=True, **{'class': 'Mark I'})], themes=THEMES, find=find,
                            page={'logos': {'A37089573E6F': f'{CDN}/9b7c7c13/images/dark/logo_dock_01.png?v=77aa'}})
            self.assertEqual(view.refused(out['view']), '', find)
            self.assertEqual(set(out['view']), {'html', 'css'})

    def test_each_card_wears_its_theme_and_its_mark(self):
        v = self.view([final()], themes=THEMES)['view']
        self.assertIn('data-mark="3" data-wears="A37089573E6F"', v['html'])
        self.assertIn('<canvas class="mk-rain" aria-hidden="true"></canvas>', v['html'])   # Mark III: the rain's canvas, empty until the page drives it
        self.assertIn('.agent-card[data-wears="A37089573E6F"] .mk-frame, .agent-card[data-wears="A37089573E6F"].mk-on { --active-color-01: #76AAD9;', v['css'])
        self.assertIn(f'.agent-card[data-wears="A37089573E6F"] {{ --agent-ground: url("{CDN}/0dd98026/images/dark/background.webp?v=1a2b3c4d") }}', v['css'])
        self.assertIn(f'.agent-card[data-agent="K1"] .mk-back {{ --mk-art: url("{CDN}/0dd98026/images/agent_card_larry.png?v=9f8e7d6c") }}', v['css'])
        self.assertNotIn('<canvas', self.view([final(**{'class': 'Mark I'})])['view']['html'])

    def test_the_strip_a_rating_when_not_hired_the_hired_count_by_the_sheet(self):
        v = self.view([final()])['view']
        self.assertIn('<span class="mk-rating" data-part="rating">★ 4.8 (212)</span><span class="mk-count" data-part="number"></span>', v['html'])
        self.assertIn('.mk-count::before { content: "No. " counter(mk-hired, mk-three) }', v['css'])
        self.assertNotIn('mk-rating', self.view([final(rating='', reviews='')])['view']['html'])
        self.assertNotIn('mk-rating', self.view([final(rating='9', reviews='3')])['view']['html'])   # a score is 0 to 5

    def test_the_developers_site_is_a_link_only_when_plain_https(self):
        link = '<a class="mk-site" href="https://positivefeedback.ai" target="_blank" rel="noopener noreferrer">Positive Feedback</a>'
        self.assertIn(link, self.view([final()])['view']['html'])
        for site in ('', 'http://positivefeedback.ai', 'javascript:alert(1)', 'https://a.b/"onclick=', 'https://a b'):
            html = self.view([final(developer_site=site)])['view']['html']
            self.assertNotIn('<a ', html, site)
            self.assertIn('Developer · Positive Feedback', html)

    def test_the_simple_view_is_still_and_fetches_no_cat(self):
        v = self.view([final()], themes=THEMES, find={'simple': True}, page={'logos': {'A37089573E6F': f'{CDN}/9b7c7c13/images/dark/logo_dock_01.png'}})['view']
        self.assertIn('<section class="mk-panel mk-simple">', v['html'])
        for never in ('<canvas', '<img', 'mk-back'):
            self.assertNotIn(never, v['html'])
        self.assertIn('<span class="mk-logo"></span>', v['html'])
        self.assertNotIn('--agent-ground', v['css'].split('.mk-simple .toggle')[1])   # no background picture's address
        self.assertNotIn('--mk-art', v['css'].split('.mk-simple .toggle')[1])
        self.assertIn(f'.mk-simple .agent-card[data-wears="A37089573E6F"] {{ --mk-logo: url("{CDN}/9b7c7c13/images/dark/logo_dock_01.png") }}', v['css'])

    def test_found_and_sorted_by_the_agent(self):
        cards = [final(key='K1', number='1', name='Zed', product='Pace Shift', module='Images', hired=True, price='5', rating='3.1'),
                 final(key='K2', number='2', name='alpha', product='Invoice Maps', module='Operations', price='0', rating='4.9', **{'class': 'Mark I'}),
                 final(key='K3', number='3', name='Mid', product='LARRYD', module='Jobs', hired=True, price='2', rating='', **{'class': 'Mark II'})]
        names = lambda **find: [c['name'] for c in self.view(cards, find=find)['cards']]
        self.assertEqual(names(), ['Zed', 'alpha', 'Mid'])
        self.assertEqual(names(sort='name'), ['alpha', 'Mid', 'Zed'])
        self.assertEqual(names(sort='rating'), ['alpha', 'Zed', 'Mid'])
        self.assertEqual(names(sort='price'), ['alpha', 'Mid', 'Zed'])
        self.assertEqual(names(sort='mark'), ['alpha', 'Mid', 'Zed'])
        self.assertEqual(names(sort='bogus'), ['Zed', 'alpha', 'Mid'])
        self.assertEqual(names(q='PACE images'), ['Zed'])
        self.assertEqual(names(hired=True), ['Zed', 'Mid'])
        self.assertEqual(names(product='invoicemaps'), ['alpha'])
        self.assertEqual(names(product='Pace Shift', module='images'), ['Zed'])
        out = self.view(cards, find={'q': 'nothing here'})
        self.assertEqual((out['cards'], out['total'], out['hired'], out['shown']), ([], 3, 2, 0))   # the totals are the whole collection's

    def test_nothing_hostile_leaves_the_markup_or_the_sheet(self):
        from core_engine import view
        evil = final(key='K"><script>x</script>', name='<img src=x onerror=alert(1)>', pitch='</style><script>alert(2)</script>', developer='"onmouseover="x',
                     art='x") } body { display:none } /*', wears='A"] { } *')
        themes = {'AB12': {'ground': 'x") } * { color: red } /*', 'values': {'--a': 'red; } * { x: y', '--b}': 'x', '--ok': '#fff', 'color': 'red', '--u': 'url(x)'}},
                  'A"]{}': {'values': {'--z': '1'}}, 'CD34': 'junk', 'EF56': {'values': 'junk'}}
        v = self.view([evil], themes=themes, find={'simple': False}, page={'logos': 'junk'})['view']
        self.assertNotIn('<script', v['html'])
        self.assertNotIn('<img', v['html'])
        self.assertIn('data-wears=""', v['html'])
        made = v['css'][len((FOLDER / 'card.css').read_text()):]
        self.assertEqual(made, '.agent-card[data-wears="AB12"] .mk-frame, .agent-card[data-wears="AB12"].mk-on { --ok: #fff; }\n')
        self.assertEqual(run({'do': 'collection', 'cards': [card()], 'themes': 'junk', 'find': 'junk', 'page': 'junk'})['shown'], 1)   # a wrong shape is nothing, never a crash
        self.assertEqual(view.refused(v), '')


P = '/larryd/int/en/app/agnt/home'
K = 'site=9b7c7c13&mode=dark'   # the page's other words, kept on every link (the page builds its links; the agent never does)


def links(**now):
    def at(**change):
        d = {**now, **change}
        return P + '?' + K + ''.join(f'&{k}={v}' for k, v in d.items() if v != '')
    return {'mine_on': at(mine='1'), 'mine_off': at(mine=''), 'view_simple': at(view='simple'), 'view_animated': at(view=''), 'product_off': at(product='', module=''),
            'product': {slug: at(product=slug, module='') for slug in ('invoicemaps', 'agencymgmt', 'paceshift', 'larryd')}, 'module_off': at(module=''),
            'module': {m: at(module=m) for m in ('Contacts', 'Invoices', 'Locations', 'Operations')},
            'sort': {k: at(sort='' if k == 'number' else k) for k in ('number', 'name', 'product', 'mark', 'rating', 'price')}, 'search': P, 'reset': at(q='')}


def page(**now):
    return {'path': P, 'links': links(**now), 'search': {'site': '9b7c7c13', 'mode': 'dark', **{k: v for k, v in now.items() if k != 'q'}},
            'products': [['invoicemaps', 'Invoice Maps'], ['agencymgmt', 'Agency Mgmt'], ['paceshift', 'Pace Shift'], ['larryd', 'LARRYD']],
            'modules': {'invoicemaps': ['Contacts', 'Invoices', 'Locations', 'Operations'], 'larryd': ['Agents', 'Models', 'Logs', 'Jobs']}}


class TheAgentsOwnController(unittest.TestCase):
    """The controller above the cards is the agent's own (the owner, 2026-10-07: "keep it all in the agent, outside the core"), drawn with the
    platform's controller classes; every link is the page's own, as given (page.links), never built by the agent."""
    CARDS = [final(key='K1', number='1', product='Pace Shift', module='Images', hired=True), final(key='K2', number='2', product='Invoice Maps', module='Operations'),
             final(key='K3', number='3', product='Invoice Maps', module='Contacts'), final(key='K4', number='4', product='LARRYD', module='Jobs')]

    def html(self, find=None, given=None, **now):
        return run({'do': 'collection', 'cards': self.CARDS, 'find': find or {}, 'page': page(**now) if given is None else given})['view']['html']

    def test_no_links_no_controller(self):
        for given in ({}, {'path': P}, {'path': P, 'links': 'junk'}, {'path': P, 'links': {}}, {'path': P, 'links': {'search': ''}}, {'links': {'mine_on': P}}):
            self.assertNotIn('mk-ctl', self.html(given=given), given)
        self.assertNotIn('mk-ctl', run({'do': 'collection', 'cards': self.CARDS})['view']['html'])

    def test_its_shape_is_the_platforms_controller(self):
        h = self.html()
        for part in ('<div class="sub-controller-box wl-glass mk-ctl"><div class="wl-panel"><div class="sub-contacts-header"><div class="sub-controller-box"><div class="sub-controller">',
                     '<div class="emphasis">Controller</div>', '<div class="wl-cols"><div class="wl-col--1"><div class="subtitle">Agents</div><div class="emphasis">4 total in network</div>',
                     '<div class="label wl-label">Hired agents (1)</div>', '<div class="wl-divider"></div><div class="wl-col--3"><div class="subtitle">Quick search</div>',
                     f'<form method="get" action="{P}" class="sub-search-form"><input type="hidden" name="site" value="9b7c7c13"><input type="hidden" name="mode" value="dark">',
                     '<input type="text" name="q" class="sub-search-input" placeholder="Find…" value="">', '<button class="btn btn--small" type="submit">Search</button>',
                     '<div class="label wl-label">Sort by</div><div class="annotation">'):
            self.assertIn(part, h)
        self.assertLess(h.index('mk-ctl'), h.index('mk-panel'))   # above the cards
        self.assertNotIn(' style=', h)
        self.assertNotIn('Reset', h)

    def test_every_group_shows_its_selected_one_and_every_link_is_the_pages_own(self):
        h = self.html()
        base = (P + '?' + K).replace('&', '&amp;')
        self.assertIn(f'<a class="btn btn--small" href="{base}" aria-current="true">All agents</a><a class="btn btn--small" href="{base}&amp;mine=1">Hired agents</a>', h)
        self.assertIn(f'<a class="btn btn--small" href="{base}" aria-current="true">Animated</a><a class="btn btn--small" href="{base}&amp;view=simple">Simple</a>', h)
        self.assertIn(f'<a class="btn btn--small" href="{base}" aria-current="true">Off</a><a class="btn btn--small" href="{base}&amp;product=invoicemaps">Invoice Maps</a>', h)
        self.assertEqual(re.findall(r'>([^<]+)</a>', h[h.index('Product level'):h.index('wl-divider')]), ['Off', 'Invoice Maps', 'Agency Mgmt', 'Pace Shift', 'LARRYD'])   # the page's list, its order
        self.assertNotIn('Module level', h)
        self.assertEqual(h.count('aria-current="true"'), 4)   # all/mine, view, product level, the sort
        given = set(json.dumps(links()).replace('&', '&amp;').split('"'))
        for href in re.findall(r'href="([^"]+)"', h[:h.index('mk-panel')]):
            self.assertIn(href, given, href)   # never one of the agent's own making

    def test_a_picked_product_shows_its_modules(self):
        h = self.html(find={'product': 'invoicemaps', 'module': 'contacts'}, product='invoicemaps', module='Contacts')
        self.assertEqual(re.findall(r'>([^<]+)</a>', h[h.index('Module level'):h.index('wl-divider')]), ['Off', 'Contacts', 'Invoices', 'Locations', 'Operations'])
        self.assertIn('aria-current="true">Invoice Maps</a>', h)
        self.assertIn('aria-current="true">Contacts</a>', h)
        self.assertIn('module=Operations">Operations</a>', h)
        self.assertEqual(re.findall(r'data-agent="([^"]+)"', h), ['K3'])
        self.assertNotIn('Module level', self.html(find={'product': 'paceshift'}, product='paceshift'))   # a product with no modules given: no row

    def test_the_sort_is_little_links_the_picked_one_marked(self):
        base = (P + '?' + K).replace('&', '&amp;')
        h = self.html(find={'sort': 'rating'}, sort='rating')
        self.assertIn(f'<a class="emphasis mk-sorted" href="{base}&amp;sort=rating" aria-current="true">Rating</a>', h)
        self.assertIn(f'<a class="annotation" href="{base}">Number</a>', h)
        self.assertIn('aria-current="true">Number</a>', self.html())   # Number unless another is picked

    def test_a_search_is_kept_and_can_be_reset_and_hostile_words_stay_words(self):
        given = page(q='x')
        given['search'] = {'ok': '<b>', 'Bad Name': 'x', 'q': 'never twice'}
        given['links']['reset'] = P + '?ok=1'
        h = self.html(find={'q': '"><script>x</script>'}, given=given)
        self.assertNotIn('<script', h)
        self.assertIn('value="&quot;&gt;&lt;script&gt;x&lt;/script&gt;"', h)
        self.assertIn(f'<a class="btn btn--small" href="{P}?ok=1">Reset</a>', h)
        self.assertIn('<input type="hidden" name="ok" value="&lt;b&gt;">', h)
        self.assertNotIn('Bad', h)
        self.assertEqual(h.count('name="q"'), 1)

    def test_a_link_not_given_is_a_button_left_out(self):
        given = page()
        del given['links']['view_simple'], given['links']['sort'], given['links']['product']['larryd']
        h = self.html(given=given)
        for gone in ('>Simple<', 'Sort by', '>LARRYD</a>'):
            self.assertNotIn(gone, h)
        self.assertIn('>Animated</a>', h)

    def test_the_whole_view_passes_the_runtimes_check_when_the_path_is_told(self):
        from core_engine import view
        for find, now in (({}, {}), ({'product': 'invoicemaps', 'module': 'Operations', 'q': 'pace shift', 'sort': 'mark', 'hired': True, 'simple': True},
                                     {'product': 'invoicemaps', 'module': 'Operations', 'q': 'pace+shift', 'sort': 'mark', 'mine': '1', 'view': 'simple'})):
            out = run({'do': 'collection', 'cards': self.CARDS, 'find': find, 'page': {**page(**now), 'logos': {'A37089573E6F': '/themes/9b7c7c13/images/dark/logo_dock_01.png'}}, 'themes': THEMES})
            self.assertEqual(view.refused(out['view'], P), '', find)
            self.assertTrue(view.refused(out['view']))   # and never without it
        elsewhere = page()
        elsewhere['links']['mine_on'] = '/larryd/int/en/app/hire?x=1'   # a link the page did not mean: the runtime drops the whole view
        self.assertTrue(view.refused(run({'do': 'collection', 'cards': self.CARDS, 'page': elsewhere})['view'], P))


class TheOfflineCard(unittest.TestCase):
    """The owner's OFFLINE card (approved in the lab, 2026-10-07): the platform says which card is offline (card.offline); the toggle stays, dimmed and
    locked; Locked for Hire, Offline for the price, Informational only for Agent; the sheet dims the rest."""
    def html(self, **over):
        return run({'do': 'collection', 'cards': [final(**over)]})['view']

    def test_an_offline_card_is_locked_and_says_so(self):
        v = self.html(offline=True, price='12')
        h = v['html']
        self.assertIn('<article class="agent-card mk-offline"', h)
        self.assertIn('<div class="mk-hire"><button type="button" class="toggle" aria-disabled="true" aria-pressed="false" title="Locked"><span class="toggle__knob"></span></button>'
                      '<span class="mk-annotation">Locked</span></div>', h)
        self.assertNotIn('data-hire', h)          # the platform's hire never reaches an offline card
        self.assertNotIn('>Hire<', h)
        self.assertIn('<span class="mk-annotation mk-kind">Informational only</span><span class="mk-callout mk-price" data-part="price">Offline</span>', h)
        self.assertNotIn('mTok', h)
        self.assertNotIn('>Free<', h)
        for rule in ('.agent-card.mk-offline :is(.mk-name, .mk-info, .mk-flavour, .mk-credit, .mk-kind) { opacity: .35 }',
                     '.agent-card.mk-offline .toggle { cursor: default; pointer-events: none; opacity: .5 }',
                     '.agent-card.mk-offline .mk-price { color: var(--active-color-01, inherit); opacity: 1 }'):
            self.assertIn(rule, v['css'])

    def test_only_a_true_from_the_platform_is_offline(self):
        for value in (False, None, 'true', 'offline', 1, ''):
            h = self.html(offline=value)['html']
            self.assertNotIn('mk-offline', h, value)
            self.assertIn('data-hire="K1"', h, value)
            self.assertIn('<span class="mk-annotation mk-kind">Agent</span>', h)

    def test_an_offline_view_passes_the_runtimes_check(self):
        from core_engine import view
        self.assertEqual(view.refused(self.html(offline=True)), '')
        self.assertEqual(run({'do': 'collection', 'cards': [final(offline=True)]})['cards'][0]['offline'], True)


class TheMarkLine(unittest.TestCase):
    """The card says its Mark and nothing more (the owner's design: "the top should just be Mark I")."""
    def test_the_platforms_long_class_names_show_as_the_mark_alone(self):
        for cls, shown in (('MARK I AGENT (NORMAL)', 'Mark I'), ('MARK II SUPER AGENT (HARNESS)', 'Mark II'), ('MARK III QUANTUM AI (AGENTIC CODE)', 'Mark III'), ('MARK IV REPLICA (FULL-HUMAN REPLACEMENT)', 'Mark IV'), ('Mark II', 'Mark II')):
            h = run({'do': 'collection', 'cards': [final(**{'class': cls})]})['view']['html']
            self.assertIn(f'<span class="mk-caption" data-part="class">{shown}</span>', h, cls)
            for never in ('AGENT (NORMAL)', 'SUPER AGENT', 'QUANTUM', 'HARNESS', 'AGENTIC'):
                self.assertNotIn(never, h, cls)


class TheSubscriptionWord(unittest.TestCase):
    """An agent that comes with its product's subscription says Subscription where the price stands, for an account that has it (the owner, 2026-10-07);
    an account without it sees Offline and never the word (no purchase word on an offline card: Apple's review)."""
    def html(self, **over):
        return run({'do': 'collection', 'cards': [final(price='0', **over)]})['view']['html']

    def test_subscribed_it_says_subscription_and_can_be_hired(self):
        h = self.html(subscription=True, hired=True)
        self.assertIn('data-part="price">Subscription</span>', h)
        self.assertNotIn('>Free<', h)
        self.assertNotIn('mk-offline', h)
        self.assertIn('data-hire="K1"', h)

    def test_offline_never_says_subscription_and_a_free_agent_says_free(self):
        h = self.html(offline=True)
        self.assertIn('data-part="price">Offline</span>', h)
        self.assertNotIn('ubscri', h)
        self.assertIn('data-part="price">Free</span>', self.html())
        self.assertIn('data-part="price">Free</span>', self.html(subscription='true'))   # only a true from the platform
