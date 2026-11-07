"""THE ANSWER'S MOST (frost-05 2026-11-06, row 92 pf fal): an agent's answer is capped at the sandbox's 1 MB, except an agent whose
manifest declares the DA-M store skill (the very test harness._files makes): it may answer up to STORE_ANSWER_MOST (34 MiB: one file
up to DA-M's 25 MB as base64, and its words). The sandbox reads at most that + 2 bytes and refuses past it: never held whole. On Linux
(the server) a real run proves both: a declared agent's 20 MB answer kept, an undeclared agent's 2 MB answer refused."""
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import _here  # noqa: F401
from core_engine import harness, sandbox

STORE = next(h for h, s in harness.SKILLS.items() if s.get('after') == 'files')   # the DA-M store skill's own hash
DECLARED = {'entry': 'agent.py', 'skills': [STORE]}
UNDECLARED = {'entry': 'agent.py', 'skills': []}


class TheAnswersMost(unittest.TestCase):
    def test_only_the_store_skill_raises_it(self):
        self.assertEqual(harness.answer_most(DECLARED), harness.STORE_ANSWER_MOST)
        self.assertGreaterEqual(harness.STORE_ANSWER_MOST, 4 * (25 * 1000 * 1000) // 3)   # one 25 MB file as base64 fits
        for manifest in (UNDECLARED, {'entry': 'agent.py'}, {'skills': ['not-a-skill']}, {'skills': 'x'}, None):
            self.assertEqual(harness.answer_most(manifest), sandbox.MOST_BYTES, manifest)

    def test_every_run_is_given_its_agents_most(self):
        h = harness.Harness.__new__(harness.Harness)
        h.agents, h.seconds, h.on_start = pathlib.Path('/nonexistent'), 5, None
        given = []
        with mock.patch.object(sandbox, 'run', lambda *a, **k: given.append(k.get('most_bytes')) or ('DONE', {}, '')):
            h._run('folder', DECLARED, {})
            h._run('folder', UNDECLARED, {})
        self.assertEqual(given, [harness.STORE_ANSWER_MOST, sandbox.MOST_BYTES])

    @unittest.skipUnless(sys.platform.startswith('linux'), 'the sandbox runs on Linux (the server); this Mac cannot start it (exit 71)')
    def test_a_declared_agents_20_mb_answer_is_kept_an_undeclared_agents_2_mb_is_refused(self):
        """Through the REAL sandbox (frost-cb's question, 2026-11-06: proven, not a stand-in): the agent says where it ran (HOME is
        the run's own private folder, runtime_run_*, which only sandbox.run gives) and that it could not write outside it; the
        20 MB answer comes back byte for byte; the 2 MB one is refused for its length and nothing else."""
        agent = ("import json, os, sys\n"
                 "try:\n    open('/etc/larryd_escape', 'w'); wrote = True\nexcept OSError:\n    wrote = False\n"
                 "sys.stdout.write(json.dumps({'home': os.environ.get('HOME', ''), 'wrote_outside': wrote, 'x': 'y' * %d}))\n")
        with tempfile.TemporaryDirectory() as a:
            pathlib.Path(a, 'agent.py').write_text(agent % (20 * 1000 * 1000))
            state, answer, why = sandbox.run(a, 'agent.py', {}, seconds=60, most_bytes=harness.answer_most(DECLARED))
            self.assertEqual((state, why), ('DONE', ''))
            self.assertEqual(answer['x'], 'y' * (20 * 1000 * 1000))
            self.assertTrue(pathlib.Path(answer['home']).name.startswith('runtime_run_'), answer['home'])   # the sandbox's own run folder
            self.assertIs(answer['wrote_outside'], False)   # the sandbox held: nothing written outside the run folder
        with tempfile.TemporaryDirectory() as a:
            pathlib.Path(a, 'agent.py').write_text(agent % (2 * 1000 * 1000))
            state, answer, why = sandbox.run(a, 'agent.py', {}, seconds=60, most_bytes=harness.answer_most(UNDECLARED))
            self.assertEqual((state, answer, why), ('FAILED', None, 'the answer is too long'))   # refused for its length alone

if __name__ == '__main__':
    unittest.main()
