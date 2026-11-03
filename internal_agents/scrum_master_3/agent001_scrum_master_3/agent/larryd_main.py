"""SCRUM MASTER 3'S AGENT IN LARRYD RUNTIME INTERNAL (moved 2026-11-03 from ~/virtual_sanity/scrum_master_3: the owner, "all virtual
sanity agents will use 1 single internal larryd run"; "and rip it out of the virtual sanity"). The office's own code moved whole into
this agent folder (scrum_master_3/app: its agent program and the MARK IV agent, its web/ page parts and templates, the frame), never
rewritten; its state lives in LARRYD RUNTIME INTERNAL's data (~/larryd/server/runtime/internal/instance/data/scrum_master_3).

A CALL draws what the office's /internal/view drew for this agent: the office's own home() with answers_only, this agent's canvas
taken from it (web/app.py internal_view), carried into a LARRYD view (larryd_view.carried). Drawing places nothing (the office's page
start placed its shells; a canvas never rewrites them).
A RUN does what the office's /internal/run did for it: its own module.run(store, job_key, n, agent, shells, chain) (web/app.py
run_internal), the run's end handed back as this answer's delivery instead of the office's POST to wid (/jobs/internal/result)."""
import io
import json
import os
import sys
import threading

import larryd_view   # beside this file: imported before the office's app takes the path (its agent/ package, never this folder's agent.py)

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, 'scrum_master_3', 'app')
DATA = os.path.expanduser('~/larryd/server/runtime/internal/instance/data/scrum_master_3')
OFFICE_PY = os.path.expanduser('~/virtual_workspace/.venv/bin/python')   # the office's own interpreter (its launcher's PY: flask and the platform's pipeline)


def _own_interpreter():
    if os.path.isfile(OFFICE_PY) and os.path.realpath(sys.executable) != os.path.realpath(OFFICE_PY) and not os.environ.get('SM3_INTERNAL_REEXEC'):
        os.environ['SM3_INTERNAL_REEXEC'] = '1'
        os.execv(OFFICE_PY, [OFFICE_PY, '-B', os.path.join(HERE, 'agent.py')])


def _office_env():
    os.environ['REPLICA_OFFICE_APP'] = APP          # the office it serves: its app, in this folder (agent/run's REPLICA_OFFICE_APP)
    os.environ['REPLICA_INSTANCE'] = DATA           # its instance: LARRYD RUNTIME INTERNAL's data, never ~/virtual_sanity
    os.environ['SCRUM_MASTER_INSTANCE'] = os.path.join(DATA, 'release')   # the release tools' own instance (shared_store)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ.setdefault('WID_ENV', 'localhost.rnd')
    sys.dont_write_bytecode = True
    sys.path[:] = [p for p in sys.path if os.path.realpath(p or '.') != os.path.realpath(HERE)]
    sys.path.insert(0, APP)                          # agent/run's PYTHONPATH: its app (frame/ copied into it)


def _module(file):
    import importlib
    return importlib.import_module('agent.' + file[:-3])


def _office(agent_file, write_ok):
    """The office's page objects, as web/app.py create() makes them, for the MARK IV agent and this agent alone."""
    from frame import frame_replica as frame
    if not write_ok:   # A CANVAS PLACES NOTHING: the shells as the office's page start placed them
        for name in ('add', 'add_job', 'agent', 'set_job', 'remove', 'remove_job', 'move', 'wire'):
            setattr(frame.Shells, name, lambda self, *a, **k: None)
    from web import app as office
    mark_iv = office.MARK_IV
    module = _module(agent_file)
    agents = [mark_iv] if module is mark_iv else [mark_iv, module]
    return frame, office, mark_iv, module, agents


def call(given, agent_file):
    with _quiet():
        frame, office, mark_iv, module, agents = _office(agent_file, write_ok=False)
        app = office.create(office.PAGE['store'], frame.agent(), agents=agents)
        from flask import g
        page = given.get('page') if isinstance(given.get('page'), dict) else {}
        with app.test_request_context('/'):
            layer = str(given.get('agentlayer') or '')
            g.lang = 'en'
            g.carry = {'agentlayer': layer if layer in office.LAYERS else office.PAGE['agentlayer'], 'mode': ''}
            g.answers_only = True
            answers = app.view_functions['home']()
            door = frame.Door(frame.NAME)
            agent = frame.agent() or {}
            key = door.card_key(agent['name']) if module is mark_iv else door.card_key(getattr(module, 'CARD_NAME', f"{agent['name']} {module.NAME}"))
    a = (answers or {}).get(key) if key else None
    v = (a or {}).get('view') if isinstance(a, dict) else None
    if not v or not str(v.get('html') or ''):
        why = ('its card is not in the office\'s LARRYD records' if not key else
               'the office holds no shell for it with its job (the office\'s page start places its shells)')
        v = {'html': f'<div class="annotation">{_e(getattr(module, "NAME", None) or agent.get("name"))}: nothing drawn, {why}.</div>', 'css': ''}
    out = larryd_view.carried({'html': str(v.get('html') or ''), 'css': str(v.get('css') or '')}, str(page.get('path') or ''))
    if key:   # THE CARD IN THE TOP BLOCK (the owner 2026-11-03: "top block needs the header and card and text"): the platform's one agent card, injected by the host where the office drew its card box
        import re
        out['html'] = re.sub(r'<div class="(?:lv-div )?replica-cardbox[^"]*"[^>]*>\s*</div>', f'<div data-inject="agent_card" data-agent="{key}" data-size="full"></div>', out['html'], count=1)
    return {'view': out}


