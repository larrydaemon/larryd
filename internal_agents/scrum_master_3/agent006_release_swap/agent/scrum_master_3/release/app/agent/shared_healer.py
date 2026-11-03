"""THE HEALER: GROUP 2 HEALS ITSELF WHILE HE HOLDS THE LOCK OPEN (the owner 2026-10-24: "we have two groups and it should
be clear ... group 2 the agent itself is broken and this should require an unlock"; asked whether an unlocked agent may
change itself: "go for it").

A red row whose cause is the agent's own (shared_red_rows.group_of) is queued for its healer only while the master lock is
OPEN (shared_red_rows.master_open, his press). shared_red_rows.fix hands such a record here. One healer, one row:

  1. its own tree: a detached worktree of the Scrum Master's repository (settings develop.healer.repo) at HEAD, under
     develop.healer.tree, outside ~/virtual_sanity; the hire (develop.fixer.command, the same guard) edits only there.
  2. the frozen checks (develop.healer.checks) run on that tree BEFORE the hire, once per base commit (kept), and AFTER it.
  3. its change must stay inside develop.healer.ground (the agent's code: never a row's plan, its settings, a test, the
     seal) and must break no check that passed on its base (a check that fails only in the whole run and passes alone is
     the run's order, never the change). Anything else: undone whole, STUCK said.
  4. landed by its own hunks alone on the live repository (git apply, to the files and to the index; another session's
     uncommitted work in the same files stays its own), committed, one healer at a time (a lock).
  5. the page and the round started again (develop.healer.restart), its lesson kept (shared_memory.lesson).

Every place, command and list is read from settings.json at the call (the owner 2026-10-24: dynamic, never hard coded).
    python -m agent.shared_red_rows fix <NNN> [day]   (a record of group AGENT comes here)"""
import datetime
import glob
import json
import os
import re
import subprocess
import time

from agent import shared_where as where

FAILED = re.compile(r'^(?:FAIL|ERROR): (\w+) \(([\w.]+)\)', re.M)


def conf():
    """develop.healer, read now"""
    return dict((where.SETTINGS.get('develop') or {}).get('healer') or {})


def _home(key, c=None):
    """a place of develop.healer, {scratch} his own scratch (settings scratch: the healer's trees live there)"""
    return os.path.abspath(os.path.expanduser(str((c or conf()).get(key) or '').replace('{scratch}', str(where.SCRATCH))))


def tree_of(n, c=None):
    """THIS ROW'S HEALER TREE: develop.healer.tree/<NNN>"""
    return os.path.join(_home('tree', c), f'{int(n):03d}')


def _git(root):
    return lambda *a, **k: subprocess.run(['git', '-C', root, *a], capture_output=True, text=True, **k)


def words_for(rec, agent_file, tree):
    """THE HEALER'S WORDS: the row's red, why it is the agent's, where it may write and what it must never do"""
    c = conf()
    ground = ', '.join(c.get('ground') or [])
    return (f"RED ROW {int(rec['row']):03d} {rec.get('name', '')} of the Scrum Master is red, and the cause is THE AGENT'S OWN "
            f"(the Scrum Master itself, not the platform it watches). Its own words now:\n\n{rec.get('words', '')}\n\n"
            f"Why it is the agent's: {rec.get('cause') or rec.get('said') or 'its words name the agent'}\n"
            f"The row's code: {agent_file}\n"
            f"You are in {tree}, a copy of the Scrum Master's repository. The owner unlocked the agent so it may heal itself "
            f"(the master lock, his press). FIX THE CAUSE here, in plain code, inside {ground} of this copy only.\n"
            "Never change a row's plan or its rule (app/schemas), the settings, a test or a check, the seal (LOCK.sha256) or "
            "anything outside this copy: such a change is undone whole. Never make a red row green by hiding what it "
            "measures or by softening its words; the frozen checks run on your change and one you break undoes it.\n"
            "When the cause is only the owner's hands (a pin, a seal, a lock, a password, a ruling), change nothing and say "
            "his exact steps.\n"
            "Your LAST line is exactly one of:\nFIXED: <what you changed, one line>\nOWNER: <his exact steps, one line>\n"
            "STUCK: <why, one line>\n")


def changed(git):
    """the files the healer's tree differs in from its base, staged, changed or new -> [path]"""
    git('add', '-A')
    got = git('diff', '--cached', '--name-only', '--no-renames', 'HEAD')
    return [l.strip() for l in got.stdout.splitlines() if l.strip()]


def outside(files, c=None):
    """the files outside develop.healer.ground (a row's plan, settings, a test, the seal, anything else) -> [path]"""
    ground = [str(g) for g in (c or conf()).get('ground') or []]
    return [f for f in files if not any(f.startswith(g) for g in ground) or '/tests/' in f or os.path.basename(f).startswith('test_')]


