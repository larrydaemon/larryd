"""`larryd doctor`: the pretest before submission. It checks the agent the way the LARRYD runtime will hold and run it, and says
for every problem what is wrong and what to do, in words an AI can act on without asking.
The checks, in order: the project · the manifest · the entry · no network · no secret · the shape · the skills · the knowledge."""
import ast
from html.parser import HTMLParser
import json
import pathlib
import re
import tempfile
import os
import sys
from dataclasses import asdict, dataclass

from . import knowledge, shape, sheet, skills

FIX = '`larryd doctor --fix`, or larryd_doctor with "fix": true,'   # every todo that asks for the fixer names both doors
CHECKS = ('the project', 'the manifest', 'the entry', 'no network', 'no secret', 'the shape', 'the skills', 'the knowledge')
CHECKS_VERSION = '5'   # THE LARRYD CHECKS (CHECKS.md, larryd.ai/checks.html): a new or changed check raises it
BADGE = 'larryd-checks.svg'   # `larryd doctor --badge` writes it beside agent/, never inside it (the shape keeps agent/ to its own kinds)
GOLD, RED = '#FFB000', '#910E0D'   # the brand's gold (PASS) and red (FAIL)

# no network: an agent never reaches out (the LARRYD runtime's sandbox denies all network) and never starts a process
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
PLATFORM = re.compile(r'virtual_workspace', re.I)

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
NOT_A_SECRET = re.compile(r'^(?:~/|\.{1,2}/|/)?(?:[\w.-]+/)*[\w.-]+\.(?:json|txt|db|sqlite3?|log|csv|md|py|ya?ml|toml|html|lock)$', re.I)   # a file's name or path: a name is not a secret (CORE_CLEANUP_IV 55)
KINDS = {'.py', '.json', '.txt', '.md', '.csv'}   # never .css: an agent ships no sheet, the platform draws its card from the card's data
DESIGN = 'design'   # where --fix keeps a sheet written while designing, beside agent/, never in it


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
    """Every file of the agent, by its path inside the project; compiled caches are not the agent (the LARRYD runtime skips them)."""
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
        f.add('the manifest', where, 'it is not one JSON object', 'write agent.json as one JSON object with the manifest\'s fields (`larryd guide`, section 2)')
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
        if not (isinstance(run, dict) and set(run) - {'writes'} == {'do', 'hands'} and isinstance(run.get('writes', False), bool)):   # writes: the runtime's one new word (2026-11-13): an internal agent's RUN may write the records its manifest declares; true or false, nothing else
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
    files = card.get('files')
    if 'files' in hands or 'files' in card:
        if 'files' not in hands:
            f.add(c, where, '"files" is declared, but run "hands" has no "files"', 'add "files" to run "hands", or take "files" out')
        elif 'job' not in hands:
            f.add(c, where, 'run "hands" has "files" but not "job": a file is named by a job input', 'add "job" to run "hands" and the file\'s name to "inputs"')
        elif not (isinstance(files, list) and files and len(files) <= 3 and len(set(files)) == len(files) and all(isinstance(n, str) and isinstance(inputs, dict) and n in inputs for n in files)):
            f.add(c, where, '"files" is not a list of at most 3 of the agent\'s own "inputs"', 'set "files" to the input names that carry a DA-M key, e.g. ["picture"]')
    if 'records' in card:
        _records(card, c, where, f)
    if 'live' in card:
        _live(root, card, c, where, f)
    if 'makes' in card:
        _makes(card, c, where, f)
    if 'fabric' in card:
        _fabric(card, c, where, f)
    for k, what in (('skills', 'skills that exist (`larryd skills`)'), ('knowledge', 'knowledge packs (`larryd pack`)')):
        if k in card and not (isinstance(card[k], list) and all(isinstance(x, str) for x in card[k])):
            f.add(c, where, f'"{k}" is not a list of hashes', f'set "{k}" to [] or to the hashes of {what}')
    return card


