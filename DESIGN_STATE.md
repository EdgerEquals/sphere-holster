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
- **Ionisation knee:** about 10 Torr for a 1 mm gap, or about 22 Torr with a central electrode (0.45 mm gap).
- **Electrodes:** a metal film on the inner wall screens the gas. Ionising it needs a central electrode (DBD, dielectric barrier discharge) or an external field.

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
- **Binder:** a silica sol-gel (MTES:TEOS 80:20). Pt needs a 10 nm SiO₂ or TiO₂ primer, and the tourmaline needs a silica shell formed at pH 8–9.

### Layer 4: downshifting phosphor
- **Options:** KSF, which saturates at about 8–16 W, or CASN, which saturates at about 80 W.

### Layer 5: outer layer
- **Nonlinear option:** PPLN or KDP. Either gives real gain only with a coherent pump at the megawatt level.
- **Magnetic or caloric option:** ferrite, Gd-Dy or CALORIVAC.
- **Heat sink:** Danny's choice, still open.

## Open
1. Which quartz shell: the 5.4 mm lock shell, the 6.78 mm φ shell, or the 1×2 mm test shell. Sphere or tube.
2. The heat path. At 1 W in still air, the test shell's inner wall gets past HHO autoignition.
3. The BTO thickness, and how to keep it below its Curie point.
4. The tourmaline thickness, traded against scattering at 434 nm. Also the cure temperature and whether it sits inside or outside the BTO.
5. Which phosphor, and whether the electrodes sit in layer 4. Ti/Pt blocks light, and that is the main source of heat.
6. Which layer 5 option.
7. The HHO fill amount.
8. Central electrode or external field.

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

---

## Information layer (harness architecture)
Full spec: the Drive doc "Stratified Sphere — Information Layer (Harness Architecture) 2026-10-19".

- **Harnesses:** 18 in total. There are 6 domain harnesses (optical, acoustic, electric, magnetic, thermal and chemical), which run in parallel on GitHub Actions and pass results to each other between rounds. There are also 12 knee harnesses.
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
Danny locked these four items on 2026-10-19 from review round 3 (`reviews/2026-10-19_round3/`). Treat them as decided; do not re-open them without Danny. Status updated 2026-10-19 14:15 AWST: items 1–3 built, item 4 partial. Details: `ledger/README.md`, `gateway/README.md`.

| # | Item | What it is | Source | Order | Status |
|---|---|---|---|---|---|
| 1 | GitHub review ledger | Every review finding is filed as a GitHub issue and appended to a permanent, append-only JSONL log; reviewers are scored from it. | Round 3: DeepSeek, Claude and Grok's top pick (Kimi's runner-up); closes round 2's "review loop doesn't close" gap | **First.** Everything else builds on it. | **built** (issue #7): `ledger/findings.jsonl` on main, schema v1, workflow `ledger.yml`; issue mirroring off by default (dispatch, threshold major, cap 5/day) |
| 2 | Scoring rubric (planted mistakes) | Each reviewer is scored on whether it catches mistakes deliberately planted in the work it reviews. | DeepSeek's round-2 idea (seed known defects), made concrete per Claude's round-3 suggestion (score reviewers from ledger status) | On top of the ledger | **built** (issue #8): fixture `ledger/planted/v1`, `ledger-score.yml` (offline default); no paid planted run yet |
| 3 | Monthly cost rollup per model | Spend per model per month, rolled up from the ledger's cost stamps, so spend per model is visible. | Grok's round-3 suggestion (a cost stamp on every ledger record) | On top of the ledger | **built** (issue #9): `ledger/costs_YYYY-MM.*`, `ledger-costs.yml` (monthly cron + dispatch), Pages `ledger/`; October backfilled |
| 4 | FEniCS/OpenFOAM MCP gateway | Models drive simulations directly through an MCP gateway to the open simulation stack (sandboxed). | Kimi's round-3 top pick; Claude and Grok's runner-up (after the ledger) | **After the ledger** | **partial** (issue #10): hardened FEniCS + OpenFOAM MCP containers pass CI (`mcp-gateway.yml`) and log to the ledger, but expose only the existing smoke tests; upstream dolfinx-mcp failed to initialise in CI |

Build order: (1) ledger → (2) rubric and (3) cost rollup on top of the ledger → (4) gateway after the ledger.

### Open tasks
- **Fix the ordering gap (review layer ahead of execution layer)** (issue #11). The harness can audit work that doesn't exist yet. **Status: round 4 run 2026-10-19 as the first test of the new holster version (`reviews/2026-10-19_round4/`, $0.044). Pending Danny's decision; nothing adopted or built from it.** Three of the four models (DeepSeek, Claude, Grok) proposed a CI-written execution receipt in the ledger plus a separate spec-review class; Kimi proposed stub harnesses with locked I/O schemas.

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
