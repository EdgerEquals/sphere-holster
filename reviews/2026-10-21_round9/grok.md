<!-- landed: reviewer=grok · model=grok-4.7 · channel=scripts/review_grok.py --ping · generated_utc=2026-10-21T05:41:37Z · source=/workspace/ensemble-round8/Current/round9/run_2026-10-21_grok_rerun/grok/ping.json · run_id=primary-20261021T050438Z-7c9a22 · landed_utc=2026-10-21T05:47:56Z · finish=completed -->

## Verdict

**Not ready.** `run_case(..., drive_W=1)` can deposit a constant 1 W on each channel, but nothing writes `drive_4W_*.json`, the only serializer still describes a zero run, and that call does not implement the stated drive contract.

## What's missing

**blocker** — No sweep entry point and no `drive_4W_*.json` writer. `main()` has no `--drive-W`. It always calls `run_case(pre, ref)` at the default `drive_W=0` and writes `model_data_v0.json` plus `solver_v0_output.txt` (`solver_v0.py:1419-1452`, `1466-1469`). A search of this tree finds no `drive_4W` string. The planned output cannot be produced by the code as it stands.

**blocker** — `package()` never reads `run["drive"]`. A driven run pushed through the existing serializer is labeled a zero run: `state.source` says nothing is injected (`solver_v0.py:1314`), the electric note and march equation hardcode `J_src = 0` (`solver_v0.py:1238`, `1342`), flags always append the no-drive string (`solver_v0.py:1304`), and `magnetic.none` stays true via `no_drive_em` (`solver_v0.py:1050`, `1089`, `1346`). The primary acoustic block is the isolated set, which is left at `W = 0` when the bonded set is the one driven (`solver_v0.py:1002-1003`, `1172`, `1331-1332`). Piezo is taken from those undriven isolated modes (`solver_v0.py:1184`).

**blocker** — The 1 Hz thermal envelope is a dead constant. `DRIVE_THERMAL_ENVELOPE_Hz = 1.0` (`solver_v0.py:809`) is never multiplied into `P_src`, `J_drive`, `P_gas`, or `q_mag`. `DESIGN_STATE.md:537` says it modulates the drives. `tests/test_drive_1W.py:39` only checks that the constant equals 1.0. A run now is steady power, not an enveloped drive.

**blocker** — The electric watt does not enter the thermal balance. `J_drive` is applied in `ElectricMarch.step` (`solver_v0.py:1061`, `1073`) but `q` is only optical + acoustic loss + ferrite placeholder, then `q[0] += P_gas` (`solver_v0.py:1055-1056`, `1071`). No `J^2/sigma` heat is added. `tests/test_drive_1W.py:57-59` only checks that `J` and `E` are nonzero, not that electric power is 1 W or that it heats anything.

**blocker** — Acoustic drive is frozen at the 293 K seal state. Mode energy is set before the thermal march (`solver_v0.py:988-1007`). Hot gas modes are computed afterward and then discarded for the drive; `GAS` is restored to the seal (`solver_v0.py:1081-1088`). The driven frequencies, `Q_eff`, and stress do not follow the temperature the thermal channel just produced.

**blocker** — A library call does not use the documented quartz sound speed. `MAT["quartz"]` starts at `cL=6153`, `cT=4210` (`solver_v0.py:97`). The stated default `vrh` (`6048` / `4090`) is applied only by `set_qz_sound` (`solver_v0.py:501-516`), which `main()` and the geometry sweeps call, and which `tests/test_drive_1W.py` does not. An unguarded `run_case(base5, ..., drive_W=1)` is on a different tune from the CLI default, so the mode list that receives the acoustic watt is not the documented one.

**blocker** — Nothing pins the run to the specified case. `base5` itself is the rarefied winner: `a = 0.57295` mm, wall `1.43463` mm, `t2 = 9.12441` µm, `10577.3` Pa (`solver_v0.py:62-74`). `GAS_COMP = "HHO"` (`solver_v0.py:552`). Other presets are still 1 atm, 100 atm, or φ-scaled OD at 1 atm (`solver_v0.py:75-86`). There is no script that refuses those, and `--p-atm` defaults to 1.0 (`solver_v0.py:1424`).

**nice-to-have** — `gas_Q` / `gas_Q_terms` / `gas_linewidth` (`solver_v0.py:573-589`) are never called from `run_case`. Driven `Q_eff` is solid-layer `MAT[m]["Q"]` only (`solver_v0.py:661-663`). That does not invent a second gas-Q formula, but the acoustic amplitude ignores gas damping.

