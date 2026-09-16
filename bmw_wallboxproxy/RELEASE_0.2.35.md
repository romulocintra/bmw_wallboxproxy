# Release 0.2.35

## PRO2 combination code correction

- Correct the default Inepro PRO2 register `0x400F` from `0x0001` to `0x0003`.
- Combination code `3` represents **L1 only**, matching the single-phase PRO2 configuration used by the proxy.
- Support the documented combination codes `1`, `2`, `3`, `4` and `5`.
- Reject unsupported combination codes.
- Add regression tests covering the default, supported values and validation.

This change is specifically intended to make the emulated PRO2 identity/configuration consistent with a single-phase L1 installation. It does not change the `0x500C` current encoding logic introduced in the previous releases.

## Version

- Home Assistant add-on version: `0.2.35`
