# NRSuite Version Compatibility

This table tracks which app version, firmware version, and protocol spec version are compatible.

Always check this table when pairing an app release with a firmware release.

## Compatibility Matrix

| App version | Firmware version | Protocol spec | Notes |
|---|---|---|---|
| v1.0.0-beta | v1.0.0-beta | v1.0 | Initial beta |
| v1.0.0-beta.2 | v1.0.0-beta.2 | v1.0 | Defense, BLE recon, multi-device USB, and flasher updates |
| v1.0.0-beta.2.2 / beta.2.4 | v1.0.0-beta.2 | v1.0 | External UART bridge and CH340/CP210x/FTDI hotfixes |
| v1.0.0-beta.3 | v1.0.0-beta.3 | v1.0 | IR, sensors, C5 dual-band, NRuGochi, and flasher fixes |
| v1.0.0-beta.3.1 | v1.0.0-beta.3.1 | v1.0 | Portal restart hardening, visitor logs, scan reliability, IR DB/GPIO refinements, and beta.3.1 fixes |
| v1.0.0-beta.3.1.1 | v1.0.0-beta.3.1.1 | v1.0 | IRDB presence/caching hotfix and WPS Pixie support across all ESP32 targets |
| v1.0.0-beta.3.2.0 | v1.0.0-beta.3.2.0 | v1.0 / proto_minor 2 | Dual USB/UART transport, device telemetry, pull-based scan results, scan transport diagnostics; legacy event fallback retained |
| next mesh beta | next mesh beta | v1.1 draft | Mesh Foundation: HKDF key provisioning, USB auth challenge, master election, session IDs, heartbeat |

## How to read this table

- App and firmware on the **same row** are confirmed compatible.
- Mixing versions across rows may work if the protocol spec version matches, but is not tested.
- The protocol spec version is the compatibility key. If both builds implement spec `v1.0`, they should be compatible regardless of patch version.

## Checking versions at runtime

The app queries the firmware during the connection handshake via `STATUS`:

```json
{
  "ok": true,
  "chip": "ESP32-S3",
  "fw": "1.0.0-beta.2",
  "proto": 1,
  "proto_minor": 0,
  "device_id": "NR1A2B3C4D",
  "features": ["wifi", "sniff", "deauth", "beacon", "portal"]
}
```

The app displays the firmware version and device ID. Minor version mismatches are generally safe. Major version mismatches may cause command failures.

## Spec change log

### proto_minor 2 - beta.3.2 additive scan-results reliability
- Add `scan_results_pull` capability and `SCAN_RESULTS`.
- Add optional `pull_results:true` to `SCAN_WIFI` and `WPS_LOCK_SCAN`.
- Add `scan_id`, `kind`, `truncated`, `offset`, `total`, `next_offset`, and
  `crc32` to scan result responses.
- Firmware retains a bounded 32-record snapshot and stops emitting the legacy
  result event burst when pull mode is requested.
- Legacy firmware/app combinations continue to use `scan_ap` and
  `wps_lock_ap` events.
- No frame-format or breaking JSON changes; `proto` remains `1`.

### v1.0 - beta.3.1 additive updates
- Added `portal_client_seen` with IP, best-effort MAC, User-Agent, request type, and timestamp.
- Added `request_type` to `captive_data`; GET `/login` and credential-like GET query fields are captured in addition to POST.
- Documented `SCAN_WIFI` `settle_ms` and `dwell_ms`, adaptive low-result scans, and response `dwell_ms`.
- No on-wire breaking changes; protocol compatibility remains `v1.0`.

### v1.1 - Mesh Foundation (draft)
- Add `MESH_PROVISION_KEY`, `MESH_CLEAR_KEY`, `MESH_AUTH_CHALLENGE`, `MESH_STATUS`, `MESH_ACTIVATE`, and `MESH_DEACTIVATE`.
- Add mesh events: `mesh_status`, `mesh_heartbeat`, `mesh_node_joined`, `mesh_node_left`, `mesh_activation_result`, and `mesh_error`.
- Add `proto_minor` to `STATUS`; `proto` remains an integer.
- Add `mesh` feature flag, advertised only when valid derived keys are stored.
- Add `mesh_provision` capability flag, advertised whenever mesh provisioning support is compiled in.
- Document `NRxxxxxxxx` device ID format.
- Mesh transport uses HKDF-SHA256-derived keys and mbedTLS AES-CCM.
- No breaking changes to the v1.0 frame format.

### v1.0 - documentation refresh for beta.2
- Corrected EVENT envelope documentation from `event` to `type`.
- Added current command namespaces:
  - Wi-Fi scan, sniff, client detector, hidden AP revealer
  - Deauth detector
  - Captive portal and Evil Twin helpers
  - BLE scanner, BLE GATT profiler, and BLE HID
  - USB MSC and BadUSB
- Added `STATUS` field and feature-flag reference.
- Added event reference for scanner, defense, portal, and BLE events.
- Added optional `psram` feature flag for S3 builds with initialized external PSRAM.
- Added optional `temp_c` internal chip/die temperature and `temp_sensor` capability.
- No on-wire breaking changes; protocol version remains `v1.0`.

### v1.0 - initial
- Frame format: `[0xAD 0xDE][type][id][length 4B LE][payload]`
- Frame types: COMMAND, RESPONSE, EVENT, PCAP, ACK, HTML
