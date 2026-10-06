"""`larryd doctor`: the pretest before submission. It checks the agent the way PF HANZO will hold and run it, and says
for every problem what is wrong and what to do, in words an AI can act on without asking.
The checks, in order: the project · the manifest · the entry · the air gap · no secret · the shape · the skills · the knowledge."""
import ast
import json
import pathlib
import re
import tempfile
import os
from importlib import resources
import sys
from dataclasses import asdict, dataclass

from . import knowledge, shape, skills

CHECKS = ('the project', 'the manifest', 'the entry', 'the air gap', 'no secret', 'the shape', 'the skills', 'the knowledge')
CHECKS_VERSION = '1'   # THE LARRYD CHECKS (CHECKS.md, larryd.ai/checks.html): a new or changed check raises it
BADGE = 'larryd-checks.svg'   # `larryd doctor --badge` writes it beside agent/, never inside it (the shape keeps agent/ to its own kinds)
GOLD, RED = '#FFB000', '#910E0D'   # the brand's gold (PASS) and red (FAIL)

# the air gap: an agent never reaches out (PF HANZO's sandbox denies all network) and never starts a process
NETWORK = {'socket', 'ssl', 'http', 'urllib', 'ftplib', 'smtplib', 'poplib', 'imaplib', 'nntplib', 'telnetlib', 'xmlrpc',
           'socketserver', 'asyncio', 'selectors', 'select', 'webbrowser', 'wsgiref', 'mailbox', 'smtpd'}
PROCESS = {'subprocess', 'multiprocessing', 'pty', 'ctypes', 'concurrent'}
OS_PROCESS = re.compile(r'^(system|popen|fork|forkpty|kill|killpg|exec\w*|spawn\w*|posix_spawn\w*)$')
HIDDEN = {'importlib', 'imp', 'runpy', 'pkgutil', 'zipimport', 'builtins', 'pickle', 'marshal', 'shelve'}
PATHS = re.compile(r'(^|[\s"\'=(:])(/Users/|/home/|/private/|/tmp/|/var/|/etc/|/Volumes/|~/|\.\./)')
# the disguises: code, modules and paths made at run time, which the doctor could not read in the source
BY_NAME = {'__import__', '__builtins__', '__loader__', '__spec__'}                  # the interpreter's own doors, by name
RUNS_CODE = {'eval', 'exec', 'compile', 'globals', 'locals', 'vars', 'breakpoint'}   # code or namespaces from a string
BY_STRING = {'getattr', 'setattr', 'delattr', 'hasattr'}                            # an attribute named at run time
INSIDES = {'__dict__', '__class__', '__base__', '__bases__', '__mro__', '__subclasses__', '__globals__', '__code__',
           '__closure__', '__getattribute__', '__builtins__', '__import__', '__loader__', '__spec__'}
SYS_DOORS = {'modules', 'meta_path', 'path_hooks', 'path_importer_cache'}
PATH_MAKERS = {('os', 'sep'), ('os', 'altsep'), ('path', 'sep'), ('path', 'altsep'), ('path', 'expanduser'),
               ('path', 'expandvars'), ('Path', 'home'), ('os', 'getenv')}
ABSOLUTE = re.compile(r'^(/|\\|~)[\w.@~-]+(/[\w.@~-]*)*$')   # a value that is a path from the root or the home folder (a separator alone, as in "/".join, is not)
PLATFORM = re.compile(r'virtual_workspace|pfhanzo', re.I)

