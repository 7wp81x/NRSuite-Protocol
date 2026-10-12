# HID Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `pin_session_status` | `state`, `mode`, `source`, `reason?`, `attempts_total`, `attempts_in_cycle`, `current_sequence`, `last_pin`, `last_error?`, `started_at`, `updated_at`, `persisted_in_nvs` | Session state changed |
| `pin_attempt` | `mode`, `source`, `pin`, `current_sequence`, `attempts_total`, `attempts_in_cycle`, `started_at`, `updated_at` | One PIN was typed over HID |
| `pin_range_done` | `mode`, `source`, `attempts_total`, `last_pin`, `started_at`, `updated_at` | Range/wordlist exhausted |
| `pin_range_error` | `code`, `msg` | Session or HID transport error |

HID is one-way from the ESP32's perspective. These events report what the
device typed; they do **not** indicate that the target device accepted a PIN.

> Authorized lab/testing use only. Failed PINs can lock or wipe target devices.
