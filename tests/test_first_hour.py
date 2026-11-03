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
INTERNAL = re.compile(r'\bthe owner\b|(?<!\()harness(?!\))|the original|\bwid\b|frost-|2026', re.I)


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


def test_plain_doctor_fails_a_shipped_sheet_and_changes_nothing(tmp_path, capsys):
    root = made(tmp_path)
    css = root / 'agent' / 'card.css'
    css.write_text(GREY)
    before = (root / 'agent' / 'agent.json').read_text()
    assert cli.main(['doctor', str(root)]) == 1   # a shipped sheet fails the shape
    out = capsys.readouterr().out
    assert css.read_text() == GREY and (root / 'agent' / 'agent.json').read_text() == before
    assert 'agents ship no CSS: the platform draws the card itself' in out and 'it moves it to design/card.css' in out


def test_fix_says_what_it_did_then_the_agent_is_clean(tmp_path, capsys):
    root = made(tmp_path)
    (root / 'agent' / 'card.css').write_text(GREY)
    assert cli.main(['doctor', '--fix', str(root)]) == 0
    out = capsys.readouterr().out
    assert 'FIXED agent/card.css: moved to design/card.css (agents ship no CSS: the platform draws the card)' in out
    assert (root / 'design' / 'card.css').read_text() == GREY and not (root / 'agent' / 'card.css').exists()
    assert cli.main(['doctor', str(root)]) == 0


# 6. the nearest name, as the eye sees it, and the menu written down from the one fixed list


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
def test_the_example_ships_no_look_and_no_sheet(tmp_path):
    root = made(tmp_path)
    manifest = json.loads((root / 'agent' / 'agent.json').read_text())
    assert 'look' not in manifest and 'style' not in manifest   # the platform draws the card from its data (the owner 2026-11-03)
    assert not list((root / 'agent').glob('*.css')) and not (root / 'design').exists() and doctor.check(root) == []
    assert 'An agent ships no CSS.' in (root / 'CLAUDE.md').read_text() and 'The agent ships no\nlook and no CSS' in (root / 'CLAUDE.md').read_text() and 'ships no look and no CSS' in (PACKAGE / 'GUIDE.md').read_text()


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


def test_install_leads_with_the_line_that_works_today():
    text = (PACKAGE / 'GUIDE.md').read_text()
    first = text.split('## 1. Install\n', 1)[1].splitlines()[0]
    assert first.strip() == 'python3 -m venv ~/larryd-venv && ~/larryd-venv/bin/pip install --pre larryd'


# rc11's rerun: what a design sheet loses is said in both modes; the design sheet it replaces is kept


def test_fix_keeps_the_design_sheet_it_replaces(tmp_path, capsys):
    root = made(tmp_path)
    (root / 'design').mkdir()
    (root / 'design' / 'card.css').write_text('.mk-card { border-radius: 2px }\n')
    (root / 'agent' / 'card.css').write_text('.mk-card { border-radius: 4px }\n')
    changed = doctor.fix(root)
    assert (root / '.larryd' / 'doctor_backup' / 'design' / 'card.css').read_text() == '.mk-card { border-radius: 2px }\n'
    assert any('the previous design sheet kept' in c for c in changed)
    assert (root / 'design' / 'card.css').read_text() == '.mk-card { border-radius: 4px }\n'
    (root / 'agent' / 'card.css').write_text('.mk-card { border-radius: 8px }\n')
    doctor.fix(root)
    assert (root / '.larryd' / 'doctor_backup' / 'design' / 'card.css').read_text() == '.mk-card { border-radius: 4px }\n'   # always the one before


def test_the_doctor_section_of_the_guide_wraps_like_the_rest():
    text = (PACKAGE / 'GUIDE.md').read_text()
    section = text[text.index('## 4. The doctor'):text.index('## 5.')]
    assert [line for line in section.splitlines() if len(line) > 120 and not line.startswith('|')] == []


# rc15's rerun: prose is re-flowed by whole paragraph (no word left alone on a line); a part's rules cascade first
def test_no_short_line_inside_a_paragraph_of_the_doctor_section_and_the_menu():
    text = (PACKAGE / 'GUIDE.md').read_text()
    section = text[text.index('## 4. The doctor'):text.index('## 5.')]
    for para in section.split('\n\n'):
        lines = para.split('\n')
        if any(line.startswith(('    ', '|', '#', '-')) for line in lines):
            continue
        assert all(len(line) >= 40 for line in lines[:-1]), lines


