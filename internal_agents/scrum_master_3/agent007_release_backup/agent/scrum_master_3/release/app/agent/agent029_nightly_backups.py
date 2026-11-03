"""ROW 029 BACKUPS (D THE NIGHTLY, every round): THE BACKUPS EXIST OR NOT (the owner 2026-10-23: "the backups exist or
not. green or red. can not be more simple"). The plan, global_config tower.backups, names each backup: this laptop's
whole backup (folders under tower.backups.local, each with its manifest.json, where mac; made by its own job, label, daily
at tower.backups.daily) and every slot's hourly backup (tower.backups.slots, each its timer; the slots' hourly backups
ARE MEASURED on each slot, read only, gcloud compute ssh, one read a look). Each EXISTS when a good one was made since
its due moment: the laptop's since the last daily time (given GRACE to finish), a slot's inside
tower.backups.fresh.slot_minutes. GREEN when every one exists; RED naming EVERY missing one (none hides another,
nothing held for a late slot), his one step the night's backups step by hand (STEP). A plan that cannot be read is red
with the file and key to fix (PLAN_STEP), never a rerun. Reported, never fixed (R4)."""
#     python -m agent.agent029_nightly_backups check      one look, its run written in row_runs (row 029)
import datetime
import json
import os
import subprocess
import sys

from agent import shared_where as where
from agent import shared_schedule as schedule
from agent import shared_store as store   # row_runs: the row's main
from agent import shared_words as words   # guard() at __main__
from agent import shared_chunks as chunks   # THE 3 MINUTE RULE (the owner 2026-10-23): why first, his one step last

ROW = 29

MANIFEST = 'manifest.json'   # a backup folder's own manifest, written last by the tower: a folder with none is no backup
GRACE = datetime.timedelta(hours=1)   # a scheduled backup may take this long to be made before its slot counts as missed


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def tower():
    """global_config.json's tower block, as the file says it ({} when it cannot be read)."""
    return (_json(where.path('global_config')) or {}).get('tower') or {}


def kept(tw=None):
    """Every whole backup of this laptop, newest first: the manifests under tower.backups.local and the local target's
    RESTORE copy. -> [manifest + name, path]"""
    tw = tower() if tw is None else tw
    folders = []
    local = os.path.expanduser(str((tw.get('backups') or {}).get('local') or ''))
    if local and os.path.isdir(local):
        folders += [os.path.join(local, f) for f in sorted(os.listdir(local))]
    target = (tw.get('targets') or {}).get((tw.get('auto') or {}).get('local') or '') or {}
    if target.get('root') and not target.get('slot'):
        folders.append(os.path.expanduser(target['root']).rstrip(os.sep) + '_RESTORE')
    out = []
    for path in folders:
        m = _json(os.path.join(path, MANIFEST))
        if isinstance(m, dict) and m.get('made_at'):
            out.append({**m, 'name': os.path.basename(path), 'path': path})
    return sorted(out, key=lambda m: str(m['made_at']), reverse=True)


def schedule_of(rule):
    """The laptop backup job's schedule as the tower names it (global_config tower.backups.daily, "HH:MM", local time):
    as a list of {Hour, Minute}. -> list ([] when it does not read)."""
    try:
        hour, minute = (int(x) for x in str(rule.get('daily') or '').split(':'))
    except ValueError:
        return []
    return [{'Hour': hour, 'Minute': minute}] if 0 <= hour < 24 and 0 <= minute < 60 else []


def schedule_said(when):
    """A schedule in plain words: daily at 07:00, hourly at :15. -> words"""
    out = []
    for w in when:
        if 'Hour' in w:
            out.append(('daily' if 'Weekday' not in w else f"weekly (day {w['Weekday']})") + f" at {int(w['Hour']):02d}:{int(w.get('Minute', 0)):02d}")
        else:
            out.append(f"hourly at :{int(w.get('Minute', 0)):02d}")
    return ', '.join(out) or 'no schedule'


def last_slot(when, now):
    """The newest moment the schedule names at or before now (his local time). -> aware datetime or None"""
    now = now.astimezone(schedule.ZONE).replace(second=0, microsecond=0)
    best = None
    for w in when:
        if 'Hour' in w:
            for back in range(0, 8):
                d = (now - datetime.timedelta(days=back)).replace(hour=int(w['Hour']), minute=int(w.get('Minute', 0)))
                if d <= now and ('Weekday' not in w or d.isoweekday() % 7 == int(w['Weekday']) % 7):
                    best = max(best, d) if best else d
                    break
        else:
            for back in range(0, 2):
                d = (now - datetime.timedelta(hours=back)).replace(minute=int(w.get('Minute', 0)))
                if d <= now:
                    best = max(best, d) if best else d
                    break
    return best


