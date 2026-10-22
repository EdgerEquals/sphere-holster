# Gate 1

Predictions: **no predictions this round**

Result: no predictions this round; 1 deliver, 4 hold, 1 flagged, 1 gap(s)

| item | decision | hold reasons | flags | notes |
|---|---|---|---|---|
| kimi | hold | budget_stop | - | context first: read_doc vocabulary |
| deepseek | hold | turn_cap_reached | - | text_tool_call, turn_cap_reached; context first: read_doc vocabulary |
| grok | hold | budget_stop, turn_cap_reached | - | round_budget_usd 3 reached (spent $3.2740); call_cap_reached; context first: read_doc vocabulary |
| build | hold | turn_cap_reached | - | turn_cap_reached; context first: read_doc vocabulary |
| claude_code | deliver | - | first_step_failure | context first: first native read was Glob /workspace/ssm-fx2/harness |

## answered_by trace (D9: conflict accepted, shown here)

| model | requests | answered by Claude Code | decisions delivered |
|---|---|---|---|
| kimi | 4 | 0 | 0 |
| deepseek | 3 | 0 | 0 |
| claude | 2 | 0 | 0 |
| grok | 1 | 0 | 0 |
| build | 2 | 0 | 0 |
| claude_code | 0 | 0 | 0 |

## Gaps

- {"stage": "primary", "item_id": "claude", "gap": "no reply landed"}
