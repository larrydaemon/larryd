"""THE CMO OFFICE'S AGENT, LARRYD RUNTIME INTERNAL (moved from ~/virtual_sanity/cmo 2026-11-03). LARRYD runs this file as this computer's
own process (agent.json "internal"); it hands the call to the office's own code beside it (cmo/app/bridge.py), run by the workspace's
Python (the office's own interpreter: flask, jinja2, the platform's pipeline), its state at LARRYD RUNTIME INTERNAL's data/cmo.
One JSON in on stdin, one JSON out on stdout; a red RUN ends with an error, as the office's run ended FAILED."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'office_agent.txt'), encoding='utf-8') as _fh:
    KEY = _fh.read().strip()   # which of the office's agents this card is (its KEY in cmo/app/agent/)
PYTHON = os.path.expanduser('~/virtual_workspace/.venv/bin/python')   # the office's own interpreter (its launcher's PY)
APP = os.path.join(HERE, 'cmo', 'app')
DATA = os.path.expanduser('~/larryd/server/runtime/internal/instance/data/cmo')


def main():
    given = sys.stdin.read()
    env = {**os.environ, 'PYTHONPATH': APP, 'REPLICA_OFFICE_APP': APP, 'REPLICA_INSTANCE': DATA, 'PYTHONDONTWRITEBYTECODE': '1'}
    env.pop('LARRYD_INTERNAL', None)
    got = subprocess.run([PYTHON, '-B', os.path.join(APP, 'bridge.py'), KEY], input=given, capture_output=True, text=True, cwd=APP, env=env)
    if got.returncode != 0:
        sys.stderr.write(got.stderr[-4000:])
        raise SystemExit(got.returncode)
    sys.stdout.write(got.stdout)


if __name__ == '__main__':
    main()
