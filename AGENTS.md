# AGENTS.md — information-layer handoffs (Stratified Sphere)

Spec: Drive doc "Stratified Sphere — Information Layer (Harness Architecture) 2026-10-19".
This file tells the **coordinator (Cursor)** exactly when and how to hand work to the reviewers.
Reviewers (Claude, Grok, Claude Code) read it too.

## Roles

| Who | Role | How it is reached |
|---|---|---|
| Danny | Direction and final decisions | Sees results only when something is ready or stuck |
| Stratified Sphere Bot | Holds intent, gatekeeper | Can trigger any reviewer the same way Cursor does |
| **Cursor** | Coordinator + builder: schedules rounds, merges domain outputs, decides convergence, reads the granularity dial | — |
| Claude API | Inner-loop audit of Cursor's merges, every few rounds | `/claude-audit` → `.github/workflows/claude-audit.yml` |
| Claude Code | End-of-iteration review: files issues, drafts the next change | `@claude` → `.github/workflows/claude-code-review.yml` |
| Grok (xAI API) | Source / physics-claim cross-check, **open channel** (any time) | `/grok-check` → `.github/workflows/grok-check.yml` |
| Perplexity | **Not used for now.** Do not add it. | — |

Six domains: optical, acoustic, electric, magnetic, thermal, chemical. Plasma is the source that drives them, not a domain.

## The loop

1. Cursor writes or edits a harness on a branch and opens/updates a PR.
2. Domain runs on Actions; Cursor merges the outputs into the PR branch. Each merge commit is one **round**: put `[round N]` in its message.
3. At audit points (below) Cursor hands off to Claude and Grok **in parallel**.
4. Both PASS → merge to `main` (GitHub Pages updates). Either FAIL → fix and go again with their notes.
5. At the end of an iteration → Claude Code review.

## Granularity dial (`harness/dial.yml`)

- `shallow` = scouting: cheap combined review, Sonnet / Grok with few search turns, diff capped at 60k chars.
- `deep` = validating: one call per touched domain + coordinator-merge, Opus / Grok with more search turns.
- Nothing may be described as **locked** or **validated** unless it has passed a `deep` Claude audit **and** a Grok check.

## When to hand off (rules)

| Situation | Hand-off |
|---|---|
| Every `audit_every_n_rounds` rounds (currently **3**: rounds 3, 6, 9…) | `/claude-audit` on the PR |
| Dial is `deep`, or you are about to call something locked/validated | `/claude-audit deep` **and** `/grok-check deep` |
| Any new or changed physics value, constant, material property, threshold or validity limit | `/grok-check` (any time, no round limit) |
| Before merging a PR to main | Latest `/claude-audit` and `/grok-check` on that PR must both be PASS |
| Claude and Grok disagree, or one FAILs what the other PASSed | `/claude-audit cross` and `/grok-check cross` (each gets the other's latest verdict) |
| End of an iteration | `@claude` end-of-iteration review (or `gh workflow run claude-code-review.yml`) |
| Push straight to main without a PR (avoid) | Include `[audit]` in the commit message to force an audit |

## Exact commands Cursor uses

Run these with `gh` (logged in as EdgerEquals). Comments must come from a user with write access; comments from
`github-actions[bot]` do not trigger workflows.

```bash
# Inner-loop audit (Claude API)
gh pr comment <PR> --body "/claude-audit"                         # dial default (shallow)
gh pr comment <PR> --body "/claude-audit deep"
gh pr comment <PR> --body "/claude-audit deep domains=thermal,chemical"

# Source / physics cross-check (Grok, open channel)
gh pr comment <PR> --body "/grok-check"
gh pr comment <PR> --body "/grok-check deep domains=acoustic"

# Mutual cross-check (each reviewer is given the other's latest verdict artifact for the same commit)
gh pr comment <PR> --body "/claude-audit cross"
gh pr comment <PR> --body "/grok-check cross"

# Same thing without a PR (posts an issue instead)
gh workflow run claude-audit.yml -f depth=deep -f target_ref=<branch-or-sha> [-f base_ref=main] [-f pr_number=<PR>] [-f mode=crosscheck]
gh workflow run grok-check.yml  -f depth=shallow -f target_ref=<branch-or-sha> [-f pr_number=<PR>] [-f domains=optical]

# End-of-iteration review (Claude Code)
git tag iter-<K>-start <sha> && git push origin iter-<K>-start     # at the START of each iteration
gh pr comment <PR> --body "@claude end-of-iteration review for iteration <K>: file issues for every problem and draft the next change"
gh workflow run claude-code-review.yml -f iteration=<K> -f since_ref=iter-<K>-start -f depth=deep

# Commit-message tags on main
git commit -m "Merge thermal+chemical outputs [round 6]"          # audited automatically (6 % 3 == 0)
git commit -m "Fix BTO Curie handling [audit] [deep]"             # force a deep audit
```

Comment syntax: first line must start with the trigger. Words after it, any order: `shallow` | `deep`, `cross`,
`domains=a,b` (or `domains=all`).

## Reading the results

- Verdicts are posted as a PR comment (or a new issue when there is no PR), headed `Claude review: PASS|FAIL` or
  `Grok review: PASS|FAIL`. The run fails (red check) on FAIL, on an API error, or when the API key secret is missing.
- Machine-readable JSON: artifact `claude-verdict-<sha>` / `grok-verdict-<sha>` (`gh run download <run-id>`).
- Act on every `blocker`/`major` finding before re-requesting review. Copy Claude's `claims_needing_source_check`
  into a `/grok-check` when Grok has not yet seen them.

## Retired items — must not be reintroduced

Reviewers FAIL any reintroduction. A deterministic scan (`harness/retired.txt`) also runs on added lines before any API call.

- Oil bath
- Slotted Cu/Ag shell
- Ribs / segments (ribbed or segmented shell construction)
- 6.75 kHz — allowed **only** when explicitly labelled as history
- 0.2 T
- 13 GHz atom-count ceiling
- Cold-regime work
- `Backwards_Derived_Spec_from_Ionisation` (do not cite, rebuild from, or restore)

## Limits for every agent

- Do not edit `.github/workflows/` from an automated reviewer. Do not merge to main from a reviewer.
- Do not add Perplexity or other paid reviewers without Danny's go-ahead.
- Physics values carry a tag: [lit] / [rec] / [calc] / [est]. Viewer flags validity limits instead of fabricating results.
