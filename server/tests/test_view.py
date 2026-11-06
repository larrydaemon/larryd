"""AN AGENT'S OWN VIEW (the owner, 2026-10-07): passed on only when it holds nothing that runs or reaches out; else the
whole view is dropped and the cards stay."""
import unittest

from _here import APP  # noqa: F401
from core_engine import view

GOOD = {'html': '<section class="mk-panel"><button type="button" class="toggle" data-hire="K" aria-pressed="false"></button></section>',
        'css': '.mk-frame { background: url("https://storage.googleapis.com/positivefeedback-cdn/themes/x.png") }'}


class TheCheck(unittest.TestCase):
    def test_a_plain_view_passes(self):
        self.assertEqual(view.refused(GOOD), '')
        self.assertEqual(view.checked({'cards': [], 'view': GOOD}), ({'cards': [], 'view': GOOD}, ''))

    def test_each_refusal(self):
        for markup in ('<script>x</script>', '<SCRIPT src=a>', '<style>a{}</style>', '<link rel=stylesheet href=x>', '<iframe src=x>',
                       '<object data=x>', '<embed src=x>', '<a href="javascript:alert(1)">', '<form action=x>', '<svg/onload=a()>',
                       '<img src=x onerror="a()">', '<div ONCLICK=a()>', '<div style="color:red">', '<div id=x>',
                       '<img srcset="https://storage.googleapis.com/positivefeedback-cdn/a.png 1x">', '<button type=submit>',
                       '<span src="https://storage.googleapis.com/positivefeedback-cdn/a.png">', '<!-- x -->', '<!DOCTYPE html>',
                       '<math><mi>x</mi></math>', '<template><img src=x></template>', '<div data-x=1 href=y>'):
            self.assertTrue(view.refused({'html': markup, 'css': ''}), markup)
        for address in ('//evil.example/x.png', 'https://storage.googleapis.com.evil.com/positivefeedback-cdn/x.png',
                        'https://storage.googleapis.com/positivefeedback-cdn/../x.png', 'https://storage.googleapis.com/other-bucket/x.png',
                        'https://storage.googleapis.com/positivefeedback-cdn/%2e%2e/x.png', 'https://storage.googleapis.com/positivefeedback-cdn/a%2fb.png',
                        'http://storage.googleapis.com/positivefeedback-cdn/x.png', 'https://user@storage.googleapis.com/positivefeedback-cdn/x.png',
                        'https://storage.googleapis.com:444/positivefeedback-cdn/x.png', 'data:image/png;base64,AA', 'javascript:alert(1)',
                        'https://storage.googleapis.com/positivefeedback-cdn/a/./b.png'):
            self.assertFalse(view.cdn_address(address), address)
            self.assertTrue(view.refused({'html': f'<img src="{address}">', 'css': ''}), address)
            self.assertTrue(view.refused({'html': '', 'css': f'.a {{ background: url("{address}") }}'}), address)
        for sheet in ('@import url(x);', '@IMPORT "x";', '.a { width: expression(1) }', '.a { background: url(https://evil.example/x.png) }',
                      '.a { background: url( "//evil/x" ) }', ".a { background: url('data:image/png;base64,AA') }",
                      '.a { background: u\\72l(https://evil.example/x) }', '.a { background: \\75rl(x) }',
                      '.a { background: image-set("https://evil.example/x.png" 1x) }', '.a { background: -webkit-image-set(url(x) 1x) }',
                      '.a { src: src("x") }', '.a { behavior: url(x.htc) }', '.a { background: url(javascript:alert(1)) }',
                      '</style><script>', '.a { background: url(https://storage.googleapis.com/positivefeedback-cdn/a.png' ):
            self.assertTrue(view.refused({'html': '', 'css': sheet}), sheet)
        self.assertTrue(view.refused({'html': 'x' * (200 * 1024 + 1), 'css': ''}))
        self.assertTrue(view.refused({'html': '', 'css': 'x' * (100 * 1024 + 1)}))
        self.assertTrue(view.refused({'html': '', 'css': '', 'js': ''}))
        self.assertTrue(view.refused('<div>'))

    def test_a_link_out_is_https_to_a_named_host_in_a_new_tab_that_cannot_reach_back(self):
        good = '<a class="mk-site" href="https://positivefeedback.ai" target="_blank" rel="noopener noreferrer">Positive Feedback</a>'
        self.assertEqual(view.refused({'html': good, 'css': ''}), '')
        self.assertEqual(view.refused({'html': '<a href="https://sub.example.co.uk/a/b?c=d" target="_blank" rel="noopener noreferrer">x</a>', 'css': ''}), '')
        for bad in ('<a href="https://positivefeedback.ai">x</a>', '<a href="https://positivefeedback.ai" target="_blank">x</a>',
                    '<a href="https://positivefeedback.ai" rel="noopener noreferrer">x</a>', '<a href="https://positivefeedback.ai" target="_self" rel="noopener noreferrer">x</a>',
                    '<a href="https://positivefeedback.ai" target="_blank" rel="noopener">x</a>', '<a target="_blank" rel="noopener noreferrer">x</a>',
                    '<a href="http://positivefeedback.ai" target="_blank" rel="noopener noreferrer">x</a>', '<a href="//positivefeedback.ai" target="_blank" rel="noopener noreferrer">x</a>',
                    '<a href="javascript:alert(1)" target="_blank" rel="noopener noreferrer">x</a>', '<a href="data:text/html,x" target="_blank" rel="noopener noreferrer">x</a>',
                    '<a href="https://127.0.0.1/" target="_blank" rel="noopener noreferrer">x</a>', '<a href="https://localhost/" target="_blank" rel="noopener noreferrer">x</a>',
                    '<a href="https://user@positivefeedback.ai" target="_blank" rel="noopener noreferrer">x</a>', '<a href="https://positivefeedback.ai:8443" target="_blank" rel="noopener noreferrer">x</a>',
                    '<a href="https://positivefeedback.ai" href="javascript:x" target="_blank" rel="noopener noreferrer">x</a>',
                    '<a href="https://positivefeedback.ai" target="_blank" rel="noopener noreferrer" onclick="x()">x</a>',
                    '<a href="https://positivefeedback.ai" target="_blank" rel="noopener noreferrer" download>x</a>',
                    '<div href="https://positivefeedback.ai">x</div>', '<span target="_blank">x</span>', '<div rel="noopener noreferrer">x</div>'):
            self.assertTrue(view.refused({'html': bad, 'css': ''}), bad)

    def test_a_canvas_passes_and_carries_nothing(self):
        self.assertEqual(view.refused({'html': '<canvas class="mk-rain" aria-hidden="true"></canvas>', 'css': ''}), '')
        for bad in ('<canvas onclick="x()"></canvas>', '<canvas id="x"></canvas>', '<canvas style="x"></canvas>', '<canvas width="9"></canvas>'):
            self.assertTrue(view.refused({'html': bad, 'css': ''}), bad)

    def test_the_sheet_holds_no_backslash_and_no_less_than(self):   # a </style> in the sheet would end the host's own element
        for sheet in ('.a { content: "\\3c /style>" }', '.a::before { content: "<" }', '.a { } </style>', '.a { background: u\\72l(x) }'):
            self.assertTrue(view.refused({'html': '', 'css': sheet}), sheet)

    def test_our_cdn_passes(self):
        good = 'https://storage.googleapis.com/positivefeedback-cdn/themes/9b7c7c13/images/light/background.webp?v=fd529b2e'
        self.assertTrue(view.cdn_address(good))
        self.assertEqual(view.refused({'html': f'<img class="mk-art" src="{good}" alt="" loading="lazy">', 'css': f'.a {{ background: url("{good}") }}'}), '')

    def test_a_refused_view_is_dropped_whole_and_the_cards_stay(self):
        answer, why = view.checked({'cards': [{'key': 'K'}], 'total': 1, 'view': {'html': '<script></script>', 'css': ''}})
        self.assertEqual(answer, {'cards': [{'key': 'K'}], 'total': 1})
        self.assertIn('script', why)

    def test_an_answer_without_a_view_is_untouched(self):
        self.assertEqual(view.checked({'cards': []}), ({'cards': []}, ''))


