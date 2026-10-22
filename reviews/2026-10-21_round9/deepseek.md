<!-- landed: reviewer=deepseek · model=deepseek-flash · channel=scripts/review_deepseek.py --ping · generated_utc=2026-10-21T05:28:59Z · source=/workspace/ensemble-round8/Current/round9/run_2026-10-21_deepseek_rerun/deepseek/ping.json · run_id=primary-20261021T050438Z-7c9a22 · landed_utc=2026-10-21T05:31:00Z · finish=stop -->

# DeepSeek Low

## Verdict
**Not ready** to run the 4 W sweep as the code stands.

`run_case(pre, ref, drive_W=1)` is real and tested, but nothing calls it with a drive, nothing writes `drive_4W_*.json` (`drive_4W` has **zero** hits in the code folder), and every string the output writes about itself still says "no source, nothing is injected", so a 4 W JSON would come out labelled as a zero run.

## What's missing

**Blockers**

1. **No run entry point for the sweep.** `main()` (`solver_v0.py:1419-1472`) has no `--drive` argument and calls `run_case(pre, ref)` with the default (line 1452). No preset carries a `drive_W` key either, so `pre.get("drive_W", drive_W)` (`solver_v0.py:953`) is never exercised outside the tests. Today the only way to drive a case is a hand-written `python -c` call. *Blocker* — there is no "sweep" to run.
2. **No writer for the planned output.** `drive_4W_*.json` does not exist anywhere; `main()` writes only `model_data_v0.json` / `solver_v0_output.txt` / `tourmaline_sweep_v0.json`. *Blocker*.
3. **The drive record never reaches the output.** `drive_info` is built at `solver_v0.py:1026-1033` and returned as `run["drive"]` (line 1094), but `package()` never reads it (no `run["drive"]` reference in the file). A `drive_4W_*.json` from the current packager would record no drive_W, no driven mode list, no `P_src_per_mode_W` and no `W_ac_sum_J` — i.e. no way to tell what was swept. *Blocker*.
4. **The output hard-codes "no source" text.** `state["source"]` = "none: no drive mechanism defined; nothing is injected" (`:1314`); electric march note "J_src = 0 (no-drive stub)" (`:1342-1343`); core note "J_src = 0" (`:1238`); unconditional flag "Electric/magnetic: …" (`:1304`); meta `scenario` "No source … nothing is injected" (`:1461-1463`). A driven run would self-describe as a zero run. *Blocker* — a result that misdescribes itself is not worth having.
5. **The electric watt never becomes heat.** `q = qo + q_ac + q_mag`, then `q[0] += P_gas`, then `+ ec_heat(...)` (`:1055-1057`, `:1071-1074`). `drive_J_src_for_power` sizes `J` for 1 W of ohmic power (`:836-852`) but `ElectricMarch.step` returns fields only (`:400-409`); no `J²/σ·V` term is deposited anywhere. So `thermal.total_heat_W` will report ≈ 3 W, not 4 W, and one of the four watts simply leaves the energy budget. *Blocker* for any claim the output makes about "4 W". (Fix: deposit it as heat, or state the imbalance explicitly in the output.)

**Nice-to-have**

6. **The 1 Hz envelope is inert.** `DRIVE_THERMAL_ENVELOPE_Hz = 1.0` (`:809`) is defined, documented (`DESIGN_STATE.md:537,549`) and asserted in the test (`tests/test_drive_1W.py:39`), but it is never applied to any drive — every channel is a steady DC input. Fine for a steady-state answer, but the output must not imply a modulated sweep. (`solver_v0.py:809`)
7. **Chemistry is passed zero, always.** `chem_state(pre["p_atm"]*101325.0, st["r_in"], 0.0)` (`:1022`) passes `P_gas = 0.0` regardless of drive, so `R_d → 0`, `t_conv → inf`, `P_release = 0`. That matches the DESIGN_STATE decision that chemistry drive stays 0 (`:540`), but it means the chemical channel is dead code under drive, and the `t_conv`-dependent strings in the output (`:1310`, `:1277-1280`) are meaningless. (`solver_v0.py:1022`)
8. **Gas Q is absent from the driven acoustic number.** `Q_eff` comes only from `MAT[m]["Q"]` (`:661`); `gas_Q` is called nowhere in `run_case` (only in the geometry sweeps). Defensible because only shell modes are driven, but the rarefied-fill choice was made on gas Q, so the 4 W result cannot see it. (`solver_v0.py:661`, `:584`)
9. **`peak_stress_sum` is an in-phase sum of absolute peaks** (`:700`, `:707`), and that is the number fed to the 48 MPa stress flag (`:1300`). It is an upper bound, not a stress; the flag can fire on superposition alone.
10. **`Ws_for` indexes `P_list` by `sorted(drive_freqs).index(f)`** (`:999`) — float equality against a re-sorted list. Works today because both sides come from the same list; it is fragile the moment a drive set and a carry set diverge.

## What would make a 4 W result invalid

