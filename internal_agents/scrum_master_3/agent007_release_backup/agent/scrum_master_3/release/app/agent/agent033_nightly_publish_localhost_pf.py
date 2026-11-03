"""ROW 033 PUBLISH LOCALHOST PF (D THE NIGHTLY, nightly 01:00): THE PUBLISH SUCCEEDED OR NOT (the owner 2026-10-23:
"a publish is a success or not"). Its light is the publish on this laptop alone: the publish steps step13 to step18 of
the newest night (or those steps run again since the night began), read by the one night reader (shared_night): pass
is green, FAIL or never ran is red with his one step, the publish steps alone by hand; no night on file the same
step, never the whole chain (the owner 2026-10-24). The sync (moved here from the old row 029 SYNC LOCALHOST, PART_D 2026-10-21) still runs from this file
and writes its own runs, but it is WORDS in this row, never its light: nothing here is held on a chain or a sync."""
# THE SYNC, as it was written in the old sync part (the owner's words of 2026-10-12 stand in the old file's head and in his
# memory; the names of the two accounts are never written in this file's code).
#
# WHAT IT IS. The daily rehearsal of the swap's data move, for the two accounts that stand for all. A side is brought
# level with the live side by steps we already ran by hand, one after the other, each with a clock:
#
#     snapshot   the NAMED ACCOUNTS' records READ from the live side, never written, NEVER A WHOLE DATABASE (the owner
#                2026-10-23: "we are not copying whole databases"): the one step that reaches out. Its remote command is
#                BUILT HERE from fixed parts (a database opened read only; of it only the tables of the named accounts,
#                '<account>_...', and the rows of the declared shared tables whose account column is a named account,
#                written out as text); the accounts come from the loop's own profiles (outside the platform), the
#                settings give only where to reach, which files and which shared tables, and all is held to an allow
#                list. Nothing of it is taken as a command.
#     round      the import-compare loop on a scratch copy, from that snapshot (the proven scripts, called where they
#                live outside the workspace, never copied in)
#     compare    the loop's own result, read: rows missing, extra and different must each be 0, every record exact.
#                Anything else is red, with the counts.
#     apply      the scratch copy's result put on the side. A STEP WITH NO COMMAND IS NOT BUILT and the run stops there
#                and says so: a side is never left half applied.
#
# WHAT IT IS NOT. It is not ECHO. ECHO (the tower's steps 5, 6 and 16: LARRY LLM's publish structure) makes every
# account's TABLES fit the build's schemas and moves no record from one platform to another. The sync moves two accounts'
# RECORDS and changes no structure.
#
# THE LIVE SIDE FOLLOWS THE SWITCH (the swap's own record, swaps.jsonl: _live()): today it is read from one slot, after the swap from the other,
# with nothing typed. Only the snapshot may name it; any other step that names it, or any tool that reaches out, is
# refused. No account's name or key is written here or in the settings: the loop's own profiles, outside the platform,
# know which accounts it brings.
#
# ONE AT A TIME (its own lock), never in the cool down, never while a chain of the tower runs. Its result of the day is
# a run of its side's row (row_runs, through the one door: localhost is row 023, b_rnd is row 024), written 'running: ...'
# as it begins and green ('exact: ...') or red ('stopped at ...') as it ends. A row's own look at it always begins
# 'the sync ' or 'publish: ' (a look's own), so a look is never taken for the sync. The Scrum Master reads it and starts
# nothing. Row 024 PUBLISH B RND and row 029 THE SWAP read those runs from row_runs, never from this file's code.
#
#     python -m agent.agent033_nightly_publish_localhost_pf check | localhost | b_rnd | compare <side>
import datetime
import fcntl
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

from agent import shared_where as where   # his places: every file he reads, named in settings.json
from agent import shared_schedule as schedule   # the clock, a row's word, the cool down
from agent import shared_store as store   # the one door
from agent import shared_words as words   # what is gone, cut
from agent import shared_native as native   # the tower's lock file: whether a chain runs
from agent import shared_night as night   # the night's own files, read by the one reader (N9)
from agent import shared_chunks as chunks       # THE 3 MINUTE RULE (the owner 2026-10-23): his one step last, or held while a run clears it
from agent import shared_carry as carry          # the carry's result file read for its words (never a bare brace)

DEFAULTS = {'sides': {}, 'steps': {}}   # a workspace whose settings hold no sync yet: nothing runs
CONF = where.SETTINGS.get('sync', DEFAULTS)
WORKSPACE = where.WORKSPACE
REACHES = (('gcloud', 'compute', 'ssh', '{slot}', '--zone', '{zone}', '--command'),
           ('gcloud', 'compute', 'ssh', '{slot}', '--project', '{project}', '--zone', '{zone}', '--command'))   # THE ONLY WAYS OUT: exactly these words, in this order