if __name__ == '__main__':
    unittest.main()


class ThePageItself(unittest.TestCase):
    """A controller's links and its search name ONE address: the page's own path, its query changed (the owner, 2026-10-07: the controller is
    the agent's own, outside the core). The runtime is told the path with the call; without one, no such link or form passes."""
    PATH = '/larryd/int/en/app/agnt/home'

    def ok(self, markup, path=PATH):
        return view.refused({'html': markup, 'css': ''}, path)

    def test_a_link_to_the_page_with_its_query_changed_passes(self):
        for href in (self.PATH, self.PATH + '?mine=1', self.PATH + '?q=pace+shift&sort=name&view=simple&product=invoicemaps&module=Operations', self.PATH + '?q=caf%C3%A9'):
            self.assertEqual(self.ok(f'<a class="btn btn--small" href="{href}" aria-current="true">All agents</a>'), '', href)

    def test_any_other_address_is_refused(self):
        for href in ('/larryd/int/en/app/agnt/home/../../hire', '/larryd/int/en/app/hire?x=1', '/', '//evil.example/x', '/larryd/int/en/app/agnt/home#x',
                     self.PATH + '?next=//evil.example', self.PATH + '?a=b c', self.PATH + '?a="b', self.PATH + '/more', 'larryd/int/en/app/agnt/home',
                     'javascript:alert(1)', self.PATH + '?a=<b>', self.PATH + '?a=b;c', self.PATH + '?a=b\\c'):
            self.assertTrue(self.ok(f'<a href="{href}">x</a>'), href)
        self.assertTrue(self.ok(f'<a href="{self.PATH}" target="_blank">x</a>'))            # the page itself opens in place, never a new tab
        self.assertTrue(self.ok(f'<a href="{self.PATH}?a=1">x</a>', path=''))                # no path told: no such link
        self.assertTrue(self.ok(f'<a href="{self.PATH}?a=1">x</a>', path='/another/page'))
        self.assertTrue(self.ok('<a href="//x">x</a>', path='//x'))                           # a path is one slash, plain

    def test_a_search_is_a_get_to_the_page_itself(self):
        good = (f'<form method="get" action="{self.PATH}" class="sub-search-form"><input type="hidden" name="sort" value="name">'
                '<input type="text" name="q" class="sub-search-input" placeholder="Find…" value="a &lt;b&gt;"><button class="btn btn--small" type="submit">Search</button></form>')
        self.assertEqual(self.ok(good), '')
        for bad in (f'<form method="post" action="{self.PATH}"></form>', f'<form action="{self.PATH}"></form>', '<form method="get" action="/other"></form>',
                    f'<form method="get" action="{self.PATH}?x=1"></form>', f'<form method="get" action="{self.PATH}" target="_blank"></form>',
                    f'<form method="get" action="{self.PATH}" onsubmit="x()"></form>', '<form method="get"></form>',
                    f'<form method="get" action="{self.PATH}"><input type="password" name="q"></form>', f'<form method="get" action="{self.PATH}"><input type="file" name="q"></form>',
                    f'<form method="get" action="{self.PATH}"><input type="text" name="Q-1"></form>', f'<form method="get" action="{self.PATH}"><input type="text" name="q" formaction="/x"></form>',
                    f'<form method="get" action="{self.PATH}"><input type="text" name="q" autofocus></form>', f'<form method="get" action="{self.PATH}"><input name="q"></form>',
                    '<input type="text" name="q">', '<button type="submit">x</button>', f'<form method="get" action="{self.PATH}"></form><button type="submit">x</button>',
                    f'<form method="get" action="{self.PATH}"><button type="submit" formaction="/x">x</button></form>', '<div name="q">x</div>', '<span value="1">x</span>',
                    '<div method="get">x</div>', '<div action="/x">x</div>'):
            self.assertTrue(self.ok(bad), bad)
        self.assertTrue(view.refused({'html': good, 'css': ''}))                              # no path told: no form

    def test_the_looks_own_package_files_pass_as_pictures(self):   # the dock's logos are package files, served by the page's own site, not the CDN's
        for good in ('/themes/9b7c7c13/images/dark/logo_dock_01.png', '/themes/0dd98026/images/light/logo_header.png'):
            self.assertTrue(view.package_address(good), good)
            self.assertEqual(view.refused({'html': f'<img src="{good}" alt="">', 'css': f'.a {{ --mk-logo: url("{good}") }}'}), '', good)
        for bad in ('/themes/../wid/secret.png', '/themes/a/%2e%2e/b.png', '/themes/a b.png', '/themes/a.png?x=1', '/themes//a.png', '/themes/a/', '/themes/a',
                    '/static/css/core.css', '//themes/a.png', 'themes/a.png', '/themes/a.png#x', '/themes/a/..png/b', '/themes/a\\b.png', '/themes/.a.png'):
            self.assertFalse(view.package_address(bad), bad)
            self.assertTrue(view.refused({'html': f'<img src="{bad}" alt="">', 'css': ''}), bad)
            self.assertTrue(view.refused({'html': '', 'css': f'.a {{ background: url("{bad}") }}'}), bad)
