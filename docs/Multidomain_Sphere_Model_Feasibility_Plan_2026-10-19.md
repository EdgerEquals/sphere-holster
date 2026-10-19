# Multi-domain Stratified Sphere Model: Feasibility, Tool Choice, Build Plan (2026-10-19)

**Status:** this is a planning report plus a v0 prototype. It is not validated, and nothing here has been measured.

**Tags:**
- **[lit]** published value
- **[rec]** taken from another box report
- **[calc]** computed here
- **[est]** an estimate, assumption or effort guess

**Times** are AWST (UTC+8).

**Companion files** (all in `/workspace/grok_thread/`):
- `Minimal_Test_Config_1mm_2026-10-19.md`: the bare 1 mm HHO test, plus the single-cycle drive scope.
- `sphere_model_v0/`: the solver, viewer, drive model and screenshots.

## 1. Plain-language summary

**A useful whole-sphere model is feasible** if each domain is solved at its own natural level of approximation and the domains are coupled through source terms on staggered time steps. A single "full physics" solve is not feasible, and nobody needs one:
- optics at sub-µm wavelengths in a mm–cm sphere would need about 10¹²–10¹⁵ unknowns for full-wave Maxwell;
- the timescales run from ps (light transit) to seconds or minutes (heat).

**v0 now exists.** It is a radial (l=0), timescale-separated coupled solver with a Three.js viewer:
- a quarter-cut view and an orthographic true-scale view with five wavefronts;
- a spectral map with crossings and the GO (ionisation) time animation;
- presets for the baseline, the lock values, the φ sweep and the minimal test;
- an independent single-cycle audio drive panel with coupled gas-temperature response and sweeps.

**It already shows several design-relevant results (all estimates):**
- **The full stack is thermally limited.** At 5 mm OD the quartz inner wall is ~415 K at 10 W but ~1960 K at 100 W with the outer surface held at 293 K, and BTO is above its Curie point from ~10 W.
  - The cause is the Ti/Pt electrode: it makes the stack opaque, so all Balmer light becomes heat.
  - The thick CALORIVAC and ferrite then add thermal resistance.
- **The bare 2 mm-OD minimal test cannot dissipate 1 W in still air** without its inner wall passing 573 °C, and it is then also in the HHO autoignition range.
- **Danny's "2 MHz shell mode" is not an l=0 mode at 5 mm OD.** The l=0 modes are 0.69 and 3.10 MHz with films. The 2 MHz figure corresponds to the n=4 spheroidal mode in the sweep [rec].
- **Fresnel loss on quartz is ~4.6–4.7% per surface**, not 3.5–4%.

**COMSOL and ANSYS both have optics.** Danny's claim that they lack it is not accurate (see §4).

## 2. What is feasible, and what must be approximated

| Domain | Feasible fidelity | Approximation needed | Why |
|---|---|---|---|
| Optical | Radiative transfer per band (Balmer 434/486/656 nm, phosphor emission bands), radially (v0) then with angle (discrete ordinates or Monte Carlo); transfer-matrix (thin-film) treatment for coherent layers ≤ a few µm | No full-wave Maxwell over the sphere; wave optics only for thin-film stacks or a local unit cell (FDTD/RCWA) | λ ≈ 0.4–0.8 µm vs a mm–cm sphere: full-wave is 10¹²+ cells |
| Acoustic | Exact multilayer spherical elastic transfer matrix for l=0 (v0), then all l (spheroidal and torsional) with spherical harmonics; FEM for anisotropic quartz and non-spherical defects | Isotropic VRH quartz in v0; layered isotropy; gas as an acoustic impedance | Quartz is trigonal, so l and m couple and full anisotropy needs FEM; Bechmann constants give the cL range 5324–7031 m/s [rec] |
| Thermal | 1D radial finite volume with k(T), interface resistances and convection/radiation BCs (v0), then Y_lm angular modes or 2D axisymmetric / 3D FEM | Heat-sink geometry is still open | Cheap and robust; the angular structure comes from electrodes and feeds |
| Electric | Electro-quasistatics: spherical capacitors, BTO varactor εr(E, T), DBD gas gap; 2D/3D Laplace FEM for feeds | Plasma as a lumped load or Manley-type DBD; no PIC in the core model | The EM wavelength is ≫ the sphere at MHz and audio frequencies |
| Magnetic | Magneto-quasistatics: ferrite-shell toroid L, Q_f(f), saturation near feed holes (analytic in v0), then FEM | Ferrite B–H loop simplified; feed-hole crowding as a factor [est] | Same reason as electric |
| Plasma / gas | Paschen knee from n·d; Manley DBD energy; gas energy balance; ideal-gas p and c(T) at fixed N, V | No kinetics or chemistry (H2O formation); swarm data via BOLSIG+ later | Plasma chemistry is a separate research-grade model |
| Coupling | Staggered, timescale-separated: fast domains solved quasi-statically at the current temperatures; heat sources passed to the thermal solve; T fed back to εr, k, c, Q and the gas state | Not a monolithic solve | Timescales from ps (optical transit) through ns–µs (EM, acoustic transit) and ms (wall diffusion) to s (lumped thermal) |

