#!/bin/sh
# The proof that the connector works with Claude Code itself: a scratch agent with two planted problems (a network
# import and a key); headless Claude Code, given only the larryd tools plus Read and Edit, fixes it from the doctor's
# words and runs it. Uses the claude command (and its tokens). Everything happens in a scratch folder, removed after.
set -e
LARRYD="$(cd "$(dirname "$0")/.." && pwd)/.venv/bin/larryd"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"
"$LARRYD" new proof-agent >/dev/null
KEY="sk-""ant-api03-plantedplantedplanted"   # built from pieces: no whole key-shaped string sits in this file
printf '\nimport socket\nAPI_KEY = "%s"\n' "$KEY" >> proof-agent/agent/agent.py
printf '{"mcpServers":{"larryd":{"command":"%s","args":["mcp"]}}}' "$LARRYD" > mcp.json
cd proof-agent
"$LARRYD" doctor . | tail -1
claude -p "This is a LARRYD agent project. Call larryd_doctor, fix every problem it reports by following its 'todo', call larryd_doctor again until ok is true, then call larryd_run and reply with its state and answer." \
  --mcp-config ../mcp.json --strict-mcp-config --allowedTools "mcp__larryd__larryd_doctor,mcp__larryd__larryd_run,Read,Edit" \
  --model haiku --output-format text
"$LARRYD" doctor . | tail -1
"$LARRYD" run . | head -1
