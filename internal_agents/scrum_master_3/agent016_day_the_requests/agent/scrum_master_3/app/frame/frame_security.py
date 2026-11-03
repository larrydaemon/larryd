"""THE SECURITY, THE FRAME'S OWN (the owner 2026-10-27: put security "under live and in the replica because its not for a specific agent";
"the most important lesson we had in the past if its turned off it is not a red"; "nothing can depend on the orginal. we need to update
all"), the rule of the original Scrum Master's row 016 SECURITY (2026-10-23: "this if off it can never be red and if on and it has items its
red. so how can it not be more simple") on the office's own records alone: NOTHING HERE READS THE ORIGINAL (no database of its, no settings of
its, no findings table, no SECURITY list, no runner log of its).
THE SWITCH: the office's own settings (schemas/settings.json "security": {"scan": false}); absent, or anything but exactly true: OFF.
THE FINDINGS: what the scan itself writes and nothing else: the Claude security tool leaves a report folder (CLAUDE-SECURITY-<YYYYMMDD>-<HHMMSS>)
at the top of the tree it scanned, its findings in CLAUDE-SECURITY-RESULTS.jsonl, one JSON object a line (security.tree, security.folders,
security.results name them; the original's defaults when absent). No folder there: "no scan results here", never red while off.
THIS FILE NEVER STARTS A SCAN (slow, costs tokens): it reads the folders a scan leaves, and asks pgrep alone whether one runs now. It writes
nothing, schedules nothing and holds no job. No routes, no templates: the page wires look() and panel_html()."""
import datetime
import glob
import json
import os
import re
import subprocess
import zoneinfo

from frame import frame_replica as frame

KEY = 'security'   # the office's settings key: {"scan": false, ...}
DEFAULTS = {'scan': False, 'tree': '~/virtual_workspace', 'folders': 'CLAUDE-SECURITY-*', 'results': 'CLAUDE-SECURITY-RESULTS.jsonl',
            'zone': 'America/New_York', 'reset': '07:00'}   # scan: his switch (default OFF); where the scan leaves its folders; the day's start (the original's)
SCAN_PROCESS = 'claude-security:claude-security'   # the scan tool's own command line words (read by pgrep alone)
HAND = 'YOUR 3 MIN: '
SLOT = 'LIVE'   # drawn under the live
SEVERITIES = ('critical', 'high', 'medium', 'low', 'info')
FOLDER_TIME = re.compile(r'(\d{8})-(\d{6})$')

ITEMS_STEP = ("fix the finding(s) the newest scan names, or set security.scan false in this office's settings.json "
              "(off is never red: your rule 2026-10-23)")
OFF_STEP = ("set security.scan false in this office's settings.json (off is never red: your rule 2026-10-23); the scan again is never "
            "this step: a scan is started by hand and runs for hours")

# ---- THE SECURITY BLOCK'S RULES: his words first, then the rule (the parts data_job_rule, _fix, _red, _green, as frame_live's RULE) ----
RULE = {'rule': "security scan on = green, security scan off = green, security issue list = 0 then green, security issue list = 1+ then red (the owner 2026-10-27). The switch only says whether the scan runs: this office's settings "
                "security.scan off (or absent), the scan never starts and this block is off, whatever a scan left (said as words). On: red when "
                "the newest scan's results hold findings, red when no clean scan ran today; green when a scan ran today whole and found nothing. "
                "Nothing depends on the original: the frame reads only the folders the scan itself writes, and never starts a scan.",
        'fix': "every red is one press within 3 minutes: fix the findings the newest scan names, or set security.scan false in this office's "
               "settings.json (off is never red). The scan again is never the step: it is started by hand and runs for hours.",
        'red': "security.scan is exactly true AND (the newest report folder's results file holds 1 or more findings; OR no report folder of "
               "today (since the day's reset); OR today's newest folder has no results file that reads whole (running now, or broken)).",
        'green': "security.scan is exactly true AND the newest report folder (CLAUDE-SECURITY-* at the top of security.tree) is of today AND its "
                 "CLAUDE-SECURITY-RESULTS.jsonl reads whole AND holds 0 findings. security.scan off or absent is 'off', never red."}


def conf_of(conf=None):
    """The office's security settings over the defaults (frame.SETTINGS[KEY]; a check hands its own)."""
    got = (frame.SETTINGS.get(KEY) if conf is None else conf) or {}
    return {**DEFAULTS, **(got if isinstance(got, dict) else {})}


