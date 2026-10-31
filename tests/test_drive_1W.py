"""Opt-in domain drive (drive_W): each of thermal / electric / magnetic / acoustic can take 1 W.
Default drive_W=0 keeps the zero-run acceptance rule. Frequencies come from the computed l=0 mode list
in the solver acoustic window FMIN_HZ–FMAX_HZ (DRIVE_AC_SPLIT = equal across N modes). Electrodes stay retired."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import solver_v0 as S  # noqa: E402


@pytest.fixture
def pre():
    return next(p for p in S.PRESETS if p["id"] == "base5")


def test_drive_off_is_exact_zero_run(pre):
    run = S.run_case(pre, {}, drive_W=0.0)
    assert run["W_ac"] == 0.0 and run["P_gas"] == 0.0
    assert all(m["W"] == 0.0 for m in run["ac"]["modes"])
    assert np.all(run["Tss"] == S.T_REF) and np.all(run["E_ss"] == 0.0)
    assert float(np.sum(run["q"])) == 0.0
    assert run["drive"]["drive_W"] == 0.0 and run["drive"]["n_modes_driven"] >= 0


def test_acoustic_1W_equal_split_uses_geometry_modes(pre):
    run = S.run_case(pre, {}, drive_W=1.0)
    d = run["drive"]
    assert d["drive_W"] == 1.0
    assert d["n_modes_driven"] == len(run["m_bond"]) > 0
    assert d["f_Hz"] == [round(f, 1) for f in sorted(run["m_bond"])]
    # no hardcoded 2 MHz target: every drive frequency is a computed bonded mode in the window
    assert all(S.DRIVE_WINDOW_Hz[0] <= f <= S.DRIVE_WINDOW_Hz[1] for f in run["m_bond"])
    assert "equal across N" in d["ac_split"]
    assert S.DRIVE_THERMAL_ENVELOPE_Hz == 1.0  # slow envelope modulating drives; not marched as an acoustic mode
    assert d["P_src_per_mode_W"] == pytest.approx(1.0 / d["n_modes_driven"])
    # steady W_n = P_src * Q / omega; sum of bonded mode energies > 0
    modes = run["ac_bond"]["modes"]
    assert run["W_ac"] == pytest.approx(sum(m["W"] for m in modes), rel=1e-9)
    assert run["W_ac"] > 0.0
    P_n = d["P_src_per_mode_W"]
    for m in modes:
        assert m["W"] == pytest.approx(P_n * m["Q_eff"] / (2 * math.pi * m["f"]), rel=1e-6)


def test_thermal_electric_magnetic_each_take_1W(pre):
    run = S.run_case(pre, {}, drive_W=1.0)
    # thermal: 1 W into the gas/inner-wall channel
    assert run["P_gas"] == pytest.approx(1.0)
    # magnetic placeholder: 1 W in the ferrite [est]
    assert float(np.sum(run["q_mag"])) == pytest.approx(1.0)
    assert abs(run["heat_by_layer"].get("ferrite", 0.0)) > 0.0 or float(np.sum(run["q_mag"])) == 1.0
    # electric: J_src sized for 1 W ohmic in BTO; field non-zero at end of march
    assert float(np.max(np.abs(run["J_drive"]))) > 0.0
    assert float(np.max(np.abs(run["E_ss"]))) > 0.0
    # electrodes still retired
    assert "retired" in run["drive"]["electrodes"]
    assert "ferrite heat-equivalent" in run["drive"]["magnetic_note"]


def test_drive_helpers_zero_when_off():
    assert S.drive_mode_P_src([1e6, 2e6], 0.0) == []
    assert S.drive_mode_P_src([1e6, 2e6], 1.0) == [0.5, 0.5]
    assert S.steady_mode_W(1e6, 100.0, 0.0) == 0.0
    assert S.steady_mode_W(1e6, 100.0, 1.0) == pytest.approx(100.0 / (2 * math.pi * 1e6))


def test_acoustic_window_is_1Hz_to_50MHz():
    assert S.FMIN_HZ == 1.0 and S.FMAX_HZ == 50e6 and S.N_FREQ_GRID == 20000
    assert S.DRIVE_WINDOW_Hz == (S.FMIN_HZ, S.FMAX_HZ)
    import geometry_sweep_v0 as G
    assert G.FMIN == S.FMIN_HZ and G.FMAX == S.FMAX_HZ and G.NGRID == S.N_FREQ_GRID
