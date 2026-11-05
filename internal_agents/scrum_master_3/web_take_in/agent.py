"""WEB TAKE IN, the NIGHT's first step (SM2 agent022): each request DAY committed (approved, waiting_takein in the office's database)
put on main by its own commit (cherry-pick -x), one each, in build order; a commit already on main is only marked taken_in. Red: main
not on its branch or holding uncommitted tracked files, a commit that is not there or will not apply (taken back, main untouched), or one
that touches a path under the owner's root lock (his written GO). Dry: it reads all of that and names each pick it would make."""
import os
import stat
import subprocess

import night
import office
from night import F, tail


LOCK_FLAGS = stat.SF_IMMUTABLE | stat.UF_IMMUTABLE | stat.SF_APPEND | stat.UF_APPEND   # the owner's root lock (chflags)


def git(*args):
    return subprocess.run(['git', '-C', F('workspace'), *args], capture_output=True, text=True, timeout=120)


def locked(paths):
    found = []
    for p in paths:
        full = os.path.join(F('workspace'), p)
        look = [full] if os.path.lexists(full) else []
        above = os.path.dirname(full)
        while above and not os.path.lexists(above) and above != os.path.dirname(above):
            above = os.path.dirname(above)
        for one in look + [above]:
            try:
                if getattr(os.lstat(one), 'st_flags', 0) & LOCK_FLAGS:
                    found.append(p)
                    break
            except OSError:
                found.append(p)
                break
    return found


def taken(rid, sha):
    con = office.db()
    with con:
        con.execute(f"UPDATE requests SET state = ?, state_at = ?, why = ? WHERE id = ? AND state IN ({','.join('?' * len(F('waiting')))})",
                    (F('taken'), office.now().isoformat(timespec='seconds'), f'taken into main by NIGHT: {sha[:12]}', rid, *F('waiting')))
    con.close()


def own(given, dry):
    rows = office.requests(F('waiting'))
    if not rows:
        return {'lines': ['web · take in · nothing committed by DAY to take in']}
    ws, db = F('workspace'), os.path.join(office.data_dir(), f'{office.office()}.db')
    head = git('symbolic-ref', '-q', '--short', 'HEAD').stdout.strip()
    if head != F('branch'):
        return {'why': f"the workspace is on {head or 'no branch'}, not {F('branch')}", 'step': f"git -C {ws} checkout {F('branch')}, then RUN here"}
    dirty = [x for x in git('status', '--porcelain', '--untracked-files=no').stdout.splitlines() if x.strip()]
    if dirty:
        return {'why': f"{F('branch')} holds {len(dirty)} uncommitted file(s): {', '.join(x[3:] for x in dirty[:4])}",
                'step': f'the session that owns them commits them (git -C {ws} status), then RUN here'}
    lines, would = [], []
    for r in rows:
        sha = str(r.get('commits') or '').split()[0] if r.get('commits') else ''
        if not sha:
            lines.append(f"web · take in · {r['id']} · no commit recorded: not built by DAY, left as it is")
            continue
        if git('cat-file', '-e', f'{sha}^{{commit}}').returncode != 0:
            return {'lines': lines, 'why': f"{r['id']} has no commit to take in ({sha})",
                    'step': f"sqlite3 {db} \"SELECT id, commits FROM requests WHERE id='{r['id']}'\" names it; set it back to asked, then RUN here"}
        if git('merge-base', '--is-ancestor', sha, 'HEAD').returncode == 0:
            if not dry:
                taken(r['id'], sha)
            (would if dry else lines).append(f"web · take in · {r['id']} · {sha[:12]} already on {F('branch')}: marked {F('taken')}")
            continue
        bad = locked([p for p in git('diff-tree', '--no-commit-id', '--name-only', '-r', sha).stdout.splitlines() if p])
        if bad:
            return {'lines': lines, 'why': f"{r['id']} changes {len(bad)} path(s) under your root lock: {', '.join(bad[:4])}",
                    'step': f"your written GO to unlock {', '.join(bad[:2])} for {r['id']}, then RUN here"}
        pick = ['-c', 'user.name=night', '-c', 'user.email=night@localhost', 'cherry-pick', '-x', sha]
        if dry:
            would.append(f"git -C {ws} {' '.join(pick)}  ({r['id']}, then marked {F('taken')})")
            continue
        got = git(*pick)
        if got.returncode != 0:
            git('cherry-pick', '--abort')
            return {'lines': lines, 'why': f"{r['id']}'s commit {sha[:12]} does not apply on {F('branch')}: {tail(got.stdout + got.stderr, 200)} (taken back, untouched)",
                    'step': f"set {r['id']} back to asked (sqlite3 {db} \"UPDATE requests SET state='asked', tests_sha=NULL WHERE id='{r['id']}'\") so DAY builds it on today's main, then RUN here"}
        new = git('rev-parse', 'HEAD').stdout.strip()
        taken(r['id'], new)
        lines.append(f"web · take in · {r['id']} · {sha[:12]} on {F('branch')} as {new[:12]}")
    return {'lines': lines + [f'web · take in · {len(rows)} request(s) DAY committed'], 'would': would}


if __name__ == '__main__':
    night.main(own)