## 3. Solver options compared with building from scratch

| Tool | Strengths for this job | Weaknesses | Use it for |
|---|---|---|---|
| **FEniCSx** (Python/C++) | Clean weak-form multiphysics, MPI, good Python workflow | You write the physics; piezo and anisotropy by hand | Phase 2–4 thermal, electro-quasistatics, anisotropic elastic FEM |
| **Elmer** (CSC) | Ready-made heat, elasticity, electrostatics, magnetodynamics and acoustics solvers coupled in one input file | Older UI; optics only via a basic radiation/heat model | Fast route to coupled thermal-electric-magnetic FEM |
| **MFEM** | High-order FEM, H(curl)/H(div) elements, GPU, very fast | C++, more effort | Magnetic/EM FEM; high-order elastic modes |
| **deal.II** | Mature, adaptive, excellent for eigenproblems | C++, steep | Alternative to MFEM |
| **scikit-fem** | Tiny pure-Python FEM | Small scale, no MPI | Prototypes, 2D axisymmetric checks |
| **Sparselizard** | Built-in multiphysics including piezo and nonlinear | Small community | Piezo quartz/BTO coupling |
| **Dedalus** (spectral) | Native sphere/shell/ball bases (spin-weighted spherical harmonics), very efficient for spherical layers | Smooth layered problems only; sharp material jumps need one domain per layer | Spectral acoustics and thermal in spherical shells; Y_lm checks |
| **Meep** (FDTD) | Open, well tested, material dispersion | Full-wave, so unit cells only, not the sphere | Phosphor/elbaite scattering unit cells, thin-film validation |
| **openEMS** (FDTD) | Open EM, good for RF feeds and antennas | Same scale limit | RF/feed parasitics, EM resonance checks |
| **preCICE** | Couples separate solvers (partitioned) | Integration effort | If several tools are mixed |
| **Monte Carlo RT** (own code, or MCX/pbrt-style) | Correct for scattering media and phosphors | Noise; needs optical constants | Phase 3 optics |
| **From scratch** (Python/NumPy, as v0) | Exact spherical analytic structure (transfer matrices, Bessel functions), fast, transparent, easy to validate | Limited to radially layered and symmetric problems; geometry details cannot be added | Core of phases 1–3; fast design sweeps |

**Recommendation [est]:** a hybrid.
- Keep a from-scratch semi-analytic core (spherical transfer matrices and radial finite volume) for speed, sweeps and transparency.
- Add FEniCSx or Elmer for anisotropic quartz, feeds, electrodes and the heat sink.
- Use Meep for optical unit cells.
- Use a Monte Carlo RT code for the scattering layers.
- Couple through files or preCICE.

## 4. COMSOL and ANSYS: do they have optics? Yes, both do

**COMSOL Multiphysics:**
- The **Wave Optics Module** offers full-wave FEM, the beam-envelope method for large optical structures, and laser-heating multiphysics.
- The **Ray Optics Module** offers geometrical optics, ray heating and structural-thermal-optical (STOP) analysis.
- COMSOL also has the Acoustics, AC/DC, Plasma, Heat Transfer and Structural (piezo) modules. That covers all five domains in one framework (licence cost aside).
- **Gap [est]:** I know of no built-in phosphor wavelength-conversion kinetics. They would be user-defined equations.

