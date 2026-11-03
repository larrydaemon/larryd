"""ROW 039 IN SYNC (D THE NIGHTLY, every round): TODAY'S DATA SYNC REACHED THIS LAPTOP AND SLOT B EXACTLY, OR NOT (the owner
2026-10-23: "data synced or not.. and no moving the databases or anything this is pure data to update a database nothing
more"; 2026-10-25: "does it work or not? can it be fixed in 3 min or not"). The data sync copies the live COTECLAT and demo
data down to this laptop (localhost) and to slot B rnd (b_rnd): each side's newest finished sync, as the sync itself wrote it
in row_runs under its side's row (033 PUBLISH LOCALHOST PF, 035 PUBLISH B RND: 'running: ...', 'exact: N records, 0 missing,
0 extra, 0 different', 'stopped at <step>: <why>'), is the fact. Exact = synced. GREEN when every side is synced; RED naming
every side not synced. HIS ONE STEP, ONE PIECE ALONE (the owner 2026-10-23 20:50: the carry alone, never the whole sync;
"the step needs to run on its own again to clear"): the step the first side stopped at, run alone through the sync's own
subcommand (agent033 run_step), the round or the carry of the one account its words name when they name one; a side that
never ran to its end, or whose sync was killed mid-way, its FIRST step alone, then each step after it alone in turn
(cleared): a side is synced again when its stopped step and every step after it ran alone OK, the last compare exact. The
steps' real times are their own (2026-10-23: localhost's whole sync 7.5 min, its apply about 3; b_rnd's carry with its
compare 4 to 5 min for both accounts, one account alone less); settings sync.steps.*.minutes are each step's ceiling, never
its time, and the step's own last time alone is said (took). A SYNC RUNNING NOW IS WORDS (HELD IS NOT AN ANSWER, the owner
2026-10-23; 2026-10-25): the newest finished sync stays the light. The job line (schemas/rows.json) says the data since
2026-10-25. The commits of the laptop, slot B and the apps are WORDS after it, never this row's red (the owner 2026-10-23:
pure data, nothing more).
python -m agent.agent039_nightly_in_sync check: one look, its run written in row_runs (row 039)."""
import datetime
import json
import os
import re
import sys

from agent import shared_native as native       # the native targets and their kept builds (words only)
from agent import shared_night as night         # the night's own files, read by the one reader (N9; words only)
from agent import shared_schedule as schedule   # the clock (_clock)
from agent import shared_store as store         # row_runs: the sync's own runs, the row's main
from agent import shared_where as where         # his places, by settings.json (sync.sides)
from agent import shared_chunks as chunks       # THE 3 MINUTE RULE (the owner 2026-10-23): why first, his one step last; a sync at work is words
from agent import shared_carry as carry          # the carry's own words when the run's text has none (the owner 2026-10-23 21:35)

ROW = 39
SIDES = {'localhost': 33, 'b_rnd': 35}          # whose row a side's sync run is, as the sync writes it: PUBLISH LOCALHOST PF (033), PUBLISH B RND (035)
SYNC_SAYS = ('running: ', 'exact: ', 'stopped at ')   # THE SYNC'S OWN WORDS: only a run that begins so is the sync's (a row's own look begins 'the sync ' or 'publish: ', never these)
SYNC_LINE = 'cd ~/virtual_sanity/scrum_master_3/release/app && PYTHONPATH=. ' + chunks.PY + ' -m agent.agent033_nightly_publish_localhost_pf {side} {step}'   # THE SYNC BY HAND: the sync's own subcommand for a side (localhost | b_rnd), the data only, never a build, never a chain


def sides():
    """THE SIDES OF THE DATA SYNC, as his settings name them (sync.sides), of those the sync writes a run for."""
    named = list(((where.SETTINGS.get('sync') or {}).get('sides') or {}).keys())
    return [s for s in named if s in SIDES] or list(SIDES)


def _at(text):
    try:
        got = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return got if got.tzinfo else got.replace(tzinfo=datetime.timezone.utc)


def sync_runs(st, side):
    """Every run the sync itself wrote for a side, oldest first (its row's runs whose text begins with the sync's own words)."""
    try:
        runs = st.runs(row=SIDES[side])
    except (OSError, ValueError, KeyError):
        return []
    return sorted((r for r in runs if str(r.get('text') or '').startswith(SYNC_SAYS) and _at(r.get('started'))), key=lambda r: _at(r['started']))