# no secret: files that are secrets by their name, and text that looks like one
SECRET_FILES = re.compile(r'(^\.env|\.pem$|\.key$|\.p12$|\.pfx$|^id_(rsa|dsa|ecdsa|ed25519)|^secrets?(\.|$)|credentials)', re.I)
SECRET_TEXT = (
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'a private key'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'a cloud access key'),
    (re.compile(r'\bsk-ant-[A-Za-z0-9_-]{16,}'), 'an Anthropic API key'),
    (re.compile(r'\bsk-[A-Za-z0-9_-]{32,}'), 'an API key'),
    (re.compile(r'\b(ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}'), 'a GitHub token'),
    (re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{10,}'), 'a Slack token'),
    (re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'), 'a Google API key'),
    (re.compile(r'(?i)\b\w*(secret|password|passwd|token|api_?key|private_?key)\w*["\']?\s*[:=]\s*["\'][^"\'\s]{8,}["\']'), 'a secret written into the code'),
)
KINDS = {'.py', '.json', '.txt', '.md', '.csv', '.css'}   # .css: written normally, then turned into the menu's classes by --fix
STYLE_ATTR = re.compile(r'''\bstyle\s*=\s*(\\?["'])(.*?)\1''', re.S)   # an inline style, in any of the agent's files
CLASSES = 'classes.json'   # the agent's picks from the platform's menu: {"<a part of its card>": "<menu classes>"}


@dataclass
class Problem:
    check: str
    file: str
    line: int
    wrong: str
    todo: str

    def text(self):
        where = f'{self.file}' + (f' line {self.line}' if self.line else '')
        return f'FAIL {self.check} · {where}: {self.wrong}. What to do: {self.todo}'


class _Found:
    def __init__(self):
        self.problems = []

    def add(self, check, file, wrong, todo, line=0):
        self.problems.append(Problem(check, file, line, wrong, todo))


def _files(agent):
    """Every file of the agent, by its path inside the project; compiled caches are not the agent (PF HANZO skips them)."""
    return sorted(p for p in agent.rglob('*') if '__pycache__' not in p.relative_to(agent).parts)


def _rel(root, path):
    return path.relative_to(root).as_posix()


def _manifest(root, f):
    path = root / shape.AGENT / shape.MANIFEST
    where = _rel(root, path)
    try:
        card = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, ValueError) as e:
        f.add('the manifest', where, f'it is not readable JSON ({type(e).__name__})', 'write agent.json as one JSON object; `larryd new` shows the shape')
        return None
    if not isinstance(card, dict):
        f.add('the manifest', where, 'it is not one JSON object', 'write agent.json as one JSON object with the fields in CLAUDE.md')
        return None
    c = 'the manifest'
    for k in shape.NEEDED:
        if k not in card:
            f.add(c, where, f'"{k}" is missing', f'add "{k}": {shape.FIELDS[k]}')
    for k in card:
        if k not in shape.FIELDS:
            f.add(c, where, f'"{k}" is not a manifest field', f'remove "{k}"; the fields are: {", ".join(shape.NEEDED)}')

    def text(k):
        return isinstance(card.get(k), str) and card[k].strip()

    def names(k):
        v = card.get(k)
        return isinstance(v, list) and all(isinstance(x, str) and x.isidentifier() for x in v)

    for k in ('name', 'about'):
        if k in card and not text(k):
            f.add(c, where, f'"{k}" is empty or not text', f'set "{k}" to {shape.FIELDS[k]}')
    if 'entry' in card and not (text('entry') and re.fullmatch(r'[A-Za-z_]\w*\.py', card['entry'])):
        f.add(c, where, '"entry" is not a .py file name inside agent/', 'set "entry" to the file name only, e.g. "agent.py" (no folder, no path)')
    if 'does' in card and not (names('does') and card['does']):
        f.add(c, where, '"does" is not a list of function names', 'set "does" to the names of the functions that answer a job, e.g. ["answer"]')
    does = set(card['does']) if names('does') else set()
    if 'calls' in card:
        if not names('calls'):
            f.add(c, where, '"calls" is not a list of function names', 'set "calls" to [] (or names from "does")')
        elif set(card['calls']) - does:
            f.add(c, where, f'"calls" names {sorted(set(card["calls"]) - does)}, not in "does"', 'every name in "calls" must also be in "does"')
    for k in ('reads', 'gives'):
        v = card.get(k)
        if k in card and not (isinstance(v, list) and all(isinstance(x, str) and x.strip() for x in v)):
            f.add(c, where, f'"{k}" is not a list of plain words', f'set "{k}" to {shape.FIELDS[k]}')
    if 'gives' in card and isinstance(card['gives'], list) and not card['gives']:
        f.add(c, where, '"gives" is empty', 'name what the answer holds, e.g. ["delivery"]')
    run = card.get('run')
    if 'run' in card:
        if not (isinstance(run, dict) and set(run) == {'do', 'hands'}):
            f.add(c, where, '"run" is not {"do": ..., "hands": [...]}', 'set "run" to {"do": "<one of does>", "hands": []}')
        else:
            if run['do'] not in does:
                f.add(c, where, f'run "do" is "{run["do"]}", not one of "does"', f'set run "do" to one of {sorted(does) or "the names in does"}')
            hands = run['hands']
            if not (isinstance(hands, list) and all(isinstance(x, str) for x in hands)):
                f.add(c, where, 'run "hands" is not a list of names', 'set run "hands" to [] or to what LARRYD hands: ' + ', '.join(shape.HANDS))
            elif set(hands) - set(shape.HANDS):
                f.add(c, where, f'run "hands" asks for {sorted(set(hands) - set(shape.HANDS))}, which LARRYD does not hand',
                      f'LARRYD hands today only: {", ".join(shape.HANDS)}. Take the rest out and answer without it')
    hands = run.get('hands') if isinstance(run, dict) and isinstance(run.get('hands'), list) else []
    inputs = card.get('inputs')
    if 'job' in hands:
        if not (isinstance(inputs, dict) and inputs and all(isinstance(n, str) and n.isidentifier() and isinstance(s, str) and re.fullmatch(shape.SLOT, s)
                                                            for n, s in inputs.items())):
            f.add(c, where, 'run "hands" has "job", but "inputs" is not {name: slot}', 'set "inputs" to the names the agent reads, each on a slot 001-015, e.g. {"mood": "001"}')
        elif len(set(inputs.values())) != len(inputs):
            f.add(c, where, '"inputs" puts two names on one slot', 'give each name its own slot, 001-015')
    elif 'inputs' in card:
        f.add(c, where, '"inputs" is declared, but run "hands" has no "job"', 'add "job" to run "hands", or take "inputs" out')
    for k, what in (('skills', 'skills that exist (`larryd skills`)'), ('knowledge', 'knowledge packs (`larryd pack`)')):
        if k in card and not (isinstance(card[k], list) and all(isinstance(x, str) for x in card[k])):
            f.add(c, where, f'"{k}" is not a list of hashes', f'set "{k}" to [] or to the hashes of {what}')
    return card


