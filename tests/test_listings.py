"""THE LISTINGS (sprint item 12, prepared, nothing submitted): what a listing says agrees with the package it lists."""
import json
import pathlib
import re

from larryd import __version__

REPO = pathlib.Path(__file__).resolve().parent.parent


def test_the_registry_entry_is_this_package():
    server = json.loads((REPO / 'listings' / 'mcp-registry' / 'server.json').read_text())
    pyproject = (REPO / 'pyproject.toml').read_text()
    version = re.search(r'^version = "(.+)"$', pyproject, re.M).group(1)
    assert server['version'] == server['packages'][0]['version'] == version == __version__
    assert server['packages'][0]['identifier'] == re.search(r'^name = "(.+)"$', pyproject, re.M).group(1)
    assert server['packages'][0]['packageArguments'] == [{'type': 'positional', 'value': 'mcp'}]   # the command `larryd mcp`
    assert len(server['description']) <= 100
    assert f'<!-- mcp-name: {server["name"]} -->' in (REPO / 'README.md').read_text()   # the registry's check of PyPI ownership


def test_the_image_starts_the_tool_server_and_names_it():
    dockerfile = (REPO / 'listings' / 'docker' / 'Dockerfile').read_text()
    server = json.loads((REPO / 'listings' / 'mcp-registry' / 'server.json').read_text())
    assert f'LABEL io.modelcontextprotocol.server.name="{server["name"]}"' in dockerfile
    assert 'ENTRYPOINT ["larryd", "mcp"]' in dockerfile


def test_the_plugin_folder_has_a_readme_a_directory_takes():
    words = (REPO / 'plugin' / 'README.md').read_text().split()
    assert len(words) >= 40


def test_the_short_line_fits_where_a_line_is_short():
    text = (REPO / 'listings' / 'text.md').read_text()
    short = text.split('## Short (100 characters or fewer)\n', 1)[1].split('\n', 1)[0]
    assert 0 < len(short) <= 100
    assert 'Your server has a daemon. Your agents should have one too.' in text
