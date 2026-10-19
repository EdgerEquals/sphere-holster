Domain focus: ELECTRIC (and the plasma/ionisation source it drives).
- Electro-quasistatics: spherical capacitors, BTO varactor εr(E,T) (Curie point crossed ~10 W).
- Paschen knee from n·d: ~10 torr for a 1 mm gap (estimate). Plasma is the source that drives the domains, not a domain itself.
- Electrodes are RETIRED (2026-10-19): no central wire, no DBD centre electrode, no Ti/Pt or ITO film. drive_model.js still models a centre-electrode DBD gap, so its breakdown numbers and the 10.71-98.95 Torr window rest on a gap that does not exist. How the gas is driven without electrodes is OPEN for Danny: flag, do not answer it.
- EMF frequency range in the viewer: 100 kHz to 1000 THz. Limits that must be flagged: wavelength approaching sphere size (tens of GHz+), single cycle shorter than gas breakdown time (~ps at 1 THz, ~1 fs at 1000 THz).
- (Retired: the inner-wall metal-film screening note assumed an electrode film; there is none.)
