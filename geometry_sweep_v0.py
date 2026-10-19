"""Geometry sweep v0 (opt-in, 2026-10-19): search the geometry for maximum mode locking.

Framing (DESIGN_STATE.md, geometry note + amendment, and "modes lock where they lock"): every frequency comes from the
geometry already in the model; the three cavities are the hydrogen (HHO) bubble, the quartz layer and the tourmaline
alloy layer (= the tourbillon, solver layer two). The solver does not select a mode; the sweep is a SEARCH, not a
prediction. Nothing is driven: no source, J_src = 0, P_src = 0, every mode energy stays 0. This script never writes the
default outputs (solver_v0_output.txt, model_data_v0.json, index.html, tourmaline_sweep_v0.json); it writes only
geometry_sweep_v0.json.

Swept: gas bubble radius a, quartz wall thickness w, tourbillon (layer two) thickness t2. Every other layer is built
by build_stack exactly as for base5 (BTO 2 um, Gd-Dy 3 um, phi-stepped outer zones), 1 atm HHO at 293 K.

Mode sets per geometry (acoustic, l = 0 only, search window 20 kHz - 12 MHz = the solver's l0_modes window):
  B  bubble gas cavity alone, rigid wall: f = x_n c_HHO / (2 pi a), j1(x_n) = 0. Q from solver_v0.gas_Q(f, a, p, T,
     'HHO') at the fill state (1 atm, 293 K): wall thermal boundary layer + classical bulk absorption, viscous wall loss
     0 for l = 0 [est: modelling assumption, upper bound on Q], so a B mode now has its own linewidth f/Q.
  Q  quartz layer alone (free shell, vacuum both faces): propagate() roots; Q_eff from mode_energy_stats (= 2100).
  T  tourbillon alone (free layer-two shell): propagate() roots in the window plus its first thickness mode
     (searched near cL/2t2); Q_eff from mode_energy_stats (= 150).
  S  bonded stack (all layers, gas-loaded): l0_modes() split into shell modes as run_case does; Q_eff per mode from
     all_modes_stats (W = 0).
Only l = 0 is compared: the model's shell modes are all l = 0, and in a spherically symmetric body an l != 0 mode is
orthogonal to an l = 0 mode, so it cannot lock to it.

Lock (the scoring definition): two modes i, j of DIFFERENT cavities lock when |f_i - f_j| <= (f_i/Q_i + f_j/Q_j)/2,
i.e. their own model linewidths (FWHM f/Q) overlap at half maximum. No tolerance is invented. Pairs scored: B-Q, B-T,
Q-T, B-S. Q-S and T-S are not scored (S contains Q and T, so they would match themselves).
Boundary-reflection round trips: a round trip inside one cavity (B: across the diameter and back, f = n c/(4a);
Q: n cL/(2w); T: n cL2/(2 t2)) lands on a real mode of ANOTHER cavity when |f_rt - f_mode| <= (f_mode/Q_mode)/2
(a reflection has no Q of its own: width 0). Targets: B -> Q, T, S; Q -> B, T; T -> B, Q.
Score = number of locks (mode-mode + reflection landings). Also reported: distinct real modes taking part, and
locks per real mode in the window (density-normalised, because a larger body simply has more modes in the window), and sharp_per_mode = sharp locks /
modes in the window (third ranking, rank_spm).
Cascade holding together (gate, reported per geometry): in each cavity thermal < acoustic fundamental < electric.
Knees crossed at the right thresholds: NOT SCORED. A knee crossing needs a field amplitude, and with no source every
amplitude is exactly zero; it stays unscored until a source is defined.
Golden ratio: secondary, non-scoring column (tracking scale, not a rule): adjacent ratios of the sorted distinct
lock frequencies against 1.618.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_v0 as S  # noqa: E402

PHI = S.PHI
FMIN, FMAX, NGRID = 2e4, 12e6, 4000          # same window and grid as solver l0_modes
P_ATM = 1.0                                   # base5 fill
BASE = dict(a_mm=1.5, w_mm=1.0, t2_um=5.0)    # base5
CAV_PAIRS = {("B", "Q"), ("B", "T"), ("Q", "T"), ("B", "S")}
REFL_TARGETS = {"B": ("Q", "T", "S"), "Q": ("B", "T"), "T": ("B", "Q")}
GAS_COMP = "HHO"
# Gas-cavity Q: derived by solver_v0.gas_Q(f, a, p, T, comp) at the sweep's fill state (1 atm HHO, 293 K; no source,
# so the gas stays at 293 K). Modelling assumption, not measured physics: isothermal wall, no molecular relaxation,
# no discharge loss -> an upper bound on Q (lower bound on the gas linewidth).
GAS_Q_SOURCE = ("derived: solver_v0.gas_Q(f, a, p, T, 'HHO') at 1 atm, 293 K (no source); wall thermal boundary layer "
                "+ classical bulk absorption, viscous wall loss 0 for l=0; modelling assumption (isothermal wall, no "
                "relaxation/discharge loss), upper bound on Q, not measured")


# ------------------------------------------------------------------ scoring (pure, testable)
def linewidth(m):
    """FWHM f/Q from the mode's own model Q; 0 when the model has no Q for it (fallback, tagged in the output)."""
    return m["f"] / m["Q"] if m.get("Q") else 0.0


