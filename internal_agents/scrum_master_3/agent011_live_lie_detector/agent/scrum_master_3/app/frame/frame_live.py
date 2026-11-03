"""THE LIVE, THE FRAME'S OWN (the owner 2026-10-27: "next item is the live / we add it to the replica"; "and it is global and universal for
all agents"; "the idea is the frame is not an agent / it holds agents / it does nothing on its own without an agent attached"), as the
original Scrum Master's (web/page.py follow, monitor, memory_line, system_line; web/app.py stream, sse):
THE STREAM, this page's own Server-Sent Events: the hello, every shell's row today, the X board, what runs now, the five tools, then each
new LARRYD log of this office's jobs as it is written, alive when quiet. It waits on the records' own change events (kqueue on this
office's own store, on LARRYD's database, where this office's jobs and logs are written, and on the knowledge store the office names: the
files alone, their writes alone), never on a clock asking again (POLLING IS FORBIDDEN).
THE PANEL'S DATA, the original's ACTIVE MONITORING (1 RIPGREP · FAST SEARCH, 2 SSE · LIVE STREAMING, 3 MANIFEST, 4 MEMORY · 3 WAY SWITCH,
5 SYSTEM), handed to the page to draw (web/templates). The machine's samplers run on a served page alone (SAMPLING, set by the launcher's
create(serve=True)); a check's app samples nothing. This file runs nothing, schedules nothing and holds no job: THE LIVE CHECK IS AN
AGENT (agent/agent003_live_live.py, the original's row 003) that reads this stream and says green or red.

THE LIVE IS THE REPLICA'S, NOT AN AGENT (the owner 2026-10-27 13:15: "live should be in replica not in the agent i was very clear about this";
11:12: "next item is the live / we add it to the replica" · "and it is global and universal for all agents"): the stream's own check is the
frame's (live, kick, check, the original's agent003_top_live rule word for word): on a served page that holds an agent, the frame looks at its own
stream FIRST seconds after the start and every INTERVAL seconds after (LOOK), and the X board's LIVE line reads that look; no slot of an agent, no
job, no schedule of its own. On a page holding no agent it looks at nothing."""
import datetime
import json
import os
import re
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.request
import zoneinfo

from frame import frame_replica as frame

SSE = {'retry_seconds': [3], 'alive_seconds': 25, **(((frame.read_json('global_config').get('transport') or {}).get('positions') or {}).get('SSE') or {})}   # the stream's retry and keep-alive, the platform's own transport words when it has them (global_config)
STREAMS = {'open': 0}   # ACTIVE MONITORING 2 SSE: the pages watching this stream now
_LOCK = threading.Lock()
SAMPLING = {'on': False}   # the machine's samplers (5 SYSTEM) run on a served page alone
POSITION_SAID = {0: 'NO POSITION', 1: 'SKILLS INDEX', 2: 'KNOWLEDGE STORE', 3: 'FACTS FAST SEARCH'}   # the 3 way switch's positions, the original's words
MEMORY_FRESH = 60   # seconds a route of the knowledge store is the switch's position, then IDLE
SEARCH_FRESH = 5   # seconds a facts fast search is SEARCHING NOW, then READY


# ---- the stream's framing and its address
def sse(events, retry):
    """THE PAGE'S OWN SERVER-SENT EVENTS (the original's web/app.py sse): when to open the line again, then each event as one data line."""
    yield f'retry: {int(retry) * 1000}\n\n'
    for e in events:
        yield f'data: {json.dumps(e)}\n\n'


def stream_url(port=None):
    """This page's own stream: its port (settings page) and its route (routes.json stream)."""
    return f"http://127.0.0.1:{int(port or frame.SETTINGS['page']['port'])}{frame.ROUTES['stream']}"


# ---- what the stream says: the rows, what runs now, the work
def _iso(text, zone=None):
    """A record's moment ('YYYY-MM-DD HH:MM:SS') as ISO with its zone, for the page's clocks: the pipeline stamps a record in UTC
    (system_updated_at), an agent's run in this machine's own time (started_at, ended_at: zone None); '' when none."""
    try:
        at = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return ''
    return (at.replace(tzinfo=zone) if zone else at.astimezone()).isoformat(timespec='seconds')


def marks(store, shells, rule, now=None):
    """EVERY SHELL'S ROW TODAY, as the X board reads it (one source, page.light_of): its light, its newest run's start, end and words.
    -> {shell id: {'slot', 'name', 'light', 'start', 'end', 'text'}}"""
    out = {}
    for sh in shells:
        job = sh.get('job') or {}
        if not job:
            continue
        run = (store.runs(sh['job_key'], 1) or [None])[0]
        out[str(sh['id'])] = {'slot': sh['slot'], 'name': job.get('data_full_name') or '', 'light': frame.light_of(job, rule, now),
                              'start': run['started_at'][11:16] if run else '', 'end': run['ended_at'][11:16] if run else '', 'text': frame.run_said(run) if run else ''}
    return out


def now_of(store, shells, zone):
    """WHAT RUNS NOW (the original's WORKING ON line): the job whose RUN is open (QUEUED, RUNNING), since when, how long it usually takes
    from its own past runs; else IDLE since the newest ended run, that run said as LAST (zone: the board's, its hours drawn by the page). -> dict"""
    last = None
    for sh in shells:
        job = sh.get('job') or {}
        if not job:
            continue
        if job.get('data_job_run_state') in ('QUEUED', 'RUNNING'):
            took = []
            for r in store.runs(sh['job_key'], 200):
                try:
                    took.append((datetime.datetime.fromisoformat(r['ended_at']) - datetime.datetime.fromisoformat(r['started_at'])).total_seconds())
                except (TypeError, ValueError):
                    pass
            usual = sorted(took)[len(took) // 2] if took else None
            said = '' if usual is None else 'USUALLY UNDER 1 MIN' if usual < 60 else f'USUALLY {int(round(usual / 60))} MIN'
            return {'word': 'WORKING', 'n': str(job.get('data_job_run') or ''), 'name': job.get('data_full_name') or '', 'since': _iso(job.get('system_updated_at'), datetime.timezone.utc), 'usual': said, 'last': None}
        run = (store.runs(sh['job_key'], 1) or [None])[0]
        if run and (last is None or run['ended_at'] > last['ended_at']):
            last = {**run, 'name': job.get('data_full_name') or ''}
    if last:
        return {'word': 'IDLE', 'n': '', 'name': '', 'since': _iso(last['ended_at']), 'usual': '',
                'last': {'name': last['name'], 'n': str(last['n'] or ''), 'at': last['ended_at'][11:16], 'ended': f"exit {last['exit']}"}}
    return {'word': 'IDLE', 'n': '', 'name': '', 'since': '', 'usual': '', 'last': None}


def work_of(board):
    """TODAY'S WORK N% DONE: the X board's green over its total (one source)."""
    green, total = (sum(line[k] for line in board['lines']) for k in ('green', 'total'))
    return {'green': green, 'total': total, 'percent': int(round(green * 100 / total)) if total else 0}


# ---- ACTIVE MONITORING, the five tools
def _kdb(conf):
    """A read-only connection to the knowledge store the office names (its facts: knowledge), or None."""
    path = os.path.expanduser(str((conf or {}).get('knowledge') or ''))
    if not path or not os.path.isfile(path):
        return None
    try:
        con = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=2)
        con.row_factory = sqlite3.Row
        con.execute('SELECT 1 FROM routes LIMIT 1')
        return con
    except sqlite3.Error:
        return None


