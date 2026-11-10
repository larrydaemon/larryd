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
    'files': 'only with "files" (and "job") in run.hands: which of the "inputs" carry a DA-M key the member picks; on a RUN each is handed as files = {name: {dam_key, kind, bytes, content_b64}}, at most 3, each up to 20 MB, e.g. ["picture"]',
    'records': 'the member\'s records the agent reads and writes on a CALL, and reads on a RUN whose run.hands names "records" (optional): {"<species>": ["read", "add", "edit", "remove"]}, '
               'e.g. {"opns": ["read", "add", "edit", "remove"]}; LARRYD hands them as records = {species: [rows]} and carries the '
               'answer\'s "writes" to the platform\'s own record doors, only what is declared. THE COUNTS: {"*": ["count"]} (alone or beside '
               'species) hands counts = {scope, modules: {species: how many}, products, ties: [[from, to, how many]]} on a CALL and on a RUN: '
               'the numbers of the member\'s own account, never a record',
}
FIELDS['live'] = ('the agent\'s own live page (optional, only on an agent that answers calls): {"seats": 1 to 4}; its files sit in live/ beside '
                  'agent/ (page.html, page.js, room.py, live.json) and LARRYD tells the call live = {"room": true}; the view holds one empty <div data-room></div>, and the address and the member\'s pass go to the platform alone')
FIELDS['makes'] = ('what the agent asks LARRYD to have made by an outside model on a RUN (optional): a list of models on LARRYD\'s list, e.g. '
                   '["nano-banana-2"]; the agent never reaches out: its answer carries "makes": [one ask], LARRYD\'s own hand does the errand and '
                   'stores the file in the member\'s DA-M; the card\'s "sends_to" and "data_sent" must say where the words go')
