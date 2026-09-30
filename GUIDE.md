# Building an agent for LARRYD with LARRYD

This guide is for the developer's AI first and the developer second. Read it whole before you build.
Every command named here exists and works today; what does not exist yet is listed at the end, plainly.

## What you are building
An agent is a small program that answers a job. It lives in LARRYD, air gapped, and it belongs to its
developer. LARRYD connects it to the platform: it reads what the agent needs, hands it in, and carries the answer back.
The agent itself reaches nothing.

The whole contract: LARRYD runs the agent's entry file as its own process. One JSON object comes in on stdin,
one JSON object goes out on stdout. `delivery` in the answer (plain text) is what lands in the member's job.

## 1. Install
    pip install larryd

or `pip install git+https://github.com/larrydaemon/larryd.git`. (Until version 0.1.0 is published, PyPI holds only the
name's reservation, 0.0.1.)

This gives one command, `larryd`. It is proven on Python 3.14 on a Mac.

## 2. Your developer key
LARRYD makes your developer key: a name and a secret. The secret is shown once. Keep it on your computer:

    larryd key <LARRYD's address> <your developer name>

Paste the secret when it asks; it is never typed on the command line. It is kept in `~/.larryd/developer.json`,
readable by you only, never inside a project. The Claude Code tools never see it.
Each agent also has a card key (four capital letters, 12 and then 4 hex digits, e.g. `MAGT_0123456789AB_CDEF`).
The way it works today: the SYSTEM owner makes your agent's card on LARRYD's agent add screen and hands you its key,
with your developer key. LARRYD lets you submit only the card keys it holds for you.

## 3. A new agent
    larryd new <name>

This makes the folder `<name>/`:
- `agent/`: the agent, and only the agent. It is exactly what LARRYD holds.
  - `agent/agent.json`: the manifest (its fields are explained in the project's CLAUDE.md)
  - `agent/agent.py`: the code, with one entry: `answer(job)`
- `CLAUDE.md`: the spec and the rules, for Claude Code
- `.claude/skills/larryd/SKILL.md`: the larryd skill Claude Code loads
- `samples/job.json`: a sample job for `larryd run`
- `.mcp.json`: starts the LARRYD tools in Claude Code when you open the folder with `claude`
- `larryd.json`: put the agent's card key here: `{"agent_key": "MAGT_0123456789AB_CDEF"}` (with your real key)

## 4. The rules
LARRYD's sandbox refuses 1, 2 and 3 when the agent runs; the doctor checks all of them before that.
1. No network, ever. No network module, no address.
2. Nothing outside its own folder: no path elsewhere, no link. It writes only in the folder it is run in.
3. No new process: no subprocess, no os.system, no multiprocessing.
4. The Python standard library only.
5. No secret in the agent.
6. Only what it is handed. The inputs are what `run.hands` names: `cards` (the agent cards the member sees) and `job`
   (the job's own inputs, by the names the manifest's `inputs` gives them).
7. Nothing fake. The agent answers from what it is handed, or it says plainly that it cannot.

## The job's inputs
An agent that needs words from the member (a name, a mood, a date) declares them:

    "run": {"do": "answer", "hands": ["job"]},
    "inputs": {"name": "001", "mood": "002"}

Each name sits on one of the job's input slots, 001 to 015 (the job's agent fields on the platform). On a RUN, LARRYD
reads that RUN's inputs from the platform and hands them in as `job`: `{"name": "...", "mood": "..."}`. A slot the member
left empty is simply not handed. LARRYD refuses the run when the job holds an input the agent does not declare, or a
value that is not text or is longer than 10,000 characters, and it keeps none of them. In `samples/job.json`, give the
inputs the same way: `{"do": "answer", "job": {"name": "Harbor", "mood": "calm cool"}}`.

## 5. The doctor
    larryd doctor            (or --json)

It checks the project, the manifest, the entry, the air gap, no secret, the shape, the skills and the knowledge.
Every problem names the file and line, what is wrong and what to do. Do what it says, then run it again.
Never silence a check to make it pass.

## 6. Run it here
    larryd run               (or --job <file>, --json)

The doctor runs first. Then the agent runs the way LARRYD runs it: its own process, no network, no new process,
a scratch run folder removed after, the plain Python runtime, an empty environment, 20 seconds. It is handed what
a RUN hands it: `{"do": run.do}` plus what `run.hands` names, from the sample job. The answer must be one JSON object
holding only what `gives` names. Nothing is sent anywhere. It needs a Mac today.

## 7. Submit
    larryd submit

The doctor runs first. Then `agent/` (nothing else) goes to LARRYD, signed with your developer key, for the card
key in `larryd.json`. LARRYD writes it into its locker and sends it to FROST's review. LARRYD checks that LARRYD
holds exactly the bytes you sent (the code's hash and the manifest's hash), then prints the review's state.
A changed agent is a new submission with new hashes, reviewed again.

## 8. Status
    larryd status            (or --json)

What LARRYD records for each of your agents: held or not, FROST's review, runs by state, calls, hires and
unhires, and mTok charged. It holds only your agents' keys and counts: who hired them stays on the platform.

## What LARRYD does with your agent
- It holds `agent/` in its locker with the hash of the code and of the manifest, and checks them on every call and run.
  Any change is refused as tampered.
- FROST's review: a SYSTEM owner approves or rejects those exact hashes. LARRYD shows, hires and runs an agent only
  when FROST approved the hashes it holds. `larryd status` says "approved" or "not approved" (waiting and rejected
  both read "not approved"; FROST's screen says which).
- A member hires the agent in the agent marketplace with a toggle. A RUN is a request; LARRYD runs the agent in its
  sandbox, and mTok charges the agent's own rate (0 = free).

## In Claude Code
In a project made by `larryd new`, open the folder with `claude` and approve the LARRYD tools:
larryd_new, larryd_doctor, larryd_run, larryd_submit, larryd_status, larryd_skills, larryd_pack.
Elsewhere, one line: `claude mcp add larryd -- larryd mcp`. The repository is also a Claude Code plugin marketplace.
The loop for the AI: change the agent → larryd_doctor → larryd_run → fix → again → larryd_submit.

## Skills and knowledge
- A skill is a definition named by its hash. Declare the hashes in `skills`; `larryd skills` lists them.
- A knowledge pack is a folder (`pack.json` with `name` and `about`, plus .md .txt .csv .json files) named by its hash;
  `larryd pack <folder>` checks it and gives the hash.

## Not there yet
- Skills: only one exists, the mTok charge, and LARRYD applies it to every run. FROST sign-in, DA-M store and
  LARRY LLM greeting come as skills when LARRYD has a door for them.
- Knowledge packs: LARRYD holds none yet, so declaring one in `knowledge` fails the doctor. Leave it `[]`.
- `larryd run` on Linux and Windows: it needs a Mac today (macOS sandbox-exec). The doctor works everywhere.
- The job's inputs on the live platform: LARRYD hands `job` today, but the platform's side (the route that gives PF
  LARRYD a RUN's inputs) is not on the live platform yet; until it is, a RUN of an agent that hands `job` fails with
  LARRYD's plain reason. `larryd run` works with them now.
