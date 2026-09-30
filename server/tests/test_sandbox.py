"""THE SANDBOX, proven on the real machine: each plant is also run WITHOUT the sandbox (the control), so a green test
means the sandbox stopped it, not that the plant never worked."""
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
            self.assertIn('Operation not permitted', reason)
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
        self.assertIn('Operation not permitted', reason)
        self.assertFalse(target.exists())
        self.assertEqual(self._control(folder).returncode, 0)
        self.assertTrue(target.exists(), 'the control never wrote: the plant is dead')

    def test_no_write_into_its_own_locker_folder(self):
        folder = self._agent('open(__file__ + ".new", "w").write("x")\nprint("{}")\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {})[0], 'FAILED')
        self.assertFalse((folder / 'agent.py.new').exists())

    def test_writes_inside_its_run_folder(self):
        folder = self._agent('import os, json\nopen("scratch.txt", "w").write("x")\nprint(json.dumps({"cwd_files": os.listdir(".")}))\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('DONE', {'cwd_files': ['scratch.txt']}, ''))

    def test_reads_nothing_under_users(self):
        with tempfile.NamedTemporaryFile(dir=pathlib.Path.home(), prefix='.hanzo_probe_') as probe:   # under /Users
            self.assertTrue(os.path.realpath(probe.name).startswith('/Users/'))
            folder = self._agent(f'open({probe.name!r}).read()\nprint("{{}}")\n')
            state, _answer, reason = sandbox.run(folder, 'agent.py', {})
            self.assertEqual(state, 'FAILED')
            self.assertIn('Operation not permitted', reason)
            self.assertEqual(self._control(folder).returncode, 0)

    def test_reads_its_own_folder(self):
        folder = self._agent('import json\nprint(json.dumps({"n": len(open(__file__).read()) > 0}))\n')
        self.assertEqual(sandbox.run(folder, 'agent.py', {}), ('DONE', {'n': True}, ''))

    def test_no_new_process(self):
        folder = self._agent('import subprocess\nsubprocess.run(["/bin/echo", "hi"], stdout=subprocess.DEVNULL)\nprint("{}")\n')
        state, _answer, reason = sandbox.run(folder, 'agent.py', {})
        self.assertEqual(state, 'FAILED')
        self.assertIn('Operation not permitted', reason)
        self.assertEqual(self._control(folder).returncode, 0)

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


if __name__ == '__main__':
    unittest.main()
