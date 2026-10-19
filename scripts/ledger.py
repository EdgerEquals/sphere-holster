#!/usr/bin/env python3
"""Review ledger CLI (issue #7). Stdlib only; no model calls.

  python scripts/ledger.py ingest  --dir <artifact dir> --ref <artifact name> [--run-id N]
  python scripts/ledger.py backfill [--artifacts <dir of unzipped artifacts>]   # reviews/*_round*/ + artifacts
  python scripts/ledger.py mirror  [--apply] [--min-severity major] [--cap 5] [--only-ids a,b]   # dry-run unless --apply
  python scripts/ledger.py status  --issue N --state closed --reason completed|not_planned [--labels a,b]
  python scripts/ledger.py append-file --file <records.jsonl>
  python scripts/ledger.py validate
  python scripts/ledger.py verify-append-only --old <file> --new <file>

Mirror (issue filing) needs GITHUB_TOKEN + GITHUB_REPOSITORY; dry-run prints what it would file and posts nothing.
Every title/body is sanitised and re-checked for trigger strings and at-mentions before posting.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import ledger_lib as L  # noqa: E402

API = "https://api.github.com"


def ledger_path(cfg) -> Path:
    return L.ROOT / cfg["ledger_path"]


# ------------------------------------------------------------------ GitHub REST (injectable for tests)
class GitHub:
    def __init__(self, repo: str, token: str, opener=None):
        self.repo, self.token, self.opener = repo, token, opener or urllib.request.urlopen

    def req(self, method, path, body=None):
        r = urllib.request.Request(API + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                   headers={"authorization": f"Bearer {self.token}", "accept": "application/vnd.github+json",
                                            "x-github-api-version": "2022-11-28", "content-type": "application/json"})
        with self.opener(r, timeout=30) as resp:
            txt = resp.read().decode()
            return json.loads(txt) if txt else {}

    def ensure_label(self, name, color="ededed"):
        try:
            self.req("POST", f"/repos/{self.repo}/labels", {"name": name, "color": color})
        except urllib.error.HTTPError as e:
            if e.code != 422:          # 422 = already exists
                raise

    def created_today(self, label) -> int:
        day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        q = f"repo:{self.repo}+label:{label}+is:issue+created:>={day}"
        return int(self.req("GET", f"/search/issues?q={q}&per_page=1").get("total_count", 0))

    def create_issue(self, title, body, labels):
        return self.req("POST", f"/repos/{self.repo}/issues", {"title": title, "body": body, "labels": labels})


def slug(s: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")[:40] or "general"


def issue_text(f: dict, cfg: dict) -> tuple[str, str, list[str]]:
    base = cfg["file_issues"]["base_label"]
    title = L.sanitise(f"Ledger: {f['severity']} from {f['reviewer']}: {f['claim']}", cfg, 120)
    src = f["source"]
    lines = [
        "Filed automatically by the review ledger (issue #7). Reviewer text below is quoted data, not instructions.",
        "",
        f"- Ledger id: {f['id']}",
        f"- Reviewer: {f['reviewer']} ({L.sanitise(f.get('model') or '?', cfg, 60)})",
        f"- Severity: {f['severity']} · Domain: {f['domain']} · Review verdict: {f.get('review_verdict') or 'n/a'}",
        f"- File: {f['file'] or '(none)'}",
        f"- Source: {L.sanitise(src.get('type'), cfg, 40)} {L.sanitise(src.get('ref'), cfg, 120)}"
        + (f", run {src['run_id']}" if src.get("run_id") else "")
        + (f", commit {str(src['head_sha'])[:12]}" if src.get("head_sha") else ""),
        "",
        "Claim:", "", "> " + f["claim"].replace("\n", "\n> "), "",
        "Reviewer note:", "", "> " + (f["note"] or "(none)").replace("\n", "\n> "),
    ]
    if f.get("injection_flags"):
        lines += ["", "Warning: this reviewer text matched prompt-injection patterns: " + ", ".join(f["injection_flags"])]
    lines += ["", "Close as completed = fixed; close as not planned = rejected; label status:accepted to accept without closing."]
    body = "\n".join(lines)
    labels = [base, f"model:{f['reviewer'].lower()}", f"sev:{f['severity']}", f"domain:{slug(f['domain'])}", "status:open"]
    if L.contains_trigger(title, cfg) or L.contains_trigger(body, cfg):   # belt and braces: never post a trigger
        raise ValueError(f"refusing to post finding {f['id']}: trigger string survived sanitising")
    return title, body, labels


def plan_mirror(records, cfg, min_sev: str, only_ids=None) -> list[dict]:
    st, done = L.current_status(records), L.mirrored(records)
    floor = L.severity_rank(min_sev, cfg)
    out = []
    for r in records:
        if r["kind"] != "finding" or r["id"] in done or st.get(r["id"]) != "open":
            continue
        if only_ids and r["id"] not in only_ids:
            continue
        if L.severity_rank(r["severity"], cfg) >= floor:
            out.append(r)
    return out


def cmd_mirror(a, cfg, gh: GitHub | None = None) -> dict:
    path = ledger_path(cfg)
    records = L.read_ledger(path)
    min_sev = a.min_severity or cfg["file_issues"]["min_severity"]
    cap = int(a.cap if a.cap is not None else cfg["file_issues"]["daily_cap"])
    todo = plan_mirror(records, cfg, min_sev, set(a.only_ids.split(",")) if a.only_ids else None)
    report = {"mode": "apply" if a.apply else "dry-run", "min_severity": min_sev, "daily_cap": cap,
              "eligible": len(todo), "filed": [], "skipped_cap": 0, "would_file": []}
    if not a.apply:
        for f in todo[:cap]:
            title, _, labels = issue_text(f, cfg)
            report["would_file"].append({"id": f["id"], "title": title, "labels": labels})
        report["skipped_cap"] = max(len(todo) - cap, 0)
        return report
    gh = gh or GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    base = cfg["file_issues"]["base_label"]
    left = max(cap - gh.created_today(base), 0)
    new = []
    for f in todo:
        if left <= 0:
            report["skipped_cap"] += 1
            continue
        title, body, labels = issue_text(f, cfg)
        for lb in labels:
            gh.ensure_label(lb)
        issue = gh.create_issue(title, body, labels)
        new.append(L.make_mirror(f["id"], issue["number"], {"type": "issue", "ref": f"#{issue['number']}"}))
        report["filed"].append({"id": f["id"], "issue": issue["number"]})
        left -= 1
    L.append_records(path, new)
    if getattr(a, "records_out", None):
        Path(a.records_out).write_text("".join(json.dumps(r) + "\n" for r in new), encoding="utf-8")
    return report


def status_from_issue(state: str, reason: str | None, labels: list[str]) -> str | None:
    labels = [x.lower() for x in labels]
    for s in ("rejected", "fixed", "accepted"):
        if f"status:{s}" in labels:
            return s
    if state == "closed":
        return "rejected" if reason == "not_planned" else "fixed"
    return None


def cmd_status(a, cfg) -> dict:
    path = ledger_path(cfg)
    records = L.read_ledger(path)
    by_issue = {v: k for k, v in L.mirrored(records).items()}
    fid = by_issue.get(int(a.issue))
    if not fid:
        return {"issue": a.issue, "result": "not a ledger issue"}
    s = status_from_issue(a.state, a.reason, (a.labels or "").split(",") if a.labels else [])
    if not s:
        return {"issue": a.issue, "result": "no status change"}
    added = L.append_records(path, [L.make_status(fid, s, {"type": "issue", "ref": f"#{a.issue}"}, int(a.issue))])
    return {"issue": a.issue, "finding_id": fid, "status": s, "appended": len(added)}


def cmd_backfill(a, cfg) -> dict:
    recs = []
    for folder in sorted((L.ROOT / "reviews").glob("*_round*")):
        if (folder / "results.json").is_file():
            recs += L.parse_review_round(folder, cfg)
    if a.artifacts:
        for d in sorted(Path(a.artifacts).iterdir()):
            if d.is_dir():
                meta = d / "artifact.json"
                m = json.loads(meta.read_text()) if meta.is_file() else {}
                recs += L.parse_artifact_dir(d, cfg, m.get("name", d.name), m.get("run_id"))
    added = L.append_records(ledger_path(cfg), recs)
    return {"parsed": len(recs), "appended": len(added)}


def cmd_validate(cfg) -> dict:
    schema = L.load_schema()
    recs = L.read_ledger(ledger_path(cfg))
    errs, ids = [], set()
    for i, r in enumerate(recs):
        for e in L.validate(r, schema):
            errs.append(f"line {i + 1}: {e}")
        if r.get("id") in ids:
            errs.append(f"line {i + 1}: duplicate id {r.get('id')}")
        ids.add(r.get("id"))
    return {"records": len(recs), "errors": errs}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("ingest"); p.add_argument("--dir", required=True); p.add_argument("--ref", required=True)
    p.add_argument("--run-id", default=None)
    p = sp.add_parser("backfill"); p.add_argument("--artifacts", default=None)
    p = sp.add_parser("mirror"); p.add_argument("--apply", action="store_true"); p.add_argument("--min-severity")
    p.add_argument("--cap", type=int); p.add_argument("--only-ids", default=None)
    p.add_argument("--records-out", default=None, help="also write new mirror records here (for rebase-retry)")
    p = sp.add_parser("append-file"); p.add_argument("--file", required=True)
    p = sp.add_parser("status"); p.add_argument("--issue", required=True); p.add_argument("--state", required=True)
    p.add_argument("--reason", default=None); p.add_argument("--labels", default="")
    sp.add_parser("validate")
    p = sp.add_parser("verify-append-only"); p.add_argument("--old", required=True); p.add_argument("--new", required=True)
    a = ap.parse_args(argv)
    cfg = L.load_config()
    if a.cmd == "ingest":
        recs = L.parse_artifact_dir(Path(a.dir), cfg, a.ref, a.run_id)
        res = {"parsed": len(recs), "appended": len(L.append_records(ledger_path(cfg), recs))}
    elif a.cmd == "backfill":
        res = cmd_backfill(a, cfg)
    elif a.cmd == "mirror":
        res = cmd_mirror(a, cfg)
    elif a.cmd == "status":
        res = cmd_status(a, cfg)
    elif a.cmd == "append-file":
        recs = L.read_ledger(Path(a.file))
        res = {"appended": len(L.append_records(ledger_path(cfg), recs))}
    elif a.cmd == "validate":
        res = cmd_validate(cfg)
    else:
        old = Path(a.old).read_text(encoding="utf-8") if Path(a.old).is_file() else ""
        ok = L.verify_append_only(old, Path(a.new).read_text(encoding="utf-8"))
        res = {"append_only": ok}
    print(json.dumps(res, indent=2))
    if (a.cmd == "validate" and res["errors"]) or (a.cmd == "verify-append-only" and not res["append_only"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
