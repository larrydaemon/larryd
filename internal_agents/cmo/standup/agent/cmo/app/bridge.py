"""THE CMO OFFICE INSIDE LARRYD RUNTIME INTERNAL (moved 2026-11-03; the owner: "all virtual sanity agents will use 1 single internal
larryd run"; "and rip it out of the virtual sanity"). The office's own code, moved whole beside this file (agent/, frame/, web/, schemas/,
static/), its state at ~/larryd/server/runtime/internal/instance/data/cmo (REPLICA_INSTANCE, set by the agent's launcher). Run by the
workspace's Python (the office's own: flask, jinja2, the platform's pipeline), never imported by the runtime.

  python bridge.py <agent KEY>   stdin: the runtime's JSON (a CALL: {do, page, find, records}; a RUN: {do, records})   stdout: one JSON

A CALL is what the office's /internal/view drew for this agent (home's own answers on the face asked, its sheets lifted out of the
markup), made to pass LARRYD's view gate by sanitize.py; a press the office drew as a POST form comes back as a GET to the page itself
and is pressed here first, through the office's own /agent_press (each press once: its token is kept). A RUN is what the office's
/internal/run did: the agent's own run(), the RUN's end handed back to LARRYD as the delivery (never written twice: LARRYD writes the
job's RUN end, as wid's /jobs/internal/result did for the office)."""
import contextlib
import io
import json
import re
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOKENS = 'press_tokens.json'   # the presses already pressed, by token (a reload of the page never presses twice)
PROOF = os.environ.get('CMO_PROOF') == '1'   # a proof run (python3 agent.py by hand): the RUN runs, writes nothing into LARRYD, and says what it would write


def out(obj):
    sys.stdout.write(json.dumps(obj, default=str))
    sys.stdout.flush()


def instance():
    return os.environ.get('REPLICA_INSTANCE') or ''


def used(token):
    """True when this press token was pressed before; else it is kept as pressed now."""
    path = os.path.join(instance(), TOKENS)
    try:
        with open(path, encoding='utf-8') as fh:
            seen = json.load(fh)
    except (OSError, ValueError):
        seen = {}
    if token in seen:
        return True
    now = time.time()
    seen = {k: v for k, v in seen.items() if now - v < 7 * 86400}
    seen[token] = now
    with open(path + '.writing', 'w', encoding='utf-8') as fh:
        json.dump(seen, fh)
    os.replace(path + '.writing', path)
    return False


def main():
    key = sys.argv[1]
    given = json.loads(sys.stdin.read() or '{}')
    noise = io.StringIO()
    with contextlib.redirect_stdout(noise):   # the office prints its faults; stdout is the one JSON answer
        from web import app as office
        from frame import frame_replica as frame
        import sanitize
        module = next((m for m in office.AGENTS if getattr(m, 'KEY', '') == key), None)
        if module is None:
            raise SystemExit(f'no agent {key} in the office')
        agent = frame.agent()
        app = office.create(office.PAGE['store'], agent)
        if given.get('do') in ('report', 'run'):
            answer = run(office, app, module, agent)
            if 'failed' in answer:
                sys.stderr.write(answer['failed'][:2000] + '\nAgentRunFailedError\n')
                raise SystemExit(1)
        else:
            answer = call(office, app, module, agent, given, sanitize)
    out(answer)


