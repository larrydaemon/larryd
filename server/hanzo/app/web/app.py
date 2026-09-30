"""HANZO'S HOST: the /api door, and nothing else. Every call must be signed with HANZO's secret (core_engine/signing.py),
except the developer door (/api/developer/...), where a developer signs with their own secret; an unsigned, stale or
wrongly signed call is refused (401) before any route runs. The routes hand the call to the
harness; a RUN is accepted at once (202) and runs on its own thread, its result written back to the platform."""
import datetime
import json
import logging
import os
import pathlib
import sys
import threading

from flask import Flask, g, jsonify, request

APP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

from core_engine import developers, harness as lanes_harness, platform, signing, store  # noqa: E402

CONFIG = json.loads((APP / 'schemas' / 'hanzo.json').read_text())
INSTANCE = APP.parent / 'instance'


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


NEEDS = ('account', 'scope', 'member')


def create_app(instance, secret, now=_utc_now, addresses=None, agents=None):
    """agents: the locker's folder (default HANZO's own; a test gives a scratch one)."""
    if not secret:
        raise SystemExit(f"HANZO does not start without its secret '{CONFIG['secret']['name']}'")
    db = store.open_store(instance)
    h = lanes_harness.Harness(db, APP / 'agents' if agents is None else pathlib.Path(agents), platform.Client(addresses or {}, secret),
                              CONFIG['run']['seconds'])
    running, lock = set(), threading.Lock()
    app = Flask('hanzo')
    app.config['harness'] = h

    dev = CONFIG['developers']
    secrets_dir = pathlib.Path(instance) / 'secrets' / dev['secrets']

    @app.before_request
    def signed_only():
        data = request.args.to_dict() if request.method == 'GET' else (request.get_json(silent=True) or {})
        route = request.path.removeprefix('/api')
        if route.startswith('/developer/'):
            who = request.headers.get('X-Developer', '')
            if not signing.good(developers.secret(secrets_dir, who), route, data, request.headers.get('X-Office-At'),
                                request.headers.get('X-Developer-Sig'), now(), CONFIG['signed_window_seconds']):
                return jsonify({'refused': 'not a signed call'}), 401
            g.developer = who
            return None
        if not signing.good(secret, route, data, request.headers.get('X-Office-At'), request.headers.get('X-Office'),
                            now(), CONFIG['signed_window_seconds']):
            return jsonify({'refused': 'not a signed call'}), 401
        return None

    @app.post('/api/developer/submit')
    def developer_submit():
        """A developer's agent: its files into the locker, then to FROST's review. -> its exact hashes and the review."""
        d = request.get_json(silent=True) or {}
        key = str(d.get('agent_key') or '')
        if key not in developers.theirs(db, g.developer):
            return jsonify({'refused': 'that agent is not yours'}), 403
        try:
            row = developers.receive(db, APP / 'agents' if agents is None else agents, dev['folder'], key, d.get('files'),
                                     dev['most_files'], dev['most_bytes'])
        except developers.Refused as no:
            return jsonify({'refused': no.reason}), no.status
        held = {'agent_key': key, 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']}
        try:
            review = h.submit(key)
        except lanes_harness.Refused as no:
            return jsonify({**held, 'refused': f'held in the locker, but FROST did not take it: {no.reason}; submit again'}), no.status
        return jsonify({**held, 'review': review}), 200

    @app.get('/api/developer/status')
    def developer_status():
        return jsonify(h.developer_status(developers.theirs(db, g.developer))), 200

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

    @app.get('/api/agents/answer')
    def answer():
        return answered(lambda: h.answer(*(given('agent_key')[k] for k in NEEDS + ('agent_key',))))

    @app.post('/api/agents/hire')
    def hire():
        def work():
            d = given('agent_key', 'on')
            if str(d['on']) not in ('on', 'off'):
                raise lanes_harness.Refused(400, 'on is "on" or "off"')
            return h.hire(d['account'], d['scope'], d['member'], d['agent_key'], str(d['on']) == 'on')
        return answered(work)

    @app.post('/api/agents/defaults')
    def defaults():
        return answered(lambda: h.defaults(*(given('board')[k] for k in NEEDS + ('board',))))

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


def locker_root(instance):
    """Where the agents are kept: the instance's own agents/ folder when there is one (a server: it outlives every release
    of the code), else the code's (the laptop)."""
    held = pathlib.Path(instance) / 'agents'
    return held if held.is_dir() else APP / 'agents'


def main(argv):
    """python hanzo/app/web/app.py                                   the host
    python hanzo/app/web/app.py submit <key>                        an agent HANZO holds, to FROST's review (its key, its exact hashes, its manifest)
    python hanzo/app/web/app.py developer add <name> <agent_key>    the developer may submit that agent; a new developer's secret is printed once"""
    if argv[1:3] == ['developer', 'add'] and len(argv) == 5:
        try:
            made = developers.add(store.open_store(INSTANCE), INSTANCE / 'secrets' / CONFIG['developers']['secrets'], argv[3], argv[4])
        except developers.Refused as no:
            raise SystemExit(f'refused: {no.reason}')
        print(f'{argv[3]} may submit {argv[4]}')
        if made:
            print(f'the developer\'s secret (shown this once; HANZO keeps its own copy): {made}')
        return
    side = os.environ.get(CONFIG['environment_variable'], 'localhost.rnd').split('.')[-1]
    secret_file = INSTANCE / 'secrets' / CONFIG['secret']['name']
    secret = secret_file.read_text().strip() if secret_file.is_file() else ''
    app = create_app(INSTANCE, secret, addresses=platform.addresses(CONFIG, side, INSTANCE), agents=locker_root(INSTANCE))
    if argv[1:2] == ['submit'] and len(argv) == 3:
        try:
            print(json.dumps(app.config['harness'].submit(argv[2])))
        except lanes_harness.Refused as no:
            raise SystemExit(f'refused ({no.status}): {no.reason}')
        return
    if len(argv) > 1:
        raise SystemExit(main.__doc__)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)   # no request lines: a call's query names an account and a member (data stays in wid)
    catch_up(app)
    app.run(host=CONFIG['host'], port=CONFIG['ports'][side], threaded=True)


if __name__ == '__main__':
    main(sys.argv)
