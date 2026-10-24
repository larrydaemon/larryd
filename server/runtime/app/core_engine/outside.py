"""THE OUTSIDE HAND (the owner, 2026-10-08: the Nano Banana 2 image generator and the Seedance 2.5 video generator, "all built
with larryd developer like the other agents"): an agent never reaches out; it only ASKS, in its answer, for something to be
made by a model on THE LIST below, and LARRYD's own hand does the errand. The laws, kept from the platform's first external
lane and the owner's errand standard:
1. THE LIST ONLY. Every address is built here from the list; nothing an agent or a member writes is ever an address.
2. A FIXED GRAMMAR. What goes out is the model's own few fields, each checked against its choices; nothing else is sent.
3. THE KEY NEVER TRAVELS. The harness reads it for one errand, passes it into the calls below, and forgets it: it is never
   handed to an agent, stored, logged or put in a reason.
4. POLL, NEVER LISTEN. The hand asks the provider until the work is done or the model's time is up; nothing waits for a call in.
5. WHAT COMES BACK IS NOT TRUSTED. It is fetched only from the provider's own delivery hosts over https, cut at the model's
   size, and it must BE the kind the model makes (read from its first bytes, never from a name or a header). It goes to the
   member's DA-M and nowhere else: never into an agent's run.
Every refusal is LARRYD's own fixed words (never the provider's text, which is outside text: data, never orders), short
and without a colon, so the run record's code keeps the whole of it (NOT_MADE_REPLICATE_REFUSED_THE_KEY)."""
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

PROVIDERS = {
    'replicate': {'name': 'Replicate', 'api': 'https://api.replicate.com/v1', 'delivery': ('.replicate.delivery',)},
}
MODELS = {
    'nano-banana-2': {
        'provider': 'replicate', 'path': 'google/nano-banana-2', 'kind': 'image', 'name': 'Nano Banana 2',
        'choices': {'aspect': ('1:1', '3:4', '4:3', '16:9', '9:16')},
        'first': {'aspect': '1:1'},
        'reference': 'image_input',   # THE REFERENCE (R-0040, the owner 2026-10-24: "the reference toggle and enter input box to add a key"): the member's own picture, by its DA-M key
        'most_bytes': 20 * 1024 * 1024, 'most_seconds': 180,
    },
    'seedance-2.5': {
        'provider': 'replicate', 'path': 'bytedance/seedance-2.5', 'kind': 'video', 'name': 'Seedance 2.5',
        # EVERY LENGTH THE MODEL TAKES (R-0041, the owner 2026-10-24: "give it all duration options ... doe the most we can"): Replicate's own schema
        # for bytedance/seedance-2.5 says duration is an integer, 4 to 30 seconds (-1, the model's own pick, is not offered: the member picks)
        'choices': {'aspect': ('16:9', '9:16', '1:1'), 'seconds': tuple(str(n) for n in range(4, 31)), 'size': ('480p', '720p')},
        'first': {'aspect': '16:9', 'seconds': '5', 'size': '720p'},
        'reference': 'reference_images',   # THE REFERENCE (R-0041): the member's own picture, by its DA-M key, as the model's reference image (style, character, scene)
        'most_bytes': 24 * 1024 * 1024, 'most_seconds': 1800,   # DA-M takes 25 MB with no zone named; a 30 second render takes longer than a 5 second one
    },
}
KINDS = {'image': ('png', 'jpg', 'webp'), 'video': ('mp4',)}
MOST_PROMPT = 4000
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 _-]{0,79}$')   # the file's plain name, without its ending (the hand adds the kind's own)
_ID = re.compile(r'^[A-Za-z0-9]{1,64}$')                  # a provider's request id, before it is put in an address
EVERY_SECONDS = 3
DAM_KEY = re.compile(r'DA-M_[0-9A-F]{12}_[0-9A-F]{4}')   # a member's file in DA-M, by DA-M's own key (so files.KEY): the only way a reference is named
REFERENCE_KINDS = ('png', 'jpg', 'webp')                 # a reference is a picture, read from its first bytes
MOST_REFERENCE = 10 * 1024 * 1024                        # bytes of one reference picture


def declared(manifest):
    """The models the manifest declares ("makes": ["nano-banana-2"]), each on the list; an ill-formed declaration counts for nothing."""
    asked = manifest.get('makes') if isinstance(manifest, dict) else None
    if not (isinstance(asked, list) and asked and all(isinstance(m, str) and m in MODELS for m in asked)):
        return ()
    return tuple(dict.fromkeys(asked))


def check(makes, allowed):
    """-> (asks as the hand takes them, '') or ([], why): ONE ask in an answer, a declared model, words to make it from, each choice
    one of the model's own, a plain name. Anything else refuses the answer; nothing goes out."""
    if not (isinstance(makes, list) and len(makes) == 1 and isinstance(makes[0], dict)):
        return [], 'the answer\'s makes is not a list of one ask'
    ask = makes[0]
    model = ask.get('model')
    if not (isinstance(model, str) and model in allowed):
        return [], 'the ask names a model the agent does not declare'
    spec = MODELS[model]
    if set(ask) - {'model', 'prompt', 'name', *spec['choices'], *(('reference',) if spec.get('reference') else ())}:
        return [], f'the ask holds more than {spec["name"]} takes'
    prompt = ask.get('prompt')
    if not (isinstance(prompt, str) and prompt.strip() and len(prompt) <= MOST_PROMPT):
        return [], f'the ask carries no words, or more than {MOST_PROMPT} characters'
    name = ask.get('name')
    if not (isinstance(name, str) and NAME.fullmatch(name)):
        return [], 'the ask names no plain file name'
    out = {'model': model, 'prompt': prompt.strip(), 'name': name}
    for choice, values in spec['choices'].items():
        value = ask.get(choice, spec['first'][choice])
        if not (isinstance(value, str) and value in values):
            return [], f'the ask\'s {choice} is not one of {", ".join(values)}'
        out[choice] = value
    if 'reference' in ask:   # optional: a DA-M key and nothing else (never an address: law 1); the harness reads the file for this member
        if not (isinstance(ask['reference'], str) and DAM_KEY.fullmatch(ask['reference'])):
            return [], 'the ask\'s reference is not a DA-M key'
        out['reference'] = ask['reference']
    return [out], ''


def goes_out(ask, reference=''):
    """What leaves for the provider, field by field (law 2): the words and the model's own choices, and the reference picture's
    address at the provider when the ask names one (reference: the address the provider's own file door gave it), nothing else."""
    if ask['model'] == 'nano-banana-2':
        out = {'prompt': ask['prompt'], 'aspect_ratio': ask['aspect'], 'resolution': '1K', 'output_format': 'png'}
    elif ask['model'] == 'seedance-2.5':
        out = {'prompt': ask['prompt'], 'duration': int(ask['seconds']), 'resolution': ask['size'], 'aspect_ratio': ask['aspect'],
               'generate_audio': False}   # never a sound track nobody asked for
    else:
        raise KeyError(ask['model'])
    if reference:
        out[MODELS[ask['model']]['reference']] = [reference]
    return out


def kind_of(data):
    """What a file IS, from its first bytes: png, jpg, webp, mp4, or '' (law 5)."""
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if data[:3] == b'\xff\xd8\xff':
        return 'jpg'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    if data[4:8] == b'ftyp':
        return 'mp4'
    return ''


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):   # an answer that points elsewhere is not followed (law 1)
        return None