**nice-to-have** — Vacuum shell/gas split uses a 4000-point grid (`solver_v0.py:968`) over the same 1 Hz–50 MHz window that the loaded search covers with 20 000 points (`solver_v0.py:53`, `604-608`). A missed vacuum root changes who is a "shell" mode and therefore who gets `P_src` (`solver_v0.py:973-980`, `988`).

**nice-to-have** — No frequency-response curve. `forced_spectrum` (`solver_v0.py:735`) is unused by `run_case`. The drive is one simultaneous equal split, not a tune sweep.

**nice-to-have** — `drive_model.js` is a separate viewer stub and is not this sweep. Do not treat it as the 4 W path.

## What would make a sweep result invalid

Running `python solver_v0.py` and reading `model_data_v0.json` is not the sweep. That file is the zero run, and its meta string says nothing is injected (`solver_v0.py:1459-1463`).

Treating `package()` output as the drive result is invalid even if someone passes a driven `run` into it. The labels say no drive, the main acoustic energy is the undriven isolated set, and the bonded energy is easy to miss.

A constant 4 W is not the specified experiment. Without the 1 Hz envelope, ring-up, thermal cycling, and any detune that a slow amplitude modulation would produce are absent. Quoting `DRIVE_THERMAL_ENVELOPE_Hz` from the JSON would be a false claim.

Power does not close at 4 W in the thermal solver. Acoustic steady loss is constructed to equal acoustic `P_src` (`W = P Q / ω`, then loss `= ω W / Q`), thermal is 1 W on the first quartz cell, magnetic is 1 W in the ferrite. Electric 1 W never becomes heat. `total_heat_W` near 3 W is the real balance of this code, not a failed 4 W deposit. Reading it as "all four channels heated the sphere" is wrong.

The electric field from this sizing is not an operating point. `EL_SIGMA["bto"] = 1e-10` S/m (`solver_v0.py:252`) and a 2 µm film (`BTO_T`, `solver_v0.py:224`) give a film volume of order `10^{-10}` m³, so `E → J/σ` is of order `10^{10}` V/m. The retired working field in the same file is `E_WORK = 42e6` V/m (`solver_v0.py:224`). There is no breakdown clamp and `over_voltage` on the stub is hardcoded false (`solver_v0.py:817`). `σ` is an estimate, so `E` scales as `1/σ`. A number that large means the insulator-ohmic stub has left the model's own range, not that the film holds that field.

Magnetic numbers are not magnetic. `B = 0` by spherical symmetry (`solver_v0.py:1206`). The watt is a ferrite heat placeholder (`solver_v0.py:1025`, `1030-1031`). Ferrite `Q(f)` (`solver_v0.py:231`) is unused. Any resonance, amplitude, or threshold read from `B` is meaningless. Ferrite temperature rise is a thermal result with a magnetic label.

Acoustic amplitude is only as good as solid `Q`, and it is the cold tune. Quartz `Q = 2100` is tagged reused, several film `Q` values are estimates (`solver_v0.py:97-110`). Stress and stored energy scale with that `Q`. Gas loading sets the eigenfrequency through `gas_Z` but does not add gas loss. Hot modes in `gas_hot` are a different list from `drive.f_Hz`. Mixing them, or quoting cold stress next to hot gas temperature as one coupled state, makes the joint result false. Thermal expansion, `c(T)` of quartz, and gamma falling above ~1000 K are not in the acoustic march (`c_hho` holds `γ = 1.40`, `solver_v0.py:523-526`).

The equal split is not a tuned drive. Every bonded shell mode in the window gets `1/N` W (`solver_v0.py:822-826`). `N` will be large out to 50 MHz. Most of the acoustic watt is off any one resonance. `peak_stress_sum` is an in-phase sum across different frequencies (`solver_v0.py:691-707`, `1333`). Using that sum as a real peak, or letting the 48 MPa flag (`solver_v0.py:1300`) fire on it, overstates stress. A pole or a numerical sign flip counted by `brentq` (`solver_v0.py:612-616`) would steal a share of the watt. The linear grid has `df = 2.5` kHz (`solver_v0.py:51-53`); it cannot resolve a 1 Hz acoustic mode, and spherical Neumann functions at `ka ≪ 1` are ill-conditioned, so a root near the 1 Hz floor is suspect.

The gas is not a thermal cell. `P_gas` is dumped into `q[0]`, the inner quartz cell (`solver_v0.py:1021`, `1056`). `gas_T_profile` then pretends that same watt was generated uniformly in the gas (`solver_v0.py:490-498`, `1081-1083`). Centre temperature is a post-process, capped at 3000 K. If the cap flag fires (`solver_v0.py:1311`), those temperatures are not physical. Chemistry is called with power 0 (`solver_v0.py:1022`) by design, so an autoignition flag beside `t_conv = inf` is not a combustion result. Do not read `E_store` as energy released by the 4 W drive.

