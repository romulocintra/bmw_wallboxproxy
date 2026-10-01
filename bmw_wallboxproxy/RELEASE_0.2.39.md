# Release 0.2.39

## Live BMW Wallbox PRO2 capture validation

- Add regression coverage from the supplied 2026-09-16 raw TCP capture.
- Validate the recurring PRO2 L1-current request `01 03 50 0C 00 02 15 08`.
- Validate that each response is exactly 9 RTU bytes with `Byte Count = 0x04` and a valid Modbus CRC.
- Confirm the captured `0x500C` payloads are IEEE-754 FLOAT32 in **ABCD** byte order, decoding to approximately 5.53–6.41 A.
- Keep `float32_abcd` as the default PRO2 current encoding.

The capture provides hardware evidence for the current encoding already implemented by the proxy; this release adds a regression guard so the observed wire format is not accidentally changed.
