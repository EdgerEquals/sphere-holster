"""Execution receipts, anti-stub rule and the paid-review receipt gate (round 4). Mocked; no network, no models."""
import argparse
import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ledger_lib as L  # noqa: E402
import ledger as LC  # noqa: E402
import ledger_costs as LCO  # noqa: E402
import ledger_score as LS  # noqa: E402
import receipt as R  # noqa: E402
import receipt_gate as G  # noqa: E402
import stub_detector as SD  # noqa: E402

SPEC = R.load_spec()
REPO = "EdgerEquals/stratified-sphere-model"
PERMISSIVE = lambda b, ev, spec: (True, "attestation verified (test)")  # noqa: E731
NONE_REG = lambda b, ev, spec: (False, "attestation not verified: no attestations found")  # noqa: E731

REAL_SRC = textwrap.dedent('''
    import math


    def l0_modes(R_m, c, n=4000):
        """Real work."""
        out = []
        for k in range(1, 4):
            x = k * math.pi / R_m
            out.append(x * c)
        return out


    def propagate(state, dt):
        new = [s * math.exp(-dt) for s in state]
        total = sum(new)
        return new, total


    def c_hho(T_K):
        return 1.2 + 0.001 * T_K
''')


# ------------------------------------------------------------------ stub detector
STUBS = {
    "pass": "def f(x):\n    pass\n",
    "ellipsis": "def f(x):\n    ...\n",
    "docstring_only": 'def f(x):\n    """todo"""\n',
    "docstring_pass": 'def f(x):\n    """todo"""\n    pass\n',
    "notimpl": "def f(x):\n    raise NotImplementedError\n",
    "notimpl_call": "def f(x):\n    raise NotImplementedError('later')\n",
    "return_const": "def f(x):\n    return 42\n",
    "return_none": "def f(x):\n    return None\n",
    "return_neg": "def f(x):\n    return -1.5\n",
    "return_tuple": "def f(x):\n    return ((1, 2.08), (2, 3.34))\n",
    "return_dict": "def f(x):\n    return {'f_hz': 6750.0, 'ok': True}\n",
    "bare_return": "def f(x):\n    return\n",
    "identity": "def f(x):\n    return x\n",
    "mixed": "def f(x):\n    '''doc'''\n    ...\n    return 0\n",
}


@pytest.mark.parametrize("name", sorted(STUBS))
def test_stub_shapes_are_detected(name):
    r = SD.check_entry("m.py:f", source=STUBS[name])
    assert r["stub"], name


@pytest.mark.parametrize("src", [
    "def f(x):\n    return x * 2.0 + 1\n",
    "def f(x):\n    y = x ** 2\n    return y\n",
    "def f(x):\n    if x > 0:\n        return 1\n    return -1\n",
])
def test_real_functions_pass(src):
    assert not SD.check_entry("m.py:f", source=src)["stub"]


def test_method_lookup_and_missing_entrypoint():
    src = "class A:\n    def g(self):\n        return self.v * 2\n    def h(self):\n        pass\n"
    assert not SD.check_entry("m.py:A.g", source=src)["stub"]
    assert SD.check_entry("m.py:A.h", source=src)["stub"]
    assert SD.check_entry("m.py:nope", source=src)["reason"] == "entrypoint not found"


def test_module_entrypoints():
    assert SD.check_entry("m.py", source='"""doc"""\nimport os\n')["stub"]
    assert SD.check_entry("m.py", source="import os\npass\n")["stub"]
    assert not SD.check_entry("m.py", source="import os\nx = os.getcwd()\nprint(x)\n")["stub"]


def test_repo_entrypoints_are_not_stubs():
    for comp in SPEC["components"].values():
        for e in comp["entrypoints"]:
            assert not SD.check_entry(e)["stub"], e


# ------------------------------------------------------------------ exec trace
def test_exec_trace_records_lines_and_notimplemented(tmp_path):
    mod = tmp_path / "target.py"
    mod.write_text("def f(x):\n    y = x + 1\n    return y * 2\n\ndef g():\n    raise NotImplementedError\n")
    script = tmp_path / "run.py"
    script.write_text("import target\nprint(target.f(3))\ntry:\n    target.g()\nexcept NotImplementedError:\n    pass\n")
    out = tmp_path / "trace.json"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "exec_trace.py"), "--root", str(tmp_path), "--files",
                        "target.py", "--out", str(out), "--", str(script)], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "8"
    t = json.loads(out.read_text())
    assert {2, 3} <= set(t["files"]["target.py"]) and "NotImplementedError" in t["exceptions"]["target.py"]