def age_said(seconds):
    """3 h 35 min, 12 min, 2 d 4 h. -> words"""
    m = max(0, int(seconds // 60))
    if m >= 48 * 60:
        return f'{m // 1440} d {m % 1440 // 60} h'
    return f'{m // 60} h {m % 60} min' if m >= 60 else f'{m} min'


def laptop(tw=None, now=None):
    """THE LAPTOP'S WHOLE BACKUP, from its real files and its job's own schedule. -> (ok, words): ok True only when the
    newest whole backup is made after the schedule's last slot (that slot given GRACE to finish)."""
    tw = tower() if tw is None else tw
    now = now or datetime.datetime.now(datetime.timezone.utc)
    rule = tw.get('backups') or {}
    mine = [b for b in kept(tw) if b.get('where') == 'mac' and b.get('ok')]
    local = os.path.expanduser(str(rule.get('local') or ''))
    count = len([b for b in mine if local and os.path.dirname(b['path']) == local.rstrip(os.sep)])
    when = schedule_of(rule)
    plan = schedule_said(when) if when else 'its schedule not readable (global_config tower.backups.daily)'
    if not mine:
        return False, f'laptop: no whole backup, {plan}'
    made = datetime.datetime.fromisoformat(mine[0]['made_at'])
    made = made if made.tzinfo else made.replace(tzinfo=datetime.timezone.utc)
    said = f"laptop: {age_said((now - made).total_seconds())} old, {plan}, {count} kept"
    if not when:
        return False, said
    due = last_slot(when, now - GRACE)
    if due is None:
        return False, said + ': its schedule names no moment'
    if made < due:
        return False, said + f': the {schedule._clock(due.isoformat())} backup was not made'
    return True, said + ': inside its schedule'



def _slot_probe(name, timer, reach):
    """ONE SLOT'S HOURLY BACKUP, read on the slot itself (read only): its timer's service, its last run's result and the
    moment it ended, against the slot's own clock. -> (result, age seconds) or None when the slot cannot be read"""
    svc = timer.rsplit('.', 1)[0] + '.service'
    # A RUN IN PROGRESS HAS NO EXIT TIME (2026-10-23: a probe at the top of the hour read the empty ExecMainExitTimestamp
    # as midnight, "1020 min old"): then its age is since this run began (the timer's last trigger), its result 'running'
    remote = (f'e=$(systemctl show {svc} -p ExecMainExitTimestamp --value); a=$(systemctl show {svc} -p ActiveState --value); '
              f'if [ -z "$e" ] || [ "$a" = activating ]; then '
              f'echo running $(date -d "$(systemctl show {timer} -p LastTriggerUSec --value)" +%s) $(date +%s); '
              f'else echo $(systemctl show {svc} -p Result --value) $(date -d "$e" +%s) $(date +%s); fi')
    try:
        got = subprocess.run(['gcloud', 'compute', 'ssh', name, '--project', reach['project'], '--zone', reach['zone'],
                              '--quiet', '--command', remote], capture_output=True, text=True, timeout=60)
        result, ended, clock = got.stdout.split()[-3:]
        return result, int(clock) - int(ended)
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
        return None


def slot_words(tw=None):
    """EVERY SLOT'S HOURLY BACKUP, measured on the slot itself (read only; tower.backups.slots: each its timer;
    tower.certificate.reach: the project and zone; tower.backups.fresh.slot_minutes: how old its last good run may be,
    70 when it names none: one hour between runs plus ten minutes for a run to finish). -> [(name, exists, words)]:
    exists True, False, or None when the slot could not be read (never guessed: missing until read, said plainly)."""
    tw = tower() if tw is None else tw
    backups_ = tw.get('backups') or {}
    reach = (tw.get('certificate') or {}).get('reach') or {}
    fresh = int((backups_.get('fresh') or {}).get('slot_minutes') or 70)
    out = []
    for name, slot in sorted((backups_.get('slots') or {}).items()):
        got = _slot_probe(name, slot.get('timer') or '', reach) if isinstance(slot, dict) and slot.get('timer') and reach else None
        if got is None:
            out.append((name, None, f'{name}: not measured (the slot could not be read)'))
            continue
        result, age = got
        minutes = age // 60
        if result == 'running':   # its hourly run is going now: it exists while younger than fresh, missing when it hangs past it
            ok = minutes <= fresh
            out.append((name, ok, f"{name}: its hourly backup is running now, started {minutes} min ago" + ('' if ok else f', past {fresh} min')))
        elif result != 'success':
            out.append((name, False, f'{name}: its last hourly backup ended {result}, {minutes} min ago'))
        elif minutes > fresh:
            out.append((name, False, f'{name}: {minutes} min old, past {fresh} min'))
        else:
            out.append((name, True, f'{name}: {minutes} min old, inside {fresh} min'))
    return out


def slots(tw=None):
    """THE SLOTS' HOURLY BACKUPS as one line (slot_words). -> (ok, words): None and '' when the tower names no slot;
    False when one is missing or could not be read."""
    tw = tower() if tw is None else tw
    if not (tw.get('backups') or {}).get('slots'):
        return None, ''
    got = slot_words(tw)
    return all(ok is True for _, ok, _ in got), 'slots: ' + ', '.join(said for _, _, said in got)


def plan_fault(tw=None):
    """THE PLAN THAT CANNOT BE READ (global_config tower.backups and what each backup needs to be read). -> (what, the
    key to fix) or None when the plan reads."""
    tw = tower() if tw is None else tw
    rule = tw.get('backups')
    if not isinstance(rule, dict) or not rule:
        return 'global_config.json has no tower.backups', 'tower.backups'
    if not rule.get('local'):
        return 'tower.backups.local names no folder', 'tower.backups.local'
    if not schedule_of(rule):
        return f"tower.backups.daily is not HH:MM ({rule.get('daily')!r})", 'tower.backups.daily'
    reach = (tw.get('certificate') or {}).get('reach') or {}
    for name, slot in sorted((rule.get('slots') or {}).items()):
        if not isinstance(slot, dict) or not slot.get('timer'):
            return f'tower.backups.slots.{name} names no timer', f'tower.backups.slots.{name}.timer'
        if not reach.get('project') or not reach.get('zone'):
            return 'tower.certificate.reach names no project and zone (the slots are read through it)', 'tower.certificate.reach'
    return None


def backups(day, tw=None, now=None):
    """THE BACKUPS EXIST OR NOT, every one judged apart (the laptop's, each slot's). -> schedule.said: ok True when every
    one exists; the words name every missing one first ("backup missing: ..."), then each backup as it is."""
    tw = tower() if tw is None else tw
    lok, lsaid = laptop(tw, now)
    found = slot_words(tw)
    missing = ([lsaid] if not lok else []) + [said for _, ok, said in found if ok is not True]
    ok = not missing
    every = ' · '.join([lsaid] + (['slots: ' + ', '.join(said for _, _, said in found)] if found else []))
    text = (f'all {1 + len(found)} backups exist · ' if ok else 'backup missing: ' + '; '.join(missing) + ' · ') + every
    newest = next((b['made_at'] for b in kept(tw) if b.get('where') == 'mac' and b.get('ok')), '')
    return schedule.said(ok, text, newest, newest)


STEP = chunks.rerun(None, 'backups')   # HIS ONE STEP: the night's backups step by hand (agent/rerun_step.py backups: the laptop's whole backup made, the slots checked)
SIGN_IN = 'gcloud auth login (the slots are read by gcloud compute ssh), then '   # a slot that could not be read: signed in first, the same one line
PLAN_STEP = 'set {key} in {file} (the sealed core: then PIN AND RESEAL)'   # a plan that cannot be read: the value fixed, never a rerun


def step_for(said, tw=None):
    """HIS ONE STEP, the first backup missing (the owner 2026-10-23 20:55: "each piece can trigger the red but only 1 red per
    row"; the others are words in the why): the laptop's is the backups step by hand (STEP); a slot's late one is its own
    timer's service started on the slot now, by the same ssh the probe reads it with; one running past its minutes is that
    service restarted (a start does nothing to a run going); a slot that could not be read: signed in first, then this
    row reads it again."""
    tw = tower() if tw is None else tw
    rule, reach = tw.get('backups') or {}, (tw.get('certificate') or {}).get('reach') or {}
    head = said.split(' · ', 1)[0]
    parts = head[len('backup missing: '):].split('; ') if head.startswith('backup missing: ') else []
    for part in parts[:1]:
        if part.startswith('laptop: '):
            return STEP
        name = part.split(':', 1)[0]
        slot = (rule.get('slots') or {}).get(name)
        if 'the slot could not be read' in part or not (isinstance(slot, dict) and slot.get('timer') and reach.get('project') and reach.get('zone')):
            return SIGN_IN + f'this row reads {name} again at its next round'
        svc = str(slot['timer']).rsplit('.', 1)[0] + '.service'
        verb = 'restart' if 'running now' in part else 'start'
        return (f"{name}'s hourly backup {'again' if verb == 'restart' else 'now'}: gcloud compute ssh {name} --project {reach['project']} --zone {reach['zone']} "
                f"--command 'sudo systemctl {verb} {svc}'; this row reads the slot again")
    return STEP


def check():
    """ROW 029's one look: THE BACKUPS EXIST OR NOT (the owner 2026-10-23: "green or red"). -> (state, text): green when
    every backup the plan names exists; red naming every missing one, why first, his one step last (step_for); a plan
    that cannot be read is red with its key to fix (PLAN_STEP)."""
    tw = tower()
    fault = plan_fault(tw)
    if fault:
        return chunks.chunk(ROW, 'red', f'the backups plan cannot be read: {fault[0]}', step=PLAN_STEP.format(key=fault[1], file=where.path('global_config')))
    word = backups(schedule.cycle(), tw)
    if word['ok'] is True:
        return 'green', word['said']
    return chunks.chunk(ROW, 'red', word['said'], step=step_for(word['said'], tw))


if __name__ == '__main__':
    words.guard()
    sys.exit(store.row_main(ROW, check, sys.argv[1:]))
