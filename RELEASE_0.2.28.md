# Release 0.2.28

## PRO2 fidelity

- Complete PRO2 direction/quadrant handling for import/export.
- Encode the direction field as the documented two-byte ASCII representation.
- Keep single-phase PRO2 phase-specific fields zero/blank where applicable.
- Preserve documented PRO2 measurement units, including active power in kW.
- Add regression coverage for the latest BMW Wallbox steady-state capture.

## Capture note

The 2026-09-16 capture repeatedly polls `0x500C` (L1 current) once per second. Responses observed in the supplied capture decode to approximately 18.83–19.30 A. No `0x4000` identity request is present in this steady-state capture; a startup capture is still needed for physical identity validation.
