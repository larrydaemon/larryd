"""THE SANDBOX: every agent runs as its own process with nothing but what it is handed, by the system the runtime runs on:
macOS sandbox-exec, or on Linux bubblewrap (bwrap) with a seccomp filter; on any other system nothing runs.
- no network at all (the harness makes every call; an agent never does);
- no new process (no fork, no other program);
- writes only in its own run folder (made for the run, removed after), never into the locker;
- reads nothing private: on macOS nothing under /Users but its own folder; on Linux nothing but its own folder, its run
  folder and the Python runtime (the binary, its standard library, its shared libraries);
- an empty environment, one JSON object in on stdin, one JSON object out on stdout, inside the time limit.
Anything else is FAILED with the kind of failure (never the agent's words)."""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

_BASE = os.path.realpath(sys.base_prefix)
_FRAMEWORK = os.path.join(_BASE, 'Resources', 'Python.app', 'Contents', 'MacOS', 'Python')   # a framework python3 only spawns this
PYTHON = _FRAMEWORK if os.path.isfile(_FRAMEWORK) else os.path.realpath(os.path.join(_BASE, 'bin', 'python3'))
SANDBOX_EXEC = '/usr/bin/sandbox-exec'
BWRAP = shutil.which('bwrap') or '/usr/bin/bwrap'
MOST_BYTES = 1_000_000

# LINUX: before the agent's code runs, a start-up written with the standard library alone installs a seccomp filter
# (x86_64): fork, vfork, execve, execveat and a clone that is not a thread are refused with EPERM ("Operation not
# permitted", the Mac's words); clone3 answers ENOSYS so a thread falls back to clone. Then the agent's entry runs.
_BOOT = r'''
import ctypes, platform, runpy, struct, sys
if platform.machine() != "x86_64":
    raise SystemExit("the Linux sandbox knows x86_64 only")
def f(code, jt, jf, k):
    return struct.pack("HBBI", code, jt, jf, k)
LD, JEQ, JSET, RET = 0x20, 0x15, 0x45, 0x06
ALLOW, KILL, EPERM, ENOSYS = 0x7fff0000, 0x80000000, 0x00050001, 0x00050026
prog = [f(LD, 0, 0, 4), f(JEQ, 1, 0, 0xc000003e), f(RET, 0, 0, KILL), f(LD, 0, 0, 0),
        f(JEQ, 6, 0, 57), f(JEQ, 5, 0, 58), f(JEQ, 4, 0, 59), f(JEQ, 3, 0, 322), f(JEQ, 4, 0, 435), f(JEQ, 5, 0, 56),
        f(RET, 0, 0, ALLOW), f(RET, 0, 0, EPERM),                                   # 10 allow; 11 deny
        f(RET, 0, 0, EPERM), f(RET, 0, 0, ENOSYS),                                  # 12 (unused) · 13 clone3
        f(RET, 0, 0, ALLOW),                                                         # 14 (unused)
        f(LD, 0, 0, 16), f(JSET, 1, 0, 0x10000), f(RET, 0, 0, EPERM), f(RET, 0, 0, ALLOW)]   # 15.. clone: a thread only
class Prog(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]
raw = ctypes.create_string_buffer(b"".join(prog))
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, ctypes.byref(Prog(len(prog), ctypes.addressof(raw))), 0, 0) != 0:
    raise SystemExit("the seccomp filter was not installed")
entry = sys.argv[1]
sys.argv = [entry]
runpy.run_path(entry, run_name="__main__")
'''


def _linux_runtime():
    """What the agent may read of the Python runtime: the binary, its standard library, its shared libraries."""
    import sysconfig
    stdlib = os.path.realpath(sysconfig.get_paths()['stdlib'])
    arch = sysconfig.get_config_var('MULTIARCH') or 'x86_64-linux-gnu'
    return [PYTHON, stdlib, f'/usr/lib/{arch}', '/usr/lib64']


def _linux_command(agent, run, entry):
    cmd = [BWRAP, '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
           '--setenv', 'PATH', '/usr/bin:/bin', '--setenv', 'HOME', run, '--setenv', 'TMPDIR', run, '--setenv', 'LC_CTYPE', 'C.UTF-8',
           '--dev', '/dev', '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64']
    for path in _linux_runtime():
        if os.path.exists(path):
            cmd += ['--ro-bind', path, path]
    cmd += ['--ro-bind', agent, agent, '--bind', run, run, '--chdir', run, PYTHON, '-I', '-B', '-c', _BOOT, os.path.join(agent, entry)]
    return cmd


def _profile(agent, run):
    return f'''(version 1)
(allow default)
(deny network*)
(deny process-fork)
(deny process-exec)
(allow process-exec (literal "{PYTHON}"))
(deny file-write*)
(allow file-write* (subpath "{run}") (literal "/dev/null"))
(deny file-read* (subpath "/Users"))
(allow file-read* (subpath "{agent}") (subpath "{run}"))
'''


def _kind(stderr, code):
    """The kind of failure, never the agent's words (they may carry what it was handed): the exception's name, and for a
    refusal by the system its fixed words ('[Errno 1] Operation not permitted'), never a path."""
    last = (stderr.strip().splitlines() or [''])[-1]
    m = re.match(r'^([A-Za-z_][\w.]*)(?::\s*(\[Errno \d+\] [^:\'"]+))?', last)
    if not m or not m.group(1).endswith(('Error', 'Exception', 'Exit', 'Interrupt')):
        return f'exit {code}'
    return m.group(1) + (f': {m.group(2).strip()}' if m.group(2) else '')


def run(folder, entry, given, seconds=20):
    """-> (state, answer, reason): ('DONE', {...}, '') or ('FAILED', None, why)."""
    agent = os.path.realpath(folder)
    run_dir = os.path.realpath(tempfile.mkdtemp(prefix='hanzo_run_'))
    try:
        try:
            if sys.platform == 'darwin' and os.path.isfile(SANDBOX_EXEC):
                command = [SANDBOX_EXEC, '-p', _profile(agent, run_dir), PYTHON, '-I', '-B', str(pathlib.Path(agent) / entry)]
            elif sys.platform.startswith('linux') and os.path.isfile(BWRAP):
                command = _linux_command(agent, run_dir, entry)
            else:
                return 'FAILED', None, 'no sandbox on this system: nothing runs unsandboxed'
            done = subprocess.run(command,
                                  input=json.dumps(given), capture_output=True, text=True, timeout=seconds, cwd=run_dir,
                                  env={'PATH': '/usr/bin:/bin', 'HOME': run_dir, 'TMPDIR': run_dir, 'LC_CTYPE': 'UTF-8'})
        except subprocess.TimeoutExpired:
            return 'FAILED', None, f'over the time limit ({seconds} s)'
        if done.returncode != 0:
            return 'FAILED', None, _kind(done.stderr, done.returncode)
        if len(done.stdout) > MOST_BYTES:
            return 'FAILED', None, 'the answer is too long'
        try:
            answer = json.loads(done.stdout)
        except ValueError:
            answer = None
        if not isinstance(answer, dict):
            return 'FAILED', None, 'the answer is not one JSON object'
        return 'DONE', answer, ''
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
