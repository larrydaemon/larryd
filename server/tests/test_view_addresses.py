"""A REFUSED ADDRESS GOES ALONE, BEFORE THE ANSWER LEAVES (frost-05's ruling 2026-11-06): wid places a view whole or not at all and never
rewrites it (the owner: no sanitizer of third-party code), so the runtime, the agent's own side, drops an address its gate refuses before
the answer leaves: a picture loses its src (the <img> stays, inert), a link becomes a <span> with its own words and class. Only a tag
refused for its address alone: anything else (a handler, a script, a frame) leaves the view as written and the gate refuses it whole."""
import unittest

from _here import APP  # noqa: F401
from core_engine import view

PATH = '/wid/rnd/en/app/imgs/home'
OWN = '/wid/rnd/en/embedded/picture/DA-M_0123456789AB_00CD'
DAM = 'http://127.0.0.1:5006/so/rnd/en/app/files/card/DA-M_0123456789AB_00CD/raw'
CDN = 'https://storage.googleapis.com/positivefeedback-cdn/themes/0dd98026/images/dark/agent_card.png'
OUT = 'target="_blank" rel="noopener noreferrer"'


def placed(html):
    return view.checked({'view': {'html': html, 'css': ''}}, PATH, {})


class APictureOrALinkGoesAlone(unittest.TestCase):
    def test_a_refused_picture_loses_its_src_and_the_view_stays(self):
        out, why = placed(f'<div><h2>Comp card</h2><img src="{DAM}" alt="Ana"><img src="{OWN}" alt="Bo"><img src="{CDN}" alt="c"></div>')
        self.assertEqual(why, '')
        html = out['view']['html']
        self.assertIn('Comp card', html)
        self.assertIn('<img alt="Ana">', html)   # inert, its words kept
        self.assertNotIn(DAM, html)
        self.assertIn(f'src="{OWN}"', html)   # the taken ones untouched
        self.assertIn(f'src="{CDN}"', html)

    def test_a_refused_link_becomes_its_words(self):
        out, why = placed(f'<p><a class="k" href="http://elsewhere.example/x" {OUT}>out</a> <a href="{PATH}?q=1">mine</a>'
                          f' <a href="https://example.org/x" {OUT}>fine</a></p>')
        self.assertEqual(why, '')
        html = out['view']['html']
        self.assertIn('<span class="k">out</span>', html)   # no target, no rel: the link went, its words and class stay
        self.assertIn(f'<a href="{PATH}?q=1">mine</a>', html)
        self.assertIn(f'<a href="https://example.org/x" {OUT}>fine</a>', html)
        out, why = placed('<p><a href="&#106;avascript:x()">y</a></p>')   # an address hidden in entities: the gate reads it plain, it goes
        self.assertEqual((why, out['view']['html']), ('', '<p><span>y</span></p>'))

    def test_anything_but_the_address_still_refuses_the_whole_view(self):
        for bad in (f'<img src="{DAM}" onerror="x()"><p>k</p>',   # a handler on the same tag: left as written
                    f'<img src="{DAM}"><script>x()</script>',
                    f'<a href="http://elsewhere.example/x" onclick="x()">y</a>',
                    f'<img src="{DAM}"><iframe src="{CDN}"></iframe>',
                    f'<img src="{DAM}" src="{CDN}">'):   # written twice: the gate's to refuse
            with self.subTest(bad=bad):
                out, why = placed(bad)
                self.assertNotEqual(why, '')
                self.assertNotIn('view', out)

    def test_a_view_with_nothing_refused_is_passed_on_as_written(self):
        html = f'<div><img src="{OWN}" alt="x"><a href="{PATH}">me</a></div>'
        self.assertEqual(placed(html), ({'view': {'html': html, 'css': ''}}, ''))
        self.assertEqual(view.addresses_dropped(html, PATH), (html, 0))
        self.assertEqual(view.addresses_dropped(f'<img src="{DAM}" alt="a"><a href="http://x/y">b</a>', PATH)[1], 2)
        self.assertEqual(view.addresses_dropped(None, PATH), (None, 0))


if __name__ == '__main__':
    unittest.main()
