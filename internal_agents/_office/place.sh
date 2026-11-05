#!/bin/bash
# place.sh <agent folder>: pack one internal agent (its agent.json, agent.py, and the office library office.py beside them),
# (and each kit its agent.json "libs" names, _office/<lib>.py), place it in LARRYD RUNTIME INTERNAL under its own card's key (agent.json "key"), and approve it in FROST (the owner's rule
# 2026-10-11: a session may approve agents). Nothing else in the folder is packed.
set -euo pipefail
DIR=$(cd "$1" && pwd); LIB=$(cd "$(dirname "$0")" && pwd)
KEY=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['key'])" "$DIR/agent.json")
I=$HOME/virtual_sanity/runtime_internal/instance   # LARRYD RUNTIME INTERNAL in its own home (the owner 2026-11-05: "nothing internal in larryd")
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
cp "$DIR/agent.json" "$DIR/agent.py" "$LIB/office.py" "$WORK/"
LIBS=$(python3 -c "import json,sys; print(' '.join(l + '.py' for l in json.load(open(sys.argv[1])).get('libs', [])))" "$DIR/agent.json")   # its office kits, named in agent.json "libs" (one source each, in _office)
for l in $LIBS; do cp "$LIB/$l" "$WORK/"; done
PKG="$WORK/$KEY.larryd"; (cd "$WORK" && zip -q "$PKG" agent.json agent.py office.py $LIBS)
OUT=$(cd ~/virtual_sanity/runtime_internal && LARRYD_INTERNAL=1 LARRYD_INSTANCE=$I LARRYD_KEYS_DIR=$I/keys LARRYD_OUTBOUND_DIR=$I/out LARRYD_ENV=localhost.rnd .venv/bin/python -B runtime/app/web/app.py place "$KEY" "$PKG" --slot proof 2>&1 | tail -1)
ID=$(echo "$OUT" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); r=d.get('review') or {}; assert r.get('card_key')=='$KEY', ('card key', d); print(r['id'])")
cd ~/virtual_workspace/fs/fs && WID_ENV=localhost.rnd ~/virtual_workspace/.venv/bin/python -B - "$ID" "$KEY" <<'PY'
import sys, datetime; sys.path.insert(0, 'app')
from core_engine import store, reviews, contacts, signing, global_config
s = store.Store(); account, member = reviews._author(s)
core = contacts.send(global_config.secret('service'), signing.Signer())
got = reviews.decide(s, int(sys.argv[1]), 'approve', f'approved by session 0ed35058 (owner rule 2026-10-11: a session may approve agents): {sys.argv[2]}, the full conversion of 2026-11-03', member, datetime.datetime.now(datetime.timezone.utc), core=core, account=account)
print('placed and approved', sys.argv[2], 'review', sys.argv[1], (got or {}).get('state', got) if isinstance(got, dict) else got)
PY
