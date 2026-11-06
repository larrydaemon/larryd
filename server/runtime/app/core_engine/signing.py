"""THE SIGNED CALL, both directions: the platform's office scheme, with the runtime's own secret. The text signed is
route + ' ' + at + ' ' + the data as compact sorted JSON; HMAC-SHA256, hex. Headers: X-Office (the signature) and
X-Office-At (the moment it signed, ISO UTC). A call is good only inside the window, before or after now."""
import datetime
import hashlib
import hmac
import json
import re


def sign(secret, route, data, at):
    if not secret:
        raise ValueError('no call is signed with an empty key')   # fail closed: never an empty-secret signature
    text = route + ' ' + at + ' ' + json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hmac.new(secret.encode('utf-8'), text.encode('utf-8'), hashlib.sha256).hexdigest()


def good(secret, route, data, at, signature, now, window_seconds):
    if not (secret and signature and at):
        return False
    try:
        moment = datetime.datetime.fromisoformat(at)
        if abs(now - moment) > datetime.timedelta(seconds=window_seconds):
            return False
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(sign(secret, route, data, at), signature)


# THE HARDENED CALL (the LARRYD runtime design, 2026-10-06): a key per caller (X-Office-Key names it) and a nonce
# (X-Office-Nonce) signed with the rest, so a captured call cannot be sent again. The text signed is then
# route + ' ' + at + ' ' + nonce + ' ' + the data as compact sorted JSON. A nonce is accepted once: the caller of
# good_hardened() passes `fresh`, which records the nonce and answers False when it was seen before.
def sign_hardened(secret, route, data, at, nonce):
    if not secret:
        raise ValueError('no call is signed with an empty key')
    text = route + ' ' + at + ' ' + nonce + ' ' + json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hmac.new(secret.encode('utf-8'), text.encode('utf-8'), hashlib.sha256).hexdigest()


KEY_ID = re.compile(r'[a-z0-9-]{1,32}')
NONCE = re.compile(r'[0-9a-f]{32}')
SIGNATURE = re.compile(r'[0-9a-f]{64}')
AT = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:\+00:00|Z)')


def well_formed(key_id, at, nonce, signature, known):
    """Every header of the hardened call, checked before anything is read or stored (the security review, 2026-10-06):
    a key id from the known set only (never a path or a lookup string), the timestamp in the ISO UTC form, the nonce
    32 hex characters, the signature 64 hex characters."""
    return (isinstance(key_id, str) and KEY_ID.fullmatch(key_id) is not None and key_id in known
            and isinstance(at, str) and AT.fullmatch(at) is not None
            and isinstance(nonce, str) and NONCE.fullmatch(nonce) is not None
            and isinstance(signature, str) and SIGNATURE.fullmatch(signature) is not None)


def good_hardened(keys, key_id, route, data, at, nonce, signature, now, window_seconds, fresh):
    """keys: {key id: [secrets]} (every enabled version of every caller's key; a single secret string is read as one
    version). fresh(nonce): True the first time only, asked only after the signature is good, so a bad call never uses
    up a nonce."""
    keys = keys or {}
    if not well_formed(key_id, at, nonce, signature, keys):
        return False
    versions = keys[key_id]
    versions = [versions] if isinstance(versions, str) else [v for v in versions if v]
    if not versions:
        return False
    try:
        moment = datetime.datetime.fromisoformat(at)
        if abs(now - moment) > datetime.timedelta(seconds=window_seconds):
            return False
    except (TypeError, ValueError):
        return False
    good = False
    for secret in versions:   # every version is compared (constant time each), whichever matches
        good = hmac.compare_digest(sign_hardened(secret, route, data, at, nonce), signature) or good
    if not good:
        return False
    return bool(fresh(nonce))
