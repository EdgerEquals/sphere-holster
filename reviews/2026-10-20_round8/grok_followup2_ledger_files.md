<!-- follow-up: reviewer=grok · model=grok-4.7 · channel=scripts/review_grok.py tool loop (scratch runner) · run_id=followup-20261020T144256Z-grok-ledger-files · generated_utc=2026-10-20T14:42:56Z · finish=completed · source=/tmp/r8_grok_followup2/grok/ping.json -->

# Grok

These files change the round 8 reply and the first follow-up. The design option is still not adopted. Nothing below is a schema, a cutoff, or a wire-up.

## Changes

**`run.json` (this round).** The unverified-contents gap is closed, and the beforehand-lock claim narrows. This file has `primary` and `teamwork` only: `run_id`, `started_utc`, `cc_export`, and on teamwork a `primary_run_id`. It has no `predictions_sha256`, no seal, and no item state. Absence matches “stored only if the predictions file exists”; it does not show that the lock ran. This round is two run ids, not one fire boundary. The withdrawn landed-reply boundary stays withdrawn.

**Schema required fields.** That gap is closed. Always required: `schema`, `kind`, `id`, `recorded_utc`, `source` (`type`, `ref`). Kind-specific requirements match the `allOf` blocks (finding, status, mirror, cost, gateway_run, receipt, class). Statuses are only `open`, `accepted`, `rejected`, `fixed`, `deferred`, `superseded`. `deferred` and `superseded` require `schema` `ssm-ledger/v1.2` and a `note`. There is no `held`, `blocked`, `depends-on`, disagreement, seal, or hand-off kind. `finding_id` is a back-reference, not a dependency edge. Sections 2 and 4 stay unwired. I am not putting dissent into `claim`.

**CI write claim.** `ingest-staged` refuses unless `GITHUB_ACTIONS=true` and `GITHUB_REF=refs/heads/main`, which matches the schema note that pending decisions come from CI. This file does not put that check on `append-file`, `backfill`, `status`, `mirror`, `classify-legacy`, or `ingest`. Whether `ledger_lib` refuses those is not in this paste. Models are still not a writer on the router surface already read. “Every append is CI-gated” is not what this file shows.

**Cost.** `ledger/costs_2026-10.json` is a month rollup by reviewer and `review_class`, generated `2026-10-19T11:44:47Z`. Round 8 starts `2026-10-20T10:35:05Z`. This round’s spend is absent from the only costs file, not merely ungrouped. Rows have no `run_id`. The schema allows `source.run_id` on a cost record; on-disk lines are not here, so per-record attribution stays unconfirmed. List prices are `harness/ledger.json` `prices_usd_per_mtok`. The manifest still says attribution is absent. No estimate, no new unit, no spend limit.

**Existing numeric config, not adopted.** `harness/ledger.json` and `ledger.py` mirror already have `daily_cap` 5, `min_severity` `major`, and sanitise `max_text_chars` 1500. Those are issue-filing and sanitise limits. They are not a gate-1 pass line, a quorum, a freeze rule, or a safeguard score. The ban on inventing thresholds stands. I am not deleting or reusing these.

**Hand-off vs ledger.** Unchanged conclusion, now schema-backed: findings lines are not `handoff.run`’s files, and nothing here links them.

## Unchanged

No new threshold, quorum, expiry, score floor, or reserved default. Silence is still not resolution; there is still no dissent record. Gate 1 still does not decide merit, adoption, or what the human should do. Peer `review_verdict` and planted-run fields are evidence fields in the schema, not a pass line in this option. Author-equals-checker is still not what these files enforce, and still not dropped. No one is appointed. Clean start and no adoption from this reply still stand.

## Still unseen

`ledger/findings.jsonl` is not in the paste. `ledger_lib` (append, dedup, `verify_append_only`) is called here and not defined here. On-disk prediction files, gate-1 outputs, and hand-off files for this round are not in this paste.

Cross-review is still not done. The other replies are not in front of me.