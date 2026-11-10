"""FROST'S SIGNED DECISION, CHECKED BY THE RUNTIME (the Agents Security Plan, lane C, 2026-11-09). The owner's design: "One
approver: production's FROST, by sha256 of the code and the manifest. Same everything else: the same runtime code". wid
forwards FROST's own decision on every hire and RUN (DECIDED: card_key, code_sha256, manifest_sha256, frost_decision,
frost_decision_sig); FROST signed the decision's text, compact sorted JSON, with Ed25519 (fs verbs.authorization_hire:
ctx.signer.sign(text.encode('utf-8')) -> hex). The runtime verifies exactly those bytes with FROST's public half, so a hire
or RUN that FROST did not decide is refused here even when wid let it through: TWO GUARDS, NEVER ONE (the owner, 2026-10-04);
the approved list (harness.APPROVED_DOOR) stays the other one.
THE KEY: FROST's public half only, raw Ed25519 bytes as hex, in LARRYD_FROST_PUBLIC_KEY (on this Mac and in the cloud the same
key, the owner: "they both have the same key dont over complicate it"; its one written home is global_config
offices.fs.public_key). No key, or a key that is not one: every hire and RUN is refused (fail closed). The private half never
leaves FROST. Read at each check, so a rotated key is seen without a new release of the code.
NEVER REPLAYED (the coordinator's order, 2026-11-09): FROST's text names the member it decided for and the moment it signed
("member", "at"); the call must be for that same member, and the decision must be fresh. FROST's text carries no end of its own,
so the window is the runtime's: wid asks FROST at the send (offices.asked_now, never a kept answer), so a true decision is seconds
old when it arrives; a queued run is checked when the queue is read, never when its turn comes."""
import datetime
import json
import os

ENV = 'LARRYD_FROST_PUBLIC_KEY'
FIELDS = ('card_key', 'code_sha256', 'manifest_sha256')   # what the call carries beside the decision, each the decision's own word
NO_KEY = 'no FROST public key'
NO_DECISION = "no FROST decision: the call does not carry FROST's signed decision"
BAD_SIG = "FROST's decision is not signed by FROST"
NOT_THIS = "FROST's decision is not for this agent's exact hashes"
NOT_THIS_MEMBER = "FROST's decision is for another member"
STALE = "FROST's decision is out of its time"
WINDOW = 120   # seconds a decision is taken after FROST signed it
SKEW = 60      # seconds a decision may seem to be from the future (two clocks; the signed call's own window)


def public_key():
    """FROST's public key from the environment, or None (absent, not hex, not 32 bytes, not a key)."""
    raw = (os.environ.get(ENV) or '').strip()
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        return Ed25519PublicKey.from_public_bytes(bytes.fromhex(raw)) if raw else None
    except (ImportError, ValueError):
        return None


def _at(text):
    try:
        moment = datetime.datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None
    return moment if moment.tzinfo is not None else None


def why_not(d, now=None):
    """'' when d (a CALL's, hire's or RUN's signed body, or a queued run) carries a decision FROST signed, for the call's own member,
    inside its time, and for the exact card and hashes it carries beside it; else the refusal in fixed words. Fail closed on anything
    missing or malformed. now: the moment of the check (UTC; a test names it)."""
    key = public_key()
    if key is None:
        return NO_KEY
    text, sig = d.get('frost_decision'), d.get('frost_decision_sig')
    if not isinstance(text, str) or not text or not isinstance(sig, str) or not sig:
        return NO_DECISION
    try:
        from cryptography.exceptions import InvalidSignature
        key.verify(bytes.fromhex(sig), text.encode('utf-8'))   # the very bytes FROST signed: the text as wid forwarded it, untouched
    except (InvalidSignature, ValueError):
        return BAD_SIG
    try:
        said = json.loads(text)
    except ValueError:
        return BAD_SIG
    if not isinstance(said, dict):
        return BAD_SIG
    member = str(d.get('member') or '')
    if not member or str(said.get('member') or '') != member:   # a decision for one member never opens a call for another
        return NOT_THIS_MEMBER
    at = _at(said.get('at'))
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if at is None or not -SKEW <= (now - at).total_seconds() <= WINDOW:   # an old decision, sent again, is refused
        return STALE
    for f in FIELDS:   # what the call says FROST approved must be what FROST signed (a signed decision for another card never covers this one)
        if str(d.get(f) or '') and str(d.get(f)) != str(said.get(f) or ''):
            return NOT_THIS
    return ''
