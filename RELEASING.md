# Releasing LARRYD

One version, three registries, one command, no tokens.

## The release

From a clean, synced `main`:

    release/release.sh 0.1.2

That writes 0.1.2 into every place the version lives (pyproject.toml, npm/package.json, cargo/Cargo.toml,
cargo/Cargo.lock, listings/mcp-registry/server.json), refuses if they ever disagree, runs the Python,
npm and cargo test suites, commits, tags `v0.1.2` and pushes. The push of the tag runs
`.github/workflows/release.yml`, which publishes to PyPI, npm and crates.io and then checks that all
three serve the version. The script waits for that proof and prints it.

`release/release.sh 0.1.2 --no-push` does everything except the push, to look first.

Re-run the publish for a tag that already exists (a registry was down, a job failed):

    gh workflow run release.yml -f tag=v0.1.2

Every publish step skips a version a registry already has, so re-running is always safe.

Check any time: `release/verify.sh 0.1.2 --once`.

## Why no tokens: trusted publishing

Each registry is told, once, to trust this exact workflow in this exact repository. GitHub gives the
running job a short-lived identity (OIDC) and the registry accepts it. Nothing is stored, nothing
expires, nothing to rotate. npm now limits access tokens to 90 days and restricts 2FA bypass, so a
token setup breaks every quarter; this one does not.

The one-time setup, done in each registry's website by the account owner (larrydaemon):

| registry | where | fields |
|---|---|---|
| PyPI | project larryd, Manage, Publishing, "Add a new publisher", GitHub | Owner `larrydaemon`, Repository `larryd`, Workflow name `release.yml`, Environment: leave empty |
| npm | package larryd, Settings, Trusted publisher, GitHub Actions | Organization or user `larrydaemon`, Repository `larryd`, Workflow filename `release.yml`, Environment: leave empty |
| crates.io | crate larryd, Settings, Trusted Publishing, Add, GitHub | Repository owner `larrydaemon`, Repository name `larryd`, Workflow filename `release.yml`, Environment: leave empty |

The workflow name must be exactly `release.yml` in all three. Nothing else is configured anywhere.

## The fallback: publishing from a laptop with tokens

Only for when GitHub is unavailable. `release/release.sh 0.1.2 --local` publishes from this machine
using the three files in `~/.larryd-publish/`, after checking each token is really larrydaemon's:

- `npm_token`: a **granular** access token, package `larryd`, **Read and write**, **Bypass 2FA on**.
  npm caps these at 90 days, so it will be dead when you need it; make a fresh one that day.
- `crates_token`: an API token with scopes **publish-update** and **publish-new**, crate `larryd`.
  A token without publish-update is accepted for everything except publishing a new version
  (crates.io answers 403 "does not have the required permissions"), which is exactly how the first
  0.1.1 attempt failed.
- `pypi_token`: a project token for larryd. PyPI tokens do not expire.

## Not covered here

Docker Hub (`listings/docker/`) and the MCP registry entry (`listings/mcp-registry/server.json`) are
published by their own steps in `listings/README.md`. The version check keeps server.json in step.
