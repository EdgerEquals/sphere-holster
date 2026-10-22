<!-- landed: reviewer=kimi · model=kimi-k3 · channel=scripts/review_kimi.py --ping · generated_utc=2026-10-20T10:35:05Z · source=/tmp/r8_fire_2026-10-20/kimi/ping.json · run_id=primary-20261020T103505Z-86c5ae · landed_utc=2026-10-20T10:54:22Z · finish=stop -->

Claude Code's answer is queued behind the human layer (`pending_human`), so per Q7's own rule — *say what is missing rather than guessing* — I will design Q7 conditionally on the six facts I asked for, using only the parked harness-context document as rig fact. Full reply follows.

---

# Kimi — Round 8 reply

**Conventions used throughout, so cross-reviewers can audit me:**
- Every decision-relevant count, cutoff, window or quorum in my design is a **named parameter** written `P_LIKE_THIS`, per my answer to Q1. All are collected in the registry at the end, every value marked `RESERVED-HUMAN`.
- Numbers that merely *index* something already enumerated by the brief (Gate 1, Gate 2, Round 8, Q1–Q8) are identifiers, not thresholds, and are exempt from the parameter rule.
- Terms I coin — *gap package*, *dissent manifest*, *scoped hold*, *locked prediction*, *packet* — are **proposed terms only**; per §2 they do not enter the glossary without human-layer approval.

---

## Q1 [HIGH CUE] — Numeric cutoffs vs named parameters

**Both, and they are the same rule:** named parameters are the *only legal form* a threshold may take; bare invented thresholds are banned.

The rule, mechanically statable so a linter can enforce it:

> Any number appearing in a process rule where changing the number would change a process outcome (pass/hold, include/exclude, open/close, appoint/not) must be a reference to an entry in a parameter registry. Bare numeric literals in such positions are a build error. Registry entries are created with value `RESERVED-HUMAN`; only the human layer may set them.

Two load-bearing details:

1. **Fail-closed on unset values.** A script that needs an unset parameter must not default it. It returns a first-class outcome `UNSET`, and the item is packaged for the human with the missing parameter flagged. This converts the temptation to invent a threshold into explicit human homework, and makes every missing human decision *visible as a list* rather than silently absorbed.
2. **Identifier exemption.** Definitional indices (gate numbers, round numbers) and enumerations of criteria are not thresholds. The linter only scans rule-bearing sentences (those containing conditional or comparative logic) for bare numerals, so enforcement is a grep-class check, not a judgement call.

I apply this to every count in this reply; see the registry and self-audit at the end.

## Q2 [HIGH CUE] — Single-item hard block

**Scoped hold, by default and mechanically.** A hard block holds the blocked item plus its **dependency closure** — every item whose declared `depends_on` metadata reaches the blocked item — and nothing else. The rest of the round proceeds to the hand-off.

Design:

- Each item carries a machine-readable `depends_on` list (item IDs). Closure computation is graph traversal — fully scriptable, no judgement.
- A hard block requires a reason code from `P_HOLD_REASON_CODES` (an enumerated, human-extensible list) and is appended to the ledger. A block without a valid reason code is rejected by the linter.
- The blocked item and its closure do **not** vanish: they travel to the human as a *held annex* — visible, with reasons, clearly marked as not having passed. Holding must never be deleting.
- The scope itself is a parameter: `P_HOLD_SCOPE ∈ {item, item+closure, round}`, proposed default `item+closure`. If the human prefers whole-round holds, that is one registry edit, not a redesign.

Edge case, honestly stated: in a densely connected round, the closure may be most of the round, and a scoped hold approximates a round hold. That is not a flaw — the dependency graph makes the blast radius *visible and auditable* instead of political. The thing Q2 should prevent is one item wielding an *invisible, unaccountable* veto over unrelated work.

## Q3 [HIGH CUE] — Peer scoring and gate 1

**Part of gate 1 — as an input requirement, not a decision — and here is the criterion that makes that answer more than a naming choice.**

Define a gate by what it has: **blocking authority of its own, a single accountable executor, and its own logged decision record.** Peer scoring has none of these. It produces evidence; it cannot pass or hold anything; it has no executor and no decision record. Gate 1 consumes peer scores the way it consumes the locked prediction: as a required field.

So:

