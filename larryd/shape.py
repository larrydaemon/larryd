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
    'records': 'the member\'s records the agent reads and writes on a CALL (optional): {"<species>": ["read", "add", "edit", "remove"]}, '
               'e.g. {"opns": ["read", "add", "edit", "remove"]}; LARRYD hands them as records = {species: [rows]} and carries the '
               'answer\'s "writes" to the platform\'s own record doors, only what is declared',
}
FIELDS['live'] = ('the agent\'s own live page (optional, only on an agent that answers calls): {"seats": 1 to 4}; its files sit in live/ beside '
                  'agent/ (page.html, page.js, room.py, live.json) and LARRYD hands the call live = {"link": the page with the member\'s pass}')
FIELDS['card'] = ('the card the marketplace shows, as the member sees it: {class, pitch, price, type, residency, screen, product, '
                  'module, developer, sends_to, data_sent} and, if you like, developer_site; the number and the art are LARRYD\'s to give at approval')
CARD = {
    'class': 'one of the platform\'s agent classes: MARK I AGENT (NORMAL), MARK II SUPER AGENT (HARNESS) or MARK III QUANTUM AI '
             '(AGENTIC CODE), as a guide: simple, complex, extremely complex; the class picks the card\'s effect (Mark I crt, '
             'Mark II wellness, Mark III glitch)',
    'pitch': 'one line on the card: what the member gets',
    'price': 'whole mTok per run, a whole number: 3 or "3" ("0" is free; no fractions)',
    'type': 'OFF-THE-SHELF or DEVELOPER',
    'residency': 'which marketplaces it is offered on: INTERNAL (Positive Feedback only), EXTERNAL (other marketplaces only, '
                 'e.g. the Microsoft marketplace) or BOTH (Positive Feedback and at least one other); every LARRYD agent runs in LARRYD',
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
CARD_OPTIONAL = {   # a card fact an agent may leave out
    'availability': '"offline" for an agent shown for information only: its card is dimmed and locked and it cannot be hired (leave the field out for an agent that can be hired)',
    'developer_site': 'your website, a plain https address such as https://example.com: the card links your name to it (leave the field out for no link)',
}
SITE = r'https://(?=[^/?#]{1,253}(?:[/?#]|$))(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}(?:[/?#][^\s"\'<>\\`]*)?'   # https to a named host: no user, no port, no number for a host
SCREEN = r'[a-z][a-z0-9]{1,15}/[a-z][a-z0-9]{1,15}'   # <species>/<page>
MOST_PITCH = 140                                      # characters on the card
OPTIONAL = ('inputs', 'look', 'records', 'live')
LIVE = 'live'   # the live half's folder, beside agent/
LIVE_FILES = ('live.json', 'page.html', 'page.js', 'room.py')   # all of it, and nothing else
LIVE_MAY = ('rain.js',)   # and, if the page needs it, a second script. The page's own rules are written IN the page (one <style> block), as every agent's are
LIVE_SEATS = (1, 4)
RECORD_VERBS = ('read', 'add', 'edit', 'remove')   # what an agent may declare on a species' records
PACK = 'pack.json'   # a knowledge pack: a folder of plain text files with pack.json {"name", "about"}
PACK_FIELDS = ('name', 'about')
PACK_KINDS = {'.json', '.txt', '.md', '.csv'}
NEEDED = tuple(k for k in FIELDS if k not in OPTIONAL)

# what the LARRYD runtime hands a RUN today: the cards the member sees; the job's own inputs (by the names in "inputs")
HANDS = ('cards', 'job')
SLOT = r'0(0[1-9]|1[0-5])'   # the job's input slots, 001-015
MOST_INPUT = 10_000          # characters in one input (the LARRYD runtime refuses more)
