"""DAY, Scrum Master 3's DAY switch (the owner 2026-10-28: "1 toggle turns off all the day agents ... it does nothign else"): its state
is one row of the office's database (live_status, its day_key), written only by the owner's press on its CALL; the DAY steps read it
(day.py day_state). A RUN says the state and how many DAY agents read it, and writes nothing."""
import re

import look
import office
from day import F, day_state, path_of


def day_agents(given):
    me = office.me()['key']
    return [j for j in office.workflow(given) if j.get('data_job_agentic') != 'WORKFLOW' and j.get('data_agent_key') != me
            and (j.get('data_job_group') or '').upper() == F('group')]


def scoped_theme():
    """SM2's _scoped_theme: Agency Mgmt's theme sheet on this block alone, each mode's values under the page's own mode, its fonts and
    pictures at the theme's package path; a sheet that does not read: nothing (the page's own look stays)"""
    try:
        with open(F('theme_sheet'), encoding='utf-8') as fh:
            text = re.sub(r'/\*.*?\*/', '', fh.read(), flags=re.S)
    except OSError:
        return ''
    fix = lambda css: css.replace('url("../', f'url("{F("theme_site")}/')  # noqa: E731
    out = []
    for mode in ('dark', 'light'):
        m = re.search(r'\[data-brilliance-hierarchy="[A-F0-9]+"\]\[data-theme="' + mode + r'"\]\s*\{(.*?)\n\}', text, re.S)
        if m:
            out.append(f':host-context([data-theme="{mode}"]) .id-replica-day {{{fix(m.group(1))}}}')
            out.append(f':host-context([data-theme="{mode}"]) .id-replica-day {{ background-image: url("{F("theme_site")}/images/{mode}/background.webp"); '
                       'background-size: cover; background-position: center; }')
    out += [fix(f) for f in re.findall(r'@font-face\s*\{[^}]*\}', text)]
    return '\n'.join(out)


def canvas(given):
    """SM2's DAY panel (page.py day_view): Agency Mgmt's logo and theme, its title, the switch, how many DAY agents are on"""
    on, _row = day_state()
    to = office.asked(given, F('press'))
    if to in ('on', 'off') and (to == 'on') != on:
        office.live_set(F('day_key'), office.me()['name'], F('on') if to == 'on' else F('day_off'), F('said_on') if to == 'on' else F('said_off'), trigger='press')
        on, _row = day_state()
    e, n, group = office.e, len(day_agents(given)), F('group')
    toggle = (f'<form class="ct-form" id="day-switch-form"><input type="hidden" name="{F("press")}" value="{"off" if on else "on"}">'
              f'<span class="body">{e(group.capitalize())} agents</span> <button class="pfb pfb--toggle{" pfb--on" if on else ""}" type="submit" aria-pressed="{"true" if on else "false"}" '
              f'title="{"On" if on else "Off"}"><span class="pfb__knob"></span></button> <span class="annotation">{n if on else 0} of {n} on</span></form>')
    got = look.view(
        f'<div class="replica-group" aria-label="group">{e(group)}</div><div class="replica-normal-block replica-frame-part replica-day-part" aria-label="{e(group)}">'
        f'<div class="replica-day" id="replica-day" data-place="agencymgmt"><div class="replica-day-mark" role="img" aria-label="Agency Mgmt">Agency Mgmt</div>'
        f'<div class="title" id="day-name">{e(F("title"))}</div><div class="annotation">One switch for every {e(group)} agent</div>{toggle}</div></div>', path_of(given))
    return {**got, 'css': scoped_theme() + '\n' + got['css']}


def run(given):
    on, row = day_state()
    n = len(day_agents(given))
    return office.done(f"GREEN · {'DAY is on' if on else 'DAY is off'} · {n} DAY agents read it", 'GREEN',
                       {'on': on, 'since': (row or {}).get('changed_at', ''), 'agents': n})


if __name__ == '__main__':
    office.main(canvas, run)