def allowed(side):
    """How long a side's whole sync may take, in minutes: the sum of its steps' own minutes (settings sync.sides, sync.steps.*.minutes),
    plus 5 to write its end; 60 when none is named."""
    conf = where.SETTINGS.get('sync') or {}
    steps = [s for s in (conf.get('sides') or {}).get(side) or [] if not str(s).startswith('needs:')]
    total = sum(int(((conf.get('steps') or {}).get(s) or {}).get('minutes') or 0) for s in steps)
    return (total or 60) + 5


def step_of(words):
    """THE PIECE TO RUN AGAIN ALONE (the owner 2026-10-23: "the fix is a sync whose failed step, the carry, runs again in under 3
    minutes on its own"): the step a side stopped at, from its words; '' when they name no stop."""
    got = re.search(r'stopped at (\w+)', words or '')
    if not got:
        return ''
    who = re.search(r'the ([a-z]+) account NOT exact', words or '')   # the carry's result names the account that is not exact: that account alone (minutes), never both
    return got.group(1) + (f' {who.group(1)}' if who and got.group(1) == 'carry' else '')


STEP_LOG = where.report('sync_steps')   # ONE STEP RUN ALONE, each its own line (agent033 run_step writes it; named in reports.json, so the scrub keeps it): the chunk that clears a stopped side


def steps_alone(side, since=None):
    """A side's steps run alone and ended, oldest first, since a moment (the step log). -> [{step, accounts, started, ended, ok, why, exact, counts}]"""
    try:
        with open(STEP_LOG, encoding='utf-8') as fh:
            rows = [json.loads(x) for x in fh if x.strip()]
    except (OSError, ValueError):
        return []
    mine = [r for r in rows if isinstance(r, dict) and r.get('side') == side and r.get('ended') and _at(r.get('started')) and (since is None or _at(r['started']) >= since)]
    return sorted(mine, key=lambda r: _at(r['started']))


def carry_alone(side, since):
    """THE CARRY'S OWN RECORD (the owner 2026-10-23 22:53: run it now; row 039 judges the slot's state, not who ran it): the
    side's carry run by its own tool since a moment writes the same result file the carry step reads; its newest result
    made since, as a step record: ok when the carry says ok, its accounts named. -> [] or [one record]"""
    if not since:
        return []
    result = carry.result_of(side, since=since.timestamp())
    if not result or not isinstance(result, dict) or 'ok' not in result:
        return []
    path = carry.result_path(side, since=since.timestamp())
    try:
        made = datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc)
    except (OSError, TypeError):
        return []
    stamp = made.isoformat(timespec='seconds')
    return [{'side': side, 'step': 'carry', 'accounts': [str(a) for a in (result.get('accounts') or [])], 'started': stamp, 'ended': stamp,
             'ok': bool(result.get('ok')), 'why': carry.words(result), 'exact': bool(result.get('ok')), 'counts': {}}]


def side_steps(side):
    """The side's steps in order, as his settings name them (sync.sides), the needs: ones left out."""
    conf = where.SETTINGS.get('sync') or {}
    return [s for s in (conf.get('sides') or {}).get(side) or [] if not str(s).startswith('needs:')]


