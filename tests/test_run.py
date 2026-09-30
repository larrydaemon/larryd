"""Step 3: `larryd run`. Each sandbox rule is proven by a planted agent that breaks it, with a control run of the same
code outside the sandbox that succeeds (so the plant is real, and the refusal is the sandbox's)."""
import json
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

import pytest

from larryd import cli, new, runner

# what each system says when the sandbox refuses (Linux: bubblewrap hides what the agent may not see, and a mount is
# read-only, where macOS says "Operation not permitted"; the seccomp filter says "Operation not permitted" too)
LINUX = sys.platform.startswith('linux')
SAYS = {
    'network': ('Network is unreachable', 'Connection refused') if LINUX else ('Operation not permitted',),
    'read outside': ('No such file or directory',) if LINUX else ('Operation not permitted',),
    'process': ('not permitted',),
}


def _said(result, what):
    return result.state == 'FAILED' and any(words in result.said for words in SAYS[what])


def _agent(tmp_path, body):
    """A planted agent folder: `body` answers with the dict `out`, given the job `job`."""
    folder = tmp_path / 'planted'
    folder.mkdir()
    (folder / 'agent.py').write_text('import json, sys\njob = json.load(sys.stdin)\nout = {}\n' + body + '\nprint(json.dumps(out))\n')
    return folder


def _outside(folder, given):
    """The control: the same agent run by the same plain runtime, outside the sandbox."""
    done = subprocess.run([runner.python(), '-I', '-B', str(folder / 'agent.py')], input=json.dumps(given), capture_output=True, text=True, cwd=folder)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_a_clean_agent_answers(tmp_path):
    folder = _agent(tmp_path, 'out["delivery"] = "hello " + job["do"]')
    assert runner.sandboxed(folder, 'agent.py', {'do': 'answer'}).answer == {'delivery': 'hello answer'}


@pytest.fixture
def listening():
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen()

    def serve():
        try:
            while True:
                server.accept()[0].close()
        except OSError:
            return   # the fixture closed the server
    threading.Thread(target=serve, daemon=True).start()
    yield server.getsockname()[1]
    server.close()


def test_no_network(tmp_path, listening):
    folder = _agent(tmp_path, 'import socket\ns = socket.create_connection(("127.0.0.1", job["port"]), timeout=3)\nout["connected"] = True')
    assert _outside(folder, {'port': listening}) == {'connected': True}
    result = runner.sandboxed(folder, 'agent.py', {'port': listening})
    assert _said(result, 'network')


def test_no_new_process(tmp_path):
    folder = _agent(tmp_path, 'import subprocess\nout["said"] = subprocess.run(["/bin/echo", "hi"], capture_output=True, text=True).stdout')
    assert _outside(folder, {}) == {'said': 'hi\n'}
    result = runner.sandboxed(folder, 'agent.py', {})
    assert _said(result, 'process')


def test_no_fork(tmp_path):
    folder = _agent(tmp_path, 'import os\npid = os.fork()\nif pid == 0:\n    os._exit(0)\nos.waitpid(pid, 0)\nout["forked"] = True')
    assert _outside(folder, {}) == {'forked': True}
    result = runner.sandboxed(folder, 'agent.py', {})
    assert _said(result, 'process')


def test_no_other_program(tmp_path):
    """exec without a fork: the agent's own process tries to become another program."""
    folder = _agent(tmp_path, 'import os\nos.execv("/bin/echo", ["/bin/echo", "{}"])')
    assert _outside(folder, {}) == {}
    result = runner.sandboxed(folder, 'agent.py', {})
    assert _said(result, 'process')


def test_no_write_outside_the_run_folder(tmp_path):
    target = tmp_path / 'outside'
    target.mkdir()
    folder = _agent(tmp_path, 'open(job["to"], "w").write("x")\nout["wrote"] = True')
    assert _outside(folder, {'to': str(target / 'control.txt')}) == {'wrote': True}
    result = runner.sandboxed(folder, 'agent.py', {'to': str(target / 'planted.txt')})
    assert result.state == 'FAILED' and not (target / 'planted.txt').exists()


def test_no_write_into_its_own_folder(tmp_path):
    folder = _agent(tmp_path, 'open(job["to"], "w").write("x")\nout["wrote"] = True')
    result = runner.sandboxed(folder, 'agent.py', {'to': str(folder / 'changed.py')})
    assert result.state == 'FAILED' and not (folder / 'changed.py').exists()


