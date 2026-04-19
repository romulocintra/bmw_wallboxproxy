# BMW Wallbox Proxy

This add-on runs the BMW wallbox meter emulator inside Home Assistant.

## What it does

- Polls Home Assistant entities for live electrical values.
- Exposes a Modbus TCP endpoint for the BMW wallbox or a serial gateway.
- Serves the dashboard and settings UI through Home Assistant ingress.

## Install

1. Add this repository to Home Assistant as a local or Git-based add-on repository.
2. Install the BMW Wallbox Proxy add-on.
3. Configure the add-on options in Home Assistant for transport mode, word order, register alias mode, and the Home Assistant entity IDs you want to expose.
4. Start or restart the add-on.
5. Use the web UI for dashboard and diagnostics.

## Network

- Modbus listener: container port `502/tcp`, mapped to host port `502` by default.
- Web UI: served through ingress on internal port `8099`.

## HTTP vs HTTPS for the web UI

The add-on web server should run on plain HTTP internally. Home Assistant ingress terminates the authenticated browser session and proxies requests to the add-on. Enabling HTTPS inside the Flask app is unnecessary for ingress and tends to complicate routing and certificate handling.

## Notes

- The current package uses ingress for the UI and keeps the Modbus listener exposed separately for the wallbox.
- Add-on settings are sourced from the Home Assistant add-on configuration instead of the web UI.