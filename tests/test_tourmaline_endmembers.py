"""Tourmaline end-member sweep (dravite, schorl, elbaite) for layer two / the tourbillon tourmaline component (2026-10-19).

Each end-member carries its ideal formula and its own sourced (or UNSURE / not available) coefficients. The sweep runs the
same recipe with each end-member; the default run (layer two as before) is unchanged. Zero in gives exactly zero out for
every end-member, and the synthetic comparison scales with each end-member's own coefficients."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import solver_v0 as S  # noqa: E402

MEMBERS = ("elbaite", "dravite", "schorl")


def test_table_has_three_end_members_with_formulae_and_tags():
    assert set(S.TOURMALINE) == set(MEMBERS)
    assert S.TOURMALINE["dravite"]["formula"] == "NaMg3Al6(Si6O18)(BO3)3(OH)3(OH)"
    assert S.TOURMALINE["schorl"]["formula"] == "NaFe3Al6(Si6O18)(BO3)3(OH)3(OH)"
    assert S.TOURMALINE["elbaite"]["formula"] == "Na(Li1.5Al1.5)Al6(Si6O18)(BO3)3(OH)3(OH)"
    for m, t in S.TOURMALINE.items():
        for k in ("d33_tag", "p_tag", "dipole_tag", "chi_tag"):
            assert any(x in t[k] for x in ("[lit", "[rec", "[est", "[calc", "not available")), (m, k)
        if t["dipole_Cm"] is None:
            assert t["dipole_tag"] == "not available"
    assert "UNSURE" in S.TOURMALINE["schorl"]["d33_tag"] and "UNSURE" in S.TOURMALINE["dravite"]["p_tag"]
    # Hawkins 1995 Table 5: Fe lowers p3; schorl is the lowest
    p296 = {m: S.TOURMALINE[m]["p_T"][0][1] for m in MEMBERS}
    assert p296["schorl"] < p296["dravite"] < p296["elbaite"]
    assert S.TOURMALINE["schorl"]["magnetic"] and not S.TOURMALINE["elbaite"]["magnetic"]
    assert "feature" in S.TOURMALINE_MAGNETIC_FLAG and "confound" in S.TOURMALINE_MAGNETIC_FLAG


def test_context_manager_swaps_and_restores_default_layer2():
    before = dict(S.PIEZO["layer2"])
    for m in MEMBERS:
        with S.use_tourmaline(m) as t:
            assert S.PIEZO["layer2"]["d"] == t["d33"] and S.PIEZO["layer2"]["p_T"] == t["p_T"]
            assert S.PIEZO["layer2"]["phi"] == before["phi"] and S.PIEZO["layer2"]["eps_r"] == before["eps_r"]   # same recipe
        assert S.PIEZO["layer2"] == before
    with pytest.raises(ValueError):
        S.use_tourmaline("uvite")


@pytest.mark.parametrize("member", MEMBERS)
def test_zero_in_gives_exactly_zero_out_per_member(member):
    with S.use_tourmaline(member):
        assert S.piezo_P_ac("layer2", 0.0, 293.0) == 0.0 and S.piezo_E_ac("layer2", 0.0, 293.0, 3e6) == 0.0
        assert S.pyro_P("layer2", S.T_REF) == 0.0
        z = S.electrocaloric("layer2", 300.0, 2e5, 2e5)
        assert z["ds_J_m3K"] == 0.0 and z["dq_J_m3"] == 0.0
        em = S.ElectricMarch(["layer2"]); _, En = em.step(np.array([S.T_REF]), 1e-6)
        assert En[0] == 0.0
        pre = next(p for p in S.PRESETS if p["id"] == "base5")
        run = S.run_case(pre, {})
        st = S.package(pre, [run], {})["state"]
        for dom in ("electric", "magnetic", "optical", "acoustic", "chemical"):
            assert all(v == 0.0 for v in st["fields"][dom]), dom
        assert all(v == S.T_REF for v in st["fields"]["thermal"])
        assert all(np.all(E == 0.0) for E in run["E_frames"]) and run["s_ec"]["layer2"] == 0.0


def test_synthetic_comparison_scales_with_each_members_coefficients():
    y = {m: S.tourmaline_synthetic(m) for m in MEMBERS}
    for m in MEMBERS:
        t = S.TOURMALINE[m]
        assert y[m]["piezo_P_C_m2"] == pytest.approx(S.ETA_ALIGN * 0.2 * t["d33"] * 1e6, rel=1e-12)
        assert y[m]["pyro_P_C_m2"] < 0 and y[m]["pyro_E_V_m"] > 0
        assert y[m]["ec_dT_K"] > 0
        # electrocaloric ds = p_net dE with the member's own p (Maxwell relation)
        with S.use_tourmaline(m):
            assert y[m]["ec_ds_J_m3K"] == pytest.approx(S.p_net("layer2", 300.0) * 1e5, rel=1e-12)
    # ratios follow the coefficient ratios
    assert y["elbaite"]["piezo_P_C_m2"] / y["dravite"]["piezo_P_C_m2"] == pytest.approx(2.2 / 1.8, rel=1e-12)
    r = y["elbaite"]["ec_ds_J_m3K"] / y["schorl"]["ec_ds_J_m3K"]
    with S.use_tourmaline("elbaite"):
        pe = S.pyro_p("layer2", 300.0)
    with S.use_tourmaline("schorl"):
        ps = S.pyro_p("layer2", 300.0)
    assert r == pytest.approx(pe / ps, rel=1e-12)
    # doubling the inputs doubles the outputs
    for m in MEMBERS:
        d = S.tourmaline_synthetic(m, sigma=2e6, dE=2e5)
        assert d["piezo_P_C_m2"] == pytest.approx(2 * y[m]["piezo_P_C_m2"], rel=1e-12)
        assert d["ec_dq_J_m3"] == pytest.approx(2 * y[m]["ec_dq_J_m3"], rel=1e-12)


def test_default_layer2_is_untouched_by_the_sweep():
    d = S.PIEZO_LAYER2_DEFAULT
    assert d["d"] == pytest.approx(2.0e-12) and d["p_T"] == ((296.0, 2.03e-6), (383.0, 2.68e-6))
    S.run_tourmaline_sweep(["dravite"], [next(p for p in S.PRESETS if p["id"] == "base5")], {})
    assert S.PIEZO["layer2"] == d