def _moment(text):
    try:
        at = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return at if at.tzinfo else at.astimezone()


_WORD = re.compile(r"[a-z0-9][a-z0-9_'-]*")


def search_words(question):
    """The words a facts fast search looked for: lower case, each once, in order."""
    seen, out = set(), []
    for w in _WORD.findall(str(question or '').lower()):
        if len(w) < 2 or w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


def _last_route(con, where_sql='', params=()):
    try:
        return con.execute(f"SELECT * FROM routes WHERE source != 'test' {where_sql} ORDER BY id DESC LIMIT 1", params).fetchone()
    except sqlite3.Error:
        return None


def rg_line(conf, now=None):
    """ACTIVE MONITORING 1 RIPGREP · FAST SEARCH: the knowledge store's last facts fast search (its routes, position 3), read only:
    SEARCHING while it is this young (SEARCH_FRESH), else READY with when it last searched and the words it looked for."""
    out = {'state': 'READY', 'since': '', 'last_at': '', 'what': [], 'tool': 'FACTS FAST SEARCH'}
    con = _kdb(conf)
    if con is None:
        return out
    try:
        last = _last_route(con, 'AND position = 3')
    finally:
        con.close()
    if last is None:
        return out
    keys = last.keys()
    at = _moment(last['at'] if 'at' in keys else None)
    now = now or datetime.datetime.now().astimezone()
    if at is not None:
        out['last_at'] = at.isoformat(timespec='seconds')
        if (now - at).total_seconds() < SEARCH_FRESH:
            out.update(state='SEARCHING', since=out['last_at'])
    out['what'] = search_words(last['question'] if 'question' in keys else '')
    return out


def memory_line(conf, now=None):
    """ACTIVE MONITORING 4 MEMORY · 3 WAY SWITCH (the owner 2026-10-22: "the switch shows the position being used live and can only be in
    one of those 3 positions or idle"): the knowledge store's last route, its position while fresh (MEMORY_FRESH), else IDLE; today's
    routes by position. NOT WIRED when the office names no store."""
    con = _kdb(conf)
    if con is None:
        return {'wired': False, 'state': 'NOT WIRED', 'said': 'the 3 way switch is not wired yet: no route'}
    now = now or datetime.datetime.now().astimezone()
    try:
        last = _last_route(con)
        try:
            counts = {int(r[0] or 0): int(r[1]) for r in con.execute("SELECT position, count(*) FROM routes WHERE substr(at, 1, 10) = ? AND source != 'test' GROUP BY position", (now.date().isoformat(),))}
        except sqlite3.Error:
            counts = {}
    finally:
        con.close()
    today = {'routes': sum(counts.values()), 'skills index': counts.get(1, 0), 'knowledge store': counts.get(2, 0), 'facts fast search': counts.get(3, 0), 'none': counts.get(0, 0)}
    if last is None:
        return {'wired': True, 'state': 'IDLE', 'since': '', 'bullets': [], 'words': [], 'today': today, 'row': '', 'agent': '', 'at': ''}
    keys = last.keys()
    at = _moment(last['at'] if 'at' in keys else None)
    fresh = at is not None and (now - at).total_seconds() < MEMORY_FRESH
    position = int((last['position'] if 'position' in keys else 0) or 0)
    try:
        delivered = json.loads((last['delivered'] if 'delivered' in keys else '') or '[]') or []
    except ValueError:
        delivered = []
    bullets = [str(d.get('line') or '')[:300] for d in delivered if isinstance(d, dict)]
    state = POSITION_SAID.get(position, 'IDLE') if fresh and position else 'IDLE'
    return {'wired': True, 'state': state, 'since': at.isoformat(timespec='seconds') if at else '', 'today': today,
            'bullets': bullets if state != 'IDLE' else [], 'words': search_words(last['question'] if 'question' in keys else '') if state == 'FACTS FAST SEARCH' else [],
            'row': str((last['row'] if 'row' in keys else '') or ''), 'agent': str((last['agent'] if 'agent' in keys else '') or ''), 'at': at.isoformat(timespec='seconds') if at else ''}


def manifest_line(names):
    """ACTIVE MONITORING 3 MANIFEST: the platform's manifest template this page draws (settings reads manifest), its groups by name."""
    return {'file': os.path.basename(frame.PATHS['manifest']), 'listed': len(names), 'names': list(names)}


# ---- 5 SYSTEM, the machine (the original's sample_system, link_mbps, the offices' probe), sampled on a served page alone
SYSTEM_EVERY = 5   # seconds between two samples of the machine
LINK_EVERY = 60   # seconds between two readings of the link's speed (the Wi-Fi rate takes seconds to read)
OFFICES_EVERY = 15   # seconds between two looks at the offices
_SYSTEM = {'sample': None, 'thread': None, 'link': None}
_OFFICES = {'sample': None, 'thread': None}
_SYSTEM_LOCK = threading.Lock()


def _run(cmd, timeout=4):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def _gb(n):
    return round(n / 1024 ** 3, 1)


def sample_system(run=None, before=None, at=None, link=None):
    """ONE SAMPLE OF THE MACHINE (the owner 2026-10-22: "SYSTEM = CPU, MEMORY, DISK, NETWORK with totals"), from its own commands, nothing
    installed; ALL IN PERCENT (the owner 2026-10-22: "convert all to % so they all have the same measurement"). -> dict"""
    run = run or _run
    at = at if at is not None else datetime.datetime.now().timestamp()
    out = {'at': datetime.datetime.fromtimestamp(at).astimezone().isoformat(timespec='seconds')}
    try:
        cores = int(run(['sysctl', '-n', 'hw.ncpu']).strip())
        each = [float(x) for x in run(['ps', '-A', '-o', '%cpu=']).split() if re.fullmatch(r'[0-9.]+', x)]
        load = run(['sysctl', '-n', 'vm.loadavg']).replace('{', '').replace('}', '').split()
        if not each or len(load) < 3:
            raise ValueError('the machine said nothing')
        out['cpu'] = {'percent': round(min(100.0, sum(each) / max(cores, 1)), 1), 'cores': cores, 'load': [float(x) for x in load[:3]], 'load_percent': round(float(load[0]) / max(cores, 1) * 100, 1)}
    except (ValueError, IndexError):
        out['cpu'] = None
    try:
        total = int(run(['sysctl', '-n', 'hw.memsize']).strip())
        vm = run(['vm_stat'])
        size = int(re.search(r'page size of (\d+) bytes', vm).group(1))
        pages = {k.strip().lower(): int(v.strip().rstrip('.')) for k, v in re.findall(r'^([^:]+):\s+(\d+)\.?$', vm, re.M)}
        used = (pages.get('pages active', 0) + pages.get('pages wired down', 0) + pages.get('pages occupied by compressor', 0)) * size
        level = run(['sysctl', '-n', 'kern.memorystatus_vm_pressure_level']).strip()
        out['memory'] = {'used_gb': _gb(used), 'total_gb': _gb(total), 'percent': round(used / total * 100, 1), 'pressure': {'1': 'NORMAL', '2': 'WARNING', '4': 'CRITICAL'}.get(level, '')}
    except (ValueError, AttributeError, ZeroDivisionError):
        out['memory'] = None
    try:
        import shutil
        du = shutil.disk_usage('/')
        io = run(['iostat', '-Id']).split('\n')
        nums = [float(x) for x in io[2].split()] if len(io) > 2 else []
        moved = round(sum(nums[2::3]), 1) if nums else None
        out['disk'] = {'used_gb': _gb(du.used), 'total_gb': _gb(du.total), 'percent': round(du.used / du.total * 100, 1), 'moved_gb': round(moved / 1024, 1) if moved is not None else None}
    except (OSError, ValueError, IndexError):
        out['disk'] = None
    try:
        seen, rx, tx = set(), 0, 0
        for ln in run(['netstat', '-ib']).splitlines()[1:]:
            f = ln.split()
            if len(f) >= 10 and f[2].startswith('<Link#') and f[0] not in seen and not f[0].startswith('lo'):
                seen.add(f[0])
                rx += int(f[-5])
                tx += int(f[-2])
        net = {'in_gb': _gb(rx), 'out_gb': _gb(tx), 'rx': rx, 'tx': tx, 'in_rate_kbs': None, 'out_rate_kbs': None, 'link_mbps': link}
        if before and before.get('network') and before.get('t'):
            dt = max(at - before['t'], 0.001)
            net['in_rate_kbs'] = round(max(0, rx - before['network']['rx']) / 1024 / dt, 1)
            net['out_rate_kbs'] = round(max(0, tx - before['network']['tx']) / 1024 / dt, 1)
        if link and net['in_rate_kbs'] is not None:   # the rate as a share of the link (KB/s to Mb/s: 1024 * 8 / 1e6)
            net['in_percent'] = round(net['in_rate_kbs'] * 8192 / (link * 1e6) * 100, 1)
            net['out_percent'] = round(net['out_rate_kbs'] * 8192 / (link * 1e6) * 100, 1)
        out['network'] = net
    except (ValueError, IndexError):
        out['network'] = None
    out['t'] = at
    return out


