# What LARRYD's runtime assumes about the platform

The platform changes; this is the whole list of what the runtime depends on, so re-aligning after a change is a diff
against this file, not a rebuild. Each line names where the assumption lives in the code. Checked against the
platform on 2026-10-05 (all held); the doors LARRYD calls rewritten for the core cleanup on 2026-11-05.

## The doors the platform calls on LARRYD (`web/app.py`)
| door | sends | answers |
|---|---|---|
| GET /api/agents/answer | account, scope, member, agent_key | the agent's answer (the marketplace: title, cards, total, hired, filters) |
| POST /api/agents/hire | account, scope, member, agent_key, on=on/off | what wid answered to the hire or unhire |
| POST /api/agents/defaults | account, scope, member, board | {placed: [keys]} |
| POST /api/jobs/run | account, scope, member, job_key, run | 202 {accepted, run, already} |

Every call is signed: HMAC-SHA256 over `route + ' ' + at + ' ' + compact sorted JSON`, headers X-Office and
X-Office-At, inside the window (`core_engine/signing.py`; the platform's `offices.signature`).

## The doors LARRYD calls on the platform (`core_engine/harness.py`; stood in for by `core_engine/preview.py`)
WID ALONE (the core cleanup, the owner 2026-11-05: "no agents should have anything to do with cc, fs, laryllm, so"). The
runtime holds the address of wid and of no other office (`schemas/runtime.json`); every service of a RUN is a wid door that
asks its office AS wid (wid's `core_engine/offices.py`), only while that member's RUN is open (wid's own word), never stored.
| office | door | asks | reads back |
|---|---|---|---|
| wid | GET /agnt/cards | nothing | cards: [the card, below] |
| wid | GET /agnt/hired | account, scope, member | hired: [{agent_key, board, shell_id, on, job_key}] |
| wid | POST /agnt/hire, /agnt/unhire | account, scope, member, agent_key | {shell_id, job_key, board, already} / {removed} |
| wid | GET /jobs/queued | nothing | jobs: [{account, scope, member, job_key, run}] |
| wid | GET /agnt/records/list | account, scope, member, agent_key (the agent's card key), segment, page=list, limit, offset | rows: [the record's columns], total, first: [the member's BY PRIORITY keys of this species' list, in rank order] (an agent that declares `records`; `core_engine/member_records.py` hands each ranked row its rank as `priority` 1..n, beside `key`) |
| wid | GET /agnt/records/counts | account, scope, member, agent_key (the agent's card key) | scope, modules: {species: how many records the member may list}, products: {species: product slug}, ties: [[from, to, how many]]; numbers and codes alone (an agent that declares `"records": {"*": ["count"]}`; `core_engine/member_records.py` checks it and hands it as `counts`, on a CALL and on a RUN) |
| wid | POST /agnt/records/add, /agnt/records/edit, /agnt/records/remove | account, scope, member, agent_key (the agent's card key), segment, values / key | {key} / {key} / {removed}; a refusal as {error} or {refused} (carried to the agent as `written`). WHEN THE RUNTIME ASKS THEM: on a CALL, only for the member's own confirmed act (`act`); on a RUN, only for an internal agent on LARRYD RUNTIME INTERNAL whose approved manifest says `"run": {"writes": true}` (2026-11-13, `core_engine/harness.py` `_run_writes`: the same check and the same doors; any other RUN's `writes` are dropped and its line says so; a refused write ends the RUN FAILED) |
| wid | GET /agnt/fabric | account, scope, member | apis, databases, viewer: {member_type} (an agent that declares `"fabric": {"snapshot": true}`; wid reads the snapshot) |
| wid | POST /agnt/submit | agent_key, name, code_sha256, manifest_sha256, manifest | {state, card_key}: wid writes the card, PENDING until the platform shows it |
| wid | GET /agnt/approved | nothing | approved: [{agent_key, code_sha256, manifest_sha256, card_key}] (FROST's review, as wid reads it) |
| wid | GET /agnt/review_state | agent_key, code_sha256, manifest_sha256 | {state, note}: approved only for exactly approved hashes, else the card's word (waiting, rejected, revoked, not submitted) |
| wid | GET /jobs/inputs | account, scope, job_key, run | inputs: {slot: value} |
| wid | POST /jobs/result | account, scope, job_key, run, state, log, delivery, job (the agent's answer's `job`, its job's slots, when it gives one) | {saved} |
| wid | GET /jobs/balance | account | subscriptions: [{agent_group}] (wid asks mTok) |
| wid | POST /jobs/charge | account, scope, member, job_key, run | {charged, free, paid_from}: the job's bill, from the RUN's own card (wid asks mTok) |
| wid | GET /jobs/file | account, scope, member, job_key, run, dam_key | {dam_key, content_b64, ...} (wid asks DA-M) |
| wid | POST /jobs/upload | account, scope, member, job_key, run, name, content_b64, source_key | the stored file (wid asks DA-M) |
| wid | POST /jobs/provider_key | account, scope, member, job_key, run, provider | {key}, for one errand of the RUN's own agent; read from the platform's vault at that moment, never stored |
| wid | GET /jobs/identity | account, scope, member, job_key, run | {first_name, member_type, account_name} (wid asks FROST) |
| wid | GET /jobs/greeting | account, scope, member, job_key, run | the greeting (wid asks LARRY LLM) |

TWO GUARDS, NEVER ONE (the owner's rule, 2026-10-04): an agent is verified at every call, hire and run only when (1) the
runtime's locker holds it with exactly these hashes (`place`, the owner's approved file; on Cloud Run the lockers bucket's
locker.json) AND (2) wid's /agnt/approved lists exactly these hashes (FROST's review, read by wid as an office; the runtime
never calls FROST). The list is kept APPROVED_KEEP seconds for a page's CALL (a miss asks again, once); a hire and a RUN ask
it now. A new version (new hashes) waits for its approval again.

## The card (`core_engine/preview.CARD_KEYS`, `agents/marketplace/agent.py`, the tool's `shape.CARD`)
key · number · class · name · status · pitch · price · image_dam_key · developer · type · residency · sends_to ·
data_sent · screen · product · product_slug · module. The platform's species for it is `agnt` (its card group);
`sends_to` and `data_sent` are the permission facts (Apple 5.1.1), new since the first build.

## The gate (`core_engine/gate.py`)
Shown: status LIVE, a screen, a whole mTok price, held and verified. Hireable: free, or the screen's product
subscribed. Runs: also hired and switched on. The doctor applies the same rules to a developer's card.

## The sides
rnd (the stage) and pf (live), per office, in `schemas/runtime.json`. The words agent and gate are the URL's agent
layer on the platform, not sides.