def run_checks(tree, only=(), c=None, runner=subprocess.run):
    """THE FROZEN CHECKS ON A TREE: the whole run (or only these ids, each alone), the tree's app on the path, its records
    a scratch of the run's own (the checks' office). -> (finished, {failed id})"""
    c = c or conf()
    app = os.path.join(tree, 'app')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('SCRUM_MASTER_', 'KNOWLEDGE_'))}
    env.update(SCRUM_MASTER_APP=app, PYTHONPATH=app, WID_ENV=env.get('WID_ENV', 'localhost.rnd'), PYTHONDONTWRITEBYTECODE='1')
    py, checks = _home('python', c), _home('checks', c)
    seconds = int(c.get('checks_minutes') or 15) * 60
    if only:
        bad = set()
        for t in sorted(only):
            got = runner([py, '-m', 'unittest', t], cwd=checks, env=env, capture_output=True, text=True, timeout=seconds)
            if got.returncode != 0:
                bad.add(t)
        return True, bad
    try:
        got = runner([py, '-m', 'unittest', 'discover', '-s', '.', '-p', 'test_*.py'], cwd=checks, env=env, capture_output=True, text=True, timeout=seconds)
    except subprocess.TimeoutExpired:
        return False, set()
    out = (got.stdout or '') + (got.stderr or '')
    return bool(re.search(r'^Ran \d+ tests?', out, re.M)), failed_ids(out)


def failed_ids(out):
    """the failed checks' ids (module.Class.test) from a unittest run's output: 3.14 prints the whole id in the brackets,
    older ones the class alone"""
    return {cls if cls.endswith('.' + name) else f'{cls}.{name}' for name, cls in FAILED.findall(str(out or ''))}


def base_failures(tree, sha, folder, run):
    """THE CHECKS THAT FAIL ON THE BASE ITSELF, run once per base commit and kept (logs: base_<sha>.json). -> set, or None
    when the run did not finish"""
    os.makedirs(folder, exist_ok=True)
    kept = os.path.join(folder, f'base_{sha[:12]}.json')
    try:
        with open(kept, encoding='utf-8') as fh:
            return set(json.load(fh)['failed'])
    except (OSError, ValueError, KeyError):
        pass
    done, failed = run(tree)
    if not done:
        return None
    with open(kept, 'w', encoding='utf-8') as fh:
        json.dump({'sha': sha, 'failed': sorted(failed), 'at': datetime.datetime.now().astimezone().isoformat(timespec='seconds')}, fh)
    return failed