def _tree(root, path, f):
    where = _rel(root, path)
    try:
        return ast.parse(path.read_text(), filename=where)
    except (SyntaxError, UnicodeDecodeError, ValueError) as e:
        f.add('the entry' if path.name == 'agent.py' else 'the air gap', where, f'it does not compile ({type(e).__name__}: {getattr(e, "msg", e)})',
              'fix the code so `python -m py_compile` passes on it', getattr(e, 'lineno', 0) or 0)
        return None


def _entry(root, card, trees, f):
    entry = card.get('entry') if card else None
    if not isinstance(entry, str) or not re.fullmatch(r'[A-Za-z_]\w*\.py', entry):
        return
    path = root / shape.AGENT / entry
    where = _rel(root, path)
    if not path.is_file():
        f.add('the entry', where, 'the entry file is missing', f'make agent/{entry}, or set "entry" to the file that answers the job')
        return
    tree = trees.get(path)
    if tree is None:
        return
    top = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name in card.get('does') if isinstance(card.get('does'), list) else []:
        if isinstance(name, str) and name not in top:
            f.add('the entry', where, f'"does" names "{name}", but the entry has no function {name}(job)',
                  f'add def {name}(job): ... at the top level of {entry}, or take "{name}" out of "does"')
    main = any(isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name)
               and n.test.left.id == '__name__' for n in tree.body)
    if not main:
        f.add('the entry', where, 'it never runs: there is no `if __name__ == \'__main__\':`',
              'end the entry with if __name__ == \'__main__\': main(), where main reads one JSON from stdin and prints one JSON')


def _local(agent):
    return {p.stem for p in agent.glob('*.py')} | {p.name for p in agent.iterdir() if p.is_dir() and (p / '__init__.py').is_file()}


def _air_gap(root, trees, f):
    agent = root / shape.AGENT
    local = _local(agent)
    c = 'the air gap'
    for path, tree in trees.items():
        where = _rel(root, path)
        for n in ast.walk(tree):
            mods = []
            if isinstance(n, ast.Import):
                mods = [(a.name, None) for a in n.names]
            elif isinstance(n, ast.ImportFrom) and not n.level:
                mods = [(n.module or '', [a.name for a in n.names])]
            for mod, names in mods:
                top = mod.split('.')[0]
                if top in NETWORK:
                    f.add(c, where, f'it imports {mod}, a network module; an agent never reaches out',
                          'remove it. LARRYD fetches what the agent needs and hands it in (run.hands); the agent only answers', n.lineno)
                elif top in PROCESS:
                    f.add(c, where, f'it imports {mod}, which starts processes or reaches outside Python',
                          'remove it and do the work inside this one process', n.lineno)
                elif top in HIDDEN:
                    f.add(c, where, f'it imports {mod}, which loads code the doctor cannot see', 'import what you need by name, at the top of the file', n.lineno)
                elif top == 'os' and names and any(OS_PROCESS.match(x) for x in names):
                    f.add(c, where, f'it imports {", ".join(x for x in names if OS_PROCESS.match(x))} from os, which starts or stops processes',
                          'remove it and do the work inside this one process', n.lineno)
                elif top not in sys.stdlib_module_names and top not in local:
                    f.add(c, where, f'it imports {mod}, which is not the Python standard library',
                          'use the standard library only (LARRYD runs the plain Python runtime), or put the code in agent/ yourself', n.lineno)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'os' and OS_PROCESS.match(n.attr):
                f.add(c, where, f'it calls os.{n.attr}, which starts or stops processes', 'remove it and do the work inside this one process', n.lineno)
            for wrong, todo in _disguise(n):
                f.add(c, where, wrong, todo, n.lineno)
    for path in _files(agent):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        where = _rel(root, path)
        seen = {p.line for p in f.problems if p.check == c and p.file == where}   # one problem per line: the code's own reading wins
        for i, line in enumerate(text.splitlines(), 1):
            if i in seen:
                continue
            if PLATFORM.search(line):
                f.add(c, where, 'it names the platform\'s or LARRYD\'s folder; the agent is air gapped from both',
                      'remove it. The agent reaches nothing; LARRYD hands it what it needs', i)
            elif PATHS.search(line):
                f.add(c, where, 'it names a path outside the agent\'s own folder', 'remove it. The agent reads only what it is handed and writes only in the folder it is run in', i)


