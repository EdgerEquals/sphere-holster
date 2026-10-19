"""Piezoelectric (acoustic -> electric holster) and pyroelectric (thermal -> thermal holster) couplings in solver_v0.py.

Quartz: piezoelectric (d11), NOT pyroelectric (alpha-quartz point group 32; beta-quartz 622). Layer two (elbaite
tourmaline sol-gel, point group 3m): both. Couplings report polarization / energy density inside the layer only; there
are no collecting conductors and no circuit. With no source (the circulating-power scenarios are removed and the drive is
the no-drive stub) they are exactly zero."""
import json
import math
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
        # every computed l=0 shell mode is carried (none selected), each at the solver's own eigenfrequency
        assert pz["f_modes_Hz"] == pytest.approx(run["m_iso"], rel=1e-3) and pz["n_modes"] == len(run["m_iso"]) > 0
        assert len(pz["modes"]) == len(run["m_iso"]) and "f_mode_Hz" not in pz
        for m in pz["modes"]:
            assert m["P_grain_peak_C_m2"] == 0.0 and m["U_e_layer_J"] == 0.0 and m["E_internal_open_peak_V_m"] == 0.0


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
    fs = S.run_case(pre, {})["m_iso"]   # every computed l=0 shell mode (none selected)
    assert len(fs) > 1
    lay = {m: (a, b) for m, a, b in iso}
    for f in fs:
        ac = S.mode_energy_stats(f, iso, 1.0e-6)
        for key in ("quartz", "layer2"):
            own = max(s for r, m, s in ac["profile_m"] if m == key)
            assert S.piezo_coupling(key, ac["profile_m"], *lay[key], 293.0, f)["sigma_peak_Pa"] == pytest.approx(own, rel=1e-12)
            assert own > 0


def test_every_computed_mode_is_carried_and_none_selected():
    # mode-locking framing (DESIGN_STATE 2026-10-19): the lowest-mode selection is removed; every l=0 shell mode is carried
    assert not hasattr(S, "lowest_shell_mode")
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    run = S.run_case(pre, {})
    assert [m["f"] for m in run["ac"]["modes"]] == sorted(run["m_iso"]) and run["ac"]["f"] is None
    assert [m["f"] for m in run["ac_bond"]["modes"]] == sorted(run["m_bond"])
    for m in run["ac"]["modes"] + run["ac_bond"]["modes"]:   # each mode's own energy marched from 0: all zero with no source
        assert m["W"] == 0.0 and m["peak_stress"] == 0.0 and sum(m["loss"].values()) == 0.0
        assert m["tau_ac"] == pytest.approx(m["Q_eff"] / (math.pi * m["f"]))
    st = S.package(pre, [run], {})["state"]
    a = st["acoustic"]
    assert a["n_modes"] == len(a["modes"]) == len(run["m_iso"]) and a["carried"] == f"all l=0 shell modes ({len(run['m_iso'])})"
    assert "f_mode" not in a and a["bonded"]["n_modes"] == len(run["m_bond"]) == len(a["l0_bonded"])
    v = next(x for x in st["vectors"] if x["domain"] == "acoustic")
    assert v["f_start"] == S.r4(min(run["m_iso"])) and v["f_end"] == S.r4(max(run["m_iso"]))   # spans all modes


def test_aggregates_are_sum_and_max_over_all_modes():
    # synthetic per-mode energies (the no-source run has W = 0) to check the aggregate rules on non-zero numbers
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    st = S.build_stack(pre["core_d"], pre["wall"])
    iso = [x for x in st["layers"] if x[0] in ("quartz", "layer2", "bto", "gddy")]
    fs = S.run_case(pre, {})["m_iso"]
    modes = S.all_modes_stats(fs, iso, 1.0e-6)
    agg = S.sum_over_modes(modes, iso)
    assert agg["f"] is None and agg["f_modes"] == sorted(fs)
    assert agg["W"] == pytest.approx(len(fs) * 1.0e-6)
    assert agg["peak_stress"] == max(m["peak_stress"] for m in modes)
    assert agg["tau_ac"] == max(m["tau_ac"] for m in modes)
    for k in agg["loss"]:
        assert agg["loss"][k] == pytest.approx(sum(m["loss"].get(k, 0.0) for m in modes))
    for k, row in enumerate(agg["profile_m"]):
        assert row[2] == pytest.approx(sum(m["profile_m"][k][2] for m in modes))
    assert agg["peak_stress_sum"] == pytest.approx(max(x[1] for x in agg["profile"])) and agg["peak_stress_sum"] >= agg["peak_stress"]
    lay = {m: (a, b) for m, a, b in iso}
    for key in ("quartz", "layer2"):
        pz = S.piezo_over_modes(key, modes, *lay[key], 293.0)
        per = [S.piezo_coupling(key, m["profile_m"], *lay[key], 293.0, m["f"]) for m in modes]
        assert pz["n_modes"] == len(per) == len(pz["modes"]) and pz["f_modes_Hz"] == [m["f"] for m in modes]
        assert pz["U_e_layer_J"] == pytest.approx(sum(x["U_e_layer_J"] for x in per)) and pz["U_e_layer_J"] > 0
        for k in S.PIEZO_PEAK_KEYS:
            assert pz[k] == max(x[k] for x in per)


def test_empty_mode_list_gives_no_modes_and_zeros():
    st = S.build_stack(2.0, 0.5)
    assert S.all_modes_stats([], st["layers"], 0.0) == []
    agg = S.sum_over_modes([], st["layers"])
    assert agg["f"] is None and agg["f_modes"] == [] and agg["modes"] == [] and agg["tau_ac"] is None
    assert agg["W"] == 0.0 and agg["peak_stress"] == 0.0 and agg["peak_stress_sum"] == 0.0 and agg["loss"] == {}
    assert all(s == 0.0 for _, _, s in agg["profile_m"])
    a, b = next((x[1], x[2]) for x in st["layers"] if x[0] == "quartz")
    pz = S.piezo_over_modes("quartz", [], a, b, 293.0)
    assert pz["n_modes"] == 0 and pz["f_modes_Hz"] == [] and pz["modes"] == []
    assert pz["U_e_layer_J"] == 0.0 and all(pz[k] == 0.0 for k in S.PIEZO_PEAK_KEYS)
    nm = S.no_mode_stats(st["layers"], 0.0)
    assert nm["f"] is None and nm["peak_stress"] == 0.0 and nm["loss"] == {}

