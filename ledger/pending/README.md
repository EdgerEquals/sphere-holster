# Staged ledger records (not ingested)

`findings.jsonl` is written only by CI (`ledger.yml`), so decisions recorded locally are staged here first.
Each line is a wrapper: `{staged, decided_by, decided_on, disposition, reason, finding, status}`.
`finding` and `status` are schema-valid `ssm-ledger/v1` records (`status` is null for **deferred**,
because the v1 status enum has no "deferred"; those findings stay `open`). Nothing here is read by any
workflow; ingesting it means appending the inner records through the ledger's append path.

- `2026-10-19_round5_dispositions.jsonl`: Danny's decisions on the round-5 review (see `DESIGN_STATE.md`).