def test_writes_in_its_run_folder_and_the_folder_is_gone_after(tmp_path):
    folder = _agent(tmp_path, 'import os\nopen("work.txt", "w").write("x")\nout["here"] = os.getcwd()')
    result = runner.sandboxed(folder, 'agent.py', {})
    assert result.state == 'DONE'
    assert not pathlib.Path(result.answer['here']).exists()


def test_no_read_in_the_home_folder_outside_its_folder(tmp_path):
    scratch = pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.home(), prefix='.larryd_test_'))   # a scratch file under /Users, removed after
    try:
        (scratch / 'private.txt').write_text('private')
        folder = _agent(tmp_path, 'out["read"] = open(job["from"]).read()')
        assert _outside(folder, {'from': str(scratch / 'private.txt')}) == {'read': 'private'}
        result = runner.sandboxed(folder, 'agent.py', {'from': str(scratch / 'private.txt')})
        assert _said(result, 'read outside')
    finally:
        shutil.rmtree(scratch)


def test_no_read_of_system_files(tmp_path):
    """A file every Mac and Linux has, readable by anyone: the agent reads nothing it is not handed (/etc/hosts)."""
    folder = _agent(tmp_path, 'out["read"] = open("/etc/hosts").read()[:1]')
    assert 'read' in _outside(folder, {})
    assert _said(runner.sandboxed(folder, 'agent.py', {}), 'read outside')


def test_no_read_of_another_project(tmp_path):
    """Another folder in the shared temporary area, beside the agent's own (another project, another run)."""
    other = pathlib.Path(tempfile.mkdtemp(prefix='larryd_other_project_'))
    try:
        (other / 'notes.txt').write_text('not yours')
        folder = _agent(tmp_path, 'out["read"] = open(job["from"]).read()')
        assert _outside(folder, {'from': str(other / 'notes.txt')}) == {'read': 'not yours'}
        assert _said(runner.sandboxed(folder, 'agent.py', {'from': str(other / 'notes.txt')}), 'read outside')
    finally:
        shutil.rmtree(other)


def test_the_standard_library_still_works(tmp_path):
    """Sealed tight, a normal agent still starts and uses the standard library (its compiled parts included)."""
    body = ('import csv, datetime, decimal, hashlib, math, random, re, sqlite3, statistics, pathlib\n'
            'here = pathlib.Path(__file__).parent\n'
            'out["own"] = (here / "data.txt").read_text()\n'
            'out["sum"] = str(decimal.Decimal("1.1") * 2) + hashlib.sha256(b"x").hexdigest()[:4]\n'
            'out["db"] = sqlite3.connect(":memory:").execute("select 6*7").fetchone()[0]')
    folder = _agent(tmp_path, body)
    (folder / 'data.txt').write_text('mine')
    result = runner.sandboxed(folder, 'agent.py', {})
    assert result.state == 'DONE', result.said
    assert result.answer == {'own': 'mine', 'sum': '2.22d71', 'db': 42}


def test_the_plain_runtime_only(tmp_path):
    folder = _agent(tmp_path, 'import pytest\nout["had"] = True')
    done = subprocess.run([sys.executable, str(folder / 'agent.py')], input='{}', capture_output=True, text=True)
    assert done.returncode == 0   # control: this environment has pytest installed
    result = runner.sandboxed(folder, 'agent.py', {})
    assert result.state == 'FAILED' and 'ModuleNotFoundError' in result.said


def test_an_empty_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('LARRYD_PLANTED', 'secret-value')
    folder = _agent(tmp_path, 'import os\nout["env"] = sorted(os.environ)')
    assert 'LARRYD_PLANTED' in _outside(folder, {})['env']
    result = runner.sandboxed(folder, 'agent.py', {})
    assert result.state == 'DONE' and 'LARRYD_PLANTED' not in result.answer['env']


def test_the_time_limit(tmp_path):
    folder = _agent(tmp_path, 'while True:\n    pass')
    result = runner.sandboxed(folder, 'agent.py', {}, seconds=2)
    assert result.state == 'FAILED' and 'time limit' in result.reason


@pytest.mark.parametrize('body, why', [
    ('print("not json")\nraise SystemExit(0)', 'not one JSON object'),
    ('print("[1, 2]")\nraise SystemExit(0)', 'not one JSON object'),
    ('raise ValueError("broken")', 'exit 1'),
])
def test_a_bad_answer(tmp_path, body, why):
    result = runner.sandboxed(_agent(tmp_path, body), 'agent.py', {})
    assert result.state == 'FAILED' and why in result.reason and result.todo


