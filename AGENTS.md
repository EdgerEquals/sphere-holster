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
| Kimi (Moonshot API) | Free-tier rote checks: units, arithmetic, consistency vs `DESIGN_STATE.md`, retired items (`harness/KIMI_START.md`). On demand | `/kimi-check` → `.github/workflows/kimi-check.yml` |
| DeepSeek API | Free-tier rote checks, same role as Kimi (cheapest channel). On demand | `/deepseek-check` → `.github/workflows/deepseek-check.yml` |
| Tavily (web search) | **Shared web-search slot** for any model/Cursor. Rule: use it whenever a review/check needs current info or external sources. Kimi/DeepSeek search + filter first; Claude/Grok spend after. Grok reviews: 1 pre-search by default (xAI built-in search off) | `/tavily-search <query>` → `.github/workflows/tavily-search.yml` |
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
| Cheap rote pass before spending Claude/Grok (numbers, units, DESIGN_STATE consistency, retired items) | `/deepseek-check` (and/or `/kimi-check`) — optional, any time; never replaces Claude or Grok |
| A review or check needs current information or external sources (**general trigger rule**, canonical in `.cursor/rules/handoffs.mdc` rule 10) | Tavily. First the cheap filter: `gh workflow run deepseek-check.yml -f target_ref=<ref> -f search_query='<query>'` (or a `search: <query>` line under `/deepseek-check`); only then `/grok-check` (does its own 1 Tavily pre-search; `nosearch` opts out) / `/claude-audit`. Raw search: `gh workflow run tavily-search.yml -f query='<query>'` |
| Need a quick answer from Kimi or DeepSeek on a prompt (not a review) | `gh workflow run kimi-check.yml -f ping='<prompt>'` / `deepseek-check.yml` (reply in the job summary) |

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

# Free-tier rote checks (Kimi, DeepSeek): units, arithmetic, DESIGN_STATE.md consistency, retired items
gh pr comment <PR> --body "/deepseek-check"
gh pr comment <PR> --body "/kimi-check deep domains=thermal"
gh workflow run deepseek-check.yml -f depth=shallow -f target_ref=<branch-or-sha> [-f pr_number=<PR>]
gh workflow run kimi-check.yml     -f depth=shallow -f target_ref=<branch-or-sha> [-f pr_number=<PR>]

# Ping: send one prompt, get reply + token usage + cost in the job summary (no review, nothing posted)
gh workflow run kimi-check.yml     -f ping='reply with the word pong'
gh workflow run deepseek-check.yml -f ping='reply with the word pong'

# Shared web-search slot (Tavily). Without TAVILY_API_KEY: "not configured", no call, job passes.
gh workflow run tavily-search.yml -f query='<query>' -f max_results=5 -f search_depth=basic
gh pr comment <PR> --body "/tavily-search <query>"
gh workflow run deepseek-check.yml -f target_ref=<ref> -f search_query='<query>'   # search, then filter (query => on)
gh pr comment <PR> --body $'/grok-check\nsearch: PZT-4 longitudinal sound speed'   # Grok: Tavily query override
gh pr comment <PR> --body "/grok-check nosearch"                                    # Grok: no pre-search this run
id=$(gh run list -w deepseek-check.yml -L1 --json databaseId -q '.[0].databaseId'); gh run watch "$id"
gh run download "$id" -n "deepseek-ping-$id" -D /tmp/ping && cat /tmp/ping/ping.json   # reply, usage, cost

# End-of-iteration review (Claude Code)
git tag iter-<K>-start <sha> && git push origin iter-<K>-start     # at the START of each iteration
gh pr comment <PR> --body "@claude end-of-iteration review for iteration <K>: file issues for every problem and draft the next change"
gh workflow run claude-code-review.yml -f iteration=<K> -f since_ref=iter-<K>-start -f depth=deep

# Commit-message tags on main
git commit -m "Merge thermal+chemical outputs [round 6]"          # audited automatically (6 % 3 == 0)
git commit -m "Fix BTO Curie handling [audit] [deep]"             # force a deep audit
```

Comment syntax: first line must start with the trigger. Words after it, any order: `shallow` | `deep`, `cross`,
`domains=a,b` (or `domains=all`). `/kimi-check` and `/deepseek-check` take `shallow|deep` and `domains=` (no `cross`).

## Reading the results

- Verdicts are posted as a PR comment (or a new issue when there is no PR), headed `Claude review: PASS|FAIL` or
  `Grok review: PASS|FAIL`. The run fails (red check) on FAIL, on an API error, or when the API key secret is missing.
- Kimi / DeepSeek verdicts are headed `Kimi review:` / `DeepSeek review:`; same PASS/FAIL/ERROR rules.
- Machine-readable JSON: artifact `claude-verdict-<sha>` / `grok-verdict-<sha>` / `kimi-verdict-<sha>` /
  `deepseek-verdict-<sha>` (`gh run download <run-id>`).
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
- Electrodes of any kind (2026-10-19): Ti/Pt film, ITO / transparent-electrode case, central 50 µm wire / DBD centre electrode. There are no electrodes in the design. How the gas is driven without them is open for Danny; do not answer it.

## Protected conventions (locked 2026-10-19)

- **Kelvin reference:** the 293 K outer reference temperatures stay. Danny uses them to place thermal active materials in the tone. Do not replace them with required-conductance output (rejected, round 5).
- **Kelvin canonical:** calculations, the solver, data files and `DESIGN_STATE.md` use K. °C appears only in the GUI, alongside K. Reviewers flag any °C in calculations/solver/data/spec and any GUI temperature without its °C pair.
- **GUI ambient** is a linked K/°C pair: enter either, the other updates (K = °C + 273.15).
- Round-5 decisions (fold / cut / keep / defer): `DESIGN_STATE.md`, "Danny's decisions on round-5 review (2026-10-19)".

## Limits for every agent

- Do not edit `.github/workflows/` from an automated reviewer. Do not merge to main from a reviewer.
- Do not add Perplexity, or connect Qwen or any other reviewer, without Danny's go-ahead.
- A Kimi or DeepSeek PASS never counts toward "locked" / "validated"; that still needs deep Claude + Grok.
- Physics values carry a tag: [lit] / [rec] / [calc] / [est]. Viewer flags validity limits instead of fabricating results.
