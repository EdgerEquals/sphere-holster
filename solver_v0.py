#!/usr/bin/env python3
"""
Stratified bubble sphere - multi-domain radial coupled solver, v0 (2026-10-19)
==============================================================================
ESTIMATED PHYSICS. Paper model, nothing measured. Every material number carries a tag:
  [lit]  literature value already cited in a box report      [rec] reused from a box report
  [calc] computed here                                         [est] my estimate (not sourced)

What it does (per geometry preset x circulating power level):
  OPTICAL   radial 1-D radiative march per band (H-gamma 434, H-beta 486, H-alpha 656 nm + Cr3+ 770 nm
            downshifted band): absorption + scattering per layer, phosphor ground-state saturation,
            smoky-quartz colour centres with thermal bleaching, quantum-defect heat.  (No full-wave Maxwell.)
  ACOUSTIC  exact l=0 (breathing / radial) multilayer elastic spherical-shell model (spherical Bessel
            transfer matrices), eigenmodes, mode shapes, energy partition -> Q_eff, peak stress at P_circ.
            Two configurations: 'isolated' (quartz + thin films, free at the Gd-Dy surface) and 'bonded'
            (whole stack to the ferrite). l>=1 spheroidal/torsional frequencies are NOT computed in v0;
            they are read (read-only) from shell_phi_sweep_calc_output.txt where available.
  ELECTRIC  NO DRIVE MECHANISM DEFINED [retired 2026-10-19: the BTO capacitor between metal films, the LC tank and
            the bare-shell discharge field were electrode-based and are removed]. Electric fields, dielectric loss = 0.
  MAGNETIC  no drive defined: ferrite field and loss = 0 (the ferrite shell stays as a material layer).
  THERMAL   1-D radial spherical finite-volume, implicit, k(T) for quartz, interface resistances,
            outer surface held at 293 K (reference only - no heat sink is chosen here).
  COUPLING  staggered, timescale-separated: fast domains (optical ps, acoustic/electric/magnetic us-ms)
            are solved quasi-statically and handed to the thermal transient as heat sources; temperature
            feeds back (phosphor quench, smoky bleaching, BTO eps(T)/Curie, quartz k(T)) at each macro step.
Outputs model_data_v0.json and (with --build) index.html (viewer_template.html + embedded JSON).
"""
import json, math, re, os, sys, argparse
import numpy as np
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
THREAD = os.path.dirname(HERE)
PHI = (1 + 5 ** 0.5) / 2
EPS0, MU0, C0 = 8.8541878128e-12, 4e-7 * math.pi, 299792458.0
T_REF = 293.0
UM, MM = 1e-6, 1e-3

# ----------------------------------------------------------------------------------------------
# Geometry presets. core_d = gas (HHO) bubble inner diameter; wall = crystal-quartz layer-one wall.
# Layer two (elbaite sol-gel) inner diameter = quartz OD.  Edit / add presets freely.
# ----------------------------------------------------------------------------------------------
PRESETS = [
    dict(id="base5", label="Baseline 5.00 mm OD (core r 1.5 mm, wall 1 mm, 1 atm HHO)", core_d=3.0, wall=1.0, p_atm=1.0, group="lock"),
    dict(id="lock54", label="Layer-1 lock A: 5.4 mm bubble, 1 atm HHO (wall 1 mm assumed)", core_d=5.4 - 2.0, wall=1.0, p_atm=1.0, group="lock",
         note="Read as quartz OD 5.4 mm with the 1 mm wall kept -> gas diameter 3.4 mm. If 5.4 mm is the gas diameter, rerun with --core-d 5.4."),
    dict(id="lock25", label="Layer-1 lock B: 2.5 mm bubble, 100 atm HHO (wall 1 mm assumed)", core_d=2.5 - 2.0, wall=1.0, p_atm=100.0, group="lock",
         note="Read as quartz OD 2.5 mm with the 1 mm wall kept -> 0.5 mm gas bore (geometry B of earlier reports). If 2.5 mm is the gas diameter, rerun with --core-d 2.5."),
]
# Minimal test (Danny): 1 mm ID HHO 2:1 at the Paschen knee (~10 Torr for a 1 mm gap), bare crystal-quartz shell; no drive mechanism defined
PRESETS.insert(0, dict(id="minA", label="Minimal test A: 1 mm ID, 1 mm wall, 3 mm OD, bare quartz, HHO 10 Torr (Paschen knee)", core_d=1.0, wall=1.0, p_atm=10/760, group="minimal", bare=True))
PRESETS.insert(0, dict(id="scope", label="Danny scope: 1 mm ID x 2 mm OD quartz, HHO, fill OPEN (3-D views: 10 Torr placeholder)", core_d=1.0, wall=0.5, p_atm=10/760, group="minimal", bare=True,
                       note="fill amount is open: the 3-D/steady views use 10 Torr only as a placeholder; the Drive panel computes the coupled single-cycle response for the fill you enter"))
PRESETS.insert(2, dict(id="minB", label="Minimal test B: 1 mm ID, 0.5 mm wall, 2 mm OD, bare quartz, HHO 10 Torr (Paschen knee)", core_d=1.0, wall=0.5, p_atm=10/760, group="minimal", bare=True))
for od in [1.6, 2.59, 4.19, 6.78, 10.97, 17.75]:   # golden-ratio OD sweep, case A scaling (core 0.6 OD, wall 0.2 OD) [rec shell_phi_sweep]
    PRESETS.append(dict(id=f"phi{od}", label=f"Phi sweep OD {od} mm (core 0.6*OD, wall 0.2*OD, 1 atm)", core_d=0.6 * od, wall=0.2 * od, p_atm=1.0, group="phi"))

POWERS = [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]   # W, decade steps (ascending)

# ----------------------------------------------------------------------------------------------
# Materials. rho kg/m3, cp J/kgK, k W/mK, cL/cT m/s, Q mechanical, optics dict mu_abs/mu_sca [1/m]
# ----------------------------------------------------------------------------------------------
def k_quartz(T):  # [rec power scaling: k(T)=6.2*(300/T), perpendicular-c, est from EJM 33,23 (2021)]
    return 6.2 * 300.0 / np.maximum(T, 150.0)

MAT = {
 "quartz":   dict(name="Crystal quartz (layer one)", rho=2650, cp=740, k=6.2, cL=6153, cT=4210, Q=2100, n=1.554,
                  tags="rho,cp,k [rec BTO report]; cL,cT isotropic VRH [rec shell_phi_sweep]; Q 2100 [rec]; n_o 434 [rec]"),
 "layer2":   dict(name="Layer two: 50 nm Fe-poor elbaite 20 vol% in 80:20 MTES:TEOS", rho=2300, cp=800, k=0.91, cL=3600, cT=2200, Q=150, n=1.42,
                  tags="k 0.91 mid (0.52-1.59) [rec Layer2]; cL mid of 2.6-4.7 km/s [rec binder est]; cT=0.6 cL [est]; rho [est]; Q 50-500 -> 150 [est]"),
 "phos_in":  dict(name="Inner phosphor 20 um, Cr3+ garnet (CSSG-type) in sol-gel/PiG", rho=3500, cp=700, k=1.0, cL=5000, cT=3000, Q=100, n=1.8,
                  tags="k 1.0 [rec est]; rho,cp,cL,cT,Q [est]"),
 "bto":      dict(name="BaTiO3 film 2 um (hydrothermal crystalline)", rho=6020, cp=437, k=1.35, cL=5000, cT=2700, Q=50, n=2.4,
                  tags="rho,cp,k [rec]; E~110 GPa [rec est] -> cL,cT [est]; Q~1/tan d=50 [rec]"),
 "gddy":     dict(name="Gd-Dy film 3 um (MCE ~260 K)", rho=8080, cp=270, k=7.3, cL=2950, cT=1680, Q=500, n=None,
                  tags="rho,cp,k [rec]; E~55 GPa [est]; Q [est]"),
 "calorivac":dict(name="CALORIVAC ladder, epoxy-bonded granules", rho=5000, cp=500, k=1.0, cL=1800, cT=900, Q=20, n=None,
                  tags="k_eff 1.0 (0.5-2) [rec est]; rho,cp,cL,cT,Q [est] (epoxy-dominated, lossy)"),
 "phos_out": dict(name="Outer phosphor 30 um in silicone", rho=1500, cp=1200, k=0.2, cL=1000, cT=25, Q=10, n=1.41,
                  tags="k 0.2 [rec est]; others [est]"),
 "ferrite":  dict(name="NiZn ferrite shell (Fair-Rite 61-type, mu_i 125)", rho=5000, cp=700, k=4.0, cL=6000, cT=3500, Q=500, n=None,
                  tags="mu_i 125, Q_f(f) [rec HighQ_MHz]; rho,cp,k,cL,cT,Q_mech [est, NiZn-typical]"),
}
INTERFACE_R = 3e-8   # m2K/W [rec]