def cleared(side, run, began=None):
    """A STOPPED SIDE CLEARED BY ITS CHUNKS (the owner 2026-10-23: "the step needs to run on its own again to clear"; "if any of
    the 3 fail its red"): the step the run stopped at, run alone OK after the run began, then every step of the side after it
    run alone OK in turn, the last compare exact. run None: a side that never ran to its end (began None) or was killed
    mid-way (began its start): from its FIRST step. -> (state, words): green "<side> exact (N records, HH:MM) · <step> alone
    (<accounts>) OK"; red "<side>: stopped at <step>: alone: <why> (HH:MM)" when a chunk's newest run alone failed; red
    "<side>: stopped at <next>: <step> alone OK (HH:MM), <next> not run alone since" when a later step is owed (a green also
    carries its last chunk's end, for the 30 h); None when the
    stopped step never ran alone since (the run's own words stand)."""
    order = side_steps(side)
    if run is None:
        stopped = order[0] if order else ''
    else:
        stopped, began = first_real(side, step_of(str(run.get('text') or '')).split(' ')[0]), _at(run.get('started'))   # the step's bare name (step_of adds the carry's account)
        if not began:
            return None
    if not stopped or stopped not in order:
        return None
    alone, moment, chain, records, when = steps_alone(side, began) + carry_alone(side, began), began, [], None, ''
    for name in order[order.index(stopped):]:
        recs = sorted((r for r in alone if r.get('step') == name and (moment is None or _at(r['started']) >= moment)), key=lambda r: _at(r['started']))
        if not recs:
            if name == stopped:
                return None
            return 'red', f"{side}: stopped at {name}: {chain[-1]} OK ({when}), {name} not run alone since"
        last = recs[-1]
        when = schedule._clock(last.get('ended') or last['started'])
        if not last.get('ok'):
            return 'red', f"{side}: stopped at {name}: alone: {last.get('why') or 'no words'} ({when})"
        names = ' '.join(last.get('accounts') or [])
        chain.append(f"{name} alone" + (f" ({names})" if names else ''))
        moment = _at(last['started'])
        counts = last.get('counts') if isinstance(last.get('counts'), dict) else {}
        if counts and not last.get('exact'):
            return 'red', f"{side}: stopped at {name}: alone: {last.get('why') or 'not exact'} ({when})"
        if counts:
            records = counts.get('records', 0)
    said = f"{side} exact ({records} records, {when})" if records is not None else f"{side}: every step alone OK ({when})"
    return 'green', said + ' · ' + f"{chain[0]} OK", (last.get('ended') or last['started'])   # its last chunk's end: the 30 h is counted from it (_stale)


def first_real(side, step):
    """A STOP AT A SIDE IT STANDS ON (needs:<other>, its regex word 'needs') is no step of this side to run: the side's first own
    step (the carry of b_rnd), once the side it stands on is synced (that side's own red comes first, look). -> step"""
    return (side_steps(side) or [''])[0] if step == 'needs' else step


def took(side, step):
    """THE STEP'S OWN TIME ALONE, the last time it ran alone (the step log's seconds): ' · <step> alone took N s the last time
    (HH:MM)', or '' when it never ran alone (no number without a reason: the settings' minutes are its ceiling, never its time)."""
    name = str(step or '').split(' ')[0]
    runs = [r for r in steps_alone(side) if r.get('step') == name and isinstance(r.get('seconds'), (int, float))]
    if not runs:
        return ''
    last = runs[-1]
    return f" · {name} alone took {round(float(last['seconds']))} s the last time ({schedule._clock(last.get('ended') or last['started'])})"


def side_word(st, side):
    """ONE SIDE: synced or not. -> (state, words, step, running): 'green' "<side> exact (N records, HH:MM)" or 'red'
    "<side>: stopped at <step>: <why> (HH:MM)", "<side>: never ran" or "<side>: its sync since HH:MM never ended, past its N
    min (killed mid-way)", the newest FINISHED sync the fact; a stopped side whose stopped step and the steps after it ran
    alone OK since is cleared (cleared); step: the piece his hand runs alone ('' when green); running: "the sync of <side>
    runs since HH:MM" when its newest run is still going, begun after the newest finished one: words, never the light."""
    runs = sync_runs(st, side)
    done = [r for r in runs if r.get('state') != 'running' and r.get('ended')]
    going = [r for r in runs if r.get('state') == 'running' or not r.get('ended')]
    running = ''
    if going and (not done or _at(going[-1]['started']) > _at(done[-1]['started'])):
        began, most = _at(going[-1]['started']), allowed(side)
        if began and (datetime.datetime.now(datetime.timezone.utc) - began).total_seconds() > most * 60:   # no end written past its minutes: killed mid-way (the reader 2026-10-23), not synced, never held for ever
            return _first(side, f"{side}: its sync since {schedule._clock(going[-1]['started'])} never ended, past its {most} min (killed mid-way)", began, '')
        running = f"the sync of {side} runs since {schedule._clock(going[-1]['started'])}"
    if not done:
        return _first(side, f'{side}: never ran' + (' to its end' if running else ''), None, running)
    last = done[-1]
    text = str(last.get('text') or '')
    when = schedule._clock(last.get('ended') or last['started'])
    if last.get('state') == 'green' and text.startswith('exact: '):
        if not _stale(last.get('ended') or last['started']):
            return 'green', f"{side} exact ({text[len('exact: '):].split(',')[0]}, {when})", '', running
        return _first(side, f"{side}: {_stale(last.get('ended') or last['started'])} ({when})", _cutoff(), running)   # STALE: its first step alone, then each after it in turn, within the 30 h
    chunked = cleared(side, last)   # the stopped step run alone since, and the steps after it (the owner 2026-10-23: the chunk clears it)
    if chunked and chunked[0] == 'green' and _stale(chunked[2]):   # chunks older than the 30 h are no proof either: the side again from its first step
        return _first(side, f"{side}: {_stale(chunked[2])}", _cutoff(), running)
    if chunked:
        return chunked[0], chunked[1], (_step(chunked[1]) if chunked[0] == 'red' else ''), running
    said = f'{side}: {with_carry_words(text, side, last)} ({when})'
    return 'red', said, _step(said, side), running


