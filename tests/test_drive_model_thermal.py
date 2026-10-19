"""drive_model.js thermal network: zero heat sources must give exactly zero rise above the seal temperature.

The network is solved for theta = T - T_seal, so with no discharge energy (and ambient = seal) the right-hand side
is exactly zero and every node stays at exactly T_seal (no rounding wander on the ~293 K baseline)."""
import json
import shutil
import subprocess

import pytest

NODE = shutil.which("node")

JS = r"""
const D = require(process.argv[1]);
const base = { ID_mm: 1, OD_mm: 2, T_seal: 293.15, shellModes: [{ name: "0S0 breathing (l=0)", f: 1.868e6 }] };
const out = [];
for (const [fill, V, f] of [[10, 600, 1000], [0.1, 600, 1000], [179, 600, 1000], [7600, 600, 1000], [22, 600, 1000]]) {
  const r = D.run(Object.assign({}, base, { fill_Torr: fill, V_amp: V, f }), { ncyc: 200, nlog: 40 });
  const off = r.tr.Tg.concat(r.tr.Twin, r.tr.Twout).filter(x => x !== base.T_seal).length;
  out.push({ fill, E: r.E_dis, dTg: r.dTg, dTw: r.dTw, off });
}
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_zero_source_gives_exactly_zero_rise(root, record):
    res = subprocess.run([NODE, "-e", JS, str(root / "drive_model.js")], capture_output=True, text=True, check=True)
    rows = json.loads(res.stdout)
    for r in rows:
        if r["E"] == 0:
            ok = r["dTg"] == 0 and r["dTw"] == 0 and r["off"] == 0
            record(f"drive model zero-source rise, fill {r['fill']} Torr (dT_gas, dT_wall, nodes off T_seal)",
                   "0, 0, 0", f"{r['dTg']}, {r['dTw']}, {r['off']}", "exact", "drive_model.js run()", ok=ok)
            assert ok, r
        else:
            assert r["dTg"] > 0 and r["dTw"] > 0, r   # ionising control row still heats
    assert any(r["E"] == 0 for r in rows) and any(r["E"] > 0 for r in rows)
