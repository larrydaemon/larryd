"""THE SKILLS a developer's agent may declare in its manifest, each by its hash. A skill is a definition (its name, its
technology, the PF HANZO door it goes through, what it does, what the agent does with it); its hash is the sha256 of
that definition, so a changed skill is a new skill. Only doors PF HANZO really has are skills (larryd/skills.json)."""
import json
from importlib import resources

from . import hashes


def known():
    """-> {hash: skill}: every skill that exists."""
    listed = json.loads(resources.files('larryd').joinpath('skills.json').read_text())['skills']
    return {hashes.definition(s): s for s in listed}
