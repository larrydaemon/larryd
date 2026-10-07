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
INTERNAL = re.compile(r'\bthe owner\b|harness|the original|\bwid\b|frost-|2026', re.I)


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


# 4 + 5. plain doctor says WILL CONVERT and changes nothing; --fix writes the look record, says it, and is clean after
GREY = '.mk-card { border: 1px solid #8a8a8a; border-radius: 20px }\n.mk-foot { font-size: 0.85rem; letter-spacing: 0.08em }\n'


def test_plain_doctor_says_will_convert_and_changes_nothing(tmp_path, capsys):
    root = made(tmp_path)
    css = root / 'agent' / 'card.css'
    css.write_text(GREY)
    before = (root / 'agent' / 'agent.json').read_text()
    assert cli.main(['doctor', str(root)]) == 1   # a shipped sheet fails the shape
    out = capsys.readouterr().out
    assert css.read_text() == GREY and (root / 'agent' / 'agent.json').read_text() == before and 'CONVERTED' not in out
    assert 'WILL CONVERT card.css: .mk-card: border-radius 20px -> radius step-6 (22px, the nearest step)' in out
    assert 'run `larryd doctor --fix` to write these into the look record' in out


def test_fix_says_what_it_did_then_the_agent_is_clean(tmp_path, capsys):
    root = made(tmp_path)
    (root / 'agent' / 'card.css').write_text(GREY)
    assert cli.main(['doctor', '--fix', str(root)]) == 0
    out = capsys.readouterr().out
    assert 'CONVERTED card.css: .mk-card: border-radius 20px -> radius step-6' in out and 'moved to design/card.css' in out
    assert 'WILL CONVERT' not in out and out.rstrip().endswith('agent/ holds no CSS: the look record is in agent.json, nothing left to convert')
    assert cli.main(['doctor', str(root)]) == 0
    assert 'CONVERT' not in capsys.readouterr().out


# 6. the nearest name, as the eye sees it, and the menu written down from the one fixed list
def test_roles_by_what_the_eye_sees_case_a_cost_purpose_roles_only_when_asked():
    cat = sheet.catalog()
    assert sheet.nearest_role({'font-size': '40px', 'font-weight': '900'}, cat, '.mk-name') in ('heading', 'title')   # a big black name stays a heading
    assert sheet.nearest_role({'font-size': '30px', 'font-weight': '800', 'text-transform': 'uppercase'}, cat, '.mk-name') == 'title'
    assert sheet.nearest_role({'font-size': '15px', 'font-style': 'italic'}, cat, '.mk-pitch') == 'body'
    assert sheet.nearest_role({'font-size': '12px', 'font-weight': '400'}, cat, '.mk-price') in ('caption', 'body')
    assert sheet.nearest_role({'font-size': '11px', 'font-weight': '400', 'text-transform': 'uppercase'}, cat, '.mk-price') == 'annotation'   # nav is as near; a price is not navigation
    assert sheet.nearest_role({'font-size': '11px', 'font-weight': '400', 'text-transform': 'uppercase'}, cat, '.mk-nav') == 'nav'   # it says it is navigation
    assert sheet.nearest_role({'font-size': '14px', 'font-weight': '500'}, cat, 'a.more') == 'link'
    assert '(chosen only for a selector naming nav, menu, navigation)' in sheet.table()


def test_the_menu_is_in_the_guide_and_every_project(tmp_path):
    table = sheet.table()
    cat = sheet.catalog()
    for role in cat['roles']:
        assert f'| {role} |' in table
    for name in cat['colours']:
        assert re.search(rf'\b{name.rsplit("-", 1)[1]}\b', table), name
    for step in cat['steps']:
        assert step in table
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


# 9. what ships is plain: agent/ holds no CSS; the look is in the manifest, and the guide says so
def test_the_example_ships_a_look_record_and_no_sheet(tmp_path):
    root = made(tmp_path)
    manifest = json.loads((root / 'agent' / 'agent.json').read_text())
    assert manifest['look'] == {'accent': 'active-color-01', 'radius': 'step-5', 'space': 'step-3', 'effect': 'crt'} and 'style' not in manifest
    assert not list((root / 'agent').glob('*.css')) and doctor.check(root) == []
    assert 'ships no CSS' in (root / 'CLAUDE.md').read_text() and 'ships no CSS' in (PACKAGE / 'GUIDE.md').read_text()


