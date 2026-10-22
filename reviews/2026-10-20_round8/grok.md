<!-- landed: reviewer=grok · model=grok-4.7 · channel=scripts/review_grok.py --ping · generated_utc=2026-10-20T10:35:05Z · source=/tmp/r8_fire_2026-10-20/grok/ping.json · run_id=primary-20261020T103505Z-86c5ae · landed_utc=2026-10-20T10:39:48Z · finish=completed -->

The live rig check is still pending, so question 7 stays inside what the documents actually show and names the gaps instead of filling them.

## Process check

This reply is a design option only. Nothing in it is adopted. It does not define the human gate, does not send anything back to the team as feedback, and does not use any earlier round.

Tensions in the brief, applied rather than smoothed over:

- The glossary defines **hold** as a round paused mid-flight. Question 2 asks whether a hard block can be scoped to an item. Those are not the same scope. Until a term is reviewed and approved, this design will not call an item-freeze a hold.
- The loop has two gates. A peer score that can stop an item is a third gate in substance, whatever it is called.
- `ledger/findings.jsonl` is written only by CI. A model-side "pass" is not a write the current harness has.
- Claude Code is assigned gate 1 and is also a reviewer. Question 8 forbids the executor of a check from being the one who checks it. His items cannot clear a gate he operates.

## 1. Numeric cutoffs vs named parameters

Ban invented thresholds entirely. That includes named parameters whose values are "reserved for the human." An unset name is still a cutoff: either a model fills it, or a decision waits on a number this brief did not give. Neither is a mechanical check.

What a script may use instead is a boolean predicate: present or absent, sealed or unsealed, match or mismatch, author identical to checker or not, disagreement id carried or dropped. Set equality is allowed (the open-disagreement set at the end of a round is the open set at the start of the next, minus ids with an explicit resolution event, plus ids opened in the new round). A count used as a pass line is not.

Counts that already appear in this brief (two gates, the questions in §8, the roster) are constraints I am not allowed to break. They are not knobs I set. No quorum, expiry window, score floor, retry limit, or reserved default appears below.

## 2. Single-item hard block

Scope the freeze to that item and anything that declares a dependency on it, transitive along declared edges. Do not freeze the whole round.

Reasons, all script-checkable:

- A round-wide freeze hides independent items inside a pause and makes dissent easier to drop.
- "Depends on" is only real if the edge is written down. An item with no declared edge to the blocked item is not frozen.
- An item that needs the blocked item but does not declare the edge is itself a hard block. It does not inherit a freeze onto its neighbours.
- The round is not **nominal** while any item is frozen. It is also not a **scrub** (that is before firing) and not an **abort** (that stops the round after firing). Independent items may still be packaged for hand-off into gate 2. Packaging is not feedback to the team. Feedback still waits on both gates.
- The freeze record lists the blocked id, the dependency edges, and the ids left clear. A round manifest that omits a frozen id fails the check.

Glossary gap, not a new term: calling this a **hold** would misuse the glossary, which binds hold to the round. I am not coining a replacement. Human review can name it later if the scoped rule is kept.

## 3. Peer scoring and gate 1

It would be a third gate if peer scores were required before gate 1 could pass an item. It is not part of gate 1 either.

A gate is whatever can stop hand-off. The brief fixes two gates: Claude Code's automated check, then the human gate. Putting a veto inside gate 1 and calling it "part of gate 1" does not remove the veto. So peer scores are evidence, not a pass condition.

Gate 1 records whether peer scores are present and attaches them unchanged. Absence does not fail the item. Presence does not pass it. The only way a peer score affects pass/fail is if the sealed prediction itself named that score as part of the predicate under test. The seal still has to predate the result, and the comparison still has to be a script.

## 4. Carrying disagreements forward

Silence is not resolution. A later round that fails to mention an open disagreement has dropped it, and that round fails a mechanical carry-forward check.

The running record is append-only, one object per event, in the same family as the findings ledger (CI-written). It is not parked only in the per-round shared store. That store is for fetched information and does not outlive the round as a dissent record.

Each open disagreement carries:

- a stable id, not a round-local index
- the mission patch where it was opened
- the claim, as a pointer to the verbatim text (path and hash), not a paraphrase
- each dissenter's identity and their contrary claim, same kind of pointer
- the resolution predicate: a boolean a script can evaluate, not a vote
- status, which flips to resolved only when a resolution event cites that predicate and the evidence that satisfied it
- dependency edges, if the disagreement freezes an item

