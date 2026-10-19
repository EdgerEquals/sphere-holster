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

Scripts: `scripts/review_claude.py`, `scripts/review_grok.py` (stdlib only; PyYAML optional), shared code in
`scripts/harness_common.py`. Local use: `ANTHROPIC_API_KEY=... python3 scripts/review_claude.py --depth shallow --head HEAD`.
Exit codes: 0 = verdict recorded (PASS or FAIL), 2 = API key missing (nothing called, nothing billed), 3 = API/parse error.

## Models (verified 2026-10-19)

- Claude audit: `claude-sonnet-5-5` (shallow), `claude-opus-5-5` (deep); Claude Code: `claude-opus-5-5`.
  Source: https://docs.claude.com/en/docs/about-claude/models/overview
- Grok: `grok-4.7` via `https://api.x.ai/v1/responses` with the `web_search` tool (falls back to
  `/v1/chat/completions` if `grok_web_search: false`). Sources: https://docs.x.ai/docs/models,
  https://docs.x.ai/docs/guides/tools/search-tools
- Override per run without editing files: env `CLAUDE_MODEL` / `GROK_MODEL`.

## Costs

- **GitHub Actions minutes: free.** The repo is public, and standard GitHub-hosted runners are free for public repos.
  (Private repo: 2,000 free minutes/month on Free plans, then well under a cent per minute on standard Linux runners.)
- **API tokens are billed separately** by Anthropic (`ANTHROPIC_API_KEY`) and xAI (`XAI_API_KEY`), per token, to whoever owns the key.
  List prices at setup (per million tokens, input/output): Sonnet 5.5 $2/$10, Opus 5.5 $4/$20, Grok 4.7 $2/$6 (<200k prompt).
  xAI also bills server-side web-search tool calls on top of tokens.
- **Caps** (edit `dial.yml`):
  - `claude_max_tokens` is a hard cap on Claude's output **including adaptive thinking**; `claude_effort` (low|medium|high) steers how much it thinks. Too small a cap with high effort returns no verdict (first smoke test hit this at 6000).
  - `grok_max_tokens` caps Grok's visible output (`max_output_tokens`); xAI does not count reasoning tokens against it, so
    `grok_max_turns` (agentic search turns) is the main Grok cost lever.
  - `max_diff_chars` caps the prompt size; `max_calls` caps calls per review.
  - Push-to-main audits run only every `audit_every_n_rounds` rounds or on `[audit]`, never on every push.
  - Comment triggers only work for the repo owner/members/collaborators, so strangers cannot spend the keys.
- **Rough per-run estimates [est]:** shallow Claude ≈ $0.05–0.15; deep Claude (up to 7 Opus calls, diff cached) ≈ $0.50–3;
  shallow Grok ≈ $0.05–0.20 plus searches; deep Grok ≈ $0.30–1.50 plus searches; one Claude Code end-of-iteration run
  (Opus, ≤30 turns) ≈ $1–5. Check real spend in the Anthropic and xAI consoles and set monthly spend limits there.

## Secrets (referenced, not created here)

- `ANTHROPIC_API_KEY` — claude-audit and claude-code-review.
- `XAI_API_KEY` — grok-check.
If a secret is missing the run stops before any API call, posts/prints a clear "secret not set" message and fails the check.
