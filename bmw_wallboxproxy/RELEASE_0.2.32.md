# Release 0.2.32

## Delta Electronics / Inepro PRO2 compatibility

- Make the current encoding configurable from the Home Assistant add-on configuration.
- Add `inepro_500c_encoding` with three hardware-test modes:
  - `int32_ma_cdab`: signed Int32 milliamps with CDAB word swap.
  - `float32_cdab`: IEEE-754 FLOAT32 with CDAB word swap.
  - `float32_abcd`: IEEE-754 FLOAT32 in ABCD order.
- Default to `int32_ma_cdab` for the current registers `0x500C`, `0x500E` and `0x5010`.
- Keep voltage `0x5000` and active power `0x5012` as FLOAT32 using the configured `float_word_order`.
- Preserve the exact requested quantity for all two-register reads: `Byte Count = 0x04` and a 9-byte RTU response including CRC.
- Log the selected current encoding at add-on startup.
- Add regression tests for all current encoding modes and the fixed response size.

## Hardware testing

Change `inepro_500c_encoding` in the Home Assistant add-on configuration and restart the add-on between tests. Capture the Modbus log and check whether the Wallbox proceeds from the `0x500C` poll to subsequent registers such as `0x5000` or `0x5012`.
