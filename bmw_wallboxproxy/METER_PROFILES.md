# Meter profiles and Home Assistant data

The add-on supports multiple BMW Wallbox Gen4 smart-meter profiles. `meter_model` selects the **meter register map and data encoding**. It is independent from `transport_mode`, `float_word_order`, and `register_alias_mode`.

The selected meter profile must match the meter type configured in the BMW Wallbox Installation App.

## Profiles

| `meter_model` | Meter | Phases | L1 current register | Encoding |
|---|---|---:|---:|---|
| `inepro_pro380` | Inepro PRO380 | 3 | `0x500C` | IEEE-754 FLOAT32, ABCD by default |
| `inepro_pro2` | Inepro PRO2-Mod | 1 | `0x500C` | IEEE-754 FLOAT32, ABCD by default |
| `janitza_b23` | Janitza B23 312-10J | 3 | `0x5B0C` | B23 scaled 32-bit values |

Do not treat a profile as merely a different display format. The address map itself changes. For example, the Inepro profiles use `0x500C` for L1 current while the B23 uses `0x5B0C`.

## Home Assistant entity requirements

The proxy accepts a generic set of Home Assistant entities. The runtime does not reject an installation merely because an entity is empty; instead, missing values fall back to the proxy defaults. The following classification describes what should be configured for a useful emulation.

### Inepro PRO2-Mod — single phase

**Minimum for current/load-management testing:**

```yaml
i1_entity: sensor.<grid_l1_current>
```

**Recommended for a complete electrical snapshot:**

```yaml
u1_entity: sensor.<grid_l1_voltage>
i1_entity: sensor.<grid_l1_current>
p_total_entity: sensor.<grid_power>
freq_entity: sensor.<grid_frequency>
p1_entity: sensor.<grid_l1_power>
```

**Optional:**

```yaml
e_import_total_entity: sensor.<imported_energy>
e_export_total_entity: sensor.<exported_energy>
power_offset_entity: input_number.<power_offset>
```

Do not configure L2/L3 entities merely to populate a PRO2 model. The PRO2 implementation is single-phase and deliberately returns zero for PRO380-only L2/L3 measurements.

### Inepro PRO380 — three phase

Recommended configuration:

```yaml
u1_entity: sensor.<grid_l1_voltage>
u2_entity: sensor.<grid_l2_voltage>
u3_entity: sensor.<grid_l3_voltage>
i1_entity: sensor.<grid_l1_current>
i2_entity: sensor.<grid_l2_current>
i3_entity: sensor.<grid_l3_current>
p_total_entity: sensor.<grid_power>
freq_entity: sensor.<grid_frequency>
p1_entity: sensor.<grid_l1_power>
p2_entity: sensor.<grid_l2_power>
p3_entity: sensor.<grid_l3_power>
```

Imported/exported energy and the power-offset entity are optional.

### Janitza B23 — three phase

Recommended configuration is the same three-phase HA data set as PRO380:

```yaml
u1_entity: sensor.<grid_l1_voltage>
u2_entity: sensor.<grid_l2_voltage>
u3_entity: sensor.<grid_l3_voltage>
i1_entity: sensor.<grid_l1_current>
i2_entity: sensor.<grid_l2_current>
i3_entity: sensor.<grid_l3_current>
p_total_entity: sensor.<grid_power>
freq_entity: sensor.<grid_frequency>
p1_entity: sensor.<grid_l1_power>
p2_entity: sensor.<grid_l2_power>
p3_entity: sensor.<grid_l3_power>
```

The B23 encoder applies its documented scaling when converting these values to Modbus registers. It must not use the Inepro FLOAT32 interpretation.

## Transport versus meter profile

These are separate configuration concepts:

- `meter_model`: what virtual meter the Wallbox sees.
- `transport_mode`: how Modbus frames are transported to the proxy.
- `float_word_order`: FLOAT32 word order for the Inepro profiles.
- `register_alias_mode`: legacy address compatibility for the Inepro profiles.

For a Waveshare configured as a transparent RS485/TCP bridge:

```yaml
meter_model: inepro_pro2
transport_mode: rtu_over_tcp
float_word_order: abcd
register_alias_mode: exact
```

The Waveshare must carry the raw Modbus RTU bytes. Do not combine a Modbus TCP-to-RTU conversion in the Waveshare with `rtu_over_tcp` in the proxy.

## Wallbox acceptance versus Modbus validity

A valid Modbus exchange does **not** by itself prove that the BMW Wallbox has accepted the virtual meter as a valid smart meter.

For example, a PRO2 current request can be syntactically valid:

```text
01 03 50 0C 00 02 15 08
```

with a valid FLOAT32 response and CRC. The Wallbox may still reject the meter profile or enter a conservative charging limit.

For commissioning, do not deliberately inject artificial current values if the Wallbox is already limiting charging because of an unaccepted meter. Keep the Home Assistant data live and capture the Modbus traffic from a Wallbox restart. The startup/request sequence is more useful for determining whether the Wallbox is missing an identification or validation register than changing the current value.

## Configuration UI

The Home Assistant add-on configuration exposes all entity keys because the add-on schema is generic. The web UI Settings page provides the profile-aware documentation:

- active meter model;
- phase count and encoding;
- current register used by the profile;
- minimum entity set;
- recommended entities;
- fields that are not used by the selected profile;
- current runtime values.

Change the actual options in the Home Assistant add-on configuration, then save and restart the add-on. The web UI is a read-only runtime view.
