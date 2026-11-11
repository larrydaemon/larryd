"""THE DOCTOR'S INTERNAL MODE (CORE_CLEANUP_IV items 55, 98; the owner 2026-11-06: "we want them to work the same internal and
external"). An internal agent (~/virtual_sanity/sanity_agents/<name>, ~/virtual_sanity/scrum_master_3/<block>,
~/virtual_sanity/pf_loot/<block>) is checked for the SAME things as an external one, by the doctor's own checks: the manifest and its
card, the entry, no secret, the shape, the skills, the knowledge. Three rules are the internal contract's, not the external's:

1. Its own fields and hand: the "service_key" hand (the member's key for the service its card names first, CORE_CLEANUP_IV 53),
   checked here, never handed to an external agent. An OFFICE agent (agent.json names "office") carries "key" (its runtime key, MAGT_<12>_<4>), "office" (one of the
   offices), "libs" (kits, each in its own agent/ or its repository's _office) and may carry "workflow", "group", "facts", "internal"
   ({"seconds": its own time limit}). They are checked here, then set aside so the shared checks see the rest. "reads" is not asked of
   an office agent: what it reads is its "facts".
2. Its records may be any module's, LARRYD's own activity too (jobs, logs, agnt, mdls: the internal runtime hands them), and its card
   may stand on the LARRYD Jobs page (larryd/jobs/home).
3. In place of "no network" (an internal agent runs as this computer's own process): NO REACH OUTSIDE THIS MAC. A network library, an
   outside program or an address off this Mac fails it, unless its repository's reach.json names the agent with its reason and its
   IV item (the same list its tests/test_no_reach.py reads). An import is the standard library, a file of its own agent/, the office
   library, or a kit its "libs" names (an office agent; a clean project stays standard library only).

    larryd doctor --internal <the agent's folder>
"""
import ast
import json
import pathlib
import re
import sys
import tempfile

from . import doctor, shape

INTERNAL_FIELDS = ('key', 'office', 'workflow', 'group', 'libs', 'facts', 'internal')
OFFICES = ('operations_manager', 'scrum_master_3', 'cmo', 'creative_director', 'pf_data_fabric')
KEY = re.compile(r'^MAGT_[0-9A-F]{12}_[0-9A-F]{4}$')
SPECIES = tuple(shape.FABRIC_MODULES)   # every module's records: a product's and LARRYD's own activity
VERBS = ('read', 'add', 'edit', 'remove')
JOBS_PAGE, JOBS_SCREEN = 'larryd/jobs/home', 'jobs/home'   # the internal agents' page, and the platform's screen it stands for
MOST_SECONDS = 6 * 3600   # the internal runtime's own limit for one agent (harness MOST_INTERNAL_SECONDS)
REACH = [
    ('a network library', re.compile(r'\b(urllib\.request|urlopen|http\.client|import requests|requests\.(get|post|put|Session)|httpx|aiohttp|'
                                     r'socket\.(socket|create_connection)|import socket|smtplib|ftplib|paramiko|websocket)')),
    ('an outside program', re.compile(r"""['"](ssh|scp|rsync|curl|wget|gcloud|gsutil|gh|aws|az|signal-cli|docker|kubectl)['"]""")),
    ('an address off this Mac', re.compile(r'\b(?!127\.0\.0\.1\b|0\.0\.0\.0\b)(\d{1,3}\.){3}\d{1,3}\b')),
]
C_MANIFEST, C_REACH = 'the manifest', 'no reach outside this Mac'


def _manifest_of(root):
    try:
        card = json.loads((pathlib.Path(root) / shape.AGENT / shape.MANIFEST).read_text())
    except (OSError, ValueError):
        return None
    return card if isinstance(card, dict) else None


def tag(root):
    """THE TAG (ONE SYSTEM, the owner 2026-11-07: "it just tags as internal or external"): its card's "environment", the platform's
    data_agent_environment -> 'internal' (POSITIVE FEEDBACK (INTERNAL-ONLY)), 'external' (POSITIVE FEEDBACK), or None when the card
    names none (or a value the platform does not know: the doctor says so)."""
    card = _manifest_of(root)
    env = (card.get('card') or {}).get('environment') if card and isinstance(card.get('card'), dict) else None
    if not isinstance(env, str):
        return None
    return {shape.INTERNAL_ONLY: 'internal', shape.ENVIRONMENT: 'external'}.get(env.strip().upper())


