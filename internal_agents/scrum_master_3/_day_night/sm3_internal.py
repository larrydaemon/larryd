"""SCRUM MASTER 3, ONE OF ITS DAY OR NIGHT AGENTS IN LARRYD RUNTIME INTERNAL (moved 2026-11-03 from ~/virtual_sanity/scrum_master_3).

The office's own code, moved whole: its agent program (and, for a step of the DAY or the NIGHT, the other steps of its chain, which its
run drives in a loop exactly as the office did), its frame (frame/frame_replica.py: the door to LARRYD's records through the platform's
one pipeline, the shells board) and its page parts (web/page.py), each copied into this folder (scrum_master_3/app/). The office's state
(its sqlite: the requests and the shells board) lives at ~/larryd/server/runtime/internal/instance/data/scrum_master_3/.

What the office's web/app.py did for this agent, done here:
- a CALL (/internal/view): its canvas, as the office drew it (a DAY or NIGHT agent running in the background: its one line, its name and
  RUNNING / IDLE / NOT RUNNING from its job and its runs in LARRYD; the Backlog: its own interface, its presses answered on the act lane).
- a RUN (/internal/run): its run(store, job_key, n, agent, shells, chain), the office's own code. Its run's LOGS record is written through
  the platform's pipeline as the office wrote it; its job's RUN end is LARRYD's (the delivery: its summary line; a red step exits 1 so
  LARRYD writes FAILED). A green step takes the next step's RUN and runs it here, as the office's loop did.
Runs as this computer's own process ("internal": the owner 2026-11-03), cwd its own folder."""
import contextlib
import datetime
import importlib
import inspect
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, 'scrum_master_3', 'app')   # the office's app, as its own launcher set it (agent/run): its web, agent and frame
DATA = os.path.expanduser('~/larryd/server/runtime/internal/instance/data/scrum_master_3')   # the office's instance, moved
os.environ['REPLICA_OFFICE_APP'] = APP
os.environ['REPLICA_INSTANCE'] = DATA
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
if APP not in sys.path:
    sys.path.insert(0, APP)


class _Red(Exception):
    pass


def _modules(files):
    return [importlib.import_module('agent.' + os.path.splitext(f)[0]) for f in files]


class Office:
    """The office's page as it stood for this agent: its frame, its door, its store, its agents' keys and shells."""

    def __init__(self, files):
        from web import page as parts   # the page parts first: the frame's platform() puts the platform's app (its own web/) on the path after
        from frame import frame_replica as frame
        self.parts, self.frame = parts, frame
        self.modules = _modules(files)
        self.door = frame.Door(frame.NAME)
        self.keys = {m: self.door.card_key(getattr(m, 'CARD_NAME', '')) for m in self.modules}
        self.door.agent_keys = tuple(k for k in self.keys.values() if k)
        self.door.jobs = _jobs_of(self.door)
        shape = frame.SETTINGS['root_shape']
        self.shape = shape
        self.store = Store(os.path.join(DATA, frame.NAME + '.db'), self.door, slots=(*shape['slots'], shape['agent_slot']), single=(shape['agent_slot'],))
        self.store.slot_of = {k: m.SLOT for m, k in self.keys.items() if k}
        mark = frame.agent() or {}
        self.agent = {**mark, 'key': self.door.card_key(mark.get('name') or '')} if mark else None

    def shell_of(self, module, shells):
        k = self.keys.get(module, '')
        return next((sh for sh in shells if k and sh['slot'] == module.SLOT and sh['job'] and sh['agent'] == k), None)

    def chain(self, shells):
        return [(m, sh) for m in self.modules if (sh := self.shell_of(m, shells))]


def _jobs_of(door):
    """THE OFFICE'S JOBS (frame Door.jobs), and since its agents' jobs moved onto wid's own board (identity <member>@<screen>#<wid shell>, no
    longer the office's shell): each of these agents' ONE job, found by the card key it holds. -> door.jobs replacement"""
    own = door.jobs

    def jobs():
        got = own()
        if door.agent_keys:
            marks = ','.join('?' * len(door.agent_keys))
            for r in door.rows('jobs', f'WHERE data_agent_key IN ({marks}) ORDER BY id', door.agent_keys):
                got.setdefault(door.key('jobs', r), r)
        return got
    return jobs


