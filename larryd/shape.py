"""THE SHAPE OF AN AGENT: one place, read by `new` (which makes it) and `doctor` (which checks it).
An agent project is a folder:
    CLAUDE.md                      the spec and the rules, for the developer's AI
    .claude/skills/larryd/SKILL.md the skill Claude Code loads
    samples/job.json               a sample job for `larryd run`
    agent/                         THE AGENT: exactly what the LARRYD runtime holds in its locker
        agent.json                 the manifest
        agent.py                   the code, one entry
The LARRYD runtime runs the agent as its own process with no network, one JSON object in on stdin, one JSON object out on stdout."""

AGENT = 'agent'
MANIFEST = 'agent.json'
SAMPLE = 'samples/job.json'
SKILL = '.claude/skills/larryd/SKILL.md'

# the manifest: every field, what it holds (the words the doctor uses when one is wrong)
FIELDS = {
    'name': 'the agent\'s name, as its card shows it',
    'entry': 'the file LARRYD runs, inside agent/ (agent.py)',
    'about': 'one plain sentence: what the agent answers',
    'does': 'the list of what the agent does; each one is a function of that name in the entry',
    'calls': 'what it answers at once on the member\'s screen (the CALL lane); a list, most agents leave it empty',
    'reads': 'the list of what the agent reads, in plain words',
    'run': 'what a RUN hands it: {"do": one of does, "hands": the inputs, from what LARRYD hands}',
    'gives': 'the list of what its answer holds (its outputs); "delivery" is what lands in the member\'s job',
    'skills': 'the list of skill hashes the agent uses (empty when none; `larryd skills` lists the skills that exist)',
    'knowledge': 'the list of knowledge pack hashes the agent needs (empty when none; `larryd pack` gives a pack its hash)',
    'inputs': 'only with "job" in run.hands: the job\'s inputs by name, each on one of the job\'s slots 001-015, e.g. {"mood": "001"}',
}
FIELDS['card'] = ('the card the marketplace shows, as the member sees it: {class, pitch, price, type, residency, screen, product, '
                  'module, developer, sends_to, data_sent}; the number and the art are LARRYD\'s to give at approval')
CARD = {
    'class': 'the class on the card, e.g. "MARK I AGENT (NORMAL)"',
    'pitch': 'one line on the card: what the member gets',
    'price': 'whole mTok per run, as text: "0" is free',
    'type': 'e.g. OFF-THE-SHELF or CUSTOM',
    'residency': 'INTERNAL (it runs on LARRYD) or EXTERNAL',
    'screen': 'the screen it lives on, <species>/<page>, e.g. cont/card (contact cards) or agnt/home (the agents page)',
    'product': 'the product that screen belongs to, e.g. Invoice Maps, Agency Mgmt, Pace Shift, LARRYD',
    'module': 'the module that screen is in, e.g. CONTACTS',
    'developer': 'who made it, as the card credits it: your name or company',
    'sends_to': 'the outside AI service it sends a member\'s data to, by name; "" when it sends nothing out',
    'data_sent': 'what it sends there, in plain words; "" when nothing',
}
SCREEN = r'[a-z][a-z0-9]{1,15}/[a-z][a-z0-9]{1,15}'   # <species>/<page>
MOST_PITCH = 140                                      # characters on the card
OPTIONAL = ('inputs',)
PACK = 'pack.json'   # a knowledge pack: a folder of plain text files with pack.json {"name", "about"}
PACK_FIELDS = ('name', 'about')
PACK_KINDS = {'.json', '.txt', '.md', '.csv'}
NEEDED = tuple(k for k in FIELDS if k not in OPTIONAL)

# what the LARRYD runtime hands a RUN today: the cards the member sees; the job's own inputs (by the names in "inputs")
HANDS = ('cards', 'job')
SLOT = r'0(0[1-9]|1[0-5])'   # the job's input slots, 001-015
MOST_INPUT = 10_000          # characters in one input (the LARRYD runtime refuses more)
