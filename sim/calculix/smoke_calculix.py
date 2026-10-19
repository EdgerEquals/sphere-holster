"""CalculiX smoke test: cantilever tip deflection vs Euler-Bernoulli.

Steel cantilever, L = 200 mm, 10 x 10 mm square section, E = 210 GPa,
nu = 0.3, tip load P = 100 N. Analytic tip deflection
    delta = P L^3 / (3 E I),  I = b h^3 / 12   ->  1.52381 mm.
Meshed with 20 quadratic B32 beam elements (CalculiX expands them to C3D20R
bricks internally, so this exercises the solid solver; Timoshenko shear
adds ~0.2 % at L/h = 20). Tolerance 2 %.
"""
import os
import re
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
from summary import Report  # noqa: E402

out = os.path.join(here, "out")
os.makedirs(out, exist_ok=True)
L, b, h, E, nu, P, NEL = 200.0, 10.0, 10.0, 210000.0, 0.3, 100.0, 20
I = b * h ** 3 / 12
delta = P * L ** 3 / (3 * E * I)
nn = 2 * NEL + 1
lines = ["*HEADING", "Cantilever smoke test", "*NODE, NSET=NALL"]
lines += [f"{i + 1}, {L * i / (nn - 1):.6f}, 0.0, 0.0" for i in range(nn)]
lines += ["*ELEMENT, TYPE=B32, ELSET=EALL"]
lines += [f"{e + 1}, {2 * e + 1}, {2 * e + 2}, {2 * e + 3}" for e in range(NEL)]
lines += [
    "*NSET, NSET=FIX", "1", f"*NSET, NSET=TIP", f"{nn}",
    "*MATERIAL, NAME=STEEL", "*ELASTIC", f"{E}, {nu}",
    "*BEAM SECTION, ELSET=EALL, MATERIAL=STEEL, SECTION=RECT", f"{b}, {h}", "0.0, 0.0, 1.0",
    "*BOUNDARY", "FIX, 1, 6",
    "*STEP", "*STATIC",
    "*CLOAD", f"TIP, 2, {-P}",
    "*NODE PRINT, NSET=TIP", "U",
    "*END STEP",
]
inp = os.path.join(out, "cantilever.inp")
open(inp, "w").write("\n".join(lines) + "\n")
ccx = os.environ.get("CCX", "ccx")
p = subprocess.run([ccx, "-i", "cantilever"], cwd=out, capture_output=True, text=True)
print(p.stdout[-3000:])
print(p.stderr[-2000:], file=sys.stderr)
ver = re.search(r"Version\s+([\d.]+)", p.stdout)
rep = Report(f"CalculiX {ver.group(1) if ver else '?'}", out)
rep.check("ccx exit status", 0, p.returncode, abs_tol=0)
uy = float("nan")
dat = os.path.join(out, "cantilever.dat")
if os.path.exists(dat):
    txt = open(dat).read()
    print(txt)
    m = re.search(rf"^\s*{nn}\s+(\S+)\s+(\S+)\s+(\S+)", txt.split("displacements")[-1], re.M)
    if m:
        uy = float(m.group(2))
rep.check("tip deflection uy [mm] vs -PL^3/(3EI)", round(-delta, 6), uy, rel_tol=0.02)
rep.finish()
