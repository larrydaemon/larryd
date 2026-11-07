"""THE MEMBER'S OWN DA-M PICTURE IN AN AGENT'S VIEW (CORE_CLEANUP_IV 26, 33 and 94): an agent writes src="larryd:picture/<DA-M key>";
the runtime builds wid's own door to that picture, /<office>/<side>/<lang>/embedded/picture/<key>, on the page's own office, side and
language (a path: the page's own origin), or drops the src. wid answers it under the member's own session (frost-99 2026-11-06: DA-M's
own raw address drew nothing for a member who had not opened DA-M, since an <img> follows no sign-in). The gate takes exactly that path
and still refuses any other src off our CDN, DA-M's own address included."""
import unittest

from _here import APP  # noqa: F401
from core_engine import view

PATH = '/wid/rnd/en/app/imgs/home'
B = {'wid': 'https://frost-b.positivefeedback.ai', 'so': 'https://frost-b.positivefeedback.ai', 'fs': 'https://frost-b.positivefeedback.ai'}
LOCAL = {'wid': 'http://127.0.0.1:5004', 'so': 'http://127.0.0.1:5006', 'fs': 'http://127.0.0.1:5008'}
KEY = 'DA-M_0123456789AB_00CD'
OWN = f'/wid/rnd/en/embedded/picture/{KEY}'
CDN = 'https://storage.googleapis.com/positivefeedback-cdn/themes/0dd98026/images/dark/agent_card.png'


def view_of(src):
    return {'view': {'html': f'<figure><img src="{src}" alt="My picture" loading="lazy"></figure>', 'css': ''}}


class Built(unittest.TestCase):
    def test_picture_of_builds_wids_own_door_on_the_pages_office_side_and_language(self):
        self.assertEqual(view.picture_of(PATH, KEY), OWN)
        self.assertEqual(view.picture_of('/wid/pf/fr/app/imgs/home', KEY), f'/wid/pf/fr/embedded/picture/{KEY}')
        self.assertEqual(view.picture_of('/mgmt/rnd/en/app/cont/card', KEY), f'/mgmt/rnd/en/embedded/picture/{KEY}')   # the page's own office

    def test_a_bad_key_or_page_builds_nothing(self):
        for key in ('', 'DA-M_0123456789ab_00cd', 'DA-M_0123456789AB_00C', 'DA-M_0123456789AB_00CD/../x', 'MAGT_0123456789AB_00CD', f'{KEY}/download', None):
            self.assertEqual(view.picture_of(PATH, key), '', key)
        for path in ('/not/a/page', '', None, 'https://evil.example/wid/rnd/en/app/x', '/wid/rnd/en/embedded/picture'):
            self.assertEqual(view.picture_of(path, KEY), '', path)


class Markers(unittest.TestCase):
    def test_the_marker_becomes_the_door_or_loses_its_src(self):
        html = f'<img src="larryd:picture/{KEY}" alt="A"><img src="larryd:picture/DA-M_bad" alt="B"><img src="larryd:picture/{KEY}/download" alt="C">'
        got = view.pictures(html, PATH)
        self.assertEqual(got.count(f'src="{OWN}"'), 1)
        self.assertNotIn('larryd:', got)   # the unbuildable ones: no src left at all (the picture inert)
        self.assertEqual(got.count('src='), 1)
        self.assertEqual(view.pictures(html, '').count('src='), 0)   # no page path: every marker dropped
        self.assertNotEqual(view.checked({'view': {'html': f'<a href="larryd:picture/{KEY}">x</a>', 'css': ''}}, PATH, B)[1], '')   # a picture is a src, never a link: the gate refuses it

    def test_checked_passes_the_built_picture_and_the_gate_takes_it_on_every_box(self):
        for origins, local in ((B, False), (LOCAL, True), (None, False)):   # the door is a path: the same on a public box and on the laptop
            with self.subTest(local=local):
                out, why = view.checked(view_of(f'larryd:picture/{KEY}'), PATH, origins, local=local)
                self.assertEqual((why, f'src="{OWN}"' in out['view']['html']), ('', True))
        out, why = view.checked(view_of('larryd:picture/nope'), PATH, B)
        self.assertEqual((why, 'src=' in out['view']['html']), ('', False))   # dropped src: the view still drawn, the picture inert


class TheGate(unittest.TestCase):
    def test_the_gate_takes_wids_own_door_on_the_pages_office_and_nothing_else(self):
        self.assertEqual(view.refused(view_of(OWN)['view'], PATH), '')
        self.assertEqual(view.refused(view_of(CDN)['view'], PATH), '')   # our CDN, as before
        for src in (OWN.replace('/rnd/', '/pf/'),                                       # another side
                    OWN.replace('/en/', '/fr/'),                                        # another language
                    OWN.replace('/wid/', '/mgmt/'),                                     # another office
                    OWN.replace('/picture/', '/logo/'),                                 # another door
                    OWN + '?x=1', OWN + '#x', OWN + '/raw',                             # a query, a fragment, a tail
                    OWN.replace(KEY, 'DA-M_0123456789ab_00cd'),                         # not a key
                    f'/wid/rnd/en/x/../embedded/picture/{KEY}',                         # a walk
                    f'//evil.example{OWN}',                                             # another host, scheme-less
                    f'https://frost-b.positivefeedback.ai{OWN}',                        # even the page's own host spelled out: a path only
                    f'https://frost-b.positivefeedback.ai/so/rnd/en/app/files/card/{KEY}/raw',   # DA-M's own address: no more
                    f'http://127.0.0.1:5006/so/rnd/en/app/files/card/{KEY}/raw',
                    'https://evil.example/x.png'):
            with self.subTest(src):
                self.assertNotEqual(view.refused(view_of(src)['view'], PATH), '')
                self.assertNotEqual(view.refused(view_of(src)['view'], PATH, tuple(LOCAL.values())), '')   # nor on a localhost box
        self.assertNotEqual(view.refused(view_of(OWN)['view'], ''), '')   # no page path: no office to match
        self.assertNotEqual(view.refused({'html': '<b>x</b>', 'css': f'a {{ background: url({OWN}) }}'}, PATH), '')   # a picture of the view's own, never the sheet's


if __name__ == '__main__':
    unittest.main()
