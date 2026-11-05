"""PROVE, Scrum Master 3's DAY step (SM2 agent016): on the tree still at its base and changed in its own recorded files alone, the
built request's own tests run on the hot fix tree, unchanged since frozen: every one passes, none skipped, the tree the same after;
the change's fingerprint (its diff from its base and its new files' bytes) kept in its side file. A red puts its own change back and
sets it aside, stuck today. DRY (its fact): it does every read and says the test run it would make; the real run is behind dry false."""
import os
import re
import subprocess
import time

import office
from day import F, Writer, asked_again, branch, canvas_of, changed, day_off, head, last, off, proof, red, said, set_aside, set_state, sha, side, since_pick, tests_of, the_one, tree_red, wait_step, writer_busy


def run_line(tests):
    return f"cd {F('tree')} && {F('python')} -m unittest discover -s {tests} -t {tests}"


def run(given):
    if day_off():
        return off()
    r, bad = the_one(F('built'))
    if bad:
        return red(*bad)
    if r is None:
        return said(f"nothing {F('built')}: nothing for Prove to do", [('Built', 'none')], next='Building now')
    checks = [('The request', f"{r['id']} · {' '.join(str(r['words']).split())[:100]}")]
    bad = tree_red(clean=False)
    if bad:
        return red(*bad, checks)
    info, tests = side(r), tests_of(r)
    bad = since_pick(r, info, built=True)
    checks.append(('On its base, changed in its own files alone', bad[0] if bad else f"yes: {len(info['files'])} file(s): {', '.join(info['files'][:4])}"))
    if bad:
        return red(*bad, checks)
    if not os.path.isdir(tests) or sha(tests) != r.get('tests_sha'):
        why = f'its tests folder is gone ({tests})' if not os.path.isdir(tests) else f"its tests are not the ones frozen ({str(r.get('tests_sha') or 'none')[:12]})"
        checks.append(('Its tests', why))
        return red(f"{r['id']}: {why}", f"{asked_again(r['id'])}: its tests are written anew, then RUN Pick", checks)
    checks.append(('Its tests', f"frozen, the same bytes ({r['tests_sha'][:12]})"))
    busy = writer_busy()
    checks.append(("The tree's writer mark", busy or 'free'))
    if busy:
        return red(busy, wait_step(busy), checks)
    print_ = proof(info['base'])
    checks.append(('Its change now', print_[:12]))
    if F('dry'):
        return said(f"{r['id']} · would run its {r['tests_sha'][:12]} tests on {branch()} at {head()[:12]}", checks,
                    [f"{run_line(tests)}  (PYTHONDONTWRITEBYTECODE=1 TREE_DIR={F('tree')}, at most {F('prove_seconds')} s): every one passes, none skipped"], request=r['id'])
    with Writer():
        t0 = time.monotonic()
        try:
            got = subprocess.run([F('python'), '-m', 'unittest', 'discover', '-s', tests, '-t', tests], cwd=F('tree'), capture_output=True, text=True,
                                 timeout=F('prove_seconds'), env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'TREE_DIR': F('tree')})
        except subprocess.TimeoutExpired:
            return set_aside(r, info['base'], set(info['files']) | set(changed()), f"its tests did not end in time (stopped at {F('prove_seconds')} s)", f"{asked_again(r['id'])}, then RUN Pick")
        text = (got.stdout or '') + (got.stderr or '')
        ran = int((re.search(r'^Ran (\d+) tests?', text, re.M) or [0, 0])[1])
        skipped = bool(re.search(r'skipped=\d+|expected failures=\d+', text))
        if got.returncode != 0 or ran == 0 or skipped:
            failed = re.findall(r'^(?:FAIL|ERROR): (\S+)', text, re.M)
            return set_aside(r, info['base'], set(info['files']) | set(changed()), 'a test was skipped' if skipped and got.returncode == 0 else
                             f"its tests did not pass ({last(text)[:160]}{': ' + '; '.join(failed[:4]) if failed else ''})", f"its run line: {run_line(tests)}; then {asked_again(r['id'])}")
        if proof(info['base']) != print_:
            return set_aside(r, info['base'], set(info['files']) | set(changed()), 'its tests changed the tree while they ran', f"{asked_again(r['id'])}, then RUN Pick")
        secs = round(time.monotonic() - t0)
        side(r, proof=print_, proven_at=office.stamp(), proven_tests=ran, proven_seconds=secs)
        if not set_state(r['id'], F('proven'), f'proven: {ran} of {ran} tests pass', F('built')):
            return red(f"{r['id']} is no longer {F('built')}: a press during the run wins", 'see its state, then RUN Building now')
    return said(f"{r['id']} · {ran} of {ran} tests pass, none skipped, in {secs} s · its change {print_[:12]}", checks, request=r['id'])


canvas = canvas_of('Prove')


if __name__ == '__main__':
    office.main(canvas, run)
