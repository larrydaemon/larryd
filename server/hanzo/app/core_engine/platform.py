"""THE ONLY WAY OUT: HANZO reaches the platform by signed HTTP to the addresses declared in hanzo.json (or, for a
scratch run, in instance/platform.json), and by nothing else. A GET signs its query values as strings and a POST its
JSON body, as the platform's offices do; the route is signed without the /api prefix."""
import datetime
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

from . import signing


def addresses(config, side, instance):
    scratch = pathlib.Path(instance) / 'platform.json' if instance else None
    if scratch and scratch.is_file():
        return json.loads(scratch.read_text())
    return {office: sides[side] for office, sides in config['platform'].items() if isinstance(sides, dict)}


class Client:
    def __init__(self, addresses, secret, timeout=10):
        self.addresses = dict(addresses)
        self.secret = secret
        self.timeout = timeout

    def _send(self, office, method, route, data):
        base = self.addresses[office]
        at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        headers = {'X-Office': signing.sign(self.secret, route, data, at), 'X-Office-At': at}
        url = base + '/api' + route
        body = None
        if method == 'GET':
            url += ('?' + urllib.parse.urlencode(data)) if data else ''
        else:
            body = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers, method=method), timeout=self.timeout) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            with e:
                try:
                    return e.code, json.load(e)
                except ValueError:
                    return e.code, {'refused': f'{office} answered {e.code}'}
        except (urllib.error.URLError, OSError):
            return 0, {'refused': f'{office} does not answer'}

    def get(self, office, route, data=None):
        return self._send(office, 'GET', route, {k: str(v) for k, v in (data or {}).items()})

    def post(self, office, route, data):
        return self._send(office, 'POST', route, data)
