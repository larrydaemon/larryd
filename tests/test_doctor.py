"""Step 2: `larryd doctor`. The clean agent `larryd new` makes passes every check; each planted violation is caught by
its own check, and the message says what is wrong and what to do."""
import json
import os
import re

import pytest

from larryd import cli, doctor, new


@pytest.fixture
def agent(tmp_path):
    return new.make('planted', tmp_path)


def _card(root):
    return json.loads((root / 'agent' / 'agent.json').read_text())


def _write_card(root, card):
    (root / 'agent' / 'agent.json').write_text(json.dumps(card))


def _code(root, more):
    path = root / 'agent' / 'agent.py'
    path.write_text(path.read_text() + more)


def _failed(root):
    return {p.check for p in doctor.check(root)}


def test_the_clean_agent_passes_every_check(agent):
    assert doctor.check(agent) == []


def test_no_agent_here(tmp_path):
    assert _failed(tmp_path) == {'the project'}


# ---------------------------------------------------------------- the manifest
def _drop(k):
    def plant(root):
        card = _card(root)
        del card[k]
        _write_card(root, card)
    return plant


def _set(**fields):
    def plant(root):
        card = _card(root)
        card.update(fields)
        _write_card(root, card)
    return plant


MANIFEST_PLANTS = {
    'not JSON': lambda root: (root / 'agent' / 'agent.json').write_text('{"name": '),
    'not an object': lambda root: (root / 'agent' / 'agent.json').write_text('[]'),
    'name missing': _drop('name'),
    'skills missing': _drop('skills'),
    'an unknown field': _set(price='5'),
    'empty name': _set(name=' '),
    'empty about': _set(about=''),
    'entry with a path': _set(entry='../agent.py'),
    'entry not python': _set(entry='agent.sh'),
    'does empty': _set(does=[]),
    'does not names': _set(does=['an answer']),
    'calls outside does': _set(calls=['collection']),
    'reads not a list': _set(reads='the cards'),
    'gives empty': _set(gives=[]),
    'run without hands': _set(run={'do': 'answer'}),
    'run do outside does': _set(run={'do': 'sing', 'hands': []}),
    'hands HANZO does not hand': _set(run={'do': 'answer', 'hands': ['members']}),
    'skills not a list': _set(skills='x'),
}


@pytest.mark.parametrize('name', MANIFEST_PLANTS)
def test_the_manifest_catches(agent, name):
    MANIFEST_PLANTS[name](agent)
    problems = [p for p in doctor.check(agent) if p.check == 'the manifest']
    assert problems, name
    assert all(p.wrong and p.todo for p in problems)


def test_hands_names_what_hanzo_hands(agent):
    _set(run={'do': 'answer', 'hands': ['cards']})(agent)
    assert doctor.check(agent) == []


# ---------------------------------------------------------------- the entry
def test_the_entry_missing(agent):
    (agent / 'agent' / 'agent.py').rename(agent / 'agent' / 'other.py')
    assert 'the entry' in _failed(agent)


def test_the_entry_does_not_compile(agent):
    _code(agent, '\ndef broken(:\n')
    problems = [p for p in doctor.check(agent) if p.check == 'the entry']
    assert problems and 'does not compile' in problems[0].wrong


def test_a_does_with_no_function(agent):
    _set(does=['answer', 'report'])(agent)
    problems = [p for p in doctor.check(agent) if p.check == 'the entry']
    assert problems and 'report' in problems[0].wrong and 'def report(job)' in problems[0].todo


def test_the_entry_never_runs(agent):
    path = agent / 'agent' / 'agent.py'
    path.write_text(path.read_text().replace("if __name__ == '__main__':\n    main()\n", ''))
    assert _failed(agent) == {'the entry'}


# ---------------------------------------------------------------- the air gap
AIR_GAP_PLANTS = {
    'socket': '\nimport socket\n',
    'urllib': '\nfrom urllib.request import urlopen\n',
    'http.client': '\nimport http.client\n',
    'asyncio': '\nimport asyncio\n',
    'subprocess': '\nimport subprocess\n',
    'multiprocessing': '\nfrom multiprocessing import Pool\n',
    'ctypes': '\nimport ctypes\n',
    'os.system': '\nimport os\nos.system("true")\n',
    'from os import popen': '\nfrom os import popen\n',
    'os.execv': '\nimport os\nos.execv("/bin/sh", [])\n',
    'importlib': '\nimport importlib\n',
    '__import__': '\nx = __import__("sock" + "et")\n',
    'not the standard library': '\nimport requests\n',
    'a path under /Users': '\nopen("/Users/someone/notes.txt")\n',
    'a path under ~': '\nopen("~/notes.txt")\n',
    'a path up and out': '\nopen("../secrets.txt")\n',
    'the platform': '\nWHERE = "virtual_workspace"\n',
    'PF HANZO': '\nWHERE = "pfhanzo"\n',
}


