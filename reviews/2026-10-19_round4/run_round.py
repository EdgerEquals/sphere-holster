#!/usr/bin/env python3
"""Review round 4 (issue #11): open question on the ordering gap. First test run of the new holster version.

Order (cheap-first, as round 3): Kimi + DeepSeek -> budget check -> Claude + Grok (with a labelled note of the
cheap models' one-line answers). Tavily is optional per Danny; not used in this round (no search needed for an
internal design question, and it keeps outside text from steering the answer). Reuses round 1's callers (the Grok
caller sends no tools / search_parameters, so no xAI built-in search) and round 3's helpers. Shallow caps from
harness/dial.yml. Keys from env, never printed. Qwen and Perplexity are not contacted.
Usage: python3 reviews/2026-10-19_round4/run_round.py reviews/2026-10-19_round4
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("round3", HERE.parent / "2026-10-19_round3" / "run_round.py")
r3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r3)

BUDGET_ABORT_USD = 0.50
QUESTION = ("What do you think is the best solution to the ordering gap, where the review layer is ahead of the "
            "execution layer (the harness can audit work that doesn't exist yet)?")

HEADER = f"""You are one of four independent reviewers (Kimi, DeepSeek, Claude, Grok) in a cross-model review, round 4.
Subject: the "holster" (harness) / information layer of the Stratified Sphere project. NOT the physics.

Open question from Danny: "{QUESTION}"

Answer in at most 400 words. First line exactly: "SOLUTION: <one line>". Then explain your answer: what it is,
why, what it would cost, and any risk. Use only the context below. Do not propose reviving retired items."""

CONTEXT = """===== HOLSTER CONTEXT (2026-10-19) =====
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
gateway (the others ranked it next). Danny locked all four items above."""


def first_line(text):
    for line in (text or "").splitlines():
        if line.strip().upper().lstrip("*").startswith("SOLUTION"):
            return line.split(":", 1)[-1].strip().strip("*")
    return "(no SOLUTION line)"


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    results = {"question": QUESTION, "order": ["Kimi", "DeepSeek", "Claude", "Grok"], "tavily": "not used (optional)"}
    p_cheap = f"{HEADER}\n\n{CONTEXT}\n"
    (out / "prompt_cheap.md").write_text(p_cheap, encoding="utf-8")
    for name in ("Kimi", "DeepSeek"):
        results[name] = r3.call(name, p_cheap)
    spent = sum(a["cost_usd"] for n in ("Kimi", "DeepSeek") for a in results[n])
    est_in = len(p_cheap) / 3.0 + 1500
    worst = (est_in * 2 + r3.MAX_TOKENS["Claude"][0] * 10) / 1e6 + (est_in * 2 + (r3.MAX_TOKENS["Grok"][0] + 3000) * 6) / 1e6
    results["budget_check"] = {"spent_after_cheap": round(spent, 5), "projected_worst_total": round(spent + worst, 5),
                               "abort_over": BUDGET_ABORT_USD}
    print(f"budget: spent ${spent:.4f}, projected worst total ${spent + worst:.4f}", flush=True)
    if spent + worst > BUDGET_ABORT_USD:
        results["aborted"] = True
    else:
        note = ["===== CHEAP-MODEL FILTER OUTPUT (Kimi, DeepSeek; unverified, may be wrong) ====="]
        for n in ("Kimi", "DeepSeek"):
            note.append(f"- {n} SOLUTION: {first_line(results[n][-1]['text'])}")
        p_paid = p_cheap + "\n" + "\n".join(note) + "\nYou may agree or disagree; judge independently.\n"
        (out / "prompt_paid.md").write_text(p_paid, encoding="utf-8")
        for name in ("Claude", "Grok"):
            results[name] = r3.call(name, p_paid)
    models = [n for n in ("Kimi", "DeepSeek", "Claude", "Grok") if n in results]
    results["total_usd"] = round(sum(a["cost_usd"] for n in models for a in results[n]), 6)
    print(f"TOTAL ${results['total_usd']:.4f}", flush=True)
    (out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
