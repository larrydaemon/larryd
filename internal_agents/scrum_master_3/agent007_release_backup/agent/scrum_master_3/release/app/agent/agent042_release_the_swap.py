"""ROW 042 THE SWAP (E RELEASE, every round): THE SWITCH IS SET UP CORRECTLY OR NOT (the owner 2026-10-23: "this should
never be red unless its not setup correctly.. its setup correct or not"; "its a fucking switch"). A to B on December 13,
by his hand behind the PIN; the row reads and reports, it never swaps. It asks no sync (the syncs are rows 033 and 035's
own) and it never holds. GREEN: every piece the tower's own flip needs is in place (global_config tower.swap: the public
name, its zone and record, the two slots with their addresses, the switch's record pointing at one of them, tower.sprint
naming the same two; the two secrets godaddy and swap_check_member placed: read by name only, never opened). RED: the
first missing piece, said first, his one step last."""

import datetime
import json
import os
import sys

from agent import shared_schedule as schedule   # the sprint clock: the day's count to the release
from agent import shared_store as store         # the one database door: row_main writes this row's run
from agent import shared_where as where         # his places: global_config.json, the swap's log, the workspace
from agent import shared_words as words         # guard() at the door
from agent import shared_chunks as chunks       # THE 3 MINUTE RULE (the owner 2026-10-23): why first, his one step last

ROW = 42
SECRETS = {'godaddy': "GoDaddy's credential for the public name's A record, JSON {\"token\"} or {\"key\", \"secret\"}",
           'swap_check_member': 'the member the flip signs in with on both slots (a member of the public account, one random PIN, the same on A and B, set in FROST), JSON {"username", "pin"}'}   # never a scratch member (the owner 2026-10-23 23:24: "reset the pin to a random one and use for both ... it should be from the same place for the swap"); no member or account named here (test_sync)   # what the tower's flip needs placed (lryllm core_engine/swap.py: placed)


def _read(name):
    with open(where.path(name), encoding='utf-8') as fh:
        return fh.read()


def _short(path):
    return path.replace(os.path.expanduser('~'), '~', 1)


def lane(key='current', gc=None):
    """A LANE AS THE PLATFORM'S FILES SAY IT: the swap's log (swaps.jsonl, the last flip that ended 'committed') names
    the live slot, before any flip global_config tower.swap.start does; current is the other slot of tower.sprint.slots."""
    tower = (gc if gc is not None else json.loads(_read('global_config'))).get('tower') or {}
    slots = (tower.get('sprint') or {}).get('slots') or {}
    try:
        rows = [json.loads(x) for x in _read('swaps').splitlines() if x.strip()]
    except FileNotFoundError:
        rows = []
    moved = [r for r in rows if r.get('result') in ('committed', 'rolled back', 'ROLLBACK FAILED')]
    if moved and moved[-1]['result'] == 'ROLLBACK FAILED':   # the swap's log itself says where the name points is not known
        raise ValueError(f"the last flip (to {moved[-1].get('to')}) failed and its way back failed: where the name points is not known from the record")
    flips = [r for r in rows if r.get('result') == 'committed' and r.get('to') in slots]
    live = flips[-1]['to'] if flips else (tower.get('swap') or {}).get('start')
    others = [s for s in slots if s != live]
    if live not in slots or len(others) != 1:
        raise ValueError(f'the switch points at {live!r}: not one of the two slots {list(slots)} (tower.swap.start, tower.sprint.slots)')
    at = live if key == 'live' else others[0]
    return {'key': key, 'name': slots[at].get('name', at), 'slot': at}


def placed(name, gc):
    """A secret the owner places, read BY NAME ONLY: is its file there (global_config secrets: its office's instance,
    secrets/<name>). -> (there, its path)"""
    decl = (gc.get('secrets') or {}).get(name) or {}
    office = (gc.get('offices') or {}).get(decl.get('office') or '') or {}
    if not office.get('instance'):
        return False, ''
    path = os.path.join(where.path('workspace'), office['instance'], 'secrets', name)
    return os.path.isfile(path), path


