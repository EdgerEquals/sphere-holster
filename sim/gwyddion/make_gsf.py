"""Write a tiny Gwyddion Simple Field (.gsf) height map with a known answer.

z(x, y) = A sin(2 pi * kx * i / XRes)  (integer number of periods along x)
=> mean 0, RMS roughness Sq = A / sqrt(2) exactly on the sampled grid.
"""
import math
import struct
import sys

XRES, YRES = 64, 32
XREAL, YREAL = 6.4e-6, 3.2e-6       # 6.4 um x 3.2 um
A, KX = 5.0e-9, 4                    # 5 nm amplitude, 4 periods

out = sys.argv[1] if len(sys.argv) > 1 else "test.gsf"
hdr = ("Gwyddion Simple Field 1.0\n"
       f"XRes = {XRES}\nYRes = {YRES}\nXReal = {XREAL}\nYReal = {YREAL}\n"
       "XYUnits = m\nZUnits = m\nTitle = sine height map\n").encode()
hdr += b"\0" * (4 - len(hdr) % 4)    # NUL padding to a multiple of 4 bytes
data = [A * math.sin(2 * math.pi * KX * i / XRES) for j in range(YRES) for i in range(XRES)]
with open(out, "wb") as f:
    f.write(hdr)
    f.write(struct.pack(f"<{len(data)}f", *data))
print(f"wrote {out}: {XRES}x{YRES}, expected Sq = {A / math.sqrt(2):.6e} m")
