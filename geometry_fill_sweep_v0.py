"""Geometry x rarefied-pressure sweep v0, HHO 2:1 fixed, ambient-referenced (opt-in, 2026-10-19).

Same model, lock rule, sharp definition, cascade gate and scoring as geometry_sweep_v0 (see its module doc); the fill
pressure is added as a second axis. No source: the gas sits at the ambient temperature, every mode energy is 0.
Writes only geometry_rarefied_hho_sweep_v0.json; geometry_sweep_v0.json and every default solver output are untouched.

Mix: FIXED at HHO 2:1, {'H2': 2/3, 'O2': 1/3} (the cell's fill). Off-spec mixes (1:1, 3:1, 4:1) are removed from this
script and cannot be selected; the earlier 4-mix run (0fa5d40, geometry_fill_sweep_v0.json) is disregarded: its x_H2
0.80 optimum is a chemistry artifact.
Pressure: referenced to LOCAL AMBIENT, p = factor x p_ambient, FULLY RAREFIED (every factor < 1). Factors: 9 points
evenly spaced in log p over [0.05, 0.95], factor_i = exp(ln 0.05 + i (ln 0.95 - ln 0.05)/8) = 0.0500, 0.0722, 0.1044,
0.1508, 0.2179, 0.3149, 0.4550, 0.6575, 0.9500 (step x1.4449). No golden-ratio point (none within 1 % of 1.618 or 0.618)
and none >= ambient (both asserted at import). Earlier grids are disqualified: the 5-point phi grid (0.382 .. 2.618,
incl. 1.618) and the 7-point log grid over 0.382 .. 2.618 (crosses above ambient).
Rationale (Danny, recorded, not a model result): rarefaction is suspected to bias the gas toward the ionic knee so
energy focuses across modes; pressure is the dial, but pressure heats while vacuum cools, so the rarefied regime is
also the self-cooling regime. The no-source sweep tests only the lock side of that; nothing here models ionisation or
cooling. Continuum check: at 0.05 x 1 atm the HHO mean free path (~1.5 um) stays well below the thermal boundary layer
(~24 um at 1 MHz), so gas_Q's continuum form still holds over this grid [est]. Temperature: T_gas = T_ambient.
p_ambient and T_ambient are operator-set modelling inputs for the run day (CLI --p-ambient [Pa], --T-ambient [K];
defaults AMBIENT_P_Pa / AMBIENT_T_K below; no sensor is read). Both are recorded in the JSON meta.
The gas enters everywhere through geometry_sweep_v0.evaluate(p_atm=, comp='HHO' mix, T_K=): rigid-wall B modes and bubble
round trips use c from solver_v0.gas_props(T, p, HHO); the bonded stack is gas-loaded with that c and K = gamma p
(sweep-side override of solver gas_Z for the evaluation only; the solver is not changed); gas Q per B mode =
solver_v0.gas_Q(f, a, p, T, HHO); the cascade thermal rate of B uses k/(rho cp) at (p, T). gas_props gives HHO c 533.20
m/s at 293 K vs the solver's c_hho 532.86 m/s (0.06 %); sharp counts are sensitive to that (see DESIGN_STATE).

Geometry axis: absolute box frozen on the FORMER core lattice centre (1.5/1.0/5.0), not the new G.BASE /
solver CORE (rarefied-sweep winner). LATTICE_BASE * phi^(i/8), subsampled to 4 x 4 x 3 = 48 points per pressure:
  a  i in {-16, -12, 0, 12}  -> 0.573, 0.729, 1.5, 3.087 mm
  w  i in {-16, 0, 4, 12}    -> 0.382, 1.0, 1.272, 2.058 mm
  t2 i in {-12, 0, 12}       -> 2.43, 5.0, 10.29 um
  idx [0,0,0] = former lattice centre (old base5), not the new CORE.
Coarse = 48 x 9 = 432. Refine around the top 5 coarse by sharp_per_mode (cascade gate first): each seed's geometry
+-2 lattice steps (phi^(1/4)) per axis at the seed's pressure (up to 26 new), plus the seed geometry at the neighbouring
pressure factors (+-1); clipped to the box and the pressure grid, de-duplicated. At most 140 refine points (total <= 572).
Ranking: primary (rank_spm) cascade gate, then sharp_per_mode desc, tie sharp locks; also rank (score desc, tie
distinct modes, cascade first)."""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_v0 as S  # noqa: E402
import geometry_sweep_v0 as G  # noqa: E402

