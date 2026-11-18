"""LARRYD SHIP: ONE place-and-approve command for both runtimes (CORE_CLEANUP_IV items 55, 98; the owner: "we want them to work the
same internal and external"). The same steps for every agent; only the target differs:

  1 CLEAN    the agent's folder holds no uncommitted change (what is placed is what is committed)
  2 DOCTOR   larryd doctor (external) or larryd doctor --internal (internal): no problem
  3 PACK     the files the runtime holds. Internal: its agent/ whole, with office.py and the kits its "libs" name (from its agent/,
             else its repository's _office: self-contained, production's shape); external: its agent/ whole (larryd's own bundle)
  4 KEY      the runtime key it is placed under: an office agent's agent.json "key", an internal clean project's place.json "key",
             an external agent's key in the ship lane's keys file (made once)
  5 PLACE    internal: THE LOCKER IN PLACE (ONE SYSTEM, 2026-11-07): the pack written into <the lane's locker>/<name>/agent (the
             one internal locker, ~/virtual_sanity/sanity_agents), then the internal runtime's in-place place of that folder
             (LARRYD_INTERNAL=1 and LARRYD_LOCKER: held where it is, its hashes, then sent to wid, which writes its card and FROST's
             review); no .larryd file. External: its locker in the lockers bucket (hashed by the runtime's own intake), then
             submitted to wid through the runtime's job
  6 APPROVE  in localhost FROST, the ONE waiting review of exactly this key and these two hashes, whatever card key wid minted
             (a first placement's card key is never the runtime key)
  7 PLATFORMS external: EVERY PLATFORM READY, NO PUBLISHING (the owner 2026-11-17: "make larryd ship --go do this and keep in mind we
             have macos and ios if they need it too.. should always be ready with no publishing"): each other platform the lane names
             (production B, ...) gets the same version the same way: the runtime's own submit to that slot (its wid writes its card and its
             FROST's review), then that platform's FROST approves exactly these hashes. The Mac and iPhone apps call no runtime: they reach
             agents through their data home (a slot), so a slot ready is its devices ready
  8 CARD     external: card.json beside the locker: the card key, and each platform's own card (cards: {caller: card key}) merged in,
             so the runtime finds the agent whichever platform calls; then ONE runtime restart per batch, said here, never done here

    larryd ship <the agent's folder>            the plan, step by step: nothing placed, nothing approved
    larryd ship <the agent's folder> --go       do it (the ship lane: frost-cb)

Every outside step is a command it prints before it runs it; a step that fails stops the rest and says why."""
import json
import os
import pathlib
import shlex
import shutil
import tempfile
import subprocess

from . import bundle, doctor, internal, shape

HOME = pathlib.Path.home()
CONFIG = pathlib.Path(os.environ.get('LARRYD_SHIP') or HOME / '.larryd' / 'ship.json')
# THE SHIP LANE'S OWN COMMANDS live in that file, never in this tool (a developer's larryd names no runtime): each is an argv with
# {key}, {pkg}, {root} filled in, and where it runs:
#   {"internal": {"locker": "<the one internal locker>", "place_in_place": {"argv": [..., "place", "{key}", "{folder}", "--kits", "{folder}"],
#                 "cwd": "...", "env": {"LARRYD_INTERNAL": "1", "LARRYD_LOCKER": "<the locker>", ...}}},
#    "external": {"keys": "<the lane's keys file>", "place": {"argv": [...]}, "submit": {"argv": [...], "cwd": "..."},
#                 "card": {"argv": [...]}, "card_there": {"argv": [...]}},
#    "frost": {"python": "...", "cwd": "...", "env": {...}},
#    "platforms": [{"name": "production B", "slot": "slot-b", "submit": {"argv": [..., "{key}", ...]},
#                   "frost": {"remote": ["gcloud", "compute", "ssh", "<box>", ..., "--command"], "python": "...", "cwd": "...", "env": {...}}}]}
# (external "slot" names localhost's own caller, "proof" when unsaid; "card_read" prints card.json, so the platforms' cards merge into it)
# ({folder} is <locker>/<name>/agent; --kits names the folder itself, so the runtime writes no other office.py over the agent's own.)
# internal place answers one JSON line with code_sha256 and manifest_sha256; external place answers "<key> <locker JSON>".


