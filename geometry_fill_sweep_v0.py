"""Geometry x fill-state sweep v0 (opt-in, 2026-10-19): where does the lock optimum sit across geometry AND fill?

Same model, lock rule, sharp definition, cascade gate and scoring as geometry_sweep_v0 (see its module doc); only the
fill state is added as a second axis instead of assuming 1 atm HHO. No source: T stays 293 K, every mode energy is 0.
Writes only geometry_fill_sweep_v0.json; geometry_sweep_v0.json and every default solver output are untouched.

Fill axis (20 states): p in {0.382, 0.618, 1, 1.618, 2.618} atm (phi lattice around 1 atm: phi^-2 .. phi^2) x
x_H2 in {0.50, 2/3 (HHO), 0.75, 0.80}, composition {'H2': x, 'O2': 1 - x}. The mix enters everywhere the gas does,
through geometry_sweep_v0.evaluate(p_atm=, comp=): rigid-wall B modes and bubble round trips use c from
solver_v0.gas_props(293 K, p, comp); the bonded-stack modes are gas-loaded with that c and K = gamma p (sweep-side
override of solver gas_Z for the evaluation only; the solver is not changed); gas Q per B mode = solver_v0.gas_Q(f, a,
p, 293 K, comp); the cascade thermal rate of B uses the mix's k/(rho cp). Note: HHO via gas_props has c 533.20 m/s,
gamma 1.4016 vs the solver's c_hho 532.86 m/s, gamma 1.40 (0.06 %), so the 1 atm HHO cell here differs slightly from
geometry_sweep_v0 (which keeps c_hho); gas_props is used for every mix so the mix axis is self-consistent.

Geometry axis: the geometry_sweep_v0 box (a 0.573-3.087 mm, w 0.300-2.058 mm, t2 1.91-10.29 um), lattice
BASE * phi^(i/8), subsampled to 4 x 4 x 3 = 48 points per fill state (lattice indices):
  a  i in {-16, -12, 0, 12}  -> 0.573, 0.729, 1.5, 3.087 mm (both small-bubble winners, base, the raw-score edge)
  w  i in {-16, 0, 4, 12}    -> 0.382, 1.0, 1.272, 2.058 mm
  t2 i in {-12, 0, 12}       -> 2.43, 5.0, 10.29 um
Coarse = 48 x 20 = 960. Refine around the top 5 coarse by sharp_per_mode (cascade gate first): each seed's geometry
+-2 lattice steps (phi^(1/4)) per axis at the seed's fill state (up to 26 new), plus the seed's geometry at its 4 axis
neighbours on the fill grid (p +-1, x +-1); clipped to the box and the fill grid, de-duplicated. At most 150 refine
points, so the total stays <= 1,110.
Ranking: primary (rank_spm) cascade gate, then sharp_per_mode desc, tie sharp locks; also rank (score desc, tie
distinct modes, cascade first)."""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_v0 as S  # noqa: E402
import geometry_sweep_v0 as G  # noqa: E402

P_AXIS = [0.382, 0.618, 1.0, 1.618, 2.618]          # atm
X_AXIS = [0.50, 2 / 3, 0.75, 0.80]                  # H2 mole fraction (2/3 = HHO)
GEO_SUB = dict(a_mm=[-16, -12, 0, 12], w_mm=[-16, 0, 4, 12], t2_um=[-12, 0, 12])
REFINE_GEO_K = 2                                    # +-2 lattice steps = phi^(1/4)
AXES = ("a_mm", "w_mm", "t2_um")
BOX = {k: (lo, hi) for k, (lo, hi, st) in G.COARSE.items()}


def comp_of(x):
    return {"H2": x, "O2": 1 - x}


def _ev(pt):
    gi, pi, xi = pt
    r = G.evaluate(*(G.lattice_value(ax, i) for ax, i in zip(AXES, gi)), p_atm=P_AXIS[pi], comp=comp_of(X_AXIS[xi]))
    r.pop("golden", None)
    r.update(idx=list(gi), p_idx=pi, x_idx=xi, p_atm=P_AXIS[pi], x_H2=round(X_AXIS[xi], 4))
    return r


def spm_key(r):
    return (not r["cascade_ok"], -r["sharp_per_mode"], -r["n_sharp_locks"])


def score_key(r):
    return (not r["cascade_ok"], -r["score"], -r["n_distinct_modes"])


