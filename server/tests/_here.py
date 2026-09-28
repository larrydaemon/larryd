"""The tests' one link to HANZO's code: its own app folder, found from this file (never a path outside ~/pfhanzo)."""
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parent.parent / 'hanzo' / 'app'
sys.path.insert(0, str(APP))