def test_exec_trace_passes_exit_code(tmp_path):
    script = tmp_path / "fail.py"
    script.write_text("import sys\nsys.exit(4)\n")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "exec_trace.py"), "--files", "fail.py", "--root",
                        str(tmp_path), "--out", str(tmp_path / "t.json"), "--", str(script)])
    assert r.returncode == 4 and json.loads((tmp_path / "t.json").read_text())["exit_code"] == 4


# ------------------------------------------------------------------ evaluation + emit
COMP = SPEC["components"]["compute-core"]


def full_trace(src=REAL_SRC, path="solver_v0.py"):
    lines = set()
    for e in COMP["entrypoints"]:
        lines |= set(SD.check_entry(e, source=src)["lines"])
    return {"files": {path: sorted(lines)}, "exceptions": {path: []}, "exit_code": 0}


ROWS = [{"check": "f0", "expected": 2.0816, "got": 2.0816, "status": "PASS"},
        {"check": "label", "expected": "a", "got": "a", "status": "INFO"}]
CHECKS = R.parse_checks("pytest-rows", json.dumps(ROWS))


def test_evaluate_real_vs_stub():
    srcs = {"solver_v0.py": REAL_SRC}
    assert R.evaluate(COMP, srcs, full_trace(), CHECKS)["ok"]
    stub = "def l0_modes(R_m, c, n=4000):\n    return ((1, 2.08),)\n\ndef propagate(s, dt):\n    ...\n\ndef c_hho(T):\n    raise NotImplementedError\n"
    ev = R.evaluate(COMP, {"solver_v0.py": stub}, full_trace(stub), CHECKS)
    assert not ev["ok"] and sum("stub entrypoint" in x for x in ev["reasons"]) == 3


def test_evaluate_requires_execution_numeric_checks_and_no_notimpl():
    srcs = {"solver_v0.py": REAL_SRC}
    t = full_trace(); t["files"]["solver_v0.py"] = []
    assert any("not executed" in x for x in R.evaluate(COMP, srcs, t, CHECKS)["reasons"])
    assert any("numeric" in x for x in R.evaluate(COMP, srcs, full_trace(), CHECKS[1:])["reasons"])
    t = full_trace(); t["exceptions"]["solver_v0.py"] = ["NotImplementedError"]
    assert any("NotImplementedError" in x for x in R.evaluate(COMP, srcs, t, CHECKS)["reasons"])
    bad = [dict(CHECKS[0], status="FAIL")] + CHECKS
    assert any("failed" in x for x in R.evaluate(COMP, srcs, full_trace(), bad)["reasons"])


def test_parse_checks_summary_md_with_pipes_in_tolerance():
    md = "| check | expected | got | tolerance | status |\n|---|---|---|---|---|\n| T | 1.25 | 1.2500001 | |err| 1e-7 <= 1e-3 | **PASS** |\n"
    c = R.parse_checks("summary-md", md)
    assert c == [{"name": "T", "expected": "1.25", "got": "1.2500001", "status": "PASS"}]


def ci_env(wf=".github/workflows/engineering-tests.yml", ref="refs/heads/main"):
    return {"GITHUB_ACTIONS": "true", "GITHUB_RUN_ID": "77", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "b" * 40,
            "GITHUB_REPOSITORY": REPO, "GITHUB_REF": ref, "GITHUB_JOB": "locked-values", "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_WORKFLOW_REF": f"{REPO}/{wf}@{ref}"}


def emit_args(tmp_path, trace=None, rows=None):
    (tmp_path / "trace.json").write_text(json.dumps(trace or real_repo_trace()))
    (tmp_path / "rows.json").write_text(json.dumps(rows or ROWS))
    return argparse.Namespace(component="compute-core", checks=str(tmp_path / "rows.json"),
                              trace=str(tmp_path / "trace.json"), out=str(tmp_path / "out"))


def real_repo_trace():
    src = (ROOT / "solver_v0.py").read_text()
    return full_trace(src)


def test_emit_refuses_outside_ci_wrong_workflow_and_branch(tmp_path):
    a = emit_args(tmp_path)
    assert R.emit(a, env={}) == R.EXIT_REFUSED
    assert "GitHub Actions only" in json.loads((tmp_path / "out" / "refused.json").read_text())["refused"]
    assert R.emit(a, env=ci_env(wf=".github/workflows/claude-audit.yml")) == R.EXIT_REFUSED
    assert R.emit(a, env=ci_env(ref="refs/heads/feature")) == R.EXIT_REFUSED
    assert not (tmp_path / "out" / "evidence.json").exists()


