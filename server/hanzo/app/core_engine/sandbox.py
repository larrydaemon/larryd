"""THE SANDBOX: every agent runs as its own process with nothing but what it is handed, by the system the runtime runs on:
macOS sandbox-exec, or on Linux bubblewrap (bwrap) with a seccomp filter; on any other system nothing runs.
- no network at all (the harness makes every call; an agent never does);
- no new process (no fork, no other program);
- writes only in its own run folder (made for the run, removed after), never into the locker;
- reads nothing but its own folder, its run folder and what the Python runtime needs to start (the binary, its standard
  library, the libraries those link, the system's own libraries): on macOS every other read is refused (a file's name
  and size may be looked up, never its contents: /etc/hosts, another project, the home folders); on Linux nothing
  else is mounted;
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
import ctypes, os, platform, runpy, struct, sys
os.environ.pop("PWD", None)   # bwrap's --chdir sets it; the environment is only what the runtime gives
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
    cmd += ['--ro-bind', agent, agent, '--bind', run, run,
            '--remount-ro', '/',   # bwrap's own root (a tmpfs holding the mount points) read-only: the run folder is the one place to write
            '--chdir', run, PYTHON, '-I', '-B', '-c', _BOOT, os.path.join(agent, entry)]
    return cmd


# MACOS: what the runtime reads besides the agent's folders. The system's own libraries and devices, the time zones, and
# the root folder itself (the Python binary reads "/" as it starts; its list of names, nothing under it).
_MAC_SYSTEM = ('/usr/lib', '/System', '/dev', '/usr/share/zoneinfo', '/private/var/db/timezone')
_MAC_LITERAL = ('/', '/private/etc/localtime')
_LINKED = re.compile(rb'(/[\x21-\x7e]+?\.dylib)\x00')


def _mac_runtime():
    """The folders of the Python runtime: its own (sys.base_prefix) and every library folder its binary and compiled
    standard library name in their load commands (e.g. Homebrew's openssl, mpdecimal, sqlite), outside the system's own,
    each as named and as it really is (a link resolved)."""
    folders = {_BASE}
    binaries = [PYTHON] + [str(p) for p in pathlib.Path(_BASE).rglob('lib-dynload/*.so')]
    for path in binaries:
        try:
            data = pathlib.Path(path).read_bytes()
        except OSError:
            continue
        for linked in _LINKED.findall(data):
            name = os.path.dirname(linked.decode())
            if not name.startswith(('/usr/lib', '/System', _BASE)):
                folders.update({name, os.path.realpath(name)})
    return sorted(folders)


def _profile(agent, run):
    reads = ' '.join(f'(subpath "{p}")' for p in [agent, run, *_mac_runtime(), *_MAC_SYSTEM]) + ' ' + ' '.join(f'(literal "{p}")' for p in _MAC_LITERAL)
    return f'''(version 1)
(allow default)
(deny network*)
(deny process-fork)
(deny process-exec)
(allow process-exec (literal "{PYTHON}"))
(deny file-write*)
(allow file-write* (subpath "{run}") (literal "/dev/null"))
(deny file-read*)
(allow file-read-metadata)
(allow file-read* {reads})
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
