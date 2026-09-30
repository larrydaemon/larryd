# THE LARRYD CHECKS · version 1

`larryd doctor` runs these eight checks on an agent, in this order, before it runs and before it is sent anywhere. Its
output names them the same way (`PASS the air gap`, `FAIL no secret · agent/agent.py line 12: ...`). Every failure says
the file, the line when there is one, what is wrong and what to do.

A new or changed check raises the version. `larryd doctor --json` and the badge name it.

| # | Check | What it proves | Why |
|---|---|---|---|
| 1 | **the project** | There is an agent here: a real `agent/` folder (not a link) holding `agent.json`. | Everything else is checked inside `agent/`, and only `agent/` is ever sent or run. |
| 2 | **the manifest** | `agent.json` is one JSON object with every field and no others: `name`, `entry`, `about`, `does`, `calls`, `reads`, `run`, `gives`, `skills`, `knowledge` (and `inputs` only when the agent is handed the job). `run.do` is one of `does`; `calls` only names what is in `does`; `run.hands` asks only for what LARRYD hands (`cards`, `job`); each input has its own slot. | The manifest is the agent's promise: what it does, what it is handed, what it answers. The runtime holds the agent to it. |
| 3 | **the entry** | The entry file exists, compiles, has a function for every name in `does`, and runs as a program (`if __name__ == '__main__':`). | An agent that cannot start, or that promises a function it does not have, fails in front of a person. |
| 4 | **the air gap** | No network module, no module that starts processes, no hidden imports (`importlib`, `__import__`), nothing outside the Python standard library and the agent's own files, no path outside its own folder. | An agent never reaches out. What it needs is handed to it. |
| 5 | **no secret** | No file named like a secret (`.env`, `.pem`, `id_rsa`, ...) and no text that looks like a key, token or password. | An agent holds no secret. Keys belong to the developer, never to the agent. |
| 6 | **the shape** | `agent/` holds only plain, visible UTF-8 files of the kinds an agent holds (`.py`, `.json`, `.txt`, `.md`, `.csv`), and no links. | What is checked is exactly what runs: nothing hidden, nothing that points elsewhere. |
| 7 | **the skills** | Every skill the agent declares exists (`larryd skills` lists them by hash). | The runtime carries out declared skills for the agent; a skill that does not exist would fail the run. |
| 8 | **the knowledge** | Every knowledge pack the agent declares is one LARRYD holds (`larryd pack` gives a pack its hash). | An agent may only lean on knowledge LARRYD can hand it. LARRYD holds none yet, so this is `[]` today. |

## Declared in the manifest, enforced when it runs

The doctor checks what the manifest declares. When the agent runs, the runtime holds it to the same words:

- **`run.do`**: the agent is asked to do exactly that one thing.
- **`run.hands`**: it is handed only what it names. A hand LARRYD does not have fails the run.
- **`inputs`**: the job's inputs reach it only by the names and slots declared.
- **`skills`**: only declared skills are carried out. An answer that carries files is refused unless the agent declares the DA-M store.
- **`calls`**: only an agent that declares `calls` answers on a member's screen.
- **`gives`**: an answer that holds anything `gives` does not name is refused, enforced by `larryd run` and by LARRYD's runtime: the run fails, nothing is delivered, nothing is charged.

## The walls around every agent

These hold for every agent on every run, whatever its manifest says. On a Mac they are macOS `sandbox-exec`; on Linux,
bubblewrap with a seccomp filter. Where neither is present, nothing runs.

- **No network at all.** What it needs is handed to it.
- **No other programs.** It cannot start a process.
- **None of your files.** On a Mac it reads nothing in the home folders but its own folder. On Linux it reads nothing
  but its own folder and the Python runtime. It writes only to a scratch folder, deleted after the run.
- **One JSON job in, one JSON answer out**, in an empty environment, inside a time limit.

## The badge

    larryd doctor --badge

writes `larryd-checks.svg` beside `agent/` (never inside it): **PASS** in gold or **FAIL** in red, with the day and the
checks' version. Paste `![LARRYD checks](larryd-checks.svg)` into your README.
