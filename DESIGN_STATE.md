# Stratified Sphere — Design State (single source of truth)

**Updated:** 2026-10-19 AWST · **Owner:** Danny (EdgerEquals)
**Repo:** https://github.com/EdgerEquals/stratified-sphere-model
**Live viewer:** https://edgerequals.github.io/stratified-sphere-model/
**Raw link for AI tools:** https://raw.githubusercontent.com/EdgerEquals/stratified-sphere-model/main/DESIGN_STATE.md

All figures are paper estimates from the v0 model. None have been measured.
Every tool working on this project reads this file first, never reintroduces a retired item, and treats everything under **Open** as undecided.

---

## Locked

### Core: HHO
- **Fill:** HHO at a 2:1 H₂:O₂ ratio. The fill amount is open and can be swept.
- **Ionisation knee:** about 10 Torr for a 1 mm gap. The earlier ~22 Torr figure assumed a 0.45 mm gap to a central electrode, which is retired (2026-10-19); how the gas is driven without electrodes is Open item 8.
- **Electrodes:** none. There are no electrodes in the design (Danny, 2026-10-19): no Ti/Pt film, no ITO/transparent electrode, no central wire. See Retired.

### Layer 1: quartz
- **Shape:** a sphere unless Danny says tube.
- **Lock shell:**
  - 5.4 mm OD with a 0.944 mm wall.
  - Thickness mode at 3.236 MHz.
  - Power capped at about 7.5 kW, because the shell reaches 48 MPa at about 7.67 kW.
- **Alternative:** the 6.78 mm golden-ratio (φ) size, which stays under 48 MPa at 10 kW.
- **Test shell:**
  - 1 mm ID and 2 mm OD, with a 0.5 mm wall.
  - Breathing mode at about 1.87 MHz.
- **Golden-ratio shift:** the only φ shift currently modelled is at the boundary from HHO into the quartz. Nothing outside the quartz is modelled yet.

### Layer 2: BTO dielectric
- **Thickness:** set by heat transfer.
- **Tuning:** its capacitance is the tuning value.
- **First φ step:** starts at its outer edge.
- **Curie point:** crossed at about 10 W.

### Layer 3: elbaite tourmaline sol-gel
- **Thickness:** about 5 µm, within a 3–8 µm range.
- **Binder:** a silica sol-gel (MTES:TEOS 80:20). (The earlier Pt-primer note is moot: electrodes are retired, 2026-10-19.) The tourmaline needs a silica shell formed at pH 8–9.

### Layer 4: downshifting phosphor — removed pending further work (2026-10-19)
- **Removed pending further work (2026-10-19):** the inner downshifting phosphor is out of the model for now (solver `phos_in`, Cr3+ garnet, 20 µm, 770 nm, and its constants and 770 nm band). Paused, not retired. Layer two (elbaite) now passes the light on to the BTO film and then the Gd-Dy film, which absorbs it.
- **Options (kept for when it returns):** KSF, which saturates at about 8–16 W, or CASN, which saturates at about 80 W.

### Layer 5: outer layer
- **Nonlinear option:** PPLN or KDP. Either gives real gain only with a coherent pump at the megawatt level.
- **Magnetic or caloric option:** ferrite, Gd-Dy or CALORIVAC.
- **Heat sink:** Danny's choice, still open.

### Thermal reference and temperature convention (locked 2026-10-19)
- **Kelvin reference: locked.** The 293 K outer reference temperatures stay. Danny uses them to select thermal active materials placement in the tone. Do not replace them with required-conductance output (reviewer suggestion rejected, round 5).
- **Kelvin is canonical.** All calculations, the solver, data files and this spec use Kelvin, from 0 K up. Celsius is never used in a calculation, solver, data file or spec value.
- **Celsius is a GUI-only display rule.** In the viewer/visualisation layer every displayed temperature shows its °C value alongside the K value.
- **Ambient in the GUI is a linked K/°C pair:** enter either; the other updates automatically (K = °C + 273.15). The model receives K.
- **Supersession chain (all 2026-10-19):** 293 K single reference → K + °C everywhere → Celsius-only ambient → linked K/°C ambient → **Kelvin canonical, °C in the GUI only** (current). Earlier wording that the spec states every temperature in both K and °C is superseded: the spec states K; the K + °C pairing is a GUI rule. No bulk °C conversion of the spec is needed.

## Open
1. Which quartz shell: the 5.4 mm lock shell, the 6.78 mm φ shell, or the 1×2 mm test shell. Sphere or tube.
2. The heat path. At 1 W in still air, the test shell's inner wall gets past HHO autoignition.
3. The BTO thickness, and how to keep it below its Curie point.
4. The tourmaline thickness, traded against scattering at 434 nm. Also the cure temperature and whether it sits inside or outside the BTO.
5. Which phosphor — inner phosphor removed pending further work (2026-10-19); the choice waits until it returns. (The electrode-placement / Ti/Pt light-blocking question is closed: electrodes are retired, 2026-10-19.)
6. Which layer 5 option.
7. The HHO fill amount.
8. **How the gas is driven with no electrodes.** Open for Danny. The old "central electrode or external field" choice is superseded because electrodes are retired. Since 2026-10-19 the code has **no drive mechanism defined**: `drive_model.js` and `solver_v0.py` carry a fail-closed stub (zero deposited energy, zero discharge, zero electric/magnetic field and loss). The old DBD gap, Paschen V_b and the 10.71–98.95 Torr window were removed with the electrodes. Do not invent a drive to fill the stub.

## Retired (never reintroduce)
- Oil bath
- Slotted Cu/Ag outer shell
- Ribs or segments
- 6.75 kHz (may be mentioned as history only)
- 0.2 T
- The 13 GHz atom-count ceiling
- Cold-regime work
- `Backwards_Derived_Spec_from_Ionisation`: its numbers and layer roles
- Grok's radial diamond spokes
- Electrodes of any kind (retired 2026-10-19): Ti/Pt film, ITO/transparent-electrode case, central 50 µm wire / DBD centre electrode. There are no electrodes in the design.

---

## Information layer (harness architecture)
Full spec: the Drive doc "Stratified Sphere — Information Layer (Harness Architecture) 2026-10-19".

- **Holsters (Danny, 2026-10-19):** 19 in total, one per knee and one per energy domain: **12 knee holsters + 7 energy-domain holsters**. The seven energy domains are optical, acoustic, electric, magnetic, thermal, chemical and **information** (the information layer is a real domain). Each knee and each energy domain has its **own** holster; the holster is not a single shared component. Say "energy domains", not "power domains". (Superseded: "18 harnesses: 6 domain + 12 knee", and the same-day 6 + 12 = 18 holster note.) The domain holsters run in parallel on GitHub Actions and pass results to each other between rounds.
- **Coordinator:** Cursor. It reads a granularity dial: shallow for scouting, deep for validating.
- **Checks:**
  - The Claude API audits Cursor's merges every few rounds.
  - Claude Code does the end-of-iteration reviews.
  - Grok runs source cross-checks on demand.
  - Grok and Claude check each other's output.
  - A validation harness tracks every handover.
- **Tiers, from the top:**
  1. Danny
  2. Stratified Sphere Bot, which holds the intent and acts as gatekeeper
  3. Paid reviewers: Claude, Grok and ChatGPT. Perplexity is on hold for now.
  4. Harnesses
  5. Free tiers: Kimi, DeepSeek, Qwen or Qwen Studio, and a local Llama
- **Compute:** SymPy, SciPy and C. FEniCS, MEEP, OpenFOAM and COMSOL or ANSYS are called when needed.
- **Still open:**
  - One repo or several
  - Who handles reporting
  - Julia
  - A loss map for each handover
  - A cost budget
  - Keeping Kimi working step by step
  - Knee harness details
  - Which harness to build first (thermal was suggested, then paused)

## Locked holster architecture (2026-10-19, from review round 3)
Danny locked items 1–4 on 2026-10-19 from review round 3 (`reviews/2026-10-19_round3/`) and item 5 the same day from round 4 (`reviews/2026-10-19_round4/`). Treat them as decided; do not re-open them without Danny. Status updated 2026-10-19 14:40 AWST: items 1–3 and 5 built, item 4 partial. Details: `ledger/README.md`, `gateway/README.md`.

