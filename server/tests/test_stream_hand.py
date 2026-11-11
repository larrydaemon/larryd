"""THE MEMBER'S LIVE STREAM, MEASURED ON A RUN (Live's rule, the owner 2026-11-10: "Red when your page's live stream will not open or
sends no live data within 5 seconds"): an internal agent naming "stream" in run.hands is handed, on a RUN, given["stream"] = {opened,
first_seconds, lines, seconds} as wid's /jobs/stream answers it for this open RUN of this member (wid decides and opens the line as
itself). A measure alone: an answer of any other shape, a refusal or silence is {not_read: why} and the RUN still runs (its agent says
"not measured"). Without the hand nothing is asked; on the external runtime the hand is not given. wid here is a Recorder (this process)."""
import unittest

from _here import APP  # noqa: F401
from core_engine import harness, platform
from test_job_inputs import ACCOUNT, CARD, HIRED, JOB, MEMBER, SCOPE, Echo

MEASURE = {'opened': True, 'first_seconds': 0.04, 'lines': 2, 'seconds': 5}
WORD = 'preference::Member_Color_Mode'   # a word of the member's line: never handed, whatever wid answers


class Wid:
    def __init__(self, status=200, body=None, silent=False):
        self.status, self.body, self.silent, self.said = status, dict(MEASURE) if body is None else body, silent, []

    def get(self, office, route, data=None):
        self.said.append((office, route, data))
        if route == '/jobs/stream':
            if self.silent:
                raise OSError('wid does not answer')
            return self.status, self.body
        return 200, {}

    def post(self, office, route, data):
        self.said.append((office, route, data))
        return (200, {'charged': 0, 'free': True}) if route == '/jobs/charge' else (200, {'saved': True})


class StreamHand(Echo):
    internal = True

    def ran(self, wid, hands=('stream',)):
        self.agent(None, hands=hands)
        h = harness.Harness(self.db, self.agents, wid)
        h.INTERNAL = self.internal   # the hand is LARRYD RUNTIME INTERNAL's only
        h.facts = lambda account, scope, member: ([CARD], HIRED, [], lambda key: (True, ''))
        seen = {}
        h._run = lambda folder, manifest, given: (seen.update(given) or 'DONE', {'delivery': 'ok'}, '')
        return h.run_job(ACCOUNT, SCOPE, MEMBER, JOB, 1), seen

    def asked(self, wid):
        return [d for _o, r, d in wid.said if r == '/jobs/stream']

    def test_the_measure_is_handed_for_this_open_run_of_this_member(self):
        wid = Wid()
        state, seen = self.ran(wid)
        self.assertEqual((state, seen['stream']), ('DONE', MEASURE))
        self.assertEqual(self.asked(wid), [{'account': ACCOUNT, 'scope': SCOPE, 'member': MEMBER, 'job_key': JOB, 'run': '1'}])
        self.assertEqual(harness.HANDED['stream'][:2], ('wid', '/jobs/stream'))
        self.assertGreater(platform.Client.SLOW['/jobs/stream'], 10)   # wid holds the line its seconds before it answers

    def test_a_line_that_did_not_open_is_a_measure_too(self):
        closed = {'opened': False, 'first_seconds': None, 'lines': 0, 'seconds': 5}
        state, seen = self.ran(Wid(body=closed))
        self.assertEqual((state, seen['stream']), ('DONE', closed))

    def test_a_refusal_or_silence_is_not_read_and_the_run_still_runs(self):
        for wid, why in ((Wid(403, {'refused': 'no open RUN of this member'}), 'no open RUN of this member'),
                         (Wid(503, {'refused': 'the office does not answer'}), 'the office does not answer'),
                         (Wid(404, {}), 'wid answered 404'), (Wid(silent=True), 'wid does not answer (OSError)')):
            with self.subTest(why=why):
                state, seen = self.ran(wid)
                self.assertEqual((state, seen['stream']), ('DONE', {'not_read': why}))

    def test_anything_but_the_measure_is_never_handed(self):
        for body in ({**MEASURE, 'saw': WORD}, {**MEASURE, 'lines': [WORD]}, {**MEASURE, 'opened': WORD}, {**MEASURE, 'first_seconds': WORD},
                     {**MEASURE, 'first_seconds': True}, {k: v for k, v in MEASURE.items() if k != 'lines'}, [WORD], {'events': [{'changed': WORD}]}):
            with self.subTest(body=body):
                state, seen = self.ran(Wid(body=body))
                self.assertEqual(state, 'DONE')
                self.assertEqual(seen['stream'], {'not_read': "wid answered no measure of the member's live stream"})
                self.assertNotIn(WORD, repr(seen))

    def test_without_the_hand_nothing_is_asked(self):
        wid = Wid()
        state, seen = self.ran(wid, hands=())
        self.assertEqual((state, self.asked(wid), 'stream' in seen), ('DONE', [], False))


class StreamHandElsewhere(StreamHand):
    """THE EXTERNAL RUNTIME (LARRYD_INTERNAL unset): "stream" is not a hand it gives; the RUN fails before it starts, nothing is asked."""
    internal = False

    def test_the_measure_is_handed_for_this_open_run_of_this_member(self):
        wid = Wid()
        state, seen = self.ran(wid)
        self.assertEqual(state, 'FAILED')
        self.assertIn("LARRYD cannot hand ['stream'] yet", self.results(wid)[-1]['log'])
        self.assertEqual((self.asked(wid), 'stream' in seen), ([], False))

    test_a_line_that_did_not_open_is_a_measure_too = None
    test_a_refusal_or_silence_is_not_read_and_the_run_still_runs = None
    test_anything_but_the_measure_is_never_handed = None


if __name__ == '__main__':
    unittest.main()