# Optical bands. Relative Balmer powers: case-B recombination ratios Ha/Hb 2.86, Hg/Hb 0.47 [lit, Osterbrock & Ferland 2006]
# used ONLY as a placeholder spectrum (a 1-3 mm HHO discharge is not case B) [est].
BANDS = [dict(nm=434.0, w=0.47), dict(nm=486.1, w=1.0), dict(nm=656.3, w=2.86)]
LAM_CR = 770.0                      # CSSG:Cr emission peak [rec ladder]
QY_CR = 0.778                       # IQE measured [rec ladder]
I_SAT_CR = 7.6e4 * 1e4              # W/m2; geometric mid of 2.4e4-2.4e5 W/cm2 [rec, cross-section est]
ALPHA_PHOS = 1.0e5                  # 1/m (1000 /cm) inner phosphor small-signal absorption [est]
ALPHA_METAL = 8.8e7                 # 1/m visible absorption of the metallic layers (Gd-Dy, CALORIVAC, ferrite) [est, metal-typical k~3.5]
L2_MU_EXT = {434.0: 106e2, 486.1: 68e2, 656.3: 22e2, 770.0: 15e2}  # 1/m direct extinction, P0.07 phi0.2 [rec Layer2; 770 est]
L2_MU_ABS = 0.9e2 * math.log(10) / 2.3026   # <=0.9 /cm absorption [rec Layer2]
SMOKY_ALPHA = {434.0: 50.0, 486.1: 50.0, 656.3: 30.0, 770.0: 5.0}   # 1/m (0.5/0.5/0.3 /cm) [est, dose-dependent; bands rec Coloured_Piezo]
SMOKY_BLEACH_K = 473.0              # colour bleaches ~200-300 C [rec]

# Electric [rec power scaling / BTO report]
BTO_T = 2 * UM; EPSR0 = 450.0; TAND = 0.02; PS = 0.115; E_WORK = 42e6; T_CURIE = 393.0
# Magnetic [rec HighQ_MHz: Fair-Rite 61 Q vs f]; B_sat est
FERR_MU = 125.0
FERR_QF = [(1e4, 260), (3e5, 260), (1e6, 190), (2.5e6, 155), (5e6, 130), (1e7, 62), (2e7, 4.6)]
B_SAT = 0.25     # T [est, NiZn-typical 0.2-0.35]
N_TURNS = 1; THETA0 = math.radians(10)   # meridional winding, polar feed holes +-10 deg [est]
F_WALL = 0.10    # fraction of P_circ landing on quartz inner wall as plasma heat [rec bracket 0.1-1.0]
F_OPT = 0.90     # fraction of P_circ leaving core as Balmer light [est scenario, as power-scaling 2.4]

def ferrite_Q(f):
    fs, qs = zip(*FERR_QF)
    return float(np.exp(np.interp(np.log(f), np.log(fs), np.log(qs))))

# ----------------------------------------------------------------------------------------------
def build_stack(core_d_mm, wall_mm, bare=False):
    r_in = core_d_mm / 2 * MM
    r_q = r_in + wall_mm * MM
    L = []
    if bare:
        L.append(("quartz", r_in, r_q))
        return dict(r_in=r_in, r_q=r_q, r_B=r_q, layers=L, bare=True, stations=[r_q * PHI ** j for j in range(-3, 2) if r_q * PHI ** j > 0.05 * r_in])
    def add(key, t):
        r0 = L[-1][2] if L else r_in
        L.append((key, r0, r0 + t))
    add("quartz", wall_mm * MM); add("layer2", 5 * UM); add("phos_in", 20 * UM); add("bto", BTO_T)
    r_B = L[-1][2]                       # first phi step starts at the BTO outer boundary [Danny rule, rec BTO report]
    add("gddy", 3 * UM)
    r1, r2 = r_B * PHI, r_B * PHI ** 2   # phi-stepped thick zones [v0 layout assumption]
    add("calorivac", r1 - 30 * UM - L[-1][2]); add("phos_out", 30 * UM); add("ferrite", r2 - r1)
    stations = [r_B * PHI ** j for j in range(-4, 3)]
    return dict(r_in=r_in, r_q=r_q, r_B=r_B, layers=L, bare=False, stations=[s for s in stations if s > 0.05 * r_in])

def make_grid(stack):
    pts, mat = [], []
    for key, a, b in stack["layers"]:
        t = b - a
        n = 40 if key in ("quartz", "calorivac", "ferrite") else 4
        edges = np.linspace(a, b, n + 1)
        for i in range(n):
            pts.append((edges[i], edges[i + 1])); mat.append(key)
    return pts, mat

# ------------------------------------------------- ACOUSTIC (l = 0, exact multilayer) ---------
def lame(m, lossy=False):
    p = MAT[m]; mu = p["rho"] * p["cT"] ** 2; M = p["rho"] * p["cL"] ** 2
    if lossy:
        mu = mu * (1 + 1j / p["Q"]); M = M * (1 + 1j / p["Q"])
    return M - 2 * mu, mu, M, p["rho"]

def sph(x):
    s, c = np.sin(x), np.cos(x)
    j0, y0 = s / x, -c / x
    j1, y1 = s / x ** 2 - c / x, -c / x ** 2 - s / x
    return j0, j1, y0, y1

def Smat(r, w, m, lossy=False):
    lam, mu, M, rho = lame(m, lossy)
    k = w * np.sqrt(rho / M); x = k * r
    j0, j1, y0, y1 = sph(x)
    dj, dy = k * (j0 - 2 * j1 / x), k * (y0 - 2 * y1 / x)
    return np.array([[j1, y1], [M * dj + 2 * lam * j1 / r, M * dy + 2 * lam * y1 / r]])

def propagate(f, layers, lossy=False):
    w = 2 * math.pi * f
    P = np.eye(2, dtype=complex if lossy else float)
    for m, a, b in layers:
        P = Smat(b, w, m, lossy) @ np.linalg.inv(Smat(a, w, m, lossy)) @ P
    return P

GAS = dict(p=101325.0, T=None)
# ---- CHEMICAL domain constants ----
EV, NA_, KB_ = 1.602176634e-19, 6.02214076e23, 1.380649e-23
E_D_H2 = 4.478 * EV          # H2 bond dissociation energy D0 [lit, NIST CCCBDB / Huber & Herzberg]
E_D_O2 = 5.116 * EV          # O2 D0 [lit, same]; listed for reference
DH_H2O = 241.826e3 / NA_     # J per H2O formed: -dHf H2O(g) = 241.826 kJ/mol (LHV basis) [lit, NIST Chemistry WebBook]
ETA_DISS = 0.2               # fraction of gas-deposited discharge energy spent on dissociation [PLACEHOLDER est]
NU_CHAIN = 1.0               # H2O formed per H2 dissociated below autoignition [PLACEHOLDER est]; >>1 once H+O2->OH+O branching runs away
WALL_RECOMB = 0.5            # share of dissociation energy returned by surface recombination on the inner quartz wall [PLACEHOLDER est]
D_H_1ATM = 1.5e-4            # m2/s, H-atom diffusivity in the H2/O2 mix at 1 atm, 293 K [PLACEHOLDER est]; D ~ 1/p
def chem_state(p_seal, a, P_gas):
    V = 4 / 3 * math.pi * a ** 3; N = p_seal * V / (KB_ * T_REF); N_H2 = 2 * N / 3
    R_d = ETA_DISS * P_gas / E_D_H2; R_w = NU_CHAIN * R_d
    t_conv = N_H2 / R_w if R_w > 0 else float("inf")
    E_store = (N / 3) * 2 * DH_H2O
    D = D_H_1ATM * 101325.0 / max(p_seal, 1.0)
    return dict(N=N, R_diss=R_d, R_water=R_w, t_conv=t_conv, E_store=E_store, P_release=(E_store / t_conv if t_conv > 0 else 0.0),
                D_H=D, tau_D=a * a / (math.pi ** 2 * D), P_diss=ETA_DISS * P_gas, P_wall_recomb=WALL_RECOMB * ETA_DISS * P_gas)
K_HHO0, CP_HHO = 0.1114, 2423.0   # W/m/K and J/kg/K at 293 K [rec layer1_lock_phi_calc_output]; k ~ T^0.75 [est]
def gas_T_profile(Tw, P_cond, a, rs):
    """steady gas temperature in the core: heat P_cond released uniformly in the gas, conducted to the wall at Tw.
    Kirchhoff transform with k = k0 (T/293)^0.75: theta(T) = k0*293/1.75*(T/293)^1.75; theta(r) = theta(Tw) + q (a^2 - r^2)/6, q = P_cond/V.
    Continuum conduction (Kn ~ 0.01 at 10 Torr for a 0.5 mm core); uniform deposition [est]; capped at 3000 K."""
    q = P_cond / (4 / 3 * math.pi * a ** 3); T0 = 293.0; c = K_HHO0 * T0 / 1.75
    th_w = c * (Tw / T0) ** 1.75
    return [min(T0 * ((th_w + q * (a * a - r * r) / 6) / c) ** (1 / 1.75), 3000.0) for r in rs]
