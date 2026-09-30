"""THE SSO PROXY'S HAND-OFF, as LARRYD's submit door checks it: the proxy's own handoff.py, the same code below its first
lines (the proxy signs; this side only verifies, with the proxy's public key).
    v1.<payload>.<signature>     payload = base64url(compact sorted JSON), signature = Ed25519 over "v1.<payload>"
The payload: v, iss (the proxy's public name), aud (the app origin it is posted to), provider, sub, email,
email_verified, state and nonce (FROST's own, from its start), iat, exp (a minute), jti (one use).
verify() is the check FROST makes; this file is the one both sides hold."""
import base64
import json
import secrets

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

VERSION = 'v1'
FIELDS = ('v', 'iss', 'aud', 'provider', 'sub', 'email', 'email_verified', 'state', 'nonce', 'iat', 'exp', 'jti')
PROVIDERS = ('google', 'apple')


class Refused(Exception):
    """A hand-off that is not good; args[0] is the reason's code (never the hand-off itself), one of REASONS. The code
    is for the log; what a person reads is the caller's own words."""


REASONS = ('key', 'shape', 'version', 'signature', 'unreadable', 'fields', 'identity', 'issuer', 'audience', 'time')
KEY, SHAPE, VERSION_WRONG, SIGNATURE, UNREADABLE, FIELDS_WRONG, IDENTITY, ISSUER, AUDIENCE, TIME = REASONS


def _b64(data):
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def _unb64(text):
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


def new_key():
    """-> (private PEM, public PEM) for a fresh Ed25519 key."""
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return private, public


def public_pem(private_pem):
    key = serialization.load_pem_private_key(private_pem, password=None)
    return key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)


def sign(private_pem, iss, aud, provider, sub, email, email_verified, state, nonce, now, seconds=60):
    key = serialization.load_pem_private_key(private_pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise Refused(KEY)
    payload = {'v': 1, 'iss': iss, 'aud': aud, 'provider': provider, 'sub': sub, 'email': email or '',
               'email_verified': bool(email_verified), 'state': state, 'nonce': nonce,
               'iat': int(now), 'exp': int(now) + seconds, 'jti': secrets.token_urlsafe(18)}
    signed = f"{VERSION}.{_b64(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8'))}"
    return f'{signed}.{_b64(key.sign(signed.encode("ascii")))}'


def verify(public_pem_bytes, handoff, iss, aud, now, skew=5):
    """-> the payload of a good hand-off, else Refused: the signature (with this public key), the version, the fields,
    the issuer and audience given, and the time (not before iat, not after exp; a few seconds of clock skew). One use
    (the jti) and FROST's own state, nonce and browser are FROST's to check with what it remembers."""
    key = serialization.load_pem_public_key(public_pem_bytes)
    if not isinstance(key, Ed25519PublicKey):
        raise Refused(KEY)
    try:
        version, body, sig = (handoff or '').split('.')
    except ValueError:
        raise Refused(SHAPE)
    if version != VERSION:
        raise Refused(VERSION_WRONG)
    try:
        key.verify(_unb64(sig), f'{version}.{body}'.encode('ascii'))
    except (InvalidSignature, ValueError):
        raise Refused(SIGNATURE)
    try:
        payload = json.loads(_unb64(body))
    except ValueError:
        raise Refused(UNREADABLE)
    if not isinstance(payload, dict) or sorted(payload) != sorted(FIELDS) or payload['v'] != 1:
        raise Refused(FIELDS_WRONG)
    if payload['provider'] not in PROVIDERS or not isinstance(payload['sub'], str) or not payload['sub']:
        raise Refused(IDENTITY)
    if payload['iss'] != iss:
        raise Refused(ISSUER)
    if payload['aud'] != aud:
        raise Refused(AUDIENCE)
    if not (payload['iat'] - skew <= now <= payload['exp'] + skew):
        raise Refused(TIME)
    return payload
