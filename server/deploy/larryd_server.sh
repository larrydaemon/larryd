#!/bin/bash
# LARRYD's runtime onto a server, from the laptop: server/deploy/larryd_server.sh <commit> [vm] [zone]
# The code at a named commit (git archive of server/: tracked files only, so never an instance, a secret or a venv),
# copied up and installed by install_on_server.sh (its own user, a venv, a fresh instance whose secrets are made THERE,
# a systemd unit on 127.0.0.1 only, restart on failure, logs). Nothing of the laptop's instance ever leaves it.
set -euo pipefail
COMMIT=${1:?usage: larryd_server.sh <commit> [vm] [zone]}
VM=${2:-larryd}
ZONE=${3:-us-central1-a}
REPO=$(cd "$(dirname "$0")/../.." && pwd)
SHA=$(git -C "$REPO" rev-parse --short=12 "$COMMIT^{commit}")
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
TAR="$WORK/larryd-runtime-$SHA.tar.gz"
git -C "$REPO" archive --format=tar.gz --prefix=release/ "$SHA" server > "$TAR"
if tar -tzf "$TAR" | grep -E '(^|/)(instance|secrets|\.venv)(/|$)'; then
    echo "refused: the archive holds an instance, a secret or a venv" >&2
    exit 1
fi
echo "release $SHA: $(tar -tzf "$TAR" | wc -l | tr -d ' ') entries"
gcloud compute scp --zone "$ZONE" "$TAR" "$VM:/tmp/larryd-runtime-$SHA.tar.gz"
gcloud compute ssh "$VM" --zone "$ZONE" --command "sudo bash -s -- $SHA" < "$REPO/server/deploy/install_on_server.sh"
