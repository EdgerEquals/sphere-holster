"""Ferrite Slug model v0 (Danny, 31 Oct 2026).

A square MnZn ferrite rod, 20 mm x 20 mm x 120 mm, held softly at its midpoint so it rings as a
free-free bar. A drive coil puts an AC field on the rod; a bias coil carries DC to set the operating
point. Magnetostriction turns the AC field into AC strain, and the rod's longitudinal modes
(f_n = n v / 2L, v = sqrt(E / rho)) amplify it by the mechanical Q near resonance.

EVERY material number below is a PLACEHOLDER: Danny's rod is an unknown old-radio slug. Values are
typical MnZn figures with a source where one exists. They are meant to be fitted back from his
measurements (first f_1 gives v and E/rho; amplitude vs bias gives lambda_s and the B-H curve).

Model is deliberately light:
  * mechanics: 1-D longitudinal wave in a uniform bar, free at both ends (the soft centre mount is
    treated as no constraint; it sits on the node of the odd modes).
  * magnetics: rod's internal field from the applied coil field with a demagnetising factor
    (prolate-spheroid approximation, Osborn 1945); magnetisation M = Ms tanh(chi H_in / Ms).
  * magnetostriction: isotropic quadratic law lambda = 1.5 lambda_s (M/Ms)^2, linearised about the
    DC bias -> d = d(lambda)/d(H_applied), the strain per unit AC field.
Temperatures are kelvin internally.

Run:  python3 slug/model.py          -> writes slug/slug_data_v0.json and prints a summary
      python3 slug/model.py --build  -> also rebuilds index.html via slug/build.py
"""
import json, math, os, sys, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MU0 = 4e-7 * math.pi
MM = 1e-3

# Frequency window reused from the sphere work (solver_v0.py FMIN_HZ / FMAX_HZ, Danny t382).
FMIN_HZ = 1.0
FMAX_HZ = 50e6

# ---------------------------------------------------------------------------------------------
# Geometry (Danny, 31 Oct 2026): measured by Danny, not a placeholder.
# ---------------------------------------------------------------------------------------------
GEOM = dict(width_mm=20.0, height_mm=20.0, length_mm=120.0)

# ---------------------------------------------------------------------------------------------
# Material: ALL PLACEHOLDERS (generic MnZn). value, unit, source.
# ---------------------------------------------------------------------------------------------
PLACEHOLDER = "PLACEHOLDER"
MATERIAL = {
    "rho":       dict(v=4800.0,  unit="kg/m^3", src="TDK PC50 datasheet, density 4.8e3 kg/m^3; Ferroxcube MnZn 4750-5000"),
    "E":         dict(v=120e9,   unit="Pa",     src="Ferroxcube 'Ferrite mechanical & thermal properties': MnZn Young's modulus 90-150 GPa (mid value)"),
    "nu":        dict(v=0.30,    unit="1",      src="no source; typical ceramic Poisson ratio (only used for the small Rayleigh correction)"),
    "Q_mech":    dict(v=500.0,   unit="1",      src="no source; guess, to be measured from the -3 dB width of f_1"),
    "mu_i":      dict(v=2300.0,  unit="1",      src="TDK PC40 typical initial permeability 2300 (old radio slugs may be far lower, or NiZn)"),
    "Bs":        dict(v=0.47,    unit="T",      src="TDK PC50 datasheet, Bs 470 mT at 25 C, H = 1194 A/m"),
    "lambda_s":  dict(v=-0.6e-6, unit="1",      src="TDK PC40/PC200 datasheet lambda_s = -0.6e-6; Szewczyk et al., Materials 11 (2018) 1894 report |lambda_s| ~0.6e-6 with a sign change near 0.35 T"),
    "resist":    dict(v=5.0,     unit="ohm m",  src="Ferroxcube MnZn rho_DC ~0.5-10 ohm m (mid value)"),
    "tan_d_mag": dict(v=0.01,    unit="1",      src="no source; guess for magnetic loss tangent at ~20 kHz"),
    "T_curie":   dict(v=493.0,   unit="K",      src="Ferroxcube 3C90 Tc >= 220 C (493 K)"),
}
T_OP_K = 293.0   # operating temperature, kelvin (room)

