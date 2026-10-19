"""Scoring rubric (#8) and monthly cost rollup (#9). Offline, no network, no model calls."""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ledger_lib as L  # noqa: E402
import ledger_score as S  # noqa: E402
import ledger_costs as C  # noqa: E402

CFG = L.load_config()
KEYS = S.load_keys()


def planted_verdict(findings, reviewer="kimi"):
    return {"reviewer": reviewer, "head_sha": "b" * 40, "generated_utc": "2026-10-19T06:00:00Z", "overall_verdict": "FAIL",
            "results": [{"scope": "rote", "model": "kimi-k2.6", "parsed": {"verdict": "FAIL", "findings": findings},
                         "usage": {"input_tokens": 1000, "cached_input_tokens": 0, "output_tokens": 500, "cost_usd": 0.003}}]}


def f(claim, sev="major", note=""):
    return {"severity": sev, "domain": "thermal", "file": "planted/v1/lock_shell_summary.md", "claim": claim, "note": note}


def test_fixture_has_eight_keys_in_four_categories_and_no_literal_retired_text():
    cats = [k["category"] for k in KEYS["keys"]]
    assert len(cats) == 8 and {c: cats.count(c) for c in set(cats)} == {"units": 2, "arithmetic": 2, "retired": 2, "consistency": 2}
    tmpl = (S.FIXTURE / "template.md").read_text()
    for label, pat in S.retired_entries():
        assert not re.search(pat, tmpl, re.I), label           # retired text only appears after rendering
    rendered = S.render_fixture()
    assert "{{" not in rendered
    for k in KEYS["keys"]:
        if k["category"] == "retired":
            assert re.search(S.retired_entries()[k["retired_index"]][1], rendered, re.I)


def test_fixture_arithmetic_keys_are_really_wrong_and_controls_right():
    import math
    assert 5900 / (2 * 0.944e-3) / 1e6 == pytest.approx(3.125)          # fixture says 6.25 (A2)
    assert 1 / 1e-6 == 1e6                                              # fixture says 1,000 W/m^2 (A1)
    assert (0.944e-3) ** 2 / 8.4e-7 == pytest.approx(1.06, abs=0.01)    # control line 8
    assert 4 * math.pi * 2.7 ** 2 == pytest.approx(91.6, abs=0.05)      # control line 9
    ds = (ROOT / "DESIGN_STATE.md").read_text()
    assert "5.4 mm OD" in ds and "3.236 MHz" in ds                      # consistency keys C1/C2 point at real locks


def test_perfect_reviewer_scores_full_recall_and_precision():
    fs = [f("cL written as 5900 km/s; should be m/s"), f("Wall 0.944 m should be 0.944 mm"),
          f("Heat flux should be 1,000,000 W/m^2"), f("cL/2t gives 3.125 MHz not 6.25"),
          f("Line 6 reintroduces the retired cooling item: oil bath"), f("Line 7 uses retired 0.2 T field"),
          f("Outer diameter 6.4 mm contradicts locked 5.4 mm"), f("Thickness mode should be 3.236 MHz")]
    recs = S.planted_findings_from_verdict(planted_verdict(fs), "run1", CFG)
    s = S.score([r for r in recs if r["kind"] == "finding"], KEYS, cfg=CFG)
    assert s["recall"] == 1.0 and s["precision"] == 1.0


def test_partial_reviewer_with_false_positive():
    fs = [f("Speed in km/s is wrong unit"), f("3.236 MHz is the locked value, not 3.5"),
          f("Surface area 91.6 mm^2 is wrong"), f("Style nit", sev="note")]
    recs = [r for r in S.planted_findings_from_verdict(planted_verdict(fs), "run2", CFG) if r["kind"] == "finding"]
    s = S.score(recs, KEYS, cfg=CFG)
    assert s["keys_caught"] == ["C2", "U1"] and s["recall"] == 0.25
    assert s["precision"] == pytest.approx(2 / 3, abs=1e-3)         # the note is not counted as a false positive


def test_scorecards_status_and_planted_runs(tmp_path):
    base = planted_verdict([f("Speed in km/s is wrong unit")])
    real = dict(base, reviewer="deepseek")
    real["results"] = [dict(base["results"][0], parsed={"verdict": "FAIL", "findings": [f("real issue A"), f("real issue B")]})]
    recs = L.parse_verdict_json(real, CFG, "deepseek-verdict-x")
    recs += S.planted_findings_from_verdict(base, "run3", CFG)
    fa = [r for r in recs if r["kind"] == "finding" and r["reviewer"] == "DeepSeek"][0]
    recs.append(L.make_status(fa["id"], "fixed", {"type": "issue", "ref": "#1"}, 1))
    sc = S.scorecards(recs, KEYS, CFG)
    assert sc["reviewers"]["DeepSeek"]["acceptance_rate"] == 1.0
    assert sc["reviewers"]["DeepSeek"]["by_status"]["fixed"] == 1
    assert sc["reviewers"]["Kimi"]["planted_runs"][0]["recall"] == 0.125
    md = S.render_md(sc)
    assert "| Kimi |" in md and "| Claude | 0 |" in md


def test_planted_live_refuses_without_confirm():
    with pytest.raises(SystemExit):
        S.main(["planted-live", "--reviewers", "kimi"])


def test_cost_rollup_groups_by_month_and_model():
    src = lambda i: {"type": "manual", "ref": f"r{i}", "run_id": None, "head_sha": None, "scope": None}
    recs = [L.make_cost(CFG, reviewer="Kimi", model="kimi-k2.6", tokens={"input": 100, "output": 10}, source=src(1),
                        cost_usd=0.01, event_utc="2026-10-02T00:00:00Z"),
            L.make_cost(CFG, reviewer="Kimi", model="kimi-k2.6", tokens={"input": 50, "output": 5}, source=src(2),
                        cost_usd=0.02, event_utc="2026-10-20T00:00:00Z"),
            L.make_cost(CFG, reviewer="Claude", model="claude-opus-5-5", tokens={"input": 5}, source=src(3),
                        event_utc="2026-10-21T00:00:00Z"),
            L.make_cost(CFG, reviewer="Grok", model="grok-4.7", tokens={"input": 1}, source=src(4), cost_usd=1.0,
                        event_utc="2026-11-01T00:00:00Z")]
    r = C.rollup(recs, "2026-10")
    kimi = [x for x in r["rows"] if x["reviewer"] == "Kimi"][0]
    assert kimi["calls"] == 2 and kimi["input"] == 150 and kimi["cost_usd"] == pytest.approx(0.03)
    assert r["calls_without_cost"] == 1 and r["total_usd"] == pytest.approx(0.03)   # unpriced opus not invented
    assert "Grok" not in r["per_reviewer_usd"]
    assert "**$0.0300**" in C.render_md(r)


def test_committed_october_rollup_matches_ledger():
    recs = L.read_ledger(ROOT / CFG["ledger_path"])
    committed = json.loads((ROOT / "ledger" / "costs_2026-10.json").read_text())
    assert C.rollup(recs, "2026-10")["total_usd"] == pytest.approx(committed["total_usd"])
    assert committed["total_usd"] > 0
