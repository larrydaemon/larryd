"""Step 1: `larryd new` makes the agent's project in the shape, and the agent it makes answers its sample job."""
import json
import re
import subprocess
import sys

import pytest

from larryd import cli, new, shape


def test_new_makes_the_shape(tmp_path):
    root = new.make('my-agent', tmp_path)
    for rel in (f'agent/{shape.MANIFEST}', 'agent/agent.py', shape.SAMPLE, 'CLAUDE.md', shape.SKILL):
        assert (root / rel).is_file(), rel
    assert sorted(p.name for p in (root / 'agent').iterdir()) == ['agent.json', 'agent.py']   # agent/ holds the agent only
    card = json.loads((root / 'agent' / shape.MANIFEST).read_text())
    assert list(card) == list(shape.NEEDED)
    assert card['name'] == 'my-agent' and card['run']['do'] in card['does']


def test_the_made_agent_answers_its_sample_job(tmp_path):
    root = new.make('Weather_Report', tmp_path)
    job = (root / shape.SAMPLE).read_text()
    done = subprocess.run([sys.executable, '-I', '-B', str(root / 'agent' / 'agent.py')], input=job, capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == {'delivery': 'Weather_Report answered the job.'}


def test_a_job_it_does_not_do_is_refused(tmp_path):
    root = new.make('a1', tmp_path)
    done = subprocess.run([sys.executable, '-I', str(root / 'agent' / 'agent.py')], input='{"do": "sing"}', capture_output=True, text=True)
    assert done.returncode != 0 and 'this agent does: answer' in done.stderr


@pytest.mark.parametrize('bad', ['', '1agent', 'my agent', '../out', 'a/b', 'x' * 64])
def test_a_name_that_is_not_a_plain_folder_name_is_refused(tmp_path, bad):
    with pytest.raises(ValueError, match='not a plain name'):
        new.make(bad, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_an_existing_folder_is_never_touched(tmp_path):
    (tmp_path / 'mine').mkdir()
    (tmp_path / 'mine' / 'keep.txt').write_text('mine')
    with pytest.raises(ValueError, match='already exists'):
        new.make('mine', tmp_path)
    assert [p.name for p in (tmp_path / 'mine').iterdir()] == ['keep.txt']


def _commands(text):
    return set(re.findall(r'`larryd ([a-z]+)', text))


def test_the_documents_name_only_tools_that_exist(tmp_path):
    root = new.make('docs', tmp_path)
    named = _commands((root / 'CLAUDE.md').read_text()) | _commands((root / shape.SKILL).read_text())
    real = set(cli.parser()._subparsers._group_actions[0].choices)
    assert named and named <= real, named - real


def test_the_documents_fill_every_blank(tmp_path):
    root = new.make('blanks', tmp_path)
    for rel in ('CLAUDE.md', shape.SKILL, 'agent/agent.py', shape.SAMPLE):
        text = (root / rel).read_text()
        assert not re.search(r'\{[a-z_]+\}', text), rel


def test_the_skill_is_one_claude_code_loads(tmp_path):
    text = (new.make('sk', tmp_path) / shape.SKILL).read_text()
    head = text.split('---')[1]
    assert re.search(r'^name: larryd$', head, re.M) and re.search(r'^description: .{20,}', head, re.M)


def test_cli_new(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(['new', 'cli-agent']) == 0
    assert (tmp_path / 'cli-agent' / 'agent' / 'agent.json').is_file()
    assert cli.main(['new', 'cli-agent']) == 1
    assert 'already exists' in capsys.readouterr().err
