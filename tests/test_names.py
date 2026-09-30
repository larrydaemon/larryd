"""THE NAME A DEVELOPER READS (the owner, 2026-09-30: "every one will call and think of this as larryd"): the place an
agent runs is LARRYD. No developer-facing file or message says "HANZO" (the internal name stays in the code's comments
and docstrings, the tests and the handoff). The public lines never name it either."""
import ast
import pathlib

from larryd import new

REPO = pathlib.Path(__file__).resolve().parent.parent
READ = ['README.md', 'GUIDE.md', 'pyproject.toml', 'larryd/skills.json', '.claude-plugin/marketplace.json',
        'plugin/.claude-plugin/plugin.json', 'plugin/.mcp.json', 'plugin/skills/larryd/SKILL.md'] + [
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
    readme = (REPO / 'README.md').read_text().splitlines()
    guide = (REPO / 'GUIDE.md').read_text().splitlines()
    summary = 'Your server has a daemon. Your agents should have one too.'
    assert readme[2] == summary and guide[2] == summary
    assert readme[4] == guide[4] == 'Build, test and ship AI agents with Claude Code.'
    assert f'description = "{summary}"' in (REPO / 'pyproject.toml').read_text()
