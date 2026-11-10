"""THE OFFICES ON THIS COMPUTER ARE ASKED A FEW THINGS AT A TIME (the owner 2026-11-10: "THIS PAGE IS SLOW"): one Scrum Master page had
about 45 agents each asking the same host for its records at the same moment; alone a call takes about 50 ms, together each took seconds
to a minute. Every call waits in the runtime's own line (platform.Client gate) and leaves when it is its turn; without a gate (the
Cloud Run slots) nothing waits."""
import threading
import time

from _here import APP  # noqa: F401
from core_engine import callers, platform
from test_callback_warmup import Answer
from test_review_fixes import CloudApp


class InLine(CloudApp):
    def calls(self, gate, n=8):
        inside, most, lock = [0], [0], threading.Lock()

        def opener(req, timeout=None):
            with lock:
                inside[0] += 1
                most[0] = max(most[0], inside[0])
            time.sleep(0.02)
            with lock:
                inside[0] -= 1
            return Answer()
        orig = platform.urllib.request.urlopen
        platform.urllib.request.urlopen = opener
        self.addCleanup(setattr, platform.urllib.request, 'urlopen', orig)
        client = platform.Client({'wid': 'http://127.0.0.1:5004/wid'}, '', outbound=callers.Outbound(self.out_dir), slot='slot-b', gate=gate)
        got = []
        threads = [threading.Thread(target=lambda: got.append(client.get('wid', '/agnt/records/list', {'a': 1})[0])) for _ in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return most[0], got

    def test_two_at_a_time_and_every_call_answered(self):
        most, got = self.calls(threading.BoundedSemaphore(2))
        self.assertEqual(most, 2)
        self.assertEqual(got, [200] * 8)

    def test_without_a_gate_nothing_waits(self):
        most, got = self.calls(None)
        self.assertGreater(most, 2)
        self.assertEqual(got, [200] * 8)
