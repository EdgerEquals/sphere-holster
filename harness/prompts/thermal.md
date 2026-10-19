Domain focus: THERMAL.
- 1D radial finite volume with k(T), interface resistances, convection/radiation boundary conditions.
- Known results (estimates): bare 2 mm OD test shell cannot dissipate 1 W in still air without the inner wall passing ~846 K (HHO autoignition range ~773–858 K); 5 mm OD full stack ~415 K at 10 W, ~1960 K at 100 W with outer surface at 293 K; BTO above Curie from ~10 W.
- Check every heat source from other domains arrives (optical absorption, acoustic loss, electric/dielectric loss, magnetic loss, chemical recombination heat) and that T feeds back into εr, k, c, Q and the gas state.
- Autoignition warnings must trigger from the computed temperature, not a constant.
- The 293 K outer reference (Kelvin reference) is LOCKED (Danny, 2026-10-19): do not propose replacing it with required-conductance output.
- Kelvin is canonical in every calculation, the solver and data files; °C only in the GUI, alongside K. Known gap: drive_model.js compares the autoignition range in °C (AUTOIGN_C) - flag until it is moved to K.
