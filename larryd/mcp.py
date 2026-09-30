"""`larryd mcp`: the Claude Code connector. A local tool server on stdin/stdout (the Model Context Protocol: JSON-RPC 2.0,
one message per line) that serves LARRYD's tools to Claude Code. It runs on the developer's computer and reaches
nothing itself; each tool is the same code as the command of the same name."""
import json
import sys

from . import __version__, doctor, knowledge, new, runner, skills, submit

VERSIONS = ('2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05')   # the protocol versions this server speaks, newest first


def _new(args):
    root = new.make(args['name'], args.get('where') or '.')
    return {'made': str(root), 'next': f'work in {root}: read its CLAUDE.md, change agent/agent.py and agent/agent.json, then larryd_doctor'}, False


def _doctor(args):
    problems = doctor.check(args.get('path') or '.')
    return doctor.as_json(problems), False


def _run(args):
    result = runner.run(args.get('path') or '.', args.get('job'))
    return runner.as_json(result), False


def _submit(args):
    try:
        out = submit.submit(args.get('path') or '.')
    except submit.Refused as no:
        out = no.as_json()
    return out, False


def _skills(args):
    return {'skills': [{'hash': h, **s} for h, s in skills.known().items()]}, False


def _pack(args):
    digest, wrong = knowledge.check(args['folder'])
    return {'hash': digest, 'ok': not wrong, 'problems': wrong}, False


PATH = {'type': 'string', 'description': 'the agent project\'s folder (default: the folder Claude Code runs in)'}
TOOLS = {
    'larryd_new': (_new, 'Make a new LARRYD agent project: agent/ (the manifest and one entry that answers a job), CLAUDE.md with the '
                         'spec and the rules, the larryd skill and a sample job.',
                   {'type': 'object', 'properties': {'name': {'type': 'string', 'description': 'the agent\'s name, also its folder'},
                                                     'where': {'type': 'string', 'description': 'the folder to make it in (default: here)'}},
                    'required': ['name'], 'additionalProperties': False}),
    'larryd_doctor': (_doctor, 'Check the agent before submission: the manifest, the entry, the air gap, no secret, the shape, the skills. '
                               'Every problem names the file and line, what is wrong and what to do; fix each one and check again.',
                      {'type': 'object', 'properties': {'path': PATH}, 'additionalProperties': False}),
    'larryd_run': (_run, 'Run the agent here the way LARRYD runs it (no network, no new process, a scratch run folder, a time limit) '
                         'with the sample job, and see its answer or why it failed. On a Mac or Linux.',
                   {'type': 'object', 'properties': {'path': PATH, 'job': {'type': 'string', 'description': 'a sample job file (default: samples/job.json)'}},
                    'additionalProperties': False}),
    'larryd_submit': (_submit, 'Send the agent (agent/ only, as one file) to LARRYD for review, after the doctor, and open the claim page in '
                               'the browser: the developer signs in there with Google or Apple within 10 minutes. Nothing to paste or keep.',
                      {'type': 'object', 'properties': {'path': PATH}, 'additionalProperties': False}),
    'larryd_skills': (_skills, 'List the skills an agent may declare in its manifest ("skills"), by hash, with what each does.',
                      {'type': 'object', 'properties': {}, 'additionalProperties': False}),
    'larryd_pack': (_pack, 'Check a knowledge pack (a folder with pack.json and plain text files) and give its hash.',
                    {'type': 'object', 'properties': {'folder': {'type': 'string', 'description': 'the pack\'s folder'}},
                     'required': ['folder'], 'additionalProperties': False}),
}


def _tools():
    return [{'name': n, 'description': d, 'inputSchema': s} for n, (_, d, s) in TOOLS.items()]


def _call(params):
    name, args = params.get('name'), params.get('arguments') or {}
    if name not in TOOLS:
        raise LookupError(f'no tool {name}; the tools are {", ".join(TOOLS)}')
    work, _, schema = TOOLS[name]
    unknown = set(args) - set(schema['properties'])
    missing = [k for k in schema.get('required', []) if not str(args.get(k) or '').strip()]
    if unknown or missing:
        text = f'{name} takes {", ".join(schema["properties"])}' + (f'; {", ".join(missing)} is needed' if missing else '')
        return {'content': [{'type': 'text', 'text': text}], 'isError': True}
    try:
        out, failed = work(args)
    except ValueError as no:
        return {'content': [{'type': 'text', 'text': str(no)}], 'isError': True}
    return {'content': [{'type': 'text', 'text': json.dumps(out, indent=2)}], 'structuredContent': out, 'isError': failed}


def answer(message):
    """One JSON-RPC message in -> the reply (None for a notification)."""
    method, mid = message.get('method'), message.get('id')
    if mid is None:
        return None   # a notification (e.g. notifications/initialized): no reply
    try:
        if method == 'initialize':
            asked = (message.get('params') or {}).get('protocolVersion')
            result = {'protocolVersion': asked if asked in VERSIONS else VERSIONS[0], 'capabilities': {'tools': {}},
                      'serverInfo': {'name': 'larryd', 'version': __version__},
                      'instructions': 'LARRYD builds agents for LARRYD. In an agent project, read CLAUDE.md first; '
                                      'check with larryd_doctor and try with larryd_run after every change.'}
        elif method == 'ping':
            result = {}
        elif method == 'tools/list':
            result = {'tools': _tools()}
        elif method == 'tools/call':
            result = _call(message.get('params') or {})
        else:
            return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': f'no method {method}'}}
    except LookupError as no:
        return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32602, 'message': str(no)}}
    return {'jsonrpc': '2.0', 'id': mid, 'result': result}


def serve(stdin=sys.stdin, stdout=sys.stdout):
    for line in stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            reply = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'not JSON'}}
        else:
            reply = answer(message) if isinstance(message, dict) else {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'not a request'}}
        if reply is not None:
            stdout.write(json.dumps(reply) + '\n')
            stdout.flush()
