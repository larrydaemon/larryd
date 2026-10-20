"""THE GATE: one set of rules for every agent, used by both lanes. A card is SHOWN only when it can really run (LIVE,
a screen, a whole mTok rate, in the locker and verified); a member may HIRE it when entitled; it may RUN only when
also hired and switched on. Each NO carries its plain reason."""
import re


def rate(card):
    """The agent's own rate: whole mTok per run (empty = 0 = free); None when the price is not a whole rate."""
    price = str(card.get('price') or '').strip()
    if price == '':
        return 0
    return int(price) if re.fullmatch(r'\d+', price) else None


def shown(card, verified):
    if card.get('status') != 'LIVE':
        return False, 'the card is not LIVE'
    if not card.get('screen'):
        return False, 'the card names no screen'
    if rate(card) is None:
        return False, 'the price is not a whole mTok rate'
    return verified


def entitled(card, groups):
    """Free agents are open to all; a paid agent needs its group's subscription (the group = its screen's product)."""
    if rate(card) == 0 or card.get('product_slug') in groups:
        return True, ''
    return False, f"needs the {card.get('product')} subscription"


def may_run(card, verified, hired_on, groups):
    ok, why = shown(card, verified)
    if not ok:
        return ok, why
    if not hired_on:
        return False, 'not hired, or switched off'
    return entitled(card, groups)