**ANSYS:**
- Its optics portfolio is Lumerical (FDTD/varFDTD/RCWA), Zemax OpticStudio and Speos.
- Mechanical, Fluent, Maxwell and HFSS cover the other domains.
- **Note:** Synopsys completed its acquisition of ANSYS on 17 Jul 2025, so these products now sit under Synopsys.
- Coupling across products is through Workbench and System Coupling.

**Correct statement:** "COMSOL and ANSYS both have optics; neither offers a ready-made phosphor ladder in a coupled stratified-sphere workflow, and full-wave optics over the whole sphere is impossible in any tool."

## 5. Limits of validity (v0 and the plan)

- **Geometry:** radial l=0 only in v0. The l≥1 modes (0S2, 0T2, n=4) come from the separate sweep and calc scripts. There are no electrodes, feeds or defects in 3D.
- **Quartz:** isotropic VRH (cL 5.9 km/s scaling). Real crystal quartz has an anisotropic cL of 5.3–7.0 km/s [rec], which splits modes by m.
- **Optics:**
  - The Balmer spectrum is a placeholder using case-B ratios [est]. A 1–3 mm HHO discharge is not a case-B nebula.
  - Phosphor kinetics are simplified (ground-state saturation, QY quench). (Update 2026-10-19: the inner phosphor is removed pending further work, so v0 has no phosphor kinetics now.)
  - Smoky-quartz colour centres are qualitative.
- **Plasma:**
  - The Paschen knee is a mixture rule [est] anchored to the lit H2/O2 minima.
  - The left branch is absent below pd ≈ 0.37 Torr·cm.
  - DBD energy is Manley-type.
  - No chemistry: H2O formation is a real drift and energy source, and it is unmodelled.
- **Coupled gas state:**
  - Gas temperature is computed, never an input.
  - In the steady 3D solver the gas T is taken equal to the inner-wall T, which is a lower bound.
  - In the drive model the gas T comes from its own energy balance.
  - At fixed N and V: p ∝ T, c ∝ √T, and the Paschen knee is unchanged to first order because it depends on n·d.
- **Thermal:**
  - The full stack uses a 293 K outer reference.
  - Bare presets use still-air natural convection plus radiation, with ε 0.9 [est].
  - No sink has been chosen; that is left to Danny.
- **Numbers labelled [est] are placeholders:**
  - shell Q 2100 [rec] is applied to every mode;
  - the energy partition is gas 0.6 / wall 0.3 / light 0.1;
  - gas-mode Q;
  - the DBD electrode (50 µm centre wire).

## 6. Phased build plan (effort in person-weeks [est])

| Phase | Content | Milestone and acceptance test | Effort |
|---|---|---|---|
| **0 (done today)** | v0: radial coupled solver, viewer (quarter-cut, orthographic wavefronts, spectral map, GO), presets, minimal test, single-cycle audio drive with coupled gas state and sweeps | Reproduces the sweep's 5 mm values (0S0 0.706, 1S0 3.233 MHz, 92.6 MPa at 10 kW) [rec]; bare thermal matches the hand calc (780 vs 782 K) | done |
| 1 | Acoustics l≥1: multilayer spheroidal/torsional transfer matrices, gas loading, mode-energy Q; then anisotropic quartz by FEM (FEniCSx/Sparselizard) | Lamb/Love modes of a solid isotropic sphere to <0.1%; Heyliger-type measured resonant-sphere data [lit] to ~1%; agreement with the sweep's n=4 S mode | 3–5 |
| 2 | Thermal Y_lm / 2D-axisymmetric with real electrodes, feeds and a chosen sink; contact resistances | Analytic sphere conduction; bench thermocouple or IR on a heated bare bubble | 2–3 |
| 3 | Optics: discrete-ordinates or Monte Carlo RT per band; phosphor rate equations (absorption, emission, saturation, thermal quench); elbaite scattering from Mie/Meep unit cells; ITO option replacing Ti/Pt | Energy conservation to <1%; Mie benchmark; measured transmission of coated quartz coupons | 4–6 |
| 4 | Electro-quasistatics + piezo: BTO εr(E, T), quartz piezo coupling of the shell modes, DBD with real electrode geometry; BOLSIG+ swarm data for HHO | Spherical-capacitor analytic; impedance spectrum of a test bubble (network analyser) | 3–4 |
| 5 | Magnetics: ferrite shell FEM (feed holes, saturation), Q_f(f, T) | Toroid analytic L; measured L and Q of a ferrite-shell sample | 2–3 |
| 6 | Plasma and gas: 0D chemistry (H, O, OH, H2O, O⁻) with energy release; electronegativity effects; knee drift over many cycles | Paschen curve measured on the bubble vs model; pressure/optical monitoring | 4–8 (research risk) |
| 7 | Coupling framework: staggered multi-rate scheduler, convergence checks, preCICE if mixed tools; sweep and optimisation front end | Coupled vs uncoupled limits; time-step and mesh convergence | 3–4 |
| 8 | Viewer v1: l≥1 angular fields on the cut faces, axis-dependent ortho views, drive panel tied to all domains, report export | Visual regression tests (Playwright screenshots) | 2–3 |