# ---- Sound speeds (v0.3) ----
# Crystal-quartz acoustic speeds, selectable (--qz-sound). Every value carries its source.
QZ_SOUND = {
    "vrh":   dict(cL=6048.0, cT=4090.0, label="alpha-quartz isotropic VRH aggregate",
                  src="[lit] Schmitt 2015, Treatise on Geophysics 2nd ed. vol 11, 'Geophysical properties of the near surface Earth: seismic properties', Table 2 (alpha-quartz rho 2648, K 37.8, mu 44.3 GPa -> VP 6048, VS 4090 m/s); cf. Mavko, Mukerji & Dvorkin, Rock Physics Handbook (K 37, mu 44 GPa -> 6008/4075 m/s)"),
    "z":     dict(cL=6330.0, cT=4685.0, label="single crystal, along Z (c-axis)",
                  src="[lit] cL 6.33(3) km/s Z-cut: J. Appl. Phys. 44, 5 (1973), doi:10.1063/1.1661916 (agrees with McSkimin, JASA 34, 1271 (1962)); cT = sqrt(C44/rho) = sqrt(58.14 GPa/2649) [calc from lit C44: Ohno et al., J. Appl. Phys. 100, 2006, doi:10.1063/1.2335684]"),
    "x":     dict(cL=5710.0, cT=5200.0, label="single crystal, along X",
                  src="[lit] X-cut cL 5.71(5), cT 5.20(5) km/s (one of the two transverse branches): J. Appl. Phys. 44, 5 (1973), doi:10.1063/1.1661916"),
    "danny": dict(cL=5900.0, cT=4090.0, label="Danny's value",
                  src="cL 5900 m/s [given by Danny]; cT 4090 m/s taken from the VRH entry [lit Schmitt 2015] because no shear value was given"),
    "v0":    dict(cL=6153.0, cT=4210.0, label="v0/v0.2 value",
                  src="[rec shell_phi_sweep] isotropic VRH as used by the other worker's sweep; superseded in v0.3 by the cited VRH entry"),
}
QZ_SOUND_SEL = "vrh"
def set_qz_sound(key):
    global QZ_SOUND_SEL
    QZ_SOUND_SEL = key; MAT["quartz"]["cL"] = QZ_SOUND[key]["cL"]; MAT["quartz"]["cT"] = QZ_SOUND[key]["cT"]
    MAT["quartz"]["tags"] = re.sub(r"cL,cT [^;]*;", "cL,cT " + key + " " + QZ_SOUND[key]["src"].replace(";", ",") + ";", MAT["quartz"]["tags"])
# HHO gas: c(T) = sqrt(gamma R T / M), ideal gas.
#   M = (2 x 2.016 + 32.00)/3 g/mol = 12.01 g/mol [calc; molar masses from IUPAC standard atomic weights H 1.008, O 15.999]
#   gamma = 1.40 [lit-typical: H2 and O2 are both ~1.40 near 300 K (NIST Chemistry WebBook, Thermophysical Properties of Fluid Systems);
#   a 2:1 mix of two gamma~1.4 diatomics stays ~1.40 [calc]; falls as vibration opens above ~1000 K, not modelled [est]]
#   R = 8.314462618 J/mol/K [lit CODATA]. -> 533 m/s at 293 K, c ~ sqrt(T).
def c_hho(T):
    """ideal-gas sound speed of HHO 2H2:O2: c = sqrt(gamma R T / M), M = (2*2.016+32.00)/3 = 12.01 g/mol [calc from lit molar masses],
    gamma 1.40 [est, diatomic mix near room T; falls slowly as vibrational modes open above ~1000 K, not modelled]. 533 m/s at 293 K."""
    return math.sqrt(1.4 * 8.314 * T / 0.012011)
def gas_Z(f, r_in):
    """sigma_rr/u_r presented by the HHO gas column (2:1 H2:O2, M 12.01 g/mol, gamma 1.4 [est]) times j1 (pole-free form).
    Gas temperature GAS['T'] is a COMPUTED state (coupled): fixed atom count and volume => p = p_seal * T / T_seal, c = c_hho(T)."""
    Tg = GAS["T"] or T_REF
    c = c_hho(Tg); K = 1.4 * GAS["p"]
    k = 2 * math.pi * f / c; x = k * r_in
    return -K * k * math.sin(x) / x, (math.sin(x) / x ** 2 - math.cos(x) / x)   # (num ~ K k j0, den ~ j1)
def l0_char(f, layers):
    P = propagate(f, layers); num, den = gas_Z(f, layers[0][1])
    return P[1, 0] * den + P[1, 1] * num
def l0_modes(layers, fmax=12e6, n=4000):
    fs = np.linspace(2e4, fmax, n)
    g = np.array([l0_char(f, layers) for f in fs])
    out = []
    for i in range(n - 1):
        if np.sign(g[i]) != np.sign(g[i + 1]):
            try:
                f0 = brentq(lambda f: l0_char(f, layers), fs[i], fs[i + 1], xtol=1.0)
                out.append(f0)
            except ValueError:
                pass
    return out

def mode_fields(f, layers, rgrid_layers, lossy=False, p_in=0.0):
    """state at r_in = [u0, sigma_rr]. free mode: [1,0]. forced: solve u0 from outer traction-free."""
    w = 2 * math.pi * f
    if p_in:
        P = propagate(f, layers, lossy)
        u0 = P[1, 1] * p_in / P[1, 0]
        state = np.array([u0, -p_in], dtype=complex)
    else:
        state = np.array([1.0, 0.0], dtype=complex if lossy else float)
    res = []
    for (m, a, b), rs in zip(layers, rgrid_layers):
        Sa = Smat(a, w, m, lossy); AB = np.linalg.solve(Sa, state)
        lam, mu, M, rho = lame(m, lossy)
        k = w * np.sqrt(rho / M)
        for r in rs:
            x = k * r; j0, j1, y0, y1 = sph(x)
            u = AB[0] * j1 + AB[1] * y1
            du = AB[0] * k * (j0 - 2 * j1 / x) + AB[1] * k * (y0 - 2 * y1 / x)
            lr, mr, Mr, _ = lame(m, False)
            srr = Mr * du + 2 * lr * u / r
            stt = lr * du + 2 * (lr + mr) * u / r
            e = 0.5 * (srr * du + 2 * stt * u / r)
            kin = 0.5 * rho * w ** 2 * u ** 2
            res.append((r, m, u, srr, stt, e, kin))
        state = Smat(b, w, m, lossy) @ AB
    return res

def mode_energy_stats(f, layers, P_circ):
    rg = [np.linspace(a, b, 60 if (b - a) > 50 * UM else 6) for _, a, b in layers]
    rows = mode_fields(f, layers, rg)
    W1, Wi = 0.0, {}
    for i, (m, a, b) in enumerate(layers):
        sub = [x for x in rows if x[1] == m and a <= x[0] <= b]
        r = np.array([x[0] for x in sub]); e = np.array([abs(x[5]) for x in sub])
        wi = np.trapezoid(e * 4 * np.pi * r ** 2, r)
        Wi[m] = Wi.get(m, 0) + wi; W1 += wi
    w = 2 * math.pi * f
    scale = math.sqrt((P_circ / w) / W1)
    smax = scale * max(max(abs(x[3]), abs(x[4])) for x in rows)
    invQ = sum(Wi[m] / W1 / MAT[m]["Q"] for m in Wi)
    share = {m: Wi[m] / W1 for m in Wi}
    loss = {m: P_circ * share[m] / MAT[m]["Q"] for m in Wi}
    prof = [(x[0], scale * max(abs(x[3]), abs(x[4])), scale * x[2]) for x in rows]
    return dict(f=f, W=P_circ / w, peak_stress=smax, Q_eff=1 / invQ, share=share, loss=loss, profile=prof)

def forced_spectrum(layers, r_probe, fs):
    out = []
    for f in fs:
        P = propagate(f, layers, True)
        u0 = P[1, 1] * 1.0 / P[1, 0]
        out.append(abs(u0))
    return np.array(out)

