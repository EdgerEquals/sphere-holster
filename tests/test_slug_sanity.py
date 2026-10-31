"""Ferrite Slug sanity: first longitudinal resonance from the finite-element bar vs the textbook
free-free formula f_1 = v / (2 L), v = sqrt(E / rho)."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slug"))
import model as S


def test_f1_matches_textbook():
    L = S.GEOM["length_mm"] * 1e-3
    f1_book = math.sqrt(S.mat("E") / S.mat("rho")) / (2 * L)
    f_fe, _ = S.fe_modes(n_modes=3)
    assert abs(f_fe[0] - f1_book) / f1_book < 1e-3


def test_overtones_are_integer_ratios():
    f_fe, _ = S.fe_modes(n_modes=3)
    assert abs(f_fe[1] / f_fe[0] - 2) < 2e-3 and abs(f_fe[2] / f_fe[0] - 3) < 2e-3


def test_centre_mount_on_odd_mode_nodes():
    d = S.run(n_modes=4)
    assert [m["node_at_mount"] for m in d["modes"]] == [True, False, True, False]


def test_bias_zero_gives_no_linear_coupling():
    d, m = S.strain_coeff(0.0)
    assert d == 0.0 and m == 0.0


def test_material_values_are_marked_placeholders():
    src = open(S.__file__).read()
    assert "ALL PLACEHOLDERS" in src and S.T_OP_K > 200   # kelvin internally