@pytest.mark.parametrize('name', AIR_GAP_PLANTS)
def test_the_air_gap_catches(agent, name):
    _code(agent, AIR_GAP_PLANTS[name])
    problems = [p for p in doctor.check(agent) if p.check == 'the air gap']
    assert problems, name
    assert problems[0].line > 0 and problems[0].todo


# the disguises (the new-user trial's finding #5): a module, a path or code the doctor cannot read in the source
DISGUISED_PLANTS = {
    'builtins.__import__': '\nimport builtins\nx = builtins.__import__("sock" + "et")\n',
    'getattr on __builtins__': '\nx = getattr(__builtins__, "__imp" + "ort__")("sock" + "et")\n',
    'getattr with a built name': '\nimport os\nf = getattr(os, "sys" + "tem")\n',
    'sys.modules': '\nimport sys\nm = sys.modules["o" + "s"]\n',
    'exec': '\nexec("import sock" + "et")\n',
    'eval': '\nx = eval("1 + 1")\n',
    'compile': '\nc = compile("x = 1", "made", "exec")\n',
    'globals()': '\ng = globals()["__builtins__"]\n',
    'vars()': '\nimport json\nv = vars(json)\n',
    'a class escape': '\nx = ().__class__.__base__.__subclasses__()\n',
    'pickle': '\nimport pickle\n',
    'marshal': '\nimport marshal\n',
    'chr(47) path': '\nopen(chr(47) + "etc" + chr(47) + "hosts")\n',
    'os.sep path': '\nimport os\nopen(os.sep + os.path.join("etc", "hosts"))\n',
    'os.path.sep path': '\nimport os.path\np = os.path.sep\n',
    'the home folder': '\nimport os\nh = os.path.expanduser("~")\n',
    'Path.home': '\nimport pathlib\nh = pathlib.Path.home()\n',
    'an escaped slash': '\nopen("\\x2fetc\\x2fhosts")\n',
    'a root piece': '\nopen("/" + "etc" + "/hosts")\n',
    'an absolute path': '\nopen("/opt/data.csv")\n',
}


@pytest.mark.parametrize('name', DISGUISED_PLANTS)
def test_the_air_gap_sees_through(agent, name):
    _code(agent, DISGUISED_PLANTS[name])
    problems = [p for p in doctor.check(agent) if p.check == 'the air gap']
    assert problems, name
    assert problems[0].file == 'agent/agent.py' and problems[0].line > 0 and problems[0].todo


def test_plain_code_the_disguise_rules_leave_alone(agent):
    """What a normal agent does stays clean: its own folder by __file__, a getattr by a written name, text with slashes."""
    _code(agent, '\nimport os, pathlib\nHERE = pathlib.Path(__file__).parent\nDATA = os.path.join(os.path.dirname(__file__), "data.csv")\n'
                 'class Card:\n    size = 1\nn = getattr(Card, "size", 0)\nWHEN = "10/03"\nRATIO = "a/b"\nL = chr(65)\n'
                 'D = "/".join(["2026", "09"])\nM = 3\nF = f"{M}/{M}"\n')
    assert doctor.check(agent) == []


def test_a_plant_in_another_file_of_the_agent(agent):
    (agent / 'agent' / 'helper.py').write_text('import socket\n')
    problems = [p for p in doctor.check(agent) if p.check == 'the air gap']
    assert problems and problems[0].file == 'agent/helper.py'


def test_the_agents_own_modules_are_not_outside(agent):
    (agent / 'agent' / 'helper.py').write_text('def help():\n    return 1\n')
    _code(agent, '\nimport helper\nfrom helper import help\n')
    assert doctor.check(agent) == []


def test_the_standard_library_is_fine(agent):
    _code(agent, '\nimport os.path\nimport re, datetime, collections\nfrom os import environ\n')
    assert doctor.check(agent) == []