# ---------------------------------------------------------------------------------------------
# Coils: PLACEHOLDER defaults. Positions are the coil centre as a fraction of L from one end.
# ---------------------------------------------------------------------------------------------
COILS = {
    "drive": dict(turns=50,  length_mm=40.0, inner_mm=24.0, centre_frac=0.5, I_A=0.5,  kind="AC", src=PLACEHOLDER),
    "bias":  dict(turns=200, length_mm=100.0, inner_mm=30.0, centre_frac=0.5, I_A=1.0, kind="DC", src=PLACEHOLDER),
}


def mat(k):
    return MATERIAL[k]["v"]


def area_m2(g=GEOM):
    return g["width_mm"] * g["height_mm"] * MM * MM


def bar_speed(E=None, rho=None):
    """Thin-bar longitudinal speed v = sqrt(E/rho)."""
    E = mat("E") if E is None else E
    rho = mat("rho") if rho is None else rho
    return math.sqrt(E / rho)


def textbook_freqs(n_max=5, L=None, v=None):
    """Free-free bar: f_n = n v / (2 L)."""
    L = GEOM["length_mm"] * MM if L is None else L
    v = bar_speed() if v is None else v
    return [n * v / (2 * L) for n in range(1, n_max + 1)]


def rayleigh_factor(n, L=None, g=GEOM, nu=None):
    """Rayleigh lateral-inertia correction f_n ~ f_n0 * (1 - (n pi nu r_g / L)^2 / 2), r_g = polar
    radius of gyration of the section (square side a: r_g^2 = a^2/6). Small for this rod."""
    L = GEOM["length_mm"] * MM if L is None else L
    nu = mat("nu") if nu is None else nu
    a, b = g["width_mm"] * MM, g["height_mm"] * MM
    rg2 = (a * a + b * b) / 12.0
    return 1.0 - 0.5 * (n * math.pi * nu) ** 2 * rg2 / (L * L)


