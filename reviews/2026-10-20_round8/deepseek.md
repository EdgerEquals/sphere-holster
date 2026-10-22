<!-- landed: reviewer=deepseek · model=deepseek-v4-pro · channel=scripts/review_deepseek.py --ping · generated_utc=2026-10-20T10:35:05Z · source=/tmp/r8_fire_2026-10-20/deepseek/ping.json · run_id=primary-20261020T103505Z-86c5ae · landed_utc=2026-10-20T10:38:08Z · finish=stop -->

# DeepSeek — Round 8 design answers

## Q1 — Numeric cutoffs vs named parameters (the rule that governs everything below)

**I choose: allow named parameters, ban invented numeric thresholds.**

- A **named parameter** is a symbol like `HP:min_peer_scores` whose value is **unset and reserved for the human layer**. The design may reference it freely; the design may not invent its value.
- A **measured count** is a number computed from the record itself (number of items in the round, number of peer scores actually submitted, number of open disagreements). Measured counts are allowed, because they are facts, not cutoffs.
- A **universal** ("every", "all", "none", "any") over the record is allowed.
- If a stage needs a parameter whose value the human has not set, the stage does **not** invent a default. It reports `value_unset` and holds the affected item as `gate1_unverifiable`.

No literal invented threshold appears anywhere below. Every decision cutoff is a named parameter; every other count is measured or universal.

---

## Q2 — Single-item hard block

**Scoped hold, not whole-round hold.**

A hard block on item X holds:

1. item X itself, and
2. every item that **depends on** X, where dependency is read mechanically from a mandatory `depends_on` field in each recommendation record (a list of item IDs the recommendation cites or uses).

Items with no dependency path to X proceed through the gates normally. The round summary shows the blocked subgraph and the unaffected items separately, so the hold's blast radius is visible.

- `depends_on` is mandatory. If it is missing or malformed, **that item only** is held as `gate1_unverifiable`; the defect does not expand the blast radius to the whole round.
- Whole-round hold would let one item stall unrelated findings and would make the hold signal too coarse. Scoped hold keeps the severity attached to the actual dependency.

---

## Q3 — Peer scoring and gate 1

**If peer scores are required before gate 1 can pass an item, that is part of gate 1, not a third gate.**

A gate is a **decision authority** — it can hold or release a finding. Peer scores do not have independent hold/release authority. They are **inputs** to gate 1's single pass/fail decision, the same way a preflight check is a stage inside one go/no-go rather than a separate launch.

Mechanically, gate 1's per-item pass condition becomes:

- a prediction was recorded before the result existed, and its hash is intact;
- the result is present;
- the gap (prediction vs result) is computed;
- the required peer scores are present (how many is the named parameter `HP:min_peer_scores`).

If the peer-score condition fails, the item is held as `gate1_hold_peer_scores` — a hold **inside** gate 1. The gate count stays at the two gates named in the brief, and the human gate remains the only downstream gate.

---

## Q4 — Carrying disagreements forward

Disagreements live in an append-only **disagreement index** (`ledger/disagreements.jsonl`, keyed by `disagreement_id` and `item_id`). Carrying forward is automatic: each round's hand-off includes the **full open index**, not just new entries. A disagreement is closed only by an explicit close record with a reason (`resolved` / `superseded` / `dropped`) and a citation of what changed. There is no silent drop.

Each disagreement record must contain:

- `disagreement_id` — a content-addressed hash of (item, parties, positions), so the record cannot be quietly edited;
- `item_id`, `round_id` where it arose;
- `parties` — who disagrees with whom;
- `positions` — the recommendation position and **every** dissenting position, in each party's own words;
- `evidence_refs` — paths or ledger IDs, not prose summaries;
- `resolution_condition` — a prediction or test that would settle it, written so it is checkable;
- `status` — `open` / `resolved` / `superseded` / `dropped`;
- `first_seen_round`, `last_seen_round`, `history` — an append-only list of the round IDs where it was carried;
- `depends_on` — so a disagreement's blast radius can be scoped the same way as Q2.

**Traceability check (mechanical):** a script verifies that every record with `status == open` appears in every subsequent round's hand-off index until a close record exists. If an open disagreement is absent from a later hand-off without a close record, gate 1 marks that round's package `gate1_refused`. Dissent stays visible and traceable across rounds, and its absence is itself a gate-1 failure.

---

## Q5 — Falsifying the approach

The falsification tests run entirely on the tamper-evident, append-only prediction record:

