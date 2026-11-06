"""THE LIVE PAGE'S PASS: an agent whose manifest declares "live" is handed the link to its own live page with a pass the
runtime signed for the member; with the live page not set up it is handed none. The pass is checked here exactly as a
room program checks it (the same key, the same marks)."""
import base64
import hashlib
import hmac
import json
import pathlib
import tempfile
import unittest

from _here import APP   # noqa: F401
from core_engine import live

KEY = 'k' * 48


def _read(text, key=KEY.encode()):
    body, mark = text.split('.')
    pad = lambda s: s + '=' * (-len(s) % 4)   # noqa: E731
    good = hmac.compare_digest(base64.urlsafe_b64decode(pad(mark)), hmac.new(key, body.encode(), hashlib.sha256).digest())
    return json.loads(base64.urlsafe_b64decode(pad(body))) if good else None


class ThePass(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.key = pathlib.Path(self.tmp) / 'live.key'
        self.key.write_text(KEY)
        self.env = {'LARRYD_LIVE_ADDRESS': 'https://live.example.org', 'LARRYD_LIVE_KEY_FILE': str(self.key)}

    def test_the_manifest_field(self):
        self.assertEqual(live.declared({'live': {'seats': 4}}), {'seats': 4})
        for bad in ({}, {'live': True}, {'live': {'seats': 5}}, {'live': {'seats': 0}}, {'live': {'seats': '4'}}, {'live': {'seats': 4, 'guests': 1}}, {'live': {'seats': True}}):
            self.assertIsNone(live.declared(bad), bad)

    def test_a_link_with_a_pass_the_room_program_can_check(self):
        link = live.link('ACCT_1', 'MEMB_1', 'MAGT_1', ' Ava  Lee ', {'wears': {'agencymgmt': 'B9AF66CF6633'}, 'mode': 'light'}, 'agencymgmt', environ=self.env, now=1000)
        self.assertTrue(link.startswith('https://live.example.org/#'))
        facts = _read(link.split('#', 1)[1])
        self.assertEqual({k: facts[k] for k in ('account', 'member', 'agent', 'name', 'theme', 'mode', 'ends')},
                         {'account': 'ACCT_1', 'member': 'MEMB_1', 'agent': 'MAGT_1', 'name': 'Ava Lee', 'theme': 'B9AF66CF6633', 'mode': 'light', 'ends': 1600})
        self.assertRegex(facts['once'], r'^[a-f0-9]{24}$')

    def test_the_link_is_one_a_view_may_draw(self):
        from core_engine import view
        self.assertTrue(view.link_address(live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=self.env)))

    def test_who_the_member_is_rides_on_the_pass_only_as_frost_handed_it(self):
        who = {'first_name': 'Ava', 'member_type': 'OWNER', 'account_name': 'Harbor  Films', 'email': 'ava@example.org', 'website': 'example.org'}
        facts = _read(live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=self.env, who=who).split('#', 1)[1])
        self.assertEqual((facts['name'], facts['company'], facts['email'], facts['site']), ('Ava', 'Harbor Films', 'ava@example.org', 'example.org'))
        bare = _read(live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=self.env, who={'first_name': 'Ava', 'account_name': 'Harbor Films'}).split('#', 1)[1])
        self.assertEqual((bare['company'], bare['email'], bare['site']), ('Harbor Films', '', ''))
        odd = _read(live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=self.env, who={'account_name': '<b>x</b>', 'email': 7, 'website': 'a\nb'}).split('#', 1)[1])
        self.assertEqual((odd['company'], odd['email'], odd['site']), ('', '', ''))

    def test_every_pass_is_its_own(self):
        a, b = (live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=self.env) for _ in range(2))
        self.assertNotEqual(a, b)

    def test_a_changed_pass_does_not_check(self):
        text = live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=self.env).split('#', 1)[1]
        body, mark = text.split('.')
        other = base64.urlsafe_b64encode(json.dumps({**_read(text), 'account': 'ACCT_2'}).encode()).rstrip(b'=').decode()
        self.assertIsNone(_read(other + '.' + mark))
        self.assertIsNone(_read(text, b'another key of thirty-two bytes!!'))

    def test_no_link_when_the_live_page_is_not_set_up(self):
        for env in ({}, {'LARRYD_LIVE_ADDRESS': 'https://live.example.org'}, {**self.env, 'LARRYD_LIVE_ADDRESS': 'http://live.example.org'},
                    {**self.env, 'LARRYD_LIVE_ADDRESS': 'https://10.0.0.1'}, {**self.env, 'LARRYD_LIVE_ADDRESS': 'https://live.example.org/#x'},
                    {**self.env, 'LARRYD_LIVE_KEY_FILE': str(self.key) + '.none'}):
            self.assertEqual(live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=env), '', env)
        self.key.write_text('short')
        self.assertEqual(live.link('ACCT_1', 'MEMB_1', 'MAGT_1', environ=self.env), '')

    def test_no_link_for_a_member_or_account_that_is_not_a_plain_key(self):
        for account, member in (('ACCT 1', 'MEMB_1'), ('ACCT_1', ''), ('ACCT_1', 'M"1'), (None, 'MEMB_1')):
            self.assertEqual(live.link(account, member, 'MAGT_1', environ=self.env), '')

    def test_a_theme_that_is_not_a_theme_is_left_out(self):
        facts = _read(live.link('ACCT_1', 'MEMB_1', 'MAGT_1', page={'wears': {'agencymgmt': '../x'}}, product='agencymgmt', environ=self.env).split('#', 1)[1])
        self.assertEqual((facts['theme'], facts['mode']), ('', 'dark'))


class AViewIsPassedOnWithBothTexts(unittest.TestCase):
    """A view the agent hands with markup and no sheet goes on as {html, css}: the platform's gate reads both texts and places nothing without them."""
    def test_markup_alone(self):
        from core_engine import view
        answer, why = view.checked({'open': True, 'view': {'html': '<div class="body">Door</div>'}})
        self.assertEqual((why, answer['view']), ('', {'html': '<div class="body">Door</div>', 'css': ''}))
        answer, why = view.checked({'view': {'html': '<div class="body">Door</div>', 'css': '.a { color: red; }'}})
        self.assertEqual((why, answer['view']['css']), ('', '.a { color: red; }'))


if __name__ == '__main__':
    unittest.main()