def call(office, app, module, agent, given, sanitize):
    """THE CANVAS: home's own answer for this agent (the MARK IV agent's own canvas too, which wid's header replaced on the office's
    internal door), on the face asked, after the press it carries (if any)."""
    from flask import g
    page = given.get('page') if isinstance(given.get('page'), dict) else {}
    search = page.get('search') if isinstance(page.get('search'), dict) else {}
    path = str(page.get('path') or '')
    said = ''
    layer = str(search.get('agentlayer') or '')
    press = sanitize.press_of(search, module.KEY, layer if layer in office.LAYERS else office.PAGE['agentlayer'])
    if press:
        if used(press['token']):
            said = 'that press was already pressed (the page was loaded again): nothing pressed twice'
        else:
            doors = {office.R[k] for k in ('agent_press', 'shell', 'day_switch', 'security') if k in office.R}
            route = press['route'] if press['route'] in doors else office.R['agent_press']
            with app.test_client() as c:
                got = c.post(route, data=press['fields'], headers={'Sec-Fetch-Site': 'same-origin'})
            said = {302: '', 400: 'that press is not one of the agent\'s own: nothing pressed', 403: 'the agent\'s shell is off: nothing pressed'}.get(got.status_code, f'the press answered {got.status_code}')
    layer = str(search.get('agentlayer') or '')
    keys = {m: k for m, k in ((m, frame_key(office, m, agent)) for m in office.AGENTS)}
    full, pick = [], [None]
    own = getattr(module, 'content', None)
    if own is not None:
        def content(*a, **kw):   # the agent's own content, all of it, or the part of it asked (a canvas over the gate's 200 KB, in parts)
            got = list(own(*a, **kw))
            full[:] = got
            return got if pick[0] is None else got[pick[0][0]:pick[0][1]]
        module.content = content

    def draw():
        with app.test_request_context('/'):
            g.lang = 'en'
            g.carry = {'agentlayer': layer if layer in office.LAYERS else office.PAGE['agentlayer'], 'mode': str(search.get('mode') or '') if str(search.get('mode') or '') in office.MODES else ''}
            g.answers_only = True
            answers = app.view_functions['home']()
        v = ((answers or {}).get(keys.get(module) or '') or {}).get('view') or {}
        return str(v.get('html') or ''), str(v.get('css') or '')
    html, css = draw()
    nav = ''
    if len(sanitize.view(html, css, path)['html']) > 190000 and full:   # TOO BIG FOR THE GATE WHOLE: the agent's own parts in pages, each under the gate's size, a link to each
        from web import page as office_page
        drawn = [len(sanitize.view(str(office_page.interface_view([p]) if getattr(module, 'INTERFACE', False) else office_page.content_view([p])), '', path)['html']) for p in full]
        pages, start, size = [], 0, 0
        for i, n in enumerate(drawn):
            if i > start and size + n > 150000:
                pages.append((start, i))
                start, size = i, 0
            size += n
        pages.append((start, len(full)))
        try:
            at = max(0, min(len(pages) - 1, int(str(search.get('cmo_part') or '1')) - 1))
        except ValueError:
            at = 0
        pick[0] = pages[at]
        html, css = draw()
        keep = '&'.join(f'{k}={search[k]}' for k in ('agentlayer', 'mode') if search.get(k) and str(search[k]).isalnum())
        def title(p):
            return str(p.get('title') or p.get('label') or p.get('kind') or '')[:40]
        nav = ('<div class="clarity x-pages"><div class="annotation">THIS CANVAS IN ' + str(len(pages)) + ' PARTS (the whole is over the 200 KB a view may be)</div>'
               + ' '.join((f'<b class="btn btn--small">{i + 1} · {sanitize.esc(title(full[a]))}</b>' if i == at else
                           f'<a class="btn btn--small" href="{sanitize.esc(path)}?{keep + "&" if keep else ""}cmo_part={i + 1}">{i + 1} · {sanitize.esc(title(full[a]))}</a>')
                          for i, (a, _b) in enumerate(pages)) + '</div>')
    v = sanitize.view(html, css, path, key=module.KEY, said=said)
    v['html'] = nav + v['html']
    card = frame_key(office, module, agent)   # THE CARD IN THE TOP BLOCK (the owner 2026-11-03: "top block needs the header and card and text"): the platform's one agent card, injected by the host where the office drew its card box
    if card:
        v['html'] = re.sub(r'<div class="replica-cardbox"[^>]*>\s*</div>', f'<div data-inject="agent_card" data-agent="{card}" data-size="full"></div>', v['html'], count=1)
    return {'view': v}


def frame_key(office, module, agent):
    from frame import frame_replica as frame
    door = frame.Door(frame.NAME)
    return door.card_key(agent['name']) if module is office.MARK_IV else door.card_key(getattr(module, 'CARD_NAME', f"{agent['name']} {module.NAME}"))