def _named(node):
    """The name an expression ends in: os.path.sep -> ('path', 'sep'); a plain name -> (None, name)."""
    if isinstance(node, ast.Attribute):
        inner = node.value
        return (inner.id if isinstance(inner, ast.Name) else inner.attr if isinstance(inner, ast.Attribute) else None), node.attr
    if isinstance(node, ast.Name):
        return None, node.id
    return None, None


def _disguise(n):
    """-> [(what is wrong, what to do)] for one node: code, a module or a path made at run time."""
    by_hand = 'import what you need by name, at the top of the file, and write the code itself'
    if isinstance(n, ast.Name) and n.id in BY_NAME:
        return [(f'it uses {n.id}, which reaches modules or code by a name the doctor cannot see', by_hand)]
    if isinstance(n, ast.Attribute):
        owner, attr = _named(n)
        if attr in INSIDES:
            return [(f'it reaches .{attr}, the interpreter\'s inside, where code and modules can be found by name', by_hand)]
        if owner == 'sys' and attr in SYS_DOORS:
            return [(f'it uses sys.{attr}, which reaches modules by a name the doctor cannot see', by_hand)]
        if (owner, attr) in PATH_MAKERS:
            return [(f'it uses {owner}.{attr}, which builds a path outside the agent\'s own folder',
                     'read only your own folder (pathlib.Path(__file__).parent) and write only in the folder you are run in')]
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        name, args = n.func.id, n.args
        if name in RUNS_CODE:
            return [(f'it calls {name}(), which runs code or reaches names made from a string at run time', by_hand)]
        if name in BY_STRING and len(args) >= 2 and not (isinstance(args[1], ast.Constant) and isinstance(args[1].value, str)):
            return [(f'it calls {name}() with a name built at run time', f'write the attribute itself (obj.name), or {name}(obj, "name") with the name written out')]
        if name == 'chr' and args and isinstance(args[0], ast.Constant) and args[0].value in (47, 92):
            return [('it builds a path separator with chr(), a path the doctor cannot read',
                     'read only your own folder (pathlib.Path(__file__).parent) and write only in the folder you are run in')]
    if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)):
        value = n.value.decode('latin-1') if isinstance(n.value, bytes) else n.value
        if ABSOLUTE.match(value) or PATHS.search(value) or PLATFORM.search(value):
            return [(f'it holds the path {value[:40]!r}, outside the agent\'s own folder',
                     'remove it. The agent reads only what it is handed and its own folder, and writes only in the folder it is run in')]
    return []


def _secrets(root, f):
    agent = root / shape.AGENT
    for path in _files(agent):
        where = _rel(root, path)
        if SECRET_FILES.search(path.name):
            f.add('no secret', where, 'a file named like a secret is in the agent',
                  'take it out of agent/. Keys belong to the developer, never to the agent')
            continue
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pattern, what in SECRET_TEXT:
                if pattern.search(line):
                    f.add('no secret', where, f'it holds what looks like {what}',
                          'take it out and revoke it if it was real. An agent holds no secret; LARRYD hands it what it needs', i)
                    break


def _shape(root, f):
    agent = root / shape.AGENT
    c = 'the shape'
    for path in [agent] + _files(agent):
        where = _rel(root, path)
        parts = path.relative_to(root).parts
        if path.is_symlink():
            f.add(c, where, 'it is a link; an agent is only its own files', 'replace the link with the real file inside agent/, or remove it')
        elif any(p.startswith('.') for p in parts[1:]):
            f.add(c, where, 'a hidden file or folder is in the agent', 'remove it from agent/; everything the agent is must be visible')
        elif path.is_file():
            if path.suffix not in KINDS:
                f.add(c, where, f'"{path.suffix or path.name}" is not a kind of file an agent holds',
                      f'keep only {", ".join(sorted(KINDS))} files in agent/; anything else stays outside it')
            else:
                try:
                    text = path.read_text()
                except UnicodeDecodeError:
                    f.add(c, where, 'it is not plain UTF-8 text', 'save it as UTF-8 text, or take it out of agent/')
                else:
                    if path.suffix == '.css':
                        f.add(c, where, 'the platform takes no stylesheet: a card only names classes from its menu',
                              'run `larryd doctor --fix`: it turns the sheet into the menu\'s classes (agent/classes.json) and keeps the original in .larryd/doctor_backup/')
                    elif STYLE_ATTR.search(text):
                        f.add(c, where, 'an inline style: the platform strips every style attribute',
                              'run `larryd doctor --fix`: it turns each style into the menu\'s classes')
                    elif path.name == CLASSES and path.parent == root / shape.AGENT:
                        off = _off_menu(text)
                        if off:
                            f.add(c, where, f'not on the platform\'s menu: {", ".join(off)}', 'run `larryd doctor --fix`: it keeps the menu\'s classes only')

        elif not path.is_dir():
            f.add(c, where, 'it is not a plain file or folder', 'remove it from agent/')


