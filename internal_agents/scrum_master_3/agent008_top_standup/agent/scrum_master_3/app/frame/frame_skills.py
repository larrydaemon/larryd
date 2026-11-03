"""FRAME · SKILLS (SKILLS_POSITIVE_FEEDBACK_BUILD 3.2; the owner 2026-10-27: "a list of 10 skills"; "instant memorized info with no lookup"; "it knows
how to do things based on sentences not code"; "populates to the max each time to 10"; "should match what is in the knowledge base too"; "the green is
by a review so if a review makes one red that rule sits there and is not included in a prompt to fix it"): AN AGENT'S SKILLS ARE ITS JOB'S OWN
FIELDS in LARRYD (jobs species, group sanity), exactly 10, data_job_skill_N_status (GREEN or RED, from the blind review), _type (any type that
makes sense), _description (where to look, what to look for, what to do). WRITTEN by one read on Opus 5.5 from the agent's program, its knowledge
entries (the knowledge store's skills index, read where it is, read only) and its rule; REVIEWED BLIND by a second read. The MARK IV agent's run
(agent001) calls it for every agent of its chain; the shell's bottom panel reads them from the record. No table of its own anywhere."""
import os
import re

from frame import frame_replica as frame

TEN, index, entries_of = frame.TEN, frame.index, frame.job_skills   # the frame's shared pieces (frame_replica)
SECONDS = 420                                     # one read, at most (as the rules')


def numbered(job, kind):
    """HOW MANY NUMBERED ROWS THE RECORD HOLDS for a kind (skill or rule): its data_job_<kind>_N_status fields, counted from the record the door
    hands (the jobs species' own shape), never typed; 0 when the record has none."""
    head = f'data_job_{kind}_'
    return sum(1 for k in (job or {}) if k.startswith(head) and k.endswith('_status') and k[len(head):-len('_status')].isdigit())




LINE = re.compile(r'^\s*(\d{1,2})\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*$')   # a written skill: N | TYPE | the skill; a reviewed one: N | GREEN or RED | why
FIX = re.compile(r' · FIX ([0-9a-f]{7})$')   # A SKILL FROM A REAL FIX ends with the commit it came from: the only kind kept


def numbered_lines(said, most=TEN):
    """{N: (second, third)} for the lines N | x | y of an answer, N from 1 to most, the last said for each N."""
    got = {}
    for line in str(said or '').splitlines():
        m = LINE.match(line)
        if m and 1 <= int(m.group(1)) <= most:
            got[int(m.group(1))] = (one_line(m.group(2)), one_line(m.group(3)))
    return got


def one_line(text):
    return ' '.join(str(text or '').replace('\u2014', ', ').replace('\u2013', '-').split())


SKILL = ("A skill is ONE plain sentence of clear instructions for Claude Code, learned from a real fix: the symptom it sees (the red's words or what "
         "the page shows), the exact place to look (a file, a table, a log, a port, a button by name), the exact thing to do, and how to confirm it is "
         "GREEN again. Never a description of how the code works; never a copy of the fix's words; true of the program as it is now.")


def write_words(agent, file, source, job, fixes, seen=()):
    """THE WRITER'S WORDS (3.2): the agent's program whole, its rule, and the real fixes to turn into skills, one skill each, in order."""
    name = (agent or {}).get('name') or 'the replica'
    rule = (job or {}).get('data_job_rule') or ''
    return (f"You write SKILLS for ONE agent of the {name} office, so the next red of the same kind is fixed within 3 minutes. PROGRAM agent/{file}.\n\n"
            + SKILL + "\nYou may read the other files of agent/ and schemas/settings.json; read nothing else.\n\n"
            f"Write exactly {len(fixes)} lines, one for each real fix below, in the same order, and nothing else, plain words, no em dashes, each at most 400 characters:\n"
            "N | TYPE | the skill\n(N from 1; TYPE one to four words in capitals naming the red it handles.)\n\n"
            f"ITS RULE: {rule}\n\nWHAT HAS BROKEN BEFORE (the original's history, most often first):\n" + ('\n'.join(f'- {h}' for h in seen) or '- none') + "\n\nTHE REAL FIXES:\n" + '\n\n'.join(f'{i}. {f["text"] or f["summary"]}' for i, f in enumerate(fixes, 1))
            + f"\n\nTHE PROGRAM, whole (agent/{file}):\n\n{source}")


