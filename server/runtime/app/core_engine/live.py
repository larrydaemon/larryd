"""THE LIVE PAGE'S PASS (the owner, 2026-10-08: "it runs outside the core with an agent"; "secure with our own frost identity").
An agent whose approved manifest declares "live" has a live page of its own, served by its own room program outside the
platform. The agent holds no secret and is handed none; LARRYD does: on a CALL the runtime signs a PASS for the member the
platform named and answers the PLATFORM, in its own field beside the agent's view, `room = "<the room program>/#<pass>"`; the
agent itself is told only `live = {"room": true}` (2026-10-08, the security review: an agent's markup carries no address and
no pass). The pass says who (account, member, first
name), for which agent, the member's company, email and website when FROST hands them, how the page is worn (theme, mode), when it ends (ten minutes) and a number that makes it good once.
It rides after the # of the link: never in a request line, never in a server's log. The room program checks it with the same
key. Settings, by the environment: LARRYD_LIVE_ADDRESS (https, a named host) and LARRYD_LIVE_KEY_FILE (the key's file).
With either missing the agent is told of no room and the platform is handed none: nothing is shown that does not work."""
import base64
import hashlib
import hmac
import json
import os
import pathlib
import re
import secrets
import time

from . import view

LIFE = 600   # seconds a pass is good for
SEATS = (1, 4)
THEME = re.compile(r'[A-Z0-9]{12}')
PLAIN = re.compile(r'[A-Za-z0-9_.:-]{1,80}')


def declared(manifest):
    """The manifest's "live" as LARRYD holds an agent to it: {"seats": 1 to 4}, or None."""
    live = manifest.get('live') if isinstance(manifest, dict) else None
    if isinstance(live, dict) and set(live) == {'seats'} and isinstance(live['seats'], int) and not isinstance(live['seats'], bool) \
            and SEATS[0] <= live['seats'] <= SEATS[1]:
        return live
    return None


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()


def sign(key, facts):
    body = _b64(json.dumps(facts, separators=(',', ':'), sort_keys=True).encode())
    return body + '.' + _b64(hmac.new(key, body.encode(), hashlib.sha256).digest())


def settings(environ=None):
    """-> (address, key) or (None, None): the live page's address exactly as a card's link out must be, and a key of 32 bytes or more."""
    environ = os.environ if environ is None else environ
    address, where = (environ.get('LARRYD_LIVE_ADDRESS') or '').rstrip('/'), environ.get('LARRYD_LIVE_KEY_FILE') or ''
    if not address or not where or not view.link_address(address) or '#' in address or '?' in address:
        return None, None
    try:
        key = pathlib.Path(where).read_text().strip().encode()
    except OSError:
        return None, None
    return (address, key) if len(key) >= 32 else (None, None)


def _plain(value, most):
    """A fact about the member as FROST handed it: plain words on one line, or nothing."""
    return ' '.join(value.split())[:most] if isinstance(value, str) and not any(ord(c) < 32 or c in '<>' for c in value) else ''


def link(account, member, agent_key, name='', page=None, product='', environ=None, now=None, who=None, scope='', via=''):
    """The room's address with a pass for this member, for the runtime's own answer field of an agent that declares "live" (never
    handed to the agent), or '' when the room is not set up or the platform's own words for the member are not plain keys."""
    address, key = settings(environ)
    if not key or not all(isinstance(x, str) and PLAIN.fullmatch(x) for x in (account, member, agent_key)):
        return ''
    page = page if isinstance(page, dict) else {}
    wears = page.get('wears') if isinstance(page.get('wears'), dict) else {}
    theme = wears.get(product) or wears.get('global') or ''
    who = who if isinstance(who, dict) else {}   # WHO THE MEMBER IS, as FROST's identity door handed it: only what it handed rides on the pass
    if scope and not PLAIN.fullmatch(str(scope)) or via and not PLAIN.fullmatch(str(via)):
        return ''
    facts = {'account': account, 'member': member, 'agent': agent_key, 'scope': str(scope or ''), 'via': str(via or ''),   # scope: the member's own on the platform; via: the slot that called, so the room program's asks go back to it
             'name': ' '.join(str(name or who.get('first_name') or '').split())[:40],
             'company': _plain(who.get('account_name'), 80), 'email': _plain(who.get('email'), 120), 'site': _plain(who.get('website'), 120),
             'theme': theme if isinstance(theme, str) and THEME.fullmatch(theme) else '', 'mode': 'light' if page.get('mode') == 'light' else 'dark',
             'owner': who.get('member_type') in ('owner', 'system_owner'),   # the account's owner, as FROST names its member types
             'case': 'mixed' if page.get('letter_case') == 'mixed' else 'upper',   # the member's own capitals setting, when the platform hands it with the page
             'ends': int(now if now is not None else time.time()) + LIFE, 'once': secrets.token_hex(12)}
    return f'{address}/#{sign(key, facts)}'


# ---------------------------------------------------------------- THE ROOM PROGRAM'S ASKS (the member's record, through LARRYD)
ASK_WINDOW = 60          # seconds an ask is good for
MOST_ASK = 64 * 1024     # bytes
DOES = {'list': 'read', 'add': 'add', 'edit': 'edit'}   # what a live page may ask of the member's records, and the manifest's verb for each


def mark(key, body):
    """The room program's mark on an ask: the keyed hash of the body's own bytes (the key the pass is signed with)."""
    return hmac.new(key, body, hashlib.sha256).hexdigest()


def read_ask(body, given_mark, environ=None, now=None):
    """-> (the ask, '') or (None, why): an ask of the member's records from an agent's own room program. It is the room
    program's only word to LARRYD: marked with the key LARRYD shares with it and nobody else, made within the minute, every
    name a plain key. The runtime then holds it to the agent's approved manifest and to the platform's own doors, as it holds a CALL."""
    _address, key = settings(environ)
    if not key:
        return None, 'no live page is set up'
    if not isinstance(body, bytes) or len(body) > MOST_ASK or not isinstance(given_mark, str) or not hmac.compare_digest(mark(key, body), given_mark):
        return None, 'not the room program'
    try:
        ask = json.loads(body)
    except ValueError:
        return None, 'not an ask'
    if not isinstance(ask, dict) or not isinstance(ask.get('at'), (int, float)) or isinstance(ask.get('at'), bool) \
            or abs((now if now is not None else time.time()) - ask['at']) > ASK_WINDOW:
        return None, 'a late ask'
    if not all(isinstance(ask.get(k), str) and PLAIN.fullmatch(ask[k]) for k in ('agent', 'account', 'member')) \
            or not all(isinstance(ask.get(k, ''), str) and (not ask.get(k) or PLAIN.fullmatch(ask[k])) for k in ('scope', 'via', 'key')):
        return None, 'not an ask'
    if ask.get('do') not in DOES or not isinstance(ask.get('species'), str) or not re.fullmatch(r'[a-z]{4}', ask['species']):
        return None, 'not an ask'
    values = ask.get('values', {})
    if not isinstance(values, dict):
        return None, 'not an ask'
    return {'agent': ask['agent'], 'account': ask['account'], 'scope': ask.get('scope', ''), 'member': ask['member'], 'via': ask.get('via', ''),
            'do': ask['do'], 'species': ask['species'], 'key': ask.get('key', ''), 'values': values}, ''
