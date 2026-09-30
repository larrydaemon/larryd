"""`python -m larryd`: the same as the `larryd` command (the npm and cargo launchers call it this way)."""
import sys

from .cli import main

sys.exit(main())