# Local ambient for the run day: operator-set modelling inputs (no sensor read). Override with --p-ambient / --T-ambient.
AMBIENT_P_Pa = 101325.0
AMBIENT_T_K = 293.0
# Pressure factors x p_ambient: FULLY RAREFIED, 9 points evenly spaced in log p over [0.05, 0.95] (step x1.4449), every
# factor strictly < 1 (no positive-pressure / >= ambient point) and none within 1 % of phi or 1/phi (asserted below).
# Earlier grids (5-point phi 0.382-2.618; 7-point log 0.382-2.618, crosses ambient) are disqualified.
P_WINDOW = (0.05, 0.95)
N_P = 9
P_FACTORS = [math.exp(math.log(P_WINDOW[0]) + i * (math.log(P_WINDOW[1]) - math.log(P_WINDOW[0])) / (N_P - 1)) for i in range(N_P)]
assert not any(abs(f / G.PHI - 1) < 0.01 or abs(f * G.PHI - 1) < 0.01 for f in P_FACTORS), "golden-ratio pressure point"
assert all(f < 1.0 for f in P_FACTORS), "rarefied grid: every factor must be below ambient"
X_H2 = 2 / 3                                        # fixed: HHO 2:1
COMP = {"H2": X_H2, "O2": 1 - X_H2}
GEO_SUB = dict(a_mm=[-16, -12, 0, 12], w_mm=[-16, 0, 4, 12], t2_um=[-12, 0, 12])
REFINE_GEO_K = 2                                    # +-2 lattice steps = phi^(1/4)
AXES = ("a_mm", "w_mm", "t2_um")
BOX = {k: (lo, hi) for k, (lo, hi, st) in G.COARSE.items()}
# Lattice centre FROZEN at the former core (1.5/1.0/5.0), not G.BASE. G.BASE is now the rarefied-sweep winner;
# keeping this fixed preserves the absolute box 0.573-3.087 mm / 0.382-2.058 mm / 1.91-10.29 um and the
# ea694ce results. idx [0,0,0] = former lattice centre (old base5), not the new CORE.
LATTICE_BASE = dict(a_mm=1.5, w_mm=1.0, t2_um=5.0)
AMB = dict(p_Pa=AMBIENT_P_Pa, T_K=AMBIENT_T_K)      # set by run() before the Pool forks


def lattice_value(axis, i):
    return LATTICE_BASE[axis] * G.PHI ** (i / G.LAT)


def p_abs_Pa(pi, p_ambient=None):
    return P_FACTORS[pi] * (AMB["p_Pa"] if p_ambient is None else p_ambient)


def _ev(pt):
    gi, pi = pt
    p = p_abs_Pa(pi)
    r = G.evaluate(*(lattice_value(ax, i) for ax, i in zip(AXES, gi)), p_atm=p / 101325.0, comp=COMP, T_K=AMB["T_K"])
    r.pop("golden", None)
    r.update(idx=list(gi), p_idx=pi, p_factor=round(P_FACTORS[pi], 4), p_Pa=round(p, 1), p_atm=round(p / 101325.0, 5),
             T_K=AMB["T_K"], x_H2=round(X_H2, 4))
    return r


def spm_key(r):
    return (not r["cascade_ok"], -r["sharp_per_mode"], -r["n_sharp_locks"])


def score_key(r):
    return (not r["cascade_ok"], -r["score"], -r["n_distinct_modes"])


def _slim(r):
    return {k: r[k] for k in ("a_mm", "w_mm", "t2_um", "p_factor", "p_Pa", "p_atm", "n_mode_locks", "n_reflection_locks",
                              "n_sharp_locks", "n_modes_window", "sharp_per_mode", "score", "rank", "rank_spm", "cascade_ok", "stage")}


