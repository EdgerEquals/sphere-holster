# Minimal Test Configuration: 1 mm ID HHO bubble in bare crystal quartz (2026-10-19)

**Status:** this is a paper calculation. Nothing here has been measured.
**Script:** `/workspace/grok_thread/minimal_test_calc.py`
**Output:** `/workspace/grok_thread/minimal_test_calc_output.txt`
**v0 presets:** `minA` and `minB` in `/workspace/grok_thread/sphere_model_v0/`

**Tags:**
- **[lit]** published value (source named)
- **[rec]** value already recorded in another box report
- **[calc]** computed here from those inputs
- **[est]** an estimate, scaling or assumption. Treat [est] as a placeholder until it is measured.

## 0. Configuration and what is included

| | Case A (primary) | Case B |
|---|---|---|
| Gas cavity ID | 1.0 mm | 1.0 mm |
| Quartz wall | 1.0 mm | 0.5 mm |
| OD | 3.0 mm | 2.0 mm |
| Fill | HHO, exact 2:1 H2:O2 | same |

**Included in the model:**
- the gas cavity;
- one crystal quartz wall, treated as isotropic for the acoustics: VRH average, cL scaled to 5.9 km/s where noted;
- still air outside, with natural convection and IR radiation, emissivity 0.9 [est].

**Not included:** layer two (elbaite sol-gel), the phosphors, BTO, Ti/Pt, Gd-Dy, CALORIVAC and the ferrite. None are present in the bare test.

**Electrodes:** the electrode geometry is a modelling assumption [est]. Section 5 compares three options:
- ID/OD films;
- a DBD with a central wire;
- an electrode-less external field.

## 1. Fill at the ionisation knee

**Criterion used:** the DC Paschen minimum (Townsend breakdown at the lowest voltage), with pd equal to the gas gap.
- Pure-gas minima [lit, Naidu & Kamaraju breakdown table]: H2 is 273 V at 1.15 Torr·cm; O2 is 450 V at 0.70 Torr·cm.
- For the 2:1 mix, a mole-fraction rule [est] gives about **332 V at about 1.0 Torr·cm**. The bracket is 273–450 V at 0.70–1.15 Torr·cm.
- I did not use the retired atom-count ceiling. Plasma-frequency and RF criteria are listed below as alternative definitions.

| Gap definition | p at knee | Molecules in 0.524 mm³ | Atoms |
|---|---|---|---|
| 1 mm (full ID; external field) | **10 Torr** (7–11) = 1.33 kPa = 0.0132 atm | **1.72e14** (H2 1.15e14, O2 5.75e13) | 3.45e14 |
| 0.5 mm (central electrode to wall) | 20 Torr (14–23) | 3.45e14 | 6.90e14 |
| Reference: 1 atm, 293 K | 760 Torr | 1.31e16 (76× the 1 mm knee) | – |

**Reduced field at the knee:** E/N ≈ 1000 Td [calc]. This is far above the self-sustaining threshold, which is typical at the Paschen minimum.

**Other knee definitions [calc/est]:**
- **Plasma frequency equal to the drive.** At 2 MHz the electron density is n_e ≈ 5.0e4 /cm³, an ionisation fraction of only 1.5e-13. The plasma becomes over-dense to a 2 MHz drive almost as soon as it ignites, so 2 MHz couples capacitively or through the sheath, not as a wave.
- **RF breakdown minimum,** where the collision frequency matches ω. With ν_m ≈ 5e9·p[Torr] s⁻¹ [est], the optimum frequency is about 8 GHz at 10 Torr. At MHz drives the breakdown is effectively DC-like within each half cycle.
- **Diffusion length** of the 1 mm sphere: Λ = R/π = 0.16 mm [calc].