def _tree(root, path, f):
    where = _rel(root, path)
    try:
        return ast.parse(path.read_text(), filename=where)
    except (SyntaxError, UnicodeDecodeError, ValueError) as e:
        f.add('the entry' if path.name == 'agent.py' else 'no network', where, f'it does not compile ({type(e).__name__}: {getattr(e, "msg", e)})',
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


OWN_FOLDER_LINE = 'import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))'
OWN_FOLDER = 'its own folder first on sys.path'


def _module_level(tree):
    """every node of the module's own top level (into its if/try/with, never into a function or class body)"""
    todo = list(tree.body)
    while todo:
        n = todo.pop(0)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield n
        todo.extend(ast.iter_child_nodes(n))


def _names_file(node, made):
    """does the expression come from __file__ (itself, or a module-level name made from it)?"""
    return any((isinstance(x, ast.Name) and (x.id == '__file__' or x.id in made)) for x in ast.walk(node))


def own_folder_first(root, entry, trees, kits=()):
    """THE SAME RUN BOTH SIDES (ONE SYSTEM, 2026-11-07): production starts every agent with `python -I -B` (the runtime's
    core_engine/sandbox.py), and -I keeps the agent's own folder OFF sys.path, so `import office` (any file beside the entry) fails
    there. An entry that imports a file of its own agent/ must put its own folder first on sys.path itself, at its module level and
    before that import: OWN_FOLDER_LINE. kits: the names packed beside it (an internal office agent's office.py and its "libs"),
    siblings too wherever they sit now. -> [Problem] (empty: it imports no sibling, or it puts its folder there first)."""
    agent = root / shape.AGENT
    path = agent / entry if isinstance(entry, str) else None
    tree = trees.get(path) if path else None
    if tree is None or not agent.is_dir():
        return []
    siblings = ({p.stem for p in agent.glob('*.py')} | {p.name for p in agent.iterdir() if p.is_dir() and p.name != '__pycache__'} | set(kits)) - {path.stem}
    top = list(_module_level(tree))
    def sibling(n):
        names = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module] if isinstance(n, ast.ImportFrom) and n.module and not n.level else []
        return next((x.split('.')[0] for x in names if x.split('.')[0] in siblings), None)
    anywhere = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) and sibling(n)]
    if not anywhere:
        return []
    first = min((n.lineno for n in top if isinstance(n, (ast.Import, ast.ImportFrom)) and sibling(n)), default=None)
    made = {t.id for n in top if isinstance(n, ast.Assign) and _names_file(n.value, set()) for t in n.targets if isinstance(t, ast.Name)}
    puts = [n.lineno for n in top if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'insert'
            and isinstance(n.func.value, ast.Attribute) and n.func.value.attr == 'path' and isinstance(n.func.value.value, ast.Name)
            and n.func.value.value.id == 'sys' and len(n.args) == 2 and isinstance(n.args[0], ast.Constant) and n.args[0].value == 0
            and _names_file(n.args[1], made)]
    if puts and (first is None or min(puts) < first):
        return []
    n = min(anywhere, key=lambda x: x.lineno) if first is None else next(x for x in top if getattr(x, 'lineno', 0) == first and isinstance(x, (ast.Import, ast.ImportFrom)))
    why = 'its line comes after' if puts else 'it never puts its own folder on sys.path before'
    return [Problem(OWN_FOLDER, _rel(root, path), n.lineno,
                    f'it imports {sibling(n)}, a file beside it, but {why} that import: production runs it with python -I, where its own folder is not on sys.path',
                    f'put this one line at the top of {entry}, before its first import of its own files: {OWN_FOLDER_LINE}')]


