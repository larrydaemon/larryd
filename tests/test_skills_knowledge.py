"""Step 6: skills and knowledge, the shape. A skill is a definition named by its hash; only PF HANZO's real doors are
skills (today: the mTok charge). A knowledge pack is a folder named by its hash. The doctor checks what an agent declares."""
import hashlib
import json
import os

import pytest

from larryd import cli, doctor, hashes, knowledge, new, skills


MTOK = '3c8ad8bf218a8350b26a7fb4b9eb7f6c70073553437aec8d05afee60f9740dcb'       # pinned here and in PF HANZO's tests: drift on either side is red
GREETING = '94686bdeef7ebf3df3e52f1a3086f280ee25b1457336b87f5ab39860f7248fa2'
IDENTITY = '4db76a92980ff0a3b4cbe584d0b2de4c9821a5cbf7385c0b062c43f276f0ac0f'
STORE = '1d0eb4d13f8a91b4d0cc67f8b5cb157a4b74ec2c937779d49d4bb80beecc670a'


def test_the_skills_that_exist():
    """Only a door that exists is a skill. Today: the mTok charge (applied to every run) and the LARRY LLM greeting
    (LARRYD asks LARRY LLM for the member's greeting and hands it in) and the FROST identity (who the agent works for: first
    name, member type, account name) and the DA-M store (files an agent answers, kept in the member's DA-M)."""
    known = skills.known()
    assert {h: s['name'] for h, s in known.items()} == {MTOK: 'mTok charge', GREETING: 'LARRY LLM greeting', IDENTITY: 'FROST identity', STORE: 'DA-M store'}
    for h, s in known.items():
        assert h == hashlib.sha256(json.dumps(s, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert {'name', 'technology', 'door', 'does', 'agent'} <= set(s) <= {'name', 'technology', 'door', 'does', 'agent', 'hand', 'after'} and all(s.values())
    assert known[GREETING]['hand'] == 'greeting' and known[IDENTITY]['hand'] == 'identity' and 'hand' not in known[MTOK]
    assert known[STORE]['after'] == 'files' and 'hand' not in known[STORE]


def test_run_hands_the_greeting_when_the_skill_is_declared(tmp_path):
    from larryd import runner
    root = new.make('greeted', tmp_path)
    _set(root, skills=[GREETING])
    code = root / 'agent' / 'agent.py'
    code.write_text(code.read_text().replace("return {'delivery': 'greeted answered the job.'}", "return {'delivery': job['greeting']['greetings']['morning']}"))
    assert 'has no [\'greeting\']' in runner.run(root).reason
    (root / 'samples' / 'job.json').write_text(json.dumps({'do': 'answer', 'greeting': {'date': '2026-09-30', 'greetings': {'morning': 'Up with the sun'}}}))
    result = runner.run(root)
    assert result.state == 'DONE' and result.answer == {'delivery': 'Up with the sun'}
    _set(root, skills=[])
    assert "holds ['greeting']" in runner.run(root).reason   # not declared: LARRYD would not hand it


def test_run_checks_the_files_an_answer_carries(tmp_path):
    import base64
    from larryd import runner
    root = new.make('keeper', tmp_path)
    _set(root, skills=[STORE], gives=['delivery', 'files'])
    code = root / 'agent' / 'agent.py'

    def answering(files):
        text = code.read_text()
        start = text.index('    return {')
        end = text.index('\n', start)
        code.write_text(text[:start] + f"    return {{'delivery': 'kept', 'files': {files!r}}}" + text[end:])
        return runner.run(root)

    good = {'name': 'theme.json', 'content_b64': base64.b64encode(b'{"theme": 1}').decode()}
    assert answering([good]).state == 'DONE'
    for files, words in (([dict(good, name='sub/x.json')], 'plain name'), ([dict(good, content_b64='no!')], 'not base64'),
                         ([dict(good, content_b64='')], 'is empty'), ([good] * 11, 'at most 10'), ('x', 'at most 10')):
        result = answering(files)
        assert result.state == 'FAILED' and words in result.reason, (files, result.reason)
    _set(root, skills=[])
    result = answering([good])
    assert result.state == 'FAILED' and 'does not declare the DA-M store' in result.reason


def test_a_changed_skill_is_a_new_skill():
    s = next(iter(skills.known().values()))
    assert hashes.definition({**s, 'does': s['does'] + ' and more'}) not in skills.known()


@pytest.fixture
def agent(tmp_path):
    return new.make('skilled', tmp_path)


def _set(root, **fields):
    path = root / 'agent' / 'agent.json'
    card = json.loads(path.read_text())
    card.update(fields)
    path.write_text(json.dumps(card))


def test_a_declared_skill_that_exists_passes(agent):
    _set(agent, skills=list(skills.known()))
    assert doctor.check(agent) == []


def test_a_declared_skill_that_does_not_exist_fails_and_names_the_real_ones(agent):
    _set(agent, skills=['mTok charge'])   # a name is not a hash
    problems = [p for p in doctor.check(agent) if p.check == 'the skills']
    assert problems and next(iter(skills.known())) in problems[0].todo


def test_a_declared_knowledge_pack_fails_while_hanzo_holds_none(agent):
    _set(agent, knowledge=['0' * 64])
    problems = [p for p in doctor.check(agent) if p.check == 'the knowledge']
    assert problems and 'holds no knowledge pack yet' in problems[0].todo


@pytest.mark.parametrize('field', ['skills', 'knowledge'])
def test_not_a_list(agent, field):
    _set(agent, **{field: 'x'})
    assert 'the manifest' in {p.check for p in doctor.check(agent)}


def test_the_knowledge_field_is_needed(agent):
    path = agent / 'agent' / 'agent.json'
    card = json.loads(path.read_text())
    del card['knowledge']
    path.write_text(json.dumps(card))
    assert any('"knowledge" is missing' in p.wrong for p in doctor.check(agent))


# ---------------------------------------------------------------- knowledge packs
@pytest.fixture
def pack(tmp_path):
    folder = tmp_path / 'pack'
    folder.mkdir()
    (folder / 'pack.json').write_text('{"name": "Colors", "about": "The brand colors, by name."}')
    (folder / 'colors.csv').write_text('name,hex\nnavy,#001f3f\n')
    return folder


def test_a_pack_gets_its_hash(pack):
    digest, wrong = knowledge.check(pack)
    assert wrong == [] and digest == hashes.pack(pack) and len(digest) == 64


def test_a_changed_pack_is_a_new_pack(pack):
    before = knowledge.check(pack)[0]
    (pack / 'colors.csv').write_text('name,hex\nnavy,#001f3e\n')
    assert knowledge.check(pack)[0] != before


PACK_PLANTS = {
    'no pack.json': lambda p: (p / 'pack.json').unlink(),
    'pack.json missing about': lambda p: (p / 'pack.json').write_text('{"name": "Colors"}'),
    'pack.json with more': lambda p: (p / 'pack.json').write_text('{"name": "C", "about": "a", "price": "1"}'),
    'a link': lambda p: os.symlink('/etc/hosts', p / 'hosts.txt'),
    'a hidden file': lambda p: (p / '.notes.md').write_text('x'),
    'a kind a pack does not hold': lambda p: (p / 'run.py').write_text('x'),
    'not text': lambda p: (p / 'data.txt').write_bytes(b'\xff\xfe\x00'),
}


@pytest.mark.parametrize('name', PACK_PLANTS)
def test_a_pack_that_is_not_right(pack, name):
    PACK_PLANTS[name](pack)
    digest, wrong = knowledge.check(pack)
    assert digest == '' and wrong and all(' · ' in w for w in wrong)


# ---------------------------------------------------------------- the hashes (PF HANZO's locker recipe)
def test_the_code_hash_is_the_lockers_recipe(tmp_path):
    folder = tmp_path / 'a'
    (folder / 'lib').mkdir(parents=True)
    (folder / 'agent.json').write_text('{}')
    (folder / 'agent.py').write_text('print(1)\n')
    (folder / 'lib' / 'x.txt').write_text('x')
    (folder / '__pycache__').mkdir()
    (folder / '__pycache__' / 'agent.pyc').write_bytes(b'\x00')
    h = hashlib.sha256()
    for rel, data in (('agent.py', b'print(1)\n'), ('lib/x.txt', b'x')):   # the manifest and compiled caches are not the code
        h.update(rel.encode() + b'\0' + data + b'\0')
    assert hashes.code(folder) == h.hexdigest()
    assert hashes.manifest(folder) == hashlib.sha256(b'{}').hexdigest()


# ---------------------------------------------------------------- the commands
def test_the_commands(pack, capsys):
    assert cli.main(['skills']) == 0
    assert next(iter(skills.known())) in capsys.readouterr().out
    assert cli.main(['pack', str(pack)]) == 0
    assert capsys.readouterr().out.strip() == hashes.pack(pack)
    (pack / 'pack.json').unlink()
    assert cli.main(['pack', str(pack)]) == 1
    assert capsys.readouterr().out.startswith('FAIL ')
