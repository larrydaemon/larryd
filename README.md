# LARRYD

Build an agent for LARRYD with Claude Code. The agent lives in LARRYD, air gapped, owned by its developer;
LARRYD connects it to the platform by API only.

## Install
    pip install git+<this repository>

One command, `larryd`:
- `larryd new <name>`: a new agent project (the agent, its CLAUDE.md, the larryd skill, a sample job, the connector)
- `larryd doctor`: the pretest before submission; every problem says what is wrong and what to do
- `larryd run`: runs the agent here the way LARRYD runs it, with the sample job (needs a Mac today)
- `larryd key <address> <name>`: keeps your developer key from LARRYD (the secret is pasted, never typed on the command line)
- `larryd submit`: sends the agent to LARRYD for FROST's review, after the doctor (the card key is in the project's larryd.json)
- `larryd status`: what LARRYD records for your agents: held, the review, runs, calls, hires, mTok charged
- `larryd skills`, `larryd pack <folder>`: the skills an agent may declare; a knowledge pack's hash
- `larryd mcp`: serves the tools to Claude Code (never the key)

## With Claude Code
- In a project made by `larryd new`, its `.mcp.json` starts the connector: open the folder with `claude` and approve it.
- Anywhere else, one line: `claude mcp add larryd -- larryd mcp`
- As a plugin (the tools and the skill): this repository is a Claude Code marketplace; its plugin is `plugin/`.

## Tests
    python3 -m venv .venv && .venv/bin/pip install -e . pytest && .venv/bin/python -m pytest -q
`proofs/claude_code_fixes_an_agent.sh` shows Claude Code fixing a planted agent with the tools (it uses the claude command).