# ------------------------------------------------- READ-ONLY reference: l>=1 modes ------------
def read_sweep_ref():
    """Parse shell_phi_sweep_calc_output.txt (another worker's file; read-only) for bare-quartz modes."""
    fn = os.path.join(THREAD, "shell_phi_sweep_calc_output.txt")
    ref = {}
    if not os.path.exists(fn):
        return ref
    txt = open(fn).read()
    sec = txt.split("Case A:")[1].split("Case B:")[0] if "Case A:" in txt else ""
    for blk in re.split(r"\n\s+OD\s+", sec)[1:]:
        od = float(blk.split()[0])
        d = {}
        for lab, pat in [("0S0", r"0S0 breathing\s+f\s+([\d.]+) MHz"), ("1S0", r"1S0 thickness-type\s+f\s+([\d.]+) MHz"),
                         ("0S2", r"0S2 flexural\s+f\s+([\d.]+) MHz"), ("0T2", r"0T2 torsional ([\d.]+) MHz")]:
            mm = re.search(pat, blk)
            if mm: d[lab] = float(mm.group(1)) * 1e6
        st = re.search(r"0S0 breathing.*?peak stress\s+([\d.]+) MPa", blk)
        if st: d["0S0_stress_10kW_MPa"] = float(st.group(1))
        ref[round(od, 2)] = d
    m5 = re.search(r"isotropic exact modes of the 5 mm shell below 3.2 MHz: \d+ families.*?\n(.*?)\n", txt)
    if m5:
        fam = re.findall(r"([\d.]+) ([ST]) n=(\d+)", m5.group(1))
        ref["5mm_families"] = [(float(a) * 1e6, f"{b} n={c}") for a, b, c in fam]
    return ref

# ------------------------------------------------- ELECTRIC + MAGNETIC ------------------------
def bto_cap(stack, T):
    a = [x for x in stack["layers"] if x[0] == "bto"][0]
    r1, r2 = a[1], a[2]
    epsT = EPSR0 * (1 + 2.0 * max(0.0, min(1.0, (T - 293) / (T_CURIE - 293))))   # Curie-Weiss-like rise to Tc [est]
    if T > T_CURIE: epsT = EPSR0 * 3.0 * (1.0 / (1 + (T - T_CURIE) / 60.0))   # paraelectric fall-off [est]
    C0 = 4 * math.pi * EPS0 * epsT * r1 * r2 / (r2 - r1)
    Ek = PS / (EPS0 * epsT)
    C_bias = C0 / math.cosh(E_WORK / Ek) ** 2
    return dict(C0=C0, C_bias=C_bias, eps=epsT, Ek=Ek, area=4 * math.pi * r1 * r2, r1=r1, r2=r2, piezo_on=T < T_CURIE)

def ferrite_L(stack):
    f = [x for x in stack["layers"] if x[0] == "ferrite"][0]
    a, b = f[1], f[2]
    L = MU0 * FERR_MU * N_TURNS ** 2 * (b - a) / math.pi * math.log(1 / math.tan(THETA0 / 2))
    return L, a, b

NO_DRIVE = "no drive mechanism defined (electrodes removed 2026-10-19; drive method open)"

def no_drive_em(stack, T_bto=None):
    """Fail-closed stub [retired 2026-10-19: electrode-based BTO tank / bare-shell discharge field]. No drive mechanism is
    defined, so there is no electric or magnetic field, no tank frequency and no electric/magnetic loss. Do not invent one."""
    piezo = (T_bto < T_CURIE) if (T_bto is not None and not stack.get("bare")) else False
    return dict(none=True, note=NO_DRIVE, f_e=None, f_zero_bias=None, f_bias=None, V_pk=0.0, E_pk=0.0, W=0.0, I_rms=0.0,
                P_diel=0.0, P_esr=0.0, P_ferr=0.0, B_eq=0.0, B_max=0.0, saturates=False, over_voltage=False, tau_ring=None,
                piezo_on=piezo, bare=bool(stack.get("bare")))

# ------------------------------------------------- OPTICAL -------------------------------------
def optical(stack, P_opt, Tcell, cells, mats):
    """returns per-cell absorbed heat [W], per-band power profile, termination radius."""
    heat = np.zeros(len(cells))
    prof = {b["nm"]: [] for b in BANDS}; prof[LAM_CR] = []
    wsum = sum(b["w"] for b in BANDS)
    P = {b["nm"]: P_opt * b["w"] / wsum for b in BANDS}; P[LAM_CR] = 0.0
    converted = 0.0; term_r = None; shift_r = None
    for i, ((ra, rb), m) in enumerate(zip(cells, mats)):
        T = Tcell[i]; t = rb - ra; area = 4 * math.pi * ra ** 2
        for lam in list(P.keys()):
            Pin = P[lam]
            if Pin <= 0: prof[lam].append((ra, 0.0)); continue
            I = Pin / area
            if m == "quartz":
                bleach = 1.0 if T < SMOKY_BLEACH_K else math.exp(-(T - SMOKY_BLEACH_K) / 50.0)
                a_abs = SMOKY_ALPHA.get(lam, 5.0) * bleach; frac_heat = 1.0
                Pout = Pin * math.exp(-a_abs * t); heat[i] += Pin - Pout
            elif m == "layer2":
                a_abs = L2_MU_ABS
                Pout = Pin * math.exp(-a_abs * t); heat[i] += Pin - Pout   # scattered light assumed to continue outward [est]
            elif m == "phos_in" and lam != LAM_CR:
                a_eff = ALPHA_PHOS / (1 + I / I_SAT_CR)                     # ground-state saturation (bleaching) [rec knee]
                Pout = Pin * math.exp(-a_eff * t); Pabs = Pin - Pout
                qy = QY_CR * (1.0 if T < 423 else max(0.2, 0.974 - (T - 423) * 0.002))  # 97.4 % at 150 C [rec]; slope [est]
                Pem = Pabs * qy * lam / LAM_CR
                heat[i] += Pabs - Pem
                P[LAM_CR] += 0.5 * Pem; converted += Pem       # half outward, half back toward core [est]
                heat[0] += 0.5 * Pem * 0.0                     # inward half returns to core (not tracked) [v0 limit]
                if shift_r is None and Pabs > 0.05 * Pin: shift_r = ra
            elif m in ("gddy", "calorivac", "ferrite"):
                Pout = Pin * math.exp(-ALPHA_METAL * t); heat[i] += Pin - Pout
            elif m == "phos_out":
                Pout = Pin * math.exp(-1e4 * t); heat[i] += Pin - Pout
            else:  # bto: weakly absorbing in visible [est 100/cm]
                Pout = Pin * math.exp(-1e4 * t); heat[i] += Pin - Pout
            P[lam] = Pout
            prof[lam].append((ra, Pin / area))
        tot = sum(P[b["nm"]] for b in BANDS)
        if term_r is None and tot < 0.05 * P_opt: term_r = rb
    return heat, prof, dict(term_r=term_r, shift_r=shift_r, converted_W=converted, escaped_W=sum(P.values()))

# ------------------------------------------------- THERMAL -------------------------------------
class Thermal:
    def __init__(self, cells, mats):
        self.cells, self.mats = cells, mats
        self.n = len(cells)
        ra = np.array([c[0] for c in cells]); rb = np.array([c[1] for c in cells])
        self.rc = 0.5 * (ra + rb); self.ra, self.rb = ra, rb
        self.V = 4 / 3 * np.pi * (rb ** 3 - ra ** 3)
        self.C = np.array([MAT[m]["rho"] * MAT[m]["cp"] for m in mats]) * self.V

    def kvec(self, T):
        return np.array([k_quartz(T[i]) if m == "quartz" else MAT[m]["k"] for i, m in enumerate(self.mats)])

    def conductances(self, T):
        k = self.kvec(T); G = np.zeros(self.n - 1)
        for i in range(self.n - 1):
            R = (1 / self.rc[i] - 1 / self.rb[i]) / (4 * np.pi * k[i]) + (1 / self.ra[i + 1] - 1 / self.rc[i + 1]) / (4 * np.pi * k[i + 1])
            if self.mats[i] != self.mats[i + 1]: R += INTERFACE_R / (4 * np.pi * self.rb[i] ** 2)
            G[i] = 1 / R
        Gout = 1 / ((1 / self.rc[-1] - 1 / self.rb[-1]) / (4 * np.pi * k[-1]))
        return G, Gout

    outer = "dirichlet"
    def h_outer(self, Ts):
        D = 2 * self.rb[-1]; Tf = 0.5 * (Ts + T_REF); kA = 0.0241 * (Tf / 273) ** 0.81; nu = 1.33e-5 * (Tf / 273) ** 1.75
        Ra = 9.81 / Tf * max(Ts - T_REF, 1e-6) * D ** 3 / (nu * nu / 0.71)
        Nu = 2 + 0.589 * Ra ** 0.25 / (1 + (0.469 / 0.71) ** (9 / 16)) ** (4 / 9)   # Churchill sphere correlation [lit]
        hr = 0.9 * 5.670374e-8 * (Ts ** 2 + T_REF ** 2) * (Ts + T_REF)             # eps_IR 0.9 [est]
        return (Nu * kA / D + hr) * 4 * np.pi * self.rb[-1] ** 2
    def step(self, T, q, dt):
        Tn = T.copy()
        for _ in range(3):  # Picard for k(T)
            G, Gout = self.conductances(0.5 * (T + Tn))
            A = np.zeros((3, self.n)); rhs = self.C / dt * T + q
            diag = self.C / dt
            diag = diag + np.concatenate([[0], G]) + np.concatenate([G, [0]])
            if self.outer == "natconv":
                hA = self.h_outer(Tn[-1]); Gout = 1 / (1 / Gout + 1 / hA)
            diag[-1] += Gout; rhs[-1] += Gout * T_REF
            A[1] = diag; A[0, 1:] = -G; A[2, :-1] = -G
            from scipy.linalg import solve_banded
            Tn = np.minimum(solve_banded((1, 1), A, rhs), 3000.0)
        return Tn

