"""Assert the Code_Aster cantilever result and (if present) forma01a status."""
import os
import re
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
from summary import Report  # noqa: E402

out = os.path.join(here, "out")
ver = open(os.path.join(out, "version.txt")).read() if os.path.exists(os.path.join(out, "version.txt")) else ""
m = re.search(r"(\d+\.\d+\.\d+)", ver)
rep = Report(f"Code_Aster {m.group(1) if m else '?'}", out)
st = dict(l.strip().split("=", 1) for l in open(os.path.join(out, "status.txt")) if "=" in l)
rep.check("run_aster cantilever exit status", 0, int(st.get("CANTILEVER_RC", -1)), abs_tol=0)
dy = float("nan")
tip = os.path.join(out, "tip.txt")
if os.path.exists(tip):
    mm = re.search(r"TIP_DY=(\S+)", open(tip).read())
    dy = float(mm.group(1)) if mm else dy
delta = 100.0 * 200.0 ** 3 / (3 * 210000.0 * (10.0 ** 4 / 12))
rep.check("POU_D_E tip DY [mm] vs -PL^3/(3EI)", round(-delta, 6), dy, rel_tol=1e-4)
f = st.get("FORMA01A_RC", "absent")
if f != "absent":
    rep.check("bundled verification test forma01a", 0, int(f), abs_tol=0)
else:
    print("forma01a test suite not shipped in this image; skipped (not a failure)")
rep.finish()
