"""The job's own inputs (hands ["job"]): the doctor checks "inputs" ({name: slot 001-015}, one slot each, only with the
hand), and `larryd run` hands the sample job's inputs exactly as PF HANZO would: only declared names, text, not too long."""
import json

import pytest

from larryd import doctor, new, runner, shape


@pytest.fixture
def agent(tmp_path):
    root = new.make('inputs', tmp_path)
    path = root / 'agent' / 'agent.json'
    card = json.loads(path.read_text())
    card.update(run={'do': 'answer', 'hands': ['job']}, inputs={'name': '001', 'mood': '002'})
    path.write_text(json.dumps(card))
    code = root / 'agent' / 'agent.py'
    code.write_text(code.read_text().replace("return {'delivery': 'inputs answered the job.'}", "return {'delivery': json.dumps(job.get('job'), sort_keys=True)}"))
    (root / 'samples' / 'job.json').write_text(json.dumps({'do': 'answer', 'job': {'name': 'Harbor', 'mood': 'calm cool'}}))
    return root


def _set(root, **fields):
    path = root / 'agent' / 'agent.json'
    card = json.loads(path.read_text())
    card.update(fields)
    for k, v in list(fields.items()):
        if v is None:
            del card[k]
    path.write_text(json.dumps(card))


def _manifest_problems(root):
    return [p.wrong for p in doctor.check(root) if p.check == 'the manifest']


def test_hanzo_hands_the_job_today():
    assert shape.HANDS == ('cards', 'job')


def test_a_job_agent_passes_and_runs_with_its_inputs(agent):
    assert doctor.check(agent) == []
    result = runner.run(agent)
    assert result.state == 'DONE', result.reason
    assert json.loads(result.answer['delivery']) == {'mood': 'calm cool', 'name': 'Harbor'}


@pytest.mark.parametrize('inputs, words', [
    (None, 'not {name: slot}'), ({}, 'not {name: slot}'), ({'name': '016'}, 'not {name: slot}'), ({'name': '1'}, 'not {name: slot}'),
    ({'a name': '001'}, 'not {name: slot}'), (['001'], 'not {name: slot}'), ({'name': '001', 'mood': '001'}, 'two names on one slot'),
])
def test_inputs_not_declared_right(agent, inputs, words):
    _set(agent, inputs=inputs)
    assert any(words in w for w in _manifest_problems(agent))


def test_inputs_without_the_hand(agent):
    _set(agent, run={'do': 'answer', 'hands': []})
    assert any('has no "job"' in w for w in _manifest_problems(agent))


def test_agents_without_the_hand_need_no_inputs(tmp_path):
    assert doctor.check(new.make('plain', tmp_path)) == []


@pytest.mark.parametrize('job, words', [
    ({'name': 'Harbor', 'seed': '1'}, "holds ['seed']"), ({'name': 7}, 'not text'), ({'name': 'x' * (shape.MOST_INPUT + 1)}, 'not text'),
    (['Harbor'], 'is not {name: value}'),
])
def test_a_sample_job_hanzo_would_refuse(agent, job, words):
    (agent / 'samples' / 'job.json').write_text(json.dumps({'do': 'answer', 'job': job}))
    result = runner.run(agent)
    assert result.state == 'REFUSED' and words in result.reason and result.todo


def test_a_sample_job_without_the_job(agent):
    (agent / 'samples' / 'job.json').write_text('{"do": "answer"}')
    assert "has no ['job']" in runner.run(agent).reason


def test_a_declared_input_left_empty_is_simply_not_handed(agent):
    (agent / 'samples' / 'job.json').write_text(json.dumps({'do': 'answer', 'job': {'name': 'Harbor'}}))
    assert json.loads(runner.run(agent).answer['delivery']) == {'name': 'Harbor'}
