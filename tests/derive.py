"""Symbolic (SymPy) derivations of locked values. Kept separate from solver_v0.py so the tests are independent."""
from __future__ import annotations

import functools
import math

import numpy as np
import sympy as sp
from scipy.optimize import brentq

R_CODATA = sp.Rational("8.314462618")       # J/(mol K) [lit CODATA 2018, exact]
M_H, M_O = sp.Rational("1.008"), sp.Rational("15.999")   # g/mol [lit IUPAC standard atomic weights]


@functools.lru_cache(maxsize=None)
def shell_l0_determinant():
    """Characteristic determinant D(f, a, b, cL, cT) for radial (l=0) modes of a traction-free isotropic shell a<r<b.

    u_r(r) = A j1(kr) + B y1(kr), k = 2 pi f / cL
    sigma_rr = (lambda + 2 mu) du/dr + 2 lambda u / r, lambda + 2mu = rho cL^2, lambda = rho (cL^2 - 2 cT^2)
    sigma_rr(a) = sigma_rr(b) = 0  ->  det = 0   (rho cancels)
    """
    r, k, a, b, cL, cT, f = sp.symbols("r k a b c_L c_T f", positive=True)
    j1 = sp.expand_func(sp.jn(1, k * r))
    y1 = sp.expand_func(sp.yn(1, k * r))
    lam, m = cL**2 - 2 * cT**2, cL**2
    srr = lambda u: m * sp.diff(u, r) + 2 * lam * u / r  # noqa: E731
    D = sp.Matrix([[srr(j1).subs(r, a), srr(y1).subs(r, a)],
                   [srr(j1).subs(r, b), srr(y1).subs(r, b)]]).det()
    D = sp.simplify(D.subs(k, 2 * sp.pi * f / cL))
    return D, (f, a, b, cL, cT)


def shell_l0_modes(a_m: float, b_m: float, cL: float, cT: float, fmin: float = None, fmax: float = None, n: int = None) -> list[float]:
    import solver_v0 as S
    fmin = S.FMIN_HZ if fmin is None else fmin
    fmax = S.FMAX_HZ if fmax is None else fmax
    n = S.N_FREQ_GRID if n is None else n
    D, syms = shell_l0_determinant()
    g = sp.lambdify(syms, D, "numpy")
    h = lambda x: float(g(x, a_m, b_m, cL, cT))  # noqa: E731
    fs = np.linspace(fmin, fmax, n)
    vals = [h(x) for x in fs]
    out = []
    for i in range(n - 1):
        if np.sign(vals[i]) != np.sign(vals[i + 1]):
            out.append(brentq(h, fs[i], fs[i + 1], xtol=1e-3))
    return out


def hho_sound_speed(T: float = 293.0, gamma: float = 1.40):
    g, R, T_, M = sp.symbols("gamma R T M", positive=True)
    c = sp.sqrt(g * R * T_ / M)
    M_val = (2 * (2 * M_H) + 2 * M_O) / 3 / 1000            # kg/mol, 2 H2 : 1 O2
    return c, float(c.subs({g: sp.Rational(str(gamma)), R: R_CODATA, T_: T, M: M_val}).evalf(15)), float(M_val * 1000)


def slab_thickness_mode(t: float, cL: float):
    """Half-wave plate estimate f = cL / (2 t); also returns the cL implied by a target f."""
    f, c, t_ = sp.symbols("f c_L t", positive=True)
    eq = sp.Eq(f, c / (2 * t_))
    return eq, float(sp.solve(eq, f)[0].subs({c: cL, t_: t})), (lambda f_t: float(sp.solve(eq, c)[0].subs({f: f_t, t_: t})))


def rel(got: float, exp: float) -> float:
    return (got - exp) / exp if exp else math.inf