- **Integrity.** Hash-chain the prediction ledger (the repo already locks a per-round predictions hash). If the chain breaks, or any prediction's recorded time is **after** its result's recorded time, the prediction did not precede the result, and the approach is falsified for those items.
- **Falsifiability.** Every prediction must state, machine-readably, what observable would count as a hit and what as a miss. If the record is dominated by predictions that can never be scored, the loop is not working.
- **Discriminative power (the key test).** Compare the recorded predictions against a null model computed from the same record: "predict whatever the recommendation itself asserts." If the predictions do not beat the null model's hit rate by more than `HP:min_edge` (human-reserved margin), gate 1 adds cost without adding information — the loop is re-endorsing recommendations.
- **Calibration.** If predictions carry confidence, bucket them (bucket boundaries are human-reserved parameters) and check that within each bucket the observed hit rate matches the stated confidence. Systematic miscalibration shows the predictions are not honest measures of what the team knows.
- **No self-fulfilling drift.** Check that a prediction is distinguishable from its recommendation. If predictions and recommendations are near-duplicates above `HP:max_similarity` (human-reserved threshold), the record contains recommendations wearing a prediction's clothes.

Any of integrity failure, unfalsifiable predictions dominating the record, no edge over the null model, or miscalibration — measured on the record — shows the whole approach is not working.

---

## Q6 — Final pre-human gate

The last gate before the human gate (the end of gate 1) must decide, per item, exactly one of:

- `release` — the check is complete, the gap package is well-formed, and the item is safe to hand off;
- `hold` — held with a machine-readable reason (missing prediction, missing result, hash mismatch, missing peer scores, hard-blocked, dependency-blocked, disagreement index incomplete).

What gets pushed through to the human:

- **Per item:** item ID, recommendation text, the recorded prediction, the result, the computed gap, peer scores with their authors, hard-block flags, dependency edges, and the item's open disagreements.
- **Round level:** the full open-disagreement index, the blocked-subgraph summary, and the gate-1 verdict summary.
- **Format:** canonical machine-readable JSON Lines, content-addressed and hash-chained, plus a generated human-readable `summary.md`. The summary is derived and must not contain claims absent from the machine part.

What is held back: raw model chatter, drafts, and anything that would anchor the human before the gap is visible. Held-back material is **not deleted** — it stays parked in the per-round store and is retrievable if the human asks.

The final pre-human gate does **not** decide whether a recommendation is right. It decides only whether the package is complete and trustworthy enough to hand off.

---

## Q7 — Integrating into the harness

Grounded in what exists (harness context plus a live rig check):

- `scripts/gate1.py` already exists and reads `<round-dir>/predictions.jsonl`, writes `gate1/{summary.md,items.jsonl,gaps.jsonl}`.
- `scripts/launch_round.py` already locks `predictions_sha256` into `run.json` at fire time.
- Peer scoring already exists as the teamwork cross-review: each model gives peers PASS/FAIL with a one-line reason, landing as `{model}_teamwork.md`.
- `scripts/ledger.py` / `ledger_lib.py` hold review findings; `scripts/ledger_score.py` scores reviewers against planted mistakes.
- The information layer (`harness_router.py`, `harness_store.py`) provides the shared store, cascade, and waiters queue.

**Recommended integration (small diffs to what exists):**

1. Add `ledger/predictions.jsonl` (append-only, hash-chained) and a writer step that records each recommendation's prediction **before the round fires**. Point the existing per-round lock at this ledger's round slice.
2. Build the actual recommendation-vs-prediction check inside `gate1.py`. Today it only verifies the file hash and marks items `gate1_unverifiable`. The gap should be computed by a mechanical differ (field-by-field for structured predictions; similarity/negation for prose), not by a model's judgment.
3. Feed peer scores into gate 1 as structured inputs: parse `{model}_teamwork.md` PASS/FAIL lines into `gate1/items.jsonl` as the peer-score evidence, with `HP:min_peer_scores` enforced as a precondition inside gate 1.
4. Route disagreement records through `ledger/disagreements.jsonl`, with the carry-forward check run as a small sibling script before release.
5. Reuse the information layer as-is: gate 1 and the ledger scripts fetch through the router/store, so they inherit the waiters queue and parked results without a new fetch path.
6. Write gate results to the existing findings ledger with `type: gate1`, so `ledger.py` and the cost rollups can report them without inventing a new ledger format.

**Missing today (stated, not guessed):** there is no code that writes or records predictions; the recommendation-vs-prediction comparison step is not built; and peer scoring exists only as free-text PASS/FAIL with no structured per-item binding. An integration plan must fill those three gaps.

