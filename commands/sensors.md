# Sensor Commands

## LD2450 mmWave Radar

The LD2450 is a 24 GHz mmWave presence/target radar connected to the ESP32
over UART (`256000 8N1`). The firmware parses the standard 30-byte target
frame and exposes up to three targets with X/Y position, speed, and range
resolution.

| Command | Args | Response | Notes |
|---|---|---|---|
| `LD2450_SET_CONFIG` | `{rx_gpio:int, tx_gpio:int}` | `{ok, msg, configured, rx_pin, tx_pin, ld2450_rx_gpios:[...], ld2450_tx_gpios:[...]}` plus status fields | Validates target-safe, distinct UART pins, stops the driver, persists them in ESP32 NVS, and reports the saved configuration. |
| `LD2450_START` | `{debug?:bool=false}` | `{ok:true, active, debug, valid_frames, invalid_frames, dropped_bytes, target_count, presence, has_data, last_frame_ms, last_frame_age_ms, baud, rx_pin, tx_pin, configured, ld2450_rx_gpios:[...], ld2450_tx_gpios:[...]}` | Starts/restarts the UART driver using the saved RX/TX pins. `debug` is off by default in app/protocol mode; enable it only for standalone serial bring-up. |
| `LD2450_STOP` | none | `{ok:true, active:false, ...}` | Stops parsing and clears the live target list. |
| `LD2450_STATUS` | none | `{ok:true, active, debug, valid_frames, invalid_frames, dropped_bytes, target_count, presence, has_data, last_frame_ms, last_frame_age_ms, baud, rx_pin, tx_pin, configured, ld2450_rx_gpios:[...], ld2450_tx_gpios:[...]}` | Returns current driver, GPIO configuration, safe GPIO choices, and frame counters. |

Events emitted while active:

- `ld2450_targets` — one event per valid 30-byte frame.
- `ld2450_presence` — target-present / target-lost transition.
- `ld2450_error` — parse errors or no-data timeout.

### Sign convention

X/Y/speed use **bit 15 plus 15-bit magnitude**, not two's-complement:

- bit 15 = 1 -> positive magnitude
- bit 15 = 0 -> negative magnitude

Coordinates are millimetres, speed is cm/s, resolution is millimetres.
The corrected firmware follows the reference ESPHome/HLK-LD2450 decoder.

> The LD2450 requires a stable 5 V supply unless the carrier explicitly
> supports 3.3 V. UART logic is 3.3 V-compatible. RX/TX must be crossed to
> the ESP32 (`sensor TX -> ESP32 RX`, `sensor RX -> ESP32 TX`) and must not
> share the ESP32 UART0 pins used by the USB-UART bridge.
