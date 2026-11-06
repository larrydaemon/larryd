# A CMO office agent in LARRYD RUNTIME INTERNAL (moved from ~/virtual_sanity/cmo, 2026-11-03)

- Not sandboxed: agent.json "internal" makes LARRYD RUNTIME INTERNAL run agent/agent.py as this computer's own process.
- agent/agent.py hands the call to the office's own code, moved whole into agent/cmo/app (bridge.py, sanitize.py beside it), run by
  ~/virtual_workspace/.venv/bin/python. Its state: ~/larryd/server/runtime/internal/instance/data/cmo (cmo.db, press_tokens.json).
- Edit the office code in ../office_src/ and run ../build.sh (it copies it into every CMO agent's agent/), then place_internal.sh.
- Prove by hand: CMO_PROOF=1 python3 agent/agent.py < samples/run.json (the RUN writes nothing into LARRYD); samples/call.json for a CALL.
