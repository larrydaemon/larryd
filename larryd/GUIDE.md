# Building an agent with LARRYD

Your server has a daemon. Your agents should have one too.

Build, test and ship AI agents with Claude Code.

This guide is for the developer's AI first and the developer second. Read it whole before you build.
`larryd guide` prints it; it ships in the package as `larryd/GUIDE.md` (`larryd --help` names the path).
Every command named here exists and works today; what does not exist yet is listed at the end, plainly.

Start: `larryd new <name> --from marketplace`, then read `<name>/CLAUDE.md`.

## What you are building
An agent is a small program that answers a job. Your agent runs on LARRYD, air gapped: LARRYD is also the place where
agents live and run, apart from everything else. The agent belongs to its developer. LARRYD connects it to the platform: it reads what the agent needs, hands it in, and carries the answer back.
The agent itself reaches nothing.

The whole contract: LARRYD runs the agent's entry file as its own process. One JSON object comes in on stdin,
one JSON object goes out on stdout. `delivery` in the answer (plain text) is what lands in the member's job.

## 1. Install
    python3 -m venv ~/larryd-venv && ~/larryd-venv/bin/pip install --pre larryd
    ~/larryd-venv/bin/larryd --version

That works today wherever the release is published, and with a package file or index you were given
(`pip install --pre --index-url <the index> larryd`). It needs Python 3.11 or newer (`python3 --version`; a Mac's own
python3 is 3.9). Nothing needs activating: a project made by `larryd new` names the full path of this larryd.
Until 0.1.0 is published, the public registries hold only the name's reservation, 0.0.1, which prints one line and
does nothing; from 0.1.0 these work too, each giving the one command `larryd`:

    pipx install larryd
    uv tool install --python 3.12 larryd
    npm install -g larryd
    cargo install larryd

uv brings its own Python (`brew install uv`); pipx: `brew install pipx` or `sudo apt install pipx`; npm and cargo keep
LARRYD in its own place. Outside a virtual environment Homebrew, Debian and Ubuntu refuse a plain `pip install`
(PEP 668). It is proven on Python 3.14 (a Mac) and 3.11 (Debian 12).

Your own LARRYD: `larryd` alone runs the daemon, LARRYD's runtime on this computer, in this terminal (127.0.0.1:5010,
its instance in ~/.larryd; `LARRYD_PORT` and `LARRYD_INSTANCE` name others; Ctrl-C stops it), where you can try what you
build. No sudo; as root its instance is /var/lib/larryd, for a server.

## 2. A new agent
    larryd new <name>

This makes the folder `<name>/`:
- `agent/`: the agent, and only the agent. It is exactly what LARRYD holds.
  - `agent/agent.json`: the manifest (its fields are explained in the project's CLAUDE.md)
  - `agent/agent.py`: the code, with one entry: `answer(job)`
  - an agent ships no CSS: the card's look is the `"look"` record in `agent/agent.json` (section 4)
- `CLAUDE.md`: the spec and the rules, for Claude Code
- `.claude/skills/larryd/SKILL.md`: the larryd skill Claude Code loads
- `samples/job.json`: a sample job for `larryd run`
- `.mcp.json`: starts the LARRYD tools in Claude Code when you open the folder with `claude` (it names the full path of this
  larryd, so no virtual environment needs activating)

To start from a LARRYD example instead of a blank agent:

    larryd new marketplace --from marketplace

makes the PF AGENT MARKETPLACE: its code, its manifest with a doctor-clean card, its look record, its design sheet
(`design/card.css`, not shipped) and a sample job. It is the agent the platform's own marketplace is built from.

## 3. The rules
LARRYD's sandbox refuses 1, 2 and 3 when the agent runs; the doctor checks all of them before that.
1. No network, ever. No network module, no address.
2. Nothing outside its own folder: no path elsewhere, no link. It writes only in the folder it is run in.
3. No new process: no subprocess, no os.system, no multiprocessing.
4. The Python standard library only.
5. No secret in the agent.
6. Only what it is handed. The inputs are what `run.hands` names: `cards` (the agent cards the member sees) and `job`
   (the job's own inputs, by the names the manifest's `inputs` gives them).
7. Nothing fake. The agent answers from what it is handed, or it says plainly that it cannot.

## The job's inputs
An agent that needs words from the member (a name, a mood, a date) declares them:

    "run": {"do": "answer", "hands": ["job"]},
    "inputs": {"name": "001", "mood": "002"}

Each name sits on one of the job's input slots, 001 to 015 (the job's agent fields on the platform). On a RUN, LARRYD
reads that RUN's inputs from the platform and hands them in as `job`: `{"name": "...", "mood": "..."}`. A slot the member
left empty is simply not handed. LARRYD refuses the run when the job holds an input the agent does not declare, or a
value that is not text or is longer than 10,000 characters, and it keeps none of them. In `samples/job.json`, give the
inputs the same way: `{"do": "answer", "job": {"name": "Harbor", "mood": "calm cool"}}`.

