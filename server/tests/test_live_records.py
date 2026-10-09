"""THE ROOM PROGRAM'S ASKS: an agent whose approved manifest declares a live page and a species keeps what its members
write in the member's own records, through LARRYD and the platform's own doors for agents. The door takes only the room
program's mark (the key the pass is signed with), made within the minute, and holds the ask to the manifest, the gate and
the platform, as it holds a CALL. On a developer's runtime the stand-in answers the platform's doors."""
import json
import os
import pathlib
import shutil
import tempfile
import time
import unittest

from _here import APP
from core_engine import live, preview
from test_preview import GOOD_CARD, KEY_A, SECRET, _zip
from web import app as host

KEY = 'k' * 48


def _agent(records, with_live=True):
    manifest = {'name': 'Scratch wire', 'entry': 'agent.py', 'about': 'a scratch live agent', 'does': ['door'], 'calls': ['door'], 'reads': [],
                'run': {'do': 'door', 'hands': []}, 'gives': ['view'], 'skills': [], 'card': {**GOOD_CARD, 'screen': 'sprt/home', 'module': 'Sprint', 'product': 'AGENCY MGMT'}}
    if with_live:
        manifest['live'] = {'seats': 4}
    if records is not None:
        manifest['records'] = records
    return {'agent.json': json.dumps(manifest).encode(), 'agent.py': b'import json, sys\njson.load(sys.stdin)\nprint(json.dumps({"view": {"html": "<div>x</div>"}}))\n',
            'live/page.html': b'<!doctype html>', 'live/room.py': b'import asyncio\n'}


