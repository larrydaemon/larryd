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
import signal
import subprocess
import sys
import tempfile
import time

_BASE = os.path.realpath(sys.base_prefix)
_FRAMEWORK = os.path.join(_BASE, 'Resources', 'Python.app', 'Contents', 'MacOS', 'Python')   # a framework python3 only spawns this
PYTHON = _FRAMEWORK if os.path.isfile(_FRAMEWORK) else os.path.realpath(os.path.join(_BASE, 'bin', 'python3'))
SANDBOX_EXEC = '/usr/bin/sandbox-exec'
BWRAP = shutil.which('bwrap') or '/usr/bin/bwrap'
MOST_BYTES = 1_000_000
MOST_MEMORY = 512 * 1024 * 1024   # a run's address space (the runtime's own limit, beside Cloud Run's)
MOST_CPU_SECONDS = 30             # a run's CPU time; the wall clock is `seconds` in run()
MOST_FILE_BYTES = MOST_BYTES + 1  # any file a run writes, its answer included, is cut at this size
ROOT = None   # THE RUN FOLDERS' HOME: the instance's own out/ (app.py sets it), never the temp folder every runtime on this computer shares and sweeps; None: the temp folder
GONE = 'its answer file was removed before it was read (another cleanup took the run folder)'


def home():
    """where this instance makes and sweeps its run folders"""
    if ROOT:
        os.makedirs(ROOT, exist_ok=True)
        return ROOT
    return tempfile.gettempdir()