def review_words(agent, file, source, fixes, skills):
    """THE BLIND REVIEWER'S WORDS (3.2): the program, the real fixes and the skills only; GREEN or RED for each, one line why."""
    name = (agent or {}).get('name') or 'the replica'
    return (f"You are the REVIEWER of the SKILLS of ONE agent of the {name} office. PROGRAM agent/{file}.\n\n"
            + SKILL + "\nMark a skill GREEN only when it is all of that: it names a symptom, a place to look, an action and a confirmation, it is true of the "
            "program below as it is now, and it would let Claude Code fix that red in under 3 minutes. RED when it describes the code instead of saying what to do, "
            "is out of date, is vague, or repeats another skill. You do not rewrite anything.\n"
            "You may read the other files of agent/ and schemas/settings.json; read nothing else.\n\n"
            f"Answer with exactly {len(skills)} lines and nothing else, plain words, no em dashes:\nN | GREEN or RED | one line why (at most 200 characters)\n\n"
            "THE SKILLS:\n" + '\n'.join(f'{i} | {t} | {d}' for i, (t, d) in enumerate(skills, 1)) + "\n\nTHE REAL FIXES THEY CAME FROM:\n"
            + ('\n'.join(f'- {f["summary"]}' for f in fixes) or '- none') + f"\n\nTHE PROGRAM, whole (agent/{file}):\n\n{source}")


def remember(file, n, kind, text, why):
    """A RED SKILL'S REASON INTO THE KNOWLEDGE STORE (3.2, step 5), under the agent's row."""
    row = f"{frame.NAME}/{file}"
    frame.remember('skill-red-' + re.sub(r'[^a-z0-9]+', '-', f'{frame.NAME}-{file}-{kind}'.lower()).strip('-'), 'note', f'RED SKILL {n} of {row} · {kind}',
                   f'{text} · REVIEW: {why}', row, 'frame_skills review')


def review(run, settings, app, path, agent, file, source, fixes, skills):
    """THE BLIND REVIEW of these skills [(type, description)]: ['GREEN' or 'RED', why] each, or None when the review does not mark them all."""
    if not skills:
        return []
    rc, said = run(frame.reader_command(settings), review_words(agent, file, source, fixes, skills), app, SECONDS, path)
    marks = numbered_lines(said, len(skills)) if rc == 0 else {}
    if len(marks) != len(skills) or any(m[0].upper() not in ('GREEN', 'RED') for m in marks.values()):
        return None
    return [(marks[i][0].upper(), marks[i][1]) for i in range(1, len(skills) + 1)]


