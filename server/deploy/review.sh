#!/bin/bash
# The owner's review of LARRYD's queue on the larryd machine, from the laptop:
#   server/deploy/review.sh list                           the queue (id · name · sha256 · provider · email · when · review · note)
#   server/deploy/review.sh approve <queue id> <card key>  the file into the runtime's locker, to FROST's review; the queue says approved
#   server/deploy/review.sh reject <queue id> <why>        the queue says rejected, and why
# approve: the door's user copies the queued file out (its hash checked), the runtime's user places it (its own guards,
# the locker, FROST's review), and only when that held it is the row marked; the copy is removed either way.
set -euo pipefail
VM=${LARRYD_VM:-larryd}
ZONE=${LARRYD_ZONE:-us-central1-a}
ACTION=${1:?usage: review.sh list | approve <queue id> <card key> | reject <queue id> <why>}
shift
gcloud compute ssh "$VM" --zone "$ZONE" --command "sudo bash -s -- $(printf '%q ' "$ACTION" "$@")" <<'REMOTE'
set -euo pipefail
ACTION=$1; shift
DOOR="sudo -u larrydsubmit env LARRYD_SUBMIT_INSTANCE=/srv/larryd-submit/instance /srv/larryd-submit/venv/bin/python -m larryd.submit_door"
case "$ACTION" in
  list) cd /srv/larryd-submit && $DOOR list ;;
  reject) cd /srv/larryd-submit && $DOOR mark "$1" rejected "${@:2}" ;;
  approve)
    ID=${1:?queue id}; KEY=${2:?card key}
    WORK=$(mktemp -d); chmod 0711 "$WORK"; trap 'rm -rf "$WORK"' EXIT
    chown larrydsubmit "$WORK"
    (cd /srv/larryd-submit && $DOOR export "$ID" "$WORK/agent.larryd")
    chown larryd "$WORK/agent.larryd"; chown larryd "$WORK"
    OUT=$(cd /srv/larryd/current && sudo -u larryd env HANZO_ENV=larryd.pf /srv/larryd/venv/bin/python hanzo/app/web/app.py place "$KEY" "$WORK/agent.larryd")
    echo "$OUT"
    (cd /srv/larryd-submit && $DOOR mark "$ID" approved "$KEY")
    ;;
  *) echo "usage: review.sh list | approve <queue id> <card key> | reject <queue id> <why>" >&2; exit 2 ;;
esac
REMOTE
