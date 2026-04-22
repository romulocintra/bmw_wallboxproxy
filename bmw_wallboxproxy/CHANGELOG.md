## 0.2.14

- Map power offset to HA entity instead of a fixed numeric value
- Add power offset setup guide to README

## 0.2.12

- Add phase mapping troubleshooting section to README

## 0.2.11

- Add phase remapping setting to reorder output L1/L2/L3
- All six phase order permutations selectable from the dashboard

## 0.2.10

- Add persistent power offset with GUI control
- Power offset can be adjusted from the dashboard and survives restarts

## 0.2.9

- Send TCP RST on disconnect for faster charger reconnect

## 0.2.8

- Disconnect on RTU CRC fail to resync the receive buffer
- Prevents the charger from stopping after a buffer misalignment

## 0.2.7

- Add Modbus output register table to dashboard
- Shows every register value as sent to the charger; negative power highlighted

## 0.2.6

- Fix power unit scaling: divide W values by 1000 before writing PRO380 registers
- Apparent power and power factor are corrected automatically

## 0.2.5

- Replace transport auto-detection with an explicit framing mismatch error
- Wrong transport mode now disconnects immediately with a clear log message

## 0.2.4

- Rebrand UI from BMW Meter Emulator to BMW Wallboxproxy
- Remove outdated HA config callout from the dashboard

## 0.2.3

- Two-phase idle timeout: separate initial connect timeout from established session idle timeout
- Prevents disconnect loops caused by slow charger connections

## 0.2.2

- Clean up dashboard UI
- Fix dashboard state API

## 0.2.1

- Package as Home Assistant add-on with ingress support
- Persist settings to env file across restarts
- Use HA supervisor API proxy for token-free local access
