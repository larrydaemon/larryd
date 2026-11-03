"""AGENT 002 · THE STANDUP, TOP (the owner 2026-10-26: "this is next and this is probably the first top item in scrum master and in cmo";
2026-10-27: "the scrum master 2 has 2 agents so far: scrum master 2, standup"; "all agents below it are not mark IV they are sub
agents and lower rank"): A SUB AGENT of the MARK IV agent (agent001), the first item of the replica's TOP, its card LARRYD's under
SYSTEM in the species' own class (MARK I AGENT (NORMAL): lower rank, never MARK IV), its job in TOP's first shell, its logs its runs.
Its spoken-style standup, written from its own records alone, never invented: who it is, what ran yesterday, what runs today, what
went wrong. Where nothing happened, it says so plainly. ITS RULE AND ITS SKILLS are its job's own fields in LARRYD, written by the
MARK IV agent's run (the original's row 002, its program read by the reader); the gate face reads them from the record."""
import datetime
import os
import re
import zoneinfo

KEY = 'standup'
SLOT = 'TOP'   # where it lives: the first shell of TOP
ROW = 2   # its row in the original (agent002_top_standup)
NAME = 'Standup'
PITCH = 'The standup: one minute, his exact words'   # its card's pitch in LARRYD, the owner's own rule for it (the skills index: feedback-standup-one-minute)
WHAT = 'Built yesterday, building today, stuck: the one-minute standup'   # what it does, its one line
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'daily', 'time': '07:00', 'timezone': 'America/New_York'}   # when: daily 07:00, New York


OPEN = ('asked', 'building', 'waiting_takein')   # a request still being worked
RATE = 5.14   # syllables a second aloud (the script lab's measure, the owner's rule for it: feedback-standup-one-minute)
SPOKEN = (50, 70)   # ITS ONE MINUTE: the seconds aloud it must fall in, greeting and closing included
VOICE = {'service': 'http://127.0.0.1:8824', 'voice': 'christensen'}   # ITS VOICE, the owner's (Christensen, the script lab's voice service on this laptop) when agent.json names none
SAID = ('hello', 'yesterday', 'today', 'issues', 'bye')   # what the voice reads, in order


def syllables(text):
    """a line's syllables said aloud: each word's vowel groups (a silent final e dropped), each digit one, never less than one a word"""
    n = 0
    for w in re.findall(r"[A-Za-z']+|\d", text or ''):
        if w.isdigit():
            n += 1
            continue
        w = w.lower()
        k = len(re.findall(r'[aeiouy]+', w)) - (1 if w.endswith('e') and not w.endswith(('le', 'ee')) and len(w) > 2 else 0)
        n += max(k, 1)
    return n


def seconds(said):
    """THE STANDUP'S SPOKEN LENGTH, measured: everything the voice reads (hello, its three lines, goodbye), its syllables at RATE"""
    return round(sum(syllables(said.get(k)) for k in SAID) / RATE, 1)


def named(words):
    """a request said by name: his words' first line, no links, at most 12 words; '' when nothing speakable is left"""
    first = re.sub(r'https?://\S+', '', (words or '').strip().splitlines()[0] if (words or '').strip() else '')
    return ' '.join(re.findall(r"[A-Za-z0-9'][A-Za-z0-9'+\-]*", first)[:12])


def fill(said, more):
    """ITS ONE MINUTE FROM ITS OWN RECORDS: while the standup is under the middle of SPOKEN, the next of more ((key, sentence), each a
    fact of its own records) is said after its line, each only while the whole stays at most 5 s under SPOKEN's top. Never invented."""
    goal, top = sum(SPOKEN) / 2, SPOKEN[1] - 5
    for key, text in more:
        if seconds(said) >= goal:
            break
        before = said[key]
        said[key] = before + ' ' + text
        if seconds(said) > top:
            said[key] = before
    return said