def _skills(root, card, f):
    if not card or not isinstance(card.get('skills'), list):
        return
    known = skills.known()
    for s in card['skills']:
        if isinstance(s, str) and s not in known:
            f.add('the skills', _rel(root, root / shape.AGENT / shape.MANIFEST), f'the skill "{s}" does not exist',
                  'declare only skills that exist, by their hash: ' + '; '.join(f'{h} ({k["name"]})' for h, k in known.items()) +
                  ' (`larryd skills` lists them), or take it out')


def _knowledge(root, card, f):
    if not card or not isinstance(card.get('knowledge'), list):
        return
    held = knowledge.held()
    for k in card['knowledge']:
        if isinstance(k, str) and k not in held:
            f.add('the knowledge', _rel(root, root / shape.AGENT / shape.MANIFEST), f'the knowledge pack "{k}" is not held by LARRYD',
                  'take it out: LARRYD holds no knowledge pack yet' if not held else 'declare only packs LARRYD holds, by their hash')


def _card(root, card, f):
    """The card facts, checked with the marketplace's own rules: a card the gate cannot show is no agent for hire."""
    if 'card' not in card:
        return   # the manifest check already said it is missing
    where, c, facts = _rel(root, root / shape.AGENT / shape.MANIFEST), 'the card', card.get('card')
    if not isinstance(facts, dict):
        f.add(c, where, '"card" is not an object', 'set "card" to {' + ', '.join(f'"{k}": ...' for k in shape.CARD) + '}; `larryd new` shows the shape')
        return
    for k in shape.CARD:
        if k not in facts:
            f.add(c, where, f'card "{k}" is missing', f'add card "{k}": {shape.CARD[k]}')
    for k in facts:
        if k not in shape.CARD:
            f.add(c, where, f'"{k}" is not a card field', f'remove "{k}"; the card\'s fields are: {", ".join(shape.CARD)}')

    def text(k):
        return isinstance(facts.get(k), str)

    for k in ('class', 'pitch', 'type', 'residency', 'product', 'module', 'developer'):
        if k in facts and not (text(k) and facts[k].strip()):
            f.add(c, where, f'card "{k}" is empty or not text', f'set card "{k}" to {shape.CARD[k]}')
    if text('pitch') and len(facts['pitch']) > shape.MOST_PITCH:
        f.add(c, where, f'card "pitch" is longer than {shape.MOST_PITCH} characters', 'say it in one line; the card has room for one')
    if 'price' in facts and not (text('price') and re.fullmatch(r'\d+', facts['price'])):
        f.add(c, where, 'the price is not a whole mTok rate', 'write card "price" as whole mTok per run, as text: "0" (free) or "5"')
    if 'screen' in facts and not (text('screen') and re.fullmatch(shape.SCREEN, facts['screen'])):
        f.add(c, where, 'the card names no screen', 'set card "screen" to the screen it lives on, <species>/<page>, e.g. cont/card')
    for k in ('sends_to', 'data_sent'):
        if k in facts and not text(k):
            f.add(c, where, f'card "{k}" is not text', f'set card "{k}" to {shape.CARD[k]}')
    if text('sends_to') and facts['sends_to'].strip() and not (text('data_sent') and facts['data_sent'].strip()):
        f.add(c, where, 'card "sends_to" names an outside service, but "data_sent" says nothing', 'say in card "data_sent" what is sent there, in plain words')


def check(root):
    """-> [Problem]: every problem found in the agent project at `root` (empty = the agent passes)."""
    root = pathlib.Path(root).resolve()
    f = _Found()
    agent = root / shape.AGENT
    if agent.is_symlink() or not agent.is_dir() or not (agent / shape.MANIFEST).is_file():
        f.add('the project', str(root), 'there is no agent here (no agent/agent.json)',
              'run the doctor in the agent project\'s folder (the one `larryd new` made), or make one with `larryd new <name>`')
        return f.problems
    card = _manifest(root, f)
    if card is not None:
        _card(root, card, f)
    trees = {}
    for path in _files(agent):
        if path.suffix == '.py' and path.is_file() and not path.is_symlink():
            tree = _tree(root, path, f)
            if tree is not None:
                trees[path] = tree
    _entry(root, card, trees, f)
    _air_gap(root, trees, f)
    _secrets(root, f)
    _shape(root, f)
    _skills(root, card, f)
    _knowledge(root, card, f)
    return f.problems


def report(root, problems):
    lines = [f'larryd doctor: {pathlib.Path(root).resolve()}']
    for name in CHECKS:
        mine = [p for p in problems if p.check == name]
        lines += [p.text() for p in mine] if mine else [f'PASS {name}']
    failed = len({p.check for p in problems})
    lines.append('the agent passes every check' if not problems else
                 f'{failed} of {len(CHECKS)} checks failed · {len(problems)} problem{"s" if len(problems) != 1 else ""} to fix, then run `larryd doctor` again')
    return '\n'.join(lines)


