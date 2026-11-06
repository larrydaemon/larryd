"""THE DAY KIT: the one program Scrum Master 3's DAY agents stand on beside office.py (packed when agent.json "libs" names "day"): the
hot fix tree read and written as THE DAY does (git with no optional lock, its status, its writer mark, a request's side file in the
office's own data, its base, its proof, its change put back), the DAY switch read, a step's answer (red, said, off) and its block
(canvas_of: SM2's one live line, drawn through look); and the requests' own presses (REMOVE, UPDATE, APPROVE, the swear words out)
and SM2's request table rows, shared by The requests and Backlog. Every
fact it reads is the calling agent's own (office.fact)."""
import datetime
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import zoneinfo

import look
import office

F = office.fact


class NotMeasured(RuntimeError):
    """a read of the tree that failed: not measured, never clean"""


def git(*args):
    """git in the hot fix tree, every path as typed, no optional lock taken (a read never writes the tree's index)"""
    return subprocess.run(['git', '--literal-pathspecs', *args], cwd=F('tree'), capture_output=True, text=True, errors='surrogateescape',
                          timeout=F('git_seconds'), env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})


def last(text):
    return next((ln.strip() for ln in reversed(str(text or '').splitlines()) if ln.strip()), '')


def out(*args):
    got = git(*args)
    if got.returncode != 0:
        raise NotMeasured(f'not measured: git {args[0]} failed ({last(got.stderr)[:120]})')
    return got.stdout


def cache(p):
    return '__pycache__' in p.split('/') or p.endswith(('.pyc', '.DS_Store'))


def status(*more):
    parts, items, i = out('status', '--porcelain=v1', '-z', '--untracked-files=all', *more).split('\0'), [], 0
    while i < len(parts):
        if len(parts[i]) > 3:
            items.append((parts[i][:2], parts[i][3:]))
            i += parts[i][0] in 'RC'
        i += 1
    return items


def changed():
    return [p for code, p in status() if code != '!!' and not cache(p)]


def day_state():
    """THE DAY SWITCH (the Day card's one row of the office's database): (on, its row); no row yet is on"""
    row = next((r for r in office.live_all() if r['key'] == F('day_key')), None)
    return (not row or row['state'] != F('day_off')), row


def day_off():
    return not day_state()[0]


def pid_in(path):
    try:
        raw = open(path, encoding='utf-8', errors='replace').read().split()
    except OSError:
        return None
    return int(raw[0]) if raw and raw[0].isdigit() else None


def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (TypeError, ValueError, ProcessLookupError):
        return False


def writer_busy():
    """the hot fix utility running, or another live writer holding the tree's mark: why, or ''"""
    util, other = pid_in(F('utility_lock')), pid_in(F('writer'))
    if util and alive(util):
        return f'the hot fix utility is running (pid {util}): it writes the tree now'
    if other and other != os.getpid() and alive(other):
        return f"another writer of the hot fix tree holds its mark (pid {other}, {F('writer')})"
    return ''


class Writer:
    """the tree's one writer mark, held while a real step writes the tree (the hot fix utility honours it)"""
    def __enter__(self):
        os.makedirs(os.path.dirname(F('writer')), exist_ok=True)
        with open(F('writer'), 'w', encoding='utf-8') as fh:
            fh.write(str(os.getpid()))
        return self

    def __exit__(self, *exc):
        if pid_in(F('writer')) == os.getpid():
            os.remove(F('writer'))


def wait_step(busy):
    pid = re.search(r'pid (\d+)', busy)
    return (f'ps -p {pid.group(1)} -o command= names that run: let it end' if pid else 'let that run end') + ', never delete a live mark, then RUN here'


def rebuilt():
    return f"git -C {F('repo')} worktree prune && git -C {F('repo')} worktree add {F('tree')} {F('branch')}"


