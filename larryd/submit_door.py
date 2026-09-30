"""LARRYD'S SUBMIT DOOR, on the larryd machine under /submit/ (behind nginx, 127.0.0.1). Nothing to paste, nothing to
keep on the developer's side: `larryd submit` sends one file; the developer signs in with Google or Apple (through the
SSO proxy) to claim it; it waits in the review queue.
  POST /submit/upload              the file (a zip of agent/), unsigned. Refused before anything is kept: over the size
                                   cap, over the address's hourly limit, not a safe zip, or the doctor (re-run here, reading
                                   only: nothing sent is ever run) finds a problem. Kept: held for 10 minutes under a
                                   random id; the answer is its claim page.
  GET  /submit/claim/<id>          the claim page: the agent's name and hash, Sign in with Google or Apple.
  GET  /submit/start/<id>/<provider>   this browser bound; to the proxy with this door's own one-time state and nonce.
  POST /submit/signed-in           the proxy's signed hand-off: its key, issuer, this origin, its minute, the state once,
                                   the nonce, the browser; then the held file moves into the queue with who sent it.
Anything held longer than 10 minutes is deleted (on every request; there is no loop). The address is kept only as a
hash, for an hour, for the limit."""
import hashlib
import html
import json
import os
import pathlib
import secrets
import shutil
import sqlite3
import tempfile
import time
from importlib import resources
from urllib.parse import urlencode

from flask import Flask, Response, redirect, request

from . import bundle, doctor, sso_handoff

CONFIG = json.loads(resources.files('larryd').joinpath('submit_door.json').read_text())
BIND = 'larryd_submit_bind'
PROVIDERS = {'google': 'Google', 'apple': 'Apple'}
TABLES = (
    'CREATE TABLE IF NOT EXISTS held (id TEXT PRIMARY KEY, name TEXT NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL, '
    'made_at INTEGER NOT NULL, state TEXT UNIQUE, nonce TEXT, provider TEXT)',
    'CREATE TABLE IF NOT EXISTS queue (id TEXT PRIMARY KEY, name TEXT NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL, '
    'provider TEXT NOT NULL, sub TEXT NOT NULL, email TEXT NOT NULL, submitted_at INTEGER NOT NULL, review TEXT NOT NULL, note TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS hits (address TEXT NOT NULL, at INTEGER NOT NULL)',
)


def _page(title, body, status=200):
    doc = (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
           f'<title>{html.escape(title)} · LARRYD</title><body style="font:16px/1.5 system-ui,sans-serif;max-width:36rem;margin:3rem auto;padding:0 1rem">'
           f'<h1 style="font-size:1.4rem">{html.escape(title)}</h1>{body}</body></html>')
    answer = Response(doc, status=status, mimetype='text/html')
    answer.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; form-action 'none'; base-uri 'none'"
    return answer


def _said(text, status):
    return Response(json.dumps(text) + '\n', status=status, mimetype='application/json')


def binding(state):
    return hashlib.sha256(('larryd-submit ' + state).encode('utf-8')).hexdigest()


