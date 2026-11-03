"""FRAME · X BOARD (the owner 2026-10-27: "_ xboard"; 2026-10-26: "X BOARD ... its global and an agent only in replica so it automatically in
every one using the frame"; "just show the current day ... only live data with no snapshot"; "the idea is the frame is not an agent / it holds agents / it does nothing on its own without an agent attached"): the lines, the counts, what
makes the X, every light read from frame_replica (the one source the board and every canvas read); one line per group of the shape (an office's own
groups, or its slots), its rows the shells in it, a row did its job when its job ran today and ended DONE, the slot's X when every row did.
Live, today only, nothing kept: it draws what the agents' jobs say and runs nothing of its own."""
import datetime
import zoneinfo

from frame import frame_replica as frame


def x_groups(agent, slots):
    """THE X BOARD'S LINES, each replica's own groups, one plain list for every replica (its agent's x_groups: group, its
    measure of success in bold, its rows) (the owner 2026-10-26: "make sure generic for all"; "simple easy"); an office with
    none: one line per slot, each slot's own measure (settings root_shape x_board says)."""
    given = (agent or {}).get('x_groups')
    if given:
        return [{'group': x['group'], 'says': x.get('says', ''), 'rows': list(x.get('rows') or [])} for x in given]
    says = frame.SETTINGS['root_shape']['x_board'].get('says') or {}
    return [{'group': slot, 'says': says.get(slot, ''), 'rows': []} for slot in slots]


def x_board(shells, slots, rule, now=None, groups=None, parts=None):
    """THE X BOARD, the MARK IV agent's own summary, generic for every replica (the owner 2026-10-26: "X BOARD ... its global and
    an agent only in replica so it automatically in every one using the frame"; "just show the current day ... only live data with
    no snapshot"): one line per slot of the shape, in its order; its rows are the shells in it; a row did its job when its job ran
    today and ended DONE (rule: its zone and its done word); the slot's X when every row did; its reds counted too (a row whose job
    ran today and ended in a red word, rule red). THE SHAPE'S ITEMS COUNT WITH THE SHELLS (the owner 2026-10-27: "reclassify the shape
    items to fit into the buckets and then include them in the xboard / like skills and rules are TOP for example"; parts: page.x_parts,
    each {'name', 'slot', 'green', 'red'}): in its slot's line an item is one more row, green or red as its state says, its name in WHAT
    MAKES THE X before the agents' (TOP 3/3 · skills, rules, standup); the slot's X when every shell and every item is green. Live, today
    only, nothing kept. -> {'day': 'MON OCT 26 (TODAY)', 'lines': [...]}"""
    zone = zoneinfo.ZoneInfo(rule['zone'])
    now = now or datetime.datetime.now(zone)

    def did(sh):
        return frame.light_of(sh['job'], rule, now) == 'green'

    def fell(sh):
        return frame.light_of(sh['job'], rule, now) == 'red'
    lines = []
    for g in groups or [{'group': slot, 'says': '', 'rows': []} for slot in slots]:
        items = [p for p in (parts or ()) if p.get('slot') == g['group']]   # the shape's items bucketed in this slot, counted with its rows
        if g['rows']:   # a group of named rows: each row's shell is the one whose job carries its name (none built yet: not done)
            named = {((sh['job'] or {}).get('data_full_name') or '').lower(): sh for sh in shells}
            done = [p for p in items if p.get('green')] + [r for r in g['rows'] if r in named and did(named[r])]
            red = [p for p in items if p.get('red')] + [r for r in g['rows'] if r in named and fell(named[r])]
            total, names = len(items) + len(g['rows']), [str(p['name']).lower() for p in items] + list(g['rows'])
            still = [str(p['name']).lower() for p in items if not p.get('green')] + [r for r in g['rows'] if not (r in named and did(named[r]))]
        else:   # a slot of the shape: its shells
            rows = [sh for sh in shells if sh['slot'] == g['group'] and sh.get('job')]   # the shells holding a job: an empty shell has nothing to do (the stream's rows the same, frame_live.marks); the LIVE slot's is empty now, the frame's own look its row (the owner 2026-10-27: "live should be in replica not in the agent")
            done = [p for p in items if p.get('green')] + [sh for sh in rows if did(sh)]
            red = [p for p in items if p.get('red')] + [sh for sh in rows if fell(sh)]
            total = len(items) + len(rows)
            names = [str(p['name']).lower() for p in items] + [n.lower() for n in (((sh['job'] or {}).get('data_full_name') or sh.get('agent') or '') for sh in rows) if n]
            still = [str(p['name']).lower() for p in items if not p.get('green')] + [n.lower() for n in (((sh['job'] or {}).get('data_full_name') or sh.get('agent') or '') for sh in rows if not did(sh)) if n]   # only what is real: a shell's own name; an empty shell says nothing (the owner 2026-10-26: "no fucking placeholder everythign is real")
        lines.append({'slot': g['group'], 'says': g['says'], 'green': len(done), 'red': len(red), 'total': total, 'crossed': bool(total) and len(done) == total, 'x': ', '.join(names), 'names': names, 'open': still})   # OPEN: what is not done yet, underlined on the line (the owner 2026-10-27: "can you underline the ones not done")
    return {'day': now.strftime('%a %b %d').upper() + ' (TODAY)', 'lines': lines}
