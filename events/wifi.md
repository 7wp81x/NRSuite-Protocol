# Wi-Fi Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `scan_ap` | `ssid`, `bssid`, `channel`, `rssi`, `security`, `wps`, `band` | Emitted by `SCAN_WIFI`; `band` is `2g` or `5g` |
| `deauth_stats` | `status`, `mode`, `bssid?`, `client?`, `channel?`, `count?`, `requested_frames?`, `sent_frames`, `failed_frames`, `duration_s?`, `interval_ms`, `elapsed_ms`, `pps`, `stopped?`, `reason?` | Burst completion, loop progress (`status:"running"`), or loop completion (`status:"finished"`) |
| `client_detected` | `client`, `bssid?`, `ssid?`, `subtype`, `rssi`, `channel` | Client detector |
| `client_associated` | `client`, `bssid`, `rssi` | Portal association monitor |
| `hidden_ap` | `bssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Hidden AP observed |
| `hidden_ssid_candidate` | `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Probe-request candidate |
| `hidden_ssid_resolved` | `bssid`, `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Association-based resolution |
| `hidden_ap_hop` | `channel` | Hidden AP channel hop |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)


## WPS Pixie Dust events

| Event type | Fields | Notes |
|---|---|---|
| `wps_pixie_progress` | `run_id`, `stage`, `message?` | Stages include `associate`, `identity`, `m1`...`m8`, `wrong-pin`, `complete` |
| `wps_pixie_wrong_pin` | `run_id`, `bssid`, `ssid`, `channel`, `pke`, `pkr`, `e_nonce`, `r_nonce`, `e_hash1`, `e_hash2`, `auth_key`, `m3_only`, `reason`, `first_half_valid?` | Complete material for the app-side offline PIN search. `m3_only:true` means the exchange stopped after M3 and did not send M4. |
| `wps_pixie_psk` | `run_id`, `bssid`, `ssid`, `pin`, `psk`, `auth_type`, `encr_type` | Full M1-M8 success |
| `wps_pixie_error` | `run_id`, `code`, `message`, `retry_after_s?` | `code` values include `wps_locked`, `m2d`, `nack_before_m3`, `m1_timeout`, `m3_timeout`, `timeout`, `target_not_found`, and `stopped`. Timeouts are terminal for that attempt; the app must not auto-retry them. |


## Implemented automation consumers

- `deauth_stats` includes `elapsed_ms` and `pps` alongside sent/failed counters.
- Probe Request Monitor aggregates `client_detected` events with
  `subtype:"probe_request"` in the app; no new firmware event is required.
