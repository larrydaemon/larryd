"""FRAME · AGENT ACCESS (the owner 2026-10-27: "_ agent acess"; 2026-10-26: "AGENT ACCESS this is the next replica agent"; "its missing the lock
and the pin and reseal sections below the tree"; "the idea is the frame is not an agent / it holds agents / it does nothing on its own without an agent attached"): the home tree, the lock, the pin, the reseal. The real HOME tree as the disk
has it now (git's store and compiled caches never listed, never counted), each folder's lock from its own flags; THE LOCK NOW in its three
parts; the office's own presses (his fingerprint, then his tool: master lock | master unlock | reseal all) and what the last reseal said.
It reads and draws; a press is the owner's own hand on the page; nothing runs on its own."""
import datetime
import os
import stat

from frame import frame_replica as frame

SHUT = ('.git', '__pycache__')   # never listed, never counted (git's store, compiled caches): the tree is the app's own files (the owner 2026-10-27: "and totally fucking wrong")

RESEAL_STEPS = (('vault', '1. THE VAULT: '), ('spine', '2. THE SPINE: '), ('pin', '3. THE PIN: '), ('moire', '4. THE MOIRE: '))   # the reseal's own log lines

RUNNING = []   # the press now running, one at a time


def home_tree(path, depth=0, expand=('replica',), opened=False):
    """AGENT ACCESS'S HOME, the real tree (the owner 2026-10-26: "AGENT ACCESS this is the next replica agent"; "make it fully expand"):
    a folder, its folders and files as the disk has them now, its lock from its own flags (LOCKED: every entry flagged immutable;
    UNLOCKED: not), its files counted. Read only."""
    def flagged(p):
        try:
            return bool(os.lstat(p).st_flags & (stat.SF_IMMUTABLE | stat.UF_IMMUTABLE))
        except OSError:
            return False
    try:
        names = sorted(n for n in os.listdir(path) if n != '.DS_Store' and n not in SHUT)
    except OSError:
        names = []
    dirs = [n for n in names if os.path.isdir(os.path.join(path, n)) and not os.path.islink(os.path.join(path, n))]
    files = [n for n in names if n not in dirs]
    count = locked = 0
    for root, ds, fs in os.walk(path):
        ds[:] = [d for d in ds if d not in SHUT]
        for f in [x for x in fs if x != '.DS_Store']:
            count += 1
            locked += flagged(os.path.join(root, f))
    name = os.path.basename(path.rstrip('/'))
    opened = opened or depth == 0 or name in expand   # the top, and the office's folder all the way down, drawn open
    return {'name': name, 'open': opened, 'files_in': count, 'lock': 'LOCKED' if count and locked == count and flagged(path) else 'UNLOCKED',
            'children': [home_tree(os.path.join(path, d), depth + 1, expand, opened and depth > 0) for d in dirs], 'files': files}


def lock_state(tree):
    """THE LOCK NOW, its three parts as the original reads them: ~/virtual_sanity (its tree's lock), the Claude sessions'
    sandbox (does it name ~/virtual_sanity), the knowledge store's write block (the unlock mark root keeps). -> each LOCKED or
    UNLOCKED, 'open' when all three are UNLOCKED."""
    folders = tree.get('lock') or 'LOCKED'
    try:
        with open(frame.path('sessions_sandbox'), encoding='utf-8') as fh:
            sessions = 'LOCKED' if f'(subpath "{frame.path("sanity_home")}")' in fh.read() else 'UNLOCKED'
    except OSError:
        sessions = 'LOCKED'
    try:
        database = 'UNLOCKED' if os.stat(frame.path('master_mark')).st_uid == 0 else 'LOCKED'
    except OSError:
        database = 'LOCKED'
    return {'folders': folders, 'sessions': sessions, 'database': database, 'open': folders == sessions == database == 'UNLOCKED'}


def presses():
    """THE OFFICE'S OWN PRESSES (settings root_shape presses): its folder, its tools, how long each may wait."""
    conf = frame.SETTINGS['root_shape']['presses']
    return {**conf, 'folder': conf['folder'].replace('{instance}', frame.INSTANCE)}


def busy():
    return bool(RUNNING) and RUNNING[-1].poll() is None