REMOTE = '''python3 -c "
import sqlite3,sys
Q=chr(39)
d=sys.argv[1]
A=[x[2:] for x in sys.argv[2:] if x[:2]=='a:']
R=[x[2:].split('.') for x in sys.argv[2:] if x[:2]=='r:']
if not A:
    sys.exit('no account named: nothing is read')
c=sqlite3.connect('file:'+d+'?mode=ro',uri=True)
m=dict(c.execute('SELECT name,sql FROM sqlite_master WHERE type=? AND sql IS NOT NULL',('table',)).fetchall())
def L(v):
    if v is None:
        return 'NULL'
    if isinstance(v,(int,float)):
        return repr(v)
    if isinstance(v,bytes):
        return 'X'+Q+v.hex()+Q
    return Q+str(v).replace(Q,Q+Q)+Q
n=[0,0]
def one(t,w,p):
    print(m[t]+';')
    for r in c.execute('SELECT * FROM ['+t+']'+w,p):
        print('INSERT INTO ['+t+'] VALUES('+','.join(L(v) for v in r)+');')
        n[1]+=1
    for (i,) in c.execute('SELECT sql FROM sqlite_master WHERE type=? AND tbl_name=? AND sql IS NOT NULL',('index',t)):
        print(i+';')
    n[0]+=1
print('BEGIN TRANSACTION;')
for t in sorted(m):
    if any(t.startswith(a+'_') for a in A):
        one(t,'',())
for t,k in R:
    if t in m and not any(t.startswith(a+'_') for a in A):
        one(t,' WHERE ['+k+'] IN ('+','.join('?'*len(A))+')',A)
print('COMMIT;')
sys.stderr.write('%d tables, %d rows'%tuple(n))
" '''   # the whole of what runs on the live side: one database opened READ ONLY; of it only the named accounts' own tables and their rows of the declared shared tables, written out as text. NEVER A WHOLE DATABASE: no account named, nothing is read
ACCOUNT = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*')       # an account's key as the live side names it: no space, no quote, nothing a shell reads
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')             # a shared table and its account column
WORD = re.compile(r'[a-z0-9][a-z0-9-]*')                 # a slot, a zone, a project
PATH = re.compile(r'/[A-Za-z0-9_./-]+\.db')              # a database's place on the live side: no space, no quote, nothing a shell reads
OUTWARD = re.compile(r'\b(gcloud|ssh|scp|rsync|sftp|curl|wget|nc|gsutil)\b')   # a step that is not the snapshot never reaches out
COUNTS = ('missing', 'extra', 'field_differences')


def _st(folder=None):
    """THE ONE DOOR: his database (store.door()), or a check's own scratch instance when it names one."""
    if folder:
        return store.Store(folder)
    return store.door()


ROW = 33                                       # its number in schemas/rows.json
SIDES = {'localhost': 33, 'b_rnd': 35}         # whose row a side's run is: PUBLISH LOCALHOST PF (033), PUBLISH B RND (035)


MINE = 'the sync '                                                     # a sync word begins so
LOOK = 'publish: '                                                     # every line a row's own look writes begins so (rows 023, 024)
SYNC_SAYS = ('running: ', 'exact: ', 'stopped at ')   # THE SYNC'S OWN WORDS (_text): only a run that says one of them is the sync's (the row's number was another row's before 2026-10-21)
NOT_THE_SYNC = (MINE, LOOK, 'held: ', 'he could not read it', 'its program ')   # the looks' own runs, his hold, a raised look, the round's reds


def _text(rec):
    """A side's run text: running, exact with the counts, or where it stopped and why."""
    if not rec.get('ended'):
        return f"running: {rec['side']} began"   # never the bare 'running' a look's own start line says
    if rec.get('ok'):
        return f"exact: {rec.get('counts', {}).get('records', 0)} records, 0 missing, 0 extra, 0 different"
    last = (rec.get('steps') or [{}])[-1]
    return f"stopped at {rec.get('stopped_at') or 'the compare'}: {last.get('why', '')}"


def _keep(side, rec, folder=None):
    """A side's run written through the door (row_runs of its side's row, upserted on its start), what is gone cut first."""
    state = 'running' if not rec.get('ended') else 'green' if rec.get('ok') else 'red'
    _st(folder).run(SIDES[side], rec['started'], rec.get('ended') or None, state, words.clean(_text(rec)))


def result(day, side, folder=None):
    """A side's newest sync run of a day, read from row_runs ({} when it has not begun): {started, ended, state, text,
    ok, exact}; ok and exact only for a green 'exact' run (the sync writes green only when every step ran and the
    compare was exact). A look's own lines (MINE, a raised look, the round's reds, a look's bare start line) are not
    the sync's."""
    mine = [r for r in _sync_runs(side, folder) if schedule._in(day, r.get('started'))]
    return _rec(max(mine, key=lambda r: datetime.datetime.fromisoformat(r['started']))) if mine else {}   # its newest, whatever zone each start was written in


