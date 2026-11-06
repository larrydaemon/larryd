"""BUILDING NOW, Scrum Master 3's DAY step (SM2 agent012): the request in hand (one at a time on the hot fix tree), its state and the
step that is next, whether a Claude Code worker is on it this moment (its hire mark beside its tests), its tree change against what its
build recorded, then the last build against his 3 minute rule and the ones committed waiting for tonight's take-in. Red: two in hand,
a tree change no request recorded, or one that is not its own. It reads; it writes nothing (a half built change is his to put back,
by the one line its red gives)."""
import os

import office
from day import F, alive, branch, canvas_of, changed, day_off, head, off, red, said, side, since_pick, tests_of, tree_red


def worker(r):
    """whether a worker is on it this moment: its hire mark's pid alive"""
    try:
        raw = open(os.path.join(tests_of(r), F('hire_mark')), encoding='utf-8').read().split()
    except OSError:
        return None, 'no worker now'
    pid = int(raw[0]) if raw and raw[0].isdigit() else None
    if pid and alive(pid):
        return pid, f"worker alive since {raw[1][11:16] if len(raw) > 1 else '?'} (pid {pid})"
    return None, f'no worker now (pid {pid} of a stopped run is gone)' if pid else 'no worker now'


def last_build(given):
    """the last build only, from Build's own job: its length against the 3 minute rule"""
    job = office.own_job(given, F('build_key'))
    d = office.data_of(job)
    if not job:
        return 'the last build: no Build job in the records'
    if 'seconds' not in d:
        return f"the last build: no build measured yet (Build's last run: {job.get('data_job_today_said') or 'none'})"[:300]
    return f"the last build {d['seconds']} s ({d.get('request', '')}, {job.get('data_job_last_run_at', '')}): " + ('within 3 min' if d['seconds'] <= F('within') else 'OVER 3 min')


def run(given):
    if day_off():
        return off()
    hand = office.requests(F('in_hand'))
    waiting = office.requests([F('committed'), F('ready')])
    checks = [('In hand', ', '.join(f"{r['id']} {r['state']}" for r in hand) or 'nothing in building')]
    after = f"{last_build(given)} · " + (f"{len(waiting)} committed, waiting for tonight's take-in: {', '.join(r['id'] for r in waiting)}" if waiting else "nothing committed is waiting for tonight's take-in")
    if len(hand) > 1:
        keep = max(hand, key=lambda r: F('in_hand').index(r['state']))
        ids = ', '.join(f"'{r['id']}'" for r in hand if r is not keep)
        return red(f"{len(hand)} requests are in hand at once: {', '.join(r['id'] for r in hand[:4])}",
                   f"sqlite3 {office.DATA_ROOT}/{office.office()}/{office.office()}.db \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id IN ({ids})\" (keeps {keep['id']}, furthest on), then RUN here", checks)
    bad = tree_red(clean=False)
    checks.append(('The hot fix tree', bad[0] if bad else f"{F('tree')} on {branch()}, HEAD {head()[:12]}"))
    if bad:
        return red(*bad, checks)
    if not hand:
        dirty = changed()
        checks.append(('Uncommitted', f"{len(dirty)} file(s): {', '.join(dirty[:4])}" if dirty else 'none'))
        if dirty:
            return red(f"the hot fix tree holds {len(dirty)} file(s) no request recorded: {', '.join(dirty[:4])}",
                       f"git -C {F('tree')} stash push -u -m day-left (they may be his own hand edits: the stash keeps them), then RUN here", checks)
        return said(f'nothing in building · {after}', checks, next=F('nothing_next'))
    r = hand[0]
    pid, word = worker(r)
    checks.append(('Worker', word))
    info = side(r)
    if not pid:
        bad = since_pick(r, info, built=r['state'] != F('in_hand')[0])
        checks.append(('Its tree change its own', bad[0] if bad else 'yes'))
        if bad:
            return red(*bad, checks)
    nxt = F('stage').get(r['state'], '')
    return said(f"{r['id']} {r['state']} since {str(r['state_at'] or '')[:16].replace('T', ' ')}, {nxt} is next · {word} · {after}", checks, next=nxt, request=r['id'])


canvas = canvas_of('Building now')


if __name__ == '__main__':
    office.main(canvas, run)
