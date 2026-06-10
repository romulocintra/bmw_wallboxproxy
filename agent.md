# Agent Guide - BMW Wallbox Proxy

## Objective

This project is a Home Assistant-focused Modbus meter emulator for a BMW wallbox.

The current implementation does not just emulate a PRO380-style meter over RTU framing. It provides a configurable TCP listener that can speak either:

- RTU over TCP for a serial gateway running in transparent mode
- Native Modbus TCP for direct TCP clients

Live values come from Home Assistant entity states and are exposed through a Flask UI plus JSON APIs.

## Current Runtime Topology

The implemented runtime is:

1. Home Assistant add-on starts the container via run.sh.
2. run.sh sets add-on defaults and exports APP_ENV_FILE=/data/bmw_wallboxproxy.env.
3. app.py validates startup conditions, installs shutdown hooks, and starts:
  - ha_poller thread
  - tcp_server_loop thread
  - Flask web app
4. ha_client.py polls Home Assistant REST state endpoints and updates shared live values.
5. dr_client.py accepts exactly one TCP client at a time and serves Modbus responses.
6. webapp.py exposes the dashboard, settings page, and runtime configuration APIs.

This is packaged as a Home Assistant add-on with ingress enabled. The web UI is intended to be accessed through Home Assistant ingress, while the Modbus port stays exposed separately for the wallbox or gateway.

## Architecture Summary

### Processes and Threads

- app.py is the entrypoint.
- ha_client.py runs as a background polling thread.
- dr_client.py runs as a background TCP server thread.
- Flask serves the UI and JSON endpoints.

### Shared State

state.py owns the runtime state for:

- latest Home Assistant-backed meter values
- transport mode
- float word order
- register alias mode
- compatibility profile name
- counters and timestamps
- rolling Modbus, network, and raw TCP logs

All of this is held in-process behind locks.

### Configuration Sources

The implementation uses three configuration layers:

1. Add-on options in config.yaml
  - currently only ha_token
2. Environment variables
  - direct process overrides
3. Persistent runtime env file
  - defaults to .env for local runs
  - /data/bmw_wallboxproxy.env in the add-on container

The settings page writes runtime settings back to the env file so they survive restart.

## Implemented Protocol Behavior

### Supported Transports

The server supports two framing modes:

- modbus_tcp
- rtu_over_tcp

The selected mode is runtime configurable.

Current defaults:

- add-on startup default in run.sh: rtu_over_tcp
- config.py fallback default when no env file is present: modbus_tcp

Do not simplify the documentation to only one mode unless the code changes.

### Supported Function Codes

Only read operations are implemented:

- FC 03
- FC 04

Unsupported function codes return Modbus exception code 1.
Invalid quantities return Modbus exception code 3.
Wrong slave id requests are ignored.

### Slave Address

- Fixed slave id: 1

There is no multi-slave support.

### Framing Rules

For rtu_over_tcp mode:

- requests are expected as 8-byte RTU read frames
- CRC is verified
- CRC errors do not disconnect: leading garbage bytes are dropped until the buffer realigns on a CRC-valid frame (wireless bridges can inject or lose bytes)
- replies include CRC

For modbus_tcp mode:

- requests use MBAP headers
- protocol id must be 0
- MBAP length is validated
- replies include MBAP headers and no CRC

The TCP server actively closes the connection when incoming traffic does not match the selected framing mode.

### Connection Model

- one listening socket
- one active client at a time
- a new incoming connection preempts the active one: the stale connection is closed and the newest client is served immediately (a reconnecting charger or bridge is never queued behind a half-dead session)
- SO_REUSEADDR enabled
- TCP_NODELAY enabled on the client socket so small responses are sent without Nagle delay (the charger polls every 200 ms)
- TCP keepalive configured where supported
- idle disconnect supported via MODBUS_IDLE_DISCONNECT_SECONDS
- transport mode changes force the active client to reconnect

This matches a gateway-or-wallbox use case rather than a multi-client Modbus service.

## Register Model

The register map is built on demand from the latest Home Assistant values.

### Input Value Set

The live value model currently contains 13 externally sourced fields:

- u1
- u2
- u3
- i1
- i2
- i3
- p_total
- freq
- p1
- p2
- p3
- e_import_total
- e_export_total

If Home Assistant reads fail, the last successful values remain in memory.
Startup defaults come from config.DEFAULTS.

### Derived Values

register_map.py derives additional values instead of reading them from Home Assistant:

- average voltage
- total current
- reactive power values, currently hard-coded to 0.0
- apparent power values derived from absolute active power
- power factor values derived from active and apparent power
- total active energy as import + export