def _air_gap(root, trees, f):
    agent = root / shape.AGENT
    local = _local(agent)
    c = 'no network'
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
                f.add(c, where, 'it names the platform\'s or LARRYD\'s folder',
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
                found = pattern.search(line)
                if found and what == 'a secret written into the code' and all(NOT_A_SECRET.match(v) for v in re.findall(r'["\']([^"\'\s]{8,})["\']', found.group(0))):
                    continue   # it names a file (TOKENS = 'press_tokens.json'): not a secret
                if found:
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
            if path.suffix.lower() == '.css':
                f.add(c, where, 'agents ship no CSS: the platform draws the card itself, from the card\'s data in agent.json',
                      f'take it out of agent/, or run {FIX[:-1]}: it moves it to {DESIGN}/{path.name}')
            elif path.suffix not in KINDS:
                f.add(c, where, f'"{path.suffix or path.name}" is not a kind of file an agent holds',
                      f'keep only {", ".join(sorted(KINDS))} files in agent/; anything else stays outside it')
            else:
                try:
                    path.read_text()
                except UnicodeDecodeError:
                    f.add(c, where, 'it is not plain UTF-8 text', 'save it as UTF-8 text, or take it out of agent/')

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
    # the card is part of the manifest: its problems are named under that check (a check of its own would go unlisted)
    where, c, facts = _rel(root, root / shape.AGENT / shape.MANIFEST), 'the manifest', card.get('card')
    if not isinstance(facts, dict):
        f.add(c, where, '"card" is not an object', 'set "card" to {' + ', '.join(f'"{k}": ...' for k in shape.CARD) + '}; `larryd new` shows the shape')
        return
    for k in shape.CARD:
        if k not in facts:
            f.add(c, where, f'card "{k}" is missing', f'add card "{k}": {shape.CARD[k]}' + (f', or run {FIX[:-1]} (fills PUBLIC)' if k == 'authorization' else ''))
    for k in facts:
        if k not in shape.CARD and k not in shape.CARD_OPTIONAL:
            f.add(c, where, f'"{k}" is not a card field', f'remove "{k}"; the card\'s fields are: {", ".join(shape.CARD)}')
    if 'availability' in facts and facts['availability'] not in shape.AVAILABILITY:
        f.add(c, where, f'card "availability" is {json.dumps(facts["availability"])}, not "offline" or "ADMINS ONLY"', f'set card "availability" to {shape.CARD_OPTIONAL["availability"]}')
    if 'developer_site' in facts and not (isinstance(facts['developer_site'], str) and re.fullmatch(shape.SITE, facts['developer_site'])):
        f.add(c, where, f'card "developer_site" is {json.dumps(facts["developer_site"])}, not a plain https address',
              f'set card "developer_site" to {shape.CARD_OPTIONAL["developer_site"]}')

    if 'environment' in facts and not (isinstance(facts['environment'], str) and facts['environment'].strip().upper() in (shape.ENVIRONMENT, shape.INTERNAL_ONLY)):
        f.add(c, where, f'card "environment" is {json.dumps(facts["environment"])}, not one the platform knows', f'set card "environment" to {shape.CARD_OPTIONAL["environment"]}')

    def text(k):
        return isinstance(facts.get(k), str)

    for k in ('class', 'pitch', 'type', 'residency', 'authorization', 'product', 'module', 'developer'):
        if k in facts and not (text(k) and facts[k].strip()):
            f.add(c, where, f'card "{k}" is empty or not text', f'set card "{k}" to {shape.CARD[k]}')
    lists = sheet.catalog()['card']
    means = {'class': lists['class_means'], 'residency': lists['residency_means']}   # each value's meaning, said with it
    for k, allowed in (('class', list(lists['class'])), ('type', lists['type']), ('residency', lists['residency']), ('authorization', lists['authorization']), ('product', lists['products'])):
        if text(k) and facts[k].strip() and facts[k].strip().upper() not in allowed:
            named = [f'{v} ({means[k][v]})' if k in means else v for v in allowed]
            f.add(c, where, f'card "{k}" is "{facts[k]}", not one the platform knows', f'use one of: {", ".join(named)}')
    if text('pitch') and len(facts['pitch']) > shape.MOST_PITCH:
        f.add(c, where, f'card "pitch" is longer than {shape.MOST_PITCH} characters', 'say it in one line; the card has room for one')
    price = facts.get('price')
    if 'price' in facts and not ((isinstance(price, int) and not isinstance(price, bool) and price >= 0) or (text('price') and re.fullmatch(r'\d+', price.strip()))):
        f.add(c, where, f'card "price" is {json.dumps(price)}, not a whole mTok rate', 'write card "price" as whole mTok per run, a whole number: 3 or "3" ("0" is free; no fractions)')
    screens = lists['screens']
    if 'screen' in facts:
        screen = facts['screen'].strip() if text('screen') else ''
        if screen.startswith('app/') and screen[4:] in screens:
            f.add(c, where, f'card "screen" is "{screen}", the screen\'s address', f'write it without app/: "{screen[4:]}"')
        elif screen not in screens:
            f.add(c, where, f'card "screen" is "{facts["screen"]}", not a screen of the platform',
                  'use <species>/<page>: a module\'s home, list or card, e.g. cont/card, agnt/home, or a product\'s dashboard larry/home (the card\'s values table: `larryd guide`)')
        elif text('product') and screens[screen]['product'] != 'any' and facts['product'].strip().upper() in lists['products'] and facts['product'].strip().upper() != screens[screen]['product']:
            f.add(c, where, f'card "screen" {screen} is a {screens[screen]["product"]} screen, but "product" is {facts["product"]}',
                  f'set card "product" to {screens[screen]["product"]}, or pick a screen of {facts["product"]}')
        if screen in screens and screens[screen]['product'] != 'any' and text('module') and facts['module'].strip().lower() != screens[screen]['module'].lower():
            f.add(c, where, f'card "module" is "{facts["module"]}", but the screen {screen} is in {screens[screen]["module"]}',
                  f'set card "module" to "{screens[screen]["module"]}" (the platform\'s own name for that module)')
    for k in ('sends_to', 'data_sent'):
        if k in facts and not text(k):
            f.add(c, where, f'card "{k}" is not text', f'set card "{k}" to {shape.CARD[k]}')
    if text('sends_to') and facts['sends_to'].strip() and not (text('data_sent') and facts['data_sent'].strip()):
        f.add(c, where, 'card "sends_to" names an outside service, but "data_sent" says nothing', 'say in card "data_sent" what is sent there, in plain words')


def _makes(card, c, where, f):
    """"makes": the models the agent asks LARRYD to have something made by, on a RUN: each on LARRYD's list; the answer names
    "makes" in gives; and the card says, to the member, where their words go ("sends_to") and what is sent ("data_sent")."""
    asked = card['makes']
    listed = ', '.join(shape.MAKES)
    if not (isinstance(asked, list) and asked and all(isinstance(m, str) and m in shape.MAKES for m in asked)):
        f.add(c, where, '"makes" is not a list of models on LARRYD\'s list', f'set "makes" to the models the agent asks for, from: {listed}')
        return
    if isinstance(card.get('gives'), list) and 'makes' not in card['gives']:
        f.add(c, where, '"makes" is declared, but "gives" does not name "makes"', 'add "makes" to "gives": the answer carries the ask as "makes": [{"model", "prompt", "name", ...}]')
    facts = card.get('card') if isinstance(card.get('card'), dict) else {}
    providers = sorted({shape.MAKES[m][1] for m in asked})
    said = str(facts.get('sends_to') or '')
    if not all(p.lower() in said.lower() for p in providers):
        f.add(c, where, f'"makes" sends the member\'s words to {", ".join(providers)}, but card "sends_to" does not say so',
              f'name {", ".join(providers)} in card "sends_to", and say in "data_sent" what is sent (the words the member types)')


def _fabric(card, c, where, f):
    """"fabric": THE DATA FABRIC's modules, {"modules": [codes]}, each a module with a pf_<module>.csv and declared in "records"
    with read and edit (its writes are edits of custom fields, through the record doors); the answer names "fabric" in gives."""
    asked = card['fabric']
    if asked == {'snapshot': True}:   # THE DATA FABRIC'S ONE SNAPSHOT (the runtime since 2026-11-03, fabric.declared: "no connections / just 1 updated snapshot per day"): on a CALL it hands fabric = {state, viewer}, nothing else to declare
        return
    modules = asked.get('modules') if isinstance(asked, dict) and set(asked) == {'modules'} else None
    if not (isinstance(modules, list) and modules and all(isinstance(m, str) and m in shape.FABRIC_MODULES for m in modules)):
        f.add(c, where, '"fabric" is not {"snapshot": true} nor {"modules": [module codes]}', f'set "fabric" to {{"snapshot": true}} (the one snapshot), or to {{"modules": [...]}} from: {", ".join(shape.FABRIC_MODULES)}')
        return
    records = card.get('records') if isinstance(card.get('records'), dict) else {}
    short = [m for m in modules if not all(v in (records.get(m) or []) for v in shape.FABRIC_NEEDS)]
    if short:
        f.add(c, where, f'"fabric" names {", ".join(short)}, which "records" does not declare with {", ".join(shape.FABRIC_NEEDS)}',
              f'add {", ".join(f"{chr(34)}{m}{chr(34)}: {json.dumps(list(shape.FABRIC_NEEDS))}" for m in short)} to "records"')
    if isinstance(card.get('gives'), list) and 'fabric' not in card['gives']:
        f.add(c, where, '"fabric" is declared, but "gives" does not name "fabric"', 'add "fabric" to "gives": a RUN\'s answer carries "fabric": {"writes", "state"}')


def _records(card, c, where, f):
    """"records": the member's records an agent reads and writes on a CALL: {species: [verbs]}, each species a module of the
    platform (the screens table's codes), each verb one of read, add, edit, remove; only an agent that answers calls.
    THE COUNTS: "*": ["count"], of no one species, alone or beside species; handed on a CALL and on a RUN."""
    asked = card['records']
    species = sorted({s.split('/')[0] for s in sheet.catalog()['card']['screens'] if not s.startswith('larry/')})
    shape_todo = 'set "records" to {"<species>": [verbs]}, e.g. {"opns": ["read", "add", "edit", "remove"]}'
    if not (isinstance(asked, dict) and asked):
        f.add(c, where, '"records" is not {species: [verbs]}', shape_todo)
        return
    every, count = shape.RECORD_COUNTS
    words = shape.RECORD_EVERY[1]
    for name, verbs in asked.items():
        if name == every:   # THE COUNTS, THE ROSTER and THE REVIEWS WAITING: "*" takes "count", "roster", "reviews", each once
            if not (isinstance(verbs, list) and verbs and all(isinstance(v, str) and v in words for v in verbs) and len(set(verbs)) == len(verbs)):
                f.add(c, where, f'records "{every}" is not a list of {", ".join(json.dumps(w) for w in words[:-1])} and {json.dumps(words[-1])}',
                      f'"{every}" asks for the counts, the roster and/or the reviews waiting (an internal agent only): list any of "count", "roster", "reviews", each once, or take it out')
            continue
        if not (isinstance(name, str) and name in species):
            f.add(c, where, f'records names "{name}", not a module of the platform', f'use a module\'s code: {", ".join(species)}')
        if not (isinstance(verbs, list) and verbs and all(isinstance(v, str) and v in shape.RECORD_VERBS for v in verbs)):
            f.add(c, where, f'records "{name}" is not a list of verbs', f'list what the agent does with them, from: {", ".join(shape.RECORD_VERBS)}')
    if not card.get('calls') and asked != {every: count}:   # the counts alone are handed on a RUN too; the roster only on a CALL
        f.add(c, where, '"records" is declared, but "calls" is empty', 'records are handed on a CALL (the member\'s screen): name the call in "calls", or take "records" out')


OUTSIDE = re.compile(r'(?:https?:|wss?:)?//[A-Za-z0-9]')   # an address of anywhere, written into the live page or its script
LIVE_BANNED = {'subprocess', 'multiprocessing', 'ctypes', 'importlib', 'http', 'ftplib', 'smtplib', 'telnetlib', 'xmlrpc', 'webbrowser', 'pty'}   # urllib stays: its one use is LARRYD's own door, an address LARRYD hands in the environment
LIVE_ADDRESS = re.compile(r'(?:https?:|wss?:)?//(?!127\.0\.0\.1[:/\'"])[A-Za-z0-9]')   # an address written into the room program (its own machine aside)


PAGE_TAGS = {   # THE LIVE PAGE IS A SHELL, AND ONLY THIS (the security review, 2026-10-08): every element and attribute it may hold, by name
    'html': {'lang', 'data-theme', 'data-brilliance-hierarchy', 'data-font-scale', 'data-case'}, 'head': set(), 'title': set(), 'style': set(),
    'meta': {'charset', 'name', 'content'}, 'body': {'class'}, 'main': {'class', 'id'}, 'script': {'src', 'defer'}}


class _Page(HTMLParser):
    """The live page read as the standard parser reads it: anything that is not on the list is a fault. A page that may hold
    only these few plain parts has no place for a frame, a form, a link out, an object, markup hidden in an attribute, or a
    second way to write a rule: there is nothing to tell apart from what a browser would do with it."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.wrong, self.scripts = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in PAGE_TAGS:
            self.wrong.append(f'the live page holds a <{tag[:20]}> element')
            return
        names = [k for k, _v in attrs]
        if len(set(names)) != len(names) or set(names) - PAGE_TAGS[tag]:
            self.wrong.append(f'the live page\'s <{tag}> holds an attribute it may not ({", ".join(sorted(set(names) - PAGE_TAGS[tag]))[:60] or "one written twice"})')
        had = dict(attrs)
        if tag == 'script':
            self.scripts.append(had.get('src'))
            if had.get('src') not in ('/page.js', '/rain.js'):
                self.wrong.append('the live page loads a script that is not /page.js or /rain.js')
        if tag == 'meta' and not (set(had) == {'charset'} or (had.get('name') == 'viewport' and set(had) == {'name', 'content'})):
            self.wrong.append('the live page holds a <meta> that is not its charset or its viewport')
        if any(isinstance(v, str) and ('<' in v or '>' in v or '&' in v) for v in had.values()):
            self.wrong.append('the live page holds markup inside an attribute')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_comment(self, data):
        if data != 'sheets':
            self.wrong.append('the live page holds a comment that is not <!--sheets-->')

    def handle_pi(self, data):
        self.wrong.append('the live page holds a processing instruction')

    def unknown_decl(self, data):
        self.wrong.append('the live page holds a declaration that is not its doctype')

    def handle_decl(self, decl):
        if decl.strip().lower() != 'doctype html':
            self.wrong.append('the live page holds a declaration that is not its doctype')


def _page_shape(text):
    """-> [what is wrong with the live page's own markup] (empty: it is the plain shell and nothing else)."""
    if len(text) > 200_000 or '\x00' in text:
        return ['the live page is not a plain small page']
    p = _Page()
    try:
        p.feed(text)
        p.close()
    except Exception:   # a page the standard parser cannot read is not a page LARRYD takes
        return ['the live page is not markup the standard parser reads']
    if p.scripts.count('/page.js') != 1 or len(p.scripts) != len(set(p.scripts)):
        p.wrong.append('the live page does not load /page.js exactly once')
    return list(dict.fromkeys(p.wrong))


def _live(root, card, c, where, f):
    """"live": the agent's own live page, served by its own room program outside the platform. The manifest says
    {"seats": 1 to 4}; the live half is the folder live/ beside agent/: page.html, page.js, room.py, live.json and nothing else.
    The page and its script name no outside address and build no code from text; the program is the standard library only,
    starts no process and names no address (the one door it asks is LARRYD's, handed in its environment)."""
    asked, low, high = card['live'], *shape.LIVE_SEATS
    if not (isinstance(asked, dict) and set(asked) == {'seats'} and isinstance(asked['seats'], int) and not isinstance(asked['seats'], bool) and low <= asked['seats'] <= high):
        f.add(c, where, f'"live" is not {{"seats": {low} to {high}}}', f'set "live" to {{"seats": N}}, N from {low} to {high}')
    if not card.get('calls'):
        f.add(c, where, '"live" is declared, but "calls" is empty', 'the room is drawn on a CALL (the member\'s screen): name the call in "calls", or take "live" out')
    if (root / shape.AGENT / shape.LIVE).exists():
        f.add(c, _rel(root, root / shape.AGENT / shape.LIVE), 'agent/ holds something named live', 'that name is the live half\'s place in LARRYD\'s locker: rename it')
    half = root / shape.LIVE
    if half.is_symlink() or not half.is_dir():
        f.add(c, _rel(root, half), '"live" is declared, but there is no live/ folder beside agent/', f'make live/ with {", ".join(shape.LIVE_FILES)}')
        return
    held = sorted(p.name for p in half.iterdir() if p.name not in ('__pycache__', 'store'))
    for name in held:
        if name not in shape.LIVE_FILES + shape.LIVE_MAY or (half / name).is_symlink() or not (half / name).is_file():
            f.add(c, _rel(root, half / name), 'live/ holds something that is not part of the live half', f'live/ holds only: {", ".join(shape.LIVE_FILES)}')
    for name in shape.LIVE_FILES:
        if name not in held:
            f.add(c, _rel(root, half / name), f'live/ has no {name}', f'the live half is: {", ".join(shape.LIVE_FILES)}')
    for name in ('page.html', 'page.js', 'rain.js'):
        path = half / name
        if not path.is_file() or path.is_symlink():
            continue
        for n, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            if OUTSIDE.search(line):
                f.add(c, _rel(root, path), 'the live page names an outside address', 'the page reaches only its own room program: use paths that start with /', n)
            if name != 'page.html' and re.search(r'\beval\s*\(|new\s+Function\s*\(|\.innerHTML\b|document\.write', line):
                f.add(c, _rel(root, path), 'the live page builds code or markup from text', 'make elements and set their text; never eval, new Function, innerHTML or document.write', n)
        if name == 'page.html':
            for wrong in _page_shape(path.read_text(encoding='utf-8', errors='replace')):
                f.add(c, _rel(root, path), wrong, 'the page is a shell: html, head (meta, title, the line <!--sheets-->, one <style> block), body, main, and its scripts /page.js and /rain.js; everything else is built by the script')
    page = half / 'page.html'
    if page.is_file() and not page.is_symlink():   # THE PAGE'S OWN RULES ARE WRITTEN IN THE PAGE (the owner, 2026-10-08: "the css is inline all the agents use inline"): one <style> block, rules only, no file, no address, no import, and no colour of its own (the theme's variables only)
        text = page.read_text(encoding='utf-8', errors='replace')
        # ONE BLOCK, WRITTEN EXACTLY `<style>` ... `</style>` (the security review, 2026-10-08): a doctor that read the page one way while a
        # browser read it another could be walked past. So nothing that even looks like a style tag is allowed but that one plain pair,
        # and the block between is cut out by those exact words, not by a guess at how a browser would parse.
        opens, closes = len(re.findall(r'<\s*style', text, re.I)), len(re.findall(r'<\s*/\s*style', text, re.I))
        plain = text.count('<style>') == 1 and text.count('</style>') == 1 and opens == 1 and closes == 1 and text.index('<style>') < text.index('</style>')
        if (opens or closes) and not plain:
            f.add(c, _rel(root, page), 'the live page holds more than one plain <style> block', 'write the page\'s own rules in ONE <style> block with no attribute, closed by </style>')
        elif plain:
            body = text[text.index('<style>') + 7:text.index('</style>')]
            first = text[:text.index('<style>')].count('\n') + 1
            if '\\' in body:   # a rule may hide a word behind an escape (\75rl for url): no rule needs one, so none is allowed
                f.add(c, _rel(root, page), 'the live page\'s rules hold a backslash', 'write every word of a rule plainly: no escapes', first + body[:body.index('\\')].count('\n'))
            if '<' in body:
                f.add(c, _rel(root, page), 'the live page\'s rules hold markup', 'rules only inside the <style> block')
            for n, line in enumerate(re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), body, flags=re.S).splitlines(), first):
                if re.search(r'url|image-set|image\s*\(|src\s*\(|element\s*\(|expression|binding|behavior|//', line, re.I) or re.search(r'@(?!media\b|supports\b)', line, re.I):
                    f.add(c, _rel(root, page), 'the live page\'s rules name a file or an address', 'rules only: no url(), no @import, no @font-face; of the @ rules only @media and @supports', n)
                if re.search(r'#[0-9a-fA-F]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(|\b(?:hwb|lab|lch|oklab|oklch|color)\s*\(', line, re.I):
                    f.add(c, _rel(root, page), 'the live page\'s rules write a colour of their own', 'use the theme\'s colour variables, e.g. var(--active-color-01): the page then follows the brand, dark and light', n)
    program = half / 'room.py'
    if program.is_file() and not program.is_symlink():
        try:
            tree = ast.parse(program.read_text(encoding='utf-8'))
        except (SyntaxError, ValueError) as e:
            f.add(c, _rel(root, program), f'the room program does not compile: {e}', 'fix it')
            return
        for n, line in enumerate(program.read_text(encoding='utf-8').splitlines(), 1):
            if LIVE_ADDRESS.search(line):
                f.add(c, _rel(root, program), 'the room program names an address', 'the one address it may ask is LARRYD\'s own door, handed in its environment: write none into the program', n)
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                top = name.split('.')[0]
                if top not in sys.stdlib_module_names:
                    f.add(c, _rel(root, program), f'the room program imports {top}, not the standard library', 'the room program is the Python standard library only', node.lineno)
                elif top in LIVE_BANNED:
                    f.add(c, _rel(root, program), f'the room program imports {top}', 'the room program starts no process and calls out to nothing: it listens and answers', node.lineno)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ('system', 'popen', 'create_connection', 'open_connection', 'create_subprocess_exec', 'create_subprocess_shell') \
                    or isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec', '__import__'):
                f.add(c, _rel(root, program), 'the room program starts a process, calls out or runs text as code', 'it listens and answers; take it out', node.lineno)
    limits = half / 'live.json'
    if limits.is_file() and not limits.is_symlink():
        try:
            said = json.loads(limits.read_text(encoding='utf-8'))
        except ValueError:
            said = None
        if not isinstance(said, dict) or said.get('seats') != (asked.get('seats') if isinstance(asked, dict) else None):
            f.add(c, _rel(root, limits), 'live.json does not say the same seats as the manifest', 'set "seats" in live/live.json to the manifest\'s "live" seats')


