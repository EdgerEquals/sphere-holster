"""Acceptance test: the zero run (2026-10-19).

With no drive and no input (the circulating-power scenarios are removed, the drive is the no-drive stub, J_src = 0),
every field is exactly zero everywhere (electric, magnetic, optical, acoustic, chemical, and every coupling output) and
the whole stack sits at the 293 K reference. Exact equality, no tolerance: the thermal march solves in
theta = T - 293 K, so a zero-heat state stays exactly zero.

Each coupling is then checked on its own with synthetic inputs: stress for piezo, a temperature change for pyro, an
electric-field change for electrocaloric. Zero input must give exactly zero output; non-zero input must scale as the
physics says."""
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import solver_v0 as S  # noqa: E402

ZERO_FIELDS = ("electric", "magnetic", "optical", "acoustic", "chemical")


def _flat(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _flat(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _flat(v)
    else:
        yield x


@pytest.fixture(scope="module")
def live():
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    run = S.run_case(pre, {})
    return pre, run, S.package(pre, [run], {})["state"]


@pytest.fixture(scope="module")
def model_data():
    return json.loads((ROOT / "model_data_v0.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- the zero run itself
def test_no_power_levels_or_scenario_splits_remain():
    for name in ("POWERS", "F_WALL", "F_OPT"):
        assert not hasattr(S, name)
    import inspect
    assert list(inspect.signature(S.run_case).parameters) == ["pre", "ref"]   # no power argument


def test_zero_run_live_all_fields_exactly_zero_and_stack_at_293K(live):
    pre, run, st = live
    for dom in ZERO_FIELDS:
        assert all(v == 0.0 for v in st["fields"][dom]), dom
    assert all(v == S.T_REF for v in st["fields"]["thermal"])
    assert all(v == S.T_REF for v in itertools.chain(*st["thermal_frames"]["T"]))
    assert np.all(run["Tss"] == S.T_REF) and all(np.all(fr == S.T_REF) for fr in run["frames"])
    # electric march: zero at every frame, polarization zero, no electrocaloric heat or entropy
    assert all(np.all(E == 0.0) for E in run["E_frames"]) and np.all(run["E_ss"] == 0.0) and np.all(run["P_ss"] == 0.0)
    assert all(v == 0.0 for v in run["s_ec"].values()) and all(v == 0.0 for v in run["q_ec_J"].values())
    assert set(run["s_ec"]) == {"layer2", "bto"}
    # acoustic and optical carry nothing
    assert run["W_ac"] == 0.0 and run["ac"]["peak_stress"] == 0.0 and sum(run["ac"]["loss"].values()) == 0.0
    assert float(np.sum(run["q"])) == 0.0 and run["oinfo"]["escaped_W"] == 0.0
    # gas stays at the seal state
    g = st["gas"]
    assert g["T_gas_K"] == S.T_REF and g["T_centre_K"] == S.T_REF and g["p_hot_Pa"] == g["p_seal_Pa"]


def test_zero_run_coupling_outputs_exactly_zero(live):
    _, _, st = live
    for key, pz in st["electric"]["piezo"].items():
        assert pz["P_grain_peak_C_m2"] == 0.0 and pz["U_e_layer_J"] == 0.0 and pz["E_internal_open_peak_V_m"] == 0.0
    for key, py in st["thermal"]["pyro"].items():
        assert py["dP_grain_C_m2"] == 0.0 and py["dPdt_grain_peak_A_m2"] == 0.0 and py["u_e_ss_J_m3"] == 0.0
    m = st["electric"]["march"]
    assert m["E_max_V_m"] == 0.0 and m["E_piezo_ac_max_V_m"] == 0.0
    assert all(v == 0.0 for v in _flat(m["layers"])) and all(v == 0.0 for v in m["ec_heat_J"].values())
    assert all(v == 0.0 for v in st["chemical"]["entropy_ec_J_K"].values())
    assert all(v == 0.0 for v in st["thermal"]["electrocaloric_heat_J"].values())
    assert st["thermal"]["total_heat_W"] == 0.0 and all(v == 0.0 for v in st["thermal"]["heat_W"].values())
    ch = st["chemical"]
    assert ch["P_diss_W"] == 0.0 and ch["P_release_W"] == 0.0 and ch["P_wall_recomb_W"] == 0.0 and ch["R_diss_per_s"] == 0.0


def test_zero_run_every_case_in_model_data(model_data):
    assert "powers" not in model_data["meta"]
    for c in model_data["cases"]:
        assert "powers" not in c
        st = c["state"]
        for dom in ZERO_FIELDS:
            assert all(v == 0.0 for v in st["fields"][dom]), (c["id"], dom)
        assert all(v == S.T_REF for v in st["fields"]["thermal"]), c["id"]
        assert all(v == S.T_REF for v in itertools.chain(*st["thermal_frames"]["T"])), c["id"]
        assert st["electric"]["march"]["E_max_V_m"] == 0.0 and st["optical"]["P_opt"] == 0.0
        assert st["acoustic"]["W_mJ"] == 0.0 and st["acoustic"]["peak_stress_MPa"] == 0.0
        assert st["thermal"]["total_heat_W"] == 0.0 and st["gas"]["T_gas_K"] == S.T_REF


def test_thermal_theta_march_is_exact_at_zero_heat():
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    st = S.build_stack(pre["core_d"], pre["wall"])
    cells, mats = S.make_grid(st)
    for outer in ("dirichlet", "natconv"):
        th = S.Thermal(cells, mats); th.outer = outer
        theta = np.zeros(th.n)
        for dt in np.geomspace(1e-9, 1e4, 60):
            theta = th.step(theta, np.zeros(th.n), dt)
        assert np.all(theta == 0.0), outer


# ---------------------------------------------------------------- per-coupling synthetic inputs
def test_piezo_synthetic_stress():
    for key in ("quartz", "layer2"):
        assert S.piezo_P_ac(key, 0.0, 293.0) == 0.0 and S.piezo_E_ac(key, 0.0, 293.0, 3e6) == 0.0
        p1, p2 = S.piezo_P_ac(key, 1e6, 293.0), S.piezo_P_ac(key, 3e6, 293.0)
        c = S.PIEZO[key]
        assert p1 == pytest.approx(c["phi"] * c["d"] * 1e6, rel=1e-12) and p2 == pytest.approx(3 * p1, rel=1e-12)
        e1, e2 = S.piezo_E_ac(key, 1e6, 293.0, 3e6), S.piezo_E_ac(key, 2e6, 293.0, 3e6)
        assert e2 == pytest.approx(2 * e1, rel=1e-12)
        # sigma << w eps at MHz: open-circuit limit |E| = |P| / eps
        assert e1 == pytest.approx(p1 / S.el_eps(key, 293.0), rel=1e-6)
    assert S.piezo_P_ac("quartz", 1e6, 850.0) == 0.0          # beta quartz: d11 = 0
    assert S.piezo_P_ac("bto", 1e6, 293.0) == 0.0             # BTO piezo not modelled


def test_pyro_synthetic_temperature_change():
    for key in ("layer2", "bto"):
        assert S.pyro_P(key, S.T_REF) == 0.0
    assert S.pyro_P("quartz", 400.0) == 0.0
    # BTO p is flat below Curie: polarization exactly linear in dT, signed -eta*phi*p
    d1, d2 = S.pyro_P("bto", S.T_REF + 5.0), S.pyro_P("bto", S.T_REF + 10.0)
    assert d1 == pytest.approx(-S.ETA_ALIGN * 2.0e-4 * 5.0, rel=1e-12) and d2 == pytest.approx(2 * d1, rel=1e-12)
    assert S.pyro_p("bto", 400.0) == 0.0                     # paraelectric above ~393 K
    # layer two: integral of p(T) over the step, x phi (aligned upper bound)
    Tg = np.linspace(S.T_REF, 330.0, 2001)
    ref = -S.ETA_ALIGN * 0.2 * np.trapezoid([S.pyro_p("layer2", x) for x in Tg], Tg)
    assert S.pyro_P("layer2", 330.0) == pytest.approx(ref, rel=1e-6)
    # into the electric march: E_n = -(dP)/(eps + sigma dt) from E = 0
    mats = ["quartz", "layer2", "bto", "gddy"]
    for dT in (0.0, 2.0, 4.0):
        em = S.ElectricMarch(mats); T = np.full(4, S.T_REF + dT); dt = 1e-6
        Eo, En = em.step(T, dt)
        assert np.all(Eo == 0.0)
        for i, m in enumerate(mats):
            want = -S.pyro_P(m, T[i]) / (S.el_eps(m, T[i]) + S.el_sigma(m, T[i]) * dt)
            assert En[i] == pytest.approx(want, rel=1e-12, abs=0.0)
        if dT == 0.0:
            assert np.all(En == 0.0)
    assert En[0] == 0.0 and abs(En[3]) < 1e-12 * abs(En[2])   # quartz non-polar; metal film shorts the field


def test_electric_march_relaxes_with_sigma_over_eps():
    em = S.ElectricMarch(["bto"]); T = np.array([S.T_REF + 1.0])
    em.step(T, 1e-12)                                            # pyro step: E jumps to -dP/eps
    E0 = float(em.E[0]); tau = S.el_eps("bto", T[0]) / S.el_sigma("bto", T[0])
    for _ in range(1000):
        em.step(T, tau / 1000)                                   # P constant: free relaxation
    assert float(em.E[0]) == pytest.approx(E0 * (1 + 1 / 1000) ** -1000, rel=1e-9)


def test_electrocaloric_synthetic_field_change():
    for key in ("layer2", "bto"):
        z = S.electrocaloric(key, 300.0, 1e5, 1e5)
        assert z["ds_J_m3K"] == 0.0 and z["dq_J_m3"] == 0.0 and z["dT_adiabatic_K"] == 0.0
        a, b = S.electrocaloric(key, 300.0, 0.0, 1e5), S.electrocaloric(key, 300.0, 0.0, 2e5)
        assert b["ds_J_m3K"] == pytest.approx(2 * a["ds_J_m3K"], rel=1e-12) and b["dq_J_m3"] == pytest.approx(2 * a["dq_J_m3"], rel=1e-12)
        assert a["ds_J_m3K"] == pytest.approx(S.p_net(key, 300.0) * 1e5, rel=1e-12)          # Maxwell: dS/dE = p
        assert a["dq_J_m3"] == pytest.approx(-300.0 * a["ds_J_m3K"], rel=1e-12)               # dq = -T ds
        assert a["dT_adiabatic_K"] > 0                    # field along the polar axis: entropy falls, lattice warms
        assert S.electrocaloric(key, 600.0, 0.0, 1e5)["dq_J_m3"] == pytest.approx(2 * a["dq_J_m3"] * S.p_net(key, 600.0) / S.p_net(key, 300.0))
    q = S.electrocaloric("quartz", 300.0, 0.0, 1e6)
    assert q["ds_J_m3K"] == 0.0 and q["dq_J_m3"] == 0.0
    assert S.electrocaloric("bto", 400.0, 0.0, 1e6)["dq_J_m3"] == 0.0    # above Curie: no EC (not modelled)


def test_electrocaloric_heat_enters_thermal_as_its_own_energy():
    pre = next(p for p in S.PRESETS if p["id"] == "base5")
    st = S.build_stack(pre["core_d"], pre["wall"])
    cells, mats = S.make_grid(st)
    th = S.Thermal(cells, mats); dt = 1e-9
    ib = [i for i, m in enumerate(mats) if m == "bto"]
    for dE in (0.0, 1e5, 2e5):
        q = np.zeros(th.n)
        for i in ib:
            q[i] = S.electrocaloric("bto", S.T_REF, 0.0, dE)["dq_J_m3"] * th.V[i] / dt
        theta = th.step(np.zeros(th.n), q, dt)
        if dE == 0.0:
            assert np.all(theta == 0.0)
        else:
            assert float(np.sum(th.C * theta)) == pytest.approx(float(np.sum(q)) * dt, rel=1e-3)   # heat in = heat stored
            assert all(theta[i] > 0 for i in ib)