def read_chain(store, agent, chain, settings=None, app=None, hire_with=None, force=False):
    """THE SKILLS OF THE CHAIN FROM REAL FIXES (the owner 2026-10-27: "if we do real fixes and then they are in the knowledge base too at least that gives
    us a correct baseline and then in the future a rule should only be changed if it becomes outdated or a new better rule replaces it"): each agent's
    ten slots hold skills written from its own lessons in the knowledge store (frame_replica.lessons), each ending with the commit of the fix it came
    from. A slot without that is cleared. When the program changed since its rule was read, a lesson is not yet used, or force: the skills held are
    REVIEWED BLIND against the program; a GREEN one stays as it is; a RED or empty slot is written from the next unused real fix (one read), and the new
    ones reviewed blind; a RED one stays in its slot, quarantined (never in a fix prompt), its reason in the knowledge store; with no fix left, the slot
    is blank, RED by default. No reader given (settings None): nothing is written. -> the real fixes counted"""
    counted = 0
    for module, shell in chain:
        fixes = frame.lessons(agent, module)
        counted += len(fixes)
        if not settings or not app:
            continue
        file = os.path.basename(module.__file__)
        job = shell['job'] or {}
        try:
            with open(os.path.join(app, 'agent', file), 'rb') as fh:
                raw = fh.read()
        except OSError:
            continue
        slots = [(str(job.get(f'data_job_skill_{i}_status') or ''), str(job.get(f'data_job_skill_{i}_type') or ''), str(job.get(f'data_job_skill_{i}_description') or '')) for i in range(1, TEN + 1)]
        held = [(st, t, d) if FIX.search(d) else ('RED', '', '') for st, t, d in slots]   # only a skill from a real fix is kept
        used = {FIX.search(d).group(1) for _st, _t, d in held if d}
        fresh = [f for f in fixes if f['commit'] and f['commit'] not in used]
        code = frame.code_of(job)
        moved = bool(code) and code['sha'] != frame.sha(raw)   # the program changed since its rule was read (none kept yet: not known, never a reason to ask)
        if not force and held == slots and not fresh and not moved:
            continue
        source = raw.decode('utf-8', errors='replace')
        run = hire_with or frame.hire
        path = settings.get('reads', {}).get('job_path', '')
        filled = [i for i, (_st, _t, d) in enumerate(held) if d]
        marks = review(run, settings, app, path, agent, file, source, fixes, [(held[i][1], held[i][2]) for i in filled])
        if marks is None:
            continue   # a review that does not mark them all keeps what was there
        for i, (state, _why) in zip(filled, marks):
            held[i] = (state, held[i][1], held[i][2])
        open_slots = [i for i, (st, _t, d) in enumerate(held) if not d or st == 'RED']
        take = fresh[:len(open_slots)]
        if take:
            rc, said = run(frame.reader_command(settings), write_words(agent, file, source, job, take, frame.history(agent, module)), app, SECONDS, path)
            written = numbered_lines(said, len(take)) if rc == 0 else {}
            if len(written) == len(take):
                new = [(written[n][0].upper(), f'{written[n][1]} · FIX {take[n - 1]["commit"]}') for n in range(1, len(take) + 1)]
                newmarks = review(run, settings, app, path, agent, file, source, take, new)
                if newmarks is not None:
                    for slot, (kind, text), (state, why) in zip(open_slots, new, newmarks):
                        held[slot] = (state, kind, text)
                        if state == 'RED':
                            remember(file, slot + 1, kind, text, why)
        out = {}
        for i, (st, t, d) in enumerate(held, 1):
            out.update({f'skill_{i}_status': st if d else 'RED', f'skill_{i}_type': t if d else '', f'skill_{i}_description': d})
        changed = {k: v for k, v in out.items() if (job.get('data_job_' + k) or '') != v}
        if changed:
            store.set_job(shell['job_key'], changed)
    return counted


STATE_LIGHT = {'red': 'hdr-status--error', 'yellow': 'hdr-status--warn', 'green': 'hdr-status--success', 'empty': 'hdr-status--null'}   # the original's (web/page.py STATE_LIGHT)


def light(state):
    """A SKILL'S LIGHT, the original's exactly (skills_entries.html, the owner 2026-10-27: "skills is missing the lights"): a ring, its dot the
    colour of the entry's own state word, nothing computed. -> markup"""
    from markupsafe import escape
    word = (state or '').lower()
    return (f'<span class="scrum-light" role="img" aria-label="{escape(word)}"><svg class="hdr-icon" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2" fill="none">'
            f'<circle cx="12" cy="12" r="9"/><circle class="{STATE_LIGHT.get(word, "hdr-status--null")}" cx="12" cy="12" r="4.5" stroke="none"/></svg></span>')


