// The npm launcher, run for real: no Python is said in one line; the first run installs LARRYD (from this repository)
// into a private venv and hands every argument to it, exit codes included; the second run installs nothing.
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const LAUNCHER = path.join(__dirname, '..', 'bin', 'larryd.js');
const REPO = path.join(__dirname, '..', '..');
const run = (args, env) => spawnSync(process.execPath, [LAUNCHER, ...args], { encoding: 'utf8', env: { ...process.env, ...env }, timeout: 600000 });

test('no Python: one plain line, exit 1', () => {
  const r = run(['help'], { LARRYD_PYTHON: '/nonexistent/python3', LARRYD_VENV: path.join(os.tmpdir(), `larryd-npm-none-${process.pid}`) });
  assert.strictEqual(r.status, 1);
  assert.match(r.stderr, /^larryd: LARRYD needs Python 3\.11 or newer, and python3 was not found; install Python, then run larryd again\n$/);
});

test('an older Python: says which one it found, exit 1', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'larryd-npm-old-'));
  const fake = path.join(dir, 'python3');
  fs.writeFileSync(fake, '#!/bin/sh\necho "False 3.9.6"\n', { mode: 0o755 });
  try {
    const r = run(['help'], { LARRYD_PYTHON: fake, LARRYD_VENV: path.join(dir, 'venv') });
    assert.strictEqual(r.status, 1);
    assert.match(r.stderr, /LARRYD needs Python 3\.11 or newer, and python3 here is 3\.9\.6; install a newer Python/);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('pip\'s words become the right sentence', () => {
  const { pipSaid } = require(LAUNCHER);
  assert.match(pipSaid('ERROR: Could not find a version that satisfies the requirement larryd==0.1.0 (from versions: 0.0.1)\nERROR: No matching distribution found for larryd==0.1.0', 'larryd==0.1.0'),
    /^LARRYD 0\.1\.0 is not on PyPI yet/);
  assert.match(pipSaid("WARNING: Retrying ... NewConnectionError('...: Failed to establish a new connection')", 'larryd==0.1.0'), /^could not reach PyPI/);
  assert.match(pipSaid('ERROR: something else', 'larryd==0.1.0'), /^pip could not install larryd==0\.1\.0 \(its words are above\)/);
});

test('installs once into its own venv, then hands every argument through', () => {
  const venv = fs.mkdtempSync(path.join(os.tmpdir(), 'larryd-npm-venv-'));
  fs.rmSync(venv, { recursive: true });
  const env = { LARRYD_VENV: venv, LARRYD_PIP_SPEC: REPO };
  try {
    const first = run(['help'], env);
    assert.strictEqual(first.status, 0, first.stderr);
    assert.match(first.stderr, /larryd: installing LARRYD 0\.1\.0 \(once\) into /);
    assert.match(first.stdout, /usage: larryd/);
    const second = run(['doctor', path.join(venv, 'no-agent-here'), '--json'], env);
    assert.strictEqual(second.status, 1);                       // the doctor's own exit code, handed back
    assert.strictEqual(second.stderr, '');                      // nothing installed again
    assert.strictEqual(JSON.parse(second.stdout).ok, false);
  } finally {
    fs.rmSync(venv, { recursive: true, force: true });
  }
});