# ---------------------------------------------------------------- which sandbox, by system
def test_a_mac_runs_it_under_sandbox_exec(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.sys, 'platform', 'darwin')
    real = runner.os.path.isfile
    monkeypatch.setattr(runner.os.path, 'isfile', lambda p: p == runner.SANDBOX or real(p))
    assert runner.no_sandbox() is None
    cmd = runner.command('/a', '/r', 'agent.py')
    assert cmd[:2] == [runner.SANDBOX, '-p'] and '(deny network*)' in cmd[2] and cmd[-1] == '/a/agent.py'


def test_linux_runs_it_in_the_runtimes_own_bubblewrap(monkeypatch):
    from larryd_runtime.core_engine import sandbox
    monkeypatch.setattr(sandbox, '_linux_runtime', lambda: [sandbox.PYTHON])   # sysconfig reads the real system, not a pretended one
    monkeypatch.setattr(runner.sys, 'platform', 'linux')
    real = runner.os.path.isfile
    monkeypatch.setattr(runner.os.path, 'isfile', lambda p: p == sandbox.BWRAP or real(p))
    assert runner.no_sandbox() is None
    cmd = runner.command('/a', '/r', 'agent.py')
    assert cmd == sandbox._linux_command('/a', '/r', 'agent.py')   # the very command a RUN on LARRYD gets
    assert cmd[0] == sandbox.BWRAP and '--unshare-all' in cmd and 'seccomp' in cmd[cmd.index('-c') + 1]


def test_linux_without_bubblewrap_is_refused_with_what_to_do(tmp_path, monkeypatch):
    from larryd_runtime.core_engine import sandbox
    monkeypatch.setattr(runner.sys, 'platform', 'linux')
    real = runner.os.path.isfile
    monkeypatch.setattr(runner.os.path, 'isfile', lambda p: p != sandbox.BWRAP and real(p))
    result = runner.sandboxed(_agent(tmp_path, 'out["ran"] = True'), 'agent.py', {})
    assert result.state == 'REFUSED' and 'bubblewrap' in result.reason and 'apt install bubblewrap' in result.todo


def test_windows_is_refused_and_nothing_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.sys, 'platform', 'win32')
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **k: pytest.fail('nothing runs unsandboxed'))
    result = runner.sandboxed(_agent(tmp_path, 'out["ran"] = True'), 'agent.py', {})
    assert result.state == 'REFUSED' and 'a Mac or Linux' in result.reason and 'WSL' in result.todo


# ---------------------------------------------------------------- the whole `larryd run`
@pytest.fixture
def project(tmp_path):
    return new.make('runner', tmp_path)


def _card(root, **fields):
    path = root / 'agent' / 'agent.json'
    card = json.loads(path.read_text())
    card.update(fields)
    path.write_text(json.dumps(card))


def test_the_made_agent_runs(project):
    result = runner.run(project)
    assert result.state == 'DONE' and result.answer == {'delivery': 'runner answered the job.'}


def test_the_doctor_comes_first(project):
    path = project / 'agent' / 'agent.py'
    path.write_text(path.read_text() + '\nimport socket\n')
    result = runner.run(project)
    assert result.state == 'REFUSED' and result.problems and result.problems[0].check == 'the air gap'


def test_the_job_is_what_hanzo_hands(project):
    (project / 'samples' / 'job.json').write_text('{"do": "answer", "members": []}')
    assert 'would not hand' in runner.run(project).reason
    (project / 'samples' / 'job.json').write_text('{"do": "sing"}')
    assert 'a RUN does "answer"' in runner.run(project).reason
    _card(project, run={'do': 'answer', 'hands': ['cards']})
    (project / 'samples' / 'job.json').write_text('{"do": "answer"}')
    assert "has no ['cards']" in runner.run(project).reason
    (project / 'samples' / 'job.json').write_text('{"do": "answer", "cards": []}')
    assert runner.run(project).state == 'DONE'


def test_the_answer_holds_only_what_gives_names(project):
    path = project / 'agent' / 'agent.py'
    path.write_text(path.read_text().replace("return {'delivery':", "return {'extra': 1, 'delivery':"))
    result = runner.run(project)
    assert result.state == 'FAILED' and "['extra']" in result.reason


def test_the_command(project, capsys):
    assert cli.main(['run', str(project)]) == 0
    assert 'larryd run: DONE' in capsys.readouterr().out
    other = project / 'other.json'
    other.write_text('{"do": "sing"}')
    assert cli.main(['run', str(project), '--job', str(other), '--json']) == 1
    assert json.loads(capsys.readouterr().out)['state'] == 'REFUSED'