def test_emit_in_ci_writes_canonical_evidence_and_digest(tmp_path):
    a = emit_args(tmp_path)
    assert R.emit(a, env=ci_env()) == 0
    b = (tmp_path / "out" / "evidence.json").read_bytes()
    rc = json.loads((tmp_path / "out" / "receipt.json").read_text())
    assert rc["artifact_digest"] == "sha256:" + hashlib.sha256(b).hexdigest()
    ev = json.loads(b)
    assert R.canonical(ev) == b and ev["run_url"].endswith("/actions/runs/77") and ev["result"] == "pass"
    assert ev["file_digests"]["solver_v0.py"] == "sha256:" + hashlib.sha256((ROOT / "solver_v0.py").read_bytes()).hexdigest()
    assert R.verify_receipt(ev, rc["artifact_digest"], attest=PERMISSIVE)["ok"]


def test_emit_refuses_untraced_run(tmp_path):
    a = emit_args(tmp_path, trace={"files": {"solver_v0.py": []}, "exceptions": {}, "exit_code": 0})
    assert R.emit(a, env=ci_env()) == R.EXIT_REFUSED


# ------------------------------------------------------------------ verify + attestation
def make_evidence(tmp_path):
    a = emit_args(tmp_path)
    assert R.emit(a, env=ci_env()) == 0
    b = (tmp_path / "out" / "evidence.json").read_bytes()
    return json.loads(b), b


def test_verify_rejects_fake_and_unsigned(tmp_path):
    ev, b = make_evidence(tmp_path)
    d = R.digest(b)
    edited = dict(ev, numeric_checks=99)
    assert "digest mismatch" in R.verify_receipt(edited, d, attest=PERMISSIVE)["reasons"][0]
    res = R.verify_receipt(ev, d, attest=NONE_REG)
    assert not res["ok"] and "attestation" in res["reasons"][0]
    assert not R.verify_receipt(dict(ev, workflow=".github/workflows/claude-audit.yml"), None, attest=PERMISSIVE)["ok"]
    assert not R.verify_receipt(dict(ev, result="fail"), None, attest=PERMISSIVE)["ok"]


def test_gh_attestation_command(tmp_path):
    ev, b = make_evidence(tmp_path)
    seen = {}

    def runner(cmd, **kw):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "[]", "")
    ok, _ = R.gh_attestation_verify(b, ev, SPEC, runner=runner)
    c = seen["cmd"]
    assert ok and c[:3] == ["gh", "attestation", "verify"]
    assert c[c.index("--signer-workflow") + 1] == f"{REPO}/.github/workflows/engineering-tests.yml"
    assert c[c.index("--source-ref") + 1] == "refs/heads/main" and c[c.index("--source-digest") + 1] == "b" * 40
    assert "--deny-self-hosted-runners" in c
    bad = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "no attestations found")  # noqa: E731
    assert not R.gh_attestation_verify(b, ev, SPEC, runner=bad)[0]


# ------------------------------------------------------------------ ledger: CI-only write path
RUN_META = {"workflow_path": ".github/workflows/engineering-tests.yml", "head_sha": "b" * 40, "run_id": "77"}


def test_accept_receipt_only_in_ci_with_matching_run(tmp_path):
    ev, b = make_evidence(tmp_path)
    with pytest.raises(L.ReceiptRefused, match="no local"):
        L.accept_receipt(b, "receipt-compute-core-77", RUN_META, PERMISSIVE, env={})
    with pytest.raises(L.ReceiptRefused):
        L.accept_receipt(b, "r", RUN_META, None, env={"GITHUB_ACTIONS": "true"})
    with pytest.raises(L.ReceiptRefused, match="does not match"):
        L.accept_receipt(b, "r", dict(RUN_META, run_id="78"), PERMISSIVE, env={"GITHUB_ACTIONS": "true"})
    with pytest.raises(L.ReceiptRefused, match="canonical"):
        L.accept_receipt(json.dumps(ev, indent=1).encode(), "r", RUN_META, PERMISSIVE, env={"GITHUB_ACTIONS": "true"})
    with pytest.raises(L.ReceiptRefused, match="attestation"):
        L.accept_receipt(b, "r", RUN_META, NONE_REG, env={"GITHUB_ACTIONS": "true"})
    rec = L.accept_receipt(b, "receipt-compute-core-77", RUN_META, PERMISSIVE, env={"GITHUB_ACTIONS": "true"})
    assert rec["kind"] == "receipt" and rec["schema"] == "ssm-ledger/v1.1" and rec["component"] == "compute-core"
    assert not L.validate(rec, L.load_schema())


