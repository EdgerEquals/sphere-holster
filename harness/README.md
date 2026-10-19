# harness/ — information-layer review config

| File | Purpose |
|---|---|
| `dial.yml` | Granularity dial (`shallow` scouting / `deep` validating): models, `max_tokens` caps, diff caps, calls per review, audit interval |
| `retired.txt` | Retired items + regexes; scanned on added diff lines before any API call (free) and given to every reviewer |
| `prompts/_base.md` | Common reviewer rules + JSON verdict format |
| `prompts/{optical,acoustic,electric,magnetic,thermal,chemical}.md` | Per-domain review focus |
| `prompts/coordinator-merge.md` | Always applied: checks Cursor's merge (the biggest single risk) |
| `prompts/crosscheck.md` | Added in cross-check mode (reviewer gets the other's latest verdict) |
| `prompts/_grok_source_check.md` | Grok's source-check role (web search, URLs per claim) |
| `prompts/_rote_check.md` | Kimi / DeepSeek free-tier rote-check role (units, arithmetic, DESIGN_STATE.md consistency, retired items) |
| `KIMI_START.md` | Paste-in starter for a Kimi chat session (same rote-check role, by hand) |

Scripts: `scripts/review_claude.py`, `scripts/review_grok.py`, `scripts/review_kimi.py`, `scripts/review_deepseek.py`
(stdlib only; PyYAML optional), shared code in `scripts/harness_common.py` (+ `scripts/oai_compat.py` for the
OpenAI-compatible Kimi/DeepSeek channels). Local use: `ANTHROPIC_API_KEY=... python3 scripts/review_claude.py --depth shallow --head HEAD`.
Exit codes: 0 = verdict recorded (PASS or FAIL), 2 = API key missing (nothing called, nothing billed), 3 = API/parse error.

## Models (verified 2026-10-19)

- Claude audit: `claude-sonnet-5-5` (shallow), `claude-opus-5-5` (deep); Claude Code: `claude-opus-5-5`.
  Source: https://docs.claude.com/en/docs/about-claude/models/overview
- Grok: `grok-4.7` via `https://api.x.ai/v1/responses` with the `web_search` tool (falls back to
  `/v1/chat/completions` if `grok_web_search: false`). Sources: https://docs.x.ai/docs/models,
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

## Costs

- **GitHub Actions minutes: free.** The repo is public, and standard GitHub-hosted runners are free for public repos.
  (Private repo: 2,000 free minutes/month on Free plans, then well under a cent per minute on standard Linux runners.)
- **API tokens are billed separately** by Anthropic (`ANTHROPIC_API_KEY`), xAI (`XAI_API_KEY`), Moonshot (`MOONSHOT_API_KEY`)
  and DeepSeek (`DEEPSEEK_API_KEY`), per token, to whoever owns the key.
  List prices at setup (per million tokens, input/output): Sonnet 5.5 $2/$10, Opus 5.5 $4/$20, Grok 4.7 $2/$6 (<200k prompt),
  kimi-k2.6 $0.95/$4 (cached in $0.16), deepseek-flash $0.30/$1.20 peak, half off-peak; deepseek-v4-pro $1.32/$3.96 peak,
  half off-peak (peak = 01:00–04:00 and 06:00–10:00 UTC Mon–Fri). Reasoning tokens bill as output.
  xAI also bills server-side web-search tool calls on top of tokens.
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
  shallow Grok ≈ $0.05–0.20 plus searches; deep Grok ≈ $0.30–1.50 plus searches; shallow Kimi ≈ $0.02–0.06;
shallow DeepSeek < $0.01; deep Kimi / DeepSeek (up to 7 calls) ≈ $0.10–0.40; a ping < $0.001; one Claude Code end-of-iteration run
  (Opus, ≤30 turns) ≈ $1–5. Check real spend in the Anthropic and xAI consoles and set monthly spend limits there.

## Secrets (referenced, not created here)

- `ANTHROPIC_API_KEY` — claude-audit and claude-code-review.
- `XAI_API_KEY` — grok-check.
- `DEEPSEEK_API_KEY` — deepseek-check (free/cheap tier).
- `MOONSHOT_API_KEY` — kimi-check (Moonshot AI developer API, billed separately from the kimi.com membership).
If a secret is missing the run stops before any API call, posts/prints a clear "secret not set" message and fails the check.
