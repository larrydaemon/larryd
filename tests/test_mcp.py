"""Step 5: `larryd mcp`, the Claude Code connector. A test client starts the real command and drives every tool over
stdin/stdout, the way Claude Code does; the plugin and the marketplace entry are checked against the one source."""
import json
import pathlib
import shutil
import subprocess
import sys

import pytest

from larryd import mcp, new

REPO = pathlib.Path(__file__).resolve().parent.parent
LARRYD = pathlib.Path(sys.executable).parent / 'larryd'


class Client:
    def __init__(self, cwd):
        self.p = subprocess.Popen([str(LARRYD), 'mcp'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=cwd)
        self.n = 0

    def send(self, message):
        self.p.stdin.write(json.dumps(message) + '\n')
        self.p.stdin.flush()

    def ask(self, method, params=None):
        self.n += 1
        self.send({'jsonrpc': '2.0', 'id': self.n, 'method': method, **({'params': params} if params is not None else {})})
        reply = json.loads(self.p.stdout.readline())
        assert reply['id'] == self.n and reply['jsonrpc'] == '2.0'
        return reply

    def call(self, tool, **arguments):
        return self.ask('tools/call', {'name': tool, 'arguments': arguments})['result']

    def close(self):
        self.p.stdin.close()
        assert self.p.wait(timeout=10) == 0


@pytest.fixture
def client(tmp_path):
    c = Client(tmp_path)
    hello = c.ask('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'test', 'version': '0'}})
    assert hello['result']['protocolVersion'] == '2025-06-18'
    assert hello['result']['capabilities'] == {'tools': {}} and hello['result']['serverInfo']['name'] == 'larryd'
    c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})   # a notification: no reply
    yield c
    c.close()


def test_the_tools_are_listed(client):
    tools = client.ask('tools/list')['result']['tools']
    assert [t['name'] for t in tools] == ['larryd_new', 'larryd_doctor', 'larryd_run', 'larryd_submit', 'larryd_status', 'larryd_skills', 'larryd_pack']
    assert all(t['description'] and t['inputSchema']['type'] == 'object' for t in tools)


def test_new_doctor_run_through_the_connector(client, tmp_path):
    made = client.call('larryd_new', name='via-mcp')
    assert made['isError'] is False and (tmp_path / 'via-mcp' / 'agent' / 'agent.json').is_file()
    checked = client.call('larryd_doctor', path='via-mcp')
    assert checked['structuredContent']['ok'] is True
    ran = client.call('larryd_run', path='via-mcp')
    assert ran['structuredContent']['state'] == 'DONE'
    assert ran['structuredContent']['answer'] == {'delivery': 'via-mcp answered the job.'}
    assert json.loads(ran['content'][0]['text']) == ran['structuredContent']


def test_a_planted_problem_comes_back_to_the_ai(client, tmp_path):
    client.call('larryd_new', name='planted')
    path = tmp_path / 'planted' / 'agent' / 'agent.py'
    path.write_text(path.read_text() + '\nimport socket\n')
    checked = client.call('larryd_doctor', path='planted')['structuredContent']
    gap = next(c for c in checked['checks'] if c['check'] == 'the air gap')
    assert checked['ok'] is False and gap['problems'][0]['file'] == 'agent/agent.py' and gap['problems'][0]['todo']
    ran = client.call('larryd_run', path='planted')['structuredContent']
    assert ran['state'] == 'REFUSED' and ran['problems']


def test_the_default_path_is_where_claude_code_runs(tmp_path):
    new.make('here', tmp_path)
    c = Client(tmp_path / 'here')
    c.ask('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'test', 'version': '0'}})
    assert c.call('larryd_doctor')['structuredContent']['ok'] is True
    c.close()


def test_refusals(client):
    assert client.call('larryd_new', name='../out')['isError'] is True
    missing = client.call('larryd_new')
    assert missing['isError'] is True and 'name is needed' in missing['content'][0]['text']
    assert client.call('larryd_doctor', paht='x')['isError'] is True
    assert client.ask('tools/call', {'name': 'larryd_sing', 'arguments': {}})['error']['code'] == -32602
    assert client.ask('no/such')['error']['code'] == -32601
    assert client.ask('ping')['result'] == {}
    client.send('not json')   # a line that is not JSON gets a parse error, and the server keeps serving
    client.p.stdin.write('{nope\n')
    client.p.stdin.flush()
    assert json.loads(client.p.stdout.readline())['error']['code'] == -32600
    assert json.loads(client.p.stdout.readline())['error']['code'] == -32700
    assert client.ask('ping')['result'] == {}


def test_an_unknown_protocol_version_gets_ours():
    reply = mcp.answer({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '1999-01-01'}})
    assert reply['result']['protocolVersion'] == mcp.VERSIONS[0]


# ---------------------------------------------------------------- the plugin and the marketplace entry
def test_the_plugin_skill_is_the_projects_skill():
    assert (REPO / 'plugin' / 'skills' / 'larryd' / 'SKILL.md').read_text() == new.skill(), \
        'regenerate it: python -c "from larryd import new; print(new.skill(), end=\'\')" > plugin/skills/larryd/SKILL.md'


def test_the_plugin_and_the_project_start_the_same_server(tmp_path):
    assert json.loads((REPO / 'plugin' / '.mcp.json').read_text()) == new.MCP
    assert json.loads((new.make('p', tmp_path) / '.mcp.json').read_text()) == new.MCP


def test_the_marketplace_points_at_the_plugin():
    market = json.loads((REPO / '.claude-plugin' / 'marketplace.json').read_text())
    plugin = json.loads((REPO / 'plugin' / '.claude-plugin' / 'plugin.json').read_text())
    entry = next(p for p in market['plugins'] if p['name'] == plugin['name'])
    assert (REPO / entry['source'] / '.claude-plugin' / 'plugin.json').is_file()


@pytest.mark.parametrize('what', ['plugin', '.'])
def test_claude_code_validates_them(what):
    claude = shutil.which('claude')
    assert claude, 'Claude Code (the claude command) is needed to validate the plugin'
    done = subprocess.run([claude, 'plugin', 'validate', '--strict', str(REPO / what)], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


def test_skills_and_packs_through_the_connector(client, tmp_path):
    listed = client.call('larryd_skills')['structuredContent']['skills']
    assert [s['name'] for s in listed] == ['mTok charge', 'LARRY LLM greeting'] and all(len(s['hash']) == 64 for s in listed)
    (tmp_path / 'p').mkdir()
    (tmp_path / 'p' / 'pack.json').write_text('{"name": "N", "about": "A"}')
    assert client.call('larryd_pack', folder='p')['structuredContent']['ok'] is True
    assert client.call('larryd_pack', folder='nowhere')['structuredContent']['ok'] is False


def test_the_guide_and_the_readme_name_only_what_exists():
    import re
    from larryd import cli
    real = set(cli.parser()._subparsers._group_actions[0].choices)
    for doc in ('GUIDE.md', 'README.md'):
        text = (REPO / doc).read_text()
        named = set(re.findall(r'larryd ([a-z]+)', text)) - {'repository', 'tools', 'skill', 'the'}
        assert named <= real, (doc, named - real)
        assert set(re.findall(r'\blarryd_[a-z]+', text)) <= set(mcp.TOOLS), doc
