"""`larryd new <name>`: makes the agent's project folder in the shape (shape.py), ready for Claude Code."""
import json
import pathlib
import re
from importlib import resources

from . import shape

NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,62}$')

# the LARRYD tools that exist, in the order a developer uses them; the project's documents name only these
TOOLS = (
    ('larryd new <name>', 'makes a new agent project like this one'),
    ('larryd doctor', 'checks the agent before submission; every problem says what is wrong and what to do (--json for the result as JSON)'),
    ('larryd run', 'runs the agent here the way PF HANZO runs it (no network, no new process, a scratch run folder, a time limit), '
                   'with samples/job.json or --job <file>; it needs a Mac today'),
    ('larryd mcp', 'serves these tools to Claude Code (larryd_new, larryd_doctor, larryd_run); this project\'s .mcp.json starts it'),
)
MCP = {'mcpServers': {'larryd': {'command': 'larryd', 'args': ['mcp']}}}


def _kit(name):
    return resources.files('larryd').joinpath('kit', name).read_text()


def skill():
    """The larryd skill, the same text in every project and in the Claude Code plugin."""
    return _kit('SKILL.md').format(loop='\n'.join(f'{n}. `{cmd}`: {what}' for n, (cmd, what) in enumerate(TOOLS, 1)))


def manifest(name):
    return {
        'name': name,
        'entry': 'agent.py',
        'about': f'What {name} answers, in one plain sentence.',
        'does': ['answer'],
        'calls': [],
        'reads': [],
        'run': {'do': 'answer', 'hands': []},
        'gives': ['delivery'],
        'skills': [],
    }


def make(name, where='.'):
    """-> the new project folder. Refuses a name that is not a plain folder name, and a folder that already exists."""
    if not NAME.match(name or ''):
        raise ValueError(f'"{name}" is not a plain name: start with a letter, then letters, digits, - or _ (at most 63)')
    root = pathlib.Path(where) / name
    if root.exists():
        raise ValueError(f'{root} already exists: pick another name, or work in that folder')
    fields = '\n'.join(f'- `{k}`: {v}' for k, v in shape.FIELDS.items())
    tools = '\n'.join(f'- `{cmd}`: {what}' for cmd, what in TOOLS)
    files = {
        f'{shape.AGENT}/{shape.MANIFEST}': json.dumps(manifest(name), indent=2) + '\n',
        f'{shape.AGENT}/agent.py': _kit('agent.py').format(name=name),
        shape.SAMPLE: _kit('job.json').format(),
        'CLAUDE.md': _kit('CLAUDE.md').format(name=name, fields=fields, hands=', '.join(shape.HANDS), tools=tools),
        shape.SKILL: skill(),
        '.mcp.json': json.dumps(MCP, indent=2) + '\n',
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root
