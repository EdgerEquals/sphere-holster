"""--ping mode for the Claude / Grok review runners (stdlib only), mirroring oai_compat.ping for Kimi / DeepSeek.

Sends one prompt (no diff), writes <out>/ping.json, and on success lands the reply in the review tree via
land_review_reply.land() when --land-dir (or env REVIEW_LAND_DIR) is set. --run-id (or env REVIEW_RUN_ID) is recorded
in ping.json and stamped on the landed reply; landing refuses a reply that does not belong to the round's current run. Exit codes: 0 ok, 2 missing secret,
3 API/parse error or landing failure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import harness_common as hc  # noqa: E402
import land_review_reply as lr  # noqa: E402

PING_SYSTEM = ("You are {name} on the Stratified Sphere four-model team (Kimi, DeepSeek, Claude, Grok). "
               "Answer the brief in the user message as {name}. Stay inside the scope it states. "
               "Do not invent repo file contents beyond what the brief provides.")


def _redact(s: str) -> str:
    return re.sub(r"(sk-|xai-|Bearer\s+)[A-Za-z0-9_\-]{8,}", r"\1[redacted]", str(s))


def ping_args(argv, name: str):
    ap = argparse.ArgumentParser(description=f"{name} ping")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ping", help="prompt text")
    g.add_argument("--ping-file", help="file holding the prompt (use for long briefs)")
    ap.add_argument("--depth", choices=["shallow", "deep"], default=None)
    ap.add_argument("--out", default="review-out")
    ap.add_argument("--land-dir", default=os.environ.get("REVIEW_LAND_DIR") or None,
                    help="round review dir, e.g. reviews/2026-10-19_round6; the reply lands there as {model}.md")
    ap.add_argument("--land-stem", default=None,
                    help='override land filename stem (default: model). Use e.g. kimi_teamwork for cross-review.')
    ap.add_argument("--run-id", default=os.environ.get("REVIEW_RUN_ID") or None,
                    help="current round run id (from launch_round.py / run.json); stamped on ping.json and the landed reply")
    a, _ = ap.parse_known_args(argv)
    prompt = Path(a.ping_file).read_text() if a.ping_file else a.ping
    return a, prompt


def land_after_ping(rec: dict, model_key: str, land_dir: str | None, out: Path,
                    land_stem: str | None = None) -> str | None:
    """Land a successful ping. Returns an error string (and marks rec) if landing failed.

    land_stem overrides the filename stem (default model -> {model}.md; pass f"{model}_teamwork" for
    the cross-review stage).
    """
    if not land_dir or not rec.get("ok"):
        return None
    try:
        dest = lr.land(land_dir, model_key, rec["reply"],
                       {"model": rec.get("model"), "generated_utc": rec.get("generated_utc"),
                        "source": str(out / "ping.json")},
                       name=land_stem, run_id=rec.get("run_id"))
        rec["landed"] = str(dest)
        return None
    except Exception as e:  # noqa: BLE001
        rec["landed"] = None
        rec["land_error"] = f"{type(e).__name__}: {e}"
        return rec["land_error"]


def ping_main(name: str, model_key: str, secret: str, call, argv=None) -> int:
    """call(system, user, cfg, key) -> (text, usage, model), as in review_claude.py / review_grok.py."""
    a, prompt = ping_args(sys.argv[1:] if argv is None else argv, name)
    depth, cfg = hc.level_cfg(hc.load_dial(), a.depth)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = {"reviewer": name, "mode": "ping", "depth": depth, "prompt": prompt, "generated_utc": hc.now_utc(),
           "run_id": a.run_id}
    key = os.environ.get(secret, "").strip()
    if not key:
        rec.update(ok=False, error=f"{secret} is not set; no API call was made.")
        (out / "ping.json").write_text(json.dumps(rec, indent=2))
        print(rec["error"], file=sys.stderr)
        return hc.EXIT_MISSING_SECRET
    code = 0
    try:
        text, usage, model = call(PING_SYSTEM.format(name=name), prompt, cfg, key)
        rec.update(ok=True, model=model, reply=text, usage=usage)
    except Exception as e:  # noqa: BLE001
        rec.update(ok=False, error=_redact(f"{type(e).__name__}: {e}")[:1500])
        print(rec["error"], file=sys.stderr)
        code = hc.EXIT_API_ERROR
    err = land_after_ping(rec, model_key, a.land_dir, out, land_stem=a.land_stem)
    if err:
        print(f"{name}: reply NOT landed in {a.land_dir}: {err}", file=sys.stderr)
        code = hc.EXIT_API_ERROR
    (out / "ping.json").write_text(json.dumps(rec, indent=2))
    if rec.get("ok"):
        print(f"{name} ping OK · model {rec.get('model')} · landed {rec.get('landed') or '(no --land-dir)'}")
    return code