**Total:** about 23–36 person-weeks (est) to a validated v1. Phases 1–3 deliver most of the design value.

## 7. Validation strategy

1. **Analytic benchmarks:**
   - solid and shell sphere elastic modes;
   - spherical-capacitor C and E(r);
   - toroid L;
   - sphere conduction;
   - Fresnel and thin-film transmission;
   - the rigid gas-sphere modes (x = 4.4934 etc.).
   - v0 already matches the sweep's 5 mm values exactly.
2. **Cross-code checks:**
   - the same geometry in FEniCSx/Elmer (or COMSOL, if a licence is available) for modes, thermal and electric fields;
   - Meep for optical unit cells.
3. **Literature data:** published measured sphere resonances, HHO/H2/O2 Paschen data, and optical constants of quartz, elbaite and the phosphors.
4. **Bench tests on the minimal bubble** (cheapest first):
   - optical transmission at 434/486/656 nm;
   - an impedance or resonance spectrum (piezo/laser vibrometer) for the shell modes and Q;
   - IR thermography at a known power;
   - breakdown voltage vs fill (the knee);
   - emission spectrum;
   - single-cycle drive response vs f (pressure/optical/acoustic pickup), compared with the Drive panel's sweep.
5. **Uncertainty:** every [est] parameter gets a range. Sweeps report bands, not single numbers.

## 8. The v0 prototype: what it does

**Files** (in `/workspace/grok_thread/sphere_model_v0/`):

| File | Role |
|---|---|
| `solver_v0.py` | Radial coupled solver. CLI: `--core-d --wall --p-atm --only <ids> --build` |
| `model_data_v0.json` | Data from the solver |
| `drive_model.js` | Coupled single-cycle drive model (browser + node) |
| `drive_ui.js` | The viewer's Drive panel |
| `viewer_template.html` | Viewer template |
| `build.py` | Builds `index.html` (self-contained apart from Three.js 0.160 from the jsDelivr CDN) |
| `shoot.py`, `shoot_drive.py` | Playwright/Chromium screenshot tests |
| `solver_v0_output.txt`, `drive_model_output.txt` | Text outputs |

**Presets:**
- `scope` (Danny scope: 1 mm ID × 2 mm OD, HHO, fill open);
- `minA`, `minB`;
- `base5` (5 mm baseline, 1.5 mm core radius, 1 mm wall);
- `lock54`, `lock25` (read as quartz OD with a 1 mm wall; this matches the reading in Danny's own layer1_lock_phi_calc_output.txt, whose 5.4 mm/1 mm-wall 0S0 0.617 and 1S0 3.072 MHz agree with v0's 0.63/3.073 MHz with films);
- φ sweep `phi1.6`–`phi17.75`.

**Domain physics in v0:**
- **Acoustic:** exact l=0 multilayer spherical elastic transfer matrix with HHO gas loading at the computed gas temperature. Gas-cavity modes are separated from shell modes. Mode-energy Q_eff and peak stress at P.
- **Thermal:** 1D radial implicit finite volume with k(T), interface resistances and the transient after GO.
- **Optical:** radial march per band with colour centres. (Update 2026-10-19: the inner phosphor down-shift is removed pending further work, and the Ti/Pt cut-off was removed with the electrodes; light now runs quartz -> layer two -> BTO -> Gd-Dy.)
- **Electric:** BTO varactor (εr(E, T), Curie-Weiss) with the ferrite-shell LC tank; DBD for the bare presets.
- **Magnetic:** ferrite toroid L and Q_f.

