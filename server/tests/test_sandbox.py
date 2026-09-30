"""THE SANDBOX, proven on the real machine, whichever it is (macOS sandbox-exec, or Linux bubblewrap + seccomp): each plant
is also run WITHOUT the sandbox (the control), so a green test means the sandbox stopped it, not that the plant never
worked. The same tests run on both systems; only the words of a refusal differ (a path the Linux sandbox never mounts is
"No such file", a read-only mount is "Read-only file system", where macOS says "Operation not permitted")."""
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

from _here import APP
from core_engine import sandbox

ECHO = 'import sys, json\nprint(json.dumps({"got": json.load(sys.stdin)}))\n'
LINUX = sys.platform.startswith('linux')
REFUSED = {   # the system's own words for each refusal, by system
    'network': ('Network is unreachable', 'Connection refused') if LINUX else ('Operation not permitted',),
    'write outside': ('No such file or directory', 'Read-only file system') if LINUX else ('Operation not permitted',),
    'write own folder': ('Read-only file system',) if LINUX else ('Operation not permitted',),
    'read outside': ('No such file or directory',) if LINUX else ('Operation not permitted',),
    'process': ('Operation not permitted',),
}


def said(reason, kind):
    return any(words in reason for words in REFUSED[kind])


class SandboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / 'agents'
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _agent(self, code, name='plant'):
        folder = self.root / name
        folder.mkdir()
        (folder / 'agent.py').write_text(code)
        return folder

    def _control(self, folder, given='{}'):
        """The same agent, same interpreter, NO sandbox."""
        return subprocess.run([sandbox.PYTHON, '-I', '-B', str(folder / 'agent.py')], input=given, capture_output=True, text=True, timeout=10)

    def test_echo_answers(self):
        folder = self._agent(ECHO)
        self.assertEqual(sandbox.run(folder, 'agent.py', {'a': 1}), ('DONE', {'got': {'a': 1}}, ''))

    def test_no_network(self):
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen(5)
        server.settimeout(0.3)
        port = server.getsockname()[1]
        seen = []

        def accept():
            while True:
                try:
                    c, _ = server.accept()
                    seen.append(1)
                    c.close()
                except OSError:
                    return
        t = threading.Thread(target=accept)
        t.start()
        code = f'import socket\nsocket.create_connection(("127.0.0.1", {port}), 2)\nprint("{{}}")\n'
        folder = self._agent(code)
        try:
            state, answer, reason = sandbox.run(folder, 'agent.py', {})
            self.assertEqual((state, answer), ('FAILED', None))
            self.assertTrue(said(reason, 'network'), reason)
            self.assertEqual(seen, [], 'the sandboxed agent reached the listener')
            self.assertEqual(self._control(folder).returncode, 0)   # the control connects
            t.join(1)
            self.assertEqual(seen, [1], 'the control never connected: the plant is dead')
        finally:
            server.close()
            t.join()

    def test_no_write_outside_its_run_folder(self):
        target = pathlib.Path(self.tmp.name) / 'outside.txt'
        folder = self._agent(f'open({str(target)!r}, "w").write("x")\nprint("{{}}")\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'FAILED')
        self.assertTrue(said(reason, 'write outside'), reason)
        self.assertFalse(target.exists())
        self.assertEqual(self._control(folder).returncode, 0)
        self.assertTrue(target.exists(), 'the control never wrote: the plant is dead')

    def test_no_write_into_its_own_locker_folder(self):
        folder = self._agent('open(__file__ + ".new", "w").write("x")\nprint("{}")\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'FAILED')
        self.assertTrue(said(reason, 'write own folder'), reason)
        self.assertFalse((folder / 'agent.py.new').exists())

    def test_writes_inside_its_run_folder(self):
        folder = self._agent('import os, json\nopen("scratch.txt", "w").write("x")\nprint(json.dumps({"cwd_files": os.listdir(".")}))\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('DONE', {'cwd_files': ['scratch.txt']}, ''))

    def test_reads_nothing_private(self):
        """A file in the home folder of whoever runs the runtime (on macOS under /Users; on Linux, never mounted)."""
        with tempfile.NamedTemporaryFile(dir=pathlib.Path.home(), prefix='.hanzo_probe_') as probe:
            folder = self._agent(f'open({probe.name!r}).read()\nprint("{{}}")\n')
            state, _answer, reason = sandbox.run(folder, 'agent.py', {})
            self.assertEqual(state, 'FAILED')
            self.assertTrue(said(reason, 'read outside'), reason)
            self.assertEqual(self._control(folder).returncode, 0)

    def test_reads_no_system_file(self):
        """A file every Mac and Linux has, readable by anyone (/etc/hosts): never the agent's."""
        folder = self._agent('open("/etc/hosts").read()\nprint("{}")\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'FAILED')
        self.assertTrue(said(reason, 'read outside'), reason)
        self.assertEqual(self._control(folder).returncode, 0)

    def test_reads_no_other_project(self):
        """Another folder in the shared temporary area, beside the agent's own."""
        with tempfile.TemporaryDirectory(prefix='hanzo_other_project_') as other:
            notes = pathlib.Path(other) / 'notes.txt'
            notes.write_text('not yours')
            folder = self._agent(f'open({str(notes)!r}).read()\nprint("{{}}")\n')
            state, _answer, reason = sandbox.run(folder, 'agent.py', {})
            self.assertEqual(state, 'FAILED')
            self.assertTrue(said(reason, 'read outside'), reason)
            self.assertEqual(self._control(folder).returncode, 0)

    def test_a_normal_agent_uses_the_standard_library(self):
        folder = self._agent('import csv, datetime, decimal, hashlib, json, math, random, re, sqlite3, statistics\n'
                             'print(json.dumps({"n": str(decimal.Decimal("1.1") * 2), "db": sqlite3.connect(":memory:").execute("select 6*7").fetchone()[0]}))\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('DONE', {'n': '2.2', 'db': 42}, ''))

    def test_reads_its_own_folder(self):
        folder = self._agent('import json\nprint(json.dumps({"n": len(open(__file__).read()) > 0}))\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('DONE', {'n': True}, ''))

    def test_no_new_process(self):
        folder = self._agent('import subprocess\nsubprocess.run(["/bin/echo", "hi"], stdout=subprocess.DEVNULL)\nprint("{}")\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'FAILED')
        self.assertTrue(said(reason, 'process'), reason)
        self.assertEqual(self._control(folder).returncode, 0)

    def test_no_fork(self):
        folder = self._agent('import os\npid = os.fork()\nif pid == 0:\n    os._exit(0)\nos.waitpid(pid, 0)\nprint("{}")\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'FAILED')
        self.assertTrue(said(reason, 'process'), reason)
        self.assertEqual(self._control(folder).returncode, 0)

    def test_no_other_program(self):
        """exec without a fork: the agent's own process tries to become another program (it would answer "{}" if it did).
        (macOS lets the process become the Python runtime itself again, which a framework Python needs; Linux refuses
        every exec.)"""
        folder = self._agent('import os\nos.execv("/bin/echo", ["/bin/echo", "{}"])\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'FAILED')
        self.assertTrue(said(reason, 'process'), reason)
        self.assertEqual(self._control(folder).returncode, 0)

    def test_threads_still_work(self):
        folder = self._agent('import threading, json\nout = []\nt = threading.Thread(target=lambda: out.append(1))\nt.start(); t.join()\nprint(json.dumps({"n": len(out)}))\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('DONE', {'n': 1}, ''))

    def test_time_limit(self):
        folder = self._agent('import time\ntime.sleep(30)\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}, seconds=1), ('FAILED', None, 'over the time limit (1 s)'))

    def test_answer_must_be_one_json_object(self):
        folder = self._agent('print("hello")\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('FAILED', None, 'the answer is not one JSON object'))
        folder = self._agent('print("[1, 2]")\n', 'list')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('FAILED', None, 'the answer is not one JSON object'))

    def test_the_environment_is_empty(self):
        folder = self._agent('import os, json\nprint(json.dumps({"env": sorted(k for k in os.environ if k != "__CF_USER_TEXT_ENCODING")}))\n')
        state, answer, _ = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'DONE')
        self.assertEqual(answer, {'env': ['HOME', 'LC_CTYPE', 'PATH', 'TMPDIR']})

    def test_nothing_runs_without_a_sandbox(self):
        import unittest.mock
        with unittest.mock.patch.object(sandbox.sys, 'platform', 'plan9'):
            folder = self._agent(ECHO)
            self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('FAILED', None, 'no sandbox on this system: nothing runs unsandboxed'))


if __name__ == '__main__':
    unittest.main()
