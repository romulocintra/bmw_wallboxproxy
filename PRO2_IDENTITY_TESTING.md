# PRO2 identity commissioning validation

The PRO2 implementation now keeps per-device identity values explicit rather than inventing a serial or firmware version.

Set these environment variables before starting the proxy when a physical-meter startup capture is available:

- `PRO2_SERIAL`: 8 decimal digits, encoded by the emulator as the PRO2 packed-decimal serial field.
- `PRO2_METER_CODE`: normally `0x0102` for the direct-connect PRO2 variant; use the value observed from the physical meter/capture.
- `PRO2_PROTOCOL_VERSION`: observed protocol version, for example `3.2`.
- `PRO2_SOFTWARE_VERSION`: observed firmware/software version.
- `PRO2_HARDWARE_VERSION`: observed hardware version.
- `PRO2_METER_AMPS`: observed meter-current rating.

Do not infer these values from a generic PRO380 capture. For byte-for-byte emulation, obtain a capture from the physical PRO2 from power-on through the first measurement poll and copy the observed identity fields.

## Measurement units

The proxy's internal power values are converted to kW for PRO2 register `0x5012` and the phase active-power fields. A Home Assistant source expressed in watts therefore becomes `3.5` at the register when the source is `3500 W`.

## Validation

Run the project's tests, then run `probe_meter.py` against the proxy in RTU-over-TCP mode. The expected commissioning sequence should show the identity block before the steady-state measurement requests. Missing/unsupported addresses should return Modbus exception `0x02` rather than fabricated values.
