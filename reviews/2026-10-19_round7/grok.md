<!-- landed: reviewer=grok · model=grok-4.7 · channel=scripts/review_grok.py --ping · generated_utc=2026-10-19T16:06:14Z · source=/tmp/round7-run/grok/ping.json · run_id=primary-20261019T160614Z-872eec · landed_utc=2026-10-19T16:06:58Z -->

# Grok — round 7 primary reply

**Role:** paid claim / process cross-check against this kickoff and the economics requirements. **Scope:** conversation protocol only. No sweep, no solver, no `protocol.md` file from this reply, no push.

**Source status:** this reply uses only the kickoff text. No Tavily results were provided. External claims about live launcher behavior beyond the kickoff are `not_found` and listed at the end.

---

## 1. Sharing findings

**Default: compiled conclusions, not pairwise full threads.**

| Mode | When allowed | When forbidden |
|---|---|---|
| **Compiled summary** | Primary fan-out and all cross-review. Each model writes one reply; a compiler extracts conclusion/score blocks; peers read only those blocks. | — |
| **Direct / pairwise thread** | Only if Edger_Equals opens a named dispute (one question, one round of replies) or a cheap filter flags a contradiction that cannot be scored from conclusions alone. Cap: two messages per model on that dispute. | Routine cross-review; “let me read the other three full `.md` files”; any path that re-bills full shared context. |

Direct reply is an exception with a ticket id, not the loop shape.

---

## 2. Cross-review order

Fixed order. Do not start a later stage if the earlier artifact is missing.

1. **Fire** — same brief, four models, one `run_id` (launcher stage already specified).
2. **Cheap filters first** — Kimi and DeepSeek land before Claude or Grok are asked to cross-review. They do rote consistency vs kickoff / locked geometry / two-gate rules / retired-item scan.
3. **Escalate filter** — compiler marks a finding `interesting` only if it is a protocol risk, a gate contradiction, an economics violation, or a disagreement between the two cheap filters. Units/spelling/retired-item “clean” does not escalate.
4. **Paid primary** — Claude (method) and Grok (process/claims) answer the same brief. They may see the cheap-filter **conclusions block**, not the full cheap replies, unless a finding was escalated (then attach that finding’s quote + path only).
5. **Compile** — one conclusions file for the primary run.
6. **Cross-review (gate 2)** — each model scores the other three from conclusions/scores only. Cheap models may score paid proposals; paid models must not be the first readers of rote scans.
7. **Draft `protocol.md`** — after gate 2, by Claude Code as executor staging only. Not approved until the human gate signs.

Cheap filters **finish landing** before paid cross-review starts. They do not have to finish before paid **primary** answers if the caller fires all four as one job; in that case paid models still must not treat full cheap bodies as required context. Cross-review itself waits on gate 1 (all four stamped replies).

---

## 3. Compilation: who, when, schema

**Who:** Claude Code CLI as executor, not as a fifth review voice. It extracts; it does not add scores or rewrite claims. If extraction is ambiguous, the block is `status: extract_failed` and that model is not scored until a human or a re-land fixes the reply.

**When:** immediately after gate 1 passes, before teamwork starts. Refresh the shared-context cache only when the brief, locked geometry numbers, or round-6 threshold settlement actually change — not per model.

**Conclusions/scores block (required fields):**

- `model`, `run_id`, `landed_utc`
- `scope_ack`: `protocol_only` | `out_of_scope` (out of scope → do not score as a protocol proposal)
- `aim` (model’s own paragraph; required)
- `proposals[]`: `id`, `question` (1–6), `claim`, `enforcement` (who/when), `depends_on`
- `risks[]`: `id`, `what_breaks`, `severity` (`block` | `hold` | `note`)
- `economics_ack`: tiered / cache / batched / conclusions-only — each `met` | `gap` + one line
- `self_score`: forbidden. Omit. Compiler drops any self-score.
- `citations`: kickoff section ids only unless a repo path was in the brief

Scoring still works because each proposal has a stable `id` and peers score **ids**, not prose vibe.

---

## 4. Peer scoring in practice

**Axes (1–5, integers only):** `fit_to_aim`, `gate_safety` (does not skip or self-check a gate), `economics`, `enforceability` (named owner and artifact), `scope_discipline` (no sweep, no third gate, no retired items).

**Format:** one JSON object per scorer per target proposal id, filed to `ledger/pending/` as staging — not merged into a canonical ledger until the human gate accepts the protocol. Fields: `scorer`, `target_model`, `target_id`, `primary_run_id`, `teamwork_run_id`, five axes, `note` (≤280 chars), `block` (bool).

**No self-score:** compiler rejects rows where `scorer == target_model`. Claude Code does not score. Claude-chat scores are peer scores of Claude-the-reviewer, not of Claude Code.

