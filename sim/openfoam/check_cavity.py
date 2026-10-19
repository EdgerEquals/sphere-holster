"""Sanity checks on the icoFoam lid-driven cavity run (Re = 10, lid U = 1 m/s).

- solver ran to the tutorial end time (0.5 s) and printed "End"
- final Ux / p initial residuals below 1e-4 (flow has reached steady state)
- continuity error (sum local) below 1e-7
- max |U| in the interior < lid speed (1 m/s) and > 0.1 m/s (a vortex exists)
- 400 cells (20 x 20 blockMesh)
"""
import math
import os
import re
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
from summary import Report  # noqa: E402

out = os.path.join(here, "out")
case = os.path.join(out, "cavity")
ver = dict(l.strip().split("=", 1) for l in open(os.path.join(out, "version.txt")) if "=" in l)
rep = Report(f"OpenFOAM v{ver.get('OPENFOAM_VERSION', '?')}", out)
log = open(os.path.join(case, "log.icoFoam")).read()
rep.check("icoFoam finished (End printed)", True, log.rstrip().endswith("End") or "\nEnd" in log, ok=("\nEnd" in log), note="log contains End")
last = open(os.path.join(out, "last_time.txt")).read().strip()
rep.check("final time directory [s]", 0.5, float(last), abs_tol=1e-9)
ux = [float(x) for x in re.findall(r"Solving for Ux, Initial residual = ([\d.eE+-]+)", log)]
pr = [float(x) for x in re.findall(r"Solving for p, Initial residual = ([\d.eE+-]+)", log)]
cont = [float(x) for x in re.findall(r"sum local = ([\d.eE+-]+)", log)]
rep.check("final Ux initial residual < 1e-4", "<1e-4", ux[-1] if ux else None, ok=bool(ux) and ux[-1] < 1e-4, note="steady state")
rep.check("final p initial residual < 1e-4", "<1e-4", pr[-1] if pr else None, ok=bool(pr) and pr[-1] < 1e-4, note="steady state")
rep.check("final continuity error (sum local) < 1e-7", "<1e-7", cont[-1] if cont else None, ok=bool(cont) and cont[-1] < 1e-7, note="mass conservation")

utxt = open(os.path.join(case, last, "U")).read()
body = utxt.split("internalField", 1)[1]
n = int(re.search(r"\n(\d+)\s*\n\(", body).group(1))
vecs = re.findall(r"\(([-\d.eE+]+) ([-\d.eE+]+) ([-\d.eE+]+)\)", body)[:n]
mags = [math.sqrt(float(a) ** 2 + float(b) ** 2 + float(c) ** 2) for a, b, c in vecs]
rep.check("cell count (20x20 mesh)", 400, n, abs_tol=0)
umax = max(mags)
rep.check("max interior |U| < lid speed 1 m/s and > 0.1", "(0.1, 1.0)", round(umax, 6), ok=0.1 < umax < 1.0, note="driven-cavity vortex")
rep.finish()