**Coupled gas state (new):**
- Gas T, then p = p_seal·T/T_seal, c(T), and the hot gas-cavity modes.
- Autoignition flags at ≥450 °C (approaching) and ≥500 °C (in the ~500–585 °C range).

**Viewer:**
- **Quarter-cut view:** three selectable field faces, φ-spaced layers and ticks, five domain vectors with start/end frequency.
- **Spectral map:** frequency vs radius with crossings circled, plus a crossings table and limit flags.
- **GO:** ionisation-ON time animation on a log time axis from 0.1 ps to 100 s.
- **Orthographic full-sphere view** (§8.1).
- **Drive panel** (§8.2).

### 8.1 Orthographic view mode (toggle: View → "Orthographic full sphere, true scale")

- Three.js OrthographicCamera looking straight down an axis (selectable +X/+Y/+Z). In the l=0 model all axes look the same.
- Full sphere at true scale, with true-scale layer rings, a scale bar, and radial ticks along +x.
- **Five coloured wavefronts radiating at once**, one 64° sector per domain. The radius is the propagation position. Radial stripes cos(2πf(t − t_arrival(r))) show frequency and phase.
  - A flat tint means the wavelength is under 3 px.
  - Thermal shows a diffusion envelope, because the thermal wave decays within δ = λ/2π.
- **Propagation speeds per medium:**
  - optical: c/n, group index 1.584 in quartz;
  - E/B: c/√ε_RF;
  - acoustic: 533 m/s × √(T/293) in HHO, 5.9 km/s in quartz, cL for the other layers;
  - thermal: t = (∫dr/√(4α))².
- **Clock modes:**
  - (a) **shared real-time clock:** every front at the same physical t;
  - (b) **per-domain time dilation:** each front reaches its end in 6 display-seconds, and each sector shows its own factor (e.g. ×1.6e-12 for optical, ×6e-11 for E/B, ×1e-2 for thermal). This is clearly labelled as non-simultaneous.
- **± pulsed drive** checkbox.
- When the user drive frequency is set, the E/B sectors use it. At audio f, λ is ~100 km, so they show a flat quasi-static tint.

### 8.2 Single-cycle drive panel (Danny's scope; the frequency is an independent knob)

- **Inputs:**
  - geometry ID/OD (prefilled from the preset);
  - HHO fill amount (Torr at sealing, or molecules) — **required, no default**;
  - sealing temperature, labelled "initial/ambient, not a control";
  - drive amplitude — **required**;
  - EMF frequency — **required, unset by default**; a log slider covers 20 Hz–20 kHz; one cycle lasts 1/f.
- **Outputs:**
  - the V(t) and gas-gap voltage traces against the ±knee;
  - discharge power;
  - computed ΔT for the gas, inner wall and outer wall over log time;
  - a natural-mode strip from 1e-2 to 1e15 Hz, with the audio band shaded and the drive f marked;
  - a ring-down table (f, Q, τ, amplitude per mode);
  - autoignition and knee flags.
- **Sweeps:**
  - vs drive f (20 Hz–20 kHz), with the natural thermal corners marked and the off-axis acoustic modes noted;
  - vs fill (0.1–7600 Torr), with the knee curve and the peak gas voltage.
- **Example results** (see the Minimal Test report §7): the thermal corners (gas ~20 kHz at 22 Torr; wall ~20 Hz) bracket the audio band. The acoustic modes (0.35–6.7 MHz) respond only by ringing after breakdown onsets.

### 8.3 Viewer v0.2 changes (10:42–10:59 AWST steering)

**Version label.** The header shows "v0.2 · built YYYY-MM-DD HH:MM AWST". build.py stamps it.

**Waveforms replace the straight arrows, in both views.**
- Each domain is drawn as an animated wave in its own wavelength:
  - acoustic as a pressure wave;
  - EM (optical, E, B) as a transverse wave;
  - thermal and chemical as decaying diffusion waves.
