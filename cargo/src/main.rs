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

/// Ok(a Python 3.11 or newer), or Err(Some("3.9.6")) when only an older one was found, or Err(None) when none was.
fn python() -> Result<String, Option<String>> {
    let candidates: Vec<String> = match env::var("LARRYD_PYTHON") {
        Ok(p) => vec![p],
        Err(_) => vec!["python3".into(), "python".into()],
    };
    let mut old = None;
    for p in candidates {
        let out = Command::new(&p)
            .args(["-c", "import sys; print(sys.version_info >= (3, 11), sys.version.split()[0])"])
            .stderr(Stdio::null())
            .output();
        if let Ok(out) = out {
            let said = String::from_utf8_lossy(&out.stdout).trim().to_string();
            let mut parts = said.split(' ');
            match (out.status.success(), parts.next(), parts.next()) {
                (true, Some("True"), _) => return Ok(p),
                (true, Some("False"), Some(v)) if old.is_none() => old = Some(v.to_string()),
                _ => {}
            }
        }
    }
    Err(old)
}

/// What to say when pip could not install LARRYD, from pip's own words.
fn pip_said(stderr: &str, spec: &str) -> String {
    let any = |words: &[&str]| words.iter().any(|w| stderr.contains(w));
    if any(&["No matching distribution found", "from versions: none", "Could not find a version that satisfies"]) {
        return format!("LARRYD {VERSION} is not on PyPI yet, so this launcher cannot install it; set LARRYD_PIP_SPEC to a LARRYD {VERSION} wheel, or use pipx or uv once it is published");
    }
    if any(&["Could not fetch URL", "NewConnectionError", "Temporary failure in name resolution", "Network is unreachable", "timed out"]) {
        return format!("could not reach PyPI to install {spec}; check the network, then run larryd again");
    }
    format!("pip could not install {spec} (its words are above); fix what it says, then run larryd again")
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
        let py = match python() {
            Ok(py) => py,
            Err(Some(old)) => {
                say(&format!("LARRYD needs Python 3.11 or newer, and python3 here is {old}; install a newer Python (brew install python, or python.org), or set LARRYD_PYTHON to one, then run larryd again"));
                exit(1);
            }
            Err(None) => {
                say("LARRYD needs Python 3.11 or newer, and python3 was not found; install Python, then run larryd again");
                exit(1);
            }
        };
        say(&format!("installing LARRYD {VERSION} (once) into {}", venv.display()));
        if let Some(parent) = venv.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        let spec = env::var("LARRYD_PIP_SPEC").unwrap_or_else(|_| format!("larryd=={VERSION}"));
        let made = Command::new(&py).args(["-m", "venv"]).arg(&venv).stdout(Stdio::null()).status();
        if !made.map(|s| s.success()).unwrap_or(false) {
            say(&format!("{py} could not make a venv at {}; check that folder, then run larryd again", venv.display()));
            exit(1);
        }
        let pip = Command::new(&venv_python).args(["-m", "pip", "install", "-q", &spec]).stdin(Stdio::null()).stdout(Stdio::null()).output();
        let (ok, stderr) = match pip {
            Ok(out) => (out.status.success(), String::from_utf8_lossy(&out.stderr).to_string()),
            Err(e) => (false, e.to_string()),
        };
        if !ok || !installed(&venv_python) {
            eprint!("{stderr}");
            say(&pip_said(&stderr, &spec));
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pips_words_become_the_right_sentence() {
        let missing = "ERROR: Could not find a version that satisfies the requirement larryd==0.1.0 (from versions: 0.0.1)\nERROR: No matching distribution found for larryd==0.1.0";
        assert!(pip_said(missing, "larryd==0.1.0").starts_with("LARRYD 0.1.0 is not on PyPI yet"));
        assert!(pip_said("NewConnectionError('Failed to establish a new connection')", "larryd==0.1.0").starts_with("could not reach PyPI"));
        assert!(pip_said("ERROR: something else", "larryd==0.1.0").starts_with("pip could not install larryd==0.1.0 (its words are above)"));
    }
}
