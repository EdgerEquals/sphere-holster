#!/usr/bin/env python3
"""Run a review round as a fixed four-step sequence and land every reply in the review tree (stdlib only).

  # Full round (default --stage all): fire -> land (gate 1) -> cross-review (gate 2) -> close
  python scripts/launch_round.py --round-dir reviews/2026-10-19_round6 \
      --prompt reviews/2026-10-19_round6/prompt.md --scope-file scope.txt --run-dir /tmp/round6-run

  # Single stages (recovery / re-runs); each still enforces the gate before it
  python scripts/launch_round.py --stage primary  --round-dir R --prompt P --run-dir /tmp/rN-run
  python scripts/launch_round.py --stage teamwork --round-dir R --run-dir /tmp/rN-teamwork
  python scripts/launch_round.py --stage close    --round-dir R --run-dir /tmp/rN-run   # check-only

Sequence (cannot be skipped):
  (a) fire   primary: shared brief -> review_{kimi,deepseek,claude,grok}.py --land-dir --run-id.
  (b) land   Gate 1 (primary COMPLETE): kimi.md, deepseek.md, claude.md, grok.md all present AND stamped with the
             current primary run_id (none older than the run start).
  (c) cross-review  teamwork: refuses to start unless gate 1 passes; each model gets the other three replies
             (current-run versions, with their run_id) and scores them; lands {model}_teamwork.md. Gate 2 (teamwork
             COMPLETE): all four *_teamwork.md present and stamped with the current teamwork run_id.
  (d) close  the round closes only when gate 1 and gate 2 both pass AND the teamwork run scored the current primary
             run (a primary re-fire after cross-review re-opens the round). Close is recorded in <round-dir>/run.json.

Runs are recorded in <round-dir>/run.json (land_review_reply.start_run). Starting a primary run clears the teamwork
run and any close record, so a re-fire can never be closed against cross-reviews of the old replies.

--land-only re-lands from an existing <run-dir> without any API call (recovery). Replies must still belong to the
current run for that stage (stale replies are refused). With --stage teamwork, lands as {model}_teamwork.md.
Exit codes: 0 stage/round COMPLETE (or CLOSED for close/all), 1 NOT COMPLETE / gate failed.
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
NAMES = {"kimi": "Kimi", "deepseek": "DeepSeek", "claude": "Claude", "grok": "Grok"}

TEAMWORK_BRIEF = """# Round cross-review (teamwork)

You are **{name}** on the Stratified Sphere four-model team (Kimi, DeepSeek, Claude, Grok).

## Mission (score every peer against this — pass/fail)
- Round 6 delivers **gates, sequencing, and peer-scoring design only**
- **No invented thresholds** (do not invent escalate cutoffs, amplitudes, frequencies, or pressures)
- Amplitude sweep is **blocked** and deferred to **round 8** (not round 7)
- Pass = peer stays inside that mission; Fail = peer invents numbers, runs/proposes a sweep this round, or mis-assigns the sweep to the wrong round without correcting it

## Freshness (verified by the launcher)
All four replies below are from primary run `{primary_run_id}` (each file stamped with that run_id; none predates the run start).
{freshness}
Score the text as given. Do not assume any reply is from an earlier run unless its stamp says so.

## Your own primary reply (context — do not re-argue from scratch)
{own}

## Peer replies to score
{peers}

## Required deliverable
1. For **each** peer above: **PASS** or **FAIL** against the mission, with a one-line reason.
2. Brief critique of each peer's arguments (what holds, what does not).
3. Explicit statement: do you **agree with the round-8 consensus** (sweep deferred to round 8)? Yes/No + one sentence.
4. If any peer assigns the sweep to the wrong round, say whether that alone is a FAIL or a soft flag.

