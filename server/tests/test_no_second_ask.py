"""AN OFFICE ON THIS COMPUTER IS NEVER ASKED TWICE FOR WHAT IT ALREADY HOLDS (the owner 2026-11-10: "slow"): the inside runtime gave up
on wid after 10 s and sent the same GET again for up to 40 s while wid was still working on the first; one board page made every call 3 to
4 copies and every answer took 30 to 70 s. A GET that left is not sent again; one that never left (the office restarting) still is; the
Cloud Run slots keep their retry (Cloud NAT loses answers there)."""
import socket
import urllib.error

from _here import APP  # noqa: F401
from core_engine import callers, platform
from test_callback_warmup import Answer, Clock
from test_review_fixes import CloudApp


class NoSecondAsk(CloudApp):
    def client(self, here):
        self.clock = Clock()
        return platform.Client({'wid': 'http://127.0.0.1:5004/wid'}, '', outbound=callers.Outbound(self.out_dir), slot='slot-b',
                               retry_seconds=40, clock=self.clock, sleep=self.clock.sleep, asks_again_once_sent=not here)

    def patched(self, answers):
        sent, it = [], iter(answers)

        def opener(req, timeout=None):
            sent.append(self.clock.t)
            a = next(it)
            if isinstance(a, BaseException):
                raise a
            return Answer()
        orig = platform.urllib.request.urlopen
        platform.urllib.request.urlopen = opener
        self.addCleanup(setattr, platform.urllib.request, 'urlopen', orig)
        return sent

    def test_a_get_that_left_is_sent_once_to_an_office_here(self):
        sent = self.patched([TimeoutError('no answer after sending')] * 6)
        status, body = self.client(here=True).get('wid', '/agnt/records/list', {'a': 1})
        self.assertEqual((status, len(sent)), (0, 1))
        self.assertEqual(body, {'refused': 'wid does not answer'})

    def test_a_get_that_never_left_is_still_retried_here(self):
        lost = urllib.error.URLError(socket.timeout('connect'))
        sent = self.patched([lost, lost, Answer()])
        status, _ = self.client(here=True).get('wid', '/agnt/records/list', {'a': 1})
        self.assertEqual((status, len(sent)), (200, 3))

    def test_a_slot_in_the_cloud_keeps_its_retry(self):
        sent = self.patched([TimeoutError('no answer after sending')] * 2 + [Answer()])
        status, _ = self.client(here=False).get('wid', '/agnt/records/list', {'a': 1})
        self.assertEqual((status, len(sent)), (200, 3))
