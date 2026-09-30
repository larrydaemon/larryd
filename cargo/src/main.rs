//! LARRYD from cargo: a thin launcher. LARRYD itself is a Python package; this finds Python 3.11 or newer, keeps LARRYD in
//! its own place (~/.larryd/venv, or /var/lib/larryd/venv as root; LARRYD_VENV names another), installs the same version
//! as this crate there once, and hands every argument to it. `larryd` alone starts the daemon.
use std::env;
use std::path::{Path, PathBuf};
use std::process::{exit, Command, Stdio};

const VERSION: &str = env!("CARGO_PKG_VERSION");

fn say(line: &str) {
    eprintln!("larryd: {line}");
}

fn python() -> Option<String> {
    let candidates: Vec<String> = match env::var("LARRYD_PYTHON") {
        Ok(p) => vec![p],
        Err(_) => vec!["python3".into(), "python".into()],
    };
    for p in candidates {
        let out = Command::new(&p).args(["-c", "import sys; print(sys.version_info >= (3, 11))"]).stderr(Stdio::null()).output();
        if let Ok(out) = out {
            if out.status.success() && String::from_utf8_lossy(&out.stdout).trim() == "True" {
                return Some(p);
            }
        }
    }
    None
}

fn is_root() -> bool {
    Command::new("id").arg("-u").output().map(|o| String::from_utf8_lossy(&o.stdout).trim() == "0").unwrap_or(false)
}

fn venv_dir() -> PathBuf {
    if let Ok(v) = env::var("LARRYD_VENV") {
        return PathBuf::from(v);
    }
    if is_root() {
        return PathBuf::from("/var/lib/larryd/venv");
    }
    PathBuf::from(env::var("HOME").unwrap_or_else(|_| ".".into())).join(".larryd").join("venv")
}

fn installed(venv_python: &Path) -> bool {
    if !venv_python.exists() {
        return false;
    }
    Command::new(venv_python)
        .args(["-c", "import larryd; print(larryd.__version__)"])
        .stderr(Stdio::null())
        .output()
        .map(|o| o.status.success() && String::from_utf8_lossy(&o.stdout).trim() == VERSION)
        .unwrap_or(false)
}

fn main() {
    let venv = venv_dir();
    let venv_python = venv.join("bin").join("python");
    if !installed(&venv_python) {
        let Some(py) = python() else {
            say("LARRYD needs Python 3.11 or newer, and python3 was not found; install Python, then run larryd again");
            exit(1);
        };
        say(&format!("installing LARRYD {VERSION} (once) into {}", venv.display()));
        if let Some(parent) = venv.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        let spec = env::var("LARRYD_PIP_SPEC").unwrap_or_else(|_| format!("larryd=={VERSION}"));
        let made = Command::new(&py).args(["-m", "venv"]).arg(&venv).stdout(Stdio::null()).status();
        let ok = made.map(|s| s.success()).unwrap_or(false)
            && Command::new(&venv_python).args(["-m", "pip", "install", "-q", &spec]).stdout(Stdio::null()).status().map(|s| s.success()).unwrap_or(false);
        if !ok || !installed(&venv_python) {
            say(&format!("could not install LARRYD {VERSION} into {}; check the network and Python, then run larryd again", venv.display()));
            exit(1);
        }
    }
    let mut command = Command::new(&venv_python);
    command.args(["-m", "larryd"]).args(env::args_os().skip(1));
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        let error = command.exec(); // this process becomes LARRYD: the pid it prints is the one `kill` stops
        say(&format!("could not start LARRYD: {error}"));
        exit(1);
    }
    #[cfg(not(unix))]
    {
        let status = command.status().unwrap_or_else(|e| {
            say(&format!("could not start LARRYD: {e}"));
            exit(1)
        });
        exit(status.code().unwrap_or(1));
    }
}
