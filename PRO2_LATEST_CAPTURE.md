# PRO2 latest BMW Wallbox capture

The 2026-09-16 TCP capture contains repeated requests for `01 03 50 0C 00 02`, i.e. a Function 03 read of the PRO2 L1-current register at `0x500C` for two registers.

Observed response payloads decode as approximately 18.90 A to 19.30 A using the PRO2 FLOAT32 ABCD representation. The supplied steady-state capture contains no request for `0x4000`, so it does not establish that the Wallbox reads the identity block during this polling interval.

This capture should be treated as a steady-state measurement regression, not as a commissioning/identity capture.
