"""AGENT 039 · SKILLS, TOP (the owner 2026-11-01: "move the agents manually floating in the frame and register them as real agents"):
A SUB AGENT of the MARK IV agent (agent001), its card LARRYD's under SYSTEM in the species' own class (MARK I AGENT (NORMAL)), its job in its
own shell in TOP, its logs its runs. It was the frame's own block, floating; now it is a registered agent in its own shell like every
other, and the frame holds nothing of its own. Its canvas is the panel the frame drew (PART, drawn by web/app.py from the page's own
reading); its run reads the same thing and keeps what it read."""
import datetime
import json

KEY = 'skills'
SLOT = 'TOP'
NAME = 'Skills'
CARD_NAME = 'Scrum Master Skills'   # ITS CARD IN LARRYD, as Scrum Master 2 registered it (moved here 2026-11-02 by the owner's rule: global and shared to Operations Manager, development to Scrum Master 3)
PITCH = "Every agent's skills, read today by the Scrum Master."   # its card's pitch in LARRYD
WHAT = "Every agent's skills, read today by the Scrum Master."   # what it does, its one line
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: it draws live on every look, its run reads
PART = 'skills'   # ITS CANVAS IS THE FRAME'S OLD PANEL: the page draws it into this agent's own canvas (web/app.py, PART)
ROW_FILE = 'agent039_top_skills.py'   # its program's file: its skills index is filed under it


def read(store, shells, chain):
    """WHAT IT READS NOW, one line, from the same records its panel draws. -> str"""
    g = r = 0
    for _m, sh in chain:
        job = sh.get('job') or {}
        for i in range(1, 11):
            st = str(job.get(f'data_job_skill_{i}_status') or '').upper()
            g += st.startswith('GREEN')
            r += st.startswith('RED')
    return f"{len(chain)} agents · {g} skills green · {r} red"


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT): what its panel shows, read now and kept with the run; DONE, exit 0. A record it cannot read: FAILED, exit 1,
    the fault's one line, so its shell is red and names it."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        said = read(store, shells, chain)
        out = {'summary': f'DONE · {said}', 'ok': True, 'lines': [said]}
    except Exception as fault:   # A RECORD IT CANNOT READ IS RED: never no record and no light
        line = (f'{type(fault).__name__}: {fault}'.splitlines() or [type(fault).__name__])[0][:200]
        out = {'summary': f'FAILED · {line}'}
        store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, json.dumps(out), 'FAILED')
        return out
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0, json.dumps(out), 'DONE')
    return out


def until_next(now=None, schedule=None):
    """ON RUN AGENT ONLY: never due by itself (a year, so the page's timer never fires)"""
    return 365 * 86400


def clock(schedule=None):
    """Its clock in its shell: ON RUN AGENT."""
    schedule = schedule or SCHEDULE
    return {'zone': schedule['location'], 'at': '', 'said': 'ON RUN AGENT', 'when': 'ON RUN AGENT', 'repeat': 'MANUAL', 'hour_deg': 0, 'minute_deg': 0}


def content(store, job_key, block=None):
    """ITS OWN CONTENT: none of its own words; the page puts its panel on this canvas (PART)."""
    return []