def tree_red(clean=True):
    """the hot fix tree there, its HEAD a commit, on its branch, and (clean) holding nothing uncommitted: (why, his step), or None"""
    tree = F('tree')
    if not os.path.lexists(tree):
        return f'there is no hot fix tree at {tree}', f'{rebuilt()}, then RUN here'
    if not os.path.isdir(tree) or git('rev-parse', '--verify', '-q', 'HEAD^{commit}').returncode != 0:
        return f'{tree} is there but its HEAD is no commit', f'mv {tree} {tree}.broken-$(date +%Y%m%d%H%M%S) && {rebuilt()} (moved aside, never lost), then RUN here'
    if git('symbolic-ref', '-q', 'HEAD').returncode != 0:
        return 'the hot fix tree is on no branch (a detached HEAD)', f"git -C {tree} checkout {F('branch')}, then RUN here"
    dirty = changed() if clean else []
    if dirty:
        return f"the hot fix tree holds {len(dirty)} file(s) nobody committed: {', '.join(dirty[:4])}", f'git -C {tree} stash push -u -m day-left (kept in the stash, never lost), then RUN here'
    return None


def head():
    return out('rev-parse', 'HEAD').strip()


def branch():
    return git('symbolic-ref', '-q', '--short', 'HEAD').stdout.strip()


def side_path(rid):
    return os.path.join(office.DATA_ROOT, office.office(), F('side_dir'), f'{rid}.json')


def side(r, **more):
    """a request's side file (the office's own data file, outside the tree): its pick's base, its built files, its proof; more: written into it"""
    try:
        with open(side_path(r['id']), encoding='utf-8') as fh:
            held = json.load(fh)
    except (OSError, ValueError):
        held = {}
    held = held if isinstance(held, dict) else {}
    if more:
        held.update(more)
        os.makedirs(os.path.dirname(side_path(r['id'])), exist_ok=True)
        with open(side_path(r['id']) + '.tmp', 'w', encoding='utf-8') as fh:
            json.dump(held, fh, sort_keys=True)
        os.replace(side_path(r['id']) + '.tmp', side_path(r['id']))
    return held


def tests_of(r):
    return os.path.join(F('tests'), r['id'])


def sha(folder):
    """its tests' sha256: every file of the folder but its own .day_ marks and caches"""
    h = hashlib.sha256()
    for root, dirs, files in sorted(os.walk(folder)):
        dirs[:] = sorted(d for d in dirs if d != '__pycache__')
        for f in sorted(files):
            if f.endswith('.pyc') or (root == folder and f.startswith('.day_')):
                continue
            p = os.path.join(root, f)
            h.update(os.path.relpath(p, folder).encode() + b'\0')
            with open(p, 'rb') as fh:
                h.update(fh.read())
    return h.hexdigest()


def moved(base):
    """the commits past a request's base: [(sha, committer email, parents, subject)]; a base the tree does not hold is one"""
    if not base or git('cat-file', '-e', f'{base}^{{commit}}').returncode != 0:
        return [(str(base or '?'), '', '', 'its base is not a commit of this tree')]
    return [tuple(ln.split('\0', 3)) for ln in out('log', '--format=%H%x00%ce%x00%P%x00%s', f'{base}..HEAD').splitlines() if ln.count('\0') >= 3]


def proof(base):
    """the change's own fingerprint: its diff from its base and its new files' bytes"""
    h = hashlib.sha256(git('diff', '--binary', base, '--').stdout.encode('utf-8', 'surrogateescape'))
    for f in sorted(p for p in git('ls-files', '--others', '--exclude-standard', '-z').stdout.split('\0') if p and not cache(p)):
        h.update(b'\0' + f.encode('utf-8', 'surrogateescape') + b'\0')
        try:
            h.update(open(os.path.join(F('tree'), f), 'rb').read())
        except OSError:
            h.update(b'<unreadable>')
    return h.hexdigest()


def asked_again(rid):
    return f"git -C {F('tree')} stash push -u -m day-{rid} && sqlite3 {office.DATA_ROOT}/{office.office()}/{office.office()}.db \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{rid}'\""


def since_pick(r, info, built):
    """what a step on a picked request stands on: its base recorded on a clean tree, HEAD at that base, the tree's change its own files
    (built) or none: (why, his step), or None"""
    base = info.get('base')
    if not base or not info.get('clean'):
        return f"{r['id']}: its pick recorded no base", f"{asked_again(r['id'])}, then RUN Pick"
    past = moved(base)
    if past:
        return (f"{r['id']}: the tree moved past its pick ({', '.join(m[0][:12] for m in past[:3])}): never built on",
                f"git -C {F('tree')} revert --no-edit {base[:12]}..HEAD, then {asked_again(r['id'])}, then RUN Pick")
    if head() != base:
        return f"{r['id']}: HEAD is not its base {base[:12]}", f"{asked_again(r['id'])}, then RUN Pick"
    mine = set(info.get('files') or ()) if built else set()
    if built and not mine:
        return f"{r['id']}: its built files were never recorded", f"{asked_again(r['id'])}, then RUN Pick"
    dirty = set(changed())
    if dirty != mine:
        odd = sorted(dirty ^ mine)
        return (f"{r['id']}: the tree's change is not its own ({len(odd)} file(s): {', '.join(odd[:4])})",
                f"{asked_again(r['id'])} (they may be his own hand edits: the stash keeps them), then RUN Pick")
    return None