def _pair_ok(c1, c2):
    return (c1, c2) in CAV_PAIRS or (c2, c1) in CAV_PAIRS


def _spacing(fs_sorted, f):
    """Local spacing of a sorted frequency set at f (inf for fewer than two members)."""
    if len(fs_sorted) < 2:
        return float("inf")
    k = int(np.clip(np.searchsorted(fs_sorted, f), 1, len(fs_sorted) - 1))
    return float(fs_sorted[k] - fs_sorted[k - 1])


def find_locks(modes, reflections=()):
    """modes: [dict(cav, f, Q or None)]; reflections: [dict(cav, f, n)]. Returns the list of locks (see module doc).
    Each pair of real modes counts once; each reflecting cavity counts at most one landing per target mode (its
    nearest harmonic). Each lock is flagged density_guaranteed when its full window (2 x half_width) is at least the
    local spacing of the denser of the two sets, i.e. some member would fall inside it whatever the geometry; a lock
    that is not density-guaranteed is a 'sharp' lock (it needs the geometry to line up)."""
    locks = []
    ms = sorted(modes, key=lambda m: m["f"])
    wmax = max([linewidth(m) for m in ms] + [0.0])
    fs = np.array([m["f"] for m in ms])
    byc = {}
    for m in ms:
        byc.setdefault(m["cav"], []).append(m["f"])
    byc = {k: np.array(v) for k, v in byc.items()}
    for i, mi in enumerate(ms):
        wi = linewidth(mi)
        hi = np.searchsorted(fs, mi["f"] + 0.5 * (wi + wmax), side="right")
        for j in range(i + 1, hi):
            mj = ms[j]
            if mi["cav"] == mj["cav"] or not _pair_ok(mi["cav"], mj["cav"]):
                continue
            hw = 0.5 * (wi + linewidth(mj))
            if abs(mi["f"] - mj["f"]) <= hw:
                sp = min(_spacing(byc[mi["cav"]], mi["f"]), _spacing(byc[mj["cav"]], mj["f"]))
                locks.append(dict(kind="mode", a=(mi["cav"], mi["f"]), b=(mj["cav"], mj["f"]),
                                  df_Hz=abs(mi["f"] - mj["f"]), half_width_Hz=hw, density_guaranteed=bool(2 * hw >= sp)))
    best = {}
    for r in reflections:
        for m in ms:
            if m["cav"] in REFL_TARGETS.get(r["cav"], ()):
                d = abs(r["f"] - m["f"])
                if d <= 0.5 * linewidth(m):
                    key = (r["cav"], m["cav"], m["f"])
                    if key not in best or d < best[key][0]:
                        best[key] = (d, r, m)
    rsp = {}
    for r in reflections:
        rsp.setdefault(r["cav"], []).append(r["f"])
    rsp = {k: np.array(sorted(v)) for k, v in rsp.items()}
    for (rc, _, _), (d, r, m) in sorted(best.items(), key=lambda kv: kv[1][2]["f"]):
        hw = 0.5 * linewidth(m)
        locks.append(dict(kind="reflection", a=(rc + "rt", r["f"], r["n"]), b=(m["cav"], m["f"]), df_Hz=d,
                          half_width_Hz=hw, density_guaranteed=bool(2 * hw >= _spacing(rsp[rc], r["f"]))))
    return locks


