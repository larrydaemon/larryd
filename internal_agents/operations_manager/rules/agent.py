"""RULES, the shared block of every MARK IV workflow (owned by Operations Manager): each block's rule as its job record holds it, in its
parts (1 the owner's rule, 2 why it is fixed within 3 minutes, 3 red, 4 green, 5 the blind review), with the program it was read
against and its lie detector. Its RUN reads every block's program again where it lives (the agent folder whose agent.json holds the
block's card key) and says the lie detector now: CLEAN when its sha256 is the one kept, DRIFT when it changed, TAMPER when no program
or no code was kept. Red exactly when a review says the bad verdict or a lie detector says DRIFT or TAMPER (the X board's RULES rule)."""
import datetime
import glob
import hashlib
import json
import os
import re

import look
import office

CODE = re.compile(r'^(?P<file>[\w.-]+\.py) · (?P<sha>[0-9a-f]{64})$')





def blocks(given):
    name = office.page_workflow(given)
    if not name:
        raise ValueError('no workflow found for this page: no WORKFLOW job holds its screen')
    return name, [j for j in office.workflow(given, name) if j.get('data_job_agentic') != 'WORKFLOW' and j.get('data_agent_key')]


def programs():
    """{card key: its program's path}, every agent folder under the agents root"""
    out = {}
    for spec in glob.glob(os.path.join(office.fact('agents_root'), '*', '*', 'agent.json')):
        try:
            with open(spec, encoding='utf-8') as fh:
                key = json.load(fh).get('key')
        except (OSError, ValueError):
            continue
        if key:
            out[key] = os.path.join(os.path.dirname(spec), office.fact('program'))
    return out


def detector(job, path):
    kept = CODE.match(str(job.get('data_job_rule_code') or ''))
    try:
        with open(path or '', 'rb') as fh:
            now = hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return 'TAMPER', 'no program found'
    if not kept:
        return 'TAMPER', 'no code kept'
    return ('CLEAN', '') if kept['sha'] == now else ('DRIFT', f"read against {kept['file']} {kept['sha'][:12]}, now {now[:12]}")


def red_of(job, word):
    if job.get('data_job_rules_review_verdict') == office.fact('bad_verdict'):
        return f"the review says {office.fact('bad_verdict')}"
    return f'its lie detector says {word}' if word in ('DRIFT', 'TAMPER') else ''


def run(given):
    name, bs = blocks(given)
    where = programs()
    rows = []
    for j in bs:
        if not j.get('data_job_rule'):
            rows.append({'name': j.get('data_full_name'), 'read': False})
            continue
        word, why = detector(j, where.get(j['data_agent_key']))
        rows.append({'name': j.get('data_full_name'), 'read': True, 'verdict': j.get('data_job_rules_review_verdict') or '', 'detector': word,
                     'why': why, 'kept': j.get('data_job_lie_detector') or '', 'red': red_of(j, word)})
    read = [r for r in rows if r['read']]
    count = lambda k, v: sum(1 for r in read if r[k] == v)  # noqa: E731
    reds = [r for r in read if r['red']]
    line = (f"{name}: {len(read)} of {len(rows)} rules read · {count('verdict', office.fact('good_verdict'))} {office.fact('good_verdict')}, "
            f"{count('verdict', office.fact('bad_verdict'))} {office.fact('bad_verdict')} · lie detector now {count('detector', 'CLEAN')} CLEAN, "
            f"{count('detector', 'DRIFT')} DRIFT, {count('detector', 'TAMPER')} TAMPER")
    data = {'workflow': name, 'rows': rows, 'at': office.stamp()}
    if reds:
        return office.done(f"RED · {line} · first: {reds[0]['name']}, {reds[0]['red']}", 'RED', data)
    return office.done(f'GREEN · {line}', 'GREEN', data)


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
    """SM2's RULES line: how many agents' rules are read, then IDLE since its last run"""
    name, bs = blocks(given)
    own = next((j for j in bs if j['data_agent_key'] == office.me()['key']), {})
    held = [j for j in bs if j.get('data_job_rule')]
    if not held:
        missing = [j.get('data_full_name') or '' for j in bs]
        return look.view(part('RULES', 'No rules yet' + (f' · not read yet: {", ".join(missing)}' if missing else '') + '.', ''), page_path(given))
    return look.view(part('RULES', f'{len(held)} agents', idle(own)), page_path(given))


def page_path(given):
    return str((given.get('page') or {}).get('path') or '')


if __name__ == '__main__':
    office.main(canvas, run)
