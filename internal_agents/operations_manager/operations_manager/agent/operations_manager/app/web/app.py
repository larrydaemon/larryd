"""THE OFFICE'S OWN HOST (the owner 2026-10-26: "it needs to look and function identical"; "we already made the decision to use
one ... 8835 should show our 1 copy"; set up as the Scrum Master is). It draws THE PLATFORM'S ONE AI ATOM SHELL: wid's own
web/templates/atom.html, read where it is (settings reads wid_templates), its board() macro handed the page's own values here,
never a copy of it. Served from its own folder on this laptop alone (127.0.0.1, the port in schemas/settings.json page).

THE AGENTS OF THE OFFICE are the programs of its own agent folder, found by listing it (agentNNN_*.py, in order; the owner
2026-10-27: "the scrum master 2 has 2 agents so far: scrum master 2, standup, not anything else"), never a kept list: the first is
the MARK IV agent itself (the AGENT slot), the rest its sub agents, each in its own slot. THE TEMPLATE HAS NONE (the owner 2026-10-27: "there
should not be a replica agent folder or any replica agents only frame they do not do anythign on thier own / it needs an agent like scrum master to
run it / its a frame"): with no agent folder its page draws the frame empty, holding nothing, doing nothing; the agents are each office's own. Each has its card, its job and its logs
in LARRYD under SYSTEM (frame/frame_replica.py), its shell connected to them by their keys. A RUN is a request: the agent's own
run writes its log; a slow run (the MARK IV's, with the reader) ends in its own thread.

It READS the platform's files and never imports or runs its code (as the Scrum Master: "NO LOADER, NO SYS.PATH"), but for the
one pipeline its records are written through: the templates, the three CSS files and the theme's faces, the manifest template and
engine.json are read where they are; FROST's data fabric records are read where they are, immutable. It writes only its own
store (frame/frame_replica.py: the shells) and, through the pipeline, LARRYD.

Run, from app/: <workspace>/.venv/bin/python -m web.app (or agent/run page)."""
import datetime
import importlib
import inspect
import json
import os
import re
import sys
import threading
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, urlencode

from flask import Flask, Response, abort, g, redirect, render_template, request, stream_with_context, url_for

from jinja2 import ChoiceLoader, FileSystemLoader

from frame import frame_agent_access as access
from frame import frame_replica as frame
from frame import frame_rules as rules
from frame import frame_skills as skills
from frame import frame_xboard as xboard
from web import page as parts
from frame import frame_live
from frame import frame_security   # SECURITY, the frame's piece under LIVE
from frame import frame_red as red

AGENT_FOLDER = os.path.join(frame.APP, 'agent')   # the office's own programs
MODES = ('dark', 'light')   # the look's two modes, as its theme folders name them (cdn/themes/<site>/images/dark|light)
SETTINGS_FILE = frame.SETTINGS_FILE   # THIS OFFICE'S SETTINGS, read where they are at each look and written by the owner's security switch alone (a check points it at a scratch copy)
WORKING = []   # the agents' runs at work (a RUN taken, the page's start): a check waits for them before its scratch store goes; a read of the original's page is not one


def is_live(module):
    """A LIVE AGENT (the owner 2026-10-27: "each one needs a status in the db and live streaming from the status ... not 5 minutes not anything
    else"): its schedule says live, it has its triggers and a pure look; the page's one watcher looks for it (frame_live.start_watch), no timer."""
    return (str((getattr(module, 'SCHEDULE', None) or {}).get('schedule_type') or '').lower() == 'live' and callable(getattr(module, 'look', None))
            and (callable(getattr(module, 'triggers', None)) or hasattr(module, 'TRIGGERS')))


def triggers_of(module, store=None):
    """its triggers now (its own triggers(store): the places it reads as they are set, a check's scratch ones too), else its TRIGGERS"""
    return list(module.triggers(store)) if callable(getattr(module, 'triggers', None)) else list(module.TRIGGERS)


def agents_of(folder):
    """THE OFFICE'S AGENTS, found by listing its own agent folder: agentNNN_<name>.py, in their order. -> [modules]"""
    if not os.path.isdir(folder):   # the template: the frame alone, no agent folder
        return []
    names = sorted(n[:-3] for n in os.listdir(folder) if re.fullmatch(r'agent\d{3}_[a-z0-9_]+\.py', n))
    return [importlib.import_module('agent.' + n) for n in names]


AGENTS = agents_of(AGENT_FOLDER)   # the office's own agents, in the folder's order: the MARK IV agent itself first, then its sub agents (lower rank)
MARK_IV, SUB_AGENTS = (AGENTS[0] if AGENTS else None), tuple(AGENTS[1:])
PAGE = frame.SETTINGS['page']
R = frame.ROUTES
TEMPLATES = os.path.join(frame.APP, 'web', 'templates')
PLATFORM = frame.path('wid_templates')   # the platform's own templates: atom.html and the parts it imports
THEMES = os.path.dirname(frame.path('css_technology'))   # the look's folder: technology.css at its top,
THEME = os.path.relpath(frame.path('css_theme'), THEMES)   # and LARRY LLM's own theme, <site>/css/<HIERARCHY>.css below it
HIERARCHY = os.path.splitext(os.path.basename(THEME))[0].upper()
SITE = THEME.split('/')[0]
FROST_SITE = os.path.relpath(frame.path('frost_theme'), THEMES)   # FROST IDENTITY's own theme folder (the original's frost_site): SECURITY's logo, as technology.css names it
AGENCY_SITE = os.path.relpath(frame.path('agency_theme'), THEMES)   # AGENCY MGMT's own theme folder: the DAY block's logo and fonts (the owner 2026-10-28: "use the agency mgmt logo and theme for the day block")
FACES = re.compile('(?:' + re.escape(SITE) + '|' + re.escape(FROST_SITE) + '|' + re.escape(AGENCY_SITE) + r')/(?:fonts/font_0[1-5]\.otf|images/(?:dark|light)/[a-z0-9_]{1,40}\.png)')   # what the theme's sheet names beside it (LARRY LLM's faces, FROST's logo for SECURITY: the original's FACES), nothing else of the folder
KINDS = {'.css': 'text/css', '.otf': 'font/otf', '.png': 'image/png'}
LAYERS = ('agent', 'gate')
KIND = re.compile(r'^([KRAIPMSO])([A-Z]{3})_')
KEY_WORDS = {'AGT': 'Agent key', 'JOB': 'Job key', 'LOG': 'Log key', 'MDL': 'Model key'}
say = parts.say


def key_kind(key):
    """A key's own word on its badge, by its family (the platform's key_kind for the four the shell holds)."""
    m = KIND.match(key or '')
    return KEY_WORDS.get(m.group(2), 'Key') if m else 'Key'


