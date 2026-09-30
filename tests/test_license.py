"""One license, Apache-2.0, in every package LARRYD ships: pip, the plugin, npm and cargo."""
import json
import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_every_package_carries_the_same_license_text():
    text = (ROOT / 'LICENSE').read_text()
    assert text.startswith('\n                                 Apache License') or 'Apache License\n                           Version 2.0' in text
    for folder in ('plugin', 'npm', 'cargo'):
        assert (ROOT / folder / 'LICENSE').read_text() == text, folder


def test_every_package_names_apache_2():
    assert tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['license'] == 'Apache-2.0'
    assert tomllib.loads((ROOT / 'cargo' / 'Cargo.toml').read_text())['package']['license'] == 'Apache-2.0'
    npm = json.loads((ROOT / 'npm' / 'package.json').read_text())
    assert npm['license'] == 'Apache-2.0' and 'LICENSE' in npm['files']
    assert json.loads((ROOT / 'plugin' / '.claude-plugin' / 'plugin.json').read_text())['license'] == 'Apache-2.0'


def test_no_package_still_says_all_rights_reserved():
    for path in ('README.md', 'npm/README.md', 'cargo/README.md', 'plugin/README.md'):
        assert 'All rights reserved' not in (ROOT / path).read_text(), path
