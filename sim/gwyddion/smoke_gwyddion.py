"""Gwyddion smoke test.

Generates a .gsf height map with a known RMS roughness, loads it with
Gwyddion's own file-module stack (compiled gwy_check.c against
libgwyddion20-dev) and asserts dimensions, physical size and the RMS that
Gwyddion's libprocess computes.
"""
import math
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
from summary import Report  # noqa: E402

out = os.path.join(here, "out")
os.makedirs(out, exist_ok=True)
gsf = os.path.join(out, "test.gsf")
subprocess.run([sys.executable, os.path.join(here, "make_gsf.py"), gsf], check=True)
exe = os.environ.get("GWY_CHECK", os.path.join(out, "gwy_check"))
p = subprocess.run([exe, gsf], capture_output=True, text=True)
print(p.stdout)
print(p.stderr, file=sys.stderr)
vals = dict(l.split("=", 1) for l in p.stdout.splitlines() if "=" in l)
rep = Report(f"Gwyddion {vals.get('GWY_VERSION', '?')}", out)
rep.check("gwy_file_load exit status", 0, p.returncode, abs_tol=0)
rep.check("file module detected", "gsffile", vals.get("DETECTED_MODULE"), ok=vals.get("DETECTED_MODULE") == "gsffile", note="exact (Gwyddion GSF loader)")
rep.check("XRes", 64, int(vals.get("XRES", -1)), abs_tol=0)
rep.check("YRes", 32, int(vals.get("YRES", -1)), abs_tol=0)
rep.check("XReal [m]", 6.4e-6, float(vals.get("XREAL", "nan")), rel_tol=1e-9)
rep.check("YReal [m]", 3.2e-6, float(vals.get("YREAL", "nan")), rel_tol=1e-9)
rep.check("RMS roughness Sq = A/sqrt(2) [m]", 5.0e-9 / math.sqrt(2), float(vals.get("RMS", "nan")), rel_tol=1e-5)
rep.check("mean height [m]", 0.0, float(vals.get("MEAN", "nan")), abs_tol=1e-15)
rep.finish()
