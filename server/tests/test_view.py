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

    def test_our_cdn_passes(self):
        good = 'https://storage.googleapis.com/positivefeedback-cdn/themes/9b7c7c13/images/light/agent_card.png?v=fd529b2e'
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
