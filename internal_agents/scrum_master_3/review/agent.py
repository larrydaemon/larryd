"""REVIEW, Scrum Master 3's DAY step (SM2 agent017): the change still the one proven (its fingerprint found again), a separate Claude
Code reader, blind (it never saw the build), reads the whole change from its base, its new files and its tests against his words:
LEGIT or STUPID, its verdict the last line it says. Never cut: a change too big to read whole is set aside. A STUPID puts its own
change back and sets it aside, stuck today; a read with no verdict is the reader's fault and the request stays proven.
DRY (its fact): it does every read and says the blind read it would ask; the real read is behind dry false."""
import os
import re
import shlex
import subprocess
import time

import office
from day import F, Writer, asked_again, canvas_of, changed, day_off, git, last, off, out, proof, red, said, set_aside, set_state, side, since_pick, tests_of, the_one, tree_red, wait_step, writer_busy


def words_review(r, diff, tests_text):
    a, b = F('verdicts')
    return (f"You are THE DAY's reviewer, BLIND: you never saw the build. Read the change against the owner's own words and decide.\n\n"
            f"THE REQUEST {r['id']}, his words:\n{r['words']}\n\nITS TESTS:\n{tests_text}\n\nTHE CHANGE (git diff):\n{diff}\n\n"
            f"{a} when the change does what he asked, no more, honestly (no test cheated, no shortcut, nothing faked). {b} otherwise. "
            f"Your last line exactly: VERDICT: {a} <one line why> or VERDICT: {b} <one line why>.")


def the_change(r, info, tests):
    """the whole change, its new files and its tests, as the reader reads them; what is past its caps named"""
    caps, tree, files = F('caps'), F('tree'), sorted(info['files'])
    diff = out('diff', info['base'], '--', *files)
    news = [f for f in files if git('ls-files', '--error-unmatch', '--', f).returncode != 0 and os.path.isfile(os.path.join(tree, f))]
    texts = {f: open(os.path.join(tree, f), encoding='utf-8', errors='replace').read() for f in news}
    test_files = sorted(os.path.join(rt, f) for rt, _d, fs in os.walk(tests) for f in fs if f.endswith('.py'))
    tests_text = ''.join(f'\n# {os.path.relpath(f, tests)}\n' + open(f, encoding='utf-8', errors='replace').read() for f in test_files)
    over = ([f"its diff is past {caps['diff']} characters"] if len(diff) > caps['diff'] else []) \
        + [f"new file {f} is past {caps['file']} characters" for f, t in texts.items() if len(t) > caps['file']][:3] \
        + ([f"its tests are past {caps['tests']} characters"] if len(tests_text) > caps['tests'] else [])
    return diff + ''.join(f'\n+++ new file {f}\n{t}' for f, t in texts.items()), tests_text, over


def run(given):
    if day_off():
        return off()
    r, bad = the_one(F('proven'))
    if bad:
        return red(*bad)
    if r is None:
        return said(f"nothing {F('proven')}: nothing for Review to do", [('Proven', 'none')], next='Building now')
    checks = [('The request', f"{r['id']} · {' '.join(str(r['words']).split())[:100]}")]
    bad = tree_red(clean=False)
    if bad:
        return red(*bad, checks)
    info, tests = side(r), tests_of(r)
    bad = since_pick(r, info, built=True)
    checks.append(('On its base, changed in its own files alone', bad[0] if bad else f"yes: {len(info['files'])} file(s)"))
    if bad:
        return red(*bad, checks)
    now_ = proof(info['base'])
    checks.append(('Its change is the one proven', 'yes' if now_ == info.get('proof') else f"no: {now_[:12]}, proven {str(info.get('proof') or 'none')[:12]}"))
    if now_ != info.get('proof'):
        return red(f"{r['id']}: its change is not the one proven", f"see git -C {F('tree')} diff {info['base'][:12]}; to prove it again set it back to {F('built')}, then RUN Prove", checks)
    diff, tests_text, over = the_change(r, info, tests)
    checks.append(('Read whole', '; '.join(over) if over else f'yes: {len(diff)} characters of change, {len(tests_text)} of tests'))
    busy = writer_busy()
    checks.append(("The tree's writer mark", busy or 'free'))
    if busy:
        return red(busy, wait_step(busy), checks)
    words = words_review(r, diff, tests_text)
    if F('dry'):
        return said(f"{r['id']} · would ask the blind reader" + (f" and set it aside: {'; '.join(over)}" if over else ''), checks,
                    [f"{' '.join(shlex.quote(a) for a in F('reader'))}  < its words ({len(words)} characters), at most {F('review_seconds')} s; "
                     f"its last line VERDICT: {' or '.join(F('verdicts'))} <why>"], request=r['id'])
    with Writer():
        if over:
            return set_aside(r, info['base'], info['files'], f"the change is too big for the blind reader to read whole ({'; '.join(over)})", 'a smaller request is his to ask (UPDATE on Backlog)')
        t0 = time.monotonic()
        try:
            got = subprocess.run(F('reader'), cwd=F('tree'), input=words, capture_output=True, text=True, timeout=F('review_seconds'))
            code, text = got.returncode, got.stdout or ''
        except subprocess.TimeoutExpired:
            code, text = None, ''
        secs = round(time.monotonic() - t0)
        if proof(info['base']) != now_:
            return set_aside(r, info['base'], set(info['files']) | set(changed()), 'its change moved while it was read', f"{asked_again(r['id'])}, then RUN Pick")
        m = re.match(rf"^\s*VERDICT\s*:\s*({'|'.join(F('verdicts'))})\b[\s:,.·-]*(.*?)\s*$", last(text), re.I) if code == 0 else None
        if not m or not m.group(2).strip():
            return red(f"{r['id']}: its blind read gave no verdict (exit {code}, {secs} s): it stays proven, its change kept", 'RUN Review again, one press', checks)
        if m.group(1).upper() != F('verdicts')[0]:
            return set_aside(r, info['base'], info['files'], f'its review said {m.group(1).upper()}: {m.group(2)[:200]}', f"{asked_again(r['id'])}, then RUN Pick")
        side(r, read={'verdict': m.group(1).upper(), 'why': m.group(2)[:200], 'at': office.stamp(), 'seconds': secs})
        if not set_state(r['id'], F('reviewed'), f'reviewed {m.group(1).upper()}: {m.group(2)[:200]}', F('proven')):
            return red(f"{r['id']} is no longer {F('proven')}: a press during the read wins", 'see its state, then RUN Building now')
    return said(f"{r['id']} · {m.group(1).upper()} · {m.group(2)[:160]}", checks, request=r['id'], seconds=secs)


canvas = canvas_of('Review')


if __name__ == '__main__':
    office.main(canvas, run)
