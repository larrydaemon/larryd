"""`larryd new <name>`: makes the agent's project folder in the shape (shape.py), ready for Claude Code."""
import json
import os
import pathlib
import re
import shutil
import sys
from importlib import resources

from . import shape, sheet

NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,62}$')

# the LARRYD tools that exist, in the order a developer uses them; the project's documents name only these
TOOLS = (
    ('larryd new <name>', 'makes a new agent project like this one'),
    ('larryd guide', 'prints the whole guide (it ships in the package as GUIDE.md; `larryd --help` names its path)'),
    ('larryd doctor', 'checks the agent before submission; every problem says what is wrong and what to do (--json for the result as JSON)'),
    ('larryd run', 'runs the agent here the way LARRYD runs it (no network, no new process, a scratch run folder, a time limit), '
                   'with samples/job.json or --job <file>; on a Mac or Linux'),
    ('larryd submit', 'sends the agent (agent/ only, one file) to LARRYD for review, after the doctor, and opens the page where you sign in '
                      'with Google or Apple to submit it; nothing to paste or keep'),
    ('larryd place', 'puts the agent on your own LARRYD\'s shelf: the doctor, then agent/ as one file into the locker of the runtime '
                     'running on this computer (`larryd` in another terminal); the same agent placed again replaces itself'),
    ('larryd card', 'places the agent and opens the marketplace page on this computer: every agent LARRYD holds here as a card with its '
                    'hire toggle, as the platform will show it; a card the gate cannot show is listed with why'),
    ('larryd skills', 'lists the skills an agent may declare in "skills", by hash'),
    ('larryd pack <folder>', 'checks a knowledge pack and gives its hash'),
    ('larryd mcp', 'serves these tools to Claude Code (larryd_new, larryd_doctor, larryd_run, larryd_submit, larryd_skills, '
                   'larryd_pack, larryd_card); this project\'s .mcp.json starts it'),
)
MCP = {'mcpServers': {'larryd': {'command': 'larryd', 'args': ['mcp']}}}   # the plugin's: larryd on PATH


def mcp_config():
    """A project's .mcp.json: this larryd by its absolute path, so Claude Code starts it with no venv activated and no
    PATH set; when no larryd script sits beside this Python (npm, cargo), this Python runs the module itself."""
    here = pathlib.Path(sys.executable).parent / ('larryd.exe' if os.name == 'nt' else 'larryd')
    found = str(here) if here.is_file() else shutil.which('larryd')
    server = {'command': os.path.abspath(found), 'args': ['mcp']} if found else {'command': os.path.abspath(sys.executable), 'args': ['-m', 'larryd', 'mcp']}
    return {'mcpServers': {'larryd': server}}


def _kit(name):
    """A kit template (kit/<name>.template), the text `new` fills; never read as it is."""
    return resources.files('larryd').joinpath('kit', name + '.template').read_text()


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
        'knowledge': [],
        'card': {'class': 'MARK I AGENT (NORMAL)', 'pitch': f'What {name} does for the member, in one line.', 'price': '0',
                 'type': 'OFF-THE-SHELF', 'residency': 'INTERNAL', 'screen': 'agnt/home', 'product': 'LARRYD', 'module': 'AGENT',
                 'developer': 'Independent developer', 'sends_to': '', 'data_sent': ''},
    }


EXAMPLES = ('marketplace',)   # the example agents a project may start from (larryd/kit/examples/<name>/)


def _example(example):
    """{file name: text} of an example agent, as the kit ships it."""
    folder = resources.files('larryd').joinpath('kit', 'examples', example)
    return {f.name: f.read_text() for f in folder.iterdir() if f.is_file() and not f.name.startswith('.')}


def make(name, where='.', example=None):
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
        # the job's own inputs, for an agent with "job" in run.hands and "inputs" {"name": "001", "mood": "002"}: larryd run --job samples/job_inputs.json
        'samples/job_inputs.json': resources.files('larryd').joinpath('kit', 'job_inputs.json').read_text(),
        'CLAUDE.md': _kit('CLAUDE.md').format(name=name, fields=fields, hands=', '.join(shape.HANDS), tools=tools, sheet=sheet.table(), card=sheet.card_table()),
        shape.SKILL: skill(),
        '.mcp.json': json.dumps(mcp_config(), indent=2) + '\n',
    }
    if example:   # an example agent: its own code, manifest and files replace the plain ones; its card keeps its own facts
        if example not in EXAMPLES:
            raise ValueError(f'no example "{example}": the examples are {", ".join(EXAMPLES)}')
        for file, text in _example(example).items():
            # its sample job where `larryd run` reads one; its design sheet beside agent/, never in it (agents ship no CSS)
            files[shape.SAMPLE if file == 'job.json' else 'design/card.css' if file == 'design.css' else f'{shape.AGENT}/{file}'] = text
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root
