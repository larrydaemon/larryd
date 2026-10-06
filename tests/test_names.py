"""THE NAME A DEVELOPER READS (the owner, 2026-09-30: "every one will call and think of this as larryd"): the place an
agent runs is LARRYD. The public lines say so."""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent


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
