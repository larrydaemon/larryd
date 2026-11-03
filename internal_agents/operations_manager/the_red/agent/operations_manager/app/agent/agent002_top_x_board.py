"""AGENT 003 · THE X BOARD, TOP (the owner 2026-11-01: "move the agents manually floating in the frame and register them as real agents
... put the x board on the scrum master then wire it up first"): A SUB AGENT of the MARK IV agent (agent001), the second item of TOP,
its card LARRYD's under SYSTEM in the species' own class (MARK I AGENT (NORMAL)), its job in TOP's second shell, its logs its runs.
Every group on one board: what makes its X, how many are done, and its words. It was the frame's own block, floating under the agent;
now it is a registered agent in its own shell like every other, and the frame holds nothing of its own. The board itself is the
frame's one reader (frame/frame_xboard.x_board, the page's x_now): this agent draws it on its canvas and its run counts it."""
import datetime
import json

KEY = 'x_board'
SLOT = 'TOP'   # where it lives: TOP, after the standup
NAME = 'X Board'
CARD_NAME = 'Scrum Master X Board'   # ITS CARD IN LARRYD, as it was registered while it lived in Scrum Master 2 (REPLICA SCRUM MASTER X BOARD AGENT): a card's identity is minted once and never renamed; moved to Operations Manager 2026-11-02
PITCH = 'Every group on one board: what makes its X, how many are done, and its words'   # its card's pitch in LARRYD
WHAT = 'Every group on one board: what makes its X, how many are done, and its words.'   # what it does, its one line
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: it draws live on every look, its run counts
X_BOARD = True   # ITS CANVAS IS THE X BOARD: the page draws the board it reads now (web/app.py x_now) into this agent's own canvas
ROW_FILE = 'agent003_top_x_board.py'   # its program's file: its skills index is filed under it


def counted(shells, slots, rule, agent=None, chain=(), parts_conf=None, store=None):
    """THE BOARD'S COUNT NOW, the page's own reading (web/app.py x_now): the frame's one reader, its shells and the shape's items still in the
    frame counted in their buckets (web/page.x_parts), so the run says what the board shows: each group's done of its total, and its X. -> (lines, said)"""
    from frame import frame_live, frame_xboard as xboard
    from web import page as parts
    x = xboard.x_board(shells, slots, rule, groups=xboard.x_groups(agent, slots), parts=parts.x_parts(chain, parts_conf or {}, live=frame_live.live_word()))
    if store is not None:   # THE RED, as the page counts it (web/page.with_reds, the page's own function)
        from frame import frame_red as red
        x = parts.with_reds(x, shells, list(red.why_rows(store)), red.GROUP)
    said = ', '.join(f"{line['slot']} {line['green']}/{line['total']}{' X' if line['crossed'] else ''}" for line in x['lines'])
    return x['lines'], said


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (RUN AGENT): the board counted from every agent's job as it stands, kept with the run; DONE, exit 0. A board it cannot
    read (the shape's settings, a shell it cannot count): FAILED, exit 1, the fault's one line, so its shell is red and names it."""
    from frame import frame_replica as frame
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        handed = (getattr(store, 'handed', None) or {}).get('xboard')
        if handed is not None:   # THE BOARD IT SITS ON (the owner 2026-11-02): wid counted the board its block stands on (larryd_runtime.xboard_where), as the canvas does
            said = ', '.join(f"{x['group']} {x['green']}/{x['total']}{' X' if x['crossed'] else ''}" for x in handed)
        else:   # run on this office's own page: this office's board
            shape = frame.SETTINGS['root_shape']
            lines, said = counted(shells, shape['slots'], shape['x_board'], agent, chain, shape.get('parts') or {}, store)
        out = {'summary': f'DONE · every group counted: {said}', 'ok': True, 'lines': [said]}
    except (KeyError, ValueError, TypeError, OSError) as fault:
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
    """ITS OWN CONTENT: none of its own words; the page puts the board it reads now on this canvas (X_BOARD)."""
    return []
