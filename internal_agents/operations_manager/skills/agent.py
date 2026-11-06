"""SKILLS, the shared block of every MARK IV workflow (owned by Operations Manager): each block's ten skills as its job record holds them
(data_job_skill_N_status, _type, _description). A skill is kept only when it came from a real fix: its words end with the commit it came
from (" · FIX abc1234"). Its RUN reads them again and looks up each skill's fix in the knowledge store's lessons, where real fixes live.
Skills are knowledge, never a fault: red only when the knowledge store cannot be read."""
import datetime
import re
import sqlite3

import look
import office

FIX = re.compile(r' · FIX ([0-9a-f]{7})$')





def blocks(given):
    name = office.page_workflow(given)
    if not name:
        raise ValueError('no workflow found for this page: no WORKFLOW job holds its screen')
    return name, [j for j in office.workflow(given, name) if j.get('data_job_agentic') != 'WORKFLOW' and j.get('data_agent_key')]


def slots(job):
    return [{'n': i, 'state': str(job.get(f'data_job_skill_{i}_status') or '').upper(), 'kind': str(job.get(f'data_job_skill_{i}_type') or ''),
             'line': str(job.get(f'data_job_skill_{i}_description') or '')} for i in range(1, int(office.fact('slots')) + 1)
            if job.get(f'data_job_skill_{i}_description')]


def fixes():
    """every real fix's commit the knowledge store's lessons name (COMMIT <sha> in the text, FIX <sha> in the summary)"""
    con = sqlite3.connect(f"file:{office.fact('knowledge')}?mode=ro", uri=True, timeout=5)
    try:
        got = con.execute("SELECT text, summary FROM entries WHERE kind = 'lesson'").fetchall()
    finally:
        con.close()
    out = set()
    for text, summary in got:
        out |= {c[:7] for c in re.findall(r'\bCOMMIT ([0-9a-f]{7,40})\b', str(text or '')) + re.findall(r'\bFIX ([0-9a-f]{7,40})\b', str(summary or ''))}
    return out


def run(given):
    name, bs = blocks(given)
    try:
        known = fixes()
    except sqlite3.Error as no:
        return office.done(f"RED · the knowledge store {office.fact('knowledge')} could not be read: {no}", 'RED')
    rows = []
    for j in bs:
        ss = slots(j)
        commits = [FIX.search(s['line']).group(1) for s in ss if FIX.search(s['line'])]
        rows.append({'name': j.get('data_full_name'), 'held': len(ss), 'green': sum(s['state'] == 'GREEN' for s in ss),
                     'red': sum(s['state'] == 'RED' for s in ss), 'from_fix': len(commits), 'fix_found': sum(c in known for c in commits)})
    total = lambda k: sum(r[k] for r in rows)  # noqa: E731
    line = (f"GREEN · {name}: {total('held')} skills held by {sum(1 for r in rows if r['held'])} of {len(rows)} agents · {total('green')} green, "
            f"{total('red')} red · {total('from_fix')} from a real fix, {total('fix_found')} of them found in the knowledge store ({len(known)} fixes there)")
    return office.done(line, 'GREEN', {'workflow': name, 'rows': rows, 'fixes': len(known), 'at': office.stamp()})


def idle(own):
    """SM2's green IDLE after a one-line block: READING while its job runs, else IDLE and the time since its last run (written now:
    SM2 counted it on the page), nothing before a first run"""
    if str(own.get('data_job_run_state') or '').upper() in ('RUNNING', 'QUEUED'):
        return '<span class="replica-idle"><span class="hdr-status--success">READING</span></span>'
    try:
        last = datetime.datetime.fromisoformat(str(own.get('data_job_last_run_at') or '')).replace(tzinfo=office.now().tzinfo)
    except ValueError:
        return ''
    s = max(0, int((office.now() - last).total_seconds()))
    return (f'<span class="replica-idle"><span class="hdr-status--success">IDLE</span>'
            f'<span class="scrum-since hdr-status--success">{s // 3600} H {s % 3600 // 60} MIN {s % 60} S</span></span>')


def part(name, said, after):
    """SM2's one-line frame part (replica-normal-block), under its group label"""
    return ('<div class="replica-group" aria-label="group">TOP</div>'
            f'<div class="replica-normal-block replica-frame-part" aria-label="{name}"><div class="title scaf-law-title">{name}</div>'
            f'<div class="replica-normal-body"><div class="annotation">{office.e(said)}</div>{after}</div></div>')


def canvas(given):
    """SM2's SKILLS line: agents and entries held, then IDLE when its own job read them today, else not read today"""
    name, bs = blocks(given)
    own = next((j for j in bs if j['data_agent_key'] == office.me()['key']), {})
    held = [slots(j) for j in bs]
    path = str((given.get('page') or {}).get('path') or '')
    if not any(held):
        return look.view(part('SKILLS', "No skills yet: the MARK IV agent's first run fills each agent's job.", ''), path)
    today = office.light_of(own) == 'GREEN' and (own.get('data_job_today_date') or '') == office.now().date().isoformat()
    after = idle(own) if today else '<span class="replica-idle"><span class="scrum-idle">not read today</span></span>'
    return look.view(part('SKILLS', f'{len(held)} agents · {sum(len(s) for s in held)} entries', after), path)


if __name__ == '__main__':
    office.main(canvas, run)
