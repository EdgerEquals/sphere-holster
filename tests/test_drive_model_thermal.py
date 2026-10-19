"""drive_model.js thermal network: zero heat sources must give exactly zero rise above the seal temperature.

The network is solved for theta = T - T_seal, so with no discharge energy (and ambient = seal) the right-hand side
is exactly zero and every node stays at exactly T_seal (no rounding wander on the ~293 K baseline).

Electrodes were removed 2026-10-19 and no drive mechanism is defined: the drive stub must fail closed (zero deposited
energy, zero ring amplitude, NO_DRIVE flag) for every fill. The former ionising control row went with the removed electrodes."""
import json
import shutil
import subprocess

import pytest

NODE = shutil.which("node")

JS = r"""
const D = require(process.argv[1]);
const base = { ID_mm: 1, OD_mm: 2, T_seal: 293.15, shellModes: [{ name: "0S0 breathing (l=0)", f: 1.868e6 }] };
const out = [];
for (const [fill, f] of [[10, 1000], [0.1, 1000], [179, 1000], [7600, 1000], [22, 1000]]) {
  const r = D.run(Object.assign({}, base, { fill_Torr: fill, f }), { ncyc: 200, nlog: 40 });
  const off = r.tr.Tg.concat(r.tr.Twin, r.tr.Twout).filter(x => x !== base.T_seal).length;
  const ringMax = Math.max(0, ...r.ring.map(m => Math.abs(m.amp)));
  out.push({ fill, E: r.E_dis, dTg: r.dTg, dTw: r.dTw, off, ringMax, noDrive: r.flags.some(x => x === D.NO_DRIVE || String(x).includes("no drive mechanism defined")) });
}
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_zero_source_gives_exactly_zero_rise(root, record):
    res = subprocess.run([NODE, "-e", JS, str(root / "drive_model.js")], capture_output=True, text=True, check=True)
    rows = json.loads(res.stdout)
    for r in rows:
        ok = r["E"] == 0 and r["dTg"] == 0 and r["dTw"] == 0 and r["off"] == 0
        record(f"drive model zero-source rise, fill {r['fill']} Torr (E, dT_gas, dT_wall, nodes off T_seal)",
               "0, 0, 0, 0", f"{r['E']}, {r['dTg']}, {r['dTw']}, {r['off']}", "exact", "drive_model.js run()", ok=ok)
        assert ok, r


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_no_drive_stub_fails_closed(root):
    res = subprocess.run([NODE, "-e", JS, str(root / "drive_model.js")], capture_output=True, text=True, check=True)
    for r in json.loads(res.stdout):
        assert r["E"] == 0 and r["ringMax"] == 0 and r["noDrive"], r
