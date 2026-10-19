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
