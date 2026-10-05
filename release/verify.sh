#!/usr/bin/env bash
# Proof, not a claim: ask each public registry whether it serves LARRYD <version>.
#   release/verify.sh 0.1.2            waits up to 5 minutes for all three (registries take a moment)
#   release/verify.sh 0.1.2 --once     one look, no waiting
# Exit 0 only when PyPI, npm and crates.io all have the version.
set -u
V="${1:?usage: release/verify.sh <version> [--once]}"; V="${V#v}"
ONCE="${2:-}"
TRIES=20; [ "$ONCE" = "--once" ] && TRIES=1

pypi()   { curl -fsS --max-time 20 "https://pypi.org/pypi/larryd/$V/json" >/dev/null 2>&1; }
npmv()   { curl -fsS --max-time 20 "https://registry.npmjs.org/larryd/$V" >/dev/null 2>&1; }
crates() { curl -fsS --max-time 20 -A "larryd-release" "https://crates.io/api/v1/crates/larryd/$V" >/dev/null 2>&1; }

for ((i = 1; i <= TRIES; i++)); do
  p=no; n=no; c=no
  pypi && p=yes; npmv && n=yes; crates && c=yes
  printf "larryd %s  PyPI:%-3s npm:%-3s crates.io:%-3s\n" "$V" "$p" "$n" "$c"
  if [ "$p$n$c" = "yesyesyes" ]; then echo "OK: every registry serves larryd $V"; exit 0; fi
  [ "$i" -lt "$TRIES" ] && sleep 15
done
echo "NOT YET: a registry is missing larryd $V (see the last line)" >&2
exit 1