def _sync_runs(side, folder=None):
    """Every sync run of a side in row_runs, of any day: a look's own lines (MINE, a raised look, the round's reds, a
    look's bare start line) are not the sync's."""
    try:
        runs = _st(folder).runs(row=SIDES[side])
    except (OSError, ValueError, KeyError):
        return []
    return [r for r in runs if not str(r.get('text') or '').startswith(NOT_THE_SYNC) and str(r.get('text') or '').startswith(SYNC_SAYS)
            and not (r['state'] == 'running' and (r.get('text') or '') == 'running')]


def _rec(r):
    good = r['state'] == 'green' and bool(r.get('ended')) and str(r.get('text') or '').startswith('exact')
    return {'started': r['started'], 'ended': r.get('ended') or '', 'state': r['state'], 'text': r.get('text') or '', 'ok': good, 'exact': good}


def newest(side, folder=None):
    """A SIDE'S NEWEST SYNC, LIVE (the owner 2026-10-22: "not daily and not hourly only live current data.. that is what
    active monitoring means"): -> (its newest finished run, its newest run still going when that began after it), each
    a result() record or {}, of whatever day."""
    mine = sorted(_sync_runs(side, folder), key=lambda r: datetime.datetime.fromisoformat(r['started']))
    done = [r for r in mine if r['state'] != 'running' and r.get('ended')]
    going = [r for r in mine if r['state'] == 'running' or not r.get('ended')]
    last = _rec(done[-1]) if done else {}
    on = _rec(going[-1]) if going and (not last or datetime.datetime.fromisoformat(going[-1]['started']) > datetime.datetime.fromisoformat(last['started'])) else {}
    return last, on


class Refused(Exception):
    """The sync does not start, or a step is not allowed: said, never worked round."""


class Lock:
    """ONE SYNC AT A TIME on this laptop: a lock file of its own beside its logs (outside sanity; a check's: in its own
    folder), opened through no link. A lock is not a record."""

    def __init__(self, folder=None):
        self.path = os.path.join(folder, 'sync.lock') if folder else store.door().log_path('sync', 'sync.lock')

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.fh = os.fdopen(os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600), 'r+')
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.fh.close()
            raise Refused('another sync is running')
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()


def _live():
    """WHERE THE SWITCH POINTS, read from the swap's own record (settings reads: swaps, global_config), never from the
    platform's code: the slot of the last flip that ended OK (result committed), and before any flip the declared
    starting state (global_config tower.swap.start). Never a guess: a log that is gone after a flip was logged (its
    .kept mark is there), or a last flip whose way back failed, raises; so does a switch that points at no one of the
    two slots (tower.sprint.slots)."""
    with open(where.path('global_config'), encoding='utf-8') as fh:
        tower = json.load(fh)['tower']
    swap, slots, log = tower['swap'], tower['sprint']['slots'], where.path('swaps')
    try:
        with open(log, encoding='utf-8') as fh:
            flips = [json.loads(x) for x in fh if x.strip()]
    except FileNotFoundError:
        if os.path.exists(log + '.kept'):
            raise ValueError("the swap's log is gone but a flip was logged once: where the switch points is not known from the record")
        flips = []
    moved = [r for r in flips if r.get('result') in ('committed', 'rolled back', 'ROLLBACK FAILED')]
    if moved and moved[-1]['result'] == 'ROLLBACK FAILED':
        raise ValueError(f"the last flip (to {moved[-1].get('to')}) failed and its way back failed: where the switch points is not known from the record")
    last = next((r for r in reversed(flips) if r.get('result') == 'committed' and r.get('to') in swap.get('slots', {})), None)
    live = last['to'] if last else swap.get('start')
    if live not in slots or len(slots) != 2:
        raise ValueError(f'the switch points at {live!r}: not one of the two slots {list(slots)} (tower.swap.start, tower.sprint.slots)')
    return live


# ---------------------------------------------------------------- the one step that reaches out

def reach(conf, live):
    """The words that reach the live side, made from the allow list alone: the settings pick ONE of REACHES by its
    shape and give a zone (and a project); the slot is the switch's, never the settings'."""
    given = tuple(conf.get('reach') or ())
    if given not in REACHES:
        raise Refused('the snapshot may reach the live side in the listed ways only')
    parts = {'slot': live, 'zone': conf.get('zone', ''), 'project': conf.get('project', '')}
    for name in ('slot', 'zone') + (('project',) if '{project}' in given else ()):
        if not WORD.fullmatch(str(parts[name])):
            raise Refused(f'the snapshot: no lawful {name}')
    return [w.format(**parts) for w in given]


