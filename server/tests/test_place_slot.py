"""PLACE AND SUBMIT REACH FROST THROUGH THE SLOT THEY ARE FOR (frost-0d on rc18, Cloud Run): in keys mode the runtime
has no platform address of its own (create_app gets addresses={}), only one platform client per slot, signed with its
key for that slot. place and submit used the empty default and never reached FROST ("fs has no address here"). They
take the slot (--slot, or LARRYD_SLOT for the door's configured slot), use THAT slot's client, and refuse plainly when
no slot is named or the slot is unknown. On a laptop (no slots) the one harness is used as before."""
import os
import unittest
from unittest import mock

from _here import APP  # noqa: F401
from test_review_fixes import CloudApp, MARKET, marketplace_package
from web import app as host

CARD = 'MAGT_00000000CB01_0001'


class Frost:
    """One slot's platform client: what FROST answers at /agents/submit, and what it was asked."""
    def __init__(self, name):
        self.name, self.asked = name, []

    def post(self, office, route, data):
        self.asked.append((office, route))
        return 200, {'id': 1, 'state': 'waiting', 'card_key': CARD}

    def get(self, office, route, data=None):
        self.asked.append((office, route))
        return 200, {'approved': []}


class PlaceOnCloudRun(CloudApp):
    def setUp(self):
        super().setUp()
        self.app = self.make()
        self.frost = {}
        for slot, h in self.app.config['harnesses'].items():
            self.frost[slot] = h.client = Frost(slot)
        self.package, _row = marketplace_package()

    def test_two_slots_and_an_empty_default(self):
        self.assertEqual(sorted(self.app.config['harnesses']), ['slot-a', 'slot-b'])
        self.assertEqual(self.app.config['harness'].client.addresses, {})   # the default reaches no FROST: never used here

    def test_place_reaches_frost_through_the_named_slot(self):
        out = host.place(self.app, MARKET, self.package, role='marketplace', slot='slot-b')
        self.assertEqual(out['review']['state'], 'waiting', out)
        self.assertIn(('fs', '/agents/submit'), self.frost['slot-b'].asked)
        self.assertEqual(self.frost['slot-a'].asked, [])

    def test_the_door_s_configured_slot(self):
        with mock.patch.dict(os.environ, {'LARRYD_SLOT': 'slot-a'}):
            out = host.place(self.app, MARKET, self.package)
        self.assertEqual(out['review']['state'], 'waiting', out)
        self.assertIn(('fs', '/agents/submit'), self.frost['slot-a'].asked)

    def test_no_slot_named_is_refused_before_anything_is_held(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('LARRYD_SLOT', None)
            with self.assertRaises(SystemExit) as no:
                host.place(self.app, MARKET, self.package)
        self.assertIn('name the slot', str(no.exception))
        self.assertIn('slot-a, slot-b', str(no.exception))
        from core_engine import locker
        self.assertIsNone(locker.held(self.app.config['harness'].db, MARKET))

    def test_an_unknown_slot_is_refused(self):
        with self.assertRaises(SystemExit) as no:
            host.place(self.app, MARKET, self.package, slot='slot-z')
        self.assertIn('no slot slot-z', str(no.exception))

    def test_submit_and_review_use_the_named_slot_too(self):
        host.place(self.app, MARKET, self.package, slot='slot-b')
        self.frost['slot-b'].asked.clear()
        host.harness_for_slot(self.app, 'slot-b').submit(MARKET)
        self.assertIn(('fs', '/agents/submit'), self.frost['slot-b'].asked)
        with self.assertRaises(SystemExit):
            host.harness_for_slot(self.app, '')


class PlaceOnTheLaptop(unittest.TestCase):
    def test_the_one_harness_without_a_slot(self):
        import pathlib
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            (base / 'instance').mkdir()
            app = host.create_app(base / 'instance', secret='scratch-secret', agents=base / 'agents')
            self.assertIs(host.harness_for_slot(app, ''), app.config['harness'])


if __name__ == '__main__':
    unittest.main()
