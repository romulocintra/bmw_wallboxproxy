## 0.2.24

- Add first-class Janitza B21 312-10J single-phase support using the B-series 0x5Bxx register map.
- Keep Janitza B21/B23 power values in watts internally and encode the documented 0.01 W resolution exactly once.
- Make deterministic `test_mode` available to every supported meter profile. PRO2 and B21 expose L1 only; PRO380 and B23 expose coherent three-phase values.
- Add TCP raw packet diagnostics controls to the dashboard: **Download logs** and **Copy to clipboard**.
- Document the diagnostic workflow for capturing BMW Wallbox Modbus requests and comparing raw frames with the selected meter profile.
- Expand regression coverage for Janitza scaling and single-/three-phase test-mode behaviour.

## 0.2.23

- Add an optional PRO2 test mode for hardware compatibility diagnostics.
- When enabled with `meter_model: inepro_pro2`, the proxy cycles deterministic single-phase current values: 0, 6, 10, 16, 20, 25, 32, 25, 20, 16, 10 and 6 A.
- Generate coherent 230 V / 50 Hz / unity-PF power values alongside the current sequence.
- Advance the sequence per Modbus register-map request so the BMW Wallbox can be observed against changing meter readings without Home Assistant sensor data.
- Add regression tests and add-on configuration wiring for `test_mode`.

## 0.2.22

- Fix add-on configuration wiring so `meter_model` is passed from the Home Assistant add-on options into the runtime.
- Show the effective configured meter profile consistently in the web UI and Modbus register-map selection.
- Log the active meter model at add-on startup for easier diagnostics.
- Add automated tests covering meter-model environment/configuration wiring and web profile rendering/API exposure.
- Add GitHub Actions CI to run the full pytest suite on every pull request and push to `main`.
- Add a complete `CONFIGURATION.md` reference covering every Home Assistant add-on option and fixed runtime/network settings.
- Expand README configuration documentation and keep add-on configuration references synchronized.

## 0.2.21

- Document the supported meter profiles and their protocol-specific behaviour
- Add profile-specific Home Assistant entity requirements and configuration guidance
- Distinguish meter model selection from transport/compatibility settings in the web UI
- Show the active meter profile, protocol details, current register and entity roles in Settings
- Add PRO2 single-phase configuration and troubleshooting documentation
- Clarify that valid Modbus responses do not by themselves prove BMW Wallbox meter acceptance
- Document startup/request-sequence capture as the safe diagnostic approach when the Wallbox falls back to the 6 A conservative limit

## 0.2.18

- Answer non-read Modbus requests with a proper exception reply instead of silently dropping them; RTU frames are now length-decoded per function code rather than assumed to be 8 bytes
- Reply with exception code 4 when a register build fails so one bad live value cannot tear down the charger session
- Clamp out-of-range live values to the IEEE754 single-precision limits instead of raising
- Log session duration, request count, reply count and time since the last reply on every disconnect
- Detect and surface stale Home Assistant data: live data age is shown on the dashboard, exposed in /api/state, and logged when it goes stale or recovers
- Reuse one pooled HTTP session for Home Assistant reads, bound each read with a configurable timeout, and hold a fixed poll cadence
- Treat unavailable/unknown entity states as unavailable rather than read errors
- Close connections gracefully and only send RST when preempting a stale connection, so a reply in flight is never discarded
- Serve a request already in flight before handing over to a newly connected client

## 0.2.17

- Enable TCP_NODELAY on the Modbus client socket so responses are never delayed by Nagle's algorithm
- Recover from RTU CRC errors by resyncing the byte stream instead of disconnecting the charger
- Serve a reconnecting charger or bridge immediately by replacing the stale connection instead of leaving it queued
