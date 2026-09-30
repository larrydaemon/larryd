---
name: larryd
description: Build, check and ship a LARRYD agent with LARRYD. Use when working on this agent project - changing agent/agent.py or agent/agent.json, checking the agent, running it, or submitting it.
---

# Building a LARRYD agent with LARRYD

In an agent project (made by `larryd new`), the agent is the folder `agent/`: the manifest `agent.json` and the code.
The project's CLAUDE.md holds the spec and the rules; read it first.

## The loop
{loop}

## When something is wrong
Every message from a LARRYD tool says what is wrong and what to do. Do what it says, then run the tool again.
Never hide a problem to make a check pass: a check that is silenced is a lie.