def link_mbps(run=None):
    """THE NETWORK LINK'S SPEED in Mb/s: the default route's interface, its wired media or its Wi-Fi rate. -> float or None"""
    run = run or _run
    dev = re.search(r'interface:\s*(\S+)', run(['route', '-n', 'get', 'default']) or '')
    if not dev:
        return None
    media = re.search(r'media:.*?\((\d+)(G?)base', run(['ifconfig', dev.group(1)]) or '', re.I)
    if media:
        return float(media.group(1)) * (1000 if media.group(2) else 1)
    try:
        got = json.loads(run(['system_profiler', 'SPAirPortDataType', '-json'], timeout=40) or '{}')
        for x in got['SPAirPortDataType'][0]['spairport_airport_interfaces']:
            if x.get('_name') == dev.group(1):
                rate = (x.get('spairport_current_network_information') or {}).get('spairport_network_rate')
                return float(rate) if rate else None
    except (ValueError, KeyError, IndexError, TypeError):
        return None
    return None


def _link_loop():
    while True:
        _SYSTEM['link'] = link_mbps()
        time.sleep(LINK_EVERY)


def _system_loop():
    threading.Thread(target=_link_loop, name='link-sampler', daemon=True).start()
    while True:
        got = sample_system(before=_SYSTEM['sample'], link=_SYSTEM.get('link'))
        with _SYSTEM_LOCK:
            _SYSTEM['sample'] = got
        write_report('system', got)
        time.sleep(SYSTEM_EVERY)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None   # a door's redirect is the answer itself: read, never followed


def said_at(address, timeout=2):
    """The HTTP code an address of ours answers (a redirect read, never followed), or None when nothing answers in time."""
    try:
        with urllib.request.build_opener(_NoRedirect).open(address, timeout=timeout) as answer:
            return answer.status
    except urllib.error.HTTPError as e:
        return e.code
    except (OSError, ValueError):
        return None


def office_cards(conf=None, env=None):
    """THE OFFICES AND MINIS THIS BOX HOSTS, as the platform's global_config.json names them (generated, never typed): each with its port on
    this run's side, its home page and its API door. -> [{'name', 'kind', 'port', 'host', 'home', 'api'}]"""
    conf = frame.read_json('global_config') if conf is None else conf
    env = str(os.environ.get(conf.get('environment_variable', 'WID_ENV'), frame.SETTINGS['root_shape']['page']['environment']) if env is None else env)
    box, _, side = env.partition('.')
    b = (conf.get('boxes') or {}).get(box) or {}
    bind, slot, offices, minis = b.get('bind', '127.0.0.1'), bool(b.get('public')), [], []
    for key, o in (conf.get('offices') or {}).items():
        port = (o.get('ports') or {}).get(side)
        if port:
            host = o.get('host', bind)
            offices.append({'name': key.upper(), 'kind': 'office', 'port': int(port), 'host': host, 'home': f'http://{host}:{port}/{key}/{side}/en/app/{key}/home', 'api': f'http://{host}:{port}/api/'})
        mini = o.get('mini') or {}
        port = (mini.get('ports') or {}).get(side)
        if port and not slot:
            host = mini.get('host', bind)
            minis.append({'name': f'{key}-mini'.upper(), 'kind': 'mini', 'port': int(port), 'host': host, 'home': f'http://{host}:{port}/{key}-mini/{side}/en/app/mini/home', 'api': f'http://{host}:{port}/api/'})
    return offices + minis


def listeners(run=None):
    """{port: pid} of every listening TCP port of this machine, read once (lsof -F pn)."""
    import shutil
    said = (run or _run)([shutil.which('lsof') or '/usr/sbin/lsof', '-nP', '-iTCP', '-sTCP:LISTEN', '-F', 'pn'], timeout=5)
    found, pid = {}, None
    for line in (said or '').splitlines():
        if line.startswith('p'):
            pid = int(line[1:]) if line[1:].isdigit() else None
        elif line.startswith('n') and line.rpartition(':')[2].isdigit():
            found.setdefault(int(line.rpartition(':')[2]), pid)
    return found


def probe_offices(cards=None, ask=None, listening=None, at=None):
    """ONE LOOK AT THE OFFICES (the owner 2026-10-24: "the scrum master should always know what is up or down"): each card asked for its home
    page and its API door, all together; UP IS AN ANSWER under 500; the listeners read once for the PID."""
    from concurrent.futures import ThreadPoolExecutor
    cards = [dict(c) for c in (office_cards() if cards is None else cards)]
    ask = ask or said_at
    with ThreadPoolExecutor(max_workers=max(1, len(cards))) as together:
        homes = list(together.map(lambda c: ask(c['home']), cards))
        doors = list(together.map(lambda c: ask(c['api']), cards))
    pids = (listening or listeners)()
    for c, code, door in zip(cards, homes, doors):
        c.update(answer=code, up=isinstance(code, int) and code < 500, api_answer=door, api_up=isinstance(door, int) and door < 500, pid=pids.get(c['port']))
    up = sum(1 for c in cards if c['up'])
    state = 'NO OFFICE' if not cards else 'ALL UP' if up == len(cards) else f'{len(cards) - up} DOWN'
    return {'at': at or datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'cards': cards, 'up': up, 'down': len(cards) - up, 'state': state}


