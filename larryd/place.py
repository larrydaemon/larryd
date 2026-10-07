"""`larryd place` and `larryd card`: your agent on your own LARRYD's shelf. place packs agent/ exactly as submit does
(the doctor first) and hands it to the runtime running on this computer, which holds it in its locker the way the
server holds an approved agent, and gives it a card key for this computer. card does that and opens the marketplace
page, where every agent this runtime holds is a card with its hire toggle, as the platform will show it. Nothing
leaves this computer."""
import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
import webbrowser

from . import bundle, doctor, shape

PORT = 5010   # the runtime's own port; LARRYD_PORT names another (as it does for the daemon)
PAGE = '/marketplace'


class Refused(Exception):
    def __init__(self, wrong, todo, **more):
        super().__init__(wrong)
        self.wrong, self.todo, self.more = wrong, todo, more

    def as_json(self):
        return {'ok': False, 'wrong': self.wrong, 'todo': self.todo, **self.more}


def address():
    return f"http://127.0.0.1:{int(os.environ.get('LARRYD_PORT') or PORT)}"


def key_for(name):
    """A card key for this computer only, the same for the same name: the platform gives the real one at approval."""
    digest = hashlib.sha256(str(name).encode('utf-8')).hexdigest().upper()
    return f'DAGT_{digest[:12]}_{digest[12:16]}'


WAIT = 6.0   # seconds `place` and `card` keep asking a runtime that is still starting, before saying none answers


def _post(url, data, timeout=30, wait=None):
    """POST once; a refused connection (a runtime still starting) is asked again every half second for WAIT seconds."""
    end = time.monotonic() + (WAIT if wait is None else wait)
    while True:
        status, answer = _post_once(url, data, timeout)
        if status or time.monotonic() >= end:
            return status, answer
        time.sleep(0.5)


def _post_once(url, data, timeout):
    req = urllib.request.Request(url, data=data, method='POST', headers={'Content-Type': 'application/octet-stream', 'X-Larryd-Place': '1'})
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
        return 0, {'refused': 'no LARRYD runtime answers'}


def place(root):
    """-> {ok, agent_key, sha256, held, marketplace}. Refused with what is wrong and what to do."""
    doctor.fix_look(root)   # a design sheet becomes the look record, as submit does (never a reason to refuse)
    problems = doctor.check(root)
    if problems:
        raise Refused('the doctor found problems; LARRYD would not hold this agent', 'fix each one (`larryd doctor`), then place it again',
                      problems=[doctor.asdict(p) for p in problems])
    name = json.loads((pathlib.Path(root) / shape.AGENT / shape.MANIFEST).read_text())['name']
    data, digest = bundle.make(root)
    key = key_for(name)
    status, answer = _post(f'{address()}{PAGE}/place?key={key}', data)
    if status == 0:
        raise Refused(f'no LARRYD runtime answers on {address()}', 'start it first: run `larryd` in another terminal, then place again')
    if status == 401:
        raise Refused(f'the LARRYD on {address()} is a server, not your own runtime', 'start your own with `larryd` (set LARRYD_PORT if 5010 is taken)')
    if status != 201:
        raise Refused(f"LARRYD did not hold it: {answer.get('refused', status)}", 'read what LARRYD said, fix it, then place again')
    return {'ok': True, 'agent_key': key, 'sha256': digest, 'held': answer.get('held', {}), 'marketplace': f'{address()}{PAGE}'}


def card(root, open_browser=True):
    """place, then the marketplace page in the browser (or its address, with open_browser=False)."""
    out = place(root)
    opened = bool(open_browser) and bool(webbrowser.open(out['marketplace']))
    return {**out, 'opened': opened}