def _load(text_path, to):
    """A database written out as text, made a database again in a new file. The counters of its numbered tables come
    last (written out first, they name tables that are not there yet). Whole or not at all."""
    with open(text_path, encoding='utf-8') as fh:
        text = fh.read()
    lines = text.splitlines(keepends=True)
    late = [l for l in lines if 'sqlite_sequence' in l.split('(', 1)[0]]
    body = ''.join(l for l in lines if l not in late)
    if 'COMMIT;' not in body:
        raise OSError('the text of the database did not come whole')
    os.makedirs(os.path.dirname(to), exist_ok=True)
    db = sqlite3.connect(to + '.new')
    try:
        db.executescript(body)
        db.executescript(''.join(late))
        db.commit()
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise OSError('the database made from the text is not whole')
    finally:
        db.close()
    os.replace(to + '.new', to)
    return os.path.getsize(to)


def accounts(conf):
    """THE ACCOUNTS THE SYNC BRINGS, read from the loop's own profiles (outside the platform: no account's key is written
    in this file or in the settings): conf accounts.from (a JSON file of profiles) and accounts.field (the key of each
    profile that names its account on the live side). -> the keys, sorted. None found, or one that is not a lawful key:
    Refused (the snapshot never reads a database without the accounts it is for)."""
    where_from = (conf.get('accounts') or {}).get('from')
    field = (conf.get('accounts') or {}).get('field')
    if not where_from or not field:
        raise Refused('the snapshot names no account (sync.steps.snapshot.accounts): it reads the named accounts only, never a whole database')
    try:
        with open(os.path.expanduser(str(where_from)), encoding='utf-8') as fh:
            profiles = json.load(fh)
    except (OSError, ValueError) as e:
        raise Refused(f'the accounts could not be read from the loop\'s profiles: {type(e).__name__}')
    keys = sorted({str(p[field]) for n, p in profiles.items() if not n.startswith('_') and isinstance(p, dict) and p.get(field)})
    if not keys:
        raise Refused('the loop\'s profiles name no account: nothing is read')
    for k in keys:
        if not ACCOUNT.fullmatch(k):
            raise Refused('the loop\'s profiles name an account that is not a lawful key')
    return keys


def snap_folder(conf, day):
    """The snapshot's folder of the day, in his one scratch folder. -> path"""
    root = os.path.expanduser(str(conf['root']))
    if root.startswith('{scratch}'):   # a value not yet filled (as settings.json writes it): his one scratch folder
        root = where.SCRATCH + root[len('{scratch}'):]
    return os.path.join(root, day)


def snapshot(conf, day, runner=subprocess.run, live=None):
    """THE NAMED ACCOUNTS READ FROM THE LIVE SIDE, NEVER WRITTEN, NEVER A WHOLE DATABASE (the owner 2026-10-23: "we are
    not copying whole databases"): of each declared database, opened read only there, only the tables of the named
    accounts and their rows of its declared shared tables (shared_rows: {database: {table: account column}}) written out
    as text, made a database again here in a new folder of the day. -> (the folder, lines)."""
    paths = conf.get('databases') or {}
    if not paths:
        raise Refused('the snapshot: no database is declared')
    keys = accounts(conf)
    shared = conf.get('shared_rows') or {}
    words = reach(conf, live or _live())
    root = snap_folder(conf, day)
    said = []
    for local, remote in paths.items():
        if not PATH.fullmatch(remote) or '..' in remote or not re.fullmatch(r'[A-Za-z0-9_-]+(/[A-Za-z0-9_.-]+)*\.db', local) or '..' in local:
            raise Refused(f'the snapshot: {local} is not a lawful place for a database')
        rows = shared.get(local) or {}
        if not all(NAME.fullmatch(str(t)) and NAME.fullmatch(str(k)) for t, k in rows.items()):
            raise Refused(f'the snapshot: a shared table of {local} is not a lawful name')
        args = ' '.join([remote] + [f'a:{k}' for k in keys] + [f'r:{t}.{k}' for t, k in sorted(rows.items())])
        text = os.path.join(root, local + '.sql')
        os.makedirs(os.path.dirname(text), exist_ok=True)
        with os.fdopen(os.open(text, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600), 'w', encoding='utf-8') as fh:
            done = runner(words + [REMOTE + args], stdout=fh, stderr=subprocess.PIPE, text=True, timeout=int(conf.get('minutes', 20)) * 60)
        if done.returncode != 0:
            raise OSError(f"{local} could not be read from the live side (exit {done.returncode}): {(done.stderr or '').strip()[-160:]}")
        size = _load(text, os.path.join(root, local))
        os.remove(text)
        said.append(f"{local} · {(done.stderr or '').strip()[-60:]} · {size:,} bytes · read only, the named accounts only")
    return root, said


