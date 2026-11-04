"""PF DATA FABRIC: the account's data fabric at a glance, from ONE SNAPSHOT (the owner 2026-11-04: "it should only use a
snapshot from the database so the data is very fast and no connections / just 1 updated snapshot per day / everything else
we need to delete"). A CALL (panel) draws the dashboard's panel from what it is handed: FROST's once-a-day snapshot (the APIs
and the databases Positive Feedback looked at) and who looks; three views, CSV (the sixteen module files and pf_mapping.csv,
the open format), API and DATABASES, the dots at the bottom. Nothing is brought in, read or asked: no RUN, no records, no
custom fields, no files. LARRYD runs this file as its own process: one JSON object comes in on stdin, one JSON object goes
out on stdout."""
import html
import json
import re
import sys

FILES = (('pf_contacts.csv', 'cont', 'CONTACTS'), ('pf_invoices.csv', 'invc', 'INVOICES'), ('pf_locations.csv', 'locn', 'LOCATIONS'),
         ('pf_operations.csv', 'opns', 'OPERATIONS'), ('pf_hierarchies.csv', 'hrcy', 'HIERARCHIES'), ('pf_media.csv', 'mdia', 'MEDIA'),
         ('pf_brands.csv', 'brnd', 'BRANDS'), ('pf_sprints.csv', 'sprt', 'SPRINTS'), ('pf_images.csv', 'imgs', 'IMAGES'),
         ('pf_videos.csv', 'vdeo', 'VIDEOS'), ('pf_audio.csv', 'audo', 'AUDIO'), ('pf_productions.csv', 'prdn', 'PRODUCTIONS'),
         ('pf_agents.csv', 'agnt', 'AGENTS'), ('pf_models.csv', 'mdls', 'MODELS'), ('pf_logs.csv', 'logs', 'LOGS'), ('pf_jobs.csv', 'jobs', 'JOBS'))
MAPPING = 'pf_mapping.csv'   # THE SEVENTEENTH FILE (the owner, 2026-10-25: "define the name and custom slot 001 to 100 and type and basic info for each")


# ---------------------------------------------------------------- THE CALL: the panel
def _date(at):
    return (at or '')[:10]


OWN_QUERY = ('way', 'file')   # what the panel's own links change; every other word of the page's address stays (found on B, 2026-10-25: a
                              # dot that dropped site= opened another site's dashboard, where the panel is not)


def _quoted(value):
    """A value as an address carries it: letters, digits and _ . ~ - as they are, every other byte as %XX."""
    return ''.join(chr(b) if chr(b).isascii() and (chr(b).isalnum() or chr(b) in '_.~-') else f'%{b:02X}' for b in value.encode('utf-8'))


def _link(path, kept=None, **query):
    """The page itself with its own address words kept (site, mode, theme, ...) and the panel's own changed."""
    words = {k: v for k, v in (kept or {}).items() if k not in OWN_QUERY and isinstance(k, str) and isinstance(v, str) and re.fullmatch(r'[a-z_]{1,32}', k)}
    words.update({k: v for k, v in query.items() if v})
    q = '&'.join(f'{k}={_quoted(v)}' for k, v in words.items() if v)
    return html.escape(path + ('?' + q if q else ''))


def _size(n):
    n = int(n or 0)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
        n /= 1024


ADMINS = ('system_owner', 'account_owner', 'owner')   # an admin or above
MASK = '••••••••'


def sees(level, viewer):
    """THE PAGE'S MASK (the owner, 2026-10-25: "this is just UI and nothign to do with real security"): level 1, Positive
    Feedback's own technology layer, shown whole to the system owner alone; level 2, the account's own, to an admin or above."""
    return viewer == 'system_owner' if str(level or '1') == '1' else viewer in ADMINS


def _masked(address):
    m = re.match(r'^([a-z]+://)', address or '')
    return (m.group(1) if m else '') + MASK if address else ''


