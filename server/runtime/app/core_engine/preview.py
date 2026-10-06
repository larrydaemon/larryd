"""THE DEVELOPER'S PLATFORM. On a developer's computer LARRYD's runtime has no platform to ask, so this answers in the
platform's place, from the instance alone and in the platform's own shapes: the cards from the locker's manifests (a
developer's agent carries its card facts; the number and the art are the platform's to give at approval), the one
member's hires from one small file, every product subscribed, every held agent approved. The harness, the gate, the
lanes and the sandbox run exactly as on the server; only the answers come from here. Never used when a platform
address is declared, and never on a server: only the daemon a developer starts asks for it."""
import json
import pathlib
import re
import sqlite3

from . import gate, locker

ACCOUNT = SCOPE = MEMBER = 'developer'       # the one member of a developer's runtime
BOARD = 'agnt/home'                          # the marketplace's own screen: a board's first visit places it there
MARKETPLACE_KEY = 'MAGT_000000000000_0001'    # the marketplace's card key on a developer's runtime
MARKETPLACE_CARD = {'number': '0', 'class': 'SYSTEM AGENT', 'screen': BOARD, 'product': 'LARRYD', 'module': 'AGENT',
                    'pitch': 'Every agent for hire, one toggle each.', 'developer': 'LARRYD', 'price': '0',
                    'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'sends_to': '', 'data_sent': ''}
CARD_KEYS = ('class', 'pitch', 'price', 'type', 'residency', 'screen', 'product', 'module', 'developer', 'sends_to', 'data_sent')


def slug(product):
    return re.sub(r'[^a-z0-9]', '', str(product or '').lower())


def hold_marketplace(db, agents):
    """The marketplace in the locker of a developer's runtime, as the server holds it: added on first start, refreshed
    when a release changed its files (the daemon lays the folder down fresh on every start). -> its key."""
    ok, _why = locker.verify(db, agents, MARKETPLACE_KEY)
    if ok:
        return MARKETPLACE_KEY
    con = sqlite3.connect(db)
    try:
        con.execute("DELETE FROM runtime_locker WHERE folder = 'marketplace' OR agent_key = ?", (MARKETPLACE_KEY,))
        con.commit()
    finally:
        con.close()
    locker.add(db, agents, MARKETPLACE_KEY, 'marketplace')
    return MARKETPLACE_KEY


def hidden(cards, verify):
    """[(name, why)]: the cards the gate does not show, each with its plain reason (what a developer must fix)."""
    out = []
    for c in cards:
        shown, why = gate.shown(c, verify(c['key']))
        if not shown:
            out.append((c.get('name') or c['key'], why))
    return out


class Local:
    """Answers the platform's doors from the instance: the same (status, body) a signed call would bring back."""

    def __init__(self, db, agents, instance):
        self.db, self.agents = db, pathlib.Path(agents)
        self.place = pathlib.Path(instance) / 'preview'
        self.place.mkdir(parents=True, exist_ok=True)
        self.hired_file = self.place / 'hired.json'

    # ------------------------------------------------------------------ what the platform would know
    def _rows(self):
        con = sqlite3.connect(self.db)
        con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute('SELECT * FROM runtime_locker ORDER BY registered_at, agent_key')]
        finally:
            con.close()

    def cards(self):
        """Every held agent as the platform's card: the marketplace as the system card, a developer's agent from the
        card facts in its manifest (missing facts stay empty: the gate then says what is missing)."""
        out, n = [], 0
        for row in self._rows():
            try:
                manifest = locker.manifest(self.agents, row['folder'])
            except (OSError, ValueError):
                continue
            if row['folder'] == 'marketplace':
                facts = dict(MARKETPLACE_CARD)
            else:
                n += 1
                given = manifest.get('card') if isinstance(manifest.get('card'), dict) else {}
                facts = {k: str(given.get(k) or '') for k in CARD_KEYS}
                facts['number'] = str(n)
            out.append({'key': row['agent_key'], 'name': manifest.get('name') or row['name'], 'status': 'LIVE', 'image_dam_key': '',
                        **facts, 'product_slug': slug(facts['product'])})
        return out

    def _hired(self):
        try:
            return [k for k in json.loads(self.hired_file.read_text()) if isinstance(k, str)]
        except (OSError, ValueError):
            return []

    def _save(self, keys):
        self.hired_file.write_text(json.dumps(sorted(set(keys))) + '\n')

    # ------------------------------------------------------------------ the doors
    def get(self, office, route, data=None):
        return self._answer('GET', office, route, data or {})

    def post(self, office, route, data):
        return self._answer('POST', office, route, data or {})

    def _answer(self, method, office, route, data):
        cards = {c['key']: c for c in self.cards()}
        hired = self._hired()
        if (method, office, route) == ('GET', 'wid', '/agnt/cards'):
            return 200, {'cards': list(cards.values())}
        if (method, office, route) == ('GET', 'wid', '/agnt/hired'):
            return 200, {'hired': [{'agent_key': k, 'board': cards[k]['screen'], 'shell_id': i, 'on': True, 'job_key': ''}
                                   for i, k in enumerate(hired, 1) if k in cards]}
        if (method, office, route) == ('POST', 'wid', '/agnt/hire'):
            key = str(data.get('agent_key') or '')
            if key not in cards:
                return 404, {'refused': 'no such agent'}
            already = key in hired
            self._save(hired + [key])
            return 200, {'shell_id': len(hired) + 1, 'job_key': '', 'board': cards[key]['screen'], 'already': already}
        if (method, office, route) == ('POST', 'wid', '/agnt/unhire'):
            key = str(data.get('agent_key') or '')
            self._save([k for k in hired if k != key])
            return 200, {'removed': int(key in hired)}
        if (method, office, route) == ('GET', 'wid', '/jobs/queued'):
            return 200, {'jobs': []}
        if (method, office, route) == ('GET', 'cc', '/mtok/balance'):
            groups = sorted({c['product_slug'] for c in cards.values() if c['product_slug']})
            return 200, {'account': ACCOUNT, 'balance': 0, 'subscriptions': [{'agent_group': g} for g in groups]}
        if (method, office, route) == ('GET', 'fs', '/agents/approved'):
            return 200, {'approved': [{'agent_key': r['agent_key'], 'code_sha256': r['code_sha256'], 'manifest_sha256': r['manifest_sha256']}
                                      for r in self._rows()]}
        if (method, office, route) == ('GET', 'fs', '/agents/review_state'):
            return 200, {'state': 'approved', 'note': ''}
        if (method, office, route) == ('POST', 'fs', '/agents/submit'):
            return 200, {'state': 'approved', 'agent_key': data.get('agent_key', '')}
        return 404, {'refused': f"the developer's runtime has no {office}{route}"}
