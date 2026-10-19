# Staged ledger records

`findings.jsonl` is written only by CI (`ledger.yml`), so decisions recorded locally are staged here first.
Each line is a wrapper: `{staged, decided_by, decided_on, disposition, reason, finding, status}`.
`finding` and `status` are schema-valid ledger records; `status.status` equals `disposition`
(accepted / fixed / rejected / deferred / superseded). `deferred` and `superseded` status records use
`ssm-ledger/v1.2` and carry a `note` (reason, revisit condition, or what removed the target).

Ingest: a push to main touching `ledger/pending/**` triggers `ledger.yml`, which runs
`python scripts/ledger.py ingest-staged` and commits through `scripts/ledger_commit.sh` (append-only check, retry).
Lines are validated first (`ledger_lib.parse_staged_line`); refused lines are reported and skipped. Re-ingest is a
no-op. Locally, `python scripts/ledger.py ingest-staged --dry-run` shows what CI would append; without `--dry-run`
it refuses outside Actions on main. Files stay here after ingest as the decision record.

- `2026-10-19_round5_dispositions.jsonl`: Danny's decisions on the round-5 review (see `DESIGN_STATE.md`).
  Fold 6 (ring-jump fix) and the ionisation-window item are `superseded` (that code was removed with the electrodes,
  2026-10-19); the five deferred items are `deferred`.
