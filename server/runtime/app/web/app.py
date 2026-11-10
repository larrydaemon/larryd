"""THE RUNTIME'S HOST: the /api door, and nothing else. Every call must be signed with the runtime's secret (core_engine/signing.py);
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
import re
import resource
import secrets
import shutil
import sys
import threading
import time
import traceback
from urllib.parse import quote

from flask import Flask, Response, jsonify, redirect, render_template, request, send_from_directory
from werkzeug.exceptions import HTTPException

APP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

from core_engine import callers, clock, decision, harness as lanes_harness, intake, jobs as long_runs, live, locker, lockers as bucket_lockers, platform, preview, records as run_records, sandbox, signing, slot as one_slot, store, warmup  # noqa: E402

CONFIG = json.loads((APP / 'schemas' / 'runtime.json').read_text())
INSTANCE = pathlib.Path(os.environ['LARRYD_INSTANCE']) if os.environ.get('LARRYD_INSTANCE') else APP.parent / 'instance'   # the daemon names it
DEVELOPER = 'LARRYD_DEVELOPER'   # the daemon sets it to 1 on a developer's computer; a server runs this file itself, without it


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


NEEDS = ('account', 'scope', 'member')
MAX_BODY = 4 * 1024 * 1024   # a signed call's body; anything larger is refused unread (4 MB since 2026-11-04: a page's call carries the platform's handed answers, records included, the platform sends at most 3.5 MB)
RETRY_IN_REQUEST = 40   # a call back made inside a request retries this long (the request itself ends at 60 s)
RETRY_IN_JOB = 60       # a job execution's calls back retry this long
HERE_AT_ONCE = 2        # how many calls the runtime on this computer has inside its own platform host at one time; the rest wait in line (platform.Client gate)
HERE_RUNS = 3           # how many RUNs the runtime on this computer runs at one time (core_engine/slot.Slots); Cloud Run: one per instance


KEY = re.compile(r'[A-Z]{4}_[0-9A-F]{12}_[0-9A-F]{4}')   # a key as the platform's one generator writes it


AGENT_KEY = re.compile(r'^MAGT_[0-9A-F]{12}_[0-9A-F]{4}$')


def failed_where(error):
    """A failed call's own place for the log (2026-11-10: "FileNotFoundError on /api/agents/answer" named no agent): the file and line it was
    raised at (the innermost frame, the file's name alone) and the agent key the call names, only when it is a well-formed MAGT key;
    nothing else of the call, and nothing of it to the caller"""
    frames = traceback.extract_tb(error.__traceback__) if error.__traceback__ else []
    at = f' at {os.path.basename(frames[-1].filename)}:{frames[-1].lineno}' if frames else ''
    try:
        named = request.values.get('agent_key') or ((request.get_json(silent=True) or {}).get('agent_key') if request.is_json else '')
    except Exception:   # a body that cannot be read names no agent
        named = ''
    return at + (f' for {named}' if isinstance(named, str) and AGENT_KEY.match(named) else '')


def create_app(instance, secret, now=_utc_now, addresses=None, agents=None, developer=False, keys=None, nonces=None, cloud=None,
               retry_seconds=RETRY_IN_REQUEST, outside=None):
    """agents: the locker's folder (default the runtime's own; a test gives a scratch one). developer: the developer's runtime
    (the marketplace page; the platform's answers from the instance when no address is declared).
    keys: the hardened call (Cloud Run): {key id: [versions]} of the callers. cloud: Cloud Run's parts (the runtime design):
    {'outbound': callers.Outbound, 'records': run records, 'lockers': BucketLockers or None, 'claims': job claims,
    'jobs': the job starter or None}. retry_seconds: how long a call back to a slot is retried (Cloud Run only).
    On Cloud Run the app is NOT READY (/ready answers 503) until warm_up() has run: the startup probe holds every call
    back until the instance can reach the slots. On Cloud Run the runtime REFUSES TO START without its own outbound key for every
    slot that may call it (no call back to the platform is ever signed with an empty key)."""
    cloud = dict(cloud or {})
    if keys is not None:
        outbound = cloud.get('outbound')
        callers_known = sorted((keys.now() if hasattr(keys, 'now') else keys) or {})
        if outbound is None or not callers_known or any(c not in outbound.slots() for c in callers_known):
            raise SystemExit('the runtime does not start without its own outbound key for every slot that may call it')
    elif not secret:
        raise SystemExit(f"LARRYD does not start without its secret '{CONFIG['secret']['name']}'")
    db = store.open_store(instance)
    locker_dir = APP / 'agents' if agents is None else pathlib.Path(agents)
    lockers = cloud.get('lockers')
    held_from_bucket = None
    if lockers is not None:   # Cloud Run: the instance's locker is only a cache of the lockers bucket, filled at start
        locker_dir.mkdir(parents=True, exist_ok=True)
        held_from_bucket = lockers.sync(db, locker_dir, CONFIG['intake'])
    local = bool(developer) and not addresses
    if local:
        preview.hold_marketplace(db, locker_dir)
    records = cloud.get('records') or run_records.SqliteRecords(db)
    client = preview.Local(db, locker_dir, instance) if local else platform.Client(addresses or {}, secret)
    # THE OUTSIDE HAND (core_engine/outside.py). The runtime holds NO provider key, anywhere: each errand asks wid, which reads the platform's vault
    # for it (harness._provider_key; the owner: "a single source setup"). outside = {'hand', 'a_day'} replaces the hand or the limit (the lab, a test)
    hand_parts = {'a_day': (CONFIG.get('makes') or {}).get('a_day'), **(outside or {})}
    h = lanes_harness.Harness(db, locker_dir, client, CONFIG['run']['seconds'], records=records, **hand_parts)
    harnesses = {}
    if keys is not None:   # one harness per slot: its calls go back to THAT slot, signed with the runtime's key for it
        slots = CONFIG['slots']
        here = pathlib.Path(instance) / 'slots.json'   # THE RUNTIME ON THIS COMPUTER (LARRYD RUNTIME INTERNAL only, the owner 2026-11-03: "the localhost one is on the computer localhost here"): its instance names where each caller's offices answer, {caller: {office: address}}
        local = json.loads(here.read_text()) if os.environ.get('LARRYD_INTERNAL') == '1' and here.is_file() else {}
        here_gate = threading.BoundedSemaphore(HERE_AT_ONCE)   # one line for every call to the offices on this computer
        for caller in cloud['outbound'].slots():
            base = slots.get(caller, '')
            offices = local[caller] if isinstance(local.get(caller), dict) else {o: f'{base}/{o}' for o in slots['offices']} if base else {}
            harnesses[caller] = lanes_harness.Harness(
                db, locker_dir, platform.Client(offices, '',
                                                outbound=cloud['outbound'], slot=caller, retry_seconds=retry_seconds,
                                                asks_again_once_sent=not isinstance(local.get(caller), dict),
                                                gate=here_gate if isinstance(local.get(caller), dict) else None),   # an office on this computer is never asked twice for what it already holds
                CONFIG['run']['seconds'], records=records, caller=caller, **hand_parts)
    claims = cloud.get('claims') or long_runs.MemoryClaims()
    job_starter = cloud.get('jobs')
    running, lock = set(), threading.Lock()
    slot = (one_slot.Slots(HERE_RUNS, CONFIG['run']['seconds'] + 60) if os.environ.get('LARRYD_INTERNAL') == '1'   # THIS COMPUTER: a few runs at a time, so a long step never makes the other blocks wait past the platform's 20 minutes
            else one_slot.Slot(CONFIG['run']['seconds'] + 60))   # ONE RUN PER INSTANCE: above the run's own hard limit, plus a minute
    run_most = (lanes_harness.Harness.MOST_INTERNAL_SECONDS + 60) if os.environ.get('LARRYD_INTERNAL') == '1' else None   # A RUN's slot on this computer: an internal agent's own limit (up to 6 hours) plus a minute, never a CALL's 80 s (the 305 "slot stuck" lines of 2026-11-09)
    sandbox.ROOT = str(pathlib.Path(instance) / 'runs')   # this instance's own run folders: another runtime's sweep of the shared temp folder never reaches them (Session 9 2026-11-10: a RUN's answer file was gone at sandbox.run, the thread died, the platform closed the RUN at 20 minutes); never out/, the outbound keys' folder, whose every entry is read as a key
    for stray in pathlib.Path(instance, 'out').glob('runtime_[ro][ua][nt]_*'):   # run folders 39ef274 made among the outbound keys (14:38 to this start): never a key, its process gone
        shutil.rmtree(stray, ignore_errors=True)
    sandbox.sweep(**({'older_than': run_most} if run_most else {}))   # a run's folders left by a stopped instance are removed before anything runs; on this computer a folder younger than the longest RUN is a RUN in flight (OPERATION BDAY item 1: at 12:08 a second start swept two live RUNs' folders)
    app = Flask('runtime', template_folder=str(APP / 'web'))
    app.config['harness'] = h
    app.config['harnesses'] = harnesses
    app.config['slot'] = slot
    app.config['developer'] = bool(developer)
    app.config['lockers'] = lockers
    app.config['held_from_bucket'] = held_from_bucket
    app.config['records'] = records
    app.config['ready'] = threading.Event()
    if keys is None:
        app.config['ready'].set()   # a laptop or a test has no NAT to warm

    def harness_for():
        """The calling slot's harness on Cloud Run (its key id named it), else the one harness."""
        caller = request.headers.get('X-Office-Key') if keys is not None else None
        return harnesses.get(caller, h) if caller else h

    @app.get('/ready')
    def ready():
        """Cloud Run's startup probe (unsigned: the probe cannot sign). Says only ready or not, nothing else."""
        return (jsonify({'ready': True}), 200) if app.config['ready'].is_set() else (jsonify({'ready': False}), 503)

    @app.before_request
    def signed_only():
        if request.path == '/ready' and request.method == 'GET':
            return None   # the startup probe; the route answers one word and runs nothing
        if developer and request.path.startswith('/marketplace'):
            return None   # the developer's own page, on 127.0.0.1, in the browser: no office signs it
        if request.path == '/api/live/records' and request.method == 'POST':
            return None   # an agent's own room program: no office; the door itself checks its mark, made with the key LARRYD shares with it alone
        route = request.path.removeprefix('/api')
        if keys is not None:   # THE HARDENED CALL (Cloud Run): a key per caller and a nonce, never the shared secret
            known, h = keys.now(), request.headers
            if (request.content_length or 0) > MAX_BODY or not signing.well_formed(h.get('X-Office-Key'), h.get('X-Office-At'),
                                                                                     h.get('X-Office-Nonce'), h.get('X-Office'), known):
                return jsonify({'refused': 'not a signed call'}), 401   # before the body is read or anything is stored
            if request.method != 'GET':   # the cap on the bytes actually read (a chunked body has no Content-Length to trust)
                raw = request.stream.read(MAX_BODY + 1)
                if len(raw) > MAX_BODY:
                    return jsonify({'refused': 'too large'}), 413   # never read on, nothing stored
                request._cached_data = raw   # the body as read, for get_json below
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
        logging.getLogger('runtime').error('a call failed: %s on %s%s', type(error).__name__, request.path, failed_where(error))   # the kind, the door, where it was raised and whose agent; never a run's data
        return jsonify({'refused': 'the runtime could not answer'}), 500

    @app.get('/api/health')
    def health():
        if slot.stuck():   # held past the limit with nothing that can be reclaimed: Cloud Run replaces this instance
            return jsonify({'office': CONFIG['office'], 'refused': 'the slot is stuck'}), 503
        counts = store.counts(db)
        if lockers is not None:
            counts = {'locker': counts['locker'], 'runs': 'firestore'}   # the run records are Firestore's, never this disk's
        return jsonify({'office': CONFIG['office'], **counts})

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

    def busy():
        return jsonify({'refused': 'busy: this instance is running another agent, try again'}), 409

    def granted(d, what, decided=True):
        """THE SECOND GUARD at the door: refused here, before the platform is asked or anything is recorded. decided: FROST's
        signed decision verified too (frost_decided); a let-go carries none (wid decides nothing to let an agent go)."""
        if not access_granted(d):
            raise lanes_harness.Refused(403, NOT_GRANTED)
        if decided:
            why = frost_decided(d, what)
            if why:
                raise lanes_harness.Refused(403, why)

    @app.route('/api/agents/answer', methods=['GET', 'POST'])
    def answer():
        """GET: the agent's answer for the member's screen. POST (a JSON body, signed whole like every POST door): the same, and
        the body may hand the agent what the page asks beside its cards: find (the controller's search, sort and filters), themes
        (each theme a card may wear) and page (the page's own already-loaded logos); each a JSON object, else left out."""
        inside = os.environ.get('LARRYD_INTERNAL') == '1'   # LARRYD RUNTIME INTERNAL (this computer, internal agents): every page's agents answered at once, never one at a time (the owner 2026-11-03: "it loads very slow")
        token = object() if inside else slot.take()   # the slot first, atomically, before any of the agent's code
        if not token:
            return busy()
        run_with = harness_for()
        run_with.on_start = lambda pid: slot.attach(token, pid)   # the run's process group, so a reclaim can kill it whole

        def work():
            d = given('agent_key')
            why = frost_decided(d, f"CALL of {d['agent_key']}", quiet=True)   # the same check as a hire and a RUN (the coordinator, 2026-11-09)
            if why:
                raise lanes_harness.Refused(403, why)
            beside = {k: d[k] for k in lanes_harness.BESIDE if isinstance(d.get(k), dict)} if request.method == 'POST' else {}
            return run_with.answer(*(d[k] for k in NEEDS + ('agent_key',)), beside=beside, handed=d.get('handed') if request.method == 'POST' else None,
                                   act=request.method == 'POST' and d.get('act') is True)   # the member's own confirmed act: only the platform says so, on a POST, as a JSON true
        try:
            return answered(work)
        finally:
            run_with.on_start = None
            if not inside:
                slot.give_back(token)

    @app.post('/api/live/records')
    def live_records():
        """AN AGENT'S ROOM PROGRAM ASKS FOR THE MEMBER'S RECORD (list, add, edit): the body marked with the live key, made within
        the minute; the harness of the slot the member's CALL came through carries it, held to the agent's approved manifest."""
        raw = request.stream.read(live.MOST_ASK + 1)
        ask, why = live.read_ask(raw, request.headers.get('X-Talk-Mark'))
        if ask is None:
            return jsonify({'refused': why}), 401
        run_with = harnesses.get(ask['via'], h) if keys is not None else h
        try:
            return jsonify(run_with.live_records(ask['agent'], ask['account'], ask['scope'], ask['member'], ask['do'], ask['species'], ask['key'], ask['values'])), 200
        except lanes_harness.Refused as no:
            return jsonify({'refused': no.reason}), no.status

    @app.post('/api/agents/hire')
    def hire():
        def work():
            d = given('agent_key', 'on')
            if str(d['on']) not in ('on', 'off'):
                raise lanes_harness.Refused(400, 'on is "on" or "off"')
            granted(d, f"hire of {d['agent_key']}", decided=str(d['on']) == 'on')
            return harness_for().hire(d['account'], d['scope'], d['member'], d['agent_key'], str(d['on']) == 'on')
        return answered(work)

    @app.post('/api/agents/defaults')
    def defaults():
        return answered(lambda: harness_for().defaults(*(given('board')[k] for k in NEEDS + ('board',))))

    def start(account, scope, member, job_key, run, caller=''):
        """-> True started, False already started (anywhere), None the instance is busy (the slot is held).
        Cloud Run: the run is claimed once across every instance, then started as its own Cloud Run job execution; this
        instance answers at once and runs nothing after its answer (no thread, the CPU is the request's only).
        A laptop: the run goes on a thread here, holding the slot (no CPU limit there). In keys mode the run is always
        THE CALLER's (its calls back to that slot): a caller with no harness here is refused before anything is taken."""
        runner = h
        if keys is not None:
            runner = harnesses.get(caller)
            if runner is None:
                raise lanes_harness.Refused(403, f'no harness for the caller {caller!r} here')
        if job_starter is not None:
            if not claims.claim(job_key, run):
                return False
            job_starter.start(['job', caller, account, scope, member, job_key, str(int(run))])
            return True
        with lock:
            if (job_key, run) in running:
                return False
            token = slot.take(f'{job_key}#{run}', run_most)   # the slot is taken here, before the thread exists: named for the log, held for the RUN's own limit
            if not token:
                return None
            running.add((job_key, run))

        def go():
            runner.on_start = lambda pid: slot.attach(token, pid)   # THE RUN'S PROCESS IS ITS SLOT'S (OPERATION BDAY item 1): this thread's own, never another run's
            try:
                runner.run_job(account, scope, member, job_key, run)
            except lanes_harness.Refused as no:   # the platform refused the RUN before its agent ran (already ended: two starts met, the push and the queue walk): said in one line, never a trace
                logging.getLogger('runtime').warning('run %s of %s not started: %s', run, job_key, no.reason)
            except Exception as broke:   # noqa: BLE001  A RUN NEVER HANGS (OPERATION BDAY item 1): any error of the run's own thread ends it FAILED with that error, in one line
                logging.getLogger('runtime').warning('run %s of %s broke: %s: %s', run, job_key, type(broke).__name__, broke)
                runner._end(account, scope, member, '', job_key, run, 'FAILED', f'LARRYD stopped on an error of its own: {type(broke).__name__}: {broke}')
            finally:
                runner.on_start = None
                with lock:
                    running.discard((job_key, run))
                slot.give_back(token)
                kick = app.config.get('drain')
                if kick is not None:   # THE SLOT IS FREE: the queue walked once more, so a chain's next step the platform handed while this run held the slot starts now, not at the next tick
                    kick()
        try:
            threading.Thread(target=go, daemon=True).start()
        except BaseException:
            with lock:
                running.discard((job_key, run))
            slot.give_back(token)
            raise
        return True

    @app.post('/api/jobs/run')
    def run_job():
        try:
            d = given('job_key', 'run')
        except lanes_harness.Refused as no:
            return jsonify({'refused': no.reason}), no.status
        if not str(d['run']).isdigit():
            return jsonify({'refused': 'run is the RUN number'}), 400
        try:
            granted(d, f"RUN {d['run']} of {d['job_key']}")
        except lanes_harness.Refused as no:
            return jsonify({'refused': no.reason}), no.status
        caller = request.headers.get('X-Office-Key', '') if keys is not None else ''
        try:
            started = start(d['account'], d['scope'], d['member'], d['job_key'], int(d['run']), caller)
        except lanes_harness.Refused as no:
            return jsonify({'refused': no.reason}), no.status
        if started is None:
            return busy()
        card = str(d.get('card_key') or '')
        if started and KEY.fullmatch(card):   # THE RUN IS IN FLIGHT FROM THIS MOMENT (its own job starts in up to a minute): written down now, so its agent's page can say so on its very next load
            (harnesses.get(caller) or h).started(card, d['job_key'], int(d['run']), d['account'], d['member'])
        return jsonify({'accepted': d['job_key'], 'run': int(d['run']), 'already': not started}), 202

    @app.post('/api/clock/tick')
    def clock_tick():
        """THE CLOCK'S TICK BY A DOOR (Cloud Run: Cloud Scheduler calls it, signed as every call; this computer ticks in-process):
        each due job whose agent is held and approved is pressed RUN in wid, then the catch-up. -> job keys and words only."""
        return jsonify({'ticked': [{'job_key': k, 'said': w} for k, w in app.config['clocks'].tick(now())]}), 200

    app.config['start'] = start
    app.config['clocks'] = clocks(app)
    if developer:
        _marketplace_pages(app, h, pathlib.Path(instance), secrets.token_hex(16))
    return app


CARD_FILES = ('page.css', 'reference_theme.css', 'view.js')
# the shelf page under a strict policy: no inline style or script anywhere, so a card's look can only arrive by the
# card script's style.setProperty, after its check against the menu
STRICT = ("default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' data:; form-action 'self'; "
          "base-uri 'none'; frame-ancestors 'none'")


def _strict(body, status=200):
    from flask import make_response
    response = make_response(body, status)
    response.headers['Content-Security-Policy'] = STRICT
    return response


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
            return _strict(render_template('marketplace.html', refused=why.reason, token=token, marketplace_key=preview.MARKETPLACE_KEY), why.status)
        return _strict(render_template('marketplace.html', A=answer, hidden=not_shown, no=request.args.get('no', ''), token=token,
                                       marketplace_key=preview.MARKETPLACE_KEY))

    @app.get('/marketplace/<name>')
    def marketplace_file(name):
        """The card template's own files: its sheet and script, the page's sheet, the reference theme."""
        if name not in CARD_FILES:
            return refused('no such file')
        return send_from_directory(pathlib.Path(__file__).resolve().parent, name, max_age=0)

    @app.get('/marketplace/view.css')
    def marketplace_view_sheet():
        """The marketplace's own sheet (its marketplace.css, in its view), served from this origin: the page's policy allows no inline style."""
        if mine():
            return refused(mine())
        try:
            answer, _not_shown = collection()
        except lanes_harness.Refused as why:
            return jsonify({'refused': why.reason}), why.status
        return Response((answer.get('view') or {}).get('css', ''), mimetype='text/css', headers={'Cache-Control': 'no-store'})

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
        h.forget_approved()   # the developer's runtime approves what it holds: the placed agent shows on the next call
        return jsonify({'held': {'agent_key': key, 'name': row['name'], 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']},
                        'marketplace': '/marketplace'}), 201


SLOT_ENV = 'LARRYD_SLOT'   # the slot an operator's place, submit or review is for, when --slot is not given (the door's configured slot)


def harness_for_slot(app, slot=''):
    """The harness whose platform client reaches THE SLOT an agent is for. On Cloud Run (keys mode) the runtime has no
    platform address of its own, only one client per slot signed with its key for that slot: the slot must be named
    (--slot, or LARRYD_SLOT) and known, or nothing is done. On a laptop (no slots) the one harness."""
    harnesses = app.config['harnesses']
    if not harnesses:
        return app.config['harness']
    slot = slot or os.environ.get(SLOT_ENV, '')
    if not slot:
        raise SystemExit(f'name the slot this agent is for (--slot <slot> or {SLOT_ENV}): one of {", ".join(sorted(harnesses))}')
    if slot not in harnesses:
        raise SystemExit(f'no slot {slot}: the slots are {", ".join(sorted(harnesses))}')
    return harnesses[slot]


def place(app, agent_key, data, role='', slot=''):
    """An approved agent file into the locker (<intake folder>/<key>/, or marketplace/<key>/ for the marketplace role): the first
    guard. Then to the platform's wid (its card written, PENDING until the platform's review, FROST's, approves these exact hashes:
    the second guard) through the slot it is for (harness_for_slot). -> what was held, and wid's answer or why wid did not take it (the agent
    stays held; `submit <key>` sends it again)."""
    h, conf = harness_for_slot(app, slot), CONFIG['intake']   # refused before anything is held when no slot is named
    try:
        files = intake.check(intake.from_zip(data, conf['most_files'], conf['most_bytes']), conf['most_files'], conf['most_bytes'])
        group = lanes_harness.MARKETPLACE if role == 'marketplace' else conf['folder']   # the marketplace keeps its own folder (as the bucket's sync files it)
        row = intake.receive(h.db, h.agents, group, agent_key, files)
    except intake.Refused as no:
        raise SystemExit(f'refused ({no.status}): {no.reason}')
    held = {'agent_key': agent_key, 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']}
    if app.config.get('lockers') is not None:   # Cloud Run: the approved package is kept in the lockers bucket, read by every instance
        app.config['lockers'].publish(agent_key, row, data, role=role)
    try:
        review = h.submit(agent_key)
    except lanes_harness.Refused as no:
        return {**held, 'refused': f'held in the locker, but wid did not take it: {no.reason}; send it again with submit {agent_key}'}
    card_key = str(review.get('card_key') or '')
    if KEY.fullmatch(card_key):   # BOTH KEYS LINKED (the owner, 2026-10-06): the platform minted its card's key at submission
        locker.link(h.db, agent_key, card_key)
        if app.config.get('lockers') is not None:
            app.config['lockers'].link(agent_key, card_key)
    return {**held, 'review': review}


def place_in_place(app, agent_key, where, kits=None, slot=''):
    """THE PLACE, IN PLACE (LARRYD_INTERNAL=1 and LARRYD_LOCKER, core_engine/locker.in_place): the agent is held where it is,
    <LARRYD_LOCKER>/<name>/agent (where: that folder, or <name>, or its path), its kits written into it first (kits: their folder;
    by default the locker's own _office), nothing copied into instance/. Then to wid as place does (its card PENDING until FROST's
    review approves these exact hashes). -> what was held, and wid's answer or why wid did not take it."""
    h, conf, root = harness_for_slot(app, slot), CONFIG['intake'], locker.in_place()
    path = pathlib.Path(where).expanduser()
    path = path if path.is_absolute() or path.exists() else root / path
    path = path / 'agent' if (path / 'agent').is_dir() else path
    if kits is None and (root / '_office').is_dir():
        kits = root / '_office'
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        raise SystemExit(f'refused (400): {where} is not inside the locker {root}')
    try:
        row = intake.hold_in_place(h.db, root, agent_key, rel.as_posix(), conf['most_files'], conf['most_bytes'], kits=kits)
    except intake.Refused as no:
        raise SystemExit(f'refused ({no.status}): {no.reason}')
    held = {'agent_key': agent_key, 'folder': row['folder'], 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']}
    try:
        review = h.submit(agent_key)
    except lanes_harness.Refused as no:
        return {**held, 'refused': f'held in the locker, but wid did not take it: {no.reason}; send it again with submit {agent_key}'}
    card_key = str(review.get('card_key') or '')
    if KEY.fullmatch(card_key):   # BOTH KEYS LINKED, as place
        locker.link(h.db, agent_key, card_key)
    return {**held, 'review': review}


def warm_up(app, shake=None, sleep=None, then=None):
    """Cloud Run, at start (the service) or before a run (a job execution): the warm-up handshakes to every slot with a
    callback address, then `then` (the service's catch-up: still inside the start-up, where the instance has its CPU),
    then the app is ready. -> the warm-up's result."""
    kw = {'shake': shake or warmup.handshake, **({'sleep': sleep} if sleep else {})}
    try:
        result = warmup.warm(warmup.hosts(CONFIG['slots']), **kw)
        if then is not None:
            then(app)
    finally:
        app.config['ready'].set()
    return result


NOT_GRANTED = 'the platform did not grant this member access'


def access_granted(d):
    """THE SECOND GUARD (the owner: two guards, never one): the platform's own access decision for the member, carried
    in a hire's or run's signed body and in each queued run (runtime.json "access"): only the value that grants passes."""
    return str(d.get(CONFIG['access']['field']) or '') == CONFIG['access']['grants']


def frost_decided(d, what, quiet=False):
    """FROST'S SIGNED DECISION (core_engine/decision.py), checked on every CALL, hire and RUN: '' verified, else the refusal. Said in
    the log in one line, by keys only (never a member or a record: data stays in wid); quiet: a verified CALL is not said (a page
    asks every agent on it at each load), its refusal always is."""
    why = decision.why_not(d)
    if why:
        logging.getLogger('runtime').warning('FROST decision refused for %s: %s', what, why)
    elif not quiet:
        logging.getLogger('runtime').warning('FROST decision verified for %s (card %s)', what, d.get('card_key') or '?')
    return why


def catch_up(app, wait=None, sleep=time.sleep):
    """At start, once (never a loop): the RUNs the platform queued while the runtime was away. On Cloud Run every
    slot's queue is read, and each run is claimed once across every instance before it starts (two new instances never
    start the same run). A queued run without the platform's access decision is ended REFUSED, never started.
    wait (seconds, the drain's): a run met while the one slot is held waits for it, up to that long, so the queue is walked
    one run after another (ONE RUN PER INSTANCE kept); without it, a busy slot leaves that run QUEUED in the platform."""
    status = 0
    sources = list(app.config['harnesses'].items()) or [('', app.config['harness'])]
    for caller, h in sources:
        began = time.monotonic()
        status, body = h.client.get('wid', '/jobs/queued', {'runtime': 'internal'} if os.environ.get('LARRYD_INTERNAL') == '1' else None)   # THE TWO RUNTIMES: each is handed its own queue (the external one's as before, None)
        if caller:   # the instance's first call back to that slot: its answer and how long it took (no data)
            logging.getLogger('runtime').warning('catch-up: %s answered %s in %.1f s', caller, status, time.monotonic() - began)
        queue = body.get('jobs', []) if status == 200 else []
        checked = [(j, NOT_GRANTED if not access_granted(j) else frost_decided(j, f"RUN {j['run']} of {j['job_key']}")) for j in queue]   # every run checked as the queue is read (a decision is fresh now, not after the runs before it)
        for j, why in checked:
            if why:   # the second guard and FROST's signed decision on this path too: ended REFUSED (told and recorded), never started
                h._end(j['account'], j['scope'], j['member'], '', j['job_key'], int(j['run']), 'REFUSED', why)
                continue
            args = (j['account'], j['scope'], j['member'], j['job_key'], int(j['run']), caller)
            started, until = app.config['start'](*args), time.monotonic() + (wait or 0)
            while started is None and wait and time.monotonic() < until:   # THE ONE SLOT IS HELD: wait for it (the drain only)
                sleep(1)
                started = app.config['start'](*args)
    return status


class Drain:
    """THE QUEUE WALKED TO ITS END (2026-11-09: the clock pressed 42 Scrum Master 3 blocks, the runtime started 2 and left
    40 QUEUED until the platform closed them). One thread at a time walks the platform's queue (catch_up with wait); a
    call while it walks marks it to read the queue once more when it ends, so a run queued meanwhile is never left behind."""

    def __init__(self, app, wait, thread=threading.Thread):
        self.app, self.wait, self.thread = app, wait, thread
        self.lock, self.busy, self.again = threading.Lock(), False, False

    def __call__(self):
        with self.lock:
            if self.busy:
                self.again = True
                return False
            self.busy, self.again = True, False
        self.thread(target=self._walk, daemon=True).start()
        return True

    def _walk(self):
        while True:
            try:
                catch_up(self.app, wait=self.wait)
            except Exception:   # a walk that failed is logged; the next tick's press calls the drain again
                logging.getLogger('runtime').exception('drain: the queue walk failed')
            with self.lock:
                if not self.again:
                    self.busy = False
                    return
                self.again = False


OPEN_FILES = 4096   # the runtime's open files, at least: launchd starts it with 256 (open_files)


def open_files(at_least=OPEN_FILES):
    """THE RUNTIME'S OPEN FILES (the owner 2026-11-10, "we need it all healthy and working"): launchd starts the runtime
    with 256 open files; a board's page has it draw every agent's view together and each view asks wid back, every call a
    socket, so the same limit that silenced wid at 02:00 (its "Too many open files") stands here. The runtime raises its
    own soft limit to at_least as it starts, never above the hard one, never lowering one already higher; a kernel that
    refuses leaves it as it stood -> (before, after)."""
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    want = at_least if hard == resource.RLIM_INFINITY else min(at_least, hard)
    if soft < want:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))
        except (ValueError, OSError):
            pass
    return soft, resource.getrlimit(resource.RLIMIT_NOFILE)[0]


def clocks(app):
    """THE CLOCK READER (core_engine/clock.py) over the same sources as the catch-up: one clock per slot's harness (its wid, its
    verify), the catch-up run once after a tick that queued a RUN. The same on both runtimes; LARRYD_INTERNAL=1 asks wid for the
    internal jobs, as the catch-up does."""
    inside = os.environ.get('LARRYD_INTERNAL') == '1'
    sources = list(app.config['harnesses'].values()) or [app.config['harness']]
    drain = Drain(app, wait=CONFIG['run']['seconds'] + 60)   # a held slot is waited for up to the run's hard limit plus the slot's margin
    app.config['drain'] = drain
    return clock.Clocks([clock.Clock(clock.WidJobs(h.client, internal=inside), h.verify_now, clock.Memory(h.db)) for h in sources],
                        then=drain)


def locker_root(instance):
    """Where the agents are kept: the instance's own agents/ folder when there is one (a server: it outlives every release
    of the code), else the code's (the laptop)."""
    held = pathlib.Path(instance) / 'agents'
    return held if held.is_dir() else APP / 'agents'


def cloud_parts():
    """Cloud Run's parts, named by its environment (the Dockerfile and the service), or None on a laptop."""
    if not os.environ.get('LARRYD_KEYS_DIR'):
        return None
    out = os.environ.get('LARRYD_OUTBOUND_DIR')
    return {'outbound': callers.Outbound(out) if out else None,
            'records': run_records.FirestoreRecords() if os.environ.get('LARRYD_RECORDS') == 'firestore' else None,
            'lockers': bucket_lockers.BucketLockers(os.environ['LARRYD_LOCKERS']) if os.environ.get('LARRYD_LOCKERS') else None,
            'claims': long_runs.FirestoreClaims() if os.environ.get('LARRYD_JOB') else None,
            'jobs': long_runs.from_environment()}


def main(argv):
    """python runtime/app/web/app.py                                   the host
    python runtime/app/web/app.py submit <key> [--slot <slot>]        an agent the runtime holds, to the platform's wid (its key, its exact hashes, its manifest)
    python runtime/app/web/app.py place <card key> <file.larryd> [marketplace] [--slot <slot>]   an agent the owner approved: into the locker (and, on Cloud Run, the lockers bucket), then to the platform's wid
    python runtime/app/web/app.py place <card key> <folder> [--kits <folder>] [--slot <slot>]   LARRYD_INTERNAL=1 and LARRYD_LOCKER: the agent held in place, <LARRYD_LOCKER>/<name>/agent, its kits written into it
    python runtime/app/web/app.py adopt <card key> <name> [--slot <slot>]   LARRYD_INTERNAL=1 and LARRYD_LOCKER: a copy held in instance/agents moved to <name>/agent in place, on its approved hashes
    python runtime/app/web/app.py review <card key>... [--slot <slot>]   what the runtime records for those agents, with the platform's word on the hashes it holds
    python runtime/app/web/app.py remove <key> [--slot <slot>]        a placed agent taken out of the locker, only when the platform's word on its exact hashes is revoked
      (on Cloud Run --slot, or LARRYD_SLOT, names the slot whose wid is asked: slot-a, slot-b or proof)
    python runtime/app/web/app.py job <slot> <account> <scope> <member> <job key> <run>   a Cloud Run job execution: one RUN, its result to that slot
    python runtime/app/web/app.py callbacks <slot> <n>                Cloud Run: the warm-up, the first call back to that slot and n more (statuses and times)
    python runtime/app/web/app.py selftest                            Cloud Run: the marketplace agent run once in the sandbox, its record written"""
    side = os.environ.get(CONFIG['environment_variable'], 'localhost.rnd').split('.')[-1]
    secret_file = INSTANCE / 'secrets' / CONFIG['secret']['name']
    secret = secret_file.read_text().strip() if secret_file.is_file() else ''
    keys_dir = os.environ.get('LARRYD_KEYS_DIR')   # Cloud Run: the callers' keys, one folder each (the hardened call)
    cloud = cloud_parts()
    here = locker.in_place()   # THE LOCKER IN PLACE (LARRYD_INTERNAL=1 and LARRYD_LOCKER): every agent held where it is, none in instance/
    if here is not None and not here.is_dir():
        raise SystemExit(f'{locker.IN_PLACE} names no folder: {here}')
    app = create_app(INSTANCE, secret, retry_seconds=RETRY_IN_JOB if argv[1:2] == ['job'] else RETRY_IN_REQUEST, addresses=platform.addresses(CONFIG, side, INSTANCE) if not cloud else {},
                     agents=here or ((INSTANCE / 'agents') if cloud and cloud.get('lockers') else locker_root(INSTANCE)),
                     developer=os.environ.get(DEVELOPER) == '1',
                     keys=callers.Keys(keys_dir) if keys_dir else None, nonces=callers.nonces() if keys_dir else None, cloud=cloud)
    slot = ''
    if '--slot' in argv[2:]:   # place, submit, review: the slot whose wid is asked
        at = argv.index('--slot')
        if at + 1 >= len(argv):
            raise SystemExit('--slot needs a slot name')
        slot, argv = argv[at + 1], argv[:at] + argv[at + 2:]
    kits = None
    if '--kits' in argv[2:]:   # place in place: the folder of the kits written into the agent (default: the locker's _office)
        at = argv.index('--kits')
        if at + 1 >= len(argv):
            raise SystemExit('--kits needs a folder')
        kits, argv = pathlib.Path(argv[at + 1]).expanduser(), argv[:at] + argv[at + 2:]
    if here is not None and argv[1:2] == ['place']:   # IN PLACE: a folder in the locker, never a .larryd file unpacked into it
        if len(argv) != 4 or not pathlib.Path(argv[3]).expanduser().is_dir() and not (here / argv[3]).is_dir():
            raise SystemExit(f'in place: place <card key> <the agent\'s folder in {here}> [--kits <folder>] [--slot <slot>]')
        print(json.dumps(place_in_place(app, argv[2], argv[3], kits=kits, slot=slot)))
        return
    if here is not None and argv[1:2] == ['adopt'] and len(argv) == 4:   # THE ONE-TIME MOVE: a held copy in instance/agents adopted in place, its approved hashes kept
        db = harness_for_slot(app, slot).db
        try:
            row = locker.adopt(db, INSTANCE / 'agents', here, argv[2], argv[3] if (here / argv[3] / locker.MANIFEST).is_file() else f'{argv[3]}/agent')
        except ValueError as why:
            raise SystemExit(f'refused: {why}')
        print(json.dumps({'agent_key': argv[2], 'folder': row['folder'], 'code_sha256': row['code_sha256'], 'manifest_sha256': row['manifest_sha256']}))
        return
    if argv[1:2] == ['place'] and len(argv) in (4, 5):
        print(json.dumps(place(app, argv[2], pathlib.Path(argv[3]).read_bytes(), role=argv[4] if len(argv) == 5 else '', slot=slot)))
        return
    if argv[1:2] == ['review'] and len(argv) >= 3:
        print(json.dumps(harness_for_slot(app, slot).review_state(argv[2:])))
        return
    if argv[1:2] == ['remove'] and len(argv) == 3:
        if app.config.get('lockers') is not None:   # Cloud Run: the lockers bucket keeps the package too; this command never leaves it half done
            raise SystemExit('refused: on Cloud Run the lockers bucket keeps the agent too; remove it where its locker is a folder')
        got = harness_for_slot(app, slot).remove(argv[2])
        if 'refused' in got:
            raise SystemExit(f"refused: {got['refused']}")
        print(json.dumps(got))
        return
    if argv[1:2] == ['submit'] and len(argv) == 3:
        try:
            review = harness_for_slot(app, slot).submit(argv[2])
        except lanes_harness.Refused as no:
            raise SystemExit(f'refused ({no.status}): {no.reason}')
        card_key = str(review.get('card_key') or '')
        if KEY.fullmatch(card_key):   # BOTH KEYS LINKED here too (PF Virtual Wire, 2026-10-08: sent again by its key, its card was approved and never shown: the bucket held no card.json)
            locker.link(harness_for_slot(app, slot).db, argv[2], card_key)
            if app.config.get('lockers') is not None:
                app.config['lockers'].link(argv[2], card_key)
        print(json.dumps(review))
        return
    if argv[1:2] == ['job'] and len(argv) == 8:
        _slot, account, scope, member, job_key, run = argv[2:]
        h = app.config['harnesses'].get(_slot)
        if h is None:
            raise SystemExit('no such slot')
        if keys_dir:
            print(json.dumps({'warm_up': warm_up(app)}))   # the same warm-up as the service, before the run calls back
        state = h.run_job(account, scope, member, job_key, int(run))
        print(json.dumps({'job_key': job_key, 'run': int(run), 'state': state}))
        return
    if argv[1:2] == ['callbacks'] and len(argv) == 4:   # the proof: a cold execution's first call back, then n more
        print(json.dumps(callbacks(app, argv[2], int(argv[3]))))
        return
    if argv[1:2] == ['selftest']:
        print(json.dumps(selftest(app)))
        return
    if len(argv) > 1:
        raise SystemExit(main.__doc__)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)   # no request lines: a call's query names an account and a member (data stays in wid)
    if keys_dir:   # Cloud Run: the instance listens at once; /ready answers only after the warm-up and the catch-up
        threading.Thread(target=warm_up, args=(app,), kwargs={'then': catch_up}, daemon=True).start()
    else:
        catch_up(app)
    if os.environ.get('LARRYD_INTERNAL') == '1':   # THIS COMPUTER: the clock ticks in-process every 60 s (Cloud Run ticks it through /api/clock/tick)
        app.config['clocks'].start()
    before, after = open_files()   # THE RUNTIME'S OPEN FILES: raised as it starts, said in its log
    logging.getLogger('runtime').warning('open files: %d -> %d', before, after)   # the runtime's log says what it did
    app.run(host=os.environ.get('LARRYD_HOST') or CONFIG['host'], port=int(os.environ.get('PORT') or os.environ.get('LARRYD_PORT') or CONFIG['ports'][side]),
            threaded=True)   # 127.0.0.1, except in a container (Cloud Run names LARRYD_HOST and PORT)


def callbacks(app, caller, n):
    """THE CALLBACK PROOF (a Cloud Run job execution, cold): the warm-up, then the first call back to that slot
    (wid's queue, a read: nothing written into the platform), then n more. -> the warm-up, each answer's status and
    time (any answer from the slot, even a refusal, proves the way back is open). Statuses and times only, never a body."""
    h = app.config['harnesses'].get(caller)
    if h is None:
        raise SystemExit('no such slot')
    began = time.monotonic()
    out = {'warm_up': warm_up(app)}
    tries = []
    for _ in range(n + 1):
        t = time.monotonic()
        status, _body = h.client.get('wid', '/jobs/queued')
        tries.append((status, round((time.monotonic() - t) * 1000)))
    first, rest = tries[0], tries[1:]
    return {**out, 'first_call_back': {'status': first[0], 'ms': first[1], 'after_start_s': round(time.monotonic() - began - sum(ms for _, ms in rest) / 1000, 1)},
            'steady': {'answered': sum(1 for st, _ in rest if st), 'of': n, 'statuses': sorted({st for st, _ in rest}),
                       'p50_ms': sorted(ms for _, ms in rest)[len(rest) // 2] if rest else None}}


def selftest(app):
    """The proof that an agent really runs here (the review's M5): the image's own marketplace agent, run once in the
    sandbox with an empty collection, and its record written where this runtime writes them (Firestore on Cloud Run).
    Nothing is placed in the lockers bucket for it: the bucket holds approved agents only."""
    h = app.config['harness']
    folder = APP / 'agents' / 'marketplace'
    manifest = json.loads((folder / 'agent.json').read_text())
    state, answer, reason = sandbox.run(folder, manifest['entry'], {'do': (manifest.get('calls') or ['collection'])[0], 'cards': []}, h.seconds)
    h.records.record('selftest', '', state, reason, caller='selftest')   # no platform key: the image's own agent
    return {'state': state, 'reason': reason, 'answer_keys': sorted(answer) if isinstance(answer, dict) else []}

if __name__ == '__main__':
    main(sys.argv)
