<!-- landed: reviewer=deepseek · model=deepseek-flash · channel=scripts/review_deepseek.py --ping · generated_utc=2026-10-19T16:06:14Z · source=/tmp/round7-run/deepseek/ping.json · run_id=primary-20261019T160614Z-872eec · landed_utc=2026-10-19T16:06:55Z -->

# `reviews/2026-10-19_round7/claude.md` — Claude (chat), primary reply

**Scope check:** conversation/protocol design only. No sweep, no solver runs, no `drive_4W_*`, no commits, no push. This is the reply body; filing/stamping under `reviews/2026-10-19_round7/` is the executor's job (`land_review_reply.py`), not hand-written front-matter.

**What I could not verify (marking my calibration):** I do not have `DESIGN_STATE`, `reviews/2026-10-19_round6/handoff.md`, the round-6 ledger schema, or the threshold artifact in front of me. Where my answer depends on one of those, I say so explicitly and give the reconciling step. I am not going to assert a schema I have not read.

---

## A. Sharing findings — compiled by default, threaded by exception (Q1)

**Default = compiled.** Every model writes only its own slot. A deterministic script (`scripts/compile_summary.py`, no model call) reads the slots and emits `summary.md`. Models read `summary.md`. Nobody reads a peer's full body.

**Threaded/pairwise is the exception and must be declared.** A thread opens only when a named claim-ID is in direct contradiction between two models and the escalation rule (§B) flags it. Constraints: max one round-trip, both sides cite the claim ID, and the thread must terminate by writing a conclusions block back to the slot — a thread that doesn't produce a conclusions block is discarded.

**Why this split:** the economics requirement is "paid once, reused." Four independent full contexts is the failure mode, not the baseline. But pure compiled-only loses the thing four models are for — the contradiction. So threading exists, but it is a costed, bounded, declared event rather than a side effect of everyone reading everything.

**Failure mode I'm guarding against:** consensus-by-summarization. A compiler that merges "Kimi says X, DeepSeek says not-X" into "the team discussed X" has destroyed the output. The compiler **must not resolve** — see §C.

## B. Cross-review order (Q2)

| Stage | Who | Sees | Output |
|---|---|---|---|
| A | Kimi, DeepSeek (parallel) | brief + cached context | `kimi.md`, `deepseek.md` |
| B | compiler | Stage A slots | `summary_cheap.md` — rote counts + **escalations** |
| C | Claude (chat), Grok | `summary_cheap.md` only, not peer bodies | `claude.md`, `grok.md` |
| D | compiler | all four slots | `summary.md` |
| E | all four (round-robin, claim-ID based) | `summary.md` | `*_teamwork.md` |
| F | compiler + Claude Code | scores + gate results | gate package → Edger_Equals |

**Cheap filters finish before paid models start** — that is stage B gating stage C, which is the whole point of the tiering requirement.

**"Interesting" needs a written definition or the filters will escalate everything.** Proposed criteria (escalate if any): contradicts `DESIGN_STATE` or locked geometry; proposes adding/removing/reordering a gate; introduces a new cost or billing path; is contradicted by another model's conclusion; would change round-8 launch commands or artifact paths. Rote items (typos, already-locked units, retired-item rescans) never escalate — they land as **counts plus a list** in the summary's rote section so no paid model re-derives them.

**Asymmetry I want on the record:** stage C models see cheap conclusions; cheap models do not see paid conclusions before landing. That is economically correct and epistemically unfair. Mitigation: Kimi and DeepSeek get a short "response to escalations" addendum pass after `summary.md` exists, at cheap-model rates. Without it, the cheap tier is structurally under-informed and its scores should be discounted — which nobody will remember to do.

**Round-robin coverage:** 3 targets each, 12 score blocks, cheap because conclusions-only. If cost forces partial coverage, priority order is: score the claims you escalated or that contradict your own first, then fill round-robin.

## C. Compiled context and required schema (Q3)