PLACEHOLDER = re.compile(r'^What .+ (answers, in one plain sentence|does for the member, in one line)\.$')   # the blank's own words


def placeholders(root):
    """-> [str]: the blank's placeholder words still in the manifest ("about", the card's "pitch"). A warning while
    building (the doctor passes, larryd run works); larryd submit refuses until they say what the agent really does."""
    try:
        data = json.loads((pathlib.Path(root).resolve() / shape.AGENT / shape.MANIFEST).read_text())
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    card = data.get('card') if isinstance(data.get('card'), dict) else {}
    found = [('"about"', data.get('about')), ('card "pitch"', card.get('pitch'))]
    return [f'{name} is still the blank\'s placeholder ("{text}"): say what your agent really does'
            for name, text in found if isinstance(text, str) and PLACEHOLDER.match(text.strip())]


def is_project(root):
    """Is there an agent project here (a real agent/ holding agent.json)?"""
    agent = pathlib.Path(root).resolve() / shape.AGENT
    return agent.is_dir() and not agent.is_symlink() and (agent / shape.MANIFEST).is_file()


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
    for name in CHECKS + tuple(sorted({p.check for p in problems} - set(CHECKS))):   # a problem is always named, under its check
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
                                            'problems': [asdict(p) for p in problems if p.check == n]} for n in CHECKS + tuple(sorted({p.check for p in problems} - set(CHECKS)))]}