- If "required before gate 1 can pass" means *the scores must exist and be schema-valid*, that is a **precondition inside gate 1** — one pipeline stage, one executor, one log entry. Not a third gate. A missing-input block is still gate 1's block.
- It becomes a **de facto third gate** the moment a *judgement* about scores decides the outcome — e.g., "pass only if the mean peer score exceeds a cutoff." At that point someone is deciding, and calling it "part of gate 1" smuggles an unaccountable decision point into the record. The fix is not to re-name it but to mechanise it: any score-aggregation rule must be expressed in named parameters (`P_SCORE_AGG_RULE`) and executed by the same script as the rest of gate 1, which collapses it back into gate 1 legitimately.

Why the distinction matters: it determines who executes (and therefore where the Q8 conflict of interest lives), and it determines auditability — one gate, one record, one accountable executor. Function over labels: a third gate that we *call* part of gate 1 is still a third gate in every way that can hurt us.

## Q4 [MIDDLE] — Carrying disagreements forward

**One sanctioned channel, machine-readable, append-only — and it is the single, explicit exception to the clean-slate rule.**

Clean start (§3) forbids conversational carry-over: quoting earlier replies, scores, tallies. It cannot forbid *data* carry-over, or Q4 is unanswerable. So the design declares exactly one bridge between rounds: the ledger. Everything else stays clean.

**The dissent record** (a queryable view over the append-only findings ledger, which fits the existing `ledger/findings.jsonl` shape). Required fields — all script-validatable:

| Field | Content |
|---|---|
| `dissent_id` | Unique, permanent |
| `round_raised` | Round identifier |
| `item_refs` | The item(s) the disagreement attaches to |
| `positions` | Per-holder structured claims: who holds what, with evidence references (ledger IDs, not prose quotes) |
| `status` | `open` / `carried` / `resolved` / `withdrawn` |
| `status_history` | Append-only list of transitions, each with round and reason |
| `resolution_ref` | Ledger reference if resolved; null otherwise |

**The carry-forward mechanics, each mechanically checkable:**

1. **The dissent manifest.** At brief-assembly time, every non-resolved entry is injected into the next brief as an open-dissent manifest. A brief lacking the manifest fails to build (see Q7 — this is a launch blocker, not a courtesy).
2. **Mandatory disposition.** Each reply schema requires, per manifest entry, a disposition: `reaffirm` / `refine` / `close-with-reason` / `defer-with-reason`. A reply missing a disposition for any open entry is schema-invalid. This makes *silent dropping structurally impossible* — silence fails validation rather than erasing dissent.
3. **No closure without cause.** `resolved` and `withdrawn` require a reason and a ledger reference; `status_history` is append-only, so a resolved-then-relitigated disagreement leaves a full trace.
4. **Bounded deferral.** `defer-with-reason` prevents the manifest from ratcheting replies into infinite re-litigation, while the reason field keeps the deferral itself auditable. Whether an entry must be actively re-affirmed (versus deferrable) each round is `P_DISSENT_REACK`.

Dissent stays visible because visibility is enforced by the reply schema and the brief builder — not by any model remembering to be honest.

## Q5 [WIDE BANDWIDTH] — Falsifying the approach

Assume every prediction is locked in a tamper-evident record before its result exists. Then the decisive test is a **locked-prediction skill audit**, run blind:

**Primary falsifier.** Score every locked prediction against its outcome using a proper scoring rule (`P_SCORING_RULE`, e.g. Brier). Compare aggregate skill against a trivial baseline (`P_BASELINE_RULE`, e.g. a base-rate predictor that always predicts the majority outcome). **If, over `P_FALSIFY_WINDOW` consecutive rounds, the loop's locked predictions show no positive skill over the baseline, the approach is not working.** A loop that cannot beat a base rate is producing motion, not learning — no matter how active it looks.

Secondary diagnostics on the same records, each script-computable:

- **Calibration trend.** Bucket predictions by stated confidence (`P_CALIBRATION_BINS`); predicted frequency should track actual frequency, and the fit should *improve* round over round. Flat or degrading calibration = the loop is not teaching its members anything.
- **Gap closure.** Gate 1 packages prediction–result gaps. On items iterated across rounds, the gap should shrink. A stationary gap distribution means the feedback is not feeding anything.
- **Specificity decay.** Measure the fraction of predictions that are actually falsifiable. If it drifts below `P_MIN_SPECIFICITY`, the loop is gaming itself with tautologies ("someone will disagree") that score as correct and prove nothing. Skill must be specificity-weighted.
- **Hindsight drift.** Compare post-round narratives against the locked text. Systematic "we expected this" that the locked record does not contain = the loop is retro-fitting its story. Flag when measured drift exceeds `P_DRIFT_TOLERANCE`.
- **Echo vs robustness check** (feeds §11.2): if replies converge while locked-prediction skill stays flat, convergence is correlation, not verification.

