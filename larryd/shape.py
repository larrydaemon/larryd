"""THE SHAPE OF AN AGENT: one place, read by `new` (which makes it) and `doctor` (which checks it).
An agent project is a folder:
    CLAUDE.md                      the spec and the rules, for the developer's AI
    .claude/skills/larryd/SKILL.md the skill Claude Code loads
    samples/job.json               a sample job for `larryd run`
    agent/                         THE AGENT: exactly what PF HANZO holds in its locker
        agent.json                 the manifest
        agent.py                   the code, one entry
PF HANZO runs the agent as its own process with no network, one JSON object in on stdin, one JSON object out on stdout."""

AGENT = 'agent'
MANIFEST = 'agent.json'
SAMPLE = 'samples/job.json'
SKILL = '.claude/skills/larryd/SKILL.md'

# the manifest: every field, what it holds (the words the doctor uses when one is wrong)
FIELDS = {
    'name': 'the agent\'s name, as its card shows it',
    'entry': 'the file PF HANZO runs, inside agent/ (agent.py)',
    'about': 'one plain sentence: what the agent answers',
    'does': 'the list of what the agent does; each one is a function of that name in the entry',
    'calls': 'what it answers at once on the member\'s screen (the CALL lane); a list, most agents leave it empty',
    'reads': 'the list of what the agent reads, in plain words',
    'run': 'what a RUN hands it: {"do": one of does, "hands": the inputs, from what PF HANZO hands}',
    'gives': 'the list of what its answer holds (its outputs); "delivery" is what lands in the member\'s job',
    'skills': 'the list of skill hashes the agent uses (empty when none)',
}
NEEDED = tuple(FIELDS)

# what PF HANZO hands a RUN today (its harness hands the cards only). Nothing else exists yet.
HANDS = ('cards',)