- **What is scaled.** Only the display wavelength. A per-domain factor S = a/(3·λ_gas) (or 1·λ for decaying waves) is printed as "λ shown ×S". Amplitudes are normalised. Times and positions are true.
- **Physical wavelengths (no φ):**

  | Domain | HHO core | Quartz |
  |---|---|---|
  | Acoustic | c_hot/f | 5900/f |
  | Optical | c/f | c/f ÷ 1.554 |
  | E / B | c/f | ÷ √4.5 |
  | Thermal | 2π√(2α/ω) | 2π√(2α/ω) |
  | Chemical | 2π√(2D_H/ω) | — |

**Golden-ratio rule.**
- The ONLY φ shift is at the HHO→quartz boundary (inner wall), and it is Danny's postulate, not physics.
- "phimode" controls how it is applied:
  - default "λ": quartz λ × φ on top of the physical ratio;
  - "phase": +2π/φ² at the wall;
  - "off".
- `PHI_BOUNDARIES` has a hook `{id:'quartz_outside', apply:false}` that is not applied.
- The waves start in the HHO core and end at the quartz outer surface. The chemical wave ends at the inner wall.
- Nothing outside the quartz OD is computed for the waves. The outer layers are drawn greyed and labelled "outside quartz OD: not modelled yet".
- The ID/OD sweeps and the sound-speed citation work are unchanged.

**Face labels for mobile.**
- Each face carries a large label such as "face 1 THERMAL", "face 2 ACOUSTIC" or "face 3 CHEMICAL". It updates when the Faces dropdowns change.
- Each face has a colour-keyed outline. The legend lists face → domain.
- Touch controls:
  - one finger orbits;
  - two fingers pinch-zoom and pan;
  - the orthographic view supports pinch-zoom and pan.
- On narrow screens the side panel stacks, and the HUD is compacted to about 16% of the height.

**Power decades.**
- Every preset is precomputed at 0.1 W, 1 W, 10 W, 100 W, 1 kW, 10 kW and 100 kW, in ascending order in the selector.
- All panels work at every power.
- At high power these flags fire:
  - autoignition;
  - quartz softening and 3000 K clamp;
  - stress.

**HHO core was a black disc: cause and fix.**
- **Cause.** The field sampler set the core to 0 for the acoustic, E and B fields, and to a uniform value for thermal and optical. It also used only 11 samples.
- **Fix.** The core is now sampled at 40 points with physical fields:
  - acoustic cavity pressure p(r) ∝ j0(kr), drawn on a log colour scale over 8 decades;
  - thermal: the conduction profile, with T_centre > T_mean > T_wall (scope at 1 W: 1228/1073/962 K);
  - optical: net radial flux of a uniform emitter, ∝ r/a [est];
  - electric: the bare-sphere radial E;
  - chemical: dissociation power density.
- B is genuinely 0 in the core for the l=0 drive. The HUD says so.
- Each domain has a core note in the HUD.

**Quartz opacity.**
- The quartz shell defaults to opacity 0.70, with depthWrite off and a crisp white edge outline.
- A slider sets it from 0 to 1. Shot 34 shows 0.3.

**CHEMICAL as a sixth domain** (solver, viewer, drive panel, ortho, waveforms, tables, sweeps).
- **Physics:**
  - the discharge dissociates H2/O2 into H, O and OH radicals;
  - stored recombination/combustion energy is 2H2+O2→2H2O;
  - reaction progress and heat release feed the thermal solve and the autoignition flag;
  - there is no chemistry outside the core except surface recombination on the inner wall.
- **Literature constants:**
  - D0(H2) = 4.478 eV and D0(O2) = 5.116 eV [lit, NIST CCCBDB / Huber & Herzberg];
  - ΔHf H2O(g) = −241.826 kJ/mol, about 242 kJ/mol LHV [lit, NIST Chemistry WebBook];
  - chain branching H+O2→OH+O drives autoignition [lit, standard H2–O2 mechanism, e.g. Glassman, *Combustion*].
