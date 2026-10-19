I reached the repo. This is a review of what is on `main`, not a re-run of the solver. Figures below are the repo’s own estimates.

## What I think you are trying to do

You are trying to design a small sealed quartz bubble filled with stoichiometric HHO (2:1 H₂:O₂), driven near a Paschen ionisation knee, with concentric functional shells around it: a dielectric/piezo layer (BTO), an elbaite sol-gel, a downshifting phosphor, and an outer magnetic, nonlinear, or heat-sink layer. The point of the model is not a single “full physics” solve. It is a radial, timescale-separated coupling of light, sound, electric and magnetic fields, heat, and a stub of chemistry, so you can see which geometry and power stay under stress, Curie, phosphor-saturation, and autoignition limits, and look at that in the browser viewer.

Around that physics you have built an information layer: a design-state file, a review ledger, planted-mistake scoring, cost rollup, a receipt gate, and a multi-model review loop. That layer is there so estimates do not get promoted to “locked” without a trace. The physics is still a paper model. `DESIGN_STATE.md` says so, and nothing in the solver output has been measured.

## What to fix, and how

Do these in this order. Do not open the retired list (oil bath, slotted Cu/Ag shell, ribs, 6.75 kHz except as history, 0.2 T, the 13 GHz atom-count ceiling, cold-regime work, `Backwards_Derived_Spec_from_Ionisation`).

**1. One geometry of record, shared by the spec and the solver.**

`DESIGN_STATE.md` and `solver_v0.py` do not describe the same object.

- Lock shell: spec says 5.4 mm OD and a 0.944 mm wall. The `lock54` preset keeps a 1 mm wall and notes that 5.4 mm might be the gas diameter instead. Those are different devices.
- Test shell: spec is 1 mm ID, 2 mm OD, 0.5 mm wall. That matches `scope` / `minB`, but `minA` is a third shell (1 mm wall, 3 mm OD).
- Layer order: spec is quartz, then BTO, then tourmaline, then phosphor, then an open outer layer. The solver stack is quartz, elbaite (`layer2`, 5 µm), inner phosphor, Ti/Pt, BTO, Gd-Dy, CALORIVAC, outer phosphor, ferrite, with φ steps starting at the BTO outer edge. The material name string for layer 2 still says “50 nm”.
- Thickness mode in the spec is 3.236 MHz. The solver’s `lock54` summary drives at 3.018 MHz.

Best way: put radii, thicknesses, fill pressure, and layer order in one JSON (or YAML) that both `DESIGN_STATE.md` and the solver load. A CI check fails if the markdown numbers and the preset diverge. Until that file exists, stop adding presets. Ambiguous labels (“5.4 mm bubble”) should be deleted, not commented.

**2. Treat the thermal boundary as the design result, not a temperature under a fake sink.**

For the full stack the outer surface is held at 293 K. No sink has been chosen, so those temperatures are a reference, not a prediction. For the bare 2 mm shell the solver already uses still-air convection plus radiation, and `solver_v0_output.txt` puts the quartz inner wall at about 962 K at 1 W (`scope` and `minB`), with the gas centre near 1228 K. That is the result that should lead the viewer: at 1 W in still air the minimal test is past HHO autoignition. The 100 kW lines that sit on the 3000 K cap are a numerical ceiling, not a design point. The spec already caps the lock shell near 7.5 kW because stress hits about 48 MPa around 7.67 kW.

Best way: for every case, report the outer conductance required to stay under autoignition, under the BTO Curie point (spec: crossed near 10 W), and under the stress cap. Do not plot a temperature unless the boundary condition that produced it is named on the plot. Drop decade powers that only hit the 3000 K clamp from the default viewer sweep.

**3. Close the power books before adding physics.**

`F_WALL = 0.10` and `F_OPT = 0.90` are scenario splits, not a conservation law. Dielectric loss is taken as `P * tan δ` on the same circulating power, ESR and ferrite loss are added again, and the inward half of the phosphor emission is explicitly not tracked (`heat[0] += 0.5 * Pem * 0.0`). Ti/Pt is modelled as nearly opaque (`ALPHA_PT` implies a 100 nm film transmits on the order of 10⁻⁴), so almost all Balmer light becomes heat at the electrode. That is probably the dominant thermal bug in the full stack, and it is already called out in the feasibility plan.

