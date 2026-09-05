# BMW Wallbox Proxy (Multi-Meter)

Home Assistant add-on for emulating the Modbus smart meter expected by a BMW Wallbox Gen4, using measurements supplied by Home Assistant.

This fork is intended for testing and installations where the enhanced meter-model support needs to run **alongside the original BMW Wallbox Proxy**.

## Supported meter models

| Model | Installation | Encoding | Serial settings | L1 current register |
|---|---|---|---|---|
| `inepro_pro380` | 3-phase | IEEE-754 FLOAT32, ABCD | 9600 8E1, address 1 | `0x500C` |
| `inepro_pro2` | **1-phase** | IEEE-754 FLOAT32, ABCD | 9600 8E1, address 1 | `0x500C` |
| `janitza_b23` | 3-phase | 32-bit scaled integers | Must match Wallbox configuration | `0x5B0C` |

The selected `meter_model` must match the meter model configured in the BMW Wallbox Installation App. `meter_model` is the virtual meter profile; it is separate from the TCP/RTU transport and compatibility settings.

See [`METER_PROFILES.md`](METER_PROFILES.md) for profile-specific Home Assistant entity requirements and [`CONFIGURATION.md`](CONFIGURATION.md) for the complete add-on option reference.

## Configuration

The Home Assistant add-on configuration is the source of truth. Change options in the add-on configuration page, save, and restart the add-on. The web UI is read-only and shows the effective runtime profile.

### All add-on options

| Option | Default | Description |
|---|---|---|
| `ha_token` | empty | Optional Home Assistant long-lived token; Supervisor mode normally uses the Supervisor token instead. |
| `meter_model` | `inepro_pro380` | Virtual meter profile: `inepro_pro380`, `inepro_pro2`, or `janitza_b23`. |
| `transport_mode` | `rtu_over_tcp` | Modbus framing: raw RTU carried over TCP or Modbus TCP. |
| `float_word_order` | `abcd` | FLOAT32 word order for Inepro profiles. |
| `register_alias_mode` | `exact` | Legacy register compatibility mode for Inepro profiles. |
| `u1_entity` | empty | Home Assistant L1 voltage entity. |
| `u2_entity` | empty | Home Assistant L2 voltage entity. |
| `u3_entity` | empty | Home Assistant L3 voltage entity. |
| `i1_entity` | empty | Home Assistant L1 current entity. Minimum useful HA input for PRO2 current/load-management testing. |
| `i2_entity` | empty | Home Assistant L2 current entity. |
| `i3_entity` | empty | Home Assistant L3 current entity. |
| `p_total_entity` | empty | Home Assistant total active-power entity. |
| `freq_entity` | empty | Home Assistant grid-frequency entity. |
| `p1_entity` | empty | Home Assistant L1 active-power entity. |
| `p2_entity` | empty | Home Assistant L2 active-power entity. |
| `p3_entity` | empty | Home Assistant L3 active-power entity. |
| `e_import_total_entity` | empty | Home Assistant aggregate imported/forward energy entity. |
| `e_export_total_entity` | empty | Home Assistant aggregate exported/reverse energy entity. |
| `power_offset_entity` | empty | Optional Home Assistant Number helper supplying a power offset in watts. |

For profile-specific requirements, use **Meter Profile / Settings** in the web UI or read [`METER_PROFILES.md`](METER_PROFILES.md).

### Single-phase PRO2 example

```yaml
meter_model: inepro_pro2
transport_mode: rtu_over_tcp
float_word_order: abcd
register_alias_mode: exact
u1_entity: sensor.inverter_grid_l1_voltage
i1_entity: sensor.inverter_grid_l1_current
p_total_entity: sensor.inverter_grid_power
freq_entity: sensor.inverter_grid_frequency
p1_entity: sensor.inverter_grid_power
e_import_total_entity: sensor.inverter_grid_imported_energy
e_export_total_entity: sensor.inverter_grid_exported_energy
power_offset_entity: input_number.wallbox_power_offset
```

For a minimal current-only test, `i1_entity` is the important field. L2/L3 inputs are not required for PRO2.

## Meter profiles

### Inepro PRO380

The `inepro_pro380` profile follows the documented PRO380 Modbus register map, including voltage, current, active/reactive/apparent power, power factor, frequency and energy registers. Measurement values are IEEE-754 FLOAT32 using ABCD byte/word order.

### Inepro PRO2

The `inepro_pro2` profile is specifically intended for **single-phase installations**. It uses the PRO2 register map and FLOAT32 ABCD encoding. Registers that are PRO380-only L2/L3 measurements are returned as zero instead of duplicating L1 values.

### Janitza B23

The `janitza_b23` profile uses the B23 register map and scaled 32-bit representation. Voltage uses 0.1 V, current 0.01 A, active/reactive/apparent power 0.01 W/var/VA, and frequency 0.01 Hz. Signed values are handled according to the B23 register definition.

## Parallel installation with the original add-on

