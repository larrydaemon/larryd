"""ONE REPOSITORY, TWO PARTS (the owner, 2026-09-29): the runtime lives in server/. The pip package ships the tool and the
daemon's code (the runtime's code, as larryd_runtime), and never an instance, a secret, a database, a test or the deploy.
Neither part reaches into the other's code: the tool never names server/, the runtime never imports the tool."""
import pathlib
import re
import subprocess
import sys
import tarfile
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent


NEVER = ('instance', 'secrets', 'hanzo_link', 'tests', 'deploy', '.venv', '__pycache__')


def test_the_package_holds_the_tool_and_the_daemons_code_only(tmp_path):
    done = subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '-q', '-w', str(tmp_path), str(REPO)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    wheel = next(tmp_path.glob('larryd-*.whl'))
    names = zipfile.ZipFile(wheel).namelist()
    assert names and all(n.startswith(('larryd/', 'larryd_runtime/', 'larryd-')) for n in names), [n for n in names if not n.startswith(('larryd/', 'larryd_runtime/', 'larryd-'))]
    assert not [n for n in names if set(n.split('/')) & set(NEVER) or n.endswith('.db')], [n for n in names if set(n.split('/')) & set(NEVER) or n.endswith('.db')]
    runtime = {n for n in names if n.startswith('larryd_runtime/')}
    for needed in ('larryd_runtime/web/app.py', 'larryd_runtime/core_engine/sandbox.py', 'larryd_runtime/schemas/hanzo.json',
                   'larryd_runtime/schemas/store.json', 'larryd_runtime/agents/marketplace/agent.py'):
        assert needed in runtime, needed
    assert 'larryd_runtime/agents/dev' not in {n.rsplit('/', 1)[0] for n in runtime}   # a developer's agent never ships


def test_the_source_package_holds_no_instance_secret_test_or_deploy(tmp_path):
    done = subprocess.run([sys.executable, '-m', 'build', '--sdist', '--outdir', str(tmp_path), str(REPO)], capture_output=True, text=True)   # needs `build` (pip install build)
    assert done.returncode == 0, done.stderr
    names = tarfile.open(next(tmp_path.glob('larryd-*.tar.gz'))).getnames()
    bad = [n for n in names if '/server/' in n and (set(n.split('/')) & set(NEVER) or n.endswith('.db'))]
    assert not bad, bad
    assert any(n.endswith('/server/hanzo/app/web/app.py') for n in names)   # the daemon's code builds from the source package


def test_the_tool_never_names_the_runtime():
    for path in (REPO / 'larryd').rglob('*.py'):
        assert not re.search(r'\bserver/|\bfrom server\b|import server\b|hanzo/app', path.read_text()), path.name


def test_the_runtime_never_imports_the_tool():
    for path in (REPO / 'server').rglob('*.py'):
        if '.venv' in path.parts:
            continue
        assert not re.search(r'^\s*(from|import)\s+larryd\b', path.read_text(), re.M), path.name
