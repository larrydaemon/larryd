"""THE GATE: one set of rules for every agent, used by both lanes. A card is SHOWN only when it can really run (APPROVED,
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
    if card.get('status') != 'APPROVED':
        return False, 'the card is not APPROVED'
    if not card.get('screen'):
        return False, 'the card names no screen'
    if rate(card) is None:
        return False, 'the price is not a whole mTok rate'
    return verified


PLAN_OF = {'invoicemaps': 'organize', 'agencymgmt': 'manage', 'paceshift': 'create'}   # each product's plan in mTok, the word under its name in the dock (the platform's engine.json products[].agent_group): Organize, Manage, Create; LARRYD has none


def group_of(card):
    """The plan that is this card's product's subscription: the card's own agent_group when the platform hands one, else its product's (PLAN_OF)."""
    return card.get('agent_group') or PLAN_OF.get(card.get('product_slug') or '') or ''


def subscribed(card, groups):
    """Does the account hold this card's product's subscription (its plan among the plans the account bought)?"""
    group = group_of(card)
    return bool(group) and group in groups


def entitled(card, groups):
    """Free agents are open to all; a paid agent needs its product's subscription (its plan: Organize, Manage or Create)."""
    if rate(card) == 0 or subscribed(card, groups):
        return True, ''
    return False, f"needs the {card.get('product')} subscription"


def may_run(card, verified, hired_on, groups):
    ok, why = shown(card, verified)
    if not ok:
        return ok, why
    if not hired_on:
        return False, 'not hired, or switched off'
    return entitled(card, groups)
