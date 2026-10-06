"""AN AGENT'S LOOK, AT RENDER: the record of names from the agent's own held, approved manifest ("look"), cleaned
against the one fixed menu (schemas/look.json, the developer tool's kit/catalog.json word for word): anything not a
name on the menu is dropped. The card template puts what is left on the card element as custom properties that point
at the LIVE theme variables (never a resolved colour or length), so a card follows the brand and light or dark."""
import json
import pathlib

MENU = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'schemas' / 'look.json').read_text())
FIELDS = ('accent', 'radius', 'space', 'effect')


def clean(look):
    """-> the record with only menu names: {accent, radius, space, effect, text: {part: role}}; {} for anything else."""
    if not isinstance(look, dict):
        return {}
    out = {k: look[k] for k in FIELDS if isinstance(look.get(k), str) and look[k] in MENU[k]}
    text = look.get('text')
    if isinstance(text, dict):
        kept = {p: r for p, r in text.items() if isinstance(p, str) and isinstance(r, str) and p in MENU['parts'] and r in MENU['roles']}
        if kept:
            out['text'] = kept
    return out