def voiced(conf, text):
    """THE VOICE, MEASURED: the voice service (agent.json voice, else VOICE) asked to say the line in christensen's voice; its answer
    must be a sound (200, audio) within 60 s, never the default Mac voice. -> the voice's name; ValueError naming the fault."""
    import time
    import urllib.error
    import urllib.parse
    import urllib.request
    conf = conf or VOICE
    if not conf.get('service') or str(conf.get('voice')).lower() != 'christensen':
        raise ValueError(f"its voice is not christensen (agent.json voice: {conf!r})")
    ask = conf['service'].rstrip('/') + '/wav?' + urllib.parse.urlencode({'voice': conf['voice'], 'text': text[:600]})
    end = time.monotonic() + 60
    while True:
        left = end - time.monotonic()   # ITS 60 S IN ALL: each try waits at most what is left of the minute
        if left <= 0:
            raise ValueError(f"the voice {conf['voice']} at {conf['service']} made no sound in 60 s")
        try:
            with urllib.request.urlopen(ask, timeout=min(20, left)) as got:
                if got.status == 200 and got.headers.get('Content-Type', '').startswith('audio'):
                    return conf['voice']
                if got.status != 202:
                    raise ValueError(f"the voice {conf['voice']} at {conf['service']} answered {got.status} {got.headers.get('Content-Type')}")
        except urllib.error.HTTPError as e:
            raise ValueError(f"the voice {conf['voice']} at {conf['service']} answered {e.code}") from e
        except TimeoutError as e:
            raise ValueError(f"the voice {conf['voice']} at {conf['service']} made no sound in 60 s") from e
        except OSError as e:
            raise ValueError(f"the voice {conf['voice']} at {conf['service']} is not running ({e})") from e
        time.sleep(max(0, min(1, end - time.monotonic())))


def said_list(xs):
    xs = [x for x in xs if x]
    return (', '.join(xs[:-1]) + ' and ' + xs[-1]) if len(xs) > 1 else (xs[0] if xs else '')


def facts(conf, today, yesterday):
    """THE SCRUM MASTER'S OWN FACTS, read where they are, read only (its requests, its rows' runs, the project's changes):
    {'done', 'changes', 'open', 'red', 'stuck'}, every request as (id, his words) (the owner 2026-10-27: "missing the descriptions
    load them please"); None for an agent that names none."""
    import os
    import sqlite3
    import subprocess
    if not conf or not conf.get('db') or not conf.get('rows'):
        return None
    db = os.path.expanduser(conf['db'])
    con = sqlite3.connect(f'file:{db}?immutable=1', uri=True)
    try:
        done = [(r[0], r[1]) for r in con.execute("SELECT id, words FROM requests WHERE state IN ('green', 'shipped') AND substr(done_at, 1, 10) = ? ORDER BY done_at", (yesterday,))]
        open_ = [(r[0], r[1]) for r in con.execute(f"SELECT id, words FROM requests WHERE state IN ({','.join('?' * len(OPEN))}) ORDER BY position, id", OPEN)]
        stuck = [(r[0], r[1]) for r in con.execute("SELECT id, words FROM requests WHERE state = 'stuck_today' ORDER BY position, id")]
        last = {}
        for row, state in con.execute('SELECT row, state FROM row_runs WHERE substr(started, 1, 10) = ? ORDER BY started', (today,)):
            last[row] = state
    finally:
        con.close()
    import json as _json
    with open(os.path.expanduser(conf['rows']), encoding='utf-8') as fh:
        names = {r['n']: r['name'].lower() for r in _json.load(fh)['rows']}
    red = [names.get(n, f'row {n}') for n, state in sorted(last.items()) if state == 'red']
    changes = None   # NOT MEASURED until the git log is read: never a 0 that was not counted, never a stop (no git path named: not measured)
    if conf.get('git'):
        try:
            log = subprocess.run(['git', '-C', os.path.expanduser(conf['git']), 'log', '--oneline', f'--since={yesterday} 00:00', f'--until={today} 00:00'],
                                 capture_output=True, text=True, timeout=20)
            if log.returncode == 0:
                changes = len(log.stdout.splitlines())
        except (OSError, subprocess.SubprocessError):
            pass
    return {'done': done, 'changes': changes, 'open': open_, 'red': red, 'stuck': stuck}