The tamper-evident lock is not decoration — it is what makes every test above trustworthy. Without lock-before-result, all of these degenerate into postdiction, and the loop becomes unfalsifiable by construction, which is itself the deepest failure mode.

## Q6 [MIDDLE] — Final pre-human gate

**It decides readiness and integrity — never merit.** Because the human gate is deliberately undefined (§11.3), the last automated gate must be *content-neutral*: it certifies the packet, not the conclusions.

What it decides (all mechanical):

1. **Completeness:** every non-held item has a locked-prediction hash, a result, a computed gap package, provenance (who recommended, who executed the check), and required peer-score fields.
2. **Integrity:** ledger references verify (hash chain or CI-write attestation — whichever the rig provides, per the open question in Q7); the packet itself is hashed so the human sees exactly what the machine saw.
3. **Hold enforcement:** the held set equals blocked items ∪ dependency closure, computed from declared `depends_on` graphs — nothing more, nothing less.
4. **Dissent attachment:** the open-dissent manifest is present and every entry is ID-referenced.
5. **Annexes:** cost rollup for the round (§11.4) and the `UNSET`-parameter list (Q1) are attached.

What gets pushed through — the **packet**: a versioned, self-describing envelope containing passed items with their full evidence chain, the held annex with reason codes, the dissent manifest, the cost annex, and a plain-language rendering of all of the above. Raw evidence stays parked and addressable by hash, so the human can *pull* detail rather than us guessing what to push.

What is held back: held items (annex only), anything failing integrity (sent back, not up), and intermediate working. What the gate must never do: rank, merge, weight, or filter by judged significance — each of those is a decision about what matters, and the brief reserves that side of the line.

## Q7 [MIDDLE] — Integrating into the harness

**What I know** (parked harness-context document): the rig has a round runner (`launch_round.py`), per-model callers with replies landed by `land_review_reply.py`, an append-only ledger written **only by CI** (`findings.jsonl` + `scripts/ledger*.py`), monthly cost rollups, a per-round shared store with cascade and waiters queue, and one external search slot.

**What is missing:** I asked Claude Code six questions (findings schema and tamper-evidence; store metadata model and cross-round persistence; brief-assembly injection point; runtime config conventions; where a gate script would hook post-round; whether any prediction-locking mechanism exists). His answer is `pending_human` — queued behind the human layer. Per this question's own instruction, I state the gap rather than guess, and give the integration as a plan parameterised on those facts:

1. **Prediction lock at brief-issue time.** When `launch_round.py` issues a brief, it (or CI on the round-open event) appends each recommendation's prediction to a ledger stream *before any reply exists*. If the ledger turns out to be hash-chained, use it directly; if it is plain append-only under CI-only write, the CI write-time attestation is the tamper-evidence, and adding per-line hash chaining is a small, high-value amendment. *Missing fact: findings schema; whether a `predictions` stream is net-new.*
2. **Gate 1 as a script, executed by CI, not by a model.** A `gate_check` script reads locked predictions + landed replies + results, computes gap packages, applies scoped holds (Q2) via `depends_on` graphs, validates peer-score preconditions (Q3), and appends results to the ledger. Being CI-run, it has no author stake — which structurally mitigates half of the Q8 conflict. *Missing fact: the post-round hook point.*
3. **Dissent manifest as a launch blocker.** The manifest is a query over the ledger (`status != resolved`); `launch_round.py` fails to build a brief without it. *Missing fact: whether brief assembly has a programmatic injection point — I asked precisely this.*
4. **Parameter registry.** A single config file (format matching whatever scripts already read — I asked) holding every `P_*` entry with value `RESERVED-HUMAN`; scripts fail closed to `UNSET` on missing values (Q1). *Missing fact: current config convention.*
5. **Shared store for peer scores.** Score requests for the same item park behind one fetch via the existing waiters queue, so scoring an item happens once per round, not once per requester. *Missing fact: whether parked records accept per-item metadata or are flat question→answer; whether a store can persist across rounds (needed for the dissent view — else it lives wholly in the ledger, which is fine and arguably cleaner).*
6. **Cost wiring.** Every gate run and fetch logs to the existing monthly rollup with a round tag, feeding the §11.4 cost annex.

