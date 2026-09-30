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
