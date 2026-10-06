"""HANZO'S HOST: the /api door, and nothing else. Every call must be signed with HANZO's secret (core_engine/signing.py);
an unsigned, stale or wrongly signed call is refused (401) before any route runs. (A developer's agent comes in through
LARRYD's submit door and the owner's review, then `place` below; never through this door.) The routes hand the call to the
harness; a RUN is accepted at once (202) and runs on its own thread, its result written back to the platform.

THE DEVELOPER'S RUNTIME (LARRYD_DEVELOPER=1, set only by the daemon a developer starts): with no platform address
declared, the platform's answers come from core_engine/preview.py, and the runtime also serves /marketplace, the
developer's own shelf: every held agent as a card with its hire toggle, through the very same harness, gate, lanes
and sandbox as the server. A server never sets the flag and never has the page."""
import datetime
import json
import logging
import os
import pathlib
import secrets
import sys
import threading
from urllib.parse import quote

from flask import Flask, jsonify, redirect, render_template, request
from werkzeug.exceptions import HTTPException

APP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

from core_engine import callers, harness as lanes_harness, intake, platform, preview, signing, store  # noqa: E402

CONFIG = json.loads((APP / 'schemas' / 'hanzo.json').read_text())
INSTANCE = pathlib.Path(os.environ['LARRYD_INSTANCE']) if os.environ.get('LARRYD_INSTANCE') else APP.parent / 'instance'   # the daemon names it
DEVELOPER = 'LARRYD_DEVELOPER'   # the daemon sets it to 1 on a developer's computer; a server runs this file itself, without it


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


NEEDS = ('account', 'scope', 'member')
MAX_BODY = 64 * 1024   # a signed call's body; anything larger is refused unread


def create_app(instance, secret, now=_utc_now, addresses=None, agents=None, developer=False, keys=None, nonces=None):
    """agents: the locker's folder (default HANZO's own; a test gives a scratch one). developer: the developer's runtime
    (the marketplace page; the platform's answers from the instance when no address is declared)."""
    if not secret and keys is None:
        raise SystemExit(f"HANZO does not start without its secret '{CONFIG['secret']['name']}'")
    db = store.open_store(instance)
    locker_dir = APP / 'agents' if agents is None else pathlib.Path(agents)
    local = bool(developer) and not addresses
    if local:
        preview.hold_marketplace(db, locker_dir)
    client = preview.Local(db, locker_dir, instance) if local else platform.Client(addresses or {}, secret)
    h = lanes_harness.Harness(db, locker_dir, client, CONFIG['run']['seconds'])
    running, lock = set(), threading.Lock()
    app = Flask('hanzo', template_folder=str(APP / 'web'))
    app.config['harness'] = h
    app.config['developer'] = bool(developer)

    @app.before_request
    def signed_only():
        if developer and request.path.startswith('/marketplace'):
            return None   # the developer's own page, on 127.0.0.1, in the browser: no office signs it
        route = request.path.removeprefix('/api')
        if keys is not None:   # THE HARDENED CALL (Cloud Run): a key per caller and a nonce, never the shared secret
            known, h = keys.now(), request.headers
            if (request.content_length or 0) > MAX_BODY or not signing.well_formed(h.get('X-Office-Key'), h.get('X-Office-At'),
                                                                                     h.get('X-Office-Nonce'), h.get('X-Office'), known):
                return jsonify({'refused': 'not a signed call'}), 401   # before the body is read or anything is stored
            data = request.args.to_dict() if request.method == 'GET' else (request.get_json(silent=True) or {})
            ok = signing.good_hardened(known, h.get('X-Office-Key'), route, data, h.get('X-Office-At'), h.get('X-Office-Nonce'),
                                       h.get('X-Office'), now(), CONFIG['signed_window_seconds'], nonces.fresh)
        else:
            data = request.args.to_dict() if request.method == 'GET' else (request.get_json(silent=True) or {})
            ok = signing.good(secret, route, data, request.headers.get('X-Office-At'), request.headers.get('X-Office'),
                              now(), CONFIG['signed_window_seconds'])
        if not ok:
            return jsonify({'refused': 'not a signed call'}), 401
        return None

    @app.errorhandler(Exception)
    def failed(error):   # nothing of an exception is ever echoed to a caller (the security review, 2026-10-06)
        if isinstance(error, HTTPException):
            return jsonify({'refused': error.name}), error.code   # a 404 or 405 stays itself, with its plain name only
        logging.getLogger('hanzo').exception('a call failed')
        return jsonify({'refused': 'the runtime could not answer'}), 500

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
    if developer:
        _marketplace_pages(app, h, pathlib.Path(instance), secrets.token_hex(16))
    return app


