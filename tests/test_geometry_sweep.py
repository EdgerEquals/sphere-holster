"""Geometry sweep v0 (geometry_sweep_v0.py, opt-in): lock scoring, linewidth rule, default runs unchanged, zero run exact.

A lock is two modes of different cavities whose own model linewidths (f/Q) overlap at half maximum,
|f_i - f_j| <= (f_i/Q_i + f_j/Q_j)/2, or a boundary-reflection round trip landing inside a real mode's half-width.
No tolerance is invented. Since the derived gas Q (solver_v0.gas_Q) the gas-cavity modes carry their own width f/Q;
a mode passed with Q=None (the pure unit tests below) still has width 0."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import solver_v0 as S  # noqa: E402
import geometry_sweep_v0 as G  # noqa: E402


@pytest.fixture
def vrh():
    """The default solver run uses --qz-sound vrh; switch for the test and restore the module state afterwards."""
    old = S.QZ_SOUND_SEL; tags = S.MAT["quartz"]["tags"]; cl, ct = S.MAT["quartz"]["cL"], S.MAT["quartz"]["cT"]
    S.set_qz_sound("vrh")
    yield
    S.QZ_SOUND_SEL = old; S.MAT["quartz"].update(tags=tags, cL=cl, cT=ct)


def test_synthetic_lock_inside_linewidth_is_counted():
    # Q mode at 1 MHz, Q 1000 -> FWHM 1 kHz, half-width 500 Hz; gas mode (no Q, width 0) 400 Hz away -> lock
    locks = G.find_locks([dict(cav="Q", f=1.0e6, Q=1000.0), dict(cav="B", f=1.0e6 + 400.0, Q=None)])
    assert len(locks) == 1 and locks[0]["kind"] == "mode"
    assert locks[0]["half_width_Hz"] == pytest.approx(500.0) and locks[0]["df_Hz"] == pytest.approx(400.0)


def test_no_lock_outside_linewidth():
    assert G.find_locks([dict(cav="Q", f=1.0e6, Q=1000.0), dict(cav="B", f=1.0e6 + 600.0, Q=None)]) == []
    # both widths count: (1 kHz + 1 kHz)/2 = 1 kHz
    two = [dict(cav="Q", f=1.0e6, Q=1000.0), dict(cav="T", f=1.0e6 + 999.0, Q=1000.0 * (1.0e6 + 999.0) / 1.0e6)]
    assert len(G.find_locks(two)) == 1
    two[1]["f"] = 1.0e6 + 1001.0
    assert G.find_locks(two) == []


def test_same_cavity_and_contained_pairs_never_lock():
    assert G.find_locks([dict(cav="Q", f=1.0e6, Q=10.0), dict(cav="Q", f=1.0e6 + 1.0, Q=10.0)]) == []
    # the bonded stack S contains the quartz and the tourbillon: Q-S and T-S are not scored
    assert G.find_locks([dict(cav="Q", f=1.0e6, Q=10.0), dict(cav="S", f=1.0e6, Q=10.0)]) == []
    assert G.find_locks([dict(cav="T", f=1.0e6, Q=10.0), dict(cav="S", f=1.0e6, Q=10.0)]) == []
    assert len(G.find_locks([dict(cav="B", f=1.0e6, Q=None), dict(cav="S", f=1.0e6, Q=10.0)])) == 1


def test_reflection_landing_uses_the_target_linewidth_and_counts_once_per_target():
    m = [dict(cav="S", f=2.0e6, Q=100.0)]   # half-width 10 kHz
    refl = [dict(cav="B", f=2.0e6 + 9.0e3, n=7), dict(cav="B", f=2.0e6 - 5.0e3, n=6), dict(cav="B", f=2.0e6 + 11.0e3, n=8)]
    locks = G.find_locks(m, refl)
    assert len(locks) == 1 and locks[0]["kind"] == "reflection" and locks[0]["a"][2] == 6   # nearest harmonic only
    assert G.find_locks(m, [dict(cav="B", f=2.0e6 + 11.0e3, n=8)]) == []
    assert G.find_locks([dict(cav="B", f=2.0e6, Q=None)], [dict(cav="B", f=2.0e6, n=1)]) == []   # own cavity: no


def test_density_guaranteed_flag():
    dense = [dict(cav="B", f=1.0e6 + k * 1.0e3, Q=None) for k in range(5)] + [dict(cav="S", f=1.002e6, Q=100.0)]
    lk = G.find_locks(dense)
    assert lk and all(x["density_guaranteed"] for x in lk)   # 10 kHz window vs 1 kHz spacing
    sparse = [dict(cav="B", f=1.0e6 + k * 1.0e5, Q=None) for k in range(5)] + [dict(cav="S", f=1.2e6 + 100.0, Q=100.0)]
    lk = G.find_locks(sparse)
    assert len(lk) == 1 and not lk[0]["density_guaranteed"]


def test_golden_column_is_secondary_and_reports_ratio():
    locks = [dict(kind="mode", a=("B", 1.0e6), b=("S", 1.0e6), density_guaranteed=False),
             dict(kind="mode", a=("B", G.PHI * 1.0e6), b=("S", G.PHI * 1.0e6), density_guaranteed=False)]
    g = G.golden_column(locks)
    assert g["nearest_phi"] == pytest.approx(G.PHI, abs=1e-4) and g["n_within_5pct_of_phi"] == 1


def test_base5_geometry_reproduces_the_solver_modes_and_stays_zero(vrh):
    r = G.evaluate(1.5, 1.0, 5.0, details=True)
    data = json.loads((ROOT / "model_data_v0.json").read_text(encoding="utf-8"))
    ac = next(c for c in data["cases"] if c["id"] == "base5")["state"]["acoustic"]
    assert len(r["modes_Hz"]["S"]) == len(ac["l0_bonded"])
    for f, g in zip(r["modes_Hz"]["S"], ac["l0_bonded"]):
        assert f == pytest.approx(g, rel=1e-3)
    assert r["OD_mm"] == pytest.approx(5.0) and r["cascade_ok"]
    assert r["score"] == r["n_mode_locks"] + r["n_reflection_locks"]


def test_gas_modes_carry_the_derived_gas_Q(vrh):
    r = G.evaluate(1.5, 1.0, 5.0, details=True)
    a = S.build_stack(3.0, 1.0)["r_in"]
    f0 = r["modes_Hz"]["B"][0]
    q = S.gas_Q(f0, a, p=G.P_ATM * 101325.0, T=S.T_REF, comp="HHO")
    assert 0 < q < float("inf")
    assert r["gas_Q_first"] == pytest.approx(q, rel=1e-3) and r["Q_eff"]["B"]["Q_first"] == pytest.approx(q, rel=1e-3)
    assert "derived" in r["Q_eff"]["B"]["source"]
    assert r["sharp_per_mode"] == pytest.approx(r["n_sharp_locks"] / r["n_modes_window"], abs=1e-4)


def test_build_stack_default_is_base_and_tourbillon_thickness_is_opt_in():
    assert S.build_stack(3.0, 1.0) == S.build_stack(3.0, 1.0, t_l2=5 * S.UM)
    l2 = [x for x in S.build_stack(3.0, 1.0, t_l2=8 * S.UM)["layers"] if x[0] == "layer2"][0]
    assert l2[2] - l2[1] == pytest.approx(8e-6)


def test_sweep_has_no_source_and_zero_run_stays_exact():
    for name in ("POWER", "P_SRC", "J_SRC", "drive"):
        assert not hasattr(G, name)
    G.evaluate(0.9, 0.5, 3.0)   # a sweep evaluation must not leave state behind
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    run = S.run_case(pre, {})
    assert run["W_ac"] == 0.0 and run["ac"]["W"] == 0.0 and all(m["W"] == 0.0 for m in run["ac"]["modes"])
    assert all(float(t) == 293.0 for t in run["Tss"]) and all(float(e) == 0.0 for e in run["E_ss"])
    assert S.GAS["T"] == S.T_REF and S.GAS["p"] == 101325.0


def test_sweep_output_file_is_consistent():
    d = json.loads((ROOT / "geometry_sweep_v0.json").read_text(encoding="utf-8"))
    m = d["meta"]
    assert m["n_total"] == len(d["results"]) == m["n_coarse"] + m["n_refine"]
    assert "unscored" in m["knees"] and m["T_K"] == 293.0
    ranks = [r["rank"] for r in d["results"]]
    assert ranks == list(range(1, len(ranks) + 1))
    assert d["base5"]["a_mm"] == 1.5 and d["base5"]["w_mm"] == 1.0 and d["base5"]["t2_um"] == 5.0
    for r in d["top10"]:
        assert r["cascade_ok"] and r["score"] == len(r["locks"])
    assert "derived" in m["gas_Q"] and 0 < m["gas_Q_range"][0] <= m["gas_Q_range"][1]
    assert sorted(r["rank_spm"] for r in d["results"]) == list(range(1, len(ranks) + 1))
    spm = [r["sharp_per_mode"] for r in d["top10_spm"]]
    assert spm == sorted(spm, reverse=True) and all(r["cascade_ok"] for r in d["top10_spm"])
