"""MEEP smoke test: 2D rectangular metal (PEC) cavity, Ez (TM) modes.

Cell a x b with MEEP's default metallic boundaries (no PML). Analytic TM_mn
frequencies in MEEP units (c = 1):  f_mn = 0.5 * sqrt((m/a)^2 + (n/b)^2).
A broadband Ez point source excites the cavity; Harminv must find TM11 and
TM21 within 0.5 % of analytic, with high Q (lossless cavity).
"""
import math
import os
import sys

import meep as mp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from summary import Report  # noqa: E402

rep = Report(f"MEEP {mp.__version__}", os.path.join(os.path.dirname(__file__), "out"))

a, b = 1.0, 0.8
res = 40
f11 = 0.5 * math.sqrt((1 / a) ** 2 + (1 / b) ** 2)
f21 = 0.5 * math.sqrt((2 / a) ** 2 + (1 / b) ** 2)
fcen, df = 0.5 * (f11 + f21), 1.2 * (f21 - f11) + 0.2

sim = mp.Simulation(
    cell_size=mp.Vector3(a, b),
    resolution=res,
    boundary_layers=[],
    sources=[mp.Source(mp.GaussianSource(fcen, fwidth=df), component=mp.Ez,
                       center=mp.Vector3(-0.17 * a, 0.11 * b))],
)
h = mp.Harminv(mp.Ez, mp.Vector3(0.21 * a, -0.13 * b), fcen, df)
sim.run(mp.after_sources(h), until_after_sources=300)

modes = sorted(h.modes, key=lambda m: m.freq)
print("Harminv modes:", [(round(m.freq, 6), round(m.Q, 1), abs(m.amp)) for m in modes])


def nearest(f):
    if not modes:
        return float("nan"), 0.0
    pool = [m for m in modes if abs(m.Q) > 1e3] or modes   # ignore low-Q fitting artefacts
    m = min(pool, key=lambda m: abs(m.freq - f))
    return m.freq, m.Q


for label, fa in (("TM11", f11), ("TM21", f21)):
    fg, Q = nearest(fa)
    rep.check(f"{label} frequency (c/a units), a={a}, b={b}, res={res}", round(fa, 6), round(fg, 6), rel_tol=5e-3)
    rep.check(f"{label} Q > 1e4 (lossless PEC cavity)", ">1e4", round(Q, 1), ok=(abs(Q) > 1e4), note="|Q| > 1e4")
rep.finish()
