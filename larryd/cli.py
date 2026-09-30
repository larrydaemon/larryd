"""The one command: `larryd`."""
import argparse
import json
import sys

from . import doctor, knowledge, mcp, new, runner, skills


def parser():
    p = argparse.ArgumentParser(prog='larryd', description='LARRYD: build an agent for PF HANZO with Claude Code.')
    sub = p.add_subparsers(dest='command', required=True)
    n = sub.add_parser('new', help='make a new agent project')
    n.add_argument('name', help='the agent\'s name, also its folder')
    d = sub.add_parser('doctor', help='check the agent before submission')
    d.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    d.add_argument('--json', action='store_true', help='the result as JSON')
    r = sub.add_parser('run', help='run the agent here, the way PF HANZO runs it, with a sample job')
    r.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    r.add_argument('--job', help='the sample job (default: samples/job.json)')
    r.add_argument('--json', action='store_true', help='the result as JSON')
    sub.add_parser('mcp', help='serve the tools to Claude Code (a local tool server on stdin/stdout)')
    sub.add_parser('skills', help='list the skills an agent may declare, by hash')
    k = sub.add_parser('pack', help='check a knowledge pack and give its hash')
    k.add_argument('folder', help='the pack\'s folder')
    return p


def main(argv=None):
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
    if args.command == 'mcp':
        mcp.serve()
        return 0
    return 2


if __name__ == '__main__':
    sys.exit(main())