def test_append_refuses_receipts_outside_ingest(tmp_path):
    ev, b = make_evidence(tmp_path)
    rec = L.accept_receipt(b, "r", RUN_META, PERMISSIVE, env={"GITHUB_ACTIONS": "true"})
    with pytest.raises(L.ReceiptRefused):
        L.append_records(tmp_path / "l.jsonl", [rec])
    assert L.append_records(tmp_path / "l.jsonl", [rec], allow_receipts=True)


def test_artifact_dir_refuses_receipt_locally(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    ev, b = make_evidence(tmp_path)
    refused = []
    assert L.parse_artifact_dir(tmp_path / "out", L.load_config(), "receipt-compute-core-77", "77", refused=refused) == []
    assert refused and "no local" in refused[0]


def test_review_class_json_applies_to_findings_and_costs(tmp_path):
    d = tmp_path / "art"; d.mkdir()
    v = {"reviewer": "Claude", "head_sha": "a" * 40, "generated_utc": "2026-10-19T03:41:16Z", "overall_verdict": "FAIL",
         "results": [{"scope": "s", "model": "claude-sonnet-5-5", "parsed": {"verdict": "FAIL", "findings": [
             {"severity": "major", "domain": "thermal", "file": "DESIGN_STATE.md", "claim": "c", "note": "n"}],
             "retired_reintroduced": []}, "usage": {"input_tokens": 10, "output_tokens": 5}}]}
    (d / "verdict.json").write_text(json.dumps(v))
    (d / "review_class.json").write_text(json.dumps({"review_class": "spec-review"}))
    recs = L.parse_artifact_dir(d, L.load_config(), "claude-verdict-x", "1")
    assert recs and all(r["review_class"] == "spec-review" for r in recs)
    assert all(not L.validate(r, L.load_schema()) for r in recs)


def test_legacy_backfill_idempotent_and_v1_lines_still_valid():
    recs = L.read_ledger(ROOT / "ledger" / "findings.jsonl")
    schema = L.load_schema()
    assert all(not L.validate(r, schema) for r in recs)
    cls = L.legacy_backfill(recs)
    assert cls and all(c["review_class"] == "legacy" and not L.validate(c, schema) for c in cls)
    assert L.legacy_backfill(recs + cls) == []
    assert set(L.review_classes(recs + cls).values()) == {"legacy"}


# ------------------------------------------------------------------ gate decision table
def receipt_record(tmp_path):
    ev, b = make_evidence(tmp_path)
    return L.accept_receipt(b, "receipt-compute-core-77", RUN_META, PERMISSIVE, env={"GITHUB_ACTIONS": "true"})


def reader_for(overrides=None):
    overrides = overrides or {}

    def read(p):
        if p in overrides:
            return overrides[p]
        f = ROOT / p
        return f.read_bytes() if f.is_file() else None
    return read


@pytest.mark.parametrize("mode,spec_review,paid_override,dry,exp_class,exp_paid,exp_route", [
    ("enforce", False, False, False, "spec-review", False, "cheap"),
    ("enforce", False, True, False, "spec-review", True, "none"),
    ("enforce", True, False, False, "spec-review", False, "cheap"),
    ("warn", False, False, False, "spec-review", True, "none"),
    ("off", False, False, False, "spec-review", True, "none"),
    ("enforce", False, False, True, "spec-review", False, "none"),
])
def test_gate_no_receipt_table(mode, spec_review, paid_override, dry, exp_class, exp_paid, exp_route):
    d = G.decide(["solver_v0.py"], [], reader_for(), mode=mode, spec_review=spec_review, spec_review_paid=paid_override,
                 dry_run=dry, verifier=PERMISSIVE)
    assert (d["review_class"], d["paid"], d["route"]) == (exp_class, exp_paid, exp_route)
    if dry:
        assert d["would_route"] == ["deepseek"] and d["cheap_reviewers"] == []


def test_gate_docs_only_is_spec_review():
    d = G.decide(["DESIGN_STATE.md"], [], reader_for(), mode="enforce", verifier=PERMISSIVE)
    assert d["review_class"] == "spec-review" and d["components"] == [] and d["route"] == "cheap"


def test_gate_valid_receipt_is_code_review(tmp_path):
    rec = receipt_record(tmp_path)
    d = G.decide(["solver_v0.py", "DESIGN_STATE.md"], [rec], reader_for(), mode="enforce", verifier=PERMISSIVE)
    assert d["review_class"] == "code-review" and d["paid"] and d["route"] == "none"
    assert d["receipts"]["compute-core"]["receipt_id"] == rec["id"]
    # explicit spec-review still wins
    assert G.decide(["solver_v0.py"], [rec], reader_for(), mode="enforce", spec_review=True,
                    verifier=PERMISSIVE)["review_class"] == "spec-review"


def test_gate_rejects_stale_unsigned_and_stub_receipts(tmp_path):
    rec = receipt_record(tmp_path)
    changed = reader_for({"solver_v0.py": (ROOT / "solver_v0.py").read_bytes() + b"\n# edit\n"})
    d = G.decide(["solver_v0.py"], [rec], changed, mode="enforce", verifier=PERMISSIVE)
    assert d["review_class"] == "spec-review" and "changed since receipt" in d["notes"][0]
    d = G.decide(["solver_v0.py"], [rec], reader_for(), mode="enforce", verifier=NONE_REG)
    assert d["review_class"] == "spec-review" and "attestation" in d["notes"][0]
    stub = b"def l0_modes(R_m, c, n=4000):\n    return ((1, 2.08),)\n"
    rec2 = json.loads(json.dumps(rec))
    rec2["evidence"]["file_digests"]["solver_v0.py"] = "sha256:" + hashlib.sha256(stub).hexdigest()
    rec2["artifact_digest"] = R.digest(R.canonical(rec2["evidence"]))
    d = G.decide(["solver_v0.py"], [rec2], reader_for({"solver_v0.py": stub}), mode="enforce", verifier=PERMISSIVE)
    assert d["review_class"] == "spec-review" and "stub" in d["notes"][0]


def test_dial_mode_parsing(monkeypatch):
    import harness_common as H
    for raw, want in ((False, "off"), (True, "enforce"), ("warn", "warn"), ("bogus", "enforce")):
        monkeypatch.setattr(H, "load_dial", lambda raw=raw: {"receipt_gate": raw, "spec_review_route": ["deepseek"]})
        assert G.dial_mode_and_route()[0] == want
    monkeypatch.undo()
    assert G.dial_mode_and_route() == ("enforce", ["deepseek"])


# ------------------------------------------------------------------ scorer + costs + rubric
def finding(i, reviewer="Claude", cls=None):
    r = L.make_finding(L.load_config(), reviewer=reviewer, model="m", severity="major", domain="thermal", file="x",
                       claim=f"claim {i}", note="n", source={"type": "verdict_artifact", "ref": "r", "run_id": "1"})
    if cls:
        r["review_class"] = cls
    return r


def test_scorer_excludes_spec_review():
    recs = [finding(1, cls="code-review"), finding(2, cls="spec-review"), finding(3)]
    recs.append(L.make_status(recs[1]["id"], "accepted", {"type": "issue", "ref": "#1"}))
    sc = LS.scorecards(recs)
    c = sc["reviewers"]["Claude"]
    assert c["findings"] == 2 and c["spec_review_excluded"] == 1 and c["by_status"]["accepted"] == 0
    assert c["by_class"] == {"code-review": 1, "spec-review": 1, "legacy": 1}
    assert "excluded" in LS.render_md(sc)


def test_planted_receipt_rubric_rejects_fake_and_stub():
    rr = LS.receipt_rubric()
    kinds = {c["kind"] for c in rr["cases"]}
    assert kinds == {"fake receipt", "stub receipt"} and rr["all_rejected"]
    assert all(c["rejected"] for c in rr["cases"])


def test_mirror_skips_spec_review():
    cfg = L.load_config()
    recs = [finding(1, cls="spec-review"), finding(2, cls="code-review"), finding(3)]
    ids = {r["id"] for r in LC.plan_mirror(recs, cfg, "major")}
    assert recs[0]["id"] not in ids and {recs[1]["id"], recs[2]["id"]} <= ids


def test_costs_split_by_review_class():
    cfg = L.load_config()
    mk = lambda i, cls: dict(L.make_cost(cfg, reviewer="Kimi", model="kimi-k2.6", tokens={"input": 1000, "output": 100},  # noqa: E731
                                         source={"type": "verdict_artifact", "ref": f"r{i}", "run_id": str(i)},
                                         cost_usd=0.01, cost_basis="reported", event_utc="2026-10-19T00:00:00Z"),
                                **({"review_class": cls} if cls else {}))
    r = LCO.rollup([mk(1, "code-review"), mk(2, "spec-review"), mk(3, None)], "2026-10")
    assert r["per_class_usd"] == {"code-review": 0.01, "legacy": 0.01, "spec-review": 0.01}
    assert {x["review_class"] for x in r["rows"]} == {"code-review", "spec-review", "legacy"}
    assert "review class" in LCO.render_md(r)
