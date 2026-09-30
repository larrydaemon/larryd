"""`larryd submit`: three steps, one gate, nothing to carry. The doctor first; then agent/ packed into one file
(bundle.py); the file sent to LARRYD's submit door; the claim page opened in the browser, where the developer signs in
with Google or Apple. Nothing to paste and nothing to save: no key, no secret, no account on this computer.
LARRYD_SUBMIT names another door (a scratch one); the default is LARRYD's own."""
import json
import os
import urllib.error
import urllib.request
import webbrowser

from . import bundle, doctor

DOOR = 'https://login.positivefeedback.ai/submit/upload'


class Refused(Exception):
    def __init__(self, wrong, todo, **more):
        super().__init__(wrong)
        self.wrong, self.todo, self.more = wrong, todo, more

    def as_json(self):
        return {'ok': False, 'wrong': self.wrong, 'todo': self.todo, **self.more}


def door():
    return os.environ.get('LARRYD_SUBMIT') or DOOR


def send(data, timeout=60):
    """-> (status, answer): the file to the door. A silent door is (0, {...})."""
    req = urllib.request.Request(door(), data=data, method='POST', headers={'Content-Type': 'application/octet-stream'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        with e:
            try:
                return e.code, json.load(e)
            except ValueError:
                return e.code, {'refused': f'LARRYD answered {e.code}'}
    except (urllib.error.URLError, OSError):
        return 0, {'refused': 'LARRYD does not answer'}


TODO = {0: 'check this computer\'s network, then submit again',
        400: 'the file was not a safe agent file: submit again with this version of larryd',
        413: f'the agent is too big: keep agent/ under {bundle.MOST_FILES} files and {bundle.MOST_BYTES} bytes',
        422: 'fix each problem (`larryd doctor`), then submit again',
        429: 'too many files from this network in an hour: try again later'}


def submit(root, open_browser=True):
    problems = doctor.check(root)
    if problems:
        raise Refused('the doctor found problems; LARRYD would not take this agent', 'fix each one (`larryd doctor`), then submit again',
                      problems=[doctor.asdict(p) for p in problems])
    data, digest = bundle.make(root)
    status, answer = send(data)
    if status != 201 or not str(answer.get('claim', '')).startswith('https://'):
        raise Refused(f"LARRYD refused it: {answer.get('refused', status)}", TODO.get(status, 'read what LARRYD said, fix it, then submit again'),
                      status=status, **({'problems': answer['problems']} if answer.get('problems') else {}))
    opened = bool(open_browser) and webbrowser.open(answer['claim'])
    return {'ok': True, 'sha256': digest, 'claim': answer['claim'], 'minutes': answer.get('minutes', 10), 'opened': opened}
