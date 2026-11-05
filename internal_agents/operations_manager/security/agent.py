"""SECURITY, the shared block of every MARK IV workflow (owned by Operations Manager): the security look, read only. The switch is data
(agent.json facts "scan": on only when exactly true); the findings are what the scan itself writes: a report folder at the top of the
tree it scanned, its results one JSON object a line. The owner's rule (2026-10-27): scan on = green, scan off = green, 0 issues = green,
1 or more issues = red. A scan running now is words, never the light. It never starts a scan."""
import datetime
import glob
import html
import json
import os
import re
import subprocess
import zoneinfo

import look as lookkit
import office

STAMP = re.compile(r'(\d{8})-(\d{6})$')


def folders():
    zone = zoneinfo.ZoneInfo(office.fact('zone'))
    out = []
    for p in glob.glob(os.path.join(office.fact('tree'), office.fact('folders'))):
        if os.path.islink(p) or not os.path.isdir(p):
            continue
        m = STAMP.search(os.path.basename(p))
        try:
            at = datetime.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S').replace(tzinfo=datetime.timezone.utc).astimezone(zone) if m else None
        except ValueError:
            at = None
        out.append({'path': p, 'name': os.path.basename(p), 'at': at or datetime.datetime.fromtimestamp(os.path.getmtime(p), zone)})
    return sorted(out, key=lambda f: f['at'])


def findings(folder):
    """its results file, every line a JSON object, or None when it does not read whole (half a list is never the list)"""
    path = os.path.join(folder['path'], office.fact('results'))
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    out = []
    try:
        with open(path, encoding='utf-8') as fh:
            for n, raw in enumerate(fh.read().splitlines(), 1):
                if not raw.strip():
                    continue
                rec = json.loads(raw)
                if not isinstance(rec, dict):
                    return None
                text = lambda *keys: next((str(rec[k]).strip() for k in keys if isinstance(rec.get(k), (str, int)) and str(rec[k]).strip()), '')  # noqa: E731
                out.append({'id': text('claudeSecurityPluginFindingId', 'id')[:80] or f'line-{n}', 'title': text('title', 'category', 'summary')[:160],
                            'file': text('file')[:300], 'line': rec.get('line') if isinstance(rec.get('line'), int) else None, 'severity': text('severity').lower()[:20]})
    except (OSError, ValueError):
        return None
    return out


def running():
    try:
        got = subprocess.run(['pgrep', '-f', office.fact('process')], capture_output=True, text=True, timeout=10)
        return any(p.isdigit() for p in got.stdout.split())
    except (OSError, subprocess.SubprocessError):
        return False


def look():
    on = office.fact('scan') is True
    every = folders()
    whole = next(({**f, 'found': got} for f in reversed(every) if (got := findings(f)) is not None), None)
    if whole:
        by = ', '.join(f'{n} {s}' for s in office.fact('severities') if (n := sum(1 for x in whole['found'] if x['severity'] == s)))
        last = f"the last whole scan {whole['at'].strftime('%b %d %H:%M')} ({whole['name']}): {len(whole['found'])} finding(s)" + (f': {by}' if by else '')
    elif every:
        last = 'no whole scan here: no report folder holds a results file that reads whole'
    else:
        last = f"no scan results here (no {office.fact('folders')} folder in {office.fact('tree')})"
    items = (whole or {}).get('found', [])
    scan = running()
    words = ('on' if on else 'off') + (' · the scan runs now' if scan else '') + f' · {last}'
    return {'switch': 'on' if on else 'off', 'open': len(items), 'items': items[:int(office.fact('most'))], 'last': last, 'scan': scan,
            'words': words, 'folders': len(every), 'state': 'RED' if items else 'GREEN'}


def yesterday():
    """MON NOV 2 (YESTERDAY), as SM2 says it: each scan that began that day, its time and what it left; none: said so"""
    day = office.now().date() - datetime.timedelta(days=1)
    lines = []
    for f in folders():
        if f['at'].date() == day:
            got = findings(f)
            said = f"{len(got)} issue{'' if len(got) == 1 else 's'} found" if got is not None else 'its results do not read whole'
            lines.append(f'<div class="annotation scaf-mono">{f["at"].strftime("%H:%M")} · scan began · {html.escape(said)}</div>')
    return day.strftime('%a %b %-d').upper() + ' (YESTERDAY)', ''.join(lines) or '<div class="annotation scaf-mono">no scan began that day</div>'


