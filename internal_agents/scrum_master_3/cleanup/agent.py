"""CLEANUP, Scrum Master 3's DAY step, the day's last (SM2 agent020): the caches cleared under the tree's writer mark, then the hot fix
tree proven to hold nothing uncommitted, then what the day made ready said (that list never decides the light). DRY (its fact): it does
every read and says the caches it would clear."""
import os

import office
from day import F, Writer, branch, cache, canvas_of, changed, day_off, head, off, red, said, status, tree_red, wait_step, writer_busy


def caches():
    return [p for code, p in status('--ignored') if code in ('??', '!!') and cache(p) and not p.endswith('/')]


def run(given):
    if day_off():
        return off()
    checks = []
    busy = writer_busy()
    checks.append(('The hot fix utility and the writer mark', busy or 'free'))
    if busy:
        return red(busy, wait_step(busy), checks)
    bad = tree_red(clean=False)
    checks.append(('The hot fix tree', bad[0] if bad else f"{F('tree')} on {branch()}, HEAD {head()[:12]}"))
    if bad:
        return red(*bad, checks)
    left = changed()
    checks.append(('Uncommitted', f"{len(left)} file(s): {', '.join(left[:4])}" if left else 'none'))
    if left:
        return red(f"the tree holds {len(left)} file(s) nobody committed: {', '.join(left[:4])}", f"see git -C {F('tree')} status; commit or clear them by hand, then RUN here", checks)
    found = caches()
    checks.append(('Caches to clear', f"{len(found)}: {', '.join(found[:4])}" if found else 'none'))
    today = office.now().date().isoformat()
    ready = [r['id'] for r in office.requests([F('ready')]) if str(r.get('done_at') or '')[:10] == today]
    made = f"ready today: {', '.join(ready)}" if ready else 'nothing made ready today'
    if F('dry'):
        return said(f"the tree clean at {head()[:12]} · would clear {len(found)} cache file(s) · {made}", checks,
                    [f"rm -f -- {F('tree')}/<each of the {len(found)} cache file(s): __pycache__, .pyc, .DS_Store>"] if found else [], next='')
    with Writer():
        for p in found:
            try:
                os.remove(os.path.join(F('tree'), p))
            except OSError:
                pass
        left = [p for code, p in status('--ignored') if code != '!!' or cache(p)]
    if left:
        return red(f"the tree holds {len(left)} file(s) nobody committed: {', '.join(left[:4])}", f"see git -C {F('tree')} status; clear them by hand, then RUN here", checks)
    return said(f"{len(found)} cache(s) cleared · the tree clean at {head()[:12]} · {made}", checks, next='')


canvas = canvas_of('Cleanup')


if __name__ == '__main__':
    office.main(canvas, run)