def badge(problems, day):
    """The doctor's result as a small SVG for a README: -> the SVG text. PASS in the brand's gold, FAIL in red, with the
    day it was checked and the checks' version."""
    word, colour = ('PASS', GOLD) if not problems else ('FAIL', RED)
    left = f'LARRYD checks v{CHECKS_VERSION}'
    right = f'{word} {day}'
    lw, rw = 8 + 7 * len(left), 8 + 7 * len(right)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{lw + rw}" height="22" role="img" aria-label="{left}: {right}">'
            f'<title>{left}: {right}</title>'
            f'<rect width="{lw}" height="22" fill="#000000"/><rect x="{lw}" width="{rw}" height="22" fill="{colour}"/>'
            f'<g font-family="Menlo,Consolas,monospace" font-size="12" text-anchor="middle">'
            f'<text x="{lw / 2}" y="15" fill="{GOLD}">{left}</text>'
            f'<text x="{lw + rw / 2}" y="15" fill="{"#000000" if not problems else "#FFFFFF"}">{right}</text></g></svg>\n')


def as_json(problems):
    return {'ok': not problems, 'checks_version': CHECKS_VERSION, 'checks': [{'check': n, 'ok': not any(p.check == n for p in problems),
                                            'problems': [asdict(p) for p in problems if p.check == n]} for n in CHECKS]}


ELEMENTS = {'h1': 'heading', 'h2': 'title', 'h3': 'subtitle', 'h4': 'subtitle', 'p': 'body', 'small': 'annotation', 'label': 'label',
            'a': 'link', 'nav': 'nav', 'blockquote': 'callout', 'aside': 'callout', 'code': 'notes', 'pre': 'notes'}   # what a developer writes by habit, said as the catalog's roles


def _catalog():
    return json.loads(resources.files('larryd').joinpath('kit', 'catalog.json').read_text())


def _menu():
    return set(_catalog()['classes'])


def _off_menu(text):
    """The class names in a classes.json that are not on the menu (or ['the file is not {name: classes}'])."""
    try:
        data = json.loads(text)
    except ValueError:
        return ['the file is not JSON']
    if not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values()):
        return ['the file is not {"part": "classes"}']
    menu = _menu()
    return sorted({w for v in data.values() for w in v.split() if w not in menu})


def _px(value):
    m = re.fullmatch(r'\s*(-?[\d.]+)\s*(px|rem|em)?\s*', value or '')
    return float(m.group(1)) * (16 if m.group(2) in ('rem', 'em') else 1) if m else None


def _nearest(px, steps):
    return min(steps, key=lambda k: abs(steps[k] - px))


GAPS = {'xs': 4, 's': 8, 'm': 14, 'l': 22}   # the platform's layout steps (the proposal: plans/AGENT_CARD_LOOKS_PROPOSAL_20261006.md)
TYPE = ('font', 'font-family', 'font-size', 'font-weight', 'font-style', 'line-height', 'letter-spacing', 'text-transform')


