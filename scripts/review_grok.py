#!/usr/bin/env python3
"""Grok (xAI API) source / physics-claims cross-check of Cursor's latest merge/diff (stdlib only).

Uses the OpenAI-compatible xAI endpoint https://api.x.ai/v1:
  - /v1/responses with the server-side web_search tool when grok_web_search is true (default)
  - /v1/chat/completions otherwise
Usage:
  python scripts/review_grok.py --depth shallow --head HEAD
  python scripts/review_grok.py --mode crosscheck --other-verdict claude/verdict.json
Needs env XAI_API_KEY. Exit codes: 0 ok (PASS or FAIL recorded), 2 missing secret, 3 API/parse error.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import harness_common as hc  # noqa: E402

BASE = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")


def call(system: str, user: str, cfg: dict, key: str):
    model = os.environ.get("GROK_MODEL") or cfg["grok_model"]
    hdr = {"authorization": f"Bearer {key}"}
    if cfg.get("grok_web_search", True):
        payload = {
            "model": model,
            "input": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "tools": [{"type": "web_search"}],
            "max_output_tokens": int(cfg["grok_max_tokens"]),   # visible-output cap
            "max_turns": int(cfg.get("grok_max_turns", 4)),      # caps agentic search turns
            "store": False,
        }
        r = hc.post_json(f"{BASE}/responses", payload, hdr)
        texts, cites = [], []
        for item in r.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        texts.append(c.get("text", ""))
                        cites += [a.get("url") for a in c.get("annotations", []) if a.get("url")]
        text = "\n".join(texts)
        if cites:
            text += "\n\nCitations returned by the API:\n" + "\n".join(f"- {u}" for u in dict.fromkeys(cites))
        return text, r.get("usage", {}), r.get("model", model)
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": int(cfg["grok_max_tokens"]),
    }
    r = hc.post_json(f"{BASE}/chat/completions", payload, hdr)
    text = r["choices"][0]["message"].get("content") or ""
    u = r.get("usage", {})
    return text, {"input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens")}, r.get("model", model)


if __name__ == "__main__":
    hc.run_review("Grok", "XAI_API_KEY", call)