def _offices_loop():
    while True:
        try:
            got = probe_offices()
        except Exception as e:   # noqa: BLE001  (a look that fails is said on the row, never a dead sampler)
            got = {'at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'cards': [], 'up': 0, 'down': 0, 'state': f'NOT MEASURED: {type(e).__name__}: {e}'[:160]}
        with _SYSTEM_LOCK:
            _OFFICES['sample'] = got
        write_report('offices', got)
        time.sleep(OFFICES_EVERY)


def offices_line():
    """ACTIVE MONITORING 5 SYSTEM, THE OFFICES: the newest look, never waited for (a sampler of its own on a served page; before its
    first, or on a page never served: MEASURING)."""
    with _SYSTEM_LOCK:
        if _OFFICES['thread'] is None and SAMPLING['on']:
            _OFFICES['thread'] = threading.Thread(target=_offices_loop, name='offices-sampler', daemon=True)
            _OFFICES['thread'].start()
        got = _OFFICES['sample']
    return got or {'state': 'MEASURING', 'cards': [], 'up': 0, 'down': 0}


def system_line():
    """ACTIVE MONITORING 5 SYSTEM: the newest sample, never waited for (a sampler of its own every SYSTEM_EVERY seconds on a served page;
    before its first, or on a page never served: MEASURING); the offices on the same row."""
    with _SYSTEM_LOCK:
        if _SYSTEM['thread'] is None and SAMPLING['on']:
            _SYSTEM['thread'] = threading.Thread(target=_system_loop, name='system-sampler', daemon=True)
            _SYSTEM['thread'].start()
        got = _SYSTEM['sample']
    offices = offices_line()
    if not got:
        return {'state': 'MEASURING', 'offices': offices}
    return {**{k: v for k, v in got.items() if k != 't'}, 'state': 'MEASURED', 'offices': offices}


def monitor(conf, manifest_names):
    """ACTIVE MONITORING, the five tools now. -> {'rg', 'sse', 'manifest', 'memory', 'system'}"""
    with _LOCK:
        open_now = STREAMS['open']
    return {'rg': rg_line(conf), 'sse': {'state': 'BROADCASTING' if open_now else 'NO VIEWER', 'open': open_now},
            'manifest': manifest_line(manifest_names), 'memory': memory_line(conf), 'system': system_line()}


def panel(store, shells, conf, board, manifest_names, zone):
    """THE PANEL'S FIRST DRAW, for the page: what runs now, the five tools, today's work (the stream moves them from there)."""
    got = {'now': now_of(store, shells, zone), 'monitor': monitor(conf, manifest_names), 'work': work_of(board)}
    _PANEL['data'] = got
    write_report('panel', got)
    return {**got, 'rules': {**RULE, 'reports': reports_state()}}   # THE LIVE BLOCK'S RULES and its reports, drawn at its foot


# ---- THE STREAM
class Watch:
    """THE FILES WHOSE OWN CHANGE WAKES THE STREAM (kqueue, vnode events; never a clock asking again): each path, its -wal and its -journal,
    held open across the waits; one born later is taken up at the next wait (a wake or the keep-alive). Never a folder (a folder fires for
    every file beside the one that matters), never an attribute (the platform's own read touches its file): proven 2026-10-27."""
    FLAGS = ('KQ_NOTE_WRITE', 'KQ_NOTE_EXTEND', 'KQ_NOTE_DELETE', 'KQ_NOTE_RENAME')   # a record written, grown, gone or renamed; never an attribute (a read's touch is not a change: proven 2026-10-27, LARRYD's file)

    def __init__(self, paths):
        import select
        self.select, self.paths, self.fds, self.kq = select, [p for p in paths if p], {}, select.kqueue()

    def arm(self):
        s = self.select
        fflags = 0
        for name in self.FLAGS:
            fflags |= getattr(s, name)
        for p in self.paths:
            for q in (p, p + '-wal', p + '-journal'):
                if q not in self.fds and os.path.exists(q):
                    try:
                        fd = os.open(q, os.O_RDONLY | getattr(os, 'O_EVTONLY', 0))
                    except OSError:
                        continue
                    self.fds[q] = fd
                    self.kq.control([s.kevent(fd, filter=s.KQ_FILTER_VNODE, flags=s.KQ_EV_ADD | s.KQ_EV_CLEAR, fflags=fflags)], 0)

    def wait(self, seconds):
        """Blocks until one of the files changes, or seconds pass (the keep-alive). -> the descriptors that fired (empty: the keep-alive)"""
        self.arm()
        if not self.fds:   # nothing to watch at all: the keep-alive alone
            time.sleep(seconds)
            return set()
        return {ev.ident for ev in self.kq.control(None, 64, seconds)}

    def close(self):
        for fd in self.fds.values():
            os.close(fd)
        self.fds.clear()
        self.kq.close()


def follow(store, conf, board, manifest_names, rule, alive_every=None, watched=(), watch=None, more=None):
    """THE STREAM'S EVENTS (the original's follow): the hello, every shell's row today, the X board, what runs now, the five tools; then, the
    moment one of the watched files changes (this office's store, LARRYD's database, the knowledge store), each row that moved, the board
    when it changed, what runs now when it changed, each new LARRYD log of this office's jobs as a line, the tools when they changed; alive
    after alive_every quiet seconds. board: the X board now (one source, the page's); watch: a check's own waiter; more: what the frame's other parts send of their own ({event: value}, THE RED's reds: the original's stream
    sent its reds), first after the tools and then whenever it changed, looked at on every wake and every keep-alive."""
    alive_every = int(SSE['alive_seconds']) if alive_every is None else alive_every
    with _LOCK:
        STREAMS['open'] += 1
    try:
        yield from _follow(store, conf, board, manifest_names, rule, alive_every, [store.db_path, *watched], watch, more)
    finally:
        with _LOCK:
            STREAMS['open'] -= 1


def _follow(store, conf, board, manifest_names, rule, alive_every, paths, watch, more=None):
    zone = rule['zone']
    yield {'start': True}
    shells = store.board()
    rows = marks(store, shells, rule)
    yield {'rows': rows}
    x = board()
    yield {'board': x, 'work': work_of(x)}
    now = now_of(store, shells, zone)
    yield {'now': now}
    mon = monitor(conf, manifest_names)
    yield {'monitor': mon}
    extra = more() if more else {}
    for k, v in extra.items():
        yield {k: v}
    seen = {sh['job_key']: {r['id'] for r in store.runs(sh['job_key'], 5)} for sh in shells if sh.get('job')}
    watch = watch or Watch(paths)
    try:
        while True:
            fired = watch.wait(alive_every)
            said = False
            if fired:
                shells = store.board()
                rows_now = marks(store, shells, rule)
                moved = {k: v for k, v in rows_now.items() if rows.get(k) != v}
                if moved:
                    rows, said = rows_now, True
                    yield {'rows': moved}
                x_now = board()
                if x_now != x:
                    x, said = x_now, True
                    yield {'board': x, 'work': work_of(x)}
                now_now = now_of(store, shells, zone)
                if now_now != now:
                    now, said = now_now, True
                    yield {'now': now}
                for sh in shells:
                    if not sh.get('job'):
                        continue
                    had = seen.setdefault(sh['job_key'], set())
                    for r in reversed(store.runs(sh['job_key'], 5)):
                        if r['id'] not in had:
                            had.add(r['id'])
                            said = True
                            yield {'line': f"{(sh['job'] or {}).get('data_full_name') or sh['job_key']} · RUN {r['n']} · {r['started_at']} to {r['ended_at']} · exit {r['exit']}", 'said': frame.run_said(r)}
            if more:   # what the frame's other parts send (THE RED's reds), each when it changed
                extra_now = more()
                for k, v in extra_now.items():
                    if extra.get(k) != v:
                        said = True
                        yield {k: v}
                extra = extra_now
            mon_now = monitor(conf, manifest_names)
            if mon_now != mon:
                mon, said = mon_now, True
                yield {'monitor': mon}
            if not fired and not said:   # the keep-alive: quiet for alive_every seconds (a wake that moved nothing says nothing)
                yield {'alive': datetime.datetime.now().isoformat(timespec='seconds')}
    finally:
        watch.close()


# ---- THE LIVE'S OWN LOOK (the original's agent003_top_live rule, word for word; the owner 2026-10-25: "if live data is showig green. if not red") ----
SLOT = 'LIVE'   # the shape's slot the panel sits in (settings root_shape slots)
SECONDS = 5   # the most it waits for live data: the stream sends the board the moment it opens
INTERVAL = 300   # seconds between two looks (five minutes; his word changes it)
FIRST = 20   # seconds after the page is served to its first look: its page is up by then
AGAIN = 20   # seconds to the next look after a red one: one missed look never stands as the light for INTERVAL (the owner 2026-10-31: "it should be live data")
LOOK = {'state': '', 'text': '', 'at': ''}   # the last look: green, red, or '' before a first one


def live(url, opener=urllib.request.urlopen, seconds=SECONDS, clock_=time.monotonic):
    """The first live event the stream sends, its keys said (rows, board, a line, alive), or '' when none comes in time. Raises OSError when
    the stream cannot be opened."""
    end = clock_() + seconds
    with opener(url, timeout=seconds) as got:
        while clock_() < end:
            line = got.readline()
            if not line:
                return ''
            line = line.decode('utf-8', errors='replace').strip()
            if not line.startswith('data:'):
                continue
            try:
                event = json.loads(line[5:])
            except ValueError:
                continue
            if isinstance(event, dict) and not event.get('start'):   # the opening hello is not data
                return ', '.join(sorted(event)) or 'an event'
    return ''


def kick(url):
    """The one step when the stream is dark: this page started again, by its pid (never by a name pattern)."""
    port = url.rsplit(':', 1)[1].split('/')[0]
    return f'this page started again by its pid: lsof -t -iTCP:{port} -sTCP:LISTEN, SIGTERM, then agent/run page (seconds)'


def check(url=None, opener=urllib.request.urlopen):
    """THE LIVE'S ONE RULE: this page's own live stream read; live data in it, green; nothing, red, with the one step. -> (state, text)"""
    url = url or stream_url()
    try:
        got = live(url, opener)
    except OSError as e:
        return 'red', f"no live data: the page's live stream does not open ({url}: {type(e).__name__}) · {kick(url)}"
    if not got:
        return 'red', f"no live data: the page's live stream sent nothing in {SECONDS} s ({url}) · {kick(url)}"
    return 'green', f"live data showing: the page's live stream sends {got} ({url})"


def look(url=None, opener=urllib.request.urlopen):
    """ONE LOOK at this page's own stream, kept as the frame's state (LOOK) the X board's LIVE line reads. -> (state, text)"""
    state, text = check(url, opener)
    LOOK.update(state=state, text=text, at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    write_report('look', dict(LOOK))
    write_report('look_log', f"{LOOK['at']} · {state} · {text}")
    heal()
    return state, text


def watch(first=FIRST, every=INTERVAL, again=AGAIN):
    """The frame's look at its own stream on a served page holding an agent: FIRST seconds after the start, then every INTERVAL seconds, AGAIN
    seconds after a red one, a timer to the next look (never a poll of anything else). -> the first timer"""
    def go():
        state, _text = look()
        later = threading.Timer(again if state == 'red' else every, go)
        later.daemon = True
        later.start()
    t = threading.Timer(first, go)
    t.daemon = True
    t.start()
    return t


# ---- THE LIVE BLOCK'S RULES (the owner 2026-10-27 13:22: "the rules for this are outside sanity and replaced so they can be deleted and self heal if
# they are gone / add that to the rules for the live block"): his sentence first, then the rule; its reports named in schemas/reports.json ----
RULE = {'rule': "the rules for this are outside sanity and replaced so they can be deleted and self heal if they are gone. This page's own live stream "
                "read: live data in it, green; nothing, red, with the one step.",
        'fix': "every report is written again by its own writer within seconds and by the next look of the LIVE (self heal); a dark stream: this page "
               "started again by its pid.",
        'red': "the stream sends no live data within SECONDS, or a listed report is older than its max_age (the writer stopped).",
        'green': "the stream sends live data, and every listed report under ~/scratch/reports/<office>/live/ is present and fresh."}
with open(os.path.join(frame.SCHEMAS, 'reports.json'), encoding='utf-8') as _fh:
    REPORTS = json.load(_fh)   # THE REPORT LIST, the frame's (schemas/reports.json, the original's shape)
REPORT_ROOT = {'at': ''}   # a check's own root (a temp folder); else the list's root, written by a served page alone
_PANEL = {'data': None}


def report_root():
    """Where the LIVE's reports live: a check's own root, else the list's (outside ~/virtual_sanity) on a served page; '' when nothing is written."""
    if REPORT_ROOT['at']:
        return REPORT_ROOT['at']
    return os.path.expanduser(REPORTS['root'].replace('{office}', frame.NAME)) if SAMPLING['on'] else ''


def report_path(entry, root):
    return entry['path'].replace('{root}', root).replace('{office}', frame.NAME)


def write_report(name, data):
    """ONE REPORT WRITTEN, replaced whole (a log: one line added); its folder made again when it is gone (self heal). -> its path, '' when nothing is written"""
    root = report_root()
    entry = next(e for e in REPORTS['reports'] if e['name'] == name)
    if not root or data is None:
        return ''
    path = report_path(entry, root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if entry['kind'] == 'appended':
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write((data if isinstance(data, str) else json.dumps(data, default=str)) + '\n')
    else:
        tmp = path + '.writing'
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, default=str)
        os.replace(tmp, path)
    return path


def heal():
    """THE NEXT LOOK WRITES EVERY REPORT IT HOLDS AGAIN (the owner: "so they can be deleted and self heal if they are gone")."""
    for name, held in (('system', _SYSTEM['sample']), ('offices', _OFFICES['sample']), ('panel', _PANEL['data'])):
        write_report(name, held)


def reports_state(now=None):
    """THE LIVE'S REPORTS NOW: each listed one present and fresh (GREEN), gone (NOT WRITTEN YET, never an error) or older than its max_age (RED, the
    writer stopped); the whole: RED when one is red, NOT WRITTEN YET when one is missing, else GREEN. -> {'state', 'rows'}"""
    root = report_root()
    now = now or time.time()
    rows = []
    for e in REPORTS['reports']:
        path = report_path(e, root) if root else e['path']
        try:
            age = (now - os.path.getmtime(path)) / 3600 if root else None
        except OSError:
            age = None
        state = 'NOT WRITTEN YET' if age is None else 'RED' if e['max_age'] is not None and age > e['max_age'] else 'GREEN'
        rows.append({'name': e['name'], 'path': path, 'state': state})
    words = [r['state'] for r in rows]
    return {'state': 'RED' if 'RED' in words else 'NOT WRITTEN YET' if 'NOT WRITTEN YET' in words else 'GREEN', 'rows': rows}


def live_word():
    """THE X BOARD'S LIVE ITEM: red when the last look was red or a report is older than its max_age; green when the look was green; else not seen."""
    if LOOK['state'] == 'red' or reports_state()['state'] == 'RED':
        return 'red'
    return LOOK['state']


# ---- THE ONE LIVE STATUS PLACE (the owner 2026-10-27: "each one needs a status in the db and live streaming from the status these are all under live
# for a reason / not 5 minutes not anything else / that is total bullshit and not LIVE / what we learned before you can have a status location in the
# scrum master db and then the sse streaming is tied to that one place / then they all just update that single db based on a trigger"): the table
# live_status of the office's own database (declared in instance/<office>.json), written by ONE watcher thread on a trigger alone (the kernel's own
# file events, kqueue), each row only when its light, summary, why or step changed; the page's stream wakes on that database's write. The page hands
# the items (the frame never imports an agent): [{'key', 'name', 'triggers', 'look'}]; a trigger is a file path, a folder path ending in '/', 'ports'
# (the office hosts answering: the one honest probe, a dead host writes nothing) or 'status:<key>' (another row of live_status changing). ----
STATUS_TABLE = 'live_status'
STATES = ('GREEN', 'RED', 'OFF')
FIELDS = ('state', 'summary', 'why', 'step')   # what a look says; a row is written only when one of them changed
DEBOUNCE = 0.3   # seconds a trigger waits for the burst it belongs to (an editor's or a commit's many writes: one look)
DEBOUNCE_MOST = 2.0   # never later than this after the first trigger of a burst
HEARTBEAT_EVERY = 60   # seconds between two heartbeats written to the 'watcher' row (checked_at), never more often
HEARTBEAT_STALE = 180   # a heartbeat older than this: the watcher is dead (watcher_alive False; the page's LIVE red)
PORTS_EVERY = 5   # seconds between two TCP looks at the office hosts (approved by the owner as the one exception)
PORT_SECONDS = 0.5   # each connect's most
TREE_FDS = 4000   # the most descriptors one folder trigger holds (its folders and files); more: its folders alone, then its top folders and their children
SKIP_DIRS = ('.git', '__pycache__', 'node_modules')   # never descended into below a folder trigger (a cache's churn is no change of the tree's own)
FD_RESERVE = 256   # descriptors the watcher never takes: the page's databases, sockets and files (launchd starts a job at 256; the watcher once took 252 of them and every database open failed, 2026-10-27)
OPEN_MAX = 10240   # the most a macOS process may raise its soft open-file limit to when the hard one is unlimited
NY = zoneinfo.ZoneInfo('America/New_York')


def _fd_room():
    """the process's open-file limit, its soft one first raised to its hard one (launchd's 256 is the soft one alone) -> the soft limit now"""
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    want = OPEN_MAX if hard == resource.RLIM_INFINITY else min(hard, OPEN_MAX)
    if soft != resource.RLIM_INFINITY and soft < want:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))
            soft = want
        except (ValueError, OSError):
            pass
    return OPEN_MAX if soft == resource.RLIM_INFINITY else soft