def golden_column(locks):
    """Non-scoring: adjacent ratios of the sorted distinct SHARP-lock frequencies vs phi (all locks if none is sharp;
    dense density-guaranteed locks would only give ratios ~1.00x)."""
    sharp = [lk for lk in locks if not lk.get("density_guaranteed")]
    fl = sorted(0.5 * (lk["a"][1] + lk["b"][1]) for lk in (sharp or locks))
    d = []
    for f in fl:
        if not d or f / d[-1] - 1 > 1e-3:
            d.append(f)
    rat = [d[k + 1] / d[k] for k in range(len(d) - 1)]
    if not rat:
        return dict(basis="sharp" if sharp else "all", n_lock_freqs=len(d), freqs_Hz=[round(x, 1) for x in d], ratios=[],
                    nearest_phi=None, nearest_phi_dev_pct=None, n_within_5pct_of_phi=0)
    k = min(range(len(rat)), key=lambda i: abs(rat[i] / PHI - 1))
    return dict(basis="sharp" if sharp else "all", n_lock_freqs=len(d), freqs_Hz=[round(x, 1) for x in d], ratios=[round(x, 4) for x in rat], nearest_phi=round(rat[k], 4),
                nearest_phi_dev_pct=round(100 * (rat[k] / PHI - 1), 2),
                n_within_5pct_of_phi=sum(1 for x in rat if abs(x / PHI - 1) <= 0.05))


# ------------------------------------------------------------------ modes from the model's geometry
def free_modes(L, fmin=FMIN, fmax=FMAX, n=NGRID):
    """Traction-free l=0 shell roots (same method as run_case vac_modes)."""
    fs = np.linspace(fmin, fmax, n)
    g = np.array([S.propagate(f, L)[1, 0] for f in fs])
    o = []
    for i in range(n - 1):
        if np.sign(g[i]) != np.sign(g[i + 1]):
            try:
                o.append(brentq(lambda f: S.propagate(f, L)[1, 0], fs[i], fs[i + 1], xtol=1.0))
            except ValueError:
                pass
    return o


def split(loaded, vac):
    """Shell modes of a gas-loaded stack = loaded roots within 1 % of the vacuum roots (run_case rule)."""
    shell = []
    for v in vac:
        if loaded:
            b = min(loaded, key=lambda f: abs(f / v - 1))
            if abs(b / v - 1) < 0.01 and b not in shell:
                shell.append(b)
    return sorted(shell)


def gas_rigid_l0(a, c, fmax=FMAX):
    """Rigid-wall l=0 gas-cavity modes: j1(x)=0 <=> tan x = x, x in (n pi, (n+1/2) pi)."""
    out, n = [], 1
    while True:
        x = brentq(lambda x: math.sin(x) - x * math.cos(x), n * math.pi + 1e-9, (n + 0.5) * math.pi - 1e-9)
        f = x * c / (2 * math.pi * a)
        if f > fmax:
            return out
        if f >= FMIN:
            out.append(f)
        n += 1


def _by_pair(locks):
    out = {}
    for x in locks:
        k = x["a"][0] + "-" + x["b"][0] if x["kind"] == "mode" else x["a"][0] + "->" + x["b"][0]
        if x["kind"] == "mode":
            k = "-".join(sorted((x["a"][0], x["b"][0])))
        out[k] = out.get(k, 0) + 1
    return out


def q_of(f, L):
    return S.mode_energy_stats(f, L, 0.0)["Q_eff"]


def _fill_gas_Z(gp):
    """Opt-in (fill sweep only): solver_v0.gas_Z with the mix's own c and gamma from gas_props at the fill state
    (K = gamma p). Same pole-free form; used only while evaluate(comp=...) runs, then the solver's own is restored."""
    c, K = gp["c"], gp["gamma"] * S.GAS["p"]
    def gz(f, r_in):
        k = 2 * math.pi * f / c; x = k * r_in
        return -K * k * math.sin(x) / x, (math.sin(x) / x ** 2 - math.cos(x) / x)
    return gz