def create_app(instance, config=None, now=time.time):
    conf = config or CONFIG
    instance = pathlib.Path(instance)
    for folder in (instance, instance / 'held', instance / 'queue'):
        folder.mkdir(parents=True, exist_ok=True)
        os.chmod(folder, 0o700)
    db = instance / conf['database']
    con = sqlite3.connect(db)
    with con:
        for table in TABLES:
            con.execute(table)
    con.close()
    public_key = conf['proxy']['public_key'].encode('utf-8')
    app = Flask('larryd_submit')
    app.config['MAX_CONTENT_LENGTH'] = bundle.MOST_BYTES   # the cap, before the body is read

    def connect():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def forget_old():
        """Held files past their 10 minutes, and addresses past their hour: gone."""
        at = int(now())
        c = connect()
        with c:
            old = [r['id'] for r in c.execute('SELECT id FROM held WHERE made_at < ?', (at - conf['hold_seconds'],))]
            c.execute('DELETE FROM held WHERE made_at < ?', (at - conf['hold_seconds'],))
            c.execute('DELETE FROM hits WHERE at < ?', (at - 3600,))
        c.close()
        for i in old:
            (instance / 'held' / f'{i}.larryd').unlink(missing_ok=True)

    def address():
        """The sender's address as a hash (behind nginx, the one it sets; never kept as itself)."""
        real = request.headers.get('X-Forwarded-For', '') if request.remote_addr in ('127.0.0.1', '::1') else ''
        return hashlib.sha256(('larryd-submit ' + (real or request.remote_addr or '')).encode()).hexdigest()

    @app.before_request
    def tidy():
        forget_old()

    @app.after_request
    def no_store(answer):
        answer.headers['Cache-Control'] = 'no-store'
        answer.headers['Referrer-Policy'] = 'no-referrer'
        answer.headers['X-Content-Type-Options'] = 'nosniff'
        return answer

    @app.errorhandler(413)
    def too_big(_):
        return _said({'refused': f'the file is larger than {bundle.MOST_BYTES} bytes'}, 413)

    @app.post('/submit/upload')
    def upload():
        who, at = address(), int(now())
        c = connect()
        with c:
            seen = c.execute('SELECT COUNT(*) FROM hits WHERE address = ? AND at >= ?', (who, at - 3600)).fetchone()[0]
            c.execute('INSERT INTO hits VALUES (?, ?)', (who, at))
        c.close()
        if seen >= conf['uploads_per_address_per_hour']:
            return _said({'refused': f"more than {conf['uploads_per_address_per_hour']} files from this address in an hour: try again later"}, 429)
        data = request.get_data(cache=False)
        scratch = pathlib.Path(tempfile.mkdtemp(prefix='larryd_submit_'))
        try:
            wrong = bundle.open_safely(data, scratch)
            if wrong:
                return _said({'refused': 'not a safe agent file', 'problems': wrong}, 400)
            problems = doctor.check(scratch)
            if problems:
                return _said({'refused': 'the doctor found problems', 'problems': [doctor.asdict(p) for p in problems]}, 422)
            name = json.loads((scratch / 'agent' / 'agent.json').read_text())['name']
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        held = secrets.token_urlsafe(24)
        path = instance / 'held' / f'{held}.larryd'
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        c = connect()
        with c:
            c.execute('INSERT INTO held (id, name, sha256, size, made_at) VALUES (?, ?, ?, ?, ?)',
                      (held, str(name)[:80], hashlib.sha256(data).hexdigest(), len(data), at))
        c.close()
        return _said({'claim': f"{conf['origin']}/submit/claim/{held}", 'minutes': conf['hold_seconds'] // 60}, 201)

    def held_row(held):
        c = connect()
        row = c.execute('SELECT * FROM held WHERE id = ?', (held,)).fetchone()
        c.close()
        return row

    def gone():
        return _page('Not here', '<p>This file is not waiting here: it was claimed, or ten minutes went by. Run <code>larryd submit</code> again.</p>', 404)

    @app.get('/submit/claim/<held>')
    def claim(held):
        row = held_row(held)
        if row is None:
            return gone()
        links = ' '.join(f'<p><a href="/submit/start/{html.escape(held)}/{p}">Sign in with {n} to submit</a></p>' for p, n in PROVIDERS.items())
        return _page(f'Submit {row["name"]}',
                     f'<p>Your agent <strong>{html.escape(row["name"])}</strong> is here, checked by the doctor.<br>'
                     f'Its file: <code>{row["sha256"][:16]}</code> ({row["size"]} bytes).</p>'
                     f'<p>Sign in so we know who sent it. We keep your name from the sign-in and your email, to tell you the review\'s answer.</p>{links}')

    @app.get('/submit/start/<held>/<provider>')
    def start(held, provider):
        row = held_row(held)
        if row is None:
            return gone()
        if provider not in PROVIDERS:
            return _page('Not a sign-in', '<p>Sign in with Google or Apple.</p>', 404)
        state, nonce = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
        c = connect()
        with c:
            c.execute('UPDATE held SET state = ?, nonce = ?, provider = ? WHERE id = ?', (state, nonce, provider, held))
        c.close()
        query = {'provider': provider, 'state': state, 'nonce': nonce, 'back': conf['origin'] + '/submit/signed-in'}
        answer = redirect(conf['proxy']['start'] + '?' + urlencode(query))
        answer.set_cookie(BIND, binding(state), max_age=conf['hold_seconds'], secure=True, httponly=True, samesite='Lax', path='/submit/signed-in')
        return answer

    @app.post('/submit/signed-in')
    def signed_in():
        state = request.form.get('state', '')
        kept = request.cookies.get(BIND, '')
        if not state or not kept or not secrets.compare_digest(kept, binding(state)):
            return _page('Start again', '<p>This sign-in came back to another browser, or it was not started here. Open the claim page again.</p>', 400)
        try:
            given = sso_handoff.verify(public_key, request.form.get('handoff', ''),
                                       conf['proxy']['issuer'], conf['origin'], now())
        except sso_handoff.Refused:
            return _page('Start again', '<p>The sign-in did not come back as it should. Open the claim page again.</p>', 400)
        c = connect()
        with c:
            row = c.execute('SELECT * FROM held WHERE state = ?', (state,)).fetchone()
            if row is not None:
                c.execute('DELETE FROM held WHERE id = ?', (row['id'],))   # one use
        c.close()
        if row is None or given['state'] != state or given['nonce'] != row['nonce'] or given['provider'] != row['provider']:
            return _page('Start again', '<p>This sign-in is not the one started for this file, or it was used already.</p>', 400)
        queued = secrets.token_urlsafe(12)
        os.replace(instance / 'held' / f"{row['id']}.larryd", instance / 'queue' / f'{queued}.larryd')
        c = connect()
        with c:
            c.execute('INSERT INTO queue VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (queued, row['name'], row['sha256'], row['size'], given['provider'], given['sub'], given['email'], int(now()), 'waiting', ''))
        c.close()
        answer = _page('Submitted',
                       f'<p><strong>{html.escape(row["name"])}</strong> (<code>{row["sha256"][:16]}</code>) is in the review queue.</p>'
                       f'<p>What happens next: a person at LARRYD reviews it. The answer goes to '
                       f'<strong>{html.escape(given["email"] or "the email of your sign-in")}</strong>. You can close this page.</p>')
        answer.delete_cookie(BIND, path='/submit/signed-in', secure=True, httponly=True, samesite='Lax')
        return answer

    return app


def main(argv):
    """python -m larryd.submit_door list     the review queue (on the larryd machine; LARRYD_SUBMIT_INSTANCE)"""
    instance = pathlib.Path(os.environ.get('LARRYD_SUBMIT_INSTANCE') or 'instance')
    if argv == ['list']:
        c = sqlite3.connect(instance / CONFIG['database'])
        for r in c.execute('SELECT id, name, sha256, provider, email, submitted_at, review FROM queue ORDER BY submitted_at'):
            print(' · '.join(str(x) for x in r))
        return 0
    raise SystemExit(main.__doc__)


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
