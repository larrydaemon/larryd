"""THE PLATFORM'S OWN PAGES, LINKED FROM AN AGENT'S VIEW (CORE_CLEANUP_IV 20 and 96, frost-05's rulings b and c' under the owner's blanket
approval): an agent writes a marker (href="larryd:upload/<zone>", "larryd:download/<DA-M key>", "larryd:frost/<page>"); the runtime builds
the address on the origin of the office that serves it (the platform's own word, page.origins), or drops the href. On a LOCALHOST box only,
the gate takes plain http to exactly those handed origins (each office its own port); another host, another port, or any other box: refused."""
import unittest

from _here import APP  # noqa: F401
from core_engine import view

PATH = '/wid/rnd/en/app/imgs/home'
B = {'wid': 'https://frost-b.positivefeedback.ai', 'so': 'https://frost-b.positivefeedback.ai', 'fs': 'https://frost-b.positivefeedback.ai'}
LOCAL = {'wid': 'http://127.0.0.1:5004', 'so': 'http://127.0.0.1:5006', 'fs': 'http://127.0.0.1:5008'}
OUT = 'target="_blank" rel="noopener noreferrer"'
KEY = 'DA-M_0123456789AB_00CD'


def view_of(href):
    return {'view': {'html': f'<p><a href="{href}" {OUT}>Add files</a></p>', 'css': ''}}


class Built(unittest.TestCase):
    def test_upload_of_builds_dams_add_files_page_on_its_origin(self):
        self.assertEqual(view.upload_of(PATH, 'imgs', B['so']), 'https://frost-b.positivefeedback.ai/so/rnd/en/app/files/add?zone=imgs')
        self.assertEqual(view.upload_of(PATH, '', B['so']), 'https://frost-b.positivefeedback.ai/so/rnd/en/app/files/add')   # no zone
        for zone in ('a/b', 'A', 'x' * 33, '../x', 'a b', None):
            self.assertEqual(view.upload_of(PATH, zone, B['so']), '', zone)   # a zone with a slash (or any not plain) refused
        self.assertEqual(view.upload_of(PATH, 'imgs', ''), '')   # no host refused
        self.assertEqual(view.upload_of('/not/a/page', 'imgs', B['so']), '')

    def test_frost_of_builds_a_frost_page_on_frosts_origin(self):
        self.assertEqual(view.frost_of(PATH, 'vault', B['fs']), 'https://frost-b.positivefeedback.ai/fs/rnd/en/vault')
        self.assertEqual(view.frost_of(PATH, 'member/access', B['fs']), 'https://frost-b.positivefeedback.ai/fs/rnd/en/member/access')
        for name in ('', '../vault', 'Vault', 'a/b/c/d', 'x?y=1'):
            self.assertEqual(view.frost_of(PATH, name, B['fs']), '', name)

    def test_http_is_built_only_for_a_handed_origin_on_a_localhost_box(self):
        self.assertEqual(view.upload_of(PATH, 'imgs', LOCAL['so']), '')   # not a localhost box: no http
        self.assertEqual(view.upload_of(PATH, 'imgs', LOCAL['so'], tuple(LOCAL.values())), 'http://127.0.0.1:5006/so/rnd/en/app/files/add?zone=imgs')
        self.assertEqual(view.upload_of(PATH, 'imgs', 'http://127.0.0.1:9999', tuple(LOCAL.values())), '')   # an origin nobody handed
        self.assertEqual(view.download_of(PATH, KEY, LOCAL['so'], tuple(LOCAL.values())), f'http://127.0.0.1:5006/so/rnd/en/app/files/card/{KEY}/download')


class Markers(unittest.TestCase):
    def test_markers_become_addresses_or_lose_their_href(self):
        html = f'<a href="larryd:upload/imgs" {OUT}>A</a><a href="larryd:frost/vault" {OUT}>B</a><a href="larryd:download/{KEY}" {OUT}>C</a><a href="larryd:upload/a/b" {OUT}>D</a>'
        got = view.resolve(html, PATH, B)
        self.assertIn('href="https://frost-b.positivefeedback.ai/so/rnd/en/app/files/add?zone=imgs"', got)
        self.assertIn('href="https://frost-b.positivefeedback.ai/fs/rnd/en/vault"', got)
        self.assertIn(f'href="https://frost-b.positivefeedback.ai/so/rnd/en/app/files/card/{KEY}/download"', got)
        self.assertNotIn('larryd:', got)   # the unbuildable one: no href left at all
        self.assertEqual(view.resolve(html, PATH, None).count('href='), 0)   # no origins handed: every marker dropped

    def test_checked_passes_a_resolved_view_and_the_gate_takes_it(self):
        out, why = view.checked(view_of('larryd:upload/imgs'), PATH, B, local=False)
        self.assertEqual(why, '')
        self.assertIn('/so/rnd/en/app/files/add?zone=imgs', out['view']['html'])
        out, why = view.checked(view_of('larryd:upload/imgs'), PATH, LOCAL, local=True)
        self.assertEqual((why, 'http://127.0.0.1:5006/so/rnd/en/app/files/add?zone=imgs' in out['view']['html']), ('', True))


class TheGate(unittest.TestCase):
    def test_http_only_for_the_handed_origins_on_a_localhost_box(self):
        local = tuple(LOCAL.values())
        self.assertEqual(view.refused(view_of('http://127.0.0.1:5006/so/rnd/en/app/files/add')['view'], PATH, local), '')
        for href in ('http://127.0.0.1:5007/so/rnd/en/app/files/add',   # another port
                     'http://evil.example:5006/so/rnd/en/app/files/add',   # another host
                     'http://127.0.0.1:5006@evil.example/x',               # a user part
                     'http://127.0.0.1:5006/../../etc/passwd'):
            with self.subTest(href):
                self.assertNotEqual(view.refused(view_of(href)['view'], PATH, local), '')
        self.assertNotEqual(view.refused(view_of('http://127.0.0.1:5006/so/rnd/en/app/files/add')['view'], PATH, ()), '')   # any other box: refused

    def test_checked_on_a_box_that_is_not_localhost_never_takes_http(self):
        out, why = view.checked(view_of('http://127.0.0.1:5006/so/rnd/en/app/files/add'), PATH, LOCAL, local=False)
        self.assertNotEqual(why, '')
        self.assertNotIn('view', out)
        self.assertEqual(view.checked(view_of('https://example.com/x'), PATH, None)[1], '')   # a plain link out, as before


if __name__ == '__main__':
    unittest.main()
