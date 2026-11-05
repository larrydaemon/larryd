"""AGENT ACCESS, the shared block of every MARK IV workflow (owned by Operations Manager): who may reach what on this computer.
The sanity home's real tree as the disk has it now (each folder's lock from its own flags, its files counted), THE LOCK in its three
parts (folders, sessions, database) and the pin and reseal records, each read where it lives. View only: locking, unlocking and
resealing are the owner's own hands, never a press here."""
import datetime
import json
import os
import sqlite3
import stat

import look
import office

FLAGS = stat.SF_IMMUTABLE | stat.UF_IMMUTABLE



def flagged(path):
    try:
        return bool(os.lstat(path).st_flags & FLAGS)
    except (OSError, AttributeError):
        return False


def tree(path, depth=0, opened=False):
    """a folder as the disk has it: LOCKED when it and every file under it is flagged immutable; open to the depth fact, or all the way
    down inside a folder the expand fact names"""
    shut = set(office.fact('shut') or ())
    try:
        names = sorted(n for n in os.listdir(path) if n not in shut)
    except OSError:
        names = []
    dirs = [n for n in names if os.path.isdir(os.path.join(path, n)) and not os.path.islink(os.path.join(path, n))]
    count = locked = 0
    for root, ds, fs in os.walk(path):
        ds[:] = [d for d in ds if d not in shut]
        for f in fs:
            if f not in shut:
                count += 1
                locked += flagged(os.path.join(root, f))
    name = os.path.basename(path.rstrip('/'))
    opened = opened or name in (office.fact('expand') or ())
    deeper = opened or depth + 1 < int(office.fact('depth'))
    return {'name': name, 'files': count, 'locked': locked, 'lock': 'LOCKED' if count and locked == count and flagged(path) else 'UNLOCKED',
            'children': [tree(os.path.join(path, d), depth + 1, opened) for d in dirs] if deeper else [],
            'more': len(dirs) if not deeper else 0, 'own_files': [n for n in names if n not in dirs] if opened or depth == 0 else []}


def lock_state(folders):
    home = office.fact('sanity_home')
    try:
        with open(office.fact('sessions_sandbox'), encoding='utf-8') as fh:
            sessions = 'LOCKED' if f'(subpath "{home}")' in fh.read() else 'UNLOCKED'
    except OSError:
        sessions = 'LOCKED'
    try:
        database = 'UNLOCKED' if os.stat(office.fact('master_mark')).st_uid == 0 else 'LOCKED'
    except OSError:
        database = 'LOCKED'
    return {'folders': folders, 'sessions': sessions, 'database': database}