def lane():
    try:
        got = json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        raise Stop(f'this computer is not a ship lane: no {CONFIG} (the lane writes it once)')
    if not isinstance(got, dict):
        raise Stop(f'{CONFIG} is not one JSON object')
    return got


def _cmd(step, **fill):
    """a lane command, its {placeholders} filled -> (argv, cwd, env)"""
    if not isinstance(step, dict) or not isinstance(step.get('argv'), list):
        raise Stop('the ship lane names no command for this step')
    argv = [str(a).format(**fill) for a in step['argv']]
    return argv, (str(pathlib.Path(step['cwd']).expanduser()) if step.get('cwd') else None), {k: str(v).format(**fill) for k, v in (step.get('env') or {}).items()}


class Stop(Exception):
    """a step that cannot go on: its words say why"""


def _run(argv, cwd=None, env=None, timeout=900):
    got = subprocess.run(argv, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True, timeout=timeout)
    return got.returncode, got.stdout, got.stderr


def target_of(root):
    """THE TAG picks the road: its card's "environment" when it carries one, else the old folder-shape rule (internal.is_internal)"""
    return 'internal' if internal.is_internal(root) else 'external'


def clean(root, run=_run):
    """1 CLEAN -> the commit it is placed from. Its own folder AND, for an office agent, the kits it is packed with (its repository's
    _office): what is placed is what is committed, all of it."""
    code, out, err = run(['git', '-C', str(root), 'status', '--short', '--', '.'])
    if code != 0:
        raise Stop(f'not in a git repository: {err.strip()[-200:]}')
    if out.strip():
        raise Stop('it holds uncommitted changes: commit them first (what is placed is what is committed)')
    try:
        card = json.loads((root / shape.AGENT / shape.MANIFEST).read_text())
    except (OSError, ValueError):
        card = {}
    if isinstance(card, dict) and card.get('office'):
        kits = [k for k in ['office'] + list(card.get('libs') or []) if not (root / shape.AGENT / f'{k}.py').is_file()]   # a kit inside agent/ is its own folder's
        code, out, _ = run(['git', '-C', str(root.parent), 'status', '--short', '--', *[f'_office/{k}.py' for k in kits]]) if kits else (0, '', '')
        if out.strip():
            raise Stop(f'a kit it is packed with holds uncommitted changes ({out.strip().splitlines()[0].strip()}): commit it first')
    code, out, _ = run(['git', '-C', str(root), 'log', '-1', '--format=%h', '--', '.'])
    return out.strip()


def check(root, where):
    """2 DOCTOR"""
    problems = internal.check(root) if where == 'internal' else doctor.check(root)
    if problems:
        raise Stop(f'the doctor{" --internal" if where == "internal" else ""} found {len(problems)} problem(s): ' + '; '.join(p.text() for p in problems[:3]))


def files_of(root):
    """3 PACK, internal -> {path inside agent/: bytes}: its agent/ whole (no __pycache__), and office.py and each kit its "libs" name
    that is not inside it yet, from its repository's _office (internal.kit): what the locker holds, self-contained"""
    agent = root / shape.AGENT
    card = json.loads((agent / shape.MANIFEST).read_text())
    files = {}
    for p in sorted(agent.rglob('*')):
        rel = p.relative_to(agent)
        if '__pycache__' in rel.parts or p.is_dir():
            continue
        if p.is_symlink() or not p.is_file():
            raise Stop(f'agent/{rel.as_posix()} is a link or not a plain file: an agent is only its own files')
        files[rel.as_posix()] = p.read_bytes()
    if card.get('office'):
        for name in ['office'] + list(card.get('libs') or []):
            if f'{name}.py' not in files:
                path = internal.kit(root, name)
                if path is None:
                    raise Stop(f'the kit {name}.py is neither in its agent/ nor in its repository\'s _office')
                files[f'{name}.py'] = path.read_bytes()
    return files


def pack(root, where='external'):
    """3 PACK -> (the bytes: the .larryd file (external), or the files the locker holds (internal: {path: bytes}), the manifest)"""
    agent = root / shape.AGENT
    card = json.loads((agent / shape.MANIFEST).read_text())
    if where == 'internal':
        return files_of(root), card
    return bundle.make(root)[0], card


