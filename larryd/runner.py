"""`larryd run`: runs the agent on this computer the way PF HANZO runs it, in a scratch world, with a sample job.
- the doctor first: an agent it refuses is not run;
- the job handed is what PF HANZO would hand a RUN: {"do": run.do, ...run.hands}, taken from the sample job;
- its own process under macOS sandbox-exec: no network, no new process, writes only in a scratch run folder (made for
  the run, removed after), reads nothing under /Users but the agent's own folder, an empty environment, a time limit;
- one JSON object out, holding only what "gives" names.
Scratch only: nothing is sent anywhere, no live record is read or written. It needs a Mac today (sandbox-exec)."""
import base64
import binascii
import json
import os
import re
import pathlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

from . import doctor, shape, skills

SANDBOX = '/usr/bin/sandbox-exec'
SECONDS = 20          # PF HANZO's run limit
MOST_BYTES = 1_000_000


@dataclass
class Result:
    state: str                       # DONE · FAILED · REFUSED
    answer: dict | None = None
    reason: str = ''                 # what is wrong, in plain words
    todo: str = ''                   # what to do
    said: str = ''                   # what the agent wrote on stderr (on this computer only; PF HANZO keeps none of it)
    problems: list = field(default_factory=list)


def python():
    """The plain Python runtime (no packages from any virtual environment), as PF HANZO runs agents. A framework build
    starts through its app binary, so that one is the program the sandbox lets start."""
    base = os.path.realpath(sys.base_prefix)
    app = os.path.join(base, 'Resources', 'Python.app', 'Contents', 'MacOS', 'Python')
    return app if os.path.isfile(app) else os.path.realpath(os.path.join(base, 'bin', f'python{sys.version_info.major}.{sys.version_info.minor}'))


def profile(agent, run, runtime):
    base = os.path.realpath(sys.base_prefix)
    return '\n'.join([
        '(version 1)',
        '(allow default)',
        '(deny network*)',
        '(deny process-fork)',
        '(deny process-exec)',
        f'(allow process-exec (literal "{runtime}"))',
        '(deny file-write*)',
        f'(allow file-write* (subpath "{run}") (literal "/dev/null"))',
        '(deny file-read* (subpath "/Users"))',
        f'(allow file-read* (subpath "{agent}") (subpath "{run}") (subpath "{base}"))',
        '',
    ])


def sandboxed(agent, entry, given, seconds=SECONDS):
    """Run one agent folder's entry with `given` on stdin. -> Result (DONE with the answer, or FAILED with why)."""
    if sys.platform != 'darwin' or not os.path.isfile(SANDBOX):
        return Result('REFUSED', reason='larryd run needs a Mac today (it uses macOS sandbox-exec, as LARRYD does)',
                      todo='run it on a Mac; the doctor works everywhere')
    agent = os.path.realpath(agent)
    run = os.path.realpath(tempfile.mkdtemp(prefix='larryd_run_'))
    runtime = python()
    try:
        try:
            done = subprocess.run([SANDBOX, '-p', profile(agent, run, runtime), runtime, '-I', '-B', os.path.join(agent, entry)],
                                  input=json.dumps(given), capture_output=True, text=True, timeout=seconds, cwd=run,
                                  env={'PATH': '/usr/bin:/bin', 'HOME': run, 'TMPDIR': run, 'LC_CTYPE': 'UTF-8'})
        except subprocess.TimeoutExpired:
            return Result('FAILED', reason=f'it ran over the time limit ({seconds} s)', todo='make the answer finish well inside the limit')
        said = done.stderr.strip()
        if done.returncode != 0:
            return Result('FAILED', reason=f'it stopped with exit {done.returncode}', said=said,
                          todo='read what it said below; if it was refused ("Operation not permitted"), it tried to reach out, '
                               'start a process or touch a file outside its run folder: do the work with only what it is handed')
        if len(done.stdout) > MOST_BYTES:
            return Result('FAILED', reason='its answer is longer than 1 MB', said=said, todo='answer with less')
        try:
            answer = json.loads(done.stdout)
        except ValueError:
            answer = None
        if not isinstance(answer, dict):
            return Result('FAILED', reason='its answer is not one JSON object', said=said,
                          todo='print exactly one JSON object on stdout (json.dumps of a dict) and nothing else')
        return Result('DONE', answer=answer, said=said)
    finally:
        shutil.rmtree(run, ignore_errors=True)