- **PLACEHOLDERS [est]:**
  - dissociation share of gas-deposited discharge energy 0.2;
  - chain length 1 H2O per dissociated H2;
  - wall-recombination share 0.5;
  - H-atom diffusivity 1.5e-4 m²/s at 1 atm, scaled as 1/p.
- **Results:**
  - scope at 1 W: stored energy 4.6e-5 J, converted in 0.41 ms, releasing 0.11 W meanwhile;
  - base5 at 1 W: 0.095 J over 8.5 s.
  - After conversion, the dissociation–recombination cycle gives about zero net heat.
- **Knee: not defined.** Displayed everywhere the other domains show a knee.
- **Flag.** "Chemical: … would autoignite" fires when the gas centre is ≥ 500 °C (773 K).

### 8.4 Viewer v0.3 changes (11:33 AWST steering): drive range, sweeps, sound speeds

**(a) EMF drive frequency: 100 kHz to 1000 THz.**
- The frequency is typed with SI suffixes (k M G T P, e.g. `2.5M`, `600T`) or set with a log slider that has decade ticks.
- An axis strip under the slider marks:
  - the natural acoustic modes of the current geometry (cyan): gas modes from c(T), and quartz shell l=0 modes computed for the selected sound speeds;
  - the Balmer lines Hα 656.28, Hβ 486.13, Hγ 434.05 and Hδ 410.17 nm [lit NIST ASD];
  - the visible band 380–750 nm (400–789 THz);
  - three dashed limits: quasi-static, EM resonance and breakdown formation.
- **Regime flags** (`regime()` in drive_model.js), all shown live:

  | Flag | Fires when | Scope (2 mm OD) |
  |---|---|---|
  | Quasi-static degrading | OD·√εr > λ/10, i.e. f > c/(10·OD·√4.5) | ~7.07 GHz |
  | Quasi-static INVALID | f ≥ first dielectric-sphere EM resonance, c·2/(2π b √εr) [est] | ~45.0 GHz |
  | No discharge forms | half-cycle < electron-avalanche formation time ln(1+1/γ)·gap/v_e; the knee is then set to ∞ | ~20.8 ns (above ~24 MHz) |
  | Static knee not reached | half-cycle < Townsend ion-feedback time gap/v_i | ~225 ns (above ~2.2 MHz) |
  | OPTICAL BAND: drive is light | drive λ is visible | — |
  | Infrared / ultraviolet | drive λ is IR or UV | — |
  | Within 1% of a Balmer line | drive λ matches Hα–Hδ to 1% | — |

  The formation times use PLACEHOLDER drift velocities v_e = 1e5 and v_i = 2e3 m/s [est]. In the IR, UV and optical bands the circuit/DBD drive model does not apply.

**(b) Typed sweep bounds.**
- Each sweep has lower and upper bounds with SI suffixes and a point count (2–200).
- Sweep types: drive f (default 100k–1000T), fill (Torr), ID and OD.
- Invalid bounds are refused with a message.

**(c) ID and OD sweeps.**
- The ID sweep holds OD fixed; the OD sweep holds ID fixed. OD > ID is enforced, and ID must exceed the 0.1 mm electrode. Invalid points are counted and skipped.
- **Top panel, per-domain response** (each curve normalised to its maximum):
  - optical: light per cycle;
  - acoustic: gas l=0 and shell 0S0 ring;
  - electric: peak gas voltage;
  - thermal: ΔT of the gas;
  - chemical: heat per cycle;
  - magnetic: stated as B = 0.
  - The knee V_b(geometry) is drawn dashed. Its minimum and the ionisation on/off crossings are marked.
- **Bottom panel, natural modes vs geometry** (log f):
  - gas l=0 modes, shell l=0 modes, thermal and chemical corners, and the EM resonance;
  - the drive f as a white line, with ○ where a mode crosses the drive;
  - "Chemical knee: not defined".

**(d) Sound speeds, cited and selectable.**
- **HHO gas.** c(T) = √(γRT/M) with:
  - γ = 1.40 [lit-typical: H2 and O2 both ≈1.40 near 300 K, NIST Chemistry WebBook fluid data];
  - M = 12.01 g/mol [calc from IUPAC atomic weights];
  - R = 8.314462618 [CODATA].
  - This gives 533 m/s at 293 K, rising with the computed gas T.