_WATCHERS = {}   # the store's real path -> its one watcher in this process
_WATCHERS_LOCK = threading.Lock()


def _ny_now():
    return datetime.datetime.now(NY).isoformat(timespec='seconds')


def status_declared(tables=None):
    """the live_status table as the office's schema declares it (instance/<office>.json)"""
    for t in (tables or frame.schema())['tables']:
        if t['name'] == STATUS_TABLE:
            return t
    raise LookupError(f'{STATUS_TABLE} is not declared in instance/{frame.NAME}.json')


def _open_rw(store_path, table):
    """the writer's connection, its table made when it is missing (the store grows only its first table; this one is the watcher's)"""
    con = sqlite3.connect(store_path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute(frame.create_sql(table))
    con.commit()
    return con


def _open_ro(store_path):
    import urllib.parse
    con = sqlite3.connect('file:' + urllib.parse.quote(os.path.abspath(store_path)) + '?mode=ro', uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def statuses(store_path):
    """EVERY ROW OF THE ONE STATUS PLACE, read only, in key order; the in-memory checked_at of this process's watcher laid over (the last look, never
    written: no write churn). [] when the store or the table is not there yet. -> [{'key', 'name', 'state', 'summary', 'why', 'step', 'changed_at', 'checked_at', 'trigger'}]"""
    if not os.path.exists(store_path):
        return []
    try:
        con = _open_ro(store_path)
        try:
            rows = [dict(r) for r in con.execute(f'SELECT * FROM "{STATUS_TABLE}" ORDER BY key')]
        finally:
            con.close()
    except sqlite3.OperationalError:   # no table yet (no watcher has opened this store)
        return []
    w = _WATCHERS.get(os.path.realpath(store_path))
    if w:
        for r in rows:
            if r['key'] in w.checked:
                r['checked_at'] = w.checked[r['key']]
    return rows


def status(store_path, key):
    """ONE ROW of the status place by its key, read only; None when it is not there."""
    return next((r for r in statuses(store_path) if r['key'] == key), None)


def watcher_alive(store_path, now=None):
    """THE WATCHER'S HEARTBEAT: True when its row is GREEN and its heartbeat (the 'watcher' row's checked_at, written once a minute) is younger than
    HEARTBEAT_STALE seconds; False otherwise (no watcher, a dead thread: the page's LIVE red)."""
    if not os.path.exists(store_path):
        return False
    try:
        con = _open_ro(store_path)
        try:
            row = con.execute(f'SELECT state, checked_at, changed_at FROM "{STATUS_TABLE}" WHERE key = ?', ('watcher',)).fetchone()
        finally:
            con.close()
    except sqlite3.OperationalError:
        return False
    if not row or row['state'] != 'GREEN':
        return False
    try:
        beat = datetime.datetime.fromisoformat(row['checked_at'] or row['changed_at'])
    except (TypeError, ValueError):
        return False
    return ((now or datetime.datetime.now(NY)) - beat).total_seconds() < HEARTBEAT_STALE


def office_ports(conf=None):
    """THE OFFICE HOSTS, as agent004_live_audit's "offices online" reads them (global_config offices): each office's rnd port, each mini's rnd port,
    wid's pf port. -> [(name, port)]"""
    conf = frame.read_json('global_config') if conf is None else conf
    out = []
    for office, o in (conf.get('offices') or {}).items():
        out.append((office, int(o['ports']['rnd'])))
        if isinstance(o.get('mini'), dict) and o['mini'].get('ports'):
            out.append((f'{office}-mini', int(o['mini']['ports']['rnd'])))
    wid = (conf.get('offices') or {}).get('wid') or {}
    if (wid.get('ports') or {}).get('pf') and wid['ports']['pf'] != wid['ports'].get('rnd'):
        out.append(('wid pf', int(wid['ports']['pf'])))
    return out


def ports_answering(hosts=None, seconds=PORT_SECONDS):
    """ONE TCP LOOK AT THE OFFICE HOSTS, all together (a connect within seconds each). -> frozenset of the ports that answered"""
    import socket
    from concurrent.futures import ThreadPoolExecutor
    hosts = office_ports() if hosts is None else hosts

    def answers(port):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=seconds):
                return True
        except OSError:
            return False
    if not hosts:
        return frozenset()
    with ThreadPoolExecutor(max_workers=len(hosts)) as together:
        said = list(together.map(lambda h: answers(h[1]), hosts))
    return frozenset(p for (_, p), up in zip(hosts, said) if up)


def ports_now(store_path):
    """the office ports this process's watcher of that store saw answering at its last look (None: no watcher, or no item watches 'ports')"""
    w = _WATCHERS.get(os.path.realpath(store_path))
    return None if w is None else w.ports


class _Watcher:
    """THE ONE WATCHER OF ONE STORE: one daemon thread on one kqueue; a file trigger holds the file and its folder (an atomic write replaces the file:
    the folder sees it, the file is taken up again); a folder trigger holds its folders and files (TREE_FDS the most; more: its folders alone, then its
    top folders and their children, said on the watcher's row); the store and its -wal/-journal (another writer's row: 'status:<key>'); 'ports' a TCP
    look every PORTS_EVERY seconds."""

    def __init__(self, store_path, items, table, hosts=None, on_change=None):
        import select
        self.on_change = on_change   # the page's own hook, called when an item's LIGHT flips (never on an unchanged look): on_change(key, got, old_state, trigger)
        self.s, self.store_path, self.table = select, store_path, table
        self.items = {it['key']: it for it in items}
        self.order = [it['key'] for it in items]
        self.checked = {}   # key -> the last look's time (memory alone)
        self.seen = {}   # key -> the row's (state, summary, why, step) as last read from the store
        self.pending = {}   # key -> [first, due, trigger]
        self.fds = {}   # fd -> (kind, path, trigger)  kind: file, parent, dir, store
        self.paths = {}   # (kind, path, trigger) -> fd
        self.stamps = {}   # a file trigger's (inode, size, mtime) when last seen
        self.notes = []   # what the watcher says of itself (a big tree's fallback)
        self.hosts = hosts
        self.ports = None
        self.kq = select.kqueue()
        self.room = _fd_room()   # the descriptors this process may hold; a folder trigger leaves FD_RESERVE of them
        self.fflags = select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND | select.KQ_NOTE_ATTRIB | select.KQ_NOTE_DELETE | select.KQ_NOTE_RENAME
        self.store_fflags = self.fflags & ~select.KQ_NOTE_ATTRIB   # the store: never an attribute (a reader's touch is no row written; Watch's own lesson)
        self.tree = {}   # a folder trigger -> how much of it is held: 'all' (folders and files), 'dirs' (folders alone), 'top' (top folders and their children)
        self.by_trigger = {}   # trigger -> [item keys]
        for it in items:
            for t in it.get('triggers') or ():
                self.by_trigger.setdefault(t, []).append(it['key'])
        self.thread = None

    # -- the descriptors
    def _hold(self, kind, path, trigger):
        ident = (kind, path, trigger)
        if ident in self.paths:
            return True
        try:
            fd = os.open(path, os.O_RDONLY | getattr(os, 'O_EVTONLY', 0))
        except OSError:
            return False
        self.fds[fd], self.paths[ident] = ident, fd
        self.kq.control([self.s.kevent(fd, filter=self.s.KQ_FILTER_VNODE, flags=self.s.KQ_EV_ADD | self.s.KQ_EV_CLEAR, fflags=self.store_fflags if kind == 'store' else self.fflags)], 0)
        return True

    def _drop(self, fd):
        ident = self.fds.pop(fd, None)
        if ident:
            self.paths.pop(ident, None)
        try:
            os.close(fd)   # closing a descriptor removes its kevent
        except OSError:
            pass

    @staticmethod
    def _stamp(path):
        try:
            st = os.stat(path)
            return (st.st_ino, st.st_size, st.st_mtime_ns, st.st_mode, st.st_uid, getattr(st, 'st_flags', 0))   # its owner and flags too: a lock (chflags schg/uchg) or a mark handed to root is a change of its own
        except OSError:
            return None

    def _arm_file(self, path, trigger):
        self._hold('parent', os.path.dirname(path) or '.', trigger)
        self._hold('file', path, trigger)
        self.stamps[trigger] = self._stamp(path)

    def _arm_tree(self, root, trigger):
        most = max(0, min(TREE_FDS, self.room - FD_RESERVE - len(self.fds)))   # never the descriptors the page's databases need
        dirs, files = [], []
        for here, subdirs, names in os.walk(root):
            subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS)
            dirs.append(here)
            files += [os.path.join(here, n) for n in names]
            if len(dirs) > most:
                break
        if len(dirs) + len(files) <= most:
            held, self.tree[trigger] = dirs + files, 'all'
        elif len(dirs) <= most:
            held, self.tree[trigger] = dirs, 'dirs'
            self.notes.append(f'{root}: its {len(dirs)} folders watched, not its {len(files)} files (a file written in place unseen; added, removed or replaced seen)')
        else:
            top = [root] + [os.path.join(root, d) for d in sorted(os.listdir(root)) if os.path.isdir(os.path.join(root, d)) and d not in SKIP_DIRS]
            held = top + [os.path.join(t, d) for t in top[1:] for d in sorted(os.listdir(t)) if os.path.isdir(os.path.join(t, d)) and d not in SKIP_DIRS]
            held, self.tree[trigger] = held[:most], 'top'
            self.notes.append(f'{root}: too big ({len(dirs)}+ folders): its top folders and their children watched ({len(held)})')
        for p in held:
            self._hold('dir', p, trigger)

    def _arm_store(self):
        for q in (self.store_path, self.store_path + '-wal', self.store_path + '-journal'):
            if os.path.exists(q):
                self._hold('store', q, '')

    def arm(self):
        for t in self.by_trigger:
            if t == 'ports' or t.startswith('status:'):
                continue
            if t.endswith('/'):
                self._arm_tree(os.path.expanduser(t).rstrip('/') or '/', t)
            else:
                self._arm_file(os.path.expanduser(t), t)
        self._arm_store()

    # -- the triggers
    def _wake(self, trigger, now):
        for key in self.by_trigger.get(trigger, ()):
            p = self.pending.get(key)
            if p:
                p[1] = min(p[0] + DEBOUNCE_MOST, now + DEBOUNCE)
            else:
                self.pending[key] = [now, now + DEBOUNCE, trigger]

    def _event(self, ev, now):
        ident = self.fds.get(ev.ident)
        if not ident:
            return
        kind, path, trigger = ident
        gone = ev.fflags & (self.s.KQ_NOTE_DELETE | self.s.KQ_NOTE_RENAME)
        if kind == 'store':
            if gone:
                self._drop(ev.ident)
            self._store_changed(now)
            return
        if kind == 'file':
            if gone:   # an atomic write replaced it: the old one let go, the new one taken up below
                self._drop(ev.ident)
            stamp = self._stamp(path)
            moved = stamp != self.stamps.get(trigger)
            self.stamps[trigger] = stamp
            self._hold('file', path, trigger)
            if moved or ev.fflags & ~self.s.KQ_NOTE_ATTRIB:   # an attribute alone counts only when the file's own stamp moved (a reader's touch is no change)
                self._wake(trigger, now)
            return
        if kind == 'parent':   # its folder moved: only the file's own change counts
            fpath = os.path.expanduser(trigger)
            stamp = self._stamp(fpath)
            if stamp != self.stamps.get(trigger):
                self.stamps[trigger] = stamp
                self._hold('file', fpath, trigger)
                self._wake(trigger, now)
            return
        # a folder (or a file) of a folder trigger: one gone let go; a folder's new children held, as much of the tree as it holds
        if gone:   # replaced (an atomic write) or gone: let go, the new one taken up when it is there
            self._drop(ev.ident)
            if os.path.exists(path):
                self._hold('dir', path, trigger)
        elif kind == 'dir' and os.path.isdir(path) and self.tree.get(trigger) in ('all', 'dirs'):
            try:
                names = [n for n in os.listdir(path) if n not in SKIP_DIRS]
            except OSError:
                names = []
            held = sum(1 for k in self.paths if k[2] == trigger)
            for n in names:
                child = os.path.join(path, n)
                if held >= TREE_FDS:
                    break
                if ('dir', child, trigger) not in self.paths and (self.tree[trigger] == 'all' or os.path.isdir(child)) and self._hold('dir', child, trigger):
                    held += 1
        self._wake(trigger, now)

    def _store_changed(self, now):
        """another writer's row (or this one's): a row whose light, summary, why or step moved wakes the items that list 'status:<key>'"""
        self._arm_store()
        try:
            con = _open_ro(self.store_path)
            try:
                rows = {r['key']: tuple(r[f] or '' for f in FIELDS) for r in con.execute(f'SELECT * FROM "{STATUS_TABLE}"')}
            finally:
                con.close()
        except sqlite3.Error:
            return
        for key, said in rows.items():
            if self.seen.get(key) != said:
                self.seen[key] = said
                self._wake('status:' + key, now)

    # -- the looks and the one write
    def _look(self, key):
        it = self.items[key]
        try:
            got = it['look']() or {}
            state = str(got.get('state') or '').upper()
            if state not in STATES:
                return {'state': 'RED', 'summary': f"{it.get('name') or key}: its look said no light", 'why': f'state {got.get("state")!r} is none of {", ".join(STATES)}', 'step': ''}
            return {'state': state, **{f: str(got.get(f) or '') for f in FIELDS[1:]}}
        except Exception as e:   # noqa: BLE001  (a look that fails is RED with its one line, never a dead watcher)
            line = f'{type(e).__name__}: {e}'.splitlines()[0][:300] if str(e) else type(e).__name__
            return {'state': 'RED', 'summary': f"{it.get('name') or key}: its look failed", 'why': line, 'step': ''}

    def _write(self, con, key, name, got, trigger, now_iso):
        """the row written ONLY when its light, summary, why or step changed. -> True when written"""
        old = con.execute(f'SELECT state, summary, why, step FROM "{STATUS_TABLE}" WHERE key = ?', (key,)).fetchone()
        new = tuple(got[f] for f in FIELDS)
        if old and tuple(old[f] or '' for f in FIELDS) == new:
            return False
        con.execute(f'INSERT INTO "{STATUS_TABLE}" (key, name, state, summary, why, step, changed_at, checked_at, trigger) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) '
                    'ON CONFLICT(key) DO UPDATE SET name = excluded.name, state = excluded.state, summary = excluded.summary, why = excluded.why, '
                    'step = excluded.step, changed_at = excluded.changed_at, checked_at = excluded.checked_at, trigger = excluded.trigger',
                    (key, name, *new, now_iso, now_iso, trigger))
        con.commit()
        return True

    def _due(self, con, now):
        for key in [k for k, p in self.pending.items() if p[1] <= now]:
            trigger = self.pending.pop(key)[2]
            got = self._look(key)
            now_iso = _ny_now()
            self.checked[key] = now_iso
            was = con.execute(f'SELECT state FROM "{STATUS_TABLE}" WHERE key = ?', (key,)).fetchone()
            was = was['state'] if was else None
            if self._write(con, key, self.items[key].get('name') or key, got, trigger, now_iso):
                if self.on_change and was != got['state']:   # A FLIP (or its first row ever): the page's hook, once; a hook that fails never stops the watcher
                    try:
                        self.on_change(key, got, was, trigger)
                    except Exception as e:   # noqa: BLE001
                        self.notes.append(f'{key}: its flip hook failed ({type(e).__name__}: {e})'.splitlines()[0][:200])
                self._store_changed(time.monotonic())   # its dependents woken at once (the store's own event follows and finds nothing new)

    def _beat(self, con, first=False):
        now_iso = _ny_now()
        said = {'state': 'GREEN', 'summary': f'watching {len(self.items)} items', 'why': ' · '.join(self.notes), 'step': ''}
        if first:
            self._write(con, 'watcher', 'watcher', said, 'start', now_iso)
        con.execute(f'UPDATE "{STATUS_TABLE}" SET checked_at = ? WHERE key = ?', (now_iso, 'watcher'))
        con.commit()
        self.checked['watcher'] = now_iso

    def _probe(self, now):
        got = ports_answering(self.hosts)
        if self.ports is not None and got != self.ports:
            self._wake('ports', now)
        self.ports = got

    def loop(self):
        con = None
        try:
            con = _open_rw(self.store_path, self.table)
            self.arm()
            self._beat(con, first=True)
            self._store_changed(time.monotonic())   # what the store holds now, so a row is a trigger only when it moves
            for key in self.order:   # every item looked at once at the start
                self.pending[key] = [0, 0, 'start']
            if 'ports' in self.by_trigger:
                self.ports = ports_answering(self.hosts)
            next_beat, next_ports = time.monotonic() + HEARTBEAT_EVERY, time.monotonic() + PORTS_EVERY
            while True:
                now = time.monotonic()
                self._due(con, now)
                now = time.monotonic()
                if now >= next_beat:
                    self._beat(con)
                    next_beat = now + HEARTBEAT_EVERY
                if 'ports' in self.by_trigger and now >= next_ports:
                    self._probe(now)
                    next_ports = time.monotonic() + PORTS_EVERY
                waits = [next_beat - now] + ([next_ports - now] if 'ports' in self.by_trigger else []) + [p[1] - now for p in self.pending.values()]
                for ev in self.kq.control(None, 64, max(0.0, min(waits))):
                    self._event(ev, time.monotonic())
        except Exception as e:   # noqa: BLE001  (the watcher's own death said on its row: the page's LIVE red)
            try:
                if con is not None:
                    self._write(con, 'watcher', 'watcher', {'state': 'RED', 'summary': 'the watcher stopped', 'why': f'{type(e).__name__}: {e}'.splitlines()[0][:300], 'step': 'start the page again'}, 'fault', _ny_now())
            finally:
                with _WATCHERS_LOCK:
                    if _WATCHERS.get(os.path.realpath(self.store_path)) is self:
                        _WATCHERS.pop(os.path.realpath(self.store_path), None)
                for fd in list(self.fds):
                    self._drop(fd)
                self.kq.close()
                if con is not None:
                    con.close()


