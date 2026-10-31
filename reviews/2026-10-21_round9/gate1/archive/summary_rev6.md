# Gate 1

Predictions: **no predictions this round**

Result: no predictions this round; 1 deliver, 5 hold, 1 flagged, 0 gap(s)

| item | decision | hold reasons | flags | notes |
|---|---|---|---|---|
| kimi | hold | budget_stop | - | context first: read_doc vocabulary |
| deepseek | hold | turn_cap_reached | - | text_tool_call, turn_cap_reached; context first: read_doc vocabulary |
| claude | hold | budget_stop, turn_cap_reached | - | round_budget_usd 9.216649 reached (spent $9.3880); call_cap_reached; context first: read_doc vocabulary |
| grok | hold | budget_stop, turn_cap_reached | - | call_cap_reached; context first: read_doc vocabulary |
| build | hold | turn_cap_reached | - | turn_cap_reached; context first: read_doc vocabulary |
| claude_code | deliver | - | first_step_failure | context first: first native read was Glob /workspace/ssm-fx2/harness |

## answered_by trace (D9: conflict accepted, shown here)

| model | requests | answered by Claude Code | decisions delivered |
|---|---|---|---|
| kimi | 4 | 0 | 0 |
| deepseek | 4 | 0 | 0 |
| claude | 5 | 0 | 0 |
| grok | 2 | 0 | 0 |
| build | 2 | 0 | 0 |
| claude_code | 0 | 0 | 0 |
