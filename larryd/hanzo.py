"""THE WAY TO PF HANZO: `larryd key`, `larryd submit`, `larryd status`. LARRYD reaches PF HANZO by signed HTTP to the one
address the developer was given, and by nothing else.
- The developer's key: PF HANZO makes it (a name and a secret, shown once); `larryd key <address> <name>` keeps it in
  ~/.larryd/developer.json (0600), never in the agent project. LARRYD_HOME names another folder (a scratch one).
- The agent's card key: in the project's larryd.json, outside agent/ (it is not a secret).
- The signature: HMAC-SHA256 of route + ' ' + at + ' ' + the data as compact sorted JSON (the route without /api), sent as
  X-Developer (the name), X-Developer-Sig and X-Office-At (the moment, ISO UTC); PF HANZO refuses it outside 60 s."""
import base64
import datetime
import hashlib
import hmac
import json
import os
import pathlib
import re
import stat
import urllib.error
import urllib.parse
import urllib.request

from . import doctor, hashes, shape

PROJECT = 'larryd.json'
KEY = re.compile(r'^[A-Z]{4}_[0-9A-F]{12}_[0-9A-F]{4}$')   # as the platform mints it; FROST's review takes only this
NAME = re.compile(r'^[a-z][a-z0-9-]{1,39}$')


class Refused(Exception):
    def __init__(self, wrong, todo, **more):
        super().__init__(wrong)
        self.wrong, self.todo, self.more = wrong, todo, more

    def as_json(self):
        return {'ok': False, 'wrong': self.wrong, 'todo': self.todo, **self.more}


def home():
    return pathlib.Path(os.environ.get('LARRYD_HOME') or pathlib.Path.home() / '.larryd')


def save_key(address, developer, secret):
    """Keep the developer's key (0600, in a 0700 folder). The secret comes from stdin, never the command line."""
    parts = urllib.parse.urlsplit(address or '')
    if parts.scheme not in ('http', 'https') or not parts.netloc or parts.path not in ('', '/') or parts.query:
        raise Refused(f'"{address}" is not PF HANZO\'s address', 'give the address exactly as PF HANZO gave it, e.g. https://hanzo.example')
    if not NAME.match(developer or ''):
        raise Refused(f'"{developer}" is not a developer name', 'give the name PF HANZO made for you')
    if not re.fullmatch(r'[0-9a-f]{64}', secret or ''):
        raise Refused('that is not a developer secret', 'paste the 64-character secret PF HANZO showed you once')
    folder = home()
    folder.mkdir(parents=True, exist_ok=True)
    os.chmod(folder, 0o700)
    path = folder / 'developer.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump({'hanzo': address.rstrip('/'), 'developer': developer, 'secret': secret}, f)
    os.chmod(path, 0o600)
    return path


def key():
    path = home() / 'developer.json'
    if not path.is_file():
        raise Refused('there is no developer key here', 'run `larryd key <PF HANZO address> <your developer name>` and paste your secret')
    if stat.S_IMODE(os.stat(path).st_mode) & 0o077:
        raise Refused(f'{path} can be read by others', f'make it yours only (chmod 600 {path}), or save the key again with `larryd key`')
    return json.loads(path.read_text())


def sign(secret, route, data, at):
    text = route + ' ' + at + ' ' + json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hmac.new(secret.encode('utf-8'), text.encode('utf-8'), hashlib.sha256).hexdigest()


def call(k, method, route, data, timeout=30):
    """-> (status, answer). A silent PF HANZO is (0, {'refused': ...})."""
    at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    headers = {'X-Developer': k['developer'], 'X-Developer-Sig': sign(k['secret'], route, data, at), 'X-Office-At': at}
    body = None
    if method == 'POST':
        body = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(k['hanzo'] + '/api' + route, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        with e:
            try:
                return e.code, json.load(e)
            except ValueError:
                return e.code, {'refused': f'PF HANZO answered {e.code}'}
    except (urllib.error.URLError, OSError):
        return 0, {'refused': 'PF HANZO does not answer'}


def agent_key(root):
    path = pathlib.Path(root) / PROJECT
    try:
        found = json.loads(path.read_text()).get('agent_key', '') if path.is_file() else ''
    except (ValueError, AttributeError):
        found = ''
    if not KEY.match(found or ''):
        raise Refused(f'{PROJECT} holds no card key', f'put the card key PF HANZO gave you for this agent in {PROJECT}: {{"agent_key": "XXXX_0123456789AB_CDEF"}}')
    return found


def package(root):
    """The agent as PF HANZO will hold it: every file of agent/ (compiled caches are not the agent), and its hashes."""
    agent = pathlib.Path(root) / shape.AGENT
    files = {p.relative_to(agent).as_posix(): base64.b64encode(p.read_bytes()).decode('ascii')
             for p in sorted(agent.rglob('*')) if p.is_file() and '__pycache__' not in p.relative_to(agent).parts}
    return files, hashes.code(agent), hashes.manifest(agent)


def submit(root):
    root = pathlib.Path(root).resolve()
    problems = doctor.check(root)
    if problems:
        raise Refused('the doctor found problems; PF HANZO would not take this agent', 'fix each one (`larryd doctor`), then submit again',
                      problems=[doctor.asdict(p) for p in problems])
    k, card_key = key(), agent_key(root)
    files, code, manifest = package(root)
    status, answer = call(k, 'POST', '/developer/submit', {'agent_key': card_key, 'files': files})
    if status != 200:
        raise Refused(f"PF HANZO refused it: {answer.get('refused', status)}", _todo(status), status=status)
    if (answer.get('code_sha256'), answer.get('manifest_sha256')) != (code, manifest):
        raise Refused('PF HANZO holds other bytes than the ones sent', 'submit again; if it repeats, tell PF HANZO',
                      sent={'code_sha256': code, 'manifest_sha256': manifest}, held=answer)
    return {'ok': True, 'agent_key': card_key, 'code_sha256': code, 'manifest_sha256': manifest, 'review': answer.get('review')}


def _todo(status):
    return {0: 'check PF HANZO\'s address in your developer key (`larryd key`), then submit again',
            401: 'your developer key was refused: save it again with `larryd key` (and check this computer\'s clock)',
            403: 'this agent\'s card key is not yours: check larryd.json',
            413: 'the agent is too big: keep it under 200 files and 5 MB',
            502: 'PF HANZO holds it, but FROST did not take it: submit again later'}.get(status, 'read what PF HANZO said, fix it, then submit again')


def status():
    code, answer = call(key(), 'GET', '/developer/status', {})
    if code != 200:
        raise Refused(f"PF HANZO refused it: {answer.get('refused', code)}", _todo(code), status=code)
    return {'ok': True, **answer}
