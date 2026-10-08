# Building an agent with LARRYD

Your server has a daemon. Your agents should have one too.

Build, test and ship AI agents with Claude Code.

This guide is for the developer's AI first and the developer second. Read it whole before you build.
`larryd guide` prints it; it ships in the package as `larryd/GUIDE.md` (`larryd --help` names the path).
Every command named here exists and works today; what does not exist yet is listed at the end, plainly.

Start: `larryd new <name>` for a blank agent (or `larryd new <name> --from marketplace` for the example), then read
`<name>/CLAUDE.md`.

> **Today.** Works now, on your own computer: install from a package or index you were given, make an agent
> (`larryd new`), check it (`larryd doctor`), run it (`larryd run`), and see its card on your own LARRYD
> (`larryd card`).
>
> Not live yet: the public install (the registries hold only the name's reservation), `larryd submit` opening with the
> platform, RUNs that hand the job's own inputs on the platform, and the platform's sides of the skills (the LARRY LLM
> greeting, the FROST identity, the DA-M store). Each is said again where it comes up, and listed under "Not there yet".

## The platform in one minute
LARRYD agents work for members of Positive Feedback, the platform. An account is a company; a member is a person in
it. The platform's products (Invoice Maps, Agency Mgmt, Pace Shift, LARRYD) each have modules (Contacts, Invoices,
Media, Agents, ...), and every screen is named `<species>/<page>` (its address is `app/<species>/<page>`, e.g.
`app/cont/card`). Your agent lives on one screen. Its card appears in the agent marketplace, where a member hires it
with the card's hire toggle; once hired, it is ready to switch on in the member's settings. A member's work is a job;
a RUN asks your agent to work on one, and its answer (`delivery`) lands in that job. Each RUN costs the member the
agent's price in mTok (see below).

## What you are building
An agent today is a deterministic Python program: given the same job, it gives the same answer. "AI" here means it is
built with Claude Code; the agent itself calls no model. Your agent runs inside LARRYD, sealed off: no network, no files
outside its own run, no other programs. LARRYD connects it to the platform: it reads what the agent needs, hands it in,
and carries the answer back. The agent belongs to its developer.

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
- `samples/job.json`: a sample job for `larryd run`; `samples/job_inputs.edit-me.json`: a job with its own inputs, for
  once the agent declares them (`"job"` in `run.hands`, `"inputs"`): give it your input names, rename it to
  `job_inputs.json`, then `larryd run --job samples/job_inputs.json`
- `.mcp.json`: starts the LARRYD tools in Claude Code when you open the folder with `claude` (it names the full path
  of this
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
6. Only what it is handed. The inputs are what `run.hands` names: `cards` (the agent cards the member sees; for agents
   that show the marketplace) and `job`
   (the job's own inputs, by the names the manifest's `inputs` gives them).
7. Nothing fake. The agent answers from what it is handed, or it says plainly that it cannot.

## The job's inputs
An agent that needs words from the member (a name, a mood, a date) declares them:

    "run": {"do": "answer", "hands": ["job"]},
    "inputs": {"name": "001", "mood": "002"}

Each name sits on one of the job's input slots, 001 to 015 (the job's agent fields on the platform). On a RUN, LARRYD
reads that RUN's inputs from the platform and hands them in as `job`: `{"name": "...", "mood": "..."}`. A slot the
member
left empty is simply not handed. LARRYD refuses the run when the job holds an input the agent does not declare, or a
value that is not text or is longer than 10,000 characters, and it keeps none of them. In a sample job (the project's
`samples/job_inputs.edit-me.json`, renamed to `job_inputs.json` once its names are yours), give the inputs the same
way: `{"do": "answer", "job": {"name": "Harbor", "mood": "calm cool"}}`.

## The member's records
An agent that works on a member's own records (a calendar on the Operations screen, say) declares which, and what it
does with them:

    "calls": ["month"],
    "records": {"opns": ["read", "add", "edit", "remove"]}

The species is the module's code from the screens table (opns = Operations, cont = Contacts, ...); the verbs are read,
add, edit and remove, any of them. On a CALL (the agent answering on the member's screen) LARRYD reads that member's
records of each declared species through the platform's own record doors and hands them in as
`records = {"opns": [rows]}`: each row the record's fields by the platform's names, its key as `"key"`. The agent's
answer may carry `"writes"` (name it in `gives`):

    "writes": [{"do": "add", "species": "opns", "values": {"identity_operations_date": "2030-10-07", "identity_operations_headline": "Partners", "data_meeting_time": "14:00"}},
               {"do": "edit", "species": "opns", "key": "MOPN_...", "values": {"data_meeting_time": "15:00"}},
               {"do": "remove", "species": "opns", "key": "MOPN_..."}]

LARRYD carries each to the platform's own doors for that member (at most 20 in one answer; values a flat {field: text}),
then runs the agent ONCE MORE on the same page with the records as they are now and `written`, what the platform said of
each (`[{"do", "species", "key", "ok", "why"}]`, a new record's key on an add), so what the agent draws is the truth; writes
on that second run are ignored. A write on a species or verb the manifest does not declare refuses the whole answer, and
nothing is carried. The declaration is in the manifest's hash: FROST approves what the agent may read and write with the
agent itself. A RUN is handed no records; a CALL is handed `records` only. On your own LARRYD the records live in one
small file (`~/.larryd/preview/records_<species>.json`), which you may write by hand to try an agent.

## The app's own parts in a view
An agent's view draws with the platform's own classes (they work inside the view: the page's sheets stand in it), so a view
reads like the app. Buttons: `btn btn--small` (a selected one carries `aria-current="true"`), a row of them in
`wl-btnrow`, a form's field `sub-search-input`, a controller `sub-controller-box` with its `wl-cols` columns and
`wl-divider`, the glass box `sub-controller-box wl-glass` with `wl-panel` inside, the type roles (`subtitle`, `emphasis`,
`body`, `caption`, `annotation`, `label wl-label`).

THE CIRCLES, one standard platform-wide: every round control is `<a class="btn btn--small round">` (or a `button`) with
ONE plain-text glyph inside and no rule of the agent's own on it (the themes give the look: no fill at rest, the glass
sheen, the border and glyph in the button colour; the fill, dark words, glow and lift on hover):

| Circle | The glyph | Written |
|---|---|---|
| back, previous | `<` | `&lt;` |
| forward, next | `>` | `&gt;` |
| close | `X` | `X` |
| run, play | `▶` | `&#9654;` |
| up | `▲` | `&#9650;` |
| down | `▼` | `&#9660;` |
| add | `+` | `+` |
| remove | `−` | `&#8722;` |

## 4. The doctor
    larryd doctor --fix      (write normally, then this; or plain `larryd doctor` to check only, --json for JSON)

Your card's look is a small record of NAMES in `agent/agent.json`, never CSS:

    "look": {"accent": "active-color-04", "radius": "step-2", "space": "step-3", "effect": "wellness",
             "text": {"name": "title", "price": "callout"}}

The platform's one card template draws every card and puts the record on the card as custom properties that point at
the live theme (`--accent: var(--active-color-04)`), so your card follows the brand and light or dark by itself. Every
value must be a name on the menu below; the platform checks it again at submission and when it draws the card, and
drops anything else. A look the record does not name keeps the template's default.

Design in CSS if you like: write `agent/card.css` normally and run `larryd doctor --fix`.

- It maps each value to the nearest name on the menu and says each mapping (CONVERTED ...):
  - the card's first colour to the theme colour variable nearest as the eye sees it (OKLab distance against the
    reference theme, done once; only the name is kept);
  - its corner radius and its padding to the nearest step;
  - written type on a part of the card to the nearest role (by size and weight, a different case costing 6px, an
    unwritten case being none as in CSS; a role made for navigation, a link or a field's label only when the selector
    says so).
- Never an effect: the card's class picks it (Mark I crt, Mark II wellness, Mark III glitch).
- Every other value is said too, as DROPPED ... with why:
  - colour is card-wide (the accent only), so a part's colour is dropped: a part takes a role, never a colour;
  - gap and margin: "space" is the card's padding, and the template sets the gaps from it;
  - layout, position, hover and other states are the template's;
  - shadows, transforms, transitions and animation belong to the effect the class picks;
  - @import, @font-face and @keyframes never become a name.
- It writes the look record, moves the sheet to `design/card.css` (agents ship no CSS), and keeps your original
  manifest, and the design sheet it replaces, in `.larryd/doctor_backup/`.
- Plain `larryd doctor` changes nothing: while a sheet is in `agent/` it fails the shape and says what it WILL CONVERT
  and WILL DROP. `larryd place` and `larryd submit` convert it the same way first, so CSS is never a reason to refuse.
- `--fix` also fills the card's missing facts with honest defaults it names. The same files always give the same
  result.

### The menu (a fixed list, the same for the doctor, this guide and the platform)

"accent": a theme colour variable, `active-color-01` to `active-color-64`. The number names a slot that every theme
fills with its own colour, in each brand and in light and dark: the same number is the same slot everywhere, so the
card follows the live theme. The colours below are the reference theme's only; a designed colour goes to the nearest
as the eye sees it.

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

The type roles (designed type on a part goes to the nearest role, nearest by size and weight, a different case costing
6px (an unwritten case is none, as in CSS); the role brings its own font, style and letter spacing):

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
beside this guide in the package).

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

Not live yet: until LARRYD opens submissions with the platform, `larryd submit` says it cannot reach the door. When
it is open, three steps, nothing to carry:

1. The doctor runs (and converts a design sheet, as `--fix` does); a problem stops it here.
2. `agent/` (nothing else) is packed into one file and sent to LARRYD.
3. Your browser opens the claim page: sign in there with Google or Apple within 10 minutes, and the agent waits in the
   review queue; the page says what happens next.

No account to make, no key or secret to paste or keep. LARRYD reads what it receives and runs none of it: it re-runs
the doctor itself, and refuses a file that is too big (5 MB), unsafe, or the eleventh from one address within an hour
(10 per address per hour). Unclaimed files are deleted after 10 minutes.
`--no-browser` prints the claim page instead of opening it. A changed agent is a new submission, reviewed again.
A person at LARRYD reviews it. Approved, it goes into LARRYD's locker under its card key and to the platform's review
(FROST's); rejected, the answer says why. Either way the answer goes to the email of your sign-in.

## What LARRYD does with your agent
- It holds `agent/` in its locker with the hash of the code and of the manifest, and checks them on every call and run.
  Any change is refused as tampered.
- FROST's review: a SYSTEM owner (the platform's own people) approves or rejects those exact hashes. LARRYD shows,
  hires and runs an agent only
  when FROST approved the hashes it holds.
- A member hires the agent in the agent marketplace with a toggle. A RUN is a request; LARRYD runs the agent in its
  sandbox, and mTok charges the agent's own rate (0 = free).

## mTok
mTok is the platform's usage unit: members' accounts hold it, and a RUN of your agent costs the member its price, a
whole number of mTok you set per run in the card (`"price"`, 0 = free), charged after a DONE run. Payouts to developers
are not there yet: nothing here promises a money value or a share.

## What the card says about data and where the agent is offered
- `availability` (optional): `"offline"` for an agent shown for information only. Its card is dimmed and locked, it says
  Offline where its price stands, and it cannot be hired. Leave the field out for an agent that can be hired.
- `developer_site` (optional): your website, a plain https address such as `https://example.com`. The card links your
  name to it, in a new tab. Leave the field out for no link.
- `sends_to` and `data_sent`: the agent itself never reaches out. When the platform sends a member's data to an outside
  AI service for the agent, `sends_to` names that service and `data_sent` says what is sent; the platform asks the
  member before anything goes out. An agent that sends nothing leaves both `""`.
- `residency` is which marketplaces the agent is offered on: INTERNAL = Positive Feedback's own agent marketplace only;
  EXTERNAL = other marketplaces only (e.g. the Microsoft marketplace), not Positive Feedback; BOTH = Positive Feedback
  and at least one external marketplace. It is not where the agent runs: every LARRYD agent runs in LARRYD.
- `class`, as a guide to how much the agent does: Mark I = simple, Mark II = complex, Mark III = extremely complex. The
  class also picks the card's effect.
- `authorization`: who may hire it, PUBLIC (every account) or PRIVATE (one account). It is your starting setting; the
  platform's authorize panel (in FROST) can change it at any time after, and a PRIVATE agent's owning account is
  entered there.
- `developer`: who made it, as the card credits it: your name, or your company's.

## In Claude Code
In a project made by `larryd new`, open the folder with `claude` and approve the LARRYD tools:
larryd_new, larryd_doctor, larryd_run, larryd_submit, larryd_skills, larryd_pack, larryd_card.
Elsewhere, one line: `claude mcp add larryd -- larryd mcp`. The repository is also a Claude Code plugin marketplace.
The loop for the AI: change the agent → larryd_doctor → larryd_run → fix → again → larryd_submit.

## Skills and knowledge
- A skill is a definition named by its hash. Declare the hashes in `skills`; `larryd skills` lists them.
  - The mTok charge: LARRYD charges the member the agent's own rate after a DONE run (every run; declaring it changes
    nothing).
  - The LARRY LLM greeting: before the RUN, LARRYD asks LARRY LLM for the greeting it gives the member today and hands
    it
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
- The public install: until 0.1.0 is published, the registries hold only the name's reservation (0.0.1).
- `larryd submit` with the platform: the door is not open yet.
- Payouts in mTok to developers.
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

The card's allowed values:

