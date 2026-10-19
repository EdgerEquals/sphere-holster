# Cross-model review, round 4: the ordering gap (issue #11), the first test run of the new holster

Date: 2026-10-19, about 14:12–14:14 AWST. Open question (verbatim from Danny): "What do you think is the best solution to the ordering gap, where the review layer is ahead of the execution layer (the harness can audit work that doesn't exist yet)?"

The prompt states the question, gives the holster context (including what was just built for #7 to #10) and fixes the format: at most 400 words, a first line `SOLUTION: <one line>`, then what, why, cost and risk. It proposes no answer.

Script: `run_round.py`, which reuses round 1's callers and round 3's helpers with the shallow caps from `harness/dial.yml`. Cheap-first order:
1. **Kimi and DeepSeek** got the context (`prompt_cheap.md`).
2. Budget check: $0.021 spent, $0.23 projected worst case, abort threshold $0.50.
3. **Claude and Grok** got the same prompt plus the cheap models' SOLUTION lines, labelled as unverified (`prompt_paid.md`). Grok was sent no tools or search_parameters.

Tavily wasn't used; Danny made it optional, and leaving it out kept outside text from steering the answers. Qwen and Perplexity were not contacted.

| Model | id | in | cached | out | reasoning | words | s | cost |
|---|---|---|---|---|---|---|---|---|
| Kimi | kimi-k2.6 | 837 | 0 | 4662 | 4355 | 244 | 118.3 | $0.0194 |
| DeepSeek | deepseek-flash | 877 | 0 | 1174 | 786 | 264 | 8.4 | $0.0017 |
| Claude | claude-sonnet-5-5 | 1539 | 0 | 957 | n/r | 458 | 10.0 | $0.0126 |
| Grok | grok-4.7 | 2185 | 1152 | 1238 | 845 | 298 | 20.2 | $0.0101 |
| **Total** | | | | | | | | **$0.0438** |

- All four replied on the first attempt.
- DeepSeek was billed at its peak rate, and Grok's API-reported cost was $0.0101.
- Claude's API doesn't report thinking tokens separately (n/r).
- Claude went over the 400-word limit.
- No model reintroduced a retired item. The automatic scan found 0 hits, and a manual read confirmed it.

## Answers (one line each; full replies in the per-model files)
- **Kimi:** CI-checked stub harnesses with locked I/O schemas. Paid reviews run only after the stub for that component has merged.
- **DeepSeek:** gate every review on a CI-signed execution receipt in the ledger. Reviews with no receipt become a separate "spec-review" class.
- **Claude:** a CI-written execution receipt in the ledger before any paid review of a component. Components without one get a cheaper "spec-review" class that is excluded from scoring. Claude partly disagrees with Kimi's stubs.
- **Grok:** gate paid review on a CI-signed receipt that the target files exist and were imported by a smoke job. Spec review stays a separate class that is not scored. Grok rejects stubs as execution.

**Agreement:** DeepSeek, Claude and Grok converge on an execution receipt written by CI into the ledger, plus a separate spec-review class. Kimi proposes stubs instead; Claude and Grok push back on that. Claude and Grok saw the cheap models' SOLUTION lines, so their answers aren't fully independent.

## Through the new holster (live test)
- **Ledger** (`ledger/findings.jsonl`): 8 records came from this round, 4 cost and 4 findings (each model's SOLUTION line, severity note). Round 3's TOP lines were added too, because the parser now reads headline lines. 99 records in total, 0 schema errors, and the append-only check passed.
- **Issue mirror:** a dry run found 0 findings at or above "major", so no issues were filed.
- **Cost rollup** (`ledger/costs_2026-10.md`): the October total is now $0.9098.

Status: Danny decides what happens next; issue #11 stays open.