def switched_on(conf):
    return conf.get('scan') is True


def _zone(conf):
    return zoneinfo.ZoneInfo(str(conf['zone']))


def began(conf, now=None):
    """The start of today's day: the reset hour in his zone (the original's cycle)."""
    zone = _zone(conf)
    h, m = (int(x) for x in str(conf['reset']).split(':'))
    reset = datetime.timedelta(hours=h, minutes=m)
    local = (now or datetime.datetime.now(datetime.timezone.utc)).astimezone(zone)
    day = (local - reset).date()
    return datetime.datetime.combine(day, datetime.time(), zone) + reset


def findings_of(path):
    """A scan's findings file (one JSON object a line) -> [{id, title, file, line, severity}]; a line that is no JSON object makes the whole
    file unread (ValueError): half a list is never the list. Everything in it is data, cut short."""
    out = []
    with open(path, encoding='utf-8') as fh:
        whole = fh.read()
    for n, raw in enumerate(whole.splitlines(), 1):
        if not raw.strip():
            continue
        rec = json.loads(raw)
        if not isinstance(rec, dict):
            raise ValueError(f'line {n} is no finding')
        text = lambda *keys: next((str(rec[k]).strip() for k in keys if isinstance(rec.get(k), (str, int)) and str(rec[k]).strip()), '')
        line = rec.get('line')
        out.append({'id': text('claudeSecurityPluginFindingId', 'id')[:80] or f'line-{n}', 'title': text('title', 'category', 'summary')[:160],
                    'file': text('file')[:300], 'line': line if isinstance(line, int) and not isinstance(line, bool) else None,
                    'severity': text('severity').lower()[:20]})
    return out


def folders(conf):
    """The report folders the scan left at the top of its tree, oldest first: [{path, name, at}] (at: its name's moment in his zone, else its
    mtime); links never followed."""
    tree = os.path.expanduser(str(conf['tree']))
    out = []
    for p in glob.glob(os.path.join(tree, str(conf['folders']))):
        if os.path.islink(p) or not os.path.isdir(p):
            continue
        m = FOLDER_TIME.search(os.path.basename(p))
        try:
            at = datetime.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S').replace(tzinfo=datetime.timezone.utc).astimezone(_zone(conf)) if m else None   # ITS NAME'S MOMENT IS UTC (the folder of 2026-10-27 23:46 New York is named 20261028-034601), said in his zone
        except ValueError:
            at = None
        if at is None:
            at = datetime.datetime.fromtimestamp(os.path.getmtime(p), _zone(conf))
        out.append({'path': p, 'name': os.path.basename(p), 'at': at})
    return sorted(out, key=lambda f: f['at'])


def read_folder(f, conf):
    """One folder's results: (findings list, '') or (None, why it does not read)."""
    path = os.path.join(f['path'], str(conf['results']))
    if os.path.islink(path) or not os.path.isfile(path):
        return None, 'no results file'
    try:
        return findings_of(path), ''
    except (OSError, ValueError) as e:
        return None, f'its results file does not read whole ({type(e).__name__})'


def alive(words):
    """The pid of a process whose command line holds these words ('' when none): a look by pgrep, never a start."""
    try:
        got = subprocess.run(['pgrep', '-f', words], capture_output=True, text=True, timeout=10)
        pids = [p for p in str(got.stdout or '').split() if p.isdigit()]
        return pids[0] if pids else ''
    except Exception:   # noqa: BLE001
        return ''


def _counts(found):
    by = {s: sum(1 for f in found if f['severity'] == s) for s in SEVERITIES}
    said = ', '.join(f'{n} {s}' for s, n in by.items() if n)
    return f'{len(found)} finding(s)' + (f': {said}' if said else '')