def create(store_path=None, agent=None, run=None, door=None, agents=None, serve=False):
    """THE OFFICE'S PAGE: its store, its agent (agent.json), its door to LARRYD, and THE AGENTS IT HOLDS (agents: the folder's own by default; a check hands
    fewer: an agent whose file is gone leaves the page drawing and the others running, the owner 2026-10-27: "more plug and play to turn on and off individual agents").
    serve: the page is being served on its port (the launcher): the machine's samplers run and an interval agent's first look comes FIRST seconds after the
    start; a check's app is never served, so it opens no port and samples nothing."""
    shape = frame.SETTINGS['root_shape']
    agents = list(AGENTS if agents is None else agents)
    MARK_IV, SUB_AGENTS = (agents[0] if agents else None), tuple(agents[1:])   # the MARK IV agent itself, then its sub agents (lower rank)
    if MARK_IV is None:   # THE FRAME HOLDING NO AGENT (the template): no card, no job, no run, no look; it draws the frame empty
        agent = None
    STANDUP = next((m for m in SUB_AGENTS if m.KEY == 'standup'), None)   # the sub agent with a standup to read aloud and an original to read from
    if serve and agent:   # A SERVED PAGE HOLDING AN AGENT: the machine sampled and the LIVE's reports written; the frame holding no agent does nothing (the owner 2026-10-27: "its a frame")
        frame_live.SAMPLING['on'] = True
        def red_tick():   # THE RED ON A SERVED PAGE HOLDING AN AGENT (frame/frame_red.py; none on the empty frame): a round every SECONDS, as the frame's stream and samplers run here; a timer to its next round, never a poll
            try:
                red_round()
            finally:
                again = threading.Timer(red.SECONDS, red_tick)
                again.daemon = True
                again.start()
        first_red = threading.Timer(red.FIRST, red_tick)
        first_red.daemon = True
        first_red.start()
        frame_live.watch()   # THE LIVE'S OWN LOOK, the frame's (the owner 2026-10-27: "live should be in replica not in the agent"): its stream looked at FIRST seconds after the start, then every INTERVAL
    x_board, x_groups = xboard.x_board, xboard.x_groups   # THE X BOARD, the MARK IV agent's own summary (agent001)
    door = door or frame.Door(run or frame.NAME)   # THE OFFICE'S DOOR TO LARRYD, its live store; a check hands a scratch store's (never the live one)
    from core_engine import look   # THE LOOK, the platform's own (the Door put its app on the path): the dock's logo slots and the faces a sheet names, read where they are
    store = frame.Shells(store_path or PAGE['store'], door, slots=(*shape['slots'], shape['agent_slot']), single=(shape['agent_slot'],))
    keys = {MARK_IV: door.card_key(agent['name']), **{it: door.card_key(getattr(it, 'CARD_NAME', f"{agent['name']} {it.NAME}")) for it in SUB_AGENTS}} if agent else {}   # THE AGENT KEYS, LARRYD's cards under SYSTEM by name (the owner 2026-10-27: "we will register these agents in larryd"): the MARK IV agent's and each sub agent's; '' until run register
    if agent:
        agent = {**agent, 'key': keys[MARK_IV]}

    def key_of(module):
        return keys.get(module, '')

    def module_of(agent_key):
        """the agent program a card key names, none for a card of another office"""
        return next((m for m, k in keys.items() if k and k == agent_key), None)

    def internal_key():
        """POSITIVE FEEDBACK'S OWN RUNNER's key, this office's copy (instance/secrets/internal_runner_key, placed beside wid's): '' while none."""
        try:
            with open(os.path.join(frame.INSTANCE, 'secrets', 'internal_runner_key'), encoding='utf-8') as fh:
                return fh.read().strip()
        except OSError:
            return ''

    def to_wid(method, route, data):
        """ONE SIGNED CALL TO wid's MACHINE DOOR as POSITIVE FEEDBACK'S OWN RUNNER (key id internal-runner), wid's address from global_config."""
        from core_engine import offices as _offices
        key = internal_key()
        if not key:
            raise OSError('no internal_runner_key in this office')
        o = (frame.read_json('global_config').get('offices') or {}).get('wid') or {}
        at, nonce = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), _offices.nonce()
        body = data if method == 'POST' else {}
        headers = {'Content-Type': 'application/json', 'X-Office': _offices.hardened_signature(key, route, body, at, nonce), 'X-Office-At': at,
                   'X-Office-Key': door.runtime.RUNNER_KEY_ID, 'X-Office-Nonce': nonce}
        req = urllib.request.Request(f"http://{o.get('host', '127.0.0.1')}:{(o.get('ports') or {}).get(side)}{_offices.API}{route}",
                                     data=json.dumps(body).encode('utf-8') if method == 'POST' else None, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode('utf-8') or '{}')

    class EndsAtWid:
        """THE OFFICE'S STORE FOR A RUN wid HANDED IT: every read the office's own, the RUN's end written by wid (/jobs/internal/result)."""
        def __init__(self, account, scope, handed=None):
            self.account, self.scope, self.handed = account, scope, handed or {}   # handed: the RUN as wid handed it (an X board's lines of the board its block sits on)

        def __getattr__(self, name):
            return getattr(store, name)

        def ran(self, job_key, n, started_at, ended_at, exit_code, said, state):
            to_wid('POST', '/jobs/internal/result', {'account': self.account, 'scope': self.scope, 'job_key': job_key, 'run': str(n), 'state': state,
                                                     'log': f'{started_at} → {ended_at} · exit {exit_code}', 'delivery': str(said or '')})

    def run_internal(j):
        """A RUN wid HANDED THIS OFFICE (its door, or the catch-up at its start): only for an agent this office holds; its own run code,
        in its own thread. -> True when it is this office's agent."""
        module = module_of(str(j.get('agent_key') or ''))
        if module is None:
            return False
        ends, n = EndsAtWid(str(j['account']), str(j['scope']), j), int(j['run'])

        def go():
            started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                shells_ = store.board()
                module.run(ends, str(j['job_key']), n, agent, shells_, chain=chain_of(shells_))
            except Exception as fault:   # A RUN THAT CRASHES IS RED: FAILED, exit 1, its one line, never no record
                line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
                try:
                    ends.ran(str(j['job_key']), n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps({'summary': f'FAILED · {line}'}), 'FAILED')
                except (OSError, ValueError):
                    pass
        threading.Thread(target=go, daemon=True).start()
        return True

    if serve:   # THE CATCH-UP, once at the start (like the LARRYD runtime's): the RUNs wid queued for this office's agents while it was away
        def catch_up():
            try:
                for j in to_wid('GET', '/jobs/internal/queued', {}).get('jobs') or []:
                    run_internal(j)
            except (OSError, ValueError):
                pass
        threading.Timer(3, catch_up).start()

    INTERNAL_NONCES = set()


    def slot_of(module):
        return shape['agent_slot'] if module is MARK_IV else module.SLOT

    side = os.environ.get(frame.read_json('global_config').get('environment_variable', 'WID_ENV'), '').partition('.')[2] or shape['page']['console']['side']   # this run's side, as the original's page_url reads it

    def office_api(office):
        """AN OFFICE'S API, OFFICIAL AND WITH ITS STATUS, as the platform's shell asks it (wid web/app.py office_api; the owner 2026-10-25: "data like API <its address>/api/ - UP · 404 ... so its
        official and has a status"): the address of its api door on this side (global_config, never typed) and what that door answered just now, UP and its HTTP status, or DOWN when
        nobody answers. Asked once a page load, never polling."""
        said = g.setdefault('office_api', {})
        if office not in said:
            o = frame.read_json('global_config')['offices'].get(office) or {}
            port = (o.get('ports') or {}).get(side)
            if not port:
                said[office] = 'DOWN'
                return said[office]
            at = f"http://{o.get('host')}:{port}{door.api}/"
            try:
                with urllib.request.urlopen(urllib.request.Request(at, method='GET'), timeout=2) as r:
                    said[office] = f'{at} - UP · {r.status}'
            except urllib.error.HTTPError as e:   # an answer, even a refusal: the door is up
                said[office] = f'{at} - UP · {e.code}'
            except OSError:
                said[office] = f'{at} - DOWN'
        return said[office]

    def shell_of(module, shells=None):
        """the shell holding a program's job: by its agent key, in its slot; none before it is placed"""
        k = key_of(module)
        return next((sh for sh in (shells if shells is not None else store.board()) if k and sh['slot'] == slot_of(module) and sh['job'] and sh['agent'] == k), None) if agent else None

    def chain_of(shells):
        """THE CHAIN: every agent of the office with its shell, in the agent folder's order (the MARK IV agent first), for the sanity"""
        return [(m, sh) for m in agents if (sh := shell_of(m, shells))]

    def red_round():
        """THE RED'S ROUND (frame/frame_red.py; the owner 2026-10-27: "it needs an agent like scrum master to run it"): every red of this office, a fixer
        hired NOW for each red nothing forces; each fixer's end logged on the Scrum Master's job."""
        shells = store.board()
        mine = shell_of(MARK_IV, shells)
        return red.round_(store, shells, chain_of(shells), agent, mine['job_key'] if mine else '', shape['x_board'])

    def place():
        with placing:
            if placed[0]:   # PLACED ONCE (the owner 2026-10-28: "the page is very slow to load"): every agent already in its shell; a shell action places again
                return
            _place()
            placed[0] = True

    def _place():
        """EVERY AGENT IN ITS SHELL (the owner 2026-10-26: "and why is there no job"; 2026-10-27: "all shells need to auto connect. right now its
        empty and that should not be possible"): the MARK IV agent in the AGENT slot's one shell, each sub agent in its own slot in the folder's
        order, each with a real job (its name, its schedule) and its card on it, by the store's own steps, once; nothing typed."""
        if not agent:
            return
        held = next(sh for sh in store.board() if sh['slot'] == shape['agent_slot'])
        if not held['job']:
            store.add_job(held['id'])
        if held['agent'] != key_of(MARK_IV):
            store.agent(held['id'], key_of(MARK_IV))
        held = next(sh for sh in store.board() if sh['slot'] == shape['agent_slot'])
        if held['job'].get('data_full_name') != agent['name'] or held['job'].get('data_job_schedule_type') != MARK_IV.SCHEDULE['schedule_type']:
            store.set_job(held['job_key'], {'full_name': agent['name'], **MARK_IV.SCHEDULE})
        for slot in dict.fromkeys(it.SLOT for it in SUB_AGENTS):
            for place_, item in enumerate(it for it in SUB_AGENTS if it.SLOT == slot):
                rows = [sh for sh in store.board() if sh['slot'] == slot]
                if len(rows) <= place_:
                    store.add(place_ - 1, beside=rows[-1]['id'])
                    rows = [sh for sh in store.board() if sh['slot'] == slot]
                sh = rows[place_]
                if not sh['job']:
                    store.add_job(sh['id'])
                    sh = next(x for x in store.board() if x['id'] == sh['id'])
                if sh['job'].get('data_full_name') != item.NAME or sh['job'].get('data_job_schedule_type') != item.SCHEDULE['schedule_type']:
                    store.set_job(sh['job_key'], {'full_name': item.NAME, **item.SCHEDULE})
                if sh['agent'] != key_of(item):
                    store.agent(sh['id'], key_of(item))

    placing = threading.Lock()   # the page places its agents once at a time (a request and the start, together)
    placed = [False]   # every agent in its shell since the last shell action: a page draw never places again (it rebuilt the board 10 times a load)

    def working(target, run=True):
        t = threading.Thread(target=target, daemon=True)
        if run:
            WORKING.append(t)
        t.start()
        return t

    def run_agent(held, module):
        """ONE AGENT'S RUN, after its RUN was taken (QUEUED): the program's own run writes its log and ends the RUN (DONE or FAILED); a
        program that works for minutes (BACKGROUND: the MARK IV agent's reader) runs in its own thread, the page answers at once."""
        shells = store.board()
        n = int(next(sh for sh in shells if sh['id'] == held['id'])['job']['data_job_run'] or 0)

        def go():
            import datetime
            import json
            started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                module.run(store, held['job_key'], n, agent, shells, chain=chain_of(shells))
            except Exception as fault:   # A RUN THAT CRASHES IS RED: its run record FAILED, exit 1, the fault's one line, through the store's own ran(), never no record and no light
                line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
                store.ran(held['job_key'], n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps({'summary': f'FAILED · {line}'}), 'FAILED')
                return
            if module is MARK_IV:   # THE SCRUM MASTER RUNS THE FRAME'S READS, THE RED AMONG THEM, on its RUN AGENT (the owner 2026-10-27: "its a frame")
                red_round()
            if module is STANDUP:
                read_original()
                again = threading.Timer(300, read_original)   # the original writes its minute just after 07:00: read it five minutes on
                again.daemon = True   # never holds the process (a check's, the page's) open
                again.start()
        if getattr(module, 'BACKGROUND', False):
            working(go)
            return f"RUN {n} QUEUED"
        go()
        return f"RUN {n} DONE"

    def platform_url(office, path, **query):
        """AN ADDRESS ON THE PLATFORM, as its own page_url says one (core_engine/global_config.py): the office's http://<host>:<port> from
        global_config.json, read where it is, then /<office>/<side>/<lang><path>?<query>, this page's side; empty values left out."""
        from urllib.parse import urlencode
        o = (frame.read_json('global_config').get('offices') or {}).get(office) or {}
        query = {k: v for k, v in query.items() if v}
        return f"http://{o.get('host', '127.0.0.1')}:{(o.get('ports') or {}).get(side, '')}/{office}/{side}/{shape['page']['console']['lang']}{path}" + ('?' + urlencode(query) if query else '')

    def link(*parts_, species=None, page=None, key=None, settings=False, to='', path='', **kw):
        """THE PLATFORM'S ONE LINK MAKER, answered for this page (wid web/app.py link): its own action door; a full address as it is; a stored
        path (app/larry/home), a screen (species, page) or none (the dashboard, schemas/screens.json product_screens[0]) on the office that
        serves the products (global_config databases.products), carrying site, mode and theme (the owner 2026-10-27: "none of the header or
        doc links acutally work")."""
        if to == 'app/shell':
            return R['shell']
        if to == 'mode':
            return R['mode']   # the header's DARK / LIGHT: this page's own door, never a post to another site (the owner 2026-10-27: "Bad Request ... when i click light mode")
        kw = {**({'mode': g.carry['mode']} if g.get('carry', {}).get('mode') else {}), **kw}   # the mode the page wears rides on to the platform's pages, as the platform's own links carry it
        if path and str(path).startswith(('http://', 'https://')):
            return path
        cfg = frame.read_json('global_config')
        if path:
            where = '/' + str(path).lstrip('/')
        else:
            species = species or (parts_[0] if parts_ else None)
            page = page or (parts_[1] if len(parts_) > 1 else None)
            if not species:
                with open(os.path.join(frame.path('wid_app'), 'schemas', 'screens.json'), encoding='utf-8') as fh:
                    species, page = json.load(fh)['product_screens'][0].split('/')
            where = f'/app/{species}/{page or "home"}' + (f'/{key}' if key else '') + ('/settings' if settings else '')
        return platform_url(cfg['databases']['products'], where, **{k: v for k, v in kw.items() if k in ('site', 'mode', 'theme')})

    def hub_card(key):
        """A KEY'S ONE CARD IN THE HUB, as the platform's shells link it (wid web/app.py hub_card): app/hub/card/<module>/<key> on the office of
        the technology that holds the hub (settings root_shape hub, global_config technologies)."""
        from core_engine import hub as the_hub
        cfg = frame.read_json('global_config')
        return platform_url(cfg['technologies'][shape['hub']], f"/app/hub/card/{the_hub.module_of(key) or 'record'}/{key}") if key else ''

    app = Flask(__name__, template_folder=TEMPLATES, static_folder=os.path.join(frame.APP, 'static'), static_url_path='/static')
    app.config.update(TEMPLATES_AUTO_RELOAD=True)   # nothing kept for a browser: no cookie key, no session
    app.jinja_loader = ChoiceLoader([FileSystemLoader(TEMPLATES), FileSystemLoader(PLATFORM)])
    app.jinja_env.filters['t'] = say
    app.jinja_env.filters['masked'] = lambda value: value   # the platform's layout's filters, answered for this page (nothing here is a secret)
    app.jinja_env.globals.update(   # what the platform's shell asks of its page, answered for this page
        link=link,   # THE PLATFORM'S LINKS, made the platform's way (the owner 2026-10-27: "none of the header or doc links acutally work")
        here=lambda **kw: R['home'] + '?agentlayer=' + kw.get('agentlayer', g.carry['agentlayer']) + ('&mode=' + g.carry['mode'] if g.carry.get('mode') else ''),
        csrf='', view_host=lambda: True, library_base=lambda: '', view_looks=lambda html: {}, room_hosts=lambda: '', room_line=lambda: '',
        look_sheet=lambda sheet: '/themes/' + sheet,
        url_for=lambda endpoint, **kw: (R['core_css'] if kw.get('filename') == 'css/core.css' else '/' + kw['filename'] if endpoint == 'static' and str(kw.get('filename', '')).startswith('js/') else url_for(endpoint, **kw)),
        look_faces=look.faces, look_place_faces=look.place_faces,   # the faces a sheet declares, for the page's preload: the platform's own answer
        dock_slot=lambda kind: next((s[-2:] for s, k in look.config().get('dock', {}).items() if k == kind), '') if look.on() else '',   # THE DOCK'S LOGO SLOT of a product, the look's own dock map (themes.json), as every site and app wears it (the owner 2026-10-27: "the footer is missing the logos in the dock .. why make text versions like that")
        creative_picture=lambda hierarchy, mode: '',   # the board's picture is the creative page's: this page draws no board
        has_settings=lambda address: False, settings_link=lambda address: '',   # no settings page here: nobody signs in, nothing to set
        ahead_rules=lambda: '', ahead_here=lambda: '',
        ground=lambda theme, mode: {'page': f'/cdn/themes/{SITE}/images/{mode}/background.webp', 'places': {}, 'modes': {m: {'page': f'/cdn/themes/{SITE}/images/{m}/background.webp', 'places': {}} for m in ('dark', 'light')}},   # the shell's view links wid's core.css: here, read where it is
        csp_nonce=lambda: '', office_api=office_api, office_apis=lambda apis: {row: (lambda o: f"http://{o['host']}:{o['ports'][side]}/api/" if (o.get('ports') or {}).get(side) else '')(frame.read_json('global_config')['offices'].get(office) or {}) if office else '' for row, office in (apis or {}).items()}, key_kind=key_kind, hub_card=hub_card)   # a key's card in THE HUB, as the platform's shells link it

    def group_of(agent_key, shells=None):
        """THE GROUP an agent sits in (the owner 2026-10-26: "on the top right of each agent add TOP or whatever it is"; "keep in mind we are calling it group"): its shell's group (TOP, LIVE, DAY, NIGHT, RELEASE). The replica's own agent, in the AGENT slot, wears none (the owner 2026-10-27: "SHAPE on the top delete it very top right")."""
        held = next((sh for sh in (store.board() if shells is None else shells) if agent_key and sh['agent'] == agent_key), None)   # the page's own shells when it has them (a board rebuilt for every canvas made the page slow)
        return held['slot'] if held and held['slot'] != shape['agent_slot'] else ''

    def panels(board, live_block, sec_html):
        """THE FRAME'S OLD PANELS, each now an agent's canvas: drawn from this page's own reading, the frame drawing none of them. -> {part: markup}"""
        from markupsafe import Markup
        mod = app.jinja_env.get_template('operations_manager_parts.html').module
        lv = live_block or {}
        return {'access': Markup(mod.access_view(board['access'], board['lock'], board['reseal'], '')), 'rules': Markup(board['rules']['html']), 'skills': Markup(board['skills']['html']),
                'live': Markup(lv.get('panel') or ''), 'red': Markup(lv.get('why') or ''), 'security': Markup(sec_html or '')}

    XBOARD_CSS = ' '.join(re.findall(r'[^{}]*replica-x[^{}]*\{[^{}]*\}', re.sub(r'/\*.*?\*/', '', open(os.path.join(frame.APP, 'static', 'css', frame.NAME + '.css'), encoding='utf-8').read(), flags=re.S)))   # THE X BOARD'S OWN LOOK, this office's sheet's rules for it, carried into the X Board agent's canvas (its own root)

    def grouped(answer, word):
        """THE AGENT'S OWN BLOCK WEARS ITS GROUP at its top right (the owner 2026-10-27: "THE AGENT", never the shell): the word as the first line of the agent's view, right-aligned, in the caption face; the shell is not touched."""
        from markupsafe import Markup
        if not answer or not word:
            return answer
        v = answer.get('view') or {}
        top = 'head' if v.get('head') else 'html'   # its first part: the canvas header where it has one (atom.html canvas), else its view
        css = (v.get('css') or Markup('')) + Markup(' ' + frame.GROUP_CSS)
        return {**answer, 'view': {**v, top: frame.group_line(word) + v[top], 'css': css}}   # the one group word (frame_replica.group_line)

    def layer(asked):
        return asked if asked in LAYERS else PAGE['agentlayer']

    @app.before_request
    def guard():
        g.lang = 'en'   # its page speaks English (the platform's layout reads g.lang)
        if request.method == 'POST' and (request.headers.get('Sec-Fetch-Site') or 'same-origin') != 'same-origin':
            abort(403)   # a press from its own page only: the browser's own word on where the press came from
        g.carry = {'agentlayer': layer(request.values.get('agentlayer', '')), 'mode': request.args.get('mode', '') if request.args.get('mode', '') in MODES else ''}   # the page's mode in its address, nobody signed in (the platform's carry for a signed-out visitor)

    def the_look():
        sheets = [name for name in ('technology.css', THEME) if os.path.isfile(os.path.join(THEMES, name))]
        return {'mode': g.carry.get('mode') or shape['page']['mode'], 'hierarchy': HIERARCHY, 'sheets': sheets, 'site': SITE, 'font_scale': 'normal', 'letter_case': 'upper', 'sounds': 'off'}

    def console_url():
        """THE LARRY LLM CONSOLE the strip links (the owner 2026-10-27: "add the larry llm"), as the original's page links it: the office's
        own http://<host>:<port> from global_config.json, read where it is, then /<office>/<side>/<lang><path> (settings page console)."""
        c, offices = shape['page']['console'], frame.read_json('global_config').get('offices') or {}
        o = offices.get(c['office']) or {}
        return f"http://{o.get('host', '127.0.0.1')}:{(o.get('ports') or {}).get(c['side'], '')}/{c['office']}/{c['side']}/{c['lang']}{c['path']}"

    def page_parts():
        """WHAT THE PLATFORM'S LAYOUT ASKS OF ITS PAGE, as the LARRY LLM dashboard wears it (settings root_shape page): its
        address and product, the dock's four products (engine.json, in its dock's order), the module strip with LARRY LLM underlined
        as the current module (the owner 2026-10-27: "add the larry llm"), the CRT and the mood light on, the footer on, the online
        light; nobody signed in here, so no member, no hub, no settings."""
        engine, page = frame.read_json('engine'), shape['page']
        products = [{**p, 'site': p['slug']} for p in sorted(engine['products'], key=lambda p: engine['dock'].index(p['slug']) if p['slug'] in engine['dock'] else 99)]
        return {'address': page['address'], 'product': page['product'], 'product_label': page['product_label'], 'products': products,
                'nav': [{'name': page['product_label'], 'link': console_url(), 'current': True}],
                'MENU': 'menu/home', 'ACCOUNT': 'account/home', 'animated': 'crt', 'draws': {'mood_light': True},
                'device': {'name': 'web', 'parts': {'footer': True}}, 'dot': {'label': 'online', 'class': 'hdr-status--success'},
                'websites': {o: c.get('website') for o, c in (frame.read_json('global_config').get('offices') or {}).items()},   # each technology's own website (the footer's links), as the platform's
                'site_legal': {p_: frame.read_json('global_config')['legal'][p_] for p_ in ('contact', 'privacy', 'terms')}, 'heading': None, 'clean': False}

    def manifest():
        """The platform's manifest template, read where it is, its ▸ moved in the pointer groups its settings name (pointer)."""
        m, at = frame.read_json('manifest'), frame.SETTINGS.get('pointer') or {}
        for side_ in ('data', 'ai'):
            m[side_] = [dict(grp, rows=[[label, '▸' if label == at[grp['t']] else '', default] for label, _pt, default in grp['rows']]) if grp['t'] in at else grp for grp in m[side_]]
        return m

    def manifest_names():
        m = manifest()
        return [grp['t'] for side_ in ('data', 'ai') for grp in m[side_]]

    def x_now(shells=None):
        """THE X BOARD NOW, one source for the page, the header and the stream: the shells in the shape's order, and the shape's items in their buckets
        (settings root_shape parts; the owner 2026-10-27: "reclassify the shape items to fit into the buckets and then include them in the xboard")."""
        if shells is None:
            order = [shape['agent_slot'], *shape['slots']]
            shells = sorted(store.board(), key=lambda sh: order.index(sh['slot']))
        x = x_board(shells, shape['slots'], shape['x_board'], groups=x_groups(agent, shape['slots']), parts=parts.x_parts(chain_of(shells), shape.get('parts') or {}, live=frame_live.live_word()))
        return parts.with_reds(x, shells, reds_now(shells), red.GROUP)   # AN AGENT IN THE RED IS NOT DONE, THE RED ITS GROUP'S OWN ROW: one function, the page's and the X Board agent's run alike (web/page.py with_reds)

    def reds_now(shells=None):
        """EVERYTHING RED, ONE LIST (the owner 2026-10-27: "LARRYD REPORT 3 GREEN · 1 RED ... also you just fucking lied too"): THE RED's agents'
        runs, and every agent whose RULES the X board counts red, from the same records the board reads (frame_rules.view_of: the review STUPID,
        the code changed since, a DRIFT or TAMPER lie detector), so THE RED never says nothing is red while the board counts one. -> [row]"""
        return list(red.why_rows(store))   # THE RED's own table: its agents' red runs and their red RULES, one list, a fixer on each (frame/frame_red.py what_is_red)

    def records_watched():
        """THE FILES WHOSE CHANGE WAKES THE STREAM, beside this office's own store (never a clock asking again): LARRYD's own database, where this office's jobs
        and logs are written through the pipeline (the door's store: a check's is its scratch copy), and the knowledge store the office names (the 3 way switch's
        routes), and THE OFFICE'S OWN DATABASE by name, THE ONE LIVE STATUS PLACE (its live_status row written by the frame's watcher wakes the stream; the owner
        2026-10-27: "the sse streaming is tied to that one place"). The files alone, their writes alone: never their folder, never an attribute (the platform's own read touches its file; proven 2026-10-27)."""
        db = door.st.db_of('logs')
        know = os.path.expanduser(str(((agent or {}).get('facts') or {}).get('knowledge') or ''))
        return [p for p in (os.path.join(door.s.dirs[db], f'{db}.db'), know, store.db_path) if p]

    @app.get(R['home'])
    def home():
        engine = frame.read_json('engine')
        place()
        order = [shape['agent_slot'], *shape['slots']]
        shells = sorted(store.board(), key=lambda sh: order.index(sh['slot']))   # in the shape's own order, its agent first (both layers)
        chain = chain_of(shells)
        held = shell_of(STANDUP, shells) if STANDUP else None
        if held and not loaded:   # the original's days, loaded once per run of this page (never twice: a loaded run is known)
            STANDUP.load_history(store, held['job_key'], agent.get('facts'))
            loaded.append(True)
        controls = g.carry['agentlayer'] == 'gate' and side == 'rnd'   # THE CONTROLS FOR THE AGENT ON THE RND FACE ALONE, the public face the middle canvas alone (the owner 2026-10-27: "TOP HEADER CONTROL FOR AGENT (RND FACE ONLY) MIDDLE CANVAS (PUBLIC ONLY) BOTTOM CONTROL FOR AGENT (RND FACE ONLY) do not fucking mix them it pisses me off"; "it will not show in the pf view only the rnd view")
        for module, sh in chain:   # each agent's clock: its job's schedule, the shell's simplest view
            sh['clock'] = module.clock(module.SCHEDULE) if hasattr(module, 'clock') else STANDUP.clock(module.SCHEDULE) if STANDUP else None   # an agent with a clock of its own (the LIVE's interval) says it; the others wear the standup's daily clock
        cards = {r.get('MAGT_norm_key'): r for r in door.rows('agnt', 'ORDER BY id')} if agent else {}   # EVERY AGENT'S OWN RECORD (agnt): its number, its name, its pitch, as register wrote them
        for module, sh in chain:   # THE ONE SHELL'S HEADER AND FOOTER WIRED (the owner 2026-11-01: "wire it up"): what the job does not hold, handed to the shell (atom.html canvas reads sh.canvas)
            sh['canvas'] = parts.canvas_fields(sh, door.logs(sh['job_key'], 400) if sh.get('job_key') else [], cards.get(sh.get('agent')) or {}, frame.light_of(sh['job'], shape['x_board']))
        mine = shell_of(MARK_IV, shells)
        last = (store.runs(mine['job_key'], 1) or [None])[0] if mine else None   # the MARK IV agent's last run: the skills' and the rules' head
        x = x_now(shells)   # THE X BOARD, drawn once: its lines (the shells, and the shape's items in their buckets), and the header's counts from the same lines
        bucket = lambda name: next((slot for slot, names in (shape.get('parts') or {}).items() if name in names), '')   # THE GROUP A FRAME BLOCK WEARS: its X board bucket (settings root_shape parts; the owner 2026-10-27 13:27: "should not be shape"; "x board and agent access TOP"); the word SHAPE never
        live_block = ({'slot': frame_live.SLOT, 'at': next((i for i, sh in enumerate(shells) if sh['slot'] == frame_live.SLOT), len(shells)), 'name': (agent or {}).get('name') or shape['name'], 'stream': R['stream'],   # THE LIVE PANEL in the LIVE agent's slot, both faces (the owner 2026-10-27: "next item is the live / we add it to the replica"): the original's panel with the frame's own data; at: where the slot begins among the shells (the agent face draws it there)
                       **frame_live.panel(store, shells, (agent or {}).get('facts'), x, manifest_names(), shape['x_board']['zone'])} if agent else None)   # THE LIVE PANEL IS THE FRAME'S, in every office holding an agent (the owner 2026-10-27: \"live should be in replica not in the agent\"); the template draws none
        if live_block:
            from markupsafe import Markup, escape
            live_block['why'] = Markup(parts.why_view(reds_now(shells), {sh['job_key']: sh['job'] or {} for sh in shells}, rules.rule_block, red.now_line(store)))   # WHY IT'S RED inside the panel, under its monitor table, the original's (scrum.html lines 125 to 128)
            live_job = {'data_job_' + ('rule' if k == 'rule' else 'rule_' + k): v for k, v in frame_live.RULE.items() if k in ('rule', 'fix', 'red', 'green')}   # THE LIVE'S RULE, the same RULES button every agent's canvas has, behind it, never in the open (the owner 2026-10-27: "live rules are no different than any other agent rules and in the agent like all the rest")
            live_block['panel'] = Markup('<style>' + parts.CANVAS_CSS + '</style>') + parts.live_view(dict(live_block, why='')) + (Markup(f'<div class="replica-live-foot"><details class="replica-live-rules"><summary class="btn btn--small">▶ Rules · {escape(rules.rules_word(live_job))}</summary><div class="scrum-rules-panel clarity">{rules.rule_block(os.path.basename(frame_live.__file__), live_job, fold=False)}</div></details></div>') if controls else Markup('')) + Markup('<div class="replica-normal-block replica-red replica-live" aria-label="THE RED"><span class="replica-red-group" aria-label="group">LIVE</span>') + live_block['why'] + Markup('</div>')   # the LIVE panel wears LIVE above it, outside; THE RED under it in the same box wears none (the owner 2026-10-28: "LIVE / there is an extra in the box")   # the panel's markup, the replica's own (web/page.py), never an agent's   # the clarity rules panel's sheet once on the page, for the LIVE's RULES button and WHY IT'S RED's folded rules
            live_block['html'] = Markup('')   # THE LIVE PANEL, THE RED and SECURITY are registered agents now, each in its own shell in LIVE (the owner 2026-11-01): the frame draws none of them
            sec = frame_security.look(conf=security_conf())   # SECURITY UNDER LIVE, the frame's own (the owner 2026-10-27: "put it under live and in the replica because its not for a specific agent"; "if its turned off it is not a red")
            sec_html = Markup(frame_security.panel_html(sec, parts.security_toggle(bool(sec.get('switch')), R['security'], g.carry['agentlayer'], sec.get('scan') == 'running'), light=g.carry['agentlayer'] == 'gate'))   # SECURITY's panel, its agent's canvas now
        day_mods = [m for m in SUB_AGENTS if getattr(m, 'SLOT', '') == 'DAY']
        day_shells = [sh for sh in shells if sh['slot'] == 'DAY' and sh.get('agent') in {key_of(m) for m in day_mods}]
        day_block = ({'slot': 'DAY', 'at': next((i for i, sh in enumerate(shells) if sh['slot'] == 'DAY'), len(shells)),   # THE DAY BLOCK where the DAY slot begins, both faces (the owner 2026-10-28: "a single day block at the top with a toggle and 1 toggle turns off all the day agents ... it does nothign else")
                      'html': frame.group_line(bucket('DAY') or 'DAY') + parts.day_view(sum(1 for sh in day_shells if sh.get('on', True)), len(day_shells), R['day_switch'], g.carry['agentlayer'],
                                                                                  os.path.join(frame.path('agency_theme'), 'css', 'B9AF66CF6633.css'), '/themes/' + AGENCY_SITE)}
                     if agent and day_mods and g.carry['agentlayer'] != 'gate' else None)   # the public face alone, as SECURITY (the owner 2026-10-28)
        from markupsafe import Markup
        red_block = None   # THE RED IS NO CANVAS OF ITS OWN: its rows are WHY IT'S RED inside the LIVE panel, the original's (the owner 2026-10-27: "look at the fuckign original")
        product = next((p['name'] for p in engine['products'] if p['slug'] == shape['page']['product']), shape['page']['product_label'])   # the product's own name (engine.json)
        board = {'board': 'replica', 'back': g.carry['agentlayer'], 'shells': shells, 'sequence': None, 'agents': [{'key': k, 'name': n, 'product_slug': '', 'module': '', 'group': ''} for k, n in store.agents()], 'pick': {'columns': [{'product_slug': '', 'module': ''}], 'rows': ['']},
                 'verdict': store.said(), 'jobs_site': None, 'manifest': manifest(), 'fabric': parts.fabric(g.carry['agentlayer']),
                 'access': (tree := access.home_tree(frame.path('sanity_home'), expand=('replica', frame.NAME))), 'lock': access.lock_state(tree), 'reseal': access.reseal_state(),
                 'skills': skills.skills_view(chain, MARK_IV.SCHEDULE if MARK_IV else None, last, agent, group=bucket('SKILLS')),   # THE SKILLS AND THE RULES OF THE CHAIN, under AGENT ACCESS and above TOP, each agent's from its own job (the owner 2026-10-26: "1. skills in the frame 2. rules in the frame 3. standup in the agent")
                 'rules': rules.rules_view(chain, MARK_IV.SCHEDULE if MARK_IV else None, last, agent, rules.busy(), group=bucket('RULES')),
                 'x_board': x, 'live': live_block, 'day': day_block, 'red': red_block,
                 'header': parts.header_view(parts.header_board(product, (agent or {}).get('name') or shape['name'], (agent or {}).get('class') or frame.SETTINGS['card']['class'], x, shape['x_board']['zone'], reds=len(reds_now(shells)))),   # THE HEADER, first on the page, outside the frame and the shells (the owner 2026-10-27)
                 'root': {'name': shape['name'], 'slots': shape['slots'], 'agent_slot': shape['agent_slot'], 'group_x_board': frame.group_line(bucket('X BOARD')), 'group_access': frame.group_line(bucket('AGENT ACCESS')), 'on': store.root_on(), 'title': shape['title'], 'note': shape['note'],
                          'classes': shape['classes'] if side == 'rnd' else []}}   # THE CLASSES SAID AT THE TOP OF THE FRAME, the gate face of the rnd side alone (the owner 2026-10-27: "on the top of the frame in the gate view rnd ... so its very clear how it works")   # THE ROOT SHAPE around the shells: its name, its fixed slots, on or off by its agent, its words
        answers = {}
        PANELS = panels(board, live_block, sec_html if live_block else '')   # THE FRAME'S OLD PANELS, each an agent's canvas now
        panel_of = lambda part: PANELS.get(part, '')
        if agent:
            view = parts.agent_view(agent, [line.replace('{version}', engine['larry_llm_version']) for line in parts.hero(shape['hero'])], mine or next((sh for sh in shells if sh['slot'] == shape['agent_slot']), None),
                                    R['shell'], what={'title': shape['title'], 'note': shape['note']}, module=MARK_IV, job=mine['job'] if mine else {},
                                    rows=parts.rows_of(store, mine['job'], MARK_IV.SCHEDULE['timezone'], row_file=getattr(MARK_IV, 'ROW_FILE', ''), facts=(agent or {}).get('facts')) if mine and controls else None, light=frame.light_of(mine['job'] if mine else {}, shape['x_board']), controls=controls)
            if view:
                answers[agent['key']] = grouped(view, shape['agent_slot'] if g.carry['agentlayer'] == 'gate' else '')   # THE MARK IV AGENT'S OWN CANVAS WEARS AGENT on the gate alone; the public face never (the owner 2026-10-27: "it says agent on the top right / i never fucking asked for that remove")
            lives = {r['key']: r for r in frame_live.statuses(store.db_path)}   # THE ONE STATUS PLACE: each live agent's row, its live line on its canvas head
            for module, sh in chain:   # EVERY SUB AGENT ON THE ONE CANVAS (the owner 2026-10-27: "a template to standarize the look of the canvas for the agent in the gate view ... so all the agents use the same style"): its light, its name big, its one line, its file, its own words, SKILLS and ROWS
                if g.carry['agentlayer'] != 'gate' and is_live(module) and module is not MARK_IV:   # A LIVE AGENT ON THE PUBLIC FACE: a very basic block, its green live line on top (the owner 2026-10-27), no canvas, no buttons, no rows
                    answers[key_of(module)] = grouped({'agent_key': key_of(module), 'hire_keys': [], 'room_at': '', 'room_pass': '',
                                                       'view': {'html': parts.live_block(module, status_row(module, sh, lives)), 'css': Markup(parts.CANVAS_CSS + ' ' + parts.LIVE_BLOCK_CSS)}}, '')   # NO LIVE WORD IN THE BLOCK (the owner 2026-10-28: "LIVE is in the block"): the LIVE panel above them says LIVE once, outside
                    continue
                if module is MARK_IV:
                    continue
                if getattr(module, 'SLOT', '') in ('DAY', 'NIGHT', 'RELEASE') and not getattr(module, 'INTERFACE', False):   # A DAY AGENT RUNNING IN THE BACKGROUND (the owner 2026-10-28: "if something is just running in the background it should look like AGENT / AUDIT / RED 19 S / LIVE"): its one line, the LIVE agents' own block, on both faces; on the gate its canvas is that line (the canvas is what the pf view shows), its header and footer the shell's
                    line = parts.live_block(module, status_row(module, sh, lives))
                    if g.carry['agentlayer'] != 'gate':
                        answers[key_of(module)] = grouped({'agent_key': key_of(module), 'hire_keys': [], 'room_at': '', 'room_pass': '', 'view': {'html': line, 'css': Markup(parts.CANVAS_CSS + ' ' + parts.LIVE_BLOCK_CSS)}}, '')
                    else:
                        view = parts.canvas(module, agent, key_of(module), sh['job'], [{'kind': 'html', 'html': line}], parts.rows_of(store, sh['job'], module.SCHEDULE['timezone'], row_file=getattr(module, 'ROW_FILE', ''), facts=(agent or {}).get('facts')) if controls else None, frame.light_of(sh['job'], shape['x_board']), controls)
                        view['view']['css'] = Markup(view['view']['css'] + ' ' + parts.LIVE_BLOCK_CSS)
                        answers[key_of(module)] = grouped(view, group_of(key_of(module), shells))
                    continue
                interface = getattr(module, 'INTERFACE', False)   # AN AGENT WITH AN INTERFACE OF ITS OWN (the owner 2026-10-28: "if we need an interfact like to add request it needs to look like the original"): drawn in the original's markup, its presses working on both faces (the canvas is what the pf view shows)
                content = module.content(store, sh['job_key'], original[0] if (module is STANDUP and original) else None) if hasattr(module, 'content') else ()
                part = getattr(module, 'PART', '')   # A FRAME PANEL THAT IS AN AGENT NOW (the owner 2026-11-01: "register them as real agents"): its old panel, read by this page now, on its own canvas
                if part:
                    content = [{'kind': 'html', 'html': str(panel_of(part))}]
                if getattr(module, 'X_BOARD', False):   # THE X BOARD AGENT'S CANVAS IS THE BOARD (agent003; the owner 2026-11-01): the board this page reads now, in its own shell
                    content = [{'kind': 'html', 'html': str(app.jinja_env.get_template('operations_manager_xboard.html').module.x_board_view(x, ''))}]
                content = [parts.pressable(p, R['agent_press'], module.KEY, g.carry['agentlayer'], controls or interface) for p in content if controls or interface or p.get('kind') not in ('press', 'form')]   # AN AGENT'S OWN BUTTON: the page names its route, the agent and the face it is on; the control face alone carries it
                answers[key_of(module)] = grouped(parts.canvas(module, agent, key_of(module), sh['job'], content, parts.rows_of(store, sh['job'], module.SCHEDULE['timezone'], row_file=getattr(module, 'ROW_FILE', ''), facts=(agent or {}).get('facts')) if controls else None, frame.light_of(sh['job'], shape['x_board']), controls, live=status_row(module, sh, lives) if is_live(module) else None, interface=interface), group_of(key_of(module), shells))
                if getattr(module, 'X_BOARD', False):   # the board's own look carried into its canvas (its own root)
                    v_ = answers[key_of(module)]['view']
                    v_['css'] = Markup(str(v_.get('css') or '') + ' ' + XBOARD_CSS)
        for slot_, title_ in (('NIGHT', parts.NIGHT_TITLE), ('RELEASE', parts.RELEASE_TITLE)):   # THE NIGHT AND RELEASE BLOCKS (the owner 2026-10-31), the DAY block's shape, each above its first agent
            mods_ = [m for m in SUB_AGENTS if getattr(m, 'SLOT', '') == slot_]
            shells_ = [sh for sh in shells if sh['slot'] == slot_ and sh.get('agent') in {key_of(m) for m in mods_}]
            if agent and mods_ and g.carry['agentlayer'] != 'gate' and key_of(mods_[0]) in answers and not g.get('answers_only'):   # the group's own switch is this page's board, never an agent's canvas asked by wid
                first = answers[key_of(mods_[0])]
                block = parts.day_view(sum(1 for sh in shells_ if sh.get('on', True)), len(shells_), R['day_switch'], g.carry['agentlayer'],
                                       os.path.join(frame.path('agency_theme'), 'css', 'B9AF66CF6633.css'), '/themes/' + AGENCY_SITE, slot=slot_, title=title_)
                answers[key_of(mods_[0])] = {**first, 'view': {**first['view'], 'html': block + first['view']['html']}}
        if g.get('answers_only'):   # THE INTERNAL VIEW DOOR asks this page's own canvases, never a page drawn (internal_view)
            return answers
        return render_template(frame.NAME + '.html', **page_parts(), A=board, answers=answers, look=the_look(), page_css=R['page_css'], board_css=R['board_css'], larry_version=engine['larry_llm_version'])

    @app.post(R['mode'])
    def mode():
        """DARK / LIGHT from the header's icons, the platform's own way (wid web/app.py color_mode) for a page nobody is signed in to: no member, so
        nothing is saved; the mode rides in the page's address and the page it was pressed on comes back wearing it; sent behind (behind=1)
        by a page that already flipped: nothing more to send. A word that is no mode, or a page not this one's own: 400."""
        word = request.form.get('mode', '')
        if word not in MODES:
            abort(400)
        if request.form.get('behind') == '1':
            return '', 204
        back = request.form.get('back', '') or R['home']
        if not back.startswith('/') or back.startswith('//'):
            abort(400)
        path, _, query = back.partition('?')
        rest = [(k, v) for k, v in parse_qsl(query) if k != 'mode']
        return redirect(path + '?' + urlencode(rest + [('mode', word)]))

    def background(module):
        """an agent that draws the one status line: a live agent, or a DAY agent running in the background"""
        return is_live(module) or (getattr(module, 'SLOT', '') in ('DAY', 'NIGHT', 'RELEASE') and not getattr(module, 'INTERFACE', False))

    day_rows = {}   # a day agent's row by its job's run: its run history is read again only when that run moves (the stream asks on every wake)

    def status_row(module, sh, rows):
        """its row of the three statuses (parts.live_line): a live agent's from the one status place, a day agent's from its own runs, an open run first"""
        job = (sh or {}).get('job')
        if is_live(module):
            return parts.run_status(job, rows.get(module.KEY) or {'key': module.KEY})
        run = (job or {}).get('data_job_run'), (job or {}).get('data_job_run_state')
        if run[1] in frame.OPEN_RUN:
            return parts.run_status(job, {'key': module.KEY, 'state': 'IDLE', 'changed_at': ''})
        if module.KEY not in day_rows or day_rows[module.KEY][0] != run:
            day_rows[module.KEY] = run, parts.day_status(store, job, module.KEY)
        return day_rows[module.KEY][1]

    def live_parts():
        """every status line and every public block drawn from one read of the rows, by the agent's key (the page's script puts each in place)"""
        if not agent:
            return {'live_lines': {}, 'live_blocks': {}}
        rows, shells = {r['key']: r for r in frame_live.statuses(store.db_path)}, store.board()
        drawn = [(m, status_row(m, shell_of(m, shells), rows)) for m in agents if background(m)]
        return {'live_lines': {m.KEY: str(parts.live_line(r)) for m, r in drawn}, 'live_blocks': {m.KEY: str(parts.live_block(m, r)) for m, r in drawn}}

    def security_conf():
        """this office's security settings read where they are (never the copy loaded at the start: his switch moves them); None when unreadable"""
        try:
            with open(SETTINGS_FILE, encoding='utf-8') as fh:
                return json.load(fh).get(frame_security.KEY) or {}
        except (OSError, ValueError):
            return None

    @app.post(R['security'])
    def security_switch():
        """THE OWNER'S SECURITY SWITCH (the original's row 16 toggle; the page's guard: a press from its own page only): security.scan written true or
        false in this office's settings, atomically (the whole file written beside it, then put in its place), then back to the face it was pressed on.
        ON starts the scan once, now (frame_security.start); OFF starts nothing; the light is the issue list's alone; the watcher's settings trigger looks again."""
        to = request.form.get('to', '')
        if to not in ('on', 'off'):
            abort(400)
        with open(SETTINGS_FILE, encoding='utf-8') as fh:
            conf = json.load(fh)
        sec = conf.get(frame_security.KEY) if isinstance(conf.get(frame_security.KEY), dict) else {}
        conf[frame_security.KEY] = {**sec, 'scan': to == 'on'}
        part = f'{SETTINGS_FILE}.{os.getpid()}.writing'
        with open(part, 'w', encoding='utf-8') as fh:
            json.dump(conf, fh, indent=1, ensure_ascii=False)
            fh.write('\n')
        os.replace(part, SETTINGS_FILE)
        if to == 'on':   # ON RUNS IT ONCE, NOW (the original's row 16; the owner 2026-10-27: "what do you think the toggle does... just looks cool?"): its own process, never a second while one runs
            frame_security.start(conf=conf[frame_security.KEY])
        return redirect(R['home'] + '?agentlayer=' + layer(request.form.get('back', '')))

    @app.get(R['health'])
    def health():
        """THIS OFFICE'S RUNTIME, UP OR NOT, answered at once (the Data Fabric's look; the owner's rule "fix the problem, never the rule"):
        a light route like the LARRYD runtime's own /health, never the whole board drawn. Nothing read, nothing written."""
        return {'office': frame.NAME, 'up': True}

    @app.post(R['internal_view'])
    def internal_view():
        """wid ASKS THIS OFFICE FOR ITS AGENTS' CANVASES (web/app.py internal_answers; the owner's rule "the canvas is exactly what shows in the pf
        agent mode, one template from the same records"): the agents asked, ALL in one call, each its canvas exactly as this page draws it (home's
        own answers, never a second drawing), on the face asked (agentlayer); signed as POSITIVE FEEDBACK'S OWN RUNNER, each nonce once. -> 200
        {views: {agent_key: {agent_key, view: {html, css}}}} for the ones this office holds (none: an empty map); 401 when the call is not wid's."""
        from core_engine import offices as _offices
        data = request.get_json(silent=True) or {}
        key = internal_key()
        fresh = lambda value: value not in INTERNAL_NONCES and not INTERNAL_NONCES.add(value)
        if not (key and _offices.hardened({door.runtime.RUNNER_KEY_ID: key}, request.headers.get('X-Office-Key'), R['internal_view'], data, request.headers.get('X-Office-At'),
                                          request.headers.get('X-Office-Nonce'), request.headers.get('X-Office'), datetime.datetime.now(datetime.timezone.utc), fresh)):
            return {'refused': 'not wid'}, 401
        wanted = {k for k in (data.get('agents') or []) if isinstance(k, str)}
        g.carry = {'agentlayer': layer(str(data.get('agentlayer') or '')), 'mode': str(data.get('mode') or '') if str(data.get('mode') or '') in MODES else ''}
        g.answers_only = True
        answers = home()
        import re as _re
        style = _re.compile(r'<style[^>]*>(.*?)</style>', _re.S | _re.I)
        views = {}
        for k, a in (answers or {}).items():
            html, css = str((a.get('view') or {}).get('html') or '') if isinstance(a, dict) else '', str((a.get('view') or {}).get('css') or '') if isinstance(a, dict) else ''
            if k not in wanted or not html or (agent and k == agent.get('key')):   # THE MARK IV AGENT'S HEADER IS wid's OWN (its card, the big header): never this page's
                continue
            views[k] = {'agent_key': k, 'view': {'html': style.sub('', html), 'css': ' '.join([css, *style.findall(html)]).strip()}}   # a sheet inside the markup goes with the sheet, where wid's view gate takes it
        return {'views': views}, 200

    @app.post(R['internal_run'])
    def internal_run():
        """wid HANDS THIS OFFICE AN INTERNAL-ONLY AGENT'S RUN (core_engine/larryd_runtime.py hand_internal), signed as POSITIVE FEEDBACK'S OWN
        RUNNER, each nonce once: 202 when it is this office's agent (its run started), 404 when not, 401 when the call is not wid's."""
        from core_engine import offices as _offices
        data = request.get_json(silent=True) or {}
        key = internal_key()
        fresh = lambda value: value not in INTERNAL_NONCES and not INTERNAL_NONCES.add(value)
        if not (key and _offices.hardened({door.runtime.RUNNER_KEY_ID: key}, request.headers.get('X-Office-Key'), R['internal_run'], data, request.headers.get('X-Office-At'),
                                          request.headers.get('X-Office-Nonce'), request.headers.get('X-Office'), datetime.datetime.now(datetime.timezone.utc), fresh)):
            return {'refused': 'not wid'}, 401
        return ({'taken': True}, 202) if run_internal(data) else ({'refused': 'not this office\'s agent'}, 404)

    @app.get(R['agent_press'])
    def agent_press_look():
        """THE PRESS ADDRESS LOOKED AT (the owner 2026-10-29: "Method Not Allowed ... it died and has this link"): a press cut off (the page restarted under it) leaves
        the browser on this address, and a reload asks it again with a look; the page itself, never an error page"""
        return redirect(R['home'])

    @app.post(R['agent_press'])
    def agent_press():
        """AN AGENT'S OWN BUTTON (the owner 2026-10-28: "for the backlog add a big button to clear all backlog"; the page's guard: a press from its own page
        only): the agent by its KEY, the press one of its own PRESSES, its press(store, job_key, do) run, its words said on its shell, back to its face."""
        key, do = request.form.get('agent', ''), request.form.get('do', '')
        module = next((m for m in agents if getattr(m, 'KEY', '') == key and callable(getattr(m, 'press', None))), None)
        if module is None or do not in getattr(module, 'PRESSES', ()):
            abort(400)
        held = shell_of(module)
        if not store.root_on() or (held and not held.get('on', True)):   # the replica off, or the agent's shell off: nothing inside it acts, as every shell action
            abort(403)
        fields = {k: request.form.getlist(k) if len(request.form.getlist(k)) > 1 or k in getattr(module, 'LISTS', ()) else request.form.get(k, '') for k in request.form if k not in ('agent', 'do', 'back', 'csrf')}   # WHAT HE TYPED OR CHECKED IN ITS FORM (ADD REQUEST TO BACKLOG, the owner 2026-10-28: "rebuild it so it looks like the original agent"), as typed
        said = module.press(store, held['job_key'] if held else '', do, fields=fields) if 'fields' in inspect.signature(module.press).parameters else module.press(store, held['job_key'] if held else '', do)
        if held:
            store.say(held['id'], True, said)
        return redirect(R['home'] + '?agentlayer=' + layer(request.form.get('back', '')))

    @app.post(R['day_switch'])
    def day_switch():
        """THE DAY BLOCK'S ONE TOGGLE (the owner 2026-10-28: "1 toggle turns off all the day agents ... it does nothign else"; the page's guard: a press from
        its own page only): every DAY agent's shell switched on or off, the store's own switch, then back to the face it was pressed on."""
        to = request.form.get('to', '')
        if to not in ('on', 'off'):
            abort(400)
        if not store.root_on():
            abort(403)
        slot = request.form.get('slot', 'DAY')   # the NIGHT block's toggle names its slot (2026-10-31)
        if slot not in ('DAY', 'NIGHT', 'RELEASE'):
            abort(400)
        keys = {key_of(m) for m in SUB_AGENTS if getattr(m, 'SLOT', '') == slot}
        for sh in store.board():
            if sh['slot'] == slot and sh.get('agent') in keys:
                store.switch(sh['id'], to == 'on')
        return redirect(R['home'] + '?agentlayer=' + layer(request.form.get('back', '')))

    @app.get(R['stream'])
    def stream():
        """THE LIVE, this page's own stream (the original's web/app.py stream: Server-Sent Events, the frame's generator, frame/frame_live.py follow): the hello,
        every shell's row today, the X board, what runs now, the five tools, then each new LARRYD log of this office's jobs as it is written; alive when quiet.
        Read by the page's own panel and by the frame's own look at it (frame_live.look); it waits on the records' own change events, never on a clock."""
        return Response(stream_with_context(frame_live.sse(frame_live.follow(store, (agent or {}).get('facts'), x_now, manifest_names(), shape['x_board'], watched=records_watched(), more=lambda: {'reds': {'html': parts.why_body(reds_now(), {sh['job_key']: sh['job'] or {} for sh in store.board()}, rules.rule_block), 'n': len(reds_now()), 'head': str(parts.why_head(reds_now(), red.now_line(store)))}, 'live_status': frame_live.statuses(store.db_path), **live_parts()}), frame_live.SSE['retry_seconds'][0])),
                        mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    @app.post(R['shell'])
    def shell():
        f = request.form
        here, shell_id = layer(f.get('back', '')), f.get('shell', '')
        args = {'value': f.get('value', ''), 'n': int(f['n']) if f.get('n', '').isdigit() else 0,
                'index': int(f['index']) if f.get('index', '').isdigit() else None, 'clear': bool(f.get('clear'))}
        try:
            done = store.act(shell_id, f.get('do', ''), **args)
        except KeyError:
            abort(404)
        except (ValueError, IndexError) as e:
            done = {'ok': False, 'text': str(e)}
        if done.get('ok') and f.get('do') == 'run' and agent:   # A RUN of one of the office's agents: its own program runs it now (its run, kept with the job)
            held = next((sh for sh in store.board() if str(sh['id']) == str(shell_id)), None)
            module = module_of(held['agent']) if held else None
            if module:
                done = {'ok': True, 'text': run_agent(held, module)}
        if 'ok' in done:
            store.say(shell_id, done['ok'], done['text'])
        if f.get('do') != 'run':   # a shell changed (added, removed, its job or agent): the next draw places every agent again
            placed[0] = False
        return redirect(R['home'] + '?agentlayer=' + here)

    def _file(path, kind, cache='no-cache'):
        try:
            with open(path, 'rb') as fh:
                return Response(fh.read(), mimetype=kind, headers={'Cache-Control': cache, 'X-Content-Type-Options': 'nosniff'})
        except OSError:
            abort(404)

    loaded, original = [], []   # the original's standup block, read at its own moments (start, RUN, 07:00), drawn from here

    def read_original():
        if agent and STANDUP and agent.get('standup_from'):
            got = STANDUP.with_words(STANDUP.original_block(agent['standup_from']), agent.get('facts'))   # its lists with his words (the owner 2026-10-27)
            if got:
                original[:] = [got]
    working(read_original, run=False)
    if agent:   # EVERY AGENT AT ITS OWN HOUR, by itself (a timer to its next time, never a poll): its RUN taken, its run, then the next day; the MARK IV agent's run at the page's start too
        def delay(module, first=False):
            """seconds to an agent's next run: its own until_next when it has one (the LIVE's interval), else the standup's daily clock; on a served page an
            interval agent's first look comes FIRST seconds after the start (its page is up by then); a check's app is never served, so it opens no port"""
            if first and serve and getattr(module, 'FIRST', None):
                return module.FIRST
            if hasattr(module, 'until_next'):
                return module.until_next(schedule=module.SCHEDULE)
            return STANDUP.until_next(schedule=module.SCHEDULE) if STANDUP else 86400

        def at_time(module):
            held = shell_of(module)
            if held and store.run(held['id'])[0]:
                run_agent(held, module)
            later = threading.Timer(delay(module), at_time, (module,))
            later.daemon = True
            later.start()
        for module in agents:
            if is_live(module):   # A LIVE AGENT HAS NO TIMER: the one watcher looks on its triggers alone (start_live)
                continue
            first = threading.Timer(delay(module, first=True), at_time, (module,))
            first.daemon = True
            first.start()

        CLOSE_EVERY, CLOSE_TRIES = 15, 240   # a live run LARRYD would not close: tried again every 15 s, for an hour
        looked, synced = {}, set()   # each live agent's last raw look (for its flip's run), and the agents whose first look was squared with their job

        def write_live(module, got, raw, trigger):
            """ONE RUN IN LARRYD FOR A LIVE AGENT'S FLIP (its job's light, THE RED and its history follow the one place): RUN taken, its run ended at
            once, exit 0 for GREEN or OFF, 1 for RED, what the look said and what woke it; its own record with it (record: No Shortcuts' baseline).
            A shell switched off, or a run open, takes none."""
            import datetime
            held = shell_of(module)
            took, word = store.run(held['id']) if held else (False, '')
            if not took:
                return False
            started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            n = int(word.split()[1])   # 'RUN n QUEUED', the run just taken
            red_ = got.get('state') == 'RED'
            try:
                said = said_live(module, got, raw, trigger)
            except Exception as fault:   # noqa: BLE001  (what the look said could not be made: FAILED, exit 1, the fault's one line)
                red_, said = True, {'summary': 'FAILED · ' + (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200], 'trigger': trigger}
            close_live(held['job_key'], n, started, 1 if red_ else 0, said, 'FAILED' if red_ else 'DONE')
            return True

        def said_live(module, got, raw, trigger):
            """what the live run says: what the look said, its record (its own fault said with it), what woke it"""
            said = dict((raw or {}).get('said') or {'summary': ('FAILED · ' if got['state'] == 'RED' else '') + (got.get('summary') or '') + (f" · {got['why']}" if got.get('why') else '')})
            try:
                if raw and callable(getattr(module, 'record', None)):
                    said.update(module.record(raw))
            except Exception as fault:   # noqa: BLE001  (its record failed: said with the run, the run still written)
                said['record_fault'] = f'{type(fault).__name__}: {fault}'.splitlines()[0][:200]
            said.setdefault('summary', got.get('summary') or '')
            said['trigger'] = trigger
            return said

        def close_live(job_key, n, started, code, said, state, tries=0):
            """A RUN TAKEN IS ALWAYS CLOSED, WITH ITS OWN RESULT (the moiré's RUN 13, then RUN 24 in the owner's reseal of 2026-10-31: LARRYD refused past store.ran's own tries, the
            run stayed QUEUED, the fault lost): the fault's line on the page's log, the same end tried again CLOSE_EVERY seconds until it lands, CLOSE_TRIES times (an hour)."""
            import datetime
            try:
                store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code, json.dumps(said), state)
            except Exception as fault:   # noqa: BLE001
                print(f'live run {job_key} RUN {n} not closed, try {tries + 1}: ' + (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200], file=sys.stderr, flush=True)
                if tries + 1 < CLOSE_TRIES:
                    again = threading.Timer(CLOSE_EVERY, close_live, (job_key, n, started, code, said, state, tries + 1))
                    again.daemon = True
                    again.start()

        def live_look(module):
            """A LIVE AGENT'S LOOK FOR THE WATCHER: its own pure look, then its own files kept (keep: New Files' line and ledger), never LARRYD. Its first look
            squares its job with the one place when no flip will come (the row already says this light, the job's last run another)."""
            looked.pop(module.KEY, None)
            got = module.look(store, store.board())
            if callable(getattr(module, 'keep', None)):
                module.keep(got)
            looked[module.KEY] = got
            if module.KEY not in synced:
                synced.add(module.KEY)
                row = frame_live.status(store.db_path, module.KEY)
                held = shell_of(module)
                want = 'FAILED' if str(got.get('state')).upper() == 'RED' else 'DONE'
                if row and row.get('state') == str(got.get('state')).upper() and held and (held['job'] or {}).get('data_job_run_state') != want:
                    write_live(module, {**got, 'state': str(got.get('state')).upper()}, got, 'start')
            return got

        def live_flip(key, got, was, trigger):
            """THE WATCHER'S FLIP HOOK (frame_live on_change): an agent's light flipped (or its first row): ONE run for its job; never on an unchanged look"""
            module = next((m for m in agents if is_live(m) and m.KEY == key), None)
            if module is not None:
                write_live(module, got, looked.pop(key, None), trigger)

        def security_look():
            """SECURITY FOR THE WATCHER: frame_security.look over this office's settings read where they are (a switch turned is its trigger), its
            light mapped: green GREEN, red RED, off OFF"""
            try:
                with open(SETTINGS_FILE, encoding='utf-8') as fh:
                    conf = json.load(fh).get(frame_security.KEY) or {}
            except (OSError, ValueError):
                conf = None
            got = frame_security.look(conf=conf)
            state = {'green': 'GREEN', 'red': 'RED'}.get(got.get('state'), 'OFF')
            return {'state': state, 'summary': got.get('summary') or '', 'why': got.get('summary') if state == 'RED' else '', 'step': got.get('step') or ''}

        def start_live():
            """THE ONE WATCHER OF THIS OFFICE (frame_live.start_watch on its own store): one item per live agent of the chain (its KEY, NAME, triggers,
            look) and SECURITY (this office's settings, the scanned tree's top folder); the flip hook writes each agent's run."""
            items = [{'key': m.KEY, 'name': m.NAME, 'triggers': triggers_of(m, store), 'look': (lambda m=m: live_look(m))} for m in agents if is_live(m)]
            items.append({'key': frame_security.KEY, 'name': 'Security', 'triggers': [SETTINGS_FILE, os.path.expanduser(str(frame_security.conf_of()['tree'])).rstrip('/')], 'look': security_look})
            return frame_live.start_watch(store.db_path, items, on_change=live_flip)

        def at_start():   # AT THE PAGE'S START: every agent in its shell, the one watcher started (the live agents and SECURITY), then the MARK IV agent's run (the chain's sanity: the skills taken, each program read where it changed; a start where nothing changed asks nothing)
            place()
            for sh in (store.board() if serve else ()):   # A RUN LEFT OPEN BY THE PAGE BEFORE THIS ONE DIED WITH IT (a served page alone: a check's app has no page before it) (the owner 2026-10-28: STUCK ON "SCRUM MASTER", every rerun refused: RUN 56 IS ALREADY RUNNING): it is closed FAILED with its reason, so a new run can start
                job = sh['job'] or {}
                if job.get('data_job_run_state') in frame.OPEN_RUN and str(job.get('data_job_run') or '').isdigit():
                    at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    store.ran(sh['job_key'], int(job['data_job_run']), at, at, 1, json.dumps({'summary': f"FAILED · run {job['data_job_run']} was {job['data_job_run_state']} when the page restarted, so it ended with that page; the next run starts now"}), 'FAILED')
            start_live()
            held = shell_of(MARK_IV)
            if held and store.run(held['id'])[0]:
                run_agent(held, MARK_IV)   # the same run as RUN AGENT's: a crash ends it FAILED with its line, never a run left QUEUED
        working(at_start)

    @app.route(R['voice'], methods=['GET', 'POST'])
    def voice(door):   # the route's own word (routes.json voice: /voice/<door>), the door asked: queue or wav
        which = door
        """THE STANDUP SPOKEN in its agent's own voice (the owner 2026-10-26: "is the voice correct?"): the script lab's voice
        service on this laptop, the voice its run names (the Scrum Master: christensen). queue: the lines made ahead; wav: one
        line, 200 its sound, 202 not made yet; 503 the voice is not running."""
        import json as _json
        import urllib.parse
        conf = (agent or {}).get('voice')
        if not conf:
            abort(404)
        if not conf.get('service') and conf.get('office'):   # THE VOICE IS ANOTHER OFFICE'S (the owner 2026-11-02: the Creative Director's): asked at its page's voice door, its port from its own settings
            with open(os.path.join(os.path.expanduser(conf['office']), 'app', 'schemas', 'settings.json'), encoding='utf-8') as _fh:
                conf = {**conf, 'service': f"http://127.0.0.1:{int(_json.load(_fh)['page']['port'])}/voice"}
        if which == 'queue' and request.method == 'POST':
            lines = [{'voice': conf['voice'], 'text': str(t)[:600]} for t in (request.get_json(silent=True) or {}).get('lines', [])[:60]]
            ask = urllib.request.Request(conf['service'] + '/queue', data=_json.dumps({'lines': lines, 'now': True}).encode(), headers={'Content-Type': 'application/json'}, method='POST')
        elif which == 'wav' and request.method == 'GET':
            ask = urllib.request.Request(conf['service'] + '/wav?' + urllib.parse.urlencode({'voice': conf['voice'], 'text': request.args.get('text', '')[:600]}))
        else:
            abort(404)
        try:
            with urllib.request.urlopen(ask, timeout=10) as got:
                return Response(got.read(), status=got.status, mimetype=got.headers.get('Content-Type', 'application/octet-stream'))
        except urllib.error.HTTPError as e:
            return Response(e.read(), status=e.code, mimetype='application/json')
        except OSError:
            return Response(_json.dumps({'ready': False, 'why': 'the voice is not running'}), status=503, mimetype='application/json')

    @app.post(R['press'])
    def press_one():
        """AGENT ACCESS'S OWN PRESS (the lock, the reseal): from its own page only (the guard), his fingerprint then his tool."""
        which = request.form.get('press', '')
        if which not in ('lock', 'unlock', 'reseal'):
            abort(400)
        access.press(which)
        return redirect(R['home'] + '?agentlayer=' + layer(request.form.get('back', '')))

    @app.get('/js/<name>.js')
    def page_js(name):
        """The platform's own page scripts its layout names (ground, crt, moodlight, ...), read where they are."""
        if not re.fullmatch(r'[a-z_]{1,40}', name or ''):
            abort(404)
        return _file(frame.path('wid_js', name + '.js'), 'text/javascript')

    @app.get('/media/<path:name>')
    def media(name):
        """AN OFFICE'S WORKING FILES, OUTSIDE THE LOCKED FOLDER (the owner 2026-10-28: "virtual sanity is a locked down folder and all reports and scratch
        is located outside this"): its settings' page.media folder (none: 404), a file inside it only, served with ranges so a player seeks"""
        from flask import send_from_directory
        root = os.path.expanduser(str(PAGE.get('media') or ''))
        if not root or not os.path.isdir(root):
            abort(404)
        return send_from_directory(root, name, conditional=True)

    @app.get('/positive-feedback-logo.png')
    def positive_feedback_logo():
        """THE ONE RED POSITIVE FEEDBACK LOGO, the same file for dark and light, from the frame's own home (the rule-skill-loop's, above his words)."""
        return _file(os.path.join(frame.FRAME_APP, 'static', 'images', 'positive_feedback_logo.png'), 'image/png', cache='max-age=3600')

    @app.get('/cdn/themes/<path:name>')
    def cdn_theme(name):
        """The theme's background picture, from this laptop's own CDN folder (the platform's own door, /cdn/themes/)."""
        if not re.fullmatch(r'[a-f0-9]{8}/images/(dark|light)/background(_thumb)?\.webp', name or ''):
            abort(404)
        return _file(frame.path('cdn_themes', *name.split('/')), 'image/webp', cache='max-age=3600')

    @app.get(R['board_css'])
    def board_css():
        """THE REPORT PANEL AND THE STATUS BOARD'S LINES (the header's classes): LARRY LLM's own core.css read where it is (settings
        reads css_larry_core), its report panel and .lsb rules alone (a block of its own rules kept with only them), nothing else of
        that sheet: never a copy."""
        try:
            with open(frame.path('css_larry_core'), encoding='utf-8') as fh:
                lines = fh.read().splitlines()
        except OSError:
            abort(404)
        out, block, ours = [], None, ('.lsb', '.console-report-panel', '.lrp-inner')
        for line in lines:
            if block is not None:
                if line.startswith('}'):
                    if len(block) > 1:
                        out.extend(block + ['}'])
                    block = None
                elif line.lstrip().startswith(ours):
                    block.append(line)
            elif line.startswith('@'):
                block = [line.split('{')[0].rstrip() + ' {']
            elif line.startswith(ours):
                out.append(line)
        return Response('\n'.join(out) + '\n', mimetype='text/css', headers={'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff'})

    @app.get(R['core_css'])
    def core_css():
        """wid's core layout sheet, read where it is (settings reads css_core): the AI atom shell's own rules."""
        return _file(frame.path('css_core'), 'text/css')

    @app.get(R['theme'])
    def theme_file(name):
        """A file of the look's folder its page links (technology.css, the theme's sheet, the faces it names): nothing else."""
        if name not in ('technology.css', THEME) and not FACES.fullmatch(name or ''):
            abort(404)
        return _file(os.path.join(THEMES, *name.split('/')), KINDS.get(os.path.splitext(name)[1], 'application/octet-stream'))

    app.office = {'store': store, 'door': door, 'agent': agent, 'agents': agents, 'MARK_IV': MARK_IV, 'key_of': key_of, 'shell_of': shell_of,   # LARRYD RUNTIME INTERNAL (2026-11-03): the moved agent's own driver (office.py) reaches the office's own pieces, one CALL or RUN at a time
                  'chain_of': chain_of, 'place': place, 'home': home, 'run_agent': run_agent, 'red_round': red_round}
    return app


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['register']:   # run register: this office's cards (the MARK IV agent's, each sub agent's) and its model written into LARRYD under SYSTEM, once, through the frame's door
        for name, key in frame.Door(frame.NAME).register(frame.agent(), SUB_AGENTS).items():
            print(f'{name}: {key}')
        raise SystemExit(0)
    # ITS OWN OFFICE (the owner 2026-10-26: "each agent to be setup just like the original scrum master"): this folder's settings name its port, its store and its agent; nothing is picked by name
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)   # no request log: the office's logs are its agents' runs in LARRYD (the owner 2026-10-27: "all logs should be stored in larryd logs"); a fault alone reaches its launcher's log
    create(PAGE['store'], frame.agent(), serve=True).run(host='127.0.0.1', port=int(PAGE['port']), threaded=True)
