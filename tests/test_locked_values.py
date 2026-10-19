"""Locked values from DESIGN_STATE.md (and cited docs), re-derived symbolically with SymPy.

Every expected number is parsed from the cited file at test time (see harness/locked_values.yml),
so a change in DESIGN_STATE.md, the yml, the derivation, or solver_v0.py shows up as expected-vs-got.
"""
import sys

import pytest

import derive as dv

from pathlib import Path
sys.path.insert(0, str(Path(dv.__file__).resolve().parent.parent))
import solver_v0 as solver  # noqa: E402

QZ = solver.QZ_SOUND


def src(locked, key):
    v = locked["values"][key]
    return f"{v['cite']['file']}:{v['found_line']}"


def val(locked, key):
    v = locked["values"][key]
    assert v["found"] is not None, f"{key}: pattern {v['cite']['pattern']!r} not found in {v['cite']['file']}"
    return v["found"]


# ---------- the yml must agree with the documents it cites ----------
@pytest.mark.parametrize("key", [
    "lock_shell_od_mm", "lock_shell_wall_mm", "lock_shell_thickness_mode_MHz", "test_shell_id_mm",
    "test_shell_od_mm", "test_shell_wall_mm", "test_shell_breathing_MHz", "hho_sound_speed_293K_mps",
    "hho_gamma", "dHf_H2O_gas_kJ_per_mol"])
def test_yml_matches_cited_document(locked, record, key):
    v = locked["values"][key]
    found = val(locked, key)
    ok = record(f"{key} (yml vs doc)", v["expected"], found, "exact", src(locked, key), ok=found == float(v["expected"]))
    moved = v["cite"].get("line") != v["found_line"]
    assert ok, f"{key}: harness/locked_values.yml says {v['expected']} but {src(locked, key)} says {found}"
    if moved:
        record(f"{key} line moved", v["cite"].get("line"), v["found_line"], "-", v["cite"]["file"], info=True)


# ---------- geometry ----------
def test_test_shell_wall_is_half_od_minus_id(locked, record):
    import sympy as sp
    ID, OD = sp.nsimplify(val(locked, "test_shell_id_mm")), sp.nsimplify(val(locked, "test_shell_od_mm"))
    wall = (OD - ID) / 2
    exp = val(locked, "test_shell_wall_mm")
    ok = record("test shell wall = (OD-ID)/2 [mm]", exp, float(wall), "exact", src(locked, "test_shell_wall_mm"),
                ok=float(wall) == exp)
    assert ok, f"(OD-ID)/2 = {float(wall)} mm, DESIGN_STATE wall = {exp} mm"


# ---------- quartz shell modes ----------
def _lock_geom(locked):
    b = val(locked, "lock_shell_od_mm") / 2 * 1e-3
    t = val(locked, "lock_shell_wall_mm") * 1e-3
    return b - t, b, t


def test_lock_shell_thickness_mode(locked, record):
    d = locked["derivations"]["lock_shell_thickness_mode"]
    a, b, t = _lock_geom(locked)
    sp_ = QZ[d["sound_speed"]]
    modes = dv.shell_l0_modes(a, b, sp_["cL"], sp_["cT"])
    got = modes[1] / 1e6                                    # 2nd l=0 root = 1S0 thickness-type
    exp = val(locked, "lock_shell_thickness_mode_MHz")
    r = dv.rel(got, exp)
    ok = record(f"lock shell 1S0, exact l=0, cL/cT {sp_['cL']:.0f}/{sp_['cT']:.0f} ({d['sound_speed']}) [MHz]",
                exp, got, f"±{d['tol_rel']:.1%} (got {r:+.2%})", src(locked, "lock_shell_thickness_mode_MHz"),
                ok=abs(r) <= d["tol_rel"])
    # Informational: what the other readings of 3.236 MHz would give / need
    vrh = dv.shell_l0_modes(a, b, QZ["vrh"]["cL"], QZ["vrh"]["cT"])[1] / 1e6
    record("lock shell 1S0 with solver default VRH 6048/4090 [MHz]", exp, vrh, f"info ({dv.rel(vrh, exp):+.2%})",
           "solver_v0.QZ_SOUND['vrh']", info=True)
    _, slab, implied = dv.slab_thickness_mode(t, QZ["vrh"]["cL"])
    record("slab cL/(2t) with VRH cL 6048 [MHz]", exp, slab / 1e6, f"info ({dv.rel(slab / 1e6, exp):+.2%})",
           "f = cL/(2t)", info=True)
    record("cL implied by slab cL/(2t) = 3.236 MHz [m/s]", "-", implied(exp * 1e6), "info", "2 t f", info=True)
    assert ok, (f"lock shell 1S0 = {got:.4f} MHz vs DESIGN_STATE {exp} MHz ({r:+.2%}, tol ±{d['tol_rel']:.1%}) "
                f"using cL/cT {sp_['cL']}/{sp_['cT']}")