| # | Item | What it is | Source | Order | Status |
|---|---|---|---|---|---|
| 1 | GitHub review ledger | Every review finding is filed as a GitHub issue and appended to a permanent, append-only JSONL log; reviewers are scored from it. | Round 3: DeepSeek, Claude and Grok's top pick (Kimi's runner-up); closes round 2's "review loop doesn't close" gap | **First.** Everything else builds on it. | **built** (issue #7): `ledger/findings.jsonl` on main, schema v1, workflow `ledger.yml`; issue mirroring off by default (dispatch, threshold major, cap 5/day) |
| 2 | Scoring rubric (planted mistakes) | Each reviewer is scored on whether it catches mistakes deliberately planted in the work it reviews. | DeepSeek's round-2 idea (seed known defects), made concrete per Claude's round-3 suggestion (score reviewers from ledger status) | On top of the ledger | **built** (issue #8): fixture `ledger/planted/v1`, `ledger-score.yml` (offline default); no paid planted run yet |
| 3 | Monthly cost rollup per model | Spend per model per month, rolled up from the ledger's cost stamps, so spend per model is visible. | Grok's round-3 suggestion (a cost stamp on every ledger record) | On top of the ledger | **built** (issue #9): `ledger/costs_YYYY-MM.*`, `ledger-costs.yml` (monthly cron + dispatch), Pages `ledger/`; October backfilled |
| 4 | FEniCS/OpenFOAM MCP gateway | Models drive simulations directly through an MCP gateway to the open simulation stack (sandboxed). | Kimi's round-3 top pick; Claude and Grok's runner-up (after the ledger) | **After the ledger** | **partial** (issue #10): hardened FEniCS + OpenFOAM MCP containers pass CI (`mcp-gateway.yml`) and log to the ledger, but expose only the existing smoke tests; upstream dolfinx-mcp failed to initialise in CI |
| 5 | Receipt gate + spec-review class | A paid Claude/Grok review counts as a **code review** only if a CI execution receipt covers every component it touches; otherwise it is a **spec review**: routed to the cheap Kimi/DeepSeek path by default, never scored, never mirrored as fixable issues. Receipts are written by CI only (GitHub artifact attestation) and must prove real execution: the entrypoint is imported **and** called (line trace), is not a stub (AST check: pass / ... / raise NotImplementedError / return-a-constant), and passes ≥1 numeric check. A stub with locked I/O never qualifies. | Round 4 (issue #11): DeepSeek, Claude and Grok proposed the receipt + spec-review class; Kimi's pushback (a stub with locked I/O schemas would satisfy a naive receipt) is built in as the anti-stub rule | Gates items 1–3; uses item 4's CI | **built** 2026-10-19: `harness/receipts.json`, `scripts/receipt.py`, `scripts/stub_detector.py`, `scripts/exec_trace.py`, `scripts/receipt_gate.py`, `.github/actions/receipt/`; receipts from engineering-tests (compute-core), sim-stack (sim-fenics), mcp-gateway (mcp-gateway); dial `receipt_gate: enforce|warn|off` (enforce); ledger schema v1.1. Verified in CI 2026-10-19: first attested receipts for all three components at 719ec3f; gate dry-runs classify a DESIGN_STATE-only commit as spec-review and a `solver_v0.py` commit as code-review; pre-gate findings tagged legacy |

Build order: (1) ledger → (2) rubric and (3) cost rollup on top of the ledger → (4) gateway after the ledger → (5) receipt gate in front of the paid reviews.

Receipt gate rules (item 5): code-review needs a valid receipt for **every** touched component (`harness/receipts.json`), at the target's exact file contents (sha256 per file), with a verified attestation from the producing workflow on main. Docs/spec/config-only diffs are always spec-review. Existing findings before the gate are `legacy` (no receipt). Paid models run on a spec-review only with the `spec_review=spec-review-paid` dispatch input; `spec_review=spec-review` forces a spec review (e.g. a DESIGN_STATE review).

### Open tasks
- ~~**Fix the ordering gap (review layer ahead of execution layer)** (issue #11).~~ **Decided and built 2026-10-19** as locked item 5 (receipt gate + spec-review class, with Kimi's stub concern as the anti-stub rule). Round 4: `reviews/2026-10-19_round4/`.

## Simulation stack (CI)
Workflow `.github/workflows/sim-stack.yml` (one job per tool; push to `sim/**`, manual, weekly). Details and digests: `sim/README.md`. Status as of 2026-10-19: all six pass.

| Tool | Pinned version | Smoke test | Status |
|---|---|---|---|
| FEniCSx | DOLFINx 0.11.0 (Docker, digest-pinned) | Poisson (exact P2, sin·sin P1 rate ≈ 2) + 1D heat T_max = qL²/8k | PASS |
| MEEP | pymeep 1.35.0 nompi, Python 3.12.15 (conda-forge) | 2D PEC cavity, Harminv TM11/TM21 within 0.5 % | PASS |
| OpenFOAM | v2512 (opencfd Docker, digest-pinned) | icoFoam lid-driven cavity: residuals, continuity, max\|U\| < lid | PASS |
| CalculiX | ccx 2.21 (Ubuntu 24.04 apt 2.21-1) | B32 cantilever vs PL³/3EI, 2 % | PASS |
| Code_Aster | 18.1.0 (simvia Docker, digest-pinned) | POU_D_E cantilever vs PL³/3EI + bundled forma01a | PASS |
| Gwyddion | 2.64 (Ubuntu 24.04 apt 2.64-1.1build3) | load .gsf via Gwyddion GSF module, size + RMS = A/√2 | PASS |

## Danny's decisions on round-5 review (2026-10-19)
Source: `reviews/2026-10-19_round5/` (Claude and Grok replies to the open repo prompt). Decided by Danny on 2026-10-19. Staged ledger dispositions: `ledger/pending/2026-10-19_round5_dispositions.jsonl` (not yet ingested; the ledger is CI-written).

### Fold (accepted; to be built later, after Danny's validation)
1. **One geometry-of-record file** read by both this file and the solver, with a CI check that fails on drift (Grok).
2. **Recompute drive frequencies from that file**, with the sound speed and formula recorded in the output. This settles 3.236 vs 3.018 MHz (Grok).
3. **A power budget that sums to the input**, tested, with no double-counted loss (Grok).
4. **Keep placeholder chemistry (`P_release`) out of the heat sources**; ignition becomes a validity flag (Grok).
5. **Small number fixes:** `phos_out` cT = 25 m/s; the BTO ε(T) curve's "Curie-Weiss" label; the layer-2 "50 nm" label vs 5 µm (Grok).
6. **Fix the factor-of-2 ring-jump bug** in `drive_model.js` (`maxJump` taken from the partial-step Ed/dt), with an ncyc-invariance test (Claude found the split; traced 2026-10-19).
7. **GUI temperatures: K with °C alongside, ambient as a linked pair** (Danny's clarification, 2026-10-19): every temperature the viewer displays shows °C next to K, and the Kelvin-only ambient field (`dTa`, commit 21b5fa5) becomes two linked fields, K and °C, that sync both ways (K = °C + 273.15). The model, solver, data files and spec stay in K; no bulk °C conversion of the spec. Not built yet. Known K-canonical gap for this fold: `drive_model.js` compares the autoignition range in °C (`AUTOIGN_C = [500, 585]`) and prints flags in °C; that should become K internally (773.15–858.15 K) with °C only in the display.

### Cut (rejected)
- **All electrode items.** There are no electrodes in the design, period: no Ti/Pt film, no ITO/transparent-electrode case, no central 50 µm wire / DBD centre electrode. Added to Retired.
- **Electrodes removed from the model entirely (Danny, 2026-10-19).** No formula, geometry, preset or code path references an electrode. `drive_model.js` lost the centre-electrode gap (r0, gap, Cd/Cg, share, V_amp), Paschen V_b, the ionisation window and the knee/clamp conduction; `solver_v0.py` lost the Ti/Pt layer, ALPHA_PT, sheet resistances, the BTO-on-Ti/Pt LC tank and the bare-shell discharge field. Both now return "no drive mechanism defined" (fail closed: zero energy, zero discharge-derived outputs). How the gas is driven is Open item 8.

### Keep (reviewer suggestion rejected)
- **The Kelvin reference** (293 K outer reference temperatures) stays, because Danny uses it to select thermal active materials placement in the tone. Grok's suggestion to replace it with required-conductance output is rejected. Locked above.

### Deferred (sounded good; later)
- Claude's three labelled temperatures (peak / cycle average / periodic steady state).
- A single solver entry point.
- Uncertainty bands.
- l ≥ 1 and anisotropic quartz modes.
- FEniCS / MEEP / OpenFOAM cases, held until folds 1–3 pass.

## Intended model behaviour (2026-10-19)
Design intent from Danny, recorded only. No drive mechanism or new physics is coded for it; the drive stays "no drive mechanism defined". Reviewers check model changes against this section.

### The knee, ignition and cascading cooling
Danny: *"The system is driven over the knee — that is what makes it go that way. If it gets too hot, it ignites. If it is cooling and cooling cascading, then it will never ignite. Modelling this ignition-vs-cooling behaviour is part of what we want to try."*

- The **knee is the thermal trigger**: the system is driven over the knee.
- **Ignition** (HHO autoignition, 773.15–858.15 K) is the failure mode when it gets too hot.
- **Cascading cooling** is the mechanism that prevents ignition.
- Reviewers flag any design or output that crosses autoignition without the cooling cascade. They must not propose electrode-based drives (electrodes are retired) to get there.

### Knee frequency is emergent, not a dial
Danny: the frequency and switching of the knee energy come from within the system itself. There is an input pump, but more layers must be built out before reaching it. The knee is **self-oscillating**; its frequency is an **emergent property of the layers**, not an externally set dial.

- Reviewers flag any change that treats knee frequency as an external input or dial as contrary to intent.
- The `drive_model.js` drive-frequency input `f` (and the former `V_amp`, removed with the electrodes) is **legacy scaffolding** relative to this intent. It stays for now (see deferred items below).
- A frequency sweep to find which frequencies talk to each other is a **future** item; the model is not there yet.

### Three thermal rates plus thermal mass, never lumped
The model must treat these independently, never folded into one time constant:

1. **Switching frequency:** how quickly or slowly the knee is switched.
2. **Heat-transfer speed:** how fast heat moves through a material before it soaks or saturates.
3. **Heat-removal rate:** how fast heat leaves the system, by whatever path (conduction, convection, radiation).

**Thermal mass** (how much heat a material holds before it pushes back) is also required. Reviewers flag any lumping of these into one time constant, for example the single `tauLumped`.

### Deferred / fold items from this intent
- **Model ignition vs cascading cooling** (drive over the knee vs cascading cooling). Ties to Claude's periodic-steady-state temperature item (round-5 deferred: peak / cycle average / periodic steady state).
- **Retire the external drive-frequency input** (`f` in `drive_model.js`, and `T = 1/f`, `ncyc`, `regime(p.f)`) once the layers exist for the knee to self-oscillate. Do not remove it before then.
- **Frequency sweep** (which frequencies talk to each other): future, after the layers are built.
- **Thermal rates: where the code is now, and what is missing** (as of 2026-10-19):

| Quantity | Where it is now | What is missing |
|---|---|---|
| (a) Switching frequency | Only the external `p.f` in `drive_model.js` (cycle `T = 1/f`, `ncyc` steps). `solver_v0.py` has no switching (the steady/transient P_circ scenarios were removed 2026-10-19; it now runs one no-source march). | Emergent self-oscillating knee switching. Today it is a dial, which is contrary to intent. |
| (b) Heat-transfer speed | `drive_model.js`: `tau_g = a²/(π²α_g)` (gas conduction), `tau_w = (b−a)²/(π²α_q)` (quartz wall diffusion), gas-wall conductance `Ggw = Cv_g/tau_g`, 24-cell quartz conduction with k(T). `solver_v0.py`: 1-D finite-volume conduction through every layer, with k(T) for quartz and interface resistances. | No per-layer "time to soak/saturate" output. `drive_model.js` models quartz only (no other layers). `Ggw` ties gas transfer to gas heat capacity. |
| (c) Heat-removal rate | `drive_model.js`: `Gout` = natural convection + radiation (`natconvH`, Churchill sphere + radiation) in series with outer-cell conduction, to ambient `Ta`. `solver_v0.py`: outer surface held at 293 K (the locked Kelvin reference, an ideal sink, not a removal rate). | No breakdown of removal by path (conduction / convection / radiation reported separately). No finite removal rate in the solver. |
| Thermal mass | `drive_model.js`: `Cq` (ρ c_p V per quartz cell), `Cv_g` (gas). `solver_v0.py`: ρ c_p per material for every layer. | Not reported per layer as "heat held before pushing back". |
| Lumping (flag) | `tauLumped = Ctot/hA0` in `drive_model.js` folds total thermal mass and removal into one time constant. It sets the run length (`tEnd`) and is listed as a "whole-bubble" thermal mode. | Replace with separate transfer / removal / mass quantities; keep `tauLumped` only as a labelled diagnostic, if at all. |

## Future item: next-layer wave behaviour (parked until multi-state)
Design intent from Danny (2026-10-19), recorded only. Nothing is coded for it. Parked until the model moves from single-state to multi-state. Kelvin stays canonical, electrodes stay removed from the model, and the drive stays "no drive mechanism defined".

1. **Guided channels, not a pure sphere.** The wave will not come out purely spherically. It travels through different guided channels depending on the regime it is in.
2. **Spin and rotation.** At some points the wave will spin and rotate.
3. **Rotating oscillation.** When the wave is oscillating, the oscillation is not just radial in-and-out; it is also rotating.
4. **Sequencing.**
   - Keep building out the single-state model first.
   - The time-domain run is the natural bridge: the solver marches in time, keeps history, and records the field at fixed radii, so the wave tail and the oscillation are visible.
   - Then promote to multi-state, with the guided channels, spin/rotation and rotating oscillation as the first multi-state features.

## Decision: ionisation and plasma sit inside the electric holster (2026-10-19)
Danny's decision (2026-10-19). Ionisation and plasma are not their own energy domains. They sit inside the existing holsters:

- **Electric holster: the field side.** Ionisation threshold, the Paschen curve and electron density. Paschen here means gas-breakdown physics as a field-side quantity of the gas (breakdown field vs pressure × length); it does not refer to electrodes, which remain removed from the model.
- **Chemical holster: the plasma chemistry.** Recombination, the HHO reactions and the autoignition cascade.
- **The plasma state straddles both holsters.** The crossover between them is a documented handoff between the electric and chemical holsters, not a gap.

## Future item: handoff rules between holsters (2026-10-19)
Recorded only; nothing is coded and no reviewer has been run. Many things will sit in more than one holster (the plasma state above is the first example), so the model needs rules for how handoffs between holsters work. This is to be put to the crew (Claude and Grok) with a push, but not yet.

## Decision: all six physical energy domains from the start (2026-10-19)
Danny's decision (2026-10-19). The model carries all six physical energy domains from the start: optical, acoustic, electric, magnetic, thermal and chemical.

- **Five propagating waves:** optical, acoustic, magnetic, thermal and chemical.
- **Electric is the driving field, not a wave.** The electric domain is the field that drives the whole system. It does not travel as a wave; it sets the thresholds (the ionisation knee and the Paschen curve, as gas-breakdown physics of the fill) and the drive conditions for the others.
- **Time-domain run (future item):** build it to carry all six domains, so each domain's wave or field is visible as the front expands.

Note: this concerns the six physical domains. The information domain (the 7th, per the 19-holster architecture) is unchanged; it is not a propagating physical wave.

## Future item: electrocaloric term in the BTO film and layer two (2026-10-19)
Danny's intent (2026-10-19), recorded only; nothing is coded. Add the electrocaloric term to the BTO film and to the tourmaline layer (layer two).

- **What it is:** electrocaloric is the reverse of pyroelectric: an electric field changes the material's entropy and temperature.
- **Materials:** barium titanate is a classic electrocaloric material, and the sol-gel recipe (MTES:TEOS 80:20 binder, doped grains) may carry it too.
- **Caveat:** randomly oriented grains largely cancel each other out, so the net effect depends on grain alignment in the recipe.
- **Field source:** the field is the electric holster's field. It is not applied by electrodes, which remain removed from the model.
- **Holsters: it straddles three.**
  - The electric holster owns the field side: the applied field drives the entropy change.
  - The thermal holster owns the temperature side: the cooling or heating that results.
  - The chemical holster owns the entropy change itself, since entropy is a thermodynamic state variable in the same family as the HHO reactions and recombination.
- **Another crossover, like plasma:** the electric field sets the condition, the thermal holster sees the temperature shift, and the chemical holster tracks the entropy. It is a good worked example for the future item on handoff rules between holsters (to be put to Claude and Grok later; not run yet).

## Note: layer-two recipe, field tuning during gel formation (2026-10-19)
Danny's intent (2026-10-19), recorded only; nothing is coded. While the tourmaline sol-gel (layer two) is still a gel during formation, it is tuned by bombarding it with two fields:

1. **Acoustic field:** sets the standing-wave node right to the layer's size, so the vibration mode matches the geometry.
2. **EMF field:** sets the grain orientation to the frequency wanted, so the piezoelectric and electrocaloric terms are net-positive rather than cancelling out from randomly oriented grains. This is a formation-process field applied to the gel during fabrication, with electrodes still removed from the model and the design. Its frequency is a fabrication tuning frequency, not a knee-frequency dial; the knee frequency stays emergent.

This tuning is what makes the piezoelectric coupling (which reads the acoustic solver's vibration mode) and the electrocaloric term real rather than upper limits. Until it is modelled, the solver keeps reporting the layer-two net polarization as a fully aligned upper bound (random grains ≈ 0).

## Decision: drive removed, electric field marched, zero-run acceptance rule (2026-10-19)
Danny's decision (2026-10-19). The circulating-power figures are gone from the solver completely: the P_circ scenarios, the wall-heat and light splits (F_WALL, F_OPT) and the list of power levels. They are not kept as a test source. Each preset now has one no-source run, and the viewer shows that single state with no power selector.

- **Electric field:** a real field, marched in time like the others. In each cell, ε dE/dt + σE = −dP/dt − J_src, with J_src = 0 from the no-drive stub and E = 0 at the 293 K seal state. Spherical symmetry gives B = 0 from these radial fields.
- **Couplings, all in the code:**
  - Pyroelectric polarization (layer two, and BTO at p 2.0e-4 C/m²K [lit], 0 above the Curie point [est]) feeds the electric march.
  - Piezo (acoustic stress) enters as the phasor of the same equation at the mode frequency.
  - Electrocaloric, (∂S/∂E)_T = p: the heat −T·p·dE goes to thermal, and the entropy p·dE goes to the chemical holster.
  - Polar grains are reported as the aligned upper bound (random grains ≈ 0) [est].
- **Thermal march:** solved in θ = T − 293 K, so a zero-heat state stays exactly at 293 K.
- **Acceptance rule (zero run):** with no drive and no input, every field is exactly zero everywhere: electric, magnetic, optical, acoustic, chemical and every coupling output. The whole stack sits at 293 K. The check uses exact equality; rounding noise is fixed at the source, not hidden by a tolerance. Each coupling is also checked on its own with synthetic inputs (stress for piezo, a temperature change for pyro, a field change for electrocaloric): zero in gives exactly zero out, and non-zero input scales as the physics says. The test is `tests/test_acceptance_zero_run.py`.

## Future item: electric and magnetic fields as one coupled wave (2026-10-19)
Danny's intent (2026-10-19), recorded only; nothing is coded. The electric and magnetic fields are coupled: they are two halves of one electromagnetic wave. The geometry's spin and rotation (the inhalation/exhalation cycle) is the coupling between them, and they spin and rotate with each other. To be reached eventually. Today the solver marches the electric field on its own, and B = 0 by spherical symmetry.

## Parked future item: outer boundary condition per domain (2026-10-19)
Danny's intent (2026-10-19), parked; nothing is coded. Some fields expand beyond the shell's outer layer, so each domain needs its own boundary condition at the outer surface: what radiates, what diffuses and what stops there.

- **First two:** electric and magnetic. The electric field extends outward and is always coupled with the magnetic field.
- **Thermal:** the existing 293 K outer reference stays as it is.

## Note: boundary pairs (2026-10-19)
Danny's framing (2026-10-19), recorded only; nothing is coded.

- **Two boundaries per layer:** every layer has an inner boundary (the layer before it) and an outer boundary (the layer after it). The stack is therefore a chain of interfaces rather than a pile of materials.
- **The final boundary:** whatever we decide on, it is where the model is driven and where power is extracted. It is an open question: no suggestions or candidate ideas are recorded. The right topology will be worked out when we get to it, because we will know what we need at that point.
- **Build direction:** the model is being built from the top down, or in-out.

## Future item: EMF build: E-B coupling (next build after drive removal) (2026-10-19)
Danny's intent (2026-10-19), recorded only; nothing is coded. The electric and magnetic fields are two halves of one electromagnetic wave. The geometry's spin and rotation (the inhalation/exhalation cycle) is the coupling between them, and they spin and rotate with each other.

1. **The missing half:** the magnetic field B is the half that the electric field currently lacks.
2. **The coupling mechanism:** the spin-rotation cycle is what couples E and B.
3. **The tourbillon layer:** this is what will let the tourbillon layer be fully modelled for amplitudes and behaviour. Without the magnetic side, its behaviour is only half-specified. Its composition is defined in "Composition and tuning (tourbillon layer)" below.
4. **A seeded E field first:** a seeded E field, through the piezo coupling, could excite the tourbillon mechanically and show ring behaviour before the magnetic side exists. The EMF would then sustain and shape what the tourbillon started. A seeded E field is a test seed, not a drive.

### Recipe parameters (tourbillon layer)
- **Continuum model:** the model never tracks individual particle positions; it marches fields through shells with bulk properties. The tourbillon's particle-level detail therefore folds into effective constants rather than positions.
- **A recipe, not a geometry:** the tourbillon layer is specified by:
  - powder size (finer powder means more grain boundaries, more scattering and a lower Q);
  - density;
  - the chemistry ratio (which shifts the piezo and pyro coefficients).
- **First-class inputs:** these fold into the layer's effective coupling strengths, damping and Q. This is the same way the gel-tuning note treats the sol-gel recipe.
- **Caveat:** the model cannot resolve structure inside the layer. If the tourbillon's behaviour depends on particle arrangement rather than composition, that would need a separate discrete model.

### Composition and tuning (tourbillon layer)
Danny's specification (2026-10-19), recorded only; nothing is coded. The solver still has quartz, layer2, BTO and Gd-Dy as separate shells.

- **One mixed layer, not four separate shells:** tourmaline, BTO (barium titanate, not barium nitrate) and Gd-Dy grains are suspended in the MTES:TEOS 80:20 silicate binder (the same sol-gel family as the gel-tuning note), then dipped and cured into a single shell.
- **The binder** is the carrier, not a substrate.
- **A dial per component:** each component gets its own powder size, density and chemistry ratio. These fold into the layer's effective coupling strengths, damping and Q, as in "Recipe parameters (tourbillon layer)" above.
- **Tuning:** the layer is tuned to two modes at once, an acoustic mode and a radio-wave mode, so all three components operate in both fields at the same time. These tuning modes are fabrication and design targets, not a knee-frequency dial; the knee frequency stays emergent. Electrodes stay removed.

### Tourmaline end-member sweep (tourbillon layer, tourmaline component) (2026-10-19)
Danny's request (2026-10-19). Tourmaline is a solid solution, so each end-member is its own composition entry. The backbone is X Y3 Z6 (T6O18)(BO3)3 V3 W.

- **Substitutions:**
  - Y site: Mg in dravite, Fe2+ in schorl, Li + Al in elbaite (2Fe2+ ⇄ Li+ + Al3+);
  - W site: OH, F or O.

| End-member | Ideal formula | d33 (∥c) | p3 at 296 K / 383 K (µC/m²K) | Dipole moment (unit cell, along c) | Mass susceptibility (SI) |
|---|---|---|---|---|---|
| Elbaite (Li-rich) | Na(Li1.5Al1.5)Al6(Si6O18)(BO3)3(OH)3(OH) | 2.2 pC/N [lit, Xue et al. 2024] | 3.95 / 4.79 [lit, Hawkins 1995 Table 5, Fe-free prediction] | 0.652e-29 C·m [lit calc, Xue et al. 2024 Table 8] | 7.3e-9 m³/kg [lit, Sigamony 1944, rose specimen; elbaite proxy, UNSURE] |
| Dravite (Mg-rich) | NaMg3Al6(Si6O18)(BO3)3(OH)3(OH) | 1.8 pC/N [lit, Xue et al. 2024] | 3.52 / 4.26 [calc from the Hawkins 1995 Table 4 fit for sample S19, uvite-dravite; end-member value UNSURE] | 0.476e-29 C·m [lit calc, Xue et al. 2024 Table 8] | not available |
| Schorl (Fe-rich) | NaFe3Al6(Si6O18)(BO3)3(OH)3(OH) | 2.0 pC/N [est, UNSURE: no number found] | 2.03 / 2.68 [lit, Hawkins 1995 Table 5, ideal schorl, FeO 20.46 wt%] | not available | 1.68e-7 m³/kg [lit, Sigamony 1944, black specimen; schorl proxy, UNSURE] |

Spontaneous polarization: not available for any of the three. Grain ε_r is 7 [est] for all three; no per-species value is adopted.

Sources:
- Hawkins, Mackinnon & Schneeberger, Am. Mineral. 80, 491 (1995).
- Xue et al., Acta Mineralogica Sinica 44 (2024), doi 10.3724/j.1000-4734.2024.44.020: d33 from Table 2, dipole moment by point-charge calculation from Table 8.
- Sigamony, Proc. Indian Acad. Sci. A 20, 200 (1944): specimens identified by colour, not by species; cgs values converted to SI.
- Ideal formulae: Henry et al., Am. Mineral. 96, 895 (2011).
- Schorl d33 ranking is qualitative only (elbaite > schorl > dravite, Adv. Mater. Res. 1015, 259 (2014)), and another report has dravite above elbaite.

- **Magnetic flag:** schorl is iron-bearing and paramagnetic (Fe2+ on the Y site). It adds a magnetic coupling that elbaite lacks. That is a feature if the layer is meant to couple to the magnetic field, and a confound if the electric response (piezo, pyro, electrocaloric) is being isolated. It is not coupled in the solver yet (B = 0).
- **Sweep:** `python3 solver_v0.py --tourmaline {elbaite,dravite,schorl,all} [--only base5]`. It runs the same recipe (φ 0.20, binder, ε_r, aligned upper bound) once per end-member and writes `tourmaline_sweep_v0.json`. Default runs are unchanged. With no source, every end-member is exactly zero everywhere (the zero-run acceptance rule). The file's synthetic block applies the same stress, temperature step and field change to each end-member.
- **Discrepancy found, nothing changed:** the default layer-two pyro values (2.03e-6 at 296 K, 2.68e-6 at 383 K C/m²K) are tagged in `solver_v0.py` as the "elbaite end member". In Hawkins 1995 Table 5 they are the ideal **schorl** values (FeO 20.46 wt%). The Fe-free prediction there is 3.95 / 4.79. In the same source, the "1.8-2.2 pC/N" d33 range is Mg-tourmaline 1.8 and Li-tourmaline 2.2, not a range for Li-tourmaline. The default is left as it is, pending Danny's decision.

## Decision: phosphor stays out of the model (2026-10-19)
Danny's decision (2026-10-19), with his reasoning. This follows the inner-phosphor removal in commit 3965699.

- **The phosphor's knee is linear:** its saturation knee is a soft roll-off. It can only flatten or compress the amplitude. It cannot generate new frequencies or shift them.
- **Frequency shifting needs a strong non-linearity:** a χ² term, which the phosphor cannot provide.
- **Light path:** stays quartz → tourmaline → BTO → Gd-Dy.
- **The non-linear, frequency-shifting knee** is the Layer 5 option (PPLN or KDP). It gives real gain only with a coherent pump at the megawatt level.

## Note: tourmaline sweep results are baseline-only (2026-10-19)
Danny's note (2026-10-19) on the tourmaline end-member sweep from commit 66af444 (`tourmaline_sweep_v0.json`).

- **What the runs show:** all 27 runs (three end-members, elbaite, dravite and schorl, across nine presets) are exactly zero in every field and exactly 293 K.
- **Why:** no drive source has been connected and the final layer has not yet been built.
- **How to read it:** the zeros are the honest baseline, not a result. They confirm zero-run acceptance for each end-member; they say nothing yet about how the end-members compare in operation.

## Future item: planned kilowatt drive experiment (2026-10-19)
Danny's planned experiment (2026-10-19). Not built; recorded so it follows on from the baseline note above.

- **What:** drive a kilowatt of energy into the EMF field at a frequency that switches the ionisation knee. The correct term is the ionisation knee, not the plasma knee.
- **The drive frequency is not assumed:** it is derived from the geometry of the final layer, which has not been built yet.
- **The chain:** geometry sets the resonant frequency; the resonant frequency sets the ionisation knee's switching point; the kilowatt drive probes how the system reacts.
- **Status:** exploratory. An assumption is acceptable here because the goal is to see how the system reacts, not to claim precision.

## Future item: drive triad, EMF, acoustic and thermal (2026-10-19)
Danny's design (2026-10-19), following the planned kilowatt drive experiment above. Not built.

- **Dual drive:** the system is driven by both an EMF mode and an acoustic mode.
- **Ordering:** the acoustic mode sits below the electric mode in frequency, but drives it.
- **Thermal drive channel:** a thermal drive is included as well.
- **Full design:** a triad of EMF, acoustic and thermal drives.

## Design decision: the piezo knee is the mixer (2026-10-19)
Danny's decision (2026-10-19), following the drive triad above. Not built.

- **No separate non-linearity:** the non-linearity needed for the acoustic-to-electric frequency step is not added separately. It comes from the piezo element's own knee.
- **The piezo knee:** a piezo element is linear in its small-signal regime. Past a certain field strength its response stops being proportional and the non-linear terms kick in. That knee is where frequency mixing happens.
- **Driving the knee deliberately:** the lower-frequency energy (the acoustic mode, and below it the thermal mode) pumps the piezo back and forth across its knee. The non-linearity does the frequency conversion, pushing energy up to the electric mode's frequency.
- **Roles:** the knee is the mixer; the lower-frequency drive is the pump.
- **Principle:** the same as a parametric amplifier, where the pump sits below the signal and pushes energy upward.

## Design decision: bidirectional knee mechanism in every layer (2026-10-19)
Danny's decision (2026-10-19), following the piezo knee note above. Not built.

- **The mechanism:** energy downshifts one way, reflects off a boundary, and shifts back up in phase on the return to feed the next cycle.
- **Scope:** it applies to every layer of the system, not just the piezo, including the hydrogen bubble.
- **Per layer:** each layer gets its own knee, its own pump and its own boundary reflection.
- **The boundary reflection is a candidate idler, not a confirmed one.** An idler is a real mode of the system, with its own frequency and resonance, that carries energy. A boundary reflection may simply bounce the same wave back.
- **Open question for the geometry:** whether the reflected energy lands on a real mode (making the round trip parametric) or is just a reflection (so the up-conversion must come from elsewhere). The geometry can answer this once the final layer is built.

## Design decision: geometry from frequency, golden-ratio tracking, storage and shifting ladders (2026-10-19)
Danny's decisions (2026-10-19), recorded as one piece, following the bidirectional knee note above. Not built.

1. **Geometry derivation is reversed.** Derive the geometry from the frequency we already have, using the three cavities we have: the two layers and the hydrogen bubble. Each cavity's resonant frequency is set by its geometry, so the dimensions that place each cavity in the cascade can be solved for.
2. **Geometry becomes a sweep variable.** Sweep the dimensions and score each geometry on how many round trips come back in phase: boundary reflections landing on real modes, knees crossed at the right thresholds, and the cascade holding together. The geometry that maximises in-phase returns is the one that survives the checks already recorded.
3. **The geometry sweep is correlated to the golden ratio.** Sweep the tone down from the high frequency we are at, and the geometry of everything follows that tone. It does not have to follow the whole 1.618; it can sit anywhere on that spectrum, but it must move in time with the tone, tracking along the wave where it needs to be. The golden ratio is the scale of the tracking, not a rigid rule.
4. **Layers split into two jobs.**
   - **Storage layers** store energy, freewheeling and flywheeling, holding energy in circulation.
   - **Shifting layers** do frequency conversion at the knees.
   - There will be many ladders. The geometry sweep must keep every ladder's round trips in phase together, not just one at a time.
   - The golden-ratio tracking keeps storage and shifting layers moving as one system: storage layers hold the energy while shifting layers move it up the ladder, and the sweep finds the shape where both jobs stay in phase across all ladders at once.

**Amendment (2026-10-19), Danny's corrections to point 1 above:**
- **Frequencies come from the geometry already in the model.** The model holds the geometry, so every frequency is derived from it, not supplied from outside. Where point 1 says "derive the geometry from the frequency we already have", read it as: the frequencies we have are the ones the model's geometry gives.
- **The three cavities are the hydrogen bubble, the quartz layer and the tourmaline alloy layer.** This replaces "the two layers and the hydrogen bubble" in point 1.
- **Same layer, two names:** the tourmaline alloy layer is the tourbillon, the single mixed shell of tourmaline, BTO and Gd-Dy grains in the MTES:TEOS 80:20 binder (see "Composition and tuning" under the EMF build future item). The record treats them as one layer.

## Flag: the 2 MHz selection target is an unverified artifact (2026-10-19)
Danny's flag (2026-10-19). Recorded only; nothing in the code changes.

- **Where:** `solver_v0.py` L737, `f_target = 2.0e6`. L738 (and L742 for the bonded stack) picks the l=0 shell mode nearest 2 MHz in log distance.
- **No stated reason:** there is no comment or docstring explaining why 2 MHz was chosen. It has been unchanged since the first snapshot commit `c4906c4`.
- **Feasibility plan:** `docs/Multidomain_Sphere_Model_Feasibility_Plan_2026-10-19.md` calls it "Danny's '2 MHz shell mode'" but gives no reason. The plan itself notes there is no l=0 mode at 2 MHz at 5 mm OD: the l=0 modes there are 0.69 and 3.10 MHz, and 2 MHz matches the n=4 spheroidal mode instead.
- **Minimal Test Config:** `docs/Minimal_Test_Config_1mm_2026-10-19.md` treats 2 MHz as a drive frequency in its plasma-frequency check, and notes that 1.87 MHz is the closest actual mode.
- **Tests:** `tests/test_piezo_pyro_couplings.py` L139 repeats the same nearest-to-2 MHz selection.
- **What it is:** not a design target and not a source. It only picks the mode nearest 2 MHz.
- **Status:** a question for the team, not a target, pending a decision on whether to keep, replace or remove it.

## Note: 2 MHz target removed from the solver and tests (2026-10-19)
Danny's decision (2026-10-19), following the flag above.

- **Removed:** the 2 MHz selection target (`f_target = 2.0e6` and the nearest-to-2 MHz selection) has been removed from `solver_v0.py` and from `tests/test_piezo_pyro_couplings.py`.
- **New rule:** the solver now selects the lowest computed l=0 shell mode (the fundamental), for the isolated shell and likewise for the bonded stack, from the geometry alone. It still reports all computed modes (`l0_isolated`, `l0_bonded`, gas-cavity modes). If no shell mode is computed, no frequency is invented.
- **Leftovers:** if the team finds any remaining detection of 2 MHz in outputs, labels or docs, it is a leftover artifact of the removed target, not a design value. Treat it as noise to clean up, not a target to optimize toward.

## Design framing: modes lock where they lock; the sweep searches for maximum locking (2026-10-19)
Danny's framing (2026-10-19), following the 2 MHz removal note above. Not built.

- **The solver does not select a mode.** The modes are what the geometry produces, and the solver lists them all. The modes lock where they lock.
- **The geometry sweep's job:** optimise for maximum locking, that is, find the geometry where the most modes lock at once.
- **Golden-ratio tracking:** the path walked through the geometry space.
- **In-phase round-trip score:** boundary reflections landing on real modes, knees crossed at the right thresholds, and the cascade holding together. This is what tells you when a good spot has been found.
- **The sweep is a search, not a prediction.**

## Note: solver now carries every mode (2026-10-19)
The code now matches the framing above.

- **Selection removed:** the single-mode selection (the lowest l=0 shell mode, from `4710eed`) is gone from `solver_v0.py`. The solver no longer picks a mode, for the isolated shell or the bonded stack.
- **Every mode carried:** every computed l=0 shell mode, isolated and bonded, goes through the mode-energy calculation (its own mode shape, energy marched from 0, Q_eff, tau_ac, peak stress, loss and energy shares) and through the piezo coupling (each layer at each mode's own frequency). Per-mode results are in `acoustic.modes`, `acoustic.bonded.modes` and `electric.piezo.<layer>.modes`.
- **Aggregates, not a selection:** where one number is needed, it is taken over all modes. Mode energy, loss and piezo layer energy are summed over all modes. The acoustic stress field, the piezo AC field and the core gas pressure are summed over all modes (in-phase superposition, an upper bound), and the quartz stress flag uses that sum. Peak stress, the piezo peaks (sigma, P, E, u_e) and tau_ac are the maximum over all modes. Q_eff and energy shares stay per mode, because combining them would need a weighting the model does not have.
- **No source:** every mode's energy is still marched from 0 with no drive, so every field and mode energy is exactly zero and the stack stays at exactly 293 K. If no mode is computed, the lists are empty and no frequency is invented.

## Note: geometry sweep v0, search for maximum mode locking (2026-10-19)
Danny's request (2026-10-19), following the geometry note and the mode-locking framing above. Opt-in script `geometry_sweep_v0.py`, output `geometry_sweep_v0.json`. No source: every mode energy is 0, the stack stays at 293 K, and the default outputs are unchanged. It is a search, not a prediction.

- **Swept:** gas bubble radius 0.573–3.087 mm (base5 1.5), quartz wall 0.300–2.058 mm (base5 1.0) and tourbillon (layer two) thickness 1.91–10.29 µm (base5 5). The coarse grid is 8 × 9 × 8 = 576 points in φ^(1/2) steps around base5. A refine of φ^(1/8) steps, ±2 per axis, around the top 5 coarse points adds 175, kept inside the same box, for 751 in all. Every other layer is built by `build_stack` as for base5 (new optional `t_l2`, default 5 µm), with 1 atm HHO at 293 K and the VRH quartz speeds.
- **Modes per cavity (acoustic, l=0, 20 kHz–12 MHz, the solver's window):** bubble gas cavity with a rigid wall (B; the model has no gas Q, so its linewidth is 0 [est]); the quartz layer as a free shell (Q; Q_eff 2100 from `mode_energy_stats`); the tourbillon as a free shell (T; Q_eff 150, plus its first thickness mode); and the bonded stack's shell modes (S; `l0_modes` split as in `run_case`, Q_eff per mode from `all_modes_stats`). Only l=0 modes are compared, because l≠0 modes are orthogonal to the l=0 shell modes.
- **Lock (scoring definition):** two modes of different cavities lock when |f_i − f_j| ≤ (f_i/Q_i + f_j/Q_j)/2, meaning their own model linewidths overlap at half maximum. No tolerance is invented. The pairs scored are B–Q, B–T, Q–T and B–S; Q–S and T–S are left out because S contains Q and T. A boundary-reflection round trip (B: n·c/4a; Q: n·cL/2w; T: n·cL₂/2t₂) locks when it lands inside the half-width of a real mode of another cavity, counted once per target mode. **Score** = number of locks. Also reported: the distinct modes taking part, and **sharp** locks, which are locks not guaranteed by mode density alone (the lock window is narrower than the local mode spacing).
- **Cascade gate:** thermal < acoustic < electric in every cavity. 7 of 751 geometries fail it; all of those have the tourbillon at about 2 µm, where its thermal frequency rises above its breathing mode. Ranking applies the gate first, then the score.
- **Knees crossed at the right thresholds: unscored.** A knee crossing needs a field amplitude, and with no source every amplitude is exactly 0. This stays unscored until a source exists.
- **Golden ratio:** a secondary, non-scoring column. It gives the adjacent ratios of the sharp-lock frequencies against 1.618 (the tracking scale, not a rule).
- **Top geometries (score):** #1 bubble 3.087 mm, wall 1.938 mm, tourbillon 8.59 µm (OD 10.05 mm), score 215 (154 mode + 61 reflection locks, 22 sharp, 174 distinct modes). #2 bubble 3.087 mm, wall 2.058 mm, tourbillon 9.69 µm, score 215 (24 sharp). The whole top 10 sits at the 3.087 mm bubble with a wall of 1.94–2.06 mm, scoring 210–215. **base5 ranks 391 of 751**, with score 68 (40 mode + 28 reflection locks, 14 sharp).
- **Trend:** the score follows the number of modes in the window (correlation 0.98). That means it rises with bubble radius (0.95) and wall thickness (0.64), and hardly depends on tourbillon thickness (0.04). Almost every lock is a gas-cavity mode or round trip landing on a broad bonded-stack mode (Q_eff ~ 20–300). The quartz layer takes part only through 60 B–Q and 188 reflection–Q locks across the whole sweep, and the tourbillon only through 24 reflection–T locks. No Q–T lock occurs anywhere. Under the current scoring, the best spot is the edge of the box: the score is driven by mode density, not by a sharp alignment.

## Future item: transient solver (pulse in, layer-by-layer response out) (2026-10-19)
Danny's intent (2026-10-19), recorded only; nothing is coded. Today's solver is steady-state: the thermal march converges to a wall temperature, `GAS = {p, T}` is set once (and reset to 293 K after the hot-gas pass), and modes are computed from that frozen picture. The transient mode follows the coupled physics instead. Once a geometry locks and a threshold triggers, even a single pulse puts energy into every domain at once, and each layer's transient response is what the model measures and feeds back on. Every parameter references and modulates the others.

1. **Purpose:** a time-domain run. The pulse is the input; the layer-by-layer transient response is the output.
2. **State variables evolved each step:**
   - live gas pressure and temperature, plus the density and sound speed derived from them;
   - mode frequencies and amplitudes per cavity (bubble, quartz, tourmaline alloy layer, bonded stack);
   - lock state;
   - the thermal field across every layer;
   - piezo and BTO state (polarisation, strain, permittivity ε(T), Curie side).
3. **Coupling terms:**
   - gas heating from the pulse and from chemistry (2H₂+O₂ heat release);
   - thermal conduction between layers;
   - acoustic coupling between cavities through the wall;
   - piezo response to strain;
   - optical absorption feeding back into heating.
   - **Gas Q at the live state:** the derived gas Q, `gas_Q(f, a, p, T, comp)`, is evaluated at the live gas state each step, never at the 293 K default. The same goes for each mode's linewidth in the lock check.
4. **Pulse input:** a single electromagnetic pulse, entering as a source term through the piezo/BTO layer. There are no electrodes. This defines the source only for the transient run; the no-source run and the zero-run acceptance rule stay as they are (no pulse gives exactly 0 and 293 K).
5. **Per-step log:**
   - per-layer temperature;
   - gas pressure;
   - mode frequencies per cavity;
   - lock state;
   - energy per energy domain.
6. **Open questions:**
   - **Time step and stability:** the domains run from nanoseconds (electric) through microseconds (acoustic) to seconds (thermal), so the scheme needs splitting or adaptive steps.
   - **Initial conditions:** whether to start from the steady-state solution.
   - **The trigger:** how the threshold is detected, and what counts as a lock.
   - **Known defect:** the averaged gas temperature in the current steady run reads 293.023 K with no heating. This is a quadrature artifact and must be fixed at its source before transient runs build on it.

## Geometry sweep re-run with derived gas Q (2026-10-19)
Method change: the sweep's gas-cavity (B) modes no longer have width 0. Each takes Q = `solver_v0.gas_Q(f, a, p, T, 'HHO')` at the fill state (1 atm HHO, 293 K; no source, so the gas stays at 293 K): wall thermal boundary layer plus classical bulk absorption, viscous wall loss 0 for l = 0. This is a modelling assumption (isothermal wall, no relaxation or discharge loss, so an upper bound on Q), not measured physics. The lock rule is unchanged, |f_i − f_j| ≤ (f_i/Q_i + f_j/Q_j)/2, but the gas mode now contributes its own width. Same grid (coarse 576 on the φ^(1/2) lattice + refine around the top 5); the refine seeds moved, so 769 geometries this time (751 before). New field `sharp_per_mode` = sharp locks / modes in the window, with a third ranking `rank_spm` (cascade gate first, then sharp_per_mode, tie sharp locks) and `top10_spm`.

- **Gas Q:** first B mode 298.5 for base5 (254 kHz); first-mode range 170 (a 0.573 mm) to 447 (a 3.087 mm); high modes near 12 MHz fall to about 43–45.
- **Top by score:** a 3.087 mm, w 2.058 mm, t2 9.12 µm, score 309 (236 mode + 73 reflection), 30 sharp, 217 modes, sharp per mode 0.138 (rank_spm 353). Top 10 by score are all a 3.087 mm, w 2.058 mm; the edge-of-range bias stays.
- **Top by sharp per mode:** a 0.573 mm, w 1.272 mm, t2 2.43 µm, 20 sharp / 59 modes = 0.339. The top 5 are all a 0.573 mm; the top 20 include 0.573 and 0.729 mm, now joined by 0.927 and 1.179 mm.
- **base5:** score 81 (52 + 29), rank 447/769; 15 sharp / 108 modes = 0.139, rank_spm 346.
- **Against 29dca55 (gas width 0):** the old score #1 (3.087 / 1.938 / 8.59 µm, 215) now scores 295 (rank 28). Total locks across the sweep rose from 71,576 to 104,821 (+46 %) and sharp locks from 10,343 to 13,961. Every lock involves the bubble both before and after (no Q–T lock in either run). The small-bubble winners survive the derived gas width at the top of the sharp-per-mode ranking (0.321 → 0.339).

## Geometry x fill-state sweep (2026-10-19)
Opt-in `geometry_fill_sweep_v0.py` → `geometry_fill_sweep_v0.json`. It asks where the lock optimum sits across geometry and fill together instead of assuming 1 atm HHO. The lock rule, sharp definition, cascade gate and scoring are unchanged; there's no source, so T stays 293 K. The solver isn't changed, and `geometry_sweep_v0.json` isn't regenerated.

- **Fill axis (20 states):** p ∈ {0.382, 0.618, 1, 1.618, 2.618} atm (φ⁻² … φ²) × x_H2 ∈ {0.50, 2/3 (HHO), 0.75, 0.80}, with O₂ making up the rest.
- **Mix consistency:** the gas enters everywhere through `geometry_sweep_v0.evaluate(p_atm=, comp=)`.
  - B modes and bubble round trips use c from `gas_props(293 K, p, comp)`.
  - The bonded stack is gas-loaded with that c and K = γp, via a temporary sweep-side override of `gas_Z` that is restored afterwards.
  - Gas Q per B mode is `gas_Q(f, a, p, 293 K, comp)`.
  - The B cascade thermal rate uses the mix's k/(ρcₚ).
  - The default `evaluate()` path is unchanged.
- **Geometry subsample:** 48 points per fill state on the same φ^(1/8) lattice and box: a {0.573, 0.729, 1.5, 3.087} mm × w {0.382, 1.0, 1.272, 2.058} mm × t2 {2.43, 5.0, 10.29} µm.
- **Counts:** coarse 960, plus 51 refine points (geometry ±φ^(1/4) per axis at each of the top 5 seeds' fill states, plus each seed geometry at its four fill-grid neighbours; the seeds overlap), so **1,011 in total**, 124.6 s on 8 workers. No geometry failed the cascade check.
- **Top by sharp per mode:** a 0.573 mm, w 1.825 mm, t2 2.15 µm at 1.618 atm, x_H2 0.80: 26 sharp / 66 modes = 0.394. The top 10 are all x_H2 0.80, with a 0.573 or 0.646 mm.
- **Top by score:** a 3.087 mm, w 2.058 mm, t2 2.43 µm at 0.382 atm, x_H2 0.50: score 536 (439 mode + 97 reflection), 50 sharp / 244 modes = 0.205. Low pressure and an O₂-rich mix raise raw score; the large-bubble edge still wins on score in every fill state.
- **Small bubbles:** in every one of the 20 fill states, the best sharp-per-mode geometry has a 0.573 or 0.729 mm bubble. Mix matters more than pressure: the coarse mean of sharp per mode is highest at x_H2 0.80 (0.198–0.214) and lowest at HHO (0.160–0.172).
- **1 atm HHO:** best 0.573 / 1.0 / 5.0 at 0.315 (rank_spm 69 of 1,011); base5 scores 80, with 12 sharp / 108 = 0.111.
- **Sensitivity caveat:** HHO through `gas_props` has c 533.20 m/s against c_hho's 532.86 m/s (0.06 %). That alone changes the sharp counts in 41 of 48 1 atm HHO cells relative to 3b81839, for example base5 going from 15 sharp to 12. So differences of about 0.03 in sharp per mode between single cells are within that sensitivity; the mix trend in the means is the firmer result.
- **Gas Q:** the first B mode's Q ranges from 91 to 800 across the sweep.

## Geometry × rarefied-pressure sweep, HHO 2:1 fixed, ambient-referenced (2026-10-19)
Supersedes the geometry × fill-state sweep above (0fa5d40). That run is **disregarded**: off-spec mixes are a chemistry artifact (its x_H2 0.80 optimum at 0.394), and its pressure grid was a φ lattice (0.382 … 2.618 atm, including 1.618; the 1.618 atm finding is disqualified). `geometry_fill_sweep_v0.json` is left in the tree only as that disregarded record. The script can no longer produce it: **off-spec mixes (1:1, 3:1, 4:1) are removed from `geometry_fill_sweep_v0.py`**, and the mix is fixed at HHO 2:1 (x_H2 = 2/3). New output: `geometry_rarefied_hho_sweep_v0.json`.

- **Rationale (Danny, recorded hypothesis, not a model result):** rarefaction may bias the gas toward the ionic knee so that energy focuses across modes. Pressure is the dial, but pressure heats while vacuum cools, so the rarefied regime is also the self-cooling regime. This no-source sweep scores locks only; nothing here models ionisation or cooling.
- **Ambient-referenced grid:** p = factor × p_ambient and T_gas = T_ambient. Both are operator-set inputs for the run day (`--p-ambient` / `--T-ambient`; defaults `AMBIENT_P_Pa` = 101325 Pa and `AMBIENT_T_K` = 293 K; no sensor is read), and both are recorded in the JSON meta. Gas Q, linewidth, sound speed and gas loading are evaluated at (p, T_ambient).
- **Fully rarefied, log-even factors (9):** exp(linspace(ln 0.05, ln 0.95, 9)) = **0.0500, 0.0722, 0.1044, 0.1508, 0.2179, 0.3149, 0.4550, 0.6575, 0.9500** (step ×1.4449). Every factor is < 1, and none is within 1 % of 1.618 or 0.618; both conditions are asserted in the script. A 7-point log grid over 0.382 … 2.618 was set up in between and discarded before any run, because it crosses above ambient.
- **Grid:** 48 geometries per pressure (same 4 × 4 × 3 subsample) = 432 coarse, plus 67 refine (geometry ±φ^(1/4) at the seed pressure and the seed geometry at neighbouring pressures, mix fixed) = **499**, 72.2 s on 8 workers. No geometry failed the cascade check.
- **Top by sharp per mode:** a 0.573 mm, w 1.435 mm, t2 9.12 µm at 0.1044 × ambient (10,577 Pa): 26 sharp / 63 modes = **0.413** (79 mode + 29 reflection locks). Next, 0.408 at 0.1508 × (0.573 / 1.825 / 2.43). Both are refine points; on the coarse grid alone the best is 0.389 at 0.0722 × (0.573 / 1.0 / 5.0).
- **Small bubbles:** the best geometry at every one of the 9 pressures has a 0.573 mm bubble, except 0.3149 ×, where it's 0.729 mm. The best per-pressure value rises from about 0.31 near ambient to about 0.39–0.41 at 0.07–0.15 ×, then falls back to 0.31 at 0.05 ×.
- **Top by score:** a 3.087 mm, w 2.058 mm, t2 10.29 µm at 0.05 × (5,066 Pa), score 1,746 (1,589 mode + 157 reflection), but only 39 sharp / 218 modes = 0.179. At low pressure the gas Q falls (first gas mode Q from 22 to 435 across the sweep), so gas linewidths widen and the raw score fills up with locks that are guaranteed by mode density, not geometry. Sharp per mode is the meaningful ranking here.
- **base5 (1.5 / 1.0 / 5.0):** at 0.95 ×, score 82, 13 sharp / 108 = 0.120. Its best is at 0.0722 ×: 29 sharp / 108 = 0.269.
- **Caveats:** sharp counts move by a few under a 0.06 % sound-speed change (see the note above), so single-cell differences of about 0.03 are within that sensitivity. Refine points also cluster around the seeds' pressures (0.0722, 0.1044, 0.1508 ×), so those cells had extra evaluations. The continuum form of `gas_Q` still holds at 0.05 × (mean free path ~1.5 µm against a thermal layer of ~24 µm at 1 MHz) [est].

## Core geometry replaced by rarefied-sweep winner (2026-10-19)
The previous core design (`base5`) was bubble a = 1.5 mm, quartz wall = 1.0 mm, tourbillon t2 = 5.0 µm, fill 1 atm HHO 2:1 at 293 K (quartz OD 5.00 mm). It is **replaced** by the rarefied HHO-only sweep winner from commit `ea694ce` (`geometry_rarefied_hho_sweep_v0.json` `top10_spm[0]`, stage refine):

- bubble a = **0.57295 mm**
- wall w = **1.43463 mm**
- tourbillon t2 = **9.12441 µm**
- fill p = **0.1044 × ambient** = 10,577.3 Pa ≈ **0.10439 atm** HHO 2:1 (sharp per mode **0.4127**)
- quartz OD ≈ **4.015 mm**

Named constants in `solver_v0.py`: `CORE_A_MM`, `CORE_W_MM`, `CORE_T2_UM`, `CORE_P_ATM` / `CORE_P_Pa` / `CORE_P_FACTOR`. `PRESETS` `base5`, `build_stack` default `t_l2`, and `geometry_sweep_v0.BASE` / `P_ATM` all point at this core. The rarefied fill-sweep lattice stays frozen on the **former** centre (1.5 / 1.0 / 5.0) via `LATTICE_BASE` so `idx [0,0,0]` and the ea694ce absolute box are unchanged. Historical `geometry_sweep_v0.json` results (1 atm lattice around the old centre) are left as-is; only the `base5` summary record is re-evaluated at the new core.