# ---------------------------------------------------------------- the steps that stay here

def lawful(step, live):
    """A step that is not the snapshot: its words and its environment never name the live side and never reach out."""
    words = ' '.join([*step.get('command', []), *(f'{k}={v}' for k, v in (step.get('env') or {}).items())])
    if OUTWARD.search(words):
        raise Refused('only the snapshot reaches out: this step names a tool that leaves the laptop')
    if live and re.search(rf'(?<![A-Za-z0-9-]){re.escape(live)}(?![A-Za-z0-9-])', words):
        raise Refused('only the snapshot names the live side')


def exact(files):
    """THE COMPARE'S OWN RESULT, READ: every module of every result file, rows missing, extra and different each 0 and
    every expected record matched exactly. -> (exact, counts). A file that is not there or cannot be read is not exact."""
    counts = {'records': 0, 'missing': 0, 'extra': 0, 'different': 0, 'unread': 0}
    for path in files:
        try:
            with open(path, encoding='utf-8') as fh:
                found = json.load(fh)
            rows = [r for r in found.values() if isinstance(r, dict) and 'expected_records' in r]
            if not rows:
                raise ValueError('no module in it')
            for r in rows:
                counts['records'] += int(r['expected_records'])
                counts['missing'] += int(r['missing']) + max(0, int(r['expected_records']) - int(r['matched']))
                counts['extra'] += int(r['extra'])
                counts['different'] += int(r['field_differences']) + (int(r['matched']) - int(r['matched_exact']))
        except (OSError, ValueError, KeyError, TypeError):
            counts['unread'] += 1
    return bool(files) and not any(counts[k] for k in ('missing', 'extra', 'different', 'unread')) and counts['records'] > 0, counts


def _fill(value, words):
    return os.path.expanduser(str(value).format(**words))


def run(side, now=None, folder=None, runner=subprocess.run, cooling=None, building=None, live=None):
    """ONE SIDE BROUGHT LEVEL, step by step, its record written as it begins and as it ends. It never starts in the cool
    down or while a chain of the tower runs; a step that is not built, not lawful, red or past its clock stops it
    there. -> its record."""
    day = schedule.cycle(now)
    if side not in CONF['sides']:
        raise Refused(f'{side} is no side of the sync')
    if schedule.cool(now, building) if cooling is None else cooling:
        raise Refused('the cool down is on: nothing starts before the nightly build')
    if native.running() if building is None else building:
        raise Refused('a chain of the tower is running')
    live = live or _live()
    given = now is not None
    now = schedule._now(now)
    clock = (lambda: now.isoformat(timespec='seconds')) if given else store.stamp   # a run's times as the row keeps them; a check's moment when it gives one
    rec = {'side': side, 'day': day, 'started': clock(), 'ended': '', 'ok': None, 'exact': False, 'counts': {}, 'steps': [], 'stopped_at': ''}
    words = {'n': 'sync' + day.replace('-', ''), 'day': day, 'snap': ''}
    with Lock(folder):
        _keep(side, rec, folder)
        for name in CONF['sides'][side]:
            began = time.monotonic()
            ok, why = _one(name, words, rec, day, runner, live, folder)
            rec['steps'].append({'step': name, 'ok': ok, 'seconds': round(time.monotonic() - began, 1), 'why': why})
            if not ok:
                rec['stopped_at'] = name
                break
        rec['ended'] = clock()
        rec['ok'] = not rec['stopped_at'] and rec['exact']   # level means every step ran AND the compare was exact
        _keep(side, rec, folder)
    return rec


def _last_words(out, err=''):
    """A command's last words: the last line that says something (a letter or a digit in it), stderr first, then stdout;
    a JSON answer's own 'error' or 'why' when it has one (the reader 2026-10-23: a last line of "}" says nothing)."""
    carried = carry.from_output(out)   # the carry's result holds accounts: their words (the owner 2026-10-23 21:35: never a bare brace)
    if carried:
        return carried[:300]
    for text in (err, out):
        text = (text or '').strip()
        if not text:
            continue
        if text.startswith('{'):
            try:
                got = json.loads(text)
                for key in ('error', 'why', 'stopped', 'message', 'said'):
                    if isinstance(got, dict) and got.get(key):
                        return str(got[key])[:200]
            except ValueError:
                pass
        for line in reversed(text.splitlines()):
            if re.search(r'[A-Za-z0-9]', line):
                return line.strip()[:200]
    return ''


def _one(name, words, rec, day, runner, live, folder, extra=None):
    """ONE STEP OF A SIDE, run: its own kind (needs, snapshot, compare, command) said as (ok, why); a compare's
    counts kept in rec; extra: more of the command's environment (one step run alone: its accounts). -> (ok, why)"""
    step, why, ok = CONF['steps'].get(name) or {}, '', False
    try:
        if name.startswith('needs:'):   # this side stands on another's exact result of the same day
            other = result(day, name[6:], folder)
            ok = bool(other.get('ok') and other.get('exact'))
            why = '' if ok else f'{name[6:]} is not exact today'
        elif step.get('live'):
            words['snap'], said = snapshot(step, day, runner, live)
            ok, why = True, '; '.join(said)[:300]
        elif step.get('results'):
            rec['exact'], rec['counts'] = exact([_fill(p, words) for p in step['results']])
            ok = rec['exact']
            why = ', '.join(f'{k} {v}' for k, v in rec['counts'].items())
        elif not step.get('command'):
            why = f"NOT BUILT: {step.get('why', 'this step has no command yet')}"
        else:
            lawful(step, live)
            done = runner([_fill(w, words) for w in step['command']], cwd=_fill(step.get('cwd') or WORKSPACE, words), capture_output=True, text=True,
                          timeout=int(step.get('minutes', 30)) * 60,
                          env={**os.environ, 'PATH': where.path('job_path') + ':' + os.environ.get('PATH', ''), **{k: _fill(v, words) for k, v in (step.get('env') or {}).items()}, **(extra or {})})
            ok = done.returncode == 0
            why = _last_words(done.stdout) if ok else f"exit {done.returncode}: {_last_words(done.stdout, done.stderr) or 'no words'}"
    except Refused as e:
        why = f'REFUSED: {e}'
    except subprocess.TimeoutExpired:
        why = 'it ran past its minutes and was stopped'
    except (OSError, ValueError, sqlite3.Error) as e:
        why = f'{type(e).__name__}: {e}'[:300]
    return ok, why


STEP_LOG = where.report('sync_steps')   # ONE STEP RUN ALONE (the owner 2026-10-23: "if something takes longer than 3 min break it into chunks"): each its own line, never a run the row judges; named in reports.json like every report (the scrub deletes any other file of his logs: it took this one at 14:59, 23:03 and 23:06 on 2026-10-23)


def follows(side, name, conf=None):
    """THE RESULT READS RIGHT AFTER A STEP in its side's order (a compare: a read of result files, no seconds). A step run
    alone takes them with it, each its own record, so no side waits on a hand for a 0 second piece; the rule stands (the
    steps after a step run alone run alone too: they do, right after, by the same hand). A command step is never taken
    unasked: it costs minutes and takes its own guards. -> [step names]"""
    conf = CONF if conf is None else conf
    order = conf['sides'].get(side) or []
    out = []
    for nxt in order[order.index(name) + 1:] if name in order else []:
        if 'results' not in (conf['steps'].get(nxt) or {}):
            break
        out.append(nxt)
    return out


def run_step(side, name, now=None, folder=None, runner=subprocess.run, cooling=None, building=None, live=None, log=None, accounts=None, follow=True):
    """ONE STEP OF A SIDE RUN ALONE, a chunk of the whole run: the same guards and lock as the whole run, the day's
    snapshot folder for the steps after it, its seconds kept in its own log (STEP_LOG). It never writes the side's
    run: the row judges the whole sync only. accounts: the round or the carry of these accounts only (SYNC_ACCOUNTS: sync_round.sh,
    apply.py; one account alone is a chunk of minutes, the two together the better part of an hour). follow: a step that
    ends OK takes the result reads right after it (follows), each its own record, in rec['followed']. -> its record."""
    day = schedule.cycle(now)
    if side not in CONF['sides']:
        raise Refused(f'{side} is no side of the sync')
    if name not in CONF['sides'][side]:
        raise Refused(f"{name} is no step of {side} ({', '.join(CONF['sides'][side])})")
    if schedule.cool(now, building) if cooling is None else cooling:
        raise Refused('the cool down is on: nothing starts before the nightly build')
    if native.running() if building is None else building:
        raise Refused('a chain of the tower is running')
    if accounts and (name not in ('round', 'carry') or not all(re.fullmatch(r'[a-z]+', a) for a in accounts)):
        raise Refused('accounts are for the round and the carry only, by their profile names')
    live = live or _live()
    snap = snap_folder(CONF['steps']['snapshot'], day) if 'snapshot' in CONF['steps'] else ''
    words = {'n': 'sync' + day.replace('-', ''), 'day': day, 'snap': snap if os.path.isdir(snap) else ''}
    rec = {'side': side, 'day': day, 'step': name, 'accounts': list(accounts or []), 'started': store.stamp(), 'ended': '', 'seconds': None, 'ok': None, 'why': '', 'exact': False, 'counts': {}}
    with Lock(folder):
        began = time.monotonic()
        rec['ok'], rec['why'] = _one(name, words, rec, day, runner, live, folder, {'SYNC_ACCOUNTS': ' '.join(accounts)} if accounts else None)
        rec['seconds'], rec['ended'] = round(time.monotonic() - began, 1), store.stamp()
    with open(log or STEP_LOG, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(rec) + '\n')
    rec['followed'] = []
    for nxt in (follows(side, name) if follow and rec['ok'] else []):
        try:
            rec['followed'].append(run_step(side, nxt, now, folder, runner, cooling, building, live, log, follow=False))
        except Refused as e:
            rec['followed'].append({'side': side, 'step': nxt, 'accounts': [], 'ok': False, 'why': f'did not start: {e}', 'seconds': None})
            break
    return rec


