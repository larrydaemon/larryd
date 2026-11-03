"""THE CARRY'S OWN WORDS (the owner 2026-10-23 21:35, angry: the b_rnd sync said "stopped at carry: exit 1: }", the JSON's
last line, and the real fault was in its result file: "the demo account landed 0 of 1499 records (7 old members not on the
target), coteclat exact"). The carry (/Users/frost/data_sync/apply.py <n> <snap> --target <side>) writes
~/data_sync/apply/<target>/<n>/result.json: per account a block {exact, old_members_not_on_the_target, compare_file, ...}
and the compare file's counts. Read here for rows 033, 035 and 039 (no row imports another). A data sync carries the
named accounts' records only (the owner 2026-10-23 21:45: "a data sync from production to localhost NEVER" a whole
database): these words speak of accounts and records, never of databases."""
import glob
import json
import os

APPLY = os.path.expanduser('~/data_sync/apply')   # where the carry leaves its result, per target
COUNTS = ('expected', 'landed', 'landed_records', 'matched', 'missing', 'extra', 'different')   # the compare's counts, by the names it uses


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def blocks(result):
    """The accounts of a carry result: [(name, block)] for every dict in it that says 'exact'."""
    return [(k, v) for k, v in (result or {}).items() if isinstance(v, dict) and 'exact' in v] if isinstance(result, dict) else []


def _counts(block):
    """The compare's counts of an account that is not exact: the sum over its compare file's tables (each a dict with
    expected_records and landed_records), or the block's own counts. -> 'landed 0 of 1499 records, 1499 missing' or ''"""
    cmp = _json(str(block.get('compare_file') or '')) or {}
    tables = [v for v in cmp.values() if isinstance(v, dict) and 'expected_records' in v]
    found = {}
    if tables:
        found['expected'] = sum(int(t.get('expected_records') or 0) for t in tables)
        found['landed'] = sum(int(t.get('landed_records') or 0) for t in tables)
        found['missing'] = max(0, found['expected'] - found['landed'])
    for source in (block, cmp):
        for holder in (source, source.get('counts') if isinstance(source.get('counts'), dict) else {}, source.get('summary') if isinstance(source.get('summary'), dict) else {}):
            for k in COUNTS:
                if k in holder and isinstance(holder[k], (int, float)) and k not in found:
                    found[k] = int(holder[k])
    landed = found.get('landed', found.get('landed_records'))
    out = []
    if landed is not None and found.get('expected') is not None:
        out.append(f"landed {landed} of {found['expected']} records")
    elif landed is not None:
        out.append(f'landed {landed} records')
    for k in ('missing', 'extra', 'different'):
        if found.get(k):
            out.append(f'{found[k]} {k}')
    return ', '.join(out)


def words(result):
    """ONE LINE FOR THE CARRY, every account named: 'the demo account landed 0 of 1499 records (7 old members not on the target), coteclat exact'. '' when the result holds no account."""
    said = []
    for name, b in blocks(result):
        if b.get('exact') is True:
            said.append(f'{name} exact')
            continue
        old = b.get('old_members_not_on_the_target') or []
        detail = _counts(b)
        more = f"{len(old)} old member{'s' if len(old) != 1 else ''} not on the target" if old else ''
        inside = ', '.join(x for x in (detail, more) if x) if detail else more
        said.append(f"the {name} account {'NOT exact: ' + detail if detail else 'NOT exact'}" + (f" ({more})" if more and detail else (f" ({more})" if more else '')))
    said.sort(key=lambda s: not s.startswith('the '))   # the faults first, the exact ones after
    return ', '.join(said)


def result_path(target, since=None):
    """The newest carry result file of a target (~/data_sync/apply/<target>/sync*/result.json), made at or after `since` (an
    epoch seconds, when given): its path, or None."""
    paths = sorted(glob.glob(os.path.join(APPLY, target, 'sync*', 'result.json')), key=lambda p: os.path.getmtime(p))
    for path in reversed(paths):
        if since is not None and os.path.getmtime(path) < since - 60:
            return None
        return path
    return None


def result_of(target, since=None):
    """The newest carry result of a target, made at or after `since`: its dict, or None."""
    path = result_path(target, since)
    return _json(path) if path else None


def fault(target, since=None):
    """The carry's own words for a target's newest result (made at or after `since`), or ''."""
    return words(result_of(target, since))


def from_output(out):
    """The carry's words from its command's stdout: the JSON object it prints last (from the last line that opens one to the
    end), when it holds accounts; else ''."""
    lines = (out or '').splitlines()
    starts = [i for i, l in enumerate(lines) if l.strip().startswith('{')]
    for i in reversed(starts):
        try:
            got = json.loads('\n'.join(lines[i:]))
        except ValueError:
            continue
        return words(got) if blocks(got) else ''
    return ''