# ---- THE LOOK ----
def look(now=None, conf=None, process=None):
    """ONE LOOK, read only: OFF -> 'off' (never red, says so; what a scan left as words); ON -> red when the newest whole scan holds findings
    (ITEMS_STEP), red when no clean scan of today (OFF_STEP), else green. A scan running now is words after the red. Never starts a scan.
    -> {'state', 'summary', 'switch', 'open', 'scan', 'scan_said', 'last', 'items', 'step', 'tree', 'rule'}"""
    conf = conf_of(conf)
    on = switched_on(conf)
    every = folders(conf)
    whole = None   # the newest folder whose results read whole: its findings stay open until a newer whole scan
    for f in reversed(every):
        found, _why = read_folder(f, conf)
        if found is not None:
            whole = {**f, 'found': found}
            break
    stamp = lambda f: f['at'].strftime('%b %d %H:%M')
    if whole:
        last = f"the last whole scan {stamp(whole)} ({whole['name']}): {_counts(whole['found'])}"
    elif every:
        last = 'no whole scan here: no report folder holds a results file that reads whole'
    else:
        last = f"no scan results here (no {conf['folders']} folder in {conf['tree']})"
    items = [{'id': f['id'], 'title': f['title'], 'severity': f['severity'], 'file': f['file'], 'line': f['line']} for f in (whole or {}).get('found', [])]
    out = {'switch': on, 'open': len(items), 'scan': '', 'scan_said': '', 'last': last, 'items': items, 'step': '', 'tree': conf['tree'], 'rule': RULE}
    running = (process or alive)(SCAN_PROCESS)
    out.update(scan='running' if running else '', scan_said='the scan runs now' if running else '')
    words = ('on' if on else 'off') + (' · the scan runs now' if running else '') + f' · {last}'
    if out['open']:   # THE ONE RULE (the owner 2026-10-27): "security issue list = 1+ then red"
        return {**out, 'state': 'red', 'step': ITEMS_STEP, 'summary': f"{out['open']} issue(s) open · {words} · {HAND}{ITEMS_STEP}"}
    return {**out, 'state': 'green', 'summary': f"0 issues open · {words}"}   # "security scan on = green / security scan off = green / security issue list = 0 then green"


