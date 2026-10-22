# Stratified Sphere: fresh context for the discrete, time-evolving model (draft, 2026-10-21)

**Owner:** Danny. This draft is for his review and replaces nothing until he approves it.
**Built from:** DESIGN_STATE.md (19–21 Oct), AGENTS.md, docs/vocabulary.md, the Minimal Test Config, and today's knee table and ionisation-knee notes.
**Not carried over:** the old solver (solver_v0) is a past reference only. None of its code is design.

**Tags:**
- **[DS]** DESIGN_STATE.md
- **[D]** Danny's decision, AWST time given
- **[lit]** published
- **[calc]** worked out from tagged numbers
- **[est]** estimate

Nothing here is measured. No hardware sphere exists yet; "sphere" means the sphere code [vocabulary].

## 1. Purpose

Build, from scratch in Python [D 16:59], a model of the stratified sphere that:
- is **discrete**, made of pieces that each carry their own state, and **evolves over time** rather than being one static snapshot [D 16:54];
- carries all **six physical energy domains** from the start [DS], with every coupling between them as an energy flow and an energy book that closes;
- treats **coherence and resonance** as central, tracking each mode's phase as well as its energy [D 17:03];
- switches over the **knees**, the parametric thresholds where a domain's response changes sharply [D 17:03];
- shows, as its main output, a **visualisation of the amplitude waves moving through the sphere** [D 17:04].

## 2. The sphere (base5)

**Gas core.** HHO at 2:1 H₂:O₂ [DS], sealed.
- Bubble radius 0.57295 mm, so inner diameter 1.1459 mm [DS].
- Fill 10,577.3 Pa = 79.34 Torr = 0.1044 × ambient [DS; calc], so the number of molecules is fixed. Heating raises pressure, not density.
- It never ignites [D 18:41].

**Layers, inside out:**

| # | Layer | Thickness | Notes |
|---|---|---|---|
| 1 | Crystal quartz | 1.43463 mm wall [DS] | Quartz OD ≈ 4.015 mm [DS]. Piezoelectric, not pyroelectric [lit]. One of the three cavities [DS] |
| 2 | Layer two, elbaite tourmaline sol-gel in MTES:TEOS 80:20 silica binder | 9.12441 µm [DS] | Piezo and pyro. Grain alignment is set during gel formation by acoustic and EMF fields [DS] |
| 3 | BTO (barium titanate) film | 2 µm [est, earlier design value] | Its capacitance is the tuning value. The first φ step starts at its outer edge [DS] |
| 4 | Gd-Dy film | 3 µm [est, earlier design value] | Magnetocaloric, Curie ~260 K [lit] |
| 5 | CALORIVAC (epoxy-bonded La(Fe,Mn,Si)₁₃H granules) | to r ≈ 3.27 mm, ≈ 1.24 mm thick [calc, φ step, est layout] | Graded magnetocaloric. Keep below 473 K (hydrogen loss) [lit] |
| 6 | NiZn ferrite (Fair-Rite 61 type) | to r ≈ 5.29 mm, ≈ 2.02 mm thick [calc, φ² step, est layout] | Saturates ~0.25 T, Curie > 573 K [lit Fair-Rite] |

- **Overall OD:** ≈ 10.57 mm [calc].
- **Layer 5 slot** [DS] is open: PPLN/KDP (non-linear), or ferrite / Gd-Dy / CALORIVAC (magnetic or caloric). The heat sink is Danny's choice.
- **Tourbillon:** Danny's specification is one mixed layer, with tourmaline, BTO and Gd-Dy grains in the same binder [DS]. It is also the third cavity [DS]. Whether layers 2–4 are separate shells or that single shell is open (Q13).
- **Thermal reference:** the outer reference is 293 K [DS, locked]. Kelvin internally; the display shows °C alongside K [DS].

## 3. Energy domains

- **Six physical domains** [DS]: optical, acoustic, electric, magnetic, thermal, chemical.
  - Five travel as waves: optical, acoustic, magnetic, thermal, chemical.
  - Electric is the driving field. It sets the thresholds and drive conditions for the others [DS].