# ------------------------------------------------- SCENARIO RUN -------------------------------
def run_case(pre, P, ref):
    bare = pre.get("bare", False)
    st = build_stack(pre["core_d"], pre["wall"], bare)
    GAS["p"] = pre["p_atm"] * 101325.0; GAS["T"] = T_REF   # sealing (initial/ambient) state: p_seal at T_seal = 293 K
    cells, mats = make_grid(st)
    th = Thermal(cells, mats)
    if bare: th.outer = "natconv"   # still air + radiation; heat sink left to Danny
    T = np.full(th.n, T_REF)
    lay = st["layers"]
    iso = [x for x in lay if x[0] in ("quartz", "layer2", "phos_in", "bto", "gddy")]
    # acoustic: l=0 modes, isolated and bonded. Gas-loaded roots are split into shell modes (within 1 % of the
    # vacuum shell modes) and HHO gas-cavity modes (coupled through the wall).
    def vac_modes(L_):
        fs = np.linspace(2e4, 12e6, 4000); g = np.array([propagate(f, L_)[1, 0] for f in fs]); o = []
        for i in range(len(fs) - 1):
            if np.sign(g[i]) != np.sign(g[i + 1]):
                o.append(brentq(lambda f: propagate(f, L_)[1, 0], fs[i], fs[i + 1], xtol=1.0))
        return o
    def split(loaded, vac):
        shell = []
        for v in vac:
            if loaded:
                b = min(loaded, key=lambda f: abs(f / v - 1))
                if abs(b / v - 1) < 0.01 and b not in shell: shell.append(b)
        shell.sort()
        return shell, [f for f in loaded if f not in shell]
    m_iso_all = l0_modes(iso); m_bond_all = l0_modes(lay)
    m_iso, gas_iso = split(m_iso_all, vac_modes(iso)); m_bond, _ = split(m_bond_all, vac_modes(lay))
    f_target = 2.0e6
    f_ac = min(m_iso, key=lambda f: abs(math.log(f / f_target))) if m_iso else f_target
    ac = mode_energy_stats(f_ac, iso, P)
    ac_bond = mode_energy_stats(min(m_bond, key=lambda f: abs(math.log(f / f_target))), lay, P) if m_bond else None
    # static fill-pressure stress in the quartz (Lame thick sphere, inner wall hoop) [calc]
    p = pre["p_atm"] * 101325.0; a, b = st["r_in"], st["r_q"]
    s_fill = p * (b ** 3 + 2 * a ** 3) / (2 * (b ** 3 - a ** 3))
    # wall-temperature stress knee & 573 C (constant-k estimates consistent with power-scaling method)
    R_wall = (1 / a - 1 / b) / (4 * math.pi * 6.2)
    q_ac = np.zeros(th.n)
    for i, m in enumerate(mats):
        if m in ac["loss"]:
            Vm = sum(th.V[j] for j, mm in enumerate(mats) if mm == m)
            q_ac[i] = ac["loss"][m] * th.V[i] / Vm
    chem = chem_state(pre["p_atm"] * 101325.0, st["r_in"], (1.0 if bare else F_WALL) * P)   # chemical domain (core only)
    # time stepping with staggered coupling
    times = np.concatenate([[0], np.logspace(-7, 2, 46)])
    frames = [T.copy()]; history = []
    t_prev = 0.0
    idx = lambda key: [i for i, m in enumerate(mats) if m == key]
    i_bto = idx("bto")
    EM = (lambda T_: no_drive_em(st)) if bare else (lambda T_: no_drive_em(st, float(np.mean(T_[i_bto]))))   # no drive mechanism defined
    for tk in times[1:]:
        # fast domains quasi-static at current temperatures
        em = EM(T)
        qo, oprof, oinfo = optical(st, F_OPT * P, T, cells, mats)
        q = qo + q_ac
        q[0] += (1.0 if bare else F_WALL) * P
        if tk <= chem["t_conv"]: q[0] += chem["P_release"]   # transient 2H2+O2->2H2O heat release until the fill is converted
        # sub-steps
        nsub = 6; dts = np.diff(np.linspace(t_prev, tk, nsub + 1))
        for dt in dts:
            T = th.step(T, q, dt)
        t_prev = tk
        frames.append(T.copy())
        history.append(dict(t=tk, P_heat=float(q.sum())))
    # steady state (long implicit steps)
    Tss = T.copy()
    for _ in range(40 if not bare else 400):
        em = EM(Tss)
        qo, oprof, oinfo = optical(st, F_OPT * P, Tss, cells, mats)
        q = qo + q_ac; q[0] += (1.0 if bare else F_WALL) * P
        Tss = th.step(Tss, q, 1e4 if not bare else 5.0)
    heat_by_layer = {}
    for i, m in enumerate(mats): heat_by_layer[m] = heat_by_layer.get(m, 0) + float(q[i])
    em_hot = em
    # coupled gas state [calc; gas T est = inner-wall T, a LOWER bound under discharge heating]: fixed N and V => n constant,
    # p = p_seal*T/T_seal, c = c_hho(T); gas-loaded modes recomputed hot. 
    a_ = st["r_in"]; P_cond = (1.0 if bare else F_WALL) * P   # heat that leaves the gas by conduction to the wall
    rs_ = np.linspace(0, a_, 81); Tp_ = np.array(gas_T_profile(float(Tss[0]), P_cond, a_, rs_))
    Tg = float(min(np.trapezoid(Tp_ * rs_ ** 2, rs_) * 3 / a_ ** 3, 3000.0)); Tg_centre = float(Tp_[0]); p_seal = GAS["p"]
    GAS["T"] = Tg; GAS["p"] = p_seal * Tg / T_REF
    hot_all = l0_modes(iso); hot_shell, hot_gas = split(hot_all, vac_modes(iso))
    gas_hot = dict(T_gas=Tg, T_centre=Tg_centre, T_wall=float(Tss[0]), P_cond=P_cond, p_seal=p_seal, p_hot=GAS["p"], c_seal=c_hho(T_REF), c_hot=c_hho(Tg), shell=hot_shell, gas_modes=hot_gas,
                   n_m3=p_seal / (1.380649e-23 * T_REF))
    GAS["p"] = p_seal; GAS["T"] = T_REF
    em = EM(np.full(th.n, T_REF))   # design point (293 K) used for fields, vectors, crossings
    return dict(stack=st, cells=cells, mats=mats, th=th, frames=frames, times=times, Tss=Tss, q=q,
                ac=ac, ac_bond=ac_bond, m_iso=m_iso, m_bond=m_bond, gas_modes=gas_iso, em=em, em_hot=em_hot, oprof=oprof, oinfo=oinfo,
                s_fill=s_fill, R_wall=R_wall, heat_by_layer=heat_by_layer, gas_hot=gas_hot, chem=chem)

# ------------------------------------------------- display + tracks ---------------------------
def display_map(st):
    """physical radius -> display radius in [0,1]; films exaggerated to >= 2.2 % each (not to scale)."""
    R = st["layers"][-1][2]
    bounds = [(0.0, st["r_in"], "core")] + [(a, b, m) for m, a, b in st["layers"]]
    disp = [max(b - a, 0.022 * R) for a, b, _ in bounds]
    s = sum(disp); acc = 0; table = []
    for (a, b, m), d in zip(bounds, disp):
        table.append([a, b, acc / s, (acc + d) / s, m]); acc += d
    return table

def to_disp(table, r):
    for a, b, da, db, m in table:
        if a <= r <= b + 1e-15:
            return da + (db - da) * (r - a) / (b - a) if b > a else da
    return 1.0

