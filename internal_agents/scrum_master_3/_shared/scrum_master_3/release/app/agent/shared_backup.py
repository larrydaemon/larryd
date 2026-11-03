"""HIS OWN BACKUP (the owner 2026-10-25: "the agent needs its own git and backup and this was supsed to be done a long time
ago"): the Scrum Master's code, his checks and his database, copied whole into a folder of their own in his one scratch
folder (~/scratch/scrum_master_3/backups, outside every virtual folder), the newest few kept. The laptop's backup (the tower's, ~/spine_scratch/tower_backups) holds the workspace only.

WHAT ONE BACKUP HOLDS (settings backup), one folder scrum_master_<stamp> under backup.home:
  app.bundle, checks.bundle   his git and his checks' git, every commit (git bundle --all): what was reviewed
  app.tar.gz, checks.tar.gz   the trees as they stand, uncommitted work too: what was live
  scrum_master_3_release.db             his database, copied by sqlite's own backup (never a file copy of a database being written)
  knowledge.db                the knowledge store the same way (row 026: a lost store is put back from it in seconds)
  manifest.json               written LAST: a folder without one is no backup (as the tower's)
WHEN: the daily chain's BACKUP at 00:05, before the night's TAKE IN at 00:10 (settings daily.jobs); and by hand at any time,
before any change lands: agent/run backup. backup.keep: the newest kept, the older ones removed (only his own folders).

RESTORE (by hand, his word): git clone <folder>/app.bundle shows every commit; tar -xzf <folder>/app.tar.gz -C
~/virtual_sanity/scrum_master_3/release puts app/ back as it stood; tar -xzf <folder>/checks.tar.gz -C ~/scratch/tests/scrum_master_3;
the database: the page and the round stopped first, then <folder>/scrum_master_3_release.db over instance/scrum_master_3_release.db.

    python -m agent.shared_backup make     one backup now
    python -m agent.shared_backup list     the backups kept, newest first
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile

from agent import shared_store as store   # his database's place (instance), a moment as a run's time is kept
from agent import shared_knowledge as knowledge   # the knowledge store's place (read by sqlite's backup only)
from agent import shared_where as where   # his app, his office, his settings
from agent import shared_words as words   # guard() at the door

CONF = where.SETTINGS['backup']
NAME = re.compile(r'scrum_master_\d{8}T\d{6}')   # his own folders, the only ones ever removed
MANIFEST = 'manifest.json'
SKIP = ('__pycache__', '.DS_Store')


def home():
    return os.path.expanduser(os.environ.get('SCRUM_MASTER_BACKUPS') or CONF['home'])


def checks():
    return os.path.expanduser(os.environ.get('SCRUM_MASTER_CHECKS') or CONF['checks'])


def _git(repo, *args, run=subprocess.run):
    return run(['git', '-C', repo, *args], capture_output=True, text=True, timeout=120)


def _bundle(repo, to, run=subprocess.run):
    """Every commit of a repository into one file. -> its newest commit, or '' when it has none."""
    head = _git(repo, 'rev-parse', 'HEAD', run=run)
    if head.returncode != 0:
        return ''
    made = _git(repo, 'bundle', 'create', to, '--all', run=run)
    if made.returncode != 0:
        raise OSError(f'git bundle of {repo}: {store.one_line(made.stderr)[-200:]}')
    return head.stdout.strip()


def _dirty(repo, path, run=subprocess.run):
    return bool(_git(repo, 'status', '--porcelain', '--', path, run=run).stdout.strip())


def _tar(folder, to):
    """A tree as it stands (its compilers' folders left out), its own name at the top."""
    with tarfile.open(to, 'w:gz') as t:
        t.add(folder, arcname=os.path.basename(folder), filter=lambda i: None if os.path.basename(i.name) in SKIP else i)


def _database(to, source=None):
    """His database (or the one named) by sqlite's own backup: a copy that is whole even while the round writes."""
    src = sqlite3.connect(f'file:{source}?mode=ro', uri=True) if source else sqlite3.connect(store.door().path)   # the store is only read
    dst = sqlite3.connect(to)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def _sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def kept():
    """Every backup kept, newest first: its manifest and its folder. A folder without a manifest is no backup."""
    out = []
    root = home()
    for name in sorted(os.listdir(root), reverse=True) if os.path.isdir(root) else []:
        if not NAME.fullmatch(name):
            continue
        try:
            with open(os.path.join(root, name, MANIFEST), encoding='utf-8') as fh:
                out.append({**json.load(fh), 'name': name, 'path': os.path.join(root, name)})
        except (OSError, ValueError):
            continue
    return out


def _prune(keep):
    """The older of his own folders removed, the newest keep whole backups left; a folder without a manifest older than the
    newest whole one is removed too (a backup that broke halfway). -> the names removed"""
    whole = [b['name'] for b in kept()]
    stay = set(whole[:keep])
    newest = whole[0] if whole else ''
    gone = []
    for name in os.listdir(home()):
        if NAME.fullmatch(name) and name not in stay and (name in whole or name < newest):
            shutil.rmtree(os.path.join(home(), name))
            gone.append(name)
    return sorted(gone)


SM3 = os.path.dirname(where.OFFICE)   # Scrum Master 3's home: these tools live in its release/ folder
SM3_DB = os.path.join(os.environ.get('REPLICA_INSTANCE') or os.path.join(SM3, 'instance'), 'scrum_master_3.db')   # MOVED 2026-11-03: the office's database in LARRYD RUNTIME INTERNAL's data   # its own database (the office's extras)


def make(now=None, run=subprocess.run):
    """ONE BACKUP NOW. -> its manifest. A backup that breaks halfway leaves no folder and raises."""
    at = (now or datetime.datetime.now(datetime.timezone.utc)).astimezone()
    folder = os.path.join(home(), 'scrum_master_' + at.strftime('%Y%m%dT%H%M%S'))
    os.makedirs(folder)
    try:
        office, tests = SM3, checks()   # SCRUM MASTER 3 ITSELF (its own git at its home), never only these tools
        commits = {'app': _bundle(office, os.path.join(folder, 'app.bundle'), run), 'checks': _bundle(tests, os.path.join(folder, 'checks.bundle'), run)}
        dirty = {'app': _dirty(office, 'app', run), 'checks': _dirty(tests, 'checks', run)}
        _tar(os.path.join(SM3, 'app'), os.path.join(folder, 'app.tar.gz'))
        _tar(where.APP, os.path.join(folder, 'release.tar.gz'))   # its release tools as they stand
        if os.path.isfile(SM3_DB):
            _database(os.path.join(folder, os.path.basename(SM3_DB)), SM3_DB)   # its own extras' database
        _tar(os.path.join(tests, 'checks'), os.path.join(folder, 'checks.tar.gz'))
        _database(os.path.join(folder, 'scrum_master_3_release.db'))
        if os.path.isfile(knowledge.db_file()):
            _database(os.path.join(folder, 'knowledge.db'), knowledge.db_file())
        files = {f: {'bytes': os.path.getsize(os.path.join(folder, f)), 'sha256': _sha(os.path.join(folder, f))} for f in sorted(os.listdir(folder))}
        manifest = {'made_at': at.isoformat(timespec='seconds'), 'commits': commits, 'uncommitted': dirty, 'files': files, 'ok': True}
        with open(os.path.join(folder, MANIFEST), 'w', encoding='utf-8') as fh:   # LAST: only now is it a backup
            json.dump(manifest, fh, indent=1)
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    manifest['removed'] = _prune(int(CONF['keep']))
    return manifest


def said(m):
    size = sum(f['bytes'] for f in m['files'].values())
    left = ', '.join(f"{k} uncommitted" for k, v in m['uncommitted'].items() if v)
    return (f"backup made {m['made_at']}: app {m['commits']['app'][:12] or 'no commit'}, checks {m['commits']['checks'][:12] or 'no commit'}"
            + (f" ({left})" if left else '') + f", {len(m['files'])} files, {size // 1024} KB" + (f" · removed {len(m['removed'])} older" if m.get('removed') else ''))


def main(argv):
    if argv[:1] == ['make']:
        print(f"{store.stamp()[:16]} · {said(make())} · {home()}", flush=True)
        return 0
    if argv[:1] == ['list']:
        for b in kept():
            print(f"{b['name']} · app {b['commits']['app'][:12]} · checks {b['commits']['checks'][:12]} · {b['path']}")
        return 0
    print('usage: python -m agent.shared_backup make | list')
    return 2


if __name__ == '__main__':
    words.guard()
    sys.exit(main(sys.argv[1:]))