def changes_said(n):
    """the day's change count in words: counted, or honestly not measured (the git log could not be read)"""
    return f'{n} changes in all' if n is not None else 'the changes not measured (the git log could not be read)'


def standup(agent, shells, zone='America/New_York', now=None, store=None, own=None):
    """THE STANDUP OF THE DAY, in his exact openings (the owner 2026-10-12: "yesterday i worked on / today im working on /
    these are the current issues"): from the agent's own facts (facts) when it has them, else from its own shells' runs.
    -> {'written', 'hello', 'yesterday', 'today', 'issues', 'bye', 'detail'}"""
    now = now or datetime.datetime.now(zoneinfo.ZoneInfo(zone))
    today, yesterday = now.date().isoformat(), (now.date() - datetime.timedelta(days=1)).isoformat()
    f = facts(agent.get('facts'), today, yesterday)
    if f is not None:
        done, open_, red, stuck = f['done'], f['open'], f['red'], f['stuck']
        y = (f"Yesterday I worked on {said_list([i for i, _w in done[:6]])}{' and more' if len(done) > 6 else ''}, {changes_said(f['changes'])}." if done
             else f"Yesterday I worked on nothing that went green, {changes_said(f['changes'])}.")
        td = (f"Today I'm working on {len(open_)} open {'request' if len(open_) == 1 else 'requests'}, first {said_list([i for i, _w in open_[:3]])}." if open_
              else "Today I'm working on nothing new: no request is open.")
        segs = ([f"{said_list(red)} {'are' if len(red) > 1 else 'is'} red"] if red else []) + ([f"{len(stuck)} {'request is' if len(stuck) == 1 else 'requests are'} stuck"] if stuck else [])
        issues = 'These are the current issues: ' + (', and '.join(segs) if segs else 'nothing is red') + '.'
        line = lambda i, w: f'{i} · {w[:90]}'   # a request: its id and his words (the owner 2026-10-27: "missing the descriptions load them please")
        detail = {'yesterday': [line(i, w) for i, w in done], 'today': [line(i, w) for i, w in open_], 'blocked': [*(f'{r} is red' for r in red), *(line(i, w) for i, w in stuck)]}
        more = ([('yesterday', f'One was {n}.') for _i, w in done if (n := named(w))] + [('today', f'One is {n}.') for _i, w in open_ if (n := named(w))]
                + [('issues', f'Stuck is {n}.') for _i, w in stuck if (n := named(w))])
    else:
        jobs = [sh['job'] for sh in shells if sh.get('job') and (sh['job'].get('data_full_name') or '').lower() != NAME.lower()]
        def name(j):
            return j.get('data_full_name') or j.get('data_agent_key') or 'a job'
        held = [sh for sh in shells if sh.get('job') and (sh['job'].get('data_full_name') or '').lower() != NAME.lower()]
        runs = {sh['job_key']: [r for r in (store.runs(sh['job_key'], 200) if store else []) if r['n'] >= 1] for sh in held}   # EACH JOB'S OWN RUNS, its LARRYD logs (RUN 1 and up), never its latest state and date alone

        def ran_on(sh, day, ended_done=False):
            return any(str(r['started_at'])[:10] == day and (r['exit'] == 0 or not ended_done) for r in runs[sh['job_key']])
        done = [name(sh['job']) for sh in held if ran_on(sh, yesterday, ended_done=True)]
        open_ = [name(sh['job']) for sh in held if ran_on(sh, today)]
        refused = [name(j) for j in jobs if j.get('data_job_run_state') == 'REFUSED']
        y = f"Yesterday I worked on {said_list(done)}." if done else 'Yesterday I worked on nothing: nothing ran.'
        td = f"Today I'm working on {said_list(open_)}." if open_ else "Today I'm working on nothing yet: nothing has run."
        issues = f"These are the current issues: {said_list(refused)} refused." if refused else 'These are the current issues: none.'
        detail = {'yesterday': done, 'today': open_, 'blocked': refused}
        more = []   # EACH JOB'S OWN RUNS SAID (its LARRYD logs): how often it ran yesterday and today, how its last run ended

        def times(k):
            return f"{k} {'time' if k == 1 else 'times'}"
        for sh in held:
            j, rs = sh['job'], runs[sh['job_key']]
            ys, ts = [r for r in rs if str(r['started_at'])[:10] == yesterday], [r for r in rs if str(r['started_at'])[:10] == today]
            if ys:
                more.append(('yesterday', f"{name(j)} ran {times(len(ys))}, {sum(1 for r in ys if r['exit'] == 0)} of them ended well."))
            if ts:
                more.append(('today', f"{name(j)} has run {times(len(ts))} so far."))
            if rs:
                r = max(rs, key=lambda r: (str(r['started_at']), r['n']))
                more.append(('today', f"The last run of {name(j)}, run {r['n']}, started at {str(r['started_at'])[11:16]} and ended {'well' if r['exit'] == 0 else 'with exit ' + str(r['exit'])}."))
            state = str(j.get('data_job_run_state') or '')
            if state in ('FAILED', 'REFUSED'):
                more.append(('issues', f"{name(j)} ended its last run {state.lower()}."))
    more += records(agent, shells, store, own, now)   # A QUIET DAY STILL ITS ONE MINUTE: more of its own records, said after the day's own facts
    said = {'written': now.strftime('%H:%M'), 'hello': f"Hey comrade! This is the standup of {agent['name']}, its sub agent.",
            'yesterday': y, 'today': td, 'issues': issues, 'bye': 'Full power, comrade. Keep the faith.', 'detail': detail}
    return fill(said, more)