def put_back(base, files):
    """a red before the commit leaves nothing of it behind: its own files alone back to its base, a new one removed. -> the ones that would not go back"""
    files = sorted(set(files))
    olds = [f for f in files if out('ls-tree', '-z', base, '--', f)]
    if olds:
        git('checkout', base, '--', *olds)
    for f in files:
        if f in olds:
            continue
        git('rm', '--cached', '-q', '--ignore-unmatch', '--', f)
        p = os.path.join(F('tree'), f)
        if os.path.lexists(p) and not os.path.isdir(p):
            os.remove(p)
    return sorted(set(changed()) & set(files))


def set_state(rid, state, why, when, **more):
    """a request's state written only while it is still in the state read (a press between the read and the write wins)"""
    cols = {'state': state, 'state_at': office.now().isoformat(timespec='seconds'), 'why': why, **more}
    con = office.db()
    with con:
        n = con.execute(f"UPDATE requests SET {', '.join(f'{k} = ?' for k in cols)} WHERE id = ? AND state = ?", (*cols.values(), rid, when)).rowcount
    con.close()
    return n == 1


def set_aside(r, base, files, why, step):
    """a red of Build, Prove or Review on the real path: its own change put back, it stuck today"""
    kept = put_back(base, files)
    set_state(r['id'], F('stuck'), why[:300], r['state'])
    return red(f"{r['id']}: {why}" + (f"; {len(kept)} file(s) would not go back: {', '.join(kept[:4])}" if kept else ''), step)


def the_one(state):
    """the one request at a stage (one at a time on the tree): (request, None), (None, None) when none, (None, a red)"""
    rows = office.requests([state])
    if len(rows) > 1:
        return None, (f"{len(rows)} requests are {state} at once: {', '.join(r['id'] for r in rows[:4])}",
                      f"sqlite3 {office.DATA_ROOT}/{office.office()}/{office.office()}.db \"UPDATE requests SET state='asked' WHERE state='{state}' AND id<>'{rows[0]['id']}'\", then RUN here")
    return (rows[0] if rows else None), None


def red(why, step, checks=()):
    return office.done(f'RED · {why} · YOUR 3 MIN: {step}', 'RED', {'checks': [list(c) for c in checks], 'why': why, 'step': step})


def said(line, checks=(), would=(), **more):
    """a green or dry answer: its line, what it checked, what it would run, and the next step named"""
    nxt = more.pop('next', F('next'))
    dry = bool(F('dry')) and bool(would)
    text = ('DRY · ' if dry else 'GREEN · ') + line + (f' · next: {nxt}' if nxt else '')
    return office.done(text, 'GREEN', {'checks': [list(c) for c in checks], 'would': list(would), 'dry': dry, 'next': nxt or '', **more})


def off():
    return office.done('GREEN · DAY is off: nothing read, nothing changed', 'GREEN', {'day': 'off'})


def clock(seconds):
    """SM2's live counter, said at CALL time: 30 H 58 MIN 26 S"""
    h, m, s = seconds // 3600, seconds % 3600 // 60, seconds % 60
    return f'{h} H {m} MIN {s} S' if h else f'{m} MIN {s} S' if m else f'{s} S'


def gone(at):
    """seconds since a stamp (a job's naive local time, or a request's own zoned one), None when it does not read"""
    try:
        got = datetime.datetime.fromisoformat(str(at or '').strip())
    except ValueError:
        return None
    got = got.astimezone() if got.tzinfo else got
    secs = int((datetime.datetime.now(got.tzinfo) - got).total_seconds())
    return secs if secs >= 0 else None


