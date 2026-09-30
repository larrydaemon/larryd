"""THE NAME A DEVELOPER READS (the owner, 2026-09-30: "every one will call and think of this as larryd"): the place an
agent runs is LARRYD. No developer-facing file or message says "HANZO" (the internal name stays in the code's comments
and docstrings, the tests and the handoff). The public lines never name it either."""
import ast
import json
import pathlib

from larryd import new

REPO = pathlib.Path(__file__).resolve().parent.parent
READ = ['README.md', 'GUIDE.md', 'larryd/skills.json', '.claude-plugin/marketplace.json',
        'plugin/.claude-plugin/plugin.json', 'plugin/.mcp.json', 'plugin/skills/larryd/SKILL.md', 'plugin/README.md'] + [
        p.relative_to(REPO).as_posix() for p in (REPO / 'listings').rglob('*') if p.is_file()] + [
        p.relative_to(REPO).as_posix() for p in (REPO / 'larryd' / 'kit').rglob('*') if p.is_file()]


def said(path):
    """Every string literal in a module that is not a docstring: what the code can show a developer."""
    tree = ast.parse(path.read_text())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docs.add(id(first.value))
    return [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


def test_the_package_s_own_words_never_say_hanzo():
    """pyproject.toml's [project] (the name, the description, what PyPI shows); its build settings may name the runtime's folder."""
    text = (REPO / 'pyproject.toml').read_text()
    project = text.split('[project]', 1)[1].split('\n[', 1)[0]
    assert project.strip() and 'HANZO' not in project.upper()


def test_no_developer_facing_file_says_hanzo():
    for rel in READ:
        assert 'HANZO' not in (REPO / rel).read_text().upper(), rel


def test_no_message_in_the_code_says_hanzo():
    for path in sorted((REPO / 'larryd').glob('*.py')):
        for n in said(path):
            assert 'HANZO' not in n.value, f'{path.name}:{n.lineno}: {n.value[:80]}'


def test_a_made_project_never_says_hanzo(tmp_path):
    root = new.make('named', tmp_path)
    for path in root.rglob('*'):
        if path.is_file():
            assert 'HANZO' not in path.read_text().upper(), path.name


def test_the_public_lines():
    readme = [line for line in (REPO / 'README.md').read_text().splitlines() if not line.startswith('<!--')]   # the registry's mcp-name line is not a line people read
    readme = readme[:1] + readme[2:] if readme[1] == '' and readme[2] == '' else readme
    guide = (REPO / 'GUIDE.md').read_text().splitlines()
    summary = 'Your server has a daemon. Your agents should have one too.'
    assert readme[2] == summary and guide[2] == summary
    assert readme[4] == guide[4] == 'Build, test and ship AI agents with Claude Code.'
    both = f'{summary} Build, test and ship AI agents with Claude Code.'   # one description on every registry: the hook, then what it is
    assert f'description = "{both}"' in (REPO / 'pyproject.toml').read_text() and f'description = "{both}"' in (REPO / 'cargo' / 'Cargo.toml').read_text()
    assert json.loads((REPO / 'npm' / 'package.json').read_text())['description'] == both


def test_every_registry_points_at_larryd_ai_never_elsewhere():
    py = (REPO / 'pyproject.toml').read_text()
    assert 'Homepage = "https://larryd.ai"' in py
    assert 'homepage = "https://larryd.ai"' in (REPO / 'cargo' / 'Cargo.toml').read_text()
    assert json.loads((REPO / 'npm' / 'package.json').read_text())['homepage'] == 'https://larryd.ai'
    for path in ('pyproject.toml', 'cargo/Cargo.toml', 'npm/package.json', 'README.md', 'GUIDE.md', 'larryd/submit.py'):
        assert 'larryllm' not in (REPO / path).read_text().lower(), path
