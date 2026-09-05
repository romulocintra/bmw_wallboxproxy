# Configuration reference

The Home Assistant add-on configuration is the source of truth. After changing options, save the add-on configuration and restart the add-on. The web UI is read-only and displays the effective runtime configuration.

## Meter profiles

| Option | Values | Default | Purpose |
|---|---|---|---|
| `meter_model` | `inepro_pro380`, `inepro_pro2`, `janitza_b23` | `inepro_pro380` | Selects the virtual meter register map and encoding. Must match the meter selected in the BMW Installation App. |

`inepro_pro380` and `inepro_pro2` use IEEE-754 FLOAT32 values. `janitza_b23` uses the documented B23 scaled representation. The profile is independent from the transport settings below.

## Modbus transport

| Option | Values | Default | Purpose |
|---|---|---|---|
| `transport_mode` | `rtu_over_tcp`, `modbus_tcp` | `rtu_over_tcp` | Selects the framing expected by the proxy. Use `rtu_over_tcp` with a transparent RS485/TCP bridge carrying raw RTU frames. |
| `float_word_order` | `abcd`, `cdab` | `abcd` | FLOAT32 word order used by Inepro profiles. `abcd` is the documented/default order for PRO380/PRO2. |
| `register_alias_mode` | `exact`, `alias_minus_1`, `alias_plus_1`, `alias_both` | `exact` | Legacy register-address compatibility mode for Inepro profiles. Janitza B23 does not use Inepro aliases. |

For a Waveshare transparent bridge, the normal combination is:

```yaml
meter_model: inepro_pro2
transport_mode: rtu_over_tcp
float_word_order: abcd
register_alias_mode: exact
```

Do not configure the Waveshare as a Modbus TCP-to-RTU converter at the same time as `rtu_over_tcp` in the proxy.

## Home Assistant authentication

| Option | Type | Default | Purpose |
|---|---|---|---|
| `ha_token` | password | empty | Optional Home Assistant long-lived access token. In Home Assistant Supervisor mode the add-on's Supervisor token is used instead. |

The add-on declares `homeassistant_api: true` and normally uses the Supervisor API internally. The web UI reports the effective authentication mode but does not expose credentials.

## Home Assistant entity mappings

All entity options are strings and may be left empty. Empty or unavailable entities fall back to the proxy's safe/default values; profile documentation identifies which inputs are useful or recommended.

| Option | Data | Used by | Purpose |
|---|---|---|---|
| `u1_entity` | Voltage L1 | PRO380, PRO2, B23 | L1 voltage |
| `u2_entity` | Voltage L2 | PRO380, B23 | L2 voltage |
| `u3_entity` | Voltage L3 | PRO380, B23 | L3 voltage |
| `i1_entity` | Current L1 | all profiles | L1 current; minimum useful input for PRO2 current/load-management testing |
| `i2_entity` | Current L2 | PRO380, B23 | L2 current |
| `i3_entity` | Current L3 | PRO380, B23 | L3 current |
| `p_total_entity` | Total power | all profiles | Total active power |
| `freq_entity` | Frequency | all profiles | Grid frequency |
| `p1_entity` | Power L1 | PRO380, B23; recommended PRO2 | L1 active power |
| `p2_entity` | Power L2 | PRO380, B23 | L2 active power |
| `p3_entity` | Power L3 | PRO380, B23 | L3 active power |
| `e_import_total_entity` | Imported energy | all profiles | Aggregate imported/forward active energy |
| `e_export_total_entity` | Exported energy | all profiles | Aggregate exported/reverse active energy |
| `power_offset_entity` | Number helper, watts | optional | Adds a fixed power offset before values are presented to the charger |

### Recommended PRO2 single-phase configuration

```yaml
u1_entity: sensor.inverter_grid_l1_voltage
i1_entity: sensor.inverter_grid_l1_current
p_total_entity: sensor.inverter_grid_power
freq_entity: sensor.inverter_grid_frequency
p1_entity: sensor.inverter_grid_power
e_import_total_entity: sensor.inverter_grid_imported_energy
e_export_total_entity: sensor.inverter_grid_exported_energy
power_offset_entity: input_number.wallbox_power_offset
```

L2/L3 entities are not required for PRO2. They are deliberately not treated as real PRO2 measurements.

## Complete example

```yaml
ha_token: ""
meter_model: inepro_pro2
transport_mode: rtu_over_tcp
float_word_order: abcd
register_alias_mode: exact
u1_entity: sensor.inverter_grid_l1_voltage
u2_entity: ""
u3_entity: ""
i1_entity: sensor.inverter_grid_l1_current
i2_entity: ""
i3_entity: ""
p_total_entity: sensor.inverter_grid_power
freq_entity: sensor.inverter_grid_frequency
p1_entity: sensor.inverter_grid_power
p2_entity: ""
p3_entity: ""
e_import_total_entity: sensor.inverter_grid_imported_energy
e_export_total_entity: sensor.inverter_grid_exported_energy
power_offset_entity: input_number.wallbox_power_offset
```

## Add-on runtime/network settings

The following values are fixed by the add-on package rather than exposed as user options:

| Setting | Value | Meaning |
|---|---|---|
| Modbus host | `0.0.0.0` | Listen on all container interfaces |
| Modbus port | `502` | BMW Wallbox Modbus TCP listener |
| Web UI host | `0.0.0.0` | Listen on all container interfaces |
| Web UI port | `8099` | Home Assistant ingress backend |
| Ingress | enabled | Web UI is exposed through Home Assistant ingress |
| Add-on host TCP port | `502` | Host port mapped to container port 502 |

These are intentionally not duplicated in the Home Assistant options schema.

## Where to verify configuration

Open the add-on Web UI and go to **Meter Profile / Settings**. It shows:

- active `meter_model`
- meter profile and phase count
- register encoding and L1 current register
- required, recommended and optional HA entities
- configured entity values
- transport and Home Assistant authentication status
- current session/request information

If the displayed meter profile does not match the Home Assistant add-on configuration, restart the add-on and check the startup log for `Meter model: ...`. The add-on startup explicitly imports `meter_model` from the Home Assistant configuration.
