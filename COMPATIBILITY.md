# NRSuite Version Compatibility

This table tracks which app version, firmware version, and protocol spec version are compatible with each other.

Always check this table when pairing an app release with a firmware release.

## Compatibility Matrix

| App version | Firmware version | Protocol spec | Notes |
|---|---|---|---|
| v1.0.0-beta | v1.0.0-beta | v1.0 | Initial beta release |

## How to read this table

- App and firmware on the **same row** are confirmed compatible.
- Mixing versions across rows may work if the spec version matches, but is not tested and not supported -- update both sides together when possible.
- The protocol spec version is the authoritative compatibility key. If two builds both implement spec `v1.0`, they should be compatible regardless of app/firmware version patch numbers.

## Checking versions at runtime

The app queries the firmware version during connection handshake via the `STATUS` command:

```json
{
  "ok": true,
  "chip": "ESP32",
  "fw": "1.0.0-beta",
  "features": [...]
}
```

The app displays this version on the connection screen. If the version does not match the expected spec, the app will show a warning but will not block the connection -- minor version mismatches are generally safe; major version mismatches may cause command failures.

## Spec change log

### v1.0 (initial)
- Frame format: `[0xAD 0xDE][type][id][length 4B LE][payload]`
- Frame types: COMMAND, RESPONSE, EVENT, PCAP, ACK, HTML
- Commands: PING, STATUS, SCAN_WIFI, START_SNIFF, STOP_SNIFF, DEAUTH, START_BEACON, STOP_BEACON, BEACON_STATUS, PORTAL_STATUS
