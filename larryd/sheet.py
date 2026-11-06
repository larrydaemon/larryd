"""THE CARD'S FIXED LISTS (kit/catalog.json: class, type, residency, authorization, product, screens), read by the doctor and said in the
guide and every CLAUDE.md. The platform draws the card from these values; an agent ships no look (the owner 2026-11-03: "larryd should just
have the agent code and data to populate the database and our endpoint dynamically generates the card from dynamic data")."""
import json
from importlib import resources


def catalog():
    return json.loads(resources.files('larryd').joinpath('kit', 'catalog.json').read_text())


def card_table(cat=None):
    """THE CARD'S ALLOWED VALUES as Markdown (the platform's own fixed lists), one text for the guide and every CLAUDE.md."""
    import textwrap
    card = (cat or catalog())['card']
    by = {}
    for screen, where in card['screens'].items():
        by.setdefault((where['product'], where['module']), []).append(screen)
    lines = ['| Field | Allowed values |', '|---|---|',
             '| class | ' + '; '.join(f'{k}: {card["class_means"][k]}' for k in card['class']) + ' |',
             '| type | ' + ', '.join(card['type']) + ' |',
             '| residency | which marketplaces it is offered on: ' + '; '.join(f'{k}: {v}' for k, v in card['residency_means'].items())
             + ' (every LARRYD agent runs in LARRYD) |',
             '| authorization | ' + ', '.join(card['authorization']) + ' (who may hire it: your starting setting; the platform\'s authorize '
             'panel can change it at any time after, and a PRIVATE agent\'s owning account is entered there) |',
             '| product | ' + ', '.join(card['products']) + ' |',
             '| price | a whole number of mTok per run: 3 or "3"; "0" is free |', '',
             '| Screen (<species>/<page>, at app/<species>/<page>) | Product | Module |', '|---|---|---|']
    lines += [f'| {", ".join(screens)} | {product} | {module} |' for (product, module), screens in by.items()]
    note = ('The platform draws the card from these values (an agent ships no look). A value off these lists fails with the ones to use.')
    return '\n'.join(lines) + '\n\n' + textwrap.fill(note, 118)