def start(conf=None, now=None, popen=None):
    """THE TOGGLE TURNED ON RUNS THE SCAN ONCE, NOW (the original's row 16: "On runs it once, now"): the scan's own command, its request on stdin,
    in its tree, a process of its own, its words in this office's scratch log; never a second one while one runs. -> what happened, in words"""
    import subprocess
    conf = conf_of(conf)
    if alive(SCAN_PROCESS):
        return 'the scan already runs'
    if not conf.get('command') or not conf.get('request'):
        return 'no scan command in this office settings (security.command, security.request)'
    folder = os.path.expanduser(f'~/scratch/reports/{frame.NAME}/security')
    os.makedirs(folder, exist_ok=True)
    log = os.path.join(folder, f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    with open(log, 'w', encoding='utf-8') as out, open(log + '.request', 'w', encoding='utf-8') as req:
        req.write(conf['request'])
    with open(log, 'a', encoding='utf-8') as out, open(log + '.request', encoding='utf-8') as req:
        (popen or subprocess.Popen)([os.path.expanduser(x) for x in conf['command']], cwd=os.path.expanduser(conf['tree']), stdin=req, stdout=out,
                                    stderr=subprocess.STDOUT, start_new_session=True)
    return f'the scan started (its words in {log})'


# ---- THE PANEL ----
DOES = 'The security scan, on his switch only, and its open issues, in one block'   # its one short sentence, as the original's row 16 says its own


def panel_html(result, toggle='', now=None, light=True):
    """THE SECURITY PANEL, drawn as the original Scrum Master's row 16 SECURITY (scrum.html; the owner 2026-10-27: "does this look like the original
    to you with the red background and frost identity logo"): its block wears FROST's place (data-place="frost", so technology.css paints the whole
    of it FROST's red and names FROST Identity's logo, .fm-mark), the alternate block's ground as row 16's; its light in the left cell (the frame's
    one public light, so that cell is id="security-title"); in the right cell the logo at the top, centred, its group tag top right, its title, its
    when, its one sentence, its runner line and the switch's form, the original's order; under it the day said as the original says it and the
    look's words in its report cell, plain as the original's (a tick on green, the red cross on red with the issues and his one step). The light
    is the issue list's alone (look). toggle: the page's own switch markup (its form, drawn by the page: the frame holds no route). now: the day
    said (a check hands its own). Everything escaped. -> Markup"""
    from markupsafe import Markup, escape
    r = result or {}
    state = str(r.get('state') or '')
    light = '' if not light else frame.LIGHT_SVG.format(   # NO LIGHT ON THE PUBLIC FACE (the owner 2026-10-28: "in the red security box there is a green light in the corner that should not be there for the pf public agent")
                                   word=escape(state or 'not seen yet'), state=escape(state or 'none'),
                                   dot={'green': '<circle class="hdr-status--success" cx="12" cy="12" r="4.5" stroke="none"/>',
                                        'red': '<circle class="hdr-status--error" cx="12" cy="12" r="4.5" stroke="none"/>'}.get(state, ''))
    red = state == 'red'
    day = (now or datetime.datetime.now(_zone(conf_of()))).strftime('%a %b %-d').upper() + ' (TODAY)'   # the original's day line: THU OCT 22 (TODAY)
    mark = ('<svg class="hdr-icon" viewBox="0 0 24 24" data-failed="yes"><rect class="hdr-status--error" x="11" y="5" width="2" height="14" transform="rotate(45 12 12)"/>'
            '<rect class="hdr-status--error" x="11" y="5" width="2" height="14" transform="rotate(-45 12 12)"/></svg>') if red else '<span class="larry-up">✓</span>' if state else ''
    n = int(r.get('open') or 0)
    words = (f'<div class="annotation scaf-mono" id="security-items">{n} issue{"" if n == 1 else "s"} open'
             f' · {escape("on" if r.get("switch") else "off")}' + (f' · {escape(str(r.get("scan_said")))}' if r.get('scan_said') else '')
             + f' · {escape(str(r.get("last") or ""))}</div>'
             + ''.join(f'<div class="annotation scaf-mono" data-security-item="{escape(i["id"])}">- {escape(i["severity"].upper())} · {escape(i["title"])}'
                       + (f' · {escape(i["file"])}' + (f':{int(i["line"])}' if i.get('line') is not None else '') if i.get('file') else '') + '</div>'
                       for i in (r.get('items') or [])[:50])
             + (f'<div class="annotation scaf-mono" id="security-step">{escape(HAND + str(r["step"]))}</div>' if red and r.get('step') else ''))
    head = ('<div class="fm-mark fm-mark--small" role="img" aria-label="FROST Identity">FROST Identity</div>'
            '<div class="title" id="security-name">SECURITY</div>'   # no LIVE tag inside the red box (the owner 2026-10-28: "i asked so many fucking time delte the LIVE in the red box"): LIVE stands above it, outside
            '<div class="annotation size--xs">frame.frame_security</div>' + str(toggle or ''))   # no When line, no sentence (the owner 2026-10-28: "remove When: on every change / The security scan, on his switch only, and its open issues, in one block")
    return Markup(f'<div class="replica-security" id="replica-security" aria-label="SECURITY" data-state="{escape(state or "none")}">'
                  '<div class="scaf-wrap"><table class="scaf-table" id="security-monitor">'
                  '<tbody class="scrum-step-block scaf-block-alt" data-row-name="SECURITY" data-place="frost">'
                  f'<tr class="scaf-row-name scaf-row-alt"><td id="security-title">{light}</td><td>{head}</td></tr>'
                  f'<tr class="scrum-day-head scaf-row-alt" data-day="this"><td></td><td class="caption">{escape(day)}</td></tr>'
                  f'<tr class="{"scaf-row-warned " if red else ""}scaf-row-alt" data-step="security" data-light="{escape(state or "grey")}"><td></td>'
                  f'<td data-done="{"no" if red else "yes"}">{mark}{words}</td></tr>'
                  + yesterday_rows(now) +
                  '</tbody></table></div></div>')


def yesterday_rows(now=None, conf=None):
    """YESTERDAY UNDER TODAY, as the original's row 16 (the owner 2026-10-28: "missing the yesterday under it"): the day said, then each scan that
    began that day, from its own report folder: its time and what it left (its findings counted, or why its results do not read); none began: said so.
    -> markup"""
    from markupsafe import escape
    conf = conf_of(conf)
    day = (now or datetime.datetime.now(_zone(conf))).astimezone(_zone(conf)).date() - datetime.timedelta(days=1)
    lines = []
    for f in folders(conf):
        if f['at'].date() != day:
            continue
        found, why = read_folder(f, conf)
        said = (f"{len(found)} issue{'' if len(found) == 1 else 's'} found" if found is not None else why)
        lines.append(f'<div class="annotation scaf-mono" data-security-yesterday="{escape(f["name"])}">{escape(f["at"].strftime("%H:%M"))} · scan began · {escape(said)}</div>')
    if not lines:
        lines.append('<div class="annotation scaf-mono" data-security-yesterday="">no scan began that day</div>')
    head = day.strftime('%a %b %-d').upper() + ' (YESTERDAY)'
    return (f'<tr class="scrum-day-head scaf-row-alt" data-day="yesterday"><td></td><td class="caption">{escape(head)}</td></tr>'
            f'<tr class="scaf-row-alt" data-step="security-yesterday"><td></td><td>{"".join(lines)}</td></tr>')
