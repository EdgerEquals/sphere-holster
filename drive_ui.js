/* drive_ui.js - Drive panel for the v0 viewer: independent single-cycle drive, coupled response, sweeps. ESTIMATED PHYSICS. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id), DM = window.DriveModel;
  const FMIN = 1e5, FMAX = 1e15;   // v0.3: EMF drive range 100 kHz – 1000 THz (log slider)
  // typed values with SI suffixes: k M G T P (also m = milli, u/µ = micro); unit words Hz/Torr/mm are ignored
  const SI = { '': 1, k: 1e3, M: 1e6, G: 1e9, T: 1e12, P: 1e15, m: 1e-3, u: 1e-6, 'µ': 1e-6 };
  function parseSI(str) {
    const m = String(str).trim().match(/^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*([kMGTPmuµ]?)\s*(?:Hz|hz|Torr|torr|mm)?$/);
    return m ? parseFloat(m[1]) * SI[m[2]] : NaN;
  }
  window.parseSI = parseSI;
  const s2f = v => FMIN * Math.pow(FMAX / FMIN, v / 1000), f2s = f => Math.round(1000 * Math.log(f / FMIN) / Math.log(FMAX / FMIN));
  const fmtF = f => f >= 1e12 ? (f / 1e12).toPrecision(4) + ' THz' : f >= 1e9 ? (f / 1e9).toPrecision(4) + ' GHz' : f >= 1e6 ? (f / 1e6).toPrecision(4) + ' MHz' : f >= 1e3 ? (f / 1e3).toPrecision(4) + ' kHz' : f.toPrecision(3) + ' Hz';
  const fmtT = t => t >= 1 ? t.toPrecision(3) + ' s' : t >= 1e-3 ? (t * 1e3).toPrecision(3) + ' ms' : t >= 1e-6 ? (t * 1e6).toPrecision(3) + ' µs' : t >= 1e-9 ? (t * 1e9).toPrecision(3) + ' ns' : t >= 1e-12 ? (t * 1e12).toPrecision(3) + ' ps' : (t * 1e15).toPrecision(3) + ' fs';
  const e3 = x => (x === 0 ? '0' : Math.abs(x) >= 1e4 || Math.abs(x) < 1e-2 ? x.toExponential(2) : x.toPrecision(3));
  const DC = { optical: '#ffd23f', acoustic: '#38c6ff', electric: '#ff4fd8', magnetic: '#4dff88', thermal: '#ff6a3d', chemical: '#b98cff' };
  let caseC = null, last = null;

  function shellModes(C, ID, OD) {   // l=0 shell modes are now computed in drive_model.js; preset l>=1 refs only when the geometry is the preset's
    const out = []; if (!(Math.abs(ID - C.core_d_mm) < 1e-6 && Math.abs(OD - C.OD_quartz_mm) < 1e-6)) return out;
    Object.entries(C.acoustic_ref_l_ge_1 || {}).forEach(([n, f]) => out.push({ name: n, f, tag: 'calc minimal_test' }));
    return out;
  }
  window.drivePresetChanged = function (C) {
    caseC = C; $('dID').value = C.core_d_mm; $('dOD').value = C.OD_quartz_mm; setSweepDefaults(); drawFaxis();
    $('dMsg').textContent = C.propagation && C.propagation.bare ? '' : 'drive model covers the bare quartz bubble only (outer layers not included)';
  };
  function params() {
    const p = { ID_mm: +$('dID').value, OD_mm: +$('dOD').value, T_seal: +$('dTs').value, V_amp: +$('dV').value, f: parseSI($('dF').value),
      shellModes: caseC ? shellModes(caseC, +$('dID').value, +$('dOD').value) : [] };
    const fill = +$('dFill').value; if ($('dFillU').value === 'torr') p.fill_Torr = fill; else p.fill_molecules = fill;
    if ($('dTa').value !== '') p.T_amb = +$('dTa').value;   // ambient air T; blank => ambient = sealing T
    const miss = [];
    if (!($('dFill').value !== '' && fill > 0)) miss.push('HHO fill amount');
    if (!($('dV').value !== '' && p.V_amp > 0)) miss.push('drive amplitude');
    if (!($('dF').value !== '' && p.f > 0)) miss.push('drive frequency (e.g. 2.5M, 100k, 600T)');
    if (!(p.ID_mm > 0 && p.OD_mm > p.ID_mm)) miss.push('geometry (OD > ID)');
    if (!(p.T_seal > 0)) miss.push('initial (sealing) T');
    if (p.T_amb !== undefined && !(p.T_amb > 0)) miss.push('ambient T > 0 K (or blank = sealing T)');
    return { p, miss };
  }
  function setF(f, fromSlider) {
    if (!(f > 0)) { window.DRIVE_F = null; $('dT').textContent = '–'; $('dReg').innerHTML = ''; drawFaxis(); return; }
    window.DRIVE_F = f; $('dT').textContent = fmtT(1 / f);
    if (!fromSlider) $('dFs').value = Math.max(0, Math.min(1000, f2s(f)));
    $('dMsg').textContent = (f < FMIN || f > FMAX) ? 'note: ' + fmtF(f) + ' is outside the 100 kHz–1000 THz drive range' : '';
    showRegime(); drawFaxis();
  }
  function curGeom() { const ID = +$('dID').value, OD = +$('dOD').value; return ID > 0 && OD > ID ? DM.geometry({ ID_mm: ID, OD_mm: OD }) : null; }
  function showRegime() {
    const g = curGeom(), f = window.DRIVE_F; if (!g || !f) { $('dReg').innerHTML = ''; return; }
    const r = DM.regime(f, g);
    $('dReg').innerHTML = (r.flags.length ? r.flags.map(x => `<div class="flag">⚠ ${x}</div>`).join('') : '<div class="ok">regime: quasi-static circuit model valid; half-cycle longer than the breakdown formation times [est]</div>') +
      `<div class="small">limits for this geometry [est]: quasi-static to ~${fmtF(r.fQS)} (OD·√εr = λ/10); EM resonance ~${fmtF(r.fEM)}; avalanche formation ~${fmtT(r.tauE)} (no discharge above ~${fmtF(0.5 / r.tauE)}); Townsend ion feedback ~${fmtT(r.tauI)} (static knee needs f < ~${fmtF(0.5 / r.tauI)}); visible band 400–789 THz</div>`;
  }
  // frequency axis under the slider: decade ticks, natural acoustic modes, Balmer lines + visible band, regime limits
  function drawFaxis() {
    const cv = $('dFax'); if (!cv) return; const g = cv.getContext('2d'), W = cv.width, H = cv.height; g.clearRect(0, 0, W, H);
    const L = 8, Rr = 8, X = f => L + (W - L - Rr) * Math.log(f / FMIN) / Math.log(FMAX / FMIN);
    g.font = '9px system-ui';
    const vis = [2.998e8 / DM.VIS[1], 2.998e8 / DM.VIS[0]];
    const grd = g.createLinearGradient(X(vis[0]), 0, X(vis[1]), 0); ['#d00000', '#ff8800', '#ffee00', '#00c040', '#0060ff', '#7a00d0'].forEach((c, i) => grd.addColorStop(i / 5, c));
    g.fillStyle = grd; g.globalAlpha = 0.45; g.fillRect(X(vis[0]), 0, X(vis[1]) - X(vis[0]), H - 12); g.globalAlpha = 1;
    g.fillStyle = '#ddd'; g.fillText('visible', X(vis[0]) - 2, 9);
    DM.BALMER.forEach(([n, l], i) => { const x = X(2.998e8 / l); g.strokeStyle = '#fff'; g.beginPath(); g.moveTo(x, 10); g.lineTo(x, H - 12); g.stroke(); if (i < 3) { g.fillStyle = '#fff'; g.fillText(n, x - 4 + (i - 1) * 9, 19 + i * 0); } });
    const geo = curGeom();
    if (geo) {
      const N = (+$('dFill').value > 0 && $('dFillU').value === 'torr') ? (+$('dFill').value) * DM.TORR * geo.V / (1.380649e-23 * (+$('dTs').value || 293)) : 1e15;  // mode f do not depend on N
      const ms = DM.naturalModes({ ID_mm: +$('dID').value, OD_mm: +$('dOD').value }, { T: +$('dTs').value || 293, N });
      ms.filter(m => m.domain === 'acoustic' && m.f >= FMIN && m.f <= FMAX).forEach(m => { const x = X(m.f); g.strokeStyle = DC.acoustic; g.beginPath(); g.moveTo(x, 12); g.lineTo(x, H - 12); g.stroke(); });
      g.fillStyle = DC.acoustic; const ac = ms.filter(m => m.domain === 'acoustic').map(m => m.f);
      if (ac.length) g.fillText('acoustic modes', X(Math.min(...ac)) + 2, 28);
      const r = DM.regime(1e6, geo);
      [[r.fQS, 'QS λ/10', '#ff8a7a'], [r.fEM, 'EM res', '#ff4fd8'], [0.5 / r.tauE, 'no-form', '#ffd27a']].forEach(([f, t, c], i) => { if (f > FMIN && f < FMAX) { const x = X(f); g.strokeStyle = c; g.setLineDash([3, 2]); g.beginPath(); g.moveTo(x, 12); g.lineTo(x, H - 12); g.stroke(); g.setLineDash([]); g.fillStyle = c; g.fillText(t, x + 2, 38 - i * 9 + 9); } });
    }
    g.strokeStyle = '#9aa6bd'; g.fillStyle = '#9aa6bd';
    for (let e = 5; e <= 15; e++) { const x = X(Math.pow(10, e)); g.beginPath(); g.moveTo(x, H - 12); g.lineTo(x, H - 7); g.stroke(); const lab = ['100k', '1M', '10M', '100M', '1G', '10G', '100G', '1T', '10T', '100T', '1000T'][e - 5]; g.fillText(lab, Math.min(x - 8, W - 28), H - 1); }
    if (window.DRIVE_F) { const x = X(window.DRIVE_F); g.strokeStyle = '#fff'; g.lineWidth = 2; g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H - 12); g.stroke(); g.lineWidth = 1; }
  }
  window.drawFaxis = drawFaxis;
  ['dID', 'dOD', 'dTs', 'dFill'].forEach(id => $(id).addEventListener('input', () => { showRegime(); drawFaxis(); }));
  $('dF').addEventListener('input', () => setF(parseSI($('dF').value), false));
  const toSI = f => { const u = [[1e15, 'P'], [1e12, 'T'], [1e9, 'G'], [1e6, 'M'], [1e3, 'k'], [1, '']].find(([v]) => f >= v) || [1, '']; return +(f / u[0]).toPrecision(4) + u[1]; };
  $('dFs').addEventListener('input', () => { const f = +s2f(+$('dFs').value).toPrecision(4); $('dF').value = toSI(f); setF(f, true); });
  // quartz sound-speed selector (cited) + HHO c(T)
  function showSound() {
    const q = DM.setQuartzSound($('dQz').value); window.QZ_CL = q.cL; window.QZ_CT = q.cT;
    const T = +$('dTs').value || 293.15;
    $('dQzSrc').innerHTML = `quartz cL ${q.cL} m/s, cT ${q.cT} m/s — ${q.src}<br>HHO gas c(T) = √(γRT/M), γ 1.40 [lit-typical, H2 and O2 both ≈1.40 near 300 K, NIST Chemistry WebBook fluid data], M 12.01 g/mol [calc from IUPAC atomic weights], R 8.314462618 [CODATA] → ${DM.cHHO(T).toFixed(1)} m/s at ${T} K (533 m/s at 293 K); computed hot c is used everywhere (gas T is a coupled state). Precomputed 3-D presets use the solver's set (${(window.CUR_CASE && window.CUR_CASE.propagation.qz_sound_sel) || 'vrh'}); this selector drives the drive panel, sweeps and waveform λ.`;
    drawFaxis();
  }
  $('dQz').addEventListener('change', showSound); $('dTs').addEventListener('input', showSound);
  // sweep bounds (typed, SI suffixes) + point count
  const SWDEF = { f: ['100k', '1000T', 40, 'Hz'], fill: ['0.1', '7.6k', 40, 'Torr at sealing'] };
  function setSweepDefaults() {
    const k = $('dSweep').value, ID = +$('dID').value || 1, OD = +$('dOD').value || 2;
    const d = k === 'ID' ? [String(+Math.max(0.2 * ID, 0.12).toPrecision(3)), String(+(0.98 * OD).toPrecision(4)), 40, 'mm (OD fixed ' + OD + ' mm; OD > ID enforced)'] :
      k === 'OD' ? [String(+(1.02 * ID).toPrecision(4)), String(+(10 * OD).toPrecision(3)), 40, 'mm (ID fixed ' + ID + ' mm; OD > ID enforced)'] : SWDEF[k];
    $('dLo').value = d[0]; $('dHi').value = d[1]; $('dN').value = d[2]; $('dSwU').textContent = d[3];
  }
  $('dSweep').addEventListener('change', setSweepDefaults);

  // ---------- plots ----------
  function axes(g, x0, y0, w, h, title) {
    g.strokeStyle = '#2a3244'; g.strokeRect(x0, y0, w, h); g.fillStyle = '#9aa6bd'; g.font = '10px system-ui'; g.fillText(title, x0 + 4, y0 + 11);
  }
  function line(g, xs, ys, X, Y, col, dash) {
    g.strokeStyle = col; g.setLineDash(dash || []); g.beginPath(); let st = false;
    for (let i = 0; i < xs.length; i++) { const x = X(xs[i]), y = Y(ys[i]); if (!isFinite(x) || !isFinite(y)) continue; st ? g.lineTo(x, y) : g.moveTo(x, y); st = true; }
    g.stroke(); g.setLineDash([]);
  }
  function drawTraces(r) {
    const cv = $('dTr'), g = cv.getContext('2d'), W = cv.width; g.clearRect(0, 0, W, cv.height);
    const L = 60, Rr = 8, T = r.cycle_s, tr = r.tr, wP = W - L - Rr;
    // A: V and V_gas over the cycle
    const iC = tr.t.findIndex(t => t > 1.1 * T); const nC = iC < 0 ? tr.t.length : iC;
    const tC = tr.t.slice(0, nC), XA = t => L + wP * t / (1.1 * T);
    const vmax = Math.max(r.inputs.V_amp, isFinite(r.Vb) ? r.Vb : 0) * 1.1, YA = v => 8 + 42 - 42 * v / vmax;
    axes(g, L, 8, wP, 84, 'drive V(t) (grey), gas-gap V (magenta), ±knee (dashed)  — one cycle = ' + fmtT(T));
    line(g, tC, tr.V.slice(0, nC), XA, YA, '#8f98aa'); line(g, tC, tr.Vg.slice(0, nC), XA, YA, DC.electric);
    if (isFinite(r.Vb)) { line(g, [0, 1.1 * T], [r.Vb, r.Vb], XA, YA, '#ffd27a', [4, 3]); line(g, [0, 1.1 * T], [-r.Vb, -r.Vb], XA, YA, '#ffd27a', [4, 3]); }
    g.fillStyle = '#9aa6bd'; g.fillText(vmax.toFixed(0) + ' V', 4, 14); g.fillText('0', 30, YA(0) + 3); g.fillText('-' + vmax.toFixed(0), 4, 90);
    // B: discharge power
    const Pm = Math.max(...tr.P.slice(0, nC), 1e-30), YB = v => 100 + 84 - 76 * v / Pm;
    axes(g, L, 100, wP, 84, 'discharge power (Manley-type, from rest) [est] — E/cycle ' + e3(r.E_dis) + ' J; light ' + e3(r.E_opt) + ' J');
    line(g, tC, tr.P.slice(0, nC), XA, YB, DC.optical); g.fillStyle = '#9aa6bd'; g.fillText(e3(Pm) + ' W', 2, 112); g.fillText('t →', W - 30, 196);
    // C: temperatures vs log time
    const t0 = tr.t[0], t1 = tr.t[tr.t.length - 1], XC = t => L + wP * Math.log(t / t0) / Math.log(t1 / t0);
    const dTg = tr.Tg.map(x => x - r.inputs.T_seal), dTw = tr.Twin.map(x => x - r.inputs.T_seal), dTo = tr.Twout.map(x => x - r.inputs.T_seal);
    const m = Math.max(...dTg, ...dTw, 1e-30), YC = v => 200 + 92 - 84 * v / m;
    axes(g, L, 200, wP, 92, 'computed ΔT (log t): gas (orange), inner wall (red), outer wall (pink); p ∝ T_gas, c ∝ √T_gas');
    line(g, tr.t, dTg, XC, YC, '#ffa040'); line(g, tr.t, dTw, XC, YC, '#ff4040'); line(g, tr.t, dTo, XC, YC, '#ff9ad0');
    g.fillStyle = '#9aa6bd'; g.fillText(e3(m) + ' K', 2, 212); g.fillText(fmtT(t0), L, 298); g.fillText(fmtT(t1), W - 50, 298);
    const xe = XC(T); g.strokeStyle = '#555'; g.beginPath(); g.moveTo(xe, 200); g.lineTo(xe, 292); g.stroke(); g.fillText('end of cycle', xe + 3, 288);
  }
  function drawModes(r) {
    const cv = $('dModes'), g = cv.getContext('2d'), W = cv.width, H = cv.height; g.clearRect(0, 0, W, H);
    const L = 10, Rr = 10, lo = -2, hi = 15, X = f => L + (W - L - Rr) * (Math.log10(f) - lo) / (hi - lo);
    g.fillStyle = 'rgba(255,210,122,0.12)'; g.fillRect(X(FMIN), 14, X(FMAX) - X(FMIN), H - 34);
    g.fillStyle = '#ffd27a'; g.font = '10px system-ui'; g.fillText('drive range 100 kHz–1000 THz', X(FMIN) + 2, 24);
    const rows = { thermal: 0, chemical: 1, acoustic: 2, electric: 3, magnetic: 4, optical: 5 };
    r.modes.forEach(m => { const y = 26 + rows[m.domain] * 12; g.fillStyle = DC[m.domain]; g.beginPath(); g.arc(X(m.f), y, 3, 0, 7); g.fill(); });
    Object.entries(rows).forEach(([d, i]) => { g.fillStyle = DC[d]; g.fillText(d, W - 60, 29 + i * 12); });
    g.strokeStyle = '#ffffff'; g.beginPath(); g.moveTo(X(r.inputs.f), 12); g.lineTo(X(r.inputs.f), H - 20); g.stroke();
    g.fillStyle = '#fff'; g.fillText('drive ' + fmtF(r.inputs.f), X(r.inputs.f) + 3, 12);
    g.fillStyle = '#9aa6bd'; for (let e = lo; e <= hi; e += 3) g.fillText('1e' + e, X(Math.pow(10, e)) - 8, H - 4);
    g.fillText('natural modes / relaxation corners of THIS geometry at the computed gas T (response properties, not the drive)', L, H - 14 + 0);
  }
  function drawSweep(kind, pts, base) {
    const cv = $('dSw'), g = cv.getContext('2d'), W = cv.width, H = cv.height; g.clearRect(0, 0, W, H);
    const ok = pts.filter(p => !p.error); if (!ok.length) { g.fillStyle = '#ff8a7a'; g.fillText('sweep: ' + (pts[0] && pts[0].error), 10, 20); return; }
    if (kind === 'ID' || kind === 'OD') return drawGeomSweep(kind, pts, ok, base);
    const L = 40, Rr = 10, T = 22, B = 34, x0 = ok[0].x, x1 = ok[ok.length - 1].x;
    const X = x => L + (W - L - Rr) * Math.log(x / x0) / Math.log(x1 / x0);
    const series = [['E_dis', 'energy/cycle', 'J', DC.optical], ['dTg', 'ΔT_gas peak', 'K', '#ffa040'], ['dTw', 'ΔT_wall,in peak', 'K', '#ff4040'],
      ['ringGas', 'gas l=0 ring p', 'Pa', DC.acoustic], ['ringShell', 'shell 0S0 ring σ', 'Pa', '#a0e8ff'], ['Echem', 'chemical heat/cycle', 'J', DC.chemical]];
    g.strokeStyle = '#2a3244'; g.strokeRect(L, T, W - L - Rr, H - T - B);
    g.fillStyle = '#9aa6bd'; g.font = '10px system-ui';
    g.fillText(kind === 'f' ? 'response vs drive frequency ' + fmtF(x0) + '–' + fmtF(x1) + ' (' + pts.length + ' pts ; each curve / its max; log x) at the entered fill & amplitude' : 'response vs HHO fill (Torr at sealing; log x) at the entered f & amplitude', L, 12);
    series.forEach(([k, n, u, c], i) => {
      const mx = Math.max(...ok.map(p => p[k]), 0); const Y = v => T + (H - T - B) * (1 - (mx > 0 ? v / mx : 0));
      line(g, ok.map(p => p.x), ok.map(p => p[k]), X, Y, c); g.fillStyle = c; g.fillText(n + ' max ' + e3(mx) + ' ' + u, L + 4 + (i % 3) * 165, T + 12 + Math.floor(i / 3) * 12);
    });
    if (kind === 'fill') { // knee curve vs available gas voltage
      const vg = base.share * base.V_amp, vb = ok.map(p => isFinite(p.Vb) ? p.Vb : NaN), mx = Math.max(vg, ...vb.filter(isFinite)) * 1.05;
      const Y = v => T + (H - T - B) * (1 - v / mx);
      line(g, ok.map(p => p.x), vb, X, Y, '#ffd27a', [4, 3]); line(g, [x0, x1], [vg, vg], X, Y, '#ff4fd8', [2, 3]);
      g.fillStyle = '#ffd27a'; g.fillText('dashed: ionisation knee V_b(fill) [HHO, est]; magenta: peak gas V', L + 4, H - B - 6);
      const kf = base.kneeFill; if (kf > x0 && kf < x1) { g.strokeStyle = '#ffd27a'; g.beginPath(); g.moveTo(X(kf), T); g.lineTo(X(kf), H - B); g.stroke(); g.fillText('Paschen-min fill ' + kf.toPrecision(3) + ' Torr', X(kf) + 3, H - B - 18); }
    } else {
      (base.modes || []).forEach(m => { if (m.f >= x0 && m.f <= x1) { g.strokeStyle = DC[m.domain]; g.setLineDash([2, 3]); g.beginPath(); g.moveTo(X(m.f), T); g.lineTo(X(m.f), H - B); g.stroke(); g.setLineDash([]); g.fillStyle = DC[m.domain]; g.fillText(m.name.split(' [')[0].split(' 1/')[0], X(m.f) + 2, H - B - 8); } });
      const ac = (base.modes || []).filter(m => m.domain === 'acoustic').map(m => m.f);
      if (ac.length && Math.min(...ac) > x1) { g.fillStyle = DC.acoustic; g.fillText('acoustic modes ' + fmtF(Math.min(...ac)) + '–' + fmtF(Math.max(...ac)) + ' lie above this axis →', W - 290, T + 40); }
      if (base.f) { g.strokeStyle = '#fff'; g.beginPath(); g.moveTo(X(base.f), T); g.lineTo(X(base.f), H - B); g.stroke(); }
    }
    g.fillStyle = '#9aa6bd'; g.fillText(kind === 'f' ? fmtF(x0) : x0 + ' Torr', L, H - B + 14); g.fillText(kind === 'f' ? fmtF(x1) : x1 + ' Torr', W - 60, H - B + 14);
    const nflag = ok.filter(p => p.flags.some(f => f.indexOf('autoignition') >= 0)).length;
    if (nflag) { g.fillStyle = '#ff8a7a'; g.fillText('⚠ ' + nflag + ' sweep points approach/enter HHO autoignition (~500–585 C)', L, H - 4); }
  }
  // ID / OD sweeps: per-domain response (top) and natural modes vs geometry with the drive f and knee marked (bottom)
  function drawGeomSweep(kind, pts, ok, base) {
    const cv = $('dSw'), g = cv.getContext('2d'), W = cv.width, H = cv.height;
    const L = 46, Rr = 10, x0 = ok[0].x, x1 = ok[ok.length - 1].x, X = x => L + (W - L - Rr) * Math.log(x / x0) / Math.log(x1 / x0);
    g.font = '10px system-ui'; g.fillStyle = '#9aa6bd';
    g.fillText(`response vs ${kind} ${x0}–${x1} mm (${pts.length} pts; ${pts.length - ok.length} invalid: OD ≤ ID or ID ≤ electrode) at the entered fill, amplitude & f`, 4, 11);
    // top panel: per-domain response (each / its max)
    const T1 = 18, H1 = 112;
    g.strokeStyle = '#2a3244'; g.strokeRect(L, T1, W - L - Rr, H1);
    const series = [['E_opt', 'optical: light/cycle', 'J', DC.optical], ['ringGas', 'acoustic: gas l=0 ring', 'Pa', DC.acoustic], ['ringShell', 'acoustic: shell 0S0 ring', 'Pa', '#a0e8ff'],
      ['Vgas', 'electric: peak gas V', 'V', DC.electric], ['dTg', 'thermal: ΔT_gas', 'K', DC.thermal], ['Echem', 'chemical: heat/cycle', 'J', DC.chemical]];
    series.forEach(([k, n, u, c], i) => {
      const mx = Math.max(...ok.map(p => p[k]), 0), Y = v => T1 + H1 * (1 - (mx > 0 ? v / mx : 0));
      line(g, ok.map(p => p.x), ok.map(p => p[k]), X, Y, c); g.fillStyle = c; g.fillText(n + ' max ' + e3(mx) + ' ' + u, L + 4 + (i % 3) * 165, T1 + 11 + Math.floor(i / 3) * 11);
    });
    g.fillStyle = DC.magnetic; g.fillText('magnetic: B = 0 for the symmetric radial drive (all points)', L + 4, T1 + H1 - 4);
    // knee: V_b vs geometry (dashed) against the peak gas voltage
    const vb = ok.map(p => isFinite(p.Vb) ? p.Vb : NaN), vmx = Math.max(...ok.map(p => p.Vgas), ...vb.filter(isFinite), 1) * 1.05, YV = v => T1 + H1 * (1 - v / vmx);
    line(g, ok.map(p => p.x), vb, X, YV, '#ffd27a', [4, 3]);
    let imin = -1; vb.forEach((v, i) => { if (isFinite(v) && (imin < 0 || v < vb[imin])) imin = i; });
    if (imin >= 0) { const x = X(ok[imin].x); g.fillStyle = '#ffd27a'; g.beginPath(); g.arc(x, YV(vb[imin]), 3.5, 0, 7); g.fill(); g.fillText('knee min ' + vb[imin].toFixed(0) + ' V @ ' + kind + ' ' + ok[imin].x.toPrecision(3), Math.min(x + 4, W - 150), YV(vb[imin]) - 4); }
    for (let i = 1; i < ok.length; i++) { const a = ok[i - 1].Vgas - (vb[i - 1] || Infinity), b = ok[i].Vgas - (vb[i] || Infinity); if (isFinite(a) && isFinite(b) && a * b < 0 || (isFinite(a) !== isFinite(b))) { const x = X(ok[i].x); g.strokeStyle = '#ffd27a'; g.beginPath(); g.moveTo(x, T1); g.lineTo(x, T1 + H1); g.stroke(); g.fillStyle = '#ffd27a'; g.fillText('ionisation on/off', x + 2, T1 + H1 - 14); } }
    // bottom panel: natural modes vs geometry (log f)
    const T2 = T1 + H1 + 8, H2 = H - T2 - 16;
    g.strokeStyle = '#2a3244'; g.strokeRect(L, T2, W - L - Rr, H2);
    const names = {}; ok.forEach(p => p.modes.forEach(m => { if (!(m.domain === 'optical')) (names[m.name] = names[m.name] || { domain: m.domain, xs: [], fs: [] }); if (names[m.name]) { names[m.name].xs.push(p.x); names[m.name].fs.push(m.f); } }));
    const fl = [], drive = base.f;   // y range: acoustic modes + drive, ±1 decade; other corners drawn where they fall inside
    Object.values(names).forEach(s => { if (s.domain === 'acoustic') fl.push(...s.fs); }); if (drive) fl.push(drive);
    const lo = Math.floor(Math.log10(Math.min(...fl))) - 1, hi = Math.ceil(Math.log10(Math.max(...fl))) + 1, Yf = f => T2 + H2 * (1 - (Math.log10(f) - lo) / (hi - lo));
    g.save(); g.beginPath(); g.rect(L, T2, W - L - Rr, H2); g.clip();
    Object.entries(names).forEach(([n, s]) => { if (n.indexOf('gas l=') === 0 && n.indexOf('l=0') < 0) return; line(g, s.xs, s.fs, X, Yf, DC[s.domain], s.domain === 'thermal' || s.domain === 'chemical' ? [3, 2] : []); });
    if (drive) { g.strokeStyle = '#fff'; g.beginPath(); g.moveTo(L, Yf(drive)); g.lineTo(W - Rr, Yf(drive)); g.stroke(); g.fillStyle = '#fff'; g.fillText('drive ' + fmtF(drive), W - 90, Yf(drive) - 3);
      let nlab = 0; Object.entries(names).forEach(([n, s]) => { if (n.indexOf('gas l=') === 0 && n.indexOf('l=0') < 0) return; for (let i = 1; i < s.fs.length; i++) if ((s.fs[i - 1] - drive) * (s.fs[i] - drive) < 0) { const xc = s.xs[i - 1] * Math.pow(s.xs[i] / s.xs[i - 1], Math.log(drive / s.fs[i - 1]) / Math.log(s.fs[i] / s.fs[i - 1])); g.strokeStyle = DC[s.domain]; g.beginPath(); g.arc(X(xc), Yf(drive), 5, 0, 7); g.stroke(); if (nlab < 4) { g.fillStyle = DC[s.domain]; g.fillText(n.split(' [')[0] + ' = drive @ ' + xc.toPrecision(3) + ' mm', Math.min(X(xc) + 6, W - 210), Yf(drive) + 12 + 11 * nlab); } nlab++; } }); }
    g.restore();
    g.fillStyle = '#9aa6bd'; g.fillText('1e' + hi + ' Hz', 2, T2 + 9); g.fillText('1e' + lo + ' Hz', 2, T2 + H2); g.fillText(x0 + ' mm', L, H - 3); g.fillText(x1 + ' mm', W - 50, H - 3);
    g.fillText('natural modes vs ' + kind + ': acoustic (cyan: gas l=0, shell l=0 computed), thermal/chemical corners (dashed), EM res (magenta); ○ = mode crosses drive f. Chemical knee: not defined', L + 2, T2 + 10);
    const nflag = ok.filter(p => p.flags.some(f => f.indexOf('autoignition') >= 0)).length;
    if (nflag) { g.fillStyle = '#ff8a7a'; g.fillText('⚠ ' + nflag + ' points approach/enter HHO autoignition', W - 230, H - 3); }
  }
  function table(r) {
    const gm = r.modes.filter(m => m.name.indexOf('gas l=0 n=1') === 0)[0];
    const f293 = 4.4934 * DM.cHHO(r.inputs.T_seal) / (2 * Math.PI * r.geom.a);
    const rows = [
      ['Fill (input)', `${e3(r.N)} HHO molecules (${e3(r.N * 2 / 3)} H2 + ${e3(r.N / 3)} O2); n ${e3(r.n)} /m³ (fixed); sealed p ${e3(r.p_seal)} Pa = ${e3(r.p_seal / DM.TORR)} Torr at ${r.inputs.T_seal} K (initial); ambient ${r.T_amb} K`],
      ['Ionisation knee (computed)', isFinite(r.Vb) ? `${r.Vb.toFixed(0)} V across the ${(r.geom.gap * 1e3).toFixed(2)} mm gas gap (HHO Paschen [est, anchored to lit H2/O2 minima]); gas takes ${(r.geom.share * 100).toFixed(1)} % of applied V; Paschen-min fill for this gap ${r.kneeFill_Torr.toPrecision(3)} Torr. Depends on n·d, so heating at fixed N, V leaves it unchanged to first order. O2 is electronegative (attachment raises V_b, makes the discharge filamentary; O⁻+H2 detachment partly offsets) [est, qualitative]` : 'left of the Paschen curve: no breakdown'],
      ['Discharge (computed)', `E/cycle ${e3(r.E_dis)} J (gas ${e3(r.E_gas)}, wall ${e3(r.E_wall)}, light ${e3(r.E_opt)} ≈ ${e3(r.photons_Ha_equiv)} Hα-equivalent photons) [partition est]; charge moved ${e3(r.Q_tr)} C; chemical energy stored in the fill ${e3(r.chem_energy_J)} J [lit ΔH]`],
      ['Gas state (computed)', `T_gas peak ${r.maxTg.toFixed(3)} K (ΔT ${e3(r.dTg)} K); p peak ${e3(r.p_max)} Pa; c ${r.c_seal.toFixed(1)} → ${r.c_max.toFixed(1)} m/s; gas l=0 mode ${fmtF(f293)} → ${fmtF(gm.f)} (Q ${e3(gm.Q)} [est])`],
      ['Chemical (computed; knee: not defined)', `dissociated ${e3(r.chem.n_diss)} H2, formed ${e3(r.chem.n_water)} H2O (${e3(r.chem.frac_converted * 100)} % of the H2 converted this cycle); heat released ${e3(r.chem.E_release)} J fed to the gas; D0(H2) 4.478 eV, ΔH 241.8 kJ/mol H2O [lit]; dissociation share 0.2, chain 1, D_H [placeholders]`],
      ['Drive regime (computed)', (r.regime.flags.length ? r.regime.flags.join('; ') : 'quasi-static circuit model valid') + ` — λ0 ${(r.regime.lambda0).toPrecision(3)} m; EM resonance ~${fmtF(r.regime.fEM)}; avalanche formation ~${fmtT(r.regime.tauE)}, ion feedback ~${fmtT(r.regime.tauI)} [est]`],
      ['Sound speeds (cited)', `quartz ${r.qz_sound.key}: cL ${r.qz_sound.cL}, cT ${r.qz_sound.cT} m/s (${r.qz_sound.src}); HHO c = √(γRT/M): ${r.c_seal.toFixed(1)} → ${r.c_max.toFixed(1)} m/s`],
      ['Quartz (computed)', `inner wall ΔT peak ${e3(r.dTw)} K; fill hoop stress ${e3(r.sigma_fill)} Pa → ${e3(r.sigma_peak_static)} Pa at peak gas T; still-air lumped τ ${fmtT(r.tauLumped)}`]];
    let h = '<table>' + rows.map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`).join('') + '</table>';
    h += '<div class="small">Ring-down per mode after the single cycle (impulse approximation for f_mode ≫ f_drive) [est]:</div><table><tr><th>mode</th><th>f</th><th>Q</th><th>ring τ</th><th>amplitude</th><th></th></tr>' +
      r.ring.map(z => `<tr><td>${z.name.split(' [')[0]}</td><td>${fmtF(z.f)}</td><td>${z.Q ? e3(z.Q) : '–'}</td><td>${z.tau ? fmtT(z.tau) : '–'}</td><td>${e3(z.amp)} ${z.unit}</td><td class="small">${z.what}</td></tr>`).join('') + '</table>';
    h += '<div class="small">Other domains: electric quasi-static (sphere EM resonance ~' + fmtF(r.modes.find(m => m.domain === 'electric').f) + ' [est]); magnetic B = 0 by symmetry of the radial current; optical follows the discharge power within ~10 ns [est]; thermal corners: ' +
      r.modes.filter(m => m.domain === 'thermal').map(m => fmtF(m.f)).join(', ') + '.</div>';
    h += r.flags.length ? r.flags.map(f => `<div class="flag">⚠ ${f}</div>`).join('') : '<div class="ok">No autoignition / knee flags for this single cycle.</div>';
    $('dOut').innerHTML = h;
  }
  function runOne() {
    const { p, miss } = params();
    if (miss.length) { $('dMsg').textContent = 'enter: ' + miss.join(', '); return null; }
    $('dMsg').textContent = ''; setF(p.f, false);
    const r = DM.run(p); if (r.error) { $('dMsg').textContent = r.error; return null; }
    last = r; drawTraces(r); drawModes(r); table(r); window.DRIVE_LAST = r; return r;
  }
  $('dRun').onclick = runOne;
  $('dSweepGo').onclick = () => {
    const kind = $('dSweep').value, { p, miss } = params();
    const need = miss.filter(m => !(kind === 'f' && m.indexOf('drive frequency') === 0) && !(kind === 'fill' && m === 'HHO fill amount') && !((kind === 'ID' || kind === 'OD') && m.indexOf('geometry') === 0));
    const lo = parseSI($('dLo').value), hi = parseSI($('dHi').value), np = Math.round(+$('dN').value);
    if (!(lo > 0 && hi > lo)) need.push('sweep bounds (lower < upper, > 0; suffixes k M G T P)');
    if (!(np >= 2 && np <= 200)) need.push('point count 2–200');
    if (need.length) { $('dMsg').textContent = 'enter: ' + need.join(', '); return; }
    $('dMsg').textContent = '';
    const g = DM.geometry(Object.assign({}, p, { ID_mm: p.ID_mm > 0 ? p.ID_mm : 1, OD_mm: p.OD_mm > p.ID_mm ? p.OD_mm : 2 * (p.ID_mm || 1) }));
    let pts, base = { share: g.share, V_amp: p.V_amp, kneeFill: DM.kneeFill_Torr(g.gap) };
    if (kind === 'f') {
      pts = DM.sweep(p, 'f', DM.logspace(lo, hi, np));
      const r0 = DM.run(Object.assign({}, p, { f: p.f > 0 ? p.f : lo }), { ncyc: 200, nlog: 60 }); base.modes = r0.error ? [] : r0.modes; base.f = p.f > 0 ? p.f : null;
    } else if (kind === 'fill') {
      const q = Object.assign({}, p); delete q.fill_molecules; pts = DM.sweep(q, 'fill_Torr', DM.logspace(lo, hi, np));
    } else {
      const q = Object.assign({}, p, { shellModes: [] }); pts = DM.sweep(q, kind + '_mm', DM.logspace(lo, hi, np)); base.f = p.f;
    }
    drawSweep(kind, pts, base); window.DRIVE_SWEEP = { kind, pts };
  };
  window.setDrive = (o) => { for (const [k, v] of Object.entries(o)) { const el = $(k); if (el) el.value = v; } if ('dSweep' in o && !('dLo' in o)) setSweepDefaults(); if ('dQz' in o) showSound(); setF(parseSI($('dF').value), false); };
  setSweepDefaults(); showSound();
})();
