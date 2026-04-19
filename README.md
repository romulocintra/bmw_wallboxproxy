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