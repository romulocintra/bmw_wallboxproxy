# Release 0.2.30

## Delta Electronics / Inepro compatibility

- Default Inepro FLOAT32 word order to CDAB for Delta Electronics BMW wallboxes.
- Complete the PRO2 voltage phase block at `0x5000`: L1/L2/L3 (`0x5000`, `0x5002`, `0x5004`).
- Complete the PRO2 current phase block at `0x500C`: L1/L2/L3 (`0x500C`, `0x500E`, `0x5010`).
- Add Delta compatibility handling for two-register reads starting at `0x5000` and `0x500C`, expanding them to the complete six-register phase block.
- Add regression coverage for the expected 17-byte RTU response, CDAB FLOAT32 encoding, CRC and zero-valued unused phases.

## Notes

The repository's documented Inepro map defines `0x5006` as the L3 voltage word and `0x5008` as frequency; `0x502A` is total power factor. The implementation keeps those documented addresses rather than overlapping the voltage phase block with frequency data.
