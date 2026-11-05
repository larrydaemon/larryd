"""THE RED, the shared block of every MARK IV workflow (owned by Operations Manager): whatever is red in the page's workflow, one row
each: a block whose job's light is RED (red since its last run, its YOUR 3 MIN step from its job's own today line), and a block whose
rules are red (the review's bad verdict, a DRIFT or TAMPER lie detector); never itself. Who works on it: an open FIX request of the workflow's own
office naming it. THE RED rounds: the office's requests whose words start with the fix words. Its RUN is red when a red has nothing
working on it, the first such row's step as YOUR 3 MIN; never green by hiding a red."""
import datetime
import html
import json

import look
import office




def line_of(job):
    """its job's own line: its delivery's first line (a delivery kept whole as one JSON: its summary)"""
    first = str(job.get('data_job_delivery') or '').split('\n', 1)[0]
    if first.startswith('{'):
        try:
            return str(json.loads(first).get('summary') or '')
        except (ValueError, AttributeError):
            return ''
    return first


def step_of(job):
    """its YOUR 3 MIN step, as its own job says it: its delivery's line, its today line, what its last RUN found"""
    words = office.fact('step_words')
    found = office.data_of(job)
    for text in (line_of(job), job.get('data_job_today_said'), found.get('summary'), found.get('said')):
        if text and words in str(text):
            return str(text).split(words, 1)[1].strip()
    return str(found.get('step') or '')


def reds(given):
    name = office.page_workflow(given)
    place = (office.fact('offices') or {}).get(name)
    if not place:
        raise ValueError(f'no office for the workflow {name!r}: the offices fact names none' if name else 'no workflow found for this page')
    fixes = [r for r in office.requests(office_name=place) if str(r.get('words') or '').startswith(office.fact('fix_words'))]
    open_ = [r for r in fixes if r.get('state') in office.fact('working')]
    out = []
    for j in office.workflow(given, name):
        if j.get('data_job_agentic') == 'WORKFLOW' or j.get('data_agent_key') in ('', None, office.me()['key']):
            continue
        n = j.get('data_full_name') or j['data_agent_key']
        who = next((r['id'] for r in open_ if n in str(r.get('words') or '')), '')
        if office.light_of(j) == 'RED':
            why = line_of(j) or j.get('data_job_today_said') or 'its light is RED'
            out.append({'name': n, 'kind': 'light', 'why': why[:300], 'since': j.get('data_job_last_run_at') or '', 'step': step_of(j), 'who': who})
        detector = j.get('data_job_lie_detector') or ''
        if j.get('data_job_rules_review_verdict') == office.fact('bad_verdict') or detector in office.fact('bad_detector'):
            why = (j.get('data_job_rules_review_description') if j.get('data_job_rules_review_verdict') == office.fact('bad_verdict')
                   else f'its lie detector says {detector}')
            out.append({'name': n, 'kind': 'rules', 'why': f'RULES: {why}'[:300], 'since': j.get('data_job_rules_review_date') or '',
                        'step': office.fact('rules_step'), 'who': who})
    rounds = {s: sum(1 for r in fixes if r.get('state') == s) for s in sorted({r.get('state') for r in fixes})}
    return name, place, sorted(out, key=lambda r: r['kind'] != 'light'), {'all': len(fixes), 'open': len(open_), 'by_state': rounds}


def at(text):
    try:
        got = datetime.datetime.fromisoformat(str(text or '').replace('Z', '+00:00'))
    except ValueError:
        return None
    return got if got.tzinfo else got.replace(tzinfo=office.now().tzinfo)


def ago(text, word=''):
    """SM2's own ticking words (its page's ago()), written at CALL time: 'RED 3 H 5 MIN 2 S'; '' when the time does not read"""
    t = at(text)
    if t is None:
        return ''
    s = max(0, int((office.now() - t).total_seconds()))
    h, m = s // 3600, s % 3600 // 60
    return word + (f'{h} H ' if h else '') + (f'{m} MIN ' if h or m else '') + f'{s % 60} S'


