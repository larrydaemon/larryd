"""The one command: `larryd`."""
import argparse
import datetime
import getpass
import json
import pathlib
import sys

from . import __version__, doctor, hanzo, knowledge, mcp, new, runner, skills


def parser():
    p = argparse.ArgumentParser(prog='larryd', description='LARRYD. Your server has a daemon. Your agents should have one too. Build, test and ship AI agents with Claude Code.')
    p.add_argument('--version', action='version', version=f'larryd {__version__}')
    sub = p.add_subparsers(dest='command', required=True)
    n = sub.add_parser('new', help='make a new agent project')
    n.add_argument('name', help='the agent\'s name, also its folder')
    d = sub.add_parser('doctor', help='check the agent before submission')
    d.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    d.add_argument('--json', action='store_true', help='the result as JSON')
    d.add_argument('--badge', action='store_true', help=f'also write {doctor.BADGE} beside agent/: PASS or FAIL, the day, the checks\' version, for your README')
    r = sub.add_parser('run', help='run the agent here, the way LARRYD runs it, with a sample job')
    r.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    r.add_argument('--job', help='the sample job (default: samples/job.json)')
    r.add_argument('--json', action='store_true', help='the result as JSON')
    y = sub.add_parser('key', help='keep your developer key (the secret is read from stdin, never the command line); alone: where a key comes from')
    y.add_argument('address', nargs='?', help='LARRYD\'s address, as LARRYD gave it')
    y.add_argument('developer', nargs='?', help='your developer name, as LARRYD made it')
    s = sub.add_parser('submit', help='send the agent to LARRYD, for FROST\'s review')
    s.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    s.add_argument('--json', action='store_true', help='the result as JSON')
    t = sub.add_parser('status', help='what LARRYD records for your agents')
    t.add_argument('--json', action='store_true', help='the result as JSON')
    v = sub.add_parser('developer', help='on your own LARRYD (the daemon on this machine): make a developer who may submit an agent')
    v.add_argument('action', choices=['add'])
    v.add_argument('name', help='the developer\'s name (small letters, digits, dashes)')
    v.add_argument('agent_key', help='the agent\'s card key the developer may submit')
    sub.add_parser('mcp', help='serve the tools to Claude Code (a local tool server on stdin/stdout)')
    sub.add_parser('help', help='these commands; `larryd` alone starts the daemon (LARRYD\'s runtime on 127.0.0.1)')
    sub.add_parser('skills', help='list the skills an agent may declare, by hash')
    k = sub.add_parser('pack', help='check a knowledge pack and give its hash')
    k.add_argument('folder', help='the pack\'s folder')
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:   # bare `larryd`: the daemon, LARRYD's runtime on this machine
        from . import daemon
        return daemon.run()
    if argv == ['help']:
        parser().print_help()
        return 0
    args = parser().parse_args(argv)
    if args.command == 'new':
        try:
            root = new.make(args.name)
        except ValueError as no:
            print(f'larryd new: {no}', file=sys.stderr)
            return 1
        print(f'made {root}/ · open it with Claude Code: cd {root} && claude')
        return 0
    if args.command == 'doctor':
        problems = doctor.check(args.path)
        print(json.dumps(doctor.as_json(problems), indent=2) if args.json else doctor.report(args.path, problems))
        if args.badge:
            root = pathlib.Path(args.path).resolve()
            if root.is_dir():
                (root / doctor.BADGE).write_text(doctor.badge(problems, datetime.date.today().isoformat()))
                print(f'wrote {root / doctor.BADGE}: paste ![LARRYD checks]({doctor.BADGE}) into your README', file=sys.stderr if args.json else sys.stdout)
        return 1 if problems else 0
    if args.command == 'run':
        result = runner.run(args.path, args.job)
        print(json.dumps(runner.as_json(result), indent=2) if args.json else runner.report(result))
        return 0 if result.state == 'DONE' else 1
    if args.command == 'skills':
        for h, s in skills.known().items():
            print(f'{h}  {s["name"]} ({s["technology"]}): {s["does"]}. The agent: {s["agent"]}')
        return 0
    if args.command == 'pack':
        digest, wrong = knowledge.check(args.folder)
        print('\n'.join(f'FAIL {w}' for w in wrong) if wrong else digest)
        return 1 if wrong else 0
    if args.command == 'key':
        if not args.address or not args.developer:
            print(hanzo.WHERE_KEYS_COME_FROM)
            return 0 if not args.address else 1
        secret = getpass.getpass('your developer secret: ') if sys.stdin.isatty() else sys.stdin.readline()
        try:
            path = hanzo.save_key(args.address, args.developer, secret.strip())
        except hanzo.Refused as no:
            print(f'larryd key: {no.wrong}. What to do: {no.todo}', file=sys.stderr)
            return 1
        code, answer = hanzo.call(hanzo.key(), 'GET', '/developer/status', {})
        if code == 200:
            print(f'kept in {path} (yours only) · LARRYD knows you: {len(answer.get("agents", []))} agent(s) yours')
            return 0
        if code == 0:
            print(f'kept in {path} (yours only) · not checked: LARRYD does not answer at {args.address.rstrip("/")}')
            return 0
        print(f'larryd key: kept in {path}, but LARRYD refused it ({code}). What to do: {hanzo.todo(code)}', file=sys.stderr)
        return 1
    if args.command in ('submit', 'status'):
        try:
            out = hanzo.submit(args.path) if args.command == 'submit' else hanzo.status()
        except hanzo.Refused as no:
            out = no.as_json()
        print(json.dumps(out, indent=2) if args.json else _said(args.command, out))
        return 0 if out['ok'] else 1
    if args.command == 'developer':
        from . import daemon
        return daemon.developer_add(args.name, args.agent_key)
    if args.command == 'mcp':
        mcp.serve()
        return 0
    return 2


def _said(command, out):
    if not out['ok']:
        lines = [f'larryd {command}: {out["wrong"]}. What to do: {out["todo"]}']
        return '\n'.join(lines + [doctor.Problem(**p).text() for p in out.get('problems', [])])
    if command == 'submit':
        review = out['review'] or {}
        return (f'larryd submit: {out["agent_key"]} is held by LARRYD\ncode {out["code_sha256"]}\nmanifest {out["manifest_sha256"]}\n'
                f'FROST\'s review: {review.get("state", "unknown")}')
    lines = ['larryd status:']
    for a in out['agents']:
        runs = ', '.join(f'{n} {s}' for s, n in sorted(a['runs'].items())) or 'no runs'
        note = f' ({a["note"]})' if a.get('note') else ''
        lines.append(f'{a["agent_key"]} · {"held" if a["held"] else "not held"} · review: {a["review"]}{note} · {runs} · {a["calls"]} calls · '
                     f'hired {a["hires"]}, unhired {a["unhires"]} · {a["charged"]} mTok charged')
    return '\n'.join(lines if out['agents'] else lines + ['no agent is yours yet'])


if __name__ == '__main__':
    sys.exit(main())