This fork deliberately uses a different Home Assistant add-on name and slug:

```text
Name: BMW Wallbox Proxy (Multi-Meter)
Slug: bmw_wallboxproxy_multimeter
Host TCP port: 502
Container TCP port: 502
```

The different slug allows the fork to be installed separately from the original add-on. Both add-ons use the standard host TCP port `502`, so **only one of them should be running at a time**.

### Install the fork

1. Open **Settings → Add-ons → Add-on Store**.
2. Open the three-dot menu and select **Repositories**.
3. Add the repository shown on the project page.
4. Refresh the store.
5. Install **BMW Wallbox Proxy (Multi-Meter)**.

The original add-on can remain installed separately, but stop it before starting this fork if it is using port `502`.

## Recommended Waveshare setup

When using a Waveshare RS485-to-Ethernet adapter, use it as a **transparent serial/TCP bridge** when the proxy is configured with:

```yaml
transport_mode: rtu_over_tcp
```

Topology:

```text
BMW Wallbox Gen4
      │
      │ RS485 / Modbus RTU
      ▼
Waveshare RS485 → Ethernet
      │
      │ TCP carrying raw RTU frames
      ▼
BMW Wallbox Proxy (Multi-Meter)
      │
      │ TCP :502
      ▼
Home Assistant
```

Do not configure the Waveshare as a Modbus TCP-to-RTU gateway while also using `rtu_over_tcp` in the proxy.

## PRO380 / PRO2 serial settings

For the documented/default Inepro configuration:

```text
Baud rate:    9600
Data bits:    8
Parity:       Even
Stop bits:    1
Modbus ID:    1
```

In compact notation this is **9600 8E1**.

The BMW Wallbox RS485 connection is:

```text
Pin 8: 485 D+ / Tx+ / Rx+
Pin 9: 485 D- / Tx- / Rx-
```

The communication parameters configured in the BMW Installation App must match the proxy/bridge path.

## Modbus protocol behaviour

The proxy validates incoming RTU frames before responding:

- Modbus RTU CRC is checked.
- Requests for another slave address are ignored.
- Responses are encoded according to the selected meter model.
- PRO380/PRO2 values use FLOAT32 ABCD.
- Janitza B23 values use the documented scaled integer representation.

Example PRO380/PRO2 request for L1 current:

```text
01 03 50 0C 00 02 15 08
```

Example Janitza B23 request for L1 current:

```text
01 03 5B 0C 00 02 17 2C
```

## Web UI

The **Meter Profile / Settings** page is a read-only view of the effective configuration. It shows the active meter model, profile details, current register, required/recommended/optional entity fields, configured HA entities, and transport/authentication state.

The meter profile shown by the UI is read from the same runtime `METER_MODEL` value used by the Modbus register map. The add-on startup explicitly imports `meter_model` from the Home Assistant add-on configuration, so changing the add-on option and restarting keeps the configuration and UI synchronized.

## Tests and CI

The repository contains tests for meter-model mapping, Modbus encoding/protocol behaviour, power offsets, profile dispatch, configuration wiring, and web profile rendering/API output.

GitHub Actions runs `pytest -q` automatically on every pull request and on pushes to `main`.

Run locally from the repository root:

```bash
pip install -r bmw_wallboxproxy/requirememts.txt
pip install pytest
pytest -q
```

## Troubleshooting

### The Wallbox does not detect or accept the meter

A valid Modbus exchange does **not** by itself prove that the BMW Wallbox has accepted the virtual meter. If the Wallbox limits charging to a conservative value, do not use artificial current values as the first diagnostic.

Check, in order:

1. The BMW Installation App meter model matches `meter_model`.
2. Modbus address matches; normally `1` for PRO380/PRO2.
3. Serial settings match exactly; PRO380/PRO2 default to `9600 8E1`.
4. Waveshare is operating as a transparent serial/TCP bridge when using `rtu_over_tcp`.
5. RS485 polarity is correct: pin 8 = D+, pin 9 = D-.
6. The Wallbox is actually sending Modbus requests.
7. The proxy returns a response with a valid CRC.
8. PRO380/PRO2 responses contain FLOAT32 ABCD data.
9. Janitza responses use B23 scaled integers rather than FLOAT32.
10. Restart the Wallbox and capture the initial request sequence; look for identification/validation reads before relying only on the recurring measurement poll.
11. The correct add-on is running and listening on host port `502`.

A healthy PRO380/PRO2 exchange should look like:

```text
TCP RX  01 03 50 0C 00 02 15 08
TCP TX  01 03 04 XX XX XX XX CRC CRC
```

A healthy B23 exchange should look like:

```text
TCP RX  01 03 5B 0C 00 02 17 2C
TCP TX  01 03 04 XX XX XX XX CRC CRC
```

## Disclaimer

This is an independent open-source project and is not affiliated with, endorsed by, or sponsored by BMW AG, BMW Group, Inepro, Janitza, Waveshare, Delta Electronics, or any related company.
