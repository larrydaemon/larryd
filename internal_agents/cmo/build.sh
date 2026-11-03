#!/bin/bash
# build.sh: each CMO agent's folder (agent/) from the one office source (office_src/): the office's code whole (cmo/app), the launcher, its own agent.json and which agent it is.
set -euo pipefail
C=$(cd "$(dirname "$0")" && pwd)
for pair in chief_marketing_officer:mark_iv standup:standup one_min_sm_video:one_min_sm_video; do
  slug=${pair%%:*}; key=${pair##*:}; A=$C/$slug/agent
  mkdir -p "$A"; rm -rf "$A/cmo" "$A/agent.py"
  cp -R "$C/office_src/cmo" "$A/cmo"; cp "$C/office_src/launcher/agent.py" "$A/agent.py"; echo "$key" > "$A/office_agent.txt"
  find "$A" -name __pycache__ -prune -exec rm -rf {} +
done
