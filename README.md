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

See [`METER_PROFILES.md`](METER_PROFILES.md) for the profile-specific Home Assistant entity requirements.

### Inepro PRO380

The `inepro_pro380` profile follows the documented PRO380 Modbus register map, including voltage, current, active/reactive/apparent power, power factor, frequency and energy registers.

Measurement values are IEEE-754 FLOAT32 using ABCD byte/word order. The implementation uses the documented register addresses rather than treating the PRO380 as a generic floating-point device.

### Inepro PRO2

The `inepro_pro2` profile is specifically intended for **single-phase installations**.

It uses the PRO2 register map and FLOAT32 ABCD encoding. Registers that are PRO380-only L2/L3 measurements are returned as zero instead of duplicating L1 values.

For current/load-management testing, `i1_entity` is the minimum useful HA input. A more complete emulation should also provide `u1_entity`, `p_total_entity`, `freq_entity`, and `p1_entity`.

### Janitza B23

The `janitza_b23` profile uses the B23 register map and its scaled 32-bit representation:

- Voltage: `0.1 V`
- Current: `0.01 A`
- Active/reactive/apparent power: `0.01 W/var/VA`
- Frequency: `0.01 Hz`

Signed values are handled according to the B23 register definition.

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

Do not configure the Waveshare as a Modbus TCP-to-RTU gateway while also using `rtu_over_tcp` in the proxy. That would convert the Modbus framing twice.

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

## Configuration

The Home Assistant add-on schema intentionally exposes a common set of entity fields for all meter profiles. The profile-specific requirements are documented in the web UI Settings page and in [`METER_PROFILES.md`](METER_PROFILES.md).

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
```

For a minimal current-only test, `i1_entity` is the important field. For normal commissioning, configure the recommended PRO2 fields above rather than relying on defaults.

### Three-phase PRO380 example

```yaml
meter_model: inepro_pro380
transport_mode: rtu_over_tcp
float_word_order: abcd
register_alias_mode: exact
u1_entity: sensor.inverter_grid_l1_voltage
u2_entity: sensor.inverter_grid_l2_voltage
u3_entity: sensor.inverter_grid_l3_voltage
i1_entity: sensor.inverter_grid_l1_current
i2_entity: sensor.inverter_grid_l2_current
i3_entity: sensor.inverter_grid_l3_current
p_total_entity: sensor.inverter_grid_power
freq_entity: sensor.inverter_grid_frequency
p1_entity: sensor.inverter_grid_l1_power
p2_entity: sensor.inverter_grid_l2_power
p3_entity: sensor.inverter_grid_l3_power
```

### Janitza B23 example

```yaml
meter_model: janitza_b23
transport_mode: rtu_over_tcp
u1_entity: sensor.inverter_grid_l1_voltage
u2_entity: sensor.inverter_grid_l2_voltage
u3_entity: sensor.inverter_grid_l3_voltage
i1_entity: sensor.inverter_grid_l1_current
i2_entity: sensor.inverter_grid_l2_current
i3_entity: sensor.inverter_grid_l3_current
p_total_entity: sensor.inverter_grid_power
freq_entity: sensor.inverter_grid_frequency
```

Do not apply Inepro FLOAT32 assumptions to the B23 profile.

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

## PRO2-Mod physical meter emulation

The `inepro_pro2` profile is a dedicated single-phase **Inepro PRO2-Mod** emulator. It is intentionally based on the manufacturer's PRO2-Mod Modbus register map rather than treating PRO2 as a reduced PRO380.

The documented serial defaults are:

```text
9600 baud
8 data bits
Even parity
1 stop bit
Modbus address 1
```

The implementation now exposes the documented PRO2 read-only configuration/identity area (`0x4000`-`0x401D`), the single-phase measurement area (`0x5000`-`0x502A`) and the complete energy area through `0x6049`.

Known manufacturer defaults are represented as meter values:

- Modbus ID `1`
- Baud register `9600` (`0x2580`)
- Meter rating `100 A`
- S0 output `1000 imp/kWh`
- Combination code `01` / C01 (forward only)
- LCD cycle `10 s`
- Parity `01` / even
- Current direction `F`
- Error code `0`
- Power-down counter `0`
- Present quadrant `1`
- Tariff `1` / T1

Device-unique values such as serial number, firmware/hardware versions, checksum and active-status word cannot be reconstructed from Home Assistant sensor data, so the emulator uses stable zero placeholders for those fields. These are deliberately documented as placeholders rather than being presented as real meter identity.

All PRO2 measurement values use the documented IEEE-754 FLOAT32 ABCD representation. L2/L3 measurement registers are not treated as real PRO2 measurements because the manufacturer marks those fields as PRO380-only.

The energy map is complete. Only aggregate total/forward/reverse active-energy values are sourced from Home Assistant; tariff-specific, phase-specific and reactive-energy values remain explicit zeroes because the proxy currently has no corresponding HA entities.

This profile is intended to be tested against a BMW Wallbox Gen4 configured as an **Inepro PRO2**. A syntactically valid Modbus response is not proof that the Wallbox has accepted the virtual meter. If the Wallbox enters a conservative charging limit, keep the HA values live and capture the traffic from a Wallbox restart rather than injecting artificial current values.

## Phase Mapping

The proxy maps grid-meter phases L1/L2/L3 to the phases expected by the wallbox. Incorrect mapping can cause wrong per-phase power readings and unnecessary load-management throttling.

The dashboard provides the six possible phase-order mappings. The selected order is persisted across restarts.

A zero total with an uneven per-phase distribution is not necessarily a mapping error: a symmetric three-phase charger can reach its total-power target while normal household phase imbalance remains.

## Power Offset

Power offset shifts the power readings presented to the wallbox by a fixed number of watts.

The recommended approach is to use a Home Assistant Number helper and configure its entity as `power_offset_entity`.

A negative offset makes the charger see more export and therefore tends to increase charging/back-feeding. A positive offset has the opposite effect.

The dashboard also provides a temporary manual override for commissioning and diagnostics.

## Tests

The repository contains tests for:

- PRO380 FLOAT32 ABCD encoding and register mapping
- PRO380 energy-register mapping
- PRO2 single-phase behaviour
- PRO2 zeroed L2/L3 registers
- Janitza B23 scaled integer encoding and signed power
- Meter-model dispatch and invalid models
- Modbus CRC validation
- RTU-over-TCP request/response handling
- Wrong slave address and invalid CRC handling
- Power-offset behaviour
- Register alias behaviour

Run the suite from the repository root with:

```bash
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
