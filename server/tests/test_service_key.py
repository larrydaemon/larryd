"""THE SERVICE KEY OF A CONNECTOR (CORE_CLEANUP_IV 50, 53, 100; frost-07's shape): an internal agent naming "service_key" in run.hands is
handed, on a RUN, given["service_key"] = {service, key}: the service is the first plain word of its card's sends_to, the key the hiring
member's own from FROST's vault as wid hands it for this open RUN (wid decides: the member's Allow, the card). Not allowed or none
stored: {service, key: '', why} and the RUN still runs (the agent draws its step, sends nothing). Anything else: the RUN fails first.
The key is kept nowhere. wid here is a Recorder (this process)."""
import json
import unittest

from _here import APP  # noqa: F401
from core_engine import harness
from test_job_inputs import ACCOUNT, CARD, HIRED, JOB, KEY, MEMBER, SCOPE, Echo

SECRET = 'mon-key-Zanzibar-7731'


class Wid:
    def __init__(self, status=200, body=None):
        self.status, self.body, self.said = status, body if body is not None else {'key': SECRET}, []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        return 200, {}

    def post(self, office, route, data):
        self.said.append((office, route, data))
        if route == '/jobs/provider_key':
            return self.status, self.body
        return (200, {'charged': 0, 'free': True}) if route == '/jobs/charge' else (200, {'saved': True})


class ServiceKey(Echo):
    internal = True

    def ran(self, wid, sends_to='monday.com (the member\'s boards)', hands=('service_key',)):
        self.agent(None, hands=hands)
        h = harness.Harness(self.db, self.agents, wid)
        h.INTERNAL = self.internal   # the hand is LARRYD RUNTIME INTERNAL's only (one source: LARRYD_INTERNAL=1 at its start)
        h.facts = lambda account, scope, member: ([{**CARD, 'sends_to': sends_to}], HIRED, [], lambda key: (True, ''))
        seen = {}
        h._run = lambda folder, manifest, given: (seen.update(given) or 'DONE', {'delivery': 'ok'}, '')
        return h.run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), seen

    def asked(self, wid):
        return [d for _o, r, d in wid.said if r == '/jobs/provider_key']

    def test_the_members_own_key_is_handed_for_the_service_named_first(self):
        wid = Wid()
        state, seen = self.ran(wid)
        self.assertEqual(state, 'DONE')
        self.assertEqual(seen['service_key'], {'service': 'monday', 'key': SECRET})
        self.assertEqual(self.asked(wid), [{'account': ACCOUNT, 'scope': SCOPE, 'member': MEMBER, 'job_key': JOB, 'run': '1', 'provider': 'monday'}])
        for path in self.instance.rglob('*'):
            if path.is_file():
                self.assertNotIn(SECRET.encode(), path.read_bytes(), f'{path.name} keeps the key')

    def test_not_allowed_or_none_stored_still_runs_with_the_reason(self):
        for status, body, why in ((403, {'refused': 'not allowed by this member: they have not said yes to this agent sending their data'}, 'not allowed'),
                                  (404, {'refused': 'nothing by that key'}, 'none stored')):
            with self.subTest(why=why):
                state, seen = self.ran(Wid(status, body))
                self.assertEqual(state, 'DONE')
                self.assertEqual(seen['service_key'], {'service': 'monday', 'key': '', 'why': why})

    def test_anything_else_fails_the_run_before_it_starts(self):
        wid = Wid(403, {'refused': 'not an approved agent that sends to this provider'})
        state, seen = self.ran(wid)
        self.assertEqual(state, 'FAILED')
        self.assertNotIn('service_key', seen)
        self.assertIn('could not read the service key', self.results(wid)[-1]['log'])
        state, _seen = self.ran(Wid(), sends_to='')
        self.assertEqual(state, 'FAILED')

    def test_the_service_is_the_first_plain_word_lowercased(self):
        _state, seen = self.ran(Wid(), sends_to='WhatsApp Cloud API (Meta)')
        self.assertEqual(seen['service_key']['service'], 'whatsapp')

    def test_without_the_hand_nothing_is_asked(self):
        wid = Wid()
        state, seen = self.ran(wid, hands=())
        self.assertEqual((state, self.asked(wid), 'service_key' in seen), ('DONE', [], False))


class ServiceKeyElsewhere(ServiceKey):
    """THE EXTERNAL RUNTIME (LARRYD_INTERNAL unset): "service_key" is not a hand it gives; the RUN fails as it always did, nothing is asked."""
    internal = False

    def test_the_members_own_key_is_handed_for_the_service_named_first(self):
        wid = Wid()
        state, seen = self.ran(wid)
        self.assertEqual(state, 'FAILED')
        self.assertIn("LARRYD cannot hand ['service_key'] yet", self.results(wid)[-1]['log'])
        self.assertNotIn('service_key', seen)
        self.assertEqual(self.asked(wid), [])

    test_not_allowed_or_none_stored_still_runs_with_the_reason = None
    test_anything_else_fails_the_run_before_it_starts = None
    test_the_service_is_the_first_plain_word_lowercased = None


if __name__ == '__main__':
    unittest.main()