def is_internal(root):
    """Is the agent at `root` an INTERNAL one? Its tag when its card carries one; else the old folder-shape rule (an office agent, or a
    project of an internal repository: a reach.json beside it), until every agent carries its tag."""
    root = pathlib.Path(root).resolve()
    tagged = tag(root)
    if tagged:
        return tagged == 'internal'
    card = _manifest_of(root)
    return card is not None and ('office' in card or (root.parent / 'reach.json').is_file())


def kit(root, name):
    """where a kit (office.py, look.py, day.py ...) is: inside the agent's own folder (self-contained, production's shape: the locker
    in place writes them there) first, else its repository's _office (the old packing). -> its path, or None."""
    root = pathlib.Path(root)
    for path in (root / shape.AGENT / f'{name}.py', root.parent / '_office' / f'{name}.py'):
        if path.is_file() and not path.is_symlink():
            return path
    return None


def allowed(root):
    """{agent folder: reason} of its repository's reach.json, {} when there is none"""
    path = pathlib.Path(root).resolve().parent / 'reach.json'
    try:
        got = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in got.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(got, dict) else {}


def _seconds(card, f):
    """any internal agent's own time limit"""
    got = card.get('internal')
    seconds = got.get('seconds') if isinstance(got, dict) else got
    if 'internal' in card and not (isinstance(got, dict) and isinstance(seconds, int) and not isinstance(seconds, bool) and 1 <= seconds <= MOST_SECONDS):
        f.add(C_MANIFEST, 'agent/agent.json', f'"internal" is not {{"seconds": 1 to {MOST_SECONDS}}}', f'set "internal" to {{"seconds": 1 to {MOST_SECONDS}}}')


def _fields(root, card, f):
    """rule 1: the internal fields, checked here"""
    where = 'agent/agent.json'
    _seconds(card, f)
    if 'office' not in card:
        for k in INTERNAL_FIELDS:
            if k in card and k != 'internal':   # its time limit is any internal agent's (an office app's too)
                f.add(C_MANIFEST, where, f'"{k}" belongs to an office agent, and this one names no "office"', f'take "{k}" out, or name its "office"')
        return
    if not (isinstance(card.get('key'), str) and KEY.match(card['key'])):
        f.add(C_MANIFEST, where, '"key" is not its runtime key (MAGT_ and 12 and 4 capital hex)', 'set "key" to the key it is placed under')
    if card.get('office') not in OFFICES:
        f.add(C_MANIFEST, where, f'"office" is {card.get("office")!r}, not one of the offices', f'set "office" to one of: {", ".join(OFFICES)}')
    if kit(root, 'office') is None:
        f.add(C_MANIFEST, where, "it has no office.py, neither in its agent/ nor in its repository's _office (the office library every office agent runs with)",
              'keep the office library in its agent/office.py (self-contained, as the locker holds it), or in <the repository>/_office/office.py')
    libs = card.get('libs', [])
    if not (isinstance(libs, list) and all(isinstance(x, str) and re.fullmatch(r'[a-z_][a-z0-9_]*', x) for x in libs)):
        f.add(C_MANIFEST, where, '"libs" is not a list of kit names', 'set "libs" to [] or to names of kits in its agent/ (or <the repository>/_office), e.g. ["look"]')
        libs = []
    for lib in libs:
        if kit(root, lib) is None:
            f.add(C_MANIFEST, where, f'"libs" names {lib}, but {lib}.py is neither in its agent/ nor in its repository\'s _office',
                  f'put {lib}.py in its agent/ (or <the repository>/_office), or take "{lib}" out of "libs"')
    for k, kind in (('workflow', str), ('group', str), ('facts', dict), ('internal', dict)):
        if k in card and not isinstance(card[k], kind):
            f.add(C_MANIFEST, where, f'"{k}" is not {"text" if kind is str else "an object"}', f'set "{k}" right, or take it out')


