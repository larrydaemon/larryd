"""AGENT 002 · VOICE, TOP (the owner 2026-11-02: "give it the audio for the voice to read the standups because audio is in pace shift"):
a SUB AGENT of the Creative Director's MARK IV agent (agent001). The voice every internal manager's standup is read in is the
Creative Director's: its office's agent.json names the voice (the script lab's voice service and the voice, christensen), its page's
voice door (/voice/<door>) serves it, and the other offices ask that door. Its run only reads: the voice service's own state."""
import datetime
import json
import os
import urllib.error
import urllib.request

KEY = 'voice'
SLOT = 'TOP'
NAME = 'Voice'
PITCH = 'The voice that reads every standup: loaded, and how many lines are made.'   # its card's pitch in LARRYD
WHAT = 'The voice that reads every standup: loaded, and how many lines are made.'    # what it does, its one line
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY
ROW_FILE = 'agent002_top_voice.py'   # its program's file: its skills index is filed under it


def _conf():
    """THE VOICE THIS OFFICE HOLDS: its agent.json voice {service, voice}."""
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'schemas', 'agent.json'), encoding='utf-8') as fh:
        conf = json.load(fh).get('voice') or {}
    if not (conf.get('service') and conf.get('voice')):
        raise ValueError('the office names no voice (agent.json voice)')
    return conf


def read(store=None, shells=None, chain=()):
    """WHAT IT READS NOW, one line: the voice service's state (loaded, lines waiting, lines kept). -> str"""
    conf = _conf()
    try:
        with urllib.request.urlopen(conf['service'] + '/state', timeout=10) as got:
            state = json.loads(got.read().decode('utf-8') or '{}')
    except (urllib.error.URLError, OSError) as e:
        raise ValueError(f"the voice {conf['voice']} at {conf['service']} is not running ({e})") from e
    if not state.get('loaded'):
        raise ValueError(f"the voice {conf['voice']} is still loading: {state.get('why') or 'not loaded'}")
    return f"the voice {conf['voice']}: loaded · {state.get('kept', 0)} lines made · {state.get('waiting', 0)} waiting"


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT): the voice's state, read now and kept with the run; DONE, exit 0. A voice not answering or not loaded:
    FAILED, exit 1, its one line, so its shell is red and names it."""
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        said = read(store, shells, chain)
        out = {'summary': f'DONE · {said}', 'ok': True, 'lines': [said]}
    except Exception as fault:   # A VOICE IT CANNOT READ IS RED: never no record and no light
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
    """ITS OWN CONTENT: none of its own words."""
    return []
