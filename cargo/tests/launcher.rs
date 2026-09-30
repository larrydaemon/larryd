//! The cargo launcher, run for real: no Python is said in one line; the first run installs LARRYD (from this repository)
//! into a private venv and hands every argument to it, exit codes included; the second run installs nothing.
use std::path::PathBuf;
use std::process::Command;

fn launcher() -> Command {
    Command::new(env!("CARGO_BIN_EXE_larryd"))
}

fn scratch(name: &str) -> PathBuf {
    let dir = std::env::temp_dir().join(format!("larryd-cargo-{name}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    dir
}

#[test]
fn no_python_one_plain_line() {
    let out = launcher().arg("help").env("LARRYD_PYTHON", "/nonexistent/python3").env("LARRYD_VENV", scratch("none")).output().unwrap();
    assert_eq!(out.status.code(), Some(1));
    assert_eq!(
        String::from_utf8_lossy(&out.stderr),
        "larryd: LARRYD needs Python 3.11 or newer, and python3 was not found; install Python, then run larryd again\n"
    );
}

#[test]
fn an_older_python_says_which_one_it_found() {
    let dir = scratch("old");
    std::fs::create_dir_all(&dir).unwrap();
    let fake = dir.join("python3");
    std::fs::write(&fake, "#!/bin/sh\necho \"False 3.9.6\"\n").unwrap();
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&fake, std::fs::Permissions::from_mode(0o755)).unwrap();
    }
    let out = launcher().arg("help").env("LARRYD_PYTHON", &fake).env("LARRYD_VENV", dir.join("venv")).output().unwrap();
    let _ = std::fs::remove_dir_all(&dir);
    assert_eq!(out.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&out.stderr).contains("LARRYD needs Python 3.11 or newer, and python3 here is 3.9.6; install a newer Python"));
}

#[test]
fn installs_once_then_hands_every_argument_through() {
    let venv = scratch("venv");
    let repo = PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf();
    let first = launcher().arg("help").env("LARRYD_VENV", &venv).env("LARRYD_PIP_SPEC", &repo).output().unwrap();
    assert!(first.status.success(), "{}", String::from_utf8_lossy(&first.stderr));
    assert!(String::from_utf8_lossy(&first.stderr).contains("larryd: installing LARRYD 0.1.0 (once) into "));
    assert!(String::from_utf8_lossy(&first.stdout).contains("usage: larryd"));
    let second = launcher().args(["doctor", venv.join("no-agent-here").to_str().unwrap(), "--json"]).env("LARRYD_VENV", &venv).output().unwrap();
    assert_eq!(second.status.code(), Some(1)); // the doctor's own exit code, handed back
    assert_eq!(String::from_utf8_lossy(&second.stderr), ""); // nothing installed again
    assert!(String::from_utf8_lossy(&second.stdout).contains("\"ok\": false"));
    let _ = std::fs::remove_dir_all(&venv);
}
