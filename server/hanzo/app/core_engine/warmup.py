"""THE WARM-UP (the infra lane's finding, 2026-10-06): a FRESH Cloud Run instance on Direct VPC egress through Cloud NAT
loses the slot's return packets for its first 15 to 35 seconds; after that every handshake answers. So an instance (and
a long-run job execution) shakes hands with each slot it may call back, a TLS handshake only and nothing sent into the
platform, until THREE succeed in a row or 60 seconds pass. Only then does the service report ready (/ready, the startup
probe), so no call reaches an instance before it can call back. Past 60 seconds it reports ready anyway and says so in
the log: the callbacks' own retries are the next guard, and a callback that still fails is recorded, never silent."""
import logging
import socket
import ssl
import time
import urllib.parse

LOG = logging.getLogger('hanzo')
IN_A_ROW = 3
MOST_SECONDS = 60
TRY_SECONDS = 3   # one handshake's limit
PAUSE = 0.5       # between tries


def handshake(host, port=443, seconds=TRY_SECONDS):
    """One TLS handshake, the certificate verified, then closed: no byte of a request is ever sent."""
    with socket.create_connection((host, port), timeout=seconds) as raw:
        with ssl.create_default_context().wrap_socket(raw, server_hostname=host):
            return True


def hosts(slots):
    """The (host, port) of every slot with a callback address (slot A has none today: it is never warmed or called)."""
    out = []
    for name, base in slots.items():
        if isinstance(base, str) and base.startswith('https://'):   # the slots' addresses; 'about' and 'offices' are not
            u = urllib.parse.urlsplit(base)
            out.append((u.hostname, u.port or 443))
    return sorted(set(out))


def warm(targets, shake=handshake, clock=time.monotonic, sleep=time.sleep, most=MOST_SECONDS):
    """-> {'ready': True when every target answered IN_A_ROW in a row, 'seconds': how long it took, 'tries': n}."""
    start, tries, done = clock(), 0, set()
    run = {t: 0 for t in targets}
    while len(done) < len(run) and clock() - start < most:
        for t in run:
            if t in done:
                continue
            tries += 1
            try:
                shake(*t)
                run[t] += 1
            except (OSError, ValueError):
                run[t] = 0   # a lost handshake starts the count again
            if run[t] >= IN_A_ROW:
                done.add(t)
        if len(done) < len(run):
            sleep(PAUSE)
    took = round(clock() - start, 1)
    ok = len(done) == len(run)
    if ok:
        LOG.warning('warm-up: %d slot(s) answered %d handshakes in a row after %.1f s (%d tries)', len(run), IN_A_ROW, took, tries)
    else:
        LOG.error('warm-up: not every slot answered in %d s (%d tries); ready anyway, the callbacks retry', most, tries)
    return {'ready': ok, 'seconds': took, 'tries': tries}