def canvas(given):
    """SM2's Security panel (frame_security.panel_html): FROST's place (technology.css paints it FROST's red and names FROST Identity's logo),
    the switch drawn (a press only answers: the switch is the owner's), today's look and yesterday's scans"""
    a, e = look(), html.escape
    path = (given.get('page') or {}).get('path') or ''
    mode = office.asked(given, 'mode') if office.asked(given, 'mode') in ('light', 'dark') else 'dark'
    on, red = a['switch'] == 'on', a['state'] == 'RED'
    said = (office.fact('press_said') if office.asked(given, 'security') else 'On: it started when switched on and runs once' if on
            else 'Off: it never starts (it is slow and spends many tokens). On runs it once, now.')
    toggle = (f'<form class="ct-form" id="security-switch-form"><input type="hidden" name="security" value="{"off" if on else "on"}"><span class="body">Security scan</span> '
              f'<button class="pfb pfb--toggle{" pfb--on" if on else ""}" type="submit" title="{"On" if on else "Off"}"><span class="pfb__knob"></span></button> '
              f'<span class="annotation">{e(said)}</span></form>')
    n = a['open']
    words = (f'<div class="annotation scaf-mono" id="security-items">{n} issue{"" if n == 1 else "s"} open · {a["switch"]}'
             + (' · the scan runs now' if a['scan'] else '') + f' · {e(a["last"])}</div>'
             + ''.join(f'<div class="annotation scaf-mono">- {e(i["severity"].upper())} · {e(i["title"])}' + (f' · {e(i["file"])}' + (f':{i["line"]}' if i['line'] is not None else '') if i['file'] else '') + '</div>'
                       for i in a['items'])
             + (f'<div class="annotation scaf-mono" id="security-step">YOUR 3 MIN: {e(office.fact("step"))}</div>' if red else ''))
    mark = '<span class="hdr-status--error">✗</span>' if red else '<span class="larry-up">✓</span>'
    day, lines = yesterday()
    markup = (f'<div class="replica-group" aria-label="group">{e(office.fact("group_said"))}</div><div data-theme="{mode}"><div class="replica-normal-block replica-frame-part replica-security-part" aria-label="SECURITY">'
              f'<div class="replica-security" id="replica-security" aria-label="SECURITY" data-state="{a["state"].lower()}"><div class="scaf-wrap"><table class="scaf-table" id="security-monitor">'
              '<tbody class="scrum-step-block scaf-block-alt" data-row-name="SECURITY" data-place="frost">'
              '<tr class="scaf-row-name scaf-row-alt"><td id="security-title"></td><td><div class="fm-mark fm-mark--small" role="img" aria-label="FROST Identity">FROST Identity</div>'
              f'<div class="title" id="security-name">SECURITY</div><div class="annotation size--xs">{e(office.fact("frame_said"))}</div>{toggle}</td></tr>'
              f'<tr class="scrum-day-head scaf-row-alt" data-day="this"><td></td><td class="caption">{office.now().strftime("%a %b %-d").upper()} (TODAY)</td></tr>'
              f'<tr class="{"scaf-row-warned " if red else ""}scaf-row-alt" data-step="security"><td></td><td>{mark}{words}</td></tr>'
              f'<tr class="scrum-day-head scaf-row-alt" data-day="yesterday"><td></td><td class="caption">{day}</td></tr>'
              f'<tr class="scaf-row-alt" data-step="security-yesterday"><td></td><td>{lines}</td></tr></tbody></table></div></div></div></div>')
    return lookkit.view(markup, path, office.fact('css'))


def run(given):
    a = look()
    data = {k: a[k] for k in ('switch', 'open', 'last', 'scan', 'folders')}
    if a['open']:
        return office.done(f"RED · {a['open']} issue(s) open · {a['words']} · YOUR 3 MIN: {office.fact('step')}", 'RED', data)
    return office.done(f"GREEN · 0 issues open · {a['words']}", 'GREEN', data)


if __name__ == '__main__':
    office.main(canvas, run)
