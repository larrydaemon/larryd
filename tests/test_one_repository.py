"""ONE REPOSITORY, TWO PARTS (the owner, 2026-09-29): the pip package is the tool only; the runtime lives in server/ and
never ships in it. Neither part reaches into the other: the tool never names server/, the runtime never imports the tool."""
import pathlib
import re
import subprocess
import sys
import tarfile
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent


def test_the_package_holds_no_server_file(tmp_path):
    done = subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '-q', '-w', str(tmp_path), str(REPO)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    wheel = next(tmp_path.glob('larryd-*.whl'))
    names = zipfile.ZipFile(wheel).namelist()
    assert names and all(n.startswith(('larryd/', 'larryd-')) for n in names), [n for n in names if not n.startswith(('larryd/', 'larryd-'))]
    assert not [n for n in names if 'server' in n.split('/') or 'hanzo/app' in n]


def test_the_source_package_holds_no_server_file(tmp_path):
    done = subprocess.run([sys.executable, '-m', 'build', '--sdist', '--outdir', str(tmp_path), str(REPO)], capture_output=True, text=True)   # needs `build` (pip install build)
    assert done.returncode == 0, done.stderr
    names = tarfile.open(next(tmp_path.glob('larryd-*.tar.gz'))).getnames()
    assert not [n for n in names if '/server/' in n or n.endswith('/server')], [n for n in names if 'server' in n]


def test_the_tool_never_names_the_runtime():
    for path in (REPO / 'larryd').rglob('*.py'):
        assert not re.search(r'\bserver/|\bfrom server\b|import server\b|hanzo/app', path.read_text()), path.name


def test_the_runtime_never_imports_the_tool():
    for path in (REPO / 'server').rglob('*.py'):
        if '.venv' in path.parts:
            continue
        assert not re.search(r'^\s*(from|import)\s+larryd\b', path.read_text(), re.M), path.name
