# Ferrite Slug (active model, from 31 Oct 2026)

A square MnZn ferrite rod, 20 x 20 x 120 mm, mounted softly at its midpoint so it rings as a free-free bar.
A drive coil supplies the AC field and a bias coil carries DC to set the operating point; the model estimates
magnetostrictive vibration near the longitudinal resonances (f_n = n v / 2L, v = sqrt(E/rho)) as a function of bias.
All material values are PLACEHOLDERS (generic MnZn) to be fitted back from measurements on the real rod.

- `slug/model.py`: model; writes `slug/slug_data_v0.json` (`--build` also rebuilds `index.html`)
- `slug/viewer_template.html` + `slug/build.py`: viewer, built into `index.html` (GitHub Pages)
- `tests/test_slug_sanity.py`: f_1 from a finite-element bar vs the textbook formula
- Archived sphere: `archive/stratified_sphere/` (`index_rev1.html` is the frozen sphere viewer). The sphere
  sources stay in place; `build.py` now writes `sphere.html` so it cannot overwrite `index.html`.

---

# Stratified Sphere Model

Multi-domain (optical, acoustic, electric, thermal, magnetic) model and Three.js browser viewer for the stratified bubble sphere.

Note (2026-10-19): the inner downshifting phosphor is removed pending further work; in the solver the light runs quartz -> layer two (elbaite) -> BTO -> Gd-Dy.

Status: v0 work in progress. Physics values are estimates unless a source is cited.

- `solver_v0.py`: radial coupled solver that precomputes fields and spectra
- `model_data_v0.json`: solver output loaded by the viewer
- `viewer_template.html`: Three.js viewer (in progress; `index.html` to follow)

Terminology: see [`docs/vocabulary.md`](docs/vocabulary.md).