def _stale(moment):
    """AN EXACT SYNC, OR ITS CHUNKS' LAST, COUNTS WHILE IT IS WITHIN THE NIGHT READER'S 30 H (the reader 2026-10-25: yesterday's
    exact is no proof of today's). -> '' when fresh, else the words of its age"""
    return night.too_old(None, [{'by': 'rerun', 'finished': moment}]).replace('the newest pass', 'its newest exact sync')


def _cutoff():
    """the moment the 30 h began: chunks run alone after it clear a stale side"""
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=night.MAX_AGE_HOURS)


def _step(words, side=''):
    """the piece a side's red words name, alone: the step it stopped at (with the one account when named), a stop at a side
    it stands on its own first step"""
    got = step_of(words)
    bare = got.split(' ')[0]
    return first_real(side, bare) if side and bare == 'needs' else got


def _first(side, words, began, running):
    """A SIDE THAT NEVER RAN TO ITS END, OR WAS KILLED MID-WAY: no stop is known, so its first step alone and each after it in
    turn (cleared, run None); its chunks' word when they ran since, within the 30 h (the reader 2026-10-25: never chunks of
    any age), else red with its first step. -> side_word's four"""
    chunked = cleared(side, None, max(began, _cutoff()) if began else _cutoff())
    if chunked and chunked[0] == 'green' and not _stale(chunked[2]):
        return 'green', chunked[1], '', running
    if chunked:
        return 'red', chunked[1], _step(chunked[1]), running
    return 'red', words, (side_steps(side) or [''])[0], running


def with_carry_words(text, side, run):
    """A stopped side's words with the carry's own when the run's why says nothing (the owner 2026-10-23 21:35: "stopped at
    carry: exit 1: }" was the JSON's last line; the fault was in the carry's result file: the demo account landed 0 of 1499
    records). A why with no letter or digit in it is no words: the newest result of that side's carry, made at or after
    the run began, speaks."""
    head, sep, rest = text.partition(': exit ')
    if sep:
        code, _, why = rest.partition(': ')
        prefix = f'{head}: exit {code}'
    else:
        prefix, _, why = text.partition(': ')
    if re.search(r'[A-Za-z0-9]', why or ''):
        return text
    began = _at(run.get('started'))
    said = carry.fault(side, since=began.timestamp() if began else None)
    return f"{prefix}: {said or 'no words of its own (its result file does not read either)'}"


def look(st=None):
    """THE DATA IS SYNCED OR NOT: every side. -> (state, text, step, waiting): green "data synced: ..."; red "data not
    synced: <every side not synced> · <the synced ones>" with ONE step: the first side's piece alone, a side that stands
    on another not synced waiting on that side's red first; a sync running now is words (waiting), never the light. The
    commits are words after it (commits_said), never the light."""
    st = st or store.door()
    words_ = [(side, *side_word(st, side)) for side in sides()]
    bad = [(side, w, step) for side, state, w, step, _ in words_ if state == 'red']
    good = [w for side, state, w, _, _ in words_ if state == 'green']
    running = '; '.join(r for *_, r in words_ if r)
    tail = commits_said(st)
    if bad:   # ONE RED, the first side not synced (the owner 2026-10-23 20:55); a side stopped at needs:<other> waits on that side's own red first
        side, _, step = next((b for b in bad if 'stopped at needs:' not in b[1]), bad[0])
        text = 'data not synced: ' + '; '.join(w for _, w, _ in bad) + (' · ' + ' · '.join(good) if good else '') + took(side, step)
        return 'red', text + tail, SYNC_LINE.format(side=side, step=step).rstrip(), running
    return 'green', 'data synced: ' + ' · '.join(good) + (f' · {running}' if running else '') + tail, '', ''


