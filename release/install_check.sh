#!/usr/bin/env bash
# THE STRANGER'S CHECK: on a brand-new machine, install LARRYD from the public registry with one line from larryd.ai, then
# use it the way the page says. usage: release/install_check.sh <pipx|uv|npm|cargo> <version>. Exit 0 only when all pass.
set -u
HOW="$1"; V="$2"; ok=0; bad=0
pass() { echo "PASS $*"; ok=$((ok+1)); }
fail() { echo "FAIL $*"; bad=$((bad+1)); }
W=$(mktemp -d); cd "$W"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
case "$HOW" in
  pipx)  pipx install "larryd==$V" ;;
  uv)    uv tool install --python 3.12 "larryd==$V" ;;
  npm)   npm install -g "larryd@$V" ;;
  cargo) cargo install larryd --version "$V" ;;
esac || fail "the install line"
hash -r
got=$(larryd --version 2>&1 | tail -1); echo "$got"
[ "$got" = "larryd $V" ] && pass "larryd --version is $V" || fail "larryd --version said: $got"
larryd new check-agent >/dev/null 2>&1 && [ -f check-agent/agent/agent.json ] && pass "larryd new" || fail "larryd new"
cd check-agent
larryd doctor > doctor.txt 2>&1; tail -1 doctor.txt
grep -q "passes every check" doctor.txt && pass "larryd doctor" || { cat doctor.txt; fail "larryd doctor"; }
larryd run > run.txt 2>&1; head -4 run.txt
grep -q "larryd run: DONE" run.txt && pass "larryd run (in the sandbox)" || { cat run.txt; fail "larryd run"; }
cd "$W"
python3 - <<'PY' && pass "larryd mcp lists its tools" || fail "larryd mcp"
import json, subprocess
p = subprocess.Popen(['larryd', 'mcp'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
def send(o): p.stdin.write(json.dumps(o) + '\n'); p.stdin.flush()
send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "check", "version": "1"}}})
p.stdout.readline(); send({"jsonrpc": "2.0", "method": "notifications/initialized"}); send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
tools = [t['name'] for t in json.loads(p.stdout.readline())['result']['tools']]; p.terminate(); print(tools)
assert 'larryd_run' in tools and 'larryd_doctor' in tools
PY
python3 - <<'PY' && pass "larryd (the daemon) starts on 127.0.0.1:5010 and Ctrl-C stops it" || fail "the daemon"
import os, pty, select, signal, subprocess, sys, time, urllib.request, urllib.error
pid, fd = pty.fork()
if pid == 0:
    signal.signal(signal.SIGINT, signal.SIG_DFL); os.execvp('larryd', ['larryd'])
out = b''; t = time.time()
while time.time() - t < 30 and b'listens on' not in out:
    if select.select([fd], [], [], 0.5)[0]:
        try: out += os.read(fd, 4096)
        except OSError: break
print(out.decode(errors='replace').strip()[:200])
code = None
for _ in range(20):   # it says "listens on" a moment before the socket takes calls
    try: code = urllib.request.urlopen('http://127.0.0.1:5010/', timeout=5).status
    except urllib.error.HTTPError as e: code = e.code
    except OSError: time.sleep(0.5); continue
    break
print('GET / ->', code)
os.write(fd, b'\x03'); t = time.time(); done = None
while time.time() - t < 15:
    w = os.waitpid(pid, os.WNOHANG)
    if w[0]: done = w[1]; break
    time.sleep(0.2)
if done is None: os.kill(pid, 9)
sys.exit(0 if b'listens on' in out and code == 401 and done is not None else 1)
PY
echo "== $HOW $V on $(uname -sm): $ok passed, $bad failed"
[ "$bad" -eq 0 ] && [ "$ok" -eq 6 ]
