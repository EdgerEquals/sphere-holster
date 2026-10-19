# Holster review ledger (issues #7, #8, #9)

Locked by Danny on 2026-10-19 (review round 3); see `DESIGN_STATE.md`, "Locked holster architecture". No part of
this makes model calls except the dispatch-only `planted-live` scoring mode, which needs `confirm=spend`.

## Files
| Path | What |
|---|---|
| `findings.jsonl` | The ledger. Append-only JSON Lines, one record per line (`kind`: finding, status, mirror, cost, gateway_run). |
| `schema/finding.v1.schema.json` | Versioned JSON Schema for every record (`schema: ssm-ledger/v1`). |
| `scorecards.json`, `scorecards.md` | Reviewer scorecards (#8): status counts, acceptance rate, planted-mistake recall/precision. |
| `costs_YYYY-MM.json`, `costs_YYYY-MM.md` | Monthly cost rollup per model (#9). |
| `index.html` | Pages view of the cost tables and scorecards: https://edgerequals.github.io/stratified-sphere-model/ledger/ |
| `planted/v1/` | Planted-mistake fixture (`template.md`) and answer key (`keys.json`). |

Code: `scripts/ledger_lib.py` (core), `scripts/ledger.py` (CLI), `scripts/ledger_score.py`, `scripts/ledger_costs.py`,
`scripts/ledger_commit.sh`. Config: `harness/ledger.json`. Workflows: `ledger.yml`, `ledger-score.yml`, `ledger-costs.yml`.

## Storage decision: main, not a data branch
DeepSeek and Claude suggested a protected data branch with Issues as a mirror. The ledger lives on **main** instead:
- Pushes made with the workflow `GITHUB_TOKEN` do not trigger other workflows, so ledger appends cause no CI runs and
  can never fire a paid audit.
- The scorer, the cost rollup, the tests and GitHub Pages read the same tree as the code. A data branch would need
  its own checkout in every consumer, plus its own protection rules and sync.
- Append-only is enforced by code, not by branch settings. `append_records` only opens the file in append mode after
  validating and deduplicating. `scripts/ledger_commit.sh` checks before every push that the new file starts with the
  exact bytes on `origin/main` (`ledger.py verify-append-only`) and that every line validates. On a push race it
  resets, re-applies and retries, so concurrent appends never conflict.
- Issues are a mirror, as suggested: the JSONL is the record, and an issue never replaces a line in it.

## How findings flow
1. A review workflow (claude-audit, grok-check, kimi-check, deepseek-check) or the MCP gateway smoke test finishes.
   `ledger.yml` (workflow_run) downloads its artifacts and parses `verdict.json`, `ping.json`, `gateway_run.json`
   and Tavily `results.json` into records:
   - Findings are deduplicated by sha256 over (reviewer, domain, file, claim).
   - Every call also gets a cost record with tokens and USD, as reported by the API or computed from list prices.
2. Reviewer text is sanitised before it is stored:
   - Secret patterns are redacted.
   - Slash commands, bracket tags and at-mentions are defused; the config stores them only as parts.
   - HTML, comments, images and code fences are stripped, and length is capped.
   - Prompt-injection phrases are flagged in `injection_flags`.
3. Mirroring to issues is **off by default** (`file_issues.auto_on_workflow_run: false`). Dispatch `ledger.yml` with
   `action=mirror` to dry-run, or with `apply=true` to file. Only findings at or above `min_severity` (default major)
   are filed, up to `daily_cap` (default 5) new issues per UTC day. Each issue gets the labels `ledger`,
   `model:<x>`, `sev:<x>`, `domain:<x>` and `status:open`. Titles and bodies are checked again for trigger strings
   before posting.
4. Closing a ledger issue appends a status record:
   - Closed as completed = fixed.
   - Closed as not planned = rejected.
   - A `status:accepted`, `status:rejected` or `status:fixed` label overrides either.
   Scorecards then refresh.

The backfill (2026-10-19) holds rounds 1 to 3 plus every unexpired verdict, ping and Tavily artifact. Round replies
are prose, so their bold-led points are stored as severity `note` and nothing was mirrored to issues.

## Scoring (#8)
- `planted/v1` seeds eight mistakes into a lock-shell summary: two units, two arithmetic, two retired items and two
  contradictions of DESIGN_STATE. It also has two correct control lines.
- Retired items are stored as `{{RETIRED:n}}` placeholders, so the retired text never sits in the repo.
- A reviewer's findings are matched to the keys:
  - recall = keys caught / 8
  - precision = matched findings / (matched + unmatched non-note findings)
- **Offline (free):** dispatch `ledger-score.yml`, which defaults to `mode=offline`, or run
  `python scripts/ledger_score.py offline`.
- **Real scored run (paid):** dispatch `ledger-score.yml` with `mode=planted-live`, `reviewers=kimi,deepseek` (or
  any of claude, grok) and `confirm=spend`, or locally run
  `python scripts/ledger_score.py planted-live --reviewers kimi,deepseek --confirm spend`. The fixture is rendered
  into a throwaway local commit that is never pushed, and the unchanged `scripts/review_<name>.py` reviewers check
  it. Rough cost per run at shallow:
  - Kimi ~$0.02, DeepSeek ~$0.002, Claude ~$0.03, Grok ~$0.02
  - all four ~$0.07
  - Grok gets no search tools in this mode.

## Costs (#9)
`ledger-costs.yml` runs at 00:07 Perth time on the 1st of each month, and can also be dispatched. It ingests any
unexpired reviewer artifacts the ledger hasn't seen, then writes `costs_YYYY-MM.*` and `index.html`. Only spend that
reached the ledger is counted. Ad-hoc local calls outside the harness are not, unless they are saved as a
`reviews/*` round.
