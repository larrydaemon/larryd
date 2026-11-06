"""THE AGENT MARKETPLACE, run as it really runs: in the sandbox, from its locker folder. A controller at the top and a grid of cards below,
nothing more (the owner 2026-11-03: "the marketplace just makes the marketplace / has a controler at the top and a grid of cards below..
nothing more than that"); each card a placeholder the platform fills with its one agent card ("larryd should just have the agent code and
data ... our endpoint dynamically generates the card from dynamic data / no other info from larryd")."""
import json
import re
import unittest

from _here import APP
from core_engine import sandbox

FOLDER = APP / 'agents' / 'marketplace'
SHEET = FOLDER / 'marketplace.css'


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
    def test_one_card_as_data_alone(self):
        out = run({'do': 'collection', 'cards': [card()]})
        self.assertEqual((out['total'], out['hired'], out['shown']), (1, 0, 1))
        self.assertEqual(out['cards'], [{'key': 'MAGT_AAAAAAAAAAAA_0001', 'number': 1, 'name': 'The Agent Marketplace', 'class': 'MARK I AGENT (NORMAL)',
                                         'product': 'LARRYD', 'module': 'AGENT', 'hired': False, 'hireable': True, 'offline': False}])   # nothing of a card's look

    def test_counts_and_order_come_from_the_cards(self):
        cards = [card(key='MAGT_KEY3', number='3', hired=True), card(key='MAGT_KEY1', number='1'), card(key='MAGT_KEY2', number='', name='PF Night Watch')]
        out = run({'do': 'collection', 'cards': cards})
        self.assertEqual([c['key'] for c in out['cards']], ['MAGT_KEY1', 'MAGT_KEY3', 'MAGT_KEY2'])   # by number; unnumbered last
        self.assertEqual((out['total'], out['hired']), (3, 1))
        self.assertIsNone(out['cards'][2]['number'])

    def test_filters_are_the_cards_own_values(self):
        cards = [card(key='MAGT_A', product='INVOICE MAPS', module='CONTACTS', type='DEVELOPER', residency='EXTERNAL'), card(key='MAGT_B')]
        self.assertEqual(run({'do': 'collection', 'cards': cards})['filters'],
                         {'product': ['INVOICE MAPS', 'LARRYD'], 'module': ['AGENT', 'CONTACTS'], 'type': ['DEVELOPER', 'OFF-THE-SHELF'],
                          'residency': ['EXTERNAL', 'INTERNAL'], 'class': ['MARK I AGENT (NORMAL)']})

    def test_an_empty_collection_is_empty(self):
        out = run({'do': 'collection', 'cards': []})
        self.assertEqual(out.pop('view'), {'html': '<div class="mk-grid"></div>', 'css': SHEET.read_text()})
        self.assertEqual(out, {'cards': [], 'total': 0, 'hired': 0, 'shown': 0, 'filters': {'product': [], 'module': [], 'type': [], 'residency': [], 'class': []}})

    def test_only_a_true_from_the_platform_is_offline(self):
        for value, said in ((True, True), (False, False), (None, False), ('true', False), (1, False)):
            self.assertEqual(run({'do': 'collection', 'cards': [card(offline=value)]})['cards'][0]['offline'], said, value)

    def test_found_and_sorted_by_the_agent(self):
        cards = [card(key='MAGT_KEY1', number='1', name='Zed', product='Pace Shift', module='Images', hired=True, price='5', **{'class': 'Mark III'}),
                 card(key='MAGT_KEY2', number='2', name='alpha', product='Invoice Maps', module='Operations', price='0', **{'class': 'Mark I'}),
                 card(key='MAGT_KEY3', number='3', name='Mid', product='LARRYD', module='Jobs', hired=True, price='2', **{'class': 'Mark II'})]
        names = lambda **find: [c['name'] for c in run({'do': 'collection', 'cards': cards, 'find': find})['cards']]
        self.assertEqual(names(), ['Zed', 'alpha', 'Mid'])
        self.assertEqual(names(sort='name'), ['alpha', 'Mid', 'Zed'])
        self.assertEqual(names(sort='price'), ['alpha', 'Mid', 'Zed'])
        self.assertEqual(names(sort='mark'), ['alpha', 'Mid', 'Zed'])
        self.assertEqual(names(sort='bogus'), ['Zed', 'alpha', 'Mid'])
        self.assertEqual(names(q='PACE images'), ['Zed'])
        self.assertEqual(names(hired=True), ['Zed', 'Mid'])
        self.assertEqual(names(product='invoicemaps'), ['alpha'])
        self.assertEqual(names(product='Pace Shift', module='images'), ['Zed'])
        out = run({'do': 'collection', 'cards': cards, 'find': {'q': 'nothing here'}})
        self.assertEqual((out['cards'], out['total'], out['hired'], out['shown']), ([], 3, 2, 0))   # the totals are the whole collection's


