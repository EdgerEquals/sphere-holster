#!/usr/bin/env python3
"""Kimi (Moonshot AI API) free-tier rote check of Cursor's latest merge/diff (stdlib only).

Role (harness/KIMI_START.md): units, arithmetic, consistency vs DESIGN_STATE.md, retired items. No physics sourcing.
OpenAI-compatible endpoint https://api.moonshot.ai/v1/chat/completions, streamed (idle + hard timeouts).
kimi-k2.6 thinks even on trivial prompts, so kimi_max_tokens in harness/dial.yml must stay >= 12000.
Usage:
  python scripts/review_kimi.py --depth shallow --head HEAD
  python scripts/review_kimi.py --ping "reply with the word pong"
  python scripts/review_kimi.py --list-models
Needs env MOONSHOT_API_KEY. Exit codes: 0 ok (PASS or FAIL recorded), 2 missing secret, 3 API/parse error.
Override without editing files: env KIMI_MODEL, KIMI_BASE_URL.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oai_compat as oc  # noqa: E402

# USD per 1M tokens (input cache-miss, cached input, output). Source: https://platform.moonshot.ai/docs/pricing/chat (2026-10-19)
PRICES = {"kimi-k2.6": (0.95, 0.16, 4.00), "kimi-k2.7-code-highspeed": (1.90, 0.38, 8.00)}
SRC = "https://platform.moonshot.ai/docs/pricing/chat"


def price(model, u, when):
    p = next((v for k, v in PRICES.items() if model.startswith(k)), None)
    if p is None:
        return 0.0, f"no price on file for {model}; cost not estimated ({SRC})"
    miss = max(u["input_tokens"] - u["cached_input_tokens"], 0)
    cost = (miss * p[0] + u["cached_input_tokens"] * p[1] + u["output_tokens"] * p[2]) / 1e6
    return cost, f"{model}: ${p[0]}/M in, ${p[1]}/M cached, ${p[2]}/M out (reasoning billed as output) · {SRC}"


KIMI = oc.Provider(name="Kimi", key="kimi", secret="MOONSHOT_API_KEY",
                   base_url="https://api.moonshot.ai/v1", price_fn=price)

if __name__ == "__main__":
    oc.main(KIMI)
