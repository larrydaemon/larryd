"""NEW FILES, Scrum Master 3's LIVE check, on demand (the owner: "the main thing is a extra file that is unexpected"). Every file
of the workspace is known by its birth, its change time and its kind against its last RUN: what is new, changed and gone is
counted, every new page named, and only an UNEXPECTED new file is red:
  a new name at the top of the workspace; a new file with a sealed core file's name outside the core; a new file outside the
  three places (git, the offices' instance folders, the compilers' folders) that git does not see; a program in a data folder;
  a kind that is not a compiler's own in its folder; a new link.
Claude Code's own files (a .claude folder anywhere, CLAUDE.md, CLAUDE.local.md, .mcp.json) are expected: counted, never red.
Each unexpected file gets a number (F-0001 ...) the first time it is seen, never given twice, and stays open (red) until it is
gone, seen by git, or the owner says it belongs (facts "belongs": its number or path, and why). Its ledger and its line live in
its own RUN's data, read back on the next RUN: it writes no file. Past most_files its walk stops: red on every RUN, never a
ledger item, and a cut walk never moves its line."""
import datetime
import html
import json
import os
import re
import subprocess
import time
import unicodedata

import look as lookkit
import office

HAND = 'YOUR 3 MIN: '


class Fault(Exception):
    def __init__(self, where, line):
        self.where, self.step = where, office.fact('fault_steps')[where]
        super().__init__(f'{where}: {line}')


def claudes(p):
    parts = unicodedata.normalize('NFC', p).lower().rstrip(os.sep).split(os.sep)
    return office.fact('claude_folder') in parts[:-1] or parts[-1] in office.fact('claude_names')


def walk(top):
    """{path: [birth, changed, is a link]} of every file, nothing opened, no link followed; cut when past most_files"""
    found, most, skip = {}, office.fact('most_files'), set(office.fact('never_walked'))
    for root, dirs, names in os.walk(top):
        if len(found) > most:
            return found, True
        links = [d for d in dirs if os.path.islink(os.path.join(root, d))]
        dirs[:] = [d for d in dirs if d not in skip and d not in links]
        for name in names + links:
            path = os.path.join(root, name)
            try:
                st = os.lstat(path)
            except OSError:
                continue
            found[os.path.relpath(path, top)] = [getattr(st, 'st_birthtime', st.st_ctime), st.st_mtime, os.path.islink(path)]
    return found, len(found) > most


