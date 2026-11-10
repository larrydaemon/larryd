"""THE RUNTIME'S OPEN FILES (the owner 2026-11-10, "we need it all healthy and working"): launchd starts the runtime with 256
open files, the same limit that silenced wid ("Too many open files") when a board's page had every agent's view drawn
together; the runtime raises its own soft limit as it starts, never above the hard one, never lowering one already higher."""
import resource
import unittest
from _here import APP   # noqa: F401
from web import app as host


class OpenFiles(unittest.TestCase):
    def setUp(self):
        self.soft, self.hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        self.addCleanup(resource.setrlimit, resource.RLIMIT_NOFILE, (self.soft, self.hard))

    def test_raised_one_step_never_lowered_the_hard_limit_untouched(self):
        step = self.soft + 8 if self.hard == resource.RLIM_INFINITY or self.hard >= self.soft + 8 else self.hard
        self.assertEqual(host.open_files(at_least=step), (self.soft, step))
        self.assertEqual(host.open_files(at_least=1), (step, step))
        self.assertEqual(resource.getrlimit(resource.RLIMIT_NOFILE), (step, self.hard))

    def test_the_start_asks_at_least_4096(self):
        self.assertGreaterEqual(host.OPEN_FILES, 4096)   # 256 was the break
        before, after = host.open_files()
        self.assertEqual(before, self.soft)
        self.assertGreaterEqual(after, min(host.OPEN_FILES if self.hard == resource.RLIM_INFINITY else min(host.OPEN_FILES, self.hard), max(self.soft, after)))
