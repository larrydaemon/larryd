"""The one command: `larryd`."""
import argparse
import datetime
import json
import pathlib
import sys

from . import __version__, doctor, knowledge, mcp, new, place, runner, skills, submit


def parser():
    p = argparse.ArgumentParser(prog='larryd', description='LARRYD. Your server has a daemon. Your agents should have one too. Build, test and ship AI agents with Claude Code.')
    p.add_argument('--version', action='version', version=f'larryd {__version__}')
    sub = p.add_subparsers(dest='command', required=True)
    n = sub.add_parser('new', help='make a new agent project')
    n.add_argument('name', help='the agent\'s name, also its folder')
    n.add_argument('--from', dest='example', choices=['marketplace'], help='start from a LARRYD example agent (marketplace: the PF agent marketplace)')
    d = sub.add_parser('doctor', help='check the agent before submission')
    d.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    d.add_argument('--json', action='store_true', help='the result as JSON')
    d.add_argument('--fix', action='store_true', help='write the agent\'s card sheet in the platform\'s form, fill the card (originals kept in .larryd/doctor_backup/), then check again')
    d.add_argument('--badge', action='store_true', help=f'also write {doctor.BADGE} beside agent/: PASS or FAIL, the day, the checks\' version, for your README')
    r = sub.add_parser('run', help='run the agent here, the way LARRYD runs it, with a sample job')
    r.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    r.add_argument('--job', help='the sample job (default: samples/job.json)')
    r.add_argument('--json', action='store_true', help='the result as JSON')
    s = sub.add_parser('submit', help='send the agent to LARRYD for review: the doctor, one file, then sign in with Google or Apple in the browser')
    s.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    s.add_argument('--json', action='store_true', help='the result as JSON')
    s.add_argument('--no-browser', action='store_true', help='print the claim page instead of opening it')
    pl = sub.add_parser('place', help='put the agent on your own LARRYD\'s shelf (the runtime on this computer): the doctor, one file, held in its locker')
    pl.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    pl.add_argument('--json', action='store_true', help='the result as JSON')
    c = sub.add_parser('card', help='place the agent and open the marketplace page: every agent on this computer as a card with its hire toggle')
    c.add_argument('path', nargs='?', default='.', help='the agent project (default: here)')
    c.add_argument('--json', action='store_true', help='the result as JSON')
    c.add_argument('--no-browser', action='store_true', help='print the page\'s address instead of opening it')
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
            root = new.make(args.name, example=args.example)
        except ValueError as no:
            print(f'larryd new: {no}', file=sys.stderr)
            return 1
        print(f'made {root}/ · open it with Claude Code: cd {root} && claude')
        return 0
    if args.command == 'doctor':
        notes = [] if args.json else doctor.conversions(args.path)   # what becomes the menu (the owner, 2026-10-06), said before --fix removes the sheet, so the author learns it
        if args.fix:
            for change in doctor.fix(args.path):
                print(f'FIXED {change}')
        problems = doctor.check(args.path)
        print(json.dumps(doctor.as_json(problems), indent=2) if args.json else doctor.report(args.path, problems))
        for note in notes:
            print(f'CONVERTED {note}')
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
    if args.command == 'submit':
        try:
            out = submit.submit(args.path, open_browser=not args.no_browser)
        except submit.Refused as no:
            out = no.as_json()
        print(json.dumps(out, indent=2) if args.json else _said(out))
        return 0 if out['ok'] else 1
    if args.command in ('place', 'card'):
        try:
            out = place.place(args.path) if args.command == 'place' else place.card(args.path, open_browser=not args.no_browser)
        except place.Refused as no:
            out = no.as_json()
        print(json.dumps(out, indent=2) if args.json else _placed(args.command, out))
        return 0 if out['ok'] else 1
    if args.command == 'mcp':
        mcp.serve()
        return 0
    return 2


def _placed(command, out):
    if not out['ok']:
        lines = [f'larryd {command}: {out["wrong"]}. What to do: {out["todo"]}']
        return '\n'.join(lines + [doctor.Problem(**p).text() for p in out.get('problems', [])])
    where = ' (opened in your browser)' if out.get('opened') else ''
    return f'larryd {command}: held {out["held"].get("name", "the agent")} as {out["agent_key"]}. The marketplace: {out["marketplace"]}{where}'


def _said(out):
    if not out['ok']:
        lines = [f'larryd submit: {out["wrong"]}. What to do: {out["todo"]}']
        return '\n'.join(lines + [doctor.Problem(**p).text() for p in out.get('problems', [])])
    where = 'opened in your browser' if out['opened'] else 'open it in your browser'
    return ''.join(f'FIXED {c}\n' for c in out.get('sheets', [])) + (f'larryd submit: sent ({out["sha256"][:16]}). Sign in with Google or Apple to submit it, within {out["minutes"]} minutes:\n'
            f'{out["claim"]}   ({where})')


if __name__ == '__main__':
    sys.exit(main())
