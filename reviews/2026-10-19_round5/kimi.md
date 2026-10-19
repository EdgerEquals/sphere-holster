I can’t fetch external URLs, clone repos, or browse the live web, so I cannot pull down `github.com/EdgerEquals/stratified-sphere-model` directly. If you paste the README, directory tree, or key source files here, I can give you a concrete, line-by-line audit.

That said, the name **Stratified Sphere model** places it squarely in a well-known family of geophysical/astrophysical/fluid-dynamics codes. Below is my general assessment of what typically breaks, what’s usually missing, and what the underlying scientific goal likely is.

---

### What I think you’re trying to do
In my own words: you appear to be building a numerical simulation of a **density-stratified (or entropy-stratified) fluid on a spherical shell**—most likely an atmosphere, ocean, or stellar/planetary interior. The “stratification” implies vertical structure (layers of differing density or potential temperature), while the “sphere” means you’re wrestling with the geometry of a rotating planet or star. The model probably solves some form of the Euler, Navier-Stokes, Boussinesq, or “primitive” equations in spherical coordinates, possibly with an eye toward long-term stability, energy conservation, or climate-like dynamics.

---

### What you should probably fix

1. **Pole singularities & CFL constraints**
   Spherical coordinates create a coordinate singularity at the poles and a severe Courant limit on longitudinal spacing. If you’re using finite differences on a latitude-longitude grid, you likely need either:
   - A **cubed-sphere** or **icosahedral** grid, or
   - A **spectral transform** (spherical harmonics) with dealiasing, or
   - A **zonal filter** near the poles to avoid instability.

2. **Hydrostatic inconsistency in the pressure gradient**
   On a discretized sphere with terrain-following or height-based coordinates, the pressure gradient can generate spurious vertical velocities. Fix: use **Lagrangian vertical coordinates**, **isopycnal layers**, or a well-balanced pressure-gradient scheme.

3. **Conservation of invariants**
   Stratified sphere models that run for many time steps must conserve mass, total energy, potential enstrophy, and angular momentum to machine precision. If your code lacks:
   - **Flux-form** (conservative) advection, or
   - **PV-conserving** discretizations (e.g., mimetic finite volumes, TRiSK stencil, or spectral div/curl),
   …you’ll drift into unphysical states.

4. **Boundary conditions at the “bottom” and “top”**
   A sphere has no lateral walls, but it has a lower boundary (surface/topography) and an upper boundary (rigid lid, sponge layer, or top-of-atmosphere). Common bugs:
   - Reflective vs. non-penetrating lower BCs that leak energy,
   - Sponge layers that introduce spurious reflection or damping,
   - Missing **bottom friction** or **top radiative cooling** terms.

5. **Time-stepping stiffness**
   Stratification introduces fast buoyancy (gravity) waves. If you’re explicit, your time step is probably brutally small. Fix: use **split-explicit**, **semi-implicit**, or **IMEX** time stepping to separate slow vortical modes from fast gravity waves.

6. **Parallel decomposition**
   Lat-lon grids don’t scale well on distributed machines because of the meridional convergence. If you’re using MPI, check whether your decomposition is **1D (zonal)** or **2D (pencil/cube)**; the latter is needed for scalability.

---

### What is likely missing

| Category | Typical Gap | Why It Matters |
|---|---|---|
| **Testing** | No manufactured solutions or convergence tests on the sphere (e.g., Williamson test cases for shallow water, or Jablonowski-Williamson baroclinic wave). | Without an analytical benchmark, you can’t distinguish a coding bug from a model limitation. |
| **Documentation** | No theory guide deriving the continuous equations, the discretization, and the conservation proofs. | Future contributors (and reviewers) can’t verify correctness. |
| **CI / Build system** | No GitHub Actions, no `Dockerfile`/`Singularity` definition, or no dependency lock file. | Reproducibility across HPC and laptops breaks immediately. |
| **Grid & topography generation** | Hard-coded grids or missing grid-rotation utilities. | A sphere model needs rotated poles, variable resolution, or seamless topography ingest. |
| **I/O & Post-processing** | Output in custom binary instead of NetCDF/Zarr; no plotting utilities for spherical slices, meridional overturning, or PV maps. | Scientists need to *see* the stratification and overturning circulations. |
| **Parameter space exploration** | No ensemble or sensitivity framework. | You can’t tell whether a result is robust or an accident of one Rayleigh number. |
| **Coupling / Forcing** | Missing diurnal cycle, seasonal insolation, or topography drag parameterizations. | A stratified sphere without forcing is just an initial-value problem with viscous decay. |

---

### Next step
If you want actionable, specific feedback, paste any of the following into this chat:
- The top-level `README.md`
- The main solver/driver file (e.g., `model.py`, `sphere.f90`, `main.cpp`)
- The directory structure (`tree -L 2`)
- A sample config / namelist file

I’ll tell you exactly where the boundary conditions look suspicious, where the discretization might be losing conservation, and how to structure the repo for reproducibility.
