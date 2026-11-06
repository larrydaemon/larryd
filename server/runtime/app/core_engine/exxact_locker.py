"""EXXACT_LOOT'S LOCKER: pf Loot's construction (~/virtual_sanity/pf_loot/_office/away.py), Exxact_Loot's own copy and own label, so a
locker of one Loot is never a locker of the other (the owner: "not mixed").

    sign = Ed25519 over version | job | kind | sender | ephemeral public key | sha256(ciphertext)
    seal = X25519 (an ephemeral key to the receiver's key) -> HKDF-SHA256 (info: exxact-loot-locker-v1) -> Fernet

A lane that is read or changed can neither read nor forge a locker. Private keys never travel: the key ceremony exchanges the publics once,
by hand (keys(), trust()). Stdlib and `cryptography` only; the same file runs on the asker's side and on the box side."""
import base64
import datetime
import hashlib
import os
import re
import secrets

LOCKER_VERSION = 1
HKDF_INFO = b'exxact-loot-locker-v1'
KEY_FILES = ('sign.key', 'sign.pub', 'seal.key', 'seal.pub')
PEER_FILES = ('peer_sign.pub', 'peer_seal.pub')
NAME = re.compile(r'^JOB-[0-9A-F]{12}-[0-9A-F]{4}$')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def _b64(b):
    return base64.b64encode(b).decode()


def _unb64(s):
    return base64.b64decode(str(s).encode(), validate=True)


def _write(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as fh:
        fh.write(text)
    os.chmod(path, 0o600)


def _read(folder, name):
    with open(os.path.join(folder, name)) as fh:
        return fh.read().strip()


def keys(folder):
    """THE KEY CEREMONY, one side: make this side's signing and sealing keys when missing (never replaced) -> its two publics"""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
    os.makedirs(folder, mode=0o700, exist_ok=True)
    if not all(os.path.isfile(os.path.join(folder, n)) for n in KEY_FILES):
        raw = dict(encoding=Encoding.Raw, format=PrivateFormat.Raw, encryption_algorithm=NoEncryption())
        pub = dict(encoding=Encoding.Raw, format=PublicFormat.Raw)
        sign, seal_ = Ed25519PrivateKey.generate(), X25519PrivateKey.generate()
        for name, data in (('sign.key', sign.private_bytes(**raw)), ('sign.pub', sign.public_key().public_bytes(**pub)),
                           ('seal.key', seal_.private_bytes(**raw)), ('seal.pub', seal_.public_key().public_bytes(**pub))):
            _write(os.path.join(folder, name), _b64(data))
    return {'sign': _read(folder, 'sign.pub'), 'seal': _read(folder, 'seal.pub')}


def trust(folder, peer):
    """THE KEY CEREMONY, the other half: this side trusts the other side's two publics ({'sign', 'seal'})"""
    os.makedirs(folder, mode=0o700, exist_ok=True)
    for name, key in (('peer_sign.pub', peer['sign']), ('peer_seal.pub', peer['seal'])):
        if len(_unb64(key)) != 32:
            raise ValueError(f'{name}: not a 32-byte public key')
        _write(os.path.join(folder, name), key)


def ready(folder):
    """-> '' when this side holds its keys and trusts a peer, else what is missing"""
    missing = [n for n in KEY_FILES + PEER_FILES if not os.path.isfile(os.path.join(folder, n))]
    return '' if not missing else 'the key ceremony is not done: missing ' + ', '.join(missing)


def _body(job, kind, sender, eph_pub, ct_sha256):
    return f'{LOCKER_VERSION}|{job}|{kind}|{sender}|{eph_pub}|{ct_sha256}'.encode()


def _fernet(shared):
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    return Fernet(base64.urlsafe_b64encode(HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=HKDF_INFO).derive(shared)))


def seal(payload, job, kind, sender, folder):
    """bytes -> a locker: signed by this side (sign.key), sealed to the peer it trusts (peer_seal.pub)"""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    eph = X25519PrivateKey.generate()
    eph_pub = _b64(eph.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))
    ct = _fernet(eph.exchange(X25519PublicKey.from_public_bytes(_unb64(_read(folder, 'peer_seal.pub'))))).encrypt(payload)
    ct_hash = hashlib.sha256(ct).hexdigest()
    sig = Ed25519PrivateKey.from_private_bytes(_unb64(_read(folder, 'sign.key'))).sign(_body(job, kind, sender, eph_pub, ct_hash))
    return {'v': LOCKER_VERSION, 'job': job, 'kind': kind, 'sender': sender, 'eph_pub': eph_pub, 'ct': ct.decode(),
            'ct_sha256': ct_hash, 'sig': _b64(sig), 'created': now()}


def unseal(locker, folder, kind=None):
    """a locker -> its bytes: the peer's signature checked FIRST, then opened with this side's seal.key; ValueError on anything off"""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    if not isinstance(locker, dict) or locker.get('v') != LOCKER_VERSION:
        raise ValueError('not a locker of this version')
    if kind and locker.get('kind') != kind:
        raise ValueError('a locker of another kind')
    if not NAME.match(str(locker.get('job') or '')):
        raise ValueError('the locker names no job')
    ct = str(locker.get('ct') or '').encode()
    ct_hash = hashlib.sha256(ct).hexdigest()
    if ct_hash != locker.get('ct_sha256'):
        raise ValueError('the locker was changed')
    try:
        Ed25519PublicKey.from_public_bytes(_unb64(_read(folder, 'peer_sign.pub'))).verify(
            _unb64(locker.get('sig') or ''), _body(locker['job'], locker['kind'], locker.get('sender'), locker.get('eph_pub'), ct_hash))
    except (InvalidSignature, ValueError) as no:
        raise ValueError('the signature is not the trusted peer\'s') from no
    me = X25519PrivateKey.from_private_bytes(_unb64(_read(folder, 'seal.key')))
    try:
        return _fernet(me.exchange(X25519PublicKey.from_public_bytes(_unb64(locker['eph_pub'])))).decrypt(ct)
    except Exception as no:   # noqa: BLE001  never opened
        raise ValueError('the locker is not sealed to this side') from no


def job_key(payload):
    """a job's own name, by its content and a random tail (two equal asks are two jobs)"""
    return f"JOB-{hashlib.sha256(payload).hexdigest()[:12].upper()}-{secrets.token_hex(2).upper()}"
