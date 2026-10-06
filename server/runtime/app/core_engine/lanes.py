"""THE LANES' PURE PART: from the platform's answers to what an agent is handed. A card goes in only when the gate
shows it; each carries the member's state (hired = a shell holding it, switched on) and whether they may hire it."""
from . import gate


def hired_on(hired, agent_key):
    return any(h.get('agent_key') == agent_key and h.get('on') is True for h in hired)


def groups(balance):
    return sorted({s['agent_group'] for s in (balance or {}).get('subscriptions') or [] if s.get('agent_group')})


def assemble(cards, hired, subscribed, verify):
    out = []
    for c in cards:
        if not gate.shown(c, verify(c['key']))[0]:
            continue
        may, why = gate.entitled(c, subscribed)
        out.append({**c, 'hired': hired_on(hired, c['key']), 'hireable': may, 'reason': why, 'needs': '' if may else c['product']})
    return out
