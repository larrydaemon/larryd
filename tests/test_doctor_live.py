"""The doctor and an agent's own live page ("live"): the manifest's field, and the live half beside agent/ (page.html,
page.js, room.py, live.json and nothing else; no outside address; the standard library only; nothing that calls out)."""
import json

import pytest

from larryd import doctor, new

PAGE = '<!doctype html><html><head><!--sheets--></head><body><main id="talk"></main><script src="/page.js" defer></script></body></html>'
SCRIPT = "'use strict';\nfetch('/me');\n"
PROGRAM = 'import asyncio\nimport json\n\n\nasync def main():\n    await asyncio.start_server(lambda r, w: None, "127.0.0.1", 0)\n'


@pytest.fixture
def agent(tmp_path):
    root = new.make('planted', tmp_path)
    card = json.loads((root / 'agent' / 'agent.json').read_text())
    card['calls'] = [card['does'][0]]
    card['live'] = {'seats': 4}
    (root / 'agent' / 'agent.json').write_text(json.dumps(card))
    half = root / 'live'
    half.mkdir()
    (half / 'page.html').write_text(PAGE)
    (half / 'page.js').write_text(SCRIPT)
    (half / 'room.py').write_text(PROGRAM)
    (half / 'live.json').write_text(json.dumps({'seats': 4}))
    return root


def _wrongs(root):
    return [p.wrong for p in doctor.check(root) if p.check == 'the manifest']


def _live(root, value):
    card = json.loads((root / 'agent' / 'agent.json').read_text())
    card['live'] = value
    (root / 'agent' / 'agent.json').write_text(json.dumps(card))


def test_a_declared_live_page_passes(agent):
    assert doctor.check(agent) == []


@pytest.mark.parametrize('value', ['yes', {}, {'seats': 0}, {'seats': 5}, {'seats': '4'}, {'seats': True}, {'seats': 4, 'guests': True}])
def test_the_field_is_seats_one_to_four_and_nothing_else(agent, value):
    _live(agent, value)
    assert any('"live" is not {"seats": 1 to 4}' in w for w in _wrongs(agent))


def test_live_needs_a_call(agent):
    card = json.loads((agent / 'agent' / 'agent.json').read_text())
    card['calls'] = []
    (agent / 'agent' / 'agent.json').write_text(json.dumps(card))
    assert '"live" is declared, but "calls" is empty' in _wrongs(agent)


def test_live_needs_its_folder(agent):
    for part in (agent / 'live').iterdir():
        part.unlink()
    (agent / 'live').rmdir()
    assert any('no live/ folder' in w for w in _wrongs(agent))


def test_a_missing_part_is_named(agent):
    (agent / 'live' / 'room.py').unlink()
    assert 'live/ has no room.py' in _wrongs(agent)


def test_nothing_else_sits_in_the_live_half(agent):
    (agent / 'live' / 'extra.css').write_text('body { color: red }')
    assert 'live/ holds something that is not part of the live half' in _wrongs(agent)


@pytest.mark.parametrize('line', ["fetch('https://example.com/x');", "new WebSocket('wss://example.com');", "var s = '//cdn.example.com/a.js';"])
def test_the_script_names_no_outside_address(agent, line):
    (agent / 'live' / 'page.js').write_text(SCRIPT + line + '\n')
    assert 'the live page names an outside address' in _wrongs(agent)


@pytest.mark.parametrize('line', ['eval(x);', 'var f = new Function("a", "return a");', 'box.innerHTML = words;', 'document.write(words);'])
def test_the_script_builds_nothing_from_text(agent, line):
    (agent / 'live' / 'page.js').write_text(SCRIPT + line + '\n')
    assert 'the live page builds code or markup from text' in _wrongs(agent)


@pytest.mark.parametrize('page', [PAGE.replace('</body>', '<script>alert(1)</script></body>'), PAGE.replace('<main', '<main style="color:red"'),
                                  PAGE.replace('<main', '<main onclick="x()"'), PAGE.replace('<head>', '<head><style>b{}</style>'),
                                  PAGE.replace('src="/page.js"', 'src="https://example.com/a.js"')])
