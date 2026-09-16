# BMW Wallbox Proxy 0.2.33

## Custom test values

`test_mode` can now use fixed electrical values from the Home Assistant add-on configuration instead of the built-in current sequence.

Available options:

- `test_current_a`: fixed current in amperes. Leave empty to keep the existing 0/6/10/16/20/25/32 A sequence.
- `test_voltage_v`: test line voltage in volts. Default `230.0`.
- `test_frequency_hz`: test grid frequency in hertz. Default `50.0`.
- `test_power_factor`: test power factor from 0 to 1. Default `1.0`.

The proxy derives coherent active, reactive and apparent power values from these settings. For example, to test the Delta PRO2 encoding at exactly 19.5 A:

```yaml
test_mode: true
test_current_a: 19.5
test_voltage_v: 230.0
test_frequency_hz: 50.0
test_power_factor: 1.0
meter_model: inepro_pro2
transport_mode: rtu_over_tcp
float_word_order: cdab
inepro_500c_encoding: int32_ma_cdab
register_alias_mode: exact
```

With `test_current_a` set, the current remains fixed instead of advancing through the default sequence, making repeated Wallbox polls easier to compare across captures.

## Delta PRO2 compatibility

The `inepro_500c_encoding` selector has four independent modes:

- `int32_ma_cdab`: 19.32 A = `0x00004B78` -> wire bytes `4B 78 00 00`.
- `int32_ma_abcd`: 19.32 A = `0x00004B78` -> wire bytes `00 00 4B 78`.
- `float32_cdab`
- `float32_abcd`

The selected current encoding applies to `0x500C`, `0x500E` and `0x5010`. `float_word_order` does not alter the explicit Int32 mode, and legacy register aliases no longer overwrite canonical registers. The response size remains determined by the Wallbox request: a two-register request returns 4 payload bytes and a 9-byte RTU frame including CRC.
