"""Geometry x rarefied-pressure sweep (geometry_fill_sweep_v0.py, opt-in): HHO 2:1 fixed, ambient-referenced log-even
rarefied pressure grid, mix-consistent gas, defaults untouched."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import solver_v0 as S  # noqa: E402
import geometry_sweep_v0 as G  # noqa: E402
import geometry_fill_sweep_v0 as F  # noqa: E402


@pytest.fixture
def vrh():
    """The sweeps run with --qz-sound vrh; switch for the test and restore the module state afterwards."""
    old = S.QZ_SOUND_SEL; tags = S.MAT["quartz"]["tags"]; cl, ct = S.MAT["quartz"]["cL"], S.MAT["quartz"]["cT"]
    S.set_qz_sound("vrh")
    yield
    S.QZ_SOUND_SEL = old; S.MAT["quartz"].update(tags=tags, cL=cl, cT=ct)


def test_rarefied_pressure_grid_and_fixed_hho_mix():
    f = F.P_FACTORS
    assert len(f) == 9 and f[0] == pytest.approx(0.05) and f[-1] == pytest.approx(0.95)
    assert all(x < 1.0 for x in f)                                                   # fully rarefied
    r = [f[i + 1] / f[i] for i in range(8)]
    assert max(r) == pytest.approx(min(r), rel=1e-9)                                  # log-even
    assert not any(abs(x / G.PHI - 1) < 0.01 or abs(x * G.PHI - 1) < 0.01 for x in f)  # no golden-ratio point
    assert F.COMP == {"H2": pytest.approx(2 / 3), "O2": pytest.approx(1 / 3)}
    for name in ("X_AXIS", "comp_of", "X_AXIS_HHO"):                                   # off-spec mixes removed
        assert not hasattr(F, name)
    n_geo = 1
    for v in F.GEO_SUB.values(): n_geo *= len(v)
    assert n_geo == 48
    assert F.p_abs_Pa(3, p_ambient=100000.0) == pytest.approx(f[3] * 100000.0)


def test_ambient_T_and_p_drive_B_modes_and_gas_Q(vrh):
    p_Pa, T = 0.2179 * 99000.0, 300.0
    r = G.evaluate(1.5, 1.0, 5.0, details=True, p_atm=p_Pa / 101325.0, comp=F.COMP, T_K=T)
    gp = S.gas_props(T, p_Pa, F.COMP)
    a = S.build_stack(3.0, 1.0)["r_in"]
    assert r["c_gas"] == pytest.approx(gp["c"], rel=1e-5)
    assert r["modes_Hz"]["B"] == pytest.approx([round(x, 1) for x in G.gas_rigid_l0(a, gp["c"])], abs=0.2)
    f0 = r["modes_Hz"]["B"][0]
    assert r["gas_Q_first"] == pytest.approx(S.gas_Q(f0, a, p_Pa, T, F.COMP), rel=1e-3)
    # the override is temporary: the solver's own gas_Z, 1 atm and 293 K are back afterwards
    assert S.gas_Z.__module__ == "solver_v0" and S.GAS["p"] == 101325.0 and S.GAS["T"] == S.T_REF


def test_default_evaluate_unchanged_by_the_fill_option(vrh):
    a = G.evaluate(1.5, 1.0, 5.0)
    assert a["c_gas"] == pytest.approx(S.c_hho(S.T_REF), abs=1e-3)
    d = json.loads((ROOT / "geometry_sweep_v0.json").read_text(encoding="utf-8"))["base5"]
    for k in ("score", "n_mode_locks", "n_reflection_locks", "n_sharp_locks", "n_modes_window"):
        assert a[k] == d[k]


def test_rarefied_sweep_output_structure():
    d = json.loads((ROOT / "geometry_rarefied_hho_sweep_v0.json").read_text(encoding="utf-8"))
    m = d["meta"]
    assert m["n_total"] == len(d["results"]) == m["n_coarse"] + m["n_refine"] and m["n_coarse"] == 432
    assert m["n_total"] <= 1200 and "p_ambient_Pa" in m and "T_ambient_K" in m
    assert m["p_factors"] == [round(x, 4) for x in F.P_FACTORS] and all(x < 1 for x in m["p_factors"])
    assert m["mix"]["H2"] == pytest.approx(2 / 3, abs=1e-6)
    assert all(r["p_Pa"] < m["p_ambient_Pa"] and r["x_H2"] == pytest.approx(0.6667) for r in d["results"])
    assert sorted(r["rank_spm"] for r in d["results"]) == list(range(1, m["n_total"] + 1))
    spm = [r["sharp_per_mode"] for r in d["top10_spm"]]
    assert spm == sorted(spm, reverse=True)
    assert len(d["pressure_best"]) == 9 and all(c["n"] >= 48 for c in d["pressure_best"])