def _marketplace_pages(app, h, instance, token):
    """THE DEVELOPER'S SHELF: the marketplace's answer of cards, drawn in the platform's structure (cards.html's: the
    controller's counts, then each card: NO. · class · HIRE toggle · name · art · product · module · pitch · developer ·
    TYPE ▸ RESIDENCY · price), plus what a developer needs and a member never sees: the cards the gate does not show,
    each with why. The first visit places the marketplace itself, once, as the platform's first visit of a board does."""
    who = (preview.ACCOUNT, preview.SCOPE, preview.MEMBER)
    first = instance / 'preview' / 'first_visit.json'

    def mine():
        """The developer's own browser or CLI on this computer, and nothing else: the loopback host name (a rebound name is
        refused) and no cross-site origin (a form or a fetch from another site is refused). -> '' or why not."""
        if request.host.split(':')[0] not in ('127.0.0.1', 'localhost'):
            return "not this computer's address"
        origin = request.headers.get('Origin')
        if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
            return 'not from this page'
        return ''

    def refused(why):
        return jsonify({'refused': why}), 403

    def collection():
        if not first.exists():
            first.parent.mkdir(parents=True, exist_ok=True)
            h.defaults(*who, preview.BOARD)
            first.write_text(json.dumps({'board': preview.BOARD}) + '\n')
        answer = h.answer(*who, h.marketplace_key())
        cards, _hired, _groups, verify = h.facts(*who)
        return answer, preview.hidden(cards, verify)

    @app.get('/marketplace')
    def marketplace():
        if mine():
            return refused(mine())
        try:
            answer, not_shown = collection()
        except lanes_harness.Refused as why:
            return render_template('marketplace.html', refused=why.reason, token=token, marketplace_key=preview.MARKETPLACE_KEY), why.status
        return render_template('marketplace.html', A=answer, hidden=not_shown, no=request.args.get('no', ''), token=token,
                               marketplace_key=preview.MARKETPLACE_KEY)

    @app.get('/marketplace.json')
    def marketplace_json():
        if mine():
            return refused(mine())
        try:
            answer, not_shown = collection()
        except lanes_harness.Refused as why:
            return jsonify({'refused': why.reason}), why.status
        return jsonify({**answer, 'not_shown': [{'name': n, 'why': w} for n, w in not_shown]})

    @app.post('/marketplace/hire')
    def marketplace_hire():
        if mine():
            return refused(mine())
        form = request.form
        if form.get('token') != token:
            return redirect('/marketplace?no=' + quote('the page was stale; it is fresh now, toggle again'))
        try:
            h.hire(*who, str(form.get('key') or ''), form.get('value') == 'on')
        except lanes_harness.Refused as why:
            return redirect('/marketplace?no=' + quote(('The agent could not be hired: ' if form.get('value') == 'on' else
                                                        'The agent could not be let go: ') + why.reason))
        return redirect('/marketplace')

    @app.post('/marketplace/place')
    def marketplace_place():
        """`larryd place`: the agent's one file (agent/ as a zip) into this runtime's locker, the way the server places an
        approved one; the same agent placed again replaces itself."""
        if mine():
            return refused(mine())
        if request.headers.get('X-Larryd-Place') != '1' or not (request.content_type or '').startswith('application/octet-stream'):
            return refused('not larryd place')   # a browser cannot send this header without a preflight nobody answers
        key, conf = str(request.args.get('key') or ''), CONFIG['intake']
        try:
            files = intake.check(intake.from_zip(request.get_data(), conf['most_files'], conf['most_bytes']), conf['most_files'], conf['most_bytes'])
            row = intake.receive(h.db, h.agents, conf['folder'], key, files)
        except intake.Refused as no:
            return jsonify({'refused': no.reason}), no.status
        return jsonify({'held': {'agent_key': key, 'name': row['name'], 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']},
                        'marketplace': '/marketplace'}), 201


def place(app, agent_key, data):
    """An approved agent file into the locker (<intake folder>/<card key>/), then to FROST's review. -> what was held, and
    FROST's review or why FROST did not take it (the agent stays held; `submit <key>` sends it again)."""
    h, conf = app.config['harness'], CONFIG['intake']
    try:
        files = intake.check(intake.from_zip(data, conf['most_files'], conf['most_bytes']), conf['most_files'], conf['most_bytes'])
        row = intake.receive(h.db, h.agents, conf['folder'], agent_key, files)
    except intake.Refused as no:
        raise SystemExit(f'refused ({no.status}): {no.reason}')
    held = {'agent_key': agent_key, 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']}
    try:
        return {**held, 'review': h.submit(agent_key)}
    except lanes_harness.Refused as no:
        return {**held, 'refused': f'held in the locker, but FROST did not take it: {no.reason}; send it again with submit {agent_key}'}


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
    python hanzo/app/web/app.py place <card key> <file.larryd>      an agent the owner approved (LARRYD's review queue): into the locker, then to FROST's review
    python hanzo/app/web/app.py review <card key>...                what HANZO records for those agents, with FROST's word on the hashes it holds"""
    side = os.environ.get(CONFIG['environment_variable'], 'localhost.rnd').split('.')[-1]
    secret_file = INSTANCE / 'secrets' / CONFIG['secret']['name']
    secret = secret_file.read_text().strip() if secret_file.is_file() else ''
    keys_dir = os.environ.get('LARRYD_KEYS_DIR')   # Cloud Run: the callers' keys, one file each (the hardened call)
    app = create_app(INSTANCE, secret, addresses=platform.addresses(CONFIG, side, INSTANCE), agents=locker_root(INSTANCE),
                     developer=os.environ.get(DEVELOPER) == '1',
                     keys=callers.Keys(keys_dir) if keys_dir else None, nonces=callers.nonces() if keys_dir else None)
    if argv[1:2] == ['place'] and len(argv) == 4:
        print(json.dumps(place(app, argv[2], pathlib.Path(argv[3]).read_bytes())))
        return
    if argv[1:2] == ['review'] and len(argv) >= 3:
        print(json.dumps(app.config['harness'].review_state(argv[2:])))
        return
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
    app.run(host=os.environ.get('LARRYD_HOST') or CONFIG['host'], port=int(os.environ.get('PORT') or os.environ.get('LARRYD_PORT') or CONFIG['ports'][side]),
            threaded=True)   # 127.0.0.1, except in a container (Cloud Run names LARRYD_HOST and PORT)


if __name__ == '__main__':
    main(sys.argv)
