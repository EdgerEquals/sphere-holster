#!/usr/bin/env python3
"""Fire the four round pings as one job and land every reply in the review tree (stdlib only).

  python scripts/launch_round.py --round-dir reviews/2026-10-19_round6 \
      --prompt reviews/2026-10-19_round6/prompt.md --scope-file scope.txt --run-dir /tmp/round6-run

Steps: build the shared user text (optional scope override + prompt) once into <run-dir>/user_prompt.txt; run
review_{kimi,deepseek,claude,grok}.py --ping-file ... --out <run-dir>/<model> --land-dir <round-dir> in parallel;
then land_review_reply.check(). The run is COMPLETE (exit 0) only when kimi.md, deepseek.md, claude.md and grok.md
all exist with a reply body in <round-dir>. Replies left only in <run-dir> = exit 1, not done.
--land-only re-lands from an existing <run-dir> without any API call (recovery for older runs).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import land_review_reply as lr  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Launch the four round pings and land replies")
    ap.add_argument("--round-dir", required=True)
    ap.add_argument("--run-dir", required=True, help="scratch dir for ping.json / stdout / stderr per model")
    ap.add_argument("--prompt", help="team brief (e.g. reviews/<round>/prompt.md)")
    ap.add_argument("--scope-file", help="optional scope override prepended to the brief")
    ap.add_argument("--depth", choices=["shallow", "deep"], default="shallow")
    ap.add_argument("--models", default=",".join(lr.MODELS))
    ap.add_argument("--land-only", action="store_true", help="no API calls; land from existing --run-dir and check")
    a = ap.parse_args(argv)
    run = Path(a.run_dir)
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    if a.land_only:
        return lr.main(["--round-dir", a.round_dir, "--from-run-dir", str(run)])
    if not a.prompt:
        ap.error("--prompt is required unless --land-only")
    run.mkdir(parents=True, exist_ok=True)
    text = Path(a.prompt).read_text()
    if a.scope_file:
        text = Path(a.scope_file).read_text().rstrip() + "\n\n=== TEAM BRIEF (verbatim) ===\n\n" + text
    brief = run / "user_prompt.txt"
    brief.write_text(text)
    procs = {}
    for m in models:
        d = run / m
        d.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(HERE / f"review_{m}.py"), "--ping-file", str(brief), "--depth", a.depth,
               "--out", str(d), "--land-dir", a.round_dir]
        procs[m] = (subprocess.Popen(cmd, stdout=open(d / "stdout.txt", "w"), stderr=open(d / "stderr.txt", "w")), d)
    rc = {m: p.wait() for m, (p, _) in procs.items()}
    for m, code in rc.items():
        print(f"{m}: exit {code}" + ("" if code == 0 else f" (see {procs[m][1] / 'stderr.txt'})"))
    missing = lr.check(a.round_dir, models)
    if missing:
        print(f"NOT COMPLETE: missing/empty in {a.round_dir}: " + ", ".join(f"{m}.md" for m in missing), file=sys.stderr)
        return 1
    print(f"COMPLETE: {', '.join(f'{m}.md' for m in models)} landed in {a.round_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
