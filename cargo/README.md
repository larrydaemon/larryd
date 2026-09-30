# LARRYD

Your server has a daemon. Your agents should have one too.

Build, test and ship AI agents with Claude Code.

    cargo install larryd
    larryd help

This package is a thin launcher: LARRYD itself is a Python package. The first run finds Python 3.11 or newer, installs
the same version of LARRYD into its own place (~/.larryd/venv, or /var/lib/larryd/venv as root), and from then on hands
every argument to it. `larryd` alone starts the daemon: LARRYD's runtime on this machine, on 127.0.0.1.

More: https://github.com/larrydaemon/larryd
