"""`larryd doctor`: the pretest before submission. It checks the agent the way PF HANZO will hold and run it, and says
for every problem what is wrong and what to do, in words an AI can act on without asking.
The checks, in order: the project · the manifest · the entry · the air gap · no secret · the shape · the skills."""
import ast
import json
import pathlib
import re
import sys
from dataclasses import asdict, dataclass

from . import shape, skills

CHECKS = ('the project', 'the manifest', 'the entry', 'the air gap', 'no secret', 'the shape', 'the skills')

# the air gap: an agent never reaches out (PF HANZO's sandbox denies all network) and never starts a process
NETWORK = {'socket', 'ssl', 'http', 'urllib', 'ftplib', 'smtplib', 'poplib', 'imaplib', 'nntplib', 'telnetlib', 'xmlrpc',
           'socketserver', 'asyncio', 'selectors', 'select', 'webbrowser', 'wsgiref', 'mailbox', 'smtpd'}
PROCESS = {'subprocess', 'multiprocessing', 'pty', 'ctypes', 'concurrent'}
OS_PROCESS = re.compile(r'^(system|popen|fork|forkpty|kill|killpg|exec\w*|spawn\w*|posix_spawn\w*)$')
HIDDEN = {'importlib', 'imp', 'runpy', 'pkgutil', 'zipimport'}
PATHS = re.compile(r'(^|[\s"\'=(:])(/Users/|/home/|/private/|/tmp/|/var/|/etc/|/Volumes/|~/|\.\./)')
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
KINDS = {'.py', '.json', '.txt', '.md', '.csv'}


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
                f.add(c, where, 'run "hands" is not a list of names', 'set run "hands" to [] or to what PF HANZO hands: ' + ', '.join(shape.HANDS))
            elif set(hands) - set(shape.HANDS):
                f.add(c, where, f'run "hands" asks for {sorted(set(hands) - set(shape.HANDS))}, which PF HANZO does not hand',
                      f'PF HANZO hands today only: {", ".join(shape.HANDS)}. Take the rest out and answer without it')
    if 'skills' in card and not (isinstance(card['skills'], list) and all(isinstance(x, str) for x in card['skills'])):
        f.add(c, where, '"skills" is not a list', 'set "skills" to [] or to the hashes of skills that exist')
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
                          'remove it. PF HANZO fetches what the agent needs and hands it in (run.hands); the agent only answers', n.lineno)
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
                          'use the standard library only (PF HANZO runs the plain Python runtime), or put the code in agent/ yourself', n.lineno)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'os' and OS_PROCESS.match(n.attr):
                f.add(c, where, f'it calls os.{n.attr}, which starts or stops processes', 'remove it and do the work inside this one process', n.lineno)
            if isinstance(n, ast.Name) and n.id == '__import__':
                f.add(c, where, 'it uses __import__, which loads code the doctor cannot see', 'import what you need by name, at the top of the file', n.lineno)
    for path in _files(agent):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        where = _rel(root, path)
        for i, line in enumerate(text.splitlines(), 1):
            if PLATFORM.search(line):
                f.add(c, where, 'it names the platform\'s or PF HANZO\'s folder; the agent is air gapped from both',
                      'remove it. The agent reaches nothing; PF HANZO hands it what it needs', i)
            elif PATHS.search(line):
                f.add(c, where, 'it names a path outside the agent\'s own folder', 'remove it. The agent reads only what it is handed and writes only in the folder it is run in', i)


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
                          'take it out and revoke it if it was real. An agent holds no secret; PF HANZO hands it what it needs', i)
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
                  'declare only skills that exist, by their hash, or take it out' + ('' if known else '; no skill exists yet, so set "skills" to []'))


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


def as_json(problems):
    return {'ok': not problems, 'checks': [{'check': n, 'ok': not any(p.check == n for p in problems),
                                            'problems': [asdict(p) for p in problems if p.check == n]} for n in CHECKS]}
