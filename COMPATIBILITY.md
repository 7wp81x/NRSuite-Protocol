# NRSuite Version Compatibility

This table tracks which app version, firmware version, and protocol spec version are compatible.

Always check this table when pairing an app release with a firmware release.

## Compatibility Matrix

| App version | Firmware version | Protocol spec | Notes |
|---|---|---|---|
| v1.0.0-beta | v1.0.0-beta | v1.0 | Initial beta |
| v1.0.0-beta.2 | v1.0.0-beta.2 | v1.0 | Defense, BLE recon, multi-device USB, and flasher updates |

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
  "device_id": "NR1A2B3C4D",
  "features": ["wifi", "sniff", "deauth", "beacon", "portal"]
}
```

The app displays the firmware version and device ID. Minor version mismatches are generally safe. Major version mismatches may cause command failures.

## Spec change log

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
- No on-wire breaking changes; protocol version remains `v1.0`.

### v1.0 - initial
- Frame format: `[0xAD 0xDE][type][id][length 4B LE][payload]`
- Frame types: COMMAND, RESPONSE, EVENT, PCAP, ACK, HTML
