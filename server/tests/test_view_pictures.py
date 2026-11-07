"""THE MEMBER'S OWN DA-M PICTURE IN AN AGENT'S VIEW (CORE_CLEANUP_IV 26, 33 and 94), the twin of the download link: an agent writes
src="larryd:picture/<DA-M key>"; the runtime builds DA-M's raw picture of that file (/so/<side>/<lang>/app/files/card/<key>/raw) on the
page's own side and language at DA-M's origin (the platform's own word, page.origins), or drops the src. The gate takes exactly that address
(https to a named host, or on a LOCALHOST box plain http to a handed origin) and still refuses any other src off our CDN."""
import unittest

from _here import APP  # noqa: F401
from core_engine import view

PATH = '/wid/rnd/en/app/imgs/home'
B = {'wid': 'https://frost-b.positivefeedback.ai', 'so': 'https://frost-b.positivefeedback.ai', 'fs': 'https://frost-b.positivefeedback.ai'}
LOCAL = {'wid': 'http://127.0.0.1:5004', 'so': 'http://127.0.0.1:5006', 'fs': 'http://127.0.0.1:5008'}
KEY = 'DA-M_0123456789AB_00CD'
RAW = f'/so/rnd/en/app/files/card/{KEY}/raw'
CDN = 'https://storage.googleapis.com/positivefeedback-cdn/themes/0dd98026/images/dark/agent_card.png'


def view_of(src):
    return {'view': {'html': f'<figure><img src="{src}" alt="My picture" loading="lazy"></figure>', 'css': ''}}


class Built(unittest.TestCase):
    def test_picture_of_builds_dams_raw_picture_on_the_pages_side_and_language(self):
        self.assertEqual(view.picture_of(PATH, KEY, B['so']), 'https://frost-b.positivefeedback.ai' + RAW)
        self.assertEqual(view.picture_of('/wid/pf/fr/app/imgs/home', KEY, B['so']), f'https://frost-b.positivefeedback.ai/so/pf/fr/app/files/card/{KEY}/raw')
        self.assertEqual(view.picture_of(PATH, KEY, LOCAL['so'], tuple(LOCAL.values())), 'http://127.0.0.1:5006' + RAW)   # a localhost box: DA-M's own port

    def test_a_bad_key_page_or_origin_builds_nothing(self):
        for key in ('', 'DA-M_0123456789ab_00cd', 'DA-M_0123456789AB_00C', 'DA-M_0123456789AB_00CD/../x', 'MAGT_0123456789AB_00CD', f'{KEY}/download', None):
            self.assertEqual(view.picture_of(PATH, key, B['so']), '', key)
        self.assertEqual(view.picture_of('/not/a/page', KEY, B['so']), '')
        for origin in ('', None, 'http://frost-b.positivefeedback.ai', 'https://user@frost-b.positivefeedback.ai', 'https://10.0.0.1', 'https://frost-b.positivefeedback.ai:8443'):
            self.assertEqual(view.picture_of(PATH, KEY, origin), '', origin)
        self.assertEqual(view.picture_of(PATH, KEY, LOCAL['so']), '')   # not a localhost box: no http
        self.assertEqual(view.picture_of(PATH, KEY, 'http://127.0.0.1:9999', tuple(LOCAL.values())), '')   # an origin nobody handed


