#!/usr/bin/env python3
"""Reviewer scoring (issue #8): planted-mistake precision/recall + status-based scorecards from the ledger.

  python scripts/ledger_score.py offline                     # default: score what is already in the ledger, no calls
  python scripts/ledger_score.py render --out <file>          # write the rendered planted fixture (for inspection)
  python scripts/ledger_score.py score-verdict --reviewer kimi --verdict <verdict.json> [--append]
  python scripts/ledger_score.py planted-live --reviewers kimi,deepseek --confirm spend   # PAID: dispatch only

Planted run: the fixture (ledger/planted/<v>/template.md, retired items as {{RETIRED:n}} placeholders) is rendered
into a throwaway local commit; the normal reviewer scripts (scripts/review_<name>.py, unchanged) review that commit;
their findings are matched against keys.json. Precision = matched findings / (matched + unmatched non-note findings);
recall = keys caught / keys planted. Outputs: ledger/scorecards.json and ledger/scorecards.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import ledger_lib as L  # noqa: E402

FIXTURE = L.ROOT / "ledger" / "planted" / "v1"
RETIRED_FILE = L.ROOT / "harness" / "retired.txt"


def retired_entries(path: Path = RETIRED_FILE) -> list[tuple[str, str]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            label, pat, _ = [p.strip() for p in line.split(" | ", 2)]
            out.append((label, pat))
    return out


def render_fixture(fixture: Path = FIXTURE, retired=None) -> str:
    retired = retired or retired_entries()
    return re.sub(r"\{\{RETIRED:(\d+)\}\}", lambda m: retired[int(m.group(1))][0].split("(")[0].strip(),
                  (fixture / "template.md").read_text(encoding="utf-8"))


def load_keys(fixture: Path = FIXTURE) -> dict:
    return json.loads((fixture / "keys.json").read_text(encoding="utf-8"))


def key_patterns(key: dict, retired) -> list[re.Pattern]:
    pats = list(key.get("match") or [])
    if key["category"] == "retired":
        pats.append(retired[key["retired_index"]][1])
    pats.append(rf"\b(line|item|point) {key['line']}\b")
    return [re.compile(p, re.I | re.M) for p in pats]


def score(findings: list[dict], keys: dict, retired=None, cfg=None) -> dict:
    retired = retired or retired_entries()
    cfg = cfg or L.load_config()
    pats = {k["id"]: key_patterns(k, retired) for k in keys["keys"]}
    cat = {k["id"]: k["category"] for k in keys["keys"]}
    hit, tp, fp, matched = set(), 0, 0, []
    for f in findings:
        text = " ".join(str(f.get(x) or "") for x in ("claim", "note", "file"))
        ks = [kid for kid, ps in pats.items() if any(p.search(text) for p in ps)]
        if ks:
            tp += 1; hit.update(ks); matched.append({"finding": f.get("id"), "keys": ks})
        elif L.severity_rank(f.get("severity", "note"), cfg) > 0:
            fp += 1
    n = len(keys["keys"])
    by_cat = {}
    for c in sorted(set(cat.values())):
        ids = [k for k, v in cat.items() if v == c]
        by_cat[c] = {"planted": len(ids), "caught": len([k for k in ids if k in hit])}
    return {"fixture": keys["fixture"], "keys_planted": n, "keys_caught": sorted(hit),
            "recall": round(len(hit) / n, 3) if n else None,
            "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
            "matched_findings": tp, "unmatched_findings": fp, "by_category": by_cat, "matches": matched}


RECEIPT_CASES = L.ROOT / "ledger" / "planted" / "v1" / "receipts" / "cases.json"


def receipt_rubric(cases_path: Path = RECEIPT_CASES) -> dict:
    """#8 rubric, round 4: planted 'fake receipt' and 'stub receipt' cases must all be rejected, for the expected
    reason. 'permissive' cases use a verifier that accepts any signature, so the stub/digest checks must catch them
    on their own; 'none-registered' cases use a verifier that finds no attestation (as gh would for a hand-made file)."""
    import receipt as R
    verifiers = {"permissive": lambda b, ev, spec: (True, "attestation verified (planted: permissive)"),
                 "none-registered": lambda b, ev, spec: (False, "attestation not verified: no attestations found")}
    data = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    rows = []
    for c in data["cases"]:
        res = R.verify_receipt(c["evidence"], c.get("claimed_digest"), attest=verifiers[c["verifier"]],
                               sources=c.get("target_sources"))
        why = "; ".join(res["reasons"])
        ok = (not res["ok"]) and c["expect_reason"].lower() in why.lower()
        rows.append({"id": c["id"], "kind": c["kind"], "rejected": not res["ok"], "reason": why[:240], "pass": ok})
    return {"fixture": data["fixture"], "cases": rows, "all_rejected": all(r["pass"] for r in rows)}


def scorecards(records: list[dict], keys: dict | None = None, cfg=None) -> dict:
    cfg = cfg or L.load_config()
    keys = keys or load_keys()
    st = L.current_status(records)
    classes = L.review_classes(records)
    cards = {}
    for r in records:
        if r["kind"] != "finding" or r.get("reviewer") not in L.REVIEWERS.values():
            continue
        c = cards.setdefault(r["reviewer"], {"findings": 0, "by_status": {"open": 0, "accepted": 0, "rejected": 0, "fixed": 0},
                                             "by_severity": {s: 0 for s in cfg["severity_order"]}, "planted_runs": [],
                                             "spec_review_excluded": 0, "by_class": {k: 0 for k in L.REVIEW_CLASSES}})
        c.setdefault("spec_review_excluded", 0); c.setdefault("by_class", {k: 0 for k in L.REVIEW_CLASSES})
        if r["source"]["type"] == "planted":
            continue
        cls = classes.get(r["id"], "legacy")
        c["by_class"][cls] += 1
        if cls == "spec-review":            # round 4: spec reviews never count toward scorecards
            c["spec_review_excluded"] += 1
            continue
        c["findings"] += 1
        c["by_status"][st.get(r["id"], "open")] += 1
        c["by_severity"][r["severity"]] += 1
    for c in cards.values():
        good, bad = c["by_status"]["accepted"] + c["by_status"]["fixed"], c["by_status"]["rejected"]
        c["acceptance_rate"] = round(good / (good + bad), 3) if (good + bad) else None
    runs = {}
    for r in records:
        if r["kind"] == "finding" and r["source"]["type"] == "planted" and classes.get(r["id"]) != "spec-review":
            runs.setdefault((r["reviewer"], r["source"].get("run_id")), []).append(r)
    for (rev, run), fs in sorted(runs.items(), key=lambda kv: str(kv[0])):
        s = score(fs, keys, cfg=cfg)
        cards.setdefault(rev, {"findings": 0, "by_status": {}, "by_severity": {}, "planted_runs": [], "acceptance_rate": None})
        cards[rev]["planted_runs"].append({"run": run, "event_utc": fs[0].get("event_utc"), **{k: s[k] for k in
                                           ("fixture", "recall", "precision", "keys_caught", "by_category")}})
    return {"generated_utc": L.ledger_as_of(records), "fixture": keys["fixture"], "reviewers": cards,
            "receipt_rubric": receipt_rubric()}


def render_md(sc: dict) -> str:
    L_ = ["# Reviewer scorecards", "", f"Ledger as of {sc['generated_utc']}, from `ledger/findings.jsonl` (issue #8).", "",
          "Acceptance = (accepted + fixed) / (accepted + fixed + rejected), from closed ledger issues. Planted = the latest "
          f"planted-mistake run against `{sc['fixture']}` (recall = seeded mistakes caught / planted).", "",
          "| Reviewer | findings | open | accepted | fixed | rejected | acceptance | planted recall | planted precision | planted runs |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for rev in ("Claude", "Grok", "Kimi", "DeepSeek"):
        c = sc["reviewers"].get(rev)
        if not c:
            L_.append(f"| {rev} | 0 | | | | | n/a | not run | not run | 0 |"); continue
        b, last = c.get("by_status", {}), (c["planted_runs"][-1] if c["planted_runs"] else None)
        fmt = lambda v: "n/a" if v is None else f"{v:.0%}"
        L_.append(f"| {rev} | {c['findings']} | {b.get('open', 0)} | {b.get('accepted', 0)} | {b.get('fixed', 0)} | "
                  f"{b.get('rejected', 0)} | {fmt(c.get('acceptance_rate'))} | "
                  f"{fmt(last['recall']) if last else 'not run'} | {fmt(last['precision']) if last else 'not run'} | "
                  f"{len(c['planted_runs'])} |")
    L_ += ["", "Spec-review findings (no execution receipt) are excluded from every number above; legacy = before the "
           "receipt gate. Excluded per reviewer: " + ", ".join(f"{rev} {sc['reviewers'].get(rev, {}).get('spec_review_excluded', 0)}"
                                                         for rev in ("Claude", "Grok", "Kimi", "DeepSeek")) + "."]
    rr = sc.get("receipt_rubric")
    if rr:
        L_ += ["", f"## Planted receipt cases (`{rr['fixture']}`): {'all rejected' if rr['all_rejected'] else 'NOT ALL REJECTED'}", "",
               "| case | kind | rejected | reason |", "|---|---|---|---|"]
        for c in rr["cases"]:
            L_.append(f"| {c['id']} | {c['kind']} | {'yes' if c['rejected'] else 'NO'} | {c['reason'][:120]} |")
    return "\n".join(L_) + "\n"


def write_scorecards(records, out_dir: Path) -> dict:
    sc = scorecards(records)
    (out_dir / "scorecards.json").write_text(json.dumps(sc, indent=2) + "\n", encoding="utf-8")
    (out_dir / "scorecards.md").write_text(render_md(sc), encoding="utf-8")
    return sc


def planted_findings_from_verdict(v: dict, run_id: str, cfg) -> list[dict]:
    return [r for r in L.parse_verdict_json(v, cfg, "planted-v1", run_id, source_type="planted", salt=run_id)
            if r["kind"] in ("finding", "cost")]


def planted_live(reviewers: list[str], depth: str, run_id: str, cfg) -> list[dict]:
    """PAID. Render fixture into a throwaway commit in a temp clone and run the normal reviewer scripts on it."""
    recs = []
    with tempfile.TemporaryDirectory() as td:
        wt = Path(td) / "wt"
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(L.ROOT), str(wt)], check=True)
        dest = wt / load_keys()["rendered_path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_fixture(), encoding="utf-8")
        g = lambda *a: subprocess.run(["git", "-C", str(wt), *a], check=True, capture_output=True, text=True).stdout
        g("add", "-A"); g("-c", "user.name=ledger", "-c", "user.email=ledger@localhost", "commit", "-qm", "planted fixture (local only)")
        for rv in reviewers:
            out = Path(td) / f"out-{rv}"
            subprocess.run([sys.executable, str(wt / "scripts" / f"review_{rv}.py"), "--depth", depth, "--base", "HEAD~1",
                            "--head", "HEAD", "--domains", "all", "--out", str(out),
                            "--intent", "Lock-shell summary for the thermal harness."], cwd=wt, check=False)
            vf = out / "verdict.json"
            if vf.is_file():
                recs += planted_findings_from_verdict(json.loads(vf.read_text()), f"{run_id}-{rv}", cfg)
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd")
    sp.add_parser("offline")
    p = sp.add_parser("render"); p.add_argument("--out", required=True)
    p = sp.add_parser("score-verdict"); p.add_argument("--verdict", required=True); p.add_argument("--run-id", default="manual")
    p.add_argument("--append", action="store_true")
    p = sp.add_parser("planted-live"); p.add_argument("--reviewers", default="kimi,deepseek")
    p.add_argument("--depth", default="shallow"); p.add_argument("--confirm", default=""); p.add_argument("--run-id", default="local")
    p.add_argument("--records-out", default=None, help="also write the new records here (so a push retry never re-calls models)")
    a = ap.parse_args(argv)
    cfg = L.load_config()
    path = L.ROOT / cfg["ledger_path"]
    cmd = a.cmd or "offline"
    if cmd == "render":
        Path(a.out).write_text(render_fixture(), encoding="utf-8"); print(a.out); return
    if cmd == "score-verdict":
        recs = planted_findings_from_verdict(json.loads(Path(a.verdict).read_text()), a.run_id, cfg)
        print(json.dumps(score([r for r in recs if r["kind"] == "finding"], load_keys(), cfg=cfg), indent=2))
        if a.append:
            L.append_records(path, recs)
    elif cmd == "planted-live":
        if a.confirm != "spend":
            sys.exit("planted-live makes PAID model calls. Re-run with --confirm spend (dispatch only).")
        revs = [r.strip().lower() for r in a.reviewers.split(",") if r.strip()]
        bad = [r for r in revs if r not in L.REVIEWERS]
        if bad:
            sys.exit(f"unknown reviewer(s): {bad}")
        recs = planted_live(revs, a.depth, a.run_id, cfg)
        L.append_records(path, recs)
        if a.records_out:
            Path(a.records_out).write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
        print(json.dumps({k: score([r for r in recs if r["kind"] == "finding" and r["source"]["run_id"].endswith(k)],
                                   load_keys(), cfg=cfg)["recall"] for k in revs}))
    sc = write_scorecards(L.read_ledger(path), path.parent)
    print(render_md(sc))


if __name__ == "__main__":
    main()