def fe_modes(n_el=400, n_modes=5, L=None, E=None, rho=None, A=None):
    """Independent numeric check: linear finite elements for the 1-D free-free bar, solve
    K u = w^2 M u. Returns the first n_modes non-zero frequencies and mode shapes."""
    L = GEOM["length_mm"] * MM if L is None else L
    E = mat("E") if E is None else E
    rho = mat("rho") if rho is None else rho
    A = area_m2() if A is None else A
    h = L / n_el
    N = n_el + 1
    K = np.zeros((N, N)); M = np.zeros((N, N))
    ke = E * A / h * np.array([[1, -1], [-1, 1]])
    me = rho * A * h / 6 * np.array([[2, 1], [1, 2]])
    for e in range(n_el):
        K[e:e + 2, e:e + 2] += ke; M[e:e + 2, e:e + 2] += me
    Li = np.linalg.cholesky(M); Linv = np.linalg.inv(Li)
    w2, V = np.linalg.eigh(Linv @ K @ Linv.T)
    V = Linv.T @ V
    idx = np.argsort(w2)[1:n_modes + 1]       # drop the rigid-body mode
    f = np.sqrt(np.maximum(w2[idx], 0)) / (2 * math.pi)
    shapes = V[:, idx].T
    shapes = [s / np.max(np.abs(s)) for s in shapes]
    return list(f), [list(np.round(s[::max(1, n_el // 60)], 4)) for s in shapes]


def demag_factor(g=GEOM):
    """Axial demagnetising factor, prolate-spheroid approximation (Osborn, Phys. Rev. 67, 351, 1945)
    with the rod replaced by a circle of equal area: m = L / d_eq."""
    d_eq = 2 * math.sqrt(area_m2(g) / math.pi)
    m = GEOM["length_mm"] * MM / d_eq
    s = math.sqrt(m * m - 1)
    return (m / s * math.log(m + s) - 1) / (m * m - 1), m


def coil_centre_field(c):
    """On-axis field at the centre of a finite solenoid: H = N I / sqrt(l^2 + D^2), D = coil
    diameter (inner diameter used). A/m."""
    l, D = c["length_mm"] * MM, c["inner_mm"] * MM
    return c["turns"] * c["I_A"] / math.sqrt(l * l + D * D)


def magnetisation(H_app, Nd=None):
    """Solve M = Ms tanh(chi (H_app - Nd M) / Ms) by bisection. Returns M, H_in, slope dM/dH_app."""
    Nd = demag_factor()[0] if Nd is None else Nd
    chi = mat("mu_i") - 1; Ms = mat("Bs") / MU0
    sgn = 1 if H_app >= 0 else -1; Ha = abs(H_app)
    lo, hi = 0.0, min(Ms, Ha / Nd if Nd > 0 else Ms)
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if mid < Ms * math.tanh(chi * (Ha - Nd * mid) / Ms): lo = mid
        else: hi = mid
    M = 0.5 * (lo + hi)
    x = chi * (Ha - Nd * M) / Ms
    sech2 = 1 - math.tanh(x) ** 2
    dM_dHin = chi * sech2
    dM_dHa = dM_dHin / (1 + Nd * dM_dHin)
    return sgn * M, sgn * (Ha - Nd * M), dM_dHa


def strain_coeff(H_bias):
    """Linearised magnetostriction about the bias: d = d(lambda)/d(H_applied) = 3 lambda_s (M/Ms^2) dM/dH_a.
    Strain per (A/m) of applied AC field."""
    Ms = mat("Bs") / MU0
    M, Hin, dM = magnetisation(H_bias)
    return 3 * mat("lambda_s") * M / (Ms * Ms) * dM, M / Ms


def modal_coupling(n, c, L=None):
    """Fraction of a uniform magnetostrictive strain eps over the coil region [x1,x2] that reaches
    mode n. For phi_n = cos(n pi x / L), the generalised force is E A (phi_n(x2) - phi_n(x1)) eps.
    Returned as the ratio to the full-length odd-mode value |phi_n(L) - phi_n(0)| = 2."""
    L = GEOM["length_mm"] * MM if L is None else L
    half = 0.5 * min(c["length_mm"] * MM, L)
    x0 = c["centre_frac"] * L
    x1, x2 = max(0.0, x0 - half), min(L, x0 + half)
    phi = lambda x: math.cos(n * math.pi * x / L)
    return abs(phi(x2) - phi(x1)) / 2.0


def end_amplitude(n, H_bias, drive=None, Q=None):
    """Peak end displacement (m) of mode n at its resonance for the drive coil's AC peak field.
    Static modal end displacement for uniform eps over the full length is 4 L eps / (n^2 pi^2);
    scaled by modal_coupling and Q."""
    drive = COILS["drive"] if drive is None else drive
    Q = mat("Q_mech") if Q is None else Q
    L = GEOM["length_mm"] * MM
    h_ac = coil_centre_field(drive)
    d, m = strain_coeff(H_bias)
    eps = abs(d) * h_ac
    return Q * modal_coupling(n, drive) * 4 * L * eps / (n * n * math.pi ** 2), eps, d, m


def skin_depth(f):
    return math.sqrt(mat("resist") / (math.pi * f * MU0 * mat("mu_i")))


def run(n_modes=5):
    L = GEOM["length_mm"] * MM
    v = bar_speed()
    tb = textbook_freqs(n_modes)
    fe, shapes = fe_modes(n_modes=n_modes)
    ray = [tb[i] * rayleigh_factor(i + 1) for i in range(n_modes)]
    Nd, aspect = demag_factor()
    mu_app = mat("mu_i") / (1 + Nd * (mat("mu_i") - 1))
    Ms = mat("Bs") / MU0
    chi = mat("mu_i") - 1
    bias = COILS["bias"]
    H_per_A = coil_centre_field(dict(bias, I_A=1.0))
    # Bias sweep in applied field; also expressed as bias-coil current.
    Hs = np.linspace(0, 3 * Ms / chi * (1 + Nd * chi), 241)
    curve = []
    for H in Hs:
        amp, eps, d, m = end_amplitude(1, H)
        curve.append(dict(H=round(float(H), 3), I=round(float(H / H_per_A), 5), d=d, m=round(m, 5), amp_m=amp, eps=eps))
    best = max(curve, key=lambda r: r["amp_m"])
    modes = []
    for i in range(n_modes):
        n = i + 1
        mid_disp = abs(math.cos(n * math.pi / 2))
        modes.append(dict(n=n, f_textbook=tb[i], f_fe=fe[i], f_rayleigh=ray[i],
                          node_at_mount=mid_disp < 1e-9, coupling_drive=modal_coupling(n, COILS["drive"]),
                          amp_best_bias_m=end_amplitude(n, best["H"])[0], shape=shapes[i]))
    sanity = dict(f1_textbook=tb[0], f1_fe=float(fe[0]), rel_err=float(abs(fe[0] - tb[0]) / tb[0]), tol=1e-3)
    sanity["pass"] = bool(sanity["rel_err"] < sanity["tol"])
    return dict(model="Ferrite Slug", version="v0", geometry=GEOM, material=MATERIAL, coils=COILS,
                T_op_K=T_OP_K, window_Hz=[FMIN_HZ, FMAX_HZ], v_bar=v, L_m=L, demag=dict(Nd=Nd, aspect=aspect, mu_apparent=mu_app),
                bias_H_per_A=H_per_A, drive_h_ac=coil_centre_field(COILS["drive"]),
                skin_depth_f1_m=skin_depth(tb[0]), half_width_m=GEOM["width_mm"] * MM / 2,
                modes=modes, bias_curve=curve, best_bias=best, sanity=sanity)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    d = run()
    with open(os.path.join(HERE, "slug_data_v0.json"), "w") as f:
        json.dump(d, f, indent=1)
    print(f"Ferrite Slug v0  (ALL MATERIAL VALUES ARE PLACEHOLDERS)")
    print(f"v_bar = {d['v_bar']:.1f} m/s  L = {d['L_m']} m")
    for m in d["modes"]:
        print(f"  n={m['n']}: textbook {m['f_textbook']:.1f} Hz | FE {m['f_fe']:.1f} Hz | Rayleigh-corrected {m['f_rayleigh']:.1f} Hz"
              f" | node at mount: {m['node_at_mount']} | drive coupling {m['coupling_drive']:.3f}")
    s = d["sanity"]
    print(f"sanity f1: FE {s['f1_fe']:.2f} vs textbook {s['f1_textbook']:.2f} Hz, rel err {s['rel_err']:.2e} -> {'PASS' if s['pass'] else 'FAIL'}")
    dm = d["demag"]; b = d["best_bias"]
    print(f"demag Nd = {dm['Nd']:.4f} (aspect {dm['aspect']:.2f}), apparent rod permeability {dm['mu_apparent']:.1f}")
    print(f"bias coil: {d['bias_H_per_A']:.0f} A/m per A; drive h_ac = {d['drive_h_ac']:.1f} A/m peak")
    print(f"best bias: H_app {b['H']:.0f} A/m = {b['I']:.2f} A in bias coil, M/Ms {b['m']:.3f}, d {b['d']:.3e} 1/(A/m), "
          f"f1 end amplitude {b['amp_m']*1e9:.2f} nm (Q={mat('Q_mech'):.0f})")
    print(f"skin depth at f1 = {d['skin_depth_f1_m']*1e3:.0f} mm vs half-width {d['half_width_m']*1e3:.0f} mm")
    if not s["pass"]:
        sys.exit(1)
    if a.build:
        import subprocess; subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True)


if __name__ == "__main__":
    main()