- **Crystal quartz**, selector `dQz`:

  | Option | cL / cT (m/s) | Source |
  |---|---|---|
  | VRH aggregate (default) | 6048 / 4090 | [lit] Schmitt 2015, Treatise on Geophysics 2nd ed. vol 11, Table 2; cf. Mavko et al., Rock Physics Handbook 6008/4075 |
  | Single crystal ∥Z | 6330 / 4685 | cL [lit] J. Appl. Phys. 44, 5 (1973), doi:10.1063/1.1661916; cT = √(C44/ρ) with C44 = 58.14 GPa [lit Ohno et al. 2006, doi:10.1063/1.2335684] |
  | Single crystal ∥X | 5710 / 5200 | [lit] same 1973 paper |
  | Danny | 5900 / 4090 | cL [given by Danny]; cT from VRH |
  | v0 | 6153 / 4210 | [rec shell_phi_sweep], superseded |

- The selector drives:
  - the drive panel's computed free-shell l=0 modes, from the exact j1/y1 traction-free root;
  - all sweeps;
  - the quartz wavelength of the acoustic waveform.
- The precomputed 3-D presets were rerun with `--qz-sound vrh` (the default), which moves scope 0S0 from 1.868 to 1.855 MHz.
- The other worker's Shell_Diameter_Phi_Sweep still uses 6153/4210 and was not edited.

## 9. The v0 prototype: what it does not do

- No l≥1 fields in the solver; no anisotropic quartz.
- No 3D electrodes, feeds or heat sink.
- No plasma kinetics. Chemistry is a lumped, placeholder-parameterised model (§8.3), not a reaction mechanism.
- No measured optical constants for the elbaite sol-gel or the phosphors beyond the [rec]/[est] values.
- The full-stack scenario assumes every domain circulates P at once, with a 10%/90% wall/light split [est].
- No uncertainty bands yet.
- The viewer is radially symmetric, so the axis choice does not change the picture.

## 10. Screenshots

All in `/workspace/grok_thread/sphere_model_v0/screenshots/`, from headless Chromium with no console errors:

| File(s) | Content |
|---|---|
| 01, 03, 04 | minB quarter-cut: steady 1 W, then after GO at 1 ms and 100 ms |
| 02 | minB spectral panel |
| 05–09 | minB orthographic: shared clock at 3 ps, 150 ns and 20 ms; dilated; GO running |
| 10, 11 | minA orthographic (dilated) and quarter-cut |
| 12–16 | base5: quarter-cut, spectral panel, after GO at 10 µs and 1 s, true scale at 10 kW |
| 17 | base5 orthographic (dilated) |
| 18 | phi6.78 at 1 kW |
| 19 | lock54 spectral |
| 20–25 | Drive panel: blank inputs refused; single cycle at 1 kHz / 22 Torr / 600 V (example inputs); f sweep; fill sweep; response table; scope orthographic with the drive f |
| 26 | scope quarter-cut |
| 27–30 | v0.2 scope waveforms: quarter-cut steady and after GO; orthographic shared clock and dilated |
| 31, 32 | base5 at 10 W: waveforms, quarter-cut with outer layers greyed "not modelled yet"; orthographic |
| 33 | minA at 100 kW: quarter-cut, face 1 CHEMICAL, flags firing |
| 34 | scope with the quartz opacity slider at 0.3 (default 0.7 in 27) |
| 35–38 | iPhone 390×844 (touch): face labels; after one-finger orbit; after pinch-zoom; orthographic |
| 39–41 | v0.3 drive frequency axis and regime flags at 2.5 MHz (ion-feedback caution), 50 GHz (quasi-static invalid, no formation) and 600 THz (optical band) |
| 42 | f sweep, 100k–1000T, 60 points |
| 43, 44 | ID sweep (OD 2 mm) and OD sweep (ID 1 mm) at 2 MHz: per-domain response, knee, modes vs geometry with crossings |
| 45 | fill sweep with typed bounds 1–1k Torr, 25 points |
| 46, 47 | sound-speed selector on Danny 5900 m/s, with sources; quarter-cut waveforms using quartz 5900 |
| 48–50 | iPhone: frequency axis and regime flags; ID sweep; top with the v0.3 label |