def check():
    """ROW 039's one look: the data synced or not (look), under the 3 minute rule: red why first with that one piece alone
    last, a sync at work said as words before it; else green. -> (state, text)"""
    state, text, step, waiting = look(store.door())
    return chunks.chunk(ROW, state, text, waiting=waiting, step=step)


# ---------------------------------------------------------------- THE COMMITS, WORDS ONLY (never this row's red since 2026-10-23)
def _read(name):
    with open(where.path(name), encoding='utf-8') as fh:
        return fh.read()


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def current(tower):
    """THE SPRINT SLOT, AS THE PLATFORM'S FILES SAY IT: the swap's log (swaps.jsonl, the last flip that ended
    'committed') names the live slot, before any flip tower.swap.start does; the current slot is the other one of
    tower.sprint.slots. A switch on no one of the two slots, or a last flip whose way back failed, raises ValueError."""
    slots = (tower.get('sprint') or {}).get('slots') or {}
    try:
        rows = [json.loads(x) for x in _read('swaps').splitlines() if x.strip()]
    except FileNotFoundError:
        rows = []
    moved = [r for r in rows if r.get('result') in ('committed', 'rolled back', 'ROLLBACK FAILED')]
    if moved and moved[-1]['result'] == 'ROLLBACK FAILED':
        raise ValueError(f"the last flip (to {moved[-1].get('to')}) failed and its way back failed: where the name points is not known from the record")
    flips = [r for r in rows if r.get('result') == 'committed' and r.get('to') in slots]
    live = flips[-1]['to'] if flips else (tower.get('swap') or {}).get('start')
    others = [s for s in slots if s != live]
    if live not in slots or len(others) != 1:
        raise ValueError(f'the switch points at {live!r}: not one of the two slots {list(slots)} (tower.swap.start, tower.sprint.slots)')
    return others[0]


def published():
    """The commit this laptop's pf side runs: the newest publish that went in (status OK or ROLLED BACK), as the tower's
    Deploy History beside its tree keeps it (preflight_pf: publish_<stamp>.json); '' when none."""
    folder = where.path('preflight_pf')
    try:
        names = [f for f in os.listdir(folder) if f.startswith('publish_') and f.endswith('.json')]
    except OSError:
        return ''
    done = sorted((_json(os.path.join(folder, f)) for f in names), key=lambda m: str(m.get('made_at', '')), reverse=True)
    return next((m.get('local') or '' for m in done if m.get('status') in ('OK', 'ROLLED BACK')), '')


def commits(st=None):
    """THE COMMIT ON EACH SIDE (the night, localhost pf, the sprint slot's rnd side, the built apps), as the files say it:
    -> (one: every side on one commit, {side: commit}); raises when the lanes cannot be read."""
    tower = json.loads(_read('global_config')).get('tower') or {}
    slot = current(tower)
    rnd = _json(os.path.join(os.path.expanduser((tower.get('slots') or {}).get('records') or ''), f'{slot}.rnd', 'state.json'))
    n = night.night()
    at = {'the night': (n or {}).get('commit') or '', 'localhost pf': published(), f'{slot} rnd': rnd.get('commit') or ''}
    at.update({name: (native.kept(name) or {}).get('commit') or '' for name in native.targets()})
    return len(set(at.values())) == 1 and all(at.values()), at


def commits_said(st=None):
    """THE COMMITS AS WORDS ONLY (the owner 2026-10-23: this row is the data, nothing more): ' · commits: all on <12 hex>'
    (and the requests shipped from it, N7/N8, as before), or each side's commit by name; the lanes unreadable is said,
    never a red. -> words (beginning ' · ') or ''"""
    try:
        one, at = commits(st)
    except Exception as e:   # noqa: BLE001  (words only)
        return f' · commits: not readable ({type(e).__name__}: {str(e)[:80]})'
    if not one:
        return ' · commits: ' + ', '.join(f'{k} {v[:9] or "none"}' for k, v in at.items())
    said = f" · commits: all on {next(iter(at.values()))[:12]}"
    try:   # SHIPPED FROM HERE (item 6, N7, N8): the requests green on the night's commit, now on every side
        from agent import shared_requests as requests
        made = requests.shipped(st or store.door(), night.night())
        if made:
            said += f" · shipped: {', '.join(made)}"
    except Exception as e:   # noqa: BLE001  (said on the row; the words stand)
        said += f' · the shipping could not run: {type(e).__name__}: {e}'
    return said


if __name__ == '__main__':
    sys.exit(store.row_main(ROW, check, sys.argv[1:]))
