# Flow report: 2026-10-21_round9

Generated 2026-10-21 13:48 AWST. Files only; nothing was sent anywhere.

## Did anything reach Danny?

- Packet (to_danny/packet.md): 1 item(s) delivered: claude_code.md
- Questions waiting for Danny (to_danny/questions.jsonl): 0 (from the cascade's human level; held replies are in held/ only, no queue note)

## Did anything get stopped?

- Held items: 4: kimi (budget_stop); deepseek (turn_cap_reached); grok (budget_stop, turn_cap_reached); build (turn_cap_reached)
- Requests stopped by budget, caps, timeouts or missing answers: none
- Tool-loop caps reached: 6: build primary turn_cap_reached; deepseek primary turn_cap_reached; deepseek primary text_tool_call; claude primary call_cap_reached; grok primary call_cap_reached; build primary turn_cap_reached
- Claude Code calls failed: 0
- Replies refused at landing: 0
- Model calls not made because the round total was reached: 2: kimi primary; grok primary

## Round spend (round_budget_usd = total; fetch_budget_usd = fetches only)

- Model replies: $5.2166
- Fetches: $0.0000 of fetch_budget_usd 1.5
- Total: $5.2166 of round_budget_usd 5.383321

### Model reply spend by model and stage

| model | stage | calls | input tokens | cached | output tokens | cost USD |
|---|---|---|---|---|---|---|
| build | primary | 37 | 1201347 | 1007936 | 23943 | 0.4429 |
| claude | primary | 10 | 470768 | 27108 | 7246 | 1.9280 |
| claude_code | primary | 1 | 254018 | 197270 | 10984 | 0.5429 |
| deepseek | primary | 42 | 1923207 | 1696000 | 48270 | 0.1486 |
| grok | primary | 23 | 1291257 | 1053440 | 31490 | 1.1913 |
| kimi | primary | 18 | 682204 | 546048 | 26049 | 0.9630 |

## Per model

| model | first request | requests | store hits | waited | not from store | answers from Claude Code (incl. via store) | decisions delivered | fetch cost USD |
|---|---|---|---|---|---|---|---|---|
| build | primary: read_doc vocabulary | 2 | 2 | 0 | 0 | 0 | 0 | 0.0000 |
| claude | primary: read_doc vocabulary | 2 | 1 | 0 | 1 | 0 | 0 | 0.0000 |
| claude_code | primary: native_read **/vocabulary.md | 0 | 0 | 0 | 0 | 0 | 0 | 0.0000 |
| deepseek | primary: read_doc vocabulary | 4 | 3 | 0 | 1 | 0 | 0 | 0.0000 |
| grok | primary: read_doc vocabulary | 2 | 2 | 0 | 0 | 0 | 0 | 0.0000 |
| kimi | primary: read_doc vocabulary | 4 | 4 | 0 | 0 | 0 | 0 | 0.0000 |

## Code folder reads (read_file / search_code; counted only, no cost)

| model | read_file | search_code | characters returned | files touched |
|---|---|---|---|---|
| build | 22 | 14 | 252400 | 6 |
| claude | 10 | 8 | 99547 | 4 |
| deepseek | 36 | 34 | 463926 | 5 |
| grok | 23 | 36 | 366196 | 6 |
| kimi | 25 | 15 | 295493 | 5 |

## Claude Code (information switch)

- Calls: 1 (ping 1); ok 1, failed 0
- Tool uses: 18 (Glob 5, Read 11, Grep 2)
  - *
  - **/*
  - **/MAP.md
  - **/vocabulary.md
  - /tmp/ensemble_cc_export/primary-20261021T050438Z-7c9a22/MAP.md
  - /tmp/ensemble_cc_export/primary-20261021T050438Z-7c9a22/docs/harness_context.md
  - /tmp/ensemble_cc_export/primary-20261021T050438Z-7c9a22/docs/vocabulary.md
  - /tmp/ensemble_cc_export/primary-20261021T050438Z-7c9a22/solver_v0.py
  - /tmp/ensemble_cc_export/primary-20261021T050438Z-7c9a22/tests/test_drive_1W.py
  - /workspace/ssm-fx2/harness/cc_reference/facts.jsonl
  - ^EL_SIGMA|^BTO_T|run_case\(|"bto":.*eps|def el_eps|add_argument
  - drive_W|DRIVE_THERMAL_ENVELOPE_Hz|drive_4W|gas_Q\(|gas_linewidth\(|def el_sigma|class ElectricMarch|def chem_state|def make_grid|def all_modes_stats|def sum_over_modes|def gas_T_profile|ohm
  - {MAP.md,DESIGN_STATE.md,docs/**}
- Reported cost (CLI): $0.5429

## Fetch costs (store cost records; count toward fetch_budget_usd / round_budget_usd)

- none
- Total: $0.0000, 0 credit(s)
