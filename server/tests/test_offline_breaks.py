"""THE FOUR BREAKS frost-0d's offline end to end found (2026-10-06, OFFLINE_E2E.md), each proven here first, on the
laptop's runtime AND the Cloud Run path (the lockers bucket):
1. `place <key> <file> marketplace` holds the agent AS the marketplace (marketplace/<key>), as the bucket's role does;
2. the marketplace is found on the platform by the card key FROST minted (both keys linked), never the runtime's own;
3. one status, APPROVED: what FROST's approve writes is what the gate shows (LIVE is gone);
4. every run record names its caller: the account and the member keys, on the laptop's table as in Firestore."""
import pathlib
import shutil
import sqlite3
import tempfile
import unittest

from _here import APP  # noqa: F401
from core_engine import gate, harness, locker, records, store
from core_engine import lockers as bucket_lockers
from test_review_fixes import CloudApp, MARKET, marketplace_package
from web import app as host

CARD = 'MAGT_00000000CA01_0001'       # the card key FROST mints at submission
ACCOUNT, MEMBER = 'ACCT_000000000001_0001', 'MCON_000000000002_0002'


class Frost:
    """FROST as a receipt that mints the card's key at submission (what the live FROST answers)."""
    def post(self, office, route, data):
        return 200, {'id': 1, 'state': 'waiting', 'card_key': CARD}

    def get(self, office, route, data=None):
        return 200, {'approved': []}


def card(key=CARD, status='APPROVED'):
    return {'key': key, 'status': status, 'screen': 'larryd/agnt/home', 'price': '', 'product': 'LARRYD', 'product_slug': 'larryd',
            'name': 'PF AGENT MARKETPLACE', 'module': 'AGENT'}


class Platform(harness.Harness):
    """The platform's facts given in this process: its cards are keyed by the CARD key, as wid's /agnt/cards keys them."""
    cards = [card()]
    asked = []

    def facts(self, account, scope, member):
        return self.cards, [], [], self._verifier_from_locker()

    def _verifier_from_locker(self):
        return lambda key: locker.verify(self.db, self.agents, key)

    def _ask(self, office, method, route, data):
        self.asked.append(route)
        return {'done': route}


