#!/usr/bin/env bash
# THE ONE RELEASE COMMAND. From a clean main:
#
#   release/release.sh 0.1.2
#
# writes 0.1.2 into every place the version lives, proves they agree, runs the three test suites,
# commits, tags v0.1.2 and pushes. GitHub Actions (.github/workflows/release.yml) then publishes to
# PyPI, npm and crates.io by trusted publishing, and this script waits until all three serve it.
# No token is needed or stored anywhere for the normal path.
#
#   release/release.sh 0.1.2 --no-push    everything except the push (look first)
#   release/release.sh 0.1.2 --local      publish from this machine instead of GitHub, with the
#                                         tokens in ~/.larryd-publish (see RELEASING.md for what
#                                         each token must be). For when GitHub is unavailable.
set -euo pipefail
cd "$(dirname "$0")/.."

V="${1:?usage: release/release.sh <version> [--no-push|--local]}"; V="${V#v}"; MODE="${2:-}"
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "version must look like 0.1.2"; exit 1; }

# ---- preflight -------------------------------------------------------------------------------
[ "$(git branch --show-current)" = "main" ] || { echo "release from main (you are on $(git branch --show-current))"; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "the tree is not clean; commit or stash first"; git status --short; exit 1; }
git fetch -q origin main --tags
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "main is not in sync with origin/main"; exit 1; }
git rev-parse -q --verify "refs/tags/v$V" >/dev/null && { echo "tag v$V already exists"; exit 1; }

# ---- the version, written everywhere ------------------------------------------------------
python3 - "$V" <<'PY'
import json, pathlib, re, sys
v = sys.argv[1]
def sub_first(path, pattern, repl):
    p = pathlib.Path(path); s = p.read_text(); new, n = re.subn(pattern, repl, s, count=1, flags=re.M)
    assert n == 1, f"could not find the version line in {path}"; p.write_text(new)
sub_first("pyproject.toml", r'^version = "[^"]+"', f'version = "{v}"')
sub_first("cargo/Cargo.toml", r'^version = "[^"]+"', f'version = "{v}"')
sub_first("npm/package.json", r'"version": "[^"]+"', f'"version": "{v}"')
mcp = pathlib.Path("listings/mcp-registry/server.json")
if mcp.exists():
    d = json.loads(mcp.read_text()); d["version"] = v
    for pkg in d.get("packages", []):
        if "version" in pkg: pkg["version"] = v
    mcp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {v} into pyproject.toml, cargo/Cargo.toml, npm/package.json" + (", listings/mcp-registry/server.json" if mcp.exists() else ""))
PY
( cd cargo && (cargo update --workspace --offline -q 2>/dev/null || cargo update --workspace -q) )   # Cargo.lock follows

# ---- proof before anything leaves this machine ---------------------------------------------
python3 release/check_versions.py "v$V"
echo "--- tests ---"
VENV=~/.larryd-publish/venv                      # the release's own Python, made on first use, outside the repo
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet -e ".[door]" pytest build twine
"$VENV/bin/python" -m pytest -q tests
( cd npm && npm test --silent )
( cd cargo && cargo test -q )

# ---- commit and tag ---------------------------------------------------------------------------
git add -A
git commit -q -m "LARRYD $V: one version everywhere (pip, npm, cargo, the registry entry)"
git tag -a "v$V" -m "LARRYD $V"
echo "committed and tagged v$V"
[ "$MODE" = "--no-push" ] && { echo "not pushed (--no-push). To release: git push origin main --tags"; exit 0; }

if [ "$MODE" = "--local" ]; then
  # Fallback: publish from here. Each token is checked for identity before anything is uploaded.
  P=~/.larryd-publish
  [ -s "$P/npm_token" ] && [ -s "$P/crates_token" ] && [ -s "$P/pypi_token" ] || { echo "tokens missing in $P (see RELEASING.md)"; exit 1; }
  T=$(mktemp -d); chmod 700 "$T"; printf '//registry.npmjs.org/:_authToken=%s\n' "$(cat "$P/npm_token")" > "$T/npmrc"; chmod 600 "$T/npmrc"
  WHO=$(npm whoami --userconfig "$T/npmrc" 2>/dev/null || true)
  [ "$WHO" = "larrydaemon" ] || { echo "npm token is not larrydaemon's or is dead (whoami said '$WHO'); make a new granular token, see RELEASING.md"; rm -rf "$T"; exit 1; }
  CARGO_REGISTRY_TOKEN="$(cat "$P/crates_token")" cargo owner --list larryd >/dev/null 2>&1 || { echo "crates token rejected; make a new one with publish-update, see RELEASING.md"; rm -rf "$T"; exit 1; }
  git push -q origin main --tags
  rm -rf dist && "$VENV/bin/python" -m build >/dev/null
  TWINE_USERNAME=__token__ TWINE_PASSWORD="$(cat "$P/pypi_token")" "$VENV/bin/python" -m twine upload --skip-existing dist/*
  ( cd npm && npm publish --access public --userconfig "$T/npmrc" )
  ( cd cargo && CARGO_REGISTRY_TOKEN="$(cat "$P/crates_token")" cargo publish )
  rm -rf "$T"
else
  git push -q origin main --tags
  echo "pushed: GitHub Actions is publishing v$V (gh run watch, or https://github.com/larrydaemon/larryd/actions)"
fi

bash release/verify.sh "$V"
