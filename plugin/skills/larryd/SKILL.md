---
name: larryd
description: Build, check and ship a LARRYD agent with LARRYD. Use when working on this agent project - changing agent/agent.py or agent/agent.json, checking the agent, or running it.
---

# Building a LARRYD agent with LARRYD

In an agent project (made by `larryd new`), the agent is the folder `agent/`: the manifest `agent.json` and the code.
The project's CLAUDE.md holds the spec and the rules; read it first.

## The loop
1. `larryd new <name>`: makes a new agent project like this one
2. `larryd doctor`: checks the agent before submission; every problem says what is wrong and what to do (--json for the result as JSON)
3. `larryd run`: runs the agent here the way LARRYD runs it (no network, no new process, a scratch run folder, a time limit), with samples/job.json or --job <file>; it needs a Mac today
4. `larryd skills`: lists the skills an agent may declare in "skills", by hash
5. `larryd pack <folder>`: checks a knowledge pack and gives its hash
6. `larryd mcp`: serves these tools to Claude Code (larryd_new, larryd_doctor, larryd_run, larryd_skills, larryd_pack); this project's .mcp.json starts it

## When something is wrong
Every message from a LARRYD tool says what is wrong and what to do. Do what it says, then run the tool again.
Never hide a problem to make a check pass: a check that is silenced is a lie.