def job(root, card, sample):
    """What PF HANZO would hand: {"do": run.do} + each of run.hands, from the sample job. -> (given, None) or (None, Result)."""
    try:
        wanted = json.loads(pathlib.Path(sample).read_text())
    except (OSError, ValueError) as e:
        return None, Result('REFUSED', reason=f'the sample job {sample} is not readable JSON ({type(e).__name__})',
                            todo=f'write {shape.SAMPLE} as one JSON object, e.g. {{"do": "{card["run"]["do"]}"}}')
    if not isinstance(wanted, dict):
        return None, Result('REFUSED', reason='the sample job is not one JSON object', todo=f'write it as {{"do": "{card["run"]["do"]}"}}')
    plan = card['run']
    known = skills.known()
    skill_hands = [known[h]['hand'] for h in card.get('skills') or [] if h in known and known[h].get('hand')]
    if wanted.get('do', plan['do']) != plan['do']:
        return None, Result('REFUSED', reason=f'the sample job does "{wanted["do"]}", but a RUN does "{plan["do"]}" (run.do)',
                            todo=f'set "do" in the sample job to "{plan["do"]}"')
    extra = sorted(set(wanted) - {'do'} - set(plan['hands']) - set(skill_hands))
    if extra:
        return None, Result('REFUSED', reason=f'the sample job holds {extra}, which LARRYD would not hand (run.hands is {plan["hands"]})',
                            todo='take them out of the sample job; the agent gets only what run.hands names')
    missing = [h for h in list(plan['hands']) + skill_hands if h not in wanted]
    if missing:
        return None, Result('REFUSED', reason=f'the sample job has no {missing}, which run.hands names',
                            todo=f'add {missing} to the sample job, shaped as LARRYD hands them')
    if 'job' in plan['hands']:
        inputs, job = card.get('inputs') or {}, wanted['job']
        if not isinstance(job, dict):
            return None, Result('REFUSED', reason='the sample job\'s "job" is not {name: value}',
                                todo=f'write it as {{"job": {{{", ".join(repr(n) + ": ..." for n in inputs)}}}}}')
        extra = sorted(set(job) - set(inputs))
        if extra:
            return None, Result('REFUSED', reason=f'the sample job\'s "job" holds {extra}, which "inputs" does not declare (LARRYD would refuse the run)',
                                todo='take them out of the sample job, or declare them in "inputs"')
        for name, value in sorted(job.items()):
            if not isinstance(value, str) or len(value) > shape.MOST_INPUT:
                return None, Result('REFUSED', reason=f'the input "{name}" is not text of at most {shape.MOST_INPUT} characters (LARRYD would refuse the run)',
                                    todo='make every input plain text, and shorter')
    return {'do': plan['do'], **{h: wanted[h] for h in list(plan['hands']) + skill_hands}}, None


def run(root, sample=None, seconds=SECONDS):
    root = pathlib.Path(root).resolve()
    problems = doctor.check(root)
    if problems:
        return Result('REFUSED', reason='the doctor found problems; LARRYD would not take this agent',
                      todo='fix each problem below, then run `larryd run` again', problems=problems)
    card = json.loads((root / shape.AGENT / shape.MANIFEST).read_text())
    given, refused = job(root, card, sample or root / shape.SAMPLE)
    if refused:
        return refused
    result = sandboxed(root / shape.AGENT, card['entry'], given, seconds)
    if result.state == 'DONE':
        extra = sorted(set(result.answer) - set(card['gives']))
        if extra:
            return Result('FAILED', answer=result.answer, said=result.said, reason=f'the answer holds {extra}, which "gives" does not name',
                          todo='name them in "gives" in agent.json, or take them out of the answer')
        wrong = _files(card, result.answer)
        if wrong:
            return Result('FAILED', answer=result.answer, said=result.said, reason=wrong[0], todo=wrong[1])
    return result


FILE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 ._-]{0,120}$')
MOST_FILES = 10


def _files(card, answer):
    """The files an answer carries, checked as LARRYD checks them before it stores them in the member's DA-M: -> None, or
    (what is wrong, what to do)."""
    files = answer.get('files')
    if files is None:
        return None
    known = skills.known()
    if not any(known.get(h, {}).get('after') == 'files' for h in card.get('skills') or []):
        return ('the answer carries files, but the agent does not declare the DA-M store', 'declare the DA-M store in "skills" (`larryd skills` gives its hash)')
    if not isinstance(files, list) or len(files) > MOST_FILES:
        return (f'"files" is not a list of at most {MOST_FILES}', f'answer at most {MOST_FILES} files, as a list')
    for i, f in enumerate(files, 1):
        if not (isinstance(f, dict) and set(f) == {'name', 'content_b64'} and isinstance(f['name'], str) and FILE_NAME.match(f['name'])
                and isinstance(f['content_b64'], str)):
            return (f'file {i} is not {{"name", "content_b64"}} with a plain name', 'give each file a plain name (no folder) and its bytes as base64, nothing else')
        try:
            raw = base64.b64decode(f['content_b64'], validate=True)
        except (binascii.Error, ValueError):
            return (f'file {i} is not base64', 'put each file\'s bytes in content_b64 as base64')
        if not raw:
            return (f'file {i} is empty', 'answer only files that hold something')
    return None


def report(result):
    lines = [f'larryd run: {result.state}']
    if result.state == 'DONE':
        lines.append(json.dumps(result.answer, indent=2))
    else:
        lines.append(f'{result.reason}. What to do: {result.todo}')
        lines += [p.text() for p in result.problems]
    if result.said:
        lines += ['the agent said (on this computer only):', result.said]
    return '\n'.join(lines)


def as_json(result):
    return {'state': result.state, 'answer': result.answer, 'reason': result.reason, 'todo': result.todo, 'said': result.said,
            'problems': [doctor.asdict(p) for p in result.problems]}