def _records(card, f):
    """rule 2: any module's records, by the platform's verbs"""
    records = card.get('records')
    if records is None or records == {}:
        return
    good = isinstance(records, dict) and all(
        (k in SPECIES and isinstance(v, list) and v and all(x in VERBS for x in v))
        or (k == shape.RECORD_EVERY[0] and isinstance(v, list) and v and all(x in shape.RECORD_EVERY[1] for x in v) and len(set(v)) == len(v))
        for k, v in records.items())
    if not good:
        f.add(C_MANIFEST, 'agent/agent.json', '"records" is not {species: [verbs]} of the platform\'s modules',
              f'set "records" to {{"<one of {", ".join(SPECIES)}>": ["read", ...]}} or {{"*": [{", ".join(repr(x) for x in shape.RECORD_EVERY[1])}, each once]}}')


SERVICE_KEY = 'service_key'   # an internal agent's own hand (CORE_CLEANUP_IV 53): the member's key for the service its card names FIRST in sends_to


def _service_key(card, f):
    """rule 1b: the "service_key" hand is an internal agent's, and only for a card that names its service first in sends_to"""
    run = card.get('run') if isinstance(card.get('run'), dict) else {}
    hands = run.get('hands') if isinstance(run.get('hands'), list) else []
    if SERVICE_KEY in hands and not str((card.get('card') or {}).get('sends_to') or '').strip():
        f.add(C_MANIFEST, 'agent/agent.json', 'run "hands" has "service_key", but its card names no service in "sends_to"',
              'name the service first in the card\'s "sends_to" (its key is that service\'s), or take "service_key" out')


def _shared(card):
    """the manifest the shared checks read: the internal fields set aside, the records checked by rule 2, the Jobs page as its screen"""
    out = {k: v for k, v in card.items() if k not in INTERNAL_FIELDS and k != 'records'}   # its records: rule 2, checked here
    run = out.get('run')
    if isinstance(run, dict) and isinstance(run.get('hands'), list) and SERVICE_KEY in run['hands']:
        out['run'] = {**run, 'hands': [h for h in run['hands'] if h != SERVICE_KEY]}   # rule 1b, checked here
    if 'office' in card and 'reads' not in out:
        out['reads'] = ['its facts']   # rule 1: an office agent's reads are its facts
    c = out.get('card')
    if isinstance(c, dict) and c.get('screen') == JOBS_PAGE:
        out['card'] = {**c, 'screen': JOBS_SCREEN}
    return out


def _imports(root, card, trees, f):
    """rule 3, its imports: the standard library, its own files, the office library and its named kits"""
    agent = root / shape.AGENT
    own = {p.stem for p in agent.rglob('*.py')} | {p.name for p in agent.rglob('*') if p.is_dir()}   # its own modules and packages, at any depth
    kits = ({'office'} | set(card.get('libs') or [])) if 'office' in card else set()
    provided = runtime_provides()
    for path, tree in trees.items():
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) and node.module and not node.level else []
            for name in names:
                top = name.split('.')[0]
                if top in sys.stdlib_module_names or top in own or top in kits or top in provided:
                    continue
                f.add(C_REACH, doctor._rel(root, path), f"it imports {top}: not the standard library, its own files, a kit it names, or what the internal runtime's python holds",
                      'use the standard library, put the code in agent/, or name the kit in "libs"', node.lineno)


def _entry(root, card, trees, f):
    """the doctor's own entry check, but an office agent's "does" may be answered by the kit its entry hands itself to: an entry that
    ends in office.main(...), day.main(...) or night.main(...) of a kit it names answers its CALL (canvas) and its RUN (run) there"""
    entry = card.get('entry') if isinstance(card.get('entry'), str) else ''
    tree = trees.get(root / shape.AGENT / entry)
    kits = ({'office'} | set(card.get('libs') or [])) if 'office' in card else set()
    handed = tree is not None and any(
        isinstance(n, ast.If) and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == 'main'
                                      and isinstance(c.func.value, ast.Name) and c.func.value.id in kits for c in ast.walk(n)) for n in tree.body)
    if handed:
        top = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        does = [d for d in card.get('does') or [] if isinstance(d, str)]
        card = {**card, 'does': [d for d in does if d in top or d not in ('canvas', 'run')]}   # the kit answers canvas and run
    doctor._entry(root, card, trees, f)


