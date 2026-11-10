"""THE RUNTIME VERIFIES FROST'S SIGNED DECISION (the Agents Security Plan, lane C, 2026-11-09; the owner: "One approver:
production's FROST, by sha256 of the code and the manifest"). Every hire and RUN carries FROST's decision and its Ed25519
signature (wid's DECIDED); the runtime checks those exact bytes with FROST's public key (LARRYD_FROST_PUBLIC_KEY) and refuses,
in fixed words, a decision that is missing, changed, signed by another key, or for another card; no key at all refuses everything
(fail closed). The access field and the approved list stay: two guards, never one. A scratch key only, never FROST's."""
import datetime
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from _frost import PUBLIC, decided, decided_for
from _here import APP  # noqa: F401
from core_engine import decision, signing
from web import app as host

SECRET = 'scratch-secret-for-the-frost-decision'
WHO = {'account': 'ACCT_000000000001_0001', 'scope': 'SCRATCH', 'member': 'MCON_000000000002_0002'}
ALLOW = {host.CONFIG['access']['field']: host.CONFIG['access']['grants']}
DECIDED = decided()   # for WHO's member, signed now (each test module runs in seconds, inside the window)


class TheCheck(unittest.TestCase):
    def test_a_decision_signed_by_frosts_key_verifies(self):
        self.assertEqual(decision.why_not({**WHO, **decided()}), '')

    def test_one_changed_byte_is_refused(self):
        text = DECIDED['frost_decision']
        changed = text.replace('MCON_000000000002_0002', 'MCON_000000000002_0003')
        self.assertNotEqual(changed, text)
        self.assertEqual(decision.why_not({**WHO, **DECIDED, 'frost_decision': changed}), decision.BAD_SIG)
        sig = DECIDED['frost_decision_sig']
        flipped = sig[:-1] + ('0' if sig[-1] != '0' else '1')
        self.assertEqual(decision.why_not({**WHO, **DECIDED, 'frost_decision_sig': flipped}), decision.BAD_SIG)

    def test_another_keys_signature_is_refused(self):
        self.assertEqual(decision.why_not({**WHO, **decided(key=Ed25519PrivateKey.generate())}), decision.BAD_SIG)

    def test_a_missing_or_malformed_decision_is_refused(self):
        for d in ({}, {'frost_decision': DECIDED['frost_decision']}, {'frost_decision_sig': DECIDED['frost_decision_sig']},
                  {**DECIDED, 'frost_decision': ''}, {**DECIDED, 'frost_decision_sig': ''}):
            self.assertEqual(decision.why_not(d), decision.NO_DECISION)
        self.assertEqual(decision.why_not({**WHO, **DECIDED, 'frost_decision_sig': 'not hex'}), decision.BAD_SIG)

    def test_a_missing_key_refuses_everything(self):
        with mock.patch.dict(os.environ, {decision.ENV: ''}):
            self.assertEqual(decision.why_not({**WHO, **DECIDED}), decision.NO_KEY)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(decision.ENV)
            self.assertEqual(decision.why_not({**WHO, **DECIDED}), 'no FROST public key')
        os.environ[decision.ENV] = PUBLIC
        for bad in ('zz', 'ab' * 31, 'ab' * 33):   # not hex, short, long
            with mock.patch.dict(os.environ, {decision.ENV: bad}):
                self.assertEqual(decision.why_not({**WHO, **DECIDED}), decision.NO_KEY)

    def test_a_decision_for_another_member_is_never_replayed(self):
        other = {**WHO, 'member': 'MCON_000000000003_0003'}
        self.assertEqual(decision.why_not({**other, **decided()}), decision.NOT_THIS_MEMBER)
        self.assertEqual(decision.why_not({**{k: v for k, v in WHO.items() if k != 'member'}, **decided()}), decision.NOT_THIS_MEMBER)
        self.assertEqual(decision.why_not({**other, **decided(member=other['member'])}), '')

    def test_a_decision_out_of_its_time_is_refused(self):
        at = datetime.datetime(2026, 11, 9, 12, 0, 0, tzinfo=datetime.timezone.utc)
        d = {**WHO, **decided(at=at.isoformat())}
        later = lambda s: at + datetime.timedelta(seconds=s)   # noqa: E731
        self.assertEqual(decision.why_not(d, now=later(0)), '')
        self.assertEqual(decision.why_not(d, now=later(decision.WINDOW)), '')
        self.assertEqual(decision.why_not(d, now=later(decision.WINDOW + 1)), decision.STALE)        # sent again later: refused
        self.assertEqual(decision.why_not(d, now=later(-decision.SKEW)), '')
        self.assertEqual(decision.why_not(d, now=later(-decision.SKEW - 1)), decision.STALE)         # from the future
        for bad in ('', 'yesterday', '2026-11-09T12:00:00'):   # none, not a moment, no zone
            self.assertEqual(decision.why_not({**WHO, **decided(at=bad)}, now=later(0)), decision.STALE)

    def test_the_call_must_carry_what_frost_signed(self):
        self.assertEqual(decision.why_not({**WHO, **DECIDED, 'card_key': 'MAGT_00000000AA01_0001', 'code_sha256': 'c' * 64}), '')
        self.assertEqual(decision.why_not({**WHO, **DECIDED, 'card_key': 'MAGT_00000000AA02_0001'}), decision.NOT_THIS)
        self.assertEqual(decision.why_not({**WHO, **DECIDED, 'code_sha256': 'd' * 64}), decision.NOT_THIS)
        self.assertEqual(decision.why_not({**WHO, **DECIDED, 'manifest_sha256': 'd' * 64}), decision.NOT_THIS)


