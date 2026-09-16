## 0.2.37

- Fix the PRO2 register-map default combination code to `0x0003`, matching the L1-only reference profile.
- Keep explicit combination-code overrides supported for compatibility testing.
- Update PRO2 regression tests to verify the default combination code instead of requiring callers to provide it explicitly.

## 0.2.36

- Align the PRO2 identity defaults with the supplied single-phase L1 reference profile.
- Use meter code `0x0102` and reference protocol/software/hardware values for the emulated PRO2 identity.
- Add PRO2 CT rate `0x400C` and CT mode `0x401F` to the identity/configuration map.
- Keep combination code `0x0003` for L1-only operation and validate documented combination codes `1` through `5`.
- Preserve the single-phase current locations `0x500A` and `0x500C` and the import/export direction and quadrant registers.
- Add regression coverage for identity, current aliases and import/export direction.

## 0.2.34

- Add `test_raw_response_enabled` and `test_raw_response` for exact RTU read-response testing without changing the normal register map.
- Recalculate and append the Modbus CRC automatically.
- Validate raw response hex, function code, byte count and even register payload size.
- Add regression coverage for enabled/disabled behaviour, CRC generation, request isolation and invalid payloads.
- Align the web UI PRO2 profile with the configured current encoding and independent FLOAT32 word order.
- Add the Janitza B21 profile to the web UI.
- Align configuration documentation with all four PRO2 current encoding modes and the raw-response test feature.

## 0.2.33

- Add custom deterministic test values to the Home Assistant add-on configuration.
- Allow a fixed test current with `test_current_a`; when left empty, the existing current sequence is preserved.
- Allow custom test voltage, frequency and power factor with `test_voltage_v`, `test_frequency_hz` and `test_power_factor`.
- Generate coherent active, reactive and apparent power values from the configured test voltage/current/power factor.
- Keep the feature available across all supported meter profiles while preserving the existing PRO2 single-phase collapse behaviour.
- Make PRO2 Int32 current word order explicit with independent `int32_ma_cdab` and `int32_ma_abcd` modes.
- Ensure `float_word_order` and `register_alias_mode` cannot silently change the canonical PRO2 Int32 current registers.
- Add regression coverage for custom values, explicit Int32 byte ordering and alias interaction.

## 0.2.32

- Make the Delta Electronics Inepro PRO2 current encoding configurable from the Home Assistant add-on configuration.
- Add `inepro_500c_encoding` with `int32_ma_cdab`, `float32_cdab`, and `float32_abcd` modes.
- Default the experimental Delta current mode to Int32 milliamps with CDAB word swap.
- Apply the selected current encoding to PRO2 registers `0x500C`, `0x500E`, and `0x5010` while preserving the exact two-register / 4-byte response size.
- Keep PRO2 voltage `0x5000` and active power `0x5012` on the configured FLOAT32 word order.
- Add regression tests for all three current encoding modes and the unchanged voltage/power encoding.
- Document the hardware test workflow and configuration options for iterating on Delta meter compatibility.

## 0.2.31

- Fix the Delta Electronics / Inepro PRO2 response to two-register FLOAT32 reads at `0x5000`, `0x500C`, `0x500E`, `0x5010` and `0x5012`.
- Preserve the requested quantity so a two-register read returns `Byte Count = 0x04`, 4 payload bytes and exactly 9 RTU bytes including CRC.
- Remove the previous three-phase expansion that returned `Byte Count = 0x0C` for a two-register request and could cause the Delta wallbox to reject and repeat the poll.
- Document CDAB word-swapped FLOAT32 encoding for the Delta compatibility configuration.
- Add regression tests for exact response size, CDAB payloads and CRC validation.
