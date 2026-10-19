#!/usr/bin/env python3
"""Review round 1: same prompt to Claude, Grok, Kimi, DeepSeek. Stdlib only; keys from env (never printed).

Usage: python3 reviews/2026-10-19_round1/run_round.py DESIGN_STATE.md out_dir
"""
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import harness_common as hc  # noqa: E402  (post_sse: streaming with idle/deadline timeouts)

VIEWER = """Viewer v0.3, live at https://edgerequals.github.io/stratified-sphere-model/?v=3:
- EMF drive range 100 kHz to 1000 THz, with regime flags (quasi-static field model invalid from tens of GHz; single cycle shorter than gas breakdown time near THz; optical band = drive is light) and hydrogen Balmer lines marked.
- Typed sweep bounds (bottom/top) for the frequency sweep; inner- and outer-diameter sweeps.
- Cited quartz sound speeds with a selector: VRH aggregate 6048/4090 m/s (default), single crystal Z 6330/4685, X 5710/5200, Danny's 5900 (cT 4090 from VRH).
Known caveats:
- Electron/ion drift speeds are placeholders, so the discharge formation thresholds (~24 MHz no-avalanche, ~2.2 MHz static knee not reached) are order-of-magnitude only.
- The EM resonance limit is an estimate.
- With the cited VRH speeds the test shell 0S0 breathing mode moved from 1.868 to 1.855 MHz (DESIGN_STATE says "about 1.87").
- The locked 3.236 MHz lock-shell thickness mode matches the exact spherical-shell 1S0 mode with cL 5900 m/s (+0.11%), but the formula and sound speed behind 3.236 MHz were never recorded (slab cL/2t would need cL ~6110 m/s)."""

QUESTION = """You are one of four independent reviewers (Claude, Grok, Kimi, DeepSeek) in a cross-model review round.
Below is the project's DESIGN_STATE.md (single source of truth) and a short summary of the current viewer.
All figures are paper estimates; nothing is measured.

Answer in at most 400 words, in this structure:
1. Start with exactly one line: "VERDICT: PASS" or "VERDICT: FAIL" — on the INTERNAL CONSISTENCY of the locked values and the open options (do locked items contradict each other, the open list, or the viewer caveats?). Then give your reasons.
2. Top three risks or gaps.
3. One improvement suggestion.
Do not browse; judge only from the text given."""


def build_prompt(design_state: str) -> str:
    return f"{QUESTION}\n\n===== DESIGN_STATE.md =====\n{design_state}\n===== VIEWER SUMMARY =====\n{VIEWER}\n"


