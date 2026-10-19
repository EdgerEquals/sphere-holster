#!/usr/bin/env python3
"""Fire the four round pings as one job and land every reply in the review tree (stdlib only).

  python scripts/launch_round.py --round-dir reviews/2026-10-19_round6 \
      --prompt reviews/2026-10-19_round6/prompt.md --scope-file scope.txt --run-dir /tmp/round6-run

  # Cross-review stage (each model scores the other three); lands {model}_teamwork.md
  python scripts/launch_round.py --stage teamwork --round-dir reviews/2026-10-19_round6 \
      --run-dir /tmp/round6-teamwork

Stages:
  primary (default): shared brief -> review_{kimi,deepseek,claude,grok}.py --land-dir; COMPLETE when
    kimi.md, deepseek.md, claude.md, grok.md all present.
  teamwork: build a per-model prompt that includes the other three primary replies; land as
    {model}_teamwork.md; COMPLETE only when all four *_teamwork.md are present. Does not overwrite
    the primary {model}.md files.

--land-only re-lands from an existing <run-dir> without any API call (recovery for older runs).
With --stage teamwork --land-only, lands as {model}_teamwork.md.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import land_review_reply as lr  # noqa: E402

HEADER_RE = re.compile(r"\A<!-- landed: .*?-->\n+", re.S)

TEAMWORK_BRIEF = """# Round 6 cross-review (teamwork)

You are **{name}** on the Stratified Sphere four-model team (Kimi, DeepSeek, Claude, Grok).

## Mission (score every peer against this — pass/fail)
- Round 6 delivers **gates, sequencing, and peer-scoring design only**
- **No invented thresholds** (do not invent escalate cutoffs, amplitudes, frequencies, or pressures)
- Amplitude sweep is **blocked** and deferred to **round 8** (not round 7)
- Pass = peer stays inside that mission; Fail = peer invents numbers, runs/proposes a sweep this round, or mis-assigns the sweep to the wrong round without correcting it

## Discrepancy flag (required note)
`reviews/2026-10-19_round6/kimi.md` is still from the **first land** and may still call the sweep **round 7**. DeepSeek, Claude, and Grok (refire) correctly say **round 8**. Call this out when scoring Kimi (or when you are Kimi correcting your own prior reply).

## Your own primary reply (context — do not re-argue from scratch)
{own}

## Peer replies to score
{peers}

## Required deliverable
1. For **each** peer above: **PASS** or **FAIL** against the mission, with a one-line reason.
2. Brief critique of each peer's arguments (what holds, what does not).
3. Explicit statement: do you **agree with the round-8 consensus** (sweep deferred to round 8)? Yes/No + one sentence.
4. If scoring Kimi (or if you are Kimi): note the round-7 vs round-8 discrepancy and whether that alone is a FAIL or a soft flag.

Stay inside this cross-review. Do not run a sweep. Do not invent thresholds. Keep the reply concise.
"""


def _body(path: Path) -> str:
    return HEADER_RE.sub("", path.read_text()).strip()


def build_teamwork_prompt(round_dir: Path, model: str) -> str:
    names = {"kimi": "Kimi", "deepseek": "DeepSeek", "claude": "Claude", "grok": "Grok"}
    own_path = round_dir / f"{model}.md"
    if not own_path.is_file():
        raise FileNotFoundError(f"missing primary reply {own_path}")
    peer_bits = []
    for m in lr.MODELS:
        if m == model:
            continue
        p = round_dir / f"{m}.md"
        if not p.is_file():
            raise FileNotFoundError(f"missing peer reply {p}")
        peer_bits.append(f"### {names[m]} (`{m}.md`)\n\n{_body(p)}")
    return TEAMWORK_BRIEF.format(name=names[model], own=_body(own_path), peers="\n\n".join(peer_bits))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Launch the four round pings and land replies")
    ap.add_argument("--round-dir", required=True)
    ap.add_argument("--run-dir", required=True, help="scratch dir for ping.json / stdout / stderr per model")
    ap.add_argument("--prompt", help="team brief (e.g. reviews/<round>/prompt.md); required for primary stage")
    ap.add_argument("--scope-file", help="optional scope override prepended to the brief")
    ap.add_argument("--depth", choices=["shallow", "deep"], default="shallow")
    ap.add_argument("--models", default=",".join(lr.MODELS))
    ap.add_argument("--stage", choices=["primary", "teamwork"], default="primary",
                    help="primary lands {model}.md; teamwork lands {model}_teamwork.md from peer context")
    ap.add_argument("--land-only", action="store_true", help="no API calls; land from existing --run-dir and check")
    a = ap.parse_args(argv)
    run = Path(a.run_dir)
    round_dir = Path(a.round_dir)
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    suffix = "_teamwork" if a.stage == "teamwork" else ""

    if a.land_only:
        return lr.main(["--round-dir", a.round_dir, "--from-run-dir", str(run), "--suffix", suffix])

    run.mkdir(parents=True, exist_ok=True)
    procs = {}
    for m in models:
        d = run / m
        d.mkdir(parents=True, exist_ok=True)
        if a.stage == "teamwork":
            brief = d / "teamwork_prompt.txt"
            brief.write_text(build_teamwork_prompt(round_dir, m))
            land_stem = f"{m}_teamwork"
        else:
            if not a.prompt:
                ap.error("--prompt is required unless --land-only or --stage teamwork")
            text = Path(a.prompt).read_text()
            if a.scope_file:
                text = Path(a.scope_file).read_text().rstrip() + "\n\n=== TEAM BRIEF (verbatim) ===\n\n" + text
            brief = run / "user_prompt.txt"
            if not brief.exists() or m == models[0]:
                brief.write_text(text)
            land_stem = m
        cmd = [sys.executable, str(HERE / f"review_{m}.py"), "--ping-file", str(brief), "--depth", a.depth,
               "--out", str(d), "--land-dir", a.round_dir, "--land-stem", land_stem]
        procs[m] = (subprocess.Popen(cmd, stdout=open(d / "stdout.txt", "w"), stderr=open(d / "stderr.txt", "w")), d)

    rc = {m: p.wait() for m, (p, _) in procs.items()}
    for m, code in rc.items():
        print(f"{m}: exit {code}" + ("" if code == 0 else f" (see {procs[m][1] / 'stderr.txt'})"))

    missing = lr.check(a.round_dir, models, suffix=suffix)
    label = f"{{m}}{suffix}.md"
    if missing:
        print(f"NOT COMPLETE: missing/empty in {a.round_dir}: " + ", ".join(label.format(m=m) for m in missing),
              file=sys.stderr)
        return 1
    print(f"COMPLETE: {', '.join(label.format(m=m) for m in models)} landed in {a.round_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