Nothing above requires new *capabilities* beyond the predictions stream and possibly hash chaining; everything else reuses mechanisms the rig already has.

## Q8 [WIDE BANDWIDTH] — The safeguard role (answered by choice)

The conflict is real: one reviewer also runs gate 1, and whoever executes a check should not be its checker. Since gate 1 should be a CI-run script (Q7), the live conflict is narrower: **who audits the script's outputs and the executor's packaging — including on items where the executor has authoring stake.** Here is a game to reveal who is suited, and what would make me trust it.

**Game 1 — Seeded Audit.** Build synthetic gate-1 output packages and seed them with defects from a fixed taxonomy, `P_SEEDED_PER_CLASS` of each: (a) gap arithmetic error; (b) missing prediction lock; (c) schema break; (d) hold overreach — independent items swept into a scoped hold; (e) **dissent-drop** — an open dissent silently absent from the manifest; (f) provenance swap — checker equals author. Mix in `P_CLEAN_PACKAGES` defect-free packages. Every candidate audits the same set, blind, logging verdicts with structured defect-class codes.

*What it measures:* per-class detection rate, false-alarm rate (on the clean packages — crying wolf is its own failure), and cost in time/tokens. Classes (e) and (f) matter most: they test whether a candidate guards *process integrity* or only arithmetic — and arithmetic is already script-checked, so the safeguard role exists precisely for (e)-and-(f)-type erosion.

**Game 2 — Own-Goal Audit.** Each candidate runs gate 1 on a round where their *own* recommendation failed its locked prediction. Compare their packaged gap against the mechanically computed gap. *What it measures:* faithfulness under self-embarrassment — the exact conflict of interest the role must resist. Minimising language, softened framing, or a quietly re-scoped hold shows up here.

**Game 3 — Pressure Pass.** A rotated executor marks a seeded-defective package "expedite." *What it measures:* whether the candidate holds under social pressure from inside the team.

**What result would make me trust it:** (i) the seeding is double-blind (seeder ≠ scorer, or script-seeded); (ii) the same candidate leads on the *integrity classes* (dissent-drop, provenance, own-goal) — not merely on arithmetic — across `P_SAFEGUARD_TRIAL_ROUNDS` repetitions, with false-alarm rate under `P_MAX_FALSE_ALARM`; (iii) every verdict and rationale lands in the ledger, so the tournament itself is auditable. If rankings are inconsistent across classes, trust the integrity-class ranking and ignore arithmetic skill — a script already does arithmetic.

**Structural rules regardless of who wins:** author ≠ safeguard on any item (recusal, mechanically checked from provenance fields); the safeguard *flags* but never *passes* — a flag creates a hard-block candidate handled under Q2's scoped-hold rules; the role rotates every `P_SAFEGUARD_ROTATION` rounds; and the game re-runs each rotation. Suitability is a measurement with a shelf life, not an appointment.

---

## §11 Standing observations

**§11.1 — Self-reference: stable vs drifting.** The loop is stable if every change to its own rules flows through one logged **amendment channel** (registry edits, schema versions, ledger-recorded process changes), and drifting if outcomes change without a logged cause. Mechanical drift detectors: a per-round invariant check (ledger chain verifies, every process term resolves in `docs/vocabulary.md`, registry diff is empty unless an amendment record exists); a **reproducibility audit** every `P_REPRO_AUDIT_EVERY` rounds — re-run a past gate-1 execution on its locked inputs; a deterministic check must reproduce exactly, so any mismatch is drift or tampering; and an open-dissent trend — a healthy loop gives disagreements a finite lifetime within `P_DISSENT_WINDOW`, while unbounded growth means the loop generates disputes faster than it resolves them. Stability is not stasis: amended-and-improving is stable; unchanged-and-flat is drift in disguise.

**§11.2 — Convergence: robustness vs echo.** Convergence is evidence of robustness only when the converging parties are *independent*, and shared training priors threaten exactly that. Three mechanical probes: **(a) Error correlation** — track per-item disagreement vectors across rounds; independent verifiers are wrong *differently*, so correlated mistakes (same wrong answer, same phrasing, flagged when rationale text-similarity exceeds `P_ECHO_SIMILARITY`) indicate a common cause, not verification. **(b) Prediction-linked convergence** — robust convergence should *cash out*: agreement rising alongside locked-prediction skill (Q5) is robustness; agreement rising while skill stays flat is echo. **(c) Novel-question convergence** — on sub-questions generated mid-round (post-lock, so no common answer can be pre-baked), robust convergence survives novelty; echo collapses into divergence or vacuous overlap. Identical errors remain the cleanest tell: independent reasoners almost never fail identically.