OURS = ('PF FROST IDENTITY API', 'PF DA-M API', 'PF MTOK API', 'PF LARRY LLM API')   # OUR OWN APIS, in the panel by default with no counts (the owner, 2026-10-25, R-0058: "by default they should all be in the api panel")
SAMPLE = {   # SAMPLE INFO for our four until FROST lists them (the owner 2026-10-26, R-0177: "these need some fake info they are blank"): never a real address
    'PF FROST IDENTITY API': ('Identity · members, sign-in, the vault', 'https://sample.positivefeedback.api/frost-identity/v1/'),
    'PF DA-M API': ('Files · drop zones, versions, DATA FABRIC folder', 'https://sample.positivefeedback.api/da-m/v1/'),
    'PF MTOK API': ('mTok · tokens, ledgers, transfers', 'https://sample.positivefeedback.api/mtok/v1/'),
    'PF LARRY LLM API': ('LARRY LLM · models, prompts, agents', 'https://sample.positivefeedback.api/larry-llm/v1/')}
SAMPLE_STATE = 'SAMPLE · NOT ASKED YET'


def _api_count(state):
    """How many APIs the API tab lists: FROST's, and ours where FROST lists them not (each name once, R-0172)."""
    apis = state.get('apis', [])
    listed = {str(a.get('api_name') or '').upper() for a in apis}
    return len(apis) + sum(1 for n in OURS if n not in listed)


def _api_lines(state, viewer=''):
    """THE APIS WE HAVE (the owner, 2026-10-25): our own four first (OURS, with their SAMPLE info), then each FROST keeps:
    its name, what it is for, its address and its status."""
    apis = state.get('apis', [])
    width = max([len(n) for n in OURS] + [len(a.get('api_name', '')) for a in apis])
    listed = {str(a.get('api_name') or '').upper() for a in apis}
    ours = [{'api_name': n, 'api_for': SAMPLE[n][0], 'api_address': SAMPLE[n][1], 'api_state': SAMPLE_STATE, 'level': '1'} for n in OURS if n not in listed]   # ONE LINE A NAME (the owner 2026-10-26: "it has duplicates on the top. remove them"): ours only where FROST lists it not
    out = ['<span class="rc0">CONNECTED</span>', '']
    for a in ours + apis:
        word = a.get('api_state') or ''
        tone = 2 if word.startswith(('UP', 'KEY IN THE VAULT · THERE')) else 4 if word.startswith(('DOWN', 'KEY IN THE VAULT · NOT')) else 7
        address = a.get('api_address', '') if sees(a.get('level'), viewer) else _masked(a.get('api_address', ''))
        where = ' · '.join(w for w in (a.get('api_for', ''), address) if w)
        out.append(f'<span class="rc1">{html.escape(a.get("api_name", "").ljust(width))}</span>  <span class="rc{tone}">{html.escape(word)}</span>'
                   + (f'  <span class="rc6">{html.escape(where)}</span>' if where else ''))
    return out + ['...']


DB_NAMES = {('WID', 'config.db'): 'Web interface daemon configuration', ('WID', 'wid.db'): 'Web interface daemon Invoice maps', ('WID', 'lrd.db'): 'Web interface daemon LARRYD (OS)',
            ('WID', 'mgmt.db'): 'Web interface daemon Agency mgmt', ('WID', 'ps.db'): 'Web interface daemon Pace Shift', ('WID', 'im.db'): 'Web interface daemon Invoice maps', ('FS', 'fs.db'): 'FROST Identity',
            ('FS', 'fs_config.db'): 'FROST Identity configuration', ('FS', 'datafabric.db'): 'FROST Identity PF Data Fabric', ('SO', 'so.db'): 'DA-M',
            ('SO', 'so_config.db'): 'DA-M configuration', ('CC', 'cc.db'): 'mTok', ('CC', 'cc_config.db'): 'mTok configuration',
            ('LRYLLM', 'lryllm.db'): 'LARRY LLM', ('LRYLLM', 'lryllm_config.db'): 'LARRY LLM configuration'}   # THE FULL NAME (the owner, 2026-10-25: "add a new column with the full name so its clear")
