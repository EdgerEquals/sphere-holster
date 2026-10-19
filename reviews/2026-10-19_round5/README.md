# Round 5: repo reachability test (2026-10-19)

The four holster models each got the prompt below **verbatim**, as the only user message. No repo contents were pasted into context. Each model had only the fetch/search tools its channel genuinely has. The point was to find out which models can reach the repo by themselves.

## Prompt (exact, also in `prompt.txt`)

> This is the Stratified Sphere model. Everything we've done lives in the repo at github.com/EdgerEquals/stratified-sphere-model — fetch it and look at the data yourselves; we're testing that you can reach it. Then tell us what you think we should fix and the best way to go about it. Also tell us what you think is missing. Last, tell us back in your own words what you think we're trying to do with this model.

## Results

| Model | Tools available | Fetched the repo? | Cost (USD) | Reply |
|---|---|---|---|---|
| Kimi `kimi-k2.6` | none | **No**. It said it can't fetch URLs, then gave a generic checklist for an atmosphere/ocean "stratified sphere" code. | 0.0100 | `kimi.md` |
| DeepSeek `deepseek-flash` (peak rate) | none | **No**. It said it has no network and "won't pretend I did", then gave a generic checklist and guessed from the name only. | 0.0026 | `deepseek.md` |
| Claude `claude-sonnet-5-5` (effort medium) | Anthropic server-side `web_fetch` (max 6 uses, 10k tokens per page), `web_search` (max 2 uses) | **Yes**. 5 fetches, all succeeded, 0 searches. | 0.2315 | `claude.md` |
| Grok `grok-4.7` (effort low) | holster Tavily pre-search (1 basic search, 5 results, given as system context), xAI built-in `web_search` with browsing (`max_turns` 3 requested) | **Yes**, through xAI web_search/open_page. The Tavily pre-search returned nothing relevant. 13 server-side tool calls. | 0.2951 | `grok.md` |
| **Total** | | | **0.5393** | |

Tavily: 1 credit, used by the Grok pre-search only.

The total went over the US$0.50 target. Grok's `max_turns: 3` did not cap its server-side tool calls: it made 13 and read about 140k input tokens, 53k of them cached. Claude read about 67k input tokens from 5 full GitHub HTML pages. Next time, use lower `max_content_tokens` for Claude, fewer fetches, or raw.githubusercontent URLs. Turn off xAI browsing for Grok, or cap it more tightly.

## How each channel ran
- **Kimi / DeepSeek** used the holster's ping path, unchanged:
  - `python scripts/review_kimi.py --ping "<prompt>"`
  - `python scripts/review_deepseek.py --ping "<prompt>"`
  - `oai_compat.py` has no function-tool support. The Tavily context is added only when a search query is given, and none was given. So these two had no tools.
- **Claude** used a direct Messages API call (`claude_run.py`) with the native server tools. The `claude-audit` holster normally has no tools.
- **Grok** used `scripts/tavily_search.py --grok-context`, with the prompt as the intent, to derive the query. The `/responses` call (`grok_run.py`) had `tools: [{"type":"web_search"}]`. This is the holster's `grok_web_search: true` setting, enabled for this run only. `harness/dial.yml` was not changed.

## Evidence of real fetches (from `tool_log.json`)

**Claude** fetched these pages; the number is the returned characters:
- `github.com/EdgerEquals/stratified-sphere-model` (29k)
- `.../blob/main/DESIGN_STATE.md` (28k)
- `.../blob/main/AGENTS.md` (28k)
- `.../blob/main/drive_model_output.txt` (16k)
- `.../issues` (12.5k)

**Grok** opened these pages:
- the repo root and README
- the raw files `DESIGN_STATE.md`, `AGENTS.md`, `solver_v0.py` (twice), `solver_v0_output.txt` and `docs/Multidomain_Sphere_Model_Feasibility_Plan_2026-10-19.md`
- the GitHub API listings of `docs/` and `reviews/`
- a `find_in_page` search on `solver_v0.py`

It also ran 2 searches.

### Cited values checked against this repo at d022e76

**Claude**
- `drive_model_output.txt` gives ring gas 8.093e-3 Pa and shell 2.215e-4 Pa at 20 Hz in the example runs. The sweep gives 4.047e-3 Pa and 1.108e-4 Pa. At 20 kHz the figures are 8.060 vs 4.030 Pa. **All exist.** The factor-of-2 finding is real in the file.
- HHO c = 532.9 m/s from M = 0.012011: **exists**.
- The 7.5 kW cap and 48 MPa, Curie ~10 W, KSF 8–16 W and 434 nm figures are all in `DESIGN_STATE.md`: **exist**.
- The README still says "`index.html` to follow": **exists**.
- Issues #3, #4 and #6 are PASS: **true**.
- **Loose:**
  - "18 harnesses": there are 14 workflow files.
  - The 10 K gas-heating estimate is Claude's own arithmetic.
  - The fused-silica inference is its own estimate.

**Grok**
- In `solver_v0.py`, `lock54`, `F_WALL = 0.10`, `F_OPT = 0.90`, `heat[0] += 0.5 * Pem * 0.0`, `ALPHA_PT`, `ETA_DISS`, `NU_CHAIN`, `WALL_RECOMB`, `P_release`, `phos_out ... cT=25`, the "50 nm" name, the linear "Curie-Weiss-like" ε ramp and the Curie flag ~393 K all **exist**.
- `solver_v0_output.txt` gives `T_qz_in` 1 W 962.2 K, gas centre 1228.0 K, a 3000 K clamp at 100 kW and a `drive 3.018 MHz` line: **exist**.
- `docs/` references `/workspace/grok_thread/`: **exists**.
- The retired list it quotes comes from `AGENTS.md` and `DESIGN_STATE.md`. Grok told us not to reopen those items; it did not propose them.
- No hallucinated file contents were found for Claude or Grok.
- Kimi and DeepSeek invented nothing about the repo. Both stated plainly that they could not fetch it.

## Files
- `kimi.md`, `deepseek.md`, `claude.md`, `grok.md`: the full replies, verbatim.
- `tool_log.json`: models, tool definitions, every tool call and URL, usage, costs, and the Tavily pre-search results.
- `claude_run.py`, `grok_run.py`: the exact request scripts. Keys are read from env and never printed.
- `prompt.txt`
