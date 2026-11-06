"""THE RED, THE FRAME'S OWN (the owner 2026-10-27, list 3 item 8: "whatever is broken or stuck it hires an agent to fix it and keeps working
until fixed"; list 4 item 7, 13:18: "still missing skills tasks, live, red", its home app/frame/frame_red.py; item 8, 13:24: "only frame they do
not do anythign on thier own / it needs an agent like scrum master to run it"; 2026-10-21: "a row NOT DONE runs the thing that forces it
done, immediately, by itself (never 'nobody is working on it')"; 2026-10-22: "keep trying to fix it"): the original Scrum Master's rows 7, 15
and 25 and its WHY IT'S RED table as ONE frame file, for every agent of every office, drawn in the LIVE group. It has no slot, no job and no
schedule of its own: the office's Scrum Master (its agent001) runs it with the frame's reads, on its RUN AGENT; on a served page its round
also comes every SECONDS on the page's own timer, as the frame's stream and samplers run there (a check's app is never served). It imports
the standard library and the frame alone.

WHAT IS RED, and nothing else: an agent of this office whose job's last run today ended FAILED or REFUSED (the X board's red words; the LIVE
stream's own check is one of them when its stream is dark), or whose RUN is open (QUEUED, DROPPED, RUNNING) with no sign of life for over 3
minutes (stuck), or which was due by its job's SCHEDULE over 3 minutes ago and has no run since (missed: a shell whose card was never
registered has its RUN refused and never runs). Each is one row: Agent | Why it's red (the run's own last words) | Red since | Who works on
it | Your 3 min.

THE HIRE: every red with nothing forcing it gets ONE FIXER NOW, in its own detached worktree of this office's repo under ~/scratch/red
(<office>/<agent>/<try>), the original's fixer command (shared_developer CONF fixer, its disallowed list whole) and brief (shared_red_rows
words_for); the ground is this office's app/, the wall the frame, the web, the schemas, every test and check, the platform's core and LARRYD
(a change there undoes the whole turn). FIXED with a change: committed in its tree, applied by that one commit on this office's repo, the
red agent run again to prove it (green closes the row; red again is the next chunk). OWNER: his one step, nothing changed. AGENT: the file
and line of the frame or core that is the cause. STUCK: hired again after RETRY (30 minutes). A fixer is stopped by its own pid only. Each
fixer's end is a LARRYD log (RUN 0) on the Scrum Master's job.

ITS OWN RULE (its light): GREEN when nothing is red, or every red agent forces its own fix (its fixer alive, its fix applied and its rerun
pending, or the owner's one step said from its fixer's OWNER line); RED when a red has nothing working on it (no fixer could be hired) or
its fixer is stuck and its retry is not due yet, the first such row's step as YOUR 3 MIN. It is never green by hiding a red: every red is a
row of WHY IT'S RED."""
import datetime
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import zoneinfo

from frame import frame_replica as frame

NAME = 'The Red'
WHAT = 'Whatever is broken or stuck: it hires an agent to fix it and keeps working until fixed, every red under 3 minutes'
GROUP = 'LIVE'   # where the frame draws it: the LIVE group (the owner 2026-10-27: "and live is LIVE")
RULE = {'data_job_rule': "Every red agent of this office forces its own fix: a fixer hired at once, its fix applied, or the owner's step.",   # ITS OWN RULE, in the six parts the RULES button shows
        'data_job_rule_fix': "His one step is on the row as YOUR 3 MIN: the fixer's OWNER line, or why its fixer is stuck and when it is hired again by itself.",
        'data_job_rule_red': 'when a red agent has nothing working on it (no fixer could be hired) or its fixer is stuck and its retry is not due yet',
        'data_job_rule_green': "when nothing is red, or every red agent has its fixer alive, its fix applied with its rerun pending, or the owner's one step said"}
SECONDS = 60   # one round a minute on a served page (the original's row 25: "every round")
FIRST = 10   # seconds after the page is served to its first round
QUIET = datetime.timedelta(minutes=3)   # no sign of life for over 3 minutes: stuck (the original's row 7)
LATE = datetime.timedelta(minutes=3)   # due by its schedule and no run 3 minutes on: missed
HIRE = True   # A RED GETS AN AGENT WORKING ON IT (the owner 2026-10-27: "and if it has a red an agent should be working on it / that was in the original spec"; off from 15:18 until his word, and this is his word)
RETRY = datetime.timedelta(minutes=30)   # a stuck fixer is hired again after this long (the original's shared_red_rows RETRY)
HOME = '~/scratch/red'   # the fixers' own trees: <office>/<agent>/<try>, removed when the fixer's turn ends
REPO = None   # the repo a fixer's tree is made from: this office's own (frame.OFFICE); a check hands a scratch one
FIXER = {'command': ['claude', '-p', '--model', 'claude-opus-5-5', '--permission-mode', 'acceptEdits', '--allowedTools', 'Read,Edit,Write,Glob,Grep,Bash,WebFetch,WebSearch',   # THE ORIGINAL'S FIXER, word for word (scrum_master schemas/settings.json develop.fixer, the CONF['fixer'] in use)
                     '--disallowedTools', 'Task,NotebookEdit,Bash(git push:*),Bash(git commit:*),Bash(git reset:*),Bash(git checkout:*),Bash(git switch:*),Bash(git restore:*),Bash(git rebase:*),Bash(git merge:*),Bash(git branch:*),Bash(git tag:*),Bash(git worktree:*),Bash(git stash:*),Bash(git add:*),Bash(git rm:*),Bash(git clean:*),Bash(gcloud:*),Bash(gsutil:*),Bash(ssh:*),Bash(scp:*),Bash(rsync:*),Bash(sudo:*),Bash(launchctl:*),Bash(kill:*),Bash(pkill:*),Bash(killall:*),Edit(//Users/frost/virtual_sanity_records/**),Write(//Users/frost/virtual_sanity_records/**),Edit(//Users/frost/virtual_sanity/**),Write(//Users/frost/virtual_sanity/**),Edit(//Users/frost/scratch/reports/**),Write(//Users/frost/scratch/reports/**),Edit(//Users/frost/scratch/tests/**),Write(//Users/frost/scratch/tests/**),Edit(//Users/frost/scratch/requests/**),Write(//Users/frost/scratch/requests/**),Edit(//Users/frost/spine_scratch/**),Write(//Users/frost/spine_scratch/**),Edit(//Users/frost/.claude/**),Write(//Users/frost/.claude/**)'],
          'minutes': 25}