## 4. The doctor
    larryd doctor --fix      (write normally, then this; or plain `larryd doctor` to check only, --json for JSON)

Your card's look is a small record of NAMES in `agent/agent.json`, never CSS:

    "look": {"accent": "active-color-04", "radius": "step-2", "space": "step-3", "effect": "wellness",
             "text": {"name": "title", "price": "callout"}}

The platform's one card template draws every card and puts the record on the card as custom properties that point at
the live theme (`--accent: var(--active-color-04)`), so your card follows the brand and light or dark by itself. Every
value must be a name on the menu below; the platform checks it again at submission and when it draws the card, and
drops anything else. A look the record does not name keeps the template's default.

Design in CSS if you like: write `agent/card.css` normally and run `larryd doctor --fix`. It maps each value to the
nearest name on the menu and says each mapping (CONVERTED ...): the card's first colour to the theme colour variable
nearest as the eye sees it (OKLab distance against the reference theme, done once; only the name is kept), its corner
radius and its padding to the nearest step, written type on a part of the card to the nearest role (by case first, an
unwritten case being none as in CSS, then size and weight; a role made for navigation, a link or a field's label only
when the selector says so), the sheet's animation words to the nearest effect. Every other value is said too, as
DROPPED ... with why: colour is card-wide (the accent only), so a part's colour is dropped (a part takes a role, never
a colour); gap and margin are dropped ("space" is the card's padding and the template sets the gaps from it); layout,
position, hover and other states, shadows, transforms and transitions are the template's and the effect's; @import,
@font-face and @keyframes never become a name. It writes the look record, moves the sheet to `design/card.css` (agents
ship no CSS) and keeps your original manifest, and the design sheet it replaces, in `.larryd/doctor_backup/`. Plain
`larryd doctor` changes nothing: while a sheet is in `agent/` it fails the shape and says what it WILL CONVERT and
WILL DROP. `larryd place` and `larryd submit` convert it the same way first, so CSS is never a reason to refuse. --fix
also fills the card's missing facts with honest defaults it names. The same files always give the same result.

### The menu (a fixed list, the same for the doctor, this guide and the platform)

"accent": a theme colour variable, `active-color-01` to `active-color-64`. The card follows the live theme (brand,
light
or dark), so the colours below are the reference theme's only; a designed colour goes to the nearest as the eye sees
it.

| Colour (reference theme) | active-color-NN |
|---|---|
| `#92866F` | 01, 02, 03, 04, 06, 13, 15, 16, 17, 18, 21, 22, 25, 26, 31, 32, 33, 35, 36, 37, 38, 40, 41, 43, 52, 56, 57, 59, 62, 63, 64 |
| `#D5C5AA` | 05, 23, 28 |
| `#EFE5C6` | 07, 46, 48, 50 |
| `#FDFDFD` | 08 |
| `#121212` | 09, 14, 24, 27, 29, 54, 60 |
| `#1F1F1D` | 10, 20, 34, 42, 44, 53, 55, 61 |
| `#17191A` | 11, 12, 30, 39, 45, 47, 49, 51, 58 |
| `#F1E8C7` | 19 |

"radius" is the card's corner, "space" its padding (the template sets the gaps inside from it); each is a step of the
scale (a designed length goes to the nearest step; a tie rounds down):

| Step | step-0 | step-1 | step-2 | step-3 | step-4 | step-5 | step-6 | step-7 | step-8 | step-9 |
|---|---|---|---|---|---|---|---|---|---|---|
| px | 0 | 2 | 4 | 8 | 12 | 16 | 22 | 32 | 48 | 64 |

"effect": none, crt, wellness, glitch.

"text": a part of the card and its type role (each part has a default; name only the ones you change). A part takes a
role, never a colour: colour is card-wide, the accent only.

| Part | Default role | What it is |
|---|---|---|
| number | caption | the card's number (No. 001) |
| class | caption | the class line (MARK I AGENT) |
| name | title | the agent's name |
| info | annotation | the product and module |
| pitch | body | the one-line pitch |
| developer | annotation | the developer credit |
| facts | annotation | the type and residency |
| price | callout | the price |

The type roles (designed type on a part goes to the nearest role, nearest by case first, an unwritten case being none
as in CSS, then size and weight; the role brings its own font, style and letter spacing):

| Role | Size | Weight | Case | For |
|---|---|---|---|---|
| heading | 48px | 900 | uppercase | the page or card heading |
| title | 32px | 900 | uppercase | a name, the card's name |
| subtitle | 14.4px | 900 | uppercase | a section's title |
| body | 14.4px | 300 | none | running text, the card's pitch |
| caption | 11.2px | 600 | uppercase | an eyebrow, the card's class line |
| label | 14.4px | 500 | uppercase | a field's label (chosen only for a selector naming label, field) |
| link | 14.4px | 500 | none | a link (chosen only for a selector naming link, a, href) |
| nav | 11.2px | 400 | uppercase | the main navigation (chosen only for a selector naming nav, menu, navigation) |
| subnav | 14.4px | 400 | uppercase | a sub navigation (chosen only for a selector naming subnav, tabs, tab, navigation) |
| callout | 17.6px | 500 | uppercase | a figure that stands out, the card's price |
| notes | 17.6px | 500 | uppercase | small notes |
| annotation | 9.6px | 300 | uppercase | facts, the card's product, module and type |

It checks the project, the manifest, the entry, the air gap, no secret, the shape, the skills and the knowledge.
Every problem names the file and line, what is wrong and what to do. Do what it says, then run it again.
Never silence a check to make it pass. What each check proves, and why: THE LARRYD CHECKS ([CHECKS.md](CHECKS.md),
larryd.ai/checks.html).

    larryd doctor --badge

also writes `larryd-checks.svg` beside `agent/` (never inside it): PASS in gold or FAIL in red, with the day and the
checks' version. Paste `![LARRYD checks](larryd-checks.svg)` into your README; run it again after each change.

## 5. Run it here
    larryd run               (or --job <file>, --json)

The doctor runs first. Then the agent runs the way LARRYD runs it: its own process, no network, no new process,
a scratch run folder removed after, the plain Python runtime, an empty environment, 20 seconds. It is handed what
a RUN hands it: `{"do": run.do}` plus what `run.hands` names, from the sample job. The answer must be one JSON object
holding only what `gives` names. Nothing is sent anywhere. On a Mac or Linux (Linux: LARRYD's own bubblewrap sandbox,
`sudo apt install bubblewrap`); on Windows, use WSL.

## 6. Submit
    larryd submit

Three steps, one gate, nothing to carry. The doctor runs first. Then `agent/` (nothing else) is packed into one file
and sent to LARRYD, and your browser opens its claim page. Sign in there with Google or Apple within 10 minutes, and
it waits in the review queue; the page says what happens next. No account to make, no key or secret to paste or keep.
LARRYD reads what it receives and runs none of it: it re-runs the doctor itself, and refuses a file that is too big
(5 MB), unsafe, or one of too many from one network in an hour. Unclaimed files are deleted after 10 minutes.
`--no-browser` prints the claim page instead of opening it. A changed agent is a new submission, reviewed again.
A person at LARRYD reviews it. Approved, it goes into LARRYD's locker under its card key and to the platform's review
(FROST's); rejected, the answer says why. Either way the answer goes to the email of your sign-in.

## What LARRYD does with your agent
- It holds `agent/` in its locker with the hash of the code and of the manifest, and checks them on every call and run.
  Any change is refused as tampered.
- FROST's review: a SYSTEM owner approves or rejects those exact hashes. LARRYD shows, hires and runs an agent only
  when FROST approved the hashes it holds.
- A member hires the agent in the agent marketplace with a toggle. A RUN is a request; LARRYD runs the agent in its
  sandbox, and mTok charges the agent's own rate (0 = free).

## In Claude Code
In a project made by `larryd new`, open the folder with `claude` and approve the LARRYD tools:
larryd_new, larryd_doctor, larryd_run, larryd_submit, larryd_skills, larryd_pack, larryd_card.
Elsewhere, one line: `claude mcp add larryd -- larryd mcp`. The repository is also a Claude Code plugin marketplace.
The loop for the AI: change the agent → larryd_doctor → larryd_run → fix → again → larryd_submit.

## Skills and knowledge
- A skill is a definition named by its hash. Declare the hashes in `skills`; `larryd skills` lists them.
  - The mTok charge: LARRYD charges the member the agent's own rate after a DONE run (every run; declaring it changes nothing).
  - The LARRY LLM greeting: before the RUN, LARRYD asks LARRY LLM for the greeting it gives the member today and hands it
    in as `greeting` (`{"date", "lang", "greetings": {time of day: the words}}`). In `samples/job.json`, give a
    `greeting` of that shape.
  - The FROST identity: before the RUN, LARRYD asks FROST who the agent works for and hands it in as `identity`:
    `{"first_name", "member_type", "account_name"}`, nothing else (no email, no address, no key).
  - The DA-M store: the answer may carry `"files": [{"name", "content_b64"}]` (name `files` in `gives`); after the
    charge, LARRYD keeps each in the member's own DA-M, the agent's card key as its source. At most 10 files, plain
    names, all inside the answer's own limit of 1 MB.
- A knowledge pack is a folder (`pack.json` with `name` and `about`, plus .md .txt .csv .json files) named by its hash;
  `larryd pack <folder>` checks it and gives the hash.

## Not there yet
- Skills: the platform's sides of the LARRY LLM greeting, the FROST identity and the DA-M store are not on the live
  platform yet; until they are, a RUN of an agent that declares one fails with LARRYD's plain reason.
- Knowledge packs: LARRYD holds none yet, so declaring one in `knowledge` fails the doctor. Leave it `[]`.
- `larryd run` on Windows itself (use WSL). The doctor works everywhere.
- The job's inputs on the live platform: LARRYD hands `job` today, but the platform's side (the route that gives
  LARRYD a RUN's inputs) is not on the live platform yet; until it is, a RUN of an agent that hands `job` fails with
  LARRYD's plain reason. `larryd run` works with them now.

## The card and the shelf

Every agent for hire is a card on the marketplace: its number and class, the hire toggle, its name, its art, the
product and module of the screen it lives on, its pitch, its developer, its type and residency, its price in whole
mTok, and, when it sends a member's data to an outside AI service, where and what. The card's facts are the `card`
field of `agent/agent.json` (the doctor checks them with the marketplace's own rules); the number and the art are
LARRYD's to give at approval.

See your card the way a member will, on your own LARRYD:

    larryd                   (in another terminal: your runtime, on 127.0.0.1:5010)
    larryd card              (places the agent in its locker and opens http://127.0.0.1:5010/marketplace)

`larryd place` does the placing without opening the page. The same agent placed again replaces itself. A card the
marketplace cannot show (no screen, a price that is not whole mTok) is listed under "Not on the shelf" with why.

