"""VOICE, the Creative Director office's TOP sub agent (agent002_top_voice.py), moved whole into LARRYD RUNTIME INTERNAL (2026-11-03),
replacing the sandboxed port of earlier today. Its program is the office's own, copied beside this file (agent/agent002_top_voice.py),
with the office's agent.json it reads the voice from (schemas/agent.json: the script lab's voice service http://127.0.0.1:8824 and the
voice christensen).

A CALL ({do: "canvas"}) answers the canvas the office's page drew for it (web/page.py canvas with its content(), which is empty: the
replica canvas alone), under its group word TOP (web/app.py grouped).
A RUN ({do: "read"}) is the office's own run (agent002 run): the voice service's state read now (GET /state: loaded, lines made, lines
waiting). DONE: its line is the delivery. A voice not answering or not loaded: FAILED, exit 1, its one line."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
CANVAS_CSS = ".replica-canvas { display: block } .replica-rows td .replica-row-press { margin-top: 8px } .replica-rows td .scrum-update-words { display: block; width: 100%; box-sizing: border-box; margin-bottom: 6px } .replica-canvas-head, .replica-canvas-foot { background-color: var(--active-color-01); color: var(--active-color-09); padding: 14px 18px } .replica-canvas-head .body, .replica-canvas-head .annotation { color: inherit } .replica-canvas-foot .replica-rows, .replica-canvas-foot .replica-rows td, .replica-canvas-foot .replica-rows th { background-color: var(--active-color-09); color: var(--active-color-01) } .replica-canvas-foot .scaf-row-alt td { background-color: var(--active-color-09) } .replica-canvas-foot .replica-rows .caption, .replica-canvas-foot .replica-rows .annotation { color: inherit } .replica-canvas-foot .replica-rows .scrum-day-head .caption { color: var(--status-ok) } .replica-canvas-foot .replica-rows tr.replica-run-said td { background-color: var(--clarity-ground); color: var(--clarity-ink); font-family: var(--clarity-face); font-size: 1.25rem; font-weight: 700; line-height: 1.5 } .replica-canvas-head { margin: 0 0 24px } .replica-canvas-foot { overflow-x: auto } .replica-canvas-title { display: flex; align-items: center; gap: 12px; margin: 0 0 6px } .replica-canvas-name { font-family: var(--clarity-face-heading); font-size: 2rem; font-weight: 900; line-height: 1.15; letter-spacing: .02em; text-transform: uppercase; margin: 0 } .replica-canvas .scrum-light { display: inline-flex; flex: none } .replica-canvas .scrum-light .hdr-status--success { fill: var(--status-ok) } .replica-canvas .scrum-light .hdr-status--error { fill: var(--status-error) } .replica-canvas .scrum-light .hdr-status--warn { fill: var(--status-warn) } .replica-canvas-what { margin: 0 0 2px } .replica-canvas-file { margin: 0; font-family: ui-monospace, Menlo, monospace; letter-spacing: .02em } .replica-canvas-content { margin: 0 0 24px } .replica-canvas-foot details { margin-top: 12px } .replica-canvas-foot summary.pfb { list-style: none } .replica-canvas-foot summary::-webkit-details-marker { display: none } .replica-canvas-panel { margin: 8px 0 0; padding: 10px 12px; border: 1px solid currentColor; border-radius: 4px; font: 15px/1.6 ui-monospace, Menlo, monospace; user-select: text; background-color: var(--active-color-09); color: var(--active-color-01) } .replica-loop-logo { display: block; width: 240px; max-width: 60%; height: auto; margin: 4px auto 18px } .replica-loop .body { font-size: 1.25rem; line-height: 1.6 } .scrum-rules-panel.clarity { margin: 10px 0 0; padding: 18px 22px 16px; border: 3px solid var(--clarity-ink); border-radius: 0; text-transform: none; background-color: var(--clarity-ground); color: var(--clarity-ink) } .scrum-rules-panel .annotation[data-rules-state] { font-family: var(--clarity-face-caption); font-size: .8rem; font-weight: 600; line-height: 1.5; letter-spacing: .06em; text-transform: uppercase; color: var(--clarity-ink); opacity: 1; margin: 0 0 14px } .scrum-rules-panel .body { font-family: var(--clarity-face); font-size: 1.25rem; font-weight: 400; line-height: 1.5; letter-spacing: normal; text-transform: none; color: var(--clarity-ink); margin: 0 0 10px } .scrum-rules-panel .body > span:first-child { font-family: var(--clarity-face-heading); font-weight: 900; letter-spacing: .04em; text-transform: uppercase; margin-right: .4em } .scrum-rules-panel .annotation { font-family: var(--clarity-face); font-size: 1rem; font-weight: 400; line-height: 1.45; text-transform: none; color: var(--clarity-ink-notes); opacity: 1; margin: 0 0 10px } .scrum-rules-panel .scrum-rules-title { font-family: var(--clarity-face-heading); font-size: 1.3rem; font-weight: 900; line-height: 1.3; letter-spacing: .04em; text-transform: uppercase; color: var(--clarity-ink); margin: 0 0 12px } .scrum-rules-panel .scrum-rules-big { font-family: var(--clarity-face-heading); font-size: 1.9rem; font-weight: 700; line-height: 1.25; letter-spacing: normal; text-transform: none; color: var(--clarity-ink); margin: 0 0 18px } .scrum-rules-panel .hdr-status--success { color: var(--clarity-ok) } .scrum-rules-panel .hdr-status--error { color: var(--clarity-bad) } .scrum-rules-panel .scrum-idle { color: var(--clarity-warn) } .replica-skills { width: 100%; border-collapse: collapse; table-layout: fixed } .replica-skills th, .replica-skills td { padding: 4px 8px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--ui-row-divider) } .replica-skills th:nth-child(1) { width: 34px } .replica-skills th:nth-child(2) { width: 9ch } .replica-skills th:nth-child(3) { width: 10ch } .replica-skills th { font-size: var(--font-label-sz); letter-spacing: var(--font-label-ls) } .replica-skills td:nth-child(4) { overflow-wrap: anywhere } .replica-canvas-panel .subtitle, .replica-canvas-panel .body, .replica-canvas-panel .annotation { color: inherit } .replica-canvas-panel .replica-rule > div { margin: 0 0 6px } .replica-canvas .scrum-slot { display: grid; grid-template-columns: 18px minmax(0, 1fr); gap: 0 10px; align-items: start; text-transform: none } .replica-canvas .scrum-slot code { font: inherit; color: inherit; white-space: pre-wrap; word-break: break-word } .replica-rows { width: 100%; margin: 0; border-collapse: collapse; table-layout: fixed } .replica-rows th, .replica-rows td { padding: 6px 10px; vertical-align: middle; border-bottom: 1px solid var(--ui-row-divider) } .replica-rows thead th, .replica-view-all .replica-rows td:not([colspan]) { width: 20% } .replica-view-all > td { padding: 6px 0 } .replica-view-all summary { margin: 0 10px 6px } .replica-rows th, .replica-rows td { text-align: center } .replica-rows td[colspan] { text-align: left } .replica-rows thead th { border-bottom-width: 2px } .replica-rows .scrum-day-head td { padding-top: 12px } .replica-rows thead th, .replica-rows .caption, .replica-rows .smoke-status, .replica-rows .annotation, .replica-rows .larry-up, .replica-rows .hdr-status--error { font-size: var(--font-label-sz); letter-spacing: var(--font-label-ls) } .replica-rows .scaf-mono { font-size: 1rem; line-height: 1.5 } .replica-rows .hdr-status--success { color: var(--status-ok); font-weight: 700 } .replica-rows .hdr-status--error { color: var(--status-error); font-weight: 700 } .replica-copy { display: block; font: 15px/1.6 ui-monospace, Menlo, monospace; user-select: all; white-space: pre-wrap; word-break: break-word } .replica-voice { margin: 14px 0 0 } .replica-standup { margin: 0 } .replica-spoken > div { margin: 0 0 8px } .replica-live-line { margin: 8px 0 0 } .replica-live-line .hdr-status--success { color: var(--status-ok); font-weight: 700 } .replica-live-line .hdr-status--error { color: var(--status-error); font-weight: 700 }"   # the office's web/page.py CANVAS_CSS, as text
GROUP_CSS = ".replica-group { text-align: right; margin: 24px 0 6px; font-family: var(--clarity-face-caption, inherit); font-size: .8rem; font-weight: 700; line-height: 1.2; letter-spacing: .08em; text-transform: uppercase; } .replica-group + * { margin-top: 0 !important; }"   # the replica's frame_replica.GROUP_CSS, as text


def program():
    spec = importlib.util.spec_from_file_location('agent002_top_voice', os.path.join(HERE, 'agent', 'agent002_top_voice.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def group_line(word):
    """A BLOCK'S GROUP WORD (frame_replica.group_line)."""
    import html
    return f'<div class="replica-group" aria-label="group">{html.escape(word)}</div>' if word else ''


