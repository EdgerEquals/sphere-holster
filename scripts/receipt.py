#!/usr/bin/env python3
"""Execution receipts (round 4 decision): written by CI only, verified by the ledger and the review gate.

A receipt says: at commit <sha>, workflow <wf> on main ran component <c>; its real entrypoints were imported AND
called (line trace), none is a stub (AST), and its numeric checks passed. The evidence JSON is serialised
canonically, its sha256 is the artifact digest, and the CI job signs it with a GitHub artifact attestation
(actions/attest-build-provenance). Anyone can read a receipt; only a CI job on main can produce a valid one.

  # in CI only (refuses unless GITHUB_ACTIONS=true and the workflow is the component's producer):
  python scripts/receipt.py emit --component compute-core --checks tests/out/locked_values_report.json \
      --trace tests/out/trace.json --out receipt-out
  # anywhere (read-only):
  python scripts/receipt.py verify --evidence receipt-out/evidence.json [--no-attest]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import stub_detector as sd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "harness" / "receipts.json"
EXIT_REFUSED = 3


def load_spec(path: Path | None = None) -> dict:
    return json.loads((path or SPEC_PATH).read_text(encoding="utf-8"))


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def workflow_from_ref(ref: str) -> str:
    """'owner/repo/.github/workflows/x.yml@refs/heads/main' -> '.github/workflows/x.yml'."""
    m = re.search(r"(\.github/workflows/[^@]+)", ref or "")
    return m.group(1) if m else ""


# ------------------------------------------------------------------ checks
def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip().replace("**", ""))
    except ValueError:
        return None


def parse_checks(fmt: str, text: str) -> list[dict]:
    out = []
    if fmt == "pytest-rows":
        for r in json.loads(text):
            out.append({"name": str(r.get("check"))[:160], "expected": r.get("expected"), "got": r.get("got"),
                        "status": r.get("status")})
    elif fmt == "summary-md":
        for line in text.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # tolerance cells may contain '|err|', so take name/expected/got from the left and status from the right
            if len(cells) >= 5 and cells[-1].replace("*", "") in ("PASS", "FAIL"):
                out.append({"name": cells[0][:160], "expected": cells[1], "got": cells[2],
                            "status": cells[-1].replace("*", "")})
    else:
        raise ValueError(f"unknown checks format {fmt}")
    return out


def numeric_checks(checks) -> list[dict]:
    good = []
    for c in checks:
        e, g = _num(c.get("expected")), _num(c.get("got"))
        if c.get("status") == "PASS" and e is not None and g is not None and math.isfinite(g):
            good.append(c)
    return good


# ------------------------------------------------------------------ anti-stub evaluation
def evaluate(comp: dict, sources: dict[str, str], trace: dict, checks: list[dict], min_numeric: int = 1) -> dict:
    """Decide whether this run proves real execution. Returns {ok, reasons, stub_report, trace_report}."""
    reasons, stub_report, trace_report = [], [], []
    executed = {k: set(v) for k, v in (trace.get("files") or {}).items()}
    for entry in comp["entrypoints"]:
        path = entry.split(":")[0]
        r = sd.check_entry(entry, source=sources[path])
        stub_report.append({"entry": entry, "stub": r["stub"], "reason": r["reason"]})
        if r["stub"]:
            reasons.append(f"stub entrypoint {entry}: {r['reason']}")
        body = set(r["lines"])
        hit = len(body & executed.get(path, set()))
        need = min(3, len(body)) if ":" in entry else min(20, math.ceil(0.5 * len(body)))
        trace_report.append({"entry": entry, "body_lines": len(body), "executed": hit, "required": need})
        if hit < max(need, 1):
            reasons.append(f"entrypoint {entry} not executed enough ({hit}/{need} body lines)")
    for path, ex in (trace.get("exceptions") or {}).items():
        if "NotImplementedError" in ex:
            reasons.append(f"NotImplementedError raised in {path}")
    failed = [c["name"] for c in checks if c.get("status") == "FAIL"]
    if failed:
        reasons.append(f"{len(failed)} check(s) failed: {failed[:3]}")
    nums = numeric_checks(checks)
    if len(nums) < min_numeric:
        reasons.append(f"only {len(nums)} passing numeric check(s); need {min_numeric}")
    if trace.get("exit_code") not in (0, None):
        reasons.append(f"traced run exited {trace.get('exit_code')}")
    return {"ok": not reasons, "reasons": reasons, "stub_report": stub_report, "trace_report": trace_report,
            "numeric_checks": len(nums)}


def file_digests(files, reader) -> dict:
    out = {}
    for f in files:
        b = reader(f)
        out[f] = None if b is None else "sha256:" + hashlib.sha256(b).hexdigest()
    return out


# ------------------------------------------------------------------ emit (CI only)
def emit(a, env=os.environ, spec=None) -> int:
    spec = spec or load_spec()
    comp = spec["components"].get(a.component)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    def refuse(msg):
        (out / "refused.json").write_text(json.dumps({"component": a.component, "refused": msg}, indent=2))
        print(f"RECEIPT REFUSED: {msg}", file=sys.stderr)
        return EXIT_REFUSED

    if comp is None:
        return refuse(f"unknown component {a.component}")
    if env.get("GITHUB_ACTIONS") != "true" or not env.get("GITHUB_RUN_ID"):
        return refuse("receipts are written by GitHub Actions only (GITHUB_ACTIONS/GITHUB_RUN_ID missing)")
    wf = workflow_from_ref(env.get("GITHUB_WORKFLOW_REF", ""))
    if wf != comp["workflow"]:
        return refuse(f"workflow {wf or '?'} is not the producer for {a.component} ({comp['workflow']})")
    ref = env.get("GITHUB_REF", "")
    if ref != spec["source_ref"]:
        return refuse(f"receipts are only issued for {spec['source_ref']} (this run: {ref or '?'})")
    sources = {e.split(":")[0]: (ROOT / e.split(":")[0]).read_text(encoding="utf-8") for e in comp["entrypoints"]}
    trace = json.loads(Path(a.trace).read_text())
    checks = parse_checks(comp["checks_format"], Path(a.checks).read_text(encoding="utf-8"))
    ev = evaluate(comp, sources, trace, checks, spec.get("min_numeric_checks", 1))
    if not ev["ok"]:
        return refuse("; ".join(ev["reasons"]))
    server = env.get("GITHUB_SERVER_URL", "https://github.com"); repo = env.get("GITHUB_REPOSITORY", "")
    evidence = {
        "type": "ssm-receipt-evidence/v1", "component": a.component, "result": "pass",
        "head_sha": env.get("GITHUB_SHA"), "repository": repo, "workflow": wf, "workflow_ref": env.get("GITHUB_WORKFLOW_REF"),
        "job": env.get("GITHUB_JOB"), "run_id": env.get("GITHUB_RUN_ID"), "run_attempt": env.get("GITHUB_RUN_ATTEMPT"),
        "run_url": f"{server}/{repo}/actions/runs/{env.get('GITHUB_RUN_ID')}", "event": env.get("GITHUB_EVENT_NAME"),
        "entrypoints": comp["entrypoints"], "files": comp["files"],
        "file_digests": file_digests(comp["files"], lambda f: (ROOT / f).read_bytes() if (ROOT / f).is_file() else None),
        "stub_check": ev["stub_report"], "trace_check": ev["trace_report"],
        "checks": [{k: (str(v)[:60] if k in ("expected", "got") else v) for k, v in c.items()} for c in checks][:60],
        "numeric_checks": ev["numeric_checks"],
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    b = canonical(evidence)
    (out / "evidence.json").write_bytes(b)
    d = digest(b)
    (out / "receipt.json").write_text(json.dumps({"component": a.component, "artifact_digest": d,
                                                  "evidence_file": "evidence.json", "head_sha": evidence["head_sha"],
                                                  "run_id": evidence["run_id"]}, indent=2))
    print(f"receipt: {a.component} {d} (run {evidence['run_id']}, {ev['numeric_checks']} numeric checks)")
    return 0


# ------------------------------------------------------------------ verify (ledger + gate)
def gh_attestation_verify(evidence_bytes: bytes, evidence: dict, spec: dict, runner=subprocess.run) -> tuple[bool, str]:
    repo = evidence.get("repository") or os.environ.get("GITHUB_REPOSITORY", "")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "evidence.json"
        p.write_bytes(evidence_bytes)
        cmd = ["gh", "attestation", "verify", str(p), "--repo", repo,
               "--signer-workflow", f"{repo}/{evidence['workflow']}", "--source-ref", spec["source_ref"],
               "--deny-self-hosted-runners", "--format", "json"]
        if evidence.get("head_sha"):
            cmd += ["--source-digest", evidence["head_sha"]]
        try:
            r = runner(cmd, capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, f"attestation check unavailable: {type(e).__name__}"
        return r.returncode == 0, ("attestation verified" if r.returncode == 0 else
                                   "attestation not verified: " + (r.stderr or r.stdout or "")[-300:].strip())


def verify_receipt(evidence: dict, claimed_digest: str | None, spec: dict | None = None, attest=gh_attestation_verify,
                   sources: dict | None = None) -> dict:
    """Full check of a stored receipt. `attest` = None skips the signature check (tests/local inspection only;
    the gate and the ledger always pass a verifier)."""
    spec = spec or load_spec()
    reasons = []
    b = canonical(evidence)
    if claimed_digest and digest(b) != claimed_digest:
        reasons.append("digest mismatch: evidence was altered or hand-written")
    comp = spec["components"].get(evidence.get("component"))
    if comp is None:
        reasons.append(f"unknown component {evidence.get('component')}")
    else:
        if evidence.get("workflow") != comp["workflow"]:
            reasons.append(f"workflow {evidence.get('workflow')} is not the producer for {evidence.get('component')}")
        if sorted(evidence.get("entrypoints") or []) != sorted(comp["entrypoints"]):
            reasons.append("entrypoints differ from harness/receipts.json")
    if evidence.get("result") != "pass":
        reasons.append("result is not pass")
    if any(s.get("stub") for s in evidence.get("stub_check") or []) or not evidence.get("stub_check"):
        reasons.append("stub entrypoint (or no stub check recorded)")
    for t in evidence.get("trace_check") or []:
        if t.get("executed", 0) < max(t.get("required", 1), 1):
            reasons.append(f"entrypoint {t.get('entry')} not executed")
    if not evidence.get("trace_check"):
        reasons.append("no execution trace recorded")
    if len(numeric_checks(evidence.get("checks") or [])) < spec.get("min_numeric_checks", 1):
        reasons.append("no passing numeric check recorded")
    if sources and comp is not None:          # re-run the stub detector on the actual target source
        for entry in comp["entrypoints"]:
            src = sources.get(entry.split(":")[0])
            if src is not None and sd.check_entry(entry, source=src)["stub"]:
                reasons.append(f"target source of {entry} is a stub")
    att = "skipped (no verifier)"
    if attest is not None and not reasons:
        ok, att = attest(b, evidence, spec)
        if not ok:
            reasons.append(att)
    return {"ok": not reasons, "reasons": reasons, "attestation": att, "digest": digest(b)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("emit"); p.add_argument("--component", required=True); p.add_argument("--checks", required=True)
    p.add_argument("--trace", required=True); p.add_argument("--out", default="receipt-out")
    p = sp.add_parser("verify"); p.add_argument("--evidence", required=True); p.add_argument("--no-attest", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "emit":
        sys.exit(emit(a))
    ev = json.loads(Path(a.evidence).read_text())
    res = verify_receipt(ev, None, attest=None if a.no_attest else gh_attestation_verify)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
