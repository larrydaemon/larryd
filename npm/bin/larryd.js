#!/usr/bin/env node
// LARRYD from npm: a thin launcher. LARRYD itself is a Python package; this finds Python 3.11 or newer, keeps LARRYD in
// its own place (~/.larryd/venv, or /var/lib/larryd/venv as root; LARRYD_VENV names another), installs the same version
// as this package there once, and hands every argument to it. `larryd` alone starts the daemon.
'use strict';
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const VERSION = require('../package.json').version;
const say = (line) => process.stderr.write(`larryd: ${line}\n`);

function python() {
  const candidates = process.env.LARRYD_PYTHON ? [process.env.LARRYD_PYTHON] : ['python3', 'python'];
  for (const p of candidates) {
    const r = spawnSync(p, ['-c', 'import sys; print(sys.version_info >= (3, 11))'], { encoding: 'utf8' });
    if (r.status === 0 && r.stdout.trim() === 'True') return p;
  }
  return null;
}

function venvDir() {
  if (process.env.LARRYD_VENV) return process.env.LARRYD_VENV;
  const root = typeof process.getuid === 'function' && process.getuid() === 0;
  return root ? '/var/lib/larryd/venv' : path.join(os.homedir(), '.larryd', 'venv');
}

function installed(venvPython) {
  if (!fs.existsSync(venvPython)) return false;
  const r = spawnSync(venvPython, ['-c', 'import larryd; print(larryd.__version__)'], { encoding: 'utf8' });
  return r.status === 0 && r.stdout.trim() === VERSION;
}

function main() {
  const venv = venvDir();
  const venvPython = path.join(venv, 'bin', 'python');
  if (!installed(venvPython)) {
    const py = python();
    if (!py) {
      say('LARRYD needs Python 3.11 or newer, and python3 was not found; install Python, then run larryd again');
      return 1;
    }
    say(`installing LARRYD ${VERSION} (once) into ${venv}`);
    fs.mkdirSync(path.dirname(venv), { recursive: true, mode: 0o700 });
    const made = spawnSync(py, ['-m', 'venv', venv], { stdio: ['ignore', 'ignore', 'inherit'] });
    const spec = process.env.LARRYD_PIP_SPEC || `larryd==${VERSION}`;
    const pip = made.status === 0 ? spawnSync(venvPython, ['-m', 'pip', 'install', '-q', spec], { stdio: ['ignore', 'ignore', 'inherit'] }) : made;
    if (pip.status !== 0 || !installed(venvPython)) {
      say(`could not install LARRYD ${VERSION} into ${venv}; check the network and Python, then run larryd again`);
      return 1;
    }
  }
  const child = spawn(venvPython, ['-m', 'larryd', ...process.argv.slice(2)], { stdio: 'inherit' });
  for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => child.kill(sig));
  child.on('exit', (code, signal) => process.exit(code === null ? (signal ? 1 : 0) : code));
  return null;
}

const code = main();
if (code !== null) process.exit(code);