def thermal_track(st, r):
    """highest modulation frequency of a thermal wave from the inner wall that still reaches radius r: f=1/(pi (int dr/sqrt(alpha))^2)"""
    s = 0.0
    for m, a, b in st["layers"]:
        al = MAT[m]["k"] / (MAT[m]["rho"] * MAT[m]["cp"])
        lo, hi = a, min(b, r)
        if hi > lo: s += (hi - lo) / math.sqrt(al)
        if r <= b: break
    return 1 / (math.pi * s ** 2) if s > 0 else None

def r4(x, n=4):
    if isinstance(x, (list, tuple, np.ndarray)): return [r4(v, n) for v in x]
    if x is None: return None
    if isinstance(x, (bool, np.bool_)): return bool(x)
    if isinstance(x, str): return x
    x = float(x)
    if x == 0 or not math.isfinite(x): return 0.0 if x == 0 else None
    return float(f"{x:.{n}g}")

def package(pre, runs, ref):
    st = runs[0]["stack"]; table = display_map(st)
    cells, mats = runs[0]["cells"], runs[0]["mats"]
    rc = [0.5 * (a + b) for a, b in cells]
    R = st["layers"][-1][2]
    # radial sample grid for viewer: core + cell centres
    r_core = list(np.linspace(0, st["r_in"], 41)[:-1])   # 40 core samples (smooth gradients in the HHO core)
    rv = r_core + rc
    rdisp = [to_disp(table, r) for r in rv]
    out = dict(id=pre["id"], label=pre["label"], group=pre["group"], note=pre.get("note", ""),
               core_d_mm=pre["core_d"], wall_mm=pre["wall"], p_atm=pre["p_atm"], fill="HHO (2H2:O2)",
               OD_quartz_mm=r4(2 * st["r_q"] / MM), R_outer_mm=r4(R / MM), r_B_mm=r4(st["r_B"] / MM),
               stations_mm=r4([s / MM for s in st["stations"]]), stations_disp=r4([to_disp(table, s) if s <= R else 1.0 + (s - R) / R * 0.3 for s in st["stations"]]),
               layers=[dict(key=m, name=(MAT[m]["name"] if m in MAT else "HHO core (plasma when ionised)"), a_mm=r4(a / MM, 6), b_mm=r4(b / MM, 6),
                            da=r4(da), db=r4(db), tags=(MAT[m]["tags"] if m in MAT else "")) for a, b, da, db, m in table],
               r_mm=r4([r / MM for r in rv]), r_disp=r4(rdisp), ncore=len(r_core), powers={})
    ac_ref = ref.get(round(2 * st["r_q"] / MM, 2), {}) if pre["group"] == "phi" else (ref.get(5.0, {}) if pre["id"] == "base5" else {})
    if pre.get("bare"):   # exact general-n bare-shell modes from minimal_test_calc_output.txt [calc]
        ac_ref = {"minA": {"0S2": 1.005e6, "0S1": 1.356e6, "0T2": 1.112e6, },
                  "minB": {"0S2": 1.243e6, "0S1": 2.050e6, "0T2": 1.632e6, }, "scope": {"0S2": 1.243e6, "0S1": 2.050e6, "0T2": 1.632e6, }}.get(pre["id"], {})
    out["acoustic_ref_l_ge_1"] = {k: r4(v) for k, v in ac_ref.items()}
    pg = pre["p_atm"] * 101325.0; rho_g = pg * 0.012011 / (8.314 * T_REF)
    out["propagation"] = dict(c=C0, n_group_quartz_486=1.584, n_rf_quartz=math.sqrt(4.5), c_sound_gas=math.sqrt(1.4 * 8.314 * T_REF / 0.012011),
                              cL_quartz=MAT["quartz"]["cL"], cT_quartz=MAT["quartz"]["cT"], cL_quartz_danny=5900.0, qz_sound_sel=QZ_SOUND_SEL, qz_sound=QZ_SOUND,
                              c_gas_formula="c = sqrt(gamma R T / M), gamma 1.40, M 12.01 g/mol, R 8.314462618; 533 m/s at 293 K", alpha_quartz=6.2 / (2650 * 740),
                              alpha_gas=r4(0.12 / (rho_g * 2403)), r_in_mm=st["r_in"] / MM, r_q_mm=st["r_q"] / MM, bare=bool(pre.get("bare")),
                              note="gas k 0.12 W/mK, cp 2403 J/kgK for 2:1 H2:O2 [est]; quartz alpha from k 6.2, rho 2650, cp 740 [rec]")
    for P, run in zip(POWERS, runs):
        ac, em, oinfo = run["ac"], run["em"], run["oinfo"]
        th = run["th"]
        # fields on viewer grid (core gets zeros except optical source / temperature of wall)
        def on_grid(vals_cells, core_val=0.0):
            return [core_val] * len(r_core) + list(vals_cells)
        # optical intensity total (W/m2) per cell
        Itot = np.zeros(len(cells))
        for lam, pr in run["oprof"].items():
            for i, (_, I) in enumerate(pr): Itot[i] += I
        acp = {round(r, 12): s for r, s, u in ac["profile"]}
        ac_r = np.array(sorted(acp)); ac_s = np.array([acp[k] for k in ac_r])
        stress = [float(np.interp(r, ac_r, ac_s)) if ac_r[0] <= r <= ac_r[-1] else 0.0 for r in rc]
        bare = run["stack"]["bare"]
        if bare:
            pass
        Efield = [0.0 for r in rc]; Bf = [0.0 for r in rc]   # no drive mechanism defined: no electric or magnetic field
        Tss = run["Tss"]; frames = run["frames"]
        # ---- REAL core fields (previously the core got zeros -> black disc) ----
        gh = run["gas_hot"]; a_in = run["stack"]["r_in"]; ch = run["chem"]
        core_T = gas_T_profile(float(Tss[0]), gh["P_cond"], a_in, r_core)
        u_a = abs(ac["profile"][0][2]); w_ac = 2 * math.pi * ac["f"]
        rho_g = gh["p_seal"] * 0.012011 / (8.314 * T_REF); k_g = w_ac / gh["c_hot"]
        def j0_(x): return 1.0 if x == 0 else math.sin(x) / x
        def j1_(x): return 0.0 if x == 0 else math.sin(x) / x ** 2 - math.cos(x) / x
        jw = j1_(k_g * a_in)
        core_p = [abs(u_a * rho_g * w_ac ** 2 * j0_(k_g * r) / (k_g * jw)) if jw else 0.0 for r in r_core]   # gas pressure amplitude, p = A j0(kr)
        core_I = [float(Itot[0]) * r / a_in for r in r_core]   # net radial flux of a uniform optically-thin emitter: F = P r/(4 pi a^3) [est]
        core_E = [0.0 for r in r_core]   # no drive mechanism defined
        core_B = [0.0 for r in r_core]
        wall_peak = max(stress) if stress else 0.0
        core_note = dict(
            acoustic=f"HHO gas pressure in the core p = A j0(kr) (gas-loaded mode at {ac['f']/1e6:.3f} MHz, c(T_gas) {gh['c_hot']:.0f} m/s): max {max(core_p):.3g} Pa = {max(core_p)/max(wall_peak,1e-30):.2g} x the quartz peak stress; continuous with the wall in radial normal stress (sigma_rr = -p), not in hoop stress. Log colour scale.",
            thermal=f"steady gas T profile (uniform heating {gh['P_cond']:.3g} W conducted to the wall, k~T^0.75): centre {core_T[0]:.0f} K, wall {float(Tss[0]):.0f} K, volume mean {gh['T_gas']:.0f} K",
            optical="net radial flux of a uniformly emitting, optically thin plasma: F(r) = P r/(4 pi a^3), zero at the centre by symmetry [est emission profile]. Log colour scale.",
            electric=f"E = 0: {NO_DRIVE}",
            chemical=f"dissociation power {ch['P_diss']:.3g} W spread uniformly in the gas [est]; fill converts to H2O in {ch['t_conv']:.3g} s releasing {ch['E_store']:.3g} J (then a dissociation-recombination cycle with ~zero net heat); outside the core only surface recombination on the inner wall. Knee: not defined.",
            magnetic=f"B = 0: {NO_DRIVE}")
        Twall = float(frames[-1][0])
        # arrival times for animation envelopes
        t_opt, t_ac = [], []; acc_o = 0.0; acc_a = 0.0
        for (a, b), m in zip(cells, mats):
            n_ = MAT[m]["n"] or 1.0
            acc_o += (b - a) * n_ / C0; acc_a += (b - a) / MAT[m]["cL"]
            t_opt.append(acc_o); t_ac.append(acc_a)
        tau_ac = ac["Q_eff"] / (math.pi * ac["f"])
        # vectors (start/termination radii and frequencies)
        lay = {m: (a, b) for m, a, b in run["stack"]["layers"]}
        f_opt = C0 / (486.1e-9)
        bond = run["ac_bond"]
        cum = 0; tot = sum(bond["loss"].values()) if bond else 1
        ac_term_bond = None
        if bond:
            for m, a, b in run["stack"]["layers"]:
                cum += bond["loss"].get(m, 0)
                if cum >= 0.9 * tot: ac_term_bond = b; break
        if bare:
            r_in_, r_q_ = run["stack"]["r_in"], run["stack"]["r_q"]
            vectors = [
                dict(domain="optical", f_start=C0 / 434e-9, f_end=C0 / 656.3e-9, r_start=r_in_, r_end=r_q_, what="Balmer lines pass the bare quartz (~90 % per wall incl. ~4.6 % Fresnel per surface); they leave the sphere"),
                dict(domain="acoustic", f_start=ac["f"], f_end=ac["f"], r_start=r_in_, r_end=r_q_, what="l=0 breathing mode of the bare shell, gas-loaded; reflects at the free outer surface"),
                dict(domain="thermal", f_start=thermal_track(run["stack"], r_in_ + 1e-6), f_end=thermal_track(run["stack"], R), r_start=r_in_, r_end=R,
                     what="1-D conduction through the wall to still air + radiation (natural convection, eps 0.9 est); no sink chosen"),
            ]
        else:
          vectors = [
            dict(domain="optical", f_start=C0 / 434e-9, f_end=C0 / (LAM_CR * 1e-9), r_start=run["stack"]["r_in"], r_shift=oinfo["shift_r"],
                 r_end=oinfo["term_r"] or R, what="Balmer 434/486/656 nm downshifted to 770 nm in the inner Cr3+ phosphor; remainder absorbed in the metallic Gd-Dy film [est]"),
            dict(domain="acoustic", f_start=ac["f"], f_end=ac["f"], r_start=run["stack"]["r_in"], r_end=lay["gddy"][1],
                 r_end_bonded=ac_term_bond, what="l=0 shell mode nearest 2 MHz; isolated shell reflects at the Gd-Dy free surface; if the ladder is bonded, 90 % of loss is reached at the marked radius"),
            dict(domain="thermal", f_start=thermal_track(run["stack"], run["stack"]["r_in"] + 1e-6), f_end=thermal_track(run["stack"], R),
                 r_start=run["stack"]["r_in"], r_end=R, what="heat diffuses to the 293 K reference surface (no sink chosen)"),
        ]
        f_chem = 1 / (2 * math.pi * max(ch["t_conv"], 1e-30))   # conversion-rate corner [calc] (was 2 x the removed electrode drive f)
        vectors.append(dict(domain="chemical", f_start=f_chem, f_end=f_chem, r_start=0.0, r_end=run["stack"]["r_in"],
                            what="H2/O2 dissociation -> H, O, OH radicals -> 2H2+O2->2H2O heat release in the HHO core (P_circ scenario); ends at the inner wall (surface recombination). Knee: not defined"))
        for v in vectors:
            for kk in ("r_start", "r_end", "r_shift", "r_end_bonded"):
                if v.get(kk) is not None:
                    v[kk + "_mm"] = r4(v[kk] / MM); v[kk + "_disp"] = r4(to_disp(table, v[kk])); del v[kk]
            v["f_start"] = r4(v["f_start"]); v["f_end"] = r4(v["f_end"])
        thermal_tr = [[r4(s / MM), r4(thermal_track(run["stack"], s))] for s in np.geomspace(run["stack"]["r_in"] * 1.0005, R, 30)]
        # limits / flags
        def Tof(key, fn=np.mean):
            ii = [i for i, m in enumerate(mats) if m == key]
            return float(fn(Tss[ii])) if ii else 0.0
        Tq_in = float(Tss[0]); Tbto = Tof("bto"); Tcal = Tof("calorivac", np.max); Tgd = Tof("gddy"); Tph = Tof("phos_in")
        Tq_out = float(Tss[[i for i, m in enumerate(mats) if m == "quartz"][-1]])
        qz = [i for i, m in enumerate(mats) if m == "quartz"]
        dT_wall = float(Tss[qz[0]] - Tss[qz[-1]])
        sig_th = 0.58e6 * dT_wall   # sigma/dT 0.58 MPa/K [rec est]
        flags = []
        def fl(cond, txt):
            if cond: flags.append(txt)
        fl(Tq_in > 846, f"Quartz inner wall {Tq_in:.0f} K > 573 C alpha-beta")
        fl(sig_th + ac["peak_stress"] + run["s_fill"] > 48e6, f"Quartz stress: thermal {sig_th/1e6:.0f} + acoustic {ac['peak_stress']/1e6:.0f} + fill {run['s_fill']/1e6:.2f} MPa > 48 MPa design")
        fl(not bare and Tbto > T_CURIE, f"BTO {Tbto:.0f} K > Curie ~393 K (piezo off)")
        fl(not bare and Tcal > 473, f"CALORIVAC max {Tcal:.0f} K > 200 C (H loss)")
        fl(not bare and Tgd > 260, f"Gd-Dy {Tgd:.0f} K above its ~260 K Tc (MCE knee missed)")
        fl(not bare and Tph > 573, f"Inner phosphor {Tph:.0f} K > 300 C (quench)")
        flags.append("Electric/magnetic: " + NO_DRIVE)
        gh = run["gas_hot"]
        for nm, TT in (("Quartz inner wall", Tq_in), ("Gas centre (conduction profile)", gh["T_centre"])):
            if TT >= 773.15: flags.append(f"{nm} {TT-273.15:.0f} C is IN the HHO autoignition range ~500-585 C [given range]")
            elif TT >= 723.15: flags.append(f"{nm} {TT-273.15:.0f} C is APPROACHING HHO autoignition (~500-585 C) [given range]")
        if gh["T_centre"] >= 773.15:
            flags.append(f"Chemical: gas centre {gh['T_centre']-273.15:.0f} C - any unconverted HHO ({run['chem']['E_store']:.2g} J stored) would autoignite (H+O2->OH+O branching); v0 assumes conversion within {run['chem']['t_conv']:.2g} s")
        fl(max(Tss) >= 2999, "Temperatures hit the 3000 K solver cap: stack has failed thermally (values not physical)")
        sel_frames = list(range(0, len(frames)))
        out["powers"][f"{P:g}"] = dict(
            P_circ=P,
            fields=dict(optical=r4(core_I + list(Itot), 3), acoustic=r4(core_p + list(stress), 3),
                        electric=r4(core_E + list(Efield), 3), magnetic=r4(core_B + list(Bf), 3), thermal=r4(core_T + list(Tss), 4),
                        chemical=r4([ch["P_diss"] / (4 / 3 * math.pi * a_in ** 3)] * len(r_core) + [(ch["P_wall_recomb"] / (4 * math.pi * a_in ** 2) / (cells[0][1] - cells[0][0])) if i == 0 else 0.0 for i in range(len(cells))], 3)),
            core_note=core_note,
            chemical=dict(E_store_J=r4(ch["E_store"]), R_diss_per_s=r4(ch["R_diss"]), R_water_per_s=r4(ch["R_water"]), t_conv_s=r4(ch["t_conv"]),
                          P_release_W=r4(ch["P_release"]), P_diss_W=r4(ch["P_diss"]), P_wall_recomb_W=r4(ch["P_wall_recomb"]), D_H=r4(ch["D_H"]), tau_D_s=r4(ch["tau_D"]),
                          f=r4(f_chem), tau_s=r4(min(ch["t_conv"], 1e3)), knee="not defined",
                          sources="D0(H2) 4.478 eV, D0(O2) 5.116 eV [lit NIST CCCBDB]; dHf H2O(g) -241.826 kJ/mol [lit NIST WebBook]; eta_diss 0.2, chain 1, wall share 0.5, D_H [PLACEHOLDERS]; branching H+O2->OH+O drives autoignition [lit, standard H2-O2 mechanism, e.g. Glassman, Combustion]"),
            units=dict(optical="W/m2", acoustic="Pa (peak, l=0 mode)", electric="V/m (peak)", magnetic="T (peak)", thermal="K (steady)", chemical="W/m3 (dissociation power density in gas; surface recombination in the first quartz cell)"),
            thermal_frames=dict(t=r4(list(run["times"]), 3), T=[r4(gas_T_profile(float(frames[k][0]), gh["P_cond"] if k > 0 else 0.0, a_in, r_core) + list(frames[k]), 4) for k in sel_frames]),
            t_opt=r4([0.0] * len(r_core) + t_opt, 3), t_ac=r4([0.0] * len(r_core) + t_ac, 3), tau_ac=r4(tau_ac), tau_e=None,
            vectors=vectors, thermal_track=thermal_tr,
            acoustic=dict(f_drive=r4(ac["f"]), l0_isolated=r4(run["m_iso"]), l0_bonded=r4(run["m_bond"][:25]), gas_cavity_modes=r4(run["gas_modes"][:8]), W_mJ=r4(ac["W"] * 1e3),
                          peak_stress_MPa=r4(ac["peak_stress"] / 1e6), Q_eff=r4(ac["Q_eff"]), loss_W=r4(sum(ac["loss"].values())),
                          share={k: r4(v) for k, v in ac["share"].items()},
                          bonded=dict(f=r4(run["ac_bond"]["f"]), Q_eff=r4(run["ac_bond"]["Q_eff"]), peak_stress_MPa=r4(run["ac_bond"]["peak_stress"] / 1e6),
                                      loss_W=r4(sum(run["ac_bond"]["loss"].values()))) if run["ac_bond"] else None,
                          fill_stress_MPa=r4(run["s_fill"] / 1e6)),
            electric=dict(none=True, note=NO_DRIVE, f_e=None, f_zero_bias=None, piezo_on=em["piezo_on"]),
            magnetic=dict(none=True, note=NO_DRIVE),
            optical=dict(P_opt=F_OPT * P, converted_W=r4(oinfo["converted_W"]), escaped_W=r4(oinfo["escaped_W"])),
            thermal=dict(T_quartz_in=r4(Tq_in), T_quartz_out=r4(Tq_out), T_phos=r4(Tph), T_bto=r4(Tbto), T_gddy=r4(Tgd), T_calorivac_max=r4(Tcal), dT_wall=r4(dT_wall),
                         heat_W={k: r4(v) for k, v in run["heat_by_layer"].items()}, total_heat_W=r4(float(run["q"].sum()))),
            gas=dict(T_gas_K=r4(gh["T_gas"]), T_centre_K=r4(gh["T_centre"]), T_wall_K=r4(gh["T_wall"]), T_seal_K=T_REF, p_seal_Pa=r4(gh["p_seal"]), p_hot_Pa=r4(gh["p_hot"]), n_m3=r4(gh["n_m3"]),
                     c_seal=r4(gh["c_seal"]), c_hot=r4(gh["c_hot"]), shell_l0_hot=r4(gh["shell"][:6]), gas_modes_hot=r4(gh["gas_modes"][:8]),
                     note="computed state, not an input: gas T = volume mean of the steady conduction profile (uniform heating conducted to the inner wall); fixed N,V => p ~ T, c ~ sqrt(T)"),
            flags=flags)
    return out

