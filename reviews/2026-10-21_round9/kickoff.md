# Round 9 kickoff: DRAFT (not approved)

## 1. Scope

**Scope:** we propose to run the 4 W sweep on the sphere code. This round checks whether the sphere code has everything it needs to run that sweep and give a result worth having.

- The sweep is not run in this round. Your reply feeds the go/no-go for it.
- Answer from the code and docs as they stand. If information is missing, say what is missing rather than guessing.

---

## 2. The 4 W sweep

As set up in the repo (read these in the code folder; `MAP.md` at its top lists every file and points to the lines below):

- **Drive:** `run_case(pre, ref, drive_W=1)` in `solver_v0.py`. Each of the four channels (thermal, electric, magnetic, acoustic) receives 1 W, so 4 W in total. The default `drive_W=0` is the zero run. See the "Opt-in 1 W domain drive plumbing" section of `DESIGN_STATE.md` and `docs/harness_context.md` §2.2.
  - **Acoustic:** split equally across the computed l = 0 modes in the window (`DRIVE_AC_SPLIT`, `drive_mode_P_src`). Drive frequencies come from the geometry's own mode list, never a hardcoded target.
  - **Electric:** volumetric source current in the BTO film, sized to the drive power (`drive_J_src_for_power`). No electrodes.
  - **Thermal:** heat into the gas core (`P_gas`).
  - **Magnetic:** deposited as heat in the ferrite as a placeholder (`drive_heat_on_material`).
- **Window:** 1 Hz to 50 MHz on a 20 000-point grid (`FMIN_HZ`, `FMAX_HZ`, `N_FREQ_GRID`, `DRIVE_WINDOW_Hz`). The 1 Hz thermal cycle is a slow envelope on the drives (`DRIVE_THERMAL_ENVELOPE_Hz`), not an acoustic mode.
- **Core:** preset `base5` in `PRESETS`, the rarefied core (`CORE_A_MM`, `CORE_W_MM`, `CORE_P_ATM`): bubble a 0.57295 mm, quartz wall 1.43463 mm, layer two 9.12441 µm, fill 0.1044 × ambient (10 577.3 Pa). See "Core geometry replaced by rarefied-sweep winner" in `DESIGN_STATE.md`.
- **Gas:** HHO 2:1 only (`GAS_COMP`). Gas Q comes from the solver (`gas_Q`, `gas_Q_terms`, `gas_linewidth`); nothing else computes it.
- **Pressure:** fully rarefied only, a factor of local ambient below 1. No φ-derived pressure.
- **Tests:** `tests/test_drive_1W.py`.
- **Output:** planned as `drive_4W_*.json`.

---

## 3. Your reply

Give these four parts, each under its own `##` heading:

1. **[HIGH CUE] Verdict.** One of: **ready**, **ready with fixes**, or **not ready** to run the 4 W sweep. One line on why.
2. **[MIDDLE] What's missing.** Each item marked **blocker** or **nice-to-have**, with the file and line it concerns where there is one.
3. **[WIDE BANDWIDTH] What would make a sweep result invalid.** Anything in the code, the physics or the run set-up that would make a 4 W result wrong or meaningless, however unlikely.
4. **[MIDDLE] What to read first in the sweep output.** Which fields or numbers in the output to check first, and what each one tells us.

---

## 4. Tools this round

Use them; this round also tests them.

- **Code folder:** `read_file` and `search_code` read a read-only copy of the sphere code and the rig code. Start with `MAP.md`.
- **Lookups:** you have a lookup budget of your own. If it runs out, `request_more_lookups` asks the shared pool for more; say what value more lookups would add.
- **A person:** if the information switch answers a question you think needs a person, `ask_for_person` says why.