Stay inside this cross-review. Do not run a sweep. Do not invent thresholds. Keep the reply concise.
"""


def _body(path: Path) -> str:
    return HEADER_RE.sub("", path.read_text()).strip()


def _gate(round_dir: Path, models, suffix: str, label: str) -> bool:
    bad = lr.check_detail(round_dir, models, suffix=suffix)
    names = f"{{m}}{suffix}.md"
    if bad:
        print(f"{label} NOT COMPLETE in {round_dir}: "
              + "; ".join(f"{names.format(m=m)} ({why})" for m, why in bad.items()), file=sys.stderr)
        return False
    run = lr.current_run(round_dir, "teamwork" if suffix else "primary")
    print(f"{label} COMPLETE: {', '.join(names.format(m=m) for m in models)} in {round_dir}"
          + (f" (run {run['run_id']})" if run else ""))
    return True


def build_teamwork_prompt(round_dir: Path, model: str) -> str:
    """Per-model cross-review brief. Refuses (FileNotFoundError / StaleReplyError) unless gate 1 passes."""
    round_dir = Path(round_dir)
    bad = lr.check_detail(round_dir)
    missing = {m: w for m, w in bad.items() if w == "missing"}
    if missing:
        raise FileNotFoundError(f"missing primary reply {round_dir / (next(iter(missing)) + '.md')}")
    if bad:
        raise lr.StaleReplyError("primary gate not passed; cross-review would score stale/empty replies: "
                                 + "; ".join(f"{m}.md ({w})" for m, w in bad.items()))
    run = lr.current_run(round_dir, "primary") or {}
    fresh, peer_bits = [], []
    for m in lr.MODELS:
        meta = lr.parse_header((round_dir / f"{m}.md").read_text())
        fresh.append(f"- `{m}.md`: run_id `{meta.get('run_id', 'unstamped')}` · generated "
                     f"`{meta.get('generated_utc', '?')}` · model `{meta.get('model', '?')}`")
        if m != model:
            peer_bits.append(f"### {NAMES[m]} (`{m}.md`)\n\n{_body(round_dir / f'{m}.md')}")
    return TEAMWORK_BRIEF.format(name=NAMES[model], own=_body(round_dir / f"{model}.md"),
                                 peers="\n\n".join(peer_bits), primary_run_id=run.get("run_id", "legacy (no run.json)"),
                                 freshness="\n".join(fresh))


def _fire(stage: str, a, round_dir: Path, run: Path, models, run_id: str) -> None:
    run.mkdir(parents=True, exist_ok=True)
    procs = {}
    for m in models:
        d = run / m
        d.mkdir(parents=True, exist_ok=True)
        if stage == "teamwork":
            brief = d / "teamwork_prompt.txt"
            brief.write_text(build_teamwork_prompt(round_dir, m))
            stem = f"{m}_teamwork"
        else:
            text = Path(a.prompt).read_text()
            if a.scope_file:
                text = Path(a.scope_file).read_text().rstrip() + "\n\n=== TEAM BRIEF (verbatim) ===\n\n" + text
            brief = run / "user_prompt.txt"
            if not brief.exists() or m == models[0]:
                brief.write_text(text)
            stem = m
        cmd = [sys.executable, str(HERE / f"review_{m}.py"), "--ping-file", str(brief), "--depth", a.depth,
               "--out", str(d), "--land-dir", str(round_dir), "--land-stem", stem, "--run-id", run_id]
        procs[m] = (subprocess.Popen(cmd, stdout=open(d / "stdout.txt", "w"), stderr=open(d / "stderr.txt", "w")), d)
    for m, (p, d) in procs.items():
        code = p.wait()
        print(f"{stage}/{m}: exit {code}" + ("" if code == 0 else f" (see {d / 'stderr.txt'})"))


def close_round(round_dir: Path, models=lr.MODELS) -> bool:
    """(d) Round closes only when both gates pass and cross-review scored the current primary run."""
    ok1 = _gate(round_dir, models, "", "Gate 1 (replies landed)")
    ok2 = _gate(round_dir, models, "_teamwork", "Gate 2 (cross-review)")
    prim, team = lr.current_run(round_dir, "primary"), lr.current_run(round_dir, "teamwork")
    if prim and (not team or team.get("primary_run_id") != prim["run_id"]):
        print(f"Gate 2 NOT COMPLETE: cross-review run {team and team.get('run_id')} did not score current primary "
              f"run {prim['run_id']}; re-run --stage teamwork", file=sys.stderr)
        ok2 = False
    if not (ok1 and ok2):
        print(f"ROUND NOT CLOSED: {round_dir}", file=sys.stderr)
        return False
    rec = lr.record_close(round_dir, primary_run_id=prim and prim["run_id"], teamwork_run_id=team and team["run_id"])
    print(f"ROUND CLOSED: {round_dir} at {rec['closed_utc']} (both gates pass)")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the four-model round: fire, land, cross-review, close")
    ap.add_argument("--round-dir", required=True)
    ap.add_argument("--run-dir", required=True, help="scratch dir for ping.json / stdout / stderr per model")
    ap.add_argument("--prompt", help="team brief (e.g. reviews/<round>/prompt.md); required for primary/all")
    ap.add_argument("--scope-file", help="optional scope override prepended to the brief")
    ap.add_argument("--depth", choices=["shallow", "deep"], default="shallow")
    ap.add_argument("--models", default=",".join(lr.MODELS))
    ap.add_argument("--stage", choices=["all", "primary", "teamwork", "close"], default="all",
                    help="all = primary -> gate 1 -> teamwork -> gate 2 -> close (default)")
    ap.add_argument("--teamwork-run-dir", help="scratch dir for the cross-review stage under --stage all "
                                               "(default <run-dir>-teamwork)")
    ap.add_argument("--land-only", action="store_true", help="no API calls; land from existing --run-dir and check")
    a = ap.parse_args(argv)
    run = Path(a.run_dir)
    round_dir = Path(a.round_dir)
    models = [m.strip() for m in a.models.split(",") if m.strip()]

    if a.stage == "close":
        return 0 if close_round(round_dir, models) else 1

    if a.land_only:
        stage = "teamwork" if a.stage == "teamwork" else "primary"
        suffix = "_teamwork" if stage == "teamwork" else ""
        lr.main(["--round-dir", str(round_dir), "--from-run-dir", str(run), "--suffix", suffix])
        return 0 if _gate(round_dir, models, suffix, f"{stage} (land-only)") else 1

    if a.stage in ("all", "primary"):
        if not a.prompt:
            ap.error("--prompt is required for --stage all/primary (unless --land-only)")
        rid = lr.start_run(round_dir, "primary")["run_id"]
        print(f"(a) fire: primary run {rid}")
        _fire("primary", a, round_dir, run, models, rid)
        if not _gate(round_dir, models, "", "(b) Gate 1 (replies landed)"):
            return 1
        if a.stage == "primary":
            return 0

    # (c) cross-review — refuses to start unless gate 1 passes on the current primary run
    if not _gate(round_dir, models, "", "Gate 1 precheck"):
        print("cross-review NOT started: gate 1 must pass first", file=sys.stderr)
        return 1
    prim = lr.current_run(round_dir, "primary")
    trun = Path(a.teamwork_run_dir) if a.teamwork_run_dir else (
        Path(str(run) + "-teamwork") if a.stage == "all" else run)
    rid = lr.start_run(round_dir, "teamwork", primary_run_id=prim and prim["run_id"])["run_id"]
    print(f"(c) cross-review: teamwork run {rid}")
    _fire("teamwork", a, round_dir, trun, models, rid)
    if not _gate(round_dir, models, "_teamwork", "Gate 2 (cross-review)"):
        return 1
    if a.stage == "teamwork":
        return 0
    return 0 if close_round(round_dir, models) else 1


if __name__ == "__main__":
    sys.exit(main())
