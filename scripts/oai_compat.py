"""Shared driver for the free/cheap-tier rote checkers (Kimi, DeepSeek) on OpenAI-compatible
/chat/completions endpoints. Stdlib only. Builds on harness_common without changing it.

Each provider script (review_kimi.py, review_deepseek.py) passes a Provider and gets:
  - a normal harness review (same CLI, verdict JSON/markdown, exit codes as review_claude/review_grok)
  - --ping "<prompt>": send just that prompt, write reply + token usage + cost to the job summary
  - --list-models: print the model IDs the key can see (/models)
Exit codes: 0 ok, 2 missing secret, 3 API/parse error (verdict ERROR is still written and posted).
Secrets are only ever sent in the Authorization header; they are never printed.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import harness_common as hc  # noqa: E402


@dataclass
class Provider:
    name: str                    # "Kimi" | "DeepSeek" (also the reviewer name in verdicts)
    key: str                     # dial key prefix: "kimi" | "deepseek"
    secret: str                  # env var / GitHub secret name
    base_url: str                # OpenAI-compatible base, e.g. https://api.moonshot.ai/v1
    price_fn: object = None      # (model, usage, when_utc) -> (cost_usd, price_note)
    extra_body: dict = field(default_factory=dict)

    @property
    def base(self) -> str:
        return os.environ.get(f"{self.key.upper()}_BASE_URL", self.base_url).rstrip("/")

    def model(self, cfg: dict) -> str:
        return os.environ.get(f"{self.key.upper()}_MODEL") or cfg[f"{self.key}_model"]


def _redact(s: str) -> str:
    return re.sub(r"(sk-|Bearer\s+)[A-Za-z0-9_\-]{8,}", r"\1[redacted]", str(s))


def normalise_usage(u: dict) -> dict:
    u = u or {}
    ctd = u.get("completion_tokens_details") or {}
    cached = u.get("prompt_cache_hit_tokens", u.get("cached_tokens",
                   (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0))) or 0
    return {"input_tokens": u.get("prompt_tokens", 0) or 0, "cached_input_tokens": cached,
            "output_tokens": u.get("completion_tokens", 0) or 0,
            "reasoning_tokens": ctd.get("reasoning_tokens"), "raw": u}


def chat(p: Provider, cfg: dict, key: str, messages: list[dict], max_tokens: int | None = None, model: str | None = None):
    """Streaming chat completion. Returns (text, usage, model, finish_reason, reasoning_chars)."""
    model = model or p.model(cfg)
    body = {"model": model, "messages": messages, "stream_options": {"include_usage": True},
            "max_tokens": int(max_tokens or cfg[f"{p.key}_max_tokens"]), **p.extra_body}
    events = hc.post_sse(f"{p.base}/chat/completions", body, {"authorization": f"Bearer {key}"},
                         idle_timeout=int(cfg.get(f"{p.key}_idle_timeout_s", 180)),
                         deadline=int(cfg.get(f"{p.key}_deadline_s", 600)))
    text, rchars, usage, stop = [], 0, {}, None
    for e in events:
        if e.get("error"):
            raise RuntimeError(f"{p.name} stream error: {_redact(json.dumps(e['error']))[:1000]}")
        model = e.get("model", model)
        for ch in e.get("choices") or []:
            d = ch.get("delta") or {}
            if d.get("content"):
                text.append(d["content"])
            if d.get("reasoning_content"):
                rchars += len(d["reasoning_content"])
            stop = ch.get("finish_reason") or stop
            if ch.get("usage"):
                usage = ch["usage"]          # Kimi puts usage on the final choice
        if e.get("usage"):
            usage = e["usage"]
    u = normalise_usage(usage)
    when = _dt.datetime.now(_dt.timezone.utc)
    if p.price_fn:
        cost, note = p.price_fn(model, u, when)
        u["cost_usd"] = round(cost, 6)
        u["cost_in_usd_ticks"] = int(round(cost * 1e10))   # rendered by harness_common.render_md
        u["price_note"] = note
    out = "".join(text)
    if not out.strip():
        raise RuntimeError(f"{model} returned no reply text (finish_reason={stop}, output tokens={u['output_tokens']}, "
                           f"reasoning tokens={u['reasoning_tokens']}, {len(events)} events). If finish_reason is "
                           f"'length', thinking used the whole cap: raise {p.key}_max_tokens in harness/dial.yml.")
    if stop == "length":
        out += f"\n\n[truncated at max_tokens cap; raise {p.key}_max_tokens in harness/dial.yml if this recurs]"
    return out, u, model, stop, rchars


def _design_state() -> str:
    f = hc.ROOT / "DESIGN_STATE.md"
    return f.read_text() if f.is_file() else "(DESIGN_STATE.md not found)"


def _web_context() -> str:
    """Optional Tavily results (shared web-search slot) written by scripts/tavily_search.py --rote-context.
    Only present when the run asked for web_search AND TAVILY_API_KEY is set AND results came back."""
    f = os.environ.get("TAVILY_CONTEXT_FILE", "").strip()
    if not f or not Path(f).is_file():
        return ""
    return Path(f).read_text()[:20000]


def review_call(p: Provider):
    def call(system: str, user: str, cfg: dict, key: str):
        parts = [system, hc.prompt("_rote_check"),
                 "CURRENT DESIGN_STATE.md (default branch, single source of truth):\n\n" + _design_state()]
        web = _web_context()
        if web:
            parts.append(web)
        sysmsg = "\n\n---\n\n".join(parts)
        text, u, model, _, _ = chat(p, cfg, key, [{"role": "system", "content": sysmsg}, {"role": "user", "content": user}])
        return text, u, model
    return call


REFORMAT_SYSTEM = (
    "Convert the review below into the required verdict JSON. Do not add new findings. Output ONLY one fenced ```json "
    "block with keys: verdict (PASS|FAIL), summary, findings [{severity, domain, file, claim, note}], "
    "retired_reintroduced [], claims_needing_source_check []. FAIL only if the review reports a blocker/major problem "
    "or a retired item.")


def reformat_call(p: Provider):
    def reformat(review_text: str, cfg: dict, key: str):
        text, u, _, _, _ = chat(p, cfg, key, [{"role": "system", "content": REFORMAT_SYSTEM},
                                              {"role": "user", "content": review_text[:30000]}])
        return text, u
    return reformat


def _summary(md: str) -> None:
    s = os.environ.get("GITHUB_STEP_SUMMARY")
    if s:
        with open(s, "a") as fh:
            fh.write(md + "\n")


def ping(p: Provider, prompt: str, depth: str | None, out: Path) -> int:
    dial = hc.load_dial()
    depth, cfg = hc.level_cfg(dial, depth)
    out.mkdir(parents=True, exist_ok=True)
    key = os.environ.get(p.secret, "").strip()
    rec = {"reviewer": p.name, "mode": "ping", "depth": depth, "prompt": prompt, "model_requested": p.model(cfg),
           "generated_utc": hc.now_utc()}
    if not key:
        msg = f"{p.secret} is not set; no API call was made. Add it under Settings > Secrets and variables > Actions."
        rec.update(ok=False, error=msg)
        (out / "ping.json").write_text(json.dumps(rec, indent=2))
        _summary(f"## ⏭️ {p.name} ping: SKIPPED\n\n{msg}")
        print(f"::error title=Missing secret {p.secret}::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg, file=sys.stderr)
        return hc.EXIT_MISSING_SECRET
    try:
        text, u, model, stop, rchars = chat(p, cfg, key, [{"role": "user", "content": prompt}])
        rec.update(ok=True, model=model, reply=text, finish_reason=stop, reasoning_chars=rchars, usage=u)
        md = [f"## ✅ {p.name} ping: OK", "", f"Model `{model}` · depth `{depth}` · finish `{stop}`", "",
              "**Prompt**", "", "```", prompt[:2000], "```", "", "**Reply**", "", "```", text[:8000], "```", "",
              "| input | cached input | output (total) | of which reasoning | cost (USD) |", "|---|---|---|---|---|",
              f"| {u['input_tokens']} | {u['cached_input_tokens']} | {u['output_tokens']} | {u['reasoning_tokens']} | "
              f"{u.get('cost_usd', '?')} |", "", f"<sub>{u.get('price_note', '')}</sub>"]
        code = 0
    except Exception as e:  # noqa: BLE001
        err = _redact(f"{type(e).__name__}: {e}")[:1500]
        rec.update(ok=False, error=err)
        md = [f"## ⚠️ {p.name} ping: ERROR", "", "```", err, "```"]
        print(f"::error title={p.name} ping failed::{err[:300]}" if os.environ.get("GITHUB_ACTIONS") else err, file=sys.stderr)
        code = hc.EXIT_API_ERROR
    (out / "ping.json").write_text(json.dumps(rec, indent=2))
    _summary("\n".join(md))
    print("\n".join(md))
    return code


def list_models(p: Provider) -> int:
    key = os.environ.get(p.secret, "").strip()
    if not key:
        print(f"{p.secret} not set", file=sys.stderr)
        return hc.EXIT_MISSING_SECRET
    req = urllib.request.Request(f"{p.base}/models", headers={"authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            ids = sorted(m.get("id", "?") for m in json.loads(r.read().decode()).get("data", []))
    except Exception as e:  # noqa: BLE001
        print(_redact(f"{p.name} /models failed: {type(e).__name__}: {e}")[:500], file=sys.stderr)
        return hc.EXIT_API_ERROR
    md = f"<details><summary>{p.name} models visible to this key ({len(ids)})</summary>\n\n" + \
         "\n".join(f"- `{i}`" for i in ids) + "\n\n</details>"
    print("\n".join(ids))
    _summary(md)
    return 0


def main(p: Provider) -> None:
    argv = sys.argv[1:]
    if "--list-models" in argv:
        sys.exit(list_models(p))
    if "--ping" in argv:
        import argparse
        ap = argparse.ArgumentParser(description=f"{p.name} ping")
        ap.add_argument("--ping", required=True)
        ap.add_argument("--depth", choices=["shallow", "deep"], default=None)
        ap.add_argument("--out", default="review-out")
        a, _ = ap.parse_known_args(argv)
        sys.exit(ping(p, a.ping, a.depth, Path(a.out)))
    # For the rote checkers an API/parse failure must surface as ERROR (exit 3) even when the free
    # retired-item scan also hit; the hits are still listed in the posted verdict. Local to this process:
    # review_claude.py / review_grok.py keep harness_common.combine unchanged.
    _combine = hc.combine
    hc.combine = lambda results, hits: "ERROR" if any(r["parsed"]["verdict"] == "ERROR" for r in results) or not results \
        else _combine(results, hits)
    hc.run_review(p.name, p.secret, review_call(p), reformat_call(p))
