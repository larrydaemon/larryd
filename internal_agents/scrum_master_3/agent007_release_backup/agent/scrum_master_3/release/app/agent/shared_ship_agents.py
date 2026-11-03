"""SHIP AN AGENT FIX TO B BY ITSELF (the owner 2026-10-24: "it needs to approve it and not give me somethign to approve
after it gets resubmitted. im only going to approve brand new agents or agents from outside developers not positive
feedback"). After a request's change to Positive Feedback's agents (~/larryd_agents, settings develop.repo_by_words
"agents") is proven, read CLEAN and committed on hotfix/<id>, the Developer ships it the way the agents went live
before (the controller session 2026-10-24, R-0036/37/40/41):
  1. its branch merged into the repository's main (fast forward, else a merge; a main checkout whose own uncommitted
     edits stand in the way stops it, said);
  2. every changed agent packed as the runtime packs it (larryd bundle, the runtime's intake, its locker hashes);
  3. put in the lockers bucket (agent.larryd, locker.json), submitted to B (the runtime job: submit <key> --slot slot-b);
  4. approved on B's FROST review as the kept SYSTEM owner (ship_approve_b.py: only the review whose name, key and both
     hashes are exactly this build's, nothing else pressed, never a sign out);
  5. made live (golive.sh: that version the bucket's current one, the runtime service restarted) and checked live (the
     bucket's locker.json says this code hash).
ONLY an agent whose card names the developer Positive Feedback AND that the runtime already holds (a key in the bucket
under the same name) is shipped this way. A BRAND NEW agent of Positive Feedback (frost-c5 2026-10-24, R-0044: "its ship must
place it and create its FROST review for the OWNER to approve, never approve it in the session") is placed once (ONE key,
minted the first time and kept in develop.ship.<name>.keys, so a ship again reuses it), put in the bucket and submitted to B,
and its waiting review is found and named, never pressed: it waits for him (finish_new: after his approval on B and his
APPROVE here, golive makes it live). An outside developer's agent is never shipped here.
Every tool, path and name is in settings develop.ship.<name>, never here."""
import json
import os
import re
import subprocess
import tempfile
import time
import uuid

from agent import shared_where as where

PACK = r'''
import json, pathlib, sys, tempfile
runtime_app, project, out = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
sys.path.insert(0, runtime_app)
from larryd import bundle
from core_engine import intake, locker
conf = json.load(open(pathlib.Path(runtime_app) / 'schemas' / 'runtime.json'))['intake']
data, digest = bundle.make(project)
files = intake.check(intake.from_zip(data, conf['most_files'], conf['most_bytes']), conf['most_files'], conf['most_bytes'])
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t) / 'a'
    for rel, b in (files.items() if isinstance(files, dict) else files):
        p = d / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b)
    row = {'name': json.loads((d / 'agent.json').read_text())['name'], 'code_sha256': locker._code_sha256(d), 'manifest_sha256': locker._manifest_sha256(d)}
out.mkdir(parents=True, exist_ok=True)
(out / 'agent.larryd').write_bytes(data); (out / 'locker.json').write_text(json.dumps(row))
print(json.dumps(row))
'''

SUBMIT = '''^@^-c@import json, runpy, sys, time
sys.path.insert(0, "runtime/app")
from core_engine import warmup
warmup.warm(warmup.hosts(json.load(open("runtime/app/schemas/runtime.json"))["slots"]))
sys.argv = ["runtime/app/web/app.py", "submit", "{key}", "--slot", "{slot}"]
try:
    runpy.run_path("runtime/app/web/app.py", run_name="__main__")
finally:
    sys.stdout.flush(); time.sleep(5)'''


def conf(name='agents'):
    """settings develop.ship.<name>, its paths made whole"""
    got = dict(((where.SETTINGS.get('develop') or {}).get('ship') or {}).get(name) or {})
    for k in ('runtime_app', 'python', 'approver_python', 'kept_owner', 'golive', 'keys'):
        if got.get(k):
            got[k] = os.path.abspath(os.path.expanduser(got[k]))
    return got