def evaluate(a_mm, w_mm, t2_um, details=False, em=False, p_atm=None, comp=None):
    """All modes, locks and score for one geometry. No source: every mode energy is 0.
    Default (p_atm=None, comp=None): the 1 atm HHO path exactly as before (c_hho, solver gas_Z). Opt-in fill state
    (geometry_fill_sweep_v0): p_atm and/or comp (name or {species: x}) set the gas everywhere it enters: the rigid-wall
    B modes and bubble round trips use c from S.gas_props, the bonded-stack gas loading uses that c and K = gamma p,
    gas Q is S.gas_Q at (p, 293 K, comp), and the cascade thermal rate uses the mix's k/(rho cp)."""
    if comp is None and p_atm is None:
        return _evaluate(a_mm, w_mm, t2_um, details, em, P_ATM, None)
    old_gz = S.gas_Z
    try:
        return _evaluate(a_mm, w_mm, t2_um, details, em, P_ATM if p_atm is None else p_atm, comp or GAS_COMP)
    finally:
        S.gas_Z = old_gz; S.GAS["p"] = P_ATM * 101325.0; S.GAS["T"] = S.T_REF


def _evaluate(a_mm, w_mm, t2_um, details, em, p_atm, comp):
    t0 = time.time()
    st = S.build_stack(2 * a_mm, w_mm, t_l2=t2_um * S.UM)
    S.GAS["p"] = p_atm * 101325.0; S.GAS["T"] = S.T_REF
    a, b = st["r_in"], st["r_q"]; t2 = t2_um * S.UM
    lay = st["layers"]
    if comp is None:
        c_g = S.c_hho(S.T_REF); qcomp = GAS_COMP
        rho_g = P_ATM * 101325.0 * 0.012011 / (8.314462618 * S.T_REF); al_B = S.K_HHO0 / (rho_g * S.CP_HHO)
    else:
        gp = S.gas_props(S.T_REF, S.GAS["p"], comp); c_g = gp["c"]; qcomp = comp
        al_B = gp["D_t"]; S.gas_Z = _fill_gas_Z(gp)
    LQ = [("quartz", a, b)]; LT = [("layer2", b, b + t2)]
    B = gas_rigid_l0(a, c_g)
    Qm = free_modes(LQ)
    m2 = S.MAT["layer2"]; f_fp = m2["cL"] / (2 * t2)
    Tm = free_modes(LT) + free_modes(LT, 0.6 * f_fp, 1.4 * f_fp, 400)
    Sm = split(S.l0_modes(lay), free_modes(lay))
    s_stats = S.all_modes_stats(Sm, lay, 0.0)
    modes = ([dict(cav="B", f=f, Q=S.gas_Q(f, a, p=p_atm * 101325.0, T=S.T_REF, comp=qcomp)) for f in B] + [dict(cav="Q", f=f, Q=q_of(f, LQ)) for f in Qm]
             + [dict(cav="T", f=f, Q=q_of(f, LT)) for f in Tm] + [dict(cav="S", f=m["f"], Q=m["Q_eff"]) for m in s_stats])
    assert all(m["W"] == 0.0 for m in s_stats)   # no source: zero run
    cLq = S.MAT["quartz"]["cL"]
    refl = ([dict(cav="B", f=n * c_g / (4 * a), n=n) for n in range(1, int(FMAX * 4 * a / c_g) + 1)]
            + [dict(cav="Q", f=n * cLq / (2 * w_mm * S.MM), n=n) for n in range(1, int(FMAX * 2 * w_mm * S.MM / cLq) + 1)]
            + [dict(cav="T", f=f_fp, n=1)])
    locks = find_locks(modes, refl)
    part = {(lk[k][0], lk[k][1]) for lk in locks for k in ("a", "b") if not lk[k][0].endswith("rt")}
    n_in = sum(1 for m in modes if m["f"] <= FMAX)
    # thermal (model convention tau = L^2/(pi^2 alpha), f = 1/(2 pi tau)) and electric (estimates), per cavity
    al = dict(B=al_B, Q=S.MAT["quartz"]["k"] / (S.MAT["quartz"]["rho"] * S.MAT["quartz"]["cp"]),
              T=m2["k"] / (m2["rho"] * m2["cp"]))
    Lc = dict(B=a, Q=w_mm * S.MM, T=t2)
    f_th = {k: math.pi * al[k] / (2 * Lc[k] ** 2) for k in al}
    nq, n2 = math.sqrt(S.EL_EPS_R["quartz"]), math.sqrt(S.EL_EPS_R["layer2"])
    f_el_sphere = S.C0 * 2 / (2 * math.pi * b * nq)            # [est] l=1 dielectric-sphere scale (no own bubble mode)
    f_el = dict(B=f_el_sphere, Q=f_el_sphere, T=S.C0 / (2 * n2 * t2))
    f_ac = dict(B=min(B) if B else None, Q=min(Qm) if Qm else None, T=min(Tm) if Tm else None)
    cascade = {k: bool(f_ac[k] and f_th[k] < f_ac[k] < f_el[k]) for k in f_th}
    gold = golden_column(locks)
    r = dict(a_mm=round(a_mm, 5), w_mm=round(w_mm, 5), t2_um=round(t2_um, 5), OD_mm=round(2 * b * 1e3, 4),
             score=len(locks), n_mode_locks=sum(1 for x in locks if x["kind"] == "mode"),
             n_reflection_locks=sum(1 for x in locks if x["kind"] == "reflection"),
             n_sharp_locks=sum(1 for x in locks if not x["density_guaranteed"]),
             n_B_locks=sum(1 for x in locks if x["a"][0] in ("B", "Brt") or x["b"][0] == "B"),
             by_pair=_by_pair(locks),
             n_distinct_modes=len(part), n_modes_window=n_in,
             locks_per_mode=round(len(locks) / n_in, 4) if n_in else 0.0,
             sharp_per_mode=round(sum(1 for x in locks if not x["density_guaranteed"]) / n_in, 4) if n_in else 0.0,
             gas_Q_first=round(modes[0]["Q"], 2) if B else None, c_gas=round(c_g, 3),
             n_modes=dict(B=len(B), Q=len(Qm), T=len(Tm), S=len(Sm)),
             cascade_ok=all(cascade.values()), cascade=cascade, golden=gold, runtime_s=round(time.time() - t0, 2))
    if details:
        r["locks"] = [dict(kind=x["kind"], a=[x["a"][0], round(x["a"][1], 1)] + list(x["a"][2:]),
                           b=[x["b"][0], round(x["b"][1], 1)], df_Hz=round(x["df_Hz"], 1),
                           half_width_Hz=round(x["half_width_Hz"], 1), density_guaranteed=x["density_guaranteed"]) for x in locks]
        r["modes_Hz"] = dict(B=[round(f, 1) for f in B], Q=[round(f, 1) for f in Qm], T=[round(f, 1) for f in Tm], S=[round(f, 1) for f in Sm])
        r["thermal_Hz"] = {k: round(v, 4) for k, v in f_th.items()}
        r["electric_est_Hz"] = {k: float("%.4g" % v) for k, v in f_el.items()}
        r["acoustic_fundamental_Hz"] = {k: (round(v, 1) if v else None) for k, v in f_ac.items()}
        r["Q_eff"] = dict(Q=q_of(Qm[0], LQ) if Qm else None, T=q_of(Tm[0], LT) if Tm else None, B=dict(source=GAS_Q_SOURCE, Q_first=round(modes[0]["Q"], 2) if B else None),
                          S=[round(m["Q_eff"], 2) for m in s_stats])
        if em:
            r["electric_open_sphere"] = em_open(a, b, b + t2)
    return r