Produced by `scripts/compile_summary.py`, run by the executor (Claude Code CLI), **pure function of the reply files** — so `summary.md` is reproducible and diffable. A summary that cannot be regenerated cannot be audited.

**Who compiles:** a script, not a model. When two models make conflicting assertions, the compiler emits *both* under an `open_disagreements` block with a marker. It never picks a winner. Resolution belongs to a paid model or the human gate, which keeps the compiler out of an editorial role and keeps Claude Code out of it too — Claude Code already runs gate (1), and I don't want it also curating what gate (1) reads.

**Required fields per conclusion block** (this is what makes scoring work without bodies):

| Field | Why it's required |
|---|---|
| `id` | stable, citable — scores attach to claims, not to vibes about a reply |
| `claim` | one falsifiable sentence |
| `type` | `fact`/`method`/`protocol`/`cost`/`risk` |
| `evidence` | `file:line`, artifact, or `run_id`; `none — assertion` is legal but scored lower on correctness |
| `confidence` | `low`/`med`/`high` — enables the calibration check in §D |
| `asks` | what the model wants decided, or `none` |
| `scope_check` | `in-scope` / `out-of-scope-round8-deferred` / `contradicts-locked` |

Plus per-reply `## Rote` (checked-and-clean, with counts) and `## Escalations`.

**Validation as a soft pre-gate:** `scripts/validate_conclusions.py` runs at land time. A malformed block does **not** fail gate 1 (presence + stamp) — it fails gate 2, with a named reason. Otherwise the compiler silently drops a model and gate 2 passes on three voices, which is worse than a loud failure.

**ID stability:** add a content-hash suffix to claim IDs. Without it, round 8 re-litigates round 6 and the ledger cannot show a claim was already settled.

## D. Peer scoring in practice (Q4)

**Axes** (1–5 each, plus a required `disagreements` list of claim IDs and a free-text `why`):

- `correctness` — survives check against `DESIGN_STATE` / artifacts
- `aim_fit` — moves the program's aim, not just the round
- `economics` — respects tiered / cached / batched constraints
- `actionability` — convertible into a launch command or a decision

Plus a boolean `calibration_penalty`: stated confidence vs. evidence tier. Marked as **proposed** — must be reconciled against round 6's actual axes before anything lands in the ledger, or the ledger forks and peer scores stop being comparable across rounds.

**Anti-self-scoring is mechanical, not honor-system:** `validate_conclusions.py` rejects any score whose `scorer == target_model`. A reply containing a score of its own claim is malformed and fails gate 2 under §C.

**Where filed:** `ledger/pending/<round>_peer_scores.jsonl`, one line per (scorer, target claim ID, axes, note). Round-6 threshold scores and round-7 protocol scores use the **same** line schema, retroactively, so there is one ledger format. Promotion out of `pending/` is a human-gate action.

## E. Automated gate placement + anti-self-check rule (Q5)

Gate (1) sits between "claim landed" and "feedback fans out" — not outside the conversation. Four rules:

1. **Provenance tag on every claim** (`kimi`/`deepseek`/`claude-chat`/`grok`/`claude-code`). The gate **refuses to auto-pass** `claude-chat` or `claude-code` provenance. Those route to a mandatory non-Claude check: Grok as paid cross-check, or Kimi/DeepSeek recompute as cheap cross-check.
2. **Prediction before result, timestamped by the gate process, not the model.** `{claim_id, predicted_value, tolerance, gate_ts}` in `ledger/pending/predictions/`. A result with no prior prediction is a `NO_PREDICTION` rejection, not a pass. This makes the gate auditable even for non-Claude claims, and it makes "prediction before result" verifiable rather than asserted.
3. **Executor ≠ checker.** `gate_check.py --claim <id>` writes `checked_by: <model>`; a line whose `checked_by` equals the claim's provenance owner is invalid and must not be promoted.
4. **Threshold version recorded.** Gate (1) reads the threshold from round 6's artifact and stamps `threshold_version` on every result, so results stay reproducible after Edger_Equals revises it.

