"""THE SIGNED CALL, both directions: the platform's office scheme, with HANZO's own secret. The text signed is
route + ' ' + at + ' ' + the data as compact sorted JSON; HMAC-SHA256, hex. Headers: X-Office (the signature) and
X-Office-At (the moment it signed, ISO UTC). A call is good only inside the window, before or after now."""
import datetime
import hashlib
import hmac
import json


def sign(secret, route, data, at):
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
    text = route + ' ' + at + ' ' + nonce + ' ' + json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hmac.new(secret.encode('utf-8'), text.encode('utf-8'), hashlib.sha256).hexdigest()


def good_hardened(keys, key_id, route, data, at, nonce, signature, now, window_seconds, fresh):
    """keys: {key id: secret} (every enabled version of every caller's key). fresh(nonce): True the first time only."""
    secret = (keys or {}).get(key_id or '')
    if not (secret and signature and at and nonce) or len(nonce) < 16:
        return False
    try:
        moment = datetime.datetime.fromisoformat(at)
        if abs(now - moment) > datetime.timedelta(seconds=window_seconds):
            return False
    except (TypeError, ValueError):
        return False
    if not hmac.compare_digest(sign_hardened(secret, route, data, at, nonce), signature):
        return False
    return bool(fresh(nonce))