def locker_of(root):
    """the internal agent's home in the one internal locker: <the lane's locker>/<name>/agent"""
    conf = lane().get('internal') or {}
    if not conf.get('locker') or not isinstance(conf.get('place_in_place'), dict):
        raise Stop(f'the ship lane names no internal locker: {CONFIG} needs "internal": {{"locker": ..., "place_in_place": ...}}')
    return pathlib.Path(conf['locker']).expanduser().resolve() / root.name / shape.AGENT


def into_locker(root, files):
    """5 PLACE, internal, its first half: the pack written into <locker>/<name>/agent, exactly (a file the pack lacks is gone). An agent
    worked on in the locker itself (sanity_agents/<name>) only gains the kits it lacked. -> that folder"""
    dest = locker_of(root)
    if dest.parent.is_symlink() or dest.is_symlink():
        raise Stop(f'{dest} is a link: the locker holds only plain folders')
    try:
        if dest.resolve() != (root / shape.AGENT).resolve():
            dest.parent.mkdir(parents=True, exist_ok=True)
            staged = pathlib.Path(tempfile.mkdtemp(prefix='.larryd_ship_', dir=dest.parent))
            for rel, data in files.items():
                (staged / rel).parent.mkdir(parents=True, exist_ok=True)
                (staged / rel).write_bytes(data)
            old = dest.parent / f'.{dest.name}.old'
            if old.exists():
                shutil.rmtree(old)
            if dest.exists():
                dest.rename(old)
            staged.rename(dest)
            if old.exists():
                shutil.rmtree(old)
        else:
            for rel, data in files.items():
                if not (dest / rel).is_file():
                    (dest / rel).write_bytes(data)
    except OSError as e:
        raise Stop(f'the locker could not be written ({type(e).__name__}: is it locked? the owner unlocks it first): {dest}')
    return dest


def key_of(root, card, where):
    """4 KEY"""
    if where == 'internal':
        if card.get('key'):
            return card['key']
        place = root / 'place.json'
        try:
            got = json.loads(place.read_text()).get('key')
        except (OSError, ValueError):
            got = None
        if not (isinstance(got, str) and internal.KEY.match(got)):
            raise Stop('an internal agent with no "key" in agent.json needs place.json {"key": its runtime key}')
        return got
    keys_file = pathlib.Path((lane().get('external') or {}).get('keys') or '/nonexistent').expanduser()
    keys = json.loads(keys_file.read_text()) if keys_file.is_file() else {}
    return keys.get(root.name) or ''   # a first placement: the ship lane mints it (place_agent.py) and it is read back from there


def place(root, key, data, where, run=_run, scratch=None):
    """5 PLACE -> {key, code_sha256, manifest_sha256}"""
    conf = lane().get(where) or {}
    if where == 'internal':   # THE LOCKER IN PLACE: into <locker>/<name>/agent, then the runtime holds that folder where it is
        folder = into_locker(root, data)
        argv, cwd, env = _cmd(conf.get('place_in_place'), key=key, pkg='', root=root, folder=folder, name=root.name)
        code, out, err = run(argv, cwd=cwd, env=env)
        last = (out.strip().splitlines() or [''])[-1]
        try:
            got = json.loads(last)
        except ValueError:
            raise Stop(f'the internal runtime did not place it: {(err or out).strip()[-300:]}')
        if not (isinstance(got, dict) and got.get('code_sha256') and got.get('manifest_sha256')):
            raise Stop(f'the internal runtime held nothing: {last[-300:]}')
        if got.get('refused'):
            raise Stop(got['refused'])
        return {'key': key, 'code_sha256': got['code_sha256'], 'manifest_sha256': got['manifest_sha256'], 'folder': str(folder)}
    pkg = pathlib.Path(scratch or tempfile.mkdtemp(prefix='larryd_ship_')) / f'{key or root.name}.larryd'
    pkg.write_bytes(data)
    argv, cwd, env = _cmd(conf.get('place'), key=key, pkg=pkg, root=root)
    code, out, err = run(argv, cwd=cwd, env=env)
    last = (out.strip().splitlines() or [''])[-1]
    if code != 0:
        raise Stop(f'the locker was not written: {err.strip()[-300:]}')
    placed_key, _, locker = last.partition(' ')
    if not internal.KEY.match(placed_key) or (key and placed_key != key):
        raise Stop(f'the ship lane placed it under {placed_key!r}, not {key or "a runtime key"}')
    got = json.loads(locker)
    argv, cwd, env = _cmd(conf.get('submit'), key=placed_key, pkg=pkg, root=root)
    code, out, err = run(argv, cwd=cwd, env=env)
    if code != 0:
        raise Stop(f'it was not submitted to wid: {err.strip()[-300:]}')
    return {'key': placed_key, 'code_sha256': got['code_sha256'], 'manifest_sha256': got['manifest_sha256']}


