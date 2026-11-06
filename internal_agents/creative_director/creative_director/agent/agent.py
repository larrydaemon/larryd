"""CREATIVE DIRECTOR, the Creative Director office's MARK IV agent (agent001_creative_director.py), moved whole into LARRYD RUNTIME
INTERNAL (2026-11-03). Its code is the office's own, copied beside this file: agent/ (its programs, the chain: agent001 itself and its
sub agent agent002 Voice), frame/ (the replica's frame_replica, frame_rules, frame_skills, frame_xboard, frame_red), web/page.py (the
page's parts that draw its canvas) and schemas/ (its settings, routes and agent.json). Its state lives at
~/larryd/server/runtime/internal/instance/data/creative_director/ (its shells table, copied once from the office's instance).

A CALL ({do: "canvas"}) answers the canvas the office's page draws for its MARK IV agent (web/page.py agent_view, the middle canvas):
the platform's hero, its card, its words and what a replica is. The office leaves an empty card box; the card's
place is the platform's own card widget (data-inject="agent_card", its own card key) instead.

A RUN ({do: "run"}) is the office's own run (agent001 run): THE CHAIN'S SANITY written into each agent's job in LARRYD (every agent's
skills from the knowledge store's index and its rule judged against its program by the Claude reader when the program changed), then
the X board of the day, HEALTHY or CRITICAL. Its LOGS record is LARRYD RUNTIME INTERNAL's: the run's summary is its delivery, and a
FAILED run exits 1 naming its first fault. The office's page also ran THE RED's round after this run (frame_red: fixers hired on the
office's own git tree in ~/virtual_sanity); that round is not run here (nothing in ~/virtual_sanity is written)."""
import os
import sys

PY = '/Users/frost/virtual_workspace/.venv/bin/python'   # THE OFFICE'S OWN PYTHON (its launcher agent/run): the platform's pipeline (core_engine) is imported with it
if os.environ.get('CREATIVE_DIRECTOR_PY') != '1' and os.path.isfile(PY):
    os.environ['CREATIVE_DIRECTOR_PY'] = '1'
    os.execv(PY, [PY, '-B', os.path.abspath(__file__)])

import importlib.util
import json
import re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

from frame import frame_replica as frame   # noqa: E402

KEY = re.compile(r'[A-Z0-9_]{8,64}')


