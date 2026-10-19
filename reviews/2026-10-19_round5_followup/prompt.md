# System

You are an independent reviewer of the Stratified Sphere project. You do not edit anything. Judge only the diff and DESIGN_STATE.md given; if you cannot verify something, say so; do not invent values or sources. Electrodes are retired and removed from the model: do not propose an electrode-based drive. Answer in plain prose with numbered points, at most ~1200 words.

# User

Danny has recorded his decisions on your round-5 review in the attached diff. How should he complete the feedback loop in the holster: what is still missing to fully close it, what should happen next and in what order, and do you disagree with any decision or how it was recorded?

The diff is `git diff main...holster-loop-2026-10-19` (generated index.html and model_data_v0.json omitted for size). Danny's decision section is "Danny's decisions on round-5 review (2026-10-19)" in DESIGN_STATE.md; the later design-intent and holster-architecture additions are in "Intended model behaviour (2026-10-19)" and "Information layer".

=== FULL UPDATED DESIGN_STATE.md ===
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

### Layer 4: downshifting phosphor
- **Options:** KSF, which saturates at about 8–16 W, or CASN, which saturates at about 80 W.

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
5. Which phosphor. (The electrode-placement / Ti/Pt light-blocking question is closed: electrodes are retired, 2026-10-19.)
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
| (a) Switching frequency | Only the external `p.f` in `drive_model.js` (cycle `T = 1/f`, `ncyc` steps). `solver_v0.py` has no switching (steady/transient P_circ scenarios). | Emergent self-oscillating knee switching. Today it is a dial, which is contrary to intent. |
| (b) Heat-transfer speed | `drive_model.js`: `tau_g = a²/(π²α_g)` (gas conduction), `tau_w = (b−a)²/(π²α_q)` (quartz wall diffusion), gas-wall conductance `Ggw = Cv_g/tau_g`, 24-cell quartz conduction with k(T). `solver_v0.py`: 1-D finite-volume conduction through every layer, with k(T) for quartz and interface resistances. | No per-layer "time to soak/saturate" output. `drive_model.js` models quartz only (no other layers). `Ggw` ties gas transfer to gas heat capacity. |
| (c) Heat-removal rate | `drive_model.js`: `Gout` = natural convection + radiation (`natconvH`, Churchill sphere + radiation) in series with outer-cell conduction, to ambient `Ta`. `solver_v0.py`: outer surface held at 293 K (the locked Kelvin reference, an ideal sink, not a removal rate). | No breakdown of removal by path (conduction / convection / radiation reported separately). No finite removal rate in the solver. |
| Thermal mass | `drive_model.js`: `Cq` (ρ c_p V per quartz cell), `Cv_g` (gas). `solver_v0.py`: ρ c_p per material for every layer. | Not reported per layer as "heat held before pushing back". |
| Lumping (flag) | `tauLumped = Ctot/hA0` in `drive_model.js` folds total thermal mass and removal into one time constant. It sets the run length (`tEnd`) and is listed as a "whole-bubble" thermal mode. | Replace with separate transfer / removal / mass quantities; keep `tauLumped` only as a labelled diagnostic, if at all. |



=== BRANCH DIFF ===
diff --git a/.cursor/rules/handoffs.mdc b/.cursor/rules/handoffs.mdc
index 32d2bcf..571a29c 100644
--- a/.cursor/rules/handoffs.mdc
+++ b/.cursor/rules/handoffs.mdc
@@ -37,6 +37,12 @@ Optional scope: append `domains=thermal,chemical` (or `domains=all`) to `/claude
 Decided by Danny on 2026-10-19 (round 3); see `DESIGN_STATE.md`, "Locked holster architecture". Status: locked. Build order: GitHub review ledger (issues plus append-only JSONL, reviewers scored) first; planted-mistake scoring rubric and monthly per-model cost rollup on top of it; FEniCS/OpenFOAM MCP gateway after the ledger. Do not re-open or re-order without Danny. Status 2026-10-19: ledger, scoring and cost rollup built (`ledger/README.md`); gateway partial (`gateway/README.md`). The ordering-gap sweep ran as round 4 (`reviews/2026-10-19_round4/`); Danny decided it the same day: **receipt gate + spec-review class** (locked item 5, built). A paid review is a code review only with a CI execution receipt for every touched component; otherwise it is a spec review (cheap route, never scored). Receipts come only from CI (`.github/actions/receipt`, attested); never write or hand-edit a receipt, and a stub with locked I/O never earns one (`scripts/stub_detector.py`). Details: `harness/README.md`, "Receipt gate".
 
 ## Never
-- Never reintroduce a retired item: oil bath; slotted Cu/Ag shell; ribs/segments; 6.75 kHz (except labelled as history); 0.2 T; 13 GHz atom-count ceiling; cold-regime work; `Backwards_Derived_Spec_from_Ionisation`.
+- Never reintroduce a retired item: oil bath; slotted Cu/Ag shell; ribs/segments; 6.75 kHz (except labelled as history); 0.2 T; 13 GHz atom-count ceiling; cold-regime work; `Backwards_Derived_Spec_from_Ionisation`; electrodes of any kind (Ti/Pt film, ITO/transparent electrode, central wire / DBD centre electrode; retired 2026-10-19).
+- Never replace the locked Kelvin reference (293 K outer reference temperatures) with required-conductance output.
+- Never use °C in calculations, the solver, data files or `DESIGN_STATE.md`: Kelvin is canonical. °C is GUI-only, shown next to K; GUI ambient is a linked K/°C pair.
 - Never add Perplexity (not in use for now). Qwen is not connected yet: do not wire it without Danny's go-ahead.
 - Never let a reviewer edit `.github/workflows/` or merge to main.
+- Never add electrode geometry, formulas, presets or code: the drive stays "no drive mechanism defined" (fail closed) until Danny defines one.
+- Never make knee frequency an external dial (it is emergent, self-oscillating); never lump switching frequency, heat-transfer speed and heat-removal rate (plus thermal mass) into one time constant. See `DESIGN_STATE.md`, "Intended model behaviour (2026-10-19)".
+- Never let a design cross autoignition without the cooling cascade (driven over the knee; too hot ignites; cascading cooling prevents ignition).
+- Architecture: 7 energy domains (optical, acoustic, electric, magnetic, thermal, chemical, information) + 12 knees, each with its own holster = 19 holsters. Say "energy domains", never "power domains".
diff --git a/AGENTS.md b/AGENTS.md
index f444b5e..35b7483 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -19,7 +19,9 @@ Reviewers (Claude, Grok, Claude Code) read it too.
 | Tavily (web search) | **Shared web-search slot** for any model/Cursor. Rule: use it whenever a review/check needs current info or external sources. Kimi/DeepSeek search + filter first; Claude/Grok spend after. Grok reviews: 1 pre-search by default (xAI built-in search off) | `/tavily-search <query>` → `.github/workflows/tavily-search.yml` |
 | Perplexity | **Not used for now.** Do not add it. | — |
 
-Six domains: optical, acoustic, electric, magnetic, thermal, chemical. Plasma is the source that drives them, not a domain.
+Seven energy domains: optical, acoustic, electric, magnetic, thermal, chemical and information (the information layer is a real domain; Danny, 2026-10-19). Plasma is the source that drives them, not a domain. Say "energy domains", not "power domains".
+
+Holsters: 19 in total, one per knee and one per energy domain (12 knee holsters + 7 energy-domain holsters). Each has its own holster; the holster is not a single shared component.
 
 ## The loop
 
@@ -127,6 +129,18 @@ Reviewers FAIL any reintroduction. A deterministic scan (`harness/retired.txt`)
 - 13 GHz atom-count ceiling
 - Cold-regime work
 - `Backwards_Derived_Spec_from_Ionisation` (do not cite, rebuild from, or restore)
+- Electrodes of any kind (2026-10-19): Ti/Pt film, ITO / transparent-electrode case, central 50 µm wire / DBD centre electrode. There are no electrodes in the design. How the gas is driven without them is open for Danny; do not answer it.
+
+## Protected conventions (locked 2026-10-19)
+
+- **Kelvin reference:** the 293 K outer reference temperatures stay. Danny uses them to place thermal active materials in the tone. Do not replace them with required-conductance output (rejected, round 5).
+- **Kelvin canonical:** calculations, the solver, data files and `DESIGN_STATE.md` use K. °C appears only in the GUI, alongside K. Reviewers flag any °C in calculations/solver/data/spec and any GUI temperature without its °C pair.
+- **GUI ambient** is a linked K/°C pair: enter either, the other updates (K = °C + 273.15).
+- Round-5 decisions (fold / cut / keep / defer): `DESIGN_STATE.md`, "Danny's decisions on round-5 review (2026-10-19)".
+- **Electrodes are gone from the model**, not just the design: no formula, geometry, preset or code path may reference one. The drive is a fail-closed stub, "no drive mechanism defined". Any electrode reference (outside a labelled retirement note) is an ERROR.
+- **Intended model behaviour** (`DESIGN_STATE.md`, "Intended model behaviour (2026-10-19)"): the system is driven over the knee (the thermal trigger); too hot means it ignites; cascading cooling prevents ignition. Flag designs/outputs that cross autoignition without the cooling cascade; never propose an electrode-based drive.
+- **Knee frequency is emergent** (self-oscillating, from the layers), never an external dial. Flag any change that treats it as an input. `drive_model.js`'s `f` is legacy scaffolding (deferred).
+- **Three thermal rates + thermal mass, never lumped:** switching frequency, heat-transfer speed, heat-removal rate, plus thermal mass. Flag any single lumped time constant (e.g. `tauLumped`).
 
 ## Limits for every agent
 
diff --git a/DESIGN_STATE.md b/DESIGN_STATE.md
index d994efa..44c706a 100644
--- a/DESIGN_STATE.md
+++ b/DESIGN_STATE.md
@@ -14,8 +14,8 @@ Every tool working on this project reads this file first, never reintroduces a r
 
 ### Core: HHO
 - **Fill:** HHO at a 2:1 H₂:O₂ ratio. The fill amount is open and can be swept.
-- **Ionisation knee:** about 10 Torr for a 1 mm gap, or about 22 Torr with a central electrode (0.45 mm gap).
-- **Electrodes:** a metal film on the inner wall screens the gas. Ionising it needs a central electrode (DBD, dielectric barrier discharge) or an external field.
+- **Ionisation knee:** about 10 Torr for a 1 mm gap. The earlier ~22 Torr figure assumed a 0.45 mm gap to a central electrode, which is retired (2026-10-19); how the gas is driven without electrodes is Open item 8.
+- **Electrodes:** none. There are no electrodes in the design (Danny, 2026-10-19): no Ti/Pt film, no ITO/transparent electrode, no central wire. See Retired.
 
 ### Layer 1: quartz
 - **Shape:** a sphere unless Danny says tube.
@@ -37,7 +37,7 @@ Every tool working on this project reads this file first, never reintroduces a r
 
 ### Layer 3: elbaite tourmaline sol-gel
 - **Thickness:** about 5 µm, within a 3–8 µm range.
-- **Binder:** a silica sol-gel (MTES:TEOS 80:20). Pt needs a 10 nm SiO₂ or TiO₂ primer, and the tourmaline needs a silica shell formed at pH 8–9.
+- **Binder:** a silica sol-gel (MTES:TEOS 80:20). (The earlier Pt-primer note is moot: electrodes are retired, 2026-10-19.) The tourmaline needs a silica shell formed at pH 8–9.
 
 ### Layer 4: downshifting phosphor
 - **Options:** KSF, which saturates at about 8–16 W, or CASN, which saturates at about 80 W.
@@ -47,15 +47,22 @@ Every tool working on this project reads this file first, never reintroduces a r
 - **Magnetic or caloric option:** ferrite, Gd-Dy or CALORIVAC.
 - **Heat sink:** Danny's choice, still open.
 
+### Thermal reference and temperature convention (locked 2026-10-19)
+- **Kelvin reference: locked.** The 293 K outer reference temperatures stay. Danny uses them to select thermal active materials placement in the tone. Do not replace them with required-conductance output (reviewer suggestion rejected, round 5).
+- **Kelvin is canonical.** All calculations, the solver, data files and this spec use Kelvin, from 0 K up. Celsius is never used in a calculation, solver, data file or spec value.
+- **Celsius is a GUI-only display rule.** In the viewer/visualisation layer every displayed temperature shows its °C value alongside the K value.
+- **Ambient in the GUI is a linked K/°C pair:** enter either; the other updates automatically (K = °C + 273.15). The model receives K.
+- **Supersession chain (all 2026-10-19):** 293 K single reference → K + °C everywhere → Celsius-only ambient → linked K/°C ambient → **Kelvin canonical, °C in the GUI only** (current). Earlier wording that the spec states every temperature in both K and °C is superseded: the spec states K; the K + °C pairing is a GUI rule. No bulk °C conversion of the spec is needed.
+
 ## Open
 1. Which quartz shell: the 5.4 mm lock shell, the 6.78 mm φ shell, or the 1×2 mm test shell. Sphere or tube.
 2. The heat path. At 1 W in still air, the test shell's inner wall gets past HHO autoignition.
 3. The BTO thickness, and how to keep it below its Curie point.
 4. The tourmaline thickness, traded against scattering at 434 nm. Also the cure temperature and whether it sits inside or outside the BTO.
-5. Which phosphor, and whether the electrodes sit in layer 4. Ti/Pt blocks light, and that is the main source of heat.
+5. Which phosphor. (The electrode-placement / Ti/Pt light-blocking question is closed: electrodes are retired, 2026-10-19.)
 6. Which layer 5 option.
 7. The HHO fill amount.
-8. Central electrode or external field.
+8. **How the gas is driven with no electrodes.** Open for Danny. The old "central electrode or external field" choice is superseded because electrodes are retired. Since 2026-10-19 the code has **no drive mechanism defined**: `drive_model.js` and `solver_v0.py` carry a fail-closed stub (zero deposited energy, zero discharge, zero electric/magnetic field and loss). The old DBD gap, Paschen V_b and the 10.71–98.95 Torr window were removed with the electrodes. Do not invent a drive to fill the stub.
 
 ## Retired (never reintroduce)
 - Oil bath
@@ -67,13 +74,14 @@ Every tool working on this project reads this file first, never reintroduces a r
 - Cold-regime work
 - `Backwards_Derived_Spec_from_Ionisation`: its numbers and layer roles
 - Grok's radial diamond spokes
+- Electrodes of any kind (retired 2026-10-19): Ti/Pt film, ITO/transparent-electrode case, central 50 µm wire / DBD centre electrode. There are no electrodes in the design.
 
 ---
 
 ## Information layer (harness architecture)
 Full spec: the Drive doc "Stratified Sphere — Information Layer (Harness Architecture) 2026-10-19".
 
-- **Harnesses:** 18 in total. There are 6 domain harnesses (optical, acoustic, electric, magnetic, thermal and chemical), which run in parallel on GitHub Actions and pass results to each other between rounds. There are also 12 knee harnesses.
+- **Holsters (Danny, 2026-10-19):** 19 in total, one per knee and one per energy domain: **12 knee holsters + 7 energy-domain holsters**. The seven energy domains are optical, acoustic, electric, magnetic, thermal, chemical and **information** (the information layer is a real domain). Each knee and each energy domain has its **own** holster; the holster is not a single shared component. Say "energy domains", not "power domains". (Superseded: "18 harnesses: 6 domain + 12 knee", and the same-day 6 + 12 = 18 holster note.) The domain holsters run in parallel on GitHub Actions and pass results to each other between rounds.
 - **Coordinator:** Cursor. It reads a granularity dial: shallow for scouting, deep for validating.
 - **Checks:**
   - The Claude API audits Cursor's merges every few rounds.
@@ -127,3 +135,71 @@ Workflow `.github/workflows/sim-stack.yml` (one job per tool; push to `sim/**`,
 | CalculiX | ccx 2.21 (Ubuntu 24.04 apt 2.21-1) | B32 cantilever vs PL³/3EI, 2 % | PASS |
 | Code_Aster | 18.1.0 (simvia Docker, digest-pinned) | POU_D_E cantilever vs PL³/3EI + bundled forma01a | PASS |
 | Gwyddion | 2.64 (Ubuntu 24.04 apt 2.64-1.1build3) | load .gsf via Gwyddion GSF module, size + RMS = A/√2 | PASS |
+
+## Danny's decisions on round-5 review (2026-10-19)
+Source: `reviews/2026-10-19_round5/` (Claude and Grok replies to the open repo prompt). Decided by Danny on 2026-10-19. Staged ledger dispositions: `ledger/pending/2026-10-19_round5_dispositions.jsonl` (not yet ingested; the ledger is CI-written).
+
+### Fold (accepted; to be built later, after Danny's validation)
+1. **One geometry-of-record file** read by both this file and the solver, with a CI check that fails on drift (Grok).
+2. **Recompute drive frequencies from that file**, with the sound speed and formula recorded in the output. This settles 3.236 vs 3.018 MHz (Grok).
+3. **A power budget that sums to the input**, tested, with no double-counted loss (Grok).
+4. **Keep placeholder chemistry (`P_release`) out of the heat sources**; ignition becomes a validity flag (Grok).
+5. **Small number fixes:** `phos_out` cT = 25 m/s; the BTO ε(T) curve's "Curie-Weiss" label; the layer-2 "50 nm" label vs 5 µm (Grok).
+6. **Fix the factor-of-2 ring-jump bug** in `drive_model.js` (`maxJump` taken from the partial-step Ed/dt), with an ncyc-invariance test (Claude found the split; traced 2026-10-19).
+7. **GUI temperatures: K with °C alongside, ambient as a linked pair** (Danny's clarification, 2026-10-19): every temperature the viewer displays shows °C next to K, and the Kelvin-only ambient field (`dTa`, commit 21b5fa5) becomes two linked fields, K and °C, that sync both ways (K = °C + 273.15). The model, solver, data files and spec stay in K; no bulk °C conversion of the spec. Not built yet. Known K-canonical gap for this fold: `drive_model.js` compares the autoignition range in °C (`AUTOIGN_C = [500, 585]`) and prints flags in °C; that should become K internally (773.15–858.15 K) with °C only in the display.
+
+### Cut (rejected)
+- **All electrode items.** There are no electrodes in the design, period: no Ti/Pt film, no ITO/transparent-electrode case, no central 50 µm wire / DBD centre electrode. Added to Retired.
+- **Electrodes removed from the model entirely (Danny, 2026-10-19).** No formula, geometry, preset or code path references an electrode. `drive_model.js` lost the centre-electrode gap (r0, gap, Cd/Cg, share, V_amp), Paschen V_b, the ionisation window and the knee/clamp conduction; `solver_v0.py` lost the Ti/Pt layer, ALPHA_PT, sheet resistances, the BTO-on-Ti/Pt LC tank and the bare-shell discharge field. Both now return "no drive mechanism defined" (fail closed: zero energy, zero discharge-derived outputs). How the gas is driven is Open item 8.
+
+### Keep (reviewer suggestion rejected)
+- **The Kelvin reference** (293 K outer reference temperatures) stays, because Danny uses it to select thermal active materials placement in the tone. Grok's suggestion to replace it with required-conductance output is rejected. Locked above.
+
+### Deferred (sounded good; later)
+- Claude's three labelled temperatures (peak / cycle average / periodic steady state).
+- A single solver entry point.
+- Uncertainty bands.
+- l ≥ 1 and anisotropic quartz modes.
+- FEniCS / MEEP / OpenFOAM cases, held until folds 1–3 pass.
+
+## Intended model behaviour (2026-10-19)
+Design intent from Danny, recorded only. No drive mechanism or new physics is coded for it; the drive stays "no drive mechanism defined". Reviewers check model changes against this section.
+
+### The knee, ignition and cascading cooling
+Danny: *"The system is driven over the knee — that is what makes it go that way. If it gets too hot, it ignites. If it is cooling and cooling cascading, then it will never ignite. Modelling this ignition-vs-cooling behaviour is part of what we want to try."*
+
+- The **knee is the thermal trigger**: the system is driven over the knee.
+- **Ignition** (HHO autoignition, 773.15–858.15 K) is the failure mode when it gets too hot.
+- **Cascading cooling** is the mechanism that prevents ignition.
+- Reviewers flag any design or output that crosses autoignition without the cooling cascade. They must not propose electrode-based drives (electrodes are retired) to get there.
+
+### Knee frequency is emergent, not a dial
+Danny: the frequency and switching of the knee energy come from within the system itself. There is an input pump, but more layers must be built out before reaching it. The knee is **self-oscillating**; its frequency is an **emergent property of the layers**, not an externally set dial.
+
+- Reviewers flag any change that treats knee frequency as an external input or dial as contrary to intent.
+- The `drive_model.js` drive-frequency input `f` (and the former `V_amp`, removed with the electrodes) is **legacy scaffolding** relative to this intent. It stays for now (see deferred items below).
+- A frequency sweep to find which frequencies talk to each other is a **future** item; the model is not there yet.
+
+### Three thermal rates plus thermal mass, never lumped
+The model must treat these independently, never folded into one time constant:
+
+1. **Switching frequency:** how quickly or slowly the knee is switched.
+2. **Heat-transfer speed:** how fast heat moves through a material before it soaks or saturates.
+3. **Heat-removal rate:** how fast heat leaves the system, by whatever path (conduction, convection, radiation).
+
+**Thermal mass** (how much heat a material holds before it pushes back) is also required. Reviewers flag any lumping of these into one time constant, for example the single `tauLumped`.
+
+### Deferred / fold items from this intent
+- **Model ignition vs cascading cooling** (drive over the knee vs cascading cooling). Ties to Claude's periodic-steady-state temperature item (round-5 deferred: peak / cycle average / periodic steady state).
+- **Retire the external drive-frequency input** (`f` in `drive_model.js`, and `T = 1/f`, `ncyc`, `regime(p.f)`) once the layers exist for the knee to self-oscillate. Do not remove it before then.
+- **Frequency sweep** (which frequencies talk to each other): future, after the layers are built.
+- **Thermal rates: where the code is now, and what is missing** (as of 2026-10-19):
+
+| Quantity | Where it is now | What is missing |
+|---|---|---|
+| (a) Switching frequency | Only the external `p.f` in `drive_model.js` (cycle `T = 1/f`, `ncyc` steps). `solver_v0.py` has no switching (steady/transient P_circ scenarios). | Emergent self-oscillating knee switching. Today it is a dial, which is contrary to intent. |
+| (b) Heat-transfer speed | `drive_model.js`: `tau_g = a²/(π²α_g)` (gas conduction), `tau_w = (b−a)²/(π²α_q)` (quartz wall diffusion), gas-wall conductance `Ggw = Cv_g/tau_g`, 24-cell quartz conduction with k(T). `solver_v0.py`: 1-D finite-volume conduction through every layer, with k(T) for quartz and interface resistances. | No per-layer "time to soak/saturate" output. `drive_model.js` models quartz only (no other layers). `Ggw` ties gas transfer to gas heat capacity. |
+| (c) Heat-removal rate | `drive_model.js`: `Gout` = natural convection + radiation (`natconvH`, Churchill sphere + radiation) in series with outer-cell conduction, to ambient `Ta`. `solver_v0.py`: outer surface held at 293 K (the locked Kelvin reference, an ideal sink, not a removal rate). | No breakdown of removal by path (conduction / convection / radiation reported separately). No finite removal rate in the solver. |
+| Thermal mass | `drive_model.js`: `Cq` (ρ c_p V per quartz cell), `Cv_g` (gas). `solver_v0.py`: ρ c_p per material for every layer. | Not reported per layer as "heat held before pushing back". |
+| Lumping (flag) | `tauLumped = Ctot/hA0` in `drive_model.js` folds total thermal mass and removal into one time constant. It sets the run length (`tEnd`) and is listed as a "whole-bubble" thermal mode. | Replace with separate transfer / removal / mass quantities; keep `tauLumped` only as a labelled diagnostic, if at all. |
+
diff --git a/drive_model.js b/drive_model.js
index 44f2178..b4338a2 100644
--- a/drive_model.js
+++ b/drive_model.js
@@ -1,8 +1,11 @@
 /* drive_model.js - v0 coupled single-cycle drive model for the bare HHO / crystal-quartz bubble.
    ESTIMATED PHYSICS, NOT VALIDATED. Runs in the browser (window.DriveModel) and in node (module.exports).
-   User sets: fill (HHO amount + sealing temperature = initial/ambient condition), geometry (ID, OD), drive (amplitude, frequency, ONE cycle).
+   User sets: fill (HHO amount + sealing temperature), ambient temperature, geometry (ID, OD), drive frequency (ONE cycle).
+   ELECTRODES REMOVED 2026-10-19 (Danny: electrodes were the wrong architecture). There is NO drive mechanism defined: the drive
+   source is a fail-closed stub that deposits no energy. Breakdown, energy per cycle, discharge heating, chemistry from the
+   discharge and acoustic ring-down are therefore all zero. The drive method is open for Danny; do not add one here.
    Computed (coupled) states: gas temperature T_g(t), pressure p = N k T_g / V, number density (fixed), HHO sound speed c(T_g),
-   gas-cavity mode frequencies and Q, ionisation knee, wall temperatures, deposited energy, ring-down per domain.
+   gas-cavity mode frequencies and Q, wall temperatures (rise above seal; ambient exchange), natural modes per domain.
    Tags: [lit] published, [rec] from another box report, [calc] computed here, [est] estimate / assumption / placeholder. */
 (function (root) {
   "use strict";
@@ -22,14 +25,12 @@
     v0: { cL: 6153, cT: 4210, label: "v0/v0.2 value", src: "[rec shell_phi_sweep] superseded by the cited VRH entry" } };
   let QZ_SEL = "vrh";
   function setQuartzSound(k) { if (QZ_SOUND[k]) QZ_SEL = k; return QZ_SOUND[QZ_SEL]; }
-  // breakdown formation time [est, order of magnitude]: electron avalanche generations ln(1+1/γ) x gap / v_drift,e ; Townsend ion feedback gap / v_drift,i
-  const FORM = { vde: 1e5, vdi: 2e3 };   // m/s drift velocities near the Paschen-minimum E/N [PLACEHOLDERS est]
   const BALMER = [["Hα", 656.28e-9], ["Hβ", 486.13e-9], ["Hγ", 434.05e-9], ["Hδ", 410.17e-9]];  // air wavelengths [lit NIST ASD]
   const VIS = [380e-9, 750e-9];  // visible band [lit-typical CIE range]
-  const PASCHEN = { Vmin: 332, pdmin: 1.0, gse: 0.01 };  // HHO mix: Vmin/pd_min [est mole-fraction rule from lit H2 273 V@1.15, O2 450 V@0.70 Torr cm]; gamma_se [est]
-  const ETA = { gas: 0.6, wall: 0.3, opt: 0.1 };          // discharge energy partition [est placeholders]
+  const ETA = { gas: 0.6, wall: 0.3, opt: 0.1 };          // energy partition of a deposited drive energy [est placeholders]; unused while no drive is defined
   const SHELL_Q = 2100;                                   // [rec] used as placeholder for every shell mode
   const AUTOIGN_C = [500, 585];
+  const NO_DRIVE = "no drive mechanism defined (electrodes removed 2026-10-19; drive method open): no breakdown, no deposited energy, no discharge heating or chemistry, no acoustic ring-down";
   const CH = { ED: 4.478 * 1.602176634e-19,   // H2 D0 [lit NIST CCCBDB]
     DH: 241.826e3 / 6.02214076e23,          // J per H2O formed (LHV, dHf H2O(g)) [lit NIST WebBook]
     eta: 0.2, nu: 1.0, D1atm: 1.5e-4 };      // dissociation share, chain length, H diffusivity at 1 atm [PLACEHOLDERS est]                           // HHO autoignition range [given by Danny; lit H2 ~500-585 C]
@@ -59,25 +60,6 @@
     }
     return out;
   }
