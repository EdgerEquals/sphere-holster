# Round 2 — Claude (claude-sonnet-5-5)

max_tokens 6000, started 2026-10-19T05:06:06+00:00 UTC, 13.0 s. Tokens in 4468 (cached 0), out 1385 (reasoning 0), 584 words. Cost $0.0228.

Raw reply, verbatim:

---

**1. Optimisation**

- **Make GitHub state the coordinator, not Cursor.** Cursor is an IDE with no scheduler or trigger surface. Build the coordinator as a small Python script run by a `coordinator.yml` workflow (`workflow_dispatch` plus `repository_dispatch`). It would read `dial.yml`, fan out domain jobs by matrix, merge, and emit one `round-N.json`. Cursor stays the editor and writes only to branches.
- **Build one thin vertical slice before the 18 harnesses.** Take thermal, with the chemical→thermal handover. Run two rounds end to end: harness → merge → Claude and Grok → verdict → handover log. This tests the loop and the merge, which the spec names as the biggest risk. Don't scaffold the knee harnesses until it works.
- **Replace the validation harness with a handover ledger.** An append-only `harness/ledger.jsonl` (from, to, sha, artifact, verdict, timestamp) written by `review-core.yml`. It needs no model and is queryable, which fits "tracks, doesn't check".
- **Close the review-round loop.** Round 1 produced four agreed findings that are still unactioned. Add a script that dedups findings across models and files issues labelled `finding:consensus-4/4`. Then run a weekly check on whether DESIGN_STATE changed. Score reviewers by agreement and by findings later accepted.
- **Cut cost and noise.** Run the deterministic `retired.txt` scan and pytest first, and skip the API when they fail. Cache by diff hash. Add the missing "radial diamond spokes" regex. Put a monthly budget in `dial.yml` and have the workflow abort at the cap. Grok web search is the cost driver at ~10× Claude, so gate it on `[calc]`/`[lit]` tags rather than running it on every diff.
- **Automate the free tier.** Move Kimi and DeepSeek into a `free-check.yml` for rote checks (units, arithmetic). Use them as a cheap pre-filter before the paid reviewers. Today the secrets are stored but unused.
- **Settle the seventh domain now.** Define the "information" domain as the ledger and loss-map domain, since it is meta, and add its prompt. Reconcile 6/7 and 18/19 in DESIGN_STATE and the spec.

**2. Weaknesses**

- **The built layer is only the review stage.** The harnesses, coordinator, loss map and convergence loop do not exist. The "mirrors the physics cascade" claim is therefore untested, and the design is ahead of the evidence.
- **Reviewers are correlated and ungrounded.** All four models read the same prose and agree because the document is incoherent, which says little about physics correctness. The CI tests check only locked values against the doc. No harness runs `solver_v0.py` or the sim-stack tools, so the engineering tools never touch the model.
- **The both-PASS gate is brittle.** Any non-PASS fails the job, so one flaky or ERROR verdict blocks a merge. There is no retry or quorum policy and no human override path. The reverse risk is that two LLM PASSes become false assurance.
- **The domain-routing keyword match is crude.** It will miss cross-domain edits, which are exactly the coupled cases that matter.
- **Trigger sprawl.** `[audit]` and `[round N]` in commit messages, `/commands`, `@claude` and AGENTS.md rules all depend on discipline. Cursor can forget a handoff, and nothing enforces it.
- **Single point of truth drift.** DESIGN_STATE.md is hand-edited, and `retired.txt`, `locked_values.yml` and the spec each duplicate parts of it.
- **Security.** Comment-triggered workflows hold paid secrets. The collaborator check helps, but prompt injection through diffs can reach the reviewers, and Grok has web access.
- **Unsettled tier names.** "Plex", the Bot, ChatGPT and Qwen are named but not connected, and the tier ladder differs between the spec and Danny's framing.