| Field | Allowed values |
|---|---|
| class | MARK I AGENT (NORMAL): simple (effect crt); MARK II SUPER AGENT (HARNESS): complex (effect wellness); MARK III QUANTUM AI (AGENTIC CODE): extremely complex (effect glitch) |
| type | OFF-THE-SHELF, DEVELOPER |
| residency | which marketplaces it is offered on: INTERNAL: Positive Feedback's own agent marketplace only; EXTERNAL: other marketplaces only (e.g. the Microsoft marketplace), not Positive Feedback; BOTH: Positive Feedback and at least one other marketplace (every LARRYD agent runs in LARRYD) |
| authorization | PUBLIC, PRIVATE (who may hire it: your starting setting; the platform's authorize panel can change it at any time after, and a PRIVATE agent's owning account is entered there) |
| product | INVOICE MAPS, AGENCY MGMT, PACE SHIFT, LARRYD |
| price | a whole number of mTok per run: 3 or "3"; "0" is free |

| Screen (<species>/<page>, at app/<species>/<page>) | Product | Module |
|---|---|---|
| cont/home, cont/list, cont/card | INVOICE MAPS | Contacts |
| invc/home, invc/list, invc/card | INVOICE MAPS | Invoices |
| locn/home, locn/list, locn/card | INVOICE MAPS | Locations |
| opns/home, opns/list, opns/card | INVOICE MAPS | Operations |
| hrcy/home, hrcy/list, hrcy/card | AGENCY MGMT | Hierarchies |
| mdia/home, mdia/list, mdia/card | AGENCY MGMT | Media |
| brnd/home, brnd/list, brnd/card | AGENCY MGMT | Brand |
| sprt/home, sprt/list, sprt/card | AGENCY MGMT | Sprint |
| imgs/home, imgs/list, imgs/card | PACE SHIFT | Images |
| vdeo/home, vdeo/list, vdeo/card | PACE SHIFT | Videos |
| audo/home, audo/list, audo/card | PACE SHIFT | Audio |
| prdn/home, prdn/list, prdn/card | PACE SHIFT | Production |
| agnt/home, agnt/list, agnt/card | LARRYD | Agents |
| mdls/home, mdls/list, mdls/card | LARRYD | Models |
| logs/home, logs/list, logs/card | LARRYD | Logs |
| jobs/home, jobs/list, jobs/card | LARRYD | Jobs |
| larry/home | any | the product's dashboard |

The class picks the card's effect: Mark I crt, Mark II wellness, Mark III glitch. `larryd doctor --fix` sets the
look's "effect" from the class, and `larryd doctor` fails when they differ. A value off these lists fails with the
ones to use.

See your card the way a member will, on your own LARRYD:

    larryd                   (in another terminal: your runtime, on 127.0.0.1:5010)
    larryd card              (places the agent in its locker and opens http://127.0.0.1:5010/marketplace)

`larryd place` does the placing without opening the page. The same agent placed again replaces itself. A card the
marketplace cannot show (no screen, a price that is not whole mTok) is listed under "Not on the shelf" with why.

## Glossary
- **FROST**: the platform's identity and security office: who a member is, what they may do, the review of agents and
  the authorize panel.
- **DA-M**: the platform's file store: a member's files (the DA-M store skill keeps an answer's files there).
- **LARRY LLM**: one of the platform's offices; for agents, it gives the greeting a member is given today (the LARRY LLM
  greeting skill).
- **locker**: where LARRYD holds an approved agent: its `agent/` files, with the hashes of its code and manifest.
- **card key**: the key the platform gives an agent's card at approval; LARRYD finds the agent by it.
- **claim page**: the page `larryd submit` opens, where you sign in with Google or Apple to submit the file you sent.
- **CALL and RUN**: the two lanes. A CALL answers at once on the member's screen (the names in `"calls"`); a RUN is a
  request on a job, run in the sandbox, whose `delivery` lands in the job and which costs the agent's price.
- **MARK classes**: the platform's three agent classes, as a guide: MARK I AGENT (NORMAL) = simple, MARK II SUPER
  AGENT (HARNESS) = complex, MARK III QUANTUM AI (AGENTIC CODE) = extremely complex. On the card the class picks the
  effect: Mark I crt, Mark II wellness, Mark III glitch.
- **residency**: which marketplaces an agent is offered on: INTERNAL (Positive Feedback only), EXTERNAL (other
  marketplaces only), BOTH (Positive Feedback and at least one other).
- **species**: the first half of a screen's name, its module's short code (`cont` for Contacts, `agnt` for Agents).
- **product**: one of the platform's products: Invoice Maps, Agency Mgmt, Pace Shift, LARRYD.
- **module**: a part of a product (Contacts, Invoices, Agents, ...), with its home, list and card screens.
- **screen**: `<species>/<page>`, e.g. `cont/card`; its address in the app is `app/<species>/<page>`. An agent lives on
  one screen.
