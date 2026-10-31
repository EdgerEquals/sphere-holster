# Harness context

**What this document is:** the first stop for questions about the harness. In this project the harness, also called the rig, is the multi-harness software architecture the Ensemble works through. Section 1 describes it, and section 2 describes the sphere code.

**If this document does not answer your question:** ask Claude Code, with `ask_claude_code`, or with `request_info` using scope `rig` or `repo`. He checks the harness live and read-only: he reads, greps and searches the repo files at the time you ask. He has no shell, cannot edit files and has no web access. If neither source has the answer, say what is missing rather than guessing.

## 1. The harness (rig)

The harness is software. Its parts are listed below.

| Part | Where | What it does |
|---|---|---|
| Round runner | `scripts/launch_round.py` | Runs a round. |
| Model callers | `scripts/review_kimi.py`, `review_deepseek.py`, `review_claude.py`, `review_grok.py`, `review_build.py`, `review_claude_code.py` | Send a brief to one model and collect its reply. `scripts/land_review_reply.py` writes each reply into the round folder. |
| Model tools | `scripts/tool_loop.py` | The tools a model can call while answering (listed below). |
| Information layer | `scripts/harness_router.py`, `scripts/harness_store.py` | Routes each tool request through the levels that can answer it. Fetched answers are parked in a per-round shared store. Requests for the same item wait for one fetch (waiters queue). |
| Claude Code route | `scripts/review_claude_code.py` | Sends repo and rig questions to Claude Code. He runs read-only: read, grep and file search only. |
| Web search | `scripts/tavily_search.py` | One shared search slot. It answers `external` questions. |
| Ledger | `ledger/findings.jsonl`, `scripts/ledger*.py` | Append-only record, one JSON object per line, written only by CI. Monthly cost rollups per model are in `ledger/costs_YYYY-MM.json` and `.md`. |
| Simulation gateway | `gateway/`, `sim/` | `sim/` holds one smoke test per external simulation tool, each checked against an analytic answer: FEniCSx (DOLFINx 0.11.0), MEEP 1.35.0, OpenFOAM v2512, CalculiX 2.21, Code_Aster 18.1.0 and Gwyddion 2.64. The CI workflow is `.github/workflows/sim-stack.yml`. `gateway/ssm_mcp_server.py` is an MCP server with the tools `list_sim_tools`, `fenics_poisson_smoke` and `openfoam_cavity_smoke`. Its containers run with no network, a read-only root filesystem, a non-root user, all capabilities dropped and `sim/` mounted read-only. |

**Tools a model can call:**
- `read_doc(name)` returns `harness_context` (this document) or `vocabulary` (`docs/vocabulary.md`).
- `request_info(question, scope)` takes scope `repo`, `rig` or `external`. `external` questions may be answered by web search. `repo` and `rig` questions go to Claude Code. Answers already in the store come back directly.
- `ask_claude_code(question)` sends the question to Claude Code.

## 2. The sphere code

The sphere does not exist in hardware yet. The sphere code is the program that models it and visualises its waveforms: a solver, sweeps and a browser viewer.

### 2.1 Layout

| Path | What it is |
|---|---|
| `solver_v0.py` | Radial (l = 0) multi-domain coupled solver. Writes `model_data_v0.json` and `solver_v0_output.txt`. |
| `build.py` | Assembles the viewer `index.html` from `viewer_template.html`, `drive_model.js`, `drive_ui.js` and `model_data_v0.json`. The viewer uses Three.js, loaded from a CDN. |
| `drive_model.js` | Single-cycle drive model for the bare gas bubble. It runs in the browser and in node, and its drive source deposits no energy. |
| `geometry_sweep_v0.py` | Geometry sweep (bubble radius, quartz wall, layer-two thickness) for mode locking. Writes `geometry_sweep_v0.json` only. |
| `geometry_fill_sweep_v0.py` | Geometry × fill-pressure sweep. Writes `geometry_rarefied_hho_sweep_v0.json` only. |
| `tests/` | pytest suite for the solver, the sweeps and the harness scripts. |
| `docs/vocabulary.md` | The glossary. |

### 2.2 The solver (`solver_v0.py`)

**Status in the code:** estimated physics in a paper model; nothing in it is measured. Every material value carries a tag: `[lit]` published, `[rec]` reused from another project report, `[calc]` computed, `[est]` estimate.

**Units:** SI throughout, with temperatures in kelvin. The reference temperature is 293 K.

**Layer stack, inside out, built by `build_stack()`:**
1. gas core (HHO);
2. crystal quartz wall (layer one);
3. layer two: elbaite in a sol-gel binder (default thickness 9.12441 µm);
4. BaTiO3 (BTO) film, 2 µm;
5. Gd-Dy film, 3 µm;
6. CALORIVAC layer;
7. outer phosphor, 30 µm;
8. NiZn ferrite shell.

