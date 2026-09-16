# Release 0.2.34

## Raw Modbus response test mode

- Add `test_raw_response_enabled` and `test_raw_response` to the Home Assistant add-on configuration.
- Allow exact RTU read response bodies to be supplied as hexadecimal bytes without the CRC.
- Recalculate and append the Modbus RTU CRC automatically.
- Keep the override isolated to read responses so normal Modbus request CRC generation is unaffected.
- Validate function code, byte count, even register payload size and hexadecimal syntax.
- Add regression coverage for enabled/disabled behaviour, CRC generation, request isolation and invalid payloads.

Example:

```yaml
test_mode: true
test_raw_response_enabled: true
test_raw_response: "01 03 04 00 00 4B 78"
```

The second byte-order candidate can be tested with:

```yaml
test_raw_response: "01 03 04 4B 78 00 00"
```

## UI/config consistency

- Update the web UI's PRO2 profile to show the configured current encoding and independent FLOAT32 word order.
- Add the Janitza B21 profile to the web UI profile list.
- Align configuration documentation with all four PRO2 current encoding modes and the raw-response test feature.

## Version

- Bump the Home Assistant add-on version to `0.2.34`.