# ---------------------------------------------------------------- no secret
SECRET_PLANTS = {
    'a private key': ('agent/key.txt', '-----BEGIN RSA ' + 'PRIVATE KEY-----\nabc\n'),   # key-shaped plants are built from pieces: no whole one sits in a file
    'a cloud key': ('agent/agent.py', '\nK = "AKIA' + 'ABCDEFGHIJKLMNOP"\n'),
    'an Anthropic key': ('agent/agent.py', '\nK = "sk-' + 'ant-api03-abcdefghijklmnop"\n'),
    'a GitHub token': ('agent/notes.md', 'ghp' + '_abcdefghijklmnopqrstuvwxyz123456\n'),
    'a password in the code': ('agent/agent.py', '\ndb_password = "hunter2hunter2"\n'),
    'a token in JSON': ('agent/data.json', '{"api_key": "abcdefgh12345678"}\n'),
    'a .env file': ('agent/.env', 'X=1\n'),
    'a .pem file': ('agent/cert.pem', 'x\n'),
    'an id_rsa file': ('agent/id_rsa', 'x\n'),
}


@pytest.mark.parametrize('name', SECRET_PLANTS)
def test_no_secret_catches(agent, name):
    rel, text = SECRET_PLANTS[name]
    path = agent / rel
    path.write_text(path.read_text() + text if path.exists() else text)
    problems = [p for p in doctor.check(agent) if p.check == 'no secret']
    assert problems, name
    assert 'revoke' in problems[0].todo or 'take it out' in problems[0].todo


def test_a_secret_outside_the_agent_is_not_the_agents(agent):
    (agent / '.env').write_text('LARRYD_KEY=sk-' + 'ant-abcdefghijklmnopqrstuv\n')   # the developer's own, outside agent/
    assert doctor.check(agent) == []


# ---------------------------------------------------------------- the shape
def test_a_link_to_a_file(agent, tmp_path):
    (tmp_path / 'outside.txt').write_text('x')
    os.symlink(tmp_path / 'outside.txt', agent / 'agent' / 'data.txt')
    assert 'the shape' in _failed(agent)


def test_a_link_to_a_folder(agent, tmp_path):
    (tmp_path / 'elsewhere').mkdir()
    os.symlink(tmp_path / 'elsewhere', agent / 'agent' / 'more')
    assert 'the shape' in _failed(agent)


def test_the_agent_folder_is_a_link(tmp_path):
    real = new.make('real', tmp_path)
    (tmp_path / 'linked').mkdir()
    os.symlink(real / 'agent', tmp_path / 'linked' / 'agent')
    assert _failed(tmp_path / 'linked') == {'the project'}


def test_a_hidden_file(agent):
    (agent / 'agent' / '.cache').mkdir()
    (agent / 'agent' / '.cache' / 'x.txt').write_text('x')
    assert 'the shape' in _failed(agent)


def test_a_kind_an_agent_does_not_hold(agent):
    (agent / 'agent' / 'run.sh').write_text('#!/bin/sh\n')
    assert _failed(agent) == {'the shape'}


def test_not_text(agent):
    (agent / 'agent' / 'data.csv').write_bytes(b'\xff\xfe\x00bin')
    assert _failed(agent) == {'the shape'}


def test_compiled_caches_are_not_the_agent(agent):
    (agent / 'agent' / '__pycache__').mkdir()
    (agent / 'agent' / '__pycache__' / 'agent.cpython-314.pyc').write_bytes(b'\x00\xff')
    assert doctor.check(agent) == []


# ---------------------------------------------------------------- the skills
def test_a_skill_that_does_not_exist(agent):
    _set(skills=['0' * 64])(agent)
    problems = [p for p in doctor.check(agent) if p.check == 'the skills']
    assert problems and 'does not exist' in problems[0].wrong


# ---------------------------------------------------------------- the words, the command
def test_every_message_names_only_tools_that_exist():
    source = open(doctor.__file__).read()
    named = set(re.findall(r'`larryd ([a-z]+)', source))
    real = set(cli.parser()._subparsers._group_actions[0].choices)
    assert named and named <= real, named - real


def test_the_command(agent, capsys):
    assert cli.main(['doctor', str(agent)]) == 0
    assert 'the agent passes every check' in capsys.readouterr().out
    _code(agent, '\nimport socket\n')
    assert cli.main(['doctor', str(agent), '--json']) == 1
    out = json.loads(capsys.readouterr().out)
    assert out['ok'] is False
    gap = next(c for c in out['checks'] if c['check'] == 'the air gap')
    assert gap['ok'] is False and gap['problems'][0]['line'] > 0 and 'What to do' not in gap['problems'][0]['todo']
    assert cli.main(['doctor', str(agent)]) == 1
    assert 'FAIL the air gap · agent/agent.py line' in capsys.readouterr().out
