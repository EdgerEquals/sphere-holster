# Context pack — Stratified Sphere: holster (harness) layer and information layer
Repo: github.com/EdgerEquals/stratified-sphere-model (public). State as of 2026-10-19 13:05 AWST, main = 8ff1f79.
Scope of this review: how the harness/information layer is DESIGNED and BUILT — not the physics.

## A. Spec (Drive doc "Information Layer (Harness Architecture) 2026-10-19", from a voice call 10:55–11:20 AWST)
- "Holster" = harness: scaffolding around a model that feeds inputs, manages context, collects outputs. "So this is our information layer now." It mirrors the physics cascade: each layer pumps into the next.
- Locked in the spec:
  - Six domain harnesses (optical, acoustic, electric, magnetic, thermal, chemical), parallel on GitHub Actions, passing results between rounds because domains are coupled (e.g. chemical heat feeds thermal).
  - Twelve knee harnesses (one per "knee", each tracking the energy it moves and which domain it feeds) → 18 harnesses + a coordinator.
  - Coordinator = Cursor: schedules rounds, merges outputs, decides convergence, reads a granularity dial tied to sweeps (shallow = scouting, deep = validating).
  - Validation harness: tracks every handover (who passed what to whom, when, whether the checker signed off); does no checking itself.
  - Review: Claude API = inner-loop domain audits + checks coordinator merges every few rounds; Claude Code = end-of-iteration reviews (files issues, drafts next change); Grok = source cross-check; Grok and Claude check each other.
  - Loop: (1) Cursor writes/edits a harness → (2) coordinator dispatches to domain runners on Actions → (3) merge → (4) Claude audit + Grok source check in parallel → (5) both PASS → main + GitHub Pages; either FAIL → back to Cursor. Danny only sees results when ready or stuck.
  - Tiers (spec): Danny → Stratified Sphere Bot (intent, gatekeeper) → paid reviewers (Claude, Grok, ChatGPT; Perplexity sparingly) → harnesses → free tiers (Kimi, DeepSeek, Qwen/Qwen Studio, local Llama). Practical depth 4–5 layers; deeper adds delay and tokens faster than accuracy.
  - Compute: SymPy, SciPy, C. Engineering models (FEniCS, MEEP, OpenFOAM, COMSOL/ANSYS) called when a harness flags something the simple model can't handle.
- Not yet explored (spec): one repo vs several; who does reporting ("Cursor or another holster", unsettled); Julia; a loss map per handover ("the coordinator's merge is the biggest single risk"); a real cost budget; keeping Kimi step-by-step; knee-harness details; which harness to build first (thermal suggested, paused).

