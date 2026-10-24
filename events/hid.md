# HID Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `pin_session_status` | `state`, `mode`, `source`, `reason?`, `attempts_total`, `attempts_in_cycle`, `current_sequence`, `last_pin`, `last_error?`, `typing_delay_ms`, `start_delay_ms`, `started_at`, `updated_at`, `persisted_in_nvs` | Session state changed |
| `pin_attempt` | `mode`, `source`, `pin`, `current_sequence`, `attempts_total`, `attempts_in_cycle`, `estimated_total`, `max_attempts`, `started_at`, `updated_at` | One PIN was typed over HID |
| `pin_range_done` | `mode`, `source`, `attempts_total`, `last_pin`, `stop_reason`, `started_at`, `updated_at` | Range/wordlist exhausted or safety cap reached |
| `pin_range_error` | `code`, `msg` | Session or HID transport error |
| `ble_pin_session_status` | `state`, `mode:"ble_hid_live"`, `source`, `configured`, `ble_connected`, `ble_advertising`, `ble_state`, `bonded`, `peer`, `attempts_total`, `attempts_in_cycle`, `current_sequence`, `last_pin`, `next_pin?`, `progress_percent`, `cooldown_active`, `cooldown_remaining_ms`, `reason?` | BLE HID PIN state changed |
| `ble_pin_attempt` | `pin`, `current_sequence`, `attempts_total`, `attempts_in_cycle`, `estimated_total`, `max_attempts`, `skipped`, `started_at`, `updated_at` | A BLE HID PIN was typed, or explicitly skipped |
| `ble_pin_done` | `attempts_total`, `last_pin`, `stop_reason`, `started_at`, `updated_at` | BLE HID PIN session finished |
| `ble_pin_error` | `code`, `msg` | BLE HID PIN session/transport error |
| `ble_pin_connection` | `state`, `ble_connected`, `ble_advertising`, `bonded`, `peer`, `auto_reconnect` | BLE advertising/connection state changed |

HID is one-way from the ESP32's perspective. These events report what the
device typed; they do **not** indicate that the target device accepted a PIN.

> Authorized lab/testing use only. Failed PINs can lock or wipe target devices.