- **Information** is the seventh domain, the information layer. It is real, but not a physical wave [DS].
- **Ionisation and plasma** sit in the electric harness on the field side, and in the chemical harness for the plasma chemistry. The plasma state crosses both [DS].
- **Electric and magnetic** are two halves of one wave. The spin and rotation of the geometry couple them [DS].
- **Harnesses:** **17 knee + 7 domain** [D 18:30]. This replaces 12 + 7.

## 4. Knees

The count follows the table [D 18:30]. Today it has 17 knees, 15 with a layer in base5. Thresholds are taken from the knee table draft.

| # | Knee | Domain(s) | Layer | Threshold |
|---|---|---|---|---|
| 1 | Balmer emission | optical ← gas | gas | 434 / 486 / 656 nm; ≥ ~14.3 eV per Hα [calc] |
| 2 | Smoky-quartz bleaching | optical ↔ thermal | quartz | from ~473 K [est] (smoky or not: open) |
| 3 | χ² frequency shift (PPLN/KDP) | optical | Layer 5, not in base5 | needs a megawatt coherent pump [DS] |
| 4 | Piezo knee (the mixer) | acoustic ↔ electric | BTO, layer two, quartz | field scale ~28.9 MV/m in BTO [calc, est] |
| 5 | Quartz α–β | acoustic / electric / thermal | quartz | 846.15 K (573 °C) [lit] |
| 6 | ΔE effect | magnetic → acoustic | needs Ni / Galfenol, not in base5 | ΔE/E ~161–168 % = one φ rung [lit] |
| 7 | **Ionisation knee** (= ionic knee [D 18:39]) | electric → chemical / optical / thermal | gas | see below |
| 8 | Plasma frequency knee (its own row [D 18:40]) | electric ↔ optical | gas | set by electron density |
| 9 | BTO Curie | electric / acoustic / thermal | BTO | 393 K [lit]; piezo and pyro off above |
| 10 | BTO field-tuned capacitance | electric | BTO | ~28.9 MV/m field scale [calc, est] |
| 11 | Ferrite saturation bend (parametric) | magnetic | ferrite | 250 mT at 1200 A/m [lit] |
| 12 | Ferrite Curie | magnetic → thermal | ferrite | > 573 K [lit] |
| 13 | Ferrite frequency roll-off | magnetic → thermal | ferrite | Q 130 at 5 MHz → 4.6 at 20 MHz [lit] |
| 14 | Gd-Dy Curie (magnetocaloric) | magnetic ↔ thermal | Gd-Dy | ~260 K [lit] |
| 15 | CALORIVAC transition | magnetic ↔ thermal ↔ acoustic | CALORIVAC | 261–310 K by grade, ~1 % volume step [lit] |
| 16 | HHO autoignition (**limit, never crossed**) | thermal → chemical | gas, inner wall | 773.15–858.15 K [DS] |
| 17 | H₂ dissociation | chemical | gas | 4.478 eV per H₂ [lit] |

- **Thermal trigger:** one of the Curie points, #9, #14 or #15. Which one is open [D 18:40].
- **Never ignite** [D 18:41]: the sphere always stays below autoignition and modulates over the ionisation knee, which is what the ionisation needs. Cascading cooling is what keeps it below [DS].
- **Damage limits** (not knees):
  - quartz stress 48 MPa [DS];
  - BTO breakdown, 2.6–30 MV/m for crystalline films [lit];
  - CALORIVAC 473 K [lit].
- **Ionisation knee for base5.** Breakdown runs along the full gas diameter, 1.146 mm, because there are no electrodes.
  - Pressure × gap is 9.09 Torr·cm [calc], about 9× the HHO Paschen minimum of ~1.0 Torr·cm [est from lit minima: H₂ 273 V at 1.15, O₂ 450 V at 0.70].
  - Needed across the gas: ~0.94 kV, ~0.82 MV/m, ~314 Td. Range 0.6–1.4 MV/m [calc/est].
  - The fill that would sit at the minimum is ~8.7 Torr ≈ 1,160 Pa [calc]. The old "10 Torr for a 1 mm gap" was the Paschen minimum for the 1 mm-ID test shell [DS]. It doesn't apply to base5.
