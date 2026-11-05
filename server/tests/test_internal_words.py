"""AN INTERNAL AGENT'S OWN WORDS ON ITS JOB (the owner 2026-11-03, Scrum Master 3: every value from the database): on LARRYD
RUNTIME INTERNAL, an internal agent's RUN log is its delivery's first line, and a check that found a red answers light RED: the
RUN ends RED (FAILED) with its own line. An external agent, or the external runtime: the runtime's own words, as before."""
import json
import unittest
from unittest import mock

from _here import APP  # noqa: F401
from core_engine import harness
from test_outside import Platform
from test_skills import World


class InternalWords(World):
    def internal(self, answer):
        self.agent([], answer=answer, gives=('delivery', 'light'))
        folder = self.agents / 'echo'
        card = json.loads((folder / 'agent.json').read_text())
        card['internal'] = {'seconds': 30}
        (folder / 'agent.json').write_text(json.dumps(card))

    def test_a_done_run_says_its_own_first_line(self):
        self.internal({'delivery': 'GREEN · 12 of 12 probes pass\nmore'})
        p = Platform()
        with mock.patch.object(harness.Harness, 'INTERNAL', True):
            self.assertEqual(self.run_with(p), 'DONE')
        end = self.results(p)[-1]
        self.assertEqual((end['state'], end['log']), ('DONE', 'RUN 1 DONE · GREEN · 12 of 12 probes pass'))

    def test_a_red_check_ends_red_with_its_own_line(self):
        self.internal({'delivery': 'RED · 1 of 12 probes fail: G8', 'light': 'RED'})
        p = Platform()
        with mock.patch.object(harness.Harness, 'INTERNAL', True):
            self.assertEqual(self.run_with(p), 'FAILED')
        end = self.results(p)[-1]
        self.assertEqual((end['state'], end['log'], end['delivery']), ('FAILED', 'RUN 1 RED · RED · 1 of 12 probes fail: G8', 'RED · 1 of 12 probes fail: G8'))

    def test_the_external_runtime_keeps_its_own_words(self):
        self.internal({'delivery': 'GREEN', 'light': 'RED'})
        p = Platform()
        with mock.patch.object(harness.Harness, 'INTERNAL', False):
            self.run_with(p)
        self.assertNotIn('RED ·', self.results(p)[-1]['log'])


class InternalLimit(unittest.TestCase):
    """AN INTERNAL AGENT'S TIME LIMIT: its manifest's own internal.seconds, at most 6 hours (the night's Web build and Test hold
    the smoke test, up to 4 hours, after the Judge); none or a wrong one: the runtime's own."""
    def limit(self, seconds):
        h = harness.Harness.__new__(harness.Harness)
        h.agents, h.seconds, h.on_start = __import__('pathlib').Path('/nowhere'), 20, None
        with mock.patch.object(harness.Harness, 'INTERNAL', True), mock.patch.object(harness.sandbox, 'run', return_value='ran') as run:
            h._run('a', {'entry': 'agent.py', 'internal': {} if seconds is None else {'seconds': seconds}}, {})
        return run.call_args[0][3]

    def test_five_hours_are_kept(self):
        self.assertEqual(self.limit(5 * 3600), 5 * 3600)

    def test_past_six_hours_is_six_hours(self):
        self.assertEqual(self.limit(9 * 3600), 6 * 3600)

    def test_none_is_the_runtimes_own(self):
        self.assertEqual(self.limit(None), 20)


if __name__ == '__main__':
    unittest.main()