def to_classes(written, where=''):
    """Written CSS declarations ("display: flex; gap: 10px; font-size: 40px ...") and the part's own name -> (the menu's
    classes, [what was said]). Type -> the nearest role of THE GLOBAL FONT CATALOG; layout -> the steps (stack, row,
    gap-*, pad-*, align-*, justify-*, cols-N); a look named or drawn (CRT scanlines, a wellness glow, a glitch) -> the
    platform's own look-*; a colour -> the theme's own (nothing to write); everything else is dropped and said. Deterministic."""
    cat = _catalog()
    roles, out, said = cat['roles'], [], []
    decls = {}
    for d in written.split(';'):
        if ':' in d:
            k, v = (x.strip() for x in d.split(':', 1))
            if k:
                decls[k.lower()] = v
    typ = {k: v for k, v in decls.items() if k in TYPE}
    if typ:
        size, wt, case = _px(typ.get('font-size')), typ.get('font-weight', ''), typ.get('text-transform')
        wt = {'bold': 700, 'normal': 400}.get(wt, int(wt) if wt.isdigit() else None)
        role = min(roles, key=lambda r: (abs(roles[r]['size'] - size) if size is not None else 0) + (abs(roles[r]['weight'] - wt) / 50 if wt else 0) + (6 if case and case != roles[r]['case'] else 0))
        out.append(role)
        said.append(f'{"; ".join(f"{k}: {v}" for k, v in typ.items())} -> {role}')
    display, direction = decls.get('display', '').lower(), decls.get('flex-direction', '').lower()
    if display in ('flex', 'inline-flex'):
        out.append('stack' if direction.startswith('column') else 'row')
    elif display in ('grid', 'inline-grid'):
        cols = decls.get('grid-template-columns', '')
        m = re.search(r'repeat\(\s*(\d+)', cols)
        n = int(m.group(1)) if m else 3 if 'auto-fill' in cols or 'auto-fit' in cols else len(cols.split()) or 1
        out.append(f'cols-{max(1, min(4, n))}')
    if _px(decls.get('gap', '').split()[0] if decls.get('gap') else '') is not None:
        out.append('gap-' + _nearest(_px(decls['gap'].split()[0]), GAPS))
    if decls.get('padding') and _px(decls['padding'].split()[0]) is not None:
        out.append('pad-' + _nearest(_px(decls['padding'].split()[0]), GAPS))
    align = {'flex-start': 'align-start', 'start': 'align-start', 'center': 'align-center', 'flex-end': 'align-end', 'end': 'align-end'}.get(decls.get('align-items', '').lower())
    justify = {'flex-start': 'justify-start', 'start': 'justify-start', 'center': 'justify-center', 'flex-end': 'justify-end', 'end': 'justify-end',
               'space-between': 'justify-between'}.get(decls.get('justify-content', '').lower())
    out += [c for c in (align, justify) if c]
    text = (where + ' ' + written).lower()
    look = ('look-glitch' if re.search(r'glitch|mark-?3|foil|flicker|jitter', text) else
            'look-wellness' if re.search(r'wellness|mark-?2|breathe|drift|blur\(', text) else
            'look-crt' if re.search(r'\bcrt\b|mark-?1|scan|repeating-linear-gradient\(\s*0deg', text) else
            'look-block' if re.search(r'block|repeating-linear-gradient\(\s*90deg', text) else '')
    if look and ('animation' in decls or 'background' in decls or 'filter' in decls or 'look' in where.lower()):
        out.append(look)
        said.append(f'{where.strip() or "the part"}: its look -> {look} (the platform draws it)')
    kept_keys = set(TYPE) | {'display', 'flex-direction', 'grid-template-columns', 'gap', 'padding', 'align-items', 'justify-content'}
    for k, v in decls.items():
        if k not in kept_keys and not (look and k in ('animation', 'background', 'filter', 'background-size', 'mix-blend-mode', 'opacity')):
            said.append(f'{k}: {v} -> dropped (the platform draws the card; colours are the theme\'s own)')
    seen = []
    for c in out:
        if c not in seen:
            seen.append(c)
    return ' '.join(seen), said


def _part(selector):
    """A rule's selector as the part of the card it names: its last class (or tag), without the agent's own prefixes."""
    words = re.findall(r'[.]?[A-Za-z][\w-]*', re.sub(r'::?[\w-]+(\([^)]*\))?|\[[^\]]*\]', '', selector.split(',')[0]))
    name = (words[-1] if words else 'card').lstrip('.')
    return ELEMENTS.get(name, re.sub(r'^mk-', '', name))   # a habit tag said as the role it means


def _sheet_classes(text):
    """A whole stylesheet -> ({part: classes}, [said]): each rule converted (to_classes), @-rules said and dropped."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    parts, said = {}, []
    for at in re.findall(r'@(?:import|font-face|keyframes|media|supports|namespace|layer)[^{;]*', text):
        said.append(f'{at.strip()} -> dropped (the platform draws its own looks and motion)')
    text = re.sub(r'@(?:keyframes|media|supports|layer)[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}', '', text)
    text = re.sub(r'@[^{;]*;', '', text)
    for selector, body in re.findall(r'([^{}]+)\{([^{}]*)\}', text):
        part = _part(selector.strip())
        classes, notes = to_classes(body, selector.strip())
        said += [f'{selector.strip()}: {n}' for n in notes]
        if classes:
            merged = (parts.get(part, '') + ' ' + classes).split()
            parts[part] = ' '.join(dict.fromkeys(merged))
    return parts, said


def conversions(root):
    """-> [str]: what `larryd doctor --fix` will make of the agent's sheets and inline styles (the owner, 2026-10-06:
    "if they write anything it can get converted automatically"), so the author learns the platform's menu."""
    notes = []
    for path in _files(pathlib.Path(root).resolve() / shape.AGENT):
        if not path.is_file() or path.suffix not in KINDS:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if path.suffix == '.css':
            parts, said = _sheet_classes(text)
            notes += [f'{path.name}: {n}' for n in said] + [f'{path.name}: {p} -> class "{c}"' for p, c in sorted(parts.items())]
        for m in STYLE_ATTR.finditer(text):
            classes, said = to_classes(m.group(2))
            notes += [f'{path.name}: style="{m.group(2)}" -> class="{classes}"'] + [f'{path.name}: {n}' for n in said]
    return notes