class Laptop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        (base / 'instance').mkdir()
        self.agents = base / 'agents'
        self.agents.mkdir()
        self.app = host.create_app(base / 'instance', secret='scratch-secret', agents=self.agents)
        self.h = self.app.config['harness']
        self.h.client = Frost()
        self.package, _row = marketplace_package()

    def tearDown(self):
        self.tmp.cleanup()

    def test_1_place_with_the_role_holds_it_as_the_marketplace(self):
        host.place(self.app, MARKET, self.package, role='marketplace')
        self.assertEqual(locker.held(self.h.db, MARKET)['folder'], f'marketplace/{MARKET}')
        self.assertEqual(locker.verify(self.h.db, self.agents, MARKET), (True, ''))

    def test_1_place_without_the_role_stays_a_developers_agent(self):
        host.place(self.app, MARKET, self.package)
        self.assertEqual(locker.held(self.h.db, MARKET)['folder'], f'dev/{MARKET}')

    def test_2_the_marketplace_is_its_card_key_on_the_platform(self):
        host.place(self.app, MARKET, self.package, role='marketplace')
        self.assertEqual(self.h.marketplace_key(), CARD)

    def test_2_a_member_hires_the_marketplace_by_its_card(self):
        host.place(self.app, MARKET, self.package, role='marketplace')
        p = Platform(self.h.db, self.agents, client=None)
        self.assertEqual(p.hire(ACCOUNT, 'SCRATCH', MEMBER, CARD, True), {'done': '/agnt/hire'})

    def test_2_the_developers_own_marketplace_does_not_shadow_the_placed_one(self):
        from core_engine import preview
        shutil.copytree(APP / 'agents' / 'marketplace', self.agents / 'marketplace', ignore=shutil.ignore_patterns('__pycache__'))
        self.assertEqual(preview.hold_marketplace(self.h.db, self.agents), preview.MARKETPLACE_KEY)   # the developer's runtime holds its own
        host.place(self.app, MARKET, self.package, role='marketplace')
        self.assertEqual(self.h.marketplace_key(), CARD)

    def test_3_an_approved_card_is_shown_and_hired(self):
        self.assertEqual(gate.shown(card(), (True, '')), (True, ''))
        host.place(self.app, MARKET, self.package, role='marketplace')
        p = Platform(self.h.db, self.agents, client=None)
        self.assertEqual(p.hire(ACCOUNT, 'SCRATCH', MEMBER, CARD, True), {'done': '/agnt/hire'})

    def test_3_live_is_not_a_status(self):
        self.assertEqual(gate.shown(card(status='LIVE'), (True, '')), (False, 'the card is not APPROVED'))
        self.assertEqual(gate.shown(card(status='REVOKED'), (True, '')), (False, 'the card is not APPROVED'))

    def test_4_a_run_record_names_the_account_and_the_member(self):
        self.h._record('job', CARD, 'DONE', job_key='MJOB_00000000000A_0001', run=1, account=ACCOUNT, member=MEMBER)
        con = sqlite3.connect(self.h.db)
        row = con.execute('SELECT lane, agent_key, state, account, member FROM runtime_runs').fetchone()
        con.close()
        self.assertEqual(row, ('job', CARD, 'DONE', ACCOUNT, MEMBER))

    def test_4_an_old_runs_table_gets_the_two_columns_and_keeps_its_rows(self):
        old = pathlib.Path(self.tmp.name) / 'old'
        old.mkdir()
        con = sqlite3.connect(old / 'runtime.db')
        con.execute('CREATE TABLE runtime_runs ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "lane" TEXT NOT NULL, "agent_key" TEXT NOT NULL, '
                    '"job_key" TEXT NOT NULL DEFAULT \'\', "run" INTEGER NOT NULL DEFAULT 0, "state" TEXT NOT NULL, "reason" TEXT NOT NULL DEFAULT \'\', '
                    '"started_at" TEXT NOT NULL, "finished_at" TEXT, "charged" INTEGER NOT NULL DEFAULT 0)')
        con.execute("INSERT INTO runtime_runs (lane, agent_key, state, started_at) VALUES ('call', 'K', 'REFUSED', 't')")
        con.commit()
        con.close()
        db = store.open_store(old)
        records.SqliteRecords(db).record('call', CARD, 'DONE', account=ACCOUNT, member=MEMBER)
        con = sqlite3.connect(db)
        rows = con.execute('SELECT agent_key, account, member FROM runtime_runs ORDER BY id').fetchall()
        con.close()
        self.assertEqual(rows, [('K', '', ''), (CARD, ACCOUNT, MEMBER)])


class CloudRun(CloudApp):
    """The same on the Cloud Run path: the bucket keeps the role and the card key; every instance finds the marketplace
    by its card and hires it."""
    def test_1_and_2_the_bucket_marketplace_is_its_card_key(self):
        package, row = marketplace_package()
        bucket_lockers.BucketLockers(bucket=self.bucket).publish(MARKET, row, package, role='marketplace')
        bucket_lockers.BucketLockers(bucket=self.bucket).link(MARKET, CARD)
        app = self.make()
        h = app.config['harness']
        self.assertEqual(locker.held(h.db, MARKET)['folder'], f'marketplace/{MARKET}')
        self.assertEqual(h.marketplace_key(), CARD)
        p = Platform(h.db, h.agents, client=None)
        self.assertEqual(p.hire(ACCOUNT, 'SCRATCH', MEMBER, CARD, True), {'done': '/agnt/hire'})

    def test_4_the_firestore_record_names_the_account_and_the_member(self):
        app = self.make()
        app.config['harnesses']['slot-b']._record('job', CARD, 'DONE', job_key='MJOB_00000000000A_0001', run=1, account=ACCOUNT, member=MEMBER)
        doc = next(iter(self.runs.docs.values()))
        self.assertEqual((doc['caller'], doc['account'], doc['member']), ('slot-b', ACCOUNT, MEMBER))


if __name__ == '__main__':
    unittest.main()