def run(given, agent_file):
    import datetime
    with _quiet():
        frame, office, mark_iv, module, agents = _office(agent_file, write_ok=True)
        agent = frame.agent()
        shape = frame.SETTINGS['root_shape']
        door = frame.Door(frame.NAME)
        store = frame.Shells(office.PAGE['store'], door, slots=(*shape['slots'], shape['agent_slot']), single=(shape['agent_slot'],))
        keys = {mark_iv: door.card_key(agent['name']), **{it: door.card_key(getattr(it, 'CARD_NAME', f"{agent['name']} {it.NAME}")) for it in agents[1:]}}
        agent = {**agent, 'key': keys[mark_iv]}
        slot_of = lambda m: shape['agent_slot'] if m is mark_iv else m.SLOT

        def shell_of(m, shells):   # web/app.py shell_of
            k = keys.get(m, '')
            return next((sh for sh in shells if k and sh['slot'] == slot_of(m) and sh['job'] and sh['agent'] == k), None)

        shells = store.board()
        chain = [(m, sh) for m in agents if (sh := shell_of(m, shells))]
        held = shell_of(module, shells)
        if not held:
            raise SystemExit(f'{module.NAME or agent["name"]}: the office holds no shell with its job for its card ({keys.get(module) or "no card"}): nothing run')
        ends = _Ends(store)
        n = int((held['job'] or {}).get('data_job_run') or 0) + 1
        started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            module.run(ends, str(held['job_key']), n, agent, shells, chain=chain)
        except Exception as fault:   # noqa: BLE001  A RUN THAT CRASHES IS RED (run_internal): FAILED, its one line
            line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
            ends.ran(str(held['job_key']), n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps({'summary': f'FAILED · {line}'}), 'FAILED')
        for t in [t for t in threading.enumerate() if t is not threading.current_thread() and not t.daemon]:
            t.join()   # its own threads (a slow step) end before its answer
    if ends.end is None:
        raise SystemExit(f'{module.NAME or agent["name"]}: its run wrote no end')
    state, exit_code, said = ends.end
    line = _line(said)
    if state != 'DONE' and exit_code:
        raise SystemExit(f'{state} · {line}'[:2000])
    return {'delivery': f'{state} · {line}'[:2000]}


class _Ends:
    """THE OFFICE'S STORE FOR THIS RUN (web/app.py EndsAtWid): every read the office's own; the run's end kept for this answer, and
    read back by the agent's own runs() as LARRYD's LOGS would show it."""
    def __init__(self, store):
        self.store, self.kept, self.end = store, [], None

    def __getattr__(self, name):
        return getattr(self.store, name)

    def ran(self, job_key, n, started_at, ended_at, exit_code, said, state):
        self.end = (state, int(exit_code or 0), said)
        self.kept.insert(0, {'id': 0, 'job_key': job_key, 'n': int(n), 'started_at': started_at, 'ended_at': ended_at, 'exit': int(exit_code or 0),
                             'said': said if isinstance(said, str) else json.dumps(said), 'log_key': ''})

    def runs(self, job_key, limit=30):
        mine = [r for r in self.kept if r['job_key'] == job_key]
        return sorted(mine + list(self.store.runs(job_key, limit)), key=lambda r: str(r['started_at']), reverse=True)[:limit]


def _line(said):
    try:
        got = json.loads(said) if isinstance(said, str) else said
    except ValueError:
        return str(said)[:1900]
    if isinstance(got, dict):
        return str(got.get('summary') or got.get('line') or json.dumps(got))[:1900]
    return str(got)[:1900]


def _e(text):
    import html
    return html.escape(str(text or ''), quote=True)


class _quiet:
    """What the office's code prints goes to stderr: stdout holds this agent's one JSON answer."""
    def __enter__(self):
        self.was = sys.stdout
        sys.stdout = sys.stderr

    def __exit__(self, *exc):
        sys.stdout = self.was


def main(agent_file):
    _own_interpreter()
    raw = sys.stdin.read()
    given = json.loads(raw or '{}')
    _office_env()
    do = given.get('do')
    if do == 'canvas':
        answer = call(given, agent_file)
    elif do == 'run':
        answer = run(given, agent_file)
    else:
        raise SystemExit('this agent does: canvas, run')
    sys.stdout.write(json.dumps(answer))
    sys.stdout.flush()
    os._exit(0)   # the office's timers and watchers (daemon threads) never hold the answer