def find_crossings(case):
    """pairs of domain frequency tracks within +-5 % at overlapping radii; thermal track vs horizontal tracks."""
    res = []
    for Pk, pdat in case["powers"].items():
        tr = []
        v = {x["domain"]: x for x in pdat["vectors"]}
        for f in pdat["acoustic"]["l0_isolated"]:
            tr.append(("acoustic l=0 (isolated)", f, v["acoustic"]["r_start_mm"], v["acoustic"]["r_end_mm"]))
        for f in pdat["acoustic"].get("gas_cavity_modes", [])[:4]:
            tr.append(("HHO gas cavity mode", f, case["propagation"]["r_in_mm"] * 0, case["propagation"]["r_in_mm"]))
        for lab, f in case.get("acoustic_ref_l_ge_1", {}).items():
            if lab in ("0S2", "0T2", "0S1"): tr.append((f"acoustic {lab} [{'calc minimal_test' if case['propagation']['bare'] else 'rec sweep'}]", f, v["acoustic"]["r_start_mm"], v["acoustic"]["r_end_mm"]))
        cr = []
        for i in range(len(tr)):
            for j in range(i + 1, len(tr)):
                a, b = tr[i], tr[j]
                if a[0].split()[0] == b[0].split()[0] and not (a[0].startswith("electric") or b[0].startswith("electric")): continue
                if abs(math.log(a[1] / b[1])) < 0.05:
                    cr.append(dict(a=a[0], b=b[0], f=r4(math.sqrt(a[1] * b[1])), r_overlap_mm=[max(a[2], b[2]), min(a[3], b[3])], radial_overlap=max(a[2], b[2]) <= min(a[3], b[3])))
        # thermal track crossing reference cycle rates and acoustic/electric
        for name, f in [("caloric rung 11 Hz [rec]", 11.0), ("caloric rung 35 Hz [rec est]", 35.0), ("EC/MCE 1 kHz", 1e3)]:
            ttr = pdat["thermal_track"]
            for k in range(len(ttr) - 1):
                (r1, f1), (r2, f2) = ttr[k], ttr[k + 1]
                if f1 and f2 and (f1 - f) * (f2 - f) <= 0:
                    cr.append(dict(a="thermal penetration track", b=name, f=f, r_mm=r4(r1), note="thermal wave at this rate dies beyond this radius"))
                    break
        pdat["crossings"] = cr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="also write index.html from viewer_template.html")
    ap.add_argument("--core-d", type=float, help="custom preset: gas core diameter mm")
    ap.add_argument("--wall", type=float, help="custom preset: quartz wall mm")
    ap.add_argument("--p-atm", type=float, default=1.0, help="custom preset: HHO fill pressure atm")
    ap.add_argument("--only", help="comma list of preset ids")
    ap.add_argument("--qz-sound", default="vrh", choices=sorted(QZ_SOUND), help="crystal-quartz cL/cT set (see QZ_SOUND)")
    args = ap.parse_args()
    set_qz_sound(args.qz_sound)
    presets = list(PRESETS)
    if args.core_d is not None and args.wall is not None:
        presets.insert(0, dict(id="custom", label=f"Custom: core d {args.core_d} mm, wall {args.wall} mm, {args.p_atm} atm HHO",
                               core_d=args.core_d, wall=args.wall, p_atm=args.p_atm, group="lock"))
    if args.only:
        keep = args.only.split(","); presets = [p for p in presets if p["id"] in keep]
    ref = read_sweep_ref()
    cases = []
    log = []
    for pre in presets:
        plist = POWERS   # all presets: 0.1 W ... 100 kW decades
        runs = [run_case(pre, P, ref) for P in plist]
        c = package(pre, runs, ref); find_crossings(c); cases.append(c)
        ks = list(c["powers"]); p0, p1, p10 = c["powers"][ks[0]], c["powers"][ks[1]], c["powers"][ks[-1]]
        log.append(f"{pre['id']:10s} OD {c['OD_quartz_mm']} mm R_out {c['R_outer_mm']} | l0 iso {[round(f/1e6,3) for f in p10['acoustic']['l0_isolated'][:4]]} MHz | drive {p10['acoustic']['f_drive']/1e6:.3f} MHz "
                   f"stress@{ks[-1]}W {p10['acoustic']['peak_stress_MPa']} MPa Qeff {p10['acoustic']['Q_eff']} | electric: no drive "
                   f"| T_gas mean {p1["gas"]["T_gas_K"]} K centre {p1["gas"]["T_centre_K"]} K p {p1['gas']['p_hot_Pa']} Pa c {p1['gas']['c_hot']} m/s @{ks[1]}W "
                   f"| T_qz_in {ks[0]}W {p0['thermal']['T_quartz_in']} K {ks[1]}W {p1['thermal']['T_quartz_in']} K, {ks[-1]}W {p10['thermal']['T_quartz_in']} K | crossings {len(p10['crossings'])}")
        print(log[-1], flush=True)
    data = dict(meta=dict(title="Stratified bubble sphere - multi-domain radial model v0", date="2026-10-19",
                          status="v0 PROTOTYPE - ESTIMATED PHYSICS - not validated - paper model, nothing measured",
                          scenario=f"All five domains circulate P_circ at once. Wall heat = {F_WALL} P_circ [rec bracket 0.1-1]; Balmer light = {F_OPT} P_circ [est]; "
                                   "acoustic drive at the l=0 isolated-shell mode nearest 2 MHz; electric/magnetic: " + NO_DRIVE + "; "
                                   "outer surface held at 293 K (reference only, no sink chosen).",
                          phi=PHI, powers=POWERS, materials=MAT, ref_file="shell_phi_sweep_calc_output.txt (read-only)" if ref else None),
                cases=cases)
    with open(os.path.join(HERE, "model_data_v0.json"), "w") as f:
        json.dump(data, f, separators=(",", ":"))
    with open(os.path.join(HERE, "solver_v0_output.txt"), "w") as f:
        f.write("\n".join(log) + "\n")
    print("wrote model_data_v0.json", os.path.getsize(os.path.join(HERE, "model_data_v0.json")) // 1024, "kB")
    if args.build:   # index.html = template + drive_model.js + drive_ui.js + this JSON
        import subprocess; subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True)

if __name__ == "__main__":
    main()
