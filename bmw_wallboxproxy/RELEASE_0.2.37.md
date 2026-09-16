# Release 0.2.37

## PRO2 combination code

- Fix the PRO2 register-map default combination code to `0x0003`, matching the L1-only reference profile.
- Preserve explicit combination-code overrides for compatibility testing.
- Update regression tests to verify that a PRO2 register map uses combination code `0x0003` when no override is supplied.

This is a corrective follow-up to 0.2.36. The change makes the runtime register map consistent with the PRO2 identity defaults and the supplied single-phase reference profile.

## Version

- Home Assistant add-on version: `0.2.37`