def land(patch, repo, lock_path, message):
    """THE HEALER'S HUNKS ON THE LIVE REPOSITORY, one healer at a time: to the files and to the index (git apply), the
    index holding nothing else first, then committed. -> ('fixed', its commit) or ('stuck', why)"""
    import fcntl
    git = _git(repo)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    with open(lock_path, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if git('diff', '--cached', '--quiet').returncode != 0:
            return 'stuck', "the agent's index holds another's staged change: nothing landed"
        for args in (('apply', '--check', '-'), ('apply', '--cached', '--check', '-')):
            got = git(*args, input=patch)
            if got.returncode != 0:
                return 'stuck', f"its change meets another change in the live agent: {got.stderr.strip()[-160:]}"
        if git('apply', '-', input=patch).returncode != 0:
            return 'stuck', 'its change could not be written into the live agent'
        if git('apply', '--cached', '-', input=patch).returncode != 0:
            git('apply', '-R', '-', input=patch)
            return 'stuck', "its change could not be staged: the live agent's files put back"
        done = git('-c', 'user.name=frost', '-c', 'user.email=frost@MacBookPro.lan', 'commit', '-q', '-F', '-', input=message)
        if done.returncode != 0:
            git('reset', '-q', '--', *_paths(patch))
            git('apply', '-R', '-', input=patch)
            return 'stuck', f"its change could not be committed: {done.stderr.strip()[-160:]}"
        return 'fixed', git('rev-parse', 'HEAD').stdout.strip()


def _paths(patch):
    return sorted(set(re.findall(r'^\+\+\+ b/(.+)$', patch, re.M)))


def restart(c=None, run=subprocess.run):
    """the page and the round started again with the healed code (develop.healer.restart: their LaunchAgents)"""
    uid = os.getuid()
    for label in (c or conf()).get('restart') or []:
        run(['launchctl', 'kickstart', '-k', f'gui/{uid}/{label}'], capture_output=True, text=True)


def message(rec, line):
    return (f"HEALED ROW {int(rec['row']):03d} {rec.get('name', '')}: {line}"[:200] + "\n\n"
            "The agent healed itself while the owner held the master lock open (the owner 2026-10-24: \"group 2 the agent "
            "itself is broken and this should require an unlock\"; \"go for it\").\n"
            f"Its red: {str(rec.get('words') or '')[:400]}\n"
            f"Why the agent's: {str(rec.get('cause') or '')[:300]}\n"
            "Proven: its change inside the agent's code alone, no frozen check broken that passed on its base.\n")


def heal(rec, folder, hire=None, checks=None, restart_=None, lesson=None, last_word=None, is_open=None):
    """ONE HEALER FOR ONE AGENT RED (see the module's words). rec: the loop's record (state fixing, its pid this process).
    -> (word, line, extra) for the record: word fixed, owner or stuck"""
    from agent import shared_developer as developer, shared_red_rows as loop
    c = conf()
    if not (is_open or loop.master_open)():
        return 'stuck', 'the master lock closed before its healer began: nothing heals while it is locked', {}
    repo, n = _home('repo', c), int(rec['row'])
    if not os.path.isdir(os.path.join(repo, '.git')) and not os.path.isfile(os.path.join(repo, '.git')):
        return 'stuck', f'no repository of the agent at {repo} (settings develop.healer.repo)', {}
    git_repo, mine = _git(repo), tree_of(n, c)
    git = _git(mine)
    git_repo('worktree', 'remove', '--force', mine)
    git_repo('worktree', 'prune')
    os.makedirs(os.path.dirname(mine), exist_ok=True)
    made = git_repo('worktree', 'add', '--detach', mine, 'HEAD')
    if made.returncode != 0:
        return 'stuck', f'its own tree could not be made: {made.stderr.strip()[-160:]}', {}
    try:
        for f in glob.glob(os.path.join(repo, 'instance', '*.json')):   # the package's schema beside its app, as the live one has it (not in git)
            os.makedirs(os.path.join(mine, 'instance'), exist_ok=True)
            with open(f, 'rb') as a, open(os.path.join(mine, 'instance', os.path.basename(f)), 'wb') as b:
                b.write(a.read())
        sha = git('rev-parse', 'HEAD').stdout.strip()
        run = checks or (lambda tree, only=(): run_checks(tree, only, c))
        base = base_failures(mine, sha, folder, run)
        if base is None:
            return 'stuck', 'the frozen checks did not finish on its base: nothing to prove a change against', {'base': sha}
        agent_file = next(iter(glob.glob(os.path.join(mine, 'app', 'agent', f'agent{n:03d}_*.py'))), '')
        conf_fixer = developer.CONF['fixer']
        code, said = (hire or developer.hire)(loop.fixer_command(n, conf_fixer['command']), words_for(rec, agent_file, mine), mine, int(c.get('minutes') or conf_fixer['minutes']) * 60)
        word, line = (last_word or loop._last_word)(said)
        files = changed(git)
        if word != 'fixed':
            return word if word in ('owner', 'stuck') else 'stuck', line if word in ('owner', 'stuck') else f'its healer said {word.upper()}: {line}', {'base': sha, 'code': code}
        if not files:
            return 'stuck', 'it said FIXED but changed nothing', {'base': sha, 'code': code}
        bad = outside(files, c)
        if bad:
            return 'stuck', f"its change touched outside the agent's code ({', '.join(bad[:3])}): undone whole", {'base': sha, 'code': code}
        done, after = run(mine)
        if not done:
            return 'stuck', 'the frozen checks did not finish on its change: undone', {'base': sha, 'code': code}
        new = after - base
        if new:
            _, still = run(mine, only=new)   # alone: a check that fails only in the whole run's order is the run's, never the change's
            new = still
        if new:
            return 'stuck', f"its change broke {len(new)} frozen check(s) that passed before it ({', '.join(sorted(new)[:3])}): undone", {'base': sha, 'code': code}
        patch = git('diff', '--cached', '--binary', '--no-renames', 'HEAD').stdout
        word, head = land(patch, repo, os.path.join(folder, 'heal.lock'), message(rec, line))
        if word != 'fixed':
            return 'stuck', head, {'base': sha, 'code': code}
        (restart_ or restart)()
        try:
            from agent import shared_memory as memory, shared_store as store
            (lesson or (lambda: memory.lesson(n, f'healed by the agent itself ({head[:9]}): {line}', str(rec.get('cause') or rec.get('words') or ''), by='the healer', st=store.door())))()
        except Exception:   # noqa: BLE001  (the lesson is kept by the next heal; the heal stands)
            pass
        return 'fixed', line, {'base': sha, 'code': code, 'commit': head, 'files': files}
    finally:
        git_repo('worktree', 'remove', '--force', mine)
        git_repo('worktree', 'prune')