DONE_WORDS = ('FIXED', 'OWNER', 'AGENT', 'STUCK')   # the fixer's last line begins with one of these
GROUND = 'app'   # the office's app is the fixer's ground,
WALL = ('app/frame', 'app/web', 'app/schemas')   # but the frame, the web and the schemas are read and never changed
CHECKS = (':(icase,glob)**/tests/**', ':(icase,glob)**/checks/**', ':(icase,glob)**/test_*.py')   # no test or check, ever
LIVE = {}   # this page's fixers at work: {red key: thread}
RECS = {}   # what forces each red, this page's own word (the LARRYD logs carry each fixer's end across a start)
STATE = {}   # each page's last round: {its store's file: what it found}
_LOCK = threading.RLock()


# ---- the moments
def _utc(text):
    """a record's stamp (the pipeline's, UTC) as an aware moment, None when none"""
    try:
        return datetime.datetime.fromisoformat(str(text)).replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None


def _local(text):
    """a run's start or end (this machine's own time) as an aware moment, None when none"""
    try:
        return datetime.datetime.fromisoformat(str(text)).astimezone()
    except (TypeError, ValueError):
        return None


def _hm(at, zone):
    return at.astimezone(zone).strftime('%H:%M') if at else ''


def _iso(at):
    return at.isoformat(timespec='seconds') if at else ''


def _now(zone):
    return datetime.datetime.now(zone)


def ticking(since, now):
    """RED SINCE's clock: D DAYS : HH : MM : SS"""
    s = max(0, int((now - since).total_seconds())) if since else 0
    return f'{s // 86400} DAYS : {s % 86400 // 3600:02d} : {s % 3600 // 60:02d} : {s % 60:02d}'


def model_said(command):
    """the fixer's model in words: claude-opus-5-5 is Opus 5.5"""
    m = command[command.index('--model') + 1] if '--model' in command else ''
    parts = m.split('-')[1:]
    return f"{parts[0].capitalize()} {'.'.join(parts[1:])}" if parts else m


# ---- WHAT IS RED
def due_at(job, runs, now, zone):
    """When its job's SCHEDULE made it due and no run came since, over LATE ago: that moment; None when it is not due or ran.
    every N minute(s): N minutes after its last run (or its job's birth); daily HH:MM: today's HH:MM in its zone, for a job born before it.
    live (the owner 2026-10-27: "not 5 minutes not anything else"): NEVER missed: it runs on every change of its triggers, and only its RED (its run) counts."""
    kind = str(job.get('data_job_schedule_type') or '').lower()
    if kind == 'live':
        return None
    born = _utc(job.get('system_created_at'))
    last = max((t for t in (_local(r['started_at']) for r in runs) if t), default=None)
    every = re.fullmatch(r'every (\d+) minutes?', kind)
    if every:
        due = (last or born) + datetime.timedelta(minutes=int(every.group(1))) if (last or born) else None
    elif kind == 'daily' and re.fullmatch(r'\d\d:\d\d', str(job.get('data_job_time') or '')):
        tz = zoneinfo.ZoneInfo(job.get('data_job_timezone') or zone.key)
        h, m = (int(x) for x in job['data_job_time'].split(':'))
        due = now.astimezone(tz).replace(hour=h, minute=m, second=0, microsecond=0)
        if (born and born > due) or (last and last >= due):
            return None
    else:
        return None
    return due if due and now - due > LATE else None


def file_of(name, chain, job_key):
    """the red agent's own program: its module's file, or the file of this office's agent folder whose NAME is the job's name"""
    for m, sh in chain or ():
        if sh.get('job_key') == job_key:
            return os.path.basename(m.__file__)
    folder = os.path.join(frame.APP, 'agent')   # the office's own agents
    for f in sorted(os.listdir(folder)) if os.path.isdir(folder) else ():
        if re.fullmatch(r'agent\d{3}_[a-z0-9_]+\.py', f):
            with open(os.path.join(folder, f), encoding='utf-8') as fh:
                if re.search(r"^NAME = '" + re.escape(name) + "'", fh.read(), re.M):
                    return f
    return ''


