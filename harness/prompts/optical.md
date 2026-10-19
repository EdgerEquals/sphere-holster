Domain focus: OPTICAL.
- Bands: hydrogen Balmer lines (H-alpha ~656 nm / ~457 THz, H-beta 486 nm, H-gamma 434 nm), phosphor emission (KSF, CASN), visible ~400–790 THz.
- Check radiative transfer per band, Fresnel loss at quartz (~4.6–4.7% per surface, not 3.5–4%), absorption in quartz (IR absorption past a few µm), scattering in the tourmaline sol-gel at 434 nm, phosphor saturation (KSF ~8–16 W, CASN ~80 W, estimates).
- The inner downshifting phosphor is removed pending further work (2026-10-19): no 770 nm band, no wavelength conversion. In the solver the Balmer light runs quartz -> layer two (elbaite) -> BTO film -> Gd-Dy film (absorbed). Flag any code that brings `phos_in` back without Danny's go-ahead; it is paused, not retired.
- Electrodes are RETIRED (2026-10-19): no Ti/Pt film, no ITO/transparent case. Flag any light-to-heat path or preset that assumes one.
- Above ~tens of GHz the drive is no longer a quasi-static field; in the optical band the "drive" is light itself. The viewer must flag, not fabricate, results there.