def canvas(given):
    """THE CALL: its canvas as the office's page drew it (page.canvas: canvas_html with content_view(module.content()), grouped by its slot)."""
    module = program()
    content = module.content(None, '')   # its own content: none of its own words
    middle = "<div class=\"replica-canvas-content\"></div>"   # content_view of its content (empty) draws nothing inside
    return {'view': {'html': group_line(module.SLOT) + f'<div class="replica-canvas">{middle}</div>', 'css': CANVAS_CSS + ' ' + GROUP_CSS}}


class EndsHere:
    """The run's end kept here (its LOGS record is written by LARRYD RUNTIME INTERNAL from this answer)."""

    def __init__(self):
        self.ended = []

    def ran(self, job_key, n, started_at, ended_at, exit_code, said, state):
        self.ended.append({'n': n, 'started_at': started_at, 'ended_at': ended_at, 'exit': exit_code, 'said': said, 'state': state})


def read(given):
    """THE RUN: the office's own run (agent002 run), the voice's state read now."""
    ends = EndsHere()
    out = program().run(ends, '', 0, None, [])
    summary = str((out or {}).get('summary') or '')
    if not ends.ended or ends.ended[-1]['state'] != 'DONE':
        raise SystemExit(summary or 'FAILED · the run wrote no summary')
    return {'delivery': summary}


def main():
    given = json.load(sys.stdin)
    do = {'canvas': canvas, 'read': read}.get(given.get('do'))
    if do is None:
        raise SystemExit('Voice does: canvas, read')
    print(json.dumps(do(given)))


if __name__ == '__main__':
    main()
