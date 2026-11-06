"""HOT FIX WALK, Scrum Master 3's DAY step (SM2 agent019): the hot fix utility once for the day's committed requests: both apps built
from the tree and walked, a red row fixed and walked again until green, by its own design (it commits its own fixes, and whatever it
finds uncommitted). So it runs only on a clean tree, nothing in hand, every committed request's commit on the tree, and nothing on the
tree past them but THE DAY's merges of main and the utility's own fixes. READY for every app turns each request ready for tonight's
take-in. DRY (its fact): it does every read and says the walk it would run."""
import os
import re
import shlex
import subprocess

import office
from day import F, asked_again, branch, canvas_of, day_off, git, head, last, off, out, red, said, set_state, tree_red, wait_step, writer_busy


def unreviewed(built):
    """what the tree holds that no review read, from the oldest committed request's commit: (why, step), or None"""
    tree, shas = F('tree'), [str(r.get('commits') or '').strip() for r in built]
    for r, s in zip(built, shas):
        if not s:
            return f"{r['id']} is committed with no commit recorded", f"git -C {tree} log --format='%H %s' --grep='^{r['id']}:' names it; record it in its commits, then RUN here"
        if git('merge-base', '--is-ancestor', s, 'HEAD').returncode != 0:
            return f"{r['id']}'s commit {s[:12]} is not on the tree", f"{asked_again(r['id'])}, then RUN here"
    oldest = max(shas, key=lambda s: int(git('rev-list', '--count', f'{s}..HEAD').stdout.strip() or 0))
    full = {git('rev-parse', s).stdout.strip() for s in shas}
    after = [tuple(ln.split('\0', 3)) for ln in out('log', '--first-parent', '--format=%H%x00%ce%x00%P%x00%s', f'{oldest}..HEAD').splitlines() if ln.count('\0') >= 3]
    odd = [m for m in after if m[0] not in full and not (m[1] == F('day_email') and len(m[2].split()) > 1) and not m[3].startswith(F('utility_fix'))]
    if odd:
        return (f"the tree holds {len(odd)} commit(s) no review read: {', '.join(m[0][:12] for m in odd[:3])}",
                ' && '.join(f"git -C {tree} revert{' -m 1' if len(m[2].split()) > 1 else ''} --no-edit {m[0][:12]}" for m in odd) + ', then RUN here')
    return None


def run(given):
    if day_off():
        return off()
    checks = []
    hand = office.requests(F('in_hand'))
    checks.append(('A request in hand', f"{hand[0]['id']} is {hand[0]['state']}" if hand else 'none'))
    if hand:
        return red(f"{hand[0]['id']} is {hand[0]['state']}: the walk never runs with a request in hand (the utility commits whatever it finds)", 'RUN Building now, then the day goes on', checks)
    busy = writer_busy()
    checks.append(('The hot fix utility and the writer mark', busy or 'free'))
    if busy:
        return red(busy, wait_step(busy), checks)
    bad = tree_red()
    checks.append(('The hot fix tree', bad[0] if bad else f"{F('tree')} on {branch()}, clean, HEAD {head()[:12]}"))
    if bad:
        return red(*bad, checks)
    built = office.requests([F('committed')])
    checks.append(('Committed, waiting for the walk', ', '.join(f"{r['id']} {str(r.get('commits') or 'NONE')[:12]}" for r in built) or 'none'))
    if not built:
        return said('nothing committed to walk', checks)
    bad = unreviewed(built)
    checks.append(('Nothing on the tree no review read', bad[0] if bad else 'yes'))
    if bad:
        return red(*bad, checks)
    command = [os.path.expanduser(a) for a in F('utility')] + F('targets')
    ids = [r['id'] for r in built]
    if F('dry'):
        return said(f"would walk {len(built)} request(s) ({', '.join(ids)}) on {branch()} at {head()[:12]}: {' and '.join(F('targets'))}", checks,
                    [f"cd {F('utility_cwd')} && {' '.join(shlex.quote(a) for a in command)}  (at most {F('utility_seconds')} s; {F('walk_minutes')})"])
    try:
        walk = subprocess.run(command, cwd=F('utility_cwd'), capture_output=True, text=True, timeout=F('utility_seconds'), env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        code, text = walk.returncode, (walk.stdout or '') + (walk.stderr or '')
    except (subprocess.TimeoutExpired, OSError) as fault:
        code, text = 1, f'{type(fault).__name__}: {fault}'
    targets = {m.group(1).lower(): (m.group(2).strip(), m.group(3).strip()[:200]) for m in re.finditer(r'\b(IPHONE|MACOS) · ([A-Z][A-Z ]*?) · (.*)$', text, re.M)}
    report = (re.findall(r'THE REPORT · (\S.*?)\s*$', text, re.M) or [''])[-1]
    named = ', '.join(f'{t} {v}' for t, (v, _w) in targets.items()) or 'no target said'
    if code != 0 or any(targets.get(t, ('',))[0] != 'READY' for t in F('targets')):
        bad = '; '.join(f'{t} {v}: {w}' for t, (v, w) in targets.items() if v != 'READY') or last(text)[:200] or f'it ended {code}'
        return red(f'not READY: {bad}', (f'read its report ({report}) and clear what it names' if report else "read the utility's last lines") + f", then RUN here; the commits stay on the tree", checks)
    moved_ = [rid for rid in ids if not set_state(rid, F('ready'), 'built, proven, reviewed, committed and walked READY by THE DAY', F('committed'), done_at=office.stamp())]
    if moved_:
        return red(f"walked READY, but a press moved {', '.join(moved_)} during the walk: not made ready", 'see their state, then RUN Cleanup', checks)
    return said(f"walked READY: {named} on {branch()} at {head()[:12]} · {len(ids)} request(s): {', '.join(ids)}", checks, report=report)


canvas = canvas_of('Hot fix walk')


if __name__ == '__main__':
    office.main(canvas, run)
