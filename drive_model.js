/* drive_model.js - v0 coupled single-cycle drive model for the bare HHO / crystal-quartz bubble.
   ESTIMATED PHYSICS, NOT VALIDATED. Runs in the browser (window.DriveModel) and in node (module.exports).
   User sets: fill (HHO amount + sealing temperature), ambient temperature, geometry (ID, OD), drive frequency (ONE cycle).
   ELECTRODES REMOVED 2026-10-19 (Danny: electrodes were the wrong architecture). There is NO drive mechanism defined: the drive
   source is a fail-closed stub that deposits no energy. Breakdown, energy per cycle, discharge heating, chemistry from the
   discharge and acoustic ring-down are therefore all zero. The drive method is open for Danny; do not add one here.
   Computed (coupled) states: gas temperature T_g(t), pressure p = N k T_g / V, number density (fixed), HHO sound speed c(T_g),
   gas-cavity mode frequencies and Q, wall temperatures (rise above seal; ambient exchange), natural modes per domain.
   Tags: [lit] published, [rec] from another box report, [calc] computed here, [est] estimate / assumption / placeholder. */
(function (root) {
  "use strict";
  const kB = 1.380649e-23, NA = 6.02214076e23, R = 8.314462618, EPS0 = 8.8541878128e-12, SIG = 5.670374419e-8, C0 = 299792458, TORR = 133.322;
  const HHO = { M: (2 * 2.016 + 32.00) / 3 / 1000,  // [calc from lit molar masses] 12.01 g/mol
    gamma: 1.40,                                    // [est] diatomic mix near room T
    cp: 2423,                                       // J/kg/K [rec layer1_lock_phi_calc_output]
    k293: 0.1114,                                   // W/m/K [rec]
    mu293: 17.88e-6 };                              // Pa s [rec]
  const QZ = { k300: 6.2, rho: 2650, cp: 740, eps: 4.5, E: 86e9, nu: 0.17 };  // k [rec]; rho, cp, E, nu [lit-typical, isotropic est]; eps_r 4.5 [rec avg]
  // v0.3 crystal-quartz sound speeds (selectable; same table as solver_v0.py QZ_SOUND)
  const QZ_SOUND = {
    vrh: { cL: 6048, cT: 4090, label: "α-quartz isotropic VRH aggregate", src: "[lit] Schmitt 2015, Treatise on Geophysics 2nd ed., vol 11, Table 2 (ρ 2648, K 37.8, μ 44.3 GPa → 6048/4090 m/s); cf. Mavko et al., Rock Physics Handbook 6008/4075 m/s" },
    z: { cL: 6330, cT: 4685, label: "single crystal along Z (c-axis)", src: "[lit] cL 6.33 km/s Z-cut, J. Appl. Phys. 44, 5 (1973) doi:10.1063/1.1661916; cT = √(C44/ρ), C44 58.14 GPa [lit Ohno et al. 2006, doi:10.1063/1.2335684] [calc]" },
    x: { cL: 5710, cT: 5200, label: "single crystal along X", src: "[lit] X-cut cL 5.71, cT 5.20 km/s, J. Appl. Phys. 44, 5 (1973) doi:10.1063/1.1661916" },
    danny: { cL: 5900, cT: 4090, label: "Danny's value", src: "cL 5900 m/s [given by Danny]; cT 4090 m/s from the VRH entry [lit] (no shear value given)" },
    v0: { cL: 6153, cT: 4210, label: "v0/v0.2 value", src: "[rec shell_phi_sweep] superseded by the cited VRH entry" } };
  let QZ_SEL = "vrh";
  function setQuartzSound(k) { if (QZ_SOUND[k]) QZ_SEL = k; return QZ_SOUND[QZ_SEL]; }
  const BALMER = [["Hα", 656.28e-9], ["Hβ", 486.13e-9], ["Hγ", 434.05e-9], ["Hδ", 410.17e-9]];  // air wavelengths [lit NIST ASD]
  const VIS = [380e-9, 750e-9];  // visible band [lit-typical CIE range]
  const ETA = { gas: 0.6, wall: 0.3, opt: 0.1 };          // energy partition of a deposited drive energy [est placeholders]; unused while no drive is defined
  const SHELL_Q = 2100;                                   // [rec] used as placeholder for every shell mode
  const AUTOIGN_C = [500, 585];
  const NO_DRIVE = "no drive mechanism defined (electrodes removed 2026-10-19; drive method open): no breakdown, no deposited energy, no discharge heating or chemistry, no acoustic ring-down";
  const CH = { ED: 4.478 * 1.602176634e-19,   // H2 D0 [lit NIST CCCBDB]
    DH: 241.826e3 / 6.02214076e23,          // J per H2O formed (LHV, dHf H2O(g)) [lit NIST WebBook]
    eta: 0.2, nu: 1.0, D1atm: 1.5e-4 };      // dissociation share, chain length, H diffusivity at 1 atm [PLACEHOLDERS est]                           // HHO autoignition range [given by Danny; lit H2 ~500-585 C]
  const X_GAS = [ // rigid-wall acoustic roots of a gas sphere: j_l'(x)=0 [calc]
    { name: "gas l=1 n=1", l: 1, x: 2.0816 }, { name: "gas l=2 n=1", l: 2, x: 3.3421 }, { name: "gas l=0 n=1 (radial)", l: 0, x: 4.4934 },
    { name: "gas l=3 n=1", l: 3, x: 4.5141 }, { name: "gas l=1 n=2", l: 1, x: 5.9404 }, { name: "gas l=0 n=2 (radial)", l: 0, x: 7.7253 } ];

  const cHHO = T => Math.sqrt(HHO.gamma * R * T / HHO.M);           // ideal-gas sound speed [calc]; 533 m/s at 293 K
  const kGas = T => HHO.k293 * Math.pow(T / 293, 0.75);              // [est] T^0.75 scaling
  const muGas = T => HHO.mu293 * Math.pow(T / 293, 0.7);             // [est]
  const kQz = T => QZ.k300 * 300 / Math.max(T, 150);                 // [rec form] k ~ 1/T
  const j0 = x => (x === 0 ? 1 : Math.sin(x) / x);

  const sj1 = x => Math.sin(x) / (x * x) - Math.cos(x) / x, sy1 = x => -Math.cos(x) / (x * x) - Math.sin(x) / x;
  const sj1p = x => Math.sin(x) / x - 2 * sj1(x) / x, sy1p = x => -Math.cos(x) / x - 2 * sy1(x) / x;
  // free hollow elastic sphere, radial (l=0) modes: u = A j1(kr) + B y1(kr), sigma_rr = 0 at r = a and r = b [calc, gas loading neglected]
  function shellRadialModes(a, b, cL, cT, n) {
    const lam2 = 2 * (cL * cL - 2 * cT * cT);
    const S = (f, r, k) => cL * cL * k * (f === 0 ? sj1p(k * r) : sy1p(k * r)) + lam2 * (f === 0 ? sj1(k * r) : sy1(k * r)) / r;
    const det = w => { const k = w / cL; return S(0, a, k) * S(1, b, k) - S(1, a, k) * S(0, b, k); };
    const out = [], wmax = 2 * Math.PI * cL * (n + 2) / (b - a) + 4 * cL / b, N = 6000;
    let w0 = 1e-3 * wmax, d0 = det(w0);
    for (let i = 1; i <= N && out.length < n; i++) {
      const w1 = wmax * i / N, d1 = det(w1);
      if (isFinite(d0) && isFinite(d1) && d0 * d1 < 0) { let lo = w0, hi = w1, dl = d0; for (let j = 0; j < 60; j++) { const m = 0.5 * (lo + hi), dm = det(m); if (dl * dm <= 0) hi = m; else { lo = m; dl = dm; } } out.push(0.5 * (lo + hi) / (2 * Math.PI)); }
      w0 = w1; d0 = d1;
    }
    return out;
  }

  function natconvH(Ts, Ta, D) {           // Churchill sphere + radiation [lit correlation; air props est]
    const Tf = 0.5 * (Ts + Ta), k = 0.0263 * Math.pow(Tf / 300, 0.8), nu = 1.57e-5 * Math.pow(Tf / 300, 1.7), Pr = 0.71;
    const Ra = Math.max(9.81 / Tf * Math.abs(Ts - Ta) * D ** 3 / (nu * nu) * Pr, 0);
    const Nu = 2 + 0.589 * Math.pow(Ra, 0.25) / Math.pow(1 + Math.pow(0.469 / Pr, 9 / 16), 4 / 9);
    const hr = 0.9 * SIG * (Ts * Ts + Ta * Ta) * (Ts + Ta);   // eps 0.9 [est]
    return Nu * k / D + hr;
  }

  function geometry(p) {
    const a = p.ID_mm / 2e3, b = p.OD_mm / 2e3;
    const V = 4 / 3 * Math.PI * a ** 3;
    return { a, b, V };   // gas core radius a, quartz OD radius b, gas volume V (electrodes removed: no gap, no capacitance split)
  }

  // radial gas mode j0(x r/a): wall value and volume-average of j0^2 (used for the boundary-layer Q) [calc]
  function overlapRadial(g, x) {
    const N = 2000; let nrm = 0;
    for (let i = 0; i < N; i++) { const r = g.a * (i + 0.5) / N; nrm += j0(x * r / g.a) ** 2 * r * r * g.a / N; }
    const Vn = 3 * nrm / g.a ** 3;  // volume-average of j0^2
    return { jw: j0(x), Vn };
  }

  function gasModeQ(g, x, T, rho) {        // [est] thermal boundary layer + classical bulk losses (radial modes; rigid wall)
    const c = cHHO(T), f = x * c / (2 * Math.PI * g.a), w = 2 * Math.PI * f;
    const alpha = kGas(T) / (rho * HHO.cp), dT = Math.sqrt(2 * alpha / w);
    const o = overlapRadial(g, x), zeta = o.jw * o.jw / o.Vn;
    const Qth_inv = (HHO.gamma - 1) * dT * (3 / g.a) / 2 * zeta;
    const acl = w * w / (2 * rho * c ** 3) * (4 / 3 * muGas(T) + (HHO.gamma - 1) * kGas(T) / HHO.cp);
    const Qcl_inv = 2 * acl * c / w;
    return { f, Q: 1 / (Qth_inv + Qcl_inv) };
  }

  function naturalModes(p, state) {       // the system's own response frequencies at gas temperature T (computed state)
    const g = geometry(p), T = state.T, rho = state.N * HHO.M / NA / g.V, out = [];
    for (const m of X_GAS) {
      const c = cHHO(T), f = m.x * c / (2 * Math.PI * g.a);
      const q = m.l === 0 ? gasModeQ(g, m.x, T, rho) : { Q: null };
      out.push({ domain: "acoustic", name: m.name + " [calc rigid-wall, c(T)]", f, Q: q.Q, tag: "calc" });
    }
    { const qs = QZ_SOUND[QZ_SEL]; shellRadialModes(g.a, g.b, qs.cL, qs.cT, 3).forEach((f, i) => out.push({ domain: "acoustic", name: (i === 0 ? "shell 0S0 breathing (l=0)" : "shell l=0 n=" + (i + 1)) + " [calc free shell, quartz " + QZ_SEL + " cL " + qs.cL + "/cT " + qs.cT + "]", f, Q: SHELL_Q, tag: "calc" })); }
    for (const s of (p.shellModes || [])) out.push({ domain: "acoustic", name: "shell " + s.name + " [" + (s.tag || "calc") + "]", f: s.f, Q: SHELL_Q, tag: s.tag || "calc" });
    const alpha_g = kGas(T) / (rho * HHO.cp), tau_g = g.a ** 2 / (Math.PI ** 2 * alpha_g);
    const alpha_q = kQz(T) / (QZ.rho * QZ.cp), tau_w = (g.b - g.a) ** 2 / (Math.PI ** 2 * alpha_q);
    out.push({ domain: "thermal", name: "gas conduction relaxation 1/(2 pi tau_g) [calc]", f: 1 / (2 * Math.PI * tau_g), tau: tau_g });
    out.push({ domain: "thermal", name: "quartz wall diffusion 1/(2 pi tau_w) [calc]", f: 1 / (2 * Math.PI * tau_w), tau: tau_w });
    if (state.tauLumped) out.push({ domain: "thermal", name: "whole-bubble to still air 1/(2 pi C R_out) [calc]", f: 1 / (2 * Math.PI * state.tauLumped), tau: state.tauLumped });
    { const pse = state.N * kB * (state.Tseal || 293) / g.V, D = CH.D1atm * 101325 / Math.max(pse, 1), tD = g.a ** 2 / (Math.PI ** 2 * D);
      out.push({ domain: "chemical", name: "radical diffusion to wall 1/(2 pi tau_D) [calc; D placeholder]; knee: not defined", f: 1 / (2 * Math.PI * tD), tau: tD }); }
    out.push({ domain: "electric", name: "dielectric-sphere EM resonance ~ c x/(2 pi b sqrt(eps)) [est]", f: C0 * 2.0 / (2 * Math.PI * g.b * Math.sqrt(QZ.eps)) });
    out.push({ domain: "magnetic", name: "same EM resonance (B = 0: no drive mechanism defined) [est]", f: C0 * 2.0 / (2 * Math.PI * g.b * Math.sqrt(QZ.eps)) });
    out.push({ domain: "optical", name: "H-alpha 656.3 nm [lit]", f: C0 / 656.3e-9 }, { domain: "optical", name: "H-beta 486.1 nm [lit]", f: C0 / 486.1e-9 }, { domain: "optical", name: "H-gamma 434.0 nm [lit]", f: C0 / 434.0e-9 });
    return out;
  }

  /* run(p): p = {ID_mm, OD_mm, fill_Torr (at T_seal) | fill_molecules, T_seal (sealing = initial K), T_amb (ambient air K, optional;
     default T_seal), f (Hz, drive frequency: sets the one-cycle time grid and the regime flags), shellModes:[{name,f,tag}]}.
     The wall exchanges heat with still air at T_amb. No drive mechanism is defined (electrodes removed 2026-10-19): the drive
     source below is a stub that deposits zero energy, so every discharge-derived output is exactly zero.
     returns traces + summary. Missing required inputs -> {error}. */
  function run(p, opts) {
    opts = opts || {};
    for (const k of ["ID_mm", "OD_mm", "T_seal", "f"]) if (!(p[k] > 0)) return { error: "enter " + k };
    if (!(p.fill_Torr > 0) && !(p.fill_molecules > 0)) return { error: "enter fill" };
    if (p.OD_mm <= p.ID_mm) return { error: "OD must exceed ID" };
    const hasAmb = p.T_amb !== undefined && p.T_amb !== null;
    if (hasAmb && !(p.T_amb > 0)) return { error: "ambient T must be > 0 K (leave unset for ambient = sealing T)" };
    const g = geometry(p), Ta = hasAmb ? p.T_amb : p.T_seal;   // ambient defaults to the sealing temperature
    const N = p.fill_molecules > 0 ? p.fill_molecules : p.fill_Torr * TORR * g.V / (kB * p.T_seal);
    const n = N / g.V, mgas = N * HHO.M / NA, rho = mgas / g.V, Cv_g = mgas * HHO.cp / HHO.gamma;
    const reg = regime(p.f, g);
    // wall grid
    const NW = 24, rr = [], Vc = [], Cq = [];
    for (let i = 0; i <= NW; i++) rr.push(g.a + (g.b - g.a) * i / NW);
    for (let i = 0; i < NW; i++) { const v = 4 / 3 * Math.PI * (rr[i + 1] ** 3 - rr[i] ** 3); Vc.push(v); Cq.push(v * QZ.rho * QZ.cp); }
    const rc = rr.slice(0, NW).map((r, i) => 0.5 * (r + rr[i + 1]));
    // thermal state is solved as theta = T - T_seal (rise above the seal temperature): with no sources and Ta = T_seal the
    // right-hand side is exactly zero, so theta stays exactly 0 (no rounding wander on a 293 K baseline) [calc]
    const Ts = p.T_seal, thAmb = Ta - Ts;   // ambient offset; exactly 0 when T_amb is unset
    let thG = 0, thW = new Array(NW).fill(0), Tg = Ts, Tw = new Array(NW).fill(Ts);   // Tg/Tw = Ts + theta (coefficient evaluation, traces)
    // lumped time constant at the initial state
    const hA0 = natconvH(p.T_seal + 1, Ta, 2 * g.b) * 4 * Math.PI * g.b ** 2, Ctot = Cq.reduce((s, x) => s + x, 0) + Cv_g;
    const tauLumped = Ctot / hA0;
    const T = 1 / p.f, w = 2 * Math.PI * p.f;
    // time grid: cycle resolved, then log relaxation
    const ts = [0]; const ncyc = opts.ncyc || 800;
    for (let i = 1; i <= ncyc; i++) ts.push(T * i / ncyc);
    const tEnd = Math.min(Math.max(5 * tauLumped, 20 * T), 200);
    const nlog = opts.nlog || 160;
    for (let i = 1; i <= nlog; i++) ts.push(T * Math.pow(tEnd / T, i / nlog));
    // DRIVE SOURCE STUB: no drive mechanism defined (electrodes removed 2026-10-19; drive method open). Fails closed:
    // deposits exactly zero energy on every step. Do not replace with an invented mechanism; Danny decides the drive.
    const driveEnergy = (t, dt) => 0;
    let Edis = 0;
    const tr = { t: [], P: [], Tg: [], Twin: [], Twout: [], p: [], c: [], fgas0: [] };
    const fx0 = 4.4934 / (2 * Math.PI * g.a);
    let maxThG = 0, maxThW = 0, Egas = 0, Ewall = 0, Eopt = 0, nDiss = 0, nWater = 0, Echem = 0, H2left = 2 * N / 3;
    for (let k = 1; k < ts.length; k++) {
      const t = ts[k], dt = t - ts[k - 1];
      const Ed = driveEnergy(t, dt), Pd = Ed / dt;
      Edis += Ed;
      Egas += ETA.gas * Ed; Ewall += ETA.wall * Ed; Eopt += ETA.opt * Ed;
      const dnd = CH.eta * ETA.gas * Ed / CH.ED, dnw = Math.min(CH.nu * dnd, H2left); H2left -= dnw; nDiss += dnd; nWater += dnw;
      const Ech = dnw * CH.DH; Echem += Ech;   // chemical heat release fed to the gas
      // thermal implicit step (coefficients lagged): nodes 0 = gas, 1..NW = wall
      const alpha_g = kGas(Tg) / (rho * HHO.cp), tau_g = g.a ** 2 / (Math.PI ** 2 * alpha_g), Ggw = Cv_g / tau_g;
      const Gw = []; for (let i = 0; i < NW - 1; i++) { const kk = kQz(0.5 * (Tw[i] + Tw[i + 1])); Gw.push(4 * Math.PI * kk / (1 / rc[i] - 1 / rc[i + 1])); }
      const Gin = 4 * Math.PI * kQz(Tw[0]) / (1 / g.a - 1 / rc[0]);
      const Gws = 1 / (1 / Ggw + 1 / Gin);
      const hA = natconvH(Tw[NW - 1], Ta, 2 * g.b) * 4 * Math.PI * g.b ** 2;
      const Gout = 1 / (1 / hA + (1 / rc[NW - 1] - 1 / g.b) / (4 * Math.PI * kQz(Tw[NW - 1])));
      const M = NW + 1, A = new Array(M).fill(0), B = new Array(M).fill(0), Cc = new Array(M).fill(0), D = new Array(M).fill(0);
      const cap = [Cv_g].concat(Cq), Told = [thG].concat(thW), src = new Array(M).fill(0);
      src[0] = (ETA.gas * Ed + Ech) / dt; src[1] = ETA.wall * Ed / dt;
      const G = [Gws].concat(Gw);   // G[i] between node i and i+1
      for (let i = 0; i < M; i++) {
        B[i] = cap[i] / dt; D[i] = cap[i] / dt * Told[i] + src[i];
        if (i > 0) { A[i] = -G[i - 1]; B[i] += G[i - 1]; }
        if (i < M - 1) { Cc[i] = -G[i]; B[i] += G[i]; }
      }
      B[M - 1] += Gout; D[M - 1] += Gout * thAmb;
      for (let i = 1; i < M; i++) { const m = A[i] / B[i - 1]; B[i] -= m * Cc[i - 1]; D[i] -= m * D[i - 1]; }
      const X = new Array(M); X[M - 1] = D[M - 1] / B[M - 1];
      for (let i = M - 2; i >= 0; i--) X[i] = (D[i] - Cc[i] * X[i + 1]) / B[i];
      thG = X[0]; thW = X.slice(1); Tg = Ts + thG; Tw = thW.map(x => Ts + x);
      maxThG = Math.max(maxThG, thG); maxThW = Math.max(maxThW, thW[0]);
      tr.t.push(t); tr.P.push(Pd); tr.Tg.push(Tg); tr.Twin.push(Tw[0]); tr.Twout.push(Tw[NW - 1]);
      tr.p.push(N * kB * Tg / g.V); tr.c.push(cHHO(Tg)); tr.fgas0.push(fx0 * cHHO(Tg));
    }
    // acoustic ring-down: no drive source, so no mode is driven (the former discharge-jump impulse source is removed with the electrodes)
    const maxTg = Ts + maxThG, maxTw = Ts + maxThW;   // peak absolute temperatures; dTg/dTw below are the peak rises themselves
    const sigOverP = (g.b ** 3 + 2 * g.a ** 3) / (2 * (g.b ** 3 - g.a ** 3));  // Lame inner hoop stress / inner pressure [calc]
    const uOverP = g.a / QZ.E * ((1 - 2 * QZ.nu) * g.a ** 3 + (1 + QZ.nu) * g.b ** 3 / 2) / (g.b ** 3 - g.a ** 3);
    const stateHot = { T: maxTg, N, tauLumped, Tseal: p.T_seal };
    const modes = naturalModes(p, stateHot);
    const ring = [];
    for (const m of modes) {
      if (m.domain !== "acoustic") continue;
      const wn = 2 * Math.PI * m.f;
      ring.push({ name: m.name, f: m.f, Q: m.Q, tau: m.Q ? 2 * m.Q / wn : null, amp: 0, unit: m.name.indexOf("gas") === 0 ? "Pa" : "Pa hoop",
        what: "not driven: no drive mechanism defined (electrodes removed 2026-10-19; drive method open)" });
    }
    const p_seal = N * kB * p.T_seal / g.V;
    const flags = [];
    for (const [nm, TT] of [["gas", maxTg], ["inner wall", maxTw]]) {
      const C = TT - 273.15;
      if (C >= AUTOIGN_C[0]) flags.push(`${nm} ${C.toFixed(0)} C is IN the HHO autoignition range ~${AUTOIGN_C[0]}-${AUTOIGN_C[1]} C`);
      else if (C >= AUTOIGN_C[0] - 50) flags.push(`${nm} ${C.toFixed(0)} C is APPROACHING HHO autoignition (~${AUTOIGN_C[0]}-${AUTOIGN_C[1]} C)`);
    }
    reg.flags.forEach(f => flags.push(f));
    flags.push(NO_DRIVE);
    return {
      inputs: p, T_amb: Ta, geom: g, N, n, rho, p_seal, drive: NO_DRIVE, regime: reg, qz_sound: Object.assign({ key: QZ_SEL }, QZ_SOUND[QZ_SEL]), cycle_s: T,
      E_dis: Edis, E_gas: Egas, E_wall: Ewall, E_opt: Eopt, photons_Ha_equiv: Eopt / (6.62607015e-34 * C0 / 656.3e-9),
      maxTg, maxTw, dTg: maxThG, dTw: maxThW, p_max: N * kB * maxTg / g.V, c_seal: cHHO(p.T_seal), c_max: cHHO(maxTg),
      sigma_fill: sigOverP * p_seal, sigma_peak_static: sigOverP * N * kB * maxTg / g.V, uOverP, tauLumped, modes, ring, flags, tr,
      chem: { n_diss: nDiss, n_water: nWater, E_release: Echem, frac_converted: nWater / (2 * N / 3), knee: "not defined" },
      chem_energy_J: N / 3 * 2 * 241.8e3 / NA * 1 // 2 H2 + O2 -> 2 H2O(g), 241.8 kJ/mol H2O [lit]; per 3 molecules -> 2 H2O
    };
  }

  // drive-frequency regime flags (v0.3) [calc thresholds]; the gap-based breakdown-formation flags were removed with the electrodes
  function regime(f, g) {
    const fl = [], fEM = C0 * 2.0 / (2 * Math.PI * g.b * Math.sqrt(QZ.eps)), fQS = C0 / (10 * 2 * g.b * Math.sqrt(QZ.eps));
    const lam = C0 / f;
    if (f >= fEM) fl.push(`quasi-static model INVALID: f ${fmtHz(f)} ≥ first dielectric-sphere EM resonance ~${fmtHz(fEM)} [est]; the sphere is ≥ a wavelength (λ0 ${fmtL(lam)}) and fields are no longer lumped`);
    else if (f >= fQS) fl.push(`quasi-static model degrading: OD·√εr > λ/10 above ~${fmtHz(fQS)} (EM resonance ~${fmtHz(fEM)}) [est]`);
    const lamv = lam;
    if (lamv >= VIS[0] && lamv <= VIS[1]) fl.push(`OPTICAL BAND: drive λ ${fmtL(lamv)} is visible light — the drive IS light; the lumped quasi-static field picture does not apply`);
    else if (lamv < VIS[0]) fl.push(`drive λ ${fmtL(lamv)} is ultraviolet light — the lumped quasi-static field picture does not apply`);
    else if (f >= 3e11) fl.push(`drive λ ${fmtL(lamv)} is infrared radiation (>300 GHz) — the lumped quasi-static field picture does not apply`);
    BALMER.forEach(([n, l]) => { if (Math.abs(lamv - l) / l < 0.01) fl.push(`drive is within 1% of Balmer ${n} ${(l * 1e9).toFixed(2)} nm`); });
    return { flags: fl, fEM, fQS, lambda0: lam };
  }
  const fmtHz = f => f >= 1e15 ? (f / 1e15).toPrecision(3) + " PHz" : f >= 1e12 ? (f / 1e12).toPrecision(3) + " THz" : f >= 1e9 ? (f / 1e9).toPrecision(3) + " GHz" : f >= 1e6 ? (f / 1e6).toPrecision(3) + " MHz" : f >= 1e3 ? (f / 1e3).toPrecision(3) + " kHz" : f.toPrecision(3) + " Hz";
  const fmtS = t => t >= 1e-3 ? (t * 1e3).toPrecision(3) + " ms" : t >= 1e-6 ? (t * 1e6).toPrecision(3) + " µs" : t >= 1e-9 ? (t * 1e9).toPrecision(3) + " ns" : t >= 1e-12 ? (t * 1e12).toPrecision(3) + " ps" : (t * 1e15).toPrecision(3) + " fs";
  const fmtL = l => l >= 1 ? l.toPrecision(3) + " m" : l >= 1e-3 ? (l * 1e3).toPrecision(3) + " mm" : l >= 1e-6 ? (l * 1e6).toPrecision(3) + " µm" : (l * 1e9).toPrecision(3) + " nm";
  function sweep(p, key, values, opts) {
    return values.map(v => { const q = Object.assign({}, p); q[key] = v; const r = run(q, Object.assign({ ncyc: 400, nlog: 80 }, opts || {}));
      return r.error ? { x: v, error: r.error } : { x: v, E_dis: r.E_dis, dTg: r.dTg, dTw: r.dTw, p_max: r.p_max,
        ringGas: (r.ring.find(z => z.name.indexOf("gas l=0 n=1") === 0) || {}).amp || 0,
        ringShell: (r.ring.find(z => z.what.indexOf("shell breathing") === 0) || {}).amp || 0, Echem: r.chem.E_release, flags: r.flags, fgas: r.modes[2].f,
        E_opt: r.E_opt, drive: r.drive, modes: r.modes.map(m => ({ domain: m.domain, name: m.name, f: m.f })) }; });
  }
  const logspace = (a, b, n) => Array.from({ length: n }, (_, i) => a * Math.pow(b / a, i / (n - 1)));
  const api = { QZ_SOUND, setQuartzSound, shellRadialModes, regime, BALMER, VIS, fmtHz, CH, run, sweep, logspace, naturalModes, cHHO, geometry, ETA, HHO, QZ, AUTOIGN_C, TORR, NO_DRIVE };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.DriveModel = api;
})(typeof window !== "undefined" ? window : this);
