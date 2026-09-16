# Release 0.2.31

## Delta Electronics / Inepro PRO2 compatibility

- Fix the Delta Electronics PRO2 Modbus RTU response for two-register FLOAT32 reads.
- Preserve the requested quantity instead of expanding reads at `0x5000` or `0x500C` to a six-register phase block.
- Return `Byte Count = 0x04` and exactly 4 payload bytes for the requested two registers.
- Return exactly 9 bytes for a normal RTU response: slave ID, function code, byte count, 4-byte FLOAT32 payload and 2-byte CRC.
- Encode the PRO2 measurement values using CDAB word-swapped FLOAT32 encoding when `float_word_order: cdab` is selected (the add-on default for Delta compatibility).
- Add regression coverage for `0x5000`, `0x500C`, `0x500E`, `0x5010` and `0x5012`.

## Regression fixed

A request such as:

```text
01 03 50 0C 00 02 15 08
```

now produces a response shaped as:

```text
01 03 04 XX XX XX XX CRC CRC
```

instead of the previous 17-byte response with `Byte Count = 0x0C`.