def live_of(job):
    """SM2's three words for a job (page.py live_line): RUNNING (green) while a run is open, NOT RUNNING (red) when its last run failed,
    else IDLE; its time since its last run, '' when never run -> (state, word, class, since)"""
    run, lit = str(job.get('data_job_run_state') or '').upper(), office.light_of(job)
    secs = gone(job.get('data_job_last_run_at'))
    since = clock(secs) if secs is not None else ''
    if run in ('RUNNING', 'QUEUED'):
        return 'RUNNING', 'RUNNING', 'hdr-status--success', since
    if lit == 'RED' or run in ('FAILED', 'REFUSED'):
        return 'RED', 'NOT RUNNING', 'hdr-status--error', since
    return 'GREEN' if lit else 'IDLE', 'IDLE', 'scrum-idle', since


def live_block(name, job, group):
    """SM2's one line of a live agent (page.py live_block): its name, its live line beside it, its group word at the right"""
    e, key = office.e, re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    state, word, cls, since = live_of(job)
    tick = f'<span class="scrum-since {cls}">{e(since)}</span>' if since else ''
    return (f'<div class="replica-live-block" data-live-block="{key}"><div class="title scaf-law-title">{e(name)}</div>'
            f'<div class="replica-live-line" data-live-key="{key}" data-live-state="{state}"><div class="subtitle"><span class="{cls}">{word}</span>{tick}</div></div>'
            f'<span class="replica-live-group" aria-label="group">{e(group)}</span></div>')


def path_of(given):
    return (given.get('page') or {}).get('path') or ''


LIVE_CSS = ''   # SM2's counter spacing is look's own (look.BASE)


def canvas_of(title):
    """a step's block as SM2 drew it: one line (live_block)"""
    def canvas(given):
        return look.view(live_block(title, office.own_job(given), office.me().get('group') or ''), path_of(given), LIVE_CSS)
    return canvas


# ── THE REQUESTS' OWN PRESSES, The requests and Backlog alike ─────────────────────────────────────────────────────────

RID = re.compile(r'R-\d{4,}')


def zone():
    return zoneinfo.ZoneInfo(F('zone'))


def now():
    return datetime.datetime.now(zone())


def pressed_as(given, prefix):
    """THE MEMBER'S PRESS, PREFIX AWARE (every CALL on the page sees the same search): office.press sends '<do> <its value>' under
    <prefix>_do, and a text box under <prefix>_words. -> (do, value, words)"""
    do, _, value = office.asked(given, f'{prefix}_do').strip().partition(' ')
    return do, value.strip(), office.asked(given, f'{prefix}_words')


def clean(text):
    """only the swear words change: a removed one leaves a mark, and only the space beside a mark is tidied"""
    swear = re.compile(F('swear'), re.I)
    if not text or not swear.search(text):
        return text
    for pattern, word in F('plain'):
        text = re.sub(pattern, lambda m, w=word: (w.upper() if w and m.group(0).isupper() and len(m.group(0)) > 1 else w) if w else '\x00', text, flags=re.I)
    text = swear.sub('\x00', text)
    text = re.sub(r"[ \t]*\x00[ \t]*(?=[,.;:!?\"')\]]|$)", '', text, flags=re.M)
    text = re.sub(r"(^|(?<=[\"'(\[]))[ \t]*\x00[ \t]*", '', text, flags=re.M)
    return re.sub(r"[ \t]*\x00[ \t]*", ' ', text)


def moment(text):
    try:
        got = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return (got if got.tzinfo else got.replace(tzinfo=zone())).astimezone(zone())


def status_of(state):
    return next((word for word, states in F('status') if state in states), str(state or '').upper().replace('_', ' '))


def env_keys(raw):
    """the boxes checked: a JSON list (a stored request) or the page's words; none kept is every box but the native ones"""
    keys = [k for k, _p, _s in F('environments')]
    if raw is None or raw == '':
        return [k for k in keys if k not in F('off_by_default')]
    got = raw if isinstance(raw, list) else str(raw).split()
    return [k for k in keys if k in got]


def env_line(keys):
    parts = []
    for place in dict.fromkeys(p for _k, p, _s in F('environments')):
        sides = [s for k, p, s in F('environments') if p == place and k in keys]
        if sides:
            parts.append(f"{place} {' · '.join(sides)}")
    return ' · '.join(parts) or 'none'