def what_is_red(store, shells, rule, now=None, chain=()):
    """EVERY RED OF THIS OFFICE NOW, one row each: FAILED or REFUSED today, stuck, or missed (module doc); a shell switched off is off. -> [{'key', 'name', 'file', 'kind', 'why', 'since', 'shell'}]"""
    zone = zoneinfo.ZoneInfo(rule['zone'])
    now = now or _now(zone)
    out = []
    for sh in shells:
        job = sh.get('job') or {}
        if not job or not sh.get('on', True):
            continue
        name = job.get('data_full_name') or sh['job_key']
        runs = [r for r in store.runs(sh['job_key'], 50) if r['n']]   # its runs (a log alone, n 0, is not a run)
        state = job.get('data_job_run_state') or ''
        life = _utc(job.get('system_updated_at'))
        red = None
        if state in frame.OPEN_RUN and life and now - life > QUIET:
            red = ('stuck', f"RUN {job.get('data_job_run') or ''} {state} since {_hm(life, zone)}: no sign of life for over 3 minutes", life)
        elif frame.light_of(job, rule, now) == 'red':
            trail = []
            for r in runs:   # newest first: the runs red in a row, the oldest of them is when it went red
                if r['exit'] == 0:
                    break
                trail.append(r)
            why = frame.run_said(runs[0]) if runs else f'its RUN ended {state}'
            red = ('failed', why, _local(trail[-1]['started_at']) if trail else life)
        else:
            due = due_at(job, runs, now, zone)
            if due:
                said = str(job.get('data_job_schedule_type') or '') + (f" {job.get('data_job_time')}" if job.get('data_job_time') else '')
                why = f'missed: due by its schedule ({said}) at {_hm(due, zone)} and no run since'
                if not job.get('data_agent_key'):
                    why += ' · its shell holds no agent: its card was never registered, so its RUN is refused (Add agent first)'
                red = ('missed', why, due)
        if red:
            out.append({'key': sh['job_key'], 'job_key': sh['job_key'], 'name': name, 'file': file_of(name, chain, sh['job_key']), 'kind': red[0], 'why': red[1], 'since': _iso(red[2]), 'shell': sh['id'],
                        'keyless': not job.get('data_agent_key')})
        bad = rules_red(job)
        if bad:   # ITS RULES RED, the same records the X board reads (the owner 2026-10-27: "also you just fucking lied too"): one row of its own, a fixer on it too
            out.append({'key': sh['job_key'] + '#rules', 'job_key': sh['job_key'], 'name': name, 'file': file_of(name, chain, sh['job_key']), 'kind': 'rules', 'why': f'RULES: {bad}',
                        'since': _iso(_utc(job.get('system_updated_at')) or now), 'shell': sh['id'], 'keyless': False})
    return out


def rules_red(job):
    """WHY A JOB'S RULES ARE RED (SKILLS_POSITIVE_FEEDBACK_BUILD 3.3, step 4: a red clears only when the agent's check says GREEN and the review
    says LEGIT): the blind review STUPID, or a DRIFT or TAMPER lie detector. -> the reason in words, or '' when not red"""
    if str(job.get('data_job_rules_review_verdict') or '') == 'STUPID':
        return str(job.get('data_job_rules_review_description') or '') or 'the review said STUPID'
    if str(job.get('data_job_lie_detector') or '') in ('DRIFT', 'TAMPER'):
        return f"its lie detector says {job.get('data_job_lie_detector')}"
    return ''   # ITS RULES STATUS RED alone is its own run's red (a row of its own here) or a job never run yet (any blank is RED by default): never a second row, never a fixer


# ---- THE RECORD: each fixer's end is a LARRYD log (RUN 0, a log alone) on the job of the agent that runs the frame's reads (the Scrum
# Master, the office's agent001); the round itself is this page's own word (STATE), drawn and streamed, never a log a minute
def _said(r):
    try:
        s = json.loads(r['said'])
    except (TypeError, ValueError):
        return {}
    return s if isinstance(s, dict) else {}


def load(store, log_job):
    """What forces each red: every fixer's end kept on the log job (oldest first, the newest word last), then this page's own (its fixers at
    work, their pids). -> {red key: rec}"""
    recs = {}
    for r in reversed(store.runs(log_job, 400) if log_job else ()):
        s = _said(r)
        if not r['n'] and isinstance(s.get('fixer'), dict) and s['fixer'].get('key'):
            recs[s['fixer']['key']] = s['fixer']
    with _LOCK:
        recs.update({k: dict(v) for k, v in RECS.items() if v.get('own') == (log_job or store.db_path)})
    return recs


def _alive(key):
    t = LIVE.get(key)
    return bool(t and t.is_alive())


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (TypeError, ValueError, ProcessLookupError, PermissionError):
        return False


def _stop(pid):
    """a fixer left by a page that ended: stopped by its own pid (its own group: it started its session), never by a name"""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(int(pid), sig)
        except (TypeError, ValueError, ProcessLookupError, PermissionError):
            return
        time.sleep(0.2)


def needs_fixer(rec, red, now):
    """Whether this red gets a fixer now: nothing forces it (no record, the chain moved on since its fix, new words after the owner's or
    the agent's line, a fixer of a page that ended), or its stuck fixer's retry is due."""
    if not rec:
        return True
    s, same = rec.get('state'), rec.get('words') == red['why']
    if s in ('fixing', 'applied') and _alive(red['key']):
        return False
    if s == 'fixing':   # its thread is gone: the page that hired it ended
        if rec.get('pid') and _pid_alive(rec['pid']):
            _stop(rec['pid'])
        return True
    if s in ('owner', 'agent'):
        return not same
    if s in ('stuck', 'applied'):
        ended = datetime.datetime.fromisoformat(rec['ended']) if rec.get('ended') else None
        return not same or not ended or now - ended >= RETRY
    return True   # fixed, yet red again: the next chunk; unhired: try again


def forcing(rec, red):
    """THE LAW (the original's row 25): a fixer alive on it, its fix applied and its rerun pending, or his own step written for these words."""
    s = (rec or {}).get('state')
    if s in ('fixing', 'applied') and (_alive(red['key']) or s == 'applied'):
        return True
    return s == 'owner' and bool(rec.get('step')) and rec.get('words') == red['why']


