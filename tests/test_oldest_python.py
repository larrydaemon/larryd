"""THE OLDEST PYTHON LARRYD SUPPORTS (requires-python >= 3.11; Debian 12's): every Python file of the tool and of the
runtime compiles under a real Python 3.11. (A nested f-string with the same quotes, fine on 3.12+, once broke the whole
command on 3.11: caught on the server.)"""
import pathlib
import re
import shutil
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent


def oldest():
    floor = re.search(r'^requires-python = ">=(\d+\.\d+)"$', (REPO / 'pyproject.toml').read_text(), re.M).group(1)
    return floor, shutil.which(f'python{floor}') or next((p for p in (f'/opt/homebrew/bin/python{floor}', f'/usr/bin/python{floor}') if pathlib.Path(p).is_file()), None)


def test_everything_compiles_on_the_oldest_python():
    floor, python = oldest()
    assert python, f'Python {floor}, the oldest LARRYD supports, is needed to run this test (brew install python@{floor})'
    files = [p for p in (REPO / 'larryd').rglob('*.py') if 'kit' not in p.parts]   # kit/ holds templates, filled in by `larryd new`
    files += [p for p in (REPO / 'server' / 'hanzo').rglob('*.py') if '.venv' not in p.parts]
    code = 'import sys, ast\nfor f in sys.argv[1:]:\n    ast.parse(open(f, encoding="utf-8").read(), filename=f)\n'
    done = subprocess.run([python, '-c', code, *map(str, files)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert len(files) > 20
