"""THE LARRY DATA FABRIC, ONE SNAPSHOT (the owner 2026-11-04: "it should only use a snapshot from the database so the data
is very fast and no connections / just 1 updated snapshot per day / everything else we need to delete"). Nothing is
brought in: no RUN, no files, no records, no custom fields. On a CALL of an agent whose approved manifest declares
"fabric": {"snapshot": true}, it is handed given["fabric"] = {state: FROST's once-a-day snapshot of the APIs and the
databases, viewer: who looks}, from ONE read of FROST's own store; nothing else is asked.

custom(): CUSTOM DATA ONLY ON CUSTOM AGENTS, an agent PRIVATE to this very account."""
STATE_DOOR = '/fabric/state'
LISTS = ('apis', 'databases')   # the snapshot's two lists, Positive Feedback's own look, shown to every account


def declared(manifest):
    """True when the approved manifest declares the Data Fabric's snapshot ("fabric": {"snapshot": true}); anything else
    counts for nothing (fail closed)."""
    asked = manifest.get('fabric') if isinstance(manifest, dict) else None
    return isinstance(asked, dict) and asked.get('snapshot') is True


def custom(card, manifest, account):
    """CUSTOM DATA ONLY ON CUSTOM AGENTS (the owner, 2026-10-25: "custom would be meaning we custom build it for that
    customer"): an agent that is PRIVATE to this very account."""
    card = card if isinstance(card, dict) else {}
    return str(card.get('authorization') or '').strip().upper() == 'PRIVATE' and bool(account) and card.get('account_key') == account


def viewer(ask, account, scope, member):
    """The snapshot and who looks -> (state, {member_type}): ONE read of FROST's own store (its door never looks again on
    the way); {member_type: ''} when FROST does not say."""
    body = ask('fs', 'GET', STATE_DOOR, {'account': account, 'scope': scope, 'member': member})
    who = body.get('viewer') if isinstance(body.get('viewer'), dict) else {}
    return {t: [r for r in (body.get(t) or []) if isinstance(r, dict)] for t in LISTS}, {'member_type': str(who.get('member_type') or '')}
