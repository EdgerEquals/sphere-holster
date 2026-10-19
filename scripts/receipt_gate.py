#!/usr/bin/env python3
"""Receipt gate for paid reviews (round 4 decision, locked 2026-10-19). No model calls, no network except the
`gh attestation verify` signature check.

Maps the reviewed diff to components (harness/receipts.json) and looks in the ledger for a CI execution receipt that
covers each touched component at the target's exact file contents. Then:
  every touched component has a valid receipt -> review_class=code-review (paid review runs; findings are scored)
  otherwise (or the spec_review input is set) -> review_class=spec-review (never scored or mirrored)
Routing by harness/dial.yml receipt_gate:
  enforce: spec-review skips the paid review and routes to spec_review_route (cheap) unless spec_review_paid=true
  warn:    paid review still runs, with a warning
  off:     paid review runs; the class is still recorded honestly
dry_run=true decides and reports only: paid=false, route=none, nothing dispatched.

  python scripts/receipt_gate.py decide --head <sha> [--base <sha>] [--spec-review false] [--spec-review-paid false]
      [--dry-run false] [--mode enforce|warn|off] [--out review-out/review_class.json] [--github-output]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import ledger_lib as L  # noqa: E402
import receipt as R  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODES = ("enforce", "warn", "off")


def truthy(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def dial_mode_and_route() -> tuple[str, list[str]]:
    import harness_common as H
    d = H.load_dial()
    m = d.get("receipt_gate", "enforce")
    if m is False:            # unquoted YAML `off` parses as false
        m = "off"
    if m is True:
        m = "enforce"
    m = str(m).strip().lower()
    route = d.get("spec_review_route") or ["deepseek"]
    return (m if m in MODES else "enforce"), [str(x) for x in (route if isinstance(route, list) else [route])]


def touched_components(changed: list[str], spec: dict) -> list[str]:
    out = []
    for name, c in spec["components"].items():
        if any(fnmatch.fnmatch(f, pat) for f in changed for pat in c["files"]):
            out.append(name)
    return out


def receipt_valid_for(rec: dict, read_at_target, verifier, spec: dict) -> tuple[bool, str]:
    ev = rec.get("evidence") or {}
    want = ev.get("file_digests") or {}
    if not want:
        return False, "receipt has no file digests"
    now = R.file_digests(list(want), read_at_target)
    stale = [f for f in want if now.get(f) != want[f]]
    if stale:
        return False, f"component changed since receipt commit {str(ev.get('head_sha'))[:12]}: {', '.join(stale[:3])}"
    sources = {}
    for e in ev.get("entrypoints") or []:
        b = read_at_target(e.split(":")[0])
        if b is not None:
            sources[e.split(":")[0]] = b.decode("utf-8", "replace")
    res = R.verify_receipt(ev, rec.get("artifact_digest"), spec, attest=verifier, sources=sources)
    return res["ok"], ("; ".join(res["reasons"]) or res["attestation"])


def decide(changed: list[str], records: list[dict], read_at_target, *, mode: str, spec_review: bool = False,
           spec_review_paid: bool = False, dry_run: bool = False, route: list[str] | None = None,
           verifier=R.gh_attestation_verify, spec: dict | None = None) -> dict:
    spec = spec or R.load_spec()
    route = route or ["deepseek"]
    comps = touched_components(changed, spec)
    receipts_used, missing, notes = {}, [], []
    for c in comps:
        cands = [r for r in records if r.get("kind") == "receipt" and r.get("component") == c][::-1]
        ok_rec = None
        for r in cands[:10]:
            ok, why = receipt_valid_for(r, read_at_target, verifier, spec)
            if ok:
                ok_rec = r; break
            notes.append(f"{c}: receipt {r['id']} rejected ({why[:160]})")
        if ok_rec:
            receipts_used[c] = {"receipt_id": ok_rec["id"], "head_sha": ok_rec["source"].get("head_sha"),
                                "run_url": (ok_rec.get("evidence") or {}).get("run_url")}
        else:
            missing.append(c)
    if spec_review:
        cls, reason = "spec-review", "explicit spec-review input (cross-cutting / design review)"
    elif not comps:
        cls, reason = "spec-review", "the diff touches no executable component with a receipt producer (docs/spec/config only)"
    elif missing:
        cls, reason = "spec-review", f"no valid execution receipt for: {', '.join(missing)}"
    else:
        cls, reason = "code-review", "valid CI execution receipt for every touched component: " + ", ".join(comps)
    if cls == "code-review" or mode in ("warn", "off"):
        paid = True
    else:
        paid = bool(spec_review_paid)
    cheap = cls == "spec-review" and not paid and mode == "enforce"
    out = {"review_class": cls, "reason": reason, "mode": mode, "components": comps, "missing": missing,
           "receipts": receipts_used, "notes": notes[:10], "changed_files": changed[:50], "dry_run": dry_run,
           "spec_review_input": spec_review, "spec_review_paid": spec_review_paid,
           "would_run_paid": paid, "would_route": route if cheap else []}
    out["paid"] = paid and not dry_run
    out["route"] = "cheap" if (cheap and not dry_run) else "none"
    out["cheap_reviewers"] = route if (cheap and not dry_run) else []
    if cls == "spec-review" and mode == "warn":
        out["warning"] = "receipt gate in warn mode: paid review runs on a spec-review target (not scored)"
    return out


def git_changed(head: str, base: str | None) -> list[str]:
    rng = [base, head] if base else [f"{head}~1", head]
    r = subprocess.run(["git", "diff", "--name-only", *rng], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:      # root commit or shallow: everything in the tree
        r = subprocess.run(["git", "ls-tree", "-r", "--name-only", head], capture_output=True, text=True, cwd=ROOT)
    return [x for x in r.stdout.splitlines() if x]


def git_reader(head: str):
    def read(path: str):
        r = subprocess.run(["git", "show", f"{head}:{path}"], capture_output=True, cwd=ROOT)
        return r.stdout if r.returncode == 0 else None
    return read


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("decide")
    p.add_argument("--head", required=True); p.add_argument("--base", default="")
    p.add_argument("--mode", default=""); p.add_argument("--spec-review", default="false")
    p.add_argument("--spec-review-paid", default="false"); p.add_argument("--dry-run", default="false")
    p.add_argument("--ledger", default=str(ROOT / "ledger" / "findings.jsonl"))
    p.add_argument("--out", default=""); p.add_argument("--github-output", action="store_true")
    p.add_argument("--no-attest", action="store_true", help="local inspection only; refused inside GitHub Actions")
    a = ap.parse_args(argv)
    dmode, route = dial_mode_and_route()
    mode = a.mode.strip().lower() if a.mode.strip().lower() in MODES else dmode
    if a.no_attest and os.environ.get("GITHUB_ACTIONS") == "true":
        sys.exit("--no-attest is not allowed in CI")
    res = decide(git_changed(a.head, a.base or None), L.read_ledger(Path(a.ledger)), git_reader(a.head), mode=mode,
                 spec_review=truthy(a.spec_review), spec_review_paid=truthy(a.spec_review_paid), dry_run=truthy(a.dry_run),
                 route=route, verifier=None if a.no_attest else R.gh_attestation_verify)
    res["head_sha"] = a.head; res["base_sha"] = a.base or None
    text = json.dumps(res, indent=2)
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n")
    if a.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            for k in ("review_class", "paid", "route", "mode"):
                v = res[k]
                fh.write(f"{k}={str(v).lower() if isinstance(v, bool) else v}\n")
            fh.write(f"cheap_reviewers={','.join(res['cheap_reviewers'])}\n")
            fh.write(f"reason={res['reason'][:300]}\n")


if __name__ == "__main__":
    main()
