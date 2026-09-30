"""The one command: `larryd`."""
import argparse
import sys

from . import new


def parser():
    p = argparse.ArgumentParser(prog='larryd', description='LARRYD: build an agent for PF HANZO with Claude Code.')
    sub = p.add_subparsers(dest='command', required=True)
    n = sub.add_parser('new', help='make a new agent project')
    n.add_argument('name', help='the agent\'s name, also its folder')
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
    return 2


if __name__ == '__main__':
    sys.exit(main())
