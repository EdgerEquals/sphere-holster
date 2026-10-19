#!/usr/bin/env python3
"""Monthly cost rollup per model (issue #9). Reads cost records from ledger/findings.jsonl (which holds every
reviewer verdict artifact, ping artifact, review-round results.json and Tavily search the ledger has ingested) and
writes ledger/costs_YYYY-MM.json + .md, plus ledger/index.html (Pages-visible table of all months + scorecards).

  python scripts/ledger_costs.py                 # current month (UTC) + rebuild index.html
  python scripts/ledger_costs.py --month 2026-10
  python scripts/ledger_costs.py --all           # every month present in the ledger
No network, no model calls.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import ledger_lib as L  # noqa: E402

ORDER = ["Claude", "Grok", "Kimi", "DeepSeek", "Tavily"]


def month_of(r: dict) -> str:
    return (r.get("event_utc") or r["recorded_utc"])[:7]


def rollup(records: list[dict], month: str) -> dict:
    rows = {}
    classes = L.review_classes(records)
    for r in records:
        if r["kind"] != "cost" or month_of(r) != month:
            continue
        key = (r["reviewer"], r.get("model") or "?", classes.get(r["id"], "legacy"))
        row = rows.setdefault(key, {"reviewer": key[0], "model": key[1], "review_class": key[2], "calls": 0, "input": 0, "cached": 0,
                                    "cache_write": 0, "output": 0, "reasoning": 0, "cost_usd": 0.0,
                                    "calls_without_cost": 0, "credits": 0.0, "sources": set()})
        row["calls"] += 1
        for k in ("input", "cached", "cache_write", "output", "reasoning"):
            row[k] += int((r.get("tokens") or {}).get(k) or 0)
        if r.get("cost_usd") is None:
            row["calls_without_cost"] += 1
        else:
            row["cost_usd"] += r["cost_usd"]
        row["credits"] += float(r.get("credits") or 0)
        row["sources"].add(r["source"]["type"])
    out = sorted(rows.values(), key=lambda x: (ORDER.index(x["reviewer"]) if x["reviewer"] in ORDER else 99, x["model"],
                                               x["review_class"]))
    for x in out:
        x["cost_usd"] = round(x["cost_usd"], 6); x["sources"] = sorted(x["sources"])
    per_reviewer = {}
    for x in out:
        per_reviewer[x["reviewer"]] = round(per_reviewer.get(x["reviewer"], 0) + x["cost_usd"], 6)
    per_class = {}
    for x in out:
        per_class[x["review_class"]] = round(per_class.get(x["review_class"], 0) + x["cost_usd"], 6)
    return {"month": month, "generated_utc": L.ledger_as_of(records), "rows": out, "per_reviewer_usd": per_reviewer,
            "per_class_usd": per_class,
            "total_usd": round(sum(x["cost_usd"] for x in out), 6),
            "tavily_credits": sum(x["credits"] for x in out),
            "calls_without_cost": sum(x["calls_without_cost"] for x in out),
            "note": "Costs are as reported by the APIs (Grok ticks, oai_compat cost_usd, round runners) or computed from "
                    "harness/ledger.json list prices. Only spend that reached the ledger is counted; calls made outside "
                    "the harness (e.g. ad-hoc local tests) are not included."}


def render_md(r: dict) -> str:
    L_ = [f"# Cost rollup {r['month']}", "", f"Ledger as of {r['generated_utc']}, from `ledger/findings.jsonl` (issue #9).", "",
          "| Reviewer | model | review class | calls | input | cached | output | reasoning | cost (USD) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for x in r["rows"]:
        cost = f"${x['cost_usd']:.4f}" + (f" (+{x['calls_without_cost']} unpriced)" if x["calls_without_cost"] else "")
        if x["reviewer"] == "Tavily":
            cost = f"$0 ({x['credits']:g} credits)"
        L_.append(f"| {x['reviewer']} | {x['model']} | {x['review_class']} | {x['calls']} | {x['input']} | {x['cached']} | {x['output']} | "
                  f"{x['reasoning']} | {cost} |")
    L_ += [f"| **Total** | | | | | | | | **${r['total_usd']:.4f}** |", "",
           "Per reviewer: " + ", ".join(f"{k} ${v:.4f}" for k, v in r["per_reviewer_usd"].items()), "",
           "Per review class: " + ", ".join(f"{k} ${v:.4f}" for k, v in r.get("per_class_usd", {}).items()) +
           " (code-review = receipt-backed; spec-review = no receipt, unscored; legacy = before the receipt gate)", "",
           r["note"]]
    return "\n".join(L_) + "\n"


def write_month(records, month: str, out_dir: Path) -> dict:
    r = rollup(records, month)
    (out_dir / f"costs_{month}.json").write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    (out_dir / f"costs_{month}.md").write_text(render_md(r), encoding="utf-8")
    return r


def write_index(out_dir: Path) -> None:
    parts = ["<!doctype html><meta charset='utf-8'><title>Stratified Sphere holster ledger</title>",
             "<style>body{font:14px system-ui;margin:2em;max-width:70em}table{border-collapse:collapse}"
             "td,th{border:1px solid #ccc;padding:3px 8px;text-align:right}td:first-child,td:nth-child(2),td:nth-child(3){text-align:left}</style>",
             "<h1>Holster ledger: monthly cost per model</h1>",
             "<p>Generated from <code>ledger/findings.jsonl</code>. Source: issues #7 to #9. Review class (round 4): "
             "code-review = backed by a CI execution receipt; spec-review = no receipt, never scored; legacy = before the gate.</p>"]
    for f in sorted(out_dir.glob("costs_*.json"), reverse=True):
        r = json.loads(f.read_text())
        split = ", ".join(f"{html.escape(k)} ${v:.4f}" for k, v in r.get("per_class_usd", {}).items())
        parts.append(f"<h2>{html.escape(r['month'])}: ${r['total_usd']:.4f}</h2><p>By review class: {split}</p>"
                     "<table><tr><th>Reviewer</th><th>model</th><th>review class</th><th>calls</th><th>input</th><th>cached</th><th>output</th><th>reasoning</th><th>cost (USD)</th></tr>")
        for x in r["rows"]:
            cost = f"{x['credits']:g} credits" if x["reviewer"] == "Tavily" else f"{x['cost_usd']:.4f}"
            parts.append("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in
                         (x["reviewer"], x["model"], x.get("review_class", "legacy"), x["calls"], x["input"], x["cached"], x["output"], x["reasoning"], cost)) + "</tr>")
        parts.append("</table>")
    recs = L.read_ledger(out_dir / "findings.jsonl")
    rcpts = [r for r in recs if r["kind"] == "receipt"]
    parts.append("<h1>Execution receipts (CI only, attested)</h1>")
    if rcpts:
        parts.append("<table><tr><th>component</th><th>commit</th><th>numeric checks</th><th>digest</th><th>run</th></tr>")
        for r in rcpts[-30:][::-1]:
            ev = r.get("evidence") or {}
            parts.append("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in (
                r["component"], str(r["source"].get("head_sha"))[:12], ev.get("numeric_checks"), r["artifact_digest"][:19] + "...")) +
                f"<td><a href='{html.escape(str(ev.get('run_url')))}'>run {html.escape(str(r['source'].get('run_id')))}</a></td></tr>")
        parts.append("</table>")
    else:
        parts.append("<p>No receipts yet.</p>")
    sc = out_dir / "scorecards.md"
    if sc.is_file():
        parts.append("<h1>Reviewer scorecards</h1><pre>" + html.escape(sc.read_text()) + "</pre>")
    (out_dir / "index.html").write_text("\n".join(parts) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--month"); ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    cfg = L.load_config()
    path = L.ROOT / cfg["ledger_path"]
    recs = L.read_ledger(path)
    months = sorted({month_of(r) for r in recs if r["kind"] == "cost"}) if a.all else \
        [a.month or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")]
    for m in months:
        r = write_month(recs, m, path.parent)
        print(render_md(r))
    write_index(path.parent)


if __name__ == "__main__":
    main()
