"""Geometry x fill-state sweep (geometry_fill_sweep_v0.py, opt-in): fill axis, mix-consistent gas, defaults untouched."""
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


def test_fill_axis_values():
    assert F.P_AXIS == [0.382, 0.618, 1.0, 1.618, 2.618]
    assert F.X_AXIS[1] == pytest.approx(2 / 3) and [round(x, 2) for x in F.X_AXIS] == [0.5, 0.67, 0.75, 0.8]
    assert F.comp_of(0.75) == {"H2": 0.75, "O2": 0.25}
    n_geo = 1
    for v in F.GEO_SUB.values(): n_geo *= len(v)
    assert n_geo == 48 and n_geo * len(F.P_AXIS) * len(F.X_AXIS) == 960


def test_mix_sound_speed_drives_B_modes_and_gas_Q(vrh):
    comp = F.comp_of(0.8); p = 0.618
    r = G.evaluate(1.5, 1.0, 5.0, details=True, p_atm=p, comp=comp)
    gp = S.gas_props(S.T_REF, p * 101325.0, comp)
    a = S.build_stack(3.0, 1.0)["r_in"]
    assert r["c_gas"] == pytest.approx(gp["c"], rel=1e-5)
    assert r["modes_Hz"]["B"] == pytest.approx([round(f, 1) for f in G.gas_rigid_l0(a, gp["c"])], abs=0.2)
    f0 = r["modes_Hz"]["B"][0]
    assert r["gas_Q_first"] == pytest.approx(S.gas_Q(f0, a, p * 101325.0, S.T_REF, comp), rel=1e-3)
    # the override is temporary: the solver's own gas_Z and 1 atm are back afterwards
    assert S.gas_Z.__module__ == "solver_v0" and S.GAS["p"] == 101325.0 and S.GAS["T"] == S.T_REF


def test_default_evaluate_unchanged_by_the_fill_option(vrh):
    a = G.evaluate(1.5, 1.0, 5.0)
    assert a["c_gas"] == pytest.approx(S.c_hho(S.T_REF), abs=1e-3)
    d = json.loads((ROOT / "geometry_sweep_v0.json").read_text(encoding="utf-8"))["base5"]
    for k in ("score", "n_mode_locks", "n_reflection_locks", "n_sharp_locks", "n_modes_window"):
        assert a[k] == d[k]


def test_fill_sweep_output_structure():
    d = json.loads((ROOT / "geometry_fill_sweep_v0.json").read_text(encoding="utf-8"))
    m = d["meta"]
    assert m["n_total"] == len(d["results"]) == m["n_coarse"] + m["n_refine"] and m["n_coarse"] == 960
    assert m["n_total"] <= 1200 and m["T_K"] == 293.0
    assert sorted(r["rank_spm"] for r in d["results"]) == list(range(1, m["n_total"] + 1))
    assert sorted(r["rank"] for r in d["results"]) == list(range(1, m["n_total"] + 1))
    spm = [r["sharp_per_mode"] for r in d["top10_spm"]]
    assert spm == sorted(spm, reverse=True)
    assert len(d["fill_best"]) == 20 and all(c["n"] >= 48 for c in d["fill_best"])
    b = d["base5_1atm_HHO"]
    assert (b["a_mm"], b["w_mm"], b["t2_um"], b["p_atm"]) == (1.5, 1.0, 5.0, 1.0)