**Aggregation:** median per axis; a single `block: true` from any peer holds that proposal out of the draft protocol until Edger_Equals overrides in the human package. Do not average away a block.

---

## 5. Automated gate inside the conversation

Gate (1) is **after** peer cross-review of recommendations, **before** fan-out of feedback. It is not a voice in the design debate.

**Anti-self-check:**

- Claude-chat recommendations are peer-scored by Kimi, DeepSeek, and Grok in gate 2 **before** Claude Code runs the prediction check on them.
- Claude Code may execute the check (prediction vs result, threshold from round 6 once settled) but **must not** be the only reviewer of a recommendation that originated on the Claude side.
- If a recommendation has no non-Claude peer score, gate (1) **holds** it. It does not pass by default.
- Claude Code does not author the prediction it then checks. Prediction is taken from the proposing model’s conclusion block (`expected` field — add to schema when recommendations become executable). Round 7 protocol proposals are design, not solver predictions; gate (1) for this round is a **process check**: scope, two gates intact, economics fields present, no self-score. Numeric threshold check waits for round 8 artifacts.

**Fan-out:** only items that pass gate (1) **and** gate (2) return to the team. Held items stay in the human package as “not fanned out.”

---

## 6. Human gate package

Edger_Equals gets **one pager plus three attachments**, not four full reply dumps.

**One-pager fields:**

- round, `primary_run_id`, `teamwork_run_id`, gate 1/2 pass/fail
- aim consensus (one sentence) and aim dissent (bullets, attributed)
- protocol decisions proposed (id, one line, peer median, any `block`)
- economics gaps
- what is held until sign-off (draft protocol text, any round-8 language)
- explicit ask: approve / amend / reject `protocol.md`

**Attachments:** compiled conclusions/scores only; teamwork score table; extract_failed list. Full `{model}.md` available on request, not in the default package.

**Held until sign-off:** writing approved `protocol.md`, any round-8 kickoff, any sweep JSON, any feedback fan-out that would change later-round prompts.

---

## 7. Aim (own words)

The team’s aim is to keep a small, paid-for argument honest: decide the next physical or process claim only after cheap checks, peer scores that are not self-grades, and a human look at the gap between what was predicted and what came back — so the rarefied-core program does not burn model budget re-reading itself or let an executor bless its own side’s advice before anyone else has weighed it.

---

## 8. Improvements against that aim

Concrete, not restatements of locked two-gate order:

1. **`--teamwork-summary` before round 8.** Kickoff says the live launcher still injects full peer bodies. Protocol should name that flag (or equivalent) as a **round-8 blocker**: no sweep kickoff while cross-review still bills full bodies. Status of whether the flag exists in-repo: `not_found` (not in this brief).
2. **Interesting-finding budget.** Cap escalations at five `block`/`hold` items per round to Claude+Grok. Overflow waits for the next round unless Edger_Equals pulls one.
3. **Cache key.** Shared context cache key = hash of brief path + locked geometry line + “threshold settled | waived | open”. Refresh only on key change. Record the key in `run.json` so a re-fire cannot pretend the cache is new.
4. **Prediction field now, even for protocol.** Every proposal that later becomes an executable check must carry `expected` and `falsifier` in the conclusion block. Empty falsifier → cannot enter gate (1) as a recommendation.
5. **Dispute cap.** Pairwise threads die after one exchange unless the human gate extends them. Stops four models from rebuilding full context “to clarify.”
6. **Separate Claude voices in the ledger.** `claude_chat` vs `claude_code`. A row that conflates them is invalid. Stops the executor’s staging commits from looking like peer agreement.
7. **Round-7 gate (1) checklist, not a fake physics threshold.** Do not invent a numeric deviation threshold in this round. Process checks only, as in §5.

---

## Process cross-check (this kickoff)

- Round situating matches the table: 6 threshold, 7 protocol, 8 sweep after protocol + Edger_Equals. **Consistent.**
- Economics are requirements, not options. A protocol draft that omits compiler, cache refresh rule, escalate criteria, or the conclusions schema is incomplete. **Gap if omitted.**
- Two gates only; this reply does not add a third. Human approval of the protocol is gate (2) applied to the deliverable, not a new gate type.
- Geometry lock and retired-item ban: not reopened. No electrodes.
- Deliverable remains `reviews/2026-10-19_round7/protocol.md` **after** debate and human approval. This reply is not that file.

## claims_needing_source_check

- Whether `scripts/launch_round.py` already implements `--teamwork-summary`: **not_found** in this run (kickoff only says it does not yet, and that full bodies remain until that mode lands).
- Exact on-disk schema of `run.json` / `ledger/pending/*.jsonl`: **not_found** beyond path names in the kickoff.