def when(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%b %d %H:%M').upper() if ts else ''


def reseal_state():
    """each step's own record: the vault by its newest owner seal, the spine by the Judge's signed seal, the pin by the ledger's last
    entry, the moire by its baseline; '' for a step with no record"""
    out = {}
    try:
        con = sqlite3.connect(f"file:{office.fact('vault_seals')}?mode=ro", uri=True, timeout=2)
        try:
            at = con.execute('SELECT MAX(sealed_at) FROM users_vault_owner_seals').fetchone()[0]
        finally:
            con.close()
        out['vault'] = f'SEALED {when(datetime.datetime.fromisoformat(at).timestamp())}' if at else ''
    except (sqlite3.Error, ValueError, TypeError):
        out['vault'] = ''
    seal = office.fact('spine_seal')
    out['spine'] = f'SEALED {when(os.path.getmtime(seal))}' if os.path.exists(seal) and os.path.exists(seal + '.sig') else ''
    try:
        with open(office.fact('pin_ledger'), encoding='utf-8') as fh:
            last = [ln for ln in fh.read().splitlines() if ln.strip()][-1]
        at = str(json.loads(last).get('at') or '')
        out['pin'] = 'PINNED ' + (when(datetime.datetime.fromisoformat(at.replace('Z', '+00:00')).timestamp()) if at else '')
    except (OSError, IndexError, ValueError):
        out['pin'] = ''
    base = office.fact('moire_baseline')
    out['moire'] = f'RESET {when(os.path.getmtime(base))}' if os.path.exists(base) else ''
    return out


def access():
    t = tree(office.fact('sanity_home'))
    lock = lock_state(t['lock'])
    word = 'LOCKED' if set(lock.values()) == {'LOCKED'} else 'OPEN' if set(lock.values()) == {'UNLOCKED'} else 'PART LOCKED'
    return {'tree': t, 'lock': lock, 'word': word, 'reseal': reseal_state(), 'at': office.stamp()}


def mark(w):
    """SM2's mark of a step: not pressed yet, a red x (NOT ..., UNLOCKED), else a green check, each its word (look drops svg)"""
    if not w:
        return '<span class="replica-press-state"><span class="replica-press-none">Not pressed yet</span></span>'
    bad = w.startswith('NOT') or w == 'UNLOCKED'
    cls = 'hdr-status--error' if bad else 'hdr-status--success'
    return (f'<span class="replica-press-state"><span class="{cls}" role="img" aria-label="{"Not done" if bad else "Done"}">{"×" if bad else "✓"}</span> '
            f'<span class="{cls}">{office.e(w)}</span></span>')


def pressed(given, which):
    """a press only answers: his tool is his own, in the terminal"""
    if office.asked(given, 'press') != which:
        return ''
    tool = (office.fact('hand_tools') or {}).get(which, '')
    return f'<div class="annotation replica-press-busy">YOURS TO RUN IN THE TERMINAL: {office.e(tool)}</div>'


def press(path, which, words):
    return (f'<form method="get" action="{office.e(path)}"><input type="hidden" name="press" value="{which}">'
            f'<button class="pfb pfb--clarity" type="submit">{words}</button></form>')   # the embedded clarity widget, class only (the owner 2026-11-04: "make sure all the agents inject the embedded buttons too")


CSS = '.replica-tree-top > li > .t-details > .t-summary::before { content: "▶"; display: inline-block; font-size: .7em; margin-right: .5em; vertical-align: .1em; }'


def canvas(given):
    """SM2's AGENT ACCESS (its frame's replica-access): the tree folded to its top line, LOCK AGENT and PIN AND RESEAL with their lines"""
    a = access()
    t, lock, r = a['tree'], a['lock'], a['reseal']
    path = str((given.get('page') or {}).get('path') or '')
    is_open = set(lock.values()) == {'UNLOCKED'}
    which = 'lock' if is_open else 'unlock'
    top = (f'<li data-home="{office.e(t["name"])}"><details data-depth="0"><summary><strong>{office.e(t["name"])}/</strong> '
           + mark(t['lock']).replace('<span class="replica-press-state">', '', 1)[:-7]
           + f' <span class="replica-access-count">· {t["files"]} FILES</span></summary></details></li>')
    text = ('<div class="replica-xboard-agent"><div class="replica-group" aria-label="group">TOP</div>'
            '<div class="clarity replica-xboard replica-access" aria-label="AGENT ACCESS">'
            '<div class="replica-xboard-head"><span class="replica-xboard-title">AGENT ACCESS</span></div>'
            f'<div class="replica-access-body"><div class="replica-access-caption">HOME</div><ul class="replica-tree replica-tree-top">{top}</ul>'
            f'<div class="replica-press">{press(path, which, "LOCK AGENT" if is_open else "UNLOCK AGENT")}{pressed(given, which)}'
            f'<ul class="replica-press-what"><li><span>Every file in {office.e(office.fact("sanity_home").replace(office.HOME, "~"))}</span>{mark(lock["folders"])}</li>'
            f'<li><span>Claude sessions\' access</span>{mark(lock["sessions"])}</li><li><span>Knowledge database writes</span>{mark(lock["database"])}</li></ul></div>'
            f'<div class="replica-press">{press(path, "reseal", "PIN AND RESEAL")}{pressed(given, "reseal")}'
            f'<ul class="replica-press-what"><li><span>Vault: every office, your key</span>{mark(r["vault"])}</li>'
            f'<li><span>Spine: wid and global_config</span>{mark(r["spine"])}</li><li><span>Lie detector: new baseline</span>{mark(r["pin"])}</li>'
            f'<li><span>Moiré: baseline reset</span>{mark(r["moire"])}</li></ul></div></div></div></div>')
    return look.view(text, path, CSS)


def run(given):
    a = access()
    t, lock = a['tree'], a['lock']
    return office.done(f"{a['word']} · folders {lock['folders']}, sessions {lock['sessions']}, database {lock['database']} · "
                       f"{t['files']} files, {t['locked']} locked · " + ', '.join(f'{k} {v or "no record"}' for k, v in a['reseal'].items()),
                       'GREEN', {'word': a['word'], 'lock': lock, 'files': t['files'], 'locked': t['locked'], 'reseal': a['reseal']})


if __name__ == '__main__':
    office.main(canvas, run)
