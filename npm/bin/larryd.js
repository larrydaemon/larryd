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

// -> { py } a Python 3.11 or newer; or { old: '3.9.6' } when only an older one was found; or {} when none was.
function python() {
  const candidates = process.env.LARRYD_PYTHON ? [process.env.LARRYD_PYTHON] : ['python3', 'python'];
  let old = null;
  for (const p of candidates) {
    const r = spawnSync(p, ['-c', 'import sys; print(sys.version_info >= (3, 11), sys.version.split()[0])'], { encoding: 'utf8' });
    const [ok, version] = r.status === 0 ? r.stdout.trim().split(' ') : [];
    if (ok === 'True') return { py: p };
    if (ok === 'False' && !old) old = version;
  }
  return old ? { old } : {};
}

// What to say when pip could not install LARRYD, from pip's own words.
function pipSaid(stderr, spec) {
  if (/No matching distribution found|from versions: none|Could not find a version that satisfies/.test(stderr)) {
    return `LARRYD ${VERSION} is not on PyPI yet, so this launcher cannot install it; set LARRYD_PIP_SPEC to a LARRYD ${VERSION} wheel, or use pipx or uv once it is published`;
  }
  if (/Could not fetch URL|NewConnectionError|Temporary failure in name resolution|Network is unreachable|timed out/.test(stderr)) {
    return `could not reach PyPI to install ${spec}; check the network, then run larryd again`;
  }
  return `pip could not install ${spec} (its words are above); fix what it says, then run larryd again`;
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
    const { py, old } = python();
    if (!py) {
      say(old ? `LARRYD needs Python 3.11 or newer, and python3 here is ${old}; install a newer Python (brew install python, or python.org), or set LARRYD_PYTHON to one, then run larryd again`
              : 'LARRYD needs Python 3.11 or newer, and python3 was not found; install Python, then run larryd again');
      return 1;
    }
    say(`installing LARRYD ${VERSION} (once) into ${venv}`);
    fs.mkdirSync(path.dirname(venv), { recursive: true, mode: 0o700 });
    const made = spawnSync(py, ['-m', 'venv', venv], { stdio: ['ignore', 'ignore', 'inherit'] });
    const spec = process.env.LARRYD_PIP_SPEC || `larryd==${VERSION}`;
    if (made.status !== 0) {
      say(`${py} could not make a venv at ${venv}; check that folder, then run larryd again`);
      return 1;
    }
    const pip = spawnSync(venvPython, ['-m', 'pip', 'install', '-q', spec], { stdio: ['ignore', 'ignore', 'pipe'], encoding: 'utf8' });
    if (pip.status !== 0 || !installed(venvPython)) {
      process.stderr.write(pip.stderr || '');
      say(pipSaid(pip.stderr || '', spec));
      return 1;
    }
  }
  const child = spawn(venvPython, ['-m', 'larryd', ...process.argv.slice(2)], { stdio: 'inherit' });
  for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => child.kill(sig));
  child.on('exit', (code, signal) => process.exit(code === null ? (signal ? 1 : 0) : code));
  return null;
}

if (require.main === module) {
  const code = main();
  if (code !== null) process.exit(code);
}
module.exports = { pipSaid };