def why_row(r, job, open_key, path):
    """ONE ROW OF WHY IT'S RED, SM2's: the name, the one step that fixes it, the why and the full rules folded under it (a press opens them),
    the status now (the fix request at work, else IDLE) with its red time"""
    e, key = html.escape, f"{r['kind']}:{r['name']}"
    opened = open_key == key
    rules = ''.join(f'<div class="body"><span>{e(label)}</span>{e(job.get(field))}</div>' for label, field in office.fact('rule_fields') if job.get(field))
    fold = (f'<form class="ct-form" method="get" action="{e(path)}"><input type="hidden" name="red_open" value="{"" if opened else e(key)}">'
            f'<button type="submit" class="pfb pfb--mini scrum-why-press">{"▼" if opened else "▶"} why it is red, and the full rules</button></form>'
            + (f'<div class="clarity scrum-rules-panel scrum-why-rules-body"><div class="body"><span>Why</span>{e(r["why"])}</div>{rules}</div>' if opened else ''))
    status = f'<span class="scrum-key">"{e(r["who"])}"</span>' if r['who'] else '<span class="scrum-idle">IDLE</span>'
    red = f' <span class="hdr-status--error scrum-red-for">{e(ago(r["since"], "RED "))}</span>' if ago(r['since']) else ''
    return (f'<tr data-why="{e(key)}"><td>{e(r["name"])}</td><td><div class="scrum-why-fix">{e(r["step"] or r["why"])}</div>{fold}</td>'
            f'<td data-status="{e(key)}"{" class=" + chr(34) + "scrum-why-working" + chr(34) if r["who"] else ""}>{status}{red}</td></tr>')


def canvas(given):
    name, place, rs, _rounds = reds(given)
    e, path = html.escape, (given.get('page') or {}).get('path') or ''
    jobs = {j.get('data_full_name') or j.get('data_agent_key'): j for j in office.workflow(given, name)}
    sinces = sorted(str(r['since']) for r in rs if at(r['since']))
    head = (f'<div id="scrum-reds" class="title" role="status"><span id="scrum-reds-count" class="{"hdr-status--error" if rs else "scrum-idle"}">{len(rs)} RED</span>'
            + (f' <span id="scrum-reds-since" class="caption hdr-status--error scrum-reds-since">{e(ago(sinces[0], "FOR "))}</span>' if sinces else '') + '</div>')
    fixing = next((r for r in rs if r['who']), None)
    own = next((j for j in jobs.values() if j.get('data_agent_key') == office.me()['key']), {})
    now = (f'<span class="hdr-status--success">WORKING ON</span> <span class="scrum-key">"{e(fixing["name"])}"</span>' if fixing
           else '<span class="scrum-idle">IDLE</span>' + (f'<span class="scrum-since scrum-idle">{e(" " + ago(own.get("data_job_last_run_at")))}</span>' if ago(own.get('data_job_last_run_at')) else ''))
    body = ''.join(why_row(r, jobs.get(r['name']) or {}, office.asked(given, 'red_open'), path) for r in rs) or '<tr class="replica-why-none"><td colspan="3">Nothing is red.</td></tr>'
    markup = ('<div class="replica-normal-block replica-red replica-live" aria-label="THE RED"><span class="replica-red-group" aria-label="group">LIVE</span>'
              f'<div id="scrum-red-head">{head}<div id="scrum-red-now" class="subtitle" role="status">{now}</div></div>'
              '<div class="scaf-wrap" id="scrum-why-wrap"><table class="scrum-term" id="scrum-why"><thead><tr><th class="scrum-why-row">Row</th><th>Why it\'s red</th>'
              f'<th class="scrum-why-status">Status now</th></tr></thead><tbody>{body}</tbody></table></div></div>')
    return look.view(markup, path, office.fact('css'))


def run(given):
    name, place, rs, rounds = reds(given)
    loose = [r for r in rs if not r['who']]
    data = {'workflow': name, 'office': place, 'reds': rs, 'rounds': rounds, 'at': office.stamp()}
    if loose:
        first = loose[0]
        return office.done(f"RED · {name}: {len(rs)} red, {len(loose)} with nothing working on it: {', '.join(sorted({r['name'] for r in loose}))}"
                           f" · YOUR 3 MIN: {first['name']}: {first['step'] or first['why']}", 'RED', data)
    return office.done(f"GREEN · {name}: " + (f"{len(rs)} red, each worked on by its fix request" if rs else 'nothing is red')
                       + f" · {rounds['all']} red rounds, {rounds['open']} open", 'GREEN', data)


if __name__ == '__main__':
    office.main(canvas, run)