class TheDoors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = host.create_app(self.tmp.name, secret=SECRET, addresses={})
        self.client = self.app.test_client()
        self.started = []
        self.app.config['harness'].run_job = lambda *a: self.started.append(a)

    def tearDown(self):
        self.tmp.cleanup()

    def post(self, route, data):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return self.client.post('/api' + route, json=data, headers={'X-Office': signing.sign(SECRET, route, data, at), 'X-Office-At': at})

    def get(self, route, data):
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        return self.client.get('/api' + route, query_string=data, headers={'X-Office': signing.sign(SECRET, route, data, at), 'X-Office-At': at})

    def test_a_call_without_frosts_decision_is_refused(self):
        r = self.get('/agents/answer', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001'})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': decision.NO_DECISION}))
        r = self.post('/agents/answer', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', **decided(key=Ed25519PrivateKey.generate())})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': decision.BAD_SIG}))

    def test_a_call_with_another_members_decision_is_refused(self):
        r = self.get('/agents/answer', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', **decided(member='MCON_000000000003_0003')})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': decision.NOT_THIS_MEMBER}))

    def test_a_call_without_a_key_is_refused(self):
        with mock.patch.dict(os.environ, {decision.ENV: ''}):
            r = self.get('/agents/answer', decided_for({**WHO, 'agent_key': 'MAGT_00000000AA01_0001'}))
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': 'no FROST public key'}))

    def test_a_call_with_its_members_decision_goes_on(self):
        r = self.get('/agents/answer', decided_for({**WHO, 'agent_key': 'MAGT_00000000AA01_0001'}))
        self.assertNotEqual(r.status_code, 403)   # past the check: the agent is not held here, so the harness says so in its own words
        self.assertNotIn(r.get_json()['refused'], (decision.NO_DECISION, decision.BAD_SIG, decision.NOT_THIS_MEMBER, decision.STALE, decision.NO_KEY))

    def test_a_hire_for_another_member_is_refused(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'on', **ALLOW, **decided(member='MCON_000000000003_0003')})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': decision.NOT_THIS_MEMBER}))

    def test_a_hire_without_frosts_decision_is_refused(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'on', **ALLOW})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': decision.NO_DECISION}))

    def test_a_hire_with_a_changed_decision_is_refused(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'on', **ALLOW, **decided(key=Ed25519PrivateKey.generate())})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': decision.BAD_SIG}))

    def test_a_hire_with_frosts_decision_goes_on(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'on', **ALLOW, **DECIDED})
        self.assertEqual((r.status_code, r.get_json()), (503, {'refused': 'the marketplace is not in the locker'}))   # past both guards

    def test_a_let_go_needs_no_decision(self):
        r = self.post('/agents/hire', {**WHO, 'agent_key': 'MAGT_00000000AA01_0001', 'on': 'off', **ALLOW})
        self.assertEqual(r.get_json(), {'refused': 'the marketplace is not in the locker'})   # wid decides nothing to let go: past the door

    def test_a_run_without_a_key_is_refused_and_never_started(self):
        with mock.patch.dict(os.environ, {decision.ENV: ''}):
            r = self.post('/jobs/run', {**WHO, 'job_key': 'MJOB_00000000000A_0001', 'run': '1', **ALLOW, **DECIDED})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': 'no FROST public key'}))
        self.assertEqual(self.started, [])

    def test_a_run_with_a_bad_signature_is_refused_and_never_started(self):
        d = {**DECIDED, 'frost_decision': DECIDED['frost_decision'].replace('allow', 'allox')}
        r = self.post('/jobs/run', {**WHO, 'job_key': 'MJOB_00000000000A_0001', 'run': '1', **ALLOW, **d})
        self.assertEqual((r.status_code, r.get_json()), (403, {'refused': decision.BAD_SIG}))
        self.assertEqual(self.started, [])

    def test_a_queued_run_frost_did_not_sign_is_ended_refused_with_the_reason(self):
        said = []

        class Platform:
            def get(self, office, route, data=None):
                return 200, {'jobs': [{**WHO, 'job_key': 'MJOB_00000000000A_0001', 'run': 1, **ALLOW, **DECIDED},
                                      {**WHO, 'job_key': 'MJOB_00000000000B_0001', 'run': 2, **ALLOW},
                                      {**WHO, 'job_key': 'MJOB_00000000000C_0001', 'run': 3, **ALLOW, **decided(key=Ed25519PrivateKey.generate())},
                                      {**WHO, 'job_key': 'MJOB_00000000000D_0001', 'run': 4, **ALLOW, **decided(member='MCON_000000000003_0003')},
                                      {**WHO, 'job_key': 'MJOB_00000000000E_0001', 'run': 5, **ALLOW, **decided(at='2026-11-01T00:00:00+00:00')}]}

            def post(self, office, route, data):
                said.append((route, data))
                return 200, {}
        h = self.app.config['harness']
        h.client = Platform()
        began = []
        self.app.config['start'] = lambda *a: began.append(a[3]) or True
        host.catch_up(self.app)
        self.assertEqual(began, ['MJOB_00000000000A_0001'])
        self.assertEqual([(d['job_key'], d['state'], d['log']) for route, d in said if route == '/jobs/result'],
                         [('MJOB_00000000000B_0001', 'REFUSED', decision.NO_DECISION), ('MJOB_00000000000C_0001', 'REFUSED', decision.BAD_SIG),
                          ('MJOB_00000000000D_0001', 'REFUSED', decision.NOT_THIS_MEMBER), ('MJOB_00000000000E_0001', 'REFUSED', decision.STALE)])
        con = sqlite3.connect(h.db)
        n = con.execute("SELECT COUNT(*) FROM runtime_runs WHERE lane = 'job' AND state = 'REFUSED'").fetchone()[0]
        con.close()
        self.assertEqual(n, 4)

    def test_a_queued_run_is_checked_when_the_queue_is_read_not_when_its_turn_comes(self):
        class Platform:
            def get(self, office, route, data=None):
                return 200, {'jobs': [{**WHO, 'job_key': f'MJOB_00000000000{n}_0001', 'run': 1, **ALLOW, **decided()} for n in 'AB']}

            def post(self, office, route, data):
                return 200, {}
        self.app.config['harness'].client = Platform()
        began, clock = [], [datetime.datetime.now(datetime.timezone.utc)]

        def start(*a):   # the first run holds the slot past the window: the second is still started, its decision checked at the read
            began.append(a[3])
            clock[0] += datetime.timedelta(seconds=decision.WINDOW * 3)
            return True
        self.app.config['start'] = start
        real = decision.why_not
        with mock.patch.object(decision, 'why_not', lambda d, now=None: real(d, now=clock[0])):
            host.catch_up(self.app)
        self.assertEqual(began, ['MJOB_00000000000A_0001', 'MJOB_00000000000B_0001'])


if __name__ == '__main__':
    unittest.main()
