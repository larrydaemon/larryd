"""`larryd submit` (0.1.1): the doctor, one file, the claim page in the browser. Nothing to paste, nothing to keep: no
key, no secret, no card key. Proven against LARRYD's own submit door (larryd/submit_door.py) served on a scratch port
here: the same code the larryd machine runs, never a stand-in."""
import json
import socket
import threading

import pytest
from werkzeug.serving import make_server

from larryd import cli, mcp, new, sso_handoff, submit, submit_door


@pytest.fixture
def door(tmp_path, monkeypatch):
    _, public = sso_handoff.new_key()
    conf = json.loads(json.dumps(submit_door.CONFIG))
    conf['proxy']['public_key'] = public.decode()
    server = make_server('127.0.0.1', 0, submit_door.create_app(tmp_path / 'door', conf))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv('LARRYD_SUBMIT', f'http://127.0.0.1:{server.server_port}/submit/upload')
    opened = []
    monkeypatch.setattr(submit.webbrowser, 'open', lambda url: opened.append(url) or True)
    yield {'dir': tmp_path / 'door', 'opened': opened}
    server.shutdown()


@pytest.fixture
def project(tmp_path):
    return new.make('sub', tmp_path)


def _held(door):
    return sorted(p.name for p in (door['dir'] / 'held').iterdir())


def test_submit_sends_one_file_and_opens_the_claim_page(door, project):
    out = submit.submit(project)
    assert out['ok'] and out['claim'].startswith('https://login.positivefeedback.ai/submit/claim/') and out['minutes'] == 10
    assert door['opened'] == [out['claim']] and len(_held(door)) == 1


def test_the_doctor_comes_first_and_nothing_is_sent(door, project):
    code = project / 'agent' / 'agent.py'
    code.write_text(code.read_text() + '\nimport socket\n')
    with pytest.raises(submit.Refused) as no:
        submit.submit(project)
    assert no.value.more['problems'][0]['check'] == 'the air gap' and _held(door) == [] and door['opened'] == []


def test_the_door_refusing_is_said_with_what_to_do(door, project, monkeypatch):
    import types
    monkeypatch.setattr(submit, 'doctor', types.SimpleNamespace(check=lambda root: [], asdict=None))   # this side's doctor let it through; the door's own doctor still reads it
    code = project / 'agent' / 'agent.py'
    code.write_text(code.read_text() + '\nimport socket\n')
    with pytest.raises(submit.Refused) as no:
        submit.submit(project)
    assert no.value.more['status'] == 422 and 'fix each problem' in no.value.todo and _held(door) == []


def test_a_silent_door_is_said(project, monkeypatch):
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    monkeypatch.setenv('LARRYD_SUBMIT', f'http://127.0.0.1:{port}/submit/upload')
    with pytest.raises(submit.Refused) as no:
        submit.submit(project)
    assert 'does not answer' in no.value.wrong and 'network' in no.value.todo


def test_the_command_says_it(door, project, capsys):
    assert cli.main(['submit', str(project), '--no-browser']) == 0
    said = capsys.readouterr().out
    assert 'Sign in with Google or Apple to submit it, within 10 minutes' in said and 'open it in your browser' in said and door['opened'] == []
    assert cli.main(['submit', str(project), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['opened'] is True


def test_the_connector_submits_the_same_way(door, project):
    out, is_error = mcp.TOOLS['larryd_submit'][0]({'path': str(project)})
    assert out['ok'] and not is_error and len(_held(door)) == 1


def test_nothing_to_paste_or_keep(project, tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    assert not (project / 'larryd.json').exists()
    for gone in (['key'], ['status'], ['developer', 'add', 'ada', 'MAGT_00000000D001_0001']):
        with pytest.raises(SystemExit):
            cli.main(gone)
    assert not (tmp_path / 'home').exists()
    assert set(mcp.TOOLS) == {'larryd_new', 'larryd_doctor', 'larryd_run', 'larryd_submit', 'larryd_skills', 'larryd_pack'}


def test_version(capsys):
    from larryd import __version__
    with pytest.raises(SystemExit) as done:
        cli.main(['--version'])
    assert done.value.code == 0 and capsys.readouterr().out == f'larryd {__version__}\n'
