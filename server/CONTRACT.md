# What LARRYD's runtime assumes about the platform

The platform changes; this is the whole list of what the runtime depends on, so re-aligning after a change is a diff
against this file, not a rebuild. Each line names where the assumption lives in the code. Checked against the
platform on 2026-10-05 (all held).

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
| office | door | asks | reads back |
|---|---|---|---|
| wid | GET /agnt/cards | nothing | cards: [the card, below] |
| wid | GET /agnt/hired | account, scope, member | hired: [{agent_key, board, shell_id, on, job_key}] |
| wid | POST /agnt/hire, /agnt/unhire | account, scope, member, agent_key | {shell_id, job_key, board, already} / {removed} |
| wid | GET /jobs/queued | nothing | jobs: [{account, scope, member, job_key, run}] |
| wid | GET /agnt/records/list | account, scope, member, agent_key (the agent's card key), segment, page=list, limit, offset | rows: [the record's columns], total, first: [the member's BY PRIORITY keys of this species' list, in rank order] (an agent that declares `records`; `core_engine/member_records.py` hands each ranked row its rank as `priority` 1..n, beside `key`) |
| wid | POST /agnt/records/add, /agnt/records/edit, /agnt/records/remove | account, scope, member, agent_key (the agent's card key), segment, values / key | {key} / {key} / {removed}; a refusal as {error} or {refused} (carried to the agent as `written`) |
| wid | GET /jobs/inputs | account, scope, job_key, run | inputs: {slot: value} |
| wid | POST /jobs/result | account, scope, job_key, run, state, log, delivery | {saved} |
| cc | GET /mtok/balance | account | subscriptions: [{agent_group}] |
| cc | POST /mtok/use | account, member, agent_key, job_key, agent_group, rate | {charged, free, paid_from} |
| fs | GET /agents/approved | nothing | approved: [{agent_key, code_sha256, manifest_sha256}] |
| fs | GET /agents/review_state | agent_key, code_sha256, manifest_sha256 | {state, note} |
| fs | POST /agents/submit | agent_key, name, code_sha256, manifest_sha256, manifest | the review |
| fs | GET /agents/identity | account, scope, member, job_key, run | {first_name, member_type, account_name} |
| so | POST /dam/upload | account, scope, member, job_key, run, name, content_b64, source_key | the stored file |
| lryllm | GET /larry/greeting | account, scope, member, job_key, run | the greeting |

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
