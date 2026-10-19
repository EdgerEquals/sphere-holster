# Stratified Sphere Model

Multi-domain (optical, acoustic, electric, thermal, magnetic) model and Three.js browser viewer for the stratified bubble sphere.

Note (2026-10-19): the inner downshifting phosphor is removed pending further work; in the solver the light runs quartz -> layer two (elbaite) -> BTO -> Gd-Dy.

Status: v0 work in progress. Physics values are estimates unless a source is cited.

- `solver_v0.py`: radial coupled solver that precomputes fields and spectra
- `model_data_v0.json`: solver output loaded by the viewer
- `viewer_template.html`: Three.js viewer (in progress; `index.html` to follow)
