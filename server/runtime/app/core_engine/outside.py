"""THE OUTSIDE HAND (the owner, 2026-10-08: the Nano Banana 2 image generator and the Seedance 2.5 video generator, "all built
with larryd developer like the other agents"): an agent never reaches out; it only ASKS, in its answer, for something to be
made by a model on THE LIST below, and LARRYD's own hand does the errand. The laws, kept from the platform's first external
lane and the owner's errand standard:
1. THE LIST ONLY. Every address is built here from the list; nothing an agent or a member writes is ever an address.
2. A FIXED GRAMMAR. What goes out is the model's own few fields, each checked against its choices (a word) or its range (a short list
   of numbers); nothing else is sent. Words (the prompt) are asked only of a model that takes them.
3. THE KEY NEVER TRAVELS. The harness reads it for one errand, passes it into the calls below, and forgets it: it is never
   handed to an agent, stored, logged or put in a reason.
4. POLL, NEVER LISTEN. The hand asks the provider until the work is done or the model's time is up; nothing waits for a call in.
5. WHAT GOES OUT AS A REFERENCE IS THE MODEL'S OWN KIND: each reference is read from its first bytes and must be a kind its slot takes
   (a picture for Replicate's models; an Exxact type's own input slot kinds, wav and mp4 among them), within that slot's most bytes.
6. WHAT COMES BACK IS NOT TRUSTED. It is fetched only from the provider's own delivery hosts over https, cut at the model's
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

from . import exxact

PROVIDERS = {
    'replicate': {'name': 'Replicate', 'api': 'https://api.replicate.com/v1', 'delivery': ('.replicate.delivery',)},
    # THE EXXACT BOX (CORE_CLEANUP_IV 97, Exxact_Loot's spec): no address and no vault key; its own hand (exxact_hand.py) drops a job into the
    # missions bucket and collects the box's answer from the returns bucket, with the runtime's own token (the buckets and keys: S4, later)
    'exxact': {'name': 'Exxact', 'api': '', 'delivery': ()},
}
MODELS = {
    'nano-banana-2': {
        'provider': 'replicate', 'path': 'google/nano-banana-2', 'kind': 'image', 'name': 'Nano Banana 2', 'prompt': True,
        # THE SIZE (CORE_CLEANUP_IV 19, the owner's blanket approval 2026-11-06): Replicate's own model text says resolution is a string and the
        # model makes 512px, 1K, 2K and 4K; 1K stays the first (as before), 2K is the larger the rows asked for (row 217 Upscale); 4K is not offered
        'choices': {'aspect': ('1:1', '3:4', '4:3', '16:9', '9:16'), 'size': ('1K', '2K')},
        'first': {'aspect': '1:1', 'size': '1K'},
        'reference': 'image_input',
        'most_references': 2,   # UP TO TWO REFERENCE PICTURES (CORE_CLEANUP_IV 18: rows 182 Face Swap, 193 Nose: "the second image is only a shape reference"); Replicate's image_input is a list (up to 14)   # THE REFERENCE (R-0040, the owner 2026-10-24: "the reference toggle and enter input box to add a key"): the member's own picture, by its DA-M key
        'most_bytes': 20 * 1024 * 1024, 'most_seconds': 180,
    },
    'seedance-2.5': {
        'provider': 'replicate', 'path': 'bytedance/seedance-2.5', 'kind': 'video', 'name': 'Seedance 2.5', 'prompt': True,
        # EVERY LENGTH THE MODEL TAKES (R-0041, the owner 2026-10-24: "give it all duration options ... doe the most we can"): Replicate's own schema
        # for bytedance/seedance-2.5 says duration is an integer, 4 to 30 seconds (-1, the model's own pick, is not offered: the member picks)
        'choices': {'aspect': ('16:9', '9:16', '1:1'), 'seconds': tuple(str(n) for n in range(4, 31)), 'size': ('480p', '720p')},
        'first': {'aspect': '16:9', 'seconds': '5', 'size': '720p'},
        'reference': 'reference_images',
        'most_references': 1,   # THE REFERENCE (R-0041): the member's own picture, by its DA-M key, as the model's reference image (style, character, scene)
        'most_bytes': 24 * 1024 * 1024, 'most_seconds': 1800,   # DA-M takes 25 MB with no zone named; a 30 second render takes longer than a 5 second one
    },
    # CORE_CLEANUP_IV 44 (frost-05 under the owner's blanket approval; the owner 12:45: model vendors go through this list, one Replicate key):
    # the fields as Replicate's own model text names them (replicate.com/<path>/llms.txt, read 2026-11-06); the choices are the conservative
    # values of its own examples and the vendor's documented ones, each proven by one real make before an agent ships on it
    'flux-krea': {
        'provider': 'replicate', 'path': 'black-forest-labs/flux-krea-dev', 'kind': 'image', 'name': 'FLUX Krea', 'prompt': True,
        'choices': {'aspect': ('1:1', '16:9', '9:16', '4:3', '3:4')},
        'first': {'aspect': '1:1'},
        'reference': 'image', 'reference_one': True,   # image to image: ONE picture, sent as a plain address (the model's "image" is a string)
        'most_references': 1,
        'most_bytes': 20 * 1024 * 1024, 'most_seconds': 180,
    },
    'kling-2.5': {
        'provider': 'replicate', 'path': 'kwaivgi/kling-v2.5-turbo-pro', 'kind': 'video', 'name': 'Kling 2.5', 'prompt': True,
        'choices': {'aspect': ('16:9', '9:16', '1:1'), 'seconds': ('5', '10')},
        'first': {'aspect': '16:9', 'seconds': '5'},
        'reference': 'start_image', 'reference_one': True,   # the first frame: ONE picture (the model then ignores the aspect, its own text says)
        'most_references': 1,
        'most_bytes': 24 * 1024 * 1024, 'most_seconds': 900,
    },
}
MOST_SAID = 1024 * 1024   # bytes of what an Exxact type that makes no file says (its numbers, as JSON)
NUMBER_RULES = ('list_numbers', 'list_ints')   # the number rules exxact.check_fields reads (a short list of numbers, of whole numbers), and no other
NUMBER_KEYS = NUMBER_RULES + ('most', 'optional')
_KIND_NAMES = {'jpeg': 'jpg'}   # exxact.kind_of says jpeg where kind_of here says jpg


def _exxact_models():
    """THE EXXACT BOX'S TYPES ON THE LIST (CORE_CLEANUP_IV 97): one model per type, named 'exxact/<type>', read from exxact.TYPES (never
    copied by hand), so a type added on Exxact_Loot's side is on the list here. The ask's grammar (check) is the same for every model:
    a field with choices of words becomes a choice (its first one first); a field of numbers is a number field (below).
    The references are the type's input slots, in the type's order; kind: what its outputs are ('data' when it makes no file: its numbers).
    THE NUMBERS (the lips gaps closed, 2026-11-06): a field whose rule is a short list of numbers ('list_numbers': face-swap's target_box) or
    of whole numbers ('list_ints': lips' slots) is on the grammar as a number field, its rule copied from TYPES as exxact.check_fields reads it
    (the range, the most, optional); a field of any other rule is not on the grammar. A type takes no words (prompt: False): TYPES has no
    prompt. Each reference slot's kinds and most bytes are the type's own input slot's (reference_rules), jpeg named jpg as kind_of names it."""
    out = {}
    for name, t in exxact.TYPES.items():
        made = {k for o in t['outputs'].values() for k in o['kinds']}
        choices = {f: tuple(r['choices']) for f, r in t['fields'].items()
                   if 'choices' in r and r['choices'] and all(isinstance(v, str) for v in r['choices'])}
        numbers = {f: {k: (tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in r.items() if k in NUMBER_KEYS}
                   for f, r in t['fields'].items() if f not in choices and sum(k in r for k in NUMBER_RULES) == 1}
        slots = tuple(t['inputs'])
        out[f'exxact/{name}'] = {
            'provider': 'exxact', 'path': name, 'kind': 'video' if 'mp4' in made else 'image' if made else 'data', 'name': f'Exxact {name}',
            'prompt': False, 'choices': choices, 'first': {f: v[0] for f, v in choices.items()}, 'numbers': numbers,
            'reference': 'inputs' if slots else '', 'references': slots, 'most_references': len(slots),
            'reference_rules': tuple((tuple(dict.fromkeys(_KIND_NAMES.get(k, k) for k in t['inputs'][s]['kinds'])), min(t['inputs'][s]['most'], MOST_ASK_REFERENCES))
                                     for s in slots),   # each slot within what one ask may hold, whatever the box takes
            'most_bytes': max([o['most'] for o in t['outputs'].values()] or [MOST_SAID]), 'most_seconds': t['most_seconds'],
        }
    return out


REFERENCE_KINDS = ('png', 'jpg', 'webp')                 # a Replicate model's reference is a picture, read from its first bytes
MOST_REFERENCE = 10 * 1024 * 1024                        # bytes of one reference picture (a Replicate model's)
MOST_ASK_REFERENCES = 100 * 1000 * 1000                  # bytes of ALL of one ask's references together (frost-05 2026-11-06: a quarter of the RUN's
                                                         # 1 GiB at most; a file read as base64 in JSON, then decoded, holds about 2.4 times its size)
for _spec in MODELS.values():   # Replicate's models: every reference a picture within MOST_REFERENCE, no number field (as before)
    _spec.setdefault('numbers', {})
    _spec.setdefault('reference_rules', ((REFERENCE_KINDS, MOST_REFERENCE),) * _spec['most_references'])
MODELS.update(_exxact_models())
KINDS = {'image': ('png', 'jpg', 'webp'), 'video': ('mp4',)}
MOST_PROMPT = 4000
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 _-]{0,79}$')   # the file's plain name, without its ending (the hand adds the kind's own)
_ID = re.compile(r'^[A-Za-z0-9]{1,64}$')                  # a provider's request id, before it is put in an address
EVERY_SECONDS = 3
DAM_KEY = re.compile(r'DA-M_[0-9A-F]{12}_[0-9A-F]{4}')   # a member's file in DA-M, by DA-M's own key (so files.KEY): the only way a reference is named


def declared(manifest):
    """The models the manifest declares ("makes": ["nano-banana-2"]), each on the list; an ill-formed declaration counts for nothing."""
    asked = manifest.get('makes') if isinstance(manifest, dict) else None
    if not (isinstance(asked, list) and asked and all(isinstance(m, str) and m in MODELS for m in asked)):
        return ()
    return tuple(dict.fromkeys(asked))


def check(makes, allowed):
    """-> (asks as the hand takes them, '') or ([], why): ONE ask in an answer, a declared model, a plain name (the made file's name,
    every model), each choice one of the model's own, each number field a short list of numbers within its range, and words to make
    it from when the model takes words (spec 'prompt': Replicate's models do; an Exxact type does not, and an ask for one may carry
    words or not: checked the same when carried, and never sent). A number field the model needs and the ask leaves out refuses it;
    an optional one left out is left out. Anything else refuses the answer; nothing goes out. A refusal never carries the member's value."""
    if not (isinstance(makes, list) and len(makes) == 1 and isinstance(makes[0], dict)):
        return [], 'the answer\'s makes is not a list of one ask'
    ask = makes[0]
    model = ask.get('model')
    if not (isinstance(model, str) and model in allowed):
        return [], 'the ask names a model the agent does not declare'
    spec = MODELS[model]
    numbers = spec.get('numbers') or {}
    if set(ask) - {'model', 'prompt', 'name', *spec['choices'], *numbers, *(('reference',) if spec.get('reference') else ())}:
        return [], f'the ask holds more than {spec["name"]} takes'
    prompt = ask.get('prompt')
    if (spec.get('prompt') or 'prompt' in ask) and not (isinstance(prompt, str) and prompt.strip() and len(prompt) <= MOST_PROMPT):
        return [], f'the ask carries no words, or more than {MOST_PROMPT} characters'
    name = ask.get('name')
    if not (isinstance(name, str) and NAME.fullmatch(name)):
        return [], 'the ask names no plain file name'
    out = {'model': model, 'name': name}
    if 'prompt' in ask:
        out['prompt'] = prompt.strip()
    for choice, values in spec['choices'].items():
        value = ask.get(choice, spec['first'][choice])
        if not (isinstance(value, str) and value in values):
            return [], f'the ask\'s {choice} is not one of {", ".join(values)}'
        out[choice] = value
    for field, rule in numbers.items():
        if field not in ask:
            if rule.get('optional'):
                continue
            return [], f'the ask names no {field}'
        value, whole = ask[field], 'list_ints' in rule
        lo, hi = rule['list_ints'] if whole else rule['list_numbers']
        if not (isinstance(value, list) and 0 < len(value) <= rule['most']
                and all(isinstance(x, int if whole else (int, float)) and not isinstance(x, bool) and lo <= x <= hi for x in value)):
            return [], f'the ask\'s {field} is not a list of at most {rule["most"]} {"whole numbers" if whole else "numbers"} from {lo} to {hi}'
        out[field] = list(value)
    if 'reference' in ask:   # optional: a DA-M key, or a list of them up to the model's most, and nothing else (never an address: law 1); the harness reads each file for this member
        refs = [ask['reference']] if isinstance(ask['reference'], str) else ask['reference']
        most = spec.get('most_references', 1)
        if not (isinstance(refs, list) and refs and all(isinstance(r, str) and DAM_KEY.fullmatch(r) for r in refs)):
            return [], 'the ask\'s reference is not a DA-M key'
        if len(refs) > most or len(set(refs)) != len(refs):
            return [], f'the ask names more than {most} reference{"" if most == 1 else "s"} {spec["name"]} takes, or one twice'
        out['reference'] = list(refs)
    return [out], ''


def goes_out(ask, reference=()):
    """What leaves for the provider, field by field (law 2): the words and the model's own choices, and the reference pictures'
    addresses at the provider when the ask names them (reference: the addresses the provider's own file door gave, in the ask's
    order; one address alone is taken as a list of one), nothing else."""
    if ask['model'] == 'nano-banana-2':
        out = {'prompt': ask['prompt'], 'aspect_ratio': ask['aspect'], 'resolution': ask.get('size', '1K'), 'output_format': 'png'}
    elif ask['model'] == 'flux-krea':
        out = {'prompt': ask['prompt'], 'aspect_ratio': ask['aspect'], 'num_outputs': 1, 'megapixels': '1', 'output_format': 'png'}
    elif ask['model'] == 'kling-2.5':
        out = {'prompt': ask['prompt'], 'duration': int(ask['seconds']), 'aspect_ratio': ask['aspect']}
    elif ask['model'] == 'seedance-2.5':
        out = {'prompt': ask['prompt'], 'duration': int(ask['seconds']), 'resolution': ask['size'], 'aspect_ratio': ask['aspect'],
               'generate_audio': False}   # never a sound track nobody asked for
    else:
        raise KeyError(ask['model'])
    refs = [reference] if isinstance(reference, str) else list(reference or ())
    refs = [r for r in refs if r]
    if refs:
        spec = MODELS[ask['model']]
        out[spec['reference']] = refs[0] if spec.get('reference_one') else refs   # a model whose field takes one address gets it plain
    return out


def reference_kind(data, kinds):
    """What a reference IS, from its first bytes (never a name or a header), when it is one of kinds (its slot's): kind_of's, and wav
    (RIFF....WAVE) only when the slot takes wav; '' otherwise."""
    kind = kind_of(data)
    if not kind and 'wav' in kinds and data[:4] == b'RIFF' and data[8:12] == b'WAVE':
        kind = 'wav'
    return kind if kind in kinds else ''


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
            return '', 'reference not a picture'
        if len(picture) > MOST_REFERENCE:
            return '', 'reference too large'
        mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'webp': 'image/webp'}[kind]
        edge = 'larryd' + hashlib.sha256(picture).hexdigest()[:24]
        body = (f'--{edge}\r\nContent-Disposition: form-data; name="content"; filename="reference.{kind}"\r\nContent-Type: {mime}\r\n\r\n').encode('ascii') + picture + f'\r\n--{edge}--\r\n'.encode('ascii')
        status, raw = self._call('POST', f"{place['api']}/files", key, raw=(body, f'multipart/form-data; boundary={edge}'), seconds=120)
        if status not in (200, 201):
            return '', self._refusal(status, name)
        urls = self._json(raw).get('urls')
        address = urls.get('get') if isinstance(urls, dict) else None
        if not (isinstance(address, str) and address.startswith(place['api'] + '/files/') and len(address) < 400 and '..' not in address):
            return '', f'{name} kept no reference'
        return address, ''

    def submit(self, ask, key, reference=()):
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
        """The whole errand: -> ({'name', 'kind', 'data'}, '') or (None, why). picture: the references' bytes when the ask names
        them (the harness read them from the member's DA-M), one per reference in the ask's order (bytes alone: a list of one); an
        ask whose references were not all read makes nothing."""
        spec = MODELS[ask['model']]
        name = PROVIDERS[spec['provider']]['name']
        pictures = [picture] if isinstance(picture, (bytes, bytearray)) else list(picture or ())
        pictures = [p for p in pictures if p]
        wanted = ask.get('reference') or []
        wanted = [wanted] if isinstance(wanted, str) else wanted
        reference = []
        if wanted:
            if len(pictures) != len(wanted):
                return None, 'reference not read'
            for one in pictures:
                address, why = self.lend(ask, one, key)
                if why:
                    return None, why
                reference.append(address)
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