def run(workers=8, refine_top=5):
    import multiprocessing as mpc
    t0 = time.time()
    geos = [(i, j, k) for i in GEO_SUB["a_mm"] for j in GEO_SUB["w_mm"] for k in GEO_SUB["t2_um"]]
    pts = [(g, pi, xi) for pi in range(len(P_AXIS)) for xi in range(len(X_AXIS)) for g in geos]
    with mpc.Pool(workers) as pool:
        coarse = pool.map(_ev, pts, chunksize=4)
        for r in coarse: r["stage"] = "coarse"
        seeds = sorted(coarse, key=spm_key)[:refine_top]
        seen = set(pts); rp = []
        def add(p):
            if p not in seen: seen.add(p); rp.append(p)
        for s_ in seeds:
            g0, pi, xi = tuple(s_["idx"]), s_["p_idx"], s_["x_idx"]
            for di in range(-REFINE_GEO_K, REFINE_GEO_K + 1, REFINE_GEO_K):
                for dj in range(-REFINE_GEO_K, REFINE_GEO_K + 1, REFINE_GEO_K):
                    for dk in range(-REFINE_GEO_K, REFINE_GEO_K + 1, REFINE_GEO_K):
                        g = (g0[0] + di, g0[1] + dj, g0[2] + dk)
                        if all(BOX[ax][0] <= v <= BOX[ax][1] for ax, v in zip(AXES, g)):
                            add((g, pi, xi))
            for dp, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if 0 <= pi + dp < len(P_AXIS) and 0 <= xi + dx < len(X_AXIS):
                    add((g0, pi + dp, xi + dx))
        refine = pool.map(_ev, rp, chunksize=4)
        for r in refine: r["stage"] = "refine"
    allr = coarse + refine
    for i, r in enumerate(sorted(allr, key=score_key)): r["rank"] = i + 1
    allr.sort(key=spm_key)
    for i, r in enumerate(allr): r["rank_spm"] = i + 1
    by_score = sorted(allr, key=score_key)
    # per-fill-state best (by sharp_per_mode, cascade gate), and best fill per bubble size
    fill_best = []
    for pi, p in enumerate(P_AXIS):
        for xi, x in enumerate(X_AXIS):
            cell = [r for r in allr if r["p_idx"] == pi and r["x_idx"] == xi]
            b = min(cell, key=spm_key); bs = min(cell, key=score_key)
            fill_best.append(dict(p_atm=p, x_H2=round(x, 4), n=len(cell), best_spm=_slim(b), best_score=_slim(bs),
                                  top_a_mm_spm=[r["a_mm"] for r in sorted(cell, key=spm_key)[:5]]))
    per_a = {}
    for ai in GEO_SUB["a_mm"]:
        av = round(G.lattice_value("a_mm", ai), 5)
        cell = [r for r in allr if r["idx"][0] == ai]
        per_a[str(av)] = dict(best=_slim(min(cell, key=spm_key)),
                              best_per_fill={f"{P_AXIS[pi]}atm_x{round(X_AXIS[xi], 3)}": _slim(min(
                                  [r for r in cell if r["p_idx"] == pi and r["x_idx"] == xi], key=spm_key))
                                  for pi in range(len(P_AXIS)) for xi in range(len(X_AXIS))})
    ref = [r for r in allr if r["idx"] == [0, 0, 0] and r["p_idx"] == 2 and r["x_idx"] == 1][0]
    gq = [r["gas_Q_first"] for r in allr if r["gas_Q_first"]]
    return dict(meta=dict(title="Geometry x fill-state sweep v0 (no source)", date="2026-10-19",
                          status="search, not a prediction; v0 estimated physics; nothing measured; no source (T 293 K)",
                          method=__doc__, T_K=S.T_REF, p_axis_atm=P_AXIS, x_H2_axis=[round(x, 4) for x in X_AXIS],
                          geometry_subsample={k: [round(G.lattice_value(k, i), 5) for i in v] for k, v in GEO_SUB.items()},
                          geometry_subsample_idx=GEO_SUB, box={k: [round(G.lattice_value(k, lo), 5), round(G.lattice_value(k, hi), 5)] for k, (lo, hi) in BOX.items()},
                          refine=f"top {refine_top} coarse by sharp_per_mode: geometry +-{REFINE_GEO_K} lattice steps (phi^(1/4)) per axis at the seed fill, plus seed geometry at its 4 fill-grid axis neighbours; clipped, de-duplicated",
                          n_coarse=len(coarse), n_refine=len(refine), n_total=len(allr), runtime_s=round(time.time() - t0, 1),
                          workers=workers, qz_sound=S.QZ_SOUND_SEL, gas_Q=G.GAS_Q_SOURCE + "; evaluated at each fill state's (p, 293 K, comp)",
                          gas_Q_first_range=[min(gq), max(gq)], n_cascade_fail=sum(1 for r in allr if not r["cascade_ok"]),
                          ranking="primary rank_spm: cascade gate, sharp_per_mode desc, tie sharp locks; also rank: cascade gate, score desc, tie distinct modes"),
                top10_spm=allr[:10], top10_score=by_score[:10], base5_1atm_HHO=ref, fill_best=fill_best,
                best_per_bubble=per_a, results=allr)


def _slim(r):
    return {k: r[k] for k in ("a_mm", "w_mm", "t2_um", "p_atm", "x_H2", "n_mode_locks", "n_reflection_locks",
                              "n_sharp_locks", "n_modes_window", "sharp_per_mode", "score", "rank", "rank_spm", "cascade_ok")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--refine-top", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(HERE, "geometry_fill_sweep_v0.json"))
    a = ap.parse_args()
    S.set_qz_sound("vrh")
    res = run(a.workers, a.refine_top)
    with open(a.out, "w") as f:
        json.dump(res, f, separators=(",", ":"))
    m = res["meta"]
    print(f"coarse {m['n_coarse']} + refine {m['n_refine']} = {m['n_total']} in {m['runtime_s']} s")
    for r in res["top10_spm"] + res["top10_score"][:5] + [res["base5_1atm_HHO"]]:
        print(f"spm#{r['rank_spm']:4d} score#{r['rank']:4d} a {r['a_mm']:.4f} w {r['w_mm']:.4f} t2 {r['t2_um']:.3f} p {r['p_atm']} x {r['x_H2']} | "
              f"mode {r['n_mode_locks']} refl {r['n_reflection_locks']} sharp {r['n_sharp_locks']} modes {r['n_modes_window']} spm {r['sharp_per_mode']} score {r['score']} {r['stage']}")
    print("wrote", os.path.basename(a.out))


if __name__ == "__main__":
    main()