# ------------------------------------------------------------------ EM: open layered sphere, l=1 (from the 2026-10-19 derivation)
def em_open(a, b, r2):
    """Complex l=1 TE/TM roots of the open gas | quartz | tourbillon sphere (Riccati-Bessel transfer, outgoing outside).
    Gas eps_r 1 [est: not in model]. Returns f_re [Hz] and Q = f_re/(-2 f_im)."""
    import mpmath as mp
    def rb(x):
        s, c = mp.sin(x), mp.cos(x)
        j0, j1 = s / x, s / x ** 2 - c / x; y0, y1 = -c / x, -c / x ** 2 - s / x
        return x * j1, x * j0 - j1, x * y1, x * y0 - y1
    nq, n2 = math.sqrt(S.EL_EPS_R["quartz"]), math.sqrt(S.EL_EPS_R["layer2"])
    layers = [(1.0, a), (nq, b), (n2, r2)]
    def char(f, mode):
        k0 = 2 * mp.pi * f / S.C0; A, Bc = mp.mpf(1), mp.mpf(0)
        for i in range(len(layers) - 1):
            n1, r = layers[i]; nn = layers[i + 1][0]
            p, dp, c, dc = rb(n1 * k0 * r); u = A * p + Bc * c; du = n1 * k0 * (A * dp + Bc * dc)
            if mode == "TM": du = du / n1 ** 2 * nn ** 2
            p2, dp2, c2, dc2 = rb(nn * k0 * r)
            sol = mp.lu_solve(mp.matrix([[p2, c2], [nn * k0 * dp2, nn * k0 * dc2]]), mp.matrix([u, du])); A, Bc = sol[0], sol[1]
        n, r = layers[-1]; p, dp, c, dc = rb(n * k0 * r); u = A * p + Bc * c; du = n * k0 * (A * dp + Bc * dc)
        if mode == "TM": du = du / n ** 2
        x = k0 * r; p0, dp0, c0, dc0 = rb(x)
        return du * (p0 + 1j * c0) - u * k0 * (dp0 + 1j * dc0)
    g0 = S.C0 * 2 / (2 * math.pi * b * nq); out = {}
    for mode, g in (("TE", g0), ("TM", 1.3 * g0)):
        try:
            z = complex(mp.findroot(lambda f: char(f, mode), mp.mpc(g, -0.2 * g)))
            out[mode] = dict(f_Hz=float("%.5g" % z.real), Q=round(z.real / (-2 * z.imag), 3) if z.imag else None)
        except Exception as e:   # noqa: BLE001
            out[mode] = dict(f_Hz=None, Q=None, error=str(e)[:80])
    return out