def press(which):
    """ONE PRESS, THE OFFICE'S OWN (the owner 2026-10-26: "make a new everythign under replica"): sudo in a terminal this page
    holds, so his fingerprint answers (his own sudo setup), then his own tool: master lock | master unlock | reseal all; what
    the terminal says goes to the office's presses folder. One at a time; a press nobody answers ends after its wait. Only he
    presses it. -> its log's path, or None while another press runs."""
    import fcntl
    import subprocess
    import termios
    import threading
    conf = presses()
    tool = {'lock': (conf['master'], 'lock'), 'unlock': (conf['master'], 'unlock'), 'reseal': (conf['reseal'], 'all')}[which]
    if busy():
        return None
    os.makedirs(conf['folder'], exist_ok=True)
    log = os.path.join(conf['folder'], f"{'reseal_all' if which == 'reseal' else 'master_' + which}_{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.log")
    head, tail = os.openpty()

    def own_terminal():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    run = subprocess.Popen(['/usr/bin/sudo', '-k', '-p', 'REPLICA password (the fingerprint was not taken): ', *tool], stdin=tail, stdout=tail, stderr=tail,
                           preexec_fn=own_terminal, close_fds=True)
    os.close(tail)
    RUNNING[:] = [run]
    wait = conf['wait']['reseal' if which == 'reseal' else 'master']

    def keep():
        clock = threading.Timer(wait, lambda: run.poll() is None and run.kill())
        clock.daemon = True   # never holds the process open
        clock.start()
        with open(log, 'ab') as out:
            while True:
                try:
                    chunk = os.read(head, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                out.write(chunk)
                out.flush()
        os.close(head)
    threading.Thread(target=keep, daemon=True).start()
    return log


def reseal_state():
    """PIN AND RESEAL'S LAST RESULT, EACH STEP FROM WHERE IT KEEPS IT (the owner reseals in his terminal or from a page, and either way each
    step leaves its own record, the same for every office: settings reads vault_seals, spine_seal, pin_ledger, moire_baseline): the vault
    SEALED by its newest owner seal, the spine SEALED by the Judge's signed seal, the pin PINNED by the ledger's last entry, the moire RESET by
    its baseline; a press made from this office's page newer than a step's record says its own word for it (NOT SEALED, ...); None for a
    step with no record yet; 'busy' while a press runs. Read only."""
    import json as _json
    import sqlite3
    out = {k: None for k, _said in RESEAL_STEPS}
    out['busy'] = busy()
    at = {}

    def stamp(path):
        try:
            return os.path.getmtime(path)
        except OSError:
            return None
    try:
        con = sqlite3.connect(f"file:{frame.path('vault_seals')}?mode=ro", uri=True)
        try:
            row = con.execute('SELECT MAX(sealed_at) FROM users_vault_owner_seals').fetchone()
        finally:
            con.close()
        if row and row[0]:
            out['vault'], at['vault'] = 'SEALED', datetime.datetime.fromisoformat(row[0]).timestamp()
    except (sqlite3.Error, ValueError, OSError):
        pass
    if stamp(frame.path('spine_seal')) and stamp(frame.path('spine_seal') + '.sig'):
        out['spine'], at['spine'] = 'SEALED', stamp(frame.path('spine_seal'))
    try:
        with open(frame.path('pin_ledger'), encoding='utf-8') as fh:
            last = [ln for ln in fh.read().splitlines() if ln.strip()][-1]
        when = _json.loads(last).get('at') or ''
        out['pin'], at['pin'] = 'PINNED', datetime.datetime.fromisoformat(when.replace('Z', '+00:00')).timestamp() if when else stamp(frame.path('pin_ledger'))
    except (OSError, IndexError, ValueError):
        pass
    if stamp(frame.path('moire_baseline')):
        out['moire'], at['moire'] = 'RESET', stamp(frame.path('moire_baseline'))
    folder = presses()['folder']
    try:
        logs = sorted(n for n in os.listdir(folder) if n.startswith('reseal_all_') and n.endswith('.log'))
        newest = os.path.join(folder, logs[-1])
        with open(newest, encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
        pressed = os.path.getmtime(newest)
    except (OSError, IndexError):
        return out
    for key, said_ in RESEAL_STEPS:   # a press from this page newer than the step's own record: its own word
        words = [ln[len(said_):].strip() for ln in lines if ln.startswith(said_) and ln[len(said_):].strip().isupper()]
        if words and pressed > (at.get(key) or 0):
            out[key] = words[-1]
    return out
