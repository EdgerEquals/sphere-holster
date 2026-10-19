# Reviewer scorecards

Ledger as of 2026-10-19T06:41:06Z, from `ledger/findings.jsonl` (issue #8).

Acceptance = (accepted + fixed) / (accepted + fixed + rejected), from closed ledger issues. Planted = the latest planted-mistake run against `planted-v1` (recall = seeded mistakes caught / planted).

| Reviewer | findings | open | accepted | fixed | rejected | acceptance | planted recall | planted precision | planted runs |
|---|---|---|---|---|---|---|---|---|---|
| Claude | 28 | 28 | 0 | 0 | 0 | n/a | not run | not run | 0 |
| Grok | 15 | 15 | 0 | 0 | 0 | n/a | not run | not run | 0 |
| Kimi | 10 | 10 | 0 | 0 | 0 | n/a | not run | not run | 0 |
| DeepSeek | 16 | 16 | 0 | 0 | 0 | n/a | not run | not run | 0 |

Spec-review findings (no execution receipt) are excluded from every number above; legacy = before the receipt gate. Excluded per reviewer: Claude 0, Grok 0, Kimi 0, DeepSeek 0.

## Planted receipt cases (`ledger/planted/v1/receipts`): all rejected

| case | kind | rejected | reason |
|---|---|---|---|
| fake-edited | fake receipt | yes | digest mismatch: evidence was altered or hand-written |
| fake-unsigned | fake receipt | yes | attestation not verified: no attestations found |
| stub-locked-io | stub receipt | yes | target source of solver_v0.py:l0_modes is a stub; target source of solver_v0.py:propagate is a stub; target source of so |
| stub-claimed | stub receipt | yes | stub entrypoint (or no stub check recorded) |