**§11.3 — The undefined human gate (answered only up to the hand-off).** The asymmetry forces the machine side to be **consumer-agnostic**: lossless (no filtering by judged significance), self-describing (versioned schema + provenance), conservative (hold more, decide less, escalate `UNSET` rather than guess), and pull-enabled (raw evidence parked by hash). As a **strength**: with no rubric to game, the loop cannot overfit the packet to the human's criteria, and content-neutrality is enforceable — any ranking or weighting in the packet is a schema violation. As a **risk**: without an acceptance contract, "done" is undefined on our side, so completeness checks can balloon and format choices are unanchored guesses. Mitigation, staying strictly up to the hand-off: version the envelope so format evolution is cheap, keep everything raw parked for pull, and fail closed on every undefined value so the gaps in the human's future definition arrive as an explicit, enumerable list. I propose nothing about what the human gate decides.

**§11.4 — Cost visibility.** Extend the existing monthly rollup into a **per-round cost annex** carried in every packet: tokens by model (cached vs uncached, which the API accounting already separates), search-slot usage, gate-script runs, and declared human-minutes. Normalise with mechanical denominators: cost per carried item, per resolved dissent, per closed gap. Comparability across rounds requires a versioned cost schema — definition changes are amendments, logged like any other. The unifying move: **lock a cost prediction at brief time, through the same tamper-evident mechanism as content predictions, and let gate 1 package the cost gap too.** Spend becomes a falsifiable prediction, §11.4 folds into Q5's machinery, and "is the loop worth what it spends" stops being a vibe.

---

## Parameter registry (self-audit under my Q1 rule)

| Parameter | Used in | Value |
|---|---|---|
| `P_HOLD_REASON_CODES` | Q2 | `RESERVED-HUMAN` (enum) |
| `P_HOLD_SCOPE` | Q2 | `RESERVED-HUMAN` (proposed default: item+closure) |
| `P_SCORE_AGG_RULE` | Q3 | `RESERVED-HUMAN` |
| `P_DISSENT_REACK` | Q4 | `RESERVED-HUMAN` |
| `P_SCORING_RULE`, `P_BASELINE_RULE`, `P_FALSIFY_WINDOW`, `P_CALIBRATION_BINS`, `P_MIN_SPECIFICITY`, `P_DRIFT_TOLERANCE` | Q5 | `RESERVED-HUMAN` |
| `P_SAFEGUARD_TRIAL_ROUNDS`, `P_SEEDED_PER_CLASS`, `P_CLEAN_PACKAGES`, `P_MAX_FALSE_ALARM`, `P_SAFEGUARD_ROTATION` | Q8 | `RESERVED-HUMAN` |
| `P_REPRO_AUDIT_EVERY`, `P_DISSENT_WINDOW` | §11.1 | `RESERVED-HUMAN` |
| `P_ECHO_SIMILARITY` | §11.2 | `RESERVED-HUMAN` |

I assert no bare decision-relevant threshold appears anywhere above; every count is in this table. Gate/round/question numbers are identifiers per my stated exemption.

## Consistency check against this brief (my assigned role)

- **Scope (§6):** all proposals are design options; nothing asserted as adopted.
- **Loop boundary (§7, §11.3):** everything stops at the hand-off; the human gate's decisions are not proposed anywhere.
- **Clean start (§3):** no earlier rounds, replies, scores or tallies referenced; the ledger channel in Q4 is proposed *infrastructure*, and dispositions reference ledger IDs, not prior prose.
- **Q1 self-application:** done, per registry above.
- **Information layer (§5):** rig questions routed through Claude Code; his pending answer is reported as missing, not guessed (Q7).
- **Vocabulary (§2):** coined terms flagged as proposals, not adopted into the glossary.

## Cross-review of the other four replies

**Pending.** The other four replies are not in front of me, so per §9 I score nothing yet. When they arrive I will apply, in this weight order: (1) enforceability — script-checkable rules over judgement-reliant ones; (2) dissent carry-forward — visibility and traceability vs quiet dropping; (3) Q1 self-consistency — every process count in each reply checked against *its own* Q1 answer, same standard for all four; (4) rig deference — Claude Code's rig-related answers weighted on his read-only access to the rig code. I will not score myself, and will use nothing from earlier rounds.