def records(agent, shells, store, own, now):
    """ITS OWN RECORDS BEYOND THE DAY, each a fact read where it is, never invented: each job's runs of the last 7 days and its last run
    (its LARRYD logs), its own last standup run, its own schedule, and the agent's own card words and role (agent.json pitch and say).
    -> [(key, sentence)] for fill, the day's facts first, the agent's words last."""
    week = (now.date() - datetime.timedelta(days=6)).isoformat()
    out, held = [], []
    for sh in shells:
        j = sh.get('job') or {}
        nm = j.get('data_full_name') or j.get('data_agent_key') or ''
        if not nm or nm.lower() == NAME.lower():
            continue
        held.append(nm)
        state = str(j.get('data_job_run_state') or '').lower()
        out.append(('issues', f"{nm} stands {state} now." if state else f"{nm} has no run state yet."))
        if not store:
            continue
        rs = [r for r in store.runs(sh['job_key'], 1000) if (r['n'] or 0) >= 1 and str(r['started_at'])[:10] >= week]
        good = sum(1 for r in rs if r['exit'] == 0)
        out.append(('yesterday', f"In the last 7 days {nm} ran {len(rs)} {'time' if len(rs) == 1 else 'times'}, {good} of them ended well." if rs
                    else f"In the last 7 days {nm} has not run."))
    if held:
        out.insert(0, ('today', f"I hold {len(held)} {'job' if len(held) == 1 else 'jobs'}: {said_list(held)}."))
    if store and own:
        rs = sorted((r for r in store.runs(own, 1000) if (r['n'] or 0) >= 1), key=lambda r: (str(r['started_at']), r['n']))
        if rs:
            r = rs[-1]
            out.append(('today', f"My last standup was run {r['n']}, at {str(r['started_at'])[11:16]} on {str(r['started_at'])[:10]}, and it ended {'well' if r['exit'] == 0 else 'with exit ' + str(r['exit'])}."))
        else:
            out.append(('today', 'This is my first standup run on record.'))
    c = clock()
    out.append(('today', f"I write this standup every day at {c['when']} {c['zone'].title()} time, or when RUN AGENT is pressed."))
    pitch, say = ((agent.get('card_words') or {}).get('pitch') or '').strip(), (agent.get('say') or '').strip()
    if pitch:
        out.append(('hello', f"{agent['name']}: {pitch}"))
    if say:
        out.append(('hello', say))
    return out