APPROVE = '''
import datetime, json, sys
sys.path.insert(0, "app")
from core_engine import contacts, global_config, reviews, signing, store
key, code, manifest, note = sys.argv[1:5]
s = store.Store()
account, member = reviews._author(s)
listed = reviews.listed(s)
found = [r for r in listed["waiting"] if (r["agent_key"], r["code_sha256"], r["manifest_sha256"]) == (key, code, manifest)]
done = [r for r in listed["decided"] if (r["agent_key"], r["code_sha256"], r["manifest_sha256"]) == (key, code, manifest) and r["state"] == "approved"]
if not found and done:   # the same version placed again: FROST approved these exact hashes before
    print(json.dumps({"approved": True, "review": done[0]["id"], "card_key": done[0].get("card_key", ""), "state": "already approved"}))
    raise SystemExit(0)
if len(found) != 1:
    print(json.dumps({"approved": False, "why": f"{len(found)} waiting reviews of exactly this key and these hashes, not one"}))
    raise SystemExit(0)
core = contacts.send(global_config.secret("service"), signing.Signer())
got = reviews.decide(s, int(found[0]["id"]), "approve", note, member, datetime.datetime.now(datetime.timezone.utc), core=core, account=account)
print(json.dumps({"approved": True, "review": found[0]["id"], "card_key": (got or {}).get("card_key", "") if isinstance(got, dict) else "", "state": (got or {}).get("state", "") if isinstance(got, dict) else str(got)}))
'''


def approve(key, hashes, note, run=_run, frost=None):
    """6 APPROVE -> {review, card_key, state}. frost: the FROST to approve in (localhost's when unsaid); one with "remote" is another
    platform's, reached by that command (its last word takes the whole command line, as gcloud compute ssh --command does)."""
    frost = lane().get('frost') or {} if frost is None else frost
    if not frost.get('python') or not frost.get('cwd'):
        raise Stop('the ship lane names no FROST to approve in')
    args = [key, hashes['code_sha256'], hashes['manifest_sha256'], note]
    env = {k: str(v) for k, v in (frost.get('env') or {}).items()}
    if frost.get('remote'):
        line = (f"cd {shlex.quote(frost['cwd'])} && env " + ' '.join(f'{k}={shlex.quote(v)}' for k, v in env.items())
                + f" {shlex.quote(frost['python'])} -B -c {shlex.quote(APPROVE)} " + ' '.join(shlex.quote(a) for a in args))
        code, out, err = run([str(a) for a in frost['remote']] + [line])
    else:
        code, out, err = run([str(pathlib.Path(frost['python']).expanduser()), '-B', '-c', APPROVE, *args],
                             cwd=str(pathlib.Path(frost['cwd']).expanduser()), env=env)
    last = (out.strip().splitlines() or [''])[-1]
    try:
        got = json.loads(last)
    except ValueError:
        raise Stop(f'FROST did not answer: {(err or out).strip()[-300:]}')
    if not got.get('approved'):
        raise Stop(f"not approved: {got.get('why')}")
    return got


def platforms(key, hashes, note, run=_run, say=print):
    """7 PLATFORMS (external) -> {caller: its card key}: every other platform the lane names, submitted to and approved, as localhost"""
    cards = {}
    for p in lane().get('platforms') or []:
        name, slot = p.get('name') or p.get('slot'), p.get('slot')
        if not slot or not isinstance(p.get('frost'), dict):
            raise Stop(f'the ship lane names a platform with no slot or no FROST: {name}')
        argv, cwd, env = _cmd(p.get('submit'), key=key, pkg='', root='', slot=slot)
        code, out, err = run(argv, cwd=cwd, env=env)
        if code != 0:
            raise Stop(f'it was not submitted to {name}: {(err or out).strip()[-300:]}')
        got = approve(key, hashes, note, run, frost=p['frost'])
        if not got.get('card_key'):
            raise Stop(f'{name} approved it but named no card key')
        cards[slot] = got['card_key']
        say(f"7 PLATFORM {name}: FROST review {got['review']} {got['state']}, card {got['card_key']}")
    return cards


