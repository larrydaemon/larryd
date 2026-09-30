"""Step 6: skills and knowledge, the shape. A skill is a definition named by its hash; only PF HANZO's real doors are
skills (today: the mTok charge). A knowledge pack is a folder named by its hash. The doctor checks what an agent declares."""
import hashlib
import json
import os

import pytest

from larryd import cli, doctor, hashes, knowledge, new, skills


def test_the_skills_that_exist():
    """Of the four technologies, only mTok has a door in PF HANZO today (it charges every DONE run through /mtok/use).
    FROST sign-in, DA-M store and LARRY LLM greeting have no PF HANZO door, so they are no skill yet: a new skill comes
    only with its door."""
    known = skills.known()
    assert [s['name'] for s in known.values()] == ['mTok charge']
    for h, s in known.items():
        assert h == hashlib.sha256(json.dumps(s, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert set(s) == {'name', 'technology', 'door', 'does', 'agent'} and all(s.values())


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