NEW_YORK = zoneinfo.ZoneInfo(SCHEDULE['timezone'])
KEYS = ('written', 'hello', 'yesterday', 'today', 'issues', 'bye', 'detail', 'seconds', 'voice')
OPENINGS = (('yesterday', 'Yesterday I worked on'), ('today', "Today I'm working on"), ('issues', 'These are the current issues:'))


def ny_now(now=None):
    """This moment (or now) on the New York clock: the clock a run is stamped with and the day it is judged by."""
    return now.astimezone(NEW_YORK) if now and now.tzinfo else (now.replace(tzinfo=NEW_YORK) if now else datetime.datetime.now(NEW_YORK))


def fault_of(said):
    """WHAT IS WRONG WITH A WRITTEN STANDUP, or '' when it is whole: every key written, its three lines non-empty, each in his opening,
    its spoken length measured again from its words within SPOKEN (its one minute), its voice christensen's (voiced by its run)."""
    missing = [k for k in KEYS if k not in said]
    if missing:
        return f"the standup lacks {', '.join(missing)}"
    bad = [k for k, opening in OPENINGS if not isinstance(said[k], str) or not said[k].startswith(opening) or not said[k][len(opening):].strip(' .:')]
    if bad:
        return f"the standup's {' and '.join(bad)} line is empty or not in its opening"
    if not all(isinstance(said[k], str) for k in SAID):
        return 'the standup has a line that is not words'
    s = seconds(said)
    if not SPOKEN[0] <= s <= SPOKEN[1]:   # ITS ONE MINUTE OR RED: measured aloud from its own words, never the number it claims
        return f'the standup is {s} s aloud, outside {SPOKEN[0]} to {SPOKEN[1]} s'
    if str(said['voice']).lower() != 'christensen':
        return f"the standup's voice is {said['voice']!r}, not christensen"
    return ''


def run(store, job_key, n, agent, shells, chain=(), hire_with=None, now=None):
    """ONE RUN (its job's RUN, by hand or at 07:00): the day's standup written from the replica's own records, kept with the run,
    stamped on the New York clock (chain and hire_with: the MARK IV agent's, not this sub agent's). DONE exit 0 when its three lines
    are written; a line missing or empty, or a run that crashed: FAILED exit 1, the fault and its one step in the said JSON. -> what it wrote."""
    import json
    now = ny_now(now)
    started, day = now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d')
    try:
        said = standup(agent, shells, now=now, store=store, own=job_key)
        said['seconds'] = seconds(said)   # ITS ONE MINUTE, measured aloud (fault_of judges it within SPOKEN)
        try:
            said['voice'], unvoiced = voiced(agent.get('voice'), said['hello']), ''   # ITS VOICE, measured: christensen made a sound, never assumed
        except ValueError as e:
            said['voice'], unvoiced = None, str(e)
        fault = unvoiced or fault_of(said)
    except Exception as crash:   # A RUN THAT CRASHES IS RED: FAILED, exit 1, its fault named
        said, fault = {}, f'the run crashed: {(f"{type(crash).__name__}: {crash}".splitlines() or [type(crash).__name__])[0][:200]}'
    if fault:
        said['failed'] = f'{fault} · step: RUN AGENT again; if it comes back, fix agent/agent002_top_standup.py'
    said['ny_day'] = day
    store.ran(job_key, n, started, datetime.datetime.now(NEW_YORK).strftime('%Y-%m-%d %H:%M:%S'), 1 if fault else 0, json.dumps(said), 'FAILED' if fault else 'DONE')
    return said