def limits(most_file=MOST_FILE_BYTES):
    """Applied in the child before the sandbox starts (Linux): memory, CPU and file size, enforced by the kernel."""
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (MOST_MEMORY, MOST_MEMORY))
    resource.setrlimit(resource.RLIMIT_CPU, (MOST_CPU_SECONDS, MOST_CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (most_file, most_file))

# LINUX: before the agent's code runs, a start-up written with the standard library alone installs a seccomp filter
# (x86_64): fork, vfork, execve, execveat and a clone that is not a thread are refused with EPERM ("Operation not
# permitted", the Mac's words); clone3 answers ENOSYS so a thread falls back to clone. Then the agent's entry runs.
_BOOT = r'''
import ctypes, os, platform, runpy, struct, sys
os.environ.pop("PWD", None)   # bwrap's --chdir sets it; the environment is only what the runtime gives
os.environ.pop("LD_LIBRARY_PATH", None)   # the loader's alone (a shared libpython's folder, _linux_command): read before this line, never the agent's
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
    """What the agent may read of the Python runtime: the binary, its standard library, its shared libraries. On a
    glibc system those sit under /usr/lib/<arch>; on Alpine (musl, the runtime's image) the loader and the system's
    libraries are /lib and /usr/lib, and Python's own (libpython, its compiled standard library) /usr/local/lib."""
    import sysconfig
    stdlib = os.path.realpath(sysconfig.get_paths()['stdlib'])
    arch = sysconfig.get_config_var('MULTIARCH') or 'x86_64-linux-gnu'
    libdir = os.path.realpath(sysconfig.get_config_var('LIBDIR') or '/usr/local/lib')
    return [PYTHON, stdlib, libdir, f'/usr/lib/{arch}', '/usr/lib64']


_SYSTEM_LIBS = ('/lib', '/lib64', '/usr/lib')


def _linux_libs():
    """bwrap's arguments for the system's library folders: a folder that is a link on the host is the same link inside;
    a real folder (Alpine's /lib, where musl's loader lives) is bound read-only."""
    out = []
    for path in _SYSTEM_LIBS:
        if os.path.islink(path):
            out += ['--symlink', os.readlink(path), path]
        elif os.path.isdir(path):
            out += ['--ro-bind', path, path]
    return out


def _shared_libdir():
    """The folder of a shared libpython the loader would not find by itself (glibc's defaults are /lib and /usr/lib; inside the
    sandbox there is no /etc/ld.so.cache to name any other), else ''."""
    import sysconfig
    if not sysconfig.get_config_var('Py_ENABLE_SHARED'):
        return ''
    libdir = os.path.realpath(sysconfig.get_config_var('LIBDIR') or '')
    return '' if not libdir or libdir in ('/lib', '/lib64', '/usr/lib', '/usr/lib64') else libdir


def _linux_command(agent, run, entry):
    cmd = [BWRAP, '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
           '--setenv', 'PATH', '/usr/bin:/bin', '--setenv', 'HOME', run, '--setenv', 'TMPDIR', run, '--setenv', 'LC_CTYPE', 'C.UTF-8',
           '--dev', '/dev'] + _linux_libs()
    if _shared_libdir():   # a Python built with a shared libpython outside the loader's own folders (/usr/local/lib: python.org's
        cmd += ['--setenv', 'LD_LIBRARY_PATH', _shared_libdir()]   # builds, the official images) finds it with no /etc/ld.so.cache inside
    for path in _linux_runtime():
        if os.path.exists(path) and not any(path == lib or path.startswith(lib + '/') for lib in _SYSTEM_LIBS if os.path.isdir(lib) and not os.path.islink(lib)):
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


def _kill_group(pid):
    """The run's whole process group (its own session: the sandbox and anything under it), killed and waited for."""
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def run(folder, entry, given, seconds=20, on_start=None, most_bytes=MOST_BYTES, internal=False):
    """-> (state, answer, reason): ('DONE', {...}, '') or ('FAILED', None, why). The run is its own process group
    (start_new_session); on_start(pid) is told it before the run is fed, so the slot can kill the whole group if it
    ever has to; on the time limit the whole group is killed and waited for. most_bytes: the answer's limit (the
    runtime's own 1 MB)."""
    agent = os.path.realpath(folder)
    run_dir = os.path.realpath(tempfile.mkdtemp(prefix='runtime_run_', dir=home()))   # private (0o700), this run's only place
    out_dir = os.path.realpath(tempfile.mkdtemp(prefix='runtime_out_', dir=home()))   # its answer, outside the folder the agent can write
    try:
        try:
            if internal:   # LARRYD RUNTIME INTERNAL (the owner 2026-11-03: "its internal so i dont think it matters and seems normal"): an internal agent runs as this computer's own process, in its own folder, with this computer's reach; never on the external runtime (harness._run decides)
                command = [sys.executable, '-B', str(pathlib.Path(agent) / entry)]
            elif sys.platform == 'darwin' and os.path.isfile(SANDBOX_EXEC):
                command = [SANDBOX_EXEC, '-p', _profile(agent, run_dir), PYTHON, '-I', '-B', str(pathlib.Path(agent) / entry)]
            elif sys.platform.startswith('linux') and os.path.isfile(BWRAP):
                command = _linux_command(agent, run_dir, entry)
            else:
                return 'FAILED', None, 'no sandbox on this system: nothing runs unsandboxed'
            linux = sys.platform.startswith('linux')
            out_path, err_path = os.path.join(out_dir, 'out'), os.path.join(out_dir, 'err')
            with open(out_path, 'w') as out, open(err_path, 'w') as err:
                child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True, cwd=agent if internal else run_dir,
                                         preexec_fn=(lambda: limits(most_bytes + 1)) if linux and not internal else None, start_new_session=True,
                                         env=dict(os.environ) if internal else {'PATH': '/usr/bin:/bin', 'HOME': run_dir, 'TMPDIR': run_dir, 'LC_CTYPE': 'UTF-8'})
                try:
                    if on_start:
                        on_start(child.pid)
                    child.communicate(json.dumps(given), timeout=seconds)
                except subprocess.TimeoutExpired:
                    _kill_group(child.pid)
                    child.wait()
                    return 'FAILED', None, f'over the time limit ({seconds} s)'
                except BaseException:
                    _kill_group(child.pid)
                    child.wait()
                    raise
                finally:
                    if on_start:
                        on_start(None)   # the run's process is gone: the slot holds no process any more
            try:
                with open(out_path) as f:
                    stdout = f.read(most_bytes + 2)
                with open(err_path) as f:
                    stderr = f.read(MOST_BYTES)
            except FileNotFoundError:   # never a thread that dies with no result, leaving the platform to close the RUN at 20 minutes
                return 'FAILED', None, GONE
        except subprocess.TimeoutExpired:
            return 'FAILED', None, f'over the time limit ({seconds} s)'
        if len(stdout) > most_bytes:
            return 'FAILED', None, 'the answer is too long'
        if child.returncode != 0:
            return 'FAILED', None, _kind(stderr, child.returncode)
        try:
            answer = json.loads(stdout)
        except ValueError:
            answer = None
        if not isinstance(answer, dict):
            return 'FAILED', None, 'the answer is not one JSON object'
        return 'DONE', answer, ''
    finally:   # every exit: done, failed, timed out, killed
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)


def sweep(older_than=120):
    """At an instance's start: any run's folders left by a run cut off before its own finally. A folder younger than
    older_than seconds is a run in flight (another instance's, or a thread's, on the same computer) and is left alone."""
    now = time.time()
    for p in pathlib.Path(home()).glob('runtime_[ro][ua][nt]_*'):
        try:
            if now - p.stat().st_mtime < older_than:
                continue
        except OSError:
            continue
        shutil.rmtree(p, ignore_errors=True)
