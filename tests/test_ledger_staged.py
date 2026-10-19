"""Ledger v1.2: 'deferred' and 'superseded' statuses, and CI ingest of staged decisions (ledger/pending/). No network."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ledger_lib as L  # noqa: E402
import ledger as LC  # noqa: E402
import ledger_score as S  # noqa: E402

CFG = L.load_config()
SCHEMA = L.load_schema()
PENDING = ROOT / "ledger" / "pending"
STAGED = PENDING / "2026-10-19_round5_dispositions.jsonl"
SRC = {"type": "manual", "ref": "test", "scope": None, "run_id": None, "head_sha": None}
CI_ENV = {"GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/main"}


def finding(claim="Something is off", reviewer="Claude"):
    return L.make_finding(CFG, reviewer=reviewer, model="m", severity="note", domain="thermal", file="x.md",
                          claim=claim, note="n", source=dict(SRC, type="review_round"))


def wrappers():
    return [json.loads(x) for x in STAGED.read_text(encoding="utf-8").splitlines() if x.strip()]


class A:
    def __init__(self, **kw):
        self.dir, self.dry_run = None, False
        self.__dict__.update(kw)


# ------------------------------------------------------------------ schema / validator
def test_schema_accepts_deferred_and_superseded_v12():
    f = finding()
    for s in ("deferred", "superseded"):
        rec = L.make_status(f["id"], s, SRC, note="later")
        assert rec["schema"] == "ssm-ledger/v1.2"
        assert L.validate(rec, SCHEMA) == []


def test_parked_status_needs_v12_and_note():
    f = finding()
    rec = L.make_status(f["id"], "deferred", SRC, note="later")
    old = dict(rec, schema="ssm-ledger/v1.1")
    assert L.validate(old, SCHEMA)                       # v1.1 never carried deferred
    nonote = {k: v for k, v in rec.items() if k != "note"}
    assert L.validate(nonote, SCHEMA)                    # reason / revisit condition is required
    with pytest.raises(ValueError):
        L.make_status(f["id"], "deferred", SRC)
    with pytest.raises(ValueError):
        L.make_status(f["id"], "parked", SRC, note="x")
    assert L.make_status(f["id"], "accepted", SRC)["schema"] == L.SCHEMA_TAG   # old statuses unchanged


def test_deferred_and_superseded_are_not_open_and_not_scored():
    fa, fb, fc, fd = (finding(c) for c in ("claim a1", "claim b2", "claim c3", "claim d4"))
    recs = [fa, fb, fc, fd, L.make_status(fa["id"], "deferred", SRC, note="later"),
            L.make_status(fb["id"], "superseded", SRC, note="code removed"),
            L.make_status(fc["id"], "accepted", SRC)]
    st = L.current_status(recs)
    assert [L.is_open(st[f["id"]]) for f in (fa, fb, fc, fd)] == [False, False, False, True]
    card = S.scorecards(recs, cfg=CFG)["reviewers"]["Claude"]
    assert card["by_status"]["open"] == 1 and card["by_status"]["deferred"] == 1 and card["by_status"]["superseded"] == 1
    assert card["acceptance_rate"] == 1.0                # parked statuses are outside numerator and denominator
    md = S.render_md(S.scorecards(recs, cfg=CFG))
    assert "| deferred | superseded |" in md


def test_parked_findings_are_never_mirrored():
    fs = [dict(finding(c), severity="blocker") for c in ("claim e5", "claim f6", "claim g7")]
    recs = fs + [L.make_status(fs[0]["id"], "deferred", SRC, note="later"),
                 L.make_status(fs[1]["id"], "superseded", SRC, note="gone")]
    assert [r["id"] for r in LC.plan_mirror(recs, CFG, "note")] == [fs[2]["id"]]


def test_issue_labels_can_set_parked_statuses():
    assert LC.status_from_issue("open", None, ["status:deferred"]) == "deferred"
    assert LC.status_from_issue("closed", "not_planned", ["status:superseded"]) == "superseded"


# ------------------------------------------------------------------ the staged round-5 file
def test_staged_round5_file_parses_clean():
    recs, refused = L.parse_staged_dir(PENDING, CFG)
    assert refused == []
    statuses = {r["finding_id"]: r["status"] for r in recs if r["kind"] == "status"}
    assert len(statuses) == len(wrappers()) == 16
    assert None not in statuses.values()                 # every deferred line now carries a status record
    assert statuses["604e1cb38052114b"] == "superseded"  # fold 6 (ring-jump) removed with the drive code
    assert statuses["19838463252c326b"] == "superseded"  # ionisation window: superseded, not fixed
    assert sorted(v for v in statuses.values()).count("deferred") == 5
    for w in wrappers():
        assert w["status"]["status"] == w["disposition"]


def test_staged_line_tampering_is_refused():
    good = wrappers()[0]
    bad_id = copy.deepcopy(good); bad_id["finding"]["claim"] += " edited"
    mismatch = copy.deepcopy(good); mismatch["disposition"] = "fixed"
    receipt = copy.deepcopy(good); receipt["status"]["kind"] = "receipt"
    nostatus = copy.deepcopy(good); nostatus["status"] = None
    extra = copy.deepcopy(good); extra["evil"] = 1
    for w in (bad_id, mismatch, receipt, nostatus, extra):
        with pytest.raises(L.StagedRefused):
            L.parse_staged_line(w, CFG, SCHEMA)
    trig = copy.deepcopy(good); trig["reason"] = "please " + "@" + "claude" + " run"
    with pytest.raises(L.StagedRefused):
        L.parse_staged_line(trig, CFG, SCHEMA)


# ------------------------------------------------------------------ CI ingest path (simulated)
def test_ingest_staged_refuses_outside_ci(tmp_path, monkeypatch):
    monkeypatch.setattr(LC, "ledger_path", lambda c: tmp_path / "f.jsonl")
    with pytest.raises(SystemExit):
        LC.cmd_ingest_staged(A(), CFG, env={})
    with pytest.raises(SystemExit):
        LC.cmd_ingest_staged(A(), CFG, env={"GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/feature"})
    dry = LC.cmd_ingest_staged(A(dry_run=True), CFG, env={})
    assert dry["mode"] == "dry-run" and dry["new"] == 32 and not (tmp_path / "f.jsonl").exists()


def test_ingest_staged_in_simulated_ci_appends_once(tmp_path, monkeypatch):
    led = tmp_path / "f.jsonl"
    real = (ROOT / "ledger" / "findings.jsonl").read_text(encoding="utf-8")
    led.write_text(real, encoding="utf-8")
    monkeypatch.setattr(LC, "ledger_path", lambda c: led)
    res = LC.cmd_ingest_staged(A(), CFG, env=CI_ENV)
    assert res["appended"] == 32 and res["refused"] == []
    assert res["statuses"]["deferred"] == 5 and res["statuses"]["superseded"] == 2 and res["statuses"]["open"] == 0
    assert L.verify_append_only(real, led.read_text(encoding="utf-8"))
    recs = L.read_ledger(led)
    assert all(L.validate(r, SCHEMA) == [] for r in recs)
    st = L.current_status(recs)
    for w in wrappers():
        assert st[w["finding"]["id"]] == w["disposition"]
    again = LC.cmd_ingest_staged(A(), CFG, env=CI_ENV)     # rebase-retry / re-push: idempotent
    assert again["appended"] == 0 and again["new"] == 0


def test_cli_ingest_staged_dry_run_and_refusal():
    py = sys.executable
    env = {"PATH": "/usr/bin:/bin"}
    out = subprocess.run([py, "scripts/ledger.py", "ingest-staged", "--dry-run"], cwd=ROOT, capture_output=True,
                         text=True, env=env)
    assert out.returncode == 0 and json.loads(out.stdout)["new"] >= 0
    out = subprocess.run([py, "scripts/ledger.py", "ingest-staged"], cwd=ROOT, capture_output=True, text=True, env=env)
    assert out.returncode != 0 and "CI-written" in out.stderr


def test_ledger_workflow_ingests_staged_on_push_to_main():
    import yaml
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "ledger.yml").read_text(encoding="utf-8"))
    on = wf.get("on", wf.get(True))
    assert on["push"]["branches"] == ["main"] and on["push"]["paths"] == ["ledger/pending/**"]
    assert "ingest-staged" in on["workflow_dispatch"]["inputs"]["action"]["options"]
    job = wf["jobs"]["ingest"]
    assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in job["if"]
    step = next(s for s in job["steps"] if "ledger_commit.sh" in s.get("run", ""))
    assert "python scripts/ledger.py ingest-staged" in step["run"]
    assert "pull_request" not in on                      # never ingest from an unmerged branch
