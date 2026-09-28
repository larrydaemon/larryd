"""THE SANDBOX: every agent runs as its own process under macOS sandbox-exec, with nothing but what it is handed.
- no network at all (the harness makes every call; an agent never does);
- no new process;
- writes only in its own run folder (made for the run, removed after), never into the locker;
- reads nothing under /Users except its own folder (the python runtime lives outside /Users);
- an empty environment, one JSON object in on stdin, one JSON object out on stdout, inside the time limit.
Anything else is FAILED with the reason."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

_BASE = os.path.realpath(sys.base_prefix)
_FRAMEWORK = os.path.join(_BASE, 'Resources', 'Python.app', 'Contents', 'MacOS', 'Python')   # a framework python3 only spawns this
PYTHON = _FRAMEWORK if os.path.isfile(_FRAMEWORK) else os.path.realpath(os.path.join(_BASE, 'bin', 'python3'))
SANDBOX_EXEC = '/usr/bin/sandbox-exec'
MOST_BYTES = 1_000_000


def _profile(agent, run):
    return f'''(version 1)
(allow default)
(deny network*)
(deny process-fork)
(deny process-exec)
(allow process-exec (literal "{PYTHON}"))
(deny file-write*)
(allow file-write* (subpath "{run}") (literal "/dev/null"))
(deny file-read* (subpath "/Users"))
(allow file-read* (subpath "{agent}") (subpath "{run}"))
'''


def run(folder, entry, given, seconds=20):
    """-> (state, answer, reason): ('DONE', {...}, '') or ('FAILED', None, why)."""
    agent = os.path.realpath(folder)
    run_dir = os.path.realpath(tempfile.mkdtemp(prefix='hanzo_run_'))
    try:
        try:
            done = subprocess.run([SANDBOX_EXEC, '-p', _profile(agent, run_dir), PYTHON, '-I', '-B', str(pathlib.Path(agent) / entry)],
                                  input=json.dumps(given), capture_output=True, text=True, timeout=seconds, cwd=run_dir,
                                  env={'PATH': '/usr/bin:/bin', 'HOME': run_dir, 'TMPDIR': run_dir, 'LC_CTYPE': 'UTF-8'})
        except subprocess.TimeoutExpired:
            return 'FAILED', None, f'over the time limit ({seconds} s)'
        if done.returncode != 0:
            last = (done.stderr.strip().splitlines() or [f'exit {done.returncode}'])[-1]
            return 'FAILED', None, last[-300:]
        if len(done.stdout) > MOST_BYTES:
            return 'FAILED', None, 'the answer is too long'
        try:
            answer = json.loads(done.stdout)
        except ValueError:
            answer = None
        if not isinstance(answer, dict):
            return 'FAILED', None, 'the answer is not one JSON object'
        return 'DONE', answer, ''
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