class TheDoor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        (root / 'live.key').write_text(KEY)
        self.env = {'LARRYD_LIVE_ADDRESS': 'https://live.example.org', 'LARRYD_LIVE_KEY_FILE': str(root / 'live.key')}
        self.old = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)
        self.agents = root / 'agents'
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
        self.app = host.create_app(root, secret=SECRET, addresses={}, agents=self.agents, developer=True)
        self.client = self.app.test_client()
        self.client.get('/marketplace')
        self.who = {'agent': KEY_A, 'account': preview.ACCOUNT, 'scope': preview.SCOPE, 'member': preview.MEMBER, 'species': 'sprt'}

    def tearDown(self):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.tmp.cleanup()

    def place(self, records={'sprt': ['read', 'add', 'edit']}, hire=True, with_live=True):
        r = self.client.post(f'/marketplace/place?key={KEY_A}', data=_zip(_agent(records, with_live)), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
        self.assertIn(r.status_code, (200, 201), r.get_data(as_text=True)[:300])
        if hire:
            self.app.config['harness'].hire(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, True)

    def test_the_answer_carries_the_runtimes_own_room(self):
        """The room inside the platform's page: the runtime's own field beside the view, the room program's address and a pass of its own; an agent with no live half has none."""
        self.place()
        h = self.app.config['harness']
        out = h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})
        self.assertRegex(out['room'], r'^https://live\.example\.org/#[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$')
        again = h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})
        self.assertNotEqual(out['room'], again['room'])   # every pass opens once: each answer has its own
        self.assertEqual(out['view'], {'html': '<div>x</div>', 'css': ''})
        self.assertNotIn('frame', out)

    def test_the_agent_is_told_its_room_is_there_and_is_handed_no_address_and_no_pass(self):
        """THE SECURITY REVIEW OF THE ROOM RULE (2026-10-08): an agent's markup is not trusted with a credential. The agent is told
        only {"room": true}; the address and the pass go to the platform alone, in the runtime's own field."""
        files = _agent({'sprt': ['read', 'add', 'edit']})
        files['agent.py'] = b'import json, sys\ngiven = json.load(sys.stdin)\nprint(json.dumps({"said": json.dumps(given)}))\n'
        files['agent.json'] = json.dumps({**json.loads(files['agent.json']), 'gives': ['said']}).encode()
        self.client.post(f'/marketplace/place?key={KEY_A}', data=_zip(files), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
        h = self.app.config['harness']
        h.hire(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, True)
        out = h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})
        handed = json.loads(out['said'])
        self.assertEqual(handed['live'], {'room': True})
        member_pass = out['room'].split('#', 1)[1]
        self.assertNotIn('live.example.org', out['said'])   # no address
        self.assertNotIn(member_pass, out['said'])           # no pass
        self.assertNotIn(member_pass.split('.')[0][:24], out['said'])

    def test_an_agent_with_a_live_page_is_handed_the_first_name_its_pass_carries(self):
        """The messenger inside the page writes a message under the same name as the live page does: FROST's own first name, plain, or none."""
        from core_engine import harness
        files = _agent({'sprt': ['read', 'add', 'edit']})
        files['agent.py'] = b'import json, sys\ngiven = json.load(sys.stdin)\nprint(json.dumps({"who": given.get("who")}))\n'
        files['agent.json'] = json.dumps({**json.loads(files['agent.json']), 'gives': ['who']}).encode()
        self.client.post(f'/marketplace/place?key={KEY_A}', data=_zip(files), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
        h = self.app.config['harness']
        h.hire(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, True)
        self.assertEqual(h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})['who'], {'member': preview.MEMBER})   # FROST handed no name: the key alone
        real = harness.Harness._identity
        try:
            harness.Harness._identity = lambda self, account, scope, member: {'first_name': '  Uma  ', 'email': 'uma@example.org'}
            self.assertEqual(h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})['who'], {'member': preview.MEMBER, 'name': 'Uma'})   # the first name alone, nothing else of them
            harness.Harness._identity = lambda self, account, scope, member: {'first_name': '<b>Uma</b>'}
            self.assertEqual(h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})['who'], {'member': preview.MEMBER})   # not plain: none
        finally:
            harness.Harness._identity = real

    def test_no_room_without_a_live_half_and_never_an_agents_own(self):
        self.place(with_live=False)
        self.assertNotIn('room', self.app.config['harness'].answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={}))
        from core_engine import harness as lanes_harness
        for with_live in (False, True):
            for gives in (['view'], ['view', 'room']):   # AN AGENT'S OWN "room" REFUSES THE WHOLE ANSWER, even when its manifest's "gives" names it, with a live half or without
                files = _agent({'sprt': ['read', 'add', 'edit']}, with_live=with_live)
                files['agent.py'] = b'import json, sys\njson.load(sys.stdin)\nprint(json.dumps({"view": {"html": "<div>x</div>"}, "room": "https://elsewhere.example.org/#a.b"}))\n'
                files['agent.json'] = json.dumps({**json.loads(files['agent.json']), 'gives': gives}).encode()
                r = self.client.post(f'/marketplace/place?key={KEY_A}', data=_zip(files), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
                self.assertIn(r.status_code, (200, 201))
                with self.assertRaises(lanes_harness.Refused, msg=(with_live, gives)):
                    self.app.config['harness'].answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})

    def ask(self, do, signed=KEY, at=None, **more):
        body = json.dumps({**self.who, 'do': do, 'at': int(time.time()) if at is None else at, **more}).encode()
        r = self.client.post('/api/live/records', data=body, headers={'X-Talk-Mark': live.mark(signed.encode(), body), 'Content-Type': 'application/json'})
        return r.status_code, r.get_json()

    def test_the_live_half_is_held_in_the_locker_with_the_agent_under_one_hash(self):
        self.place()
        held = self.app.config['harness']
        from core_engine import locker
        row = locker.held(held.db, KEY_A)
        folder = self.agents / row['folder']
        self.assertTrue((folder / 'live' / 'room.py').is_file())
        self.assertEqual(locker.verify(held.db, self.agents, KEY_A), (True, ''))
        (folder / 'live' / 'room.py').write_text('import os\n')
        self.assertEqual(locker.verify(held.db, self.agents, KEY_A), (False, 'tampered: the code changed'))
        status, body = self.ask('list')
        self.assertEqual((status, body), (403, {'refused': 'tampered: the code changed'}))

    def test_list_add_edit_through_the_platforms_own_doors(self):
        self.place()
        self.assertEqual(self.ask('list'), (200, {'rows': []}))
        status, made = self.ask('add', values={'identity_sprint_name': 'PF Messenger', 'identity_sprint_start': '2000-01-01', 'data_sprint_type': 'PF MESSENGER'})
        self.assertEqual((status, made['ok'], made['why']), (200, True, ''))
        self.assertRegex(made['key'], r'^[A-Z0-9_]+$')
        status, edited = self.ask('edit', key=made['key'], values={'data_message_001': '{"n":1,"words":"hello"}'})
        self.assertEqual((status, edited['ok']), (200, True))
        status, got = self.ask('list')
        row = got['rows'][0]
        self.assertEqual((row['key'], row['identity_sprint_name'], row['data_message_001']), (made['key'], 'PF Messenger', '{"n":1,"words":"hello"}'))

    def test_only_the_room_programs_mark_opens_it(self):
        self.place()
        self.assertEqual(self.ask('list', signed='x' * 48)[0], 401)
        self.assertEqual(self.ask('list', at=int(time.time()) - 300), (401, {'refused': 'a late ask'}))
        body = json.dumps({**self.who, 'do': 'list', 'at': int(time.time())}).encode()
        self.assertEqual(self.client.post('/api/live/records', data=body).status_code, 401)   # no mark
        self.assertEqual(self.client.post('/api/live/records', data=body, headers={'X-Talk-Mark': live.mark(KEY.encode(), body + b' ')}).status_code, 401)   # a changed body

    def test_only_what_the_approved_manifest_declares(self):
        self.place(records={'sprt': ['read']})
        self.assertEqual(self.ask('list')[0], 200)
        self.assertEqual(self.ask('add', values={'identity_sprint_name': 'x'}), (403, {'refused': 'the agent does not declare it'}))
        self.who['species'] = 'opns'
        self.assertEqual(self.ask('list'), (403, {'refused': 'the agent does not declare it'}))

    def test_an_agent_with_no_live_page_has_no_such_door(self):
        self.place(with_live=False)
        self.assertEqual(self.ask('list'), (403, {'refused': 'the agent does not declare it'}))

    def test_a_remove_is_never_asked_this_way(self):
        self.place(records={'sprt': ['read', 'add', 'edit', 'remove']})
        self.assertEqual(self.ask('remove', key='MSPR_000000000000_0000')[0], 401)

    def test_a_member_who_did_not_hire_it_is_refused(self):
        self.place(hire=False)
        self.assertEqual(self.ask('list')[0], 403)

    def test_names_that_are_not_plain_keys_are_refused(self):
        self.place()
        for field, bad in (('account', 'A B'), ('member', '../x'), ('agent', ''), ('species', 'SPRT'), ('scope', 'a"b')):
            was, self.who[field] = self.who[field], bad
            self.assertEqual(self.ask('list')[0], 401, field)
            self.who[field] = was
        self.assertEqual(self.ask('edit', key='../x', values={'a': 'b'})[0], 401)
        self.assertEqual(self.ask('add', values='junk')[0], 401)
        self.assertEqual(self.ask('add', values={'Bad-Name': 'b'})[0], 400)


if __name__ == '__main__':
    unittest.main()
