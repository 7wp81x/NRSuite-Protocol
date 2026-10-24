# Sensor Events

## LD2450 mmWave Radar

### `ld2450_targets`

Emitted once for each valid 30-byte LD2450 target frame.

| Field | Type | Description |
|---|---|---|
| `type` | string | `ld2450_targets` |
| `uptime` | uint32 | Milliseconds since boot |
| `target_count` | uint8 | Number of valid targets in the frame (0-3) |
| `has_data` | bool | True after at least one valid frame has been parsed |
| `valid_frames` | uint32 | Cumulative valid frame counter |
| `targets` | array | Zero to three target objects |

Target object:

| Field | Type | Description |
|---|---|---|
| `slot` | uint8 | 1-3 target slot |
| `x_mm` | int16 | Lateral position, millimetres |
| `y_mm` | int16 | Forward position, millimetres |
| `speed_cm_s` | int16 | Radial speed, cm/s; negative = approaching, positive = receding |
| `resolution_mm` | uint16 | Reported distance resolution, millimetres |

### `ld2450_presence`

Emitted on a presence transition.

| Field | Type | Description |
|---|---|---|
| `type` | string | `ld2450_presence` |
| `uptime` | uint32 | Milliseconds since boot |
| `present` | bool | True when one or more targets are present |
| `target_count` | uint8 | Number of valid targets at transition time |

### `ld2450_error`

Emitted for parse errors or when no valid frame has arrived after startup.

| Field | Type | Description |
|---|---|---|
| `type` | string | `ld2450_error` |
| `kind` | string | `parse_error` or `no_data` |
| `msg` | string | Human-readable error |
| `active` | bool | Driver active state |
| `valid_frames` | uint32 | Cumulative valid frame counter |
| `invalid_frames` | uint32 | Cumulative invalid frame counter |
| `dropped_bytes` | uint32 | Bytes discarded while hunting for a frame header |
| `last_frame_age_ms` | uint32 | Age of the last valid frame, or 0 if none |

The app should treat `ld2450_targets` as recovery evidence and clear the
last transient error state when new data arrives.