Document these as implemented behavior, not as physical truth.

### Address Layout

The current map includes the PRO380-style 0x5000 and 0x6000 ranges used by the UI and register map builder.

Important implemented addresses include:

- 0x5000 average voltage
- 0x5002..0x5007 phase voltages
- 0x5008 frequency
- 0x500A..0x5011 total and phase currents
- 0x5012..0x5031 active, reactive, apparent power and power factor blocks
- 0x6000..0x6023 energy blocks

Every value is encoded as a 32-bit IEEE754 float over two Modbus registers.

### Word Order

The implementation supports:

- abcd
- cdab

This is a runtime setting and part of compatibility profiles.

### Register Alias Modes

The implementation can mirror each register pair to adjacent addresses to accommodate off-by-one client behavior:

- exact
- alias_minus_1
- alias_plus_1
- alias_both

This is implemented in register_map.py and must be reflected in documentation.

## Compatibility Profiles

state.py defines runtime presets:

- pro380-default
- pro380-offset-minus-1
- pro380-swapped-words
- pro380-offset-and-swapped
- gateway-modbus-tcp

These profiles change:

- transport mode
- float word order
- register alias mode

The UI exposes these profiles and the selected profile is reported in /api/state.

## Home Assistant Integration

### Data Source

ha_client.py fetches entity state values from:

- GET /api/states/<entity_id>

using a bearer token.

### Polling Model

- polling interval is currently 1 second
- each configured entity is fetched independently
- successful reads update the shared value store
- failed reads increment counters and are logged

### Runtime-configurable HA Settings

The settings page can update:

- HA_URL
- HA_VERIFY_TLS
- all Home Assistant entity ids used for live data

The token is not editable through the web UI in add-on mode. It comes from the add-on option ha_token.

## Web UI and API Surface

### Pages

- / dashboard
- /settings settings page

### API Endpoints

- /api/state
- /api/settings/transport-mode
- /api/settings/float-word-order
- /api/settings/register-alias-mode
- /api/settings/compatibility-profile
- /api/settings/ha-live-data

### API State Payload

/api/state returns:

- current live values
- stats and counters
- Modbus log
- network log
- raw TCP log
- runtime settings and allowed options

This endpoint is also the add-on watchdog target.

## Startup and Deployment Behavior

### Local Run Expectations

For local runs, the application expects HA_TOKEN to be available through:

- environment variable
- or .env next to app.py

Binding to low ports such as 502 may require elevated privileges or CAP_NET_BIND_SERVICE on Linux and WSL.

### Add-on Mode

run.sh currently sets:

- APP_ENV_FILE=/data/bmw_wallboxproxy.env
- MODBUS_LISTEN_HOST=0.0.0.0
- MODBUS_LISTEN_PORT=502
- WEBAPP_HOST=0.0.0.0
- WEBAPP_PORT=8099
- WEBAPP_SSL_MODE=off
- WEBAPP_USE_RELOADER=false

Ingress is enabled in config.yaml and the UI is intended to run over plain HTTP internally.

## Logging and Diagnostics

The system keeps rolling logs for:

- decoded Modbus events
- network and connection events
- raw TCP payload traces

Stats also track:

- HA read successes and failures
- TCP connects and disconnects
- RX and TX frames
- CRC failures
- wrong slave id count
- short frame count
- unsupported function count
- illegal quantity count
- bytes RX and TX
- last request metadata
- active compatibility settings

The dashboard is built around these diagnostics and should be kept in sync with backend behavior.

## Changelog

When bumping the version in `bmw_wallboxproxy/config.yaml`, add a matching entry to `bmw_wallboxproxy/CHANGELOG.md` in the same commit. One entry per version, bullet points only, no fluff.

## Constraints for Future Changes

When updating this project, assume these constraints unless the implementation is intentionally changed:

- preserve add-on ingress behavior
- preserve separate Modbus TCP port exposure
- preserve runtime persistence to the env file
- preserve single-client connection semantics unless there is a clear reason to change them
- preserve compatibility profiles and transport switching behavior
- preserve the ability to use either RTU over TCP or native Modbus TCP

If any of those change in code, agent.md should be updated in the same change.

## Non-Goals in the Current Implementation

The code does not currently implement:

- write registers
- multiple slave ids
- serial port access from Python
- direct RS485 handling
- per-phase energy accumulation from Home Assistant
- non-float register encodings

## Source of Truth

If this guide and the code disagree, the code is the source of truth.

In particular, check these files before changing behavior or docs:

- app.py
- config.py
- state.py
- ha_client.py
- dr_client.py
- register_map.py
- webapp.py
- run.sh
- config.yaml
