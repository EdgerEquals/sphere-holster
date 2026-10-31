#!/usr/bin/env python3
"""Land each model's round reply in the review tree as reviews/YYYY-MM-DD_roundN/{model}.md (stdlib only).

Why this exists: the round pings (review_kimi/review_deepseek --ping, plus ad-hoc Claude/Grok runners) wrote replies
only to a scratch out dir (ping.json / reply.md under /tmp); copying them into the review folder was a manual prose
step in the kickoff, so round 6 ended with only deepseek.md landed. Every ping path now calls land() on success, and a
run is not complete until check() finds all four files.

Teamwork stage: land(..., name=f"{model}_teamwork") writes {model}_teamwork.md (cross-review of peers). check(...,
suffix="_teamwork") verifies those instead of the primary replies.

Stale-reply guard: each stage run (primary / teamwork) is recorded in <round-dir>/run.json by start_run() with a
run_id and started_utc. Every landed reply is stamped run_id=… · landed_utc=… in its provenance header. While a run
is current for a stage, land() refuses (StaleReplyError) a reply whose run_id belongs to another run, whose
generated_utc / source mtime predates the run start, or that carries no timestamp at all; check() / --check reports a
file as STALE when its header run_id is not the current run's or its generated_utc predates the run start. A round
folder with no run.json (legacy) is checked for presence only.

Usage:
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --model kimi --src /tmp/round6-run/kimi/ping.json
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --from-run-dir /tmp/round6-run
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --check
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --check --suffix _teamwork
  python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --start-run primary   # prints run_id
Sources understood: ping.json ({"reply": ...}), Claude raw.json ({"resp": {"content": [...]}}), Grok raw.json
({"final": {"output": [...]}}), or a plain .md/.txt reply. Exit codes: 0 ok, 1 missing/empty/stale replies, 2 bad or stale source.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

MODELS = ("kimi", "deepseek", "claude", "grok")
CHANNELS = {
    "kimi": "scripts/review_kimi.py --ping",
    "deepseek": "scripts/review_deepseek.py --ping",
    "claude": "scripts/review_claude.py --ping",
    "grok": "scripts/review_grok.py --ping",
}
HEADER_RE = re.compile(r"\A<!-- landed: .*?-->\n+", re.S)
HEADER_KEYS = ("model", "channel", "generated_utc", "source", "run_id", "landed_utc")
RUN_FILE = "run.json"
STAGES = ("primary", "teamwork")
TS_FMT = "%Y-%m-%dT%H:%M:%SZ"


class StaleReplyError(ValueError):
    """A reply that does not belong to (or predates) the current run for its stage."""


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime(TS_FMT)


def _ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(str(s), TS_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def stage_of(stem: str) -> str:
    return "teamwork" if stem.endswith("_teamwork") else "primary"


def _suffix_stage(suffix: str) -> str:
    return "teamwork" if suffix == "_teamwork" else "primary"


def load_runs(round_dir: str | Path) -> dict:
    f = Path(round_dir) / RUN_FILE
    if not f.is_file():
        return {}
    try:
        return json.loads(f.read_text())
    except json.JSONDecodeError:
        return {}


def _save_runs(round_dir: str | Path, runs: dict) -> None:
    d = Path(round_dir)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / (RUN_FILE + ".tmp")
    tmp.write_text(json.dumps(runs, indent=2) + "\n")
    os.replace(tmp, d / RUN_FILE)


def current_run(round_dir: str | Path, stage: str = "primary") -> dict | None:
    return load_runs(round_dir).get(stage)


def start_run(round_dir: str | Path, stage: str = "primary", run_id: str | None = None, **extra) -> dict:
    """Record a new current run for stage in <round_dir>/run.json and return it.

    Starting a primary run invalidates the teamwork run and any close record (they scored older replies).
    Starting a teamwork run invalidates the close record.
    """
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}")
    started = now_utc()
    rid = run_id or f"{stage}-{started.replace('-', '').replace(':', '')}-{secrets.token_hex(3)}"
    runs = load_runs(round_dir)
    runs[stage] = {"run_id": rid, "started_utc": started, **extra}
    runs.pop("closed", None)
    if stage == "primary":
        runs.pop("teamwork", None)
    _save_runs(round_dir, runs)
    return runs[stage]


def record_close(round_dir: str | Path, **info) -> dict:
    runs = load_runs(round_dir)
    runs["closed"] = {"closed_utc": now_utc(), **info}
    _save_runs(round_dir, runs)
    return runs["closed"]


def parse_header(text: str) -> dict:
    m = HEADER_RE.match(text or "")
    if not m:
        return {}
    inner = m.group(0).strip()[len("<!-- landed:"):-len("-->")].strip()
    out = {}
    for bit in inner.split(" · "):
        k, eq, v = bit.partition("=")
        if eq:
            out[k.strip()] = v.strip()
    return out


def header(model: str, meta: dict) -> str:
    bits = [f"{k}={meta[k]}" for k in HEADER_KEYS if meta.get(k)]
    return f"<!-- landed: reviewer={model} · " + " · ".join(bits) + " -->\n\n"


def stale_reason(meta: dict, run: dict | None) -> str | None:
    """Why a reply with this provenance does not belong to run (None = fresh, or no current run)."""
    if not run:
        return None
    rid = meta.get("run_id")
    if rid and rid != run["run_id"]:
        return f"run_id {rid} is not the current run {run['run_id']}"
    gen = _ts(meta.get("generated_utc") or meta.get("source_mtime_utc"))
    start = _ts(run.get("started_utc"))
    if gen is None:
        if rid:                      # stamped with the current run_id by the launcher; nothing older to compare
            return None
        return f"no run_id and no generated_utc/timestamp; cannot prove it belongs to run {run['run_id']}"
    if start and gen < start:
        return (f"generated {meta.get('generated_utc') or meta.get('source_mtime_utc')} predates current run "
                f"{run['run_id']} (started {run['started_utc']})")
    return None


def teamwork_mismatch(round_dir: str | Path) -> str | None:
    """Why cross-review files cannot count for the current primary run (None = consistent or legacy)."""
    runs = load_runs(round_dir)
    prim, team = runs.get("primary"), runs.get("teamwork")
    if not prim:
        return None
    if not team:
        return f"no cross-review run since current primary run {prim['run_id']}"
    if team.get("primary_run_id") != prim["run_id"]:
        return (f"cross-review run {team['run_id']} scored primary run {team.get('primary_run_id')}, "
                f"not current {prim['run_id']}")
    return None


def land(round_dir: str | Path, model: str, text: str, meta: dict | None = None,
         name: str | None = None, run_id: str | None = None) -> Path:
    """Write {round_dir}/{name or model}.md (provenance comment + reply body). Refuses an empty reply.

    name defaults to model (primary reply). Pass f"{model}_teamwork" for the cross-review stage so the primary
    {model}.md is not overwritten. If run.json holds a current run for the stage, the reply must belong to it
    (StaleReplyError otherwise) and is stamped with that run_id; landed_utc is always stamped.
    """
    model = model.lower()
    if model not in MODELS:
        raise ValueError(f"unknown model '{model}' (expected one of {', '.join(MODELS)})")
    stem = (name or model).strip()
    if not stem or "/" in stem or "\\" in stem or stem.startswith("."):
        raise ValueError(f"bad land name {name!r}")
    body = HEADER_RE.sub("", (text or "").strip()).strip()
    if not body:
        raise ValueError(f"{stem}: empty reply; nothing landed")
    meta = {"channel": CHANNELS[model], **{k: v for k, v in (meta or {}).items() if v}}
    if run_id:
        meta["run_id"] = run_id
    stage = stage_of(stem)
    run = current_run(round_dir, stage)
    why = teamwork_mismatch(round_dir) if stage == "teamwork" else None
    why = why or stale_reason(meta, run)
    if why:
        raise StaleReplyError(f"{stem}: refusing stale reply: {why}")
    if run:
        meta["run_id"] = run["run_id"]
    if not meta.get("generated_utc") and meta.get("source_mtime_utc"):
        meta["generated_utc"] = meta["source_mtime_utc"]
    meta["landed_utc"] = now_utc()
    d = Path(round_dir)
    d.mkdir(parents=True, exist_ok=True)
    dest = d / f"{stem}.md"
    tmp = dest.with_suffix(".md.tmp")
    tmp.write_text(header(model, meta) + body + "\n")
    os.replace(tmp, dest)
    return dest


def extract(src: str | Path) -> tuple[str, dict]:
    """Return (reply_text, meta) from a ping.json, Claude/Grok raw.json, or a plain reply file."""
    src = Path(src)
    mtime = datetime.fromtimestamp(src.stat().st_mtime, timezone.utc).strftime(TS_FMT)
    if src.suffix != ".json":
        meta = {"source": str(src), "source_mtime_utc": mtime}
        sib = src.with_name("raw.json")             # ad-hoc runners keep model metadata next to reply.md
        if sib.is_file():
            try:
                meta.update({k: v for k, v in extract(sib)[1].items()
                             if k not in ("source", "source_mtime_utc") and v})
            except (ValueError, json.JSONDecodeError):
                pass
        return src.read_text(), meta
    d = json.loads(src.read_text())
    meta = {"source": str(src), "source_mtime_utc": mtime}
    if "reply" in d:                                    # ping.json (oai_compat / ping_main)
        if d.get("ok") is False:
            raise ValueError(f"{src}: ping recorded ok=false ({d.get('error', '')[:200]})")
        meta.update(model=d.get("model") or d.get("model_requested"), generated_utc=d.get("generated_utc"),
                    run_id=d.get("run_id"))
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


def check_detail(round_dir: str | Path, models=MODELS, suffix: str = "") -> dict[str, str]:
    """{model: reason} for every {model}{suffix}.md that is missing, empty, or stale vs the current run."""
    stage = _suffix_stage(suffix)
    run = current_run(round_dir, stage)
    mismatch = teamwork_mismatch(round_dir) if stage == "teamwork" else None
    bad = {}
    for m in models:
        f = Path(round_dir) / f"{m}{suffix}.md"
        if not f.is_file():
            bad[m] = "missing"
            continue
        text = f.read_text()
        if not HEADER_RE.sub("", text).strip():
            bad[m] = "empty"
            continue
        if mismatch:
            bad[m] = f"STALE: {mismatch}"
            continue
        if run:
            meta = parse_header(text)
            if not meta.get("run_id"):
                bad[m] = f"STALE: no run_id stamp; predates current run {run['run_id']}"
                continue
            why = stale_reason(meta, run)
            if why:
                bad[m] = f"STALE: {why}"
    return bad


def check(round_dir: str | Path, models=MODELS, suffix: str = "") -> list[str]:
    """Models whose {model}{suffix}.md is missing, has no reply body, or predates the current run.

    suffix="" -> primary kimi.md etc. suffix="_teamwork" -> kimi_teamwork.md etc.
    """
    return list(check_detail(round_dir, models, suffix))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Land model replies into reviews/<round>/{model}.md")
    ap.add_argument("--round-dir", required=True, help="e.g. reviews/2026-10-19_round6")
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--src", help="reply source for --model (ping.json, raw.json, reply.md)")
    ap.add_argument("--from-run-dir", help="scratch run dir with <model>/{ping.json|reply.md|raw.json}; lands all found")
    ap.add_argument("--check", action="store_true", help="only verify all four replies are present")
    ap.add_argument("--suffix", default="", help='file suffix after model, e.g. "_teamwork" for {model}_teamwork.md')
    ap.add_argument("--name", help="override land filename stem (with --model/--src); e.g. kimi_teamwork")
    ap.add_argument("--run-id", help="run the reply belongs to; must match the current run in run.json if one exists")
    ap.add_argument("--start-run", choices=STAGES, help="record a new current run for this stage, print its run_id")
    a = ap.parse_args(argv)
    suffix = a.suffix or ""
    if a.start_run:
        print(start_run(a.round_dir, a.start_run)["run_id"])
        return 0
    if a.model or a.src:
        if not (a.model and a.src):
            ap.error("--model and --src go together")
        try:
            reply, meta = extract(a.src)
            stem = a.name or (f"{a.model}{suffix}" if suffix else None)
            print("landed", land(a.round_dir, a.model, reply, meta, name=stem, run_id=a.run_id))
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
                reply, meta = extract(src)
                stem = f"{m}{suffix}" if suffix else None
                print("landed", land(a.round_dir, m, reply, meta, name=stem, run_id=a.run_id))
            except (ValueError, OSError, json.JSONDecodeError) as e:
                print(f"{m}: {e}", file=sys.stderr)
    bad = check_detail(a.round_dir, suffix=suffix)
    label = f"{{m}}{suffix}.md"
    if bad:
        print(f"NOT COMPLETE: missing/empty/stale in {a.round_dir}: "
              + "; ".join(f"{label.format(m=m)} ({why})" for m, why in bad.items()), file=sys.stderr)
        return 1
    run = current_run(a.round_dir, _suffix_stage(suffix))
    print(f"all four {label.replace('{m}', '*')} present in {a.round_dir}"
          + (f" (current run {run['run_id']})" if run else " (no run.json: presence check only)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