DB_MASK = '••••••.db'
OFFICE_NAMES = {'WID': 'Web interface daemon', 'FS': 'FROST Identity', 'SO': 'DA-M', 'CC': 'mTok', 'LRYLLM': 'LARRY LLM'}


def _db_name(d):
    office, name = d.get('db_office', ''), d.get('db_name', '')
    if office.endswith('-MINI'):
        return OFFICE_NAMES.get(office[:-5], office[:-5]) + ' mini'
    return DB_NAMES.get((office, name.lower()), OFFICE_NAMES.get(office, office))


def _db_lines(state, viewer=''):
    """THE DATABASES (the owner, 2026-10-25: "list the db and say if UP"), as FROST's look counts them."""
    dbs = state.get('databases', [])
    if not dbs:
        return ['<span class="rc0">CONNECTED</span>', '', '<span class="rc3">Not looked at yet.</span>']
    out, width = ['<span class="rc0">CONNECTED</span>', ''], max(len(d.get('db_office', '')) for d in dbs)
    full = max(len(_db_name(d)) for d in dbs)
    for d in dbs:
        named = _db_name(d)
        d = {**d, 'db_name': DB_MASK if d.get('db_name') else ''}   # THE NAME MASKED FOR EVERY VIEWER (the owner 2026-10-26, R-0178: "mask the names of the db for security please")
        if not sees(d.get('level'), viewer):
            d = {**d, 'db_bytes': ''}
        native = (d.get('db_state') or '') == 'NONE HERE'   # the owner: "NONE HERE to on native device", in the database's column, nothing in the state's
        word = '' if native else (d.get('db_state') or '')
        tone = 2 if word == 'UP' else 4 if word in ('DOWN', 'NOT A DATABASE') else 7
        if native:
            d = {**d, 'db_name': 'ON NATIVE DEVICE', 'db_bytes': 'native'}
        out.append(f'<span class="rc5">{html.escape(named.ljust(full))}</span>  <span class="rc1">{html.escape(d.get("db_office", "").ljust(width))}</span>  <span class="rc{tone}">{html.escape(word.ljust(9))}</span>'
                   + (f'  <span class="{"pfdf-native" if native else "rc6"}">{html.escape(d.get("db_name", ""))}</span>  <span class="rc5">{html.escape("" if d.get("db_bytes") == "native" else _size(d.get("db_bytes")) if d.get("db_bytes") else "•••")}</span>' if d.get('db_name') else ''))
    return out + ['...']


def _snapshot_lines():
    """THE CSV FILES (the owner 2026-11-03: "use the snapshot data and not the live data"; 2026-11-04: nothing is brought
    in): each module's file, then pf_mapping.csv, the open format, as the agent manifest shows them (wid fabric_of)."""
    return ['<span class="rc0">CONNECTED</span>', ''] + [f'<span class="rc1">{html.escape(name)}</span>' for name in [n for n, _s, _short in FILES] + [MAPPING]] + ['...']


