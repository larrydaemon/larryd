"""The one command: `larryd`."""
import argparse
import json
import sys

from . import doctor, new, runner


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
    return 2


if __name__ == '__main__':
    sys.exit(main())