# ---------------------------------------------------------------- what the Scrum Master reads

def held(side='localhost', conf=None):
    """WHY A SIDE CANNOT RUN TO ITS END ('' when it can), read from the settings alone, every step that is not built
    said in the side's order: a snapshot with no database or no account, a step with no command (its own why), a
    compare with no result file, a side it stands on that cannot. Its row stays red, said why (R1: a step that never
    ran is never a green "held"). Never a whole database: the snapshot reads the named accounts only."""
    conf = CONF if conf is None else conf
    out = []
    for name in conf.get('sides', {}).get(side, []):
        step = conf.get('steps', {}).get(name) or {}
        if name.startswith('needs:'):
            other = held(name[6:], conf)
            if other:
                out.append(f'it stands on {name[6:]}, which cannot ({other})')
        elif step.get('live'):
            if not step.get('databases'):
                out.append('the snapshot declares no database (sync.steps.snapshot.databases)')
            if not (step.get('accounts') or {}).get('from'):
                out.append('the snapshot names no account (sync.steps.snapshot.accounts)')
        elif 'results' in step:
            if not step.get('results'):
                out.append(f'{name} names no result file')
        elif not step.get('command'):
            out.append(f"{name} is NOT BUILT: {step.get('why', 'it has no command yet')}")
    return '; '.join(out)


def word(side, day=None, folder=None, now=None):
    """A side's word, read from its own sync runs in row_runs, LIVE (the owner 2026-10-22: "do a full sweep... zero once
    per day rules.. its all live data only for active monitoring"): its newest finished sync of whatever day, judged and
    said with its time and age (exact green, anything else red, its own words); one running now is said first, the newest
    finished one still judged. -> (state, text). R1 (the owner): a side whose sync never ran has no fact: red, said
    plainly, never a green "held" (a setting that keeps it from starting is said after it, never turned into a pass).
    day: kept for its callers, the sync judged is the newest one; its time is in its words (no age rule: the sync is
    words in row 033 since 2026-10-23, its light is the publish)."""
    last, on = newest(side, folder)
    going = f"{MINE}of {side} runs now since {night.ago(on['started'])}; " if on else ''
    if not last:   # no sync ever ended: red, whatever a setting allows or holds
        why = held(side)
        return 'red', going + f'{MINE}of {side} never ran' + (' to its end' if on else '') + (f': it cannot run to its end: {why}' if why else '')
    said = going + f"{MINE}of {side}, the newest ({night.ago(last['started'])}): {last['text']}"
    return ('green' if last['ok'] else 'red'), said


def published(day=None, now=None):
    """THE PUBLISH ON THIS LAPTOP, SUCCEEDED OR NOT (the owner 2026-10-23: "a publish is a success or not"): step13 to
    step18 on localhost pf as the night's own result.json says them, read by the one reader (shared_night, N9), a step
    run again since the night began standing in for the night's; the newest night, whatever its age (its time and age
    are in the words); a chain running now said first (live, the owner 2026-10-22). -> (state, text): pass green,
    "published on localhost pf: ..."; FAIL, never ran, or no night on file red, "not published on localhost pf: ...".
    day: kept for its callers, the night is the newest one."""
    state, said = night.look(ROW, now=now)
    if state == 'green':
        return 'green', 'published on localhost pf: ' + said
    return 'red', 'not published on localhost pf: ' + said


PUBLISH_LINE = chunks.rerun(None, *night.PUBLISH_PF) + ' (the six steps alone: about 10 s, measured 2026-10-25)'   # THE PUBLISH STEPS BY HAND, his one step (the owner 2026-10-23): step13 to step18 on localhost pf


def budget(side='localhost', conf=None):
    """How long a side's whole sync may take, in minutes: the sum of its steps' own minutes (settings sync.steps.*.minutes);
    a step with none counts nothing. -> minutes"""
    conf = CONF if conf is None else conf
    return sum(int((conf.get('steps', {}).get(name) or {}).get('minutes') or 0) for name in conf.get('sides', {}).get(side, []) if not name.startswith('needs:'))


