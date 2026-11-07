"""ONE RUNTIME SOURCE, TWO PLACES (ONE SYSTEM, phase 1, 2026-11-07): the internal runtime's own ways live in this one source, switched
ONLY by LARRYD_INTERNAL=1 at its start; unset (Cloud Run), every one of them is off and the runtime does what it always did.
Here: the queue a start catches up on, and instance/slots.json naming where each caller's offices answer. Scratch folders only."""
import json
import os
import pathlib
import unittest
from unittest import mock

from test_review_fixes import CloudApp, host


class TheQueue(CloudApp):
    def asked(self, internal):
        env = {'LARRYD_INTERNAL': '1'} if internal else {}
        with mock.patch.dict(os.environ, env, clear=False):
            if not internal:
                os.environ.pop('LARRYD_INTERNAL', None)
            app = self.make('queue_internal' if internal else 'queue_external')
            said = []
            for h in app.config['harnesses'].values():
                h.client.get = lambda office, route, data=None: said.append((office, route, data)) or (200, {'jobs': []})
            host.catch_up(app)
        return said

    def test_the_external_runtime_asks_its_own_queue_as_before(self):
        said = self.asked(False)
        self.assertTrue(said)
        self.assertEqual({s for s in said}, {('wid', '/jobs/queued', None)})

    def test_the_internal_runtime_asks_the_internal_queue(self):
        said = self.asked(True)
        self.assertTrue(said)
        self.assertEqual([d for _o, _r, d in said], [{'runtime': 'internal'}] * len(said))


class TheSlotsFile(CloudApp):
    def offices(self, internal):
        inst = pathlib.Path(self.dir.name) / ('slots_internal' if internal else 'slots_external')
        inst.mkdir()
        (inst / 'slots.json').write_text(json.dumps({'slot-a': {'wid': 'http://127.0.0.1:59999/wid'}}))
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('LARRYD_INTERNAL', None)
            if internal:
                os.environ['LARRYD_INTERNAL'] = '1'
            app = self.make(inst.name)
        return app.config['harnesses']['slot-a'].client.addresses

    def test_the_internal_runtime_reads_where_its_callers_offices_are(self):
        self.assertEqual(self.offices(True), {'wid': 'http://127.0.0.1:59999/wid'})

    def test_the_external_runtime_never_reads_it(self):
        self.assertNotEqual(self.offices(False), {'wid': 'http://127.0.0.1:59999/wid'})


if __name__ == '__main__':
    unittest.main()