Wrong case, wrong fill, wrong speed set. Any preset other than `base5`, any pressure that is not `0.1044 ×` ambient, any composition other than HHO 2:1, or a forgotten `set_qz_sound("vrh")`, and the mode list is a different sphere. φ-OD presets are 1 atm (`solver_v0.py:86`). The disregarded φ pressure lattice must not be revived. Ambient must stay the recorded `101325` Pa; `10577.3` Pa is that factor, not a new absolute.

Continuum at this fill is an assumption, not a check inside `run_case`. `gas_Q`'s own note drops the Knudsen regime (`solver_v0.py:539`). `DESIGN_STATE.md:519` argues the continuum form still holds near `0.05×` at 293 K. Fixed `N` means heating does not by itself raise Knudsen number (`p ∝ T`). A result that quotes gas `Q` as if the drive used it is still wrong, because the drive does not call it.

This is estimated physics. The module header says nothing is measured (`solver_v0.py:5`). A 4 W figure used as a measured threshold, a hardware amplitude, or a go for a real sphere is invalid even if the bookkeeping above is fixed. Outer temperature is clamped at 293 K (`solver_v0.py:922`, `940`); that is an infinite sink, not a chosen heat sink. `l ≥ 1` is not computed (`solver_v0.py:18-19`). A real acoustic watt would not be pure breathing modes.

Parallel runs that share the global `GAS` dict (`solver_v0.py:471`, `956`) can cross-contaminate pressure if one run fails before the restore at `solver_v0.py:1088`.

## What to read first in the sweep output

Do not start with `model_data_v0.json`. If the file's source string still says no drive, stop. The fields below are the ones on the `run_case` dict (`solver_v0.py:1090-1094`). A writer has to copy them; `package()` will not.

1. `drive.drive_W`, `drive.n_modes_driven`, `drive.f_Hz`, `drive.P_src_per_mode_W`, `drive.electrodes`, `drive.magnetic_note`. These say whether this file is the 4 W call, how the acoustic watt was split, that frequencies came from the mode list, that electrodes stayed retired, and that magnetic is the ferrite-heat placeholder. `P_src_per_mode_W` must be `1/N`, and every `f_Hz` must sit in `DRIVE_WINDOW_Hz`.

2. `P_gas`, `sum(q_mag)`, `sum(J_drive**2 / sigma * V)` if the writer records it, and `heat_by_layer` / `q.sum()`. These are the power closure. Expect thermal 1 W and ferrite 1 W. Acoustic loss in `ac_bond["loss"]` should sum to about 1 W if the `Q` algebra held. Electric will be missing from `q` until that bug is fixed. If `q.sum()` is quoted as 4 W, the file is wrong or the heat path changed.

3. `W_ac` and `ac_bond["modes"]` (`f`, `Q_eff`, `W`, `peak_stress`), not `ac["W"]`. `W_ac` is the bonded stored energy. Per mode, `W` should match `P_src * Q_eff / (2 π f)`. `ac["W"]` is the isolated set and is 0 on this drive. `peak_stress` is the per-mode maximum; `peak_stress_sum` is the in-phase upper bound, not a simultaneous peak.

4. `Tss` extrema, `gas_hot.T_centre`, `gas_hot.T_wall`, `gas_hot.T_gas`, `gas_hot.p_hot`, and `flags`. Wall temperature is the thermal solver. Centre temperature is the gas post-process. The gap between them is the conduction picture, not a second heat source. Flags for 3000 K, quartz α–β (846 K), BTO Curie (393 K), and HHO autoignition say the run left the model's range. `p_seal` should be 10577.3 Pa.

5. `E_ss` max in the BTO cells, next to `J_drive`. A field of order `10^{10}` V/m means the ohmic stub, not a usable electric amplitude. Compare with `E_WORK` (4.2×10^7 V/m) before reading any piezo or electrocaloric number. `em` and `em_hot` are the no-drive stub; ignore them for this sweep.

6. `gas_hot.shell` versus `drive.f_Hz`. If those lists diverge, the acoustic drive was not retuned to the hot gas. Do not report one resonance from the cold list and a Q or stress as if it belonged to the hot list.

7. Case identity: preset id `base5`, core diameter 1.1459 mm, wall 1.43463 mm, layer two 9.12441 µm, fill HHO, and which `QZ_SOUND` set was applied. If the sound-speed set is missing from the file, the mode list is not interpretable.
