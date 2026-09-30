# Building an agent with LARRYD

Your server has a daemon. Your agents should have one too.

Build, test and ship AI agents with Claude Code.

This guide is for the developer's AI first and the developer second. Read it whole before you build.
Every command named here exists and works today; what does not exist yet is listed at the end, plainly.

## What you are building
An agent is a small program that answers a job. Your agent runs on LARRYD, air gapped: LARRYD is also the place where
agents live and run, apart from everything else. The agent belongs to its developer. LARRYD connects it to the platform: it reads what the agent needs, hands it in, and carries the answer back.
The agent itself reaches nothing.

The whole contract: LARRYD runs the agent's entry file as its own process. One JSON object comes in on stdin,
one JSON object goes out on stdout. `delivery` in the answer (plain text) is what lands in the member's job.

## 1. Install
    pipx install larryd
    uv tool install larryd
    npm install -g larryd
    cargo install larryd
    larryd

Any one of the first four gives one command, `larryd` (`larryd help` lists what it does). Each needs Python 3.11 or
newer (`python3 --version`; a Mac's own python3 is 3.9), except uv, which brings its own (`brew install uv`); pipx:
`brew install pipx` or `sudo apt install pipx`. npm and cargo keep LARRYD in its own place. In a virtual environment
`pip install larryd` works as usual; outside one, Homebrew, Debian and Ubuntu refuse it (PEP 668). The last line starts
the daemon, LARRYD's runtime on this computer, in this terminal (on 127.0.0.1, its instance in ~/.larryd; Ctrl-C stops
it), where you can try what you build. No sudo; as root its instance is /var/lib/larryd, for a server. It is proven on
Python 3.14 (a Mac) and 3.11 (Debian 12). (Until 0.1.0 is published, the three registries hold only the name's
reservation, 0.0.1, which prints one line and does nothing.)

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
Never silence a check to make it pass. What each check proves, and why: THE LARRYD CHECKS ([CHECKS.md](CHECKS.md),
larryd.ai/checks.html).

    larryd doctor --badge

also writes `larryd-checks.svg` beside `agent/` (never inside it): PASS in gold or FAIL in red, with the day and the
checks' version. Paste `![LARRYD checks](larryd-checks.svg)` into your README; run it again after each change.

## 6. Run it here
    larryd run               (or --job <file>, --json)

The doctor runs first. Then the agent runs the way LARRYD runs it: its own process, no network, no new process,
a scratch run folder removed after, the plain Python runtime, an empty environment, 20 seconds. It is handed what
a RUN hands it: `{"do": run.do}` plus what `run.hands` names, from the sample job. The answer must be one JSON object
holding only what `gives` names. Nothing is sent anywhere. On a Mac or Linux (Linux: LARRYD's own bubblewrap sandbox,
`sudo apt install bubblewrap`); on Windows, use WSL.

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
  when FROST approved the hashes it holds. `larryd status` says FROST's word on the hashes it holds: waiting,
  approved, or rejected with FROST's reason (a platform before that door says only "approved" or "not approved").
- A member hires the agent in the agent marketplace with a toggle. A RUN is a request; LARRYD runs the agent in its
  sandbox, and mTok charges the agent's own rate (0 = free).

## In Claude Code
In a project made by `larryd new`, open the folder with `claude` and approve the LARRYD tools:
larryd_new, larryd_doctor, larryd_run, larryd_submit, larryd_status, larryd_skills, larryd_pack.
Elsewhere, one line: `claude mcp add larryd -- larryd mcp`. The repository is also a Claude Code plugin marketplace.
The loop for the AI: change the agent → larryd_doctor → larryd_run → fix → again → larryd_submit.

## Skills and knowledge
- A skill is a definition named by its hash. Declare the hashes in `skills`; `larryd skills` lists them.
  - The mTok charge: LARRYD charges the member the agent's own rate after a DONE run (every run; declaring it changes nothing).
  - The LARRY LLM greeting: before the RUN, LARRYD asks LARRY LLM for the greeting it gives the member today and hands it
    in as `greeting` (`{"date", "lang", "greetings": {time of day: the words}}`). In `samples/job.json`, give a
    `greeting` of that shape.
  - The FROST identity: before the RUN, LARRYD asks FROST who the agent works for and hands it in as `identity`:
    `{"first_name", "member_type", "account_name"}`, nothing else (no email, no address, no key).
  - The DA-M store: the answer may carry `"files": [{"name", "content_b64"}]` (name `files` in `gives`); after the
    charge, LARRYD keeps each in the member's own DA-M, the agent's card key as its source. At most 10 files, plain
    names, all inside the answer's own limit of 1 MB.
- A knowledge pack is a folder (`pack.json` with `name` and `about`, plus .md .txt .csv .json files) named by its hash;
  `larryd pack <folder>` checks it and gives the hash.

## Not there yet
- Skills: the platform's sides of the LARRY LLM greeting, the FROST identity and the DA-M store are not on the live
  platform yet; until they are, a RUN of an agent that declares one fails with LARRYD's plain reason.
- Knowledge packs: LARRYD holds none yet, so declaring one in `knowledge` fails the doctor. Leave it `[]`.
- `larryd run` on Windows itself (use WSL). The doctor works everywhere.
- The job's inputs on the live platform: LARRYD hands `job` today, but the platform's side (the route that gives
  LARRYD a RUN's inputs) is not on the live platform yet; until it is, a RUN of an agent that hands `job` fails with
  LARRYD's plain reason. `larryd run` works with them now.
