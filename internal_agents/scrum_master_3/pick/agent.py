"""PICK, Scrum Master 3's DAY step (SM2 agent014, the plan): the next asked request in build order (position, then id), marked picked
only on a clean hot fix tree with nothing in hand and the tree's writer mark free, its base HEAD and the clean tree kept in its side
file (the office's own data file, outside the tree); one at a time. A press between the read and the pick wins. Nothing asked: the
backlog is built to its end, and Cleanup is next. It writes the office's database and its side file only, never the tree."""


import office
from day import F, branch, canvas_of, day_off, head, off, red, said, set_state, side, tree_red, wait_step, writer_busy


def run(given):
    if day_off():
        return off()
    checks = []
    hand = office.requests(F('in_hand'))
    checks.append(('A request in hand', f"{hand[0]['id']} is {hand[0]['state']}" if hand else 'none'))
    if hand:
        return red(f"{hand[0]['id']} is {hand[0]['state']}: one request at a time on the tree", f"RUN {F('next') if hand[0]['state'] == F('picked') else 'Building now'}, it names the step that is next", checks)
    busy = writer_busy()
    checks.append(("The tree's writer mark", busy or 'free'))
    if busy:
        return red(busy, wait_step(busy), checks)
    bad = tree_red()
    checks.append(('The hot fix tree', bad[0] if bad else f"{F('tree')} on {branch()}, clean, HEAD {head()[:12]}"))
    if bad:
        return red(*bad, checks)
    asked = office.requests([F('asked')])
    checks.append(('Asked, in build order', len(asked)))
    for r in asked:
        base = head()
        if set_state(r['id'], F('picked'), 'picked by THE DAY', F('asked')):
            side(r, id=r['id'], base=base, clean=True, picked_at=office.stamp(), files=[], prints={})
            return said(f"{r['id']} picked on {base[:12]} · {len(asked) - 1} more asked", checks, request=r['id'])
    return said('nothing asked: the backlog is built to its end', checks, next=F('done_next'))


canvas = canvas_of('Pick')


if __name__ == '__main__':
    office.main(canvas, run)