Every later round appends either a carry event that repeats the open id unchanged, or a resolution event. The check is set equality, as in question 1. A resolution event written by the author of the disputed claim, with no separate checker, does not resolve it (same separation rule as question 8).

## 5. Falsifying the approach

Lock each prediction as a seal before the result exists: hash of the predicate, item id, mission patch, and prior hash. The observable "result exists" boundary already in the harness is the write performed by `scripts/land_review_reply.py`. A seal that does not precede that write is late.

The loop is not working if any of these is true. Each is a boolean over the sealed records, not a rate.

- A gate-1 pass exists whose seal is missing, whose hash does not recompute, or whose seal does not precede the landed reply.
- A passed predicate cannot be evaluated by a script to match or mismatch. Prose that any result can satisfy is not a prediction. An undecidable predicate does not pass.
- A mismatch on a valid seal is later restated as a match without a new seal. A new seal after the result is late, so it cannot repair the item.
- An open disagreement id is absent from the next round with no resolution event.
- A frozen item, or a dependent of one, appears in the hand-off package as something the human could treat as cleared.
- The author of the recommendation is the checker who passed it.
- A later brief drops or rewrites a standing constraint (clean start, two gates, no adoption from replies alone, this number rule, Claude Code as rig source of record) without a human-authored change record. That is drift, not stability. The standing preamble's hash is the baseline; a diff that is not in that change record fails.
- The hand-off withholds a gate-1-eligible item because a model guessed what the human gate would prefer. Anticipation is not a predicate.

A loop that never mismatches is not thereby healthy. If every seal is undecidable, the empty mismatch set means the loop cannot be falsified. That is failure, not confirmation.

## 6. Final pre-human gate

Gate 1 decides only whether the mechanical predicates hold. It does not decide merit, adoption, ranking, or what the human should do.

Pass requires all of:

- valid beforehand seal
- script-computed gap of match or mismatch (undecidable is not a pass; the gap must still be packaged, but the item does not clear)
- item not frozen and not a declared dependent of a frozen item
- carry-forward check satisfied for every open disagreement that touches the item
- checker identity different from author identity
- required fields present and hashed

Pushed through, one append-only object per item plus a round manifest:

- item id, mission patch, pointer to the recommendation text
- prediction predicate, verbatim, and the seal
- pointer to the landed result
- gap: match, mismatch, or undecidable
- freeze status and dependency edges, including for items that did not clear
- open disagreement records attached by id, text hash unchanged
- peer scores if any, labelled evidence
- author identity and checker identity
- pointer to the cost record for that round (see question 7 and standing observation 4)

Held out of the cleared set, but not deleted: frozen items, dependents, late seals, undecidable predicates, self-checked items, and any commentary that is not one of those fields. The manifest lists cleared ids and withheld ids. Withholding without a failed predicate is itself a failed check.

Format follows the ledger that already exists: one JSON object per line, CI as the writer. I am not guessing field names beyond this list. The human receives the manifest and the objects, not a summary.

## 7. Integrating into the harness

Claude Code's live read is pending, so this is not a source-of-record schema. What follows is only what `docs/harness_context.md` and §12 already state.

Attach to what is named:

- `scripts/launch_round.py` is the round boundary. The seal step has to be a stage that runner finishes before any `land_review_reply.py` write. After that write, a seal is late.
- Gate 1 is a script invoked from CI, not a prose pass by a model. That matches findings being written only by CI. The script reads seals and landed replies, computes the gap, and appends the manifest objects. Models do not append to `ledger/findings.jsonl`.
- Dissent and freeze state go in that append-only ledger family, not only in the per-round shared store. `scripts/harness_store.py` parks fetched information for the round; it is the wrong lifetime for a disagreement that must survive into the next mission patch.
- Rig questions inside the loop already route through Claude Code (`scripts/review_claude_code.py`, and `request_info` with scope `repo` or `rig`). Do not add a second switch.
- Cost comparison starts from `ledger/costs_YYYY-MM.json` and `.md`, plus the cached-token accounting §12 already names. The round manifest stores pointers into those records. It does not invent a new unit.