def _env():
    return {**os.environ, 'PATH': where.path('job_path') + ':' + os.environ.get('PATH', ''), 'CLOUDSDK_CORE_DISABLE_PROMPTS': '1'}


def _run(cmd, timeout=600, cwd=None):
    """-> (exit, what it said); a command that could not run or ran past its clock: (None, why)"""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_env(), cwd=cwd)
    except subprocess.TimeoutExpired:
        return None, f'{os.path.basename(cmd[0])} ran past {timeout} s'
    except OSError as e:
        return None, f'{os.path.basename(cmd[0])} could not run ({type(e).__name__})'
    return done.returncode, (done.stdout or '') + (done.stderr or '')


def _git(root, *args):
    return _run(['git', '-C', root, *args], 120)


def changed_agents(root, base, tip):
    """The agent folders the branch changed since it left base (three dot): every top folder holding agent/agent.json."""
    code, said = _git(root, 'diff', '--name-only', '--no-renames', f'{base}...{tip}')
    if code != 0:
        return []
    names = sorted({p.split('/')[0] for p in said.splitlines() if '/' in p})
    return [n for n in names if os.path.isfile(os.path.join(root, n, 'agent', 'agent.json'))]


def test_url(c, root, folders):
    """THE PAGE HE TESTS ON (frost-c5 2026-10-24, the owner: "how can the test link be on A production?"): the first
    changed agent's card screen on B (develop.ship.<name>.test_page). -> the address, or ''"""
    for folder in folders:
        try:
            with open(os.path.join(root, folder, 'agent', 'agent.json'), encoding='utf-8') as fh:
                screen = str(((json.load(fh).get('card') or {}).get('screen')) or '')
        except (OSError, ValueError):
            continue
        if screen and c.get('test_page') and '/' in screen and ' ' not in screen:
            return c['test_page'].format(screen=screen.strip('/'))
    return ''


def held_keys(c):
    """{agent name: runtime key} of every agent the lockers bucket holds (its locker.json's name)."""
    code, said = _run(['gcloud', 'storage', 'ls', c['bucket'].rstrip('/') + '/'], 120)
    if code != 0:
        raise RuntimeError(f'the lockers bucket could not be listed: {said.strip()[-200:]}')
    out = {}
    for line in said.split():
        key = line.rstrip('/').rsplit('/', 1)[-1]
        if not key.startswith('MAGT_'):
            continue
        code, body = _run(['gcloud', 'storage', 'cat', f"{c['bucket'].rstrip('/')}/{key}/locker.json"], 60)
        try:
            out[json.loads(body)['name']] = key
        except (ValueError, KeyError, TypeError):
            continue
    return out


def live_row(c, key):
    """The bucket's current locker.json for a key, or {}."""
    code, body = _run(['gcloud', 'storage', 'cat', f"{c['bucket'].rstrip('/')}/{key}/locker.json"], 60)
    try:
        return json.loads(body) if code == 0 else {}
    except ValueError:
        return {}


def merge_main(repo, branch, base):
    """The request's branch into the repository's base branch, in its own checkout: a fast forward, else a merge by the
    Developer. -> '' when merged, else why not (the checkout is left as it was)."""
    code, on = _git(repo, 'symbolic-ref', '-q', '--short', 'HEAD')
    if code != 0 or on.strip() != base:
        return f'{repo} is not on {base} (it is on {on.strip() or "no branch"}): not merged'
    code, said = _git(repo, 'merge', '--ff-only', '-q', branch)
    if code == 0:
        return ''
    code, said = _git(repo, '-c', 'user.name=THE DEVELOPER', '-c', 'user.email=developer@localhost', 'merge', '--no-edit', '-q', branch)
    if code == 0:
        return ''
    _git(repo, 'merge', '--abort')
    return f'{branch} did not merge into {base} in {repo}: ' + ' '.join(said.split())[-240:]


