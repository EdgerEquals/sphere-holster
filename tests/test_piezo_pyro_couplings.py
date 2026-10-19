"""Piezoelectric (acoustic -> electric holster) and pyroelectric (thermal -> thermal holster) couplings in solver_v0.py.

Quartz: piezoelectric (d11), NOT pyroelectric (alpha-quartz point group 32; beta-quartz 622). Layer two (elbaite
tourmaline sol-gel, point group 3m): both. Couplings report polarization / energy density inside the layer only; there
are no collecting conductors and no circuit. With no source (the circulating-power scenarios are removed and the drive is
the no-drive stub) they are exactly zero."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import solver_v0 as S  # noqa: E402

A, B = 1.0e-3, 1.5e-3


def rows(sigma, n=11):
    return [(r, sigma) for r in np.linspace(A, B, n)]


def test_quartz_is_not_pyroelectric():
    assert S.MAT["quartz"]["p_pyro_C_per_m2K"] == 0.0
    for T in (150.0, 293.0, 800.0, 900.0):
        assert S.pyro_p("quartz", T) == 0.0
    out = S.pyro_coupling("quartz", [0, 1, 2], [293.0, 350.0, 400.0], 400.0)
    assert out["pyroelectric"] is False and out["dP_grain_C_m2"] == 0.0 and out["dPdt_grain_peak_A_m2"] == 0.0
    assert out["u_e_ss_J_m3"] == 0.0


def test_material_table_values_and_tags():
    q, l2 = S.PIEZO["quartz"], S.PIEZO["layer2"]
    assert q["d"] == pytest.approx(2.3e-12) and q["coeff"] == "d11" and q["T_off"] == pytest.approx(846.15)
    assert l2["d"] == pytest.approx(2.0e-12) and l2["coeff"] == "d33" and l2["phi"] == pytest.approx(0.20)
    assert S.pyro_p("layer2", 296.0) == pytest.approx(2.03e-6) and S.pyro_p("layer2", 383.0) == pytest.approx(2.68e-6)
    for k in ("quartz", "layer2"):
        tags = S.MAT[k]["piezo_tags"]
        assert "[lit]" in tags or "[rec]" in tags
    assert "[est]" in S.PIEZO["layer2"]["tags"]          # the 20 vol% dilution is an estimate


def test_piezo_scales_linearly_in_stress_and_quadratically_in_energy():
    for key in ("quartz", "layer2"):
        a = S.piezo_coupling(key, rows(1e6), A, B, 293.0, 3.0e6)
        b = S.piezo_coupling(key, rows(2e6), A, B, 293.0, 3.0e6)
        assert b["P_grain_peak_C_m2"] == pytest.approx(2 * a["P_grain_peak_C_m2"])
        assert b["u_e_peak_J_m3"] == pytest.approx(4 * a["u_e_peak_J_m3"])
        assert b["U_e_layer_J"] == pytest.approx(4 * a["U_e_layer_J"])
        c = S.PIEZO[key]
        assert a["P_grain_peak_C_m2"] == pytest.approx(c["d"] * 1e6)
        assert a["u_e_peak_J_m3"] == pytest.approx(c["phi"] * 0.5 * (c["d"] * 1e6) ** 2 / (S.EPS0 * c["eps_r"]))
    l2 = S.piezo_coupling("layer2", rows(1e6), A, B, 293.0, 3.0e6)
    assert l2["P_layer_net_upper_C_m2"] == pytest.approx(0.2 * l2["P_grain_peak_C_m2"])   # aligned upper bound
    assert l2["P_layer_net_random_C_m2"] == 0.0                                          # random grains cancel


def test_quartz_d11_vanishes_above_alpha_beta():
    lo = S.piezo_coupling("quartz", rows(1e6), A, B, 840.0, 3.0e6)
    hi = S.piezo_coupling("quartz", rows(1e6), A, B, 850.0, 3.0e6)
    assert lo["active"] and lo["P_grain_peak_C_m2"] > 0
    assert not hi["active"] and hi["P_grain_peak_C_m2"] == 0.0 and hi["U_e_layer_J"] == 0.0


def test_pyro_follows_dTdt_and_dT_with_synthetic_ramp():
    t = np.linspace(0.0, 10.0, 11)
    T = S.T_REF + 3.0 * t                                  # 3 K/s synthetic ramp, 293 -> 323 K
    out = S.pyro_coupling("layer2", t, T, float(T[-1]))
    assert out["dTdt_peak_K_s"] == pytest.approx(3.0)
    p_mid = S.pyro_p("layer2", float(T[-1]) - 1.5)
    assert out["dPdt_grain_peak_A_m2"] == pytest.approx(p_mid * 3.0, rel=1e-9)
    Tg = np.linspace(S.T_REF, T[-1], 1001)
    assert out["dP_grain_C_m2"] == pytest.approx(np.trapezoid([S.pyro_p("layer2", x) for x in Tg], Tg), rel=1e-4)
    assert out["P_layer_net_upper_C_m2"] == pytest.approx(0.2 * out["dP_grain_C_m2"])
    assert out["extrapolated"] is False
    twice = S.pyro_coupling("layer2", t, S.T_REF + 6.0 * t, S.T_REF + 60.0)
    assert twice["dTdt_peak_K_s"] == pytest.approx(6.0)
    hot = S.pyro_coupling("layer2", [0, 1], [293.0, 600.0], 600.0)
    assert hot["extrapolated"] is True                    # outside the 296-383 K data range


def test_zero_input_gives_zero_coupling():
    z = S.piezo_coupling("layer2", rows(0.0), A, B, 293.0, 3.0e6)
    assert z["P_grain_peak_C_m2"] == 0.0 and z["U_e_layer_J"] == 0.0
    flat = S.pyro_coupling("layer2", [0, 1, 2], [S.T_REF] * 3, S.T_REF)
    assert flat["dP_grain_C_m2"] == 0.0 and flat["dPdt_grain_peak_A_m2"] == 0.0 and flat["u_e_ss_J_m3"] == 0.0


def test_no_source_run_gives_exactly_zero_couplings_in_solver_output():
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    run = S.run_case(pre, {})
    assert run["em"]["note"] == S.NO_DRIVE
    out = S.package(pre, [run], {})
    pd = out["state"]
    for key in ("quartz", "layer2"):
        pz, py = pd["electric"]["piezo"][key], pd["thermal"]["pyro"][key]
        assert pz["P_grain_peak_C_m2"] == 0.0 and pz["U_e_layer_J"] == 0.0
        # thermal march now solves in theta = T - 293 K: the zero-heat state is exactly zero (the old ~1e-9 K drift is gone)
        assert py["dP_grain_C_m2"] == 0.0 and py["dPdt_grain_peak_A_m2"] == 0.0
        assert pz["f_mode_Hz"] == pytest.approx(run["ac"]["f"], rel=1e-3)   # solver's own eigenmode, not an input dial


def test_model_data_routes_couplings_to_electric_and_thermal_domains():
    d = json.loads((ROOT / "model_data_v0.json").read_text(encoding="utf-8"))
    seen = 0
    for c in d["cases"]:
        layers = {x["key"] for x in c["layers"]}
        for pd in [c["state"]]:
            for key in ("quartz", "layer2"):
                if key not in layers:
                    continue
                assert "electric holster" in pd["electric"]["piezo"][key]["route"]
                assert "thermal holster" in pd["thermal"]["pyro"][key]["route"]
                assert pd["thermal"]["pyro"]["quartz"]["pyroelectric"] is False
                seen += 1
    assert seen > 0
    assert d["meta"]["materials"]["quartz"]["p_pyro_C_per_m2K"] == 0.0


def test_lookup_excludes_neighbour_boundary_samples():
    # quartz and BTO samples sit at layer two's edges with much larger hoop stress; they must not leak in
    rows = [(A, "quartz", 9e6)] + [(r, "layer2", 1e6) for r in np.linspace(A, B, 6)] + [(B, "bto", 8e6)]
    out = S.piezo_coupling("layer2", rows, A, B, 293.0, 3.0e6)
    assert out["sigma_peak_Pa"] == pytest.approx(1e6)
    ref = S.piezo_coupling("layer2", [(r, 1e6) for r in np.linspace(A, B, 6)], A, B, 293.0, 3.0e6)
    assert out["U_e_layer_J"] == pytest.approx(ref["U_e_layer_J"])
    q = S.piezo_coupling("quartz", [(A - 1e-4, "quartz", 2e6), (A, "quartz", 2e6), (A, "layer2", 7e6)], A - 1e-4, A,
                         293.0, 3.0e6)
    assert q["sigma_peak_Pa"] == pytest.approx(2e6)


def test_solver_layer2_peak_comes_from_its_own_samples():
    # synthetic mode energy (the no-source run has W = 0): scale the solver's own eigenmode shape to 1 uJ
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    st = S.build_stack(pre["core_d"], pre["wall"])
    iso = [x for x in st["layers"] if x[0] in ("quartz", "layer2", "bto", "gddy")]
    f = S.run_case(pre, {})["ac"]["f"]   # the solver's own selection: lowest computed l=0 shell mode (fundamental)
    ac = S.mode_energy_stats(f, iso, 1.0e-6)
    lay = {m: (a, b) for m, a, b in iso}
    for key in ("quartz", "layer2"):
        own = max(s for r, m, s in ac["profile_m"] if m == key)
        assert S.piezo_coupling(key, ac["profile_m"], *lay[key], 293.0, f)["sigma_peak_Pa"] == pytest.approx(own, rel=1e-12)
        assert own > 0


def test_mode_selection_is_the_lowest_computed_shell_mode_and_never_invented():
    # 2 MHz selection target removed 2026-10-19: select the fundamental; with no computed mode, no frequency is invented
    assert S.lowest_shell_mode([3.121e6, 0.694e6, 6.016e6]) == 0.694e6
    assert S.lowest_shell_mode([]) is None
    st = S.build_stack(2.0, 0.5)
    nm = S.no_mode_stats(st["layers"], 0.0)
    assert nm["f"] is None and nm["peak_stress"] == 0.0 and nm["loss"] == {}
    assert all(s == 0.0 for _, _, s in nm["profile_m"])
