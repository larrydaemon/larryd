# LARRYD

<!-- mcp-name: io.github.larrydaemon/larryd -->

Your server has a daemon. Your agents should have one too.

Build, test and ship AI agents with Claude Code.

Your agent runs on LARRYD, air gapped, owned by its developer; LARRYD connects it to the platform by API only.

## Install
    pipx install larryd
    uv tool install larryd
    npm install -g larryd
    cargo install larryd
    larryd

Any one of the first four gives the command `larryd`. Each needs Python 3.11 or newer (`python3 --version` says
which you have; a Mac's own python3 is 3.9), except uv, which brings its own. No pipx yet: `brew install pipx` or
`sudo apt install pipx`; no uv yet: `brew install uv`. npm and cargo install a thin launcher that keeps LARRYD in its
own place. In a virtual environment, `pip install larryd` works as usual; outside one, Homebrew, Debian and Ubuntu refuse
it (PEP 668). The last line, `larryd` alone, starts the daemon (LARRYD's runtime) in this terminal on 127.0.0.1, with
its instance in ~/.larryd (`LARRYD_PORT` and `LARRYD_INSTANCE` name others); Ctrl-C stops it. No sudo: as root its instance is /var/lib/larryd, for a server.
From the repository: `pipx install git+https://github.com/larrydaemon/larryd.git`.
(Until 0.1.0 is published, PyPI, npm and crates.io hold only the name's reservation, 0.0.1.)

One command, `larryd` (`larryd help` lists them, `larryd --version` says which; `larryd` alone starts the daemon):
- `larryd new <name>`: a new agent project (the agent, its CLAUDE.md, the larryd skill, a sample job, the connector)
- `larryd doctor`: the pretest before submission; every problem says what is wrong and what to do
- `larryd run`: runs the agent here the way LARRYD runs it, with the sample job
- `larryd key <address> <name>`: keeps your developer key from LARRYD and checks it with LARRYD (the secret is pasted, never
  typed on the command line); `larryd key` alone says where a key and your agent's card key come from
- `larryd submit`: sends the agent to LARRYD for FROST's review, after the doctor (the card key is in the project's larryd.json)
- `larryd status`: what LARRYD records for your agents: held, the review, runs, calls, hires, mTok charged
- `larryd skills`, `larryd pack <folder>`: the skills an agent may declare; a knowledge pack's hash
- `larryd developer add <name> <card key>`: on your own LARRYD (the daemon here), a developer; the secret is shown once
- `larryd mcp`: serves the tools to Claude Code (never the key)

## With Claude Code
- In a project made by `larryd new`, its `.mcp.json` starts the connector: open the folder with `claude` and approve it.
- Anywhere else, one line: `claude mcp add larryd -- larryd mcp`
- As a plugin (the tools and the skill): this repository is a Claude Code marketplace; its plugin is `plugin/`.

## Tests
    python3 -m venv .venv && .venv/bin/pip install -e . pytest && .venv/bin/python -m pytest -q
`proofs/claude_code_fixes_an_agent.sh` shows Claude Code fixing a planted agent with the tools (it uses the claude command).

© 2026 COTECLAT LLC. All rights reserved.
