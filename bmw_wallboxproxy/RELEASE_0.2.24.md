# Release 0.2.24

## Meter profiles

### Inepro PRO2-Mod

The PRO2 profile is single-phase. L1 is the physical phase represented by the meter; L2/L3 values are zeroed. The current register is `0x500C`, using IEEE-754 FLOAT32 in ABCD order. Configuration values follow the PRO2 Modbus register map documented by Inepro.

### Janitza B21 312-10J

B21 is treated as a single-phase member of the Janitza B-series. Its `0x5Bxx` registers use the documented scaled integer representation. Voltage uses 0.1 V, current 0.01 A, power 0.01 W and frequency 0.01 Hz resolution. **Frequency at `0x5B2C` occupies one 16-bit register**; `0x5B2D` is the total power phase-angle register. Power is represented internally in watts so the encoder applies the 0.01 W scale exactly once.

### Janitza B23 312-10J

B23 remains three-phase and uses the same B-series scaled-integer family. The test mode supplies coherent L1/L2/L3 values. Frequency follows the same one-register `0x5B2C` representation.

## Deterministic test mode

Enable `test_mode` in the add-on configuration to remove Home Assistant sensor timing from protocol diagnostics.

The current sequence is:

`0, 6, 10, 16, 20, 25, 32, 25, 20, 16, 10, 6 A`

At 230 V / 50 Hz:

- PRO2/B21 expose the sequence on L1 only.
- PRO380/B23 expose the same current on all three phases.
- Active power, apparent power and power factor remain internally coherent.

This mode is intended for capturing what the BMW Wallbox actually requests and whether it accepts the selected meter profile.

## TCP raw diagnostics

The dashboard keeps the advanced **TCP raw packets** section collapsed by default. Two controls are available:

- **Download logs** — saves the current raw TCP packet buffer as a timestamped `.log` file.
- **Copy to clipboard** — copies the same raw packet buffer directly to the clipboard for pasting into an issue or diagnostic report.

The controls read the existing `/api/state` diagnostic buffer and therefore do not change the Modbus traffic.

## Recommended BMW Wallbox diagnostic workflow

1. Select the exact meter model configured in the BMW Installation App.
2. Use the matching transport mode (`rtu_over_tcp` when the TCP connection carries raw RTU frames).
3. Enable `test_mode`.
4. Restart/reconnect the Wallbox.
5. Open **TCP raw packets (advanced)**.
6. Download or copy the raw packets.
7. Compare the Wallbox request addresses, quantities and returned bytes against the selected physical meter profile.
8. Disable `test_mode` after the compatibility test.