def test_a_plain_agent_needs_no_look(tmp_path):
    root = new.make('plain', tmp_path)
    assert 'look' not in json.loads((root / 'agent' / 'agent.json').read_text()) and doctor.check(root) == []


# rc10's rerun: the guide's links ship, its tool list is the server's, a tie is said, the install line works today
def test_the_guide_s_checks_link_ships_beside_it():
    assert '[CHECKS.md](CHECKS.md)' in (PACKAGE / 'GUIDE.md').read_text()
    assert (PACKAGE / 'CHECKS.md').read_text() == (REPO / 'CHECKS.md').read_text(), 'cp CHECKS.md larryd/CHECKS.md'
    assert 'CHECKS.md' in open(REPO / 'pyproject.toml').read().split('[tool.setuptools.package-data]', 1)[1]


def test_the_guide_names_every_tool_the_server_serves():
    from larryd import mcp
    assert ', '.join(mcp.TOOLS) + '.' in (PACKAGE / 'GUIDE.md').read_text()


def test_a_tie_on_the_scale_rounds_down_and_says_so():
    from larryd import look
    record, said, _ = look.from_sheet('.mk-card { padding: 10px }')
    assert record == {'space': 'step-3'} and said[0].endswith('(8px, the nearest step; tie: rounds down)')
    assert 'a tie rounds down' in sheet.table()


def test_install_leads_with_the_line_that_works_today():
    text = (PACKAGE / 'GUIDE.md').read_text()
    first = text.split('## 1. Install\n', 1)[1].splitlines()[0]
    assert first.strip() == 'python3 -m venv ~/larryd-venv && ~/larryd-venv/bin/pip install --pre larryd'


# rc11's rerun: what a design sheet loses is said in both modes; the design sheet it replaces is kept
def test_doctor_says_will_drop_and_fix_says_dropped(tmp_path, capsys):
    root = made(tmp_path)
    sheet_text = '.mk-card { border: 1px solid #8a8a8a; gap: 12px }\n.mk-name { color: #ffb000 }\n'
    (root / 'agent' / 'card.css').write_text(sheet_text)
    cli.main(['doctor', str(root)])
    out = capsys.readouterr().out
    assert 'WILL DROP card.css: .mk-name: color -> no name on the menu (colour is card-wide' in out
    assert 'WILL DROP card.css: .mk-card: gap -> no name on the menu' in out
    assert cli.main(['doctor', '--fix', str(root)]) == 0
    out = capsys.readouterr().out
    assert 'DROPPED card.css: .mk-name: color -> no name on the menu' in out and 'WILL DROP' not in out


def test_fix_keeps_the_design_sheet_it_replaces(tmp_path, capsys):
    root = made(tmp_path)
    before = (root / 'design' / 'card.css').read_text()
    (root / 'agent' / 'card.css').write_text('.mk-card { border-radius: 4px }\n')
    changed = doctor.fix(root)
    assert (root / '.larryd' / 'doctor_backup' / 'design' / 'card.css').read_text() == before
    assert any('the previous design sheet kept' in c for c in changed)
    assert (root / 'design' / 'card.css').read_text() == '.mk-card { border-radius: 4px }\n'
    (root / 'agent' / 'card.css').write_text('.mk-card { border-radius: 8px }\n')
    doctor.fix(root)
    assert (root / '.larryd' / 'doctor_backup' / 'design' / 'card.css').read_text() == '.mk-card { border-radius: 4px }\n'   # always the one before


def test_the_doctor_section_of_the_guide_wraps_like_the_rest():
    text = (PACKAGE / 'GUIDE.md').read_text()
    section = text[text.index('## 4. The doctor'):text.index('## 5.')]
    assert [line for line in section.splitlines() if len(line) > 120 and not line.startswith('|')] == []