- **Knee frequency is emergent**, coming from the layers, not a dial [DS].
- **Every layer gets its own knee, pump and boundary reflection.** Energy shifts down, reflects, and comes back up in phase [DS].
- **Storage and shifting layers:** storage layers hold the energy; shifting layers convert frequency at the knees ("rungs store, knees mix") [DS].

## 5. Couplings and the energy book

- **Every coupling is an energy flow** from one domain or piece to another. What leaves one side arrives at the other in the same step.
- **The energy book closes every step:** drive in = change in stored energy + flows out of the sphere. It is checked every step, so a missing watt shows up at once.
- **Known couplings** [DS]:
  - acoustic → thermal (mode loss in each layer);
  - gas acoustic ↔ gas thermal (gas Q at the live state);
  - pyroelectric (thermal → electric);
  - electrocaloric (electric → thermal, with entropy going to the chemical harness);
  - piezo (acoustic ↔ electric, with phase kept);
  - temperature shifting mode frequencies (detune);
  - magnetocaloric (magnetic ↔ thermal);
  - chemistry ↔ thermal;
  - optical absorption → thermal;
  - conduction between pieces;
  - heat out through the outer boundary.
- **Three thermal rates plus thermal mass are never lumped** [DS]: switching frequency, heat-transfer speed, heat-removal rate, and thermal mass.
- **Every layer is a pair of boundaries,** inner and outer. The stack is a chain of interfaces [DS].

## 6. Coherence and resonance

- **Each ringing mode carries a size and a phase.** Energy comes from the size. Locking, detune, beats and interference come from the phase [D 17:03].
- **Lock rule** [DS]: two modes lock when their frequencies differ by no more than half the sum of their linewidths (f/Q).
- **The geometry sweep looks for maximum locking** [DS]. Modes lock where they lock, and the model never picks one. The golden ratio sets the scale of the tracking path, not a rigid rule.
- **Three cavities** [DS]: the hydrogen bubble, the quartz layer and the tourbillon.

## 7. Time evolution

- **Temperature changes dynamically all across the sphere** [D 16:47]. So mode frequencies, gas pressure, gas Q and lock state are all live, never frozen at 293 K.
- **Time scales** run from mode cycles up to 50 MHz [DS], through ring-up and ring-down, to thermal times of seconds.
- **The fast and slow parts are stepped together,** and steps shrink at knee crossings.
- **Zero run** [DS]: with no drive, every field is exactly 0 and the whole stack sits at exactly 293 K.
- **Pulse run** [DS]: a single pulse puts energy into every domain at once. Each layer's response, layer by layer, is the output.

## 8. Drive

- **The 4 W run** [D 16:07]: one steady 4 W case at base5, 1 W per channel, with the amplitudes written out.
  - **Thermal:** 1 W into the gas.
  - **Acoustic:** 1 W at the geometry's own computed mode frequencies, never a set target [DS].
  - **Magnetic:** 1 W as heat in the ferrite, a labelled placeholder until E–B coupling exists [DS].
  - **Electric:** parked [D 16:43]. A steady current through BTO would need ~9.9 × 10⁹ V/m [calc], so the options are placeholder heat or AC dielectric loss.
- **The frequency retune as the sphere heats** is parked until the discrete model exists [D 16:47].
- **Design drive** [DS]: a triad of EMF, acoustic and thermal. The acoustic mode sits below the electric mode but drives it through the piezo knee, as in a parametric amplifier.
- **How the gas is driven** with no electrodes is open [DS].

## 9. Outputs and visualisation

