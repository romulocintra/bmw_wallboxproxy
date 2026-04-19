# BMW Wallbox Proxy

This add-on runs the BMW wallbox meter emulator inside Home Assistant.

## What it does

- Polls Home Assistant entities for live electrical values.
- Exposes a Modbus TCP endpoint for the BMW wallbox or a serial gateway.
- Serves the dashboard and settings UI through Home Assistant ingress.

## Install

1. Add this repository to Home Assistant as a local or Git-based add-on repository.
2. Install the BMW Wallbox Proxy add-on.
3. Set `ha_token` in the add-on configuration.
4. Start the add-on.
5. Open the web UI from Home Assistant and configure the Home Assistant URL, TLS verification, and entity IDs.

## Network

- Modbus listener: container port `502/tcp`, mapped to host port `502` by default.
- Web UI: served through ingress on internal port `8099`.

## HTTP vs HTTPS for the web UI

The add-on web server should run on plain HTTP internally. Home Assistant ingress terminates the authenticated browser session and proxies requests to the add-on. Enabling HTTPS inside the Flask app is unnecessary for ingress and tends to complicate routing and certificate handling.

## Persistence

Runtime settings saved in the web UI are stored in `/data/bmw_wallboxproxy.env` inside the add-on container, which persists across restarts and backups.

## Notes

- The Home Assistant API token stays in the add-on configuration and is injected at startup.
- The current package uses ingress for the UI and keeps the Modbus listener exposed separately for the wallbox.