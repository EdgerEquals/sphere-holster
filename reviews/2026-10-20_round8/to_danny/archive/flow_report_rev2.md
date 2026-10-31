# Flow report: 2026-10-20_round8

Generated 2026-10-20 18:54 AWST. Files only; nothing was sent anywhere.

## Did anything reach Danny?

- Packet (to_danny/packet.md): 5 item(s) delivered: kimi.md, deepseek.md, claude.md, grok.md, claude_code.md
- Questions waiting for Danny (to_danny/questions.jsonl): 4 (from the cascade's human level; held replies are in held/ only, no queue note)
  - claude (repo): Read-only check please. (1) What is the schema of ledger/findings.jsonl (field names per line), and which script/CI job writes it? Is there any hash chaining or
  - grok (repo): Round 8 design question on integrating a review loop into the harness. Source-of-record request only — do not invent missing pieces.

What currently exists that
  - claude (rig): What fields does each line of ledger/findings.jsonl contain, and does any file or field record predictions before results or unresolved disagreements across rou
  - kimi (repo): Round 8, Q7 support — read-only rig facts needed (please answer each numbered item):

1. What is the record schema of ledger/findings.jsonl (fields, which are r

## Did anything get stopped?

- Held items: 0
- Requests stopped by budget, caps, timeouts or missing answers: none
- Tool-loop caps reached: 0
- Claude Code calls failed: 0
- Replies refused at landing: 1: kimi (reply opens as Claude Code, not Kimi)
- Model calls not made because the round total was reached: 0

## Round spend (round_budget_usd = total; fetch_budget_usd = fetches only)

- Model replies: $0.3779
- Fetches: $1.4847 of fetch_budget_usd 1.5
- Total: $1.8626 of round_budget_usd 3
- The total excludes Claude, Kimi: unpriced (unpriced_allowed), 7 call(s), 66810 input / 28040 output tokens logged, cost not counted toward round_budget_usd

### Model reply spend by model and stage

| model | stage | calls | input tokens | cached | output tokens | cost USD |
|---|---|---|---|---|---|---|
| claude | primary | 4 | 33779 | 10638 | 12891 | unpriced (excluded from total) |
| claude_code | primary | 1 | 0 | 0 | 0 | 0.2512 |
| deepseek | primary | 3 | 19516 | 12032 | 12192 | 0.0293 |
| grok | primary | 2 | 11595 | 2304 | 12937 | 0.0974 |
| kimi | primary | 3 | 33031 | 16896 | 15149 | unpriced (excluded from total) |

## Per model

| model | first request | requests | store hits | waited | not from store | answers from Claude Code (incl. via store) | decisions delivered | fetch cost USD |
|---|---|---|---|---|---|---|---|---|
| claude | primary: read_doc harness_context | 4 | 0 | 0 | 4 | 0 | 0 | 0.6084 |
| claude_code | primary: native_read **/* | 0 | 0 | 0 | 0 | 0 | 0 | 0.0000 |
| deepseek | primary: read_doc harness_context | 3 | 2 | 0 | 1 | 1 | 3 | 0.1026 |
| grok | primary: read_doc vocabulary | 3 | 2 | 0 | 1 | 0 | 0 | 0.4986 |
| kimi | primary: read_doc harness_context | 3 | 2 | 0 | 1 | 0 | 0 | 0.2752 |

## Claude Code (information switch)

- Calls: 6 (info_request 5, ping 1); ok 6, failed 0
- Tool uses: 76 (Glob 12, Read 43, Grep 21)
  - (?i)dissent|disagree|unresolved|carry.?over|carried
  - **/*
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
  - ^def |^class |round|json\.dump|metadata|meta|status|depends
- Reported cost (CLI): $1.7359

## Fetch costs (store cost records; count toward fetch_budget_usd / round_budget_usd)

- L3 Claude Code: $1.4847, 0 search credit(s)
- Total: $1.4847, 0 credit(s)