Best way: one function that returns a power table (plasma wall, light, quantum defect, electrode absorption, dielectric, ESR, ferrite, recombination) and asserts the parts sum to the input within a stated tolerance. Run it in CI on `scope` at 0.1 W and 1 W. Add one transparent-electrode preset (ITO or equivalent) beside Ti/Pt, because the spec already lists electrode placement in layer 4 as open, and the opaque film is what makes the optical path a heater.

**4. Keep the chemistry stub out of the heat sources.**

`ETA_DISS`, `NU_CHAIN`, and `WALL_RECOMB` are labelled placeholders. `P_release = E_store / t_conv` can look like a runaway water-formation power. The feasibility plan still says plasma chemistry is unmodelled. A placeholder that emits watts will be read as a result.

Best way: compute and display dissociation time, stored chemical energy, and diffusion time, but do not add `P_release` into the thermal solve until a 0D mechanism exists. Ignition should be a validity flag on gas temperature and pressure, not a chain-branching multiplier.

**5. Fix a few numbers that will silently dominate.**

- `phos_out` has `cT = 25` m/s. If that layer is in the acoustic stack, it will own the loss. Either it is a soft silicone and should be a lumped damper, or the shear speed is wrong.
- The BTO permittivity ramp is not Curie–Weiss. It rises linearly to Tc and then falls. Label it as a switch that turns piezo off above Tc, or replace it with a cited ε(T). Do not call the current curve Curie–Weiss.
- Quartz is isotropic VRH. The selectable sound-speed table is good. Drive-frequency claims (1.87 MHz breathing, 3.236 MHz thickness) should be recomputed from the geometry file in step 1, with the sound-speed key in the output. l≥1 is still not computed here; do not pick a drive frequency from the old sweep until those modes are in this solver.
- `layer2`’s name says 50 nm and the stack adds 5 µm. Spec says about 5 µm. Make the name match the number.

**6. One solver entry point.**

`solver_v0.py`, `shoot.py`, `shoot_v03.py`, `shoot_v04.py`, `shoot_v041.py`, and the drive scripts are parallel histories. The feasibility plan still points at `/workspace/grok_thread/`. The README still says the viewer is in progress, while `DESIGN_STATE.md` has a Pages URL.

Best way: `solver_v0.py` (or a thin `python -m sim`) is the only command CI and the viewer call. Older shoots become tests or get deleted. README links the live viewer and says “estimates unless tagged”.

## What is missing

- A shared geometry schema, and a test that the spec and the code cannot drift.
- Uncertainty bands. Almost every material tag is `[est]` or `[rec]`. Sweeps should show ranges, not one line in `solver_v0_output.txt`.
- A heat sink. Until Danny picks one, the missing output is required thermal resistance, not a temperature.
- A transparent electrode as a solved case, not only a note that Ti/Pt blocks light.
- l≥1 spheroidal and torsional modes, and anisotropic quartz. Isotropic l=0 cannot confirm the thickness-mode number in the spec.
- Angular structure: feeds, the central 50 µm DBD wire, and polar holes are estimates. They set both the magnetic saturation and the hot spots.
- Real plasma/chemistry: Paschen versus fill, H₂O formation, and pressure drift over cycles. The knee depends on n·d; a sealed bubble that makes water will walk off the knee.
- Measured anchors on the cheap bubble first: transmission at 434/486/656 nm, a resonance and Q, IR at a known power, breakdown versus fill. The feasibility plan already lists these. The review harness cannot substitute for them.
- The information layer is ahead of the physics. Ledger, scoring, cost rollup, and the receipt gate are built. The open physics items in `DESIGN_STATE.md` (which shell, heat path, BTO thickness versus Curie, tourmaline versus 434 nm scatter, phosphor, layer 5, fill, central electrode versus external field) are still open. That is the right gap to spend the next iteration on, not another reviewer.

I would not add FEniCS, MEEP, or OpenFOAM cases until steps 1–3 pass. The sim-stack smokes in `DESIGN_STATE.md` show the tools run. They do not show that this sphere is the thing being solved.
