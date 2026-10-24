# NFC / RFID Events

## PN532 ISO14443A reader

### `rfid_status`

Emitted after a successful configuration or scan-state transition.

| Field | Type | Description |
|---|---|---|
| `type` | string | `rfid_status` |
| `connected` | bool | PN532 detected and initialized |
| `configured` | bool | SDA/SCL GPIOs are stored in NVS |
| `interface` | string | Always `i2c` in this milestone |
| `sda_gpio` | int | Configured SDA GPIO, or `-1` when unset |
| `scl_gpio` | int | Configured SCL GPIO, or `-1` when unset |
| `firmware_version` | string | Human-readable PN532 version, for example `1.6` |
| `firmware_version_raw` | uint32 | Raw Adafruit/PN532 firmware response |
| `scanning` | bool | ISO14443A polling active |
| `tag_read_only` | bool | Always `true` in milestone 1 |
| `rfid_gpios` | int[] | Target-safe GPIO choices |

### `rfid_tag`

Emitted when an ISO14443A target is found. Repeated sightings of the same UID
are suppressed for a short interval to avoid flooding the bridge.

| Field | Type | Description |
|---|---|---|
| `type` | string | `rfid_tag` |
| `uid` | string | Uppercase hexadecimal UID, no separators |
| `atqa` | string | Four uppercase hex digits, transmission order |
| `sak` | string | Two uppercase hex digits |
| `type` | string | Estimated tag family (heuristic) |
| `timestamp_ms` | uint32 | ESP32 uptime in milliseconds |
| `read_only` | bool | Always `true` in milestone 1 |

### `rfid_error`

Emitted for configuration, initialization, or scan-start failures. The app
should display the message and refresh `RFID_STATUS`.

| Field | Type | Description |
|---|---|---|
| `type` | string | `rfid_error` |
| `kind` | string | `config`, `start`, or `error` |
| `msg` | string | Human-readable error |
| `connected` | bool | PN532 connected state at the time of the error |
| `scanning` | bool | Scan state at the time of the error |

The app must treat tag identification as read-only and must not infer memory
layout or issue write/lock operations from these events alone.
