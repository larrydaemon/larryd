"""THE FIRST HOUR OF A NEW DEVELOPER: the nine places a clean customer run of 0.1.3rc9 got stuck (pip install from the
index, `larryd new marketplace --from marketplace`, card.css edited by hand, doctor, doctor --fix, run), each closed and
held here: the guide ships and is named, no raw template is shown, help says where to start, the doctor says what WILL
convert and --fix says it is clean after, the menu is written down and matched as the eye sees it, the project's tools
start without a venv on PATH, no internal word reaches a developer, and the card sheet is part of the manifest."""
import json
import pathlib
import re
import subprocess
import sys

from larryd import cli, doctor, guide, new, sheet

REPO = pathlib.Path(__file__).resolve().parent.parent
PACKAGE = REPO / 'larryd'
INTERNAL = re.compile(r'\bthe owner\b|harness|the original|\bwid\b|hanzo|frost-|2026', re.I)


def made(tmp_path, example='marketplace'):
    return new.make('marketplace', tmp_path, example=example)


# 1. the guide ships, and help names it
def test_the_guide_ships_in_the_package_word_for_word(capsys):
    shipped = PACKAGE / 'GUIDE.md'
    assert shipped.read_text() == (REPO / 'GUIDE.md').read_text(), 'cp larryd/GUIDE.md GUIDE.md: one guide'
    assert pathlib.Path(guide.path()) == shipped
    assert 'GUIDE.md' in open(REPO / 'pyproject.toml').read().split('[tool.setuptools.package-data]', 1)[1]
    assert cli.main(['guide']) == 0 and capsys.readouterr().out == shipped.read_text()


def test_help_names_the_guide_s_path():
    assert f'The guide: {guide.path()}' in cli.parser().format_help()


# 2. no raw template where a reader looks
def test_the_kit_s_templates_say_they_are_templates_and_nothing_else_holds_a_blank():
    kit = PACKAGE / 'kit'
    blanks = re.compile(r'\{(name|fields|hands|tools|loop|sheet)\}|\{\{')
    for path in kit.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            if blanks.search(path.read_text()):
                assert path.suffix == '.template', f'{path.relative_to(REPO)} holds a blank: name it .template'
    for path in list(PACKAGE.glob('*.md')) + list(kit.glob('*.md')):
        assert not blanks.search(path.read_text()), path


def test_a_made_project_holds_no_blank(tmp_path):
    for example in (None, 'marketplace'):
        root = new.make(f'p{bool(example)}', tmp_path, example=example)
        for path in root.rglob('*'):
            if path.is_file() and path.suffix in ('.md', '.json'):
                assert not re.search(r'\{(name|fields|hands|tools|loop|sheet)\}|\{\{', path.read_text()), path


# 3. help says where to start
def test_help_ends_with_where_to_start(capsys):
    want = 'Start: larryd new <name> --from marketplace, then read <name>/CLAUDE.md (or larryd guide)'
    for argv in (['help'],):
        assert cli.main(argv) == 0
        assert capsys.readouterr().out.rstrip().splitlines()[-1] == want
    assert cli.parser().format_help().rstrip().splitlines()[-1] == want


# 4 + 5. plain doctor says WILL CONVERT and changes nothing; --fix writes, checks the written file, says it is clean
GREY = '.mk-foot { color: #8a8a8a; border-radius: 20px; font-size: 0.85rem; letter-spacing: 0.08em }\n'


def test_plain_doctor_says_will_convert_and_changes_nothing(tmp_path, capsys):
    root = made(tmp_path)
    css = root / 'agent' / 'card.css'
    css.write_text(css.read_text() + GREY)
    before = css.read_text()
    assert cli.main(['doctor', str(root)]) == 0
    out = capsys.readouterr().out
    assert css.read_text() == before and 'CONVERTED' not in out
    assert 'WILL CONVERT card.css: .mk-foot: border-radius 20px -> 22px (the spacing scale)' in out
    assert 'run `larryd doctor --fix` to write these' in out


def test_fix_says_what_it_did_then_the_written_sheet_is_clean(tmp_path, capsys):
    root = made(tmp_path)
    css = root / 'agent' / 'card.css'
    css.write_text(css.read_text() + GREY)
    assert cli.main(['doctor', '--fix', str(root)]) == 0
    out = capsys.readouterr().out
    assert 'CONVERTED card.css: .mk-foot: border-radius 20px -> 22px' in out and 'FIXED agent/card.css' in out
    assert 'WILL CONVERT' not in out and out.rstrip().endswith("the card sheet is in the platform's form: nothing left to convert")
    assert cli.main(['doctor', str(root)]) == 0
    assert 'CONVERT' not in capsys.readouterr().out


