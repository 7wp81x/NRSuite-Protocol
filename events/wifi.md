# Wi-Fi Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `scan_ap` | `ssid`, `bssid`, `channel`, `rssi`, `security`, `wps`, `band` | Emitted by legacy `SCAN_WIFI` calls. Firmware with `scan_results_pull` returns the same objects through `SCAN_RESULTS` when the app requests pull mode. |
| `deauth_stats` | `status`, `mode`, `bssid?`, `client?`, `channel?`, `target_bssid?`, `target_count?`, `count?`, `requested_frames?`, `sent_frames`, `failed_frames`, `duration_s?`, `interval_ms`, `elapsed_ms`, `pps`, `stopped?`, `reason?`, `targets?` | Burst completion, loop progress (`status:"running"`), or loop completion (`status:"finished"`). `mode:"multi"` includes aggregate and per-target `{bssid,channel,requested_frames,sent_frames,failed_frames}` counters. |
| `client_detected` | `client`, `bssid?`, `ssid?`, `subtype`, `rssi`, `channel` | Client detector |
| `client_associated` | `client`, `bssid`, `rssi` | Portal association monitor |
| `hidden_ap` | `bssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Hidden AP observed |
| `hidden_ssid_candidate` | `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Probe-request candidate |
| `hidden_ssid_resolved` | `bssid`, `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Association-based resolution |
| `hidden_ap_hop` | `channel` | Hidden AP channel hop |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)


## WPS Lock Detector events

| Event type | Fields | Notes |
|---|---|---|
| `wps_lock_ap` | `ssid`, `bssid`, `channel`, `rssi`, `security`, `wps`, `wps_parsed`, `lock_reported`, `ap_setup_locked`, `wps_version`, `config_methods`, `selected_registrar`, `last_seen_ms` | Emitted by legacy `WPS_LOCK_SCAN` calls. Pull-capable firmware returns the same objects through `SCAN_RESULTS`. Records originate from the active-scan WPS candidate set and may be enriched by a passive WPS IE pass. `lock_reported:false` means the AP did not advertise the WPS AP Setup Locked attribute and should be shown as likely unlocked rather than confirmed unlocked. When `include_non_wps:true`, non-WPS APs are returned as `scan_ap` records with `wps:false`. |

## WPS Pixie Dust events

| Event type | Fields | Notes |
|---|---|---|
| `wps_pixie_progress` | `run_id`, `stage`, `message?` | Stages include `associate`, `identity`, `m1`...`m8`, `wrong-pin`, `complete` |
| `wps_pixie_wrong_pin` | `run_id`, `bssid`, `ssid`, `channel`, `pke`, `pkr`, `e_nonce`, `r_nonce`, `e_hash1`, `e_hash2`, `auth_key`, `m3_only`, `reason`, `first_half_valid?` | Complete material for the app-side offline PIN search. `m3_only:true` means the exchange stopped after M3 and did not send M4. |
| `wps_pixie_psk` | `run_id`, `bssid`, `ssid`, `pin`, `psk`, `auth_type`, `encr_type` | Full M1-M8 success |
| `wps_pixie_error` | `run_id`, `code`, `message`, `retry_after_s?` | `code` values include `wps_locked`, `m2d`, `nack_before_m3`, `m1_timeout`, `m3_timeout`, `timeout`, `target_not_found`, and `stopped`. Timeouts are terminal for that attempt; the app must not auto-retry them. |


## Implemented automation consumers

- `deauth_stats` includes `elapsed_ms` and `pps` alongside sent/failed counters.
- `mode:"multi"` events identify the current `channel`/`target_bssid` and carry
  a `targets` array with per-target counters.
- Probe Request Monitor aggregates `client_detected` events with
  `subtype:"probe_request"` in the app; no new firmware event is required.

## WPS Attempt Detector events

| Event type | Fields | Notes |
|---|---|---|
| `wps_attempt_session` | `state`, `session_id`, `bssid`, `client`, `ssid`, `channel`, `rssi`, `stage`, `message_type`, `m1_seen`, `m2_seen`, `m3_seen`, `m4_seen`, `m5_seen`, `m6_seen`, `m7_seen`, `m8_seen`, `m2d_seen`, `nack_seen`, `crackable_material`, `credentials_likely_transferred`, `frames`, `first_seen_ms`, `last_seen_ms`, `duration_ms` | `state` is `started` or `progress`. `stage` is the latest observed stage: `Identity`, `M1`..`M8`, `M2D`, `ACK`, `NACK`, or `DONE`. The `*_seen` booleans preserve evidence from earlier in the same session, even if a later NACK/M2D becomes the latest stage. `crackable_material` is true when M1+M2+M3 were observed; `credentials_likely_transferred` is true when M7+M8 were observed. `ssid` is filled when firmware has observed a matching beacon/probe response. |

This event indicates observed WPS protocol activity, not proof of malicious
intent. Android may add source-MAC vendor metadata and a Low/Medium/High risk
label using session frequency, target/source diversity, and captured WPS
protocol evidence.

Risk guidance:

- **High:** the same session observed **M1+M2+M3** (offline WPS PIN-cracking
  material), or **M7+M8** (WPA PSK likely transferred). A later NACK does not
  remove earlier evidence.
- **Medium:** NACK/M2D alone, partial M1-M3 evidence, M7 without M8, multiple
  attempts, or multiple source MACs.
- **Low:** an isolated identity/single-message observation with no crackable or
  credential-transfer evidence.

### WPS attempt live lock-state event

| Event type | Fields | Notes |
|---|---|---|
| `wps_ap_lock_state` | `bssid`, `ssid`, `channel`, `rssi`, `wps_parsed`, `lock_reported`, `ap_setup_locked`, `observed_at_ms` | Emitted by the WPS Attempt Detector when it first observes or detects a change in an AP's WPS lock state. Android treats this as live evidence; absence of the lock attribute maps to likely-unlocked with reduced confidence. |

The app combines this live event with the last `WPS_LOCK_SCAN` result. Saved scan state is contextual only and expires; live observations take precedence for risk escalation.