---

## Q8 — The safeguard role (optional game/test — answering because it was offered)

**Test: "Checker's Two Hats."**

Setup: each candidate plays two separated roles. In the **Author** phase they write a recommendation and a prediction. In the **Checker** phase they receive a package containing their own item, other candidates' items, and planted traps: missing predictions, hash mismatches, post-hoc predictions, and near-duplicate prediction/recommendation pairs. The candidate does not know which items are traps.

The test measures:

- **Uniformity** — does the candidate apply the same pass/hold rules to their own item as to items with identical planted defects?
- **Trap detection** — does the candidate catch every planted integrity and falsifiability trap?
- **No self-exemption** — does the candidate ever pass their own item with a defect they held on another's?
- **Gap reporting** — does the candidate report the gap as the gap, or spin it into a story favouring their own recommendation?

**Result that would make me trust it:** a candidate catches every planted trap of the types they were told to catch, applies the same standard to their own item and others' (no self-exemptions across the whole run), and reports gaps without spinning. Any candidate who passes a planted trap or treats their own work more leniently has demonstrated the exact conflict the safeguard role must not have.

---

## Standing observation 1 — Self-reference: stability vs drift

What would show stability rather than drift: a **constitution snapshot** — a content-addressed hash of the loop's own definitions: glossary terms, gate names, gate semantics, and the names of all human-reserved parameters. Each round, a script hashes this snapshot and compares it to the previous round.

- **Stability** = the schema hash is unchanged unless there is an explicit, human-approved amendment record with a diff.
- **Drift** = terms redefined (same word, different meaning), gate semantics shifted, or parameter names changed or revalued without an amendment.

Additionally, predictions must be made against a rubric whose hash is unchanged between prediction and result. If the rubric drifts after the prediction, gate 1 flags the item `gate1_refused` — the goalposts moved.

The clean-slate rule resets **content**, not **constitution**. This test distinguishes a content reset (fine) from constitutional drift (not fine).

---

## Standing observation 2 — Convergence: robustness vs echoing

Convergence is robust when independent paths reach the same decision set. Mechanical proxies:

- **Justification diversity:** the converging replies cite different reasons, examples, and failure modes. Same decision set + different justifications = robustness.
- **Error independence:** the converging replies do not share distinctive errors. Shared wrong facts or shared odd phrasings = echoing.
- **Perturbation test:** re-run the question with names and examples perturbed. If the design choice survives, the convergence is on content; if it evaporates when the words change, it was cue-following.
- **Adversarial decoy:** plant a tempting wrong answer in a decoy brief. If the models adopt the decoy, they are echoing the brief, not converging on the design.

**Trust result:** robustness is shown when the decision set survives perturbation and the justifications are diverse and error-independent. Echoing is shown when shared-text similarity exceeds `HP:max_similarity` (the same human-reserved parameter from Q5) while justifications are interchangeable.

---

## Standing observation 3 — The undefined human gate

The asymmetry forces everything before the hand-off to be designed against an **unknown consumer**. The hand-off must therefore be a self-describing contract: complete, provenance-carrying, and queryable, rather than a bespoke report tuned to a known downstream decision.

- **Strength:** it stops the models from optimizing the package to please a predictable human gate, and forces every decision to justify itself in the package.
- **Risk:** the package might omit something the human later needs, or each model might privately guess the human gate's shape and shape the package to that guess.

**Mitigation that stays on the correct side of the line:** define only the hand-off contract (schema, provenance, completeness checks), keep held-back material parked and retrievable, and prohibit the pre-human stages from deciding anything that belongs to the human gate. I do not propose what the human gate decides.

---

## Standing observation 4 — Cost visibility

Make the loop's cost visible and comparable round to round by **per-stage, per-round attribution** and **stable denominators**.

The repo already has monthly cost rollups and cached-token accounting. Add per-round, per-stage attribution: fetch, model reply, peer scoring, gate 1, ledger writes. Each stage writes its token and dollar cost into a per-round cost record.

Normalize by **measured** denominators from the record: cost per item that reached gate 1, cost per released finding, cost per open disagreement carried, cost per prediction made. Compare round to round with the same schema and the same denominators, so the value question becomes mechanical: did the loop's findings change anything per unit cost?

The cost hierarchy's cheaper-agent routing is already designed into the harness; per-stage attribution makes that routing **auditable** — it shows whether the cheap agent was actually used for searches. No cutoff is needed; if a "good/bad value" comparison is ever wanted, its threshold is a human-reserved parameter, not a number I invent here.