class ReportTest(unittest.TestCase):
    def test_the_run_delivers_the_collection_report(self):
        self.assertEqual(run({'do': 'report', 'cards': [card(hired=True), card(key='MAGT_KEY2')]}), {'delivery': '2 agents in the collection · 1 hired', 'total': 2, 'hired': 1})
        self.assertEqual(run({'do': 'report', 'cards': [card()]})['delivery'], '1 agent in the collection · 0 hired')


class RefusesTest(unittest.TestCase):
    def test_an_unknown_ask_fails(self):
        state, _answer, reason = sandbox.run(FOLDER, 'agent.py', {'do': 'anything'})
        self.assertEqual((state, reason), ('FAILED', 'exit 1'))   # an agent's own words never reach a reason (data stays in wid)


class Gives(unittest.TestCase):
    """The marketplace answers only what its manifest's "gives" names (the runtime refuses anything else); its manifest carries no look."""
    def test_both_answers_stay_inside_gives(self):
        manifest = json.loads((FOLDER / 'agent.json').read_text())
        self.assertNotIn('look', manifest)
        for do in ('collection', 'report'):
            self.assertLessEqual(set(run({'do': do, 'cards': [card(hired=True)]})), set(manifest['gives']), do)


class TheGrid(unittest.TestCase):
    """THE GRID OF CARDS: one placeholder per card handed, in order, full, or mini in the Simple view; nothing of a card drawn here."""
    def test_one_placeholder_per_card_in_order(self):
        cards = [card(key='MAGT_KEY2', number='2', name='Weekly <Summary>'), card(key='MAGT_KEY1', number='1')]
        v = run({'do': 'collection', 'cards': cards})['view']
        self.assertEqual(v, {'html': '<div class="mk-grid"><div data-inject="agent_card" data-agent="MAGT_KEY1" data-size="full"></div>'
                                     '<div data-inject="agent_card" data-agent="MAGT_KEY2" data-size="full"></div></div>', 'css': SHEET.read_text()})
        self.assertNotIn('Summary', v['html'])   # no value of a card in the markup: the platform draws it

    def test_the_org_chart_view_is_mini_cards(self):   # the owner 2026-11-03: "the org chart for now will just be the mini cards"; the old Simple view is gone
        h = run({'do': 'collection', 'cards': [card()], 'find': {'orgchart': True}})['view']['html']
        self.assertEqual(h, '<div class="mk-grid mk-orgchart"><div data-inject="agent_card" data-agent="MAGT_AAAAAAAAAAAA_0001" data-size="mini"></div></div>')

    def test_a_key_that_is_not_plainly_a_key_stands_nowhere(self):
        h = run({'do': 'collection', 'cards': [card(key='K"><script>x</script>'), card(key='MAGT_OK_0001')]})['view']['html']
        self.assertNotIn('<script', h)
        self.assertEqual(re.findall(r'data-agent="([^"]+)"', h), ['MAGT_OK_0001'])

    def test_the_sheet_lays_out_and_draws_no_card(self):
        sheet = SHEET.read_text()
        for never in ('agent-card', 'mk-frame', 'pf-card', '@keyframes', 'url('):
            self.assertNotIn(never, sheet)
        from core_engine import view
        self.assertEqual(view.refused(run({'do': 'collection', 'cards': [card(), card(key='MAGT_KEY2')]})['view']), '')

    def test_the_sheet_is_in_the_agents_code_hash(self):   # FROST approves the sheet with the agent: a changed sheet is a changed agent
        import shutil, tempfile, pathlib
        from core_engine import locker
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp) / 'marketplace'
            shutil.copytree(FOLDER, copy, ignore=shutil.ignore_patterns('__pycache__'))
            before = locker._code_sha256(copy)
            (copy / 'marketplace.css').write_text((copy / 'marketplace.css').read_text() + '\n.x { }\n')
            self.assertNotEqual(before, locker._code_sha256(copy))