def who(rec, zone):
    """Who works on it, in words (the brief's own shapes); never held, never waiting."""
    rec = rec or {}
    s, at = rec.get('state'), lambda k: _hm(datetime.datetime.fromisoformat(rec[k]) if rec.get(k) else None, zone)
    if s == 'fixing':
        return f"fixer hired {at('hired')}, try {rec.get('try', 1)} ({rec.get('model', '')}, its own tree)"
    if s == 'applied':
        return f"fix applied {at('ended')}, rerun pending"
    if s == 'fixed':
        return f"FIXED {at('ended')} · {rec.get('said', '')}"
    if s == 'stuck':
        again = datetime.datetime.fromisoformat(rec['ended']) + RETRY if rec.get('ended') else None
        return f"STUCK {at('ended')} · {rec.get('said', '')} · hired again at {_hm(again, zone)}"
    if s == 'owner':
        return f"OWNER · {rec.get('step', '')}"
    if s == 'agent':
        return f"AGENT · {rec.get('said', '')}"
    return f"no fixer could be hired: {rec.get('said', '')}"


def step_of(rec, red, zone):
    """YOUR 3 MIN: his one step, the fixer's OWNER line (or AGENT's file and line); for a red nothing forces, what clears it."""
    s = (rec or {}).get('state')
    if s == 'owner':
        return rec.get('step', '')
    if s == 'agent':
        return rec.get('said', '')
    if s == 'stuck':
        again = datetime.datetime.fromisoformat(rec['ended']) + RETRY if rec.get('ended') else None
        return f"read why its fixer is stuck ({rec.get('said', '')}); its next try starts by itself at {_hm(again, zone)}"
    if s == 'unhired':
        return f"{rec.get('said', '')}; then RUN AGENT on The Red"
    return ''