**Human gate sees the asymmetry:** every Claude-origin row carries `self_checked: false` and the name of whoever covered it. This does not add a third gate; it makes gate (1) honest about its own blind spot.

## F. Human-gate package (Q6)

One page plus machine file. `gate_package.md` (a single deviation table, worst-first) + `gate_package.jsonl`. Per recommendation:

`claim_id`, `provenance`, one-sentence recommendation, prediction (value/tolerance/`gate_ts`), result (value/artifact/`run_id`/`checked_by`), deviation vs threshold → `pass`/`fail`/`indeterminate`, `self_checked` + coverer, peer score mean and spread per axis with dissents cited by claim ID, proposed feedback action if fail, cost estimate of the next step.

Plus a **"what changed since the last package"** section — without it the human gate re-reads the same unpassed rows every round and stops reading.

**Held until sign-off:** ledger lines stay in `pending/`; no fan-out; the next round's launch command is *written but not executed*. The one-pager links to full dumps rather than containing them. Edger_Equals must be able to reject with a reason code that re-enters as a claim, not as prose.

## G. Our aim, in my own words (Q7)

The aim is a loop where four models with genuinely different failure modes produce decisions — protocol now, measurement later — that none of them would reach alone, at a cost that stays below the value of those decisions, with every claim traceable to an artifact and every irreversible step (a sweep, a feedback fan-out) blocked behind a human who sees the gap between prediction and result rather than a pile of prose. Consensus is not the aim. Cheap disagreement surfaced early and expensive agreement verified late is the aim. If the loop produces agreement faster than it produces checked predictions, it has failed quietly.

## H. Improvements against that aim (Q8)

1. **Cost ledger, not a cost policy.** The economics table is requirements without measurement. Add `ledger/pending/costs.jsonl` keyed by `run_id`; otherwise "cached shared context" is an assertion and the protocol can never show it saved anything.
2. **Escalation budget.** Cap escalations per round (N, set by the human gate). Uncapped, filters escalate everything and the tiering is decorative. Overflow goes to Edger_Equals as a list, not to paid models.
3. **Compiler fixtures in `tests/`.** The compiler is now in the scoring trust path. 3 good + 3 malformed replies as fixtures, or a schema change silently moves scores.
4. **Round-6 summary backfill.** `launch_round.py` still injects full bodies. Add `--teamwork-summary` and backfill round 6 first, so conclusions-only mode is not also the compiler's first live run.
5. **Retired-item guard as a compiler rule.** Hard-flag any conclusion matching the retired list at compile time. Reviewers spending paid tokens re-discovering a retired item is the cheapest bug in this design.
6. **Pre-register the round-8 launch command in `protocol.md`.** Approval should be approval of a *specific command and artifact paths*, not of a category of action. This is what makes the round-8 hold enforceable rather than aspirational.
7. **`open_disagreements` must survive into round 8.** Carry unresolved dissent forward explicitly. Summarization that erases dissent is the most likely way this program pays for four models and gets one.
8. **Design decision worth challenging in the kickoff itself:** the "conclusions-only" default was adopted from round 6 without a compiler existing. That is a decision made before its own precondition. Items 3–4 are the cost of that ordering, and I'd rather pay it than revert.

---

## Holds / what I'm not doing

Not drafting `protocol.md` — that comes after debate, and I'm one of four voices. Not cross-reviewing until the other three land and `summary.md` exists; scoring from this kickoff alone would be scoring the brief. Not committing or pushing without instruction.

**Open question for the caller:** whether stage-C asymmetry (§B) is accepted as-is, or whether Kimi/DeepSeek get the post-`summary.md` addendum pass. That decision changes whether cheap-tier scores are comparable to paid-tier scores, and it should be settled before round 7 closes rather than discovered in round 8.
