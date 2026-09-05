# BMW Wallbox Proxy (Multi-Meter)

Home Assistant add-on for emulating the Modbus smart meter expected by a BMW Wallbox Gen4, using measurements supplied by Home Assistant.

This fork is intended for testing and installations where the enhanced meter-model support needs to run **alongside the original BMW Wallbox Proxy**.

## Supported meter models

| Model | Installation | Encoding | Serial settings |
|---|---|---|---|
| `inepro_pro380` | 3-phase | IEEE-754 FLOAT32, ABCD | 9600 8E1, address 1 |
| `inepro_pro2` | **1-phase** | IEEE-754 FLOAT32, ABCD | 9600 8E1, address 1 |
| `janitza_b23` | 3-phase | 32-bit scaled integers | Must match Wallbox configuration |

The selected `meter_model` must match the meter model configured in the BMW Wallbox Installation App.

### Inepro PRO380

The `inepro_pro380` profile follows the documented PRO380 Modbus register map, including voltage, current, active/reactive/apparent power, power factor, frequency and energy registers.

Measurement values are IEEE-754 FLOAT32 using ABCD byte/word order. The implementation uses the documented register addresses rather than treating the PRO380 as a generic floating-point device.

### Inepro PRO2

The `inepro_pro2` profile is specifically intended for **single-phase installations**.

It uses the PRO2 register map and FLOAT32 ABCD encoding. Registers that are PRO380-only L2/L3 measurements are returned as zero instead of duplicating L1 values.

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
3. Add:

```text
https://github.com/romulocintra/bmw_wallboxproxy
```

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

## Example configuration

For a single-phase installation using the PRO2 profile:

```yaml
meter_model: inepro_pro2
transport_mode: rtu_over_tcp
float_word_order: abcd
register_alias_mode: exact
```

For a three-phase PRO380:

```yaml
meter_model: inepro_pro380
```

For Janitza B23:

```yaml
meter_model: janitza_b23
```

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

### The Wallbox does not detect the meter

Check, in order:

1. The BMW Installation App meter model matches `meter_model`.
2. Modbus address matches; normally `1` for PRO380/PRO2.
3. Serial settings match exactly; PRO380/PRO2 default to `9600 8E1`.
4. Waveshare is operating as a transparent serial/TCP bridge.
5. RS485 polarity is correct: pin 8 = D+, pin 9 = D-.
6. The Wallbox is actually sending Modbus requests.
7. The proxy returns a response with a valid CRC.
8. PRO380/PRO2 responses contain FLOAT32 ABCD data.
9. Janitza responses use B23 scaled integers rather than FLOAT32.
10. The correct add-on is running and listening on host port `502`.

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