# ---- THE HIRE (the original's shared_developer.hire and shared_red_rows.fix, for one red of this office)
def hire(command, words, cwd, seconds, started=None):
    """ONE HIRED FIXER, its words on stdin, a clock on it, a session of its own, stopped whole by its own pid when its clock runs out:
    the few words a program needs of this laptop's environment and nothing else. -> (exit code or None, what it said)"""
    env = {k: os.environ[k] for k in ('HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'LC_ALL', 'TMPDIR', 'TERM') if k in os.environ}
    env.update({'PATH': frame.path('job_path') + ':' + os.environ.get('PATH', '/usr/bin:/bin'), 'PYTHONDONTWRITEBYTECODE': '1', 'SCRUM_MASTER_HIRE': '1'})   # the heard hook never takes a hire's words for the owner's
    try:
        child = subprocess.Popen([os.path.expanduser(x) for x in command], cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 start_new_session=True, env=env)
    except OSError as e:
        return None, f'no fixer could be started ({type(e).__name__})'
    if started:
        started(child.pid)
    try:
        said, _ = child.communicate(words, timeout=max(30, int(seconds)))
        code = child.returncode
    except subprocess.TimeoutExpired:
        said, code = '', None
    finally:
        _stop(child.pid)
    return code, said or ''


def all_info(job, known):
    """EVERYTHING ABOUT THE AGENT FOR ITS FIXER (3.3, step 2; the owner 2026-10-27: "all info should be sent to claude code when something breaks"):
    its rule's parts 1 to 7 from its job, its GREEN skills only (a RED skill is never in a fix prompt), its knowledge entries, past lessons first."""
    job = job or {}
    parts = '\n'.join(f'{n}. {label}: {job.get("data_job_" + f) or ""}' for n, (label, f) in enumerate((('RULE (the system owner\'s)', 'rule'), ('STATUS', 'rules_status'),
                       ('WHY IT CAN BE FIXED WITHIN 3 MINUTES', 'rule_fix'), ('RED', 'rule_red'), ('GREEN', 'rule_green'), ('REVIEW VERDICT', 'rules_review_verdict'),
                       ('REVIEW', 'rules_review_description')), 1))
    green = '\n'.join(f'- {e["kind"].upper()}: {e["line"]}' for e in frame.job_skills(job) if e['state'] == 'green') or '- none'
    return f"\nITS RULE:\n{parts}\n\nITS SKILLS (GREEN only):\n{green}\n\nITS KNOWLEDGE:\n" + ('\n'.join(f'- {k}' for k in known) or '- none') + '\n\n'


def words_for(red, office, tree, job=None, known=()):
    """THE FIXER'S BRIEF (the original's words_for, for this office), with everything about the agent (all_info); a RULES red: its program made to
    do what its rule says. The fixer changes the agent's program only: never data_job_rule, never a rule part, never a skill."""
    info = all_info(job, known)
    if red.get('kind') == 'rules':
        return (f"THE RED of the {os.path.basename(office)} office: the RULES of its agent {red['name']} ({red['file'] or 'its program'}) are red. Why:\n\n{red['why']}\n"
                + info +
                f"Its program is app/agent/{red['file']} (read it whole). You are in {tree}, this red's own copy of the office's repo. MAKE THE PROGRAM DO WHAT ITS RULE "
                "SAYS: fix it here, inside app/agent/, within 3 minutes. Never write the rule, a rule part or a skill: they are read again from the program "
                "after your fix and reviewed blind. Never change app/frame, app/web, app/schemas, a test, a check or the platform's core (~/virtual_workspace): "
                "such a change is undone whole. Never make a red green by hiding what the rule measures.\n"
                "Your LAST line is exactly one of:\nFIXED: <what you changed, one line>\nOWNER: <his exact steps, one line>\n"
                "AGENT: <the frame's or the core's own file and line that is the cause, one line>\nSTUCK: <why, one line>\n")
    reg = (f"This agent's shell holds no agent key: its card was never registered in LARRYD, so its RUN is refused. That step is not the "
           f"owner's: run {os.path.join(office, 'app', 'agent', 'run')} register yourself (seconds), then say FIXED: registered.\n") if red.get('keyless') else ''
    return (f"THE RED of the {os.path.basename(office)} office: its agent {red['name']} ({red['file'] or 'its program'}) is red. Its own words now:\n\n{red['why']}\n" + info +
            f"Its program is app/agent/{red['file']} (read it). You are in {tree}, this red's own copy of the office's repo. FIX THE CAUSE the "
            "words name, here, in plain code, inside app/. Never change app/frame, app/web, app/schemas, a test, a check, the platform's core "
            "(~/virtual_workspace) or LARRYD: such a change is undone whole. Never change the agent's rule or what it measures; never make a red "
            "agent green by hiding what it measures.\n"
            "When the cause is only the owner's hands (a pin, a seal, a lock, a password, a ruling between his words, his written GO), change "
            "nothing and say his exact steps.\n"
            "Say only what the words carry: never a count, a file or a fault they do not name. A step of yours is never his written GO, a merge, "
            "a branch move, a push or a sudo install, nor a lock or unlock the words do not name as the cause.\n"
            "THE TWO GROUPS: the agent's own program is yours to fix here; the frame (app/frame), the web (app/web), the schemas, the platform's "
            "core and LARRYD you may read and never change: when the cause lies there, change nothing and name its file and line.\n" + reg +
            "Your LAST line is exactly one of:\nFIXED: <what you changed, one line>\nOWNER: <his exact steps, one line>\n"
            "AGENT: <the frame's or the core's own file and line that is the cause, one line>\nSTUCK: <why, one line>\n")


def last_word(said):
    for line in reversed([x.strip() for x in str(said or '').splitlines() if x.strip()]):
        for w in DONE_WORDS:
            if line.upper().startswith(w + ':'):
                return w.lower(), line.split(':', 1)[1].strip()
    return 'stuck', 'its fixer gave no last word'


def _differs(git, paths):
    changed = git('diff', '--quiet', '--no-renames', 'HEAD', '--', *paths)
    new = git('ls-files', '--others', '--exclude-standard', '--', *paths)
    return changed.returncode != 0 or new.returncode != 0 or bool(new.stdout.strip())


def _links(git):
    held, new = git('ls-files', '-s'), git('ls-files', '--others', '--exclude-standard', '-z')
    if held.returncode != 0 or new.returncode != 0:
        return -1
    root = git('rev-parse', '--show-toplevel').stdout.strip()
    return sum(1 for x in held.stdout.splitlines() if x.startswith('120000 ')) + sum(1 for p in new.stdout.split('\0') if p and os.path.islink(os.path.join(root, p)))


def undo(git):
    git('reset', '-q', 'HEAD', '--', '.')
    git('checkout', '-q', 'HEAD', '--', '.')
    git('clean', '-fdq', '--', '.')
    if _differs(git, ('.',)):
        raise RuntimeError('THE TREE COULD NOT BE PUT BACK: a person looks at it')


def wall(git, links_before):
    """WHAT THE FIXER'S TURN TOUCHED: '' (this office's app alone, never its frame, web or schemas) or 'outside' (anything else, a test or
    a check, a new link: the whole turn undone, proven undone)."""
    if (_differs(git, CHECKS) or _differs(git, WALL) or _differs(git, ('.', f':(exclude){GROUND}')) or _links(git) < 0 or _links(git) > links_before):
        undo(git)
        return 'outside'
    return ''


def _keep(store, own, rec):
    """the record of a red: this page's word now, and a fixer's end as a LARRYD log (RUN 0: a log alone) on the log job"""
    with _LOCK:
        RECS[rec['key']] = dict(rec, own=own or store.db_path)
    if own and rec.get('state') != 'fixing':
        at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"THE RED · {rec.get('name', '')} · {rec.get('state', '').upper()} · {rec.get('said', '')}"[:300]
        store.ran(own, 0, at, at, 0 if rec['state'] in ('fixed', 'applied', 'owner') else 1, json.dumps({'summary': line, 'fixer': {k: v for k, v in rec.items() if k != 'own'}}), '')


def start(store, own, red, rec, chain, agent, now, hire_with=None, repo=None, home=None):
    """ONE FIXER FOR ONE RED, NOW: its own detached worktree of this office's repo, then its turn in a thread of this page (the round
    answers at once). -> its record"""
    zone_now = now.isoformat(timespec='seconds')
    office = repo or REPO or frame.OFFICE
    git_office = lambda *a: subprocess.run(['git', '-C', office, *a], capture_output=True, text=True)
    top = git_office('rev-parse', '--show-toplevel')
    n = int((rec or {}).get('try') or 0) + 1
    rec = {'key': red['key'], 'name': red['name'], 'file': red['file'], 'words': red['why'], 'try': n, 'hired': zone_now, 'model': model_said(FIXER['command'])}
    if top.returncode != 0:
        rec.update(state='unhired', said=f"this office is not a git repo ({office}): no tree for a fixer", ended=zone_now)
        _keep(store, own, rec)
        return rec
    office = top.stdout.strip()
    tree = os.path.join(os.path.expanduser(home or HOME), os.path.basename(office), (os.path.splitext(red['file'])[0] or re.sub(r'\W+', '_', red['name'].lower())) + ('_rules' if red.get('kind') == 'rules' else ''), str(n))
    if os.path.exists(tree):
        git_office('worktree', 'remove', '--force', tree)   # an old one of this red's, left by a fixer that died
    git_office('worktree', 'prune')
    os.makedirs(os.path.dirname(tree), exist_ok=True)
    made = git_office('worktree', 'add', '--detach', tree, 'HEAD')
    if made.returncode != 0:
        rec.update(state='unhired', said=f"its own tree could not be made: {made.stderr.strip()[-160:]}", ended=zone_now)
        _keep(store, own, rec)
        return rec
    rec.update(state='fixing', tree=tree, pid=None)
    _keep(store, own, rec)
    t = threading.Thread(target=_turn, args=(store, own, red, dict(rec), office, tree, chain, agent, hire_with or hire), daemon=True)
    LIVE[red['key']] = t
    t.start()
    return rec


def _turn(store, own, red, rec, office, tree, chain, agent, hire_with):
    """THE FIXER'S TURN (the original's fix): hired in its tree; the wall; FIXED and a change: committed there, applied by that one
    commit on the office's repo, the red agent run again; its tree removed whole at the end."""
    git = lambda *a: subprocess.run(['git', '-C', tree, *a], capture_output=True, text=True)
    git_office = lambda *a: subprocess.run(['git', '-C', office, *a], capture_output=True, text=True)
    now = lambda: datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    try:
        links = _links(git)

        def started(pid):
            rec['pid'] = pid
            _keep(store, own, rec)
        held = next(((m, sh) for m, sh in chain or () if sh.get('job_key') == red.get('job_key')), (None, {}))
        known = [f"{e['kind'].upper()} · {e['line']}" for e in sorted(frame.knowledge(agent, held[0]), key=lambda e: e['kind'] != 'lesson')] if held[0] else []
        code, said = hire_with(FIXER['command'], words_for(red, office, tree, held[1].get('job'), known), tree, int(FIXER['minutes']) * 60, started)
        word, line = last_word(said)
        rec.update(code=code, last=line, pid=None)
        if wall(git, links) == 'outside':
            word, line = 'stuck', 'its change touched outside the ground (the frame, the web, the schemas, a test or a check, or outside app/): undone whole'
        elif _differs(git, ('.',)):
            if word == 'fixed':
                git('add', '-A')
                done = git('commit', '-q', '-m', f"THE RED · {red['name']}: {line}"[:300])
                if done.returncode != 0:
                    word, line = 'stuck', 'its change could not be committed: undone'
                else:
                    sha = git('rev-parse', 'HEAD').stdout.strip()
                    picked = git_office('cherry-pick', sha)
                    if picked.returncode != 0:
                        git_office('cherry-pick', '--abort')
                        word, line = 'stuck', f"its fix {sha[:9]} meets another change of this office: not applied"
                    else:
                        rec['commit'] = git_office('rev-parse', 'HEAD').stdout.strip()
                        word = 'applied'
            else:
                undo(git)   # a change without FIXED is never kept
        elif word == 'fixed':
            word = 'applied' if red.get('keyless') or red.get('kind') == 'rules' else 'stuck'   # a card registered, or a rule part written through the door, changes no file: its next run proves it
            line = line if red.get('keyless') or red.get('kind') == 'rules' else 'it said FIXED but changed nothing'
        if word == 'owner':
            rec['step'] = line
        rec.update(state=word, said=line, ended=now())
        _keep(store, own, rec)
        if word == 'applied':
            rec.update(_rerun(store, red, chain, agent))
            rec['ended'] = now()
            _keep(store, own, rec)

    except Exception as e:   # noqa: BLE001  (a fixer's turn that breaks is stuck, said; never a silent record)
        rec.update(state='stuck', said=f'its turn broke: {type(e).__name__}: {e}'[:200], ended=now(), pid=None)
        _keep(store, own, rec)
    finally:
        git_office('worktree', 'remove', '--force', tree)
        git_office('worktree', 'prune')


def lesson(agent, red, rec):
    """A RED TURNED GREEN, ITS LESSON INTO THE KNOWLEDGE STORE (the owner 2026-10-27: "make sure the fix when red to green get documented into the
    knowledge base or the feedback loop will never work it will be stuck forever we want it to improve forever"): under the agent's row, the red's own
    words (the symptom), what the fixer changed, its commit (as FIX <commit>, the form the skills read) and its minutes; the next skills read turns it
    into a skill, the next fixer of the same agent gets it first."""
    row = f"{frame.NAME}/{red.get('file') or ''}"
    commit = str(rec.get('commit') or '')[:7]
    try:
        minutes = round((datetime.datetime.fromisoformat(rec.get('cleared') or rec['ended']) - datetime.datetime.fromisoformat(rec['hired'])).total_seconds() / 60, 1)
    except (KeyError, TypeError, ValueError):
        minutes = ''
    did = rec.get('said') or rec.get('last') or ''
    text = (f"RED: {red.get('why') or rec.get('words') or ''}\nFIX: {did}\nTRY {rec.get('try') or 1} · {minutes} MIN from hired to green\n\n"
            f"COMMIT {commit} · {row} · {rec.get('cleared') or rec.get('ended') or ''}")
    frame.remember(f"lesson-{frame.NAME}-{commit or re.sub(r'[^0-9]+', '', str(rec.get('hired') or ''))}", 'lesson', f"{red.get('name') or ''}: {did}"[:280],
                   f"FIX {commit}: {did}"[:400] if commit else f"FIX: {did}"[:400], row, 'frame_red', text)


def learned(agent, store, own, reds, recs, now):
    """EVERY RED THAT TURNED GREEN SINCE THE LAST ROUND gets its lesson, once: a fixer's record whose red is no longer red, its fix applied (a commit
    or a change through the door), not yet learned. -> the keys learned"""
    out = []
    red_keys = {r['key'] for r in reds}
    for key, rec in list(recs.items()):
        if key in red_keys or rec.get('learned') or rec.get('state') not in ('applied', 'fixed'):
            continue
        rec = {**rec, 'learned': True, 'cleared': now.isoformat(timespec='seconds')}
        lesson(agent, {'name': rec.get('name'), 'file': rec.get('file'), 'why': rec.get('words')}, rec)
        recs[key] = rec
        _keep(store, own, rec)
        out.append(key)
    return out


def _rerun(store, red, chain, agent):
    """THE PROOF: the red agent's program read again from its file and RUN AGENT on its shell; green closes the row (FIXED), red again is
    the next chunk (the next round hires again with the new words). -> the record's new state"""
    if red.get('kind') == 'rules':   # A RULES RED IS PROVEN BY A NEW READ: the agent that runs the frame's reads (the office's agent001) runs its chain again
        slot = frame.SETTINGS['root_shape']['agent_slot']
        reader = next(((m, sh) for m, sh in chain or () if sh.get('slot') == slot), None)
        if reader is None:
            return {'state': 'applied', 'said': 'a new read at its next time: the page holds no agent that reads the chain'}
        red = {**red, 'key': reader[1]['job_key']}
        module = reader[0]
        after = lambda: not rules_red(next((sh['job'] for sh in store.board() if sh.get('job_key') == red.get('job_key')), {}) or {})
    else:
        module, after = None, None
    module = module or next((m for m, sh in chain or () if sh.get('job_key') == red['key']), None)
    if module is None:
        return {'state': 'applied', 'said': 'rerun at its next time: the page holds no program for this shell yet'}
    spec = importlib.util.spec_from_file_location(module.__name__, module.__file__)   # its program read again from its own file, into the same module
    spec.loader.exec_module(module)
    shell = next((sh for sh in store.board() if sh.get('job_key') == red['key']), None)
    ok, said = store.run(shell['id']) if shell else (False, 'its shell is gone')
    if not ok:
        return {'state': 'stuck', 'said': f'its rerun was refused: {said}'}
    shells = store.board()
    n = int(next(sh for sh in shells if sh['id'] == shell['id'])['job']['data_job_run'] or 0)
    try:
        module.run(store, red['key'], n, agent, shells, chain=chain)
    except Exception as e:   # noqa: BLE001
        return {'state': 'fixed', 'said': f'applied; its rerun broke: {type(e).__name__}', 'rerun': 'red'}
    job = next((sh['job'] for sh in store.board() if sh.get('job_key') == red['key']), {}) or {}
    green = after() if after else job.get('data_job_run_state') == frame.SETTINGS['root_shape']['x_board']['done']
    return {'state': 'fixed', 'rerun': 'green' if green else 'red'}


# ---- ONE ROUND
def rows(reds, recs, zone):
    """the table's rows, words alone"""
    out = []
    for r in reds:
        rec = recs.get(r['key'])
        since = datetime.datetime.fromisoformat(r['since']) if r['since'] else None
        out.append({'key': r['key'], 'job_key': r.get('job_key') or r['key'], 'kind': r.get('kind', ''), 'agent': r['name'], 'file': r['file'], 'why': r['why'], 'since': r['since'], 'since_at': _hm(since, zone),
                    'who': who(rec, zone), 'step': step_of(rec, r, zone), 'forcing': forcing(rec, r)})
    return out


def round_(store, shells, chain, agent, log_job='', rule=None, now=None, hire_with=None, repo=None, home=None):
    """ONE ROUND (run by the Scrum Master with the frame's reads, and on a served page every SECONDS): every red of this office now, a fixer
    hired NOW for each red nothing forces, the table and its own light kept as this page's word. log_job: the job a fixer's end is logged on
    (the Scrum Master's). -> what it found"""
    t0 = time.monotonic()
    rule = rule or frame.SETTINGS['root_shape']['x_board']
    zone = zoneinfo.ZoneInfo(rule['zone'])
    now = now or _now(zone)
    recs = load(store, log_job)
    reds = what_is_red(store, shells, rule, now, chain=chain)
    learned(agent, store, log_job, reds, recs, now)   # RED TO GREEN, DOCUMENTED: every fixed red gone since the last round leaves its lesson
    for r in reds:
        if needs_fixer(recs.get(r['key']), r, now):
            if HIRE or hire_with:   # a check's fake hire still runs; a real fixer only on the owner's order
                recs[r['key']] = start(store, log_job, r, recs.get(r['key']), chain, agent, now, hire_with, repo, home)
    table = rows(reds, recs, zone)
    loose = [t for t in table if not t['forcing']]
    if not table:
        state, summary = 'green', 'nothing is red: every agent of this office did its job today or is not due yet'
    elif not loose:
        state, summary = 'green', ', '.join(f"{t['agent']} by {t['who']}" for t in table)
    else:
        state, summary = 'red', f"not forced: {', '.join(t['agent'] for t in loose)} · YOUR 3 MIN: {loose[0]['step']}"
    said = {'state': state, 'summary': summary, 'reds': table, 'log_job': log_job, 'at': now.isoformat(timespec='seconds'), 'took': round(time.monotonic() - t0, 3)}
    with _LOCK:
        STATE[store.db_path] = said
    return said


# ---- WHAT THE FRAME DRAWS OF IT (words, never markup)
def now_table(store):
    """the page's last round, each row's who and step as its fixer's record says now. -> (the last round, its rows) or (None, [])"""
    s = STATE.get(store.db_path)
    if s is None:
        return None, []
    zone = zoneinfo.ZoneInfo(frame.SETTINGS['root_shape']['x_board']['zone'])
    recs = load(store, s.get('log_job') or '')
    out = []
    for t in s.get('reds') or ():
        rec = recs.get(t['key'])
        red = {'key': t['key'], 'why': t['why']}
        out.append({**t, 'who': who(rec, zone) if rec else t['who'], 'step': step_of(rec, red, zone) if rec else t['step'], 'forcing': forcing(rec, red) if rec else t['forcing']})
    return s, out


def light(store):
    """its own light: the rule above, on the rows as they stand now; '' before a first round"""
    s, table = now_table(store)
    if s is None:
        return ''
    return 'green' if all(t['forcing'] for t in table) else 'red'


def content(store):
    """ITS OWN CONTENT ON THE ONE CANVAS: the table (Agent | Why it's red | Red since | Who works on it | Your 3 min), RED SINCE ticking, his
    one step a copy line under its row."""
    s, table = now_table(store)
    if s is None:
        return [{'kind': 'note', 'title': 'Whatever is red', 'text': f'Not looked yet: the Scrum Master runs it with the frame\'s reads (RUN AGENT), and a served page every minute from {FIRST} seconds after its start.'}]
    return [{'kind': 'table', 'title': 'Whatever is red', 'under': s.get('summary') or '',
             'columns': ['Agent', "Why it's red", 'Red since', 'Who works on it', 'Your 3 min'],
             'rows': [{'key': t['key'], 'cells': [t['agent'], t['why'], {'text': f"RED SINCE {t['since_at']}", 'since': t['since']}, t['who'], 'YOUR 3 MIN' if t['step'] else ''],
                       'copy': f"YOUR 3 MIN: {t['step']}" if t['step'] else ''} for t in table],
             'empty': 'Nothing is red: every agent of this office did its job today or is not due yet.'}]


def stream_part(store):
    """what the page's live stream sends of it: reds, each row's RED SINCE and who works on it (the original's stream sent its reds)"""
    s, table = now_table(store)
    return {t['key']: {'since': t['since'], 'who': t['who']} for t in table}


def days(store, zone):
    """ITS ROWS (the canvas foot): each fixer's turn today and yesterday, from its records, as an agent's runs are drawn"""
    s = STATE.get(store.db_path) or {}
    tz = zoneinfo.ZoneInfo(zone)
    today = _now(tz).date()
    turns = sorted(load(store, s.get('log_job') or '').values(), key=lambda r: r.get('hired') or '', reverse=True)
    out = []
    for day, word in ((today, 'TODAY'), (today - datetime.timedelta(days=1), 'YESTERDAY')):
        mine = [r for r in turns if r.get('hired') and datetime.datetime.fromisoformat(r['hired']).astimezone(tz).date() == day]
        runs = []
        for r in mine:
            a = datetime.datetime.fromisoformat(r['hired'])
            b = datetime.datetime.fromisoformat(r['ended']) if r.get('ended') else None
            runs.append({'start': _hm(a, tz), 'end': _hm(b, tz), 'min': str(int(round(((b - a).total_seconds() if b else 0) / 60))), 'ok': r.get('state') in ('fixed', 'owner', 'applied'),
                         'said': f"{r.get('name', '')} · try {r.get('try', 1)} · {who(r, tz)}"})
        out.append({'head': f'{day.strftime("%a %b %d").upper()} ({word}) · ITS FIXERS', 'runs': runs})
    return out


def why_rows(store):
    """WHY IT'S RED, the original's rows (scrum.html lines 125 to 128, web/page.why_red; the owner 2026-10-27: "look at the fuckign original"; "make
    sure its exactly like the origianl"): one row a red agent of this office, as the last round left it and its fixer's record says now: its name
    (the frame has no row numbers: the agent's name alone), OWNER when only his hands clear it, the one plain sentence that fixes it (the fixer's
    step, else its why), the why behind it, working ("FIXING NOW") or IDLE, and its red-since moment. -> [row]"""
    s, table = now_table(store)
    out = []
    for t in table if s is not None else ():
        owner = t['who'].startswith('OWNER')
        fix = t['step'] or ('Make the rule and the code say the same, then RUN AGENT for a new read.' if t.get('kind') == 'rules' else t['why'])
        out.append({'key': t['key'], 'job_key': t.get('job_key') or t['key'], 'name': t['agent'], 'file': t['file'], 'why': t['why'], 'fix': fix, 'owner': owner,
                    'working': t['who'].startswith('fixer hired'), 'doing': 'FIXING NOW', 'red_since': t['since']})
    return out


def now_line(store):
    """THE LINE UNDER THE RED COUNT, the original's #scrum-now (scrum.html line 113; the owner 2026-10-27: "missing IDLE under it and cycle time"):
    WORKING ON the red a fixer works on now, from its fixer's start; STUCK ON a red whose fixer is stuck, from its end; else IDLE, from the last
    round's end (its cycle). -> {'word', 'name', 'since'}"""
    s, table = now_table(store)
    if s is None:
        return {'word': 'IDLE', 'name': '', 'since': ''}
    recs = load(store, s.get('log_job') or '')
    for t in table:
        rec = recs.get(t['key']) or {}
        if rec.get('state') == 'fixing' and _alive(t['key']):
            return {'word': 'WORKING', 'name': t['agent'], 'since': rec.get('hired') or ''}
    for t in table:
        rec = recs.get(t['key']) or {}
        if rec.get('state') == 'stuck':
            return {'word': 'STUCK', 'name': t['agent'], 'since': rec.get('ended') or ''}
    return {'word': 'IDLE', 'name': '', 'since': s.get('at') or ''}
