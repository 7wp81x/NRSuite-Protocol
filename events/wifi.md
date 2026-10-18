# Wi-Fi Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `scan_ap` | `ssid`, `bssid`, `channel`, `rssi`, `security`, `wps`, `band` | Emitted by `SCAN_WIFI`; `band` is `2g` or `5g` |
| `deauth_stats` | `status`, `mode`, `bssid?`, `client?`, `channel?`, `count?`, `requested_frames?`, `sent_frames`, `failed_frames`, `duration_s?`, `interval_ms`, `elapsed_ms?`, `stopped?`, `reason?` | Burst completion, loop progress (`status:"running"`), or loop completion (`status:"finished"`) |
| `client_detected` | `client`, `bssid?`, `ssid?`, `subtype`, `rssi`, `channel` | Client detector |
| `client_associated` | `client`, `bssid`, `rssi` | Portal association monitor |
| `hidden_ap` | `bssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Hidden AP observed |
| `hidden_ssid_candidate` | `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Probe-request candidate |
| `hidden_ssid_resolved` | `bssid`, `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Association-based resolution |
| `hidden_ap_hop` | `channel` | Hidden AP channel hop |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
