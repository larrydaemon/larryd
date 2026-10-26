# THE LARRYD CHECKS · version 5

`larryd doctor` runs these eight checks on an agent, in this order, before it runs and before it is sent anywhere. Its
output names them the same way (`PASS no network`, `FAIL no secret · agent/agent.py line 12: ...`). Every failure says
the file, the line when there is one, what is wrong and what to do.

A new or changed check raises the version. `larryd doctor --json` and the badge name it.

| # | Check | What it proves | Why |
|---|---|---|---|
| 1 | **the project** | There is an agent here: a real `agent/` folder (not a link) holding `agent.json`. | Everything else is checked inside `agent/`, and only `agent/` is ever sent or run. |
| 2 | **the manifest** | `agent.json` is one JSON object with every field and no others: `name`, `entry`, `about`, `does`, `calls`, `reads`, `run`, `gives`, `skills`, `knowledge` (and `inputs` only when the agent is handed the job; `look` when the card has one, every value a name on the menu: a theme colour variable, a step, an effect, a part and its role; `records` only on an agent that answers calls: {species: [verbs]}, each species a module of the platform, each verb read, add, edit or remove, and `"*": ["count"]` for the counts alone (that one on any agent); `live` only on an agent that answers calls: {"seats": 1 to 4}, with the live half beside `agent/` in `live/`: `page.html`, `page.js`, `room.py`, `live.json` and nothing else, the page and its script naming no outside address and building nothing from text, the program the Python standard library only, starting no process and calling out to nothing). Its `card` holds the platform's own values: a class, type, residency, authorization (PUBLIC or PRIVATE, the starting setting the authorize panel can change) and product from its lists, a whole mTok price (3 or "3"), a screen that exists (`<species>/<page>`) of that product, and the look's effect is the one the class picks. `run.do` is one of `does`; `calls` only names what is in `does`; `run.hands` asks only for what LARRYD hands (`cards`, `job`); each input has its own slot. | The manifest is the agent's promise: what it does, what it is handed, what it answers. The runtime holds the agent to it. |
| 3 | **the entry** | The entry file exists, compiles, has a function for every name in `does`, and runs as a program (`if __name__ == '__main__':`). | An agent that cannot start, or that promises a function it does not have, fails in front of a person. |
| 4 | **no network** | The agent has no network module and starts no process; no hidden imports (`importlib`, `__import__`), nothing outside the Python standard library and the agent's own files, no path outside its own folder. | An agent never reaches out. What it needs is handed to it. |
| 5 | **no secret** | No file named like a secret (`.env`, `.pem`, `id_rsa`, ...) and no text that looks like a key, token or password. | An agent holds no secret. Keys belong to the developer, never to the agent. |
| 6 | **the shape** | `agent/` holds only plain, visible UTF-8 files of the kinds an agent holds (`.py`, `.json`, `.txt`, `.md`, `.csv`), and no links. No CSS: `larryd doctor --fix` turns a design sheet into the look record. | What is checked is exactly what runs: nothing hidden, nothing that points elsewhere. |
| 7 | **the skills** | Every skill the agent declares exists (`larryd skills` lists them by hash). | The runtime carries out declared skills for the agent; a skill that does not exist would fail the run. |
| 8 | **the knowledge** | Every knowledge pack the agent declares is one LARRYD holds (`larryd pack` gives a pack its hash). | An agent may only lean on knowledge LARRYD can hand it. LARRYD holds none yet, so this is `[]` today. |

## Declared in the manifest, enforced when it runs

The doctor checks what the manifest declares. When the agent runs, the runtime holds it to the same words:

- **`run.do`**: the agent is asked to do exactly that one thing.
- **`run.hands`**: it is handed only what it names. A hand LARRYD does not have fails the run.
- **`inputs`**: the job's inputs reach it only by the names and slots declared.
- **`records`**: on a CALL it is handed the member's records of the declared species only, and an answer's writes are carried only for a declared species and verb; one undeclared write refuses the whole answer, nothing is carried.
- **the counts** (`"records": {"*": ["count"]}`): on a CALL and on a RUN it is handed numbers only (how many records the member may list in each module, how many ties between two), asked of the platform for the member it named; the runtime refuses an answer that holds anything but numbers, module codes, product slugs and the scope's name, and the declaration opens no record.
- **the live half**: packed with the agent, inside the code's hash, verified with it before every call; its room program's asks of the member's records are carried only for a species and verb the manifest declares, for a member who hired the agent.
- **`live`**: on a CALL it is told `live = {"room": true}` and nothing more: no address, no pass. Its view holds one empty `<div data-room></div>`; LARRYD signs the member's pass (good once, ten minutes) and hands it with the room's address to the platform alone, in its own `room` field beside the view. The agent holds no secret; without the room set up it is told of none.
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
