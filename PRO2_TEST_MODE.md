# PRO2 test mode

The add-on has an optional deterministic test mode intended for BMW Wallbox / Inepro PRO2-Mod compatibility diagnostics.

## Enable

Set the add-on options to:

```yaml
meter_model: inepro_pro2
test_mode: true
transport_mode: rtu_over_tcp
float_word_order: abcd
register_alias_mode: exact
```

Restart the add-on after changing the option. The startup log reports the effective test-mode setting.

## Sequence

Every Modbus register-map request advances one step through this L1 current sequence:

```text
0 A
6 A
10 A
16 A
20 A
25 A
32 A
25 A
20 A
16 A
10 A
6 A
(repeat)
```

The virtual meter also reports coherent single-phase values:

- L1 voltage: 230 V
- frequency: 50 Hz
- L1 active power: `230 V × current`
- total active power: same as L1
- apparent power: same as active power
- power factor: 1.0 whenever current is non-zero
- L2/L3: zero
- aggregate imported energy: 100 kWh (fixed diagnostic value)
- aggregate exported energy: 0 kWh

For example, the 6 A step produces:

```text
0x5002 = 230.0 V
0x500C = 6.0 A
0x5012 = 1.38 kW
```

## Important behaviour

Test mode is only active for `inepro_pro2`. Other meter profiles continue using their normal Home Assistant-backed values.

The sequence is generated at Modbus response time rather than being pushed unsolicited to the Wallbox. This preserves normal Modbus request/response behaviour while making the meter readings deterministic and changing.

The mode is intended for controlled diagnostics. Disable it for normal operation so the proxy uses the real Home Assistant measurements.