def agents_of(folder):
    """THE OFFICE'S AGENTS, found by listing its own agent folder (web/app.py agents_of): agentNNN_<name>.py, in their order."""
    names = sorted(n[:-3] for n in os.listdir(folder) if re.fullmatch(r'agent\d{3}_[a-z0-9_]+\.py', n))
    out = []
    for n in names:
        spec = importlib.util.spec_from_file_location(n, os.path.join(folder, n + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[n] = module
        spec.loader.exec_module(module)
        out.append(module)
    return out


class Office:
    """The office as its page held it (web/app.py create_app): its agents, its door to LARRYD, its shells, each agent's card key."""

    def __init__(self):
        self.shape = frame.SETTINGS['root_shape']
        self.agents = agents_of(os.path.join(HERE, 'agent'))
        self.mark_iv, self.subs = self.agents[0], tuple(self.agents[1:])
        self.agent = frame.agent()
        self.door = frame.Door(frame.NAME)
        self.store = frame.Shells(frame.SETTINGS['page']['store'], self.door, slots=(*self.shape['slots'], self.shape['agent_slot']), single=(self.shape['agent_slot'],))
        self.keys = {self.mark_iv: self.door.card_key(self.agent['name']),
                     **{it: self.door.card_key(getattr(it, 'CARD_NAME', f"{self.agent['name']} {it.NAME}")) for it in self.subs}}
        self.agent = {**self.agent, 'key': self.keys[self.mark_iv]}

    def slot_of(self, module):
        return self.shape['agent_slot'] if module is self.mark_iv else module.SLOT

    def shell_of(self, module, shells):
        k = self.keys.get(module, '')
        return next((sh for sh in shells if k and sh['slot'] == self.slot_of(module) and sh['job'] and sh['agent'] == k), None)

    def chain_of(self, shells):
        return [(m, sh) for m in self.agents if (sh := self.shell_of(m, shells))]


class EndsHere:
    """THE STORE FOR A RUN LARRYD RUNTIME INTERNAL HANDED (as the office's EndsAtWid): every read the office's own; a run's end kept here
    (its LOGS record is written by the runtime from this run's answer) and read back by the run as its own record."""

    def __init__(self, store):
        self.store, self.ended = store, []

    def __getattr__(self, name):
        if name == '_edit' and os.environ.get('CREATIVE_DIRECTOR_PROOF') == '1':   # A PROOF RUN BY HAND (python3 agent.py): no RUNNING beat on the live job, which no runtime would end
            raise AttributeError(name)
        return getattr(self.store, name)

    def ran(self, job_key, n, started_at, ended_at, exit_code, said, state):
        self.ended.append({'id': -len(self.ended) - 1, 'job_key': job_key, 'n': int(n), 'started_at': started_at, 'ended_at': ended_at,
                           'exit': int(exit_code), 'said': str(said or ''), 'log_key': '', 'state': state})

    def runs(self, job_key, limit=30):
        mine = [r for r in reversed(self.ended) if r['job_key'] == job_key]
        return (mine + self.store.runs(job_key, limit))[:limit]


def canvas(given, office=None):
    """THE CALL: the MARK IV agent's canvas as the office's page draws it (web/page.py agent_view with its module, the middle canvas)."""
    from web import page as parts
    office = office or Office()
    engine = frame.read_json('engine')
    hero = [line.replace('{version}', engine['larry_llm_version']) for line in parts.hero(office.shape['hero'])]
    view = parts.agent_view(office.agent, hero, None, '/shell', what={'title': office.shape['title'], 'note': office.shape['note']},
                            module=office.mark_iv, job={}, rows=None, light='', controls=False)
    html, css = str(view['view']['html']), str(view['view']['css'])
    key = office.agent.get('key') or ''
    card = f'<div data-inject="agent_card" data-agent="{key}" data-size="full"></div>' if KEY.fullmatch(key) else ''
    html = re.sub(r'<div class="replica-cardbox"[^>]*>\s*</div>', card, html, count=1)   # THE CARD: the platform's own embedded widget in the view's card box
    return {'view': {'html': html, 'css': css}}


def run(given):
    """THE RUN: the office's own run of its MARK IV agent (agent001 run), on its own job, its RUN number the job's."""
    office = Office()
    shells = office.store.board()
    mine = office.shell_of(office.mark_iv, shells)
    if not mine:
        raise SystemExit(f"FAILED: no shell of the Creative Director office holds its job (card {office.agent.get('key') or 'not found'}): nothing read")
    job = office.door.jobs().get(mine['job_key']) or {}
    n = int(str(job.get('data_job_run') or '0') or 0) or 1
    ends = EndsHere(office.store)
    said = office.mark_iv.run(ends, mine['job_key'], n, office.agent, shells, chain=office.chain_of(shells))
    last = ends.ended[-1] if ends.ended else {'state': 'FAILED'}
    summary = str((said or {}).get('summary') or '')
    if last['state'] != frame.SETTINGS['root_shape']['x_board']['done']:
        raise SystemExit(summary or 'FAILED: the run wrote no summary')
    return {'delivery': summary}


def main():
    given = json.load(sys.stdin)
    do = {'canvas': canvas, 'run': run}.get(given.get('do'))
    if do is None:
        raise SystemExit('Creative Director does: canvas, run')
    out, sys.stdout = sys.stdout, sys.stderr   # the one JSON object alone on stdout: anything the office's code prints goes to stderr
    try:
        answer = do(given)
    finally:
        sys.stdout = out
    print(json.dumps(answer))


if __name__ == '__main__':
    main()