Layers 6–8 are sized from the BTO outer radius by fixed ratios (`PHI`, `PHI**2`). "Bare" presets have the gas core and quartz wall only.

**Gas:** the code fixes the composition as HHO, H2:O2 = 2:1 (`GAS_COMP = "HHO"`, mole fractions 2/3 and 1/3). `gas_props(T, p)` gives the gas properties. `gas_Q(f, a, p, T)` gives the Q of a gas-cavity mode (wall thermal boundary layer plus classical bulk absorption). The sweep scripts call the solver's `gas_Q` and `gas_props` and do not compute gas Q themselves.

**Domains:**
- **Acoustic:** exact l = 0 multilayer elastic spherical-shell model (spherical Bessel transfer matrices). The mode search window is 1 Hz–50 MHz (`FMIN_HZ`, `FMAX_HZ`) on a 20 000-point grid. There are two configurations: isolated (quartz plus thin films) and bonded (whole stack). Gas-loaded roots are split into shell modes and gas-cavity modes. l ≥ 1 modes are not computed.
- **Optical:** 1-D radial radiative march in three bands: 434, 486 and 656 nm.
- **Electric:** radial field marched from zero: ε dE/dt + σE = −dP/dt − J_src. P is the pyroelectric polarisation of the polar layers (layer two, BTO). The piezoelectric term enters at each acoustic mode frequency.
- **Magnetic:** B = 0 in spherical symmetry, because radial E and radial currents have no curl.
- **Thermal:** 1-D radial finite volume, implicit, with k(T) for quartz and interface resistances. Full-stack presets hold the outer surface at 293 K. Bare presets use natural convection plus radiation to still air.
- **Couplings:** piezoelectric, pyroelectric and electrocaloric. Fast domains are solved quasi-statically and passed to the thermal transient as heat sources, and temperature feeds back at each macro step.

**Drive:** `run_case(preset, ref, drive_W=0.0)` takes an optional power input, `drive_W`. `drive_W` defaults to 0. For `drive_W > 0`, thermal, electric, magnetic and acoustic each receive `drive_W` watts. Acoustic power is split equally across the computed l = 0 modes in the window. Electric is a volumetric current source in the BTO film. Thermal is heat into the gas core. Magnetic is deposited as heat in the ferrite (placeholder).

**Presets (`PRESETS`):**

| id | Core d (mm) | Wall (mm) | Fill (atm) | Stack |
|---|---|---|---|---|
| preset C | 1.0 | 0.5 | 0.01316 (10 Torr) | bare |
| `minA` | 1.0 | 1.0 | 0.01316 | bare |
| `minB` | 1.0 | 0.5 | 0.01316 | bare |
| `base5` | 1.1459 | 1.43463 | 0.10439 (10 577.3 Pa) | full, layer two 9.12441 µm |
| preset A | 3.4 | 1.0 | 1.0 | full |
| preset B | 0.5 | 1.0 | 100 | full |
| `phi1.6` … `phi17.75` | 0.6 × quartz OD | 0.2 × quartz OD | 1.0 | full; quartz OD 1.6, 2.59, 4.19, 6.78, 10.97, 17.75 mm |

### 2.3 Sweeps

- **`geometry_sweep_v0.py`** sweeps bubble radius a, quartz wall w and layer-two thickness t2 on a lattice. There is no source, so every mode energy is zero. It scores how many l = 0 modes of different cavities (gas bubble, quartz, layer two, bonded stack) overlap within their own linewidths (f/Q). Options: `--workers`, `--refine-top`, `--out`.
- **`geometry_fill_sweep_v0.py`** runs the same evaluation with fill pressure as a second axis. The gas is fixed at HHO 2:1. Pressure is a factor × local ambient, with nine log-spaced factors from 0.05 to 0.95, all below ambient. Ambient pressure and temperature are command-line inputs, recorded in the output JSON. Options: `--p-ambient` (Pa, default 101325), `--T-ambient` (K, default 293), `--workers`, `--refine-top`, `--out`.

### 2.4 How to run

From the repo root, with Python 3.12 and `pip install -r requirements.txt` (numpy, scipy, sympy, mpmath, pytest, PyYAML):

```bash
python solver_v0.py                         # all presets -> model_data_v0.json, solver_v0_output.txt
python solver_v0.py --only base5,minA       # selected presets
python solver_v0.py --core-d 1.0 --wall 0.5 --p-atm 0.0132   # custom preset (mm, mm, atm)
python solver_v0.py --build                 # also write index.html (viewer)
python solver_v0.py --tourmaline all        # layer-two end-member sweep -> tourmaline_sweep_v0.json
python geometry_sweep_v0.py --out geometry_sweep_v0.json
python geometry_fill_sweep_v0.py --p-ambient 101325 --T-ambient 293
pytest                                      # test suite
```

`--qz-sound <set>` selects the crystal-quartz sound-speed set (`QZ_SOUND` in `solver_v0.py`; default `vrh`).
