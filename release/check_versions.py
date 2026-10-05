#!/usr/bin/env python3
"""One version everywhere. Reads every place LARRYD's version is written and refuses if they differ.

    python release/check_versions.py            all places must agree
    python release/check_versions.py v0.1.2     ...and equal the tag (leading v dropped)

Places: pyproject.toml, npm/package.json, cargo/Cargo.toml, cargo/Cargo.lock, listings/mcp-registry/server.json.
Standard library only, so it runs anywhere (3.11 or newer).
"""
import json
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def places():
    out = {}
    out["pyproject.toml"] = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    out["npm/package.json"] = json.loads((ROOT / "npm/package.json").read_text())["version"]
    out["cargo/Cargo.toml"] = tomllib.loads((ROOT / "cargo/Cargo.toml").read_text())["package"]["version"]
    lock = (ROOT / "cargo/Cargo.lock").read_text()
    m = re.search(r'\[\[package\]\]\nname = "larryd"\nversion = "([^"]+)"', lock)
    out["cargo/Cargo.lock"] = m.group(1) if m else "(no larryd entry)"
    mcp = ROOT / "listings/mcp-registry/server.json"
    if mcp.exists():
        out["listings/mcp-registry/server.json"] = json.loads(mcp.read_text()).get("version", "(none)")
    return out


def main(argv):
    want = argv[1].lstrip("v") if len(argv) > 1 else None
    found = places()
    width = max(len(k) for k in found)
    for k, v in found.items():
        print(f"  {k:<{width}}  {v}")
    versions = set(found.values())
    if len(versions) != 1:
        print("REFUSED: the versions differ", file=sys.stderr)
        return 1
    (only,) = versions
    if want and only != want:
        print(f"REFUSED: files say {only}, tag says {want}", file=sys.stderr)
        return 1
    print(f"OK: {only} everywhere" + (f", matches tag v{want}" if want else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