def load_history(store, job_key, conf, days=2, now=None):
    """THE ORIGINAL'S DAYS, LOADED ONCE (the owner 2026-10-26: "you have yestedarys data so you can load it"): the Scrum Master's
    own standup runs of the last days (its row 2: start, end, green or red) and the standup it wrote each day (its note, three
    lines), read where they are, read only, into this job's runs; a run already loaded is never loaded twice. -> how many."""
    import json
    import os
    import sqlite3
    if not conf or not conf.get('db'):
        return 0
    now = now or datetime.datetime.now(zoneinfo.ZoneInfo(SCHEDULE['timezone']))
    since = (now.date() - datetime.timedelta(days=days - 1)).isoformat()
    con = sqlite3.connect(f"file:{os.path.expanduser(conf['db'])}?immutable=1", uri=True)
    try:
        rows = con.execute("SELECT started, ended, state FROM row_runs WHERE row = 2 AND started >= ? ORDER BY started", (since,)).fetchall()
        notes = dict(con.execute('SELECT day, text FROM notes WHERE day >= ?', (since,)).fetchall())
    finally:
        con.close()
    have = {r['started_at'] for r in store.runs(job_key, 1000)}
    loaded = 0
    for started, ended, state in rows:
        at = started[:19].replace('T', ' ')
        if at in have or state not in ('green', 'red'):
            continue
        lines = [l for l in (notes.get(started[:10]) or '').splitlines() if l.strip()]
        said = {'written': at[11:16], 'hello': 'Hey comrade! This is Scrum Master, a super agent harness on LARRYD.',
                'yesterday': lines[0] if len(lines) > 0 else '', 'today': lines[1] if len(lines) > 1 else '', 'issues': lines[2] if len(lines) > 2 else '',
                'bye': 'Full power, comrade. Keep the faith.', 'detail': {'yesterday': [], 'today': [], 'blocked': []}, 'loaded': True}
        store.ran(job_key, 0, at, ended[:19].replace('T', ' '), 0 if state == 'green' else 1, json.dumps(said), 'DONE')
        loaded += 1
    return loaded


def latest(store, job_key, now=None):
    """TODAY'S STANDUP: what this job's latest run (numbered 1 or more, by started_at) wrote, when it started today in New York and ended
    DONE exit 0 with its three lines whole; else None (no run yet, a run of another day, a loaded run of the original, or a FAILED one)."""
    import json
    day = ny_now(now).strftime('%Y-%m-%d')
    for r in sorted((r for r in store.runs(job_key, 1000) if (r['n'] or 0) >= 1), key=lambda r: (r['started_at'], r['n']), reverse=True)[:1]:   # two runs in one second: the higher number is the newer
        try:
            said = json.loads(r['said'])
        except (TypeError, ValueError):
            return None
        whole = isinstance(said, dict) and said.get('ny_day', str(r['started_at'])[:10]) == day == str(r['started_at'])[:10] and r['exit'] == 0 and not fault_of(said)
        return said if whole else None
    return None


def until_next(now=None, schedule=None):
    """Seconds to a top item's next run: the next time of its schedule (the standup's 07:00 when none), in its time zone."""
    schedule = schedule or SCHEDULE
    zone = zoneinfo.ZoneInfo(schedule['timezone'])
    now = now or datetime.datetime.now(zone)
    h, m = (int(x) for x in schedule['time'].split(':'))
    nxt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if nxt <= now:
        nxt += datetime.timedelta(days=1)
    return (nxt - now).total_seconds()


def clock(schedule=None):
    """A top item's clock in its shell, its job's schedule said simply (NEW YORK · 7:00 AM · DAILY), its hands on its time."""
    schedule = schedule or SCHEDULE
    h, m = (int(x) for x in schedule['time'].split(':'))
    when = datetime.time(h, m).strftime('%I:%M %p').lstrip('0')
    return {'zone': schedule['location'], 'at': schedule['time'], 'said': f"{when} · {schedule['schedule_type'].upper()}", 'when': when,
            'repeat': schedule['schedule_type'].upper(), 'hour_deg': (h % 12) * 30 + m * 0.5, 'minute_deg': m * 6}


