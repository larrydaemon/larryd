"""STANDUP, Scrum Master 3's TOP agent: the one-minute standup in the owner's exact openings (the owner 2026-10-12: "yesterday i
worked on / today im working on / these are the current issues"), from the office's own records alone: its requests (the office's
database), its workflow's red (the jobs records' lights), the project's changes (git). A RUN writes it, measures it aloud (its
minute, agent.json spoken_seconds) and has the voice say its hello; a CALL shows the standup its last RUN wrote."""
import datetime
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

import look
import office

OPEN_TODAY = ('building', 'proven', 'reviewed', 'approved')
SAID = ('hello', 'yesterday', 'today', 'issues', 'bye')



def syllables(text):
    n = 0
    for w in re.findall(r"[A-Za-z']+|\d", text or ''):
        if w.isdigit():
            n += 1
            continue
        w = w.lower()
        n += max(len(re.findall(r'[aeiouy]+', w)) - (1 if w.endswith('e') and not w.endswith(('le', 'ee')) and len(w) > 2 else 0), 1)
    return n


def seconds(said):
    return round(sum(syllables(said.get(k)) for k in SAID) / float(office.fact('syllables_a_second')), 1)


def named(words):
    """a request said by name: his words' first line, no links, at most 12 words"""
    first = (words or '').strip().splitlines()[0] if (words or '').strip() else ''
    return ' '.join(re.findall(r"[A-Za-z0-9'][A-Za-z0-9'+\-]*", re.sub(r'https?://\S+', '', first))[:12])


def listed(xs):
    xs = [x for x in xs if x]
    return (', '.join(xs[:-1]) + ' and ' + xs[-1]) if len(xs) > 1 else (xs[0] if xs else '')