def test_the_page_holds_nothing_written_in(agent, page):
    (agent / 'live' / 'page.html').write_text(page)
    assert any(w.startswith('the live page') for w in _wrongs(agent))


@pytest.mark.parametrize('line, said', [
    ('import requests', 'not the standard library'), ('import subprocess', 'imports subprocess'), ('import urllib.request\nurllib.request.urlopen("https://example.com/x")', 'names an address'),
    ('WHERE = "//example.com/x"', 'names an address'),
    ('from http import client', 'imports http'), ('import os\nos.system("ls")', 'starts a process'), ('eval("1")', 'starts a process'),
    ('import socket\nsocket.create_connection(("127.0.0.1", 1))', 'starts a process'), ('import asyncio\nasyncio.open_connection("a", 1)', 'starts a process')])
def test_the_program_is_the_standard_library_and_calls_out_to_nothing(agent, line, said):
    (agent / 'live' / 'room.py').write_text(PROGRAM + line + '\n')
    assert any(said in w for w in _wrongs(agent)), _wrongs(agent)


def test_live_json_says_the_same_seats(agent):
    (agent / 'live' / 'live.json').write_text(json.dumps({'seats': 6}))
    assert 'live.json does not say the same seats as the manifest' in _wrongs(agent)


def test_the_program_may_ask_the_one_door_larryd_hands_it(agent):
    (agent / 'live' / 'room.py').write_text(PROGRAM + 'import os\nimport urllib.request\nDOOR = os.environ.get("TALK_RECORDS")\nHERE = "http://127.0.0.1:8797"\n')
    assert doctor.check(agent) == []


def test_the_page_may_carry_one_small_sheet_of_theme_colours(agent):
    (agent / 'live' / 'page.css').write_text('/* ours */\n.box { height: 50vh; overflow-y: scroll; color: var(--active-color-01); }\n')
    assert doctor.check(agent) == []


@pytest.mark.parametrize('rule, said', [('.a { background: url(https://example.com/a.png) }', 'names a file or an address'), ('@import "x.css";', 'names a file or an address'),
                                        ('.a { color: #ff0000 }', 'writes a colour of its own'), ('.a { background: rgb(1, 2, 3) }', 'writes a colour of its own')])
def test_the_sheet_names_no_file_and_no_colour_of_its_own(agent, rule, said):
    (agent / 'live' / 'page.css').write_text(rule + '\n')
    assert any(said in w for w in _wrongs(agent)), _wrongs(agent)


# ---------------------------------------------------------------- the live half is packed, hashed and approved with the agent
def test_the_file_carries_the_live_half_and_unpacks_it_beside_agent(agent, tmp_path):
    import io
    import zipfile
    from larryd import bundle
    data, _sha = bundle.make(agent)
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert [n for n in names if n.startswith('live/')] == ['live/live.json', 'live/page.html', 'live/page.js', 'live/room.py']
    into = tmp_path / 'received'
    into.mkdir()
    assert bundle.open_safely(data, into) == []
    assert (into / 'live' / 'room.py').read_text() == PROGRAM and (into / 'agent' / 'agent.json').is_file() and not (into / 'agent' / 'live').exists()
    assert doctor.check(into) == []   # LARRYD's own doctor, on what it received, sees the same project


def test_an_agent_that_declares_no_live_page_packs_none(agent):
    import io
    import zipfile
    from larryd import bundle
    card = json.loads((agent / 'agent' / 'agent.json').read_text())
    del card['live']
    (agent / 'agent' / 'agent.json').write_text(json.dumps(card))
    names = zipfile.ZipFile(io.BytesIO(bundle.make(agent)[0])).namelist()
    assert not [n for n in names if n.startswith('live/')]


def test_the_codes_hash_covers_the_live_half(agent):
    from larryd import hashes
    before = hashes.code(agent / 'agent')
    (agent / 'live' / 'page.js').write_text(SCRIPT + "fetch('/thread');\n")
    assert hashes.code(agent / 'agent') != before   # a changed live page is a changed agent: approved again


def test_nothing_in_agent_may_take_the_live_halfs_name(agent):
    (agent / 'agent' / 'live').mkdir()
    (agent / 'agent' / 'live' / 'notes.txt').write_text('x')
    assert 'agent/ holds something named live' in _wrongs(agent)
