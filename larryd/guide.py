"""`larryd guide`: the whole guide, as it ships in the package (larryd/GUIDE.md, the repository's GUIDE.md word for word)."""
from importlib import resources


def path():
    return str(resources.files('larryd').joinpath('GUIDE.md'))


def text():
    return resources.files('larryd').joinpath('GUIDE.md').read_text()
