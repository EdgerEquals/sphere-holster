#!/usr/bin/env python3
"""Land each model's round reply in the review tree as reviews/YYYY-MM-DD_roundN/{model}.md (stdlib only).

Why this exists: the round pings (review_kimi/review_deepseek --ping, plus ad-hoc Claude/Grok runners) wrote replies
only to a scratch out dir (ping.json / reply.md under /tmp); copying them into the review folder was a manual prose
step in the kickoff, so round 6 ended with only deepseek.md landed. Every ping path now calls land() on success, and a
run is not complete until check() finds all four files.

Usage:
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --model kimi --src /tmp/round6-run/kimi/ping.json
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --from-run-dir /tmp/round6-run
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --check
Sources understood: ping.json ({"reply": ...}), Claude raw.json ({"resp": {"content": [...]}}), Grok raw.json
({"final": {"output": [...]}}), or a plain .md/.txt reply. Exit codes: 0 ok, 1 missing/empty replies, 2 bad source.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

MODELS = ("kimi", "deepseek", "claude", "grok")
CHANNELS = {
    "kimi": "scripts/review_kimi.py --ping",
    "deepseek": "scripts/review_deepseek.py --ping",
    "claude": "scripts/review_claude.py --ping",
    "grok": "scripts/review_grok.py --ping",
}
HEADER_RE = re.compile(r"\A<!-- landed: .*?-->\n+", re.S)


def header(model: str, meta: dict) -> str:
    keys = ("model", "channel", "generated_utc", "source")
    bits = [f"{k}={meta[k]}" for k in keys if meta.get(k)]
    return f"<!-- landed: reviewer={model} · " + " · ".join(bits) + " -->\n\n"


def land(round_dir: str | Path, model: str, text: str, meta: dict | None = None) -> Path:
    """Write {round_dir}/{model}.md (provenance comment + reply body). Refuses an empty reply."""
    model = model.lower()
    if model not in MODELS:
        raise ValueError(f"unknown model '{model}' (expected one of {', '.join(MODELS)})")
    body = HEADER_RE.sub("", (text or "").strip()).strip()
    if not body:
        raise ValueError(f"{model}: empty reply; nothing landed")
    meta = {"channel": CHANNELS[model], **(meta or {})}
    d = Path(round_dir)
    d.mkdir(parents=True, exist_ok=True)
    dest = d / f"{model}.md"
    tmp = dest.with_suffix(".md.tmp")
    tmp.write_text(header(model, meta) + body + "\n")
    os.replace(tmp, dest)
    return dest


def extract(src: str | Path) -> tuple[str, dict]:
    """Return (reply_text, meta) from a ping.json, Claude/Grok raw.json, or a plain reply file."""
    src = Path(src)
    if src.suffix != ".json":
        meta = {"source": str(src)}
        sib = src.with_name("raw.json")             # ad-hoc runners keep model metadata next to reply.md
        if sib.is_file():
            try:
                meta.update({k: v for k, v in extract(sib)[1].items() if k != "source" and v})
            except (ValueError, json.JSONDecodeError):
                pass
        return src.read_text(), meta
    d = json.loads(src.read_text())
    meta = {"source": str(src)}
    if "reply" in d:                                    # ping.json (oai_compat / ping_main)
        if d.get("ok") is False:
            raise ValueError(f"{src}: ping recorded ok=false ({d.get('error', '')[:200]})")
        meta.update(model=d.get("model") or d.get("model_requested"), generated_utc=d.get("generated_utc"))
        return d["reply"], meta
    if "resp" in d:                                     # Claude Messages raw.json
        r = d["resp"]
        meta["model"] = r.get("model") or d.get("model")
        return "\n".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text"), meta
    if "final" in d:                                    # Grok /responses raw.json
        f = d["final"] or {}
        meta["model"] = f.get("model") or d.get("payload_model")
        return "\n".join(c.get("text", "") for it in f.get("output", []) if it.get("type") == "message"
                         for c in it.get("content", []) if c.get("type") == "output_text"), meta
    raise ValueError(f"{src}: unrecognised JSON reply shape")


def find_source(run_dir: Path, model: str) -> Path | None:
    for name in ("ping.json", "reply.md", "raw.json"):
        p = run_dir / model / name
        if p.is_file() and p.stat().st_size:
            return p
    return None


def check(round_dir: str | Path, models=MODELS) -> list[str]:
    """Models whose {model}.md is missing or has no reply body."""
    bad = []
    for m in models:
        f = Path(round_dir) / f"{m}.md"
        if not f.is_file() or not HEADER_RE.sub("", f.read_text()).strip():
            bad.append(m)
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Land model replies into reviews/<round>/{model}.md")
    ap.add_argument("--round-dir", required=True, help="e.g. reviews/2026-10-19_round6")
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--src", help="reply source for --model (ping.json, raw.json, reply.md)")
    ap.add_argument("--from-run-dir", help="scratch run dir with <model>/{ping.json|reply.md|raw.json}; lands all found")
    ap.add_argument("--check", action="store_true", help="only verify all four replies are present")
    a = ap.parse_args(argv)
    if a.model or a.src:
        if not (a.model and a.src):
            ap.error("--model and --src go together")
        try:
            text, meta = extract(a.src)
            print("landed", land(a.round_dir, a.model, text, meta))
        except (ValueError, OSError, json.JSONDecodeError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    if a.from_run_dir:
        for m in MODELS:
            src = find_source(Path(a.from_run_dir), m)
            if src is None:
                print(f"{m}: no reply in {a.from_run_dir}/{m}/", file=sys.stderr)
                continue
            try:
                text, meta = extract(src)
                print("landed", land(a.round_dir, m, text, meta))
            except (ValueError, OSError, json.JSONDecodeError) as e:
                print(f"{m}: {e}", file=sys.stderr)
    missing = check(a.round_dir)
    if missing:
        print(f"NOT COMPLETE: missing/empty in {a.round_dir}: " + ", ".join(f"{m}.md" for m in missing), file=sys.stderr)
        return 1
    print(f"all four replies present in {a.round_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
