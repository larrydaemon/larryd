---
name: larryd
description: Build, check and ship an AI agent with LARRYD. Use when working on this agent project - changing agent/agent.py or agent/agent.json, checking the agent, running it, or submitting it.
---

# Building an agent with LARRYD

In an agent project (made by `larryd new`), the agent is the folder `agent/`: the manifest `agent.json` and the code.
The project's CLAUDE.md holds the spec and the rules; read it first.

## The loop
1. `larryd new <name>`: makes a new agent project like this one
2. `larryd doctor`: checks the agent before submission; every problem says what is wrong and what to do (--json for the result as JSON)
3. `larryd run`: runs the agent here the way LARRYD runs it (no network, no new process, a scratch run folder, a time limit), with samples/job.json or --job <file>; it needs a Mac today
4. `larryd key <address> <name>`: keeps your developer key from LARRYD (paste the secret when asked; it is never stored in the project)
5. `larryd submit`: sends the agent (agent/ only) to LARRYD for FROST's review, after the doctor; the card key is in larryd.json
6. `larryd status`: what LARRYD records for your agents: held, the review, runs, calls, hires and mTok charged
7. `larryd skills`: lists the skills an agent may declare in "skills", by hash
8. `larryd pack <folder>`: checks a knowledge pack and gives its hash
9. `larryd mcp`: serves these tools to Claude Code (larryd_new, larryd_doctor, larryd_run, larryd_submit, larryd_status, larryd_skills, larryd_pack; never the key); this project's .mcp.json starts it

## When something is wrong
Every message from a LARRYD tool says what is wrong and what to do. Do what it says, then run the tool again.
Never hide a problem to make a check pass: a check that is silenced is a lie.