# ----------------------------------------------------------------- providers
def call_claude(prompt, max_tokens):
    ev = hc.post_sse("https://api.anthropic.com/v1/messages",
                     {"model": "claude-sonnet-5-5", "max_tokens": max_tokens, "output_config": {"effort": "medium"},
                      "messages": [{"role": "user", "content": prompt}]},
                     {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                     idle_timeout=180, deadline=600)
    text, usage, stop, model = [], {}, None, "claude-sonnet-5-5"
    for e in ev:
        t = e.get("type")
        if t == "message_start":
            usage.update(e["message"].get("usage", {})); model = e["message"].get("model", model)
        elif t == "content_block_delta" and e["delta"].get("type") == "text_delta":
            text.append(e["delta"]["text"])
        elif t == "message_delta":
            usage.update(e.get("usage", {})); stop = e["delta"].get("stop_reason")
    otd = usage.get("output_tokens_details") or {}
    return dict(model=model, text="".join(text), stop=stop, input=usage.get("input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0) + usage.get("cache_read_input_tokens", 0),
                cached=usage.get("cache_read_input_tokens", 0), output=usage.get("output_tokens", 0),
                reasoning=otd.get("thinking_tokens"), raw_usage=usage)


def call_grok(prompt, max_tokens):
    ev = hc.post_sse("https://api.x.ai/v1/responses",
                     {"model": "grok-4.7", "reasoning": {"effort": "low"}, "max_output_tokens": max_tokens,
                      "store": False, "input": [{"role": "user", "content": prompt}]},   # no tools: no web search
                     {"authorization": f"Bearer {os.environ['XAI_API_KEY']}"}, idle_timeout=180, deadline=600)
    final = next((e.get("response") for e in reversed(ev) if e.get("type") in
                  ("response.completed", "response.incomplete", "response.failed")), None) or {}
    text = "\n".join(c.get("text", "") for it in final.get("output", []) if it.get("type") == "message"
                     for c in it.get("content", []) if c.get("type") == "output_text")
    u = final.get("usage", {})
    return dict(model=final.get("model", "grok-4.7"), text=text, stop=final.get("status"), input=u.get("input_tokens", 0),
                cached=(u.get("input_tokens_details") or {}).get("cached_tokens", 0), output=u.get("output_tokens", 0),
                reasoning=(u.get("output_tokens_details") or {}).get("reasoning_tokens"),
                cost_reported_usd=(u.get("cost_in_usd_ticks") or 0) / 1e10 or None, raw_usage=u)


def _openai_chat(url, key, body):
    ev = hc.post_sse(url, {**body, "stream_options": {"include_usage": True}},
                     {"authorization": f"Bearer {key}"}, idle_timeout=180, deadline=600)
    text, reasoning_chars, usage, stop, model = [], 0, {}, None, body["model"]
    for e in ev:
        model = e.get("model", model)
        for ch in e.get("choices") or []:
            d = ch.get("delta") or {}
            if d.get("content"):
                text.append(d["content"])
            if d.get("reasoning_content"):
                reasoning_chars += len(d["reasoning_content"])
            stop = ch.get("finish_reason") or stop
            if ch.get("usage"):
                usage = ch["usage"]          # Kimi puts usage on the final choice
        if e.get("usage"):
            usage = e["usage"]
    ctd = usage.get("completion_tokens_details") or {}
    cached = usage.get("prompt_cache_hit_tokens", usage.get("cached_tokens",
                       (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0))) or 0
    return dict(model=model, text="".join(text), stop=stop, input=usage.get("prompt_tokens", 0), cached=cached,
                output=usage.get("completion_tokens", 0), reasoning=ctd.get("reasoning_tokens"),
                reasoning_chars=reasoning_chars, raw_usage=usage)


def call_kimi(prompt, max_tokens):
    return _openai_chat("https://api.moonshot.ai/v1/chat/completions", os.environ["MOONSHOT_API_KEY"],
                        {"model": "kimi-k2.6", "max_tokens": max_tokens, "stream": True,
                         "messages": [{"role": "user", "content": prompt}]})


def call_deepseek(prompt, max_tokens):
    return _openai_chat("https://api.deepseek.com/chat/completions", os.environ["DEEPSEEK_API_KEY"],
                        {"model": "deepseek-flash", "max_tokens": max_tokens, "stream": True,
                         "messages": [{"role": "user", "content": prompt}]})


# ----------------------------------------------------------------- prices (USD per 1M tokens), fetched 2026-10-19
def deepseek_offpeak(t: dt.datetime) -> bool:
    peak = t.weekday() < 5 and (1 <= t.hour < 4 or 6 <= t.hour < 10)   # UTC, Mon-Fri (Chinese holidays ignored)
    return not peak


def price(name, r, t_utc):
    if name == "Claude":    # Sonnet 5.5: $2 in, $10 out, cache read 0.05x
        p = dict(inp=2.0, cached=0.10, out=10.0, src="https://docs.claude.com/en/docs/about-claude/pricing")
    elif name == "Grok":    # grok-4.7 (<200k prompt): $2 in, $0.50 cached, $6 out
        p = dict(inp=2.0, cached=0.50, out=6.0, src="https://docs.x.ai/docs/models")
    elif name == "Kimi":    # kimi-k2.6: $0.95 in (miss), $0.16 cached, $4.00 out
        p = dict(inp=0.95, cached=0.16, out=4.0, src="https://platform.moonshot.ai/docs/pricing/chat")
    else:                   # deepseek-flash: off-peak $0.15 miss / $0.003 hit / $0.60 out; peak x2
        off = deepseek_offpeak(t_utc)
        k = 1 if off else 2
        p = dict(inp=0.15 * k, cached=0.003 * k, out=0.60 * k, src="https://api-docs.deepseek.com/quick_start/pricing",
                 period="off-peak" if off else "peak")
    miss = max(r["input"] - (r.get("cached") or 0), 0)
    cost = (miss * p["inp"] + (r.get("cached") or 0) * p["cached"] + r["output"] * p["out"]) / 1e6
    return cost, p


CALLS = [("Claude", call_claude), ("Grok", call_grok), ("Kimi", call_kimi), ("DeepSeek", call_deepseek)]


def main():
    ds_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(ds_path.read_text(encoding="utf-8"))
    (out / "prompt.md").write_text(prompt, encoding="utf-8")
    results = {}
    for name, fn in CALLS:
        attempts = []
        for max_tokens in (6000, 12000):        # retry once with more headroom if thinking ate the reply
            t0 = time.time(); t_utc = dt.datetime.now(dt.timezone.utc)
            try:
                r = fn(prompt, max_tokens); r["error"] = None
            except Exception as e:  # noqa: BLE001
                r = dict(text="", error=f"{type(e).__name__}: {e}"[:800], input=0, output=0, cached=0, reasoning=None)
            r.update(max_tokens=max_tokens, seconds=round(time.time() - t0, 1), started_utc=t_utc.isoformat(timespec="seconds"))
            r["cost_usd"], r["price"] = price(name, r, t_utc)
            attempts.append(r)
            print(f"{name}: max_tokens={max_tokens} in={r['input']} out={r['output']} reasoning={r.get('reasoning')} "
                  f"stop={r.get('stop')} chars={len(r['text'])} err={r['error']} {r['seconds']}s", flush=True)
            if r["text"].strip() or r["error"]:
                break
        results[name] = attempts
    (out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