class Hand:
    """One provider's doors, reached only as the list says. places: {provider: {'api', 'delivery'}} replaces the list's addresses
    (the lab's stand-in provider, a test); it comes from the runtime's own start, never from a call."""

    def __init__(self, places=None, sleep=time.sleep, clock=time.monotonic, opener=None):
        self.places = {**{p: {'api': v['api'], 'delivery': v['delivery']} for p, v in PROVIDERS.items()}, **(places or {})}
        self.sleep, self.clock = sleep, clock
        self.opener = opener or urllib.request.build_opener(_NoRedirect)

    def _call(self, method, url, key, body=None, most=1024 * 1024, seconds=60, raw=None):
        """-> (status, bytes). 0 when the provider could not be reached. The key rides in the one header and nowhere else.
        raw: (bytes, content type) sent as they are (a file for the provider's own file door)."""
        headers = {'Accept': 'application/json'}
        if key:
            headers['Authorization'] = f'Bearer {key}'
        data = None
        if body is not None:
            data, headers['Content-Type'] = json.dumps(body).encode('utf-8'), 'application/json'
        elif raw is not None:
            data, headers['Content-Type'] = raw
        try:
            with self.opener.open(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=seconds) as r:
                return r.status, r.read(most + 1)
        except urllib.error.HTTPError as e:
            return e.code, b''
        except (urllib.error.URLError, OSError, ValueError):
            return 0, b''

    @staticmethod
    def _json(raw):
        try:
            out = json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return {}
        return out if isinstance(out, dict) else {}

    def _refusal(self, status, name):
        if status == 0:
            return f'{name} unreachable'
        if status in (401, 403):
            return f'{name} refused the key'
        if status == 402:
            return f'{name} out of credit'
        if status == 429:
            return f'{name} is busy'
        return f'{name} answered {status}'

    def lend(self, ask, picture, key):
        """THE REFERENCE PICTURE, LENT TO THE PROVIDER: the member's picture (bytes the harness read from their DA-M) put through the
        provider's own file door (Replicate's /files, on the list's api address, with the key), so the model can read it there.
        -> (its address at the provider, '') or ('', why). Only a picture goes (from its first bytes), within MOST_REFERENCE; the
        address that comes back must be on the provider's own api address (law 1: nothing the provider says is followed elsewhere)."""
        spec = MODELS[ask['model']]
        place, name = self.places[spec['provider']], PROVIDERS[spec['provider']]['name']
        kind = kind_of(picture)
        if kind not in REFERENCE_KINDS:
            return '', 'the reference is not a picture'
        if len(picture) > MOST_REFERENCE:
            return '', 'the reference picture is too large'
        mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'webp': 'image/webp'}[kind]
        edge = 'larryd' + hashlib.sha256(picture).hexdigest()[:24]
        body = (f'--{edge}\r\nContent-Disposition: form-data; name="content"; filename="reference.{kind}"\r\nContent-Type: {mime}\r\n\r\n').encode('ascii') + picture + f'\r\n--{edge}--\r\n'.encode('ascii')
        status, raw = self._call('POST', f"{place['api']}/files", key, raw=(body, f'multipart/form-data; boundary={edge}'), seconds=120)
        if status not in (200, 201):
            return '', self._refusal(status, name)
        urls = self._json(raw).get('urls')
        address = urls.get('get') if isinstance(urls, dict) else None
        if not (isinstance(address, str) and address.startswith(place['api'] + '/files/') and len(address) < 400 and '..' not in address):
            return '', f'{name} gave no address for the reference'
        return address, ''

    def submit(self, ask, key, reference=''):
        """-> (request id, '') or ('', why)."""
        spec = MODELS[ask['model']]
        place, name = self.places[spec['provider']], PROVIDERS[spec['provider']]['name']
        status, raw = self._call('POST', f"{place['api']}/models/{spec['path']}/predictions", key, {'input': goes_out(ask, reference)})
        if status not in (200, 201, 202):
            return '', self._refusal(status, name)
        rid = self._json(raw).get('id')
        if not (isinstance(rid, str) and _ID.fullmatch(rid)):
            return '', f'{name} gave no request id'
        return rid, ''

    def poll(self, ask, rid, key):
        """-> ('waiting' | 'done' | 'failed', the file's address or why)."""
        spec = MODELS[ask['model']]
        place, name = self.places[spec['provider']], PROVIDERS[spec['provider']]['name']
        status, raw = self._call('GET', f"{place['api']}/predictions/{rid}", key)
        if status in (401, 403, 402):
            return 'failed', self._refusal(status, name)
        if status != 200:
            return 'waiting', ''   # a blip: asked again until the model's time is up
        body = self._json(raw)
        state = str(body.get('status') or '').lower()
        if state == 'succeeded':
            out = body.get('output')
            out = out[0] if isinstance(out, list) and out else out
            return ('done', out) if isinstance(out, str) and out else ('failed', f'{name} made nothing')
        if state in ('failed', 'canceled'):
            return 'failed', f'{name} failed'   # its own reason is outside text: never carried
        return 'waiting', ''

    def _from_delivery(self, address, hosts):
        try:
            parts = urllib.parse.urlsplit(address)
            port = parts.port
        except ValueError:
            return False
        host = (parts.hostname or '').lower()
        if parts.scheme == 'https' and not parts.username and not parts.password and port is None:
            return any(host.endswith(h) or host == h.lstrip('.') for h in hosts if h.startswith('.'))   # the delivery host itself (replicate.delivery) or a name under it
        # A STAND-IN PROVIDER ON THIS MACHINE (the lab, a test): its whole origin, named at the runtime's own start (places), loopback only; the list itself names none
        return any(h.startswith('http://127.0.0.1:') and address.startswith(h) for h in hosts)

    def fetch(self, ask, address):
        """-> (bytes, its kind, '') or (b'', '', why): only from the provider's delivery hosts, cut at the model's size, and it must be
        the kind the model makes."""
        spec = MODELS[ask['model']]
        place, name = self.places[spec['provider']], PROVIDERS[spec['provider']]['name']
        if not self._from_delivery(address, place['delivery']):
            return b'', '', f'file not from {name}'
        status, data = self._call('GET', address, '', most=spec['most_bytes'], seconds=300)   # the key is never sent to a delivery host
        if status != 200:
            return b'', '', 'file not fetched'
        if len(data) > spec['most_bytes']:
            return b'', '', 'file too large'
        kind = kind_of(data)
        if kind not in KINDS[spec['kind']]:
            return b'', '', f'file not {"a picture" if spec["kind"] == "image" else "a video"}'
        return data, kind, ''

    def make(self, ask, key, picture=b''):
        """The whole errand: -> ({'name', 'kind', 'data'}, '') or (None, why). picture: the reference's bytes when the ask names one
        (the harness read them from the member's DA-M); an ask that names a reference and has none makes nothing."""
        spec = MODELS[ask['model']]
        name = PROVIDERS[spec['provider']]['name']
        reference = ''
        if ask.get('reference'):
            if not picture:
                return None, 'the reference picture was not read'
            reference, why = self.lend(ask, picture, key)
            if why:
                return None, why
        rid, why = self.submit(ask, key, reference)
        if why:
            return None, why
        until = self.clock() + spec['most_seconds']
        while True:
            state, said = self.poll(ask, rid, key)
            if state == 'failed':
                return None, said
            if state == 'done':
                break
            if self.clock() >= until:
                return None, f'{name} timed out'
            self.sleep(EVERY_SECONDS)
        data, kind, why = self.fetch(ask, said)
        if why:
            return None, why
        return {'name': f"{ask['name']}.{kind}", 'kind': kind, 'data': data}, ''
