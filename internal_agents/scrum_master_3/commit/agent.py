"""COMMIT, Scrum Master 3's DAY step (SM2 agent018): the reviewed request's own files committed by path on the hot fix tree, its id
and his words in the message, only when nothing was committed past its base, its tests are still the frozen ones and its change is
still the one proven and read; the request is then waiting for tonight's take-in, with its commit, and Pick is next. A commit that
landed before its run ended is recorded, never made again. DRY (its fact): it does every read and says the commit it would make."""
import os
import shlex

import office
from day import F, Writer, asked_again, branch, canvas_of, changed, day_off, git, head, last, moved, off, proof, red, said, set_state, sha, side, since_pick, tests_of, the_one, tree_red, wait_step, writer_busy


def message(r):
    return (f"{r['id']}: {r['words'] or ''}\n\nBuilt by THE DAY (Scrum Master 3's DAY group): tests first {str(r.get('tests_sha') or '')[:12]}, "
            "proven, reviewed LEGIT. No Judge, no seal, no publish.")


def take_in():
    ready = office.requests([F('committed'), F('ready')])
    bare = [r['id'] for r in ready if not str(r.get('commits') or '').strip()]
    line = (f"{len(ready)} for the take-in: " + '; '.join(f"{r['id']} commits {str(r.get('commits') or '').strip()[:12] or 'NONE'}" for r in ready)) if ready else 'nothing waiting for the take-in'
    return (f"not ready: {', '.join(bare)} wait with no commit · " if bare else '') + line


def landed(r, info):
    """its commit on HEAD already, the one past its base, THE DAY's, its message '<id>:': its sha, or ''"""
    if not info.get('base') or not info.get('committing') or changed():
        return ''
    past = moved(info['base'])
    return past[0][0] if len(past) == 1 and past[0][1] == F('day_email') and past[0][3].startswith(f"{r['id']}:") else ''


def run(given):
    if day_off():
        return off()
    r, bad = the_one(F('reviewed'))
    if bad:
        return red(*bad)
    if r is None:
        return said(f"nothing {F('reviewed')}: nothing to commit · {take_in()}", [('Reviewed', 'none')])
    checks = [('The request', f"{r['id']} · {' '.join(str(r['words']).split())[:100]}")]
    bad = tree_red(clean=False)
    if bad:
        return red(*bad, checks)
    info, tests = side(r), tests_of(r)
    sha_ = landed(r, info)
    if sha_:
        if not set_state(r['id'], F('ready'), "committed before its run ended: recorded, ready for tonight's take-in", F('reviewed'), commits=sha_, done_at=office.stamp()):
            return red(f"{r['id']}: its commit {sha_[:12]} landed but a press moved it off {F('reviewed')}", 'see its state, then RUN here')
        return said(f"{r['id']} · {sha_[:12]} · its commit landed before: recorded · {take_in()}", checks)
    bad = since_pick(r, info, built=True)
    checks.append(('On its base, changed in its own files alone', bad[0] if bad else f"yes: {len(info['files'])} file(s): {', '.join(info['files'][:4])}"))
    if bad:
        return red(*bad, checks)
    if not os.path.isdir(tests) or sha(tests) != r.get('tests_sha'):
        checks.append(('Its tests the frozen ones', 'no'))
        return red(f"{r['id']}: its tests moved since its review", f"{asked_again(r['id'])}: built anew with new tests, then RUN Pick", checks)
    checks.append(('Its tests the frozen ones', f"yes ({r['tests_sha'][:12]})"))
    if proof(info['base']) != info.get('proof'):
        checks.append(('Its change the one proven and read', 'no'))
        return red(f"{r['id']}: its change is not the one proven and read", f"see git -C {F('tree')} diff {info['base'][:12]}; to prove and read it again set it back to building, then RUN Prove", checks)
    checks.append(('Its change the one proven and read', f"yes ({str(info['proof'])[:12]})"))
    busy = writer_busy()
    checks.append(("The tree's writer mark", busy or 'free'))
    if busy:
        return red(busy, wait_step(busy), checks)
    files, ident = sorted(info['files']), ['-c', f"user.name={F('day_name')}", '-c', f"user.email={F('day_email')}"]
    if F('dry'):
        g = f"git -C {F('tree')} "
        return said(f"{r['id']} · would commit {len(files)} file(s) by path on {branch()} at {head()[:12]}, then set it {F('ready')} · {take_in()}", checks,
                    [g + 'add -- ' + ' '.join(shlex.quote(f) for f in files), g + ' '.join(shlex.quote(a) for a in ident) + ' commit -q -m ' + shlex.quote(message(r)[:300])], request=r['id'])
    with Writer():
        side(r, committing=office.stamp())
        added = git('add', '--', *files)
        made = git(*ident, 'commit', '-q', '-m', message(r)) if added.returncode == 0 else added
        if made.returncode != 0:
            git('restore', '--staged', '--', *files)
            side(r, committing='')
            return red(f"{r['id']}: its commit did not land ({last(added.stderr + made.stderr + made.stdout)[:200]})", f'rm -f "$(git -C {F("tree")} rev-parse --git-dir)/index.lock" when a stopped git left it, then RUN here', checks)
    commit = head()
    if [m[0] for m in moved(info['base'])] != [commit]:
        return red(f"{r['id']}: its commit {commit[:12]} is not the one commit past its base", f"git -C {F('tree')} log {info['base'][:12]}..HEAD names them", checks)
    if not set_state(r['id'], F('ready'), "committed, ready for tonight's take-in", F('reviewed'), commits=commit, done_at=office.stamp()):
        return red(f"{r['id']}: its commit {commit[:12]} landed but a press moved it off {F('reviewed')}: not recorded", 'see its state, then RUN here', checks)
    return said(f"{r['id']} · {commit[:12]} · {len(files)} file(s) by path · {take_in()}", checks, request=r['id'])


canvas = canvas_of('Commit')


if __name__ == '__main__':
    office.main(canvas, run)