def pack(c, project, out):
    """-> {name, code_sha256, manifest_sha256}, the package written in out (agent.larryd, locker.json)"""
    code, said = _run([c['python'], '-I', '-c', PACK, c['runtime_app'], project, out], 300)
    if code != 0:
        raise RuntimeError(f'{os.path.basename(project)} could not be packed: ' + ' '.join(said.split())[-240:])
    return json.loads(said.strip().splitlines()[-1])


def pack_at(c, root, ref, folder, out):
    """The agent as the commit ref has it, packed (git archive of its folder, never the tree's own files). -> its row"""
    with tempfile.TemporaryDirectory(prefix='ship_base_') as t:
        arch = subprocess.run(['git', '-C', root, 'archive', '--format=tar', ref, folder], capture_output=True)
        if arch.returncode != 0:
            raise RuntimeError(f'{folder} could not be read at {ref[:12]}')
        subprocess.run(['tar', '-x', '-C', t], input=arch.stdout, check=True)
        return pack(c, os.path.join(t, folder), out)


def _pending_file(c):
    return (c.get('keys') or '') and c['keys'] + '.pending.json'


def pending(c):
    """{folder: key} of the new agents placed and not yet approved by him (a ship again of one is still his to approve,
    though the bucket now holds its name)."""
    f = _pending_file(c)
    try:
        with open(f, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError, TypeError):
        return {}


def pending_put(c, folder, key=None):
    """One new agent put on the waiting list (key) or taken off it (None, after his approval and its golive)."""
    f = _pending_file(c)
    if not f:
        return
    now = pending(c)
    if key:
        now[folder] = key
    else:
        now.pop(folder, None)
    with open(f + '.new', 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(now, indent=1) + '\n')
    os.replace(f + '.new', f)


def new_key(c, folder, held):
    """THE ONE KEY OF A BRAND NEW AGENT: the bucket's (a place already made under its name), else the kept list's, else
    minted now (the runtime's shape, MAGT_<12 hex>_<4 hex>) and written in the kept list before anything is placed."""
    keys_file = c.get('keys') or ''
    kept = {}
    if keys_file and os.path.isfile(keys_file):
        with open(keys_file, encoding='utf-8') as f:
            kept = json.load(f)
    if kept.get(folder):
        return kept[folder]
    if not keys_file:
        raise RuntimeError('settings develop.ship names no keys list: a new agent\'s key would not be kept')
    h = uuid.uuid4().hex.upper()
    kept[folder] = f'MAGT_{h[:12]}_{h[12:16]}'
    tmp = keys_file + '.new'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(json.dumps(kept, indent=1) + '\n')
    os.replace(tmp, keys_file)
    return kept[folder]


def review_of(c, name, key, row, tries=8, wait=45, seen=None):
    """THE WAITING REVIEW OF THIS BUILD ON B, found and never pressed (ship_approve_b.py without --approve). -> (id, why);
    seen (a dict) is given the approver's last JSON (its card: the card key of this build once approved)"""
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ship_approve_b.py')
    last = ''
    for n in range(tries):
        code, said = _run([c['approver_python'], '-I', tool, '--kept', c['kept_owner'], '--host', c['b_host'], '--ip', c['b_ip'],
                           '--name', name, '--key', key, '--code', row['code_sha256'], '--manifest', row['manifest_sha256']], 300)
        lines = [l for l in said.strip().splitlines() if l.startswith('{')]
        try:
            got = json.loads(lines[-1]) if lines else {}
        except ValueError:
            got = {}
        if seen is not None:
            seen.clear()
            seen.update(got)
        last = str(got.get('why') or ' '.join(said.split())[-200:] or f'exit {code}')
        if last.startswith('list only: #'):
            return last[len('list only: #'):].split()[0], ''
        if n + 1 < tries:
            time.sleep(wait)
    return '', last