FIELDS['fabric'] = ('THE DATA FABRIC (optional, Positive Feedback\'s own PF DATA FABRIC): {"modules": [module codes]}, each also declared in '
                    '"records" with read and edit; on a RUN LARRYD hands fabric = {files: the newest official pf_<module>.csv of each, '
                    'state: the account\'s Fabric state} and those modules\' records with their custom fields, and carries the answer\'s '
                    '"fabric": {"writes": [edits of custom fields only], "state": {...}}; on a CALL it hands fabric = {"state": the account\'s state, "viewer": {"member_type": who looks, for the page\'s mask}}')
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
    'environment': 'where the agent runs, the platform\'s data_agent_environment: "POSITIVE FEEDBACK" (the LARRYD runtime, an EXTERNAL agent; the same as leaving it '
                   'out) or "POSITIVE FEEDBACK (INTERNAL-ONLY)" (Positive Feedback\'s own internal runtime, an INTERNAL agent): the one tag that tells them apart',
}
ENVIRONMENT, INTERNAL_ONLY = 'POSITIVE FEEDBACK', 'POSITIVE FEEDBACK (INTERNAL-ONLY)'   # the card's "environment" (wid's larryd_runtime ENVIRONMENT, INTERNAL)
SITE = r'https://(?=[^/?#]{1,253}(?:[/?#]|$))(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}(?:[/?#][^\s"\'<>\\`]*)?'   # https to a named host: no user, no port, no number for a host
SCREEN = r'[a-z][a-z0-9]{1,15}/[a-z][a-z0-9]{1,15}'   # <species>/<page>
MOST_PITCH = 140                                      # characters on the card
OPTIONAL = ('inputs', 'records', 'live', 'makes', 'fabric', 'files')
FABRIC_MODULES = ('cont', 'invc', 'locn', 'opns', 'hrcy', 'mdia', 'brnd', 'sprt', 'imgs', 'vdeo', 'audo', 'prdn', 'agnt', 'mdls', 'logs', 'jobs')   # one pf_<module>.csv each (the runtime's core_engine/fabric.py)
FABRIC_NEEDS = ('read', 'edit')   # what "records" must declare on each Fabric module: read, and edit their custom fields
LIVE = 'live'   # the live half's folder, beside agent/
LIVE_FILES = ('live.json', 'page.html', 'page.js', 'room.py')   # all of it, and nothing else
LIVE_MAY = ('rain.js',)   # and, if the page needs it, a second script. The page's own rules are written IN the page (one <style> block), as every agent's are
LIVE_SEATS = (1, 4)
MAKES = {   # THE OUTSIDE HAND'S LIST (the same as the runtime's core_engine/outside.py): the model, what it makes, who runs it, the choices an ask may name
    'nano-banana-2': ('a picture', 'Replicate', {'aspect': ('1:1', '3:4', '4:3', '16:9', '9:16'), 'size': ('1K', '2K')}),   # size: 1K first, 2K (CORE_CLEANUP_IV 19); "reference": up to 2 DA-M keys (18)
    'flux-krea': ('a picture', 'Replicate', {'aspect': ('1:1', '16:9', '9:16', '4:3', '3:4')}),   # FLUX Krea (CORE_CLEANUP_IV 44); "reference": one DA-M key, image to image
    'kling-2.5': ('a video', 'Replicate', {'aspect': ('16:9', '9:16', '1:1'), 'seconds': ('5', '10')}),   # Kling 2.5 Turbo Pro (44); "reference": one DA-M key, the first frame
    'seedance-2.5': ('a video', 'Replicate', {'aspect': ('16:9', '9:16', '1:1'), 'seconds': tuple(str(n) for n in range(4, 31)), 'size': ('480p', '720p')}),   # 4 to 30 seconds, the model's own range (R-0041)
    # CORE_CLEANUP_IV 17 / 39 (rows 51 to 54): "reference": the member's own file, ONE, a video (topaz) or a sound (the rest); topaz, whisper and resemble-enhance make nothing without it
    'topaz-video-upscale': ('a video', 'Replicate', {'size': ('1080p', '720p'), 'fps': ('keep', '24', '30', '60')}),   # upscale and retime (row 51); no words
    'whisper': ('subtitles', 'Replicate', {}),               # the sound's words as SRT subtitles (row 52); no words
    'chatterbox': ('a sound', 'Replicate', {}),              # these words in the voice of the reference recording (row 53)
    'resemble-enhance': ('a sound', 'Replicate', {}),        # the sound cleaned (row 54); no words
    # THE EXXACT BOX (CORE_CLEANUP_IV 97): the runtime builds these from Exxact_Loot's own list of types; "reference": the type's input slots, in order
    'exxact/gpu-status': ('numbers', 'Exxact', {}),                           # the two GPUs' memory, as a JSON file
    'exxact/face-swap': ('a picture', 'Exxact', {'enhance': ('natural',)}),   # references: source, target (png or jpg, 20 MB each)
    'exxact/face-landmarks': ('numbers', 'Exxact', {}),                       # references: image (png or jpg, 40 MB); every face's box and five points, as a JSON file
    'exxact/lips': ('a video', 'Exxact', {}),                                 # references: minute_vocals (wav), minute_voice (wav), move_1 to move_8 (mp4), in that order
    'exxact/mix': ('a sound', 'Exxact', {}),                                  # row 55's mixdown: references source_1 to source_16 (wav, mp3 or mp4), source_1 needed; one wav back
}
MAKES_NUMBERS = {   # THE NUMBER FIELDS an ask may name (the runtime's outside.py MODELS[model]['numbers'], from Exxact_Loot's list): a list of at most
    # 'most' numbers ('list_numbers') or whole numbers ('list_ints') within the range; optional ones may be left out. A model not named here has none
    'exxact/face-swap': {'target_box': {'list_numbers': (0, 20000), 'most': 4, 'optional': True}},
    'exxact/lips': {'slots': {'list_ints': (1, 8), 'most': 8}},   # the ON slots, each one's move_<n> laid in its order
}
MAKES_CHECKS = {   # THE FIELDS OF A SHAPE an ask must name (the runtime's outside.py MODELS[model]['checks'], held to Exxact_Loot's own exxact.FIELD_CHECKS)
    # mix_tracks: exactly 4 tracks in order (VOICE A, VOICE B, MUSIC, SFX), each {vol 0 to 2, mute, solo};
    # mix_clips: 1 to 64 clips, each {source 1 to 16 (a reference sent), track, at, in, out (in < out), gain 0 to 4, fade_in, fade_out 0 to 30}, in seconds
    'exxact/mix': {'tracks': 'mix_tracks', 'clips': 'mix_clips'},
}
MAKES_NO_WORDS = ('exxact/gpu-status', 'exxact/face-swap', 'exxact/face-landmarks', 'exxact/lips', 'exxact/mix', 'topaz-video-upscale', 'whisper', 'resemble-enhance')   # models an ask need not give a "prompt" (the Exxact box takes none)
RECORD_VERBS = ('read', 'add', 'edit', 'remove')   # what an agent may declare on a species' records
RECORD_COUNTS = ('*', ['count'])   # THE COUNTS: "records": {"*": ["count"]}, of no one species: how many, never which
RECORD_EVERY = ('*', ('count', 'roster', 'reviews', 'joins', 'payments', 'history', 'guards'))   # what "*" may hold, each once: the counts (CALL and RUN) and the roster (CORE_CLEANUP_IV 37: the account's members, key, name, type, active, read only, on a CALL; the reviews waiting, CORE_CLEANUP_IV 23: an internal agent only, on a CALL; the join requests and the payments, row 142: read only, on a CALL; the review history, row 78: an internal agent only, on a CALL; the two guards' reports, the Agents Security Plan: an internal agent only, on a CALL)
PACK = 'pack.json'   # a knowledge pack: a folder of plain text files with pack.json {"name", "about"}
PACK_FIELDS = ('name', 'about')
PACK_KINDS = {'.json', '.txt', '.md', '.csv'}
NEEDED = tuple(k for k in FIELDS if k not in OPTIONAL)

# what the LARRYD runtime hands a RUN today: the cards the member sees; the job's own inputs (by the names in "inputs")
HANDS = ('cards', 'job', 'records', 'files')   # what LARRYD hands a RUN (the runtime's harness.HANDS): records = the member's records the manifest declares with read, as a CALL gets them
SLOT = r'0(0[1-9]|1[0-5])'   # the job's input slots, 001-015
MOST_INPUT = 10_000          # characters in one input (the LARRYD runtime refuses more)
