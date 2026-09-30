"""`larryd` with no command: the daemon. LARRYD's runtime on this machine, on 127.0.0.1 only. Its instance is the system's
own place (/var/lib/larryd when root, ~/.larryd otherwise; LARRYD_INSTANCE names another), made here on first start:
its secret (0600), its locker, its logs, and no platform address yet. One line says where it listens and how to stop it.
On a developer's computer it is their own runtime; on a server it is THE runtime."""
import importlib.util
import json
import os
import pathlib
import runpy
import secrets
import shutil
import socket
import sys

PORT = 5010   # the runtime's own port (its schemas' hanzo.json); LARRYD_PORT names another


def instance_dir():
    if os.environ.get('LARRYD_INSTANCE'):
        return pathlib.Path(os.environ['LARRYD_INSTANCE'])
    return pathlib.Path('/var/lib/larryd') if hasattr(os, 'geteuid') and os.geteuid() == 0 else pathlib.Path.home() / '.larryd'


def runtime_dir():
    """The runtime's code, as the package holds it (larryd_runtime)."""
    spec = importlib.util.find_spec('larryd_runtime')
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit("larryd: LARRYD's runtime is not in this install; reinstall larryd")
    return pathlib.Path(list(spec.submodule_search_locations)[0])


def _private_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def prepare(instance, runtime):
    """The instance, made once and kept: nothing is overwritten that is already there."""
    for sub in ('', 'secrets', 'secrets/developers', 'logs', 'agents'):
        _private_dir(instance / sub)
    link = instance / 'secrets' / 'hanzo_link'
    if not link.is_file() or not link.read_text().strip():
        fd = os.open(link, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as fh:
            fh.write(secrets.token_hex(32) + '\n')
    os.chmod(link, 0o600)
    addresses = instance / 'platform.json'
    if not addresses.is_file():
        fd = os.open(addresses, os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, 'w') as fh:
            json.dump({}, fh)   # no platform address yet: every call to the platform is refused in its own words
    marketplace = instance / 'agents' / 'marketplace'
    if not marketplace.is_dir():
        shutil.copytree(runtime / 'agents' / 'marketplace', marketplace, ignore=shutil.ignore_patterns('__pycache__'))


def taken(port):
    with socket.socket() as s:
        try:
            s.bind(('127.0.0.1', port))
        except OSError:
            return True
    return False


def run():
    runtime = runtime_dir()
    instance = instance_dir()
    port = int(os.environ.get('LARRYD_PORT') or PORT)
    if taken(port):
        print(f'larryd: 127.0.0.1:{port} is taken, most likely by a LARRYD runtime already running; stop it, or set LARRYD_PORT', file=sys.stderr)
        return 1
    try:
        prepare(instance, runtime)
    except PermissionError:
        print(f'larryd: cannot make its instance at {instance}: run it as root (sudo larryd &) or set LARRYD_INSTANCE', file=sys.stderr)
        return 1
    if sys.platform.startswith('linux') and not shutil.which('bwrap'):
        print('larryd: agents need bubblewrap on Linux (sudo apt install bubblewrap); until then nothing runs unsandboxed', file=sys.stderr)
    os.environ['LARRYD_INSTANCE'] = str(instance)
    os.environ['LARRYD_PORT'] = str(port)
    print(f"LARRYD's runtime listens on http://127.0.0.1:{port} (pid {os.getpid()}) · its instance: {instance} · stop it: kill {os.getpid()}", flush=True)
    import flask.cli
    flask.cli.show_server_banner = lambda *a, **k: None   # the one line above says it all
    sys.argv = ['larryd']
    runpy.run_path(str(runtime / 'web' / 'app.py'), run_name='__main__')
    return 0
