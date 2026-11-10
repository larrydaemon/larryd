"""A SCRATCH FROST for the tests (lane C, 2026-11-09): a key made here, never FROST's, whose public half is put in
LARRYD_FROST_PUBLIC_KEY for this test process, and decided() signing a decision exactly as FROST does (fs
verbs.authorization_hire: compact sorted JSON, Ed25519 over its UTF-8 bytes, hex). A hire or RUN a test means to go past the door
carries decided(); the runtime refuses everything else (core_engine/decision.py)."""
import datetime
import json
import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from _here import APP  # noqa: F401
from core_engine import decision

KEY = Ed25519PrivateKey.generate()
PUBLIC = KEY.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
os.environ[decision.ENV] = PUBLIC


def text_of(said):
    return json.dumps(said, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def decided(member='MCON_000000000002_0002', card_key='MAGT_00000000AA01_0001', key=KEY, at=None, **more):
    """The DECIDED fields wid forwards (frost_decision, frost_decision_sig) for this member, signed now (or at) by key (the scratch
    FROST's by default)."""
    text = text_of({'member': member, 'card_key': card_key, 'code_sha256': 'c' * 64, 'manifest_sha256': 'm' * 64,
                    'access': 'allow', 'at': now() if at is None else at, **more})
    return {'frost_decision': text, 'frost_decision_sig': key.sign(text.encode('utf-8')).hex()}


def decided_for(d):
    """d with FROST's decision for d's own member, as wid sends a call."""
    return {**d, **decided(member=d['member'])}
