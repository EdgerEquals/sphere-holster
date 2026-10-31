# Gate 1

Predictions: **no predictions this round**

Result: no predictions this round; 9 deliver, 1 hold, 5 flagged, 0 gap(s)

| item | decision | hold reasons | flags | notes |
|---|---|---|---|---|
| kimi | deliver | - | - | context first: read_doc harness_context |
| deepseek | deliver | - | - | context first: read_doc harness_context |
| claude | deliver | - | - | context first: read_doc harness_context |
| grok | deliver | - | - | context first: read_doc vocabulary |
| claude_code | deliver | - | first_step_failure | context first: first native read was Glob /workspace/ssm-fx2/harness/cc_reference |
| kimi_teamwork | deliver | - | first_step_failure | context first: no requests made |
| deepseek_teamwork | deliver | - | first_step_failure | context first: no requests made |
| claude_teamwork | hold | budget_stop | first_step_failure | context first: first request was ask_claude_code {"question": "Read-only check for cross-review scoring: (1) Does scripts/gate1.py exist, and does it mark items gate1_un |
| grok_teamwork | deliver | - | - | context first: read_doc vocabulary |
| claude_code_teamwork | deliver | - | first_step_failure | context first: first native read was Grep /tmp/ensemble_cc_export/teamwork-20261020T105433Z-2b3358 |

## answered_by trace (D9: conflict accepted, shown here)

| model | requests | answered by Claude Code | decisions delivered |
|---|---|---|---|
| kimi | 3 | 0 | 0 |
| deepseek | 3 | 1 | 3 |
| claude | 7 | 0 | 0 |
| grok | 5 | 0 | 0 |
| claude_code | 0 | 0 | 0 |