def Store(*a, **kw):
    from frame import frame_replica as frame

    class _Store(frame.Shells):
        """THE OFFICE'S STORE (frame.Shells), with one change: the RUN LARRYD opened is ended by LARRYD (its delivery), so this run's own end
        writes its LOGS record alone (as Shells.ran writes it) and is kept for the answer; every other run (a next step taken here) as before."""
        own = None
        ended = None
        slot_of = {}

        def board(self):
            """THE SHELLS THESE AGENTS' JOBS SIT IN NOW: one per agent, its job found by its card key (the office's own shells table names
            jobs that moved to wid's board); each its slot, its job as the platform's one shell reads it, on (wid's board holds its switch)."""
            jobs = self._jobs()
            out = []
            for job_key, j in jobs.items():
                if j['agent_key'] not in self.slot_of:
                    continue
                out.append({'id': job_key, 'slot': self.slot_of[j['agent_key']], 'on': True, 'job': self.platform_job(j), 'job_key': job_key,
                            'agent': j['agent_key'], 'wires': [j[c] for c in frame.WIRES], 'schedule': {n: j[n] or d for n, d in self.schedule}})
            return out

        def ran(self, job_key, n, started_at, ended_at, exit_code, said, state):
            if self.own != (job_key, str(n)):
                return super().ran(job_key, n, started_at, ended_at, exit_code, said, state)
            job = self.door.jobs().get(job_key)
            if job is None:
                raise KeyError(job_key)
            logged = lambda: any(r.get('identity_log_block') == f'RUN {n}' and r.get('identity_log_time') == started_at for r in self.door.logs(job_key))
            self._busy(lambda: self.door.add_log(job, n, started_at, ended_at, exit_code, said), logged)
            word = {frame.SETTINGS['root_shape']['x_board']['done']: 'GREEN', 'FAILED': 'RED'}.get(state)
            if word:
                self._edit(job_key, {'rules_status': word})
            self.ended = {'exit': exit_code, 'said': said, 'state': state}
    return _Store(*a, **kw)


def _style_out(html, css):
    """a sheet inside the markup goes with the sheet (the office's internal_view did the same)"""
    style = re.compile(r'<style[^>]*>(.*?)</style>', re.S | re.I)
    return style.sub('', html), ' '.join([css, *style.findall(html)]).strip()


def canvas(office, module, given):
    """THE CANVAS, as the office's home() drew it for wid's /internal/view (web/app.py: a DAY or NIGHT agent with no interface of its own:
    its one line, live_block(status_row); an agent with an interface: its content in the original's markup, its presses on this page)."""
    parts, frame, store = office.parts, office.frame, office.store
    shells = store.board()
    sh = office.shell_of(module, shells)
    if sh is None:
        name = getattr(module, 'NAME', '')
        return {'html': f'<div class="replica-canvas"><div class="replica-canvas-content"><div class="body">{name}: no shell of the office holds its job (its card {office.keys.get(module) or "not found"}); its board is {os.path.join(DATA, frame.NAME + ".db")}</div></div></div>', 'css': parts.CANVAS_CSS}
    job = sh['job']
    if not getattr(module, 'INTERFACE', False):
        if job.get('data_job_run_state') in frame.OPEN_RUN:
            row = parts.run_status(job, {'key': module.KEY, 'state': 'IDLE', 'changed_at': ''})
        else:
            row = parts.day_status(store, job, module.KEY)
        return {'html': str(parts.live_block(module, row)), 'css': parts.CANVAS_CSS + ' ' + parts.LIVE_BLOCK_CSS}
    page = given.get('page') if isinstance(given.get('page'), dict) else {}
    search = page.get('search') if isinstance(page.get('search'), dict) else {}
    if not (sh.get('on', True) and store.root_on()):   # the replica off or its shell off: nothing inside it acts (the office's agent_press), its list still drawn
        search = {}
    import backlog_view   # ITS INTERFACE for the platform's view gate, from its own content() and press() (the office drew it with interface_view)
    return backlog_view.view(module, store, sh['job_key'], str(page.get('path') or ''), search)


def run(office, module, given):
    """THE RUN, the office's own run(store, job_key, n, agent, shells, chain): its job's open RUN (LARRYD opened it RUNNING), its run code,
    its chain for the steps after it. -> its said (dict)"""
    store = office.store
    key = office.keys.get(module, '')
    job = next((j for j in office.door.jobs().values() if key and j.get('data_agent_key') == key and j.get('data_job_run_state') in office.frame.OPEN_RUN), None)
    if job is None:
        raise _Red(f'no open RUN of its job in LARRYD (its card {key or "not found"}): a RUN comes from its shell\'s Run, which opens it')
    job_key, n = office.door.key('jobs', job), int(job.get('data_job_run') or 0)
    store.own = (job_key, str(n))
    shells = store.board()
    got = module.run(store, job_key, n, office.agent, shells, chain=office.chain(shells))
    if store.ended is None:
        raise _Red('its run ended without writing its end')
    try:
        said = json.loads(store.ended['said'])
    except (TypeError, ValueError):
        said = {'summary': str(store.ended['said'])}
    return said if isinstance(said, dict) else {'summary': str(said)}, store.ended['exit'] == 0


def main(module_file, files):
    given = json.loads(sys.stdin.read() or '{}')
    real = sys.stdout
    with contextlib.redirect_stdout(sys.stderr):   # what its code prints goes to the log, never into the answer
        office = Office(files)
        module = next(m for m in office.modules if m.__file__.endswith(module_file))
        if given.get('do') == 'run':
            try:
                said, ok = run(office, module, given)
            except _Red as no:
                said, ok = {'summary': f'FAILED · {no}'}, False
            line = ' '.join(str(said.get('summary') or ('DONE' if ok else 'FAILED')).split())
            if not ok:
                print(line, file=sys.stderr)
                print('StepFailedError', file=sys.stderr)   # LARRYD writes the RUN FAILED (its LOGS record holds the whole said)
                sys.stderr.flush()
                os._exit(1)
            answer = {'delivery': line}
        else:
            answer = {'view': canvas(office, module, given)}
    real.write(json.dumps(answer))
    real.flush()