def card(key, card_key, run=_run, cards=None):
    """8 CARD (external): card.json beside the locker, with each platform's own card merged in (cards: {caller: card key})"""
    conf = lane().get('external') or {}
    if cards and conf.get('card_read'):
        argv, cwd, env = _cmd(conf['card_read'], key=key, pkg='', root='', card='')
        code, out, _ = run(argv, cwd=cwd, env=env)
        try:
            held = json.loads(out) if code == 0 and out.strip() else {}
        except ValueError:
            raise Stop('card.json is there but is not JSON: it is left as it is')
        held = held if isinstance(held, dict) else {}
        merged = {**(held.get('cards') if isinstance(held.get('cards'), dict) else {}), **cards}
        if held.get('card_key') and merged == held.get('cards'):
            return 'card.json already names every platform'
        body = {'card_key': held.get('card_key') or card_key, 'cards': merged}
        argv, cwd, env = _cmd(conf.get('card'), key=key, pkg='', root='', card=json.dumps(body))
        code, _, err = run(argv, cwd=cwd, env=env)
        if code != 0:
            raise Stop(f'card.json was not written: {err.strip()[-200:]}')
        return 'card.json names ' + ', '.join(sorted(merged))
    argv, cwd, env = _cmd(conf.get('card_there'), key=key, pkg='', root='', card=json.dumps({'card_key': card_key}))
    if run(argv, cwd=cwd, env=env)[0] == 0:
        return 'card.json already there'
    argv, cwd, env = _cmd(conf.get('card'), key=key, pkg='', root='', card=json.dumps({'card_key': card_key}))
    code, _, err = run(argv, cwd=cwd, env=env)
    if code != 0:
        raise Stop(f'card.json was not written: {err.strip()[-200:]}')
    return 'card.json written'


def ship(path, go=False, note='', run=_run, say=print, scratch=None):
    """-> 0 when every step went (or, without go, could go), 1 when one stopped"""
    root = pathlib.Path(path).resolve()
    where = target_of(root)
    say(f'larryd ship: {root.name} · {where.upper()}' + ('' if go else ' · THE PLAN (nothing placed, nothing approved; --go does it)'))
    try:
        commit = clean(root, run)
        say(f'1 CLEAN    committed at {commit}')
        check(root, where)
        say(f'2 DOCTOR   larryd doctor{" --internal" if where == "internal" else ""}: every check passes')
        data, manifest = pack(root, where)
        say(f'3 PACK     {len(data)} files, {sum(len(b) for b in data.values())} bytes' if where == 'internal' else f'3 PACK     {len(data)} bytes')
        key = key_of(root, manifest, where)
        say(f'4 KEY      {key or "none yet: the ship lane mints it at its first placement"}')
        if not go:
            say(f'5 PLACE    would place it in the {where} runtime' + (' (the lockers bucket, then the submit through the runtime job)' if where == 'external' else f' in place: into {locker_of(root)}, then held there'))
            say('6 APPROVE  would approve the one waiting review of exactly this key and its hashes in localhost FROST')
            if where == 'external':
                for p in lane().get('platforms') or []:
                    say(f"7 PLATFORM would submit it to {p.get('name') or p.get('slot')} and approve the same hashes in its FROST")
                say('8 CARD     would write card.json with each platform\'s card; then ONE runtime restart for the batch (the ship lane)')
            return 0
        hashes = place(root, key, data, where, run, scratch)
        key = hashes['key']
        say(f"5 PLACE    {key} held{' in ' + hashes['folder'] if hashes.get('folder') else ''}: code {hashes['code_sha256'][:12]}, manifest {hashes['manifest_sha256'][:12]}")
        got = approve(key, hashes, note or f'approved by larryd ship (CORE_CLEANUP_IV 55): {root.name} at {commit}', run)
        say(f"6 APPROVE  FROST review {got['review']} {got['state']}, card {got['card_key']}")
        if where == 'external':
            cards = platforms(key, hashes, note or f'approved by larryd ship: {root.name} at {commit}', run, say)
            if cards:
                cards = {(lane().get('external') or {}).get('slot') or 'proof': got['card_key'], **cards}
            say(f"8 CARD     {card(key, got['card_key'], run, cards)}; restart the runtime once for the batch (the ship lane)")
        return 0
    except Stop as no:
        say(f'STOPPED    {no}')
        return 1