def with_words(block, conf):
    """THE ORIGINAL'S LISTS WITH HIS WORDS (the owner 2026-10-27: "missing the descriptions load them please"): the original's
    block names a request by its id alone; each bare id gets his words after it, read from the Scrum Master's own requests
    table (facts db), read only; nothing else of the block is touched. -> the block."""
    import os
    import re
    import sqlite3
    from markupsafe import escape
    if not block or not conf or not conf.get('db'):
        return block
    ids = set(re.findall(r'scrum-item">• (R-\d{4})</div>', block))
    if not ids:
        return block
    con = sqlite3.connect(f"file:{os.path.expanduser(conf['db'])}?immutable=1", uri=True)
    try:
        words = dict(con.execute(f"SELECT id, words FROM requests WHERE id IN ({','.join('?' * len(ids))})", sorted(ids)).fetchall())
    finally:
        con.close()
    return re.sub(r'(scrum-item">• )(R-\d{4})(</div>)', lambda m: f'{m.group(1)}{m.group(2)}{" · " + str(escape(words[m.group(2)][:90])) if words.get(m.group(2)) else ""}{m.group(3)}', block)


def original_block(page_url):
    """THE ORIGINAL'S STANDUP, as its own page shows it now (the owner 2026-10-26: "the fucking agent is done you just need to
    copy and update"): its clarity block, written by its own round and its model, read from its page, read only. None when
    its page does not answer."""
    import re
    import urllib.request
    try:
        with urllib.request.urlopen(page_url, timeout=90) as r:   # his page is big: read at its own moments, never on a draw
            h = r.read().decode('utf-8', 'replace')
    except OSError:
        return None
    at = h.find('id="scrum-standup"')   # its block, by its id
    i = h.rfind('<div', 0, at) if at >= 0 else -1
    if i < 0:
        return None
    depth, j = 0, i
    for m in re.finditer(r'<(/?)div\b[^>]*>', h[i:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            j = i + m.end()
            break
    return h[i:j]


ROW_FILE = 'agent002_top_standup.py'   # the original's program for this row: its skills index is filed under it


def content(store, job_key, block=None):
    """ITS OWN CONTENT ON THE ONE CANVAS (the owner 2026-10-27: "so all the agents use the same style"): words, never markup (the replica
    draws them, web/page.py content_view): the original's own block when the host read it (1 to 1), else the standup its last run wrote (the
    hello, its three sentences, the goodbye, the detail folded), with the READ THE STANDUP button inside it at its foot (the owner 2026-10-27:
    "a clarity big black button inside instead of the little pink one on top"); else that nothing is written yet."""
    s = latest(store, job_key)
    voice = {'kind': 'voice', 'label': 'Read the standup', 'making': 'Christensen is getting ready…', 'reading': 'Christensen is reading the standup',
             'down': 'The voice is not running (start the script lab’s voice)'}
    if block:
        return [{'kind': 'html', 'html': block}, voice]
    if s is None:
        return [{'kind': 'note', 'title': 'The standup', 'text': 'Not written today: its run writes it (daily 07:00 New York, or RUN AGENT).'}]
    return [{'kind': 'words', 'title': 'The standup', 'under': f'Written at {s["written"]}, by its run',
                    'lines': [('body', s['hello'], ''), ('subtitle', s['yesterday'], 'yesterday'), ('subtitle', s['today'], 'today'), ('subtitle', s['issues'], 'blockers'), ('body', s['bye'], '')],
                    'detail': [('yesterday', 'Yesterday', s['detail']['yesterday']), ('today', 'Today', s['detail']['today']), ('blocked', 'Blocked', s['detail']['blocked'])]}, voice]