def switch_step():
    """HIS ONE STEP when the switch's record cannot be read: the swap's own log, then the tower's own swap by hand. -> words"""
    try:
        log = _short(where.path('swaps'))
    except Exception:   # noqa: BLE001
        log = 'swaps.jsonl (settings reads swaps)'
    return (f"read the last line of the swap's log ({log}) and put the switch back by hand with the tower's own swap "
            "(lryllm core_engine/swap.py, run by the Control Tower); then this row reads the switch again")


def setup(gc=None, placed=placed):
    """THE SWITCH, PIECE BY PIECE, as the tower's own flip needs it (core_engine/swap.py flip: a slot with an address,
    the public name, its zone and record, the GoDaddy key, the scratch member; and the lanes it reads). -> (why, step,
    facts): why '' when every piece is there; else the first missing piece and his step; facts: the lanes and the name."""
    gc = gc if gc is not None else json.loads(_read('global_config'))
    tower = gc.get('tower') or {}
    swap, sprint = tower.get('swap') or {}, tower.get('sprint') or {}
    here = _short(where.path('global_config'))
    fill = 'fill {key} in ' + here + '; then this row reads the switch again'
    slots = swap.get('slots') or {}
    if len(slots) != 2:
        return f'tower.swap.slots names {len(slots)} slot(s), not two', fill.format(key='tower.swap.slots (the two slots, each with its ip)'), {}
    for slot, s in slots.items():
        if not (s or {}).get('ip'):
            return f'{slot} has no address', fill.format(key=f'tower.swap.slots.{slot}.ip'), {}
    if set((sprint.get('slots') or {})) != set(slots):
        return (f"tower.sprint.slots names {sorted(sprint.get('slots') or {})}, tower.swap.slots names {sorted(slots)}: not the same two",
                fill.format(key='tower.sprint.slots (the same two slots, each with its sprint name)'), {})
    for key in ('name', 'zone', 'record'):
        if not swap.get(key):
            return f'tower.swap.{key} is empty', fill.format(key=f'tower.swap.{key}'), {}
    try:
        live, current = lane('live', gc), lane('current', gc)
    except (OSError, ValueError) as e:
        return f"the switch's record: {e}", switch_step(), {}
    for name, what in SECRETS.items():
        there, path = placed(name, gc)
        if not there:
            return (f'the secret {name} is not placed ({what})',
                    f"place the secret {name} at {_short(path) or 'its office instance secrets/' + name} (JSON, chmod 600); this row reads only that it is there", {})
    return '', '', {'live': live, 'current': current, 'name': swap['name'], 'ips': {s: v['ip'] for s, v in slots.items()}}


def check():
    """ROW 042's one look: the switch is set up correctly or not. -> (state, text). Green: every piece there, the lanes,
    the sprint clock and his day said. Red: the first missing piece first, his one step last. Never held, never a sync."""
    why, step, facts = setup()
    s = schedule.sprint()
    day = datetime.date.fromisoformat(s['release']).strftime('%B %-d')
    if why:
        return chunks.chunk(ROW, 'red', f'the swap is not set up: {why}', step=step)
    live, current = facts['live'], facts['current']
    return 'green', (f"the swap is set up: {facts['name']} · {live['slot']} ({live['name']}, {facts['ips'][live['slot']]}) live, "
                     f"{current['slot']} ({current['name']}, {facts['ips'][current['slot']]}) the sprint being built · "
                     f"day {s['day']} of {s['of']}, {s['left']} days to Version {s['version']} on {s['release']} · "
                     f"the switch is yours on {day}, behind the PIN")


if __name__ == '__main__':
    words.guard()
    sys.exit(store.row_main(ROW, check, sys.argv[1:]))