def run(office, app, module, agent):
    """ONE RUN, the office's own run_internal: the agent's run() on the office's store, its job the one its shell holds (the RUN LARRYD
    opened on it), the RUN's end handed to LARRYD as the delivery (what the office sent wid's /jobs/internal/result)."""
    from frame import frame_replica as frame
    import datetime
    shape = frame.SETTINGS['root_shape']
    door = frame.Door(frame.NAME)
    store = frame.Shells(office.PAGE['store'], door, slots=(*shape['slots'], shape['agent_slot']), single=(shape['agent_slot'],))
    k = frame_key(office, module, agent)
    slot = shape['agent_slot'] if module is office.MARK_IV else module.SLOT
    shells = store.board()
    held = next((sh for sh in shells if k and sh['slot'] == slot and sh['job'] and sh['agent'] == k), None)
    if held is None:
        return {'failed': f'FAILED · {module.NAME or agent["name"]} holds no job in its shell (its card {k or "not in LARRYD"}): nothing ran'}
    keys = {m: frame_key(office, m, agent) for m in office.AGENTS}
    chain = [(m, sh) for m in office.AGENTS for sh in shells if keys[m] and sh['slot'] == (shape['agent_slot'] if m is office.MARK_IV else m.SLOT) and sh['job'] and sh['agent'] == keys[m]]
    ended = {}

    class EndsHere:
        """the office's store, every read its own; the RUN's end: its LOGS record written by the office's own door (as the office's store.ran),
        the job's RUN end left to LARRYD (it writes the state, the line and the delivery, as wid's /jobs/internal/result did)"""
        def __getattr__(self, name):
            return getattr(store, name)

        def set_job(self, job_key, values):
            if PROOF:   # a proof writes nothing into LARRYD: what it would write is kept on the answer
                ended.setdefault('would_write', []).append({'job_key': job_key, 'fields': sorted(values)})
                return None
            return store.set_job(job_key, values)

        def _edit(self, key, values, run=False):
            if PROOF:
                ended.setdefault('would_write', []).append({'job_key': key, 'fields': sorted(values)})
                return None
            return store._edit(key, values, run)

        def ran(self, job_key, n, started_at, ended_at, exit_code, said, state):
            ended.update({'job_key': job_key, 'n': n, 'line': f'{started_at} → {ended_at} · exit {exit_code}', 'said': said, 'state': state})
            if PROOF:
                return
            job = store.door.jobs().get(job_key)
            if job is not None:
                logged = lambda: any(r.get('identity_log_block') == f'RUN {n}' and r.get('identity_log_time') == started_at for r in store.door.logs(job_key))
                store._busy(lambda: store.door.add_log(job, n, started_at, ended_at, exit_code, said), logged)
                word = {shape['x_board']['done']: 'GREEN', 'FAILED': 'RED'}.get(state)
                if word and n:
                    store._edit(job_key, {'rules_status': word})

    n = int(held['job'].get('data_job_run') or 0)
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        module.run(EndsHere(), held['job_key'], n, agent, shells, chain=chain)
    except Exception as fault:   # A RUN THAT CRASHES IS RED, as the office's run_internal
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        EndsHere().ran(held['job_key'], n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps({'summary': f'FAILED · {line}'}), 'FAILED')
    if PROOF:
        return {'delivery': str(ended.get('said')), 'proof': {k: v for k, v in ended.items() if k != 'said'}}
    if module is office.MARK_IV and ended.get('state') == 'DONE':   # THE MARK IV AGENT RUNS THE FRAME'S RED ROUND after its run, as the office's run_agent
        try:
            from frame import frame_red as red
            mine = held
            red.round_(store, shells, chain, {**agent, 'key': k}, mine['job_key'], shape['x_board'])
        except Exception:   # noqa: BLE001 - the red round is the frame's own; its fault never turns a done run red
            pass
    if ended.get('state') != 'DONE':   # A RED RUN IS A FAILED RUN IN LARRYD TOO: the agent ends with an error (its words are on its LOGS record, written above)
        return {'failed': str(ended.get('said') or json.dumps({'summary': 'FAILED · the run wrote no end'}))}
    return {'delivery': str(ended.get('said'))}


if __name__ == '__main__':
    main()
