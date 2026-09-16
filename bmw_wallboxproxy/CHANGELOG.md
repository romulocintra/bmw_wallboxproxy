## 0.2.35

- Correct the default Inepro PRO2 combination code at register `0x400F` to `3`, which represents L1-only single-phase operation.
- Accept combination codes `1` through `5` according to the supported PRO2 table, including code `3` for L1-only.
- Reject unsupported PRO2 combination codes instead of accepting the previous values `6` and `9`/`10`.
- Add regression coverage for the default value, supported values and validation of register `0x400F`.

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

## 0.2.24

- Add first-class Janitza B21 312-10J single-phase support using the B-series 0x5Bxx register map.
- Keep Janitza B21/B23 power values in watts internally and encode the documented 0.01 W resolution exactly once.
- Make deterministic `test_mode` available to every supported meter profile. PRO2 and B21 expose L1 only; PRO380 and B23 expose coherent three-phase values.
- Add TCP raw packet diagnostics controls to the dashboard: **Download logs** and **Copy to clipboard**.
- Document the diagnostic workflow for capturing BMW Wallbox Modbus requests and comparing raw frames with the selected meter profile.
- Expand regression coverage for Janitza scaling and single-/three-phase test-mode behaviour.

## 0.2.23

- Add an optional PRO2 test mode for hardware compatibility diagnostics.
- When enabled with `meter_model: inepro_pro2`, the proxy cycles deterministic single-phase current values: 0, 6, 10, 16, 20, 25, 32, 25, 20, 16, 10 and 6 A.
- Generate coherent 230 V / 50 Hz / unity-PF power values alongside the current sequence.
- Advance the sequence per Modbus register-map request so the BMW Wallbox can be observed against changing meter readings without Home Assistant sensor data.
- Add regression tests and add-on configuration wiring for `test_mode`.