# 6. the nearest match, as the eye sees it, and the menu written down
def test_a_colour_goes_to_the_nearest_the_eye_sees_not_the_nearest_number():
    cat = sheet.catalog()
    # #ffcc99 (a peach): by RGB numbers the nearest is #D5C5AA; as the eye sees it (OKLab) it is the light cream #EFE5C6
    slot, hexa, _ = sheet.nearest_colour((0xff, 0xcc, 0x99), cat)
    assert hexa == '#EFE5C6' and cat['colours'][slot] == '#EFE5C6'
    slot, hexa, far = sheet.nearest_colour((0x8a, 0x8a, 0x8a), cat)
    assert (slot, hexa) == ('--active-color-01', '#92866F') and far < 0.05   # a grey goes to the theme's own grey-taupe, said with its distance


def test_a_see_through_colour_keeps_its_alpha_and_the_form_is_stable():
    out, said = sheet.rewrite('.a { background: rgba(0, 0, 0, 0.5); color: #ffffff80 }')
    assert 'color-mix(in srgb, var(--active-color-09) 50%, transparent)' in out and 'var(--active-color-08) 50%' in out
    assert sheet.rewrite(out) == (out, [])


def test_unwritten_weight_and_case_count_as_css_s_own():
    out, said = sheet.rewrite('.a { font-size: 0.85rem; letter-spacing: 0.08em }')
    assert 'var(--font-body)' in out and 'letter spacing' in said[0]


def test_the_menu_is_in_the_guide_and_every_project(tmp_path):
    table = sheet.table()
    cat = sheet.catalog()
    for role in cat['roles']:
        assert f'`.{cat["roles"][role]["class"]}`' in table
    for name in cat['colours']:
        assert re.search(rf'\b{name.rsplit("-", 1)[1]}\b', table), name
    assert ', '.join(str(x) for x in sheet.SPACING) in table
    assert table in (PACKAGE / 'GUIDE.md').read_text()
    assert table in (made(tmp_path) / 'CLAUDE.md').read_text()


# 7. the project's tools start with no venv on PATH
def test_the_project_names_this_larryd_by_its_full_path(tmp_path):
    server = json.loads((made(tmp_path) / '.mcp.json').read_text())['mcpServers']['larryd']
    command = pathlib.Path(server['command'])
    assert command.is_absolute() and command.is_file()
    reply = subprocess.run([str(command), *server['args']], input='{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}\n',
                           capture_output=True, text=True, timeout=30, env={'PATH': '/nonexistent'})
    assert 'larryd_doctor' in reply.stdout, reply.stderr


# 8. no internal word reaches a developer
def test_no_internal_word_in_the_kit_the_guide_or_a_made_project(tmp_path):
    files = [p for p in (PACKAGE / 'kit').rglob('*') if p.is_file() and '__pycache__' not in p.parts] + [PACKAGE / 'GUIDE.md']
    for example in (None, 'marketplace'):
        files += [p for p in new.make(f'w{bool(example)}', tmp_path, example=example).rglob('*') if p.is_file()]
    for path in files:
        for n, line in enumerate(path.read_text().splitlines(), 1):
            assert not INTERNAL.search(line), f'{path}:{n}: {line[:100]}'


# 9. the card sheet is part of the agent, and the manifest says so
def test_the_example_names_its_sheet_and_the_doctor_holds_it(tmp_path):
    root = made(tmp_path)
    manifest = json.loads((root / 'agent' / 'agent.json').read_text())
    assert manifest['style'] == 'card.css' and (root / 'agent' / 'card.css').is_file()
    assert doctor.check(root) == []
    assert 'card.css' in (root / 'CLAUDE.md').read_text() and '"style": "card.css"' in (PACKAGE / 'GUIDE.md').read_text()
    for wrong, said in (('../card.css', 'not a .css file name'), ('gone.css', 'not in agent/')):
        manifest['style'] = wrong
        (root / 'agent' / 'agent.json').write_text(json.dumps(manifest))
        assert any(said in p.wrong for p in doctor.check(root)), wrong


def test_a_plain_agent_needs_no_sheet(tmp_path):
    root = new.make('plain', tmp_path)
    assert 'style' not in json.loads((root / 'agent' / 'agent.json').read_text()) and doctor.check(root) == []