def _inside(root, path):
    """Is path (and every folder between root and it) a real, non-link path inside root? Never written through otherwise."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    here = root
    for part in rel.parts:
        here = here / part
        if here.is_symlink():
            return False
    return os.path.realpath(path).startswith(str(root) + os.sep)


def _write(root, path, text):
    """An atomic write inside root only: a temp file in the same folder, then a rename; never through a link."""
    if not _inside(root, path) or (path.exists() and not path.is_file()):
        raise PermissionError(f'{path} is a link or outside the project: not written')
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
    try:
        with os.fdopen(fd, 'w') as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _backup(root, path):
    """The original kept once in .larryd/doctor_backup/ (made private, refused if it or .larryd is a link)."""
    folder = root / '.larryd' / 'doctor_backup'
    for f in (root / '.larryd', folder):
        if f.is_symlink() or (f.exists() and not f.is_dir()):
            raise PermissionError(f'{f} is a link or not a folder: no backup made, nothing changed')
        if not f.exists():
            f.mkdir(mode=0o700)
    target = folder / path.name
    if not target.exists():
        _write(root, target, path.read_text())


def fix(root):
    """`larryd doctor --fix` (the owner, 2026-10-06: "instead of just doctor it fixes it too"): rewrites the developer's
    own sheets and inline styles into the platform's menu of classes (agent/classes.json) and fills the card's missing facts with honest defaults it names;
    the originals are kept in .larryd/doctor_backup/. -> [str]: what it changed (and what it would not touch: a link, a
    path outside the project). Deterministic: the same files give the same result. Never writes through a link."""
    root = pathlib.Path(os.path.realpath(root))
    agent, changed, cat = root / shape.AGENT, [], _catalog()
    if not _inside(root, agent):
        return [f'{agent}: a link or outside the project: nothing fixed']
    picks = {}
    for path in _files(agent):
        if not path.is_file() and not path.is_symlink() or path.suffix not in KINDS:
            continue
        if not _inside(root, path) or not path.is_file():
            if path.suffix == '.css' or path.is_symlink():
                changed.append(f'{path.relative_to(root)}: a link, left as it is (not written)')
            continue
        try:
            old = path.read_text()
        except UnicodeDecodeError:
            continue
        if path.suffix == '.css':
            parts, _said = _sheet_classes(old)
            for part, classes in parts.items():
                picks[part] = ' '.join(dict.fromkeys((picks.get(part, '') + ' ' + classes).split()))
            _backup(root, path)
            if not _inside(root, path):
                raise PermissionError(f'{path} is a link or outside the project: not removed')
            os.unlink(path)
            changed.append(f'{path.relative_to(root)}: turned into the menu\'s classes (agent/{CLASSES}); the sheet removed, kept in .larryd/doctor_backup/')
        elif STYLE_ATTR.search(old):
            new = STYLE_ATTR.sub(lambda m: f'class={m.group(1)}{to_classes(m.group(2))[0]}{m.group(1)}', old)
            _backup(root, path)
            _write(root, path, new)
            changed.append(f'{path.relative_to(root)}: each inline style turned into the menu\'s classes')
    target = agent / CLASSES
    if target.is_symlink() or (target.exists() and not _inside(root, target)):
        changed.append(f'{target.relative_to(root)}: a link, left as it is (not written)')
    else:
        try:
            have = json.loads(target.read_text()) if target.is_file() else {}
        except ValueError:
            have = {}
        have = {k: v for k, v in have.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(have, dict) else {}
        menu = _menu()
        merged = {k: ' '.join(w for w in dict.fromkeys((have.get(k, '') + ' ' + picks.get(k, '')).split()) if w in menu) for k in sorted(set(have) | set(picks))}
        merged = {k: v for k, v in merged.items() if v}
        text = json.dumps(merged, indent=2, sort_keys=True) + '\n'
        if (merged or target.exists()) and (not target.is_file() or target.read_text() != text):
            if target.is_file():
                _backup(root, target)
            _write(root, target, text)
            changed.append(f'{target.relative_to(root)}: the menu\'s classes only')
    manifest = agent / shape.MANIFEST
    if manifest.is_file() and _inside(root, manifest):
        try:
            data = json.loads(manifest.read_text())
        except ValueError:
            data = None
        if isinstance(data, dict):
            card = data.setdefault('card', {})
            defaults = {'class': 'MARK I AGENT (NORMAL)', 'price': '0', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'screen': 'agnt/home',
                        'product': 'LARRYD', 'module': 'AGENT', 'developer': 'Independent developer', 'sends_to': '', 'data_sent': '',
                        'pitch': f"What {data.get('name') or 'this agent'} does for the member, in one line."}
            missing = [k for k in defaults if k not in card]
            if missing:
                _backup(root, manifest)
                for k in missing:
                    card[k] = defaults[k]
                _write(root, manifest, json.dumps(data, indent=2) + '\n')
                changed.append(f'{manifest.relative_to(root)}: the card\'s missing facts filled ({", ".join(f"{k} = {defaults[k]!r}" for k in missing)}): check them')
    elif manifest.is_symlink():
        changed.append(f'{manifest.relative_to(root)}: a link, left as it is (not written)')
    return changed