-  function paschenV(n_m3, d_m) {           // breakdown voltage from density*gap (density referenced to 293 K)
-    const pd = n_m3 * kB * 293 / TORR * d_m * 100;   // Torr cm equivalent at 293 K
-    const A = Math.E * Math.log(1 + 1 / PASCHEN.gse) / PASCHEN.pdmin, B = PASCHEN.Vmin / PASCHEN.pdmin;
-    const den = Math.log(A * pd / Math.log(1 + 1 / PASCHEN.gse));
-    return den > 0.05 ? B * pd / den : Infinity;
-  }
-  function kneeFill_Torr(d_m) { return PASCHEN.pdmin / (d_m * 100); }   // fill (at 293 K) that puts the gap at the Paschen minimum
-  /* ionisationWindow(p): the fill range (Torr at T_seal) that ionises in this model, using ONE voltage definition: peak gas
-     voltage Vg = share x V_amp against the static Paschen V_b(n d). Same criterion as run() (gas voltage clamps at V_b) and its
-     "no ionisation" flag. Static knee only: the regime flags (formation time) can still close it at high f. [calc] */
-  function ionisationWindow(p) {
-    const g = geometry(p), Ts = p.T_seal || 293.15, Vg = g.share * p.V_amp;
-    const h = fill => Vg - paschenV(fill * TORR / (kB * Ts), g.gap);   // > 0 inside the window; -Infinity left of the Paschen curve
-    const kf = kneeFill_Torr(g.gap) * Ts / 293;                        // Paschen-minimum fill expressed at T_seal (same n)
-    if (!(h(kf) > 0)) return { Vgas: Vg, lo_Torr: null, hi_Torr: null, empty: true };
-    const bis = (a, b) => { for (let i = 0; i < 200; i++) { const m = Math.sqrt(a * b); if ((h(m) > 0) === (h(a) > 0)) a = m; else b = m; } return Math.sqrt(a * b); };
-    let hi = kf * 2; while (h(hi) > 0 && hi < 1e12) hi *= 2;
-    return { Vgas: Vg, lo_Torr: bis(kf * 1e-6, kf), hi_Torr: bis(kf, hi), empty: false };
-  }
 
   function natconvH(Ts, Ta, D) {           // Churchill sphere + radiation [lit correlation; air props est]
     const Tf = 0.5 * (Ts + Ta), k = 0.0263 * Math.pow(Tf / 300, 0.8), nu = 1.57e-5 * Math.pow(Tf / 300, 1.7), Pr = 0.71;
@@ -88,22 +70,17 @@
   }
 
   function geometry(p) {
-    const a = p.ID_mm / 2e3, b = p.OD_mm / 2e3, r0 = (p.r0_mm || 0.05) / 1e3;
+    const a = p.ID_mm / 2e3, b = p.OD_mm / 2e3;
     const V = 4 / 3 * Math.PI * a ** 3;
-    const Cg = 4 * Math.PI * EPS0 / (1 / r0 - 1 / a), Cd = 4 * Math.PI * EPS0 * QZ.eps / (1 / a - 1 / b);
-    return { a, b, r0, V, Cg, Cd, Ctot: Cg * Cd / (Cg + Cd), share: Cd / (Cg + Cd), gap: a - r0 };
+    return { a, b, V };   // gas core radius a, quartz OD radius b, gas volume V (electrodes removed: no gap, no capacitance split)
   }
 
-  // modal overlap of the discharge heat deposition (est profile ~ E^2 ~ r^-4 between r0 and a) with radial gas mode j0(x r/a)
+  // radial gas mode j0(x r/a): wall value and volume-average of j0^2 (used for the boundary-layer Q) [calc]
   function overlapRadial(g, x) {
-    const N = 2000; let num = 0, den = 0, nrm = 0;
-    for (let i = 0; i < N; i++) {
-      const r = g.r0 + (g.a - g.r0) * (i + 0.5) / N, w = Math.pow(r, -4), dr = (g.a - g.r0) / N;
-      num += w * j0(x * r / g.a) * r * r * dr; den += w * r * r * dr;
-    }
+    const N = 2000; let nrm = 0;
     for (let i = 0; i < N; i++) { const r = g.a * (i + 0.5) / N; nrm += j0(x * r / g.a) ** 2 * r * r * g.a / N; }
     const Vn = 3 * nrm / g.a ** 3;  // volume-average of j0^2
-    return { kappa: num / den / Vn, jw: j0(x), Vn };
+    return { jw: j0(x), Vn };
   }
 
   function gasModeQ(g, x, T, rho) {        // [est] thermal boundary layer + classical bulk losses (radial modes; rigid wall)
@@ -113,7 +90,7 @@
     const Qth_inv = (HHO.gamma - 1) * dT * (3 / g.a) / 2 * zeta;
     const acl = w * w / (2 * rho * c ** 3) * (4 / 3 * muGas(T) + (HHO.gamma - 1) * kGas(T) / HHO.cp);
     const Qcl_inv = 2 * acl * c / w;
-    return { f, Q: 1 / (Qth_inv + Qcl_inv), kappa: o.kappa };
+    return { f, Q: 1 / (Qth_inv + Qcl_inv) };
   }
 
   function naturalModes(p, state) {       // the system's own response frequencies at gas temperature T (computed state)
@@ -133,28 +110,27 @@
     { const pse = state.N * kB * (state.Tseal || 293) / g.V, D = CH.D1atm * 101325 / Math.max(pse, 1), tD = g.a ** 2 / (Math.PI ** 2 * D);
       out.push({ domain: "chemical", name: "radical diffusion to wall 1/(2 pi tau_D) [calc; D placeholder]; knee: not defined", f: 1 / (2 * Math.PI * tD), tau: tD }); }
     out.push({ domain: "electric", name: "dielectric-sphere EM resonance ~ c x/(2 pi b sqrt(eps)) [est]", f: C0 * 2.0 / (2 * Math.PI * g.b * Math.sqrt(QZ.eps)) });
-    out.push({ domain: "magnetic", name: "same EM resonance (B=0 for the symmetric radial drive) [est]", f: C0 * 2.0 / (2 * Math.PI * g.b * Math.sqrt(QZ.eps)) });
+    out.push({ domain: "magnetic", name: "same EM resonance (B = 0: no drive mechanism defined) [est]", f: C0 * 2.0 / (2 * Math.PI * g.b * Math.sqrt(QZ.eps)) });
     out.push({ domain: "optical", name: "H-alpha 656.3 nm [lit]", f: C0 / 656.3e-9 }, { domain: "optical", name: "H-beta 486.1 nm [lit]", f: C0 / 486.1e-9 }, { domain: "optical", name: "H-gamma 434.0 nm [lit]", f: C0 / 434.0e-9 });
     return out;
   }
 
   /* run(p): p = {ID_mm, OD_mm, fill_Torr (at T_seal) | fill_molecules, T_seal (sealing = initial K), T_amb (ambient air K, optional;
-     default T_seal), V_amp (V peak), f (Hz), shellModes:[{name,f,tag}]}. The wall exchanges heat with still air at T_amb.
+     default T_seal), f (Hz, drive frequency: sets the one-cycle time grid and the regime flags), shellModes:[{name,f,tag}]}.
+     The wall exchanges heat with still air at T_amb. No drive mechanism is defined (electrodes removed 2026-10-19): the drive
+     source below is a stub that deposits zero energy, so every discharge-derived output is exactly zero.
      returns traces + summary. Missing required inputs -> {error}. */
   function run(p, opts) {
     opts = opts || {};
-    for (const k of ["ID_mm", "OD_mm", "T_seal", "V_amp", "f"]) if (!(p[k] > 0)) return { error: "enter " + k };
+    for (const k of ["ID_mm", "OD_mm", "T_seal", "f"]) if (!(p[k] > 0)) return { error: "enter " + k };
     if (!(p.fill_Torr > 0) && !(p.fill_molecules > 0)) return { error: "enter fill" };
     if (p.OD_mm <= p.ID_mm) return { error: "OD must exceed ID" };
     const hasAmb = p.T_amb !== undefined && p.T_amb !== null;
     if (hasAmb && !(p.T_amb > 0)) return { error: "ambient T must be > 0 K (leave unset for ambient = sealing T)" };
-    if (p.ID_mm / 2e3 <= (p.r0_mm || 0.05) / 1e3) return { error: "ID must exceed the 0.1 mm centre-electrode diameter [est]" };
     const g = geometry(p), Ta = hasAmb ? p.T_amb : p.T_seal;   // ambient defaults to the sealing temperature
     const N = p.fill_molecules > 0 ? p.fill_molecules : p.fill_Torr * TORR * g.V / (kB * p.T_seal);
     const n = N / g.V, mgas = N * HHO.M / NA, rho = mgas / g.V, Cv_g = mgas * HHO.cp / HHO.gamma;
-    const Vb0 = paschenV(n, g.gap);
     const reg = regime(p.f, g);
-    const Vb = reg.noForm ? Infinity : Vb0;   // half-cycle shorter than electron-avalanche formation: no breakdown can form
     // wall grid
     const NW = 24, rr = [], Vc = [], Cq = [];
     for (let i = 0; i <= NW; i++) rr.push(g.a + (g.b - g.a) * i / NW);
@@ -174,29 +150,17 @@
     const tEnd = Math.min(Math.max(5 * tauLumped, 20 * T), 200);
     const nlog = opts.nlog || 160;
     for (let i = 1; i <= nlog; i++) ts.push(T * Math.pow(tEnd / T, i / nlog));
-    // discharge state (Manley-type, single cycle from rest, gas-voltage memory) [est]
-    let Vg = 0, Vprev = 0, Edis = 0, Qtr = 0; const jumps = []; let Pprev = 0, conducting = false;
-    const tr = { t: [], V: [], Vg: [], P: [], Tg: [], Twin: [], Twout: [], p: [], c: [], fgas0: [], Vb: [] };
+    // DRIVE SOURCE STUB: no drive mechanism defined (electrodes removed 2026-10-19; drive method open). Fails closed:
+    // deposits exactly zero energy on every step. Do not replace with an invented mechanism; Danny decides the drive.
+    const driveEnergy = (t, dt) => 0;
+    let Edis = 0;
+    const tr = { t: [], P: [], Tg: [], Twin: [], Twout: [], p: [], c: [], fgas0: [] };
     const fx0 = 4.4934 / (2 * Math.PI * g.a);
     let maxThG = 0, maxThW = 0, Egas = 0, Ewall = 0, Eopt = 0, nDiss = 0, nWater = 0, Echem = 0, H2left = 2 * N / 3;
     for (let k = 1; k < ts.length; k++) {
       const t = ts[k], dt = t - ts[k - 1];
-      const V = t <= T ? p.V_amp * Math.sin(w * t) : 0;
-      const dV = V - Vprev;
-      // gas voltage: follows share*dV until clamped at +-Vb; clamp => conduction
-      let VgNew = Vg + g.share * dV, Ed = 0;
-      if (Math.abs(VgNew) > Vb && t <= T + 1e-15) {
-        const over = Math.abs(VgNew) - Vb;              // excess gas-voltage swing dumped as charge through the barrier
-        const dq = over / g.share * g.Cd;               // charge transferred [est]
-        Ed = Vb * dq; Qtr += dq; VgNew = Math.sign(VgNew) * Vb; conducting = true;
-      } else conducting = false;
-      Vg = VgNew; Vprev = V;
-      const Pd = Ed / dt;
-      if (k <= ncyc + 1 && Math.abs(Pd - Pprev) > 0) {
-        // record jumps in discharge power (onset/end) - drive impulsive ring-down of fast modes [est]
-        if ((Pprev === 0 && Pd > 0) || (Pprev > 0 && Pd === 0)) jumps.push({ t, dP: Pd - Pprev });
-      }
-      Pprev = Pd; Edis += Ed;
+      const Ed = driveEnergy(t, dt), Pd = Ed / dt;
+      Edis += Ed;
       Egas += ETA.gas * Ed; Ewall += ETA.wall * Ed; Eopt += ETA.opt * Ed;
       const dnd = CH.eta * ETA.gas * Ed / CH.ED, dnw = Math.min(CH.nu * dnd, H2left); H2left -= dnw; nDiss += dnd; nWater += dnw;
       const Ech = dnw * CH.DH; Echem += Ech;   // chemical heat release fed to the gas
@@ -222,31 +186,21 @@
       for (let i = M - 2; i >= 0; i--) X[i] = (D[i] - Cc[i] * X[i + 1]) / B[i];
       thG = X[0]; thW = X.slice(1); Tg = Ts + thG; Tw = thW.map(x => Ts + x);
       maxThG = Math.max(maxThG, thG); maxThW = Math.max(maxThW, thW[0]);
-      tr.t.push(t); tr.V.push(V); tr.Vg.push(Vg); tr.P.push(Pd); tr.Tg.push(Tg); tr.Twin.push(Tw[0]); tr.Twout.push(Tw[NW - 1]);
-      tr.p.push(N * kB * Tg / g.V); tr.c.push(cHHO(Tg)); tr.fgas0.push(fx0 * cHHO(Tg)); tr.Vb.push(Vb);
+      tr.t.push(t); tr.P.push(Pd); tr.Tg.push(Tg); tr.Twin.push(Tw[0]); tr.Twout.push(Tw[NW - 1]);
+      tr.p.push(N * kB * Tg / g.V); tr.c.push(cHHO(Tg)); tr.fgas0.push(fx0 * cHHO(Tg));
     }
-    // fast-mode ring-down from discharge-power jumps (impulse approximation, valid while f_mode >> f_drive) [est]
+    // acoustic ring-down: no drive source, so no mode is driven (the former discharge-jump impulse source is removed with the electrodes)
     const maxTg = Ts + maxThG, maxTw = Ts + maxThW;   // peak absolute temperatures; dTg/dTw below are the peak rises themselves
     const sigOverP = (g.b ** 3 + 2 * g.a ** 3) / (2 * (g.b ** 3 - g.a ** 3));  // Lame inner hoop stress / inner pressure [calc]
     const uOverP = g.a / QZ.E * ((1 - 2 * QZ.nu) * g.a ** 3 + (1 + QZ.nu) * g.b ** 3 / 2) / (g.b ** 3 - g.a ** 3);
     const stateHot = { T: maxTg, N, tauLumped, Tseal: p.T_seal };
     const modes = naturalModes(p, stateHot);
     const ring = [];
-    const maxJump = jumps.reduce((m, j) => Math.max(m, Math.abs(j.dP)), 0);
     for (const m of modes) {
       if (m.domain !== "acoustic") continue;
       const wn = 2 * Math.PI * m.f;
-      let amp = 0, unit = "", tau = m.Q ? 2 * m.Q / wn : null, what = "";
-      if (m.name.indexOf("gas l=0") === 0) {
-        const x = m.name.indexOf("n=1") > 0 ? 4.4934 : 7.7253;
-        const kap = overlapRadial(g, x).kappa;
-        amp = (HHO.gamma - 1) * Math.abs(kap) * ETA.gas * maxJump / g.V / wn; unit = "Pa"; what = "pressure ring (centre-weighted heating) [est]";
-      } else if (m.name.indexOf("gas") === 0) { amp = 0; unit = "Pa"; what = "not driven: radially symmetric source (l>0 needs asymmetry)"; }
-      else if (m.name.indexOf("0S0") >= 0 || m.name.indexOf("l=0") >= 0 || m.name.indexOf("breathing") >= 0) {
-        const dpdot = (HHO.gamma - 1) * ETA.gas * maxJump / g.V;  // jump in dp/dt of bulk gas pressure
-        amp = sigOverP * dpdot / wn; unit = "Pa hoop"; what = "shell breathing ring from bulk-pressure kink [est]";
-      } else { amp = 0; unit = "Pa"; what = "not driven by a symmetric source (l>0)"; }
-      ring.push({ name: m.name, f: m.f, Q: m.Q, tau, amp, unit, what });
+      ring.push({ name: m.name, f: m.f, Q: m.Q, tau: m.Q ? 2 * m.Q / wn : null, amp: 0, unit: m.name.indexOf("gas") === 0 ? "Pa" : "Pa hoop",
+        what: "not driven: no drive mechanism defined (electrodes removed 2026-10-19; drive method open)" });
     }
     const p_seal = N * kB * p.T_seal / g.V;
     const flags = [];
@@ -256,11 +210,10 @@
       else if (C >= AUTOIGN_C[0] - 50) flags.push(`${nm} ${C.toFixed(0)} C is APPROACHING HHO autoignition (~${AUTOIGN_C[0]}-${AUTOIGN_C[1]} C)`);
     }
     reg.flags.forEach(f => flags.push(f));
-    if (reg.noForm) { /* already flagged */ } else if (!isFinite(Vb)) flags.push("fill is left of the Paschen curve for this gap: no breakdown at any voltage in this model");
-    else if (g.share * p.V_amp < Vb) { const iw = ionisationWindow(p); flags.push(`no ionisation: peak gas voltage ${(g.share * p.V_amp).toFixed(0)} V < knee ${Vb.toFixed(0)} V` + (iw.empty ? ' (no fill ionises at this amplitude)' : ` (ionising fills at this amplitude: ${iw.lo_Torr.toPrecision(4)}–${iw.hi_Torr.toPrecision(4)} Torr)`)); }
+    flags.push(NO_DRIVE);
     return {
-      inputs: p, T_amb: Ta, geom: g, N, n, rho, p_seal, Vb, Vb_static: Vb0, regime: reg, qz_sound: Object.assign({ key: QZ_SEL }, QZ_SOUND[QZ_SEL]), kneeFill_Torr: kneeFill_Torr(g.gap), cycle_s: T,
-      E_dis: Edis, E_gas: Egas, E_wall: Ewall, E_opt: Eopt, Q_tr: Qtr, jumps, photons_Ha_equiv: Eopt / (6.62607015e-34 * C0 / 656.3e-9),
+      inputs: p, T_amb: Ta, geom: g, N, n, rho, p_seal, drive: NO_DRIVE, regime: reg, qz_sound: Object.assign({ key: QZ_SEL }, QZ_SOUND[QZ_SEL]), cycle_s: T,
+      E_dis: Edis, E_gas: Egas, E_wall: Ewall, E_opt: Eopt, photons_Ha_equiv: Eopt / (6.62607015e-34 * C0 / 656.3e-9),
       maxTg, maxTw, dTg: maxThG, dTw: maxThW, p_max: N * kB * maxTg / g.V, c_seal: cHHO(p.T_seal), c_max: cHHO(maxTg),
       sigma_fill: sigOverP * p_seal, sigma_peak_static: sigOverP * N * kB * maxTg / g.V, uOverP, tauLumped, modes, ring, flags, tr,
       chem: { n_diss: nDiss, n_water: nWater, E_release: Echem, frac_converted: nWater / (2 * N / 3), knee: "not defined" },
@@ -268,33 +221,30 @@
     };
   }
 