def dead_sync(side='localhost', folder=None, now=None, lock_free=None):
    """A SYNC KILLED MID-RUN (the judge 2026-10-23: 'a sync killed mid-run leaves its running line forever, so the row
    stays held with nothing to clear it'): its newest run says running, yet no sync holds the sync's own lock (Lock: one
    sync at a time on this laptop), or it began longer ago than every step of the side could take (budget). -> words
    or '' when no run says running, or one does and is alive"""
    last, on = newest(side, folder)
    if not on:
        return ''
    minutes = int(((now or datetime.datetime.now(datetime.timezone.utc)) - datetime.datetime.fromisoformat(on['started']).astimezone(datetime.timezone.utc)).total_seconds() // 60)
    if lock_free is None:
        try:
            with Lock(folder):
                lock_free = True   # taken at once: nobody holds it, no sync runs
        except Refused:
            lock_free = False
        except OSError:
            lock_free = None
    most = budget(side)
    if lock_free or (most and minutes > most):
        return (f"{MINE}of {side} died: its run says running since {night.ago(on['started'])}, but "
                + ('no sync holds the sync lock' if lock_free else f'that is past the {most} min its steps could take') + ' (its line was never ended)')
    return ''


def check():
    """THE ROW'S ONE CHECK: THE PUBLISH SUCCEEDED OR NOT (the owner 2026-10-23: "bad code. a publish is a success or
    not"). The light is published() alone; the sync's newest word follows as words (its own time in them), never the
    light. -> (state, text). THE 3 MINUTE RULE: a red says why first, his one step last: the publish steps by hand
    alone (PUBLISH_LINE), also when no night is on file; a chain or a sync at work is words, never the light."""
    day = schedule.cycle()
    state, said = published(day)
    sync = ' · ' + word('localhost', day)[1]   # the sync: words only (the owner 2026-10-23), its own line on his page
    if state != 'red':
        return state, LOOK + said + sync
    n = night.night()
    stopped, where = night.stopped_at(n, brief=True) if n else ('', '')   # the stop by its rows' names: the why above carries their words
    step = PUBLISH_LINE   # its six steps alone, never the whole chain (the owner 2026-10-24), no night on file and a night stopped at the Judge too (the Judge's fault is row 032's words)
    room = chunks.MOST - len(sync) - len(f" · {chunks.HAND}{step}")   # THE SYNC'S WORDS STAY WHOLE (2026-10-24 02:10: a long night why pushed them past the cut): the publish's why is cut first, before them and before the step
    head = LOOK + said
    if len(head) > room:
        head = head[:max(0, room - 1)].rstrip() + '…'
    return chunks.chunk(ROW, 'red', head + sync, step=step)


SYNC_LINE = 'cd ~/virtual_sanity/scrum_master_3/release/app && PYTHONPATH=. WID_ENV=localhost.rnd ~/virtual_workspace/.venv/bin/python -m agent.agent033_nightly_publish_localhost_pf localhost'


def _side(side):
    def go(argv):
        if argv:   # one step alone: <side> <step>
            try:
                rec = run_step(side, argv[0], accounts=argv[1:])
            except Refused as e:
                print(f'the step did not start: {e}', flush=True)
                return 2
            print(f"{'OK ' if rec['ok'] else 'RED'} · {side} {' '.join([rec['step']] + rec['accounts'])} alone · {rec['seconds']} s · {rec['why']}", flush=True)
            for f in rec.get('followed') or []:
                print(f"{'OK ' if f['ok'] else 'RED'} · {side} {f['step']} alone, right after {rec['step']} · {f['seconds']} s · {f['why']}", flush=True)
            return 0 if rec['ok'] and all(f['ok'] for f in rec.get('followed') or []) else 1
        try:
            rec = run(side)
        except Refused as e:
            print(f'the sync did not start: {e}', flush=True)
            return 2
        for s in rec['steps']:
            print(f"{'OK ' if s['ok'] else 'RED'} · {s['step']} · {s['seconds']} s · {s['why']}", flush=True)
        print('LEVEL: exact' if rec['ok'] else f"NOT LEVEL: stopped at {rec['stopped_at'] or 'the compare'}", flush=True)
        return 0 if rec['ok'] else 1
    return go


def compare(argv):
    if len(argv) != 1 or argv[0] not in SIDES:
        print('usage: compare localhost | b_rnd')
        return 2
    state, said = word(argv[0], schedule.cycle())
    print(f'{state} · {said}', flush=True)
    return 1 if state == 'red' else 0


if __name__ == '__main__':
    words.guard()
    sys.exit(store.row_main(ROW, check, sys.argv[1:], more={**{side: _side(side) for side in CONF['sides']}, 'compare': compare}))