**Ignition (explosive) knee:**
- **Chemical energy in the bubble [calc]:** 46 µJ at 10 Torr, 92 µJ at 20 Torr, 3.5 mJ at 1 atm.
- **Minimum ignition energy:** 1.2 µJ for H2–O2 at 1 atm [lit]. Using MIE ∝ p⁻² [est], at 10–13 Torr it rises to about 4 mJ, which is more than the bubble's own chemical energy.
- **Quench distance:** 0.64 mm for H2–air at NTP [lit, ISO/TR 15916]; H2–O2 is smaller (~0.2 mm [est]). With quench ∝ 1/p [est], it is about 11 mm at 13 Torr, well above the 1 mm cavity. **So there is no self-propagating flame at the knee fill.** At 1 atm a flame **can** cross 1 mm.
- **Worst case, an isochoric burn from 1 atm:** peak 10–30 atm [est] gives an inner hoop stress of 0.57–1.7 MPa (A) or 0.72–2.2 MPa (B). That is small next to the 48 MPa design figure [rec], but the shock and thermal pulse are not modelled.
- **Practical reading [est]:** the discharge will recombine H and O to water over many pulses. The fill composition drifts, and the knee drifts with it. Plan to monitor this.

**Effect of the electronegative O2 [est, qualitative; no sourced coefficients used]:**
- O2 attaches electrons by dissociative attachment (threshold about 4.4 eV, O⁻ + O) and by three-body attachment (O2⁻, which matters more at higher pressure).
- Attachment removes seed electrons. That raises the breakdown voltage above the H2-only value (consistent with the 273 → 332 V mix estimate) and favours filamentary, streamer-like DBD over a diffuse glow.
- In H2-rich gas, associative detachment (O⁻ + H2 → H2O + e) returns electrons quickly and partly offsets the attachment.
- Net effect: a modestly higher knee, more pulse-to-pulse jitter, and a stronger dependence on the ± pulse shape. Get the real numbers from BOLSIG+ with cross-section data before relying on them.

## 2. Shell modes (bare quartz) [calc]

**Method:** exact elastic sphere-shell solution (spherical Bessel functions). Isotropic VRH quartz is used, and values in brackets are rescaled to cL = 5.9 km/s.
**Validation:** the same code reproduces the 5 mm sweep values 0S0 0.706, 1S0 3.233, 0S2 0.439 and 0T2 0.636 MHz [rec, shell_phi_sweep_calc_output.txt].

| Mode (MHz) | Case A (3 mm OD) | Case B (2 mm OD) |
|---|---|---|
| 0S0 breathing | 1.353 (1.297) | 1.868 (1.791) |
| 1S0 thickness-type | 3.819 (3.662) | 6.737 (6.460) |
| 0S2 flexural (lowest) | 1.005 (0.964) | 1.243 (1.192) |
| 0S1 | 1.356 | 2.050 |
| 0T2 torsional | 1.112 | 1.632 |
| Slab estimate cL/2h | 3.08 (2.95) | 6.15 (5.90) |

**Gas loading** (HHO c = 533 m/s, Z = 266 Rayl at 1 atm [calc]):

| Fill | Case A, 0S0 shift | Case B, 0S0 shift |
|---|---|---|
| 10–13 Torr | 0.0000% | 0.0000% |
| 1 atm | −0.0004% | −0.003% |
| 100 atm | −0.04% | −0.95% |

**Gas cavity modes:**
- The rigid-wall gas breathing mode is 0.762 MHz.
- **In case B, a higher gas-cavity radial mode (1.849 MHz in v0) sits within ~1% of the shell 0S0 (1.868 MHz).** That is an acoustic crossing worth knowing about.

**Uniform-energy stress estimate:**
- Case A: 1.3 MPa at 1 W circulating, 13 MPa at 100 W.
- Case B: 2.2 MPa at 1 W, 22 MPa at 100 W.
- At 10 kW both exceed 48 MPa (132 and 216 MPa).