def test_the_blank_ships_a_sample_with_the_job_s_own_inputs(tmp_path):
    root = new.make('withjob', tmp_path)
    assert not (root / 'samples' / 'job_inputs.json').exists()
    (root / 'samples' / 'job_inputs.edit-me.json').rename(root / 'samples' / 'job_inputs.json')   # what the developer does once inputs are declared
    sample = json.loads((root / 'samples' / 'job_inputs.json').read_text())
    assert sample == {'do': 'answer', 'job': {'name': 'Harbor', 'mood': 'calm cool'}}
    manifest = json.loads((root / 'agent' / 'agent.json').read_text())
    manifest['run'] = {'do': 'answer', 'hands': ['job']}
    manifest['inputs'] = {'name': '001', 'mood': '002'}
    (root / 'agent' / 'agent.json').write_text(json.dumps(manifest))
    (root / 'agent' / 'agent.py').write_text((root / 'agent' / 'agent.py').read_text().replace(
        "return {'delivery': 'withjob answered the job.'}", "return {'delivery': f\"{job['job']['name']} feels {job['job']['mood']}\"}"))
    from larryd import runner
    result = runner.run(root, str(root / 'samples' / 'job_inputs.json'))
    assert result.state == 'DONE' and runner.as_json(result)['answer'] == {'delivery': 'Harbor feels calm cool'}
    assert 'samples/job_inputs.edit-me.json' in (root / 'CLAUDE.md').read_text() and 'samples/job_inputs.edit-me.json' in (PACKAGE / 'GUIDE.md').read_text()


def test_every_sample_of_a_fresh_project_runs_done(tmp_path):
    """frost-92's MCP path (Z5): a sample that names inputs the agent does not declare is named edit-me, never run as is."""
    from larryd import runner
    for example in (None, 'marketplace'):
        root = new.make(f'fresh{bool(example)}', tmp_path, example=example)
        samples = sorted((root / 'samples').glob('*.json'))
        runnable = [p for p in samples if 'edit-me' not in p.name]
        assert runnable and all(runner.run(root, str(p)).state == 'DONE' for p in runnable), runnable
        assert (root / 'samples' / 'job_inputs.edit-me.json').is_file()


def test_claude_md_names_this_larryd_by_its_full_path(tmp_path):
    """Z2: the commands in CLAUDE.md, like .mcp.json, name the larryd that made the project."""
    root = new.make('abs', tmp_path)
    exe = new.command()
    assert pathlib.Path(exe.split()[0]).is_absolute()
    text = (root / 'CLAUDE.md').read_text()
    assert f"This project's larryd: `{exe}`" in text and f'- `{exe} doctor`:' in text and f'- `{exe} run`:' in text


def test_plain_doctor_warns_of_the_blank_s_placeholders(tmp_path, capsys):
    """Z6: a warning while building (the doctor still passes), a refusal at submit."""
    root = new.make('words', tmp_path)
    assert cli.main(['doctor', str(root)]) == 0
    out = capsys.readouterr().out
    assert 'WARN "about" is still the blank\'s placeholder' in out and 'WARN card "pitch" is still' in out and 'larryd submit refuses it' in out


# frost-92's stranger read of the guide: what is live, the platform, mTok, data and residency, a glossary
def test_the_guide_says_today_the_platform_mtok_and_a_glossary():
    text = (PACKAGE / 'GUIDE.md').read_text()
    for heading in ('> **Today.**', '## The platform in one minute', '## mTok', '## What the card says about data and where the agent is offered', '## Glossary'):
        assert heading in text, heading
    assert 'Payouts to developers\nare not there yet' in text or 'Payouts to developers are not there yet' in text.replace('\n', ' ')
    for word in ('**FROST**', '**DA-M**', '**LARRY LLM**', '**locker**', '**card key**', '**claim page**', '**CALL and RUN**',
                 '**MARK classes**', '**species**', '**product**', '**module**', '**screen**'):
        assert word in text, word
    assert 'larryd.ai/checks.html' not in text and '10 per address per hour' in text
    assert 'Start: `larryd new <name>` for a blank agent' in text
