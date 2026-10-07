"""THE LANES' PURE PART: from the platform's answers to what an agent is handed. A card goes in only when the gate
shows it; each carries the member's state (hired = a shell holding it, switched on) and whether they may hire it."""
from . import gate


def hired_on(hired, agent_key):
    return any(h.get('agent_key') == agent_key and h.get('on') is True for h in hired)


def groups(balance):
    return sorted({s['agent_group'] for s in (balance or {}).get('subscriptions') or [] if s.get('agent_group')})


def assemble(cards, hired, subscribed, verify, own=''):
    out = []
    for c in cards:
        if c['key'] == own:   # an agent is never handed its own card: the marketplace is the page, never a card inside itself (the owner, 2026-10-06)
            continue
        if not gate.shown(c, verify(c['key']))[0]:
            continue
        may, why = gate.entitled(c, subscribed)
        # OFFLINE IS FOR THE SUBSCRIPTION (the owner, 2026-10-07: "the offline is for the subscription to work ... this is offline until someone buys a
        # subscription to invoice maps"): a card the platform marks offline is offline only for an account WITHOUT its product's subscription; with it, online
        offline = c.get('offline') is True and c.get('product_slug') not in subscribed
        subscription = c.get('offline') is True and not offline   # it comes with the product's subscription, and this account has it: the card says Subscription where the price stands
        out.append({**c, 'offline': offline, 'subscription': subscription, 'hired': hired_on(hired, c['key']), 'hireable': True, 'reason': why, 'needs': '' if may else c['product']})   # every card can be hired: its toggle always (the owner, 2026-10-06); a RUN of a priced agent still needs its subscription (gate.may_run)
    return out
