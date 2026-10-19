# Cross-model review, round 3: next connector for the holster information layer

Date: 2026-10-19, about 13:24–13:27 AWST. Question (verbatim from Danny): "What is the next best connector to add to the Stratified Sphere holster information layer?" Each model was asked for: top recommendation, why, cost, and any risk (limit 400 words, first line `TOP: <connector>`).

Run locally from the box with `run_round.py` (reuses round 1's callers and pricing; shallow caps from `harness/dial.yml`). Cheap-first order:
1. **Tavily**: 2 basic searches, max_results 5 each. Raw results are in `tavily_results.json` and `tavily_results.md`.
2. **Kimi and DeepSeek** got the holster context, a short round-2 summary and the Tavily results (`prompt_cheap.md`).
3. Budget check: $0.028 spent after the cheap models, $0.25 projected worst case, abort threshold $0.50.
4. **Claude and Grok** got the same prompt plus Kimi's and DeepSeek's TOP lines, labelled as unverified cheap-model filter output (`prompt_paid.md`). Grok was sent no tools or search_parameters, so xAI's built-in web search was not used.

Qwen and Perplexity were not contacted.

| Model | id | in | cached | out | reasoning | words | s | cost |
|---|---|---|---|---|---|---|---|---|
| Tavily | basic ×2 | | | | | | | 2 credits, $0 (free 1,000/month) |
| Kimi | kimi-k2.6 | 2696 | 0 | 5884 | 5549 | 211 | 128.4 | $0.0261 |
| DeepSeek | deepseek-flash | 2801 | 0 | 1829 | 1431 | 284 | 10.5 | $0.0015 |
| Claude | claude-sonnet-5-5 | 4747 | 0 | 1093 | n/r | 486 | 10.6 | $0.0204 |
| Grok | grok-4.7 | 4035 | 1152 | 1288 | 778 | 356 | 19.7 | $0.0141 |
| **Total** | | | | | | | | **$0.0621** |

- All four replied on the first attempt.
- "out" includes reasoning tokens where the API reports them. Claude's API doesn't report thinking tokens separately (n/r).
- DeepSeek was billed at its off-peak rate, and Grok's API-reported cost was $0.0141.
- Claude went over the 400-word limit.
- No model reintroduced a retired item. The automatic scan found 0 hits, and a manual read confirmed it.

## Answers
- **Kimi:** an MCP physics gateway (dolfinx-mcp plus openfoam-mcp-server) so the models can drive the sim stack. Runner-up: a GitHub review-ledger bot.
- **DeepSeek:** a GitHub review-ledger connector (append-only JSONL plus Issues mirror plus reviewer scorecards). Runner-up: a read-only status connector for the FEniCS/OpenFOAM CI.
- **Claude:** a GitHub review-ledger connector (findings to Issues, dedup, `ledger/findings.jsonl`, reviewer scores). Runner-up: a sandboxed dolfinx-mcp once the ledger exists.
- **Grok:** a GitHub review-ledger connector (Issues plus Actions artifacts). Runner-up: dolfinx MCP (stdio, no network) once the ledger exists; skip openfoam-mcp for now.

**Consensus: 3 of 4 pick a GitHub review ledger first.** It costs about $0 to run, needs no new vendor or key, and closes round 2's "review loop doesn't close" gap. All four rank a FEniCS (dolfinx) MCP as the next step, as Kimi's first pick or the others' runner-up. Claude and Grok warn that openfoam-mcp-server is partial and aimed at education. Risks named most often:
- prompt injection from PR text copied into Issues
- a token scope wider than issues/contents
- schema drift
- noise in Issues
- sandboxing for any solver MCP (`--network none`, non-root)

Note: Claude and Grok saw the cheap models' TOP lines, so their agreement with DeepSeek isn't fully independent.
