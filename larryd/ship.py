"""LARRYD SHIP: ONE place-and-approve command for both runtimes (CORE_CLEANUP_IV items 55, 98; the owner: "we want them to work the
same internal and external"). The same steps for every agent; only the target differs:

  1 CLEAN    the agent's folder holds no uncommitted change (what is placed is what is committed)
  2 DOCTOR   larryd doctor (external) or larryd doctor --internal (internal): no problem
  3 PACK     the files the runtime holds: an office agent's agent.json, agent.py, its repository's _office/office.py and the kits its
             "libs" name (as place.sh packed them); any other agent: its agent/ whole (larryd's own bundle)
  4 KEY      the runtime key it is placed under: an office agent's agent.json "key", an internal clean project's place.json "key",
             an external agent's key in the ship lane's keys file (made once)
  5 PLACE    internal: the internal runtime's own place (~/virtual_sanity/runtime_internal, slot proof: held, then sent to wid,
             which writes its card and FROST's review); external: its locker in the lockers bucket (hashed by the runtime's own
             intake), then submitted to wid through the runtime's job
  6 APPROVE  in localhost FROST, the ONE waiting review of exactly this key and these two hashes, whatever card key wid minted
             (a first placement's card key is never the runtime key)
  7 CARD     external: card.json (FROST's card key) beside the locker when it is missing; then ONE runtime restart per batch, said
             here, never done here (the ship lane does it)

    larryd ship <the agent's folder>            the plan, step by step: nothing placed, nothing approved
    larryd ship <the agent's folder> --go       do it (the ship lane: frost-cb)

Every outside step is a command it prints before it runs it; a step that fails stops the rest and says why."""
import io
import json
import os
import pathlib
import tempfile
import subprocess
import zipfile

from . import bundle, doctor, internal, shape

HOME = pathlib.Path.home()
CONFIG = pathlib.Path(os.environ.get('LARRYD_SHIP') or HOME / '.larryd' / 'ship.json')
# THE SHIP LANE'S OWN COMMANDS live in that file, never in this tool (a developer's larryd names no runtime): each is an argv with
# {key}, {pkg}, {root} filled in, and where it runs:
#   {"internal": {"place": {"argv": [...], "cwd": "...", "env": {...}}},
#    "external": {"keys": "<the lane's keys file>", "place": {"argv": [...]}, "submit": {"argv": [...], "cwd": "..."},
#                 "card": {"argv": [...]}, "card_there": {"argv": [...]}},
#    "frost": {"python": "...", "cwd": "...", "env": {...}}}
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
        kits = ['office.py'] + [f'{lib}.py' for lib in card.get('libs') or []]
        code, out, _ = run(['git', '-C', str(root.parent), 'status', '--short', '--', *[f'_office/{k}' for k in kits]])
        if out.strip():
            raise Stop(f'a kit it is packed with holds uncommitted changes ({out.strip().splitlines()[0].strip()}): commit it first')
    code, out, _ = run(['git', '-C', str(root), 'log', '-1', '--format=%h', '--', '.'])
    return out.strip()


def check(root, where):
    """2 DOCTOR"""
    problems = internal.check(root) if where == 'internal' else doctor.check(root)
    if problems:
        raise Stop(f'the doctor{" --internal" if where == "internal" else ""} found {len(problems)} problem(s): ' + '; '.join(p.text() for p in problems[:3]))


def pack(root):
    """3 PACK -> (the .larryd bytes, the manifest)"""
    agent = root / shape.AGENT
    card = json.loads((agent / shape.MANIFEST).read_text())
    if 'office' not in card:
        return bundle.make(root)[0], card
    kits = root.parent / '_office'
    files = {'agent.json': agent / 'agent.json', card.get('entry', 'agent.py'): agent / card.get('entry', 'agent.py'), 'office.py': kits / 'office.py'}
    files.update({f'{lib}.py': kits / f'{lib}.py' for lib in card.get('libs') or []})
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for name, path in files.items():
            z.writestr(name, path.read_bytes())
    return out.getvalue(), card


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
    pkg = pathlib.Path(scratch or tempfile.mkdtemp(prefix='larryd_ship_')) / f'{key or root.name}.larryd'
    pkg.write_bytes(data)
    conf = lane().get(where) or {}
    argv, cwd, env = _cmd(conf.get('place'), key=key, pkg=pkg, root=root)
    code, out, err = run(argv, cwd=cwd, env=env)
    last = (out.strip().splitlines() or [''])[-1]
    if where == 'internal':
        try:
            got = json.loads(last)
        except ValueError:
            raise Stop(f'the internal runtime did not place it: {(err or out).strip()[-300:]}')
        if not (got.get('code_sha256') and got.get('manifest_sha256')):
            raise Stop(f'the internal runtime held nothing: {last[-300:]}')
        return {'key': key, 'code_sha256': got['code_sha256'], 'manifest_sha256': got['manifest_sha256']}
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


def approve(key, hashes, note, run=_run):
    """6 APPROVE -> {review, card_key, state}"""
    frost = lane().get('frost') or {}
    if not frost.get('python') or not frost.get('cwd'):
        raise Stop('the ship lane names no FROST to approve in')
    code, out, err = run([str(pathlib.Path(frost['python']).expanduser()), '-B', '-c', APPROVE, key, hashes['code_sha256'], hashes['manifest_sha256'], note],
                         cwd=str(pathlib.Path(frost['cwd']).expanduser()), env={k: str(v) for k, v in (frost.get('env') or {}).items()})
    last = (out.strip().splitlines() or [''])[-1]
    try:
        got = json.loads(last)
    except ValueError:
        raise Stop(f'FROST did not answer: {(err or out).strip()[-300:]}')
    if not got.get('approved'):
        raise Stop(f"not approved: {got.get('why')}")
    return got


def card(key, card_key, run=_run):
    """7 CARD (external): card.json beside the locker when it is missing"""
    conf = lane().get('external') or {}
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
        data, manifest = pack(root)
        say(f'3 PACK     {len(data)} bytes')
        key = key_of(root, manifest, where)
        say(f'4 KEY      {key or "none yet: the ship lane mints it at its first placement"}')
        if not go:
            say(f'5 PLACE    would place it in the {where} runtime' + (' (the lockers bucket, then the submit through the runtime job)' if where == 'external' else ''))
            say('6 APPROVE  would approve the one waiting review of exactly this key and its hashes in localhost FROST')
            if where == 'external':
                say('7 CARD     would write card.json when missing; then ONE runtime restart for the batch (the ship lane)')
            return 0
        hashes = place(root, key, data, where, run, scratch)
        key = hashes['key']
        say(f"5 PLACE    {key} held: code {hashes['code_sha256'][:12]}, manifest {hashes['manifest_sha256'][:12]}")
        got = approve(key, hashes, note or f'approved by larryd ship (CORE_CLEANUP_IV 55): {root.name} at {commit}', run)
        say(f"6 APPROVE  FROST review {got['review']} {got['state']}, card {got['card_key']}")
        if where == 'external':
            say(f"7 CARD     {card(key, got['card_key'], run)}; restart the runtime once for the batch (the ship lane)")
        return 0
    except Stop as no:
        say(f'STOPPED    {no}')
        return 1
