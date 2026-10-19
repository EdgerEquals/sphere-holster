# Cross-model review, round 2: holster (harness) and information layer

Date: 2026-10-19, about 13:05–13:07 AWST. Subject: how the harness/information layer is designed and built, not the physics.
Same prompt to four models: `prompt.md` (question + `context_pack.md`, about 2.5k tokens). Script: `run_round.py` (reuses round 1's callers, pricing and retry logic; Kimi starts at 12000 max_tokens). Qwen and Perplexity were not sent anything.

Questions: (1) how would you optimise this design, (2) where is it weak. Limit 450 words, concrete.

| Model | id | in | cached | out | reasoning | words | s | cost |
|---|---|---|---|---|---|---|---|---|
| Claude | claude-sonnet-5-5 | 4468 | 0 | 1385 | 0 | 584 | 13.0 | $0.0228 |
| Grok | grok-4.7 | 4093 | 1152 | 1114 | 64 | 618 | 16.6 | $0.0131 |
| Kimi | kimi-k2.6 | 2780 | 0 | 3220 | 2600 | 370 | 67.8 | $0.0155 |
| DeepSeek | deepseek-flash | 2897 | 0 | 1818 | 1070 | 399 | 11.8 | $0.0015 |
| **Total** | | | | | | | | **$0.0530** |

All four replied on the first attempt, so no retries were needed. Claude (584 words) and Grok (618 words) went over the 450-word limit. "out" includes reasoning tokens where the API reports them. Claude's API does not report thinking tokens separately. DeepSeek was billed at its off-peak rate. Prices are list prices; sources are in `results.json`.

## Where they agree
- **The spec is far ahead of what's built (all 4).** The domain, knee and validation harnesses, the coordinator loop and the loss map are all unbuilt. Only the review stage exists.
- **The free tier is idle (all 4).** Move Kimi and DeepSeek into CI as a cheap pre-filter ahead of the paid reviewers, using the stored secrets.
- **The review loop doesn't close (all 4).** Round 1's findings were never filed or tracked, and reviewers aren't scored. Auto-file issues for agreed findings.
- **The seventh (information) domain has no definition (all 4).** It needs reconciling with the 6/18 in the spec and DESIGN_STATE. Claude, Grok and DeepSeek suggest adding `prompts/information.md`; Claude and Grok say it should be the ledger and loss-map role.
- **Add a handover ledger (Claude, Kimi, DeepSeek; Grok via verdict artifacts plus round.yml)** as an append-only per-round or per-SHA record.
- **Add a cost budget/cap (all 4).** All four flag Grok web search as the cost driver.
- **Keyword routing is crude and misses coupled-domain edits (Claude, Grok, DeepSeek).**
- **Coordination should move into Actions or a machine-readable state, not stay with Cursor plus prose rules (Claude, Grok, DeepSeek).**

## Where they differ
- **What to build first.** Claude and Grok want one thermal vertical slice. Kimi and DeepSeek want the validation ledger before any domain harness.
- **Triggers.** Grok wants a `harness/round.yml` to replace commit-message triggers. DeepSeek would keep them but require labels. Claude flags them as sprawl.
- **Merge gate.** Claude calls the both-PASS gate brittle and asks for quorum, retry and a human override. Kimi wants a stuck detector and escalation path. DeepSeek wants it stricter: block unless both verdicts are on the same SHA.
- **Unique points.** Claude: the four reviewers are correlated and see no solver output, and prompt injection via diffs is a risk. Grok: delete the rest of the cascade until one thermal round completes, and keep the sim stack off the audit path. DeepSeek: seed known defects to score reviewers.