def card_put(c, key, card):
    """THE CARD IN THE LOCKER (frost-c5 2026-10-24: the runtime may only read the lockers bucket, so the submit job's own
    card.json write is always denied, and a brand new agent's card never shows in the marketplace): <key>/card.json =
    {"card_key": card}, written with the owner's gcloud only when it is missing or different. card '' keeps a card.json that
    already names one. -> '' when the locker holds the card, else why not"""
    where_ = f"{c['bucket'].rstrip('/')}/{key}/card.json"
    code, body = _run(['gcloud', 'storage', 'cat', where_], 60)
    try:
        now = str(json.loads(body).get('card_key') or '') if code == 0 else ''
    except (ValueError, AttributeError):
        now = ''
    if not card:
        return '' if now.startswith('MAGT_') else 'B showed no card key for it and its locker holds no card.json'
    if not re.fullmatch(r'MAGT_\w+', card):
        return f'the card key {card[:40]!r} is not whole'
    if now == card:
        return ''
    with tempfile.TemporaryDirectory(prefix='card_') as t:
        f = os.path.join(t, 'card.json')
        with open(f, 'w') as fh:
            json.dump({'card_key': card}, fh)
        code, said = _run(['gcloud', 'storage', 'cp', f, where_], 120)
    if code != 0:
        return 'its card.json could not be written: ' + ' '.join(said.split())[-200:]
    code, body = _run(['gcloud', 'storage', 'cat', where_], 60)
    try:
        return '' if code == 0 and json.loads(body).get('card_key') == card else 'its card.json does not read back as written'
    except ValueError:
        return 'its card.json does not read back as written'


def finish_new(c, waiting):
    """AFTER HIS APPROVAL ON B: every new agent the ship left waiting ({name, key, code, manifest, review}) whose review no
    longer waits on B is made live (golive) and checked live. -> (ok, word); not ok while one still waits for him."""
    done = []
    for w in waiting:
        row = {'code_sha256': w['code'], 'manifest_sha256': w['manifest']}
        seen = {}
        still, why = review_of(c, w['name'], w['key'], row, tries=1, seen=seen)
        if still:
            return False, f"{w['name']}: review #{still} still waits for the owner on B"
        if not why.startswith('0 waiting reviews are exactly this build'):   # B not read: never taken for his approval
            return False, f"{w['name']}: B's review page was not read: {why[:160]}"
        miss = card_put(c, w['key'], str(seen.get('card') or ''))
        if miss:
            return False, f"{w['name']}: {miss}"
        code, said = _run([c['golive'], w['key'], w['code'][:8]], 900)
        if code != 0:
            return False, f"{w['name']}: golive did not end well: " + ' '.join(said.split())[-200:]
        if live_row(c, w['key']).get('code_sha256') != w['code']:
            return False, f"{w['name']}: the bucket does not say its code is live after golive"
        if w.get('folder'):
            pending_put(c, w['folder'])
        done.append(f"{w['name']} live on B (review #{w['review']} approved on B, code {w['code'][:12]})")
    return True, 'shipped by itself: ' + '; '.join(done)


def approve(c, name, key, row, tries=8, wait=45, seen=None):
    """THE REVIEW ON B APPROVED as the kept SYSTEM owner (ship_approve_b.py), only this build's. -> (ok, word); seen (a
    dict) is given the approver's JSON (its card: the card key FROST gave)"""
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ship_approve_b.py')
    last = ''
    for n in range(tries):
        code, said = _run([c['approver_python'], '-I', tool, '--kept', c['kept_owner'], '--host', c['b_host'], '--ip', c['b_ip'],
                           '--name', name, '--key', key, '--code', row['code_sha256'], '--manifest', row['manifest_sha256'], '--approve'], 300)
        lines = [l for l in said.strip().splitlines() if l.startswith('{')]
        try:
            got = json.loads(lines[-1]) if lines else {}
        except ValueError:
            got = {}
        if got.get('approved'):
            if seen is not None:
                seen.update(got)
            return True, f"review #{got['approved']} approved on B"
        last = got.get('why') or ' '.join(said.split())[-200:] or f'exit {code}'
        if n + 1 < tries:
            time.sleep(wait)   # the submit lands on B's review a moment after the job
    return False, f'its review on B was not approved: {last}'