# ------------------------------------------------------------------ grid
# Grid on a phi^(1/8) lattice: point = BASE * phi^(i/8) per axis, i integer (exact de-duplication by index).
LAT = 8                                                                  # lattice: phi^(1/8)
COARSE = dict(a_mm=(-16, 12, 4), w_mm=(-20, 12, 4), t2_um=(-16, 12, 4))  # (i_lo, i_hi, step): phi^(1/2) steps around base5
REFINE_K = 2                                                             # refine: +-2 lattice steps (phi^(1/8)) per axis


def lattice_value(axis, i):
    return BASE[axis] * PHI ** (i / LAT)


def _ev(idx):
    return evaluate(*(lattice_value(ax, i) for ax, i in zip(("a_mm", "w_mm", "t2_um"), idx)))


def run(workers=8, refine_top=5):
    import multiprocessing as mpc
    t0 = time.time()
    axes_i = {k: list(range(lo, hi + 1, st)) for k, (lo, hi, st) in COARSE.items()}
    box = {k: (lo, hi) for k, (lo, hi, st) in COARSE.items()}
    pts = [(i, j, k) for i in axes_i["a_mm"] for j in axes_i["w_mm"] for k in axes_i["t2_um"]]
    key = lambda r: (not r["cascade_ok"], -r["score"], -r["n_distinct_modes"])   # cascade gate first
    with mpc.Pool(workers) as pool:
        coarse = pool.map(_ev, pts, chunksize=4)
        for r, p in zip(coarse, pts): r["idx"] = list(p); r["stage"] = "coarse"
        seeds = sorted(coarse, key=key)[:refine_top]
        seen = set(pts); rp = []
        for s_ in seeds:
            for di in range(-REFINE_K, REFINE_K + 1):
                for dj in range(-REFINE_K, REFINE_K + 1):
                    for dk in range(-REFINE_K, REFINE_K + 1):
                        p = (s_["idx"][0] + di, s_["idx"][1] + dj, s_["idx"][2] + dk)
                        inside = all(box[ax][0] <= v <= box[ax][1] for ax, v in zip(("a_mm", "w_mm", "t2_um"), p))
                        if inside and p not in seen:
                            seen.add(p); rp.append(p)
        refine = pool.map(_ev, rp, chunksize=4)
        for r, p in zip(refine, rp): r["idx"] = list(p); r["stage"] = "refine"
    allr = sorted(coarse + refine, key=key)
    for i, r in enumerate(allr): r["rank"] = i + 1
    sk = lambda r: (not r["cascade_ok"], -r["n_sharp_locks"], -r["score"])
    for i, r in enumerate(sorted(allr, key=sk)): r["rank_sharp"] = i + 1
    pk = lambda r: (not r["cascade_ok"], -r["sharp_per_mode"], -r["n_sharp_locks"])
    for i, r in enumerate(sorted(allr, key=pk)): r["rank_spm"] = i + 1
    det = lambda r, em: dict(evaluate(r["a_mm"], r["w_mm"], r["t2_um"], details=True, em=em), idx=r["idx"], rank=r["rank"],
                             rank_sharp=r["rank_sharp"], rank_spm=r["rank_spm"], stage=r["stage"])
    top = [det(r, True) for r in allr[:10]]
    top_sharp = [det(r, False) for r in sorted(allr, key=sk)[:10]]
    top_spm = [det(r, False) for r in sorted(allr, key=pk)[:10]]
    bd = det(next(r for r in allr if r["idx"] == [0, 0, 0]), True)
    n = len(allr)
    corr = {ax: float(np.corrcoef([r[ax] for r in allr], [r["score"] for r in allr])[0, 1]) for ax in ("a_mm", "w_mm", "t2_um")}
    corr["n_modes_window"] = float(np.corrcoef([r["n_modes_window"] for r in allr], [r["score"] for r in allr])[0, 1])
    return dict(meta=dict(title="Geometry sweep v0: search for maximum mode locking (no source)", date="2026-10-19",
                          status="search, not a prediction; v0 estimated physics; nothing measured; no source (every mode energy 0)",
                          scoring=__doc__.split("Lock (the scoring definition):")[1].split("Golden ratio:")[0].strip(),
                          golden="secondary non-scoring column: adjacent ratios of sorted distinct sharp-lock frequencies vs 1.618",
                          knees="unscored: knee crossings need a field amplitude; with no source every amplitude is exactly 0",
                          window_Hz=[FMIN, FMAX], p_atm=P_ATM, T_K=S.T_REF, base5=BASE, gas_Q=GAS_Q_SOURCE, 
                          coarse_axes={k: [round(lattice_value(k, i), 5) for i in v] for k, v in axes_i.items()},
                          box={k: [round(lattice_value(k, lo), 5), round(lattice_value(k, hi), 5)] for k, (lo, hi) in box.items()},
                          coarse_step="phi^(1/2)", refine=f"top {refine_top} coarse seeds, phi^(1/{LAT}) steps, +-{REFINE_K} per axis, clipped to the box",
                          n_coarse=len(coarse), n_refine=len(refine), n_total=n, runtime_s=round(time.time() - t0, 1), workers=workers,
                          score_correlation=corr,
                          qz_sound=S.QZ_SOUND_SEL,
                          n_cascade_fail=sum(1 for r in allr if not r["cascade_ok"]),
                          ranking="cascade gate first (thermal < acoustic < electric in every cavity), then primary: score (number of locks), tie-break distinct modes; secondary: sharp locks (not density-guaranteed); third: sharp_per_mode desc, tie sharp locks (rank_spm)",
                          gas_Q_range=[min(r["gas_Q_first"] for r in allr if r["gas_Q_first"]), max(r["gas_Q_first"] for r in allr if r["gas_Q_first"])]),
                top10=top, top10_sharp=top_sharp, top10_spm=top_spm, base5=bd, results=allr)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--refine-top", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(HERE, "geometry_sweep_v0.json"))
    a = ap.parse_args()
    S.set_qz_sound("vrh")
    res = run(a.workers, a.refine_top)
    with open(a.out, "w") as f:
        json.dump(res, f, separators=(",", ":"))
    m = res["meta"]
    print(f"coarse {m['n_coarse']} + refine {m['n_refine']} geometries in {m['runtime_s']} s; base5 rank {res['base5']['rank']} "
          f"(sharp rank {res['base5']['rank_sharp']}) score {res['base5']['score']} sharp {res['base5']['n_sharp_locks']}")
    for r in res["top10"] + res["top10_spm"]:
        print(f"#{r['rank']:3d} a {r['a_mm']:.4f} mm w {r['w_mm']:.4f} mm t2 {r['t2_um']:.3f} um | score {r['score']} "
              f"(mode {r['n_mode_locks']}, refl {r['n_reflection_locks']}, sharp {r['n_sharp_locks']}) distinct {r['n_distinct_modes']} cascade {r['cascade_ok']} "
              f"| modes {r['n_modes_window']} spm {r['sharp_per_mode']} (spm rank {r['rank_spm']}) | phi nearest {r['golden']['nearest_phi']}")
    print("wrote", os.path.basename(a.out))


if __name__ == "__main__":
    main()
