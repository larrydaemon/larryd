# LARRYD

<!-- mcp-name: io.github.larrydaemon/larryd -->

Your server has a daemon. Your agents should have one too.

Build, test and ship AI agents with Claude Code.

Your agent runs on LARRYD, air gapped, owned by its developer; LARRYD connects it to the platform by API only.

## Install
    npm install -g larryd
    pip install larryd
    pipx install larryd
    cargo install larryd
    sudo larryd &

Any one of the first four gives the command `larryd`; the last starts the daemon: LARRYD's runtime on this machine,
on 127.0.0.1 (as root its instance is /var/lib/larryd; as anyone else, ~/.larryd). npm and cargo install a thin
launcher that keeps LARRYD in its own place and needs Python 3.11 or newer. A system that manages its own Python
(Debian, Ubuntu, Homebrew) refuses a plain `pip install`: there use pipx (`brew install pipx` or
`sudo apt install pipx` first), npm, cargo, or a venv. `sudo larryd &` needs
`larryd` on root's PATH. From the repository: `pip install git+https://github.com/larrydaemon/larryd.git`.
(Until 0.1.0 is published, PyPI, npm and crates.io hold only the name's reservation, 0.0.1.)

One command, `larryd` (`larryd help` lists them; `larryd` alone starts the daemon):
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

© 2026 COTECLAT LLC. All rights reserved.
