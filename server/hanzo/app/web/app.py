"""HANZO'S HOST: the /api door, and nothing else. Every call must be signed with HANZO's secret (core_engine/signing.py);
an unsigned, stale or wrongly signed call is refused (401) before any route runs. The routes hand the call to the
harness; a RUN is accepted at once (202) and runs on its own thread, its result written back to the platform."""
import datetime
import json
import os
import pathlib
import sys
import threading

from flask import Flask, jsonify, request

APP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

from core_engine import harness as lanes_harness, platform, signing, store  # noqa: E402

CONFIG = json.loads((APP / 'schemas' / 'hanzo.json').read_text())
INSTANCE = APP.parent / 'instance'


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


NEEDS = ('account', 'scope', 'member')


def create_app(instance, secret, now=_utc_now, addresses=None):
    if not secret:
        raise SystemExit(f"HANZO does not start without its secret '{CONFIG['secret']['name']}'")
    db = store.open_store(instance)
    h = lanes_harness.Harness(db, APP / 'agents', platform.Client(addresses or {}, secret), CONFIG['run']['seconds'])
    running, lock = set(), threading.Lock()
    app = Flask('hanzo')
    app.config['harness'] = h

    @app.before_request
    def signed_only():
        data = request.args.to_dict() if request.method == 'GET' else (request.get_json(silent=True) or {})
        route = request.path.removeprefix('/api')
        if not signing.good(secret, route, data, request.headers.get('X-Office-At'), request.headers.get('X-Office'),
                            now(), CONFIG['signed_window_seconds']):
            return jsonify({'refused': 'not a signed call'}), 401
        return None

    @app.get('/api/health')
    def health():
        return jsonify({'office': CONFIG['office'], **store.counts(db)})

    def given(*more):
        data = request.args.to_dict() if request.method == 'GET' else (request.get_json(silent=True) or {})
        missing = [k for k in NEEDS + more if not str(data.get(k) or '').strip()]
        if missing:
            raise lanes_harness.Refused(400, f"missing: {', '.join(missing)}")
        return data

    def answered(work):
        try:
            return jsonify(work()), 200
        except lanes_harness.Refused as no:
            return jsonify({'refused': no.reason}), no.status

    @app.get('/api/marketplace/collection')
    def collection():
        return answered(lambda: h.collection(*(given()[k] for k in NEEDS)))

    @app.post('/api/marketplace/hire')
    def hire():
        def work():
            d = given('agent_key', 'on')
            if str(d['on']) not in ('on', 'off'):
                raise lanes_harness.Refused(400, 'on is "on" or "off"')
            return h.hire(d['account'], d['scope'], d['member'], d['agent_key'], str(d['on']) == 'on')
        return answered(work)

    def start(account, scope, member, job_key, run):
        with lock:
            if (job_key, run) in running:
                return False
            running.add((job_key, run))

        def go():
            try:
                h.run_job(account, scope, member, job_key, run)
            finally:
                with lock:
                    running.discard((job_key, run))
        threading.Thread(target=go, daemon=True).start()
        return True

    @app.post('/api/jobs/run')
    def run_job():
        try:
            d = given('job_key', 'run')
        except lanes_harness.Refused as no:
            return jsonify({'refused': no.reason}), no.status
        if not str(d['run']).isdigit():
            return jsonify({'refused': 'run is the RUN number'}), 400
        started = start(d['account'], d['scope'], d['member'], d['job_key'], int(d['run']))
        return jsonify({'accepted': d['job_key'], 'run': int(d['run']), 'already': not started}), 202

    app.config['start'] = start
    return app


def catch_up(app):
    """At start, once (never a loop): the RUNs the platform queued while HANZO was away."""
    status, body = app.config['harness'].client.get('wid', '/jobs/queued')
    for j in body.get('jobs', []) if status == 200 else []:
        app.config['start'](j['account'], j['scope'], j['member'], j['job_key'], int(j['run']))
    return status


def main():
    side = os.environ.get(CONFIG['environment_variable'], 'localhost.rnd').split('.')[-1]
    secret_file = INSTANCE / 'secrets' / CONFIG['secret']['name']
    secret = secret_file.read_text().strip() if secret_file.is_file() else ''
    app = create_app(INSTANCE, secret, addresses=platform.addresses(CONFIG, side, INSTANCE))
    catch_up(app)
    app.run(host=CONFIG['host'], port=CONFIG['ports'][side], threaded=True)


if __name__ == '__main__':
    main()