def changes(today, yesterday):
    """yesterday's commits by their subjects, or None when git could not be read (never a 0 that was not counted)"""
    try:
        got = subprocess.run(['git', '-C', office.fact('git'), 'log', '--format=%s', f'--since={yesterday} 00:00', f'--until={today} 00:00'],
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return got.stdout.splitlines() if got.returncode == 0 else None


def facts(given, today, yesterday):
    con = office.db()
    q = lambda sql, *a: [dict(r) for r in con.execute(sql, a)]  # noqa: E731
    done = q("SELECT id, words FROM requests WHERE state IN ('green', 'shipped', 'waiting_takein') AND substr(done_at, 1, 10) = ? ORDER BY done_at", yesterday)
    open_ = q(f"SELECT id, words FROM requests WHERE state IN ({','.join('?' * len(OPEN_TODAY))}) OR (state = 'waiting_takein' AND substr(done_at, 1, 10) = ?) "
              "OR (state = 'asked' AND substr(asked_at, 1, 10) = ?) ORDER BY position, id", *OPEN_TODAY, today, today)
    stuck = q("SELECT id, words FROM requests WHERE state = 'stuck_today' ORDER BY position, id")
    before = q("SELECT id, words, substr(done_at, 1, 10) AS day FROM requests WHERE state IN ('green', 'shipped') AND substr(done_at, 1, 10) < ? ORDER BY done_at DESC LIMIT 20", yesterday)
    counts = dict(con.execute('SELECT state, count(*) FROM requests GROUP BY state').fetchall())
    con.close()
    blocks = [j for j in office.workflow(given) if j.get('data_job_agentic') != 'WORKFLOW']
    red = [j.get('data_full_name') for j in blocks if office.light_of(j) == 'RED']
    ran = [j.get('data_full_name') for j in blocks if office.light_of(j) == 'GREEN' and (j.get('data_job_today_date') or '') == today]
    return {'done': done, 'open': open_, 'stuck': stuck, 'before': before, 'counts': counts, 'red': red, 'ran': ran, 'made': changes(today, yesterday)}


def standup(given):
    now = office.now()
    today, yesterday = now.date().isoformat(), (now.date() - datetime.timedelta(days=1)).isoformat()
    f = facts(given, today, yesterday)
    low, high = office.fact('spoken_seconds')
    hello, bye = office.fact('hello'), office.fact('bye')
    made = 'the changes not measured (the git log could not be read)' if f['made'] is None else f"{len(f['made'])} changes in all"
    lines = {'yesterday': (f"Yesterday I worked on {listed([r['id'] for r in f['done'][:6]])}{' and more' if len(f['done']) > 6 else ''}, {made}." if f['done']
                           else f'Yesterday I worked on nothing that went green, {made}.'),
             'today': "Today I'm working on nothing new: no request is open.",
             'issues': 'These are the current issues: ' + (', and '.join(
                 ([f"{listed(f['red'])} {'are' if len(f['red']) > 1 else 'is'} red"] if f['red'] else [])
                 + ([f"{len(f['stuck'])} {'request is' if len(f['stuck']) == 1 else 'requests are'} stuck"] if f['stuck'] else [])) or 'nothing is red') + '.'}
    said = lambda: {'hello': hello, **lines, 'bye': bye}  # noqa: E731
    goal, top = (low + high) / 2, high - 5

    def add(key, text):
        if seconds(said()) >= goal:
            return False
        was = lines[key]
        lines[key] = was + ' ' + text
        if seconds(said()) > top:
            lines[key] = was
        return True
    if f['open']:
        names = []
        line = lambda ns: f"Today I'm working on {len(f['open'])} open {'request' if len(f['open']) == 1 else 'requests'}" + (f', first {listed(ns)}.' if ns else '.')  # noqa: E731
        lines['today'] = line(names)
        for r in f['open']:
            n = named(r['words'])
            if not n or seconds(said()) >= goal:
                break
            was = lines['today']
            lines['today'] = line(names + [n])
            if seconds(said()) > top:
                lines['today'] = was
                break
            names.append(n)
    for r in f['done']:
        if (n := named(r['words'])) and not add('yesterday', f'One was {n}.'):
            break
    for r in f['stuck']:
        if (n := named(r['words'])) and not add('issues', f'Stuck is {n}.'):
            break
    for w in f['made'] or ():
        if (n := named(w)) and not add('yesterday', f'One change was {n}.'):
            break
    for r in f['before']:
        day = datetime.date.fromisoformat(r['day'])
        if (n := named(r['words'])) and not add('yesterday', f"Before that, on {day.strftime('%B')} {day.day}, {n} went green."):
            break
    if f['ran']:
        add('today', f"{len(f['ran'])} {'agent has' if len(f['ran']) == 1 else 'agents have'} run today without red, among them {listed(f['ran'][:5])}.")
    for state in ('green', 'shipped', 'asked', 'building', 'waiting_takein', 'stuck_today', 'removed'):
        if f['counts'].get(state):
            add('today', f"In all, {f['counts'][state]} {'request is' if f['counts'][state] == 1 else 'requests are'} {state.replace('_', ' ')}.")
    item = lambda r: f"{r['id']} · {(r['words'] or '')[:90]}"  # noqa: E731
    return {'written': now.strftime('%Y-%m-%d %H:%M'), **said(), 'seconds': seconds(said()),
            'detail': {'yesterday': [item(r) for r in f['done']], 'today': [item(r) for r in f['open']],
                       'blocked': [*(f'{n} is red' for n in f['red']), *(item(r) for r in f['stuck'])]}}


def voiced(text):
    """THE VOICE, MEASURED: the voice service asked to say the line in christensen's voice, an audio answer within 60 s, else red"""
    conf = office.fact('voice') or {}
    ask = conf['service'] + '/wav?' + urllib.parse.urlencode({'voice': conf['voice'], 'text': text[:600]})
    end = time.monotonic() + 60
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(ask, timeout=max(1, min(20, end - time.monotonic()))) as got:
                if got.status == 200 and got.headers.get('Content-Type', '').startswith('audio'):
                    return conf['voice']
                if got.status != 202:
                    raise ValueError(f"the voice answered {got.status}")
        except urllib.error.HTTPError as no:
            raise ValueError(f"the voice {conf['voice']} at {conf['service']} answered {no.code}") from no
        except OSError as no:
            raise ValueError(f"the voice {conf['voice']} at {conf['service']} is not running ({no})") from no
        time.sleep(1)
    raise ValueError(f"the voice {conf['voice']} made no sound in 60 s")


def run(given):
    s = standup(given)
    low, high = office.fact('spoken_seconds')
    missing = [k for k in ('yesterday', 'today', 'issues') if not (s.get(k) or '').strip()]
    if missing:
        return office.done(f'RED · the standup is not three lines: no {listed(missing)} line', 'RED')
    if not low <= s['seconds'] <= high:
        return office.done(f"RED · the standup is {s['seconds']} s aloud, outside {low} to {high} s", 'RED', s)
    try:
        s['voice'] = voiced(s['hello'])
    except ValueError as no:
        return office.done(f'RED · {no}', 'RED', s)
    return office.done(f"GREEN · the standup, {s['seconds']} s aloud, read by {s['voice']}", 'GREEN', s)


def canvas(given):
    """SM2's THE STANDUP panel (its page's note and words parts): not written, or the lines its last RUN wrote"""
    own = office.own_job(given)
    s = office.data_of(own)
    e = office.e
    head = '<div class="replica-group" aria-label="group">TOP</div><div class="replica-canvas"><div class="replica-canvas-content">'
    if not s.get('hello'):
        text = (f"Not written: its last run {own.get('data_job_today_said') or 'FAILED'}." if office.light_of(own) == 'RED'
                else 'Not written yet: its first run writes it (RUN AGENT).')
        body = f'<div class="clarity replica-standup"><div class="title">The standup</div><div class="notes">{e(text)}</div></div>'
    else:
        lines = ''.join(f'<div class="{cls}" data-say="{e(s.get(k))}"{f" data-part={chr(34)}{tag}{chr(34)}" if tag else ""}>{e(s.get(k))}</div>'
                        for cls, k, tag in (('body', 'hello', ''), ('subtitle', 'yesterday', 'yesterday'), ('subtitle', 'today', 'today'),
                                            ('subtitle', 'issues', 'blockers'), ('body', 'bye', '')))
        body = (f'<div class="clarity replica-standup"><div class="title">The standup</div>'
                f'<div class="annotation">Written at {e(s.get("written"))}, by its run</div><div class="replica-spoken">{lines}</div></div>')
    return look.view(head + body + '</div></div>', str((given.get('page') or {}).get('path') or ''))


if __name__ == '__main__':
    office.main(canvas, run)