def start_watch(store_path, items, tables=None, hosts=None, on_change=None):
    """THE ONE WATCHER OF THIS STORE (the page hands its items: [{'key', 'name', 'triggers': [...], 'look': callable -> {'state', 'summary', 'why',
    'step'}]}): one daemon thread, every item looked at once at the start, then each on its own triggers alone (a file path, a folder path ending in
    '/', 'ports', 'status:<key>'), its row written only when it changed. A second start for the same store does nothing. tables: a check's own
    declaration; hosts: a check's own [(name, port)] for 'ports'; on_change(key, got, old_state, trigger): called in the watcher's thread when an item's
    light flips (GREEN, RED, OFF; None before its first row), never on an unchanged look. -> the watcher (the one already running when there is one)"""
    real = os.path.realpath(store_path)
    with _WATCHERS_LOCK:
        if real in _WATCHERS:
            return _WATCHERS[real]
        keys = [it['key'] for it in items]
        if 'watcher' in keys or len(set(keys)) != len(keys):
            raise ValueError("an item's key is twice, or is 'watcher' (the watcher's own row)")
        w = _Watcher(store_path, items, status_declared(tables), hosts, on_change)
        w.thread = threading.Thread(target=w.loop, name=f'live-status-{os.path.basename(store_path)}', daemon=True)
        _WATCHERS[real] = w
        w.thread.start()
    return w
