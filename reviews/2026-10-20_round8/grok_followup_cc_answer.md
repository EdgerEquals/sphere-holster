<!-- follow-up: reviewer=grok · model=grok-4.7 · channel=scripts/review_grok.py tool loop (scratch runner) · run_id=followup-20261020T142927Z-grok-cc-answer · generated_utc=2026-10-20T14:29:32Z · finish=completed · source=/tmp/r8_grok_followup/grok/ping.json -->

# Grok

The late read changes the round 8 reply. The design option is not adopted. What follows replaces the claims the code contradicts. It does not add a schema, a cutoff, or a wire-up.

## Retracted

Section 7 said there is no prediction store, tamper check, gate, peer-score record, or hand-off, and that naming a gate script would be a guess. That is wrong.

- Predictions exist as an optional `<round-dir>/predictions.jsonl`. `gate1.py` hashes the file and does not parse it. No schema. Not append-only, not hash-chained, no writer limit.
- The beforehand lock that exists is one sha256 taken at fire: `launch_round.py` stores `predictions_sha256` in `run.json` via `start_run`, and only if the file exists. Gate 1 compares the current hash to that value. Mismatch, or the file gone after that store, holds **every** item as `gate1_refused`.
- If predictions are present and that hash matches, gate 1 returns `gate1_unverifiable` with the note that the verification step is not built. Round 8 already defers predictions: gate 1 runs without them and reports "no predictions this round" instead of failing. A missing file is not a failure today.
- `land_review_reply` / `current_run` / `start_run` were not in the export. The claim that the landed-reply write is the confirmed "result exists" boundary is withdrawn. The confirmed boundary is the fire-time hash in `run.json`.
- Gate 1 exists: `gate1.run` yields per-reply `deliver` or `hold`, writes `gate1/{summary.md, items.jsonl, gaps.jsonl}`, archives older runs as `_revN`. Hold reasons in code: `misidentified`, `stale_run`, `truncated`, `gate1_refused`, `gate1_unverifiable`, `budget_stop`, `turn_cap_reached`. `first_step_failure` is a flag only (D10) and never a hold.
- Hand-off exists: `handoff.run` writes `to_danny/packet.md`, `to_danny/gaps.jsonl`, `held/<item>.json`, and appends `handoff_log.jsonl`. Files only; nothing is sent. Append mode is not verified append-only.
- Peer scoring exists. The launch brief asks each model for peer PASS or FAIL in `{model}_teamwork.md`, which is landed and passes through gate 1. `ledger_score.py` computes planted-mistake precision and recall plus status-based acceptance. Those are counts. This design option still does not use them as a pass line.
- No dissent record. Search found nothing.

`complete` was false. Still unverified, and still not filled in: `ledger/schema/finding.v1.schema.json` required-field list, on-disk `findings.jsonl`, on-disk `costs_*.json`, `harness/ledger.json`, `ledger.py`, and the exact contents of `run.json`.

## Narrowed

**Hold.** The glossary still binds hold to the round. The code already uses hold for a per-reply gate 1 decision and writes `held/<item>.json`. Those are not the same word. The item-freeze in section 2 is still not called a hold, and it is also not gate 1's hold. Merging them would hide three different scopes under one name.

**Scoped freeze vs what the code does.** Hash tamper is not scoped. It holds every item. The ledger has statuses `open`, `accepted`, `rejected`, `fixed`, `deferred`, `superseded` only. No `held`, `blocked`, or `depends-on`, and no field linking one finding to another. `deferred` / `superseded` are parked and need a note; they are not a dependency edge. Section 2's scoped freeze is not something the ledger can represent. Section 4's dependency edges are the same gap. Neither is wired here.

**Ledger write path.** CI-only append stands. `ledger_lib.append_records` validates, drops duplicate ids, appends, never rewrites lines. `verify_append_only` checks that new text starts with old text. `ledger_commit.sh` commits as `github-actions[bot]`, verifies against `origin/main`, validates, rebases, retries up to 4 times. Proposed decisions arrive as staged wrappers in `ledger/pending/*.jsonl` and are ingested by `ledger.py ingest-staged`. Receipts are refused unless `allow_receipts=True`. Models still do not append. Field names visible in builders are not treated as the unread schema's required list.

**Store and router.** The "call surface unknown" gap is closed. `Store` is `<store_dir>/info.jsonl` (append-only; kinds `info_request`, `info_answer`, `info_invalidate`, `cost`), plus derived `index.json` and `inflight/<key>.lock`. It refuses any decision-type field (`decision`, `verdict`, `score`, `recommendation`, `approved`, and the like). So section 4's refusal to park dissent there is confirmed by the API, not only by lifetime. Decisions go to `<round-dir>/decisions_cache.jsonl`, never the store, and `seal_decisions_cache` moves that cache to `archive/` read-only at close. That seal is not a dissent ledger.

`Router.handle(tool, args, turn)` is the entry. Tools: `read_doc`, `request_info` (`repo` / `rig` / `external`), `ask_claude_code`. Cascade L0 store, L1 file, L2 Tavily, L3 Claude Code, L4 `to_danny/questions.jsonl`. Paid levels go through `Router._once` (`acquire` / `lookup` / `release` / `wait_for`). Every call writes `flow_log.jsonl`. No second switch is added. This does not change the cascade design; it removes the excuse that the surface was unknown.

**Peer scores (section 3).** Still evidence, not a third gate, and still not part of the unbuilt verification step. Correction: they are not absent. Gate 1 already lets the teamwork file through as a landed reply. Absence of that file is not described as a hold. `ledger_score.py`'s precision and recall stay outside any pass line in this option. No quorum or floor is taken from them.

**Author equals checker (section 8).** D9 accepts Claude Code as both answerer and reviewer and records it in the `answered_by` trace. The code does not no-go that pair. Section 8's rule is stricter than D9 and is not what the harness does. It is not dropped, and D9 is not overturned by this reply. The conflict stays named: source-of-record versus authorship on the same item. An empty safeguard seat still does not authorise self-check. No one is appointed.

**Cost.** `costs_YYYY-MM.json` is month-only (`write_month`): no per-round or per-`run_id` grouping. Cost records do carry `source.run_id` and `source.ref`. Inside a round, `Store.spent()` returns `{usd, credits, fetch_usd, reply_usd}`. The manifest pointer is those, not an estimate and not a new unit. If a round is gone from the store and the monthly file cannot attribute it, the manifest says attribution is absent. D16 stands: Claude Code cost is the CLI-reported figure only (`cost_basis` `reported`). No spend limit.

**Section 6 package.** Gate 1 already decides `deliver` or `hold` on mechanical checks it has, and does not compare a recommendation to a prediction. The hand-off the human already receives is `handoff.run`'s files, not a findings-ledger line. Section 6's "one JSON object per line in the findings ledger" is not the existing hand-off. Findings items and gate 1 items are not linked. Withheld ids in the existing path are gate 1 holds under `held/<item>.json`, not the freeze set from section 2.

## Unchanged

- No invented threshold, quorum, expiry, score floor, retry limit, or reserved default.
- Silence is not resolution. There is still no dissent record to attach that rule to. Saying so is not a new record kind.
- A model-side pass is still not a findings write.
- Gate 1 does not decide merit, adoption, or what the human should do. Anticipation is still not a predicate.
- The verification step is the named gap: hash lock only, no parse, no prediction-versus-result gap, no packaging of that gap. This reply does not build it.
- Standing preamble hash, clean start, and no adoption from this reply still stand. This delta cites the late read of this round's own question, not a prior round's scores.