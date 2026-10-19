#!/usr/bin/env python3
"""DeepSeek API free-tier rote check of Cursor's latest merge/diff (stdlib only).

Role (harness/KIMI_START.md): units, arithmetic, consistency vs DESIGN_STATE.md, retired items. No physics sourcing.
OpenAI-compatible endpoint https://api.deepseek.com/chat/completions, streamed (idle + hard timeouts).
Models: deepseek-flash (shallow), deepseek-v4-pro (deep). Both think by default; reasoning is billed as output.
Usage:
  python scripts/review_deepseek.py --depth shallow --head HEAD
  python scripts/review_deepseek.py --ping "reply with the word pong"
  python scripts/review_deepseek.py --list-models
Needs env DEEPSEEK_API_KEY. Exit codes: 0 ok (PASS or FAIL recorded), 2 missing secret, 3 API/parse error.
Override without editing files: env DEEPSEEK_MODEL, DEEPSEEK_BASE_URL.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oai_compat as oc  # noqa: E402

# USD per 1M tokens at PEAK (input cache-miss, cached input, output); off-peak is half.
# Peak = 01:00-04:00 and 06:00-10:00 UTC Mon-Fri (Chinese public holidays ignored here).
# Source: https://api-docs.deepseek.com/quick_start/pricing (2026-10-19)
PRICES = {"deepseek-flash": (0.30, 0.006, 1.20), "deepseek-v4-flash": (0.30, 0.006, 1.20),
          "deepseek-v4-pro": (1.32, 0.044, 3.96)}
SRC = "https://api-docs.deepseek.com/quick_start/pricing"


def price(model, u, when):
    p = next((v for k, v in PRICES.items() if model.startswith(k)), None)
    if p is None:
        return 0.0, f"no price on file for {model}; cost not estimated ({SRC})"
    peak = when.weekday() < 5 and (1 <= when.hour < 4 or 6 <= when.hour < 10)
    k = 1.0 if peak else 0.5
    miss = max(u["input_tokens"] - u["cached_input_tokens"], 0)
    cost = k * (miss * p[0] + u["cached_input_tokens"] * p[1] + u["output_tokens"] * p[2]) / 1e6
    return cost, (f"{model} {'peak' if peak else 'off-peak'}: ${p[0]*k:g}/M in, ${p[1]*k:g}/M cached, "
                  f"${p[2]*k:g}/M out (reasoning billed as output) · {SRC}")


DEEPSEEK = oc.Provider(name="DeepSeek", key="deepseek", secret="DEEPSEEK_API_KEY",
                       base_url="https://api.deepseek.com", price_fn=price)

if __name__ == "__main__":
    oc.main(DEEPSEEK)