- **Main output** [D 17:04]: an animated cross-section of the sphere showing the amplitude waves moving through each layer.
  - Thin films are widened for display and marked "not to scale".
  - Colour shows amplitude; phase shows as moving bands.
  - A switch for each domain.
  - Side panels: each mode's size and phase, energy by domain, knee events and locks.
  - Two time views: slow (seconds) and a slowed window where MHz waves are visible.
- **Data per run:**
  - for each piece over time: temperature, field, polarisation, gas pressure and species;
  - for each mode: size, phase, frequency, Q and detune;
  - energy per domain and the full energy book;
  - events: knee crossings and locks gained or lost.
- **Labels:** every number in the output carries its source tag.

## 10. Standing rules

1. **The six domains are always present until the topology proves they're not** [D 18:46]. A zero that comes from a modelling simplification is not proof that a domain is absent.
2. **Gas physics:**
   - gas Q comes from the solver at the live state [DS];
   - the gas is HHO 2:1 only [DS];
   - fully rarefied only, so every pressure is below ambient [DS];
   - no golden-ratio (φ) pressures [DS].
3. **Never ignite;** modulate over the ionisation knee [D 18:41].
4. **No electrodes** of any kind [DS].
5. **Frequencies come from the geometry,** never from an outside dial or target [DS].
6. **Kelvin internally,** °C shown alongside in the display [DS].
7. **Never reintroduce a retired item.** Treat everything under Open as undecided [DS].
8. **Terms:** say "energy domains" [DS]. Use Danny's terms; new terms only once he approves [DS].

## 11. Open questions

1. Which Curie point is the thermal trigger: BTO 393 K, Gd-Dy 260 K, or CALORIVAC?
2. How the electric channel delivers its watt: placeholder heat, or AC dielectric loss.
3. **How a field reaches the gas.**
   - With breathing modes only, any symmetric radial field gives exactly zero field inside the gas (Gauss's law [lit]).
   - The metal films (Gd-Dy, CALORIVAC) would shield the gas from an outside electric field [lit].
   - Induction would need ~9 T at 50 MHz [calc].
   - Under rule 1, this is a gap in the model, not proof that nothing reaches the gas. It needs modes beyond breathing and the E–B wave.
4. Keep base5 at 79.3 Torr (~9× the Paschen minimum), or move the fill toward ~8.7 Torr? That fill is below the lowest pressure swept so far (0.05 × ambient [DS]).
5. What "fully rarefied" means for the gas physics. At base5 the gas behaves as an ordinary conducting gas, not free-molecular (mean free path ~1 µm against a 0.57 mm radius [calc]).
6. Whether the ionisation knee is crossed at low MHz (DC-like) or in the tens of MHz (lower, diffusion-set threshold) [lit].
7. The physics of mode-to-mode coupling at the piezo knee.
8. How the solids' sound speed and density change with temperature, needed to retune the modes live.
9. The outer boundary for each domain (parked [DS]).
10. The CALORIVAC grade (sets knee #15).
11. Whether the quartz is smoky (sets knee #2).
12. Thicknesses of CALORIVAC and ferrite (today they come from the φ-step layout [est]). Also Layer 5 and the heat sink.
13. Layers 2–4 as separate films, or the single mixed tourbillon shell [DS].
14. The outer phosphor is still in the old solver; it should not carry into the new model.
15. Whether the boundary reflection lands on a real mode (a true idler) or just bounces [DS].

## 12. Retired (never reintroduce)

- **Never reintroduce** [DS]:
  - oil bath;
  - slotted Cu/Ag outer shell;
  - ribs or segments;
  - 6.75 kHz (history only);
  - 0.2 T;
  - the 13 GHz atom-count ceiling;
  - cold-regime work;
  - Backwards_Derived_Spec_from_Ionisation (its numbers and layer roles);
  - Grok's radial diamond spokes;
  - electrodes of any kind (Ti/Pt, ITO, central wire, DBD centre electrode);
  - the 2 MHz selection target;
  - off-spec gas mixes (1:1, 3:1, 4:1) and the 1.618 atm result.
- **Phosphor:** out of the model [DS].
- **Removed today:** the 1 Hz envelope [D 16:45].
