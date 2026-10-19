You are one of four independent reviewers (Kimi, DeepSeek, Claude, Grok) in a cross-model review, round 4.
Subject: the "holster" (harness) / information layer of the Stratified Sphere project. NOT the physics.

Open question from Danny: "What do you think is the best solution to the ordering gap, where the review layer is ahead of the execution layer (the harness can audit work that doesn't exist yet)?"

Answer in at most 400 words. First line exactly: "SOLUTION: <one line>". Then explain your answer: what it is,
why, what it would cost, and any risk. Use only the context below. Do not propose reviving retired items.

===== HOLSTER CONTEXT (2026-10-19) =====
- Four live model keys: Claude, Grok, Kimi, DeepSeek. Qwen dropped for now; Perplexity held out.
- Tavily search live (shared web-search slot, opt-in per run; Grok reviews use one Tavily pre-search, xAI built-in
  search off).
- Cursor as build layer (writes code and harness files), with /kimi-check and /deepseek-check cheap first-filter
  channels; Claude audit and Grok source check are the paid reviewers, triggered on PRs, issues, dispatch or
  tagged pushes to main.
- SymPy / SciPy / C core compute; pytest locked-value suite (engineering-tests) on every push.
- FEniCS / MEEP / OpenFOAM / CalculiX / Code_Aster / Gwyddion open simulation stack: digest-pinned smoke tests in CI.
- GitHub Actions / Pages / Issues / PRs / Secrets / Dependabot.
- Spec (Drive doc "Information Layer (Harness Architecture)"): 6 domain harnesses + 12 knee harnesses + a
  coordinator + a validation harness, looping Cursor -> domain runners -> merge -> Claude + Grok review -> main.
  What is built: the review stage (four reviewer channels), the compute/sim smoke tests, and (just now) the items
  below. The domain harnesses, knee harnesses, coordinator loop and loss map are NOT built.
- Just built and locked (2026-10-19, from round 3):
  1. GitHub review ledger: every reviewer finding parsed from verdict artifacts and review rounds into an
     append-only ledger/findings.jsonl on main (versioned JSON Schema, sha256 dedup, sanitised reviewer text);
     findings at or above severity "major" can be mirrored to labelled issues (daily cap 5, off by default);
     closing an issue records accepted/rejected/fixed.
  2. Scoring rubric: a planted-mistake fixture (8 seeded errors: units, arithmetic, retired items, consistency with
     DESIGN_STATE) scored per reviewer for precision/recall; scorecards from issue outcomes. Paid planted runs are
     dispatch-only and have not been run yet.
  3. Monthly cost rollup per model from the ledger (ledger/costs_YYYY-MM, Pages table). October so far ~$0.87.
  4. FEniCS/OpenFOAM MCP gateway: hardened containers (no network, read-only, non-root) exposing the existing
     sim smoke tests as MCP tools for Cursor; CI smoke test drives it without an LLM; runs are logged to the ledger.
- Retired, never reintroduce: oil bath; slotted Cu/Ag shell; ribs/segments; 6.75 kHz; 0.2 T; 13 GHz ceiling;
  cold-regime work; Backwards_Derived_Spec_from_Ionisation; radial diamond spokes.

===== ROUND 3 SUMMARY (short) =====
Asked for the next connector: DeepSeek, Claude and Grok picked the GitHub review ledger; Kimi picked the MCP physics
gateway (the others ranked it next). Danny locked all four items above.

===== CHEAP-MODEL FILTER OUTPUT (Kimi, DeepSeek; unverified, may be wrong) =====
- Kimi SOLUTION: Gate paid review triggers on Cursor-generated stub harnesses with locked I/O schemas, so auditors review concrete interface contracts instead of missing code.
- DeepSeek SOLUTION: Gate every review on a CI-signed execution receipt in the ledger, and make pre-execution audits a separate spec-review class.
You may agree or disagree; judge independently.
