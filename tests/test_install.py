"""Step 1: `pip install` of the package from the repo gives one command, `larryd`, in a fresh environment."""
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent


def test_pip_install_gives_the_larryd_command(tmp_path):
    env = tmp_path / 'venv'
    subprocess.run([sys.executable, '-m', 'venv', str(env)], check=True)
    done = subprocess.run([str(env / 'bin' / 'pip'), 'install', '-q', str(REPO)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    larryd = env / 'bin' / 'larryd'
    assert larryd.is_file()
    work = tmp_path / 'work'
    work.mkdir()
    made = subprocess.run([str(larryd), 'new', 'first'], capture_output=True, text=True, cwd=work)
    assert made.returncode == 0, made.stderr
    card = json.loads((work / 'first' / 'agent' / 'agent.json').read_text())
    assert card['name'] == 'first'
    assert (work / 'first' / 'CLAUDE.md').is_file() and (work / 'first' / '.claude' / 'skills' / 'larryd' / 'SKILL.md').is_file()
