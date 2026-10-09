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

    def test_the_answer_carries_the_runtimes_own_frame(self):
        """The live page inside the platform's page: the runtime's own field beside the view, a pass of its own; an agent with no live page has none."""
        self.place()
        h = self.app.config['harness']
        out = h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})
        self.assertTrue(out['frame'].startswith('https://live.example.org/#'), out.get('frame'))
        again = h.answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={})
        self.assertNotEqual(out['frame'], again['frame'])   # every pass opens once: each answer has its own
        self.assertEqual(out['view'], {'html': '<div>x</div>', 'css': ''})

    def test_no_frame_without_a_live_page_and_never_an_agents_own(self):
        self.place(with_live=False)
        self.assertNotIn('frame', self.app.config['harness'].answer(preview.ACCOUNT, preview.SCOPE, preview.MEMBER, KEY_A, beside={}))
        files = _agent({'sprt': ['read', 'add', 'edit']}, with_live=False)
        files['agent.py'] = b'import json, sys\njson.load(sys.stdin)\nprint(json.dumps({"view": {"html": "<div>x</div>"}, "frame": "https://elsewhere.example.org/"}))\n'
        r = self.client.post(f'/marketplace/place?key={KEY_A}', data=_zip(files), content_type='application/octet-stream', headers={'X-Larryd-Place': '1'})
        self.assertIn(r.status_code, (200, 201))
        from core_engine import harness as lanes_harness
        with self.assertRaises(lanes_harness.Refused):   # an agent's own "frame" is no field of an answer: the whole answer is refused
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
