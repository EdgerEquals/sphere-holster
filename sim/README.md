# Simulation stack smoke tests (CI)

Workflow: `.github/workflows/sim-stack.yml`, one independent job per tool.
Runs on push to `main` touching `sim/**` or the workflow, on manual dispatch
(Actions tab -> sim-stack -> Run workflow), and weekly (Monday 03:17 Perth).
Each test checks an analytic answer, prints `expected / got`, writes a table
to the job summary, and exits non-zero on any mismatch.

| Tool | Pinned version | How it is installed in CI | Smoke test (analytic check) |
|---|---|---|---|
| FEniCSx | DOLFINx 0.11.0, `dolfinx/dolfinx:v0.11.0@sha256:2ae4bfbc…fa8` | official Docker image | `fenics/smoke_fenics.py`: Poisson, exact P2 solution (L2 err < 1e-10); sin·sin solution on a 32x32 P1 mesh (L2 err < 2e-3, convergence rate 2 ± 0.15); 1D steady heat, T_max = qL²/8k |
| MEEP | pymeep 1.35.0 `nompi_py312h7a316d3_100`, Python 3.12.15 (conda-forge) | `setup-micromamba` + `meep/environment.yml` (cached) | `meep/smoke_meep.py`: 2D PEC cavity 1.0 x 0.8, Harminv TM11/TM21 within 0.5 % of f = ½·√((m/a)²+(n/b)²) |
| OpenFOAM | OpenFOAM v2512 (ESI/OpenCFD), `opencfd/openfoam-default:2512@sha256:33fb575a…19e` | official Docker image | `openfoam/run_cavity.sh` + `check_cavity.py`: icoFoam lid-driven cavity to t = 0.5 s; End reached, Ux/p residual < 1e-4, continuity < 1e-7, 0.1 < max\|U\| < lid speed, 400 cells |
| CalculiX | ccx 2.21 (`calculix-ccx=2.21-1`, Ubuntu 24.04) | apt | `calculix/smoke_calculix.py`: B32 cantilever, tip deflection vs PL³/3EI = 1.52381 mm within 2 % |
| Code_Aster | 18.1.0, `simvia/code_aster:18.1.0@sha256:4629a21a…435` (~1.5 GB) | official Docker image | `code_aster/cantilever.*` + `check_aster.py`: POU_D_E cantilever, tip DY vs PL³/3EI within 0.01 %; also runs bundled `forma01a` if the image ships the test suite |
| Gwyddion | 2.64 (`gwyddion=2.64-1.1build3`, `libgwyddion20-dev`, Ubuntu 24.04) | apt + small C loader compiled against libgwyddion | `gwyddion/smoke_gwyddion.py`: writes a 64x32 sine .gsf, loads it with Gwyddion's own GSF module, checks size, physical size and RMS Sq = A/√2 |

Full digests are in the `env:` block of the workflow. To bump a tool, change
the pin there (and in `meep/environment.yml`), then update this table and
`DESIGN_STATE.md`.

Notes
- pygwy (Gwyddion's Python scripting) is Python 2 only and is not packaged on
  current Ubuntu, so the Gwyddion test drives libgwyddion from C instead
  (`gwyddion/gwy_check.c`, headless, no display needed).
- Run any test locally with the same image, e.g.
  `docker run --rm -v "$PWD:/repo" -w /repo dolfinx/dolfinx:v0.11.0 python3 sim/fenics/smoke_fenics.py`.
- Outputs land in `sim/<tool>/out/` (git-ignored).
