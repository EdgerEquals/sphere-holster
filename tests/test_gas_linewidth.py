"""Gas-cavity loss: derived, modulated Q (thermal wall boundary layer + classical bulk absorption) for l=0 gas modes,
recomputed from pressure, temperature, composition and bubble radius; its linewidth enters the half-width lock rule."""
import math

import solver_v0 as S

A, P1, T0 = 1.5e-3, 101325.0, 293.0
F1 = 4.4934 * 533.0 / (2 * math.pi * A)          # first l=0 rigid-wall mode of the base5 bubble, ~254 kHz


def test_no_fixed_constant_and_hand_formula():
    assert not hasattr(S, "GAS_Q")
    t = S.gas_Q_terms(F1, A, P1, T0, "HHO"); g = t["props"]
    d_t = math.sqrt(g["k"] / (g["rho"] * g["cp"]) / (math.pi * F1))
    g_th = (g["gamma"] - 1) * F1 * d_t / (2 * A)
    g_cl = math.pi * F1 ** 2 / g["c"] ** 2 * (4 / 3 * g["mu"] / g["rho"] + (g["gamma"] - 1) * g["D_t"])
    assert math.isclose(t["Q"], F1 / (2 * (g_th + g_cl)), rel_tol=1e-12)
    assert t["g_visc_Hz"] == 0.0                     # radial mode: no tangential wall velocity, no viscous wall loss
    assert 200 < t["Q"] < 400                        # HHO, 1 atm, 293 K, 1.5 mm bubble: Q ~ 300
    assert math.isclose(g["k"], S.K_HHO0, rel_tol=0.01)   # Wilke mix of H2/O2 agrees with the solver's HHO k


def test_q_is_modulated_by_pressure_size_temperature_composition():
    th = lambda **kw: S.gas_Q_terms(kw.pop("f", F1), kw.pop("a", A), kw.pop("p", P1), kw.pop("T", T0), kw.pop("comp", "HHO"))
    assert math.isclose(th(p=4 * P1)["Q_th"], 2 * th()["Q_th"], rel_tol=1e-9)    # Q_th ~ sqrt(p)
    assert math.isclose(th(a=2 * A)["Q_th"], 2 * th()["Q_th"], rel_tol=1e-9)     # Q_th ~ a at fixed f
    assert math.isclose(th(p=2 * P1)["Q_cl"], 2 * th()["Q_cl"], rel_tol=1e-9)    # Q_cl ~ p
    assert math.isclose(th(f=2 * F1)["Q_cl"], 0.5 * th()["Q_cl"], rel_tol=1e-9)  # Q_cl ~ 1/f
    assert th(T=600.0)["Q"] < th()["Q"]                                           # hotter gas: more diffusive, lower Q
    assert th(comp="air")["Q"] != th()["Q"] and th(comp={"H2": 2, "O2": 1})["Q"] == th()["Q"]
    S.GAS["p"], S.GAS["T"] = 2 * P1, 400.0                                       # defaults follow the coupled gas state
    try:
        assert S.gas_Q(F1, A) == S.gas_Q(F1, A, 2 * P1, 400.0)
    finally:
        S.GAS["p"], S.GAS["T"] = 101325.0, None


def test_gas_linewidth_widens_the_lock_window():
    fq, Qq = F1, 2100.0
    lwq, lwg = fq / Qq, S.gas_linewidth(fq, A, P1, T0)
    assert math.isclose(lwg, fq / S.gas_Q(fq, A, P1, T0), rel_tol=1e-12) and lwg > 0
    df = 0.5 * lwq + 0.25 * lwg                       # outside half the partner's width, inside half the sum
    assert not S.modes_lock(fq, lwq, fq + df, 0.0)
    assert S.modes_lock(fq, lwq, fq + df, lwg)
    assert not S.modes_lock(fq, lwq, fq + 0.5 * (lwq + lwg) * 1.01, lwg)
    assert S.modes_lock(fq, lwq, fq + 0.5 * (lwq + lwg), lwg)   # inclusive (<=)
