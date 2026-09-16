# Release 0.2.36

## PRO2 single-phase reference profile

- Align the PRO2 identity defaults with the documented single-phase L1 reference profile.
- Use meter code `0x0102` for the direct-connected PRO2 reference configuration.
- Keep combination code `0x0003` for L1-only operation.
- Add the PRO2 CT rate register `0x400C` and CT mode register `0x401F` to the emulated identity/configuration map.
- Preserve both single-phase current locations: `0x500A` (1-phase current) and `0x500C` (L1 current).
- Preserve the direction/quadrant registers used to distinguish import from export (`0x4012`, `0x4017`, `0x4018`).
- Add regression coverage for the reference identity and single-phase register map.

The changes are based on the supplied Inepro PRO1-Mod / PRO2-Mod reference profile and are intended for BMW Wallbox compatibility testing. They do not change the existing configurable `0x500C` current encoding modes.

## Version

- Home Assistant add-on version: `0.2.36`