def panel(given):
    state = (given.get('fabric') or {}).get('state') or {}
    viewer = str(((given.get('fabric') or {}).get('viewer') or {}).get('member_type') or '')
    page = given.get('page') or {}
    path = page.get('path') if isinstance(page.get('path'), str) else ''
    search = page.get('search') if isinstance(page.get('search'), dict) else {}
    way = search.get('way') if search.get('way') in ('api', 'db') else 'csv'
    if way == 'api':
        lines = _api_lines(state, viewer)
        tabs = f'<span class="on">PF DATA FABRIC · API ({_api_count(state)}) ✓</span>'   # THE COUNT AFTER THE HEADER, BEFORE THE CHECK (the owner 2026-10-26: "add a count after the header before the check mark like (10)")
        tail = ['', '<span class="rc3">If it changes in one system, it changes everywhere.</span>']
    elif way == 'db':
        tabs = f'<span class="on">PF DATA FABRIC · DATABASES ({len(state.get("databases") or [])}) ✓</span>'   # the count of databases FROST looked at
        lines = _db_lines(state, viewer)
        tail = ['', '<span class="rc3">Every database of the platform, looked at by FROST, in one place.</span>']
    else:   # THE SNAPSHOT, AS THE AGENT MANIFEST SHOWS IT (the owner 2026-11-03: "convert to use the snapshot data and not the live data ... should be the same as in the agent manifest in the gate view")
        tabs = f'<span class="on">PF DATA FABRIC · CSV ({1 + len(FILES)}) ✓</span>'   # the owner: "put csv check on top so they all match"; the count of its files, pf_mapping.csv and the sixteen
        lines = _snapshot_lines()
        tail = ['', '<span class="pfdf-end">Every field, open format, any time.</span>']
    window = '\n'.join(lines + tail)
    dots = ''.join(f'<a class="way way--{w}{" on" if w == way else ""}" href="{_link(path, search, way=w)}" title="{w.upper()}"><span class="dot"></span><span class="word">{w.upper() if w == way else ""}</span></a>'
                   for w in ('csv', 'api', 'db'))
    markup = (f'<section class="pfdf pfdf--{way}">'
              f'<div class="pfdf-term"><div class="pfdf-art" aria-hidden="true"><div class="pfdf-mesh"></div><div class="pfdf-nodes"></div></div>'   # THE FABRIC in the background of the box, transparent, the tab's own colour (the owner, 2026-10-25)
              f'<div class="pfdf-tabs">{tabs}</div>'
              f'<div class="pfdf-pre">{window}</div></div>'
              f'<div class="pfdf-pick">{dots}</div>'
              '</section>')
    return {'view': {'html': markup, 'css': CSS}}