def runtime_provides():
    """what the INTERNAL runtime's own python holds beyond the standard library (its site-packages: it runs these agents), by top name"""
    import os
    found = set()
    base = pathlib.Path(os.environ.get('LARRYD_INTERNAL_RUNTIME') or pathlib.Path.home() / 'virtual_sanity' / 'runtime_internal') / '.venv' / 'lib'
    for site in base.glob('python3*/site-packages'):
        for p in site.iterdir():
            if p.suffix in ('.dist-info', '.egg-info', '.pth') or p.name.startswith(('_', '.')):
                continue
            found.add(p.name.split('.')[0] if p.suffix in ('.py', '.so') else p.name)
    return found


def _reach(root, f):
    """rule 3, its reach: nothing off this Mac, unless its repository's reach.json says why"""
    name = root.name
    if name in allowed(root):
        return
    for path in doctor._files(root / shape.AGENT):
        if path.suffix not in ('.py', '.sh', '.js') or not path.is_file() or path.is_symlink():
            continue
        for n, line in enumerate(path.read_text(errors='replace').split('\n'), 1):
            for what, rx in REACH:
                if rx.search(line):
                    f.add(C_REACH, doctor._rel(root, path), f'it reaches outside this Mac by itself ({what})',
                          'ask PF_Loot for it through its lane (~/virtual_sanity/pf_loot, README), or name the agent with its reason and IV item in its repository\'s reach.json', n)
                    break


def check(root):
    """-> [doctor.Problem]: every problem of the internal agent at `root` (empty = it passes)."""
    root = pathlib.Path(root).resolve()
    f = doctor._Found()
    agent = root / shape.AGENT
    if agent.is_symlink() or not agent.is_dir() or not (agent / shape.MANIFEST).is_file():
        f.add('the project', str(root), 'there is no agent here (no agent/agent.json)', 'run the doctor on the agent\'s folder: <the repository>/<name>')
        return f.problems
    try:
        card = json.loads((agent / shape.MANIFEST).read_text())
    except (OSError, UnicodeDecodeError, ValueError) as e:
        f.add(C_MANIFEST, 'agent/agent.json', f'it is not readable JSON ({type(e).__name__})', 'write agent.json as one JSON object')
        return f.problems
    if not isinstance(card, dict):
        f.add(C_MANIFEST, 'agent/agent.json', 'it is not one JSON object', 'write agent.json as one JSON object')
        return f.problems
    _fields(root, card, f)
    _service_key(card, f)
    _records(card, f)
    with tempfile.TemporaryDirectory() as d:   # the shared checks read the manifest from a project: the same file, its internal fields aside
        shared_root = pathlib.Path(d) / root.name
        (shared_root / shape.AGENT).mkdir(parents=True)
        (shared_root / shape.AGENT / shape.MANIFEST).write_text(json.dumps(_shared(card)))
        shared = doctor._manifest(shared_root, f)
        if shared is not None:
            doctor._card(shared_root, shared, f)
    trees = {}
    for path in doctor._files(agent):
        if path.suffix == '.py' and path.is_file() and not path.is_symlink():
            tree = doctor._tree(root, path, f)
            if tree is not None:
                trees[path] = tree
    _entry(root, card, trees, f)
    _imports(root, card, trees, f)
    _reach(root, f)
    doctor._secrets(root, f)
    doctor._shape(root, f)
    doctor._skills(root, card, f)
    doctor._knowledge(root, card, f)
    return f.problems


def warnings(root):
    """-> [doctor.Problem] said, not failed (for now: every office agent imports office.py beside it, and failing them all would stop
    the whole internal suite at once): THE SAME RUN BOTH SIDES, doctor.own_folder_first."""
    root = pathlib.Path(root).resolve()
    card = _manifest_of(root)
    if card is None:
        return []
    entry = card.get('entry') if isinstance(card.get('entry'), str) else 'agent.py'
    path = root / shape.AGENT / entry
    f = doctor._Found()
    tree = doctor._tree(root, path, f) if path.is_file() and not path.is_symlink() else None
    kits = ({'office'} | {k for k in card.get('libs') or [] if isinstance(k, str)}) if 'office' in card else set()
    return doctor.own_folder_first(root, entry, {path: tree} if tree is not None else {}, kits)


def report(root, problems):
    return doctor.report(root, problems).replace('larryd doctor:', 'larryd doctor --internal:', 1)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(report(p, check(p)))