## B. Danny's current framing (supersedes parts of A)
- SEVEN domains: optical, acoustic, electric, magnetic, thermal, chemical, and **information** as the seventh.
- Layer ladder (top down): Danny → Stratified Sphere Bot and "Plex" (Danny's name for that tier; note Perplexity itself is currently held out of the API reviews) → Claude and Grok → Cursor (build layer) → GitHub (source of truth: DESIGN_STATE.md + repo) → paid then free model tiers (Kimi, DeepSeek; Qwen not connected) → engineering models alongside.
- Known mismatch: the spec and DESIGN_STATE still say 6 domain harnesses / 18 total; the seventh (information) domain has no harness definition yet. ChatGPT appears in the spec's paid tier but is not connected.

## C. What is actually built (API-key harness)
- Repo secrets: ANTHROPIC_API_KEY, XAI_API_KEY (both used by workflows); MOONSHOT_API_KEY, DEEPSEEK_API_KEY (stored, used only by local review-round scripts; no workflows).
- Workflows:
  - `claude-audit.yml` → reusable `review-core.yml`: Claude Messages API audit of a diff. Triggers: PR/issue comment `/claude-audit [shallow|deep] [cross] [domains=a,b]` (owner/member/collaborator only), workflow_dispatch, push to main only if commit message has `[audit]`, or `[round N]` with N % 3 == 0 (`[deep]` forces deep). Verdict PASS/FAIL JSON → PR comment or issue + artifact `claude-verdict-<sha>`.
  - `grok-check.yml` → same core, xAI Responses API with web_search; `/grok-check`, dispatch; no push trigger. Cross-check mode: each reviewer downloads the other's newest verdict artifact (same SHA preferred) and must agree/disagree per finding.
  - `claude-code-review.yml`: anthropics/claude-code-action@v1 on `@claude` mentions or dispatch (iteration, since_ref): files issues, drafts next change on a `claude/iter-K-next` branch as a draft PR; never edits workflows or pushes to main. Uses GITHUB_TOKEN (repo variable CLAUDE_USE_GITHUB_TOKEN=true), not the Claude GitHub App.
  - `engineering-tests.yml`: pytest + SymPy re-derive locked values on every push/PR; expected-vs-got table in job summary.
  - `sim-stack.yml`: one job per engineering tool, pinned, analytic smoke tests (see E).
- `harness/dial.yml` granularity: shallow = claude-sonnet-5-5 effort medium, 16k max_tokens, 1 combined call, 60k-char diff cap; Grok grok-4.7 reasoning low, 4k visible output, 3 search turns, 30k diff cap, streaming with 180 s idle / 900 s deadline. deep = claude-opus-5-5 effort high 32k, one call per touched domain + coordinator-merge (max 7); Grok reasoning medium, 8 turns. Audit interval: every 3 rounds. Domain routing = keyword match on file paths and added lines.
- Prompts: `harness/prompts/` — _base (verdict JSON schema, value tags [lit]/[rec]/[calc]/[est]), one per domain (6 physical domains; no "information" prompt), coordinator-merge (always applied; loss-map checks), crosscheck, _grok_source_check.
- `harness/retired.txt`: regex list of retired items (oil bath, slotted Cu/Ag shell, ribs/segments, 6.75 kHz except as history, 0.2 T, 13 GHz atom-count ceiling, cold-regime work, Backwards_Derived_Spec_from_Ionisation); scanned deterministically on added diff lines before any API call (free) and given to reviewers. (DESIGN_STATE also retires "Grok's radial diamond spokes", not yet in retired.txt.)
- `harness/KIMI_START.md`: paste-in session starter for Kimi as free-tier checker: read DESIGN_STATE raw URL; rote checks only (units, arithmetic, consistency, retired items, diff summaries); "work one step at a time… do step 1, then stop and wait for 'next'"; PASS/FAIL first line; "UNSURE" rather than guess. Manual (chat), not automated.
- `harness/locked_values.yml` + `tests/`: each expected value parsed live from a cited DESIGN_STATE/docs line; SymPy derivations (exact spherical-shell l=0 modes, HHO c = √(γRT/M)) checked against the doc and against solver_v0.py. 17 tests pass in CI.
- `AGENTS.md` + `.cursor/rules/handoffs.mdc`: tell Cursor when to hand off (every 3rd round, deep dial, any new physics claim → Grok, both PASS before merge, disagreement → cross, iteration end → @claude).
- Today's fixes:
  1. Claude audit returned no verdict: adaptive thinking consumed the whole 6000 max_tokens. Fix: set output_config.effort, raise caps to 16k/32k, explicit error if cap is hit with no text.
  2. Grok call hit a 10-min socket timeout (non-streaming, default high reasoning, 95k-char diff). Fix: SSE streaming with idle/deadline timeouts, reasoning low for shallow, diff trim; a prose-only reply gets one cheap tool-free "reformat to JSON" call.
  3. A crashed reviewer showed a green job. Fix: any non-zero exit or any verdict other than PASS fails the job, and a fallback ERROR verdict is still uploaded and posted.
  4. Cross-check picked an old artifact (GitHub's artifact list isn't date-ordered). Fix: sort by created_at.
- Smoke-test costs: Claude shallow audit ≈ $0.02; Grok shallow ≈ $0.12–0.24 (web search dominates). Actions minutes are free (public repo).
- NOT built yet: the 6/7 domain harnesses, 12 knee harnesses, the validation (handover-tracking) harness, the coordinator's dispatch/merge/convergence loop, any loss map, a cost budget, reporting, automated free-tier calls.

## D. Four-model review workflow (round 1, 12:55–13:00 AWST)
- Local script `reviews/<date>_roundN/run_round.py`: same prompt to Claude (sonnet-5-5, effort medium), Grok (4.7, reasoning low, no search), Kimi (k2.6, thinking on), DeepSeek (flash, thinking on); streamed with timeouts; retry once with more headroom if thinking eats the reply; cost from published list prices (DeepSeek peak/off-peak by UTC hour); raw replies + table committed to the repo. Commit messages avoid `[audit]`/`[round N]`/`[deep]` so pushes don't start paid audits.
- Round 1 subject: DESIGN_STATE.md internal consistency. Result: all four FAIL; total $0.088 (Kimi $0.050 incl. one empty 6000-token reasoning-only reply; Claude $0.018; Grok $0.017; DeepSeek $0.0035).
- Agreed findings: 3.236 MHz value lacks recorded formula/sound speed (all 4); incoherent power envelope (7.5 kW shell cap vs ~10 W BTO Curie, 8–80 W phosphor saturation, 1 W autoignition, open heat path) (all 4); φ-step scope contradiction (3/4); tourmaline thickness both locked and open (3/4).
- Not yet done with the results: no automatic issue filing, no tracking whether DESIGN_STATE was fixed, no scoring of reviewer quality.

## E. Simulation / engineering stack
- In requirements.txt (CI-tested): numpy 2.5.4, scipy 1.18.1, sympy 1.14.0, mpmath 1.3.0, pytest 9.1.1, PyYAML 6.0.3. `solver_v0.py` (radial coupled solver) imports numpy + scipy.
- `sim-stack.yml` (push to sim/**, manual, weekly), all six PASS as of 2026-10-19:
  - FEniCSx / DOLFINx 0.11.0 (Docker, digest-pinned): Poisson + 1D heat vs analytic.
  - MEEP 1.35.0 (conda-forge): 2D PEC cavity TM11/TM21 within 0.5%.
  - OpenFOAM v2512 (Docker, digest-pinned): icoFoam lid-driven cavity.
  - CalculiX 2.21 (apt): cantilever vs PL³/3EI, 2%.
  - Code_Aster 18.1.0 (Docker, digest-pinned): beam cantilever + bundled forma01a.
  - Gwyddion 2.64 (apt): load .gsf, size + RMS check (C loader built with gcc).
- C: no dedicated C compute module yet (only the Gwyddion loader). COMSOL/ANSYS: "when needed", not connected (licensed).
- Smoke tests prove the tools run; none is yet wired to the sphere model or to a domain harness.
