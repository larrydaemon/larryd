"""THE DAEMON: `larryd` with no command is LARRYD's runtime on this machine, on 127.0.0.1. Its instance is made on first
start (0700, the secret 0600, no platform address, the marketplace in its locker), one line says where it listens and
how to stop it, a second one on the same port is refused in plain words, and a kill stops it."""
import datetime
import hashlib
import hmac
import json
import os
import pathlib
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request

LARRYD = pathlib.Path(sys.executable).parent / 'larryd'


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def get(port, secret=None):
    at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    headers = {}
    if secret:
        text = '/health ' + at + ' ' + json.dumps({}, sort_keys=True, separators=(',', ':'))
        headers = {'X-Office': hmac.new(secret.encode(), text.encode(), hashlib.sha256).hexdigest(), 'X-Office-At': at}
    try:
        with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}/api/health', headers=headers), timeout=5) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def test_the_daemon(tmp_path):
    port, instance = free_port(), tmp_path / 'instance'
    env = {**os.environ, 'LARRYD_INSTANCE': str(instance), 'LARRYD_PORT': str(port)}
    daemon = subprocess.Popen([str(LARRYD)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        line = daemon.stdout.readline()
        assert line.startswith(f"LARRYD's runtime listens on http://127.0.0.1:{port} (pid {daemon.pid})"), line
        assert f'its instance: {instance}' in line and f'stop it: Ctrl-C (or kill {daemon.pid})' in line
        for _ in range(60):
            try:
                status, body = get(port)
                break
            except OSError:
                time.sleep(0.25)
        assert (status, body) == (401, {'refused': 'not a signed call'})
        secret = (instance / 'secrets' / 'hanzo_link').read_text().strip()
        assert get(port, secret) == (200, {'office': 'hanzo', 'locker': 0, 'runs': 0})
        assert stat.S_IMODE(os.stat(instance).st_mode) == 0o700 and stat.S_IMODE(os.stat(instance / 'secrets' / 'hanzo_link').st_mode) == 0o600
        assert json.loads((instance / 'platform.json').read_text()) == {}
        assert (instance / 'agents' / 'marketplace' / 'agent.py').is_file()
        second = subprocess.run([str(LARRYD)], env={**env, 'LARRYD_INSTANCE': str(tmp_path / 'other')}, capture_output=True, text=True, timeout=30)
        assert second.returncode == 1 and f'127.0.0.1:{port} is taken' in second.stderr
    finally:
        daemon.send_signal(signal.SIGTERM)
        daemon.wait(timeout=10)
    with socket.socket() as s:
        s.bind(('127.0.0.1', port))   # free again: the kill stopped it


def test_ctrl_c_stops_it_without_sudo(tmp_path):
    """The docs' line: `larryd` alone, no sudo, in this terminal; Ctrl-C (SIGINT) stops it and frees the port."""
    port = free_port()
    env = {**os.environ, 'LARRYD_INSTANCE': str(tmp_path / 'instance'), 'LARRYD_PORT': str(port)}
    daemon = subprocess.Popen([str(LARRYD)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert daemon.stdout.readline().startswith("LARRYD's runtime listens")
        for _ in range(60):
            try:
                get(port)
                break
            except OSError:
                time.sleep(0.25)
        daemon.send_signal(signal.SIGINT)
        daemon.wait(timeout=10)
    finally:
        if daemon.poll() is None:
            daemon.kill()
            daemon.wait()
            raise AssertionError('Ctrl-C did not stop the daemon')
    with socket.socket() as s:
        s.bind(('127.0.0.1', port))


def test_help_names_the_daemon(capsys):
    from larryd import cli
    assert cli.main(['help']) == 0
    assert '`larryd` alone starts the daemon' in capsys.readouterr().out


def test_the_runtimes_own_marketplace_is_placed_fresh_and_nothing_else_is_touched(tmp_path):
    from larryd import daemon
    runtime = daemon.runtime_dir()
    instance = tmp_path / 'instance'
    old = instance / 'agents' / 'marketplace'
    old.mkdir(parents=True)
    (old / 'agent.json').write_text('{"name": "an older release"}')
    mine = instance / 'agents' / 'mine'
    mine.mkdir()
    (mine / 'agent.json').write_text('{"name": "the developer\'s"}')
    daemon.prepare(instance, runtime)
    secret = (instance / 'secrets' / 'hanzo_link').read_text()
    assert (old / 'agent.json').read_text() == (runtime / 'agents' / 'marketplace' / 'agent.json').read_text()
    assert 'gives' in json.loads((old / 'agent.json').read_text())
    assert (mine / 'agent.json').read_text() == '{"name": "the developer\'s"}'
    daemon.prepare(instance, runtime)
    assert (instance / 'secrets' / 'hanzo_link').read_text() == secret


def test_larryd_key_is_checked_against_a_real_runtime(tmp_path):
    """`larryd key` against the daemon itself (scratch instance and port): a developer it does not know is refused with
    name-and-secret words; a developer made with `larryd developer add` is known."""
    port, instance = free_port(), tmp_path / 'instance'
    env = {**os.environ, 'LARRYD_INSTANCE': str(instance), 'LARRYD_PORT': str(port), 'LARRYD_HOME': str(tmp_path / 'home')}
    runtime = subprocess.Popen([str(LARRYD)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert runtime.stdout.readline().startswith("LARRYD's runtime listens")
        for _ in range(60):
            try:
                get(port)
                break
            except OSError:
                time.sleep(0.25)
        key = lambda name, secret: subprocess.run([str(LARRYD), 'key', f'http://127.0.0.1:{port}', name], input=secret + '\n',  # noqa: E731
                                                  env=env, capture_output=True, text=True, timeout=30)
        unknown = key('ada', 'b' * 64)
        assert unknown.returncode == 1 and 'LARRYD refused it (401)' in unknown.stderr and 'developer name and secret' in unknown.stderr
        made = subprocess.run([str(LARRYD), 'developer', 'add', 'ada', 'MAGT_00000000D001_0001'], env=env, capture_output=True, text=True, timeout=30)
        secret = made.stdout.strip().rsplit(' ', 1)[-1]
        assert made.returncode == 0 and len(secret) == 64, made.stderr
        known = key('ada', secret)
        assert known.returncode == 0 and 'LARRYD knows you: 1 agent(s) yours' in known.stdout, known.stderr
    finally:
        runtime.send_signal(signal.SIGTERM)
        runtime.wait(timeout=10)


def test_developer_add_needs_the_daemon_started_once(tmp_path):
    env = {**os.environ, 'LARRYD_INSTANCE': str(tmp_path / 'never-started')}
    done = subprocess.run([str(LARRYD), 'developer', 'add', 'ada', 'MAGT_00000000D001_0001'], env=env, capture_output=True, text=True, timeout=30)
    assert done.returncode == 1 and 'start the daemon once' in done.stderr and not (tmp_path / 'never-started').exists()