def ship(rid, root, spec, branch, log=None, name='agents', new_ok=False):
    """THE WHOLE SHIP of one request's committed change. -> (ok, word); with new_ok a new agent left waiting for him is
    (True, {waiting, word}), else (False, word): a caller that cannot keep it says it is not live yet, never live."""
    log = log if log is not None else []
    c = conf(spec.get('ship') or name)
    if not c.get('bucket'):
        return False, f"settings develop.ship.{spec.get('ship') or name} names no lockers bucket"
    repo, base = spec['repo'], spec['base']
    code, tip = _git(root, 'rev-parse', '--verify', 'HEAD^{commit}')
    tip = tip.strip()
    agents = changed_agents(root, base, tip)
    if not agents:
        return False, 'the change holds no agent folder to ship'
    held = held_keys(c)
    plan = []
    for folder in agents:
        manifest = json.load(open(os.path.join(root, folder, 'agent', 'agent.json'), encoding='utf-8'))
        developer = str((manifest.get('card') or {}).get('developer') or '')
        if developer != c.get('developer', 'Positive Feedback'):
            return False, f"{folder} is {developer or 'no developer'}'s agent, not {c.get('developer')}'s: the owner approves it"
        waits = pending(c).get(folder)
        key = waits or held.get(manifest.get('name'))
        new = bool(waits) or not key
        if new and not waits:   # A BRAND NEW AGENT: placed and submitted, his to approve
            key = new_key(c, folder, held)
        plan.append((folder, manifest['name'], key, new))
    code, began = _git(root, 'merge-base', base, tip)   # the commit this build started from (its base as merged in)
    began = began.strip()
    done, waiting = [], []
    with tempfile.TemporaryDirectory(prefix=f'ship_{rid}_') as work:
        packed = []
        for folder, agent_name, key, new in plan:   # FIRST EVERY AGENT PACKED AND CHECKED, before main moves
            out = os.path.join(work, key)
            row = pack(c, os.path.join(root, folder), out)
            live = live_row(c, key).get('code_sha256')
            if live and live != row['code_sha256'] and began and not new:   # NEVER OVER A FIX SHIPPED OUTSIDE (frost-c5 2026-10-24: pack from the commit that is live, never an older main)
                was = pack_at(c, root, began, folder, os.path.join(work, key + '_base'))
                if live != was['code_sha256']:
                    return False, (f'{agent_name}: the live code {live[:12]} is not the one this build started from ({was["code_sha256"][:12]}): '
                                   'it was shipped outside the Scrum Master; bring that commit into main and build again')
            packed.append((folder, agent_name, key, out, row, live, new))
        why = merge_main(repo, branch, base)   # THEN main, THEN the runtime
        if why:
            return False, why
        log.append(f"{rid}: {branch} merged into {base} in {repo}")
        for folder, agent_name, key, out, row, live, new in packed:
            if new:   # PLACED ONCE, SUBMITTED, ITS REVIEW NAMED, NEVER APPROVED HERE
                if live != row['code_sha256']:
                    for part in ('agent.larryd', 'locker.json'):
                        code, said = _run(['gcloud', 'storage', 'cp', os.path.join(out, part), f"{c['bucket'].rstrip('/')}/{key}/{part}"], 300)
                        if code != 0:
                            return False, f'{agent_name}: {part} could not be put in the lockers bucket: ' + ' '.join(said.split())[-200:]
                    log.append(f'{rid}: {agent_name}, a new agent, placed as {key}, code {row["code_sha256"][:12]}')
                pending_put(c, folder, key)
                review, why = review_of(c, agent_name, key, row, tries=1)
                if not review:
                    _run(['gcloud', 'run', 'jobs', 'execute', c['job'], '--project', c['project'], '--region', c['region'], '--wait',
                          f"--args={SUBMIT.format(key=key, slot=c.get('slot', 'slot-b'))}"], int(c.get('minutes', 40)) * 60)
                    review, why = review_of(c, agent_name, key, row)
                if not review:
                    return False, f'{agent_name}: placed as {key}, but no review of it waits on B: {why}'
                log.append(f'{rid}: {agent_name}: review #{review} waits for the owner on B')
                waiting.append({'folder': folder, 'name': agent_name, 'key': key, 'code': row['code_sha256'], 'manifest': row['manifest_sha256'], 'review': review})
                continue
            if live == row['code_sha256']:
                done.append(f'{agent_name} already live ({row["code_sha256"][:12]})')
                continue
            kept = os.path.join(os.path.expanduser(c.get('backups') or '~/scratch/backup_lockers'), f"{key}_{time.strftime('%Y%m%dT%H%M%S')}")
            os.makedirs(kept, exist_ok=True)
            code, said = _run(['gcloud', 'storage', 'cp', f"{c['bucket'].rstrip('/')}/{key}/*", kept + '/'], 300)   # THE LOCKER AS IT WAS, kept before anything is put over it
            if code != 0:
                return False, f'{agent_name}: its locker could not be backed up first: ' + ' '.join(said.split())[-200:]
            log.append(f'{rid}: {agent_name} locker backed up in {kept}')
            for part in ('agent.larryd', 'locker.json'):
                code, said = _run(['gcloud', 'storage', 'cp', os.path.join(out, part), f"{c['bucket'].rstrip('/')}/{key}/{part}"], 300)
                if code != 0:
                    return False, f'{agent_name}: {part} could not be put in the lockers bucket: ' + ' '.join(said.split())[-200:]
            log.append(f'{rid}: {agent_name} ({key}) put in the lockers bucket, code {row["code_sha256"][:12]}')
            _run(['gcloud', 'run', 'jobs', 'execute', c['job'], '--project', c['project'], '--region', c['region'], '--wait',
                  f"--args={SUBMIT.format(key=key, slot=c.get('slot', 'slot-b'))}"], int(c.get('minutes', 40)) * 60)   # its exit is not the proof (it ends 1 after a good submit): the review on B is
            seen = {}
            ok, word = approve(c, agent_name, key, row, seen=seen)
            if not ok:
                return False, f'{agent_name}: {word}'
            log.append(f'{rid}: {agent_name}: {word}')
            miss = card_put(c, key, str(seen.get('card') or ''))
            if miss:
                return False, f'{agent_name}: {miss}'
            code, said = _run([c['golive'], key, row['code_sha256'][:8]], 900)
            if code != 0:
                return False, f'{agent_name}: golive did not end well: ' + ' '.join(said.split())[-200:]
            if live_row(c, key).get('code_sha256') != row['code_sha256']:
                return False, f'{agent_name}: the bucket does not say the new code is live after golive'
            done.append(f'{agent_name} live on B ({word}, code {row["code_sha256"][:12]})')
    if waiting and not new_ok:
        return False, 'SUBMITTED FOR YOUR APPROVAL ON B: ' + '; '.join(f"{w['name']} review #{w['review']} (key {w['key']}, code {w['code'][:12]})" for w in waiting)
    if waiting:
        return True, {'waiting': waiting, 'word': 'SUBMITTED FOR YOUR APPROVAL ON B: ' + '; '.join(f"{w['name']} review #{w['review']} (key {w['key']}, code {w['code'][:12]})" for w in waiting)
                      + (' · shipped by itself: ' + '; '.join(done) if done else '')}
    return True, 'shipped by itself: ' + '; '.join(done)
