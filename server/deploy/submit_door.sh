#!/bin/bash
# LARRYD's submit door onto the larryd machine, from the laptop: server/deploy/submit_door.sh <commit> [vm] [zone]
# A wheel built from a clean export of the commit, copied up, installed (with the door extra) into its own venv under its
# own user; systemd serves it on 127.0.0.1:5011; nginx sends /submit/ there on login.positivefeedback.ai. The instance
# (larryd_submit.db, held/, queue/) is made there and outlives every release.
set -euo pipefail
COMMIT=${1:?usage: submit_door.sh <commit> [vm] [zone]}
VM=${2:-larryd}
ZONE=${3:-us-central1-a}
REPO=$(cd "$(dirname "$0")/../.." && pwd)
SHA=$(git -C "$REPO" rev-parse --short=12 "$COMMIT^{commit}")
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
git -C "$REPO" archive "$SHA" | tar -x -C "$WORK" --exclude website
python3 -m venv "$WORK/.build" >/dev/null && "$WORK/.build/bin/pip" install -q build
(cd "$WORK" && .build/bin/python -m build --wheel --outdir "$WORK/dist" . >/dev/null)
WHEEL=$(ls "$WORK"/dist/larryd-*.whl)
echo "wheel $(basename "$WHEEL") from $SHA"
gcloud compute scp --zone "$ZONE" "$WHEEL" "$VM:/tmp/" >/dev/null
gcloud compute ssh "$VM" --zone "$ZONE" --command "sudo bash -s -- /tmp/$(basename "$WHEEL") $SHA" <<'REMOTE'
set -euo pipefail
WHEEL=$1; SHA=$2; HOME_DIR=/srv/larryd-submit
id larrydsubmit >/dev/null 2>&1 || useradd --system --home-dir $HOME_DIR --shell /usr/sbin/nologin larrydsubmit
install -d -o larrydsubmit -g larrydsubmit -m 0755 $HOME_DIR
install -d -o larrydsubmit -g larrydsubmit -m 0700 $HOME_DIR/instance
[ -x $HOME_DIR/venv/bin/python ] || sudo -u larrydsubmit python3 -m venv $HOME_DIR/venv
install -o larrydsubmit -m 0644 "$WHEEL" $HOME_DIR/
sudo -u larrydsubmit $HOME_DIR/venv/bin/pip install -q --force-reinstall --no-deps $HOME_DIR/$(basename "$WHEEL")
sudo -u larrydsubmit $HOME_DIR/venv/bin/pip install -q "$HOME_DIR/$(basename "$WHEEL")[door]" gunicorn
rm -f "$WHEEL"
cat > /etc/systemd/system/larryd-submit.service <<UNIT
[Unit]
Description=LARRYD submit door (login.positivefeedback.ai/submit/)
After=network.target

[Service]
User=larrydsubmit
Group=larrydsubmit
WorkingDirectory=$HOME_DIR
ExecStart=$HOME_DIR/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5011 'larryd.submit_door:create_app("$HOME_DIR/instance")'
Restart=on-failure
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$HOME_DIR/instance
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable larryd-submit >/dev/null 2>&1
systemctl restart larryd-submit
SITE=/etc/nginx/sites-available/login
if ! grep -q 'location /submit/' $SITE; then
    cp $SITE /root/login.bak_$(date -u +%Y%m%dT%H%M%SZ)
    python3 - "$SITE" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
block = '''    location /submit/ {
        client_max_body_size 5m;
        proxy_pass http://127.0.0.1:5011;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
    location / { return 404; }
}
server {
    listen 443 ssl default_server;'''
old = '''    location / { return 404; }
}
server {
    listen 443 ssl default_server;'''
assert t.count(old) == 1
p.write_text(t.replace(old, block))
PY
fi
nginx -t 2>&1 | tail -1
systemctl reload nginx
sleep 2
systemctl is-active larryd-submit
echo "submit door $SHA"
REMOTE
