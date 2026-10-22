<!-- landed: reviewer=kimi · model=kimi-k3 · channel=scripts/review_kimi.py --ping · generated_utc=2026-10-20T10:54:33Z · source=/tmp/r8_teamwork_2026-10-20/kimi/ping.json · run_id=teamwork-20261020T105433Z-2b3358 · landed_utc=2026-10-20T11:00:19Z · finish=stop -->

# Kimi — Round 8 cross-review

**Scoring rubric** (disclosed so the arithmetic is auditable; these are review-scoring weights set by me as reviewer under §9's ordering, not loop-design parameters, so they do not enter my Q1 registry): Enforceability 40%, Dissent carry-forward 25%, Number-rule self-consistency 20%, Rig handling 15%. Sub-scores on a ten-point scale. I score no reply from earlier rounds, and I do not score myself.

---

## DeepSeek — 8.7

**Number-rule audit (against his own Q1): pass.** Every cutoff is a named `HP:*` parameter; remaining counts ("two gates", "three gaps") are measured/enumerated, which his Q1 explicitly licenses. No invented literals found.

**Enforceability — 8.5.** The traceability check in Q4 (an open record absent from a later hand-off without a close record → `gate1_refused`) is exactly the grep-class mechanism the guidance rewards. Mandatory `depends_on` with malformed-field → that-item-only hold is mechanical and refuses to let a defect expand the blast radius. Two soft spots: Q8's "reports the gap as the gap, or spin it into a story" requires a judge to detect spin; and Q6's "summary must not contain claims absent from the machine part" is only partially script-checkable over prose.

**Dissent carry-forward — 9.0.** Full open index in every hand-off, content-addressed IDs blocking quiet edits, close records require reason plus citation, and absence of an open record is itself a gate failure. The `dropped` status exists but is guarded by the mandatory close record, so dropping cannot be silent. Strong design.

**Rig handling — 8.0.** Asserts specifics beyond the parked documents (`gate1.py` outputs, `{model}_teamwork.md`) via a claimed "live rig check" whose provenance I cannot verify; the claims largely match what Claude Code confirms from file-and-line reads, and the three genuinely missing pieces (no prediction writer, no comparison step, no structured peer binding) are stated honestly rather than guessed.

**Standouts:** Q5's null model ("predict whatever the recommendation asserts") paired with the self-fulfilling-drift check is the sharpest falsification pairing in this round. The constitution-snapshot hash in §11.1 is a clean stability probe.

## Claude — 9.1

**Number-rule audit: pass.** The tightest explicit allowed-list of the four (brief-fixed counts, logical words, identity); four named parameters, all fail-closed or skip-while-unset as labelled. No violations found.

**Enforceability — 9.0.** Four gate-1 statuses with UNCHECKABLE for unset decision parameters; a script-verified JSONL↔Markdown packet match; set-difference-empty carry check; Q8 measured entirely in recall/false-alarm counts with a **script baseline** — and the willingness to conclude "if no model beats the script baseline, the role shouldn't go to a model" is the most decision-useful sentence in any Q8 answer here.

**Dissent carry-forward — 9.5.** The standout rule: **a majority vote never closes an entry** — the majority may proceed while the dissent stays open. Closure only by evidence meeting the stored criterion or by holder withdrawal. He is also the only scorer besides Grok to confront the §3 conflict head-on with a concrete reconciliation (register goes to the human and brief author; re-entry only as a restated, unattributed question with ID).

**Rig handling — 8.5.** Reports `pending_human` honestly, makes the whole Q7 plan conditional, lists exactly what is missing. Small ding for asserting unverified repo specifics in Q5 (`sim/` smoke tests, `solver_v0.py`) that no parked document confirms.

**Standouts:** the method review — flagging that Claude Code holds four roles at once, and that peer scoring by answer-authors is circular — adds value beyond the questions. Minor weakness: Q5's gate-discrimination test leans on later human-gate outcomes, which sits near the hand-off line he otherwise respects.

## Grok — 9.3

**Number-rule audit: pass — and the strictest stance taken.** He rejects not only invented thresholds but reserved-value parameters ("an unset name is still a cutoff"), permitting only boolean predicates, set equality, and brief-fixed counts — and then holds himself to it perfectly. I found zero counts anywhere, including in Q8, where he explicitly refuses a tie-breaking score.

**Enforceability — 9.0.** The purest rule set: every falsifier in Q5 is a boolean over sealed records; the echo check is verbatim-span presence with an explicit refusal of length cutoffs; the preamble-hash drift check is fully mechanical. Two gaps keep this from a ten: Q2's "an item that *needs* the blocked item but does not declare the edge is itself a hard block" — *needs* is not machine-readable without the declared edge, so detection requires judgement; and "script-evaluable predicate" is a meta-judgement, though his fail-closed framing (no deciding script → no pass) mostly covers it.

**Dissent carry-forward — 9.5.** Set equality per round, carry-or-resolution events only, verbatim claim pointers with hashes, author of the disputed claim cannot self-resolve, and — uniquely — *no parked states at all*: no deferred, no superseded. Nothing can be worn down quietly. One real gap: there is no withdrawal path, so a genuinely abandoned position must be carried forever or evidence-resolved; Claude Code's "empty `settling_test` is itself a signal" handles the no-test-known case that Grok's required resolution predicate does not.

**Rig handling — 9.0.** The most disciplined of the three rig-blind replies: refuses to name fields, refuses to wire a schema while the source of record is pending, and lists precisely what the documents do and do not show.

**Standout:** the honest glossary refusal in Q2 — declining to coin a term and deferring naming to human review — is §2 applied exactly as written.

## Claude Code — 9.3

**Number-rule audit: pass.** All counts are `{named_parameters}`; the one existing exception (`OPTIONAL_PARAMS` defaults) is disclosed as an exception rather than hidden; "two gates" is declared structural. Line numbers are citations, not process counts.

**Enforceability — 9.0.** The Q6 invariant — every `models × stages` item appears in exactly one of delivered / `held/` / `gaps.jsonl`, and every hold has non-empty rule text — is the best completeness check of the round, and he demonstrates it works by showing the current export fails it. The deterministic re-run of `gate1.py` (byte-identical `items.jsonl` or someone tampered) is the cheapest real safeguard mechanism proposed anywhere in this round. Q5's "high rate / most close through" phrasing is loose inline but is banded by named parameters in his §11.1.

**Dissent carry-forward — 9.5.** Decisive advantage: he found the **actual quiet-drop path in the live ledger** — `deferred`/`superseded` at `ledger_lib.py:30` are decided-without-being-open, never mirrored, and require no human `decided_by`. His Q4 removes the deferred path entirely, refuses any mapping onto those statuses, and requires `decided_by` to be human or holder. This is the only reply that fixes a demonstrated drop mechanism rather than a hypothetical one.

**Rig handling — 10.** Weighted per §9 on his read access, and he earns it: file-and-line citations throughout, four concrete findings (broken `RULES` entries meaning holds reach the packet without rule text; verification unbuilt; his own reviewer identity missing from `ledger_lib.REVIEWERS`; the dissent drop path), and scrupulous honesty about what he did *not* read and about export-vs-live uncertainty on the broken lines.

**Standout:** rig finding 1 alone — holds arriving in the packet with no rule explaining them — changes what the team should build first.

---

## Summary

| Reply | Enforce. (40%) | Dissent (25%) | Number rule (20%) | Rig (15%) | Total |
|---|---|---|---|---|---|
| Claude Code | 9.0 | 9.5 | 9.0 | 10 | **9.3** |
| Grok | 9.0 | 9.5 | 10 | 9.0 | **9.3** |
| Claude | 9.0 | 9.5 | 9.0 | 8.5 | **9.1** |
| DeepSeek | 8.5 | 9.0 | 9.0 | 8.0 | **8.7** |

**The tie, honestly stated:** Grok and Claude Code are level on the two heaviest criteria. Grok wins the number rule outright — his boolean-only stance is the strictest reading of Q1 and the most self-consistent execution of it. Claude Code wins rig authority outright, and his findings are the only ones in this round that are *actionable against live code today*. Per §9's instruction to weight his rig access on rig-related items, if a single ordering is required I place Claude Code first on decision value and Grok second on formal strictness — but the rubric as weighted produces a dead heat, and I report it as one.

**Cross-cutting observation (this round only):** all four replies converged independently on scoped dependency-closure holds, existence-not-content for peer scores in gate 1, append-only dissent registers with mandatory carry and cause-required closure, and planted-defect audits with self-leniency measurement for the safeguard role. Per §11.2's own caution, that convergence is a signal to test, not a verification — and notably, all four also converged on the one thing the live rig currently cannot do: compare a locked prediction to its result.