def skills_panel(job):
    """THE SKILLS of an agent (the SKILLS button): its job's own skills records (jobs species, group sanity), one line a record as the store keeps it,
    status | type | skill (the owner 2026-10-27: "you have to have / 1. status | type | skill"; "a manifest just reports what is in the db"): the
    entry's own state word, its kind, its title · summary, its key small; nothing computed, no index line, no empty kind. -> (its states said: N green N red, the panel)"""
    from markupsafe import escape
    entries = entries_of(job)
    tone = {'GREEN': 'larry-status--green', 'RED': 'larry-status--red'}
    rows = ''.join(f'<tr class="replica-skill" data-skill="{escape(e["key"])}" data-why="{escape(e["kind"])}"><td>{light(e["state"])}</td>'
                   + '<td>' + (f'<span class="{tone[e["state"].upper()]}">{escape(e["state"].upper())}</span>' if e['state'].upper() in tone else str(escape(e['state'].upper()))) + '</td>'
                   + f'<td>{escape(e["kind"].upper())}</td><td>{escape(e["line"])}' + (f' <small>{escape(e["key"])}</small>' if e["key"] else '') + '</td></tr>' for e in entries)
    table = ('<table class="replica-skills"><thead><tr><th></th><th>Status</th><th>Type</th><th>Description</th></tr></thead><tbody>' + rows + '</tbody></table>') if entries else '<div class="annotation">No entry.</div>'   # A TABLE THAT LINES UP: the light, STATUS, TYPE, DESCRIPTION (the owner 2026-10-27: "table is now broken"; "status type description")
    green, red = (sum(1 for e in entries if e['state'] == w) for w in ('green', 'red'))
    return f'{green} green {red} red', f'<div class="replica-canvas-panel">{table}</div>'   # THE BUTTON SAYS THE STATES (the owner 2026-10-27: "skills dot 9 green 1 red / make it like this / for the button")


def skills_view(chain, schedule, last=None, agent=None, group=''):
    """THE SKILLS OF THE CHAIN (the owner 2026-10-26: "1. skills in the frame 2. rules in the frame 3. standup in the agent"), each
    agent's read from its own job (jobs species, group sanity), fully collapsed: one closed line, each agent closed inside it, its
    entries by kind inside; the frame (no agent) says it holds none."""
    from markupsafe import escape
    head = ''   # ONE LINE (the owner 2026-10-27: "same for these too so all are simple and clean and take up not much room"): no schedule line, no last run
    if not agent:
        body = '<div class="annotation">THE FRAME HOLDS NO AGENT: NOTHING TAKEN</div>'
    else:
        held = [(os.path.basename(module.__file__), entries_of(shell['job'])) for module, shell in chain]
        if not any(es for _f, es in held):
            body = "<div class=\"annotation\">No skills yet: the MARK IV agent's first run fills each agent's job (at the page's start, then daily).</div>"
        else:
            each = ''.join(
                f'<details class="replica-rule"><summary><strong>{escape(file)}</strong> · {len(es)} entries</summary>'
                + ''.join(f'<div class="scrum-slot body" data-skill="{escape(e["key"])}" data-why="{escape(e["kind"])}">{light(e["state"])}<span>{escape(e["state"].upper())} | {escape(e["kind"].upper())} | {escape(e["line"])} <span class="annotation">{escape(e["key"])}</span></span></div>' for e in es)
                + '</details>'
                for file, es in held)
            read_today = frame.light_of(chain[0][1]['job'], frame.SETTINGS['root_shape']['x_board']) == 'green'   # the X board's own rule (page.x_parts skills_held): today's skills read, the MARK IV agent's run, ended DONE
            body = (f'<div class="annotation">{len(held)} agents · {sum(len(es) for _f, es in held)} entries</div>'
                    + (frame.idle_after(last) if read_today else '<span class="replica-idle"><span class="scrum-idle">not read today</span></span>'))   # SAYS WHAT THE X BOARD SAYS (the owner 2026-10-28: "not matching")   # THE COUNT LINE ONLY: no dropdown, no detail (the owner 2026-10-27: "skills and rules but no drop down and no detail"); each agent's skills behind its SKILLS button on the gate
    return frame.block('SKILLS', head, body, group)
