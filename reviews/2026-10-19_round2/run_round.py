#!/usr/bin/env python3
"""Review round 2: harness / information-layer DESIGN review. Reuses round 1's callers, pricing and retry logic.

Same four models and caps as round 1, except Kimi starts at max_tokens 12000 (round 1's 6000 was eaten by reasoning).
Usage: python3 reviews/2026-10-19_round2/run_round.py reviews/2026-10-19_round2/context_pack.md <out_dir>
"""
import datetime as dt
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("round1", HERE.parent / "2026-10-19_round1" / "run_round.py")
r1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r1)

QUESTION = """You are one of four independent reviewers (Claude, Grok, Kimi, DeepSeek) in a cross-model design review.
Subject: the "holster" (harness) layer and the information layer of the Stratified Sphere project — how the
multi-model, multi-tool workflow is designed and what is actually built. NOT the physics.
The context pack below is self-contained; do not browse.

Answer in at most 450 words, concrete and specific to this design (name files, workflows, tiers, triggers):
1. How would you optimise this design?
2. Where is it weak?"""

MAX_TOKENS = {"Claude": (6000, 12000), "Grok": (6000, 12000), "Kimi": (12000, 16000), "DeepSeek": (6000, 12000)}


def main():
    pack, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    prompt = f"{QUESTION}\n\n===== CONTEXT PACK =====\n{pack.read_text(encoding='utf-8')}"
    (out / "prompt.md").write_text(prompt, encoding="utf-8")
    results = {}
    for name, fn in r1.CALLS:
        attempts = []
        for mt in MAX_TOKENS[name]:                 # second value = one retry with more headroom if reply is empty
            t0 = time.time(); t_utc = dt.datetime.now(dt.timezone.utc)
            try:
                r = fn(prompt, mt); r["error"] = None
            except Exception as e:  # noqa: BLE001
                r = dict(text="", error=f"{type(e).__name__}: {e}"[:800], input=0, output=0, cached=0, reasoning=None)
            r.update(max_tokens=mt, seconds=round(time.time() - t0, 1), started_utc=t_utc.isoformat(timespec="seconds"))
            r["cost_usd"], r["price"] = r1.price(name, r, t_utc)
            attempts.append(r)
            print(f"{name}: max_tokens={mt} in={r['input']} cached={r.get('cached')} out={r['output']} "
                  f"reasoning={r.get('reasoning')} stop={r.get('stop')} words={len(r['text'].split())} "
                  f"err={r['error']} {r['seconds']}s", flush=True)
            if r["text"].strip() or r["error"]:
                break
        results[name] = attempts
    (out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