def test_test_shell_breathing_mode(locked, record):
    d = locked["derivations"]["test_shell_breathing"]
    a = val(locked, "test_shell_id_mm") / 2 * 1e-3
    b = val(locked, "test_shell_od_mm") / 2 * 1e-3
    sp_ = QZ[d["sound_speed"]]
    got = dv.shell_l0_modes(a, b, sp_["cL"], sp_["cT"])[0] / 1e6
    exp = val(locked, "test_shell_breathing_MHz")
    r = dv.rel(got, exp)
    ok = record(f"test shell 0S0 breathing, exact l=0, {d['sound_speed']} {sp_['cL']:.0f}/{sp_['cT']:.0f} [MHz]",
                exp, got, f"±{d['tol_rel']:.0%} (got {r:+.2%})", src(locked, "test_shell_breathing_MHz"),
                ok=abs(r) <= d["tol_rel"])
    assert ok, f"test shell 0S0 = {got:.4f} MHz vs DESIGN_STATE about {exp} MHz ({r:+.2%})"


@pytest.mark.parametrize("which", ["test_0S0", "lock_1S0"])
def test_solver_matches_symbolic(locked, record, which):
    tol = locked["derivations"]["solver_agreement"]["tol_rel"]
    if which == "test_0S0":
        a, b, key, idx = (val(locked, "test_shell_id_mm") / 2e3, val(locked, "test_shell_od_mm") / 2e3,
                          locked["derivations"]["test_shell_breathing"]["sound_speed"], 0)
    else:
        a, b, _ = _lock_geom(locked)
        key, idx = locked["derivations"]["lock_shell_thickness_mode"]["sound_speed"], 1
    sym = dv.shell_l0_modes(a, b, QZ[key]["cL"], QZ[key]["cT"])[idx]
    solver.set_qz_sound(key)
    try:
        roots = solver.l0_modes([("quartz", a, b)], fmax=8e6)   # includes gas-cavity roots; pick the nearest
    finally:
        solver.set_qz_sound("vrh")
    near = min(roots, key=lambda x: abs(x - sym))
    r = dv.rel(near, sym)
    ok = record(f"solver_v0 vs SymPy, {which} ({key}) [MHz]", sym / 1e6, near / 1e6, f"±{tol:.1%} (got {r:+.3%})",
                "solver_v0.l0_modes", ok=abs(r) <= tol)
    assert ok, f"solver_v0 {near / 1e6:.4f} MHz vs SymPy {sym / 1e6:.4f} MHz ({r:+.3%})"


# ---------- HHO gas ----------
def test_hho_sound_speed(locked, record):
    d = locked["derivations"]["hho_sound_speed"]
    expr, got, M = dv.hho_sound_speed(293.0, val(locked, "hho_gamma"))
    exp = val(locked, "hho_sound_speed_293K_mps")
    ok = record(f"HHO c = sqrt(gamma R T / M) at 293 K, gamma {val(locked, 'hho_gamma')}, M {M:.3f} g/mol [m/s]", exp, got, f"±{d['tol_abs']:g} m/s",
                src(locked, "hho_sound_speed_293K_mps"), ok=abs(got - exp) <= d["tol_abs"])
    s = solver.c_hho(293.0)
    ok2 = record("solver_v0.c_hho(293 K) vs SymPy [m/s]", got, s, "±0.1%", "solver_v0.c_hho", ok=abs(dv.rel(s, got)) <= 1e-3)
    assert ok, f"HHO c(293 K) = {got:.2f} m/s vs doc {exp} m/s"
    assert ok2, f"solver c_hho {s:.2f} vs SymPy {got:.2f} m/s"


# ---------- chemistry ----------
def test_dHf_h2o_used_by_solver(locked, record):
    exp = val(locked, "dHf_H2O_gas_kJ_per_mol")
    got = solver.DH_H2O * solver.NA_ / 1e3
    ok = record("solver_v0 DH_H2O x N_A [kJ/mol]", exp, got, "±1e-9 rel",
                src(locked, "dHf_H2O_gas_kJ_per_mol"), ok=abs(dv.rel(got, exp)) <= 1e-9)
    assert ok, f"solver uses {got} kJ/mol, docs say {exp} kJ/mol"
