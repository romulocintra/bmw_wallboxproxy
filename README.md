# BMW Wallbox Proxy

Home Assistant add-on repository for a BMW wallbox Modbus meter emulator backed by Home Assistant sensor data.

## Install in Home Assistant

1. Open Home Assistant.
2. Go to Settings -> Add-ons -> Add-on Store.
3. Open the three-dot menu and select Repositories.
4. Add `https://github.com/AndreasFridh/bmw_wallboxproxy`.
5. Refresh the store and install `BMW Wallbox Proxy`.

The add-on itself lives in [bmw_wallboxproxy/config.yaml](bmw_wallboxproxy/config.yaml) and exposes:

- Home Assistant ingress UI on internal port `8099`
- Modbus TCP on host port `502`

Configure transport mode and Home Assistant entity mappings in the Home Assistant add-on configuration panel. The web UI is intended for dashboard and diagnostics.

## Phase Mapping

The proxy maps the three phases from your grid meter (L1, L2, L3) to the three phases the wallbox expects. If the wiring order between your grid meter and the wallbox does not match, the charger will read the wrong per-phase power values, which can cause incorrect load management or prevent the back-feeding session from stabilising.

### Symptoms of wrong phase order

- The BMW app shows 0 W total grid power but the per-phase breakdown is clearly unbalanced (e.g. −200 W / +50 W / +150 W).
- The charger throttles or behaves erratically even though total grid power is within limits.
- Back-feeding works but one phase appears to be exporting significantly more than expected.

Note: a sum of zero with unbalanced phases is **not always a mapping problem**. A symmetric charger achieves its target (total = 0) and stops adjusting. The residual per-phase spread is then just normal household load imbalance across phases, which a symmetric charger cannot compensate for.

### How to set the phase order

Open the proxy dashboard, find the **Phase Order** section, and select one of the six buttons (1,2,3 through 3,2,1). The setting is persisted to the env file and survives restarts.

### How to identify the correct phase order without trial and error

1. Note which phase on the grid meter shows the largest negative deviation (that is the phase the charger is back-feeding onto).
2. Check which phase the charger reports as its active output phase (visible in the BMW app or the Home Assistant wallbox integration).
3. Match them: the grid meter phase that swings most = the charger's reported active phase. Use that relationship to determine the full ordering and select the matching button.

Alternatively, if the charger supports a single-phase mode, enable it, start a session, and observe which grid meter phase changes. That phase is charger L1. The remaining two are then found by elimination or by repeating with L2.

### BMW / Starcharge DC bidirectional charger (2026)

The BMW wallbox manufactured by Starcharge uses a **symmetric 3-phase AC/DC stage**. It applies the same current on all three phases simultaneously and cannot control individual phase currents independently.

Practical consequences:

- The charger reads per-phase grid data primarily to detect single-phase overload, not to independently balance each phase.
- It adjusts total charge/discharge power based on the sum of all three phases.
- Once the total reaches the target (typically 0 W net import), the charger holds that rate. Any remaining per-phase spread is household load imbalance and is unaffected by the charger.
- Phase mapping still matters: a wrong mapping can cause the charger to misidentify which phase is overloaded and throttle unnecessarily.

With the correct phase order configured, the charger should run stable back-feeding sessions overnight without intervention.