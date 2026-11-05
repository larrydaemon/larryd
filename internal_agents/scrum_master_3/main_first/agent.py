"""MAIN FIRST, Scrum Master 3's DAY step (SM2 agent013): the hot fix tree there, on its branch and clean, nothing in hand, the tree's
writer mark free, then today's main merged into it so every request is built on today's code. DRY (its fact): it does every read and
says the merge it would run; the real merge, behind dry false, aborts a merge that does not go clean."""
import shlex

import office
from day import F, Writer, branch, canvas_of, day_off, git, head, last, off, red, said, tree_red, wait_step, writer_busy


def run(given):
    if day_off():
        return off()
    checks = []
    hand = office.requests(F('in_hand'))
    checks.append(('A request in hand', f"{hand[0]['id']} is {hand[0]['state']}" if hand else 'none'))
    if hand:
        return red(f"{hand[0]['id']} is {hand[0]['state']}: today's main is never merged under a request in hand", 'RUN Building now first', checks)
    busy = writer_busy()
    checks.append(("The tree's writer mark", busy or 'free'))
    if busy:
        return red(busy, wait_step(busy), checks)
    bad = tree_red()
    checks.append(('The hot fix tree', bad[0] if bad else f"{F('tree')} on {branch()}, clean, HEAD {head()[:12]}"))
    if bad:
        return red(*bad, checks)
    main, tree = F('main'), F('tree')
    if git('rev-parse', '--verify', '-q', f'{main}^{{commit}}').returncode != 0:
        return red(f'there is no {main} in the hot fix tree: not measured, nothing merged', f'git -C {tree} branch {main} origin/{main}, then RUN here', checks)
    checks.append((f"Today's {main}", git('log', '-1', '--format=%h · %ci · %s', main).stdout.strip()[:160]))
    if git('merge-base', '--is-ancestor', main, 'HEAD').returncode == 0:
        checks.append((f'The tree holds {main}', 'yes'))
        return said(f"{branch()} at {head()[:12]} already holds today's {main}", checks)
    behind = git('rev-list', '--count', f'HEAD..{main}').stdout.strip() or '?'
    checks.append((f'The tree holds {main}', f'no: {behind} commit(s) of {main} not merged yet'))
    merge = ['-c', f"user.name={F('day_name')}", '-c', f"user.email={F('day_email')}", 'merge', '--no-edit', main]
    if F('dry'):
        return said(f"would merge today's {main} ({behind} commit(s)) into {branch()} at {head()[:12]}", checks, [f'git -C {tree} ' + ' '.join(shlex.quote(a) for a in merge)])
    with Writer():
        got = git(*merge)
        if got.returncode != 0:
            git('merge', '--abort')
            return red(f"today's {main} did not merge by itself ({last(got.stdout + got.stderr)[:200]})", f'git -C {tree} merge {main}, resolve the conflict it names, commit the merge, then RUN here', checks)
    return said(f"today's {main} merged into {branch()} · {head()[:12]}", checks)


canvas = canvas_of('Main first')


if __name__ == '__main__':
    office.main(canvas, run)