def stored_env(r):
    try:
        got = json.loads(r.get('environment') or 'null')
    except (TypeError, ValueError):
        got = None
    return env_keys(got if isinstance(got, list) else None)


def test_url(words):
    found = [u.rstrip('.,;)') for u in re.findall(r'https?://[^\s<>"\']+', str(words or ''))]
    found = [u for u in found if not re.match(F('production_a'), u)]
    return found[-1] if found else ''


def one(con, rid):
    got = con.execute('SELECT id, words, state, state_at FROM requests WHERE id = ?', (rid,)).fetchone()
    return dict(got) if got else None


def remove(rid):
    if not RID.fullmatch(rid):
        return f'REMOVE refused · {rid or "nothing"} is not a request id'
    con, at = office.db(), now()
    with con:
        r = one(con, rid)
        if not r:
            return f'REMOVE refused · {rid}: no such request'
        if r['state'] in F('closed') + [F('removed')]:
            return f"REMOVE refused · {rid} is {r['state'].replace('_', ' ')} already: nothing to remove"
        why = (f"REMOVED BY THE OWNER {F('by_his_page')} {at:%Y-%m-%d %H:%M}: no longer wanted; it was {r['state'].replace('_', ' ')}"
               f" since {str(r['state_at'] or '')[:16].replace('T', ' ')}; its words, commits and history stay")
        con.execute('UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state = ?',
                    (F('removed'), at.isoformat(timespec='seconds'), why[:500], rid, r['state']))
    con.close()
    return f'REMOVED · {rid} · marked removed by you, never deleted'


def update(rid, words):
    words = clean(str(words or '').replace('\r\n', '\n')).strip()
    if not RID.fullmatch(rid):
        return f'UPDATE refused · {rid or "nothing"} is not a request id'
    if not words:
        return f'UPDATE refused · {rid}: an update needs your words'
    con, at = office.db(), now()
    with con:
        r = one(con, rid)
        if not r:
            return f'UPDATE refused · {rid}: no such request'
        if r['state'] == F('removed'):
            return f'UPDATE refused · {rid} was removed by you: removed is final, add it again as a new request'
        if str(r['words'] or '').rstrip().endswith(f': {words}'):
            return f'UPDATE kept already · {rid} · these words are under it'
        con.execute('UPDATE requests SET words = words || ? WHERE id = ?', (f'\n\nUPDATE {at:%Y-%m-%d %H:%M}: {words}', rid))
        if r['state'] in F('in_hand'):
            return f"UPDATED · {rid} · your words kept under its words; it stays {r['state']}: the DAY holds its change on the tree now"
        con.execute('UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state = ?',
                    (F('asked'), at.isoformat(timespec='seconds'), f"UPDATED BY THE OWNER {F('by_his_page')} {at:%Y-%m-%d %H:%M}: back in the backlog, built again with his update by the next DAY run", rid, r['state']))
    con.close()
    return f'UPDATED · {rid} · your words kept under its words; back in the backlog for the next DAY run'


def approve(rid):
    if not RID.fullmatch(rid):
        return f'APPROVE refused · {rid or "nothing"} is not a request id'
    con, at = office.db(), now()
    with con:
        r = one(con, rid)
        if not r:
            return f'APPROVE refused · {rid}: no such request'
        if r['state'] != F('ready'):
            return f"APPROVE refused · {rid} is {str(r['state']).replace('_', ' ')}, not in VERIFY: nothing to approve"
        stamp = at.isoformat(timespec='seconds')
        con.execute('UPDATE requests SET state = ?, state_at = ?, why = ?, done_at = COALESCE(done_at, ?) WHERE id = ? AND state = ?',
                    (F('approved'), stamp, f"APPROVED BY THE OWNER {F('by_his_page')} {at:%Y-%m-%d %H:%M}: done", stamp, rid, F('ready')))
    con.close()
    return f'APPROVED · {rid} · done'


def form(prefix, do, words, cls, button='pfb pfb--small', box=''):
    """SM2's press as a GET to the page: '<do>' under <prefix>_do, a text box (box: its class and placeholder) under <prefix>_words;
    button: its classes, an embedded widget's (pfb pfb--<style>, its look embedded.css's; the owner 2026-11-04: "make sure all the agents
    inject the embedded buttons too")"""
    e = office.e
    field = f'<input type="text" name="{prefix}_words" class="pin-box {box[0]}" placeholder="{e(box[1])}">' if box else ''
    return (f'<form class="{cls}"><input type="hidden" name="{prefix}_do" value="{e(do)}">{field}'
            f'<button class="{button}" type="submit">{e(words)}</button></form>')


