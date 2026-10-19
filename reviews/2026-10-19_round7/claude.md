<!-- landed: reviewer=claude · model=claude-sonnet-5-5 · channel=scripts/review_claude.py --ping · generated_utc=2026-10-19T16:06:14Z · source=/tmp/round7-run/claude/ping.json · run_id=primary-20261019T160614Z-872eec · landed_utc=2026-10-19T16:06:46Z -->

# Claude — Round 7 reply (conversation design)

Scope: protocol design only. No sweep, no solver, no `protocol.md` creation. Everything below is a proposal for Edger_Equals to accept or cut. I don't know the contents of `DESIGN_STATE`, the round-6 handoff, or the launcher beyond what the brief states, so schema and flag names are proposals, not descriptions of existing code.

## 1. Sharing findings

- **Default: compiled summary.** Models write only to their own `{model}.md`. Nobody replies pairwise or threaded to a peer's full text.
- **Direct reply is allowed only as an escalation.** It is limited to one round-trip, triggered by a flagged disagreement (two models give opposite verdicts on the same claim ID). It is capped in length and filed as `{model}_reply_to_{peer}.md`. It never replaces the compiled path.
- **Why:** pairwise threads grow as n², and every thread is a fresh full-context read for a paid model.

## 2. Cross-review order

1. Shared context is built once: brief, `DESIGN_STATE`, solver summary if one exists.
2. **Kimi and DeepSeek fire first**, independently. They also run the rote scans: units, retired items (electrodes), locked-geometry drift, consistency with the kickoff.
3. A **compile step** merges their conclusion blocks into one digest and applies the escalation criteria.
4. **Claude and Grok** run on the digest plus their own primary pass. They are not the first pass on anything a cheap filter can settle.
5. Cross-review (gate 2) runs on conclusions only. Each model scores the other three.

Gate 1 as the brief defines it stays unchanged. The one practical wrinkle is that all four primaries are still fired as one job. So the tiering applies to *what the paid models are asked to do*, not to launch timing. The paid models' primary prompt includes the instruction "do not redo rote scans; cheap-filter results are in the digest." If the caller wants strict sequencing, that needs a launcher change, which I flag as a proposal, not an assumption.

## 3. Conclusions block and compilation

**Who compiles:** a deterministic script, not a model. Because the block is a fixed schema, extraction is mechanical (parse a fenced block from each `{model}.md`). This avoids an LLM summarizer's bias and the cost of one. If a reply lacks a valid block, the compile fails loudly and the reply is bounced to its author.

**Block schema** (YAML in a fenced block at the end of each reply):

```
model: <name>
run_id: <current primary run>
claims:
  - id: C1                 # stable within the round
    statement: <≤2 sentences>
    verdict: support | oppose | amend | unsure
    confidence: 0–1
    evidence: <pointer: kickoff §, DESIGN_STATE key, or "reasoning only">
    cost_note: <optional; flags expensive patterns>
    escalate: yes | no
    escalate_reason: <required if yes>
proposals:
  - id: P1
    text: <≤3 sentences>
    touches: [sharing | order | scoring | gate1 | gate2 | package | economics]
aim: <≤80 words, own words>
improvements: [<concrete items>]
```

Rules:
- The block is required, and the scoring pass sees only the blocks.
- Claims need an ID so that scores attach to something specific, not to a whole reply.
- `evidence` makes "reasoning only" visible, so scorers can discount it.
- The `aim` and `improvements` fields make checklist row 15 mechanically checkable.

**Cache refresh:** the shared context is rebuilt and re-cached only when its inputs change (the brief, `DESIGN_STATE`, or the solver summary). The hash of these is recorded in `run.json`. A changed hash invalidates teamwork runs, the same way a primary re-fire does.

**Escalation criteria ("interesting"):** a claim escalates if any of these holds:
- Both cheap filters disagree.
- A cheap filter flags a locked-rule conflict.
- Confidence is below 0.6 on a gate-relevant claim.
- The proposal touches gate 1 or gate 2.
- The proposal changes cost structure.

Otherwise it does not escalate.

## 4. Peer scoring

- **Axes (1–5 each):** correctness against locked rules, economic compliance, gate integrity (does it keep both gates and add none), operability (could the launcher or Claude Code realistically implement it), and evidence quality.
- **Unit of scoring:** the claim or proposal ID, plus one overall line per peer.
- **Format:** a fenced JSON block in `{model}_teamwork.md`: `{scorer, target, id, axis_scores, one_line_reason}`.
- **No self-scoring:** the ledger writer rejects any row where `scorer == target`. Because Claude Code is not a fifth voice, Claude-side items are scored by the other three, never by chat Claude on its own proposals.
- **Landing:** a script converts the teamwork blocks into `ledger/pending/*.jsonl` rows. Each row carries `run_id`, `primary_run_id`, and a content hash, so stale scores cannot enter.
- **Aggregation:** use the median of the three peer scores per axis. A spread of 2 or more flags the item as contested for the human gate.

