# Flow report: 2026-10-20_round8

Generated 2026-10-20 19:00 AWST. Files only; nothing was sent anywhere.

## Did anything reach Danny?

- Packet (to_danny/packet.md): 9 item(s) delivered: kimi.md, deepseek.md, claude.md, grok.md, claude_code.md, kimi_teamwork.md, deepseek_teamwork.md, grok_teamwork.md, claude_code_teamwork.md
- Questions waiting for Danny (to_danny/questions.jsonl): 5 (from the cascade's human level; held replies are in held/ only, no queue note)
  - claude (repo): Read-only check please. (1) What is the schema of ledger/findings.jsonl (field names per line), and which script/CI job writes it? Is there any hash chaining or
  - grok (repo): Round 8 design question on integrating a review loop into the harness. Source-of-record request only — do not invent missing pieces.

What currently exists that
  - claude (rig): What fields does each line of ledger/findings.jsonl contain, and does any file or field record predictions before results or unresolved disagreements across rou
  - kimi (repo): Round 8, Q7 support — read-only rig facts needed (please answer each numbered item):

1. What is the record schema of ledger/findings.jsonl (fields, which are r
  - claude (repo): Read-only check for cross-review scoring: (1) Does scripts/gate1.py exist, and does it mark items gate1_unverifiable when predictions are present and their hash

## Did anything get stopped?

- Held items: 1: claude_teamwork (budget_stop)
- Requests ending budget_stop: 1 (asked by claude)
- Tool-loop caps reached: 0
- Claude Code calls failed: 1: ee8ae984c840 claude exit 1, finish=error_max_budget_usd: 
- Replies refused at landing: 1: kimi (reply opens as Claude Code, not Kimi)
- Model calls not made because the round total was reached: 0

## Round spend (round_budget_usd = total; fetch_budget_usd = fetches only)

- Model replies: $0.9164
- Fetches: $1.5088 of fetch_budget_usd 1.5
- Total: $2.4252 of round_budget_usd 3
- The total excludes Claude, Kimi: unpriced (unpriced_allowed), 10 call(s), 149756 input / 49424 output tokens logged, cost not counted toward round_budget_usd

### Model reply spend by model and stage

| model | stage | calls | input tokens | cached | output tokens | cost USD |
|---|---|---|---|---|---|---|
| claude | primary | 4 | 33779 | 10638 | 12891 | unpriced (excluded from total) |
| claude | teamwork | 2 | 63912 | 29497 | 7936 | unpriced (excluded from total) |
| claude_code | primary | 1 | 0 | 0 | 0 | 0.2512 |
| claude_code | teamwork | 1 | 0 | 0 | 0 | 0.3090 |
| deepseek | primary | 3 | 19516 | 12032 | 12192 | 0.0293 |
| deepseek | teamwork | 1 | 19667 | 0 | 13222 | 0.0392 |
| grok | primary | 2 | 11595 | 2304 | 12937 | 0.0974 |
| grok | teamwork | 2 | 45710 | 21632 | 21896 | 0.1903 |
| kimi | primary | 3 | 33031 | 16896 | 15149 | unpriced (excluded from total) |
| kimi | teamwork | 1 | 19034 | 0 | 13448 | unpriced (excluded from total) |

## Per model

| model | first request | requests | store hits | waited | not from store | answers from Claude Code (incl. via store) | decisions delivered | fetch cost USD |
|---|---|---|---|---|---|---|---|---|
| claude | primary: read_doc harness_context; teamwork: ask_claude_code | 7 | 1 | 0 | 6 | 0 | 0 | 0.6325 |
| claude_code | primary: native_read **/*; teamwork: native_read predictions_sha256|land_review_reply|superseded|deferred | 0 | 0 | 0 | 0 | 0 | 0 | 0.0000 |
| deepseek | primary: read_doc harness_context | 3 | 2 | 0 | 1 | 1 | 3 | 0.1026 |
| grok | primary: read_doc vocabulary; teamwork: read_doc vocabulary | 5 | 4 | 0 | 1 | 0 | 0 | 0.4986 |
| kimi | primary: read_doc harness_context | 3 | 2 | 0 | 1 | 0 | 0 | 0.2752 |

## Claude Code (information switch)

- Calls: 8 (info_request 6, ping 2); ok 7, failed 1
- Tool uses: 80 (Glob 14, Read 43, Grep 23)
  - (?i)dissent|disagree|unresolved|carry.?over|carried
  - **/*
  - **/{gate1,launch_round,ledger_lib,round_config,handoff}.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/docs/harness_context.md
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/gate1.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/handoff.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/harness_router.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/harness_store.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/launch_round.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/ledger.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/ledger_commit.sh
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/ledger_costs.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/ledger_lib.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/ledger_score.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/round_config.py
  - /tmp/ensemble_cc_export/primary-20261020T103505Z-86c5ae/scripts/stage_info_costs.py
  - /workspace/ssm-fx2/harness/cc_reference/facts.jsonl
  - \bpeer|cross[- ]?scor|score each other
  - ^def |^[A-Z_]+ = 
  - ^def |^class |REQUIRED|required|KINDS|kind|append|status
- Reported cost (CLI): $2.0690

## Fetch costs (store cost records; count toward fetch_budget_usd / round_budget_usd)

- L3 Claude Code: $1.5088, 0 search credit(s)
- Total: $1.5088, 0 credit(s)
