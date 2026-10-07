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
    'look': 'the card\'s look, names only (optional): {"accent": a theme colour variable, "radius": a step, "space": a step, '
            '"effect": none, crt, wellness or glitch, "text": {"<part>": "<role>"}}; the menu: `larryd guide`, section 4',
    'inputs': 'only with "job" in run.hands: the job\'s inputs by name, each on one of the job\'s slots 001-015, e.g. {"mood": "001"}',
}
FIELDS['card'] = ('the card the marketplace shows, as the member sees it: {class, pitch, price, type, residency, screen, product, '
                  'module, developer, sends_to, data_sent}; the number and the art are LARRYD\'s to give at approval')
CARD = {
    'class': 'one of the platform\'s agent classes: MARK I AGENT (NORMAL), MARK II SUPER AGENT (HARNESS) or MARK III QUANTUM AI '
             '(AGENTIC CODE); the class picks the card\'s effect (Mark I crt, Mark II wellness, Mark III glitch)',
    'pitch': 'one line on the card: what the member gets',
    'price': 'whole mTok per run, a whole number: 3 or "3" ("0" is free; no fractions)',
    'type': 'OFF-THE-SHELF or DEVELOPER',
    'residency': 'INTERNAL (it runs on LARRYD), EXTERNAL or BOTH; who may hire it (every account, or one private account) is '
                 'set when it is authorized, never here',
    'authorization': 'who may hire it, your starting setting: PUBLIC (every account) or PRIVATE (one account); the platform\'s '
                     'authorize panel can change it at any time after, and a PRIVATE agent\'s owning account is entered there',
    'screen': 'the screen it lives on, <species>/<page> (its address is app/<species>/<page>): a module\'s home, list or card, '
              'e.g. cont/card, or a product\'s dashboard larry/home; the card\'s values table: `larryd guide`',
    'product': 'the product that screen belongs to: INVOICE MAPS, AGENCY MGMT, PACE SHIFT or LARRYD',
    'module': 'the module that screen is in, by the platform\'s own name, e.g. Contacts (cont/...) or Agents (agnt/...)',
    'developer': 'who made it, as the card credits it: your name or company',
    'sends_to': 'the outside AI service it sends a member\'s data to, by name; "" when it sends nothing out',
    'data_sent': 'what it sends there, in plain words; "" when nothing',
}
SCREEN = r'[a-z][a-z0-9]{1,15}/[a-z][a-z0-9]{1,15}'   # <species>/<page>
MOST_PITCH = 140                                      # characters on the card
OPTIONAL = ('inputs', 'look')
PACK = 'pack.json'   # a knowledge pack: a folder of plain text files with pack.json {"name", "about"}
PACK_FIELDS = ('name', 'about')
PACK_KINDS = {'.json', '.txt', '.md', '.csv'}
NEEDED = tuple(k for k in FIELDS if k not in OPTIONAL)

# what the LARRYD runtime hands a RUN today: the cards the member sees; the job's own inputs (by the names in "inputs")
HANDS = ('cards', 'job')
SLOT = r'0(0[1-9]|1[0-5])'   # the job's input slots, 001-015
MOST_INPUT = 10_000          # characters in one input (the LARRYD runtime refuses more)
