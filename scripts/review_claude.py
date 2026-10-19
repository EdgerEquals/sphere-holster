#!/usr/bin/env python3
"""Claude API inner-loop audit of Cursor's latest merge/diff (Anthropic Messages API, stdlib only).

Usage:
  python scripts/review_claude.py --depth shallow --head HEAD
  python scripts/review_claude.py --depth deep --base origin/main --head pr-head --mode crosscheck --other-verdict grok/verdict.json
Needs env ANTHROPIC_API_KEY. Exit codes: 0 ok (PASS or FAIL recorded), 2 missing secret, 3 API/parse error.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import harness_common as hc  # noqa: E402

API_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/") + "/v1/messages"


def call(system: str, user: str, cfg: dict, key: str):
    model = os.environ.get("CLAUDE_MODEL") or cfg["claude_model"]
    payload = {
        "model": model,
        "max_tokens": int(cfg["claude_max_tokens"]),  # hard cap (includes adaptive thinking)
        "system": system,
        # Effort steers adaptive thinking; without it the model can spend the whole cap thinking.
        "output_config": {"effort": str(cfg.get("claude_effort", "medium"))},
        # cache the (identical) diff across per-domain calls in deep mode
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": user, "cache_control": {"type": "ephemeral"}}]}],
    }
    r = hc.post_json(API_URL, payload, {"x-api-key": key, "anthropic-version": "2023-06-01"})
    text = "\n".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
    if r.get("stop_reason") == "max_tokens":
        if not text.strip():
            raise RuntimeError(
                f"{model} used the whole max_tokens cap ({payload['max_tokens']}) on thinking and returned no verdict text. "
                "Raise claude_max_tokens or lower claude_effort in harness/dial.yml.")
        text += "\n\n[truncated at max_tokens cap; raise claude_max_tokens in harness/dial.yml if this recurs]"
    return text, r.get("usage", {}), r.get("model", model)


if __name__ == "__main__":
    hc.run_review("Claude", "ANTHROPIC_API_KEY", call)