def fix_sheets(root):
    """A SHEET WRITTEN WHILE DESIGNING LEAVES THE AGENT (the owner 2026-11-03: "larryd should just have the agent code and data to populate
    the database and our endpoint dynamically generates the card from dynamic data / no other info from larryd"): an old "look" or "style"
    field leaves agent.json (the manifest kept in .larryd/doctor_backup/ first), then each .css in agent/ is moved to design/ (a previous
    one there kept in .larryd/doctor_backup/ first). Every backup is made before anything moves: a backup refused changes nothing. Never
    written through a link. -> [str]: what changed. --fix, place and submit all run it: CSS is never a reason to refuse."""
    root = pathlib.Path(os.path.realpath(root))
    agent, changed = root / shape.AGENT, []
    if not _inside(root, agent):
        return [f'{agent}: a link or outside the project: nothing fixed']
    moved = []
    for path in _files(agent):
        if path.suffix.lower() != '.css':
            continue
        if not _inside(root, path) or not path.is_file():
            changed.append(f'{path.relative_to(root)}: a link, left as it is (not moved)')
            continue
        moved.append(path)
    design = root / DESIGN
    if moved and (design.is_symlink() or (design.exists() and not design.is_dir())):
        raise PermissionError(f'{design} is a link or not a folder: nothing changed')
    manifest = agent / shape.MANIFEST
    try:
        data = json.loads(manifest.read_text()) if manifest.is_file() and _inside(root, manifest) else None
    except (ValueError, UnicodeDecodeError):
        data = None
    old = [k for k in ('look', 'style') if isinstance(data, dict) and k in data]
    if old:
        _backup(root, manifest)
    for path in moved:   # the previous design sheets kept first, every one, before any sheet moves
        target = design / path.name
        if target.is_file() and not target.is_symlink():
            kept = root / '.larryd' / 'doctor_backup' / DESIGN
            for f in (root / '.larryd', root / '.larryd' / 'doctor_backup', kept):
                if f.is_symlink() or (f.exists() and not f.is_dir()):
                    raise PermissionError(f'{f} is a link or not a folder: nothing moved')
                f.mkdir(mode=0o700, exist_ok=True)
            _write(root, kept / path.name, target.read_text())
            changed.append(f'{DESIGN}/{path.name}: the previous design sheet kept in .larryd/doctor_backup/{DESIGN}/{path.name}')
    if old:
        for k in old:
            data.pop(k)
        _write(root, manifest, json.dumps(data, indent=2) + '\n')
        changed.append(f'{manifest.relative_to(root)}: {" and ".join(chr(34) + k + chr(34) for k in old)} removed (the platform draws the card from its data)')
    if moved:
        design.mkdir(exist_ok=True)
    for path in moved:
        os.replace(path, design / path.name)
        changed.append(f'{path.relative_to(root)}: moved to {DESIGN}/{path.name} (agents ship no CSS: the platform draws the card)')
    return changed


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
    """`larryd doctor --fix` (the owner, 2026-10-06: "instead of just doctor it fixes it too"): moves a design sheet out of the agent
    (fix_sheets) and fills the card's missing facts with honest defaults it names;
    the originals are kept in .larryd/doctor_backup/. -> [str]: what it changed (and what it would not touch: a link, a
    path outside the project). Deterministic: the same files give the same result. Never writes through a link."""
    root = pathlib.Path(os.path.realpath(root))
    agent = root / shape.AGENT
    changed = fix_sheets(root)
    if not _inside(root, agent):
        return changed
    manifest = agent / shape.MANIFEST
    if manifest.is_file() and _inside(root, manifest):
        try:
            data = json.loads(manifest.read_text())
        except ValueError:
            data = None
        if isinstance(data, dict):
            card = data.setdefault('card', {})
            defaults = {'class': 'MARK I AGENT (NORMAL)', 'price': '0', 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'authorization': 'PUBLIC', 'screen': 'agnt/home',
                        'product': 'LARRYD', 'module': 'Agents', 'developer': 'Independent developer', 'sends_to': '', 'data_sent': '',
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