P = '/larryd/int/en/app/agnt/home'
K = 'site=9b7c7c13&mode=dark'   # the page's other words, kept on every link (the page builds its links; the agent never does)


def links(**now):
    def at(**change):
        d = {**now, **change}
        return P + '?' + K + ''.join(f'&{k}={v}' for k, v in d.items() if v != '')
    return {'mine_on': at(mine='1'), 'mine_off': at(mine=''), 'view_card': at(view=''), 'view_orgchart': at(view='orgchart'), 'product_off': at(product='', module=''),
            'product': {slug: at(product=slug, module='') for slug in ('invoicemaps', 'agencymgmt', 'paceshift', 'larryd')}, 'module_off': at(module=''),
            'module': {m: at(module=m) for m in ('Contacts', 'Invoices', 'Locations', 'Operations')},
            'sort': {k: at(sort='' if k == 'number' else k) for k in ('number', 'name', 'product', 'mark', 'price')}, 'search': P, 'reset': at(q='')}


def page(**now):
    return {'path': P, 'links': links(**now), 'search': {'site': '9b7c7c13', 'mode': 'dark', **{k: v for k, v in now.items() if k != 'q'}},
            'products': [['invoicemaps', 'Invoice Maps'], ['agencymgmt', 'Agency Mgmt'], ['paceshift', 'Pace Shift'], ['larryd', 'LARRYD']],
            'modules': {'invoicemaps': ['Contacts', 'Invoices', 'Locations', 'Operations'], 'larryd': ['Agents', 'Models', 'Logs', 'Jobs']}}


