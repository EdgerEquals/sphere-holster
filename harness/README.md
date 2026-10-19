# harness/ — information-layer review config

| File | Purpose |
|---|---|
| `dial.yml` | Granularity dial (`shallow` scouting / `deep` validating): models, `max_tokens` caps, diff caps, calls per review, audit interval |
| `retired.txt` | Retired items + regexes; scanned on added diff lines before any API call (free) and given to every reviewer |
| `prompts/_base.md` | Common reviewer rules + JSON verdict format |
| `prompts/{optical,acoustic,electric,magnetic,thermal,chemical}.md` | Per-domain review focus. Architecture (Danny, 2026-10-19): 7 energy domains (these six + information) and 12 knees, each with its own holster = 19 holsters. **Gap:** there is no `prompts/information.md` and no `information` entry in `dial.yml` `domains:` yet; not built here. |
| `prompts/coordinator-merge.md` | Always applied: checks Cursor's merge (the biggest single risk) |
| `prompts/crosscheck.md` | Added in cross-check mode (reviewer gets the other's latest verdict) |
| `prompts/_grok_source_check.md` | Grok's source-check role (web search, URLs per claim) |
| `prompts/_rote_check.md` | Kimi / DeepSeek free-tier rote-check role (units, arithmetic, DESIGN_STATE.md consistency, retired items) |
| `KIMI_START.md` | Paste-in starter for a Kimi chat session (same rote-check role, by hand) |
| `receipts.json` | Execution-receipt components (round 4): producing workflow, files, entrypoints, check format per component |

Scripts: `scripts/review_claude.py`, `scripts/review_grok.py`, `scripts/review_kimi.py`, `scripts/review_deepseek.py`
(stdlib only; PyYAML optional), shared code in `scripts/harness_common.py` (+ `scripts/oai_compat.py` for the
OpenAI-compatible Kimi/DeepSeek channels). Local use: `ANTHROPIC_API_KEY=... python3 scripts/review_claude.py --depth shallow --head HEAD`.
Exit codes: 0 = verdict recorded (PASS or FAIL), 2 = API key missing (nothing called, nothing billed), 3 = API/parse error.

## Models (verified 2026-10-19)

- Claude audit: `claude-sonnet-5-5` (shallow), `claude-opus-5-5` (deep); Claude Code: `claude-opus-5-5`.
  Source: https://docs.claude.com/en/docs/about-claude/models/overview
- Grok: `grok-4.7` via `https://api.x.ai/v1/responses` (streamed). Web search comes from one Tavily pre-search
  (cheaper); xAI's built-in `web_search` tool is off (`grok_web_search: false`; set true to re-enable). Sources: https://docs.x.ai/docs/models,
  https://docs.x.ai/docs/guides/tools/search-tools
- Kimi: `kimi-k2.6` via `https://api.moonshot.ai/v1/chat/completions` (streamed). It thinks even on trivial prompts,
  so `kimi_max_tokens` stays >= 12000. `kimi-k3` is also listed but pricier; not used. Source:
  https://platform.moonshot.ai/docs/pricing/chat
- DeepSeek: `deepseek-flash` (shallow), `deepseek-v4-pro` (deep) via `https://api.deepseek.com/chat/completions`
  (streamed, thinking on by default). Source: https://api-docs.deepseek.com/quick_start/pricing
- Override per run without editing files: env `CLAUDE_MODEL` / `GROK_MODEL` / `KIMI_MODEL` / `DEEPSEEK_MODEL`.

## Kimi + DeepSeek channels (free-tier rote checks, on demand)

Role per `KIMI_START.md`: units and arithmetic, consistency against `DESIGN_STATE.md` (sent with every call),
reintroduced retired items. No physics sourcing (Grok) and no design audit (Claude). Never run on push.

- PR / issue comment (owner/member/collaborator only): `/kimi-check [shallow|deep] [domains=a,b]`, `/deepseek-check ...`
- Without a PR (opens an issue): `gh workflow run kimi-check.yml -f depth=shallow -f target_ref=<ref> [-f pr_number=<PR>]`
- **Ping** (no review, nothing posted; reply + input/output/reasoning tokens + cost go to the job summary and a
  `<reviewer>-ping-<run id>` artifact): `gh workflow run deepseek-check.yml -f ping='reply with the word pong'`.
  The ping job also lists the model IDs the key can see.
- Shared workflow: `.github/workflows/review-core-rote.yml` (separate from `review-core.yml`, which Claude/Grok use).
- Any failure (HTTP error, timeout, empty reply, unparseable verdict) gives verdict **ERROR**, still posts, and fails the job.

## Shared web-search slot (Tavily)

One search slot shared across all holsters (19: 12 knee + 7 energy-domain): any model, Cursor or the bot can use it. Script `scripts/tavily_search.py`
(stdlib, `POST https://api.tavily.com/search`, Bearer auth), workflow `.github/workflows/tavily-search.yml`.

- Search on its own: `gh workflow run tavily-search.yml -f query='<query>' [-f max_results=5] [-f search_depth=basic]`,
  or comment `/tavily-search <query>` on an issue/PR (owner/member/collaborator only; replies with the results).
  Results (title, URL, snippet) go to the job summary, stdout and the `tavily-results-<run id>` artifact.
- Reuse from another workflow: `uses: ./.github/workflows/tavily-search.yml` with `query`; outputs `status`, `count`,
  `results_json`. Locally: `TAVILY_API_KEY=... python3 scripts/tavily_search.py --query '<query>'`.
- **General trigger rule** (canonical: `.cursor/rules/handoffs.mdc` rule 10): whenever a review or check needs current
  information or external sources, use Tavily. **Order of spend:** Kimi/DeepSeek go through Tavily and filter
  **first**; Claude/Grok spend only after that filter (round-2 recommendation, `reviews/2026-10-19_round2/`).
- Kimi/DeepSeek: a run that gives a query searches: `gh workflow run deepseek-check.yml -f target_ref=<ref>
  -f search_query='<query>'`, or a line `search: <query>` under `/deepseek-check` (or `/kimi-check`). `-f web_search=false`
  forces it off; with no query it follows `tavily.enabled` (false). Results go into the cheap model's context as
  unverified third-party text.
- Grok: **one Tavily pre-search per review, on by default** (`tavily.grok_presearch: true`, max 5 results, basic,
  1 credit). Query = `search: <query>` comment line or `search_query` input, else derived from the PR title / commit
  subject + changed file names. xAI's built-in web search is off (`grok_web_search: false`), and Grok is told to cite
  only URLs from the Tavily results. Opt out per run: `/grok-check nosearch` or `gh workflow run grok-check.yml
  -f web_search=false`; globally: `tavily.grok_presearch: false`. The step lives in `review-core.yml` but is gated
  `reviewer == 'grok'`, so Claude runs are unchanged. Results are in the Grok verdict artifact under `tavily/`.
- Missing `TAVILY_API_KEY` or a Tavily error: every Tavily step skips quietly (`not configured`) and never fails a job.
- Claude is not wired to Tavily (Claude files unchanged). Follow-up (docs only, not built): pass the Kimi/DeepSeek
  search artifact to `/claude-audit`.
- Cost: basic/fast = 1 credit, advanced = 2; free plan 1,000 credits/month, no card
  (https://docs.tavily.com/documentation/quickstart). Key from https://app.tavily.com.

## Receipt gate (round 4, locked 2026-10-19)

Paid reviews (Claude, Grok) only count as **code reviews** when CI has proved the reviewed code really runs.

- **Receipt** = ledger record `kind: receipt` (schema v1.1): commit sha, component, CI job + result, sha256 of the
  canonical evidence file, run id/url, target files/entrypoints, stub check, line-trace coverage, numeric checks.
  Written only by `.github/actions/receipt` inside the component's own workflow on main, signed with a GitHub artifact
  attestation, and appended only by `ledger.yml` after `gh attestation verify` (signer workflow, `refs/heads/main`,
  source commit). There is no local, Cursor or reviewer write path: `scripts/receipt.py emit` refuses outside
  Actions, `ledger.py ingest` refuses receipts outside the ledger workflow, and the gate re-verifies the signature.
- **Components** (`receipts.json`): `compute-core` (engineering-tests; `solver_v0.py` l0_modes/propagate/c_hho,
  SymPy locked values), `sim-fenics` (sim-stack; `sim/fenics/smoke_fenics.py`), `mcp-gateway` (mcp-gateway;
  `gateway/ssm_mcp_server.py` handle/call_tool/run_smoke over MCP in the hardened container). A receipt is emitted on
  dispatch/schedule, or on a push that changed the component's files; it stays valid while those files are unchanged.
- **Anti-stub rule** (Kimi's round-4 concern): no receipt unless every entrypoint (a) is not a stub by AST (body only
  `pass` / `...` / `raise NotImplementedError` / returns a constant or its own argument), (b) actually executed
  (`scripts/exec_trace.py`: at least 3 body lines, or half a module), (c) raised no NotImplementedError, and (d) the run
  has ≥1 passing numeric check and no failing check. Fails closed. Planted `fake receipt` and `stub receipt` cases
  (`ledger/planted/v1/receipts/`) are part of the #8 rubric and must all be rejected (`ledger/scorecards.md`).
- **Gate** (`scripts/receipt_gate.py`, job `receipt` in `review-core.yml`, before the paid `review` job):
  code-review if every touched component has a valid receipt; otherwise spec-review. Docs/spec-only diffs are always
  spec-review. `dial.yml` `receipt_gate`: `enforce` (default: spec-review skips the paid model and dispatches
  `spec_review_route`, default DeepSeek), `warn` (paid runs, annotated), `off` (no routing). The class is recorded in
  every case.
- **Dispatch input `spec_review`** on claude-audit / grok-check: `auto` (receipt decides), `spec-review` (force a
  spec review, e.g. a cross-cutting DESIGN_STATE review; cheap route), `spec-review-paid` (spec review on the paid
  model). `gate_dry_run=true` only reports the decision: no review, no dispatch, no model call.
- **Effect downstream:** verdict artifacts carry `review_class.json`; the ledger stamps `review_class` on findings and
  costs; the scorer excludes spec-review from scorecards and planted precision/recall; mirroring skips spec-review;
  the monthly cost rollup splits spend by class. Findings from before the gate are `legacy` (no receipt).

Local inspection (read-only, no write path): `python scripts/receipt_gate.py decide --head <sha> --no-attest`,
`python scripts/stub_detector.py solver_v0.py:l0_modes`.

## Costs

- **GitHub Actions minutes: free.** The repo is public, and standard GitHub-hosted runners are free for public repos.
  (Private repo: 2,000 free minutes/month on Free plans, then well under a cent per minute on standard Linux runners.)
- **API tokens are billed separately** by Anthropic (`ANTHROPIC_API_KEY`), xAI (`XAI_API_KEY`), Moonshot (`MOONSHOT_API_KEY`)
  and DeepSeek (`DEEPSEEK_API_KEY`), per token, to whoever owns the key.
  List prices at setup (per million tokens, input/output): Sonnet 5.5 $2/$10, Opus 5.5 $4/$20, Grok 4.7 $2/$6 (<200k prompt),
  kimi-k2.6 $0.95/$4 (cached in $0.16), deepseek-flash $0.30/$1.20 peak, half off-peak; deepseek-v4-pro $1.32/$3.96 peak,
  half off-peak (peak = 01:00–04:00 and 06:00–10:00 UTC Mon–Fri). Reasoning tokens bill as output.
  xAI also bills server-side web-search tool calls on top of tokens (off by default now; Grok uses Tavily instead).
- **Caps** (edit `dial.yml`):
  - `claude_max_tokens` is a hard cap on Claude's output **including adaptive thinking**; `claude_effort` (low|medium|high) steers how much it thinks. Too small a cap with high effort returns no verdict (first smoke test hit this at 6000).
  - `grok_max_tokens` caps Grok's visible output (`max_output_tokens`); xAI does not count reasoning tokens against it, so
    `grok_reasoning_effort` (low|medium|high|xhigh; xAI default is high) and `grok_max_turns` (agentic search turns)
    are the main Grok cost and latency levers. `grok_max_diff_chars` trims the diff Grok sees.
  - Grok calls stream (SSE): `grok_idle_timeout_s` fails the call if no bytes arrive for that long, `grok_deadline_s`
    is a hard wall-clock cap. (The first smoke test, non-streaming at default high effort on a 95k-char diff,
    hit a 10-minute read timeout.)
  - `max_diff_chars` caps the prompt size; `max_calls` caps calls per review.
  - Push-to-main audits run only every `audit_every_n_rounds` rounds or on `[audit]`, never on every push.
  - Comment triggers only work for the repo owner/members/collaborators, so strangers cannot spend the keys.
- **Rough per-run estimates [est]:** shallow Claude ≈ $0.05–0.15; deep Claude (up to 7 Opus calls, diff cached) ≈ $0.50–3;
  shallow Grok ≈ $0.05–0.20; deep Grok ≈ $0.30–1.50 (plus 1 Tavily credit; xAI search fees only if grok_web_search is re-enabled); shallow Kimi ≈ $0.02–0.06;
shallow DeepSeek < $0.01; deep Kimi / DeepSeek (up to 7 calls) ≈ $0.10–0.40; a ping < $0.001; one Claude Code end-of-iteration run
  (Opus, ≤30 turns) ≈ $1–5. Check real spend in the Anthropic and xAI consoles and set monthly spend limits there.

## Secrets (referenced, not created here)

- `ANTHROPIC_API_KEY` — claude-audit and claude-code-review.
- `XAI_API_KEY` — grok-check.
- `DEEPSEEK_API_KEY` — deepseek-check (free/cheap tier).
- `MOONSHOT_API_KEY` — kimi-check (Moonshot AI developer API, billed separately from the kimi.com membership).
- `TAVILY_API_KEY` — tavily-search, the Grok pre-search and the optional Kimi/DeepSeek pre-search (set 2026-10-19). Unlike the others, a missing
  Tavily key is not an error: those steps report `not configured` and the job passes.
If a secret is missing the run stops before any API call, posts/prints a clear "secret not set" message and fails the check.
