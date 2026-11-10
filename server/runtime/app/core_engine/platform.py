"""THE ONLY WAY OUT: the runtime reaches the platform by signed HTTP to the addresses declared in runtime.json (or, for a
scratch run, in instance/platform.json), and by nothing else. A GET signs its query values as strings and a POST its
JSON body, as the platform's offices do; the route is signed without the /api prefix."""
import datetime
import json
import pathlib
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from . import signing


def addresses(config, side, instance):
    scratch = pathlib.Path(instance) / 'platform.json' if instance else None
    if scratch and scratch.is_file():
        return json.loads(scratch.read_text())
    return {office: sides[side] for office, sides in config['platform'].items() if isinstance(sides, dict)}


TOO_LARGE = 'the answer is larger than this call may hold'   # a size-capped GET's own fixed words (get(most=...))

class Client:
    """outbound + slot: the hardened scheme (Cloud Run): the call to that slot signed with the runtime's own key for it,
    a key id, a nonce and the moment (the same 60-second window the platform checks). Without them, the laptop's shared
    secret. No call is ever signed with an empty key: it is refused before it leaves.

    retry_seconds (Cloud Run): a call that gets no answer is tried again after 0.5, 1, 2, 4, 8 ... seconds until that
    many seconds have passed, each try signed again with a FRESH nonce and moment. A GET is retried on any lost answer;
    a POST only when it never left (the connection or the handshake failed), so a delivery or a charge is never sent
    twice. 0 = one try (the laptop).

    asks_again_once_sent=False (an office on this computer, LARRYD RUNTIME INTERNAL; the owner 2026-11-10: "slow"): a GET that
    left and got no answer in time is never sent again. The office holds it and is still working on it (no Cloud NAT between
    them loses an answer here); asking again only adds the same work while it is behind: on 2026-11-10 one board page made
    each call 3 to 4 copies and every answer took 30 to 70 s. A call that never left (the office restarting) is still retried."""
    BACKOFF = (0.5, 1, 2, 4, 8, 16, 32)

    def __init__(self, addresses, secret, timeout=10, outbound=None, slot=None, retry_seconds=0, clock=time.monotonic, sleep=time.sleep,
                 asks_again_once_sent=True):
        self.addresses = dict(addresses)
        self.secret = secret
        self.timeout = timeout
        self.outbound, self.slot = outbound, slot
        self.retry_seconds, self.clock, self.sleep = retry_seconds, clock, sleep
        self.asks_again_once_sent = asks_again_once_sent

    def _headers(self, route, data, at):
        if self.outbound is not None:
            key_id, key = self.outbound.key(self.slot)
            nonce = secrets.token_hex(16)
            return {'X-Office-Key': key_id, 'X-Office-Nonce': nonce, 'X-Office-At': at,
                    'X-Office': signing.sign_hardened(key, route, data, at, nonce)}
        return {'X-Office': signing.sign(self.secret, route, data, at), 'X-Office-At': at}

    def _send(self, office, method, route, data, most=None):
        if not self.addresses.get(office):
            return 0, {'refused': f'{office} has no address here'}   # an undeclared office is never called: a plain refusal
        until = self.clock() + self.retry_seconds
        for pause in self.BACKOFF + (None,):
            status, body, again = self._once(office, method, route, data, most)
            if not again or pause is None or self.clock() + pause >= until:
                return status, body
            self.sleep(pause)

    def _once(self, office, method, route, data, most=None):
        """-> status, body, and whether a retry is safe and useful (no answer came; for a POST, nothing left). most: THE ANSWER'S
        MOST BYTES (a reference file read whole, the lips gaps 2026-11-06): an answer whose length says it is over is refused before a
        byte of it is read, one that turns out over is refused at most + 1 bytes, never held whole; refused in fixed words, never retried."""
        base = self.addresses[office]
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        try:
            headers = self._headers(route, data, at)
        except (ValueError, LookupError):
            return 0, {'refused': f'no key to sign a call to {office}'}, False   # fail closed: nothing unsigned ever leaves
        url = base + '/api' + route
        body = None
        if method == 'GET':
            url += ('?' + urllib.parse.urlencode(data)) if data else ''
        else:
            body = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers, method=method), timeout=self.timeout) as r:
                if most is None:
                    return r.status, json.load(r), False
                said = r.headers.get('Content-Length')
                if said is not None and said.isdigit() and int(said) > most:
                    return 413, {'refused': TOO_LARGE}, False   # its length says it is over: not one byte of it is read
                raw = r.read(most + 1)
                if len(raw) > most:
                    return 413, {'refused': TOO_LARGE}, False   # over, found while reading: never held whole
                return r.status, json.loads(raw), False
        except urllib.error.HTTPError as e:
            with e:
                try:
                    return e.code, json.load(e), False
                except ValueError:
                    return e.code, {'refused': f'{office} answered {e.code}'}, False
        except urllib.error.URLError:   # raised before the answer was read: the connection, the handshake or the sending failed
            return 0, {'refused': f'{office} does not answer'}, True
        except OSError:   # sent, then no answer: a GET may ask again, a POST may have been taken
            return 0, {'refused': f'{office} does not answer'}, method == 'GET' and self.asks_again_once_sent

    def get(self, office, route, data=None, most=None):
        return self._send(office, 'GET', route, {k: str(v) for k, v in (data or {}).items()}, most)

    def post(self, office, route, data):
        return self._send(office, 'POST', route, data)