**Note:** neither case has an l=0 mode at exactly 2 MHz; B's 0S0 (1.87 MHz) is closest. For Danny's φ-target wall solutions, see layer1_lock_phi_calc_output.txt (another worker's file; read only).

## 3. Thermal [calc]

**Setup:** 1 W of plasma heat on the inner wall; k_quartz 6.2 W/mK [rec]. The outer boundary is natural convection (Churchill sphere correlation) plus radiation into 293 K still air. The real sink is left to Danny.

| | Case A, 1 W | Case A, 0.1 W | Case B, 1 W | Case B, 0.1 W |
|---|---|---|---|---|
| R_wall (K/W) | 17.1 | 17.1 | 12.8 | 12.8 |
| Outer-surface R (K/W) | 445 | 853 | 630 | 1371 |
| Outer surface | 738 K (465 °C) | 378 K | 923 K (650 °C) | 430 K |
| **Inner wall** | **782 K (509 °C)** | 381 K (107 °C) | **963 K (690 °C), above the 573 °C α–β transition** | 432 K (159 °C) |

**Time constants:**

| | Wall diffusion h²/(π²α) | Lumped C/(hA) at 1 W | C·R_wall | Heat capacity C |
|---|---|---|---|---|
| A | 32 ms | 11.9 s | 0.46 s | 26.7 mJ/K |
| B | 8 ms | 4.5 s | 0.09 s | 7.2 mJ/K |

**With an ideal 293 K outer sink (reference only):**
- Case A: inner wall rises 17 K per W; 573 °C is reached at ~19 W; the 48 MPa thermal-stress knee at ~4.8 W (0.58 MPa/K [rec est]).
- Case B: 12.8 K/W, ~25 W, ~6.4 W.

**Conclusion:** without a sink, still air dominates (R_out is 30–100× R_wall). A 1 W plasma can only run in a pulsed or low-duty mode, or with a heat sink.

**Cross-check:** the v0 radial transient solver gives 780 K (A) and 962 K (B) at 1 W, matching the table above.

## 4. Optics [calc; n from rec Cauchy fit, n_o ≈ 1.554]

| | 434 nm (Hγ) | 486 nm (Hβ) | 656 nm (Hα) |
|---|---|---|---|
| Fresnel R per surface | 4.71% | 4.65% | 4.54% |
| One-wall transmission, A (1 mm) | 90.1% | 90.2% | 90.4% |
| One-wall transmission, B (0.5 mm) | 90.6% | 90.7% | 90.9% |
| Transit through one wall, A / B | 5.33 / 2.66 ps | 5.28 / 2.64 ps | 5.21 / 2.60 ps |
| Maximum retardance (k ⊥ c), A / B | 21.6 / 10.8 waves | 19.2 / 9.6 | 13.8 / 6.9 |

- **Internal absorption:** under 1% per pass [est; quartz is highly transparent in the visible].
- **Gas-diameter transit:** 3.34 ps.
- **Reflection loss:** about 4.6–4.7% per surface (normal incidence), not 3.5–4%. Through one wall that is about 9–10% total. From the centre, rays hit both surfaces at normal incidence, so this is the right case.
- **Birefringence:** Δn ≈ 0.009. Because the wall is curved, the retardance varies with direction relative to the c-axis, from 0 along c up to the values above. The emitted light is depolarised and patterned.
- **Optical rotation along c:** 21.7°/mm at 589 nm [lit-typical]; ~41°/mm near 436 nm [est].
- **Not modelled:** reflection from the curved wall back into the cavity (multiple reflections, a few % [est]), and any coatings.

## 5. Electric field geometry [calc; εr 4.5 quartz, average est]

| Geometry | Case A | Case B |
|---|---|---|
| Films on ID and OD: C | 0.376 pF | 0.501 pF |
| E(r) = V·a·b/((b−a)r²), inner/outer | 3000 / 333 V/m per V (ratio 9) | 4000 / 1000 V/m per V (ratio 4) |
| Gas field with a metal film on the ID | **0, the cavity is screened** | 0 |
| DBD (50 µm central electrode, quartz barrier, OD electrode): C | 6.1 fF | 6.1 fF |
| DBD: share of applied V across the gas | 98.4% | 98.8% |
| DBD applied V at the knee (gas ~332 V, 273–450) | ~337 V | ~336 V |
| Electrode-less uniform field: cavity/applied | 0.632 | 0.654 |
| E0 needed for ~332 kV/m in the gas | ~525 kV/m (~1.6 kV across plates) | ~508 kV/m (~1.0 kV) |

**Key point:** a continuous conductive film on the ID cannot drive the gas. For a bare test, use a DBD (internal electrode or wire) or an external field across the sphere.

**Limitations of the DBD estimate:**
- The point-to-sphere field is about 10× non-uniform. Breakdown will start at the central electrode at a lower applied V than the uniform-field estimate [est].
- Use a PIC/MC or fluid-plasma model, or a bench test, to firm this up.

## 6. Does v0 run it? Yes, with these limits

**Presets** (power 0.1, 1 or 10 W of plasma heat):
- `minA`: 1 mm ID, 1 mm wall, 10 Torr HHO, bare.
- `minB`: 1 mm ID, 0.5 mm wall.

**Custom runs** use the solver CLI: `--core-d --wall --p-atm --only minA --build`.

**What v0 does for this case:**
- Gas-loaded l=0 acoustic modes, with gas-cavity modes separated out.
- Radial transient thermal with natural convection plus radiation.
- Optical radial march with Fresnel loss.
- DBD electric scenario.
- Quarter-cut view and the orthographic full-sphere wavefront view.

**Limits:**
- l=0 only in v0; the 0S2, 0T2 and 0S1 values come from the separate calc script and appear as reference lines.
- Isotropic quartz.
- No plasma model: the plasma is a heat source plus a placeholder Balmer emitter weighted by case-B ratios [est].
- The DBD drive is set to shell 0S0 as a scenario, not derived from anything.
- No magnetic element (B ≈ 0 in this test).
- No combustion.

**Screenshots** are in `/workspace/grok_thread/sphere_model_v0/screenshots/`:
- 01–04: minB quarter-cut, steady and after GO
- 02: spectral panel
- 05–09: minB orthographic, shared clock and dilated clock, GO running
- 10–11: minA

## 7. Single-cycle audio drive: Danny's scope (added 10:28–10:30 AWST)

**Danny scope:**
- 1 mm ID × 2 mm OD crystal quartz (geometry B), HHO 2:1 core.
- The **fill amount is open.**
- The sealing temperature is an initial/ambient condition, not a control.
- The drive is a single EMF cycle at a **user-set frequency** (20 Hz–20 kHz, log) and amplitude. Neither has a default.

**Model:** `sphere_model_v0/drive_model.js`, used by the viewer's Drive panel and by node. Example runs are in `sphere_model_v0/drive_model_output.txt`; the inputs used there are **examples, not design values**.

**What is computed** (coupled; gas temperature is never an input):
- **Discharge:** a Manley-type DBD from rest [est]. The gas-gap voltage follows the drive until it hits the HHO Paschen knee for the 0.45 mm gap [est], then clamps. Energy per cycle = V_b × the charge moved through the quartz barrier.
- **Energy partition [est placeholders]:** gas 0.6, wall 0.3, light 0.1.
- **Gas energy balance:** heating, then conduction to the wall (lowest diffusion mode of the sphere, τ_g = a²/(π²α_gas(T, n))), then the quartz radial conduction (k ∝ 1/T), then still air (Churchill convection + radiation). This gives T_gas(t) and T_wall(r, t).
- **States that follow** at fixed atom count and volume:
  - p = N k T_gas / V;
  - n stays constant;
  - c(T) = √(1.4 R T / 0.012011), which is 533 m/s at 293 K;
  - the gas-cavity modes f = x·c(T)/(2πa) (rigid-wall roots) with a boundary-layer + classical Q [est];
  - the Paschen knee, which depends on n·d. **It does not move to first order when the gas heats at fixed N and V.** Only a change in N (chemistry, leaks) or a change in the gap moves it.
- **Ring-down of fast modes:**
  - The gas l=0 radial modes are excited by the centre-weighted heating, through the jump in discharge power at breakdown onset (impulse approximation, valid because f_mode ≫ f_drive).
  - The shell breathing mode is excited by the kink in bulk gas pressure.
  - l>0 modes are not driven by a symmetric source.

**Natural modes and relaxation corners** of this geometry: these are response properties; the drive is set separately.

| Domain | Values |
|---|---|
| Thermal corners | gas conduction ~20 kHz at a 22 Torr fill (4.4 kHz at 100 Torr, ~0.6 kHz at 1 atm: it scales with fill); quartz wall diffusion ~20 Hz; whole bubble to still air ~0.01 Hz |
| Gas cavity modes | 353 kHz (l=1), 567 kHz (l=2), 763 kHz (l=0); they rise with √T |
| Shell modes | 1.24–6.74 MHz |
| EM sphere resonance | ~45 GHz [est] |
| Balmer lines | 457–691 THz |

**So the two thermal corners bracket the audio band.** Within the band, the drive frequency mainly decides how fast heat is deposited relative to the gas's conduction relaxation. The acoustic modes respond only by ringing at their own frequency after each breakdown onset.

**Example (22 Torr, 600 V peak, 1 kHz, one cycle):**
- E/cycle 1.3e-7 J;
- ΔT_gas 0.22 K; ΔT_wall 4e-4 K;
- gas l=0 ring ~0.4 Pa (Q ≈ 13, τ ≈ 5 µs);
- shell 0S0 ring ~0.01 Pa hoop.

**Sweeping f from 20 Hz to 20 kHz** (same fill and amplitude):
- E/cycle stays constant.
- ΔT_gas rises from 0.005 K to 2.2 K, because the deposition gets faster than the gas relaxation.
- Ring amplitudes rise ∝ f, because breakdown happens at a higher dV/dt.

**Fill sweep at 600 V:** there is breakdown only between 10.71 and 98.95 Torr in this model [calc]. The criterion is one voltage definition throughout: peak gas voltage (gas share 98.8 % × 600 V = 593 V) against the HHO Paschen breakdown voltage V_b of the 0.45 mm gap (static knee). In the 1 kHz sweep, 10.8, 27.6 and 70.3 Torr ionise; 4.24 Torr (left of the Paschen curve) and 179 Torr (V_b 868 V) do not.
- **No autoignition flag** is raised for any single cycle tested.
- The steady-state presets do flag it. For example, scope/minB at 1 W gives a 962 K inner wall, which is in the 500–585 °C range.

**Limits:**
- The Paschen form [est] has no left-branch breakdown below ~8 Torr for this gap.
- No plasma chemistry: the H2O formation and the energy it releases are not modelled. The chemical energy stored in the fill is reported for comparison.
- Rigid-wall gas modes.
- Isotropic quartz.
- The DBD electrode geometry is an estimate.

## 8. v0.2 additions for the scope (11:xx AWST)

- **Powers.** Precomputed at 0.1 W to 100 kW in decades.
- **Gas conduction profile at 1 W** [calc]: centre 1228 K, mean 1073 K, wall 962 K. The autoignition flag uses the centre value.
- **Chemical** [lit constants + PLACEHOLDER rates]:
  - the 1 mm core at the 10 Torr placeholder fill stores 4.6e-5 J as 2H2+O2;
  - at 1 W it converts to water in about 0.4 ms, releasing about 0.11 W meanwhile;
  - after that, a dissociation–recombination cycle runs with about zero net heat;
  - knee: not defined.
- **Waveforms** run only from the core to the quartz OD. The single φ shift is at the inner wall.
- See Feasibility Plan §8.3.