## 5. Automated gate inside the conversation

Gate 1 must not review Claude-side recommendations alone. I propose:

- **Anti-self-check rule:** for any recommendation whose author is Claude (chat) or whose staging was done by Claude Code, the automated gate's pass is *provisional*. It becomes valid only if at least two non-Claude models' peer scores on that item are present and not below a floor set by the human gate.
- **Prediction before run:** the prediction (value and tolerance) is written and hashed *before* the check runs, by the recommending model. Claude Code runs the check and cannot edit the prediction. This also covers non-Claude recommendations.
- **Ordering:** peer scores, then gate 1 execution, then packaging, then gate 2. This keeps the brief's order (automated, then human) intact. Peer scoring is input to gate 1, not a third gate.
- **Disagreement:** if gate 1's verdict contradicts the peer consensus, both go to the human unreconciled.

I'd call this one open: the brief says no third gate. I believe peer scores as an input condition respect that, but Edger_Equals should confirm.

## 6. Human-gate package

One page, plus pointers. Nothing else is read by default.

1. Item ID, author, and the recommendation in one sentence.
2. Prediction (value, tolerance, hash, timestamp).
3. Result, deviation, and the threshold applied. The threshold's measure and value come from round 6, not from this protocol.
4. Peer score medians and any contested flag.
5. Gate-1 verdict, marked provisional if the anti-self-check condition is unmet.
6. Links to full artifacts, which are optional reading.

**Held until sign-off:** all fan-out of feedback, ledger promotion from `pending/`, and any change to `DESIGN_STATE`. Nothing is sent to models.

## 7. Aim check

As I read it, the aim is to build a loop in which independent models propose and critique design recommendations, and a real simulation, not model opinion, decides which ones survive. Predictions are committed before results. A human reviews the gap before the team learns from it. Cheapness and auditability are part of the aim: the process should cost little, and every score and verdict should be traceable and non-self-referential, so the loop can be trusted when it later drives expensive solver work.

## 8. Improvements against the aim

1. **Prediction hash before execution** (see §5). It makes the prediction-versus-result gap tamper-evident.
2. **Deterministic compile and ledger scripts, no LLM summarizer.**
3. **Claim IDs stable across rounds** (e.g. `R7-C1`), so later rounds can cite and re-score earlier claims.
4. **Calibration tracking.** Log each model's stated confidence against eventual outcomes. After round 8 this lets scores be weighted by track record, which should be introduced only with human approval.
5. **Dissent preservation.** Compiled digests must carry minority verdicts verbatim in the claim block rather than dropping them, to avoid consensus drift.
6. **Cost ledger per round** (tokens per model per stage), so the economics requirements are measured and not just asserted.
7. **Cheap-filter audit.** Occasionally (say, one claim in ten) send a cheap-filter-closed item to a paid model. This guards against a systematic cheap-filter blind spot.
8. **Dry-run of the protocol on a trivial item** before round 8, to test the full chain (block, compile, score, ledger, package) at no solver cost. This is documentation-and-script scope, not a sweep.
9. **Block-schema validation as a pre-land check**, extending `land_review_reply.py --check` so that malformed replies fail like stale ones.

## Risks and open items

- The current launcher injects full peer bodies. Conclusions-only needs the `--teamwork-summary` mode, and it should not be changed mid-round-6.
- Whether cheap filters can truly run before paid ones depends on launcher support; otherwise tiering is enforced by prompt only.
- The anti-self-check floor value is for Edger_Equals to set.

```yaml
model: claude
run_id: <stamped by launcher>
claims:
  - id: C1
    statement: Compiled-summary sharing is the default; direct replies are a capped escalation.
    verdict: support
    confidence: 0.8
    evidence: kickoff §4.1, §5
    escalate: no
  - id: C2
    statement: Gate 1 passes on Claude-side items are provisional until two non-Claude peer scores exist; this is an input condition, not a third gate.
    verdict: unsure
    confidence: 0.6
    evidence: kickoff §9 (reasoning on interpretation)
    escalate: yes
    escalate_reason: touches gate 1 and the no-third-gate rule
proposals:
  - id: P1
    text: Deterministic script compiles a fixed-schema conclusions block; malformed replies fail pre-land.
    touches: [economics, scoring]
aim: Loop where models propose, a real simulation decides, predictions are committed first, a human reviews the gap, and the process stays cheap and auditable.
improvements: [prediction hash, claim IDs across rounds, calibration tracking, dissent preservation, per-round cost ledger, cheap-filter audit, protocol dry-run, schema validation]
```
