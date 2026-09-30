#!/bin/bash
# Runs ON the server as root (larryd_server.sh sends it): install release <sha> of LARRYD's runtime.
set -euo pipefail
SHA=${1:?release}
HOME_DIR=/srv/larryd
REL=$HOME_DIR/releases/$SHA
TAR=/tmp/larryd-runtime-$SHA.tar.gz
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -q python3-venv bubblewrap >/dev/null
id larryd >/dev/null 2>&1 || useradd --system --home-dir $HOME_DIR --shell /usr/sbin/nologin larryd
install -d -o larryd -g larryd -m 0750 $HOME_DIR $HOME_DIR/releases
install -d -o larryd -g larryd -m 0700 $HOME_DIR/instance $HOME_DIR/instance/secrets \
    $HOME_DIR/instance/logs $HOME_DIR/instance/agents
rm -rf "$REL" && mkdir -p "$REL"
tar -xzf "$TAR" -C "$REL" --strip-components=2 && rm -f "$TAR"
ln -sfn $HOME_DIR/instance "$REL/hanzo/instance"
# the code's own agents (the marketplace) are placed in the instance's locker; developers' agents stay there across releases
rm -rf $HOME_DIR/instance/agents/marketplace && cp -R "$REL/hanzo/app/agents/marketplace" $HOME_DIR/instance/agents/marketplace
chown -R larryd:larryd "$REL" $HOME_DIR/instance/agents && chmod -R go-w "$REL"
[ -x $HOME_DIR/venv/bin/python ] || sudo -u larryd python3 -m venv $HOME_DIR/venv
sudo -u larryd $HOME_DIR/venv/bin/pip install -q -r "$REL/requirements.txt"
# its secrets are made HERE, once; nothing is copied from anywhere
[ -s $HOME_DIR/instance/secrets/hanzo_link ] || sudo -u larryd sh -c "umask 077; python3 -c 'import secrets; print(secrets.token_hex(32))' > $HOME_DIR/instance/secrets/hanzo_link"
# the platform is not on a server yet: no address is declared, so every call to it is refused in its own words
[ -f $HOME_DIR/instance/platform.json ] || sudo -u larryd sh -c "umask 077; echo '{}' > $HOME_DIR/instance/platform.json"
ln -sfn "$REL" $HOME_DIR/current
cat > /etc/systemd/system/larryd-runtime.service <<UNIT
[Unit]
Description=LARRYD runtime (release $SHA), on 127.0.0.1 only
After=network-online.target

[Service]
User=larryd
Group=larryd
WorkingDirectory=$HOME_DIR/current
Environment=HANZO_ENV=larryd.pf
ExecStart=$HOME_DIR/venv/bin/python hanzo/app/web/app.py
Restart=on-failure
RestartSec=3
StandardOutput=append:$HOME_DIR/instance/logs/host.log
StandardError=append:$HOME_DIR/instance/logs/host.log
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$HOME_DIR/instance

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable -q larryd-runtime
systemctl restart larryd-runtime
for i in $(seq 1 40); do ss -tln | grep -q '127.0.0.1:5010 ' && break; sleep 0.25; done
echo "release $SHA installed; listening: $(ss -tln | awk '{print $4}' | grep ':5010$' || echo NOTHING)"