def request_row(r, prefix, today=False):
    """ONE REQUEST AS SM2'S TABLE ROW (Request | His words | Status now): its id and when, where the work goes and REMOVE; his words
    and UPDATE; its status, its why, its time in that status, APPROVE and TEST IT in VERIFY"""
    e, rid = office.e, r['id']
    at, word = moment(r['asked_at']), status_of(r['state'])
    secs = gone(r['asked_at'] if word == 'WAITING' else r['state_at'])
    lit = {'VERIFY': 'scrum-verify', 'WAITING': 'scrum-idle'}.get(word, 'hdr-status--success')
    when = at.strftime('%H:%M' if today else '%Y-%m-%d %H:%M') if at else ''
    status = f'<span class="{lit}">{e(word)}</span> ' + (f'<span class="annotation">{e(" ".join(str(r["why"]).split()))}</span>' if r.get('why') else '')
    if secs is not None:
        status += f'<div class="annotation scrum-builder">{e(word)} TIME: <span class="scrum-building-clock hdr-status--success"><span class="scrum-since">{clock(secs)}</span></span></div>'
    if word == 'VERIFY':
        url = test_url(r['words'])
        status += (f'<div class="scrum-verdict">{form(prefix, f"approve {rid}", "APPROVE", "scrum-approve scrum-verdict-form", "pfb pfb--small scrum-approve-btn")}</div>'
                   f'<div class="annotation scrum-test-link scrum-test-box">TEST IT: {e(url) if url else "no page named in the request: put its address in an UPDATE"}</div>')
    return (f'<tr data-row="{e(rid)}"><td data-cell="0">{e(rid)} · {e(when)}<div class="annotation scrum-env-line">{e(env_line(stored_env(r)))}</div>'
            f'{form(prefix, f"remove {rid}", "REMOVE", "scrum-remove", "pfb pfb--small scrum-remove-btn")}</td>'
            f'<td data-cell="1"><div class="scrum-words-text">{e(str(r["words"] or "").strip())}</div>'
            f'{form(prefix, f"update {rid}", "UPDATE", "scrum-update", "pfb pfb--small scrum-update-btn", ("scrum-update-words", "update: what you looked for and did not see"))}</td>'
            f'<td data-cell="2">{status}</td></tr>')


def request_table(rows, prefix, table_id, empty, today=False):
    """SM2's scrum-term table of requests, its one empty line when none"""
    body = ''.join(request_row(r, prefix, today) for r in rows) or f'<tr><td colspan="3" class="scrum-idle">{office.e(empty)}</td></tr>'
    return (f'<table class="scrum-term" id="{table_id}"><thead><tr><th class="scrum-why-row">Request</th><th>His words</th>'
            f'<th class="scrum-why-status">Status now</th></tr></thead><tbody>{body}</tbody></table>')


# a text box stands where SM2 had a textarea (the runtime refuses one): its sheet's own size, the words at its top; a row of one
# cell across the table (SM2's colspan, which a view's table cannot carry) drawn under it at the table's width
RQ_CSS = """
.id-scrum .t-td .scrum-update { display: flex; align-items: flex-end; gap: 8px; }
.id-scrum .scrum-update .scrum-update-words { flex: 1 1 auto; min-width: 0; box-sizing: border-box; height: 3.4em; padding: 6px 8px 1.7em; font: inherit; color: inherit; background: transparent; border: 1px solid currentColor; }
.id-scrum .scrum-update .scrum-update-words::placeholder { color: inherit; opacity: 1; }
.id-scrum .scrum-term .t-tbody:has(> .t-tr > .t-td[data-colspan]) { display: table-caption; caption-side: bottom; }
.id-scrum .scrum-term .t-tbody:has(> .t-tr > .t-td[data-colspan]) > .t-tr, .id-scrum .scrum-term .t-td[data-colspan] { display: block; }
.id-scrum .scrum-term .t-tbody .t-tr .t-td[data-colspan] { width: auto; border-top: 0; }
"""
