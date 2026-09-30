"""ONE VERSION EVERYWHERE: pip, npm, cargo, the MCP registry entry and the plugin carry the same number, so the three
install lines always give the same LARRYD."""
import json
import pathlib
import re

from larryd import __version__

REPO = pathlib.Path(__file__).resolve().parent.parent


def versions():
    pyproject = (REPO / 'pyproject.toml').read_text()
    cargo = (REPO / 'cargo' / 'Cargo.toml').read_text()
    lock = (REPO / 'cargo' / 'Cargo.lock').read_text()
    server = json.loads((REPO / 'listings' / 'mcp-registry' / 'server.json').read_text())
    return {
        'pyproject.toml': re.search(r'^version = "(.+)"$', pyproject, re.M).group(1),
        'larryd.__version__': __version__,
        'npm/package.json': json.loads((REPO / 'npm' / 'package.json').read_text())['version'],
        'cargo/Cargo.toml': re.search(r'^version = "(.+)"$', cargo.split('[package]', 1)[1], re.M).group(1),
        'cargo/Cargo.lock': re.search(r'name = "larryd"\nversion = "(.+)"', lock).group(1),
        'listings/mcp-registry/server.json': server['version'],
        'listings/mcp-registry/server.json package': server['packages'][0]['version'],
        'plugin/.claude-plugin/plugin.json': json.loads((REPO / 'plugin' / '.claude-plugin' / 'plugin.json').read_text())['version'],
    }


def test_one_version_everywhere():
    found = versions()
    assert len(set(found.values())) == 1, found


def test_the_three_install_lines_name_the_same_package():
    assert json.loads((REPO / 'npm' / 'package.json').read_text())['name'] == 'larryd'
    assert re.search(r'^name = "larryd"$', (REPO / 'cargo' / 'Cargo.toml').read_text(), re.M)
    assert re.search(r'^name = "larryd"$', (REPO / 'pyproject.toml').read_text(), re.M)


def test_the_four_install_lines_in_the_owners_order():
    lines = '    npm install -g larryd\n    pip install larryd\n    cargo install larryd\n    sudo larryd &\n'
    for doc in ('README.md', 'GUIDE.md', 'listings/text.md'):
        assert lines in (REPO / doc).read_text(), doc