- **The electric field lands ~2 orders above the design field.** By the code's own constants: BTO σ = 1e-10 S/m (`:252`), `V_bto ≈ 1.0e-10 m³`, so `inv ≈ 1.0` and `J ≈ 1 A/m²`; the steady march solution (`:407`) gives `E = J/σ ≈ 1e10 V/m` — against `E_WORK = 42e6 V/m` (`:224`), i.e. ~240× the working field and far past any BaTiO₃ breakdown. With no electrodes there is no charge continuity, so this is a conduction-limited artefact. The run will not crash, but the electric channel's `E_max`, its electrocaloric heat (`p_net(bto) = 2.0e-4 C/m²K`, `:240-243`) and its entropy output are not physical. *(my arithmetic from code constants, not a run.)*
- **Mode count N is grid-limited, and W_ac depends on N.** Acoustic roots are found by sign changes on a linear grid: 20 000 points over 1 Hz–50 MHz (`l0_modes`, `:604-619`) and 4 000 points for the vacuum reference used by `split()` (`:968`). At 10 MHz quartz `Q = 2100` gives a half-width of ~2.4 kHz, below the 12.5 kHz vacuum spacing and comparable to the 2.5 kHz main spacing, so roots can be missed or the shell/gas split can misclassify. Since `P_src,n = drive_W/N`, a different N redistributes the watt and changes `W_ac` and every stress derived from it. The repo already documents the same sensitivity on the no-source side: a 0.06 % sound-speed change moved sharp counts in 41 of 48 cells (`DESIGN_STATE.md:505,519`).
- **`W_n = P_n Q_n / ω_n` weights the result as 1/f**, and `Q_eff` is frequency-flat. Any low-frequency root — including a spurious one from the `Smat`/`linalg.inv` numerics at `x = k·a → 0` (`:457-469`) — would dominate the entire acoustic energy and stress. Check whether `W_ac` is carried by one mode near the bottom of the window before believing the total.
- **The 4 W is 3 W of heat plus 1 W that vanishes.** Gas 1 W, ferrite-placeholder 1 W and acoustic dissipation 1 W all land in the same thermal solve, and the acoustic loss is applied at its steady value from t = 0 (`:1013-1018`), so the transient frames contain a step that never happened. Only `Tss` should be read.
- **1 W into a 0.573 mm core is not a small perturbation.** `gas_T_profile` (`:490-498`) with 1 W in 7.9e-10 m³ gives a gas centre of order several hundred K; my rough stack conductance puts the whole stack ~100 K up at 3 W. That crosses the "rarefied, 293 K" premise the core was chosen for, sits near the autoignition band the code flags (`:1307-1310`), and would push BTO toward the 393 K Curie flag (`:1301`).
- **The driven frequencies are cold-state frequencies.** `m_bond` is computed at the 293 K seal state (`:981-982`) and the hot list is only computed afterwards for reporting (`:1085`). `MAT` has no dρ/dT or dc/dT for the solids, so with ~100 K of rise the driven frequencies are off the hot stack's modes by the quartz temperature coefficient (order hundreds of ppm) — at `Q ≈ 2100` one linewidth is 0.05 %, so this is not negligible for a resonance-targeted drive.
- **The bonded/isolated split is a 1 % frequency test on a 12.5 kHz grid** (`split`, `:973-980`), so which set gets the watt can flip with geometry by a hair.
- **It is not a spectrum.** All computed modes are driven simultaneously, each at its own frequency, and energies are summed (`:990-1007`). The output cannot show tune/detune, a resonance peak, or which mode responded; nothing in it is a frequency response.
- **The magnetic channel is pure heat with no field.** `q_mag` is a placeholder on the ferrite (`:855-866`, `:1025`); `B = 0` by symmetry (`:1231-1240`). Its 1 W says nothing about magnetics.
- **`--qz-sound` is a global mutable.** `set_qz_sound` rewrites `MAT["quartz"]["cL"/"cT"]` (`:514-517`); a sweep run at a non-default set and a later run at the default in one process would mix lattices unless the value is recorded in the output.

## What to read first in the sweep output

1. **`drive` block** (once it is written): `drive_W`, `n_modes_driven`, `f_Hz`, `P_src_per_mode_W`, `W_ac_sum_J` — proof the sweep did what it claims; `n_modes_driven` is the same N that sets every per-mode power.
2. **`thermal.total_heat_W`** against 4 W. Expect ≈ 3 W; the gap is the missing electric ohmic watt. A number near 4 would mean someone quietly added heat elsewhere.
3. **`thermal.heat_W` per layer** — where the 3 W actually sits (gas core, ferrite placeholder, quartz). This is the only honest map of the drive.
4. **`gas.T_centre_K`, `gas.T_gas_K`, `gas.p_hot_Pa` vs `p_seal_Pa` = 10 577 Pa** — whether the "rarefied, 293 K" premise survived the drive, and whether `p_seal → p_hot` stayed a factor below ambient.
5. **`acoustic.bonded.n_modes` and `modes[].f / Q_eff / W`** — first check the lowest driven frequency and whether one mode carries most of `W`. A single dominant mode at the bottom of the window is a numerics smell, not a result.
6. **`acoustic.bonded.W_mJ`, `peak_stress_MPa`, `peak_stress_sum_MPa`** — the energy delivered per watt, and the two very different stress aggregates before comparing anything to the 48 MPa design line.
7. **`electric.march.E_max_V_m`** — a value near 1e10 V/m means the channel is a conduction artefact; compare against `E_WORK` 42 MV/m.
8. **`gas.shell_l0_hot` / `gas_modes_hot` vs the cold `l0_bonded` list** — the hot/cold detune that the drive ignores.
9. **`flags[]`** — read every entry before quoting any number: quartz > 573 C (`:1299`), 48 MPa stress (`:1300`), BTO > 393 K Curie (`:1301`), CALORIVAC > 473 K (`:1302`), Gd-Dy above 260 K (`:1303`), autoignition band (`:1307-1310`), 3000 K cap (`:1311`).
10. **`state["source"]`, `meta.status`, `electric.march.equation`** — if these still say "no source / J_src = 0", the file is mislabelled and should not be circulated.
11. **`thermal.tau_ac` / `acoustic.bonded.tau_ac_max_s`** — the ring-down time, to judge whether the 46-step time grid (`:1035`) resolves ring-up at all.
