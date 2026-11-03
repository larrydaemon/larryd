# voice: an agent for LARRYD

You are building one agent, owned by its developer. It runs inside LARRYD, sealed off: no network, no files outside
its own run, no other programs. The platform reaches it only through LARRYD; the agent itself reaches nothing. Read
this whole file before you change anything; `larryd guide` has the rest.

## What an agent is
- The folder `agent/` is the agent. It is exactly what LARRYD holds in its locker: the manifest `agent/agent.json`
  and the code. Nothing else in this project goes to LARRYD. An agent ships no CSS.
- LARRYD runs the entry (`agent/agent.py`) as its own process. One JSON object comes in on stdin, one JSON object
  goes out on stdout. That is the whole contract.
- The job it is handed: `{"do": "<one of does>", ...the inputs named in run.hands}`.
- Its answer: one JSON object. `delivery` (plain text) is what lands in the member's job.
- The job's own inputs: with `"run": {"do": "answer", "hands": ["job"]}` and `"inputs": {"name": "001", "mood": "002"}`
  (each on one of the job's slots 001-015), the job also holds `"job": {"name": "...", "mood": "..."}`.
  `samples/job_inputs.edit-me.json` shows it. Edit me: once your agent declares those inputs, give the file your input
  names, rename it to `samples/job_inputs.json`, and run `larryd run --job samples/job_inputs.json`.

## The manifest (`agent/agent.json`)
- `name`: the agent's name, as its card shows it
- `entry`: the file LARRYD runs, inside agent/ (agent.py)
- `about`: one plain sentence: what the agent answers
- `does`: the list of what the agent does; each one is a function of that name in the entry
- `calls`: what it answers at once on the member's screen (the CALL lane); a list, most agents leave it empty
- `reads`: the list of what the agent reads, in plain words
- `run`: what a RUN hands it: {"do": one of does, "hands": the inputs, from what LARRYD hands}
- `gives`: the list of what its answer holds (its outputs); "delivery" is what lands in the member's job
- `skills`: the list of skill hashes the agent uses (empty when none; `larryd skills` lists the skills that exist)
- `knowledge`: the list of knowledge pack hashes the agent needs (empty when none; `larryd pack` gives a pack its hash)
- `inputs`: only with "job" in run.hands: the job's inputs by name, each on one of the job's slots 001-015, e.g. {"mood": "001"}
- `records`: the member's records the agent reads and writes on a CALL (optional): {"<species>": ["read", "add", "edit", "remove"]}, e.g. {"opns": ["read", "add", "edit", "remove"]}; LARRYD hands them as records = {species: [rows]} and carries the answer's "writes" to the platform's own record doors, only what is declared. THE COUNTS: {"*": ["count"]} (alone or beside species) hands counts = {scope, modules: {species: how many}, products, ties: [[from, to, how many]]} on a CALL and on a RUN: the numbers of the member's own account, never a record
- `live`: the agent's own live page (optional, only on an agent that answers calls): {"seats": 1 to 4}; its files sit in live/ beside agent/ (page.html, page.js, room.py, live.json) and LARRYD tells the call live = {"room": true}; the view holds one empty <div data-room></div>, and the address and the member's pass go to the platform alone
- `makes`: what the agent asks LARRYD to have made by an outside model on a RUN (optional): a list of models on LARRYD's list, e.g. ["nano-banana-2"]; the agent never reaches out: its answer carries "makes": [one ask], LARRYD's own hand does the errand and stores the file in the member's DA-M; the card's "sends_to" and "data_sent" must say where the words go
- `fabric`: THE DATA FABRIC (optional, Positive Feedback's own PF DATA FABRIC): {"modules": [module codes]}, each also declared in "records" with read and edit; on a RUN LARRYD hands fabric = {files: the newest official pf_<module>.csv of each, state: the account's Fabric state} and those modules' records with their custom fields, and carries the answer's "fabric": {"writes": [edits of custom fields only], "state": {...}}; on a CALL it hands fabric = {"state": the account's state, "viewer": {"member_type": who looks, for the page's mask}}
- `card`: the card the marketplace shows, as the member sees it: {class, pitch, price, type, residency, screen, product, module, developer, sends_to, data_sent} and, if you like, developer_site; the number and the art are LARRYD's to give at approval

## The rules (LARRYD's sandbox refuses 1, 2 and 3 when the agent runs)
1. No network, ever. The agent imports no network module and calls no address. LARRYD fetches what the agent
   needs from the platform and hands it in; the agent answers. A network call is refused at run time.
2. Nothing outside its own folder. No path to another folder, no link, no reading or writing elsewhere. It may write
   only in the folder it is run in (it is made for the run and removed after).
3. No new process. No subprocess, no os.system, no multiprocessing.
4. The Python standard library only. LARRYD runs the plain Python runtime: no installed packages.
5. No secret in the agent. No key, token, password or private key in any file.
6. Only what it is handed. The inputs are what run.hands names, from what LARRYD hands today: cards, job.
7. Nothing fake. The agent answers from what it is handed, or it says plainly that it cannot.
8. Plain words. Names as they are: LARRYD, FROST, mTok, DA-M, LARRY LLM.

