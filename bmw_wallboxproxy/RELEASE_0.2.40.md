# Release 0.2.40

## Fix PRO2 0x500C current encoding

The 2026-09-16 live BMW Wallbox capture shows the L1-current response as IEEE-754 FLOAT32 in ABCD byte order. In 0.2.39 the `float32_abcd` setting did not override the global `float_word_order`; it returned the already-encoded register map unchanged.

This release fixes that behavior.

- `inepro_500c_encoding: float32_abcd` now always emits ABCD for `0x500C/0x500D`.
- `inepro_500c_encoding: float32_cdab` now explicitly emits CDAB.
- The dedicated `0x500C` encoding is independent of the global `float_word_order`.
- Added regression tests covering `float32_abcd` with global `cdab`.
