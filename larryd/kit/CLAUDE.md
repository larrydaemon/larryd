# {name}: an agent for LARRYD

You are building one agent. It runs on LARRYD, air gapped (LARRYD is also the place where agents live and
run, apart from everything else), owned by its developer. The platform reaches it only through LARRYD; the agent itself reaches nothing. Read this whole file before you change anything.

## What an agent is
- The folder `agent/` is the agent. It is exactly what LARRYD holds in its locker: the manifest `agent/agent.json`
  and the code. Nothing else in this project goes to LARRYD.
- LARRYD runs the entry (`agent/agent.py`) as its own process. One JSON object comes in on stdin, one JSON object
  goes out on stdout. That is the whole contract.
- The job it is handed: `{{"do": "<one of does>", ...the inputs named in run.hands}}`.
- Its answer: one JSON object. `delivery` (plain text) is what lands in the member's job.

## The manifest (`agent/agent.json`)
{fields}

## The rules (LARRYD's sandbox refuses 1, 2 and 3 when the agent runs)
1. No network, ever. The agent imports no network module and calls no address. LARRYD fetches what the agent
   needs from the platform and hands it in; the agent answers. A network call is refused at run time.
2. Nothing outside its own folder. No path to another folder, no link, no reading or writing elsewhere. It may write
   only in the folder it is run in (it is made for the run and removed after).
3. No new process. No subprocess, no os.system, no multiprocessing.
4. The Python standard library only. LARRYD runs the plain Python runtime: no installed packages.
5. No secret in the agent. No key, token, password or private key in any file.
6. Only what it is handed. The inputs are what run.hands names, from what LARRYD hands today: {hands}.
7. Nothing fake. The agent answers from what it is handed, or it says plainly that it cannot.
8. Plain words. Names as they are: LARRYD, FROST, mTok, DA-M, LARRY LLM.

## The tools
{tools}