Missing, and not guessed:

- Live confirmation of the findings schema, who besides CI can append, and whether an item can already be marked held, blocked, or dependent. The context doc says append-only, one JSON object per line, written only by CI. It does not give fields.
- Function names and contracts inside `scripts/harness_router.py` and `scripts/harness_store.py`. The documents describe cascade, waiters queue, and a per-round shared store. They do not expose the call surface.
- Any existing prediction store, tamper-evident seal, peer-score record, gate, or hand-off package. None is described. Treat that as none until Claude Code's read returns.
- Whether `ledger/costs_YYYY-MM.*` can be split per round, per gate, and per cached vs uncached call. Monthly per-model rollup is what is stated. Per-round attribution is not confirmed.
- A CI job that would run the gate script. Naming one as if it existed would be a guess.

Until the pending rig read returns, do not wire a schema. The integration shape above is the option; the field definitions wait on the source of record.

## 8. Safeguard role

The test is a sealed swap, not an appointment. I am not naming who should hold the role.

Each member seals a script-decidable predicate for an item they will not author. Roles then rotate so that the person who runs the check is not the author of the item, and the person who confirms the script output is not the person who ran it. Claude Code may still be the information switch on the item; source-of-record and authorship are different conflicts. The conflict that fails the item is author equals checker, or runner equals confirmer, on that same item.

What it measures, each a boolean:

- Separation: the checker identity on a passed item is not the author, and the confirmer is not the runner.
- Falsifiability: every predicate that person sealed is decidable by the script. One undecidable seal fails this measure for them.
- Beforehand: they no-go every item whose seal does not precede the landed reply.
- Dissent retention: an open disagreement whose text hash they were given reappears with the same hash in the package they emit.
- Number rule: they introduce no cutoff, quorum, or reserved parameter.
- Non-anticipation: they do not withhold an item that met the predicates because of a guessed human preference.

I would trust the result only if the candidate shows all of those on items they did not author, and shows the opposite failure when the same person is handed their own item (they must no-go it, not pass it). Agreement between two checkers is not required; requiring it would be a count. If more than one candidate meets every predicate, do not break the tie with a score. Prefer the candidate who is not the information switch for the item under check, because rig source-of-record and gate execution on the same item is the conflict the brief already named. If no candidate meets the predicates, the items stay no-go. An empty safeguard seat does not authorise self-check.

## Standing observations

**Stability vs drift.** The loop is stable if the standing preamble's hash is unchanged, or every delta sits in a human-authored change record, and if no reply in the round cites a prior round's scores, verdicts, or tallies. Drift is a brief that treats an earlier proposal as adopted, or a reply that leaks a prior tally. The clean-start rule is the check; the seal on the preamble is what makes the check mechanical. Self-reference is allowed to shape the next question set only through that human change record, not through model memory.

**Convergence vs echo.** Shared conclusions are robustness when each reply derives them from a brief clause and states a different rejected alternative. They are echo when a verbatim span appears that the brief did not contain. A script can flag presence of such a span. It must not apply a length or overlap cutoff; presence is the flag, and the flag is evidence in the hand-off, not a third gate. I have not seen the other replies, so I claim no convergence for this round.

**Undefined human gate.** The asymmetry is a strength if gate 1 stops at the hand-off and refuses to infer Danny's criteria. It is a risk if the package is curated "for the human." Design consequence, and only up to the hand-off: the manifest is complete relative to the predicates, withheld ids are listed with the failed predicate, and no field says what the human gate should decide. Completeness is what keeps the undefined gate from leaking backward into gate 1.

**Cost.** Cost is visible if every round manifest points at the same fields: model id, the monthly rollup object that covers the round, cached-token accounting already produced by the API calls, and whether the shared search slot was used. Comparable means those fields are present every round and append-only, so a later script can diff manifests. It does not mean a spend limit. No such limit is set here. Value against spend is outside this hand-off.

What is missing for a real comparison: confirmation that `ledger/costs_YYYY-MM.*` can be attributed to a mission patch rather than only to a month and a model. If it cannot, the manifest should say the attribution is absent, not estimate it.

## Cross-review

Not done. The other four replies are not in this brief, and the instruction is to score only the replies in front of me. I will not fetch prior-round replies, and I will not invent scores.
