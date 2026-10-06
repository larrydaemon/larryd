"""The tests' one link to the runtime's code: its own app folder, found from this file (never a path outside server/)."""
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parent.parent / 'runtime' / 'app'
sys.path.insert(0, str(APP))