-  // drive-frequency regime flags (v0.3) [calc thresholds; drift velocities est]
+  // drive-frequency regime flags (v0.3) [calc thresholds]; the gap-based breakdown-formation flags were removed with the electrodes
   function regime(f, g) {
     const fl = [], fEM = C0 * 2.0 / (2 * Math.PI * g.b * Math.sqrt(QZ.eps)), fQS = C0 / (10 * 2 * g.b * Math.sqrt(QZ.eps));
-    const tauE = Math.log(1 + 1 / PASCHEN.gse) * g.gap / FORM.vde, tauI = g.gap / FORM.vdi, half = 0.5 / f, lam = C0 / f;
-    let noForm = false;
+    const lam = C0 / f;
     if (f >= fEM) fl.push(`quasi-static model INVALID: f ${fmtHz(f)} ≥ first dielectric-sphere EM resonance ~${fmtHz(fEM)} [est]; the sphere is ≥ a wavelength (λ0 ${fmtL(lam)}) and fields are no longer lumped`);
     else if (f >= fQS) fl.push(`quasi-static model degrading: OD·√εr > λ/10 above ~${fmtHz(fQS)} (EM resonance ~${fmtHz(fEM)}) [est]`);
-    if (half < tauE) { noForm = true; fl.push(`one cycle (${fmtS(1 / f)}) is shorter than the breakdown formation time: half-cycle ${fmtS(half)} < electron-avalanche time ~${fmtS(tauE)} = ln(1+1/γ)·gap/v_e (v_e 1e5 m/s [est]) → no discharge forms in this model`); }
-    else if (half < tauI) fl.push(`half-cycle ${fmtS(half)} < Townsend ion-feedback time ~${fmtS(tauI)} (gap/v_i, v_i 2e3 m/s [est]): the static Paschen knee is not reached in one cycle; breakdown would need overvoltage/streamer (model still uses the static knee)`);
     const lamv = lam;
-    if (lamv >= VIS[0] && lamv <= VIS[1]) fl.push(`OPTICAL BAND: drive λ ${fmtL(lamv)} is visible light — the drive IS light; the circuit/DBD drive model does not apply`);
-    else if (lamv < VIS[0]) fl.push(`drive λ ${fmtL(lamv)} is ultraviolet light — the circuit/DBD drive model does not apply`);
-    else if (f >= 3e11) fl.push(`drive λ ${fmtL(lamv)} is infrared radiation (>300 GHz) — the circuit/DBD drive model does not apply`);
+    if (lamv >= VIS[0] && lamv <= VIS[1]) fl.push(`OPTICAL BAND: drive λ ${fmtL(lamv)} is visible light — the drive IS light; the lumped quasi-static field picture does not apply`);
+    else if (lamv < VIS[0]) fl.push(`drive λ ${fmtL(lamv)} is ultraviolet light — the lumped quasi-static field picture does not apply`);
+    else if (f >= 3e11) fl.push(`drive λ ${fmtL(lamv)} is infrared radiation (>300 GHz) — the lumped quasi-static field picture does not apply`);
     BALMER.forEach(([n, l]) => { if (Math.abs(lamv - l) / l < 0.01) fl.push(`drive is within 1% of Balmer ${n} ${(l * 1e9).toFixed(2)} nm`); });
-    return { flags: fl, fEM, fQS, tauE, tauI, noForm, lambda0: lam };
+    return { flags: fl, fEM, fQS, lambda0: lam };
   }
   const fmtHz = f => f >= 1e15 ? (f / 1e15).toPrecision(3) + " PHz" : f >= 1e12 ? (f / 1e12).toPrecision(3) + " THz" : f >= 1e9 ? (f / 1e9).toPrecision(3) + " GHz" : f >= 1e6 ? (f / 1e6).toPrecision(3) + " MHz" : f >= 1e3 ? (f / 1e3).toPrecision(3) + " kHz" : f.toPrecision(3) + " Hz";
   const fmtS = t => t >= 1e-3 ? (t * 1e3).toPrecision(3) + " ms" : t >= 1e-6 ? (t * 1e6).toPrecision(3) + " µs" : t >= 1e-9 ? (t * 1e9).toPrecision(3) + " ns" : t >= 1e-12 ? (t * 1e12).toPrecision(3) + " ps" : (t * 1e15).toPrecision(3) + " fs";
   const fmtL = l => l >= 1 ? l.toPrecision(3) + " m" : l >= 1e-3 ? (l * 1e3).toPrecision(3) + " mm" : l >= 1e-6 ? (l * 1e6).toPrecision(3) + " µm" : (l * 1e9).toPrecision(3) + " nm";
   function sweep(p, key, values, opts) {
     return values.map(v => { const q = Object.assign({}, p); q[key] = v; const r = run(q, Object.assign({ ncyc: 400, nlog: 80 }, opts || {}));
-      return r.error ? { x: v, error: r.error } : { x: v, E_dis: r.E_dis, dTg: r.dTg, dTw: r.dTw, Vb: r.Vb, p_max: r.p_max,
+      return r.error ? { x: v, error: r.error } : { x: v, E_dis: r.E_dis, dTg: r.dTg, dTw: r.dTw, p_max: r.p_max,
         ringGas: (r.ring.find(z => z.name.indexOf("gas l=0 n=1") === 0) || {}).amp || 0,
         ringShell: (r.ring.find(z => z.what.indexOf("shell breathing") === 0) || {}).amp || 0, Echem: r.chem.E_release, flags: r.flags, fgas: r.modes[2].f,
-        E_opt: r.E_opt, Vgas: r.geom.share * r.inputs.V_amp, share: r.geom.share, kneeFill: r.kneeFill_Torr, modes: r.modes.map(m => ({ domain: m.domain, name: m.name, f: m.f })) }; });
+        E_opt: r.E_opt, drive: r.drive, modes: r.modes.map(m => ({ domain: m.domain, name: m.name, f: m.f })) }; });
   }
   const logspace = (a, b, n) => Array.from({ length: n }, (_, i) => a * Math.pow(b / a, i / (n - 1)));
-  const api = { QZ_SOUND, setQuartzSound, shellRadialModes, regime, BALMER, VIS, FORM, fmtHz, CH, run, sweep, logspace, naturalModes, paschenV, kneeFill_Torr, ionisationWindow, cHHO, geometry, ETA, HHO, QZ, PASCHEN, AUTOIGN_C, TORR };
+  const api = { QZ_SOUND, setQuartzSound, shellRadialModes, regime, BALMER, VIS, fmtHz, CH, run, sweep, logspace, naturalModes, cHHO, geometry, ETA, HHO, QZ, AUTOIGN_C, TORR, NO_DRIVE };
   if (typeof module !== "undefined" && module.exports) module.exports = api; else root.DriveModel = api;
 })(typeof window !== "undefined" ? window : this);
diff --git a/drive_model_output.txt b/drive_model_output.txt
index 8a1f140..45767d3 100644
--- a/drive_model_output.txt
+++ b/drive_model_output.txt
@@ -1,36 +1,39 @@
-v0 coupled single-cycle drive model - ESTIMATED PHYSICS. Geometry 1 mm ID x 2 mm OD bare crystal quartz, HHO 2:1, sealed at 293.15 K (initial/ambient).
-Example inputs only (fill, amplitude and frequency are OPEN user inputs; nothing here is a chosen design value).
+v0 coupled single-cycle drive model - ESTIMATED PHYSICS. Geometry 1 mm ID x 2 mm OD bare crystal quartz, HHO 2:1, sealed at 293.15 K.
+Example inputs only (fill, ambient and frequency are OPEN user inputs; nothing here is a chosen design value).
+DRIVE: no drive mechanism defined (electrodes removed 2026-10-19; drive method open): no breakdown, no deposited energy, no discharge heating or chemistry, no acoustic ring-down.
+Removed with the drive [retired 2026-10-19]: breakdown knee, ionisation window, energy per cycle, discharge heating, discharge chemistry, acoustic ring amplitudes.
 
-DBD geometry [est]: r0 50 um, gas gap 0.45 mm, C_gas 6.181e-15 F, C_barrier 5.007e-13 F, gas share 98.8 %; Paschen-min fill for this gap 22.2 Torr
 HHO c(T) = sqrt(1.4 R T / 0.012011): 293 K 532.9 m/s, 400 K 622.6, 773 K 865.5 m/s
 
-fill 22 Torr (N 3.794e+14), 600 V, f 1000 Hz (cycle 1.000e-3 s): knee 332 V | E/cycle 1.316e-7 J | dT_gas 2.394e-1 K | dT_wall 4.323e-4 K | p_max 2.935e+3 Pa | gas l0 762.7 kHz Q 12.7 | ring gas 4.045e-1 Pa, shell 1.108e-2 Pa | corners 2.00e+4 Hz, 20.3 Hz, 0.0102 Hz | chem heat 8.839e-9 J, H2 converted 8.701e-3 % (knee: not defined) | flags: none
-fill 22 Torr (N 3.794e+14), 600 V, f 20 Hz (cycle 5.000e-2 s): knee 332 V | E/cycle 1.316e-7 J | dT_gas 5.049e-3 K | dT_wall 6.177e-5 K | p_max 2.933e+3 Pa | gas l0 762.4 kHz Q 12.7 | ring gas 8.093e-3 Pa, shell 2.215e-4 Pa | corners 2.00e+4 Hz, 20.3 Hz, 0.0102 Hz | chem heat 8.839e-9 J, H2 converted 8.701e-3 % (knee: not defined) | flags: none
-fill 22 Torr (N 3.794e+14), 600 V, f 20000 Hz (cycle 5.000e-5 s): knee 332 V | E/cycle 1.316e-7 J | dT_gas 2.431e+0 K | dT_wall 7.771e-4 K | p_max 2.957e+3 Pa | gas l0 765.5 kHz Q 12.7 | ring gas 8.060e+0 Pa, shell 2.215e-1 Pa | corners 2.01e+4 Hz, 20.2 Hz, 0.0102 Hz | chem heat 8.839e-9 J, H2 converted 8.701e-3 % (knee: not defined) | flags: none
-fill 10 Torr (N 1.725e+14), 600 V, f 1000 Hz (cycle 1.000e-3 s): knee 743 V | E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | p_max 1.333e+3 Pa | gas l0 762.4 kHz Q 6.6 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 4.40e+4 Hz, 20.3 Hz, 0.0102 Hz | chem heat 0.000e+0 J, H2 converted 0.000e+0 % (knee: not defined) | flags: no ionisation: peak gas voltage 593 V < knee 743 V (ionising fills at this amplitude: 10.71–98.95 Torr)
-fill 100 Torr (N 1.725e+15), 2000 V, f 1000 Hz (cycle 1.000e-3 s): knee 596 V | E/cycle 1.487e-6 J | dT_gas 1.425e+0 K | dT_wall 3.725e-3 K | p_max 1.340e+4 Pa | gas l0 764.2 kHz Q 40.8 | ring gas 3.842e+0 Pa, shell 1.054e-1 Pa | corners 4.41e+3 Hz, 20.2 Hz, 0.0102 Hz | chem heat 9.991e-8 J, H2 converted 2.164e-2 % (knee: not defined) | flags: none
-fill 760 Torr (N 1.311e+16), 5000 V, f 1000 Hz (cycle 1.000e-3 s): knee 2504 V | E/cycle 9.272e-6 J | dT_gas 6.442e+0 K | dT_wall 2.101e-2 K | p_max 1.036e+5 Pa | gas l0 770.7 kHz Q 156.0 | ring gas 1.021e+1 Pa, shell 2.827e-1 Pa | corners 588 Hz, 19.9 Hz, 0.0102 Hz | chem heat 6.227e-7 J, H2 converted 1.775e-2 % (knee: not defined) | flags: none
+fill 22 Torr (N 3.794e+14), f 1000 Hz (cycle 1.000e-3 s), ambient 293.15 K: E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | gas theta at t_end 0.000e+0 K | p_max 2.933e+3 Pa | gas l0 762.4 kHz Q 12.7 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 2.00e+4 Hz, 20.3 Hz, 0.0102 Hz | chem heat 0.000e+0 J
+fill 22 Torr (N 3.794e+14), f 20 Hz (cycle 5.000e-2 s), ambient 293.15 K: E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | gas theta at t_end 0.000e+0 K | p_max 2.933e+3 Pa | gas l0 762.4 kHz Q 12.7 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 2.00e+4 Hz, 20.3 Hz, 0.0102 Hz | chem heat 0.000e+0 J
+fill 22 Torr (N 3.794e+14), f 20000 Hz (cycle 5.000e-5 s), ambient 293.15 K: E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | gas theta at t_end 0.000e+0 K | p_max 2.933e+3 Pa | gas l0 762.4 kHz Q 12.7 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 2.00e+4 Hz, 20.3 Hz, 0.0102 Hz | chem heat 0.000e+0 J
+fill 10 Torr (N 1.725e+14), f 1000 Hz (cycle 1.000e-3 s), ambient 293.15 K: E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | gas theta at t_end 0.000e+0 K | p_max 1.333e+3 Pa | gas l0 762.4 kHz Q 6.6 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 4.40e+4 Hz, 20.3 Hz, 0.0102 Hz | chem heat 0.000e+0 J
+fill 100 Torr (N 1.725e+15), f 1000 Hz (cycle 1.000e-3 s), ambient 293.15 K: E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | gas theta at t_end 0.000e+0 K | p_max 1.333e+4 Pa | gas l0 762.4 kHz Q 40.8 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 4.40e+3 Hz, 20.3 Hz, 0.0102 Hz | chem heat 0.000e+0 J
+fill 760 Torr (N 1.311e+16), f 1000 Hz (cycle 1.000e-3 s), ambient 293.15 K: E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | gas theta at t_end 0.000e+0 K | p_max 1.013e+5 Pa | gas l0 762.4 kHz Q 156.5 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 579 Hz, 20.3 Hz, 0.0102 Hz | chem heat 0.000e+0 J
+fill 22 Torr (N 3.794e+14), f 1000 Hz (cycle 1.000e-3 s), ambient 303.15 K: E/cycle 0.000e+0 J | dT_gas 9.863e+0 K | dT_wall 9.863e+0 K | gas theta at t_end 9.863e+0 K | p_max 3.032e+3 Pa | gas l0 775.1 kHz Q 12.7 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 2.05e+4 Hz, 19.7 Hz, 0.0115 Hz | chem heat 0.000e+0 J
+fill 22 Torr (N 3.794e+14), f 1000 Hz (cycle 1.000e-3 s), ambient 283.15 K: E/cycle 0.000e+0 J | dT_gas 0.000e+0 K | dT_wall 0.000e+0 K | gas theta at t_end -9.841e+0 K | p_max 2.933e+3 Pa | gas l0 762.4 kHz Q 12.7 | ring gas 0.000e+0 Pa, shell 0.000e+0 Pa | corners 2.00e+4 Hz, 20.3 Hz, 0.0113 Hz | chem heat 0.000e+0 J
 
-Sweep drive f (fill 22 Torr, 600 V):
-  f 20.00 Hz: E 1.316e-7 J, dT_gas 5.041e-3 K, dT_wall 6.175e-5 K, ring gas 4.047e-3 Pa, shell 1.108e-4 Pa
-  f 63.25 Hz: E 1.316e-7 J, dT_gas 1.587e-2 K, dT_wall 1.185e-4 K, ring gas 1.280e-2 Pa, shell 3.503e-4 Pa
-  f 200.0 Hz: E 1.316e-7 J, dT_gas 4.976e-2 K, dT_wall 2.151e-4 K, ring gas 4.046e-2 Pa, shell 1.108e-3 Pa
-  f 632.5 Hz: E 1.316e-7 J, dT_gas 1.538e-1 K, dT_wall 3.612e-4 K, ring gas 1.279e-1 Pa, shell 3.503e-3 Pa
-  f 2000 Hz: E 1.316e-7 J, dT_gas 4.529e-1 K, dT_wall 5.450e-4 K, ring gas 4.043e-1 Pa, shell 1.108e-2 Pa
-  f 6325 Hz: E 1.316e-7 J, dT_gas 1.169e+0 K, dT_wall 7.030e-4 K, ring gas 1.277e+0 Pa, shell 3.503e-2 Pa
-  f 2.000e+4 Hz: E 1.316e-7 J, dT_gas 2.427e+0 K, dT_wall 7.768e-4 K, ring gas 4.030e+0 Pa, shell 1.108e-1 Pa
+Sweep drive f (fill 22 Torr):
+  f 20.00 Hz: E 0.000e+0 J, dT_gas 0.000e+0 K, dT_wall 0.000e+0 K, ring gas 0.000e+0 Pa, shell 0.000e+0 Pa
+  f 63.25 Hz: E 0.000e+0 J, dT_gas 0.000e+0 K, dT_wall 0.000e+0 K, ring gas 0.000e+0 Pa, shell 0.000e+0 Pa
+  f 200.0 Hz: E 0.000e+0 J, dT_gas 0.000e+0 K, dT_wall 0.000e+0 K, ring gas 0.000e+0 Pa, shell 0.000e+0 Pa
+  f 632.5 Hz: E 0.000e+0 J, dT_gas 0.000e+0 K, dT_wall 0.000e+0 K, ring gas 0.000e+0 Pa, shell 0.000e+0 Pa
+  f 2000 Hz: E 0.000e+0 J, dT_gas 0.000e+0 K, dT_wall 0.000e+0 K, ring gas 0.000e+0 Pa, shell 0.000e+0 Pa
+  f 6325 Hz: E 0.000e+0 J, dT_gas 0.000e+0 K, dT_wall 0.000e+0 K, ring gas 0.000e+0 Pa, shell 0.000e+0 Pa
+  f 2.000e+4 Hz: E 0.000e+0 J, dT_gas 0.000e+0 K, dT_wall 0.000e+0 K, ring gas 0.000e+0 Pa, shell 0.000e+0 Pa
 
-Sweep fill (f 1 kHz, 600 V): ionisation window (peak gas V 592.7 V = share x 600 V vs Paschen V_b, static knee) 10.71 - 98.95 Torr:
-  fill 0.100 Torr: knee inf V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 0.255 Torr: knee inf V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 0.651 Torr: knee inf V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 1.66 Torr: knee inf V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 4.24 Torr: knee inf V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 10.8 Torr: knee 579 V, E 1.173e-8 J, dT_gas 9.924e-2 K, gas l0 762.5 kHz
-  fill 27.6 Torr: knee 339 V, E 1.308e-7 J, dT_gas 2.383e-1 K, gas l0 762.7 kHz
-  fill 70.3 Torr: knee 488 V, E 7.762e-8 J, dT_gas 1.943e-1 K, gas l0 762.6 kHz
-  fill 179 Torr: knee 868 V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 458 Torr: knee 1698 V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 1.17e+3 Torr: knee 3515 V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 2.98e+3 Torr: knee 7543 V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
-  fill 7.60e+3 Torr: knee 16605 V, E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+Sweep fill (f 1 kHz):
+  fill 0.100 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 0.255 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 0.651 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 1.66 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 4.24 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 10.8 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 27.6 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 70.3 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 179 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 458 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 1.17e+3 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 2.98e+3 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
+  fill 7.60e+3 Torr: E 0.000e+0 J, dT_gas 0.000e+0 K, gas l0 762.4 kHz
diff --git a/drive_model_run.js b/drive_model_run.js
index dafaeea..974dcfc 100644
--- a/drive_model_run.js
+++ b/drive_model_run.js
@@ -3,18 +3,19 @@ const D = require("./drive_model.js");
 const shell = [{ name: "0S0 breathing (l=0)", f: 1.868e6 }, { name: "1S0-type (l=0, n=2)", f: 6.737e6 }, { name: "0S2", f: 1.243e6, tag: "calc minimal_test" }];
 const base = { ID_mm: 1, OD_mm: 2, T_seal: 293.15, shellModes: shell };   // T_amb (ambient air K) unset => ambient = T_seal
 const e = x => x.toExponential(3);
-console.log("v0 coupled single-cycle drive model - ESTIMATED PHYSICS. Geometry 1 mm ID x 2 mm OD bare crystal quartz, HHO 2:1, sealed at 293.15 K (initial/ambient).");
-console.log("Example inputs only (fill, amplitude and frequency are OPEN user inputs; nothing here is a chosen design value).\n");
-const g = D.geometry(base);
-console.log(`DBD geometry [est]: r0 50 um, gas gap ${(g.gap*1e3).toFixed(2)} mm, C_gas ${e(g.Cg)} F, C_barrier ${e(g.Cd)} F, gas share ${(g.share*100).toFixed(1)} %; Paschen-min fill for this gap ${D.kneeFill_Torr(g.gap).toFixed(1)} Torr`);
+console.log("v0 coupled single-cycle drive model - ESTIMATED PHYSICS. Geometry 1 mm ID x 2 mm OD bare crystal quartz, HHO 2:1, sealed at 293.15 K.");
+console.log("Example inputs only (fill, ambient and frequency are OPEN user inputs; nothing here is a chosen design value).");
+console.log("DRIVE: " + D.NO_DRIVE + ".");
+console.log("Removed with the drive [retired 2026-10-19]: breakdown knee, ionisation window, energy per cycle, discharge heating, discharge chemistry, acoustic ring amplitudes.\n");
 console.log(`HHO c(T) = sqrt(1.4 R T / 0.012011): 293 K ${D.cHHO(293).toFixed(1)} m/s, 400 K ${D.cHHO(400).toFixed(1)}, 773 K ${D.cHHO(773).toFixed(1)} m/s\n`);
