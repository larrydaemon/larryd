"""THE 3 MINUTE RULE (the owner 2026-10-23 17:55: "legit mean honest and within 3 min" · "that is the rule"; 18:00: "fix each
so they are in chunks and fixable in 3 min or less"): a row's red is ONE CHUNK his hand clears in 3 minutes or less, said
first as YOUR 3 MIN: <his one step>: the red row fix loop's own word when its fixer found the step is his (shared_red_rows,
state owner), else the row's own line (a rerun, a press, a command). HELD IS NOT AN ANSWER (the owner 2026-10-23 20:40;
2026-10-25: "does it work or not?"): a red that a run, a night or another machine works on STAYS RED, what works on it
said as words before his step. The row still measures the real condition and says it whole (never a fake green): a red
that comes back after the step is the next chunk, with its own step."""
import re
import subprocess

HAND = 'YOUR 3 MIN: '
HELD = 'held: '
BROKEN = 'BROKEN: '   # THE BROKEN FILE(S) UNDER THE ROW (the owner 2026-10-24 08:46: "it should just show the name of the file that is broken and a copy link ... identifies the broken scripts that need to be edited with a copy button"; a rerun command "makes it look like it will fix the item ... and that is not true"): paths only, ' · ' between them, last in the text; the page draws each on its own line with COPY; a row that names them shows no command
MOST = 500   # a run's text is cut to this (shared_store.run_check): the why is cut before his step ever is
WHY_MIN = 200   # THE WHY KEEPS AT LEAST THIS MUCH (the owner 2026-10-23 18:09: clear why it is red): a fixer's step that leaves less falls back to the row's own line (2026-10-24 07:07: four fixers' steps of 300 to 400 chars left rows 033, 034 and 038 with a why of "(…"); the fixer's words stay whole in the row's box (page.fixer_of)
PY = '~/virtual_workspace/.venv/bin/python'
RERUN = 'cd ~/virtual_workspace/lryllm/lryllm/app && PYTHONPATH=. ' + PY + ' ~/virtual_sanity/scrum_master_3/release/app/agent/rerun_step.py {what}'
TOWER = 'cd ~/virtual_workspace/lryllm/lryllm/app && PYTHONPATH=. ' + PY   # LARRY LLM's app, its own python: where the night's native steps run
HOT_FIX_TREE = '/Users/frost/spine_worktrees/hotfix'   # the hot fix tree the apps are built from (utilities/build/walk/hotfix.py WORKTREE)


def native_test(target, what):
    """ONE APP'S WALK, the tower's native test for it on the hot fix tree: what = again (the rows still red walked, no build:
    minutes), test (the whole walk of the kept build, no build), finish (the hot fix tree's commit built, kept and walked)."""
    return f'{TOWER} -m core_engine.native_test {target} {what} --tree={HOT_FIX_TREE}'


def native_piece(target, piece):
    """ONE APP'S OWN PIECE through the rerun harness (rerun_step.py, the owner 2026-10-23 20:50: the build apart from its walk,
    never every app): piece = build (native_<target>: compiled, signed and kept from the commit localhost pf runs, as the chain
    builds it, no walk) or walk (native_test_<target>: the kept build opened and walked whole, as the chain tests it, no build)."""
    return rerun(None, f'native_{target}' if piece == 'build' else f'native_test_{target}')


SMOKE = 'cd ~/virtual_sanity/smoke && lock smoke && python3 smoke.py'   # the smoke test by hand, as his page says it
CEBF = '~/virtual_sanity/scrum_master_3/release/app/agent/run cebf'                 # the lie detector run again, now


def rerun(chain=None, *steps):
    """The one line that runs a chain of the night again ('native', 'local', 'rnd') or named steps of it (agent/rerun_step.py)."""
    return RERUN.format(what=f'--chain {chain}' if chain else ' '.join(steps))


def his_step(row, default='', day=None, read=None, text=''):
    """HIS ONE STEP for this red row: the fix loop's word when its fixer found the cause is his hands alone (its record
    today, state owner: his exact steps) for THIS red (its words then are the row's words now: a word said for an earlier
    red is stale, shared_red_rows._same_red), else the row's own default line."""
    try:
        from agent import shared_red_rows as loop
        rec = (read or loop.read)(int(row), day) or {}
        if rec.get('state') == 'owner' and str(rec.get('said') or '').strip() and (not text or loop._same_red(rec.get('words'), text)) and not loop.spent(int(row), rec, day):   # spent: the row went green after it (its red is over; this is a new one)
            return str(rec['said']).replace('`', '').strip()   # a fixer's backticks are its markdown, never a step's words (the owner's table 2026-10-24 07:40: lines copied with a trailing backtick)
    except Exception:   # noqa: BLE001  (the loop's record is a help; the row's own line stands)
        pass
    return default


def brief(held):
    """The chain's lock words, short for a row's text: an ISO stamp in them becomes his local HH:MM ("pid 31155 since
    2026-10-24T02:06:04+00:00" -> "pid 31155 since 22:06"); nothing else changes."""
    import datetime
    from agent import shared_schedule as schedule

    def local(m):
        try:
            return datetime.datetime.fromisoformat(m.group(0)).astimezone(schedule.ZONE).strftime('%H:%M')
        except ValueError:
            return m.group(0)
    return re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?', local, str(held or ''))


def broken(files):
    """the tail that names the broken files: paths only (a word that is no path stays in the why), each once, in order, '' when none"""
    seen = []
    for f in files or ():
        f = str(f or '').strip()
        if f and (f.startswith('/') or f.startswith('~/')) and f not in seen:
            seen.append(f)
    return f" · {BROKEN}" + ' · '.join(seen) if seen else ''


def _fit(head, tail):
    """the why, then the step, within a run's text: the why is cut (…) before the step ever is"""
    if len(head) + len(tail) <= MOST:
        return head + tail
    return head[:max(0, MOST - len(tail) - 1)].rstrip() + '…' + tail


def chunk(row, state, text, waiting='', step='', day=None, read=None, tail='', files=None):
    """A ROW'S RESULT UNDER THE 3 MINUTE RULE. -> (state, text): green or running as they are; a red STAYS RED while
    something works on it (waiting: what runs now, said as words before his step, never the light); a red says WHY FIRST
    (the owner 2026-10-23 18:09: "we need to be clear what is is saying why its red"), then his step last (YOUR 3 MIN: ...),
    the step never cut; tail: words kept whole between the why and the step (the chain at work on it: the owner
    2026-10-23, HELD is not an answer; the why is cut before them). The why keeps WHY_MIN at least: a fixer's step
    (his_step) that would leave less gives way to the row's own step; the row's own step is never cut. files: THE BROKEN
    FILES (the owner 2026-10-24 08:46): their paths last (BROKEN: a · b), drawn under the row with COPY; a row that names
    them shows no command line, since a command that runs the check again fixes nothing."""
    if state != 'red' or HAND in text or BROKEN in text or text.startswith(HELD):   # not red, or the row said its chunk itself: as it is
        return state, text
    if waiting:   # HELD IS NOT AN ANSWER (the owner 2026-10-23 20:40; 2026-10-25: "does it work or not?"): the red stays red, what works on it now is words before his step
        tail = f" · at work on it now: {waiting}" + tail
    named = broken(files)
    if named:   # THE BROKEN FILE IS HIS LINE: no command under the row
        return 'red', _fit(text, f"{tail}{named}")
    s = his_step(row, step, day, read, text)
    if s and step and s != step and min(len(text), WHY_MIN) + len(f"{tail} · {HAND}{s}") > MOST:   # the fixer's word would eat the why: the row's own line stands (the box shows the fixer's steps whole)
        s = step
    return 'red', _fit(text, f"{tail} · {HAND}{s}") if s else (_fit(text, tail) if tail else text)


def chain_rows():
    """THE NIGHT'S ROWS (schemas/rows.json: the nightly container, unless a row says chain false): a chain holding the tower's
    lock is what clears their red by itself. Read from his plan at every call, never a range here (the owner 2026-10-24)."""
    from agent import shared_red_rows as loop
    return loop.chain_rows()


def default_step(row):
    """A ROW'S OWN 3 MINUTE STEP when the fix loop has no word for its red: its plan keys (rows.json) rerun, a chain or steps
    of the night run again (note: words before the line, never after it: a note after it is copied as part of the line,
    the owner's table 2026-10-24), or step, a line of his own; '' when none (the red stands as it is, never a made-up step)."""
    from agent import shared_red_rows as loop
    r = loop.plan().get(int(row)) or {}
    again = r.get('rerun') or {}
    if isinstance(again, dict) and (again.get('chain') or again.get('steps')):
        return str(again.get('note') or '') + (rerun(str(again['chain'])) if again.get('chain') else rerun(None, *[str(x) for x in again['steps']]))
    return str(r.get('step') or '')


UNREAD = ('not measured', 'cannot be read', 'could not read', 'he could not read it', 'unreadable')   # a red for a fact the row could not get
KICK = 'launchctl kickstart -k gui/$(id -u)/ai.positivefeedback.spine.scrum'   # the Scrum Master's own round, started again (its plist in ~/Library/LaunchAgents)


def check_line(row):
    """THE ROW BY HAND, one line (its module from schemas/rows.json): the fault is seen whole in the terminal."""
    try:
        import json
        from agent import shared_where as where
        with open(where.ROWS_FILE, encoding='utf-8') as fh:
            module = next(r['module'] for r in json.load(fh)['rows'] if int(r['n']) == int(row))
    except Exception:   # noqa: BLE001
        module = f'agent.agent{int(row):03d}_*'
    return f'cd ~/virtual_sanity/scrum_master_3/release/app && PYTHONPATH=. WID_ENV=localhost.rnd {PY} -m {module} check'


def unread_step(row, text):
    """HIS STEP FOR A FACT THE ROW COULD NOT GET (a table, a file or a record that cannot be read): see the fault whole by
    running the row by hand, and start his round again, one line each; '' when the red is not of that kind."""
    low = str(text or '').lower()
    if not any(w in low for w in UNREAD):
        return ''
    return f"see the fault whole: {check_line(row)}; then start his round again: {KICK}"


def wrap(row, check):
    """EVERY ROW UNDER THE 3 MINUTE RULE (shared_store.row_main wraps each row's check with this): a nightly row's red is
    held while the night's chain holds the tower's lock (the chain is the real run of its piece: the rows of the nightly
    container in his plan, never one that says chain false, the data sync), whether the row said its own step or not; a row that said its own chunk is otherwise left as it is; any other red
    says his step last: the fix loop's word for this red, else the row's own default line, else nothing added. A check
    that crashes is red, "he could not read it: ...", with his step to see the fault whole (unread_step)."""
    def looked():
        try:
            state, text = check()
        except Exception as e:   # noqa: BLE001  A CRASH IS RED WITH HIS STEP (2026-10-23): the row could not read its fact; run_check would say so too, but without the step
            said = ' '.join(f'he could not read it: {type(e).__name__}: {e}'.split())[:300]
            return chunk(row, 'red', said, step=unread_step(row, said))
        if state != 'red' or str(text).startswith(HELD):
            return state, text
        waiting = ''
        if int(row) in chain_rows():   # the night's pieces (his plan: the nightly container; the data sync says chain false: the daily schedule's, no piece of the chain)
            try:
                from agent import shared_native as native
                held = native.running()
                waiting = f"the chain holding the tower's lock ({held})" if held else ''
            except Exception:   # noqa: BLE001  (the lock unreadable: the red stands)
                waiting = ''
        if HAND in str(text):   # the row said its own step: RED STAYS RED (the owner 2026-10-23 20:40, 20:50: "HELD is not an answer"; 2026-10-22: a row turned green by how it judges is fake)
            if waiting:   # the chain at work on its piece is words before the step, never the light
                head, _, step = str(text).partition(' · ' + HAND)
                return 'red', _fit(head, f" · the chain is at work on it now ({brief(held)}) · {HAND}{step}")   # the chain's words kept whole and short: the why is cut before them
            return state, text
        return chunk(row, state, text, waiting=waiting, step=default_step(row) or unread_step(row, text))
    return looked


def process(words, run=subprocess.run):
    """The pid of a process whose command line holds these words ('' when none runs): the smoke test by hand, a build."""
    try:
        got = run(['pgrep', '-f', words], capture_output=True, text=True, timeout=10)
        pids = [p for p in str(got.stdout or '').split() if p.isdigit()]
        return pids[0] if pids else ''
    except Exception:   # noqa: BLE001
        return ''
