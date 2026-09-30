"""Step 4: `larryd key`, `larryd submit`, `larryd status`. What LARRYD itself does is proven here: the key kept yours
only, the signature, the package, every refusal said with what to do, a silent PF HANZO. What PF HANZO answers is proven
live against a scratch PF HANZO host (proofs/), never by a stand-in server here."""
import base64
import hashlib
import hmac
import io
import json
import os
import socket
import stat

import pytest

from larryd import cli, hanzo, hashes, mcp, new

SECRET = 'a' * 64
KEY = 'MAGT_00000000D001_0001'


@pytest.fixture(autouse=True)
def scratch_home(tmp_path, monkeypatch):
    monkeypatch.setenv('LARRYD_HOME', str(tmp_path / 'home'))


def _closed_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def project(tmp_path):
    root = new.make('sub', tmp_path)
    (root / 'larryd.json').write_text(json.dumps({'agent_key': KEY}))
    return root


# ---------------------------------------------------------------- the key
def test_the_key_is_kept_yours_only(tmp_path):
    path = hanzo.save_key('http://127.0.0.1:5010/', 'ada', SECRET)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600 and stat.S_IMODE(os.stat(path.parent).st_mode) == 0o700
    assert hanzo.key() == {'hanzo': 'http://127.0.0.1:5010', 'developer': 'ada', 'secret': SECRET}


def test_a_key_others_can_read_is_refused():
    path = hanzo.save_key('http://127.0.0.1:5010', 'ada', SECRET)
    os.chmod(path, 0o644)
    with pytest.raises(hanzo.Refused, match='can be read by others'):
        hanzo.key()


@pytest.mark.parametrize('address, name, secret', [
    ('127.0.0.1:5010', 'ada', SECRET), ('ftp://h', 'ada', SECRET), ('http://h/api', 'ada', SECRET), ('http://h?x=1', 'ada', SECRET),
    ('http://h', 'Ada', SECRET), ('http://h', '../x', SECRET), ('http://h', 'ada', 'short'), ('http://h', 'ada', 'A' * 64),
])
def test_a_bad_key_is_refused_and_nothing_is_kept(address, name, secret):
    with pytest.raises(hanzo.Refused):
        hanzo.save_key(address, name, secret)
    assert not (hanzo.home() / 'developer.json').exists()


def test_no_key_says_what_to_do():
    with pytest.raises(hanzo.Refused) as no:
        hanzo.key()
    assert '`larryd key' in no.value.todo


def test_the_secret_comes_from_stdin_never_the_command_line(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(SECRET + '\n'))
    assert cli.main(['key', 'http://127.0.0.1:5010', 'ada']) == 0
    assert hanzo.key()['secret'] == SECRET
    assert SECRET not in capsys.readouterr().out


def test_the_key_never_lands_in_the_project(project):
    hanzo.save_key('http://127.0.0.1:5010', 'ada', SECRET)
    assert all(SECRET not in p.read_text() for p in project.rglob('*') if p.is_file())


def test_the_connector_never_takes_the_key():
    assert 'larryd_key' not in mcp.TOOLS
    assert all('secret' not in json.dumps(s[2]) for s in mcp.TOOLS.values())


# ---------------------------------------------------------------- the signature and the package
def test_the_signature_is_the_documented_scheme():
    data = {'agent_key': KEY, 'files': {'agent.py': 'eA=='}}
    at = '2026-09-29T12:00:00+00:00'
    text = '/developer/submit ' + at + ' {"agent_key":"MAGT_00000000D001_0001","files":{"agent.py":"eA=="}}'
    assert hanzo.sign(SECRET, '/developer/submit', data, at) == hmac.new(SECRET.encode(), text.encode(), hashlib.sha256).hexdigest()


def test_the_package_is_agent_only(project):
    (project / 'agent' / '__pycache__').mkdir()
    (project / 'agent' / '__pycache__' / 'x.pyc').write_bytes(b'\x00')
    files, code, manifest = hanzo.package(project)
    assert sorted(files) == ['agent.json', 'agent.py']
    assert base64.b64decode(files['agent.py']) == (project / 'agent' / 'agent.py').read_bytes()
    assert (code, manifest) == (hashes.code(project / 'agent'), hashes.manifest(project / 'agent'))


# ---------------------------------------------------------------- the refusals
def test_the_doctor_comes_first(project):
    hanzo.save_key(f'http://127.0.0.1:{_closed_port()}', 'ada', SECRET)
    path = project / 'agent' / 'agent.py'
    path.write_text(path.read_text() + '\nimport socket\n')
    with pytest.raises(hanzo.Refused) as no:
        hanzo.submit(project)
    assert no.value.more['problems'][0]['check'] == 'the air gap'


def test_no_card_key(project):
    hanzo.save_key(f'http://127.0.0.1:{_closed_port()}', 'ada', SECRET)
    (project / 'larryd.json').write_text('{"agent_key": ""}')
    with pytest.raises(hanzo.Refused, match='holds no card key'):
        hanzo.submit(project)


def test_a_silent_hanzo_is_said(project):
    hanzo.save_key(f'http://127.0.0.1:{_closed_port()}', 'ada', SECRET)
    with pytest.raises(hanzo.Refused) as no:
        hanzo.submit(project)
    assert 'does not answer' in no.value.wrong and 'address' in no.value.todo
    with pytest.raises(hanzo.Refused, match='does not answer'):
        hanzo.status()


def test_other_bytes_held_are_caught(project, monkeypatch):
    hanzo.save_key('http://127.0.0.1:1', 'ada', SECRET)
    monkeypatch.setattr(hanzo, 'call', lambda *a, **k: (200, {'code_sha256': 'f' * 64, 'manifest_sha256': 'e' * 64, 'review': {}}))
    with pytest.raises(hanzo.Refused, match='other bytes'):
        hanzo.submit(project)


def test_the_commands_say_it(project, capsys):
    hanzo.save_key(f'http://127.0.0.1:{_closed_port()}', 'ada', SECRET)
    assert cli.main(['submit', str(project)]) == 1
    assert 'larryd submit: PF HANZO refused it: PF HANZO does not answer. What to do:' in capsys.readouterr().out
    assert cli.main(['status', '--json']) == 1
    assert json.loads(capsys.readouterr().out)['ok'] is False


def test_the_made_project_has_a_place_for_the_card_key(tmp_path):
    assert json.loads((new.make('fresh', tmp_path) / 'larryd.json').read_text()) == {'agent_key': ''}


def test_a_card_key_frost_would_refuse_is_refused_here(project):
    hanzo.save_key(f'http://127.0.0.1:{_closed_port()}', 'ada', SECRET)
    (project / 'larryd.json').write_text('{"agent_key": "MAGT_SCRATCH00001_0001"}')   # capitals, not hex: not a minted key
    with pytest.raises(hanzo.Refused, match='holds no card key'):
        hanzo.submit(project)