-for (const [fill, V, f] of [[22, 600, 1000], [22, 600, 20], [22, 600, 20000], [10, 600, 1000], [100, 2000, 1000], [760, 5000, 1000]]) {
-  const r = D.run(Object.assign({}, base, { fill_Torr: fill, V_amp: V, f }));
+for (const [fill, f, Tamb] of [[22, 1000], [22, 20], [22, 20000], [10, 1000], [100, 1000], [760, 1000], [22, 1000, 303.15], [22, 1000, 283.15]]) {
+  const q = Object.assign({}, base, { fill_Torr: fill, f }); if (Tamb) q.T_amb = Tamb;
+  const r = D.run(q);
   const gm = r.modes.find(m => m.name.startsWith("gas l=0 n=1"));
-  console.log(`fill ${fill} Torr (N ${e(r.N)}), ${V} V, f ${f} Hz (cycle ${e(1/f)} s): knee ${isFinite(r.Vb)?r.Vb.toFixed(0):'inf'} V | E/cycle ${e(r.E_dis)} J | dT_gas ${e(r.dTg)} K | dT_wall ${e(r.dTw)} K | p_max ${e(r.p_max)} Pa | gas l0 ${(gm.f/1e3).toFixed(1)} kHz Q ${gm.Q.toFixed(1)} | ring gas ${e(r.ring.find(z=>z.name.startsWith('gas l=0 n=1')).amp)} Pa, shell ${e(r.ring.find(z=>z.what.startsWith('shell breathing')).amp)} Pa | corners ${r.modes.filter(m=>m.domain==='thermal').map(m=>m.f.toPrecision(3)+' Hz').join(', ')} | chem heat ${e(r.chem.E_release)} J, H2 converted ${e(r.chem.frac_converted*100)} % (knee: not defined) | flags: ${r.flags.join('; ')||'none'}`);
+  const thEnd = r.tr.Tg[r.tr.Tg.length - 1] - base.T_seal;
+  console.log(`fill ${fill} Torr (N ${e(r.N)}), f ${f} Hz (cycle ${e(1/f)} s), ambient ${r.T_amb} K: E/cycle ${e(r.E_dis)} J | dT_gas ${e(r.dTg)} K | dT_wall ${e(r.dTw)} K | gas theta at t_end ${e(thEnd)} K | p_max ${e(r.p_max)} Pa | gas l0 ${(gm.f/1e3).toFixed(1)} kHz Q ${gm.Q.toFixed(1)} | ring gas ${e(r.ring.find(z=>z.name.startsWith('gas l=0 n=1')).amp)} Pa, shell ${e(r.ring.find(z=>z.name.indexOf('0S0') >= 0).amp)} Pa | corners ${r.modes.filter(m=>m.domain==='thermal').map(m=>m.f.toPrecision(3)+' Hz').join(', ')} | chem heat ${e(r.chem.E_release)} J`);
 }
-console.log("\nSweep drive f (fill 22 Torr, 600 V):");
-D.sweep(Object.assign({}, base, { fill_Torr: 22, V_amp: 600 }), "f", D.logspace(20, 20000, 7)).forEach(p => console.log(`  f ${p.x.toPrecision(4)} Hz: E ${e(p.E_dis)} J, dT_gas ${e(p.dTg)} K, dT_wall ${e(p.dTw)} K, ring gas ${e(p.ringGas)} Pa, shell ${e(p.ringShell)} Pa`));
-const iw = D.ionisationWindow(Object.assign({}, base, { V_amp: 600 }));
-console.log(`\nSweep fill (f 1 kHz, 600 V): ionisation window (peak gas V ${iw.Vgas.toFixed(1)} V = share x 600 V vs Paschen V_b, static knee) ${iw.empty ? "empty" : iw.lo_Torr.toPrecision(4) + " - " + iw.hi_Torr.toPrecision(4) + " Torr"}:`);
-D.sweep(Object.assign({}, base, { f: 1000, V_amp: 600 }), "fill_Torr", D.logspace(0.1, 7600, 13)).forEach(p => console.log(`  fill ${p.x.toPrecision(3)} Torr: knee ${isFinite(p.Vb)?p.Vb.toFixed(0):'inf'} V, E ${e(p.E_dis)} J, dT_gas ${e(p.dTg)} K, gas l0 ${(p.fgas/1e3).toFixed(1)} kHz`));
+console.log("\nSweep drive f (fill 22 Torr):");
+D.sweep(Object.assign({}, base, { fill_Torr: 22 }), "f", D.logspace(20, 20000, 7)).forEach(p => console.log(`  f ${p.x.toPrecision(4)} Hz: E ${e(p.E_dis)} J, dT_gas ${e(p.dTg)} K, dT_wall ${e(p.dTw)} K, ring gas ${e(p.ringGas)} Pa, shell ${e(p.ringShell)} Pa`));
+console.log("\nSweep fill (f 1 kHz):");
+D.sweep(Object.assign({}, base, { f: 1000 }), "fill_Torr", D.logspace(0.1, 7600, 13)).forEach(p => console.log(`  fill ${p.x.toPrecision(3)} Torr: E ${e(p.E_dis)} J, dT_gas ${e(p.dTg)} K, gas l0 ${(p.fgas/1e3).toFixed(1)} kHz`));
diff --git a/drive_ui.js b/drive_ui.js
index 9e73a1f..c9e961f 100644
--- a/drive_ui.js
+++ b/drive_ui.js
@@ -27,13 +27,12 @@
     $('dMsg').textContent = C.propagation && C.propagation.bare ? '' : 'drive model covers the bare quartz bubble only (outer layers not included)';
   };
   function params() {
-    const p = { ID_mm: +$('dID').value, OD_mm: +$('dOD').value, T_seal: +$('dTs').value, V_amp: +$('dV').value, f: parseSI($('dF').value),
+    const p = { ID_mm: +$('dID').value, OD_mm: +$('dOD').value, T_seal: +$('dTs').value, f: parseSI($('dF').value),
       shellModes: caseC ? shellModes(caseC, +$('dID').value, +$('dOD').value) : [] };
     const fill = +$('dFill').value; if ($('dFillU').value === 'torr') p.fill_Torr = fill; else p.fill_molecules = fill;
     if ($('dTa').value !== '') p.T_amb = +$('dTa').value;   // ambient air T; blank => ambient = sealing T
     const miss = [];
     if (!($('dFill').value !== '' && fill > 0)) miss.push('HHO fill amount');
-    if (!($('dV').value !== '' && p.V_amp > 0)) miss.push('drive amplitude');
     if (!($('dF').value !== '' && p.f > 0)) miss.push('drive frequency (e.g. 2.5M, 100k, 600T)');
     if (!(p.ID_mm > 0 && p.OD_mm > p.ID_mm)) miss.push('geometry (OD > ID)');
     if (!(p.T_seal > 0)) miss.push('initial (sealing) T');
@@ -51,8 +50,8 @@
   function showRegime() {
     const g = curGeom(), f = window.DRIVE_F; if (!g || !f) { $('dReg').innerHTML = ''; return; }
     const r = DM.regime(f, g);
-    $('dReg').innerHTML = (r.flags.length ? r.flags.map(x => `<div class="flag">⚠ ${x}</div>`).join('') : '<div class="ok">regime: quasi-static circuit model valid; half-cycle longer than the breakdown formation times [est]</div>') +
-      `<div class="small">limits for this geometry [est]: quasi-static to ~${fmtF(r.fQS)} (OD·√εr = λ/10); EM resonance ~${fmtF(r.fEM)}; avalanche formation ~${fmtT(r.tauE)} (no discharge above ~${fmtF(0.5 / r.tauE)}); Townsend ion feedback ~${fmtT(r.tauI)} (static knee needs f < ~${fmtF(0.5 / r.tauI)}); visible band 400–789 THz</div>`;
+    $('dReg').innerHTML = (r.flags.length ? r.flags.map(x => `<div class="flag">⚠ ${x}</div>`).join('') : '<div class="ok">regime: quasi-static field picture valid at this f [est]</div>') +
+      `<div class="small">limits for this geometry [est]: quasi-static to ~${fmtF(r.fQS)} (OD·√εr = λ/10); EM resonance ~${fmtF(r.fEM)}; visible band 400–789 THz</div>`;
   }
   // frequency axis under the slider: decade ticks, natural acoustic modes, Balmer lines + visible band, regime limits
   function drawFaxis() {
@@ -72,7 +71,7 @@
       g.fillStyle = DC.acoustic; const ac = ms.filter(m => m.domain === 'acoustic').map(m => m.f);
       if (ac.length) g.fillText('acoustic modes', X(Math.min(...ac)) + 2, 28);
       const r = DM.regime(1e6, geo);
-      [[r.fQS, 'QS λ/10', '#ff8a7a'], [r.fEM, 'EM res', '#ff4fd8'], [0.5 / r.tauE, 'no-form', '#ffd27a']].forEach(([f, t, c], i) => { if (f > FMIN && f < FMAX) { const x = X(f); g.strokeStyle = c; g.setLineDash([3, 2]); g.beginPath(); g.moveTo(x, 12); g.lineTo(x, H - 12); g.stroke(); g.setLineDash([]); g.fillStyle = c; g.fillText(t, x + 2, 38 - i * 9 + 9); } });
+      [[r.fQS, 'QS λ/10', '#ff8a7a'], [r.fEM, 'EM res', '#ff4fd8']].forEach(([f, t, c], i) => { if (f > FMIN && f < FMAX) { const x = X(f); g.strokeStyle = c; g.setLineDash([3, 2]); g.beginPath(); g.moveTo(x, 12); g.lineTo(x, H - 12); g.stroke(); g.setLineDash([]); g.fillStyle = c; g.fillText(t, x + 2, 38 - i * 9 + 9); } });
     }
     g.strokeStyle = '#9aa6bd'; g.fillStyle = '#9aa6bd';
     for (let e = 5; e <= 15; e++) { const x = X(Math.pow(10, e)); g.beginPath(); g.moveTo(x, H - 12); g.lineTo(x, H - 7); g.stroke(); const lab = ['100k', '1M', '10M', '100M', '1G', '10G', '100G', '1T', '10T', '100T', '1000T'][e - 5]; g.fillText(lab, Math.min(x - 8, W - 28), H - 1); }
@@ -116,14 +115,11 @@
     // A: V and V_gas over the cycle
     const iC = tr.t.findIndex(t => t > 1.1 * T); const nC = iC < 0 ? tr.t.length : iC;
     const tC = tr.t.slice(0, nC), XA = t => L + wP * t / (1.1 * T);
-    const vmax = Math.max(r.inputs.V_amp, isFinite(r.Vb) ? r.Vb : 0) * 1.1, YA = v => 8 + 42 - 42 * v / vmax;
-    axes(g, L, 8, wP, 84, 'drive V(t) (grey), gas-gap V (magenta), ±knee (dashed)  — one cycle = ' + fmtT(T));
-    line(g, tC, tr.V.slice(0, nC), XA, YA, '#8f98aa'); line(g, tC, tr.Vg.slice(0, nC), XA, YA, DC.electric);
-    if (isFinite(r.Vb)) { line(g, [0, 1.1 * T], [r.Vb, r.Vb], XA, YA, '#ffd27a', [4, 3]); line(g, [0, 1.1 * T], [-r.Vb, -r.Vb], XA, YA, '#ffd27a', [4, 3]); }
-    g.fillStyle = '#9aa6bd'; g.fillText(vmax.toFixed(0) + ' V', 4, 14); g.fillText('0', 30, YA(0) + 3); g.fillText('-' + vmax.toFixed(0), 4, 90);
+    axes(g, L, 8, wP, 84, 'drive: ' + DM.NO_DRIVE + ' — one cycle = ' + fmtT(T));
+    g.fillStyle = '#ffd27a'; g.fillText('no drive mechanism defined [retired 2026-10-19: drive voltage, gas-gap voltage and knee traces]', L + 6, 50);
     // B: discharge power
     const Pm = Math.max(...tr.P.slice(0, nC), 1e-30), YB = v => 100 + 84 - 76 * v / Pm;
-    axes(g, L, 100, wP, 84, 'discharge power (Manley-type, from rest) [est] — E/cycle ' + e3(r.E_dis) + ' J; light ' + e3(r.E_opt) + ' J');
+    axes(g, L, 100, wP, 84, 'deposited drive power (none: no drive mechanism defined) — E/cycle ' + e3(r.E_dis) + ' J; light ' + e3(r.E_opt) + ' J');
     line(g, tC, tr.P.slice(0, nC), XA, YB, DC.optical); g.fillStyle = '#9aa6bd'; g.fillText(e3(Pm) + ' W', 2, 112); g.fillText('t →', W - 30, 196);
     // C: temperatures vs log time
     const t0 = tr.t[0], t1 = tr.t[tr.t.length - 1], XC = t => L + wP * Math.log(t / t0) / Math.log(t1 / t0);
@@ -157,17 +153,13 @@
       ['ringGas', 'gas l=0 ring p', 'Pa', DC.acoustic], ['ringShell', 'shell 0S0 ring σ', 'Pa', '#a0e8ff'], ['Echem', 'chemical heat/cycle', 'J', DC.chemical]];
     g.strokeStyle = '#2a3244'; g.strokeRect(L, T, W - L - Rr, H - T - B);
     g.fillStyle = '#9aa6bd'; g.font = '10px system-ui';
-    g.fillText(kind === 'f' ? 'response vs drive frequency ' + fmtF(x0) + '–' + fmtF(x1) + ' (' + pts.length + ' pts ; each curve / its max; log x) at the entered fill & amplitude' : 'response vs HHO fill (Torr at sealing; log x) at the entered f & amplitude', L, 12);
+    g.fillText(kind === 'f' ? 'response vs drive frequency ' + fmtF(x0) + '–' + fmtF(x1) + ' (' + pts.length + ' pts ; each curve / its max; log x) at the entered fill' : 'response vs HHO fill (Torr at sealing; log x) at the entered f', L, 12);
     series.forEach(([k, n, u, c], i) => {
       const mx = Math.max(...ok.map(p => p[k]), 0); const Y = v => T + (H - T - B) * (1 - (mx > 0 ? v / mx : 0));
       line(g, ok.map(p => p.x), ok.map(p => p[k]), X, Y, c); g.fillStyle = c; g.fillText(n + ' max ' + e3(mx) + ' ' + u, L + 4 + (i % 3) * 165, T + 12 + Math.floor(i / 3) * 12);
     });
-    if (kind === 'fill') { // knee curve vs available gas voltage
-      const vg = base.share * base.V_amp, vb = ok.map(p => isFinite(p.Vb) ? p.Vb : NaN), mx = Math.max(vg, ...vb.filter(isFinite)) * 1.05;
-      const Y = v => T + (H - T - B) * (1 - v / mx);
-      line(g, ok.map(p => p.x), vb, X, Y, '#ffd27a', [4, 3]); line(g, [x0, x1], [vg, vg], X, Y, '#ff4fd8', [2, 3]);
-      g.fillStyle = '#ffd27a'; g.fillText('dashed: ionisation knee V_b(fill) [HHO, est]; magenta: peak gas V', L + 4, H - B - 6);
-      const kf = base.kneeFill; if (kf > x0 && kf < x1) { g.strokeStyle = '#ffd27a'; g.beginPath(); g.moveTo(X(kf), T); g.lineTo(X(kf), H - B); g.stroke(); g.fillText('Paschen-min fill ' + kf.toPrecision(3) + ' Torr', X(kf) + 3, H - B - 18); }
+    if (kind === 'fill') {
+      g.fillStyle = '#ffd27a'; g.fillText('no drive mechanism defined [retired 2026-10-19: breakdown knee and gas-voltage curves]', L + 4, H - B - 6);
     } else {
       (base.modes || []).forEach(m => { if (m.f >= x0 && m.f <= x1) { g.strokeStyle = DC[m.domain]; g.setLineDash([2, 3]); g.beginPath(); g.moveTo(X(m.f), T); g.lineTo(X(m.f), H - B); g.stroke(); g.setLineDash([]); g.fillStyle = DC[m.domain]; g.fillText(m.name.split(' [')[0].split(' 1/')[0], X(m.f) + 2, H - B - 8); } });
       const ac = (base.modes || []).filter(m => m.domain === 'acoustic').map(m => m.f);
@@ -178,28 +170,22 @@
     const nflag = ok.filter(p => p.flags.some(f => f.indexOf('autoignition') >= 0)).length;
     if (nflag) { g.fillStyle = '#ff8a7a'; g.fillText('⚠ ' + nflag + ' sweep points approach/enter HHO autoignition (~500–585 C)', L, H - 4); }
   }
-  // ID / OD sweeps: per-domain response (top) and natural modes vs geometry with the drive f and knee marked (bottom)
+  // ID / OD sweeps: per-domain response (top) and natural modes vs geometry with the drive f marked (bottom)
   function drawGeomSweep(kind, pts, ok, base) {
     const cv = $('dSw'), g = cv.getContext('2d'), W = cv.width, H = cv.height;
     const L = 46, Rr = 10, x0 = ok[0].x, x1 = ok[ok.length - 1].x, X = x => L + (W - L - Rr) * Math.log(x / x0) / Math.log(x1 / x0);
     g.font = '10px system-ui'; g.fillStyle = '#9aa6bd';
-    g.fillText(`response vs ${kind} ${x0}–${x1} mm (${pts.length} pts; ${pts.length - ok.length} invalid: OD ≤ ID or ID ≤ electrode) at the entered fill, amplitude & f`, 4, 11);
+    g.fillText(`response vs ${kind} ${x0}–${x1} mm (${pts.length} pts; ${pts.length - ok.length} invalid: OD ≤ ID) at the entered fill & f`, 4, 11);
     // top panel: per-domain response (each / its max)
     const T1 = 18, H1 = 112;
     g.strokeStyle = '#2a3244'; g.strokeRect(L, T1, W - L - Rr, H1);
     const series = [['E_opt', 'optical: light/cycle', 'J', DC.optical], ['ringGas', 'acoustic: gas l=0 ring', 'Pa', DC.acoustic], ['ringShell', 'acoustic: shell 0S0 ring', 'Pa', '#a0e8ff'],
-      ['Vgas', 'electric: peak gas V', 'V', DC.electric], ['dTg', 'thermal: ΔT_gas', 'K', DC.thermal], ['Echem', 'chemical: heat/cycle', 'J', DC.chemical]];
+      ['dTg', 'thermal: ΔT_gas', 'K', DC.thermal], ['Echem', 'chemical: heat/cycle', 'J', DC.chemical]];
     series.forEach(([k, n, u, c], i) => {
       const mx = Math.max(...ok.map(p => p[k]), 0), Y = v => T1 + H1 * (1 - (mx > 0 ? v / mx : 0));
       line(g, ok.map(p => p.x), ok.map(p => p[k]), X, Y, c); g.fillStyle = c; g.fillText(n + ' max ' + e3(mx) + ' ' + u, L + 4 + (i % 3) * 165, T1 + 11 + Math.floor(i / 3) * 11);
     });
     g.fillStyle = DC.magnetic; g.fillText('magnetic: B = 0 for the symmetric radial drive (all points)', L + 4, T1 + H1 - 4);
-    // knee: V_b vs geometry (dashed) against the peak gas voltage
-    const vb = ok.map(p => isFinite(p.Vb) ? p.Vb : NaN), vmx = Math.max(...ok.map(p => p.Vgas), ...vb.filter(isFinite), 1) * 1.05, YV = v => T1 + H1 * (1 - v / vmx);
-    line(g, ok.map(p => p.x), vb, X, YV, '#ffd27a', [4, 3]);
-    let imin = -1; vb.forEach((v, i) => { if (isFinite(v) && (imin < 0 || v < vb[imin])) imin = i; });
-    if (imin >= 0) { const x = X(ok[imin].x); g.fillStyle = '#ffd27a'; g.beginPath(); g.arc(x, YV(vb[imin]), 3.5, 0, 7); g.fill(); g.fillText('knee min ' + vb[imin].toFixed(0) + ' V @ ' + kind + ' ' + ok[imin].x.toPrecision(3), Math.min(x + 4, W - 150), YV(vb[imin]) - 4); }
-    for (let i = 1; i < ok.length; i++) { const a = ok[i - 1].Vgas - (vb[i - 1] || Infinity), b = ok[i].Vgas - (vb[i] || Infinity); if (isFinite(a) && isFinite(b) && a * b < 0 || (isFinite(a) !== isFinite(b))) { const x = X(ok[i].x); g.strokeStyle = '#ffd27a'; g.beginPath(); g.moveTo(x, T1); g.lineTo(x, T1 + H1); g.stroke(); g.fillStyle = '#ffd27a'; g.fillText('ionisation on/off', x + 2, T1 + H1 - 14); } }
     // bottom panel: natural modes vs geometry (log f)
     const T2 = T1 + H1 + 8, H2 = H - T2 - 16;
     g.strokeStyle = '#2a3244'; g.strokeRect(L, T2, W - L - Rr, H2);
@@ -222,19 +208,18 @@
     const f293 = 4.4934 * DM.cHHO(r.inputs.T_seal) / (2 * Math.PI * r.geom.a);
     const rows = [
       ['Fill (input)', `${e3(r.N)} HHO molecules (${e3(r.N * 2 / 3)} H2 + ${e3(r.N / 3)} O2); n ${e3(r.n)} /m³ (fixed); sealed p ${e3(r.p_seal)} Pa = ${e3(r.p_seal / DM.TORR)} Torr at ${r.inputs.T_seal} K (initial); ambient ${r.T_amb} K`],
-      ['Ionisation knee (computed)', isFinite(r.Vb) ? `${r.Vb.toFixed(0)} V across the ${(r.geom.gap * 1e3).toFixed(2)} mm gas gap (HHO Paschen [est, anchored to lit H2/O2 minima]); gas takes ${(r.geom.share * 100).toFixed(1)} % of applied V; Paschen-min fill for this gap ${r.kneeFill_Torr.toPrecision(3)} Torr. Depends on n·d, so heating at fixed N, V leaves it unchanged to first order. O2 is electronegative (attachment raises V_b, makes the discharge filamentary; O⁻+H2 detachment partly offsets) [est, qualitative]` : 'left of the Paschen curve: no breakdown'],
-      ['Discharge (computed)', `E/cycle ${e3(r.E_dis)} J (gas ${e3(r.E_gas)}, wall ${e3(r.E_wall)}, light ${e3(r.E_opt)} ≈ ${e3(r.photons_Ha_equiv)} Hα-equivalent photons) [partition est]; charge moved ${e3(r.Q_tr)} C; chemical energy stored in the fill ${e3(r.chem_energy_J)} J [lit ΔH]`],
+      ['Drive (none defined)', `${r.drive} [retired 2026-10-19: breakdown knee, gas-gap voltage, charge transfer]; E/cycle ${e3(r.E_dis)} J; chemical energy stored in the fill ${e3(r.chem_energy_J)} J [lit ΔH]`],
       ['Gas state (computed)', `T_gas peak ${r.maxTg.toFixed(3)} K (ΔT ${e3(r.dTg)} K); p peak ${e3(r.p_max)} Pa; c ${r.c_seal.toFixed(1)} → ${r.c_max.toFixed(1)} m/s; gas l=0 mode ${fmtF(f293)} → ${fmtF(gm.f)} (Q ${e3(gm.Q)} [est])`],
       ['Chemical (computed; knee: not defined)', `dissociated ${e3(r.chem.n_diss)} H2, formed ${e3(r.chem.n_water)} H2O (${e3(r.chem.frac_converted * 100)} % of the H2 converted this cycle); heat released ${e3(r.chem.E_release)} J fed to the gas; D0(H2) 4.478 eV, ΔH 241.8 kJ/mol H2O [lit]; dissociation share 0.2, chain 1, D_H [placeholders]`],
-      ['Drive regime (computed)', (r.regime.flags.length ? r.regime.flags.join('; ') : 'quasi-static circuit model valid') + ` — λ0 ${(r.regime.lambda0).toPrecision(3)} m; EM resonance ~${fmtF(r.regime.fEM)}; avalanche formation ~${fmtT(r.regime.tauE)}, ion feedback ~${fmtT(r.regime.tauI)} [est]`],
+      ['Drive regime (computed)', (r.regime.flags.length ? r.regime.flags.join('; ') : 'quasi-static field picture valid') + ` — λ0 ${(r.regime.lambda0).toPrecision(3)} m; EM resonance ~${fmtF(r.regime.fEM)} [est]`],
       ['Sound speeds (cited)', `quartz ${r.qz_sound.key}: cL ${r.qz_sound.cL}, cT ${r.qz_sound.cT} m/s (${r.qz_sound.src}); HHO c = √(γRT/M): ${r.c_seal.toFixed(1)} → ${r.c_max.toFixed(1)} m/s`],
       ['Quartz (computed)', `inner wall ΔT peak ${e3(r.dTw)} K; fill hoop stress ${e3(r.sigma_fill)} Pa → ${e3(r.sigma_peak_static)} Pa at peak gas T; still-air lumped τ ${fmtT(r.tauLumped)}`]];
     let h = '<table>' + rows.map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`).join('') + '</table>';
-    h += '<div class="small">Ring-down per mode after the single cycle (impulse approximation for f_mode ≫ f_drive) [est]:</div><table><tr><th>mode</th><th>f</th><th>Q</th><th>ring τ</th><th>amplitude</th><th></th></tr>' +
+    h += '<div class="small">Ring-down per mode after the single cycle (no drive mechanism defined, so no mode is driven):</div><table><tr><th>mode</th><th>f</th><th>Q</th><th>ring τ</th><th>amplitude</th><th></th></tr>' +
       r.ring.map(z => `<tr><td>${z.name.split(' [')[0]}</td><td>${fmtF(z.f)}</td><td>${z.Q ? e3(z.Q) : '–'}</td><td>${z.tau ? fmtT(z.tau) : '–'}</td><td>${e3(z.amp)} ${z.unit}</td><td class="small">${z.what}</td></tr>`).join('') + '</table>';
-    h += '<div class="small">Other domains: electric quasi-static (sphere EM resonance ~' + fmtF(r.modes.find(m => m.domain === 'electric').f) + ' [est]); magnetic B = 0 by symmetry of the radial current; optical follows the discharge power within ~10 ns [est]; thermal corners: ' +
+    h += '<div class="small">Other domains: electric quasi-static (sphere EM resonance ~' + fmtF(r.modes.find(m => m.domain === 'electric').f) + ' [est]); magnetic B = 0 (no drive); optical: no source without a drive; thermal corners: ' +
       r.modes.filter(m => m.domain === 'thermal').map(m => fmtF(m.f)).join(', ') + '.</div>';
-    h += r.flags.length ? r.flags.map(f => `<div class="flag">⚠ ${f}</div>`).join('') : '<div class="ok">No autoignition / knee flags for this single cycle.</div>';
+    h += r.flags.length ? r.flags.map(f => `<div class="flag">⚠ ${f}</div>`).join('') : '<div class="ok">No autoignition flags for this single cycle.</div>';
     $('dOut').innerHTML = h;
   }
   function runOne() {
@@ -253,8 +238,7 @@
     if (!(np >= 2 && np <= 200)) need.push('point count 2–200');
     if (need.length) { $('dMsg').textContent = 'enter: ' + need.join(', '); return; }
     $('dMsg').textContent = '';
-    const g = DM.geometry(Object.assign({}, p, { ID_mm: p.ID_mm > 0 ? p.ID_mm : 1, OD_mm: p.OD_mm > p.ID_mm ? p.OD_mm : 2 * (p.ID_mm || 1) }));
-    let pts, base = { share: g.share, V_amp: p.V_amp, kneeFill: DM.kneeFill_Torr(g.gap) };
+    let pts, base = {};
     if (kind === 'f') {
       pts = DM.sweep(p, 'f', DM.logspace(lo, hi, np));
       const r0 = DM.run(Object.assign({}, p, { f: p.f > 0 ? p.f : lo }), { ncyc: 200, nlog: 60 }); base.modes = r0.error ? [] : r0.modes; base.f = p.f > 0 ? p.f : null;
diff --git a/harness/README.md b/harness/README.md
index 4bcd6f8..38b2feb 100644
--- a/harness/README.md
+++ b/harness/README.md
@@ -5,7 +5,7 @@
 | `dial.yml` | Granularity dial (`shallow` scouting / `deep` validating): models, `max_tokens` caps, diff caps, calls per review, audit interval |
 | `retired.txt` | Retired items + regexes; scanned on added diff lines before any API call (free) and given to every reviewer |
 | `prompts/_base.md` | Common reviewer rules + JSON verdict format |
-| `prompts/{optical,acoustic,electric,magnetic,thermal,chemical}.md` | Per-domain review focus |
+| `prompts/{optical,acoustic,electric,magnetic,thermal,chemical}.md` | Per-domain review focus. Architecture (Danny, 2026-10-19): 7 energy domains (these six + information) and 12 knees, each with its own holster = 19 holsters. **Gap:** there is no `prompts/information.md` and no `information` entry in `dial.yml` `domains:` yet; not built here. |
 | `prompts/coordinator-merge.md` | Always applied: checks Cursor's merge (the biggest single risk) |
 | `prompts/crosscheck.md` | Added in cross-check mode (reviewer gets the other's latest verdict) |
 | `prompts/_grok_source_check.md` | Grok's source-check role (web search, URLs per claim) |
@@ -47,7 +47,7 @@ reintroduced retired items. No physics sourcing (Grok) and no design audit (Clau
 
 ## Shared web-search slot (Tavily)
 
-One search slot for the whole holster: any model, Cursor or the bot can use it. Script `scripts/tavily_search.py`
+One search slot shared across all holsters (19: 12 knee + 7 energy-domain): any model, Cursor or the bot can use it. Script `scripts/tavily_search.py`
 (stdlib, `POST https://api.tavily.com/search`, Bearer auth), workflow `.github/workflows/tavily-search.yml`.
 
 - Search on its own: `gh workflow run tavily-search.yml -f query='<query>' [-f max_results=5] [-f search_depth=basic]`,
diff --git a/harness/prompts/_base.md b/harness/prompts/_base.md
index d87014f..91c6a72 100644
--- a/harness/prompts/_base.md
+++ b/harness/prompts/_base.md
@@ -1,7 +1,8 @@
 You are an independent reviewer in the Stratified Sphere "information layer" harness.
 Architecture (spec: Drive doc "Stratified Sphere — Information Layer (Harness Architecture) 2026-10-19"):
 - Cursor is the coordinator and builder. It schedules rounds, merges domain outputs and reads a granularity dial (shallow = scouting, deep = validating).
-- Six domain harnesses: optical, acoustic, electric, magnetic, thermal, chemical. They are coupled (e.g. chemical heat feeds thermal).
+- Seven energy domains: optical, acoustic, electric, magnetic, thermal, chemical and information, plus 12 knees. Each energy domain and each knee has its own holster (19 in total). The domains are coupled (e.g. chemical heat feeds thermal). Say "energy domains", not "power domains".
+- Intended behaviour (DESIGN_STATE.md, "Intended model behaviour (2026-10-19)"): the system is driven over the knee (the thermal trigger); too hot = HHO autoignition (failure); cascading cooling prevents ignition. Knee frequency is emergent (self-oscillating from the layers), not an external dial. Switching frequency, heat-transfer speed and heat-removal rate are distinct and never lumped; thermal mass is required. Flag: knee frequency treated as an input; outputs/designs crossing autoignition without the cooling cascade; any single lumped thermal time constant (e.g. tauLumped). Never propose an electrode-based drive; electrodes are removed from the model and the drive is "no drive mechanism defined".
 - You are reviewing a merge/diff produced by Cursor. You do NOT edit anything. You return a verdict.
 
 Rules for every review:
@@ -10,7 +11,9 @@ Rules for every review:
 3. Check units, orders of magnitude, sign conventions and limits of validity (e.g. quasi-static field model fails when wavelength approaches sphere size; a single EM cycle shorter than gas breakdown time cannot ionise).
 4. Check the domain couplings: does a change in one domain update the source terms it feeds into others?
 5. Retired items (listed below) must not be reintroduced. Any reintroduction is a FAIL unless clearly labelled as history.
-6. List every physics/source claim that should get an external source cross-check (Grok) in "claims_needing_source_check".
+6. Temperatures: Kelvin is canonical in calculations, the solver, data files and DESIGN_STATE.md. Flag any °C used there (major). °C appears only in the GUI, alongside K; flag any GUI temperature shown without its °C pair (minor). In the GUI, ambient is a linked K/°C pair (K = °C + 273.15).
+7. Locked, do not propose replacing: the Kelvin reference (293 K outer reference temperatures), which Danny uses to place thermal active materials in the tone. A suggestion to replace it with required-conductance output was rejected on 2026-10-19.
+8. List every physics/source claim that should get an external source cross-check (Grok) in "claims_needing_source_check".
 
 Output format — end your reply with exactly one fenced JSON block:
 ```json
diff --git a/harness/prompts/_rote_check.md b/harness/prompts/_rote_check.md
index 170153a..c3b8e78 100644
--- a/harness/prompts/_rote_check.md
+++ b/harness/prompts/_rote_check.md
@@ -3,7 +3,9 @@ Danny, then Stratified Sphere Bot, then the paid reviewers (Claude, Grok), then
 Your job is rote checks only. Do NOT do physics sourcing or design critique (Claude and Grok do that).
 - Units and arithmetic: recompute every number in the diff that is derived from other numbers; check unit conversions and orders of magnitude.
 - Consistency vs DESIGN_STATE.md (given below): treat Locked as fixed, Open as undecided. A changed or contradicted Locked value is a "major" finding unless the diff also updates DESIGN_STATE.md on purpose.
-- Retired items: any reintroduction (unless clearly labelled as history) is a FAIL.
+- Retired items: any reintroduction (unless clearly labelled as history) is a FAIL. Electrodes of any kind (Ti/Pt, ITO, central wire) are retired.
+- Intent: flag knee frequency treated as an external dial (it is emergent), any single lumped thermal time constant (switching frequency, heat-transfer speed, heat-removal rate and thermal mass are separate), and any electrode reference in model code.
+- Temperatures: any °C in a calculation, solver, data file or DESIGN_STATE.md is a finding (Kelvin is canonical); °C belongs only in the GUI, next to K.
 - If you are unsure, say UNSURE in the finding note. Do not guess and do not invent sources or numbers.
 - Keep it short: at most 10 findings, one line each, with the value, where it came from and why it passes or fails.
 Use the same JSON verdict block as everyone else; "claims_needing_source_check" lists anything Grok should look up.
diff --git a/harness/prompts/electric.md b/harness/prompts/electric.md
index bc8fedb..fbb719d 100644
--- a/harness/prompts/electric.md
+++ b/harness/prompts/electric.md
@@ -1,5 +1,6 @@
 Domain focus: ELECTRIC (and the plasma/ionisation source it drives).
-- Electro-quasistatics: spherical capacitors, BTO varactor εr(E,T) (Curie point crossed ~10 W), DBD gas gap.
-- Paschen knee from n·d: ~10 torr for a 1 mm gap, ~22 torr with a central electrode (estimates). Plasma is the source that drives the domains, not a domain itself.
+- Electro-quasistatics: spherical capacitors, BTO varactor εr(E,T) (Curie point crossed ~10 W).
+- Paschen knee from n·d: ~10 torr for a 1 mm gap (estimate). Plasma is the source that drives the domains, not a domain itself.
+- Electrodes are RETIRED (2026-10-19): no central wire, no DBD centre electrode, no Ti/Pt or ITO film. drive_model.js still models a centre-electrode DBD gap, so its breakdown numbers and the 10.71-98.95 Torr window rest on a gap that does not exist. How the gas is driven without electrodes is OPEN for Danny: flag, do not answer it.
 - EMF frequency range in the viewer: 100 kHz to 1000 THz. Limits that must be flagged: wavelength approaching sphere size (tens of GHz+), single cycle shorter than gas breakdown time (~ps at 1 THz, ~1 fs at 1000 THz).
-- A metal film on the inner wall screens the gas: check that is accounted for.
+- (Retired: the inner-wall metal-film screening note assumed an electrode film; there is none.)
diff --git a/harness/prompts/optical.md b/harness/prompts/optical.md
index 9c5b733..bb522fd 100644
--- a/harness/prompts/optical.md
+++ b/harness/prompts/optical.md
@@ -1,5 +1,5 @@
 Domain focus: OPTICAL.
 - Bands: hydrogen Balmer lines (H-alpha ~656 nm / ~457 THz, H-beta 486 nm, H-gamma 434 nm), phosphor emission (KSF, CASN), visible ~400–790 THz.
 - Check radiative transfer per band, Fresnel loss at quartz (~4.6–4.7% per surface, not 3.5–4%), absorption in quartz (IR absorption past a few µm), scattering in the tourmaline sol-gel at 434 nm, phosphor saturation (KSF ~8–16 W, CASN ~80 W, estimates).
-- Opaque electrodes (Ti/Pt) turn light into heat: confirm that heat is passed to THERMAL.
+- Electrodes are RETIRED (2026-10-19): no Ti/Pt film, no ITO/transparent case. Flag any light-to-heat path or preset that assumes one.
 - Above ~tens of GHz the drive is no longer a quasi-static field; in the optical band the "drive" is light itself. The viewer must flag, not fabricate, results there.
diff --git a/harness/prompts/thermal.md b/harness/prompts/thermal.md
index 9704694..e3c01e3 100644
--- a/harness/prompts/thermal.md
+++ b/harness/prompts/thermal.md
@@ -1,5 +1,7 @@
 Domain focus: THERMAL.
 - 1D radial finite volume with k(T), interface resistances, convection/radiation boundary conditions.
-- Known results (estimates): bare 2 mm OD test shell cannot dissipate 1 W in still air without the inner wall passing ~573 °C (HHO autoignition range); 5 mm OD full stack ~415 K at 10 W, ~1960 K at 100 W with outer surface at 293 K; BTO above Curie from ~10 W.
+- Known results (estimates): bare 2 mm OD test shell cannot dissipate 1 W in still air without the inner wall passing ~846 K (HHO autoignition range ~773–858 K); 5 mm OD full stack ~415 K at 10 W, ~1960 K at 100 W with outer surface at 293 K; BTO above Curie from ~10 W.
 - Check every heat source from other domains arrives (optical absorption, acoustic loss, electric/dielectric loss, magnetic loss, chemical recombination heat) and that T feeds back into εr, k, c, Q and the gas state.
 - Autoignition warnings must trigger from the computed temperature, not a constant.
+- The 293 K outer reference (Kelvin reference) is LOCKED (Danny, 2026-10-19): do not propose replacing it with required-conductance output.
+- Kelvin is canonical in every calculation, the solver and data files; °C only in the GUI, alongside K. Known gap: drive_model.js compares the autoignition range in °C (AUTOIGN_C) - flag until it is moved to K.
diff --git a/harness/retired.txt b/harness/retired.txt
index 890bbdc..4106efe 100644
--- a/harness/retired.txt
+++ b/harness/retired.txt
@@ -1,5 +1,7 @@
 # Retired items. Reviewers must FLAG any reintroduction (in code, docs, comments, presets or UI).
 # Format: label | python regex (case-insensitive unless noted) | note
+# An added line that itself says "retired" or "removed" is treated as a labelled retirement note and is not a hit.
+# Electrodes: any other electrode reference is an ERROR (electrodes are removed from the model, not only the design).
 oil bath | \boil[- ]?bath | retired cooling approach
 slotted Cu/Ag shell | slotted\s+(cu|ag|copper|silver)|(cu|ag)\s*/\s*(cu|ag)\s+(slotted\s+)?shell|slotted\s+shell | retired shell design
 ribs / segments | \bribs?\b|\bribbed\b|\bsegment(ed|s)?\s+(shell|layer|sphere)|shell\s+segments? | retired segmented/ribbed construction
@@ -8,3 +10,4 @@ ribs / segments | \bribs?\b|\bribbed\b|\bsegment(ed|s)?\s+(shell|layer|sphere)|s
 13 GHz atom-count ceiling | 13\s*ghz | retired atom-count ceiling argument
 cold-regime work | cold[- ]regime | retired line of work
 Backwards_Derived_Spec_from_Ionisation | backwards[_ ]derived[_ ]spec | retired spec document; do not cite or rebuild from it
+electrodes (Ti/Pt, ITO, central wire) | \belectrodes?\b|\bTi\s*/\s*Pt\b|(?-i:\bITO\b)|indium[- ]tin[- ]oxide|central\s+(50\s*[µu]m\s+)?wire | retired 2026-10-19 (Danny): there are NO electrodes in the design - no Ti/Pt film, no ITO/transparent-electrode case, no central 50 um wire / DBD centre electrode; how the gas is driven without electrodes is open for Danny
diff --git a/ledger/pending/2026-10-19_round5_dispositions.jsonl b/ledger/pending/2026-10-19_round5_dispositions.jsonl
new file mode 100644
index 0000000..c9a1650
--- /dev/null
+++ b/ledger/pending/2026-10-19_round5_dispositions.jsonl
@@ -0,0 +1,16 @@
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "accepted", "reason": "Fold 1: build after Danny's validation.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "8cf933f046b57f60", "hash": "8cf933f046b57f6017b4d58a95c552bee50b3c169071b9ec020c711505ea5bdf", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "holster", "file": "reviews/2026-10-19_round5/grok.md", "claim": "One geometry of record, shared by the spec and the solver", "note": "DESIGN_STATE.md and solver_v0.py disagree on shell sizes, layer order and 3.236 vs 3.018 MHz; one JSON/YAML loaded by both, CI fails on drift.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "f4115c367262ac81", "hash": "f4115c367262ac8148022f12a01645a175a4647fa77c39c10b5014e62dade1c2", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "8cf933f046b57f60", "status": "accepted", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "accepted", "reason": "Fold 2: record sound speed and formula in the output.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "0b2c3a78ac87d4ae", "hash": "0b2c3a78ac87d4ae97532882d730b620193d0c4c5dc63b0938763db5d799b132", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "acoustic", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Recompute drive frequencies from the geometry file with the sound-speed key in the output", "note": "1.87 MHz breathing / 3.236 MHz thickness should be recomputed from the geometry of record (settles 3.236 vs 3.018 MHz).", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "b03d47db489dba47", "hash": "b03d47db489dba473560b31c3f472a674598b4d481673cc57700cf2523b0f5f1", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "0b2c3a78ac87d4ae", "status": "accepted", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "accepted", "reason": "Fold 3: tested power budget, no double-counted loss.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "52e558b29d80f82c", "hash": "52e558b29d80f82c409d8980a1856f325aa2e5f48b253c615b97ab4aa39b36ea", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "thermal", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Close the power books before adding physics", "note": "One function returns the power table and asserts the parts sum to the input; no double-counted dielectric/ESR/ferrite loss.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "009cbf055c3ec82d", "hash": "009cbf055c3ec82d7b5e17fd80f65108071ec64f5c21aecb3c93b2ec0793e558", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "52e558b29d80f82c", "status": "accepted", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "accepted", "reason": "Fold 4.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "d0fe401e751b5b27", "hash": "d0fe401e751b5b2712284c163ccb1280f84c83961d7928a1f45d6ddf23c0062b", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "chemical", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Keep the chemistry stub out of the heat sources", "note": "P_release = E_store / t_conv is a placeholder; display it but do not add it to the thermal solve; ignition as a validity flag.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "23fdc7a241cf4ea8", "hash": "23fdc7a241cf4ea81db1c29bd0b027714ed034c50be01a0c12560f8b8268b744", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "d0fe401e751b5b27", "status": "accepted", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "accepted", "reason": "Fold 5: small number/label fixes.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "4ba3d689cf76f195", "hash": "4ba3d689cf76f195057b48472277e327bb9fb05b8956cccf0c108fe8d48ebecf", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "acoustic", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Fix a few numbers that will silently dominate", "note": "phos_out cT = 25 m/s; BTO eps(T) ramp mislabelled Curie-Weiss; layer2 name says 50 nm vs 5 um.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "874261b73c9d8149", "hash": "874261b73c9d8149f167321e5bd2987c5b1f49a558da83a5578ea8ae4a068fc7", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "4ba3d689cf76f195", "status": "accepted", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "accepted", "reason": "Fold 6: root cause traced 2026-10-19 (maxJump from partial-step Ed/dt depends on ncyc); fix with an ncyc-invariance test.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "604e1cb38052114b", "hash": "604e1cb38052114bcfdf2b68e7ab04fddeeb06aedc0cab6b6865f2992ff4effd", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Claude"}, "reviewer": "Claude", "model": "claude-sonnet-5-5", "severity": "note", "domain": "acoustic", "file": "reviews/2026-10-19_round5/claude.md", "claim": "A factor-of-2 mismatch inside drive_model_output.txt", "note": "Sweep ring-gas and shell amplitudes are exactly half the example values (8.093e-3 vs 4.047e-3 Pa at 20 Hz).", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "a149f6143bf1de3d", "hash": "a149f6143bf1de3d13109514da55076a4a8e89a6c31dd0a96e20e4a7e4d9088b", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "604e1cb38052114b", "status": "accepted", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "fixed", "reason": "Fixed in d567797 (theta = T - T_seal solve); dT_gas/dT_wall now exactly 0.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "ccdc5531e465f331", "hash": "ccdc5531e465f33112a66e4b1646414f8087b3ce18e3a1c789775c3d84828154", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Claude"}, "reviewer": "Claude", "model": "claude-sonnet-5-5", "severity": "note", "domain": "thermal", "file": "reviews/2026-10-19_round5/claude.md", "claim": "Numerical noise is reported as physics", "note": "Non-ionising cases print dT_gas of 3e-11 to 8e-10 K instead of exactly 0.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "df39ca8a7f643ef8", "hash": "df39ca8a7f643ef8dc3d6da48c632c05a20b26f9742aa7af110650f38f2cc12e", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "ccdc5531e465f331", "status": "fixed", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "fixed", "reason": "Fixed in 21b5fa5 (one voltage definition, computed bounds). Note: the window rests on a centre-electrode gap that is now retired.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "19838463252c326b", "hash": "19838463252c326b5b71c0952c6c751aed3ff858075ed4f6d2800ab862bf8897", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Claude"}, "reviewer": "Claude", "model": "claude-sonnet-5-5", "severity": "note", "domain": "electric", "file": "reviews/2026-10-19_round5/claude.md", "claim": "Ionisation window stated as 10-180 Torr at 600 V", "note": "Claude's review places the window at 10-180 Torr; computed window is 10.71-98.95 Torr (179 Torr does not ionise).", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "91ee3508a01f0743", "hash": "91ee3508a01f07439b9599933b54858a670335be2036c8b6c95b3afc21b9ec0c", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "19838463252c326b", "status": "fixed", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "rejected", "reason": "Cut: there are no electrodes in the design (no Ti/Pt, no ITO, no central wire). Retired 2026-10-19.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "00dd401c2edb093e", "hash": "00dd401c2edb093e65e7b33e09c586129a881749a6e3ea43e5cb295593d719fc", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "optical", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Add one transparent-electrode preset (ITO or equivalent) beside Ti/Pt", "note": "Ti/Pt is nearly opaque, so Balmer light becomes heat at the electrode; add an ITO case.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "b5ec5392e495599d", "hash": "b5ec5392e495599d7f87fe77228586b0ac9407335635386fbbab355ad5ed0c12", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "00dd401c2edb093e", "status": "rejected", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "rejected", "reason": "Cut: electrodes retired; no central wire or any electrode in the design. Strengthened 2026-10-19: electrodes removed from the model too (drive stub: no drive mechanism defined); the drive method is open for Danny.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "fcc0ce4254d92833", "hash": "fcc0ce4254d92833a43f271371151ceb1f906d12277ada9cbdac75f69e257d72", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "electric", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Angular structure: feeds, the central 50 um DBD wire, and polar holes are estimates", "note": "They set magnetic saturation and hot spots.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "5dd6606e8fdc96d8", "hash": "5dd6606e8fdc96d83c22e49b38ac27049b7cd15131db76c68759d7485b644776", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "fcc0ce4254d92833", "status": "rejected", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "rejected", "reason": "Keep the Kelvin reference: Danny uses the 293 K outer reference temperatures to select thermal active materials placement in the tone. Locked 2026-10-19.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "f1f872ca6d1cbabf", "hash": "f1f872ca6d1cbabfeef4feb25b54fc4b8d64cdf44c3de2d442bf41f5b897f77b", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "thermal", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Treat the thermal boundary as the design result, not a temperature under a fake sink", "note": "Report required outer conductance per limit instead of temperatures under the 293 K reference.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": {"schema": "ssm-ledger/v1.1", "kind": "status", "id": "1da4bc3cba06d494", "hash": "1da4bc3cba06d4949f9d440db15fc7c5668d69c59af96e6817d2d6fd8881b4eb", "recorded_utc": "2026-10-19T09:44:41Z", "source": {"type": "manual", "ref": "DESIGN_STATE.md#dannys-decisions-on-round-5-review-2026-10-19", "scope": "Danny decision", "run_id": null, "head_sha": null}, "finding_id": "f1f872ca6d1cbabf", "status": "rejected", "issue_number": null}}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "deferred", "reason": "Deferred: three labelled temperatures sounded good, later.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "545afd1159a2e68e", "hash": "545afd1159a2e68e05da2f2007d74603900bf2f7f92b4dc57b1e548dab69888a", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Claude"}, "reviewer": "Claude", "model": "claude-sonnet-5-5", "severity": "note", "domain": "thermal", "file": "reviews/2026-10-19_round5/claude.md", "claim": "Single-cycle is ambiguous", "note": "Label dT_gas as peak / cycle average / periodic steady state; add a multi-cycle network.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": null}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "deferred", "reason": "Deferred: later.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "8f20ab8944b5150e", "hash": "8f20ab8944b5150ea52527490cc77e4cfd4e17fc74157873b9ff9c70a724f5ff", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "holster", "file": "reviews/2026-10-19_round5/grok.md", "claim": "One solver entry point", "note": "solver_v0.py (or python -m sim) is the only command CI and the viewer call.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": null}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "deferred", "reason": "Deferred: later.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "9315644fa559b8fd", "hash": "9315644fa559b8fd263e07154d69a786a279442a9e11b4c350c13c00e4f12577", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "holster", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Uncertainty bands", "note": "Almost every material tag is est/rec; sweeps should show ranges.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": null}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "deferred", "reason": "Deferred: later.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "8c76b0b58b4b137b", "hash": "8c76b0b58b4b137b2267939def953eb97a7437eff93b0da493a39cad3aeebdef", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "acoustic", "file": "reviews/2026-10-19_round5/grok.md", "claim": "l>=1 spheroidal and torsional modes, and anisotropic quartz", "note": "Isotropic l=0 cannot confirm the thickness-mode number.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": null}
+{"staged": true, "decided_by": "Danny", "decided_on": "2026-10-19", "disposition": "deferred", "reason": "Held until folds 1-3 pass.", "finding": {"schema": "ssm-ledger/v1.1", "kind": "finding", "id": "a4566a7442c62dbf", "hash": "a4566a7442c62dbf587f175aefd776caa1172b24f12657e5fd987b190e0a6a90", "recorded_utc": "2026-10-19T09:44:30Z", "event_utc": "2026-10-19T06:55:00+00:00", "source": {"type": "review_round", "ref": "reviews/2026-10-19_round5", "run_id": null, "head_sha": null, "scope": "Grok"}, "reviewer": "Grok", "model": "grok-4.7", "severity": "note", "domain": "holster", "file": "reviews/2026-10-19_round5/grok.md", "claim": "Do not add FEniCS, MEEP or OpenFOAM cases until steps 1-3 pass", "note": "Sim-stack smokes show the tools run, not that this sphere is solved.", "review_verdict": null, "injection_flags": [], "status": "open"}, "status": null}
diff --git a/ledger/pending/README.md b/ledger/pending/README.md
new file mode 100644
index 0000000..7b95624
--- /dev/null
+++ b/ledger/pending/README.md
@@ -0,0 +1,9 @@
+# Staged ledger records (not ingested)
+
+`findings.jsonl` is written only by CI (`ledger.yml`), so decisions recorded locally are staged here first.
+Each line is a wrapper: `{staged, decided_by, decided_on, disposition, reason, finding, status}`.
+`finding` and `status` are schema-valid `ssm-ledger/v1` records (`status` is null for **deferred**,
+because the v1 status enum has no "deferred"; those findings stay `open`). Nothing here is read by any
+workflow; ingesting it means appending the inner records through the ledger's append path.
+
+- `2026-10-19_round5_dispositions.jsonl`: Danny's decisions on the round-5 review (see `DESIGN_STATE.md`).
diff --git a/scripts/harness_common.py b/scripts/harness_common.py
index 1df9e93..2e830a3 100644
--- a/scripts/harness_common.py
+++ b/scripts/harness_common.py
@@ -147,6 +147,10 @@ def added_lines(diff: str) -> list[tuple[str, str]]:
     return out
 
 
+# A line that itself labels the item as retired/removed is a retirement note, not a reintroduction (2026-10-19).
+LABELLED_RETIREMENT = re.compile(r"\b(retired|removed)\b", re.I)
+
+
 def retired_scan(diff: str) -> list[dict]:
     """Deterministic, free pre-check: retired items appearing in ADDED lines."""
     hits = []
@@ -154,7 +158,7 @@ def retired_scan(diff: str) -> list[dict]:
         for f, line in added_lines(diff):
             if f.startswith("harness/") or f in ("AGENTS.md", ".cursor/rules/handoffs.mdc"):
                 continue  # the retired list itself lives here
-            if pat.search(line):
+            if pat.search(line) and not LABELLED_RETIREMENT.search(line):
                 hits.append({"label": label, "file": f, "line": line.strip()[:200], "note": note})
     return hits
 
diff --git a/solver_v0.py b/solver_v0.py
index 08d2bfa..3bdb72c 100644
--- a/solver_v0.py
+++ b/solver_v0.py
@@ -15,9 +15,9 @@ What it does (per geometry preset x circulating power level):
             Two configurations: 'isolated' (quartz + thin films, free at the Gd-Dy surface) and 'bonded'
             (whole stack to the ferrite). l>=1 spheroidal/torsional frequencies are NOT computed in v0;
             they are read (read-only) from shell_phi_sweep_calc_output.txt where available.
-  ELECTRIC  quasi-static BTO spherical capacitor on Ti/Pt, tanh polarisation saturation (varactor C(V)),
-            Curie-Weiss eps(T), dielectric + ESR loss; LC tank with the ferrite shell as inductor.
-  MAGNETIC  quasi-static toroidal (meridional-winding) ferrite shell inductor: L, B(r), Q_f(f) loss.
+  ELECTRIC  NO DRIVE MECHANISM DEFINED [retired 2026-10-19: the BTO capacitor between metal films, the LC tank and
+            the bare-shell discharge field were electrode-based and are removed]. Electric fields, dielectric loss = 0.
+  MAGNETIC  no drive defined: ferrite field and loss = 0 (the ferrite shell stays as a material layer).
   THERMAL   1-D radial spherical finite-volume, implicit, k(T) for quartz, interface resistances,
             outer surface held at 293 K (reference only - no heat sink is chosen here).
   COUPLING  staggered, timescale-separated: fast domains (optical ps, acoustic/electric/magnetic us-ms)
@@ -47,7 +47,7 @@ PRESETS = [
     dict(id="lock25", label="Layer-1 lock B: 2.5 mm bubble, 100 atm HHO (wall 1 mm assumed)", core_d=2.5 - 2.0, wall=1.0, p_atm=100.0, group="lock",
          note="Read as quartz OD 2.5 mm with the 1 mm wall kept -> 0.5 mm gas bore (geometry B of earlier reports). If 2.5 mm is the gas diameter, rerun with --core-d 2.5."),
 ]
-# Minimal test (Danny): 1 mm ID HHO 2:1 at the Paschen knee (~10 Torr for a 1 mm gap), bare crystal-quartz shell, +-pulsed DBD
+# Minimal test (Danny): 1 mm ID HHO 2:1 at the Paschen knee (~10 Torr for a 1 mm gap), bare crystal-quartz shell; no drive mechanism defined
 PRESETS.insert(0, dict(id="minA", label="Minimal test A: 1 mm ID, 1 mm wall, 3 mm OD, bare quartz, HHO 10 Torr (Paschen knee)", core_d=1.0, wall=1.0, p_atm=10/760, group="minimal", bare=True))
 PRESETS.insert(0, dict(id="scope", label="Danny scope: 1 mm ID x 2 mm OD quartz, HHO, fill OPEN (3-D views: 10 Torr placeholder)", core_d=1.0, wall=0.5, p_atm=10/760, group="minimal", bare=True,
                        note="fill amount is open: the 3-D/steady views use 10 Torr only as a placeholder; the Drive panel computes the coupled single-cycle response for the fill you enter"))
@@ -70,11 +70,9 @@ MAT = {
                   tags="k 0.91 mid (0.52-1.59) [rec Layer2]; cL mid of 2.6-4.7 km/s [rec binder est]; cT=0.6 cL [est]; rho [est]; Q 50-500 -> 150 [est]"),
  "phos_in":  dict(name="Inner phosphor 20 um, Cr3+ garnet (CSSG-type) in sol-gel/PiG", rho=3500, cp=700, k=1.0, cL=5000, cT=3000, Q=100, n=1.8,
                   tags="k 1.0 [rec est]; rho,cp,cL,cT,Q [est]"),
- "tipt":     dict(name="Ti/Pt electrode 10/100 nm", rho=21450, cp=133, k=50, cL=3260, cT=1730, Q=1000, n=None,
-                  tags="Pt handbook-typical [est]; sheet R 2.65 ohm/sq [rec]"),
  "bto":      dict(name="BaTiO3 film 2 um (hydrothermal crystalline)", rho=6020, cp=437, k=1.35, cL=5000, cT=2700, Q=50, n=2.4,
                   tags="rho,cp,k [rec]; E~110 GPa [rec est] -> cL,cT [est]; Q~1/tan d=50 [rec]"),
- "gddy":     dict(name="Gd-Dy film 3 um (outer electrode, MCE ~260 K)", rho=8080, cp=270, k=7.3, cL=2950, cT=1680, Q=500, n=None,
+ "gddy":     dict(name="Gd-Dy film 3 um (MCE ~260 K)", rho=8080, cp=270, k=7.3, cL=2950, cT=1680, Q=500, n=None,
                   tags="rho,cp,k [rec]; E~55 GPa [est]; Q [est]"),
  "calorivac":dict(name="CALORIVAC ladder, epoxy-bonded granules", rho=5000, cp=500, k=1.0, cL=1800, cT=900, Q=20, n=None,
                   tags="k_eff 1.0 (0.5-2) [rec est]; rho,cp,cL,cT,Q [est] (epoxy-dominated, lossy)"),
@@ -92,7 +90,7 @@ LAM_CR = 770.0                      # CSSG:Cr emission peak [rec ladder]
 QY_CR = 0.778                       # IQE measured [rec ladder]
 I_SAT_CR = 7.6e4 * 1e4              # W/m2; geometric mid of 2.4e4-2.4e5 W/cm2 [rec, cross-section est]
 ALPHA_PHOS = 1.0e5                  # 1/m (1000 /cm) inner phosphor small-signal absorption [est]
-ALPHA_PT = 8.8e7                    # 1/m Pt visible absorption from k~3.5 [est] -> 100 nm passes ~1.5e-4
+ALPHA_METAL = 8.8e7                 # 1/m visible absorption of the metallic layers (Gd-Dy, CALORIVAC, ferrite) [est, metal-typical k~3.5]
 L2_MU_EXT = {434.0: 106e2, 486.1: 68e2, 656.3: 22e2, 770.0: 15e2}  # 1/m direct extinction, P0.07 phi0.2 [rec Layer2; 770 est]
 L2_MU_ABS = 0.9e2 * math.log(10) / 2.3026   # <=0.9 /cm absorption [rec Layer2]
 SMOKY_ALPHA = {434.0: 50.0, 486.1: 50.0, 656.3: 30.0, 770.0: 5.0}   # 1/m (0.5/0.5/0.3 /cm) [est, dose-dependent; bands rec Coloured_Piezo]
@@ -100,7 +98,6 @@ SMOKY_BLEACH_K = 473.0              # colour bleaches ~200-300 C [rec]
 
 # Electric [rec power scaling / BTO report]
 BTO_T = 2 * UM; EPSR0 = 450.0; TAND = 0.02; PS = 0.115; E_WORK = 42e6; T_CURIE = 393.0
-RS_PT, RS_GD, G_RING = 2.65, 0.44, 0.031
 # Magnetic [rec HighQ_MHz: Fair-Rite 61 Q vs f]; B_sat est
 FERR_MU = 125.0
 FERR_QF = [(1e4, 260), (3e5, 260), (1e6, 190), (2.5e6, 155), (5e6, 130), (1e7, 62), (2e7, 4.6)]
@@ -124,7 +121,7 @@ def build_stack(core_d_mm, wall_mm, bare=False):
     def add(key, t):
         r0 = L[-1][2] if L else r_in
         L.append((key, r0, r0 + t))
-    add("quartz", wall_mm * MM); add("layer2", 5 * UM); add("phos_in", 20 * UM); add("tipt", 0.11 * UM); add("bto", BTO_T)
+    add("quartz", wall_mm * MM); add("layer2", 5 * UM); add("phos_in", 20 * UM); add("bto", BTO_T)
     r_B = L[-1][2]                       # first phi step starts at the BTO outer boundary [Danny rule, rec BTO report]
     add("gddy", 3 * UM)
     r1, r2 = r_B * PHI, r_B * PHI ** 2   # phi-stepped thick zones [v0 layout assumption]
@@ -341,41 +338,15 @@ def ferrite_L(stack):
     L = MU0 * FERR_MU * N_TURNS ** 2 * (b - a) / math.pi * math.log(1 / math.tan(THETA0 / 2))
     return L, a, b
 
-def electric_magnetic(stack, P, T_bto, T_ferr):
-    cap = bto_cap(stack, T_bto)
-    L, a, b = ferrite_L(stack)
-    f0 = 1 / (2 * math.pi * math.sqrt(L * cap["C0"]))
-    fb = 1 / (2 * math.pi * math.sqrt(L * cap["C_bias"]))
-    fe = fb
-    w = 2 * math.pi * fe; W = P / w
-    V = math.sqrt(2 * W / cap["C_bias"])
-    V_work = E_WORK * BTO_T
-    I = w * cap["C_bias"] * V / math.sqrt(2)
-    esr = G_RING * (RS_PT + RS_GD)
-    P_diel = P * TAND; P_esr = I ** 2 * esr
-    Qf = ferrite_Q(fe); P_ferr = P / Qf
-    Ipk = math.sqrt(2 * W / L)
-    rm = 0.5 * (a + b)
-    B_eq = MU0 * FERR_MU * N_TURNS * Ipk / (2 * math.pi * rm)
-    B_max = MU0 * FERR_MU * N_TURNS * Ipk / (2 * math.pi * a * math.sin(THETA0))
-    Q_tank = 1 / (TAND + P_esr / P + 1 / Qf)
-    return dict(C0=cap["C0"], C_bias=cap["C_bias"], eps=cap["eps"], L=L, f_zero_bias=f0, f_bias=fb, f_e=fe,
-                W=W, V_pk=V, V_work=V_work, over_voltage=V > V_work, E_pk=V / BTO_T, I_rms=I, ESR=esr,
-                P_diel=P_diel, P_esr=P_esr, Q_f=Qf, P_ferr=P_ferr, B_eq=B_eq, B_max=B_max, B_sat=B_SAT,
-                saturates=B_max > B_SAT, Q_tank=Q_tank, tau_ring=2 * Q_tank / w, piezo_on=cap["piezo_on"],
-                J_feed=I / (2 * math.pi * cap["r1"] * 100e-9 * 2))
-
-def electric_bare(stack, P, f_drive):
-    """DBD: central 50 um electrode in gas, quartz barrier eps 4.5, outer electrode on OD [est geometry]. No magnetic element."""
-    r0, a, b = 50e-6, stack["r_in"], stack["r_q"]
-    S = (1 / r0 - 1 / a) + (1 / a - 1 / b) / 4.5
-    C = 4 * math.pi * EPS0 / S
-    V = 337.0   # applied V at the Paschen-min gas voltage ~332 V (gas takes ~98.5 %) [calc minimal_test_calc]
-    w = 2 * math.pi * f_drive
-    return dict(C0=C, C_bias=C, eps=4.5, L=None, f_zero_bias=f_drive, f_bias=f_drive, f_e=f_drive, W=0.5 * C * V ** 2, V_pk=V, V_work=V,
-                over_voltage=False, E_pk=V / (r0 ** 2 * S), I_rms=w * C * V / math.sqrt(2), ESR=0, P_diel=w * 0.5 * C * V ** 2 * 1e-4, P_esr=0,
-                Q_f=None, P_ferr=0, B_eq=0, B_max=0, B_sat=None, saturates=False, Q_tank=None, tau_ring=1 / f_drive, piezo_on=False, J_feed=0,
-                S=S, r0=r0, bare=True)
+NO_DRIVE = "no drive mechanism defined (electrodes removed 2026-10-19; drive method open)"
+
+def no_drive_em(stack, T_bto=None):
+    """Fail-closed stub [retired 2026-10-19: electrode-based BTO tank / bare-shell discharge field]. No drive mechanism is
+    defined, so there is no electric or magnetic field, no tank frequency and no electric/magnetic loss. Do not invent one."""
+    piezo = (T_bto < T_CURIE) if (T_bto is not None and not stack.get("bare")) else False
+    return dict(none=True, note=NO_DRIVE, f_e=None, f_zero_bias=None, f_bias=None, V_pk=0.0, E_pk=0.0, W=0.0, I_rms=0.0,
+                P_diel=0.0, P_esr=0.0, P_ferr=0.0, B_eq=0.0, B_max=0.0, saturates=False, over_voltage=False, tau_ring=None,
+                piezo_on=piezo, bare=bool(stack.get("bare")))
 
 # ------------------------------------------------- OPTICAL -------------------------------------
 def optical(stack, P_opt, Tcell, cells, mats):
@@ -407,8 +378,8 @@ def optical(stack, P_opt, Tcell, cells, mats):
                 P[LAM_CR] += 0.5 * Pem; converted += Pem       # half outward, half back toward core [est]
                 heat[0] += 0.5 * Pem * 0.0                     # inward half returns to core (not tracked) [v0 limit]
                 if shift_r is None and Pabs > 0.05 * Pin: shift_r = ra
-            elif m in ("tipt", "gddy", "calorivac", "ferrite"):
-                Pout = Pin * math.exp(-ALPHA_PT * t); heat[i] += Pin - Pout
+            elif m in ("gddy", "calorivac", "ferrite"):
+                Pout = Pin * math.exp(-ALPHA_METAL * t); heat[i] += Pin - Pout
             elif m == "phos_out":
                 Pout = Pin * math.exp(-1e4 * t); heat[i] += Pin - Pout
             else:  # bto: weakly absorbing in visible [est 100/cm]
@@ -473,7 +444,7 @@ def run_case(pre, P, ref):
     if bare: th.outer = "natconv"   # still air + radiation; heat sink left to Danny
     T = np.full(th.n, T_REF)
     lay = st["layers"]
-    iso = [x for x in lay if x[0] in ("quartz", "layer2", "phos_in", "tipt", "bto", "gddy")]
+    iso = [x for x in lay if x[0] in ("quartz", "layer2", "phos_in", "bto", "gddy")]
     # acoustic: l=0 modes, isolated and bonded. Gas-loaded roots are split into shell modes (within 1 % of the
     # vacuum shell modes) and HHO gas-cavity modes (coupled through the wall).
     def vac_modes(L_):
@@ -512,8 +483,8 @@ def run_case(pre, P, ref):
     frames = [T.copy()]; history = []
     t_prev = 0.0
     idx = lambda key: [i for i, m in enumerate(mats) if m == key]
-    i_bto, i_ferr, i_pt = idx("bto"), idx("ferrite"), idx("tipt")
-    EM = (lambda T_: electric_bare(st, P, f_ac)) if bare else (lambda T_: electric_magnetic(st, P, float(np.mean(T_[i_bto])), float(np.mean(T_[i_ferr]))))
+    i_bto = idx("bto")
+    EM = (lambda T_: no_drive_em(st)) if bare else (lambda T_: no_drive_em(st, float(np.mean(T_[i_bto]))))   # no drive mechanism defined
     for tk in times[1:]:
         # fast domains quasi-static at current temperatures
         em = EM(T)
@@ -521,9 +492,6 @@ def run_case(pre, P, ref):
         q = qo + q_ac
         q[0] += (1.0 if bare else F_WALL) * P
         if tk <= chem["t_conv"]: q[0] += chem["P_release"]   # transient 2H2+O2->2H2O heat release until the fill is converted
-        for i in i_bto: q[i] += em["P_diel"] / len(i_bto)
-        for i in i_pt: q[i] += em["P_esr"] / len(i_pt)
-        for i in i_ferr: q[i] += em["P_ferr"] * th.V[i] / sum(th.V[j] for j in i_ferr)
         # sub-steps
         nsub = 6; dts = np.diff(np.linspace(t_prev, tk, nsub + 1))
         for dt in dts:
@@ -537,15 +505,12 @@ def run_case(pre, P, ref):
         em = EM(Tss)
         qo, oprof, oinfo = optical(st, F_OPT * P, Tss, cells, mats)
         q = qo + q_ac; q[0] += (1.0 if bare else F_WALL) * P
-        for i in i_bto: q[i] += em["P_diel"] / len(i_bto)
-        for i in i_pt: q[i] += em["P_esr"] / len(i_pt)
-        for i in i_ferr: q[i] += em["P_ferr"] * th.V[i] / sum(th.V[j] for j in i_ferr)
         Tss = th.step(Tss, q, 1e4 if not bare else 5.0)
     heat_by_layer = {}
     for i, m in enumerate(mats): heat_by_layer[m] = heat_by_layer.get(m, 0) + float(q[i])
     em_hot = em
     # coupled gas state [calc; gas T est = inner-wall T, a LOWER bound under discharge heating]: fixed N and V => n constant,
-    # p = p_seal*T/T_seal, c = c_hho(T); gas-loaded modes recomputed hot. Paschen knee depends on n*d (constant) to first order.
+    # p = p_seal*T/T_seal, c = c_hho(T); gas-loaded modes recomputed hot. 
     a_ = st["r_in"]; P_cond = (1.0 if bare else F_WALL) * P   # heat that leaves the gas by conduction to the wall
     rs_ = np.linspace(0, a_, 81); Tp_ = np.array(gas_T_profile(float(Tss[0]), P_cond, a_, rs_))
     Tg = float(min(np.trapezoid(Tp_ * rs_ ** 2, rs_) * 3 / a_ ** 3, 3000.0)); Tg_centre = float(Tp_[0]); p_seal = GAS["p"]
@@ -637,15 +602,8 @@ def package(pre, runs, ref):
         stress = [float(np.interp(r, ac_r, ac_s)) if ac_r[0] <= r <= ac_r[-1] else 0.0 for r in rc]
         bare = run["stack"]["bare"]
         if bare:
-            Efield = [em["V_pk"] / (r ** 2 * em["S"] * 4.5) for r in rc]   # quartz barrier field
-            Bf = [0.0 for r in rc]
-        else:
-            Efield = [em["E_pk"] if m == "bto" else 0.0 for m in mats]
-            Bf = []
-            L_, a_, b_ = ferrite_L(run["stack"])
-            Ipk = math.sqrt(2 * em["W"] / L_)
-            for r, m in zip(rc, mats):
-                Bf.append(MU0 * FERR_MU * N_TURNS * Ipk / (2 * math.pi * r) if m == "ferrite" else 0.0)
+            pass
+        Efield = [0.0 for r in rc]; Bf = [0.0 for r in rc]   # no drive mechanism defined: no electric or magnetic field
         Tss = run["Tss"]; frames = run["frames"]
         # ---- REAL core fields (previously the core got zeros -> black disc) ----
         gh = run["gas_hot"]; a_in = run["stack"]["r_in"]; ch = run["chem"]
@@ -657,19 +615,16 @@ def package(pre, runs, ref):
         jw = j1_(k_g * a_in)
         core_p = [abs(u_a * rho_g * w_ac ** 2 * j0_(k_g * r) / (k_g * jw)) if jw else 0.0 for r in r_core]   # gas pressure amplitude, p = A j0(kr)
         core_I = [float(Itot[0]) * r / a_in for r in r_core]   # net radial flux of a uniform optically-thin emitter: F = P r/(4 pi a^3) [est]
-        if bare:
-            core_E = [em["V_pk"] / (r ** 2 * em["S"]) if r >= em["r0"] else 0.0 for r in r_core]   # DBD gas field, 0 inside the 50 um electrode
-        else:
-            core_E = [0.0 for r in r_core]
+        core_E = [0.0 for r in r_core]   # no drive mechanism defined
         core_B = [0.0 for r in r_core]
         wall_peak = max(stress) if stress else 0.0
         core_note = dict(
             acoustic=f"HHO gas pressure in the core p = A j0(kr) (gas-loaded mode at {ac['f']/1e6:.3f} MHz, c(T_gas) {gh['c_hot']:.0f} m/s): max {max(core_p):.3g} Pa = {max(core_p)/max(wall_peak,1e-30):.2g} x the quartz peak stress; continuous with the wall in radial normal stress (sigma_rr = -p), not in hoop stress. Log colour scale.",
             thermal=f"steady gas T profile (uniform heating {gh['P_cond']:.3g} W conducted to the wall, k~T^0.75): centre {core_T[0]:.0f} K, wall {float(Tss[0]):.0f} K, volume mean {gh['T_gas']:.0f} K",
             optical="net radial flux of a uniformly emitting, optically thin plasma: F(r) = P r/(4 pi a^3), zero at the centre by symmetry [est emission profile]. Log colour scale.",
-            electric=("DBD gas field E = V/(r^2 S) from the 50 um central electrode (zero inside it) [est geometry]" if bare else "E = 0 in the core in v0: the drive field is confined between the Ti/Pt and Gd-Dy electrodes (genuinely ~zero, not a rendering gap)"),
+            electric=f"E = 0: {NO_DRIVE}",
             chemical=f"dissociation power {ch['P_diss']:.3g} W spread uniformly in the gas [est]; fill converts to H2O in {ch['t_conv']:.3g} s releasing {ch['E_store']:.3g} J (then a dissociation-recombination cycle with ~zero net heat); outside the core only surface recombination on the inner wall. Knee: not defined.",
-            magnetic="B = 0 in the core (symmetric radial current; ferrite flux confined to the ferrite shell) - genuinely zero")
+            magnetic=f"B = 0: {NO_DRIVE}")
         Twall = float(frames[-1][0])
         # arrival times for animation envelopes
         t_opt, t_ac = [], []; acc_o = 0.0; acc_a = 0.0
@@ -693,27 +648,21 @@ def package(pre, runs, ref):
             vectors = [
                 dict(domain="optical", f_start=C0 / 434e-9, f_end=C0 / 656.3e-9, r_start=r_in_, r_end=r_q_, what="Balmer lines pass the bare quartz (~90 % per wall incl. ~4.6 % Fresnel per surface); they leave the sphere"),
                 dict(domain="acoustic", f_start=ac["f"], f_end=ac["f"], r_start=r_in_, r_end=r_q_, what="l=0 breathing mode of the bare shell, gas-loaded; reflects at the free outer surface"),
-                dict(domain="electric", f_start=em["f_e"], f_end=em["f_e"], r_start=em["r0"], r_end=r_q_, what="+-pulsed DBD field from a 50 um central electrode through gas and quartz barrier to the OD electrode [est geometry]"),
-                dict(domain="magnetic", f_start=em["f_e"], f_end=em["f_e"], r_start=em["r0"], r_end=r_q_, what="no magnetic element in the bare test; symmetric radial current gives B = 0 (feed-wire field not modelled)"),
                 dict(domain="thermal", f_start=thermal_track(run["stack"], r_in_ + 1e-6), f_end=thermal_track(run["stack"], R), r_start=r_in_, r_end=R,
                      what="1-D conduction through the wall to still air + radiation (natural convection, eps 0.9 est); no sink chosen"),
             ]
         else:
           vectors = [
             dict(domain="optical", f_start=C0 / 434e-9, f_end=C0 / (LAM_CR * 1e-9), r_start=run["stack"]["r_in"], r_shift=oinfo["shift_r"],
-                 r_end=oinfo["term_r"] or lay["tipt"][1], what="Balmer 434/486/656 nm downshifted to 770 nm in the inner Cr3+ phosphor; remainder absorbed by the Ti/Pt electrode"),
+                 r_end=oinfo["term_r"] or R, what="Balmer 434/486/656 nm downshifted to 770 nm in the inner Cr3+ phosphor; remainder absorbed in the metallic Gd-Dy film [est]"),
             dict(domain="acoustic", f_start=ac["f"], f_end=ac["f"], r_start=run["stack"]["r_in"], r_end=lay["gddy"][1],
                  r_end_bonded=ac_term_bond, what="l=0 shell mode nearest 2 MHz; isolated shell reflects at the Gd-Dy free surface; if the ladder is bonded, 90 % of loss is reached at the marked radius"),
-            dict(domain="electric", f_start=em["f_zero_bias"], f_end=em["f_bias"], r_start=lay["tipt"][0], r_end=lay["gddy"][0],
-                 what="field confined between Ti/Pt and Gd-Dy electrodes; varactor tunes tank from zero-bias to working-bias frequency"),
-            dict(domain="magnetic", f_start=em["f_e"], f_end=em["f_e"], r_start=lay["ferrite"][0], r_end=lay["ferrite"][1],
-                 what="toroidal flux confined in the ferrite shell; energy lost at Q_f"),
             dict(domain="thermal", f_start=thermal_track(run["stack"], run["stack"]["r_in"] + 1e-6), f_end=thermal_track(run["stack"], R),
                  r_start=run["stack"]["r_in"], r_end=R, what="heat diffuses to the 293 K reference surface (no sink chosen)"),
         ]
-        f_chem = 2 * em["f_e"]
+        f_chem = 1 / (2 * math.pi * max(ch["t_conv"], 1e-30))   # conversion-rate corner [calc] (was 2 x the removed electrode drive f)
         vectors.append(dict(domain="chemical", f_start=f_chem, f_end=f_chem, r_start=0.0, r_end=run["stack"]["r_in"],
-                            what="H2/O2 dissociation -> H, O, OH radicals -> 2H2+O2->2H2O heat release in the HHO core; ends at the inner wall (surface recombination). Knee: not defined"))
+                            what="H2/O2 dissociation -> H, O, OH radicals -> 2H2+O2->2H2O heat release in the HHO core (P_circ scenario); ends at the inner wall (surface recombination). Knee: not defined"))
         for v in vectors:
             for kk in ("r_start", "r_end", "r_shift", "r_end_bonded"):
                 if v.get(kk) is not None:
@@ -738,11 +687,7 @@ def package(pre, runs, ref):
         fl(not bare and Tcal > 473, f"CALORIVAC max {Tcal:.0f} K > 200 C (H loss)")
         fl(not bare and Tgd > 260, f"Gd-Dy {Tgd:.0f} K above its ~260 K Tc (MCE knee missed)")
         fl(not bare and Tph > 573, f"Inner phosphor {Tph:.0f} K > 300 C (quench)")
-        emh = run["em_hot"]
-        fl(not bare and abs(emh["f_e"] / em["f_e"] - 1) > 0.1, f"Tank detunes {em['f_e']/1e6:.2f} -> {emh['f_e']/1e6:.2f} MHz as BTO heats (eps(T) feedback)")
-        fl(em["over_voltage"], f"Tank needs {em['V_pk']:.0f} V on BTO > {em['V_work']:.0f} V working (half breakdown)")
-        fl(em["saturates"], f"Ferrite B_max {em['B_max']*1e3:.0f} mT near feed holes > B_sat ~{B_SAT*1e3:.0f} mT [est]")
-        fl(em["J_feed"] > 0.8e9, f"Pt feed current density {em['J_feed']/1e4:.2g} A/cm2 > 0.8e5 A/cm2 contact limit")
+        flags.append("Electric/magnetic: " + NO_DRIVE)
         gh = run["gas_hot"]
         for nm, TT in (("Quartz inner wall", Tq_in), ("Gas centre (conduction profile)", gh["T_centre"])):
             if TT >= 773.15: flags.append(f"{nm} {TT-273.15:.0f} C is IN the HHO autoignition range ~500-585 C [given range]")
@@ -759,11 +704,11 @@ def package(pre, runs, ref):
             core_note=core_note,
             chemical=dict(E_store_J=r4(ch["E_store"]), R_diss_per_s=r4(ch["R_diss"]), R_water_per_s=r4(ch["R_water"]), t_conv_s=r4(ch["t_conv"]),
                           P_release_W=r4(ch["P_release"]), P_diss_W=r4(ch["P_diss"]), P_wall_recomb_W=r4(ch["P_wall_recomb"]), D_H=r4(ch["D_H"]), tau_D_s=r4(ch["tau_D"]),
-                          f=r4(2 * em["f_e"]), tau_s=r4(min(ch["t_conv"], 1e3)), knee="not defined",
+                          f=r4(f_chem), tau_s=r4(min(ch["t_conv"], 1e3)), knee="not defined",
                           sources="D0(H2) 4.478 eV, D0(O2) 5.116 eV [lit NIST CCCBDB]; dHf H2O(g) -241.826 kJ/mol [lit NIST WebBook]; eta_diss 0.2, chain 1, wall share 0.5, D_H [PLACEHOLDERS]; branching H+O2->OH+O drives autoignition [lit, standard H2-O2 mechanism, e.g. Glassman, Combustion]"),
             units=dict(optical="W/m2", acoustic="Pa (peak, l=0 mode)", electric="V/m (peak)", magnetic="T (peak)", thermal="K (steady)", chemical="W/m3 (dissociation power density in gas; surface recombination in the first quartz cell)"),
             thermal_frames=dict(t=r4(list(run["times"]), 3), T=[r4(gas_T_profile(float(frames[k][0]), gh["P_cond"] if k > 0 else 0.0, a_in, r_core) + list(frames[k]), 4) for k in sel_frames]),
-            t_opt=r4([0.0] * len(r_core) + t_opt, 3), t_ac=r4([0.0] * len(r_core) + t_ac, 3), tau_ac=r4(tau_ac), tau_e=r4(em["tau_ring"]),
+            t_opt=r4([0.0] * len(r_core) + t_opt, 3), t_ac=r4([0.0] * len(r_core) + t_ac, 3), tau_ac=r4(tau_ac), tau_e=None,
             vectors=vectors, thermal_track=thermal_tr,
             acoustic=dict(f_drive=r4(ac["f"]), l0_isolated=r4(run["m_iso"]), l0_bonded=r4(run["m_bond"][:25]), gas_cavity_modes=r4(run["gas_modes"][:8]), W_mJ=r4(ac["W"] * 1e3),
                           peak_stress_MPa=r4(ac["peak_stress"] / 1e6), Q_eff=r4(ac["Q_eff"]), loss_W=r4(sum(ac["loss"].values())),
@@ -771,18 +716,14 @@ def package(pre, runs, ref):
                           bonded=dict(f=r4(run["ac_bond"]["f"]), Q_eff=r4(run["ac_bond"]["Q_eff"]), peak_stress_MPa=r4(run["ac_bond"]["peak_stress"] / 1e6),
                                       loss_W=r4(sum(run["ac_bond"]["loss"].values()))) if run["ac_bond"] else None,
                           fill_stress_MPa=r4(run["s_fill"] / 1e6)),
-            electric=dict(C0_nF=r4(em["C0"] * 1e9), C_bias_nF=r4(em["C_bias"] * 1e9), eps=r4(em["eps"]), f_zero_bias=r4(em["f_zero_bias"]), f_e=r4(em["f_e"]),
-                          V_pk=r4(em["V_pk"]), V_work=r4(em["V_work"]), I_rms=r4(em["I_rms"]), P_diel=r4(em["P_diel"]), P_esr=r4(em["P_esr"]),
-                          Q_tank=r4(em["Q_tank"]), piezo_on=em["piezo_on"], C_fF=r4(em["C0"] * 1e15),
-                          hot=dict(eps=r4(run["em_hot"]["eps"]), f_e=r4(run["em_hot"]["f_e"]), P_diel=r4(run["em_hot"]["P_diel"]), P_esr=r4(run["em_hot"]["P_esr"]),
-                                   piezo_on=run["em_hot"]["piezo_on"], note="at the steady-state BTO temperature (feedback via eps(T))")),
-            magnetic=dict(none=True, note="no magnetic element in the bare test") if bare else dict(L_nH=r4(em["L"] * 1e9), Q_f=r4(em["Q_f"]), P_ferr=r4(em["P_ferr"]), B_eq_mT=r4(em["B_eq"] * 1e3), B_max_mT=r4(em["B_max"] * 1e3)),
+            electric=dict(none=True, note=NO_DRIVE, f_e=None, f_zero_bias=None, piezo_on=em["piezo_on"]),
+            magnetic=dict(none=True, note=NO_DRIVE),
             optical=dict(P_opt=F_OPT * P, converted_W=r4(oinfo["converted_W"]), escaped_W=r4(oinfo["escaped_W"])),
             thermal=dict(T_quartz_in=r4(Tq_in), T_quartz_out=r4(Tq_out), T_phos=r4(Tph), T_bto=r4(Tbto), T_gddy=r4(Tgd), T_calorivac_max=r4(Tcal), dT_wall=r4(dT_wall),
                          heat_W={k: r4(v) for k, v in run["heat_by_layer"].items()}, total_heat_W=r4(float(run["q"].sum()))),
             gas=dict(T_gas_K=r4(gh["T_gas"]), T_centre_K=r4(gh["T_centre"]), T_wall_K=r4(gh["T_wall"]), T_seal_K=T_REF, p_seal_Pa=r4(gh["p_seal"]), p_hot_Pa=r4(gh["p_hot"]), n_m3=r4(gh["n_m3"]),
                      c_seal=r4(gh["c_seal"]), c_hot=r4(gh["c_hot"]), shell_l0_hot=r4(gh["shell"][:6]), gas_modes_hot=r4(gh["gas_modes"][:8]),
-                     note="computed state, not an input: gas T = volume mean of the steady conduction profile (uniform heating conducted to the inner wall); fixed N,V => p ~ T, c ~ sqrt(T); Paschen knee ~ n d unchanged to first order"),
+                     note="computed state, not an input: gas T = volume mean of the steady conduction profile (uniform heating conducted to the inner wall); fixed N,V => p ~ T, c ~ sqrt(T)"),
             flags=flags)
     return out
 
@@ -798,12 +739,6 @@ def find_crossings(case):
             tr.append(("HHO gas cavity mode", f, case["propagation"]["r_in_mm"] * 0, case["propagation"]["r_in_mm"]))
         for lab, f in case.get("acoustic_ref_l_ge_1", {}).items():
             if lab in ("0S2", "0T2", "0S1"): tr.append((f"acoustic {lab} [{'calc minimal_test' if case['propagation']['bare'] else 'rec sweep'}]", f, v["acoustic"]["r_start_mm"], v["acoustic"]["r_end_mm"]))
-        if case["propagation"]["bare"]:
-            tr.append(("electric +-pulsed DBD drive (scenario: set to shell 0S0)", pdat["electric"]["f_e"], v["electric"]["r_start_mm"], v["electric"]["r_end_mm"]))
-        else:
-          tr.append(("electric tank (working bias)", pdat["electric"]["f_e"], v["electric"]["r_start_mm"], v["electric"]["r_end_mm"]))
-          tr.append(("electric tank (zero bias)", pdat["electric"]["f_zero_bias"], v["electric"]["r_start_mm"], v["electric"]["r_end_mm"]))
-          tr.append(("magnetic ferrite tank", pdat["electric"]["f_e"], v["magnetic"]["r_start_mm"], v["magnetic"]["r_end_mm"]))
         cr = []
         for i in range(len(tr)):
             for j in range(i + 1, len(tr)):
@@ -811,11 +746,6 @@ def find_crossings(case):
                 if a[0].split()[0] == b[0].split()[0] and not (a[0].startswith("electric") or b[0].startswith("electric")): continue
                 if abs(math.log(a[1] / b[1])) < 0.05:
                     cr.append(dict(a=a[0], b=b[0], f=r4(math.sqrt(a[1] * b[1])), r_overlap_mm=[max(a[2], b[2]), min(a[3], b[3])], radial_overlap=max(a[2], b[2]) <= min(a[3], b[3])))
-        # electric varactor band covering an acoustic mode
-        f0, fb = pdat["electric"]["f_zero_bias"], pdat["electric"]["f_e"]
-        for f in pdat["acoustic"]["l0_isolated"]:
-            if not case["propagation"]["bare"] and min(f0, fb) <= f <= max(f0, fb):
-                cr.append(dict(a="electric varactor tuning band", b="acoustic l=0 (isolated)", f=r4(f), note="reachable by bias tuning (capacitance is the tuning value)", radial_overlap=True))
         # thermal track crossing reference cycle rates and acoustic/electric
         for name, f in [("caloric rung 11 Hz [rec]", 11.0), ("caloric rung 35 Hz [rec est]", 35.0), ("EC/MCE 1 kHz", 1e3)]:
             ttr = pdat["thermal_track"]
@@ -851,14 +781,14 @@ def main():
         c = package(pre, runs, ref); find_crossings(c); cases.append(c)
         ks = list(c["powers"]); p0, p1, p10 = c["powers"][ks[0]], c["powers"][ks[1]], c["powers"][ks[-1]]
         log.append(f"{pre['id']:10s} OD {c['OD_quartz_mm']} mm R_out {c['R_outer_mm']} | l0 iso {[round(f/1e6,3) for f in p10['acoustic']['l0_isolated'][:4]]} MHz | drive {p10['acoustic']['f_drive']/1e6:.3f} MHz "
-                   f"stress@{ks[-1]}W {p10['acoustic']['peak_stress_MPa']} MPa Qeff {p10['acoustic']['Q_eff']} | f_e {p10['electric']['f_e']/1e6:.3f} MHz (0-bias {p10['electric']['f_zero_bias']/1e6:.3f}) "
+                   f"stress@{ks[-1]}W {p10['acoustic']['peak_stress_MPa']} MPa Qeff {p10['acoustic']['Q_eff']} | electric: no drive "
                    f"| T_gas mean {p1["gas"]["T_gas_K"]} K centre {p1["gas"]["T_centre_K"]} K p {p1['gas']['p_hot_Pa']} Pa c {p1['gas']['c_hot']} m/s @{ks[1]}W "
                    f"| T_qz_in {ks[0]}W {p0['thermal']['T_quartz_in']} K {ks[1]}W {p1['thermal']['T_quartz_in']} K, {ks[-1]}W {p10['thermal']['T_quartz_in']} K | crossings {len(p10['crossings'])}")
         print(log[-1], flush=True)
     data = dict(meta=dict(title="Stratified bubble sphere - multi-domain radial model v0", date="2026-10-19",
                           status="v0 PROTOTYPE - ESTIMATED PHYSICS - not validated - paper model, nothing measured",
                           scenario=f"All five domains circulate P_circ at once. Wall heat = {F_WALL} P_circ [rec bracket 0.1-1]; Balmer light = {F_OPT} P_circ [est]; "
-                                   "acoustic drive at the l=0 isolated-shell mode nearest 2 MHz; LC tank = BTO capacitor + ferrite-shell inductor (1 meridional turn) at working bias; "
+                                   "acoustic drive at the l=0 isolated-shell mode nearest 2 MHz; electric/magnetic: " + NO_DRIVE + "; "
                                    "outer surface held at 293 K (reference only, no sink chosen).",
                           phi=PHI, powers=POWERS, materials=MAT, ref_file="shell_phi_sweep_calc_output.txt (read-only)" if ref else None),
                 cases=cases)
diff --git a/solver_v0_output.txt b/solver_v0_output.txt
index 5ace99a..cec6998 100644
--- a/solver_v0_output.txt
+++ b/solver_v0_output.txt
@@ -1,12 +1,12 @@
-scope      OD 2.0 mm R_out 1.0 | l0 iso [1.855, 6.611] MHz | drive 1.855 MHz stress@100000W 751.8 MPa Qeff 2100.0 | f_e 1.855 MHz (0-bias 1.855) | T_gas mean 1073.0 K centre 1228.0 K p 4881.0 Pa c 1020.0 m/s @1W | T_qz_in 0.1W 433.8 K 1W 962.2 K, 100000W 3000.0 K | crossings 6
-minA       OD 3.0 mm R_out 1.5 | l0 iso [1.347, 3.745, 6.429] MHz | drive 1.347 MHz stress@100000W 540.0 MPa Qeff 2100.0 | f_e 1.347 MHz (0-bias 1.347) | T_gas mean 906.8 K centre 1081.0 K p 4126.0 Pa c 937.4 m/s @1W | T_qz_in 0.1W 382.8 K 1W 780.2 K, 100000W 3000.0 K | crossings 8
-minB       OD 2.0 mm R_out 1.0 | l0 iso [1.855, 6.611] MHz | drive 1.855 MHz stress@100000W 751.8 MPa Qeff 2100.0 | f_e 1.855 MHz (0-bias 1.855) | T_gas mean 1073.0 K centre 1228.0 K p 4881.0 Pa c 1020.0 m/s @1W | T_qz_in 0.1W 433.8 K 1W 962.2 K, 100000W 3000.0 K | crossings 6
-base5      OD 5.0 mm R_out 6.616 | l0 iso [0.686, 3.046, 5.86, 8.721] MHz | drive 3.046 MHz stress@100000W 190.3 MPa Qeff 2009.0 | f_e 1.621 MHz (0-bias 0.718) | T_gas mean 314.5 K centre 327.8 K p 108700.0 Pa c 552.0 m/s @1W | T_qz_in 0.1W 294.2 K 1W 305.3 K, 100000W 3000.0 K | crossings 7
-lock54     OD 5.4 mm R_out 7.14 | l0 iso [0.625, 3.018, 5.846, 8.711] MHz | drive 3.018 MHz stress@100000W 174.7 MPa Qeff 2016.0 | f_e 1.446 MHz (0-bias 0.640) | T_gas mean 312.4 K centre 324.3 K p 108100.0 Pa c 550.3 m/s @1W | T_qz_in 0.1W 294.1 K 1W 304.4 K, 100000W 3000.0 K | crossings 5
-lock25     OD 2.5 mm R_out 3.344 | l0 iso [1.614, 4.295, 6.709, 9.3] MHz | drive 1.614 MHz stress@100000W 662.3 MPa Qeff 1268.0 | f_e 4.515 MHz (0-bias 1.998) | T_gas mean 371.3 K centre 439.4 K p 12840000.0 Pa c 599.8 m/s @1W | T_qz_in 0.1W 295.9 K 1W 321.9 K, 100000W 3000.0 K | crossings 7
-phi1.6     OD 1.6 mm R_out 2.165 | l0 iso [2.06, 8.764] MHz | drive 2.060 MHz stress@100000W 1189.0 MPa Qeff 840.8 | f_e 8.667 MHz (0-bias 3.836) | T_gas mean 359.5 K centre 396.7 K p 124300.0 Pa c 590.3 m/s @1W | T_qz_in 0.1W 297.1 K 1W 333.6 K, 100000W 3000.0 K | crossings 8
-phi2.59    OD 2.59 mm R_out 3.461 | l0 iso [1.301, 5.668, 10.86] MHz | drive 1.301 MHz stress@100000W 743.9 MPa Qeff 1078.0 | f_e 4.286 MHz (0-bias 1.897) | T_gas mean 334.0 K centre 358.5 K p 115500.0 Pa c 568.9 m/s @1W | T_qz_in 0.1W 295.4 K 1W 317.2 K, 100000W 3000.0 K | crossings 6
-phi4.19    OD 4.19 mm R_out 5.556 | l0 iso [0.816, 3.607, 6.934, 10.31] MHz | drive 3.607 MHz stress@100000W 226.4 MPa Qeff 1981.0 | f_e 2.107 MHz (0-bias 0.933) | T_gas mean 318.5 K centre 334.3 K p 110200.0 Pa c 555.6 m/s @1W | T_qz_in 0.1W 294.5 K 1W 307.7 K, 100000W 3000.0 K | crossings 7
-phi6.78    OD 6.78 mm R_out 8.946 | l0 iso [0.509, 2.27, 4.372, 6.509] MHz | drive 2.270 MHz stress@100000W 140.9 MPa Qeff 2040.0 | f_e 1.031 MHz (0-bias 0.456) | T_gas mean 308.9 K centre 318.9 K p 106800.0 Pa c 547.1 m/s @1W | T_qz_in 0.1W 293.9 K 1W 302.1 K, 100000W 3000.0 K | crossings 9
-phi10.97   OD 10.97 mm R_out 14.43 | l0 iso [0.316, 1.419, 2.735, 4.074] MHz | drive 2.735 MHz stress@100000W 73.2 MPa Qeff 2080.0 | f_e 0.503 MHz (0-bias 0.223) | T_gas mean 303.0 K centre 309.3 K p 104800.0 Pa c 541.9 m/s @1W | T_qz_in 0.1W 293.6 K 1W 298.7 K, 100000W 3000.0 K | crossings 7
-phi17.75   OD 17.75 mm R_out 23.31 | l0 iso [0.196, 0.884, 1.703, 2.537] MHz | drive 1.703 MHz stress@100000W 45.31 MPa Qeff 2092.0 | f_e 0.245 MHz (0-bias 0.108) | T_gas mean 299.3 K centre 303.2 K p 103500.0 Pa c 538.5 m/s @1W | T_qz_in 0.1W 293.4 K 1W 296.6 K, 100000W 3000.0 K | crossings 7
+scope      OD 2.0 mm R_out 1.0 | l0 iso [1.855, 6.611] MHz | drive 1.855 MHz stress@100000W 751.8 MPa Qeff 2100.0 | electric: no drive | T_gas mean 1073.0 K centre 1228.0 K p 4881.0 Pa c 1020.0 m/s @1W | T_qz_in 0.1W 433.8 K 1W 962.2 K, 100000W 3000.0 K | crossings 4
+minA       OD 3.0 mm R_out 1.5 | l0 iso [1.347, 3.745, 6.429] MHz | drive 1.347 MHz stress@100000W 540.0 MPa Qeff 2100.0 | electric: no drive | T_gas mean 906.8 K centre 1081.0 K p 4126.0 Pa c 937.4 m/s @1W | T_qz_in 0.1W 382.8 K 1W 780.2 K, 100000W 3000.0 K | crossings 5
+minB       OD 2.0 mm R_out 1.0 | l0 iso [1.855, 6.611] MHz | drive 1.855 MHz stress@100000W 751.8 MPa Qeff 2100.0 | electric: no drive | T_gas mean 1073.0 K centre 1228.0 K p 4881.0 Pa c 1020.0 m/s @1W | T_qz_in 0.1W 433.8 K 1W 962.2 K, 100000W 3000.0 K | crossings 4
+base5      OD 5.0 mm R_out 6.616 | l0 iso [0.687, 3.048, 5.865, 8.728] MHz | drive 3.048 MHz stress@100000W 190.4 MPa Qeff 2010.0 | electric: no drive | T_gas mean 313.8 K centre 327.2 K p 108500.0 Pa c 551.5 m/s @1W | T_qz_in 0.1W 294.2 K 1W 304.7 K, 100000W 3000.0 K | crossings 3
+lock54     OD 5.4 mm R_out 7.139 | l0 iso [0.626, 3.02, 5.851, 8.719] MHz | drive 3.020 MHz stress@100000W 174.7 MPa Qeff 2017.0 | electric: no drive | T_gas mean 311.8 K centre 323.7 K p 107800.0 Pa c 549.7 m/s @1W | T_qz_in 0.1W 294.1 K 1W 303.7 K, 100000W 3000.0 K | crossings 3
+lock25     OD 2.5 mm R_out 3.343 | l0 iso [1.615, 4.298, 6.714, 9.308] MHz | drive 1.615 MHz stress@100000W 662.6 MPa Qeff 1268.0 | electric: no drive | T_gas mean 370.3 K centre 438.6 K p 12810000.0 Pa c 599.1 m/s @1W | T_qz_in 0.1W 295.8 K 1W 320.9 K, 100000W 3000.0 K | crossings 3
+phi1.6     OD 1.6 mm R_out 2.165 | l0 iso [2.063, 8.784] MHz | drive 2.063 MHz stress@100000W 904.4 MPa Qeff 841.1 | electric: no drive | T_gas mean 357.9 K centre 395.1 K p 123800.0 Pa c 588.9 m/s @1W | T_qz_in 0.1W 296.9 K 1W 331.8 K, 100000W 3000.0 K | crossings 3
+phi2.59    OD 2.59 mm R_out 3.461 | l0 iso [1.302, 5.676, 10.88] MHz | drive 1.302 MHz stress@100000W 562.7 MPa Qeff 1079.0 | electric: no drive | T_gas mean 333.1 K centre 357.5 K p 115200.0 Pa c 568.1 m/s @1W | T_qz_in 0.1W 295.3 K 1W 316.1 K, 100000W 3000.0 K | crossings 3
+phi4.19    OD 4.19 mm R_out 5.555 | l0 iso [0.816, 3.61, 6.941, 10.32] MHz | drive 3.610 MHz stress@100000W 226.5 MPa Qeff 1982.0 | electric: no drive | T_gas mean 317.8 K centre 333.6 K p 109900.0 Pa c 555.0 m/s @1W | T_qz_in 0.1W 294.4 K 1W 307.0 K, 100000W 3000.0 K | crossings 3
+phi6.78    OD 6.78 mm R_out 8.946 | l0 iso [0.509, 2.272, 4.374, 6.513] MHz | drive 2.272 MHz stress@100000W 140.9 MPa Qeff 2041.0 | electric: no drive | T_gas mean 308.4 K centre 318.4 K p 106600.0 Pa c 546.7 m/s @1W | T_qz_in 0.1W 293.9 K 1W 301.6 K, 100000W 3000.0 K | crossings 3
+phi10.97   OD 10.97 mm R_out 14.43 | l0 iso [0.316, 1.42, 2.736, 4.075] MHz | drive 2.736 MHz stress@100000W 73.21 MPa Qeff 2081.0 | electric: no drive | T_gas mean 302.6 K centre 308.9 K p 104600.0 Pa c 541.5 m/s @1W | T_qz_in 0.1W 293.5 K 1W 298.3 K, 100000W 3000.0 K | crossings 3
+phi17.75   OD 17.75 mm R_out 23.31 | l0 iso [0.196, 0.884, 1.704, 2.538] MHz | drive 1.704 MHz stress@100000W 45.31 MPa Qeff 2092.0 | electric: no drive | T_gas mean 299.0 K centre 302.9 K p 103400.0 Pa c 538.3 m/s @1W | T_qz_in 0.1W 293.3 K 1W 296.3 K, 100000W 3000.0 K | crossings 3
diff --git a/tests/test_drive_model_thermal.py b/tests/test_drive_model_thermal.py
index 59d63ec..1414b5f 100644
--- a/tests/test_drive_model_thermal.py
+++ b/tests/test_drive_model_thermal.py
@@ -1,7 +1,10 @@
 """drive_model.js thermal network: zero heat sources must give exactly zero rise above the seal temperature.
 
 The network is solved for theta = T - T_seal, so with no discharge energy (and ambient = seal) the right-hand side
-is exactly zero and every node stays at exactly T_seal (no rounding wander on the ~293 K baseline)."""
+is exactly zero and every node stays at exactly T_seal (no rounding wander on the ~293 K baseline).
+
+Electrodes were removed 2026-10-19 and no drive mechanism is defined: the drive stub must fail closed (zero deposited
+energy, zero ring amplitude, NO_DRIVE flag) for every fill. The former ionising control row went with the removed electrodes."""
 import json
 import shutil
 import subprocess
@@ -14,10 +17,11 @@ JS = r"""
 const D = require(process.argv[1]);
 const base = { ID_mm: 1, OD_mm: 2, T_seal: 293.15, shellModes: [{ name: "0S0 breathing (l=0)", f: 1.868e6 }] };
 const out = [];
-for (const [fill, V, f] of [[10, 600, 1000], [0.1, 600, 1000], [179, 600, 1000], [7600, 600, 1000], [22, 600, 1000]]) {
-  const r = D.run(Object.assign({}, base, { fill_Torr: fill, V_amp: V, f }), { ncyc: 200, nlog: 40 });
+for (const [fill, f] of [[10, 1000], [0.1, 1000], [179, 1000], [7600, 1000], [22, 1000]]) {
+  const r = D.run(Object.assign({}, base, { fill_Torr: fill, f }), { ncyc: 200, nlog: 40 });
   const off = r.tr.Tg.concat(r.tr.Twin, r.tr.Twout).filter(x => x !== base.T_seal).length;
-  out.push({ fill, E: r.E_dis, dTg: r.dTg, dTw: r.dTw, off });
+  const ringMax = Math.max(0, ...r.ring.map(m => Math.abs(m.amp)));
+  out.push({ fill, E: r.E_dis, dTg: r.dTg, dTw: r.dTw, off, ringMax, noDrive: r.flags.some(x => x === D.NO_DRIVE || String(x).includes("no drive mechanism defined")) });
 }
 console.log(JSON.stringify(out));
 """
@@ -28,11 +32,14 @@ def test_zero_source_gives_exactly_zero_rise(root, record):
     res = subprocess.run([NODE, "-e", JS, str(root / "drive_model.js")], capture_output=True, text=True, check=True)
     rows = json.loads(res.stdout)
     for r in rows:
-        if r["E"] == 0:
-            ok = r["dTg"] == 0 and r["dTw"] == 0 and r["off"] == 0
-            record(f"drive model zero-source rise, fill {r['fill']} Torr (dT_gas, dT_wall, nodes off T_seal)",
-                   "0, 0, 0", f"{r['dTg']}, {r['dTw']}, {r['off']}", "exact", "drive_model.js run()", ok=ok)
-            assert ok, r
-        else:
-            assert r["dTg"] > 0 and r["dTw"] > 0, r   # ionising control row still heats
-    assert any(r["E"] == 0 for r in rows) and any(r["E"] > 0 for r in rows)
+        ok = r["E"] == 0 and r["dTg"] == 0 and r["dTw"] == 0 and r["off"] == 0
+        record(f"drive model zero-source rise, fill {r['fill']} Torr (E, dT_gas, dT_wall, nodes off T_seal)",
+               "0, 0, 0, 0", f"{r['E']}, {r['dTg']}, {r['dTw']}, {r['off']}", "exact", "drive_model.js run()", ok=ok)
+        assert ok, r
+
+
+@pytest.mark.skipif(NODE is None, reason="node not installed")
+def test_no_drive_stub_fails_closed(root):
+    res = subprocess.run([NODE, "-e", JS, str(root / "drive_model.js")], capture_output=True, text=True, check=True)
+    for r in json.loads(res.stdout):
+        assert r["E"] == 0 and r["ringMax"] == 0 and r["noDrive"], r
diff --git a/viewer_template.html b/viewer_template.html
index 2e3c97d..43c34e0 100644
--- a/viewer_template.html
+++ b/viewer_template.html
@@ -69,11 +69,11 @@ table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #222a3a;
   <div class="row"><span class="lab">Fill: HHO amount</span><input id="dFill" type="number" placeholder="required" style="width:90px"><select id="dFillU"><option value="torr">Torr at sealing</option><option value="mol">molecules</option></select>
    <span class="lab">initial (sealing) T</span><input id="dTs" type="number" value="293.15" style="width:64px"><span class="lab">K &mdash; initial condition, not a control</span>
    <span class="lab">ambient T</span><input id="dTa" type="number" placeholder="= sealing T" style="width:76px"><span class="lab">K (still air around the bubble; blank = sealing T)</span></div>
-  <div class="row"><span class="lab">Drive: amplitude</span><input id="dV" type="number" placeholder="required" style="width:70px"><span class="lab">V peak (applied, DBD 50 &micro;m centre electrode [est])</span></div>
+  <div class="row"><span class="lab">Drive</span><span class="lab">no drive mechanism defined (deposits zero energy; drive method open)</span></div>
   <div class="row"><span class="lab">EMF frequency</span><input id="dF" type="text" placeholder="unset, e.g. 2.5M" style="width:90px"><span class="lab">Hz (suffix k M G T P)</span><span class="small">one cycle, duration 1/f = <span id="dT">&ndash;</span></span></div>
   <div class="row"><input type="range" id="dFs" min="0" max="1000" value="500" list="dFticks" style="width:540px;margin:0"><datalist id="dFticks"><option value="0"><option value="100"><option value="200"><option value="300"><option value="400"><option value="500"><option value="600"><option value="700"><option value="800"><option value="900"><option value="1000"></datalist></div>
   <canvas id="dFax" width="540" height="58" style="background:#0d111a;border:1px solid #2a3244"></canvas>
-  <div class="small">log slider 100 kHz &ndash; 1000 THz, decade ticks; marked: natural acoustic modes (cyan), Balmer H&alpha;&ndash;H&delta; (white), visible band, quasi-static limit / EM resonance / breakdown-formation limit (dashed). Slider position means nothing until you move it or type a value.</div>
+  <div class="small">log slider 100 kHz &ndash; 1000 THz, decade ticks; marked: natural acoustic modes (cyan), Balmer H&alpha;&ndash;H&delta; (white), visible band, quasi-static limit / EM resonance. Slider position means nothing until you move it or type a value.</div>
   <div id="dReg"></div>
   <div class="row"><span class="lab">Sound speeds</span><select id="dQz"><option value="vrh">quartz &alpha; VRH aggregate 6048/4090 m/s [lit]</option><option value="z">quartz single crystal &parallel;Z 6330/4685 [lit]</option><option value="x">quartz single crystal &parallel;X 5710/5200 [lit]</option><option value="danny">Danny 5900 m/s (cT 4090 VRH)</option><option value="v0">v0/v0.2 6153/4210 [rec]</option></select></div>
   <div id="dQzSrc" class="small"></div>
@@ -103,7 +103,7 @@ import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
 const D = window.MODEL;
 const DOMS = ['optical','acoustic','electric','magnetic','thermal','chemical']; const SECT=360/DOMS.length;
 const DCOL = {optical:'#ffd34d',acoustic:'#33d1ff',electric:'#ff4fd8',magnetic:'#59ff7a',thermal:'#ff6a3d',chemical:'#b98cff'};
-const LCOL = {core:'#2b3f73',quartz:'#cfe8ff',layer2:'#e8a6c8',phos_in:'#b6ff7a',tipt:'#c0c0c0',bto:'#ffcc66',gddy:'#8888aa',calorivac:'#8a6d4a',phos_out:'#ffe680',ferrite:'#454552'};
+const LCOL = {core:'#2b3f73',quartz:'#cfe8ff',layer2:'#e8a6c8',phos_in:'#b6ff7a',bto:'#ffcc66',gddy:'#8888aa',calorivac:'#8a6d4a',phos_out:'#ffe680',ferrite:'#454552'};
 const $ = id => document.getElementById(id);
 const fmt = (x,n=3) => (x===null||x===undefined)?'–':(Math.abs(x)>=1e4||Math.abs(x)<1e-2&&x!==0)?x.toExponential(n-1):(+x).toPrecision(n);
 const fmtF = f => f>=1e12?(f/1e12).toPrecision(4)+' THz':f>=1e9?(f/1e9).toPrecision(4)+' GHz':f>=1e6?(f/1e6).toPrecision(4)+' MHz':f>=1e3?(f/1e3).toPrecision(4)+' kHz':(+f).toPrecision(3)+' Hz';
@@ -234,7 +234,7 @@ function updateCut(t){
     if(o.wave){ o.bead.visible=false; fillWave(o.wave,o.v.domain,t,(r,y)=>o.d.clone().multiplyScalar(mmToWorld(r)).add(o.perp.clone().multiplyScalar(y*0.05))); }});
 }
 function frontFraction(dom,t){ // fraction of the vector the domain front has covered by time t (true-scale propagation)
-  const v=PD.vectors.find(x=>x.domain===dom); const P=propForDomain(dom); const r=Math.min(frontRadius(P,t),v.r_end_mm);
+  const v=PD.vectors.find(x=>x.domain===dom); if(!v) return 0; /* no vector: no drive mechanism defined */ const P=propForDomain(dom); const r=Math.min(frontRadius(P,t),v.r_end_mm);
   return Math.max(0,Math.min(1,(r-v.r_start_mm)/Math.max(v.r_end_mm-v.r_start_mm,1e-9)));}
 
 // ---------------- waveforms (HHO core -> quartz OD only) ----------------
@@ -297,7 +297,7 @@ function legendHTML(){ const sel=[$('f0').value,$('f1').value,$('f2').value];
 
 // ---------------- propagation model (true scale, mm & s) ----------------
 const MATN={quartz:1.554,layer2:1.42,phos_in:1.8,bto:2.4,phos_out:1.41}; // optical index (rec/est); metals absorb
-const EPSRF={quartz:4.5,layer2:3.5,phos_in:8,bto:450,tipt:1e9,gddy:1e9,calorivac:6,phos_out:3,ferrite:12}; // RF permittivity [est]
+const EPSRF={quartz:4.5,layer2:3.5,phos_in:8,bto:450,gddy:1e9,calorivac:6,phos_out:3,ferrite:12}; // RF permittivity [est]
 function mediaList(){ const L=[{key:'gas',a:0,b:C.propagation.r_in_mm}]; C.layers.forEach(l=>{ if(l.key!=='core') L.push({key:l.key,a:l.a_mm,b:l.b_mm}); }); L.push({key:'air',a:C.R_outer_mm,b:C.R_outer_mm*1.6}); return L;}
 function propForDomain(dom){
   const pr=C.propagation, M=D.meta.materials, segs=[];
@@ -315,8 +315,8 @@ function arrivalTime(segs,r){ // r in mm
   return segs[0].alpha!=null? s*s : t;}
 function frontRadius(segs,t){ let lo=0, hi=segs[segs.length-1].b; if(arrivalTime(segs,hi)<=t) return hi;
   for(let k=0;k<50;k++){const m=0.5*(lo+hi); if(arrivalTime(segs,m)<=t) lo=m; else hi=m;} return lo;}
-function domainFreq(dom){ if((dom==='electric'||dom==='magnetic') && window.DRIVE_F) return window.DRIVE_F; if(dom==='optical') return 2.998e8/486.1e-9; if(dom==='acoustic') return PD.acoustic.f_drive; if(dom==='thermal'||dom==='chemical') return 2*(window.DRIVE_F||PD.electric.f_e); return PD.electric.f_e; }
-function termRadius(dom){ const v=PD.vectors.find(x=>x.domain===dom); const r= dom==='optical'&&C.propagation.bare? C.R_outer_mm*1.5 : v.r_end_mm; return ($('wf')&&$('wf').checked)? Math.min(r,C.OD_quartz_mm/2) : r; }
+function domainFreq(dom){ if((dom==='electric'||dom==='magnetic') && window.DRIVE_F) return window.DRIVE_F; if(dom==='optical') return 2.998e8/486.1e-9; if(dom==='acoustic') return PD.acoustic.f_drive; if(dom==='thermal'||dom==='chemical'){ if(window.DRIVE_F) return 2*window.DRIVE_F; const v=PD.vectors.find(x=>x.domain===dom); return (v&&v.f_start)||0; } return PD.electric.f_e||0; /* 0: no drive mechanism defined */ }
+function termRadius(dom){ const v=PD.vectors.find(x=>x.domain===dom); if(!v) return 0; const r= dom==='optical'&&C.propagation.bare? C.R_outer_mm*1.5 : v.r_end_mm; return ($('wf')&&$('wf').checked)? Math.min(r,C.OD_quartz_mm/2) : r; }
 
 // ---------------- orthographic scene ----------------
 let orthoSectors=[], orthoFronts=[], orthoWaves=[], OSC=1;
@@ -430,10 +430,10 @@ function drawSpec(){
   PD.acoustic.l0_isolated.forEach(f=>hline(f,mmToDisp(V.acoustic.r_start_mm),mmToDisp(V.acoustic.r_end_mm),DCOL.acoustic));
   (PD.acoustic.gas_cavity_modes||[]).slice(0,4).forEach(f=>hline(f,0,mmToDisp(C.propagation.r_in_mm),'#7fb2ff',false,1));
   Object.entries(C.acoustic_ref_l_ge_1||{}).forEach(([k,f])=>{ if(typeof f==='number' && /S|T/.test(k) && !k.includes('stress')) hline(f,mmToDisp(V.acoustic.r_start_mm),mmToDisp(V.acoustic.r_end_mm),DCOL.acoustic,true,1);});
-  // electric band
-  const fe0=PD.electric.f_zero_bias, fe=PD.electric.f_e; const x0=X(mmToDisp(V.electric.r_start_mm)), x1=Math.max(X(mmToDisp(V.electric.r_end_mm)),x0+4);
+  // electric band (absent: no drive mechanism defined)
+  if(V.electric){ const fe0=PD.electric.f_zero_bias, fe=PD.electric.f_e; const x0=X(mmToDisp(V.electric.r_start_mm)), x1=Math.max(X(mmToDisp(V.electric.r_end_mm)),x0+4);
   g.fillStyle=DCOL.electric+'55'; g.fillRect(x0,Math.min(Y(fe0),Y(fe))-2,x1-x0,Math.abs(Y(fe0)-Y(fe))+4); hline(fe,mmToDisp(V.electric.r_start_mm),mmToDisp(V.electric.r_end_mm),DCOL.electric);
-  if(!C.propagation.bare) hline(fe,mmToDisp(V.magnetic.r_start_mm),mmToDisp(V.magnetic.r_end_mm),DCOL.magnetic,false,3);
+  if(!C.propagation.bare && V.magnetic) hline(fe,mmToDisp(V.magnetic.r_start_mm),mmToDisp(V.magnetic.r_end_mm),DCOL.magnetic,false,3); }
   if(V.chemical) hline(V.chemical.f_start,0,mmToDisp(V.chemical.r_end_mm),DCOL.chemical);   // chemical: discharge-pulse rate, core only
   // thermal track
   g.strokeStyle=DCOL.thermal; g.lineWidth=2; g.beginPath(); PD.thermal_track.forEach(([r,f],i)=>{ if(!f) return; const x=X(mmToDisp(r)), y=Y(f); i?g.lineTo(x,y):g.moveTo(x,y);}); g.stroke(); g.lineWidth=1;
@@ -451,10 +451,10 @@ function fillSide(){
   $('nums').innerHTML = `<table>
    <tr><td>Geometry</td><td>gas core d ${C.core_d_mm} mm (${C.fill}, ${(C.p_atm*760).toPrecision(3)} Torr = ${C.p_atm.toPrecision(3)} atm); quartz wall ${C.wall_mm} mm; quartz OD ${C.OD_quartz_mm} mm; outer R ${C.R_outer_mm} mm</td></tr>
    <tr><td>Acoustic</td><td>l=0 shell modes ${a.l0_isolated.slice(0,4).map(fmtF).join(', ')}; HHO gas-cavity modes ${(a.gas_cavity_modes||[]).slice(0,3).map(fmtF).join(', ')}; drive ${fmtF(a.f_drive)}; W ${fmt(a.W_mJ)} mJ; peak stress ${fmt(a.peak_stress_MPa)} MPa; Q_eff ${fmt(a.Q_eff)}; loss ${fmt(a.loss_W)} W; fill-pressure hoop ${fmt(a.fill_stress_MPa)} MPa${a.bonded?`; bonded stack: ${fmtF(a.bonded.f)}, Q ${fmt(a.bonded.Q_eff)}, loss ${fmt(a.bonded.loss_W)} W`:''}</td></tr>
-   <tr><td>Electric</td><td>${C.propagation.bare?`DBD C ${fmt(e.C_fF)} fF, V ${fmt(e.V_pk)} V, drive ${fmtF(e.f_e)}`:`C0 ${fmt(e.C0_nF)} nF → ${fmt(e.C_bias_nF)} nF at bias; tank ${fmtF(e.f_zero_bias)} → ${fmtF(e.f_e)}; V_pk ${fmt(e.V_pk)} V (working ${fmt(e.V_work)} V); I_rms ${fmt(e.I_rms)} A; loss diel ${fmt(e.P_diel)} W + ESR ${fmt(e.P_esr)} W; Q_tank ${fmt(e.Q_tank)}; hot: f ${fmtF(e.hot.f_e)}`}</td></tr>
+   <tr><td>Electric</td><td>${e.none?e.note:'n/a'}</td></tr>
    <tr><td>Magnetic</td><td>${m.none?m.note:`L ${fmt(m.L_nH)} nH (1 turn); Q_f ${fmt(m.Q_f)}; ferrite loss ${fmt(m.P_ferr)} W; B equator ${fmt(m.B_eq_mT)} mT, near feed holes ${fmt(m.B_max_mT)} mT`}</td></tr>
    <tr><td>Optical</td><td>Balmer out of core ${fmt(o.P_opt)} W; downshifted ${fmt(o.converted_W)} W; escaping ${fmt(o.escaped_W)} W</td></tr>
-   ${PD.gas?`<tr><td>HHO gas state (computed, coupled)</td><td>T_gas ${fmt(PD.gas.T_gas_K)} K [est = inner wall, lower bound]; sealed ${fmt(PD.gas.p_seal_Pa)} Pa at ${PD.gas.T_seal_K} K → p ${fmt(PD.gas.p_hot_Pa)} Pa (fixed N, V); c ${fmt(PD.gas.c_seal)} → ${fmt(PD.gas.c_hot)} m/s; hot gas-loaded modes ${(PD.gas.gas_modes_hot||[]).slice(0,3).map(fmtF).join(', ')}; Paschen knee ∝ n·d (unchanged to first order)</td></tr>`:''}
+   ${PD.gas?`<tr><td>HHO gas state (computed, coupled)</td><td>T_gas ${fmt(PD.gas.T_gas_K)} K [est = inner wall, lower bound]; sealed ${fmt(PD.gas.p_seal_Pa)} Pa at ${PD.gas.T_seal_K} K → p ${fmt(PD.gas.p_hot_Pa)} Pa (fixed N, V); c ${fmt(PD.gas.c_seal)} → ${fmt(PD.gas.c_hot)} m/s; hot gas-loaded modes ${(PD.gas.gas_modes_hot||[]).slice(0,3).map(fmtF).join(', ')}</td></tr>`:''}
    ${PD.chemical?`<tr><td style="color:${DCOL.chemical}">Chemical</td><td>stored 2H2+O2→2H2O ${fmt(PD.chemical.E_store_J)} J; dissociation ${fmt(PD.chemical.P_diss_W)} W ⇒ ${fmt(PD.chemical.R_diss_per_s)} H2/s; fill converted in ${fmtT(PD.chemical.t_conv_s)} releasing ${fmt(PD.chemical.P_release_W)} W meanwhile (fed to thermal); wall recombination ${fmt(PD.chemical.P_wall_recomb_W)} W; H diffusion τ ${fmtT(PD.chemical.tau_D_s)}; <b>knee: not defined</b>. <span class="small">${PD.chemical.sources}</span></td></tr>`:''}
    <tr><td>Thermal (steady)</td><td>quartz inner ${fmt(t.T_quartz_in)} K / outer ${fmt(t.T_quartz_out)} K; wall ΔT ${fmt(t.dT_wall)} K${C.propagation.bare?'':`; phosphor ${fmt(t.T_phos)} K; BTO ${fmt(t.T_bto)} K; Gd-Dy ${fmt(t.T_gddy)} K; CALORIVAC max ${fmt(t.T_calorivac_max)} K`}; total heat ${fmt(t.total_heat_W)} W</td></tr></table>`;
   $('flags').innerHTML = PD.flags.length? PD.flags.map(f=>`<div class="flag">⚠ ${f}</div>`).join('') : '<div class="ok">No limit crossed at this power (estimated physics).</div>';


=== QUESTION (again) ===
Danny has recorded his decisions on your round-5 review in the attached diff. How should he complete the feedback loop in the holster: what is still missing to fully close it, what should happen next and in what order, and do you disagree with any decision or how it was recorded?