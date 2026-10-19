// node drive_model_run.js > drive_model_output.txt : example runs of the coupled single-cycle drive model (inputs are EXAMPLES, not design choices)
const D = require("./drive_model.js");
const shell = [{ name: "0S0 breathing (l=0)", f: 1.868e6 }, { name: "1S0-type (l=0, n=2)", f: 6.737e6 }, { name: "0S2", f: 1.243e6, tag: "calc minimal_test" }];
const base = { ID_mm: 1, OD_mm: 2, T_seal: 293.15, shellModes: shell };   // T_amb (ambient air K) unset => ambient = T_seal
const e = x => x.toExponential(3);
console.log("v0 coupled single-cycle drive model - ESTIMATED PHYSICS. Geometry 1 mm ID x 2 mm OD bare crystal quartz, HHO 2:1, sealed at 293.15 K.");
console.log("Example inputs only (fill, ambient and frequency are OPEN user inputs; nothing here is a chosen design value).");
console.log("DRIVE: " + D.NO_DRIVE + ".");
console.log("Removed with the drive [retired 2026-10-19]: breakdown knee, ionisation window, energy per cycle, discharge heating, discharge chemistry, acoustic ring amplitudes.\n");
console.log(`HHO c(T) = sqrt(1.4 R T / 0.012011): 293 K ${D.cHHO(293).toFixed(1)} m/s, 400 K ${D.cHHO(400).toFixed(1)}, 773 K ${D.cHHO(773).toFixed(1)} m/s\n`);
for (const [fill, f, Tamb] of [[22, 1000], [22, 20], [22, 20000], [10, 1000], [100, 1000], [760, 1000], [22, 1000, 303.15], [22, 1000, 283.15]]) {
  const q = Object.assign({}, base, { fill_Torr: fill, f }); if (Tamb) q.T_amb = Tamb;
  const r = D.run(q);
  const gm = r.modes.find(m => m.name.startsWith("gas l=0 n=1"));
  const thEnd = r.tr.Tg[r.tr.Tg.length - 1] - base.T_seal;
  console.log(`fill ${fill} Torr (N ${e(r.N)}), f ${f} Hz (cycle ${e(1/f)} s), ambient ${r.T_amb} K: E/cycle ${e(r.E_dis)} J | dT_gas ${e(r.dTg)} K | dT_wall ${e(r.dTw)} K | gas theta at t_end ${e(thEnd)} K | p_max ${e(r.p_max)} Pa | gas l0 ${(gm.f/1e3).toFixed(1)} kHz Q ${gm.Q.toFixed(1)} | ring gas ${e(r.ring.find(z=>z.name.startsWith('gas l=0 n=1')).amp)} Pa, shell ${e(r.ring.find(z=>z.name.indexOf('0S0') >= 0).amp)} Pa | corners ${r.modes.filter(m=>m.domain==='thermal').map(m=>m.f.toPrecision(3)+' Hz').join(', ')} | chem heat ${e(r.chem.E_release)} J`);
}
console.log("\nSweep drive f (fill 22 Torr):");
D.sweep(Object.assign({}, base, { fill_Torr: 22 }), "f", D.logspace(20, 20000, 7)).forEach(p => console.log(`  f ${p.x.toPrecision(4)} Hz: E ${e(p.E_dis)} J, dT_gas ${e(p.dTg)} K, dT_wall ${e(p.dTw)} K, ring gas ${e(p.ringGas)} Pa, shell ${e(p.ringShell)} Pa`));
console.log("\nSweep fill (f 1 kHz):");
D.sweep(Object.assign({}, base, { f: 1000 }), "fill_Torr", D.logspace(0.1, 7600, 13)).forEach(p => console.log(`  fill ${p.x.toPrecision(3)} Torr: E ${e(p.E_dis)} J, dT_gas ${e(p.dTg)} K, gas l0 ${(p.fgas/1e3).toFixed(1)} kHz`));