def unseen(top, paths):
    """which of these git does not see (ignored); git refusing is a fault, never every file counted as seen"""
    paths = [p for p in paths if not p.endswith(os.sep)]
    if not paths:
        return set()
    try:
        got = subprocess.run(['git', '-C', top, 'check-ignore', '-z', '--stdin'], input='\0'.join(paths), capture_output=True, text=True,
                             timeout=office.fact('git_seconds'), env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
    except subprocess.TimeoutExpired:
        raise Fault('the timeout', f"git check-ignore did not answer in {office.fact('git_seconds')} s") from None
    except OSError as no:
        raise Fault('git check-ignore', f'git would not start: {no}') from None
    if got.returncode not in (0, 1):
        raise Fault('git check-ignore', f"git refused (exit {got.returncode}): {' '.join((got.stderr or '').split())[:160]}")
    return {p for p in got.stdout.split('\0') if p}


def look(given):
    top = office.fact('workspace')
    was = office.data_of(office.own_job(given))
    started = time.time()
    try:
        with open(office.fact('global_config'), encoding='utf-8') as fh:
            gc = json.load(fh)
        offices, core = gc['offices'], os.path.join(gc['databases']['products'], '')
    except (OSError, ValueError, KeyError, TypeError) as no:
        raise Fault('global_config.json', f"unreadable: {type(no).__name__}: {' '.join(str(no).split())[:160]}") from None
    have, cut = walk(top)
    first = not isinstance(was.get('since'), (int, float))
    since = started if first else was['since']
    old_tops = set(was.get('tops') or [])
    tops = sorted({p.split(os.sep)[0] for p in have})

    instances = tuple(os.path.join(o['instance'], '') for o in offices.values() if o.get('instance')) + tuple(
        os.path.join(f'{n}-mini', f'{n}-mini', 'instance', '') for n in offices if os.path.isdir(os.path.join(top, f'{n}-mini', f'{n}-mini', 'instance')))
    compilers = office.fact('compilers')

    def place(p):
        if p.startswith(instances):
            return 'data'
        parts = p.split(os.sep)
        return next((k for k in compilers if (p.startswith(os.path.join(k, '')) if '/' in k else k in parts[:-1])), '')
    kind = lambda p: os.path.splitext(re.sub(r'\.\d+$', '', p))[1].lower()  # noqa: E731
    home = lambda p: p.lower().startswith(office.fact('claude_folder') + os.sep)  # noqa: E731

    new = sorted(p for p, (born, _, _) in have.items() if born > since)
    outside = [p for p in new if not place(p) and not home(p)]
    changed = sorted(p for p, (born, at, _) in have.items() if at > since and born <= since and not place(p) and not claudes(p))
    gone = max(0, int(was.get('total') or 0) + len(new) - len(have)) if not first else 0
    sealed = {os.path.basename(p).lower() for p in have if p.startswith(core) and p not in new
              and any(f'{os.sep}{f}{os.sep}' in p for f in office.fact('sealed_folders'))} | set(office.fact('sealed_names'))
    hidden = unseen(top, outside)
    at_top = [p for p in new if (os.sep not in p or (old_tops and p.split(os.sep)[0] not in old_tops)) and not claudes(p)]
    found = [('a new name at the top', t) for t in sorted({p.split(os.sep)[0] + os.sep if os.sep in p else p for p in at_top})]
    found += [("a new file with a sealed core file's name outside the core", p) for p in new if os.path.basename(p).lower() in sealed and not p.startswith(core)]
    found += [('a new file git does not see', p) for p in outside if p in hidden and p not in set(at_top)]
    found += [('a program in a data folder', p) for p in new if place(p) == 'data' and kind(p) in office.fact('programs')]
    found += [(f"not a compiler's own kind in {place(p)}", p) for p in new if place(p) in compilers and compilers[place(p)] is not None and kind(p) not in compilers[place(p)]]
    found += [('a link', p) for p in new if have[p][2]]
    tracked = {}
    for why, p in found:
        if not claudes(p):
            tracked.setdefault(p, why)

    # THE LEDGER, carried from its last RUN: a number is never given twice
    book = was.get('ledger') or {'next': 1, 'items': {}}
    items, nxt, now = dict(book.get('items') or {}), int(book.get('next') or 1), office.stamp()
    present = set(have) | {p.split(os.sep)[0] + os.sep for p in have if os.sep in p}
    for p, why in tracked.items():
        mine = items.get(p)
        if mine and (mine['state'] == 'open' or (mine['state'] == 'belongs' and mine['why'] == why)):
            mine['why'] = why
            continue
        items[p] = {'n': f'F-{nxt:04d}', 'why': why, 'first': now, 'state': 'open'}
        nxt += 1
    answers = office.fact('belongs') or {}
    for p, i in items.items():
        said = answers.get(i['n']) or answers.get(p)
        if i['state'] == 'open' and said:
            i.update(state='belongs', how=str(said)[:300], closed=now)
    waiting = [p for p, i in items.items() if i['state'] == 'open' and p not in tracked]
    in_git = {p for p in waiting if p in present and not p.endswith(os.sep)} - unseen(top, [p for p in waiting if p in present])
    for p in list(items):
        if p not in present and not cut:
            del items[p]   # gone: closed (if it ever comes back it is a new question)
        elif p in in_git:
            del items[p]   # seen by git: closed
    open_ = sorted(({'path': p, **i} for p, i in items.items() if i['state'] == 'open'), key=lambda i: i['n'])

    pages = [p for p in outside if p.endswith(office.fact('page_kind'))]
    claude = sum(1 for p in new + changed if claudes(p) or home(p))
    word = ('first look: ' + f'{len(have)} files known, new ones counted from now' if first else
            f"since {time.strftime('%H:%M', time.localtime(since))}: {len(outside)} new, {len(changed)} changed, {gone} gone")
    word += f" · new page(s): {', '.join(os.path.basename(p) for p in pages[:6])}" if pages else ''
    word += f" · Claude Code's home: {claude} files" if claude else ''
    heads, steps = [], []
    if cut:
        heads.append(f"more than {office.fact('most_files')} files: its walk stopped early")
        steps.append(office.fact('cut_step'))
    if open_:
        heads.append(f'{len(open_)} unexpected file(s): ' + '; '.join(f"{i['n']} {i['why']}: {i['path']}" for i in open_[:4])
                     + (f' (+{len(open_) - 4} more)' if len(open_) > 4 else ''))
        steps.append(office.fact('unexpected_step').format(n=open_[0]['n']))
    most = office.fact('list_most')
    return {'ok': not open_ and not cut, 'cut': cut, 'head': '; '.join(heads) or 'nothing unexpected', 'word': word, 'step': '; and '.join(steps),
            'unexpected': [{k: i[k] for k in ('n', 'why', 'path')} for i in open_], 'new': len(outside), 'changed': len(changed), 'gone': gone,
            'pages': pages, 'claude': claude, 'at': office.stamp(), 'lists': {'new': outside[:most], 'changed': changed[:most]},
            'since': since if cut else started, 'tops': tops if not cut else sorted(old_tops), 'total': len(have) if not cut else was.get('total'),
            'ledger': {'next': nxt, 'items': items}}


def run(given):
    try:
        got = look(given)
    except Exception as fault:   # noqa: BLE001  a crash is red, named, with its one step
        f = fault if isinstance(fault, Fault) else Fault('the program', (f'{type(fault).__name__}: {fault}'.splitlines() or [''])[0][:200])
        line = f'RED · {f} · {HAND}{f.step}'
        office.live_set(office.fact('live_key'), office.me()['name'], 'RED', line, str(f), f.step)
        return office.done(line, 'RED', {**office.data_of(office.own_job(given)), 'fault': str(f), 'step': f.step, 'at': office.stamp()})
    state = 'GREEN' if got['ok'] else 'RED'
    line = f"{state} · {got['head']} · {got['word']}" + (f" · {HAND}{got['step']}" if got['step'] else '')
    office.live_set(office.fact('live_key'), office.me()['name'], state, line, '' if got['ok'] else got['head'], got['step'])
    return office.done(line, state, got)


def canvas(given):
    """SM2's LIVE BLOCK, one line (page.py live_block): the name as a title, the state word in its colour and the time since that state
    began (RUNNING while its RUN is open, IDLE when its light is GREEN, NOT RUNNING when it is RED or it never ran), the group on the right"""
    job = office.own_job(given)
    light = office.light_of(job)
    row = next((r for r in office.live_all() if r['key'] == office.fact('live_key')), {})
    if str(job.get('data_job_run_state') or '').upper() in ('QUEUED', 'RUNNING'):
        word, cls, began = 'RUNNING', 'hdr-status--success', job.get('system_updated_at')
    else:
        word, cls = ('IDLE', 'scrum-idle') if light == 'GREEN' else ('NOT RUNNING', 'hdr-status--error')
        began = row.get('changed_at') if row.get('state') == light else job.get('data_job_last_run_at')
    try:
        t = datetime.datetime.fromisoformat(str(began or '').replace('Z', '+00:00'))
        s = max(0, int((office.now() - (t if t.tzinfo else t.replace(tzinfo=office.now().tzinfo))).total_seconds()))
        clock = f'<span class="scrum-since {cls}"> ' + (f'{s // 3600} H ' if s >= 3600 else '') + (f'{s % 3600 // 60} MIN ' if s >= 60 else '') + f'{s % 60} S</span>'
    except ValueError:
        clock = ''
    key, e = office.fact('live_key'), html.escape
    return lookkit.view(f'<div class="replica-live-block" data-live-block="{e(key)}"><div class="title scaf-law-title">{e(office.me()["name"])}</div>'
                        f'<div class="replica-live-line" data-live-key="{e(key)}" data-live-state="{e(light)}"><div class="subtitle"><span class="{cls}">{word}</span>{clock}</div></div>'
                        f'<span class="replica-live-group" aria-label="group">{e(office.me().get("group") or "LIVE")}</span></div>',
                        (given.get('page') or {}).get('path') or '', office.fact('css') or '')


if __name__ == '__main__':
    office.main(canvas, run)