class TheController(unittest.TestCase):
    """THE CONTROLLER AT THE TOP, drawn with the platform's controller classes; every link is the page's own, as given (page.links)."""
    CARDS = [card(key='MAGT_KEY1', number='1', product='Pace Shift', module='Images', hired=True), card(key='MAGT_KEY2', number='2', product='Invoice Maps', module='Operations'),
             card(key='MAGT_KEY3', number='3', product='Invoice Maps', module='Contacts'), card(key='MAGT_KEY4', number='4', product='LARRYD', module='Jobs')]

    def html(self, find=None, given=None, **now):
        return run({'do': 'collection', 'cards': self.CARDS, 'find': find or {}, 'page': page(**now) if given is None else given})['view']['html']

    def test_no_links_no_controller(self):
        for given in ({}, {'path': P}, {'path': P, 'links': 'junk'}, {'path': P, 'links': {}}, {'path': P, 'links': {'search': ''}}, {'links': {'mine_on': P}}):
            self.assertNotIn('mk-ctl', self.html(given=given), given)

    def test_the_controller_then_the_grid_nothing_more(self):
        h = self.html()
        for part in ('<div class="sub-controller-box wl-glass mk-ctl"><div class="wl-panel"><div class="sub-contacts-header"><div class="sub-controller-box"><div class="sub-controller">',
                     '<div class="emphasis">Controller</div>', '<div class="wl-cols"><div class="wl-col--1"><div class="subtitle">Agents</div><div class="emphasis">1 hired · 4 total in network</div>',
                     '<div class="label wl-label">Hired agents</div>', '<div class="wl-divider"></div><div class="wl-col--3"><div class="subtitle">Quick search</div>',
                     f'<form method="get" action="{P}" class="sub-search-form"><input type="hidden" name="site" value="9b7c7c13"><input type="hidden" name="mode" value="dark">',
                     '<input type="text" name="q" class="sub-search-input" placeholder="Find…" value="">', '<button class="btn btn--small" type="submit">Search</button>',
                     '<div class="label wl-label">Sort by</div><div class="annotation">'):
            self.assertIn(part, h)
        self.assertTrue(h.startswith('<div class="sub-controller-box wl-glass mk-ctl">'))
        self.assertTrue(h.endswith('</div></div></div></div></div></div><div class="mk-grid">' + ''.join(
            f'<div data-inject="agent_card" data-agent="MAGT_KEY{n}" data-size="full"></div>' for n in (1, 2, 3, 4)) + '</div>'))   # the grid right after, nothing else
        for never in (' style=', 'Reset', 'mk-title', 'mk-caption', 'mk-panel', 'Rating', 'Simple', 'Animated'):
            self.assertNotIn(never, h)

    def test_every_group_shows_its_selected_one_and_every_link_is_the_pages_own(self):
        h = self.html()
        base = (P + '?' + K).replace('&', '&amp;')
        self.assertIn(f'<a class="btn btn--small" href="{base}" aria-current="true">All agents</a><a class="btn btn--small" href="{base}&amp;mine=1">Hired agents</a>', h)
        self.assertIn(f'<a class="btn btn--small" href="{base}" aria-current="true">Card</a><a class="btn btn--small" href="{base}&amp;view=orgchart">Org chart</a>', h)
        self.assertIn(f'<a class="btn btn--small" href="{base}" aria-current="true">Off</a><a class="btn btn--small" href="{base}&amp;product=invoicemaps">Invoice Maps</a>', h)
        self.assertEqual(re.findall(r'>([^<]+)</a>', h[h.index('Product level'):h.index('wl-divider')]), ['Off', 'Invoice Maps', 'Agency Mgmt', 'Pace Shift', 'LARRYD'])
        self.assertNotIn('Module level', h)
        self.assertEqual(h.count('aria-current="true"'), 4)   # all/mine, view, product level, the sort
        given = set(json.dumps(links()).replace('&', '&amp;').split('"'))
        for href in re.findall(r'href="([^"]+)"', h):
            self.assertIn(href, given, href)   # never one of the agent's own making

    def test_a_picked_product_shows_its_modules(self):
        h = self.html(find={'product': 'invoicemaps', 'module': 'contacts'}, product='invoicemaps', module='Contacts')
        self.assertEqual(re.findall(r'>([^<]+)</a>', h[h.index('Module level'):h.index('wl-divider')]), ['Off', 'Contacts', 'Invoices', 'Locations', 'Operations'])
        self.assertIn('aria-current="true">Invoice Maps</a>', h)
        self.assertIn('aria-current="true">Contacts</a>', h)
        self.assertEqual(re.findall(r'data-agent="([^"]+)"', h), ['MAGT_KEY3'])
        self.assertNotIn('Module level', self.html(find={'product': 'paceshift'}, product='paceshift'))

    def test_the_sort_is_little_links_the_picked_one_marked(self):
        base = (P + '?' + K).replace('&', '&amp;')
        h = self.html(find={'sort': 'price'}, sort='price')
        self.assertIn(f'<a class="emphasis mk-sorted" href="{base}&amp;sort=price" aria-current="true">Price</a>', h)
        self.assertIn(f'<a class="annotation" href="{base}">Number</a>', h)
        self.assertIn('aria-current="true">Number</a>', self.html())

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
        del given['links']['view_orgchart'], given['links']['sort'], given['links']['product']['larryd']
        h = self.html(given=given)
        for gone in ('>Org chart<', 'Sort by', '>LARRYD</a>'):
            self.assertNotIn(gone, h)
        self.assertIn('>Card</a>', h)

    def test_the_whole_view_passes_the_runtimes_check_when_the_path_is_told(self):
        from core_engine import view
        for find, now in (({}, {}), ({'product': 'invoicemaps', 'module': 'Operations', 'q': 'pace shift', 'sort': 'mark', 'hired': True, 'orgchart': True},
                                     {'product': 'invoicemaps', 'module': 'Operations', 'q': 'pace+shift', 'sort': 'mark', 'mine': '1', 'view': 'orgchart'})):
            out = run({'do': 'collection', 'cards': self.CARDS, 'find': find, 'page': page(**now)})
            self.assertEqual(view.refused(out['view'], P), '', find)
            self.assertTrue(view.refused(out['view']))   # and never without it
        elsewhere = page()
        elsewhere['links']['mine_on'] = '/larryd/int/en/app/hire?x=1'   # a link the page did not mean: the runtime drops the whole view
        self.assertTrue(view.refused(run({'do': 'collection', 'cards': self.CARDS, 'page': elsewhere})['view'], P))


if __name__ == '__main__':
    unittest.main()
