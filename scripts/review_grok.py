#!/usr/bin/env python3
"""Grok (xAI API) source / physics-claims cross-check of Cursor's latest merge/diff (stdlib only).

Uses the OpenAI-compatible xAI endpoint https://api.x.ai/v1/responses (streamed).
Web search: by default Grok gets Tavily results from a pre-search (scripts/tavily_search.py --grok-context, file in
env TAVILY_CONTEXT_FILE), which is cheaper. xAI's built-in server-side web_search tool is OFF by default
(harness/dial.yml grok_web_search: false); set it true to re-enable it.
Usage:
  python scripts/review_grok.py --depth shallow --head HEAD
  python scripts/review_grok.py --mode crosscheck --other-verdict claude/verdict.json
  python scripts/review_grok.py --ping-file brief.txt --out /tmp/roundN-run/grok --land-dir reviews/YYYY-MM-DD_roundN
Needs env XAI_API_KEY. Exit codes: 0 ok (PASS or FAIL recorded), 2 missing secret, 3 API/parse error.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import harness_common as hc  # noqa: E402
import tavily_search as ts  # noqa: E402

BASE = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")
TAVILY_NOTE = ("WEB SEARCH IN THIS RUN: the built-in web search tool is off. 'Web search' in your role means the Tavily "
               "results below (one search, fetched before this call). Cite only URLs that appear there; never invent a "
               "URL. A claim they do not cover gets status \"not_found\" and goes in claims_needing_source_check.")


def call(system: str, user: str, cfg: dict, key: str):
    model = os.environ.get("GROK_MODEL") or cfg["grok_model"]
    hdr = {"authorization": f"Bearer {key}"}
    effort = str(cfg.get("grok_reasoning_effort", "low"))
    builtin = bool(cfg.get("grok_web_search", False))
    web = ts.web_context()
    if not builtin:
        system += "\n\n---\n\n" + TAVILY_NOTE + ("" if web else " No Tavily results were provided for this run.")
    if web:
        system += "\n\n---\n\n" + web
    # Always the streamed /responses path (avoids the old non-streaming read timeouts).
    payload = {
        "model": model,
        "input": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "reasoning": {"effort": effort},                     # grok-4.7: low|medium|high|xhigh (default high)
        "max_output_tokens": int(cfg["grok_max_tokens"]),   # visible-output cap (reasoning not counted)
        "store": False,
    }
    if builtin:                                              # xAI built-in search: off by default (Tavily instead)
        payload["tools"] = [{"type": "web_search"}]
        payload["max_turns"] = int(cfg.get("grok_max_turns", 3))   # caps agentic search turns
    events = hc.post_sse(f"{BASE}/responses", payload, hdr,
                         idle_timeout=int(cfg.get("grok_idle_timeout_s", 180)),
                         deadline=int(cfg.get("grok_deadline_s", 900)))
    final = next((e.get("response") for e in reversed(events)
                  if e.get("type") in ("response.completed", "response.incomplete", "response.failed")), None) or {}
    if final.get("error"):
        raise RuntimeError(f"xAI response error: {json.dumps(final['error'])[:1000]}")
    texts, cites = [], []
    for item in final.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    texts.append(c.get("text", ""))
                    cites += [a.get("url") for a in c.get("annotations", []) if a.get("url")]
    text = "\n".join(texts) or "".join(e.get("delta", "") for e in events if e.get("type") == "response.output_text.delta")
    if not text.strip():
        types = sorted({e.get("type", "?") for e in events})
        raise RuntimeError(f"xAI stream ended with no output text (status={final.get('status')}, "
                           f"{len(events)} events: {', '.join(types)[:500]})")
    if final.get("status") == "incomplete":
        text += f"\n\n[response incomplete: {json.dumps(final.get('incomplete_details'))}]"
    if cites:
        text += "\n\nCitations returned by the API:\n" + "\n".join(f"- {u}" for u in dict.fromkeys(cites))
    return text, final.get("usage", {}), final.get("model", model)


REFORMAT_SYSTEM = (
    "Convert the review below into the required verdict JSON. Do not add new findings. Output ONLY one fenced ```json "
    "block with keys: verdict (PASS|FAIL), summary, findings [{severity, domain, file, claim, note}], "
    "retired_reintroduced [], claims_needing_source_check [], sources [{claim, status, url, note}], and crosscheck [] if "
    "the review compared against another reviewer. FAIL only if the review reports a blocker/major problem or a retired item.")


def reformat(review_text: str, cfg: dict, key: str):
    model = os.environ.get("GROK_MODEL") or cfg["grok_model"]
    payload = {"model": model, "reasoning": {"effort": "low"}, "max_output_tokens": 3000, "store": False,
               "input": [{"role": "system", "content": REFORMAT_SYSTEM}, {"role": "user", "content": review_text[:30000]}]}
    r = hc.post_json(f"{BASE}/responses", payload, {"authorization": f"Bearer {key}"}, timeout=300)
    text = "\n".join(c.get("text", "") for it in r.get("output", []) if it.get("type") == "message"
                     for c in it.get("content", []) if c.get("type") == "output_text")
    return text, r.get("usage", {})


if __name__ == "__main__":
    if "--ping" in sys.argv or "--ping-file" in sys.argv:   # round brief, lands reviews/<round>/grok.md
        import ping_common as pc  # noqa: E402
        sys.exit(pc.ping_main("Grok", "grok", "XAI_API_KEY", call))
    hc.run_review("Grok", "XAI_API_KEY", call, reformat)