class Markers(unittest.TestCase):
    def test_the_marker_becomes_the_address_or_loses_its_src(self):
        html = f'<img src="larryd:picture/{KEY}" alt="A"><img src="larryd:picture/DA-M_bad" alt="B"><img src="larryd:picture/{KEY}/download" alt="C">'
        got = view.pictures(html, PATH, B)
        self.assertEqual(got.count(f'src="https://frost-b.positivefeedback.ai{RAW}"'), 1)
        self.assertNotIn('larryd:', got)   # the unbuildable ones: no src left at all (the picture inert)
        self.assertEqual(got.count('src='), 1)
        self.assertEqual(view.pictures(html, PATH, None).count('src='), 0)   # no origins handed: every marker dropped
        self.assertNotIn('src="http', view.pictures(html, PATH, LOCAL))   # http origins on a box that is not localhost: dropped
        self.assertIn(f'src="http://127.0.0.1:5006{RAW}"', view.pictures(html, PATH, LOCAL, local=True))
        self.assertNotEqual(view.checked({'view': {'html': f'<a href="larryd:picture/{KEY}">x</a>', 'css': ''}}, PATH, B)[1], '')   # a picture is a src, never a link: the gate refuses it

    def test_checked_passes_the_built_picture_and_the_gate_takes_it(self):
        out, why = view.checked(view_of(f'larryd:picture/{KEY}'), PATH, B)
        self.assertEqual(why, '')
        self.assertIn(f'src="https://frost-b.positivefeedback.ai{RAW}"', out['view']['html'])
        out, why = view.checked(view_of(f'larryd:picture/{KEY}'), PATH, LOCAL, local=True)
        self.assertEqual((why, f'src="http://127.0.0.1:5006{RAW}"' in out['view']['html']), ('', True))
        out, why = view.checked(view_of('larryd:picture/nope'), PATH, B)
        self.assertEqual((why, 'src=' in out['view']['html']), ('', False))   # dropped src: the view still drawn, the picture inert


class TheGate(unittest.TestCase):
    def test_the_gate_takes_dams_raw_picture_on_the_pages_side_and_nothing_else(self):
        self.assertEqual(view.refused(view_of('https://frost-b.positivefeedback.ai' + RAW)['view'], PATH), '')
        self.assertEqual(view.refused(view_of(CDN)['view'], PATH), '')   # our CDN, as before
        for src in ('https://frost-b.positivefeedback.ai' + RAW.replace('/rnd/', '/pf/'),            # another side
                    'https://frost-b.positivefeedback.ai' + RAW.replace('/en/', '/fr/'),             # another language
                    'https://frost-b.positivefeedback.ai' + RAW[:-4] + '/download',                  # another DA-M path
                    f'https://frost-b.positivefeedback.ai/so/rnd/en/app/files/{KEY}/raw',            # another DA-M path
                    'https://frost-b.positivefeedback.ai' + RAW + '?x=1',                            # a query
                    'https://frost-b.positivefeedback.ai' + RAW + '#x',                              # a fragment
                    'https://frost-b.positivefeedback.ai' + RAW.replace(KEY, 'DA-M_0123456789ab_00cd'),   # not a key
                    'https://frost-b.positivefeedback.ai/x/..' + RAW,                                # a walk
                    'https://user@frost-b.positivefeedback.ai' + RAW,                                # a user part
                    'https://frost-b.positivefeedback.ai:8443' + RAW,                                # a port
                    'https://10.0.0.1' + RAW,                                                        # a number for a host
                    'http://frost-b.positivefeedback.ai' + RAW,                                      # plain http off a localhost box
                    RAW,                                                                             # a bare path
                    'https://evil.example/x.png'):
            with self.subTest(src):
                self.assertNotEqual(view.refused(view_of(src)['view'], PATH), '')
        self.assertNotEqual(view.refused(view_of('https://frost-b.positivefeedback.ai' + RAW)['view'], ''), '')   # no page path: no side to match
        self.assertNotEqual(view.refused({'html': f'<a href="https://frost-b.positivefeedback.ai{RAW}">x</a>', 'css': ''}, PATH), '')   # a raw picture is a src, not a same-page link

    def test_http_only_to_a_handed_origin_on_a_localhost_box(self):
        local = tuple(LOCAL.values())
        self.assertEqual(view.refused(view_of('http://127.0.0.1:5006' + RAW)['view'], PATH, local), '')
        for src in ('http://127.0.0.1:5007' + RAW, 'http://evil.example:5006' + RAW, 'http://127.0.0.1:5006@evil.example' + RAW):
            with self.subTest(src):
                self.assertNotEqual(view.refused(view_of(src)['view'], PATH, local), '')
        self.assertNotEqual(view.refused(view_of('http://127.0.0.1:5006' + RAW)['view'], PATH, ()), '')   # any other box: refused
        out, why = view.checked(view_of('http://127.0.0.1:5006' + RAW), PATH, LOCAL, local=False)
        self.assertNotEqual(why, '')
        self.assertNotIn('view', out)


if __name__ == '__main__':
    unittest.main()