def run(workers=8, refine_top=5, p_ambient=AMBIENT_P_Pa, T_ambient=AMBIENT_T_K):
    import multiprocessing as mpc
    AMB.update(p_Pa=float(p_ambient), T_K=float(T_ambient))
    t0 = time.time()
    geos = [(i, j, k) for i in GEO_SUB["a_mm"] for j in GEO_SUB["w_mm"] for k in GEO_SUB["t2_um"]]
    pts = [(g, pi) for pi in range(len(P_FACTORS)) for g in geos]
    with mpc.Pool(workers) as pool:
        coarse = pool.map(_ev, pts, chunksize=4)
        for r in coarse: r["stage"] = "coarse"
        seeds = sorted(coarse, key=spm_key)[:refine_top]
        seen = set(pts); rp = []
        def add(p):
            if p not in seen: seen.add(p); rp.append(p)
        K = REFINE_GEO_K
        for s_ in seeds:
            g0, pi = tuple(s_["idx"]), s_["p_idx"]
            for di in (-K, 0, K):
                for dj in (-K, 0, K):
                    for dk in (-K, 0, K):
                        g = (g0[0] + di, g0[1] + dj, g0[2] + dk)
                        if all(BOX[ax][0] <= v <= BOX[ax][1] for ax, v in zip(AXES, g)):
                            add((g, pi))
            for dp in (-1, 1):
                if 0 <= pi + dp < len(P_FACTORS):
                    add((g0, pi + dp))
        refine = pool.map(_ev, rp, chunksize=4)
        for r in refine: r["stage"] = "refine"
    allr = coarse + refine
    for i, r in enumerate(sorted(allr, key=score_key)): r["rank"] = i + 1
    allr.sort(key=spm_key)
    for i, r in enumerate(allr): r["rank_spm"] = i + 1
    by_score = sorted(allr, key=score_key)
    p_best = []
    for pi, fct in enumerate(P_FACTORS):
        cell = [r for r in allr if r["p_idx"] == pi]
        coarse_cell = [r for r in cell if r["stage"] == "coarse"]
        p_best.append(dict(p_factor=round(fct, 4), p_Pa=round(p_abs_Pa(pi), 1), n=len(cell), best_spm=_slim(min(cell, key=spm_key)),
                           best_spm_coarse_only=_slim(min(coarse_cell, key=spm_key)), best_score=_slim(min(cell, key=score_key)),
                           top_a_mm_spm=[r["a_mm"] for r in sorted(cell, key=spm_key)[:5]]))
    per_a = {}
    for ai in GEO_SUB["a_mm"]:
        cell = [r for r in allr if r["idx"][0] == ai]
        per_a[str(round(lattice_value("a_mm", ai), 5))] = dict(
            best=_slim(min(cell, key=spm_key)),
            best_per_pressure={str(round(P_FACTORS[pi], 4)): _slim(min([r for r in cell if r["p_idx"] == pi], key=spm_key))
                               for pi in range(len(P_FACTORS))})
    pmax = max(range(len(P_FACTORS)), key=lambda i: P_FACTORS[i])     # nearest ambient (0.95): no 1.0 point on this grid
    ref = [r for r in allr if r["idx"] == [0, 0, 0] and r["p_idx"] == pmax][0]
    base5_all = [_slim(r) for r in sorted((r for r in allr if r["idx"] == [0, 0, 0]), key=lambda r: r["p_idx"])]
    gq = [r["gas_Q_first"] for r in allr if r["gas_Q_first"]]
    return dict(meta=dict(title="Geometry x rarefied-pressure sweep v0, HHO 2:1 fixed, ambient-referenced (no source)", date="2026-10-19",
                          status="search, not a prediction; v0 estimated physics; nothing measured; no source (gas at ambient T)",
                          method=__doc__, p_ambient_Pa=AMB["p_Pa"], T_ambient_K=AMB["T_K"],
                          ambient_source="operator-set modelling inputs for the run day (CLI --p-ambient/--T-ambient; defaults AMBIENT_P_Pa/AMBIENT_T_K); no sensor read",
                          mix=dict(H2=round(X_H2, 6), O2=round(1 - X_H2, 6), name="HHO 2:1 (fixed)"),
                          disregarded="0fa5d40 4-mix run (geometry_fill_sweep_v0.json): off-spec mixes, chemistry artifact",
                          p_factors=[round(f, 4) for f in P_FACTORS], p_grid="fully rarefied: 9 points log-even over [0.05, 0.95] x p_ambient, step x1.4449; every factor < 1; none within 1 % of phi or 1/phi; earlier phi grid and 0.382-2.618 log grid disqualified",
                          rationale="rarefaction suspected to bias the gas toward the ionic knee so energy focuses across modes; pressure is the dial, pressure heats while vacuum cools, so the rarefied regime is also the self-cooling regime (user hypothesis; this no-source sweep scores locks only)", p_grid_Pa=[round(p_abs_Pa(i), 1) for i in range(len(P_FACTORS))],
                          geometry_subsample={k: [round(lattice_value(k, i), 5) for i in v] for k, v in GEO_SUB.items()},
                          geometry_subsample_idx=GEO_SUB, box={k: [round(lattice_value(k, lo), 5), round(lattice_value(k, hi), 5)] for k, (lo, hi) in BOX.items()},
                          refine=f"top {refine_top} coarse by sharp_per_mode: geometry +-{REFINE_GEO_K} lattice steps (phi^(1/4)) per axis at the seed pressure, plus seed geometry at neighbouring pressure factors; clipped, de-duplicated",
                          n_coarse=len(coarse), n_refine=len(refine), n_total=len(allr), runtime_s=round(time.time() - t0, 1),
                          workers=workers, qz_sound=S.QZ_SOUND_SEL, gas_Q=G.GAS_Q_SOURCE.replace("1 atm, 293 K", "factor x p_ambient, T_ambient"),
                          gas_Q_first_range=[min(gq), max(gq)], n_cascade_fail=sum(1 for r in allr if not r["cascade_ok"]),
                          ranking="primary rank_spm: cascade gate, sharp_per_mode desc, tie sharp locks; also rank: cascade gate, score desc, tie distinct modes"),
                top10_spm=allr[:10], top10_score=by_score[:10], base5_0p95_ambient=ref, base5_per_pressure=base5_all, pressure_best=p_best,
                best_per_bubble=per_a, results=allr)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--refine-top", type=int, default=5)
    ap.add_argument("--p-ambient", type=float, default=AMBIENT_P_Pa, help="local ambient pressure [Pa] for the run day")
    ap.add_argument("--T-ambient", type=float, default=AMBIENT_T_K, help="local ambient temperature [K] for the run day")
    ap.add_argument("--out", default=os.path.join(HERE, "geometry_rarefied_hho_sweep_v0.json"))
    a = ap.parse_args()
    S.set_qz_sound("vrh")
    res = run(a.workers, a.refine_top, a.p_ambient, a.T_ambient)
    with open(a.out, "w") as f:
        json.dump(res, f, separators=(",", ":"))
    m = res["meta"]
    print(f"coarse {m['n_coarse']} + refine {m['n_refine']} = {m['n_total']} in {m['runtime_s']} s; p_ambient {m['p_ambient_Pa']} Pa, T_ambient {m['T_ambient_K']} K")
    for r in res["top10_spm"] + res["top10_score"][:5] + [res["base5_0p95_ambient"]]:
        print(f"spm#{r['rank_spm']:4d} score#{r['rank']:4d} a {r['a_mm']:.4f} w {r['w_mm']:.4f} t2 {r['t2_um']:.3f} p x{r['p_factor']} ({r['p_Pa']} Pa) | "
              f"mode {r['n_mode_locks']} refl {r['n_reflection_locks']} sharp {r['n_sharp_locks']} modes {r['n_modes_window']} spm {r['sharp_per_mode']} score {r['score']} {r['stage']}")
    print("wrote", os.path.basename(a.out))


if __name__ == "__main__":
    main()