## The card's facts (`"card"` in `agent/agent.json`)
The platform's own fixed lists; the doctor checks each one:

| Field | Allowed values |
|---|---|
| class | MARK I AGENT (NORMAL): simple; MARK II SUPER AGENT (HARNESS): complex; MARK III QUANTUM AI (AGENTIC CODE): extremely complex; MARK IV REPLICA (FULL-HUMAN REPLACEMENT): a full human replacement |
| type | OFF-THE-SHELF, DEVELOPER |
| residency | which marketplaces it is offered on: INTERNAL: Positive Feedback's own agent marketplace only; EXTERNAL: other marketplaces only (e.g. the Microsoft marketplace), not Positive Feedback; BOTH: Positive Feedback and at least one other marketplace (every LARRYD agent runs in LARRYD) |
| authorization | PUBLIC, PRIVATE (who may hire it: your starting setting; the platform's authorize panel can change it at any time after, and a PRIVATE agent's owning account is entered there) |
| product | INVOICE MAPS, AGENCY MGMT, PACE SHIFT, LARRYD |
| price | a whole number of mTok per run: 3 or "3"; "0" is free |

| Screen (<species>/<page>, at app/<species>/<page>) | Product | Module |
|---|---|---|
| cont/home, cont/list, cont/card | INVOICE MAPS | Contacts |
| invc/home, invc/list, invc/card | INVOICE MAPS | Invoices |
| locn/home, locn/list, locn/card | INVOICE MAPS | Locations |
| opns/home, opns/list, opns/card | INVOICE MAPS | Operations |
| hrcy/home, hrcy/list, hrcy/card | AGENCY MGMT | Hierarchies |
| mdia/home, mdia/list, mdia/card | AGENCY MGMT | Media |
| brnd/home, brnd/list, brnd/card | AGENCY MGMT | Brand |
| sprt/home, sprt/list, sprt/card | AGENCY MGMT | Sprint |
| imgs/home, imgs/list, imgs/card | PACE SHIFT | Images |
| vdeo/home, vdeo/list, vdeo/card | PACE SHIFT | Videos |
| audo/home, audo/list, audo/card | PACE SHIFT | Audio |
| prdn/home, prdn/list, prdn/card | PACE SHIFT | Production |
| agnt/home, agnt/list, agnt/card | LARRYD | Agents |
| mdls/home, mdls/list, mdls/card | LARRYD | Models |
| logs/home, logs/list, logs/card | LARRYD | Logs |
| jobs/home, jobs/list, jobs/card | LARRYD | Jobs |
| larry/home | any | the product's dashboard |

The platform draws the card from these values (an agent ships no look). A value off these lists fails with the ones to
use.

## The card itself
The platform draws every card from the facts above, in its own look, in every brand, mode and size. The agent ships no
look and no CSS: a sheet in `agent/` fails the doctor, and `larryd doctor --fix` moves it out to `design/`.

## The tools
This project's larryd: `/Users/frost/larryd/.venv/bin/larryd` (the one that made it; .mcp.json starts the same one). If `larryd` is not on your PATH, run each command below with that path.

- `/Users/frost/larryd/.venv/bin/larryd new <name>`: makes a new agent project like this one
- `/Users/frost/larryd/.venv/bin/larryd guide`: prints the whole guide (it ships in the package as GUIDE.md; `larryd --help` names its path)
- `/Users/frost/larryd/.venv/bin/larryd doctor`: checks the agent before submission; every problem says what is wrong and what to do (--json for the result as JSON)
- `/Users/frost/larryd/.venv/bin/larryd run`: runs the agent here the way LARRYD runs it (no network, no new process, a scratch run folder, a time limit), with samples/job.json or --job <file>; on a Mac or Linux
- `/Users/frost/larryd/.venv/bin/larryd submit`: sends the agent (agent/ only, one file) to LARRYD for review, after the doctor, and opens the page where you sign in with Google or Apple to submit it; nothing to paste or keep
- `/Users/frost/larryd/.venv/bin/larryd place`: puts the agent on your own LARRYD's shelf: the doctor, then agent/ as one file into the locker of the runtime running on this computer (`larryd` in another terminal); the same agent placed again replaces itself
- `/Users/frost/larryd/.venv/bin/larryd card`: places the agent and opens the marketplace page on this computer: every agent LARRYD holds here as a card with its hire toggle, as the platform will show it; a card the gate cannot show is listed with why
- `/Users/frost/larryd/.venv/bin/larryd skills`: lists the skills an agent may declare in "skills", by hash
- `/Users/frost/larryd/.venv/bin/larryd pack <folder>`: checks a knowledge pack and gives its hash
- `/Users/frost/larryd/.venv/bin/larryd mcp`: serves these tools to Claude Code (larryd_new, larryd_doctor, larryd_run, larryd_submit, larryd_skills, larryd_pack, larryd_card); this project's .mcp.json starts it

The whole guide: `larryd guide`.