CSS = """
.pfdf { position: relative; padding: 8px 0 4px; text-align: left; --fab: #0A9A4E; --fab2: #04542A; --node: #4DFF6B; --glow: rgba(77,255,107,.22); }
.pfdf--api { --fab: #CC6600; --fab2: #6B3500; --node: #FFC133; --glow: rgba(255,138,0,.22); }
.pfdf--db { --fab: #ED86FF; --fab2: #4B2A8F; --node: #07CE3B; --glow: rgba(237,134,255,.22); }
.pfdf-def { color: var(--active-color-08); margin: 0 0 18px; font-size: 15px; line-height: 1.45; opacity: .85; }
.pfdf-files { border-top: 1px solid rgba(255,255,255,.06); }
.pfdf-art { position: absolute; z-index: 0; inset: 0; overflow: hidden; perspective: 420px; pointer-events: none; opacity: .45;
  -webkit-mask-image: radial-gradient(ellipse 70% 70% at 50% 50%, #000 40%, transparent 85%); mask-image: radial-gradient(ellipse 70% 70% at 50% 50%, #000 40%, transparent 85%); }
.pfdf-art::before { content: ""; position: absolute; inset: 0; background: radial-gradient(ellipse 50% 40% at 50% 55%, var(--glow), transparent 70%); }
.pfdf-mesh { position: absolute; left: -25%; right: -25%; top: -40%; bottom: -40%; transform-origin: 50% 50%;
  background:
    repeating-linear-gradient(60deg, transparent 0 25px, var(--fab) 25px 26px),
    repeating-linear-gradient(-60deg, transparent 0 25px, var(--fab) 25px 26px),
    repeating-linear-gradient(0deg, transparent 0 21px, var(--fab2) 21px 22px);
  transform: rotateX(64deg) translateY(-8px); animation: pfdf-flow 18s linear infinite, pfdf-wave 7s ease-in-out infinite alternate; opacity: .95; }
.pfdf-nodes { position: absolute; left: -25%; right: -25%; top: -40%; bottom: -40%; transform: rotateX(64deg) translateY(-8px);
  background: radial-gradient(circle, var(--node) 0 1.6px, transparent 2.6px) 0 0 / 30px 52px, radial-gradient(circle, var(--node) 0 1.2px, transparent 2.2px) 15px 26px / 30px 52px;
  animation: pfdf-flow 18s linear infinite, pfdf-wave 7s ease-in-out infinite alternate; opacity: .9; }
@keyframes pfdf-flow { from { background-position: 0 0, 0 0, 0 0; } to { background-position: 300px 0, -300px 0, 0 220px; } }
@keyframes pfdf-wave { from { transform: rotateX(64deg) translateY(-14px) skewY(-2deg); } to { transform: rotateX(58deg) translateY(6px) skewY(2deg); } }
@media (prefers-reduced-motion: reduce) { .pfdf-mesh, .pfdf-nodes { animation: none; } }
.pfdf-term > .pfdf-tabs, .pfdf-term > .pfdf-pre { position: relative; z-index: 1; }
.pfdf-pre { background: transparent !important; }
.pfdf-txt { position: relative; z-index: 1; max-width: 900px; margin: 0 auto; }
.pfdf-label { font: 500 14px/1.4 Menlo, Monaco, "SF Mono", Consolas, "Courier New", monospace; letter-spacing: 0.12em; text-transform: uppercase; color: var(--active-color-01); margin: 0 0 8px; }
.pfdf-note { color: var(--active-color-08); margin: 14px 0 18px; font-size: 17px; line-height: 1.42; }
.pfdf-term { position: relative; z-index: 1; max-width: 900px; margin: 0 auto; border-radius: 6px; overflow: hidden; background: #04180A; border: 1px solid #04180A; box-shadow: 0 18px 50px rgba(0,0,0,0.6); transition: background-color .5s ease, border-color .5s ease; }
.pfdf-tabs { display: flex; align-items: center; gap: 22px; padding: 0 16px; height: 35px; overflow-x: auto; scrollbar-width: none; background: #04180A; border-bottom: 1px solid #0A9A4E;
  font: 400 11px/35px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; letter-spacing: 0.04em; text-transform: uppercase; }
.pfdf-tabs span, .pfdf-tabs a { color: #0A9A4E; white-space: nowrap; text-decoration: none; }
.pfdf-tabs .on { color: #4DFF6B; box-shadow: inset 0 -1px 0 #4DFF6B; }
.pfdf-pre .pfdf-end { color: #4DFF6B; }   /* the CSV theme's own green (the owner, 2026-10-25) */
.pfdf-pre { margin: 0; padding: 14px 18px 18px; min-height: 254px; box-sizing: border-box; background: #04180A; color: #0CCC68; white-space: pre; overflow: auto; max-height: 560px;
  font: 400 13px/1.55 Menlo, Monaco, "SF Mono", Consolas, "Courier New", monospace; text-shadow: none; }
.pfdf-pre .rc0 { color: #E6E6E6; } .pfdf-pre .rc1 { color: #66D9EF; } .pfdf-pre .rc2 { color: #A6E22E; } .pfdf-pre .rc3 { color: #FD971F; }
.pfdf-pre .get { color: #4DFF6B; text-decoration: underline; text-underline-offset: 3px; }
.pfdf-pre .rc4 { color: #F92672; } .pfdf-pre .rc5 { color: #AE81FF; } .pfdf-pre .rc6 { color: #E6DB74; } .pfdf-pre .rc7 { color: #38CCD1; }
.pfdf--api .pfdf-term, .pfdf--api .pfdf-tabs, .pfdf--api .pfdf-pre { background: #141414; border-color: #141414; }
.pfdf--api .pfdf-tabs { border-bottom-color: #FFC133; }
.pfdf--api .pfdf-tabs span, .pfdf--api .pfdf-tabs a { color: #FFC133; }
.pfdf--api .pfdf-tabs .on { color: #FF8A00; box-shadow: inset 0 -1px 0 #FF8A00; }
.pfdf--api .pfdf-pre { color: #FFC133; }
.pfdf--api .pfdf-pre .rc0 { color: #FF8A00; }
.pfdf--api .pfdf-pre .rc1, .pfdf--api .pfdf-pre .rc3, .pfdf--api .pfdf-pre .rc4, .pfdf--api .pfdf-pre .rc5 { color: #FF8100; }
.pfdf--api .pfdf-pre .rc2, .pfdf--api .pfdf-pre .rc7 { color: #FFA040; }
.pfdf-label, .pfdf-note { transition: opacity .3s ease; }
.pfdf-pick { position: relative; z-index: 1; display: flex; justify-content: center; gap: 40px; margin: 28px 0 0; padding-bottom: 34px; }
.pfdf-pick .way { position: relative; display: block; width: 30px; height: 30px; flex: 0 0 30px; text-decoration: none; color: inherit; }
.pfdf-pick .dot { width: 30px; height: 30px; border-radius: 50%; display: block; position: relative; box-shadow: inset 0 0 0 1px rgba(0,0,0,.14); }
.pfdf-pick .dot::after { content: ""; position: absolute; inset: -6px; border-radius: 50%; border: 1.5px solid transparent; transition: border-color .25s; }
.pfdf-pick .way--csv .dot { background: #0A9A4E; }
.pfdf-pick .way--api .dot { background: #CC6600; }
.pfdf-pick .way--db .dot { background: #ED86FF; }
.pfdf--db .pfdf-term, .pfdf--db .pfdf-pre { background: #090409; border-color: #111238; }
.pfdf--db .pfdf-tabs { background: #111238; border-bottom-color: #ED86FF; }
.pfdf--db .pfdf-tabs span, .pfdf--db .pfdf-tabs a { color: #ED86FF; }
.pfdf--db .pfdf-tabs .on { color: #07CE3B; box-shadow: inset 0 -1px 0 #07CE3B; }
.pfdf--db .pfdf-pre { color: #ED86FF; }
.pfdf--db .pfdf-pre .rc0, .pfdf--db .pfdf-pre .rc2 { color: #07CE3B; }
.pfdf--db .pfdf-pre .rc1, .pfdf--db .pfdf-pre .rc3 { color: #ED86FF; }
.pfdf--db .pfdf-pre .rc4 { color: #FF4FA3; }
.pfdf--db .pfdf-pre .rc5, .pfdf--db .pfdf-pre .rc7 { color: #B98CFF; }
.pfdf--db .pfdf-pre .rc6 { color: #F6C8FF; }
.pfdf--db .pfdf-pre .pfdf-native { color: #07CE3B; }   /* ON NATIVE DEVICE, its own colour (the owner, 2026-10-25) */
/* THE DB THEME (the owner, 2026-10-25): LARRY LLM's dark mode, purple, pink and bright green */
.pfdf-pick .way.on .dot::after { border-color: var(--active-color-01); }
.pfdf-pick .word { position: absolute; top: 44px; left: 50%; transform: translateX(-50%); white-space: nowrap; font: 600 12px/1 Helvetica, Arial, sans-serif; letter-spacing: .14em; text-transform: uppercase; color: var(--active-color-01); }
@media (max-width: 768px) { .pfdf-pre { font-size: 12px; } .pfdf-note { font-size: 15px; } }
"""



def main():
    given = json.load(sys.stdin)
    if given.get('do') != 'panel':
        raise SystemExit('PF DATA FABRIC does: panel')
    print(json.dumps(panel(given)))


if __name__ == '__main__':
    main()
