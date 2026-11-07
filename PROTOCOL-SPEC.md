# NRSuite Wire Protocol Specification

**Wire major: 1.0**
**Latest additive revision: proto_minor 2 (pull-based scan results)**
**Next draft major/minor: 1.1 (Mesh Foundation)**
**Status: Stable (beta)**

This document is the authoritative reference for the NRSuite Android app and ESP32 firmware transport.

---

## Physical Transport

| Parameter | Value |
|---|---|
| Interface | USB serial (CDC-ACM or CH34x/CP210x/FTDI via USB-OTG) |
| Baud rate | 115200 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |

The transport is a raw byte stream. Framing and resynchronization are handled by this protocol.

---

## Frame Format

Every message is an 8-byte header followed by a payload.

| Offset | Size | Field |
|---|---|---|
| 0 | 1 | Magic byte 0: `0xAD` |
| 1 | 1 | Magic byte 1: `0xDE` |
| 2 | 1 | Frame type |
| 3 | 1 | Frame ID |
| 4 | 4 | Payload length, little-endian `uint32` |
| 8 | N | Payload (`0..1024` bytes) |

### Constants

| Name | Value |
|---|---|
| `MAGIC_0` | `0xAD` |
| `MAGIC_1` | `0xDE` |
| `HEADER_SIZE` | 8 bytes |
| `MAX_PAYLOAD_SIZE` | 1024 bytes |

### Frame IDs

- Command IDs are allocated per sender, starting at `0x01`, wrapping back to `0x01` after `0xFF`.
- A `RESPONSE` carries the same frame ID as the `COMMAND` it answers.
- PCAP chunk IDs use the same 1-byte field and are acknowledged by `ACK` frames.
- ID `0x00` is reserved for uncorrelated frames; currently used for app-to-firmware PCAP ACKs.

### Resynchronization

The decoder scans for `0xAD 0xDE`. If a frame is invalid (unknown type, payload longer than 1024 bytes, truncated), it discards one byte and scans forward for the next magic pair.

---

## Frame Types

| Name | Code | Direction | Description |
|---|---|---|---|
| `COMMAND` | `0x01` | App -> Firmware | JSON command with optional arguments |
| `RESPONSE` | `0x02` | Firmware -> App | Response to a command, same frame ID |
| `EVENT` | `0x03` | Firmware -> App | Async notification |
| `PCAP` | `0x04` | Firmware -> App | Raw PCAP chunk |
| `ACK` | `0x05` | App -> Firmware | Acknowledge a PCAP chunk |
| `HTML` | `0x06` | App -> Firmware | Reserved/legacy HTML upload frame. Current app uses the `RESET_HTML` and `SET_HTML_CHUNK` commands instead. |

---

## Session Lifecycle

```
App                                      Firmware
 |                                           |
 |-- COMMAND (id=1, cmd="PING") -----------> |
 |<- RESPONSE (id=1, {"ok":true}) ---------- |
 |                                           |
 |-- COMMAND (id=2, cmd="STATUS") ---------> |
 |<- RESPONSE (id=2, {chip, fw, features}) - |
 |                                           |
 |   session active                          |
 |                                           |
 |-- COMMAND (id=N, cmd="...") -------------> |
 |<- RESPONSE (id=N, {...}) ----------------- |
 |                                           |
 |<- EVENT (type="...") --------------------- | async, any time
 |                                           |
 |<- PCAP (id=chunk, raw bytes) ------------- | streaming capture
 |-- ACK (id=0, {"chunk":chunk}) ----------> |
```

### Connection establishment

1. App opens the USB serial port.
2. App sends `PING` with a short timeout.
3. App sends `STATUS` and reads chip, firmware version, device ID, and feature flags.
4. Session is considered active after a valid `STATUS` response.

### Timeouts

| Operation | Timeout |
|---|---|
| `PING` | 1500 ms (retried by app during reconnect) |
| `STATUS` | 5000 ms |
| Default command | 8000 ms |
| Long-running commands | specified per command |

### Disconnection

A USB read/write error is treated as a normal disconnect. Either side can close the port at any time.

---

## JSON Payloads

All `COMMAND`, `RESPONSE`, `EVENT`, and `ACK` payloads are UTF-8 JSON. `PCAP` and legacy `HTML` payloads are raw bytes.

### COMMAND

```json
{
  "cmd": "COMMAND_NAME",
  "args": {}
}
```

### RESPONSE

```json
{
  "ok": true
}
```

Failures may include a message:

```json
{
  "ok": false,
  "msg": "missing cmd"
}
```

### EVENT

Events use a `type` field:

```json
{
  "type": "EVENT_NAME"
}
```

> Important: the implementation uses `type`, not `event`.

### PCAP

Raw PCAP bytes. The firmware uses a sliding window and the app sends an ACK after each accepted chunk.

### ACK

```json
{
  "chunk": 42
}
```

`chunk` is the frame ID of the PCAP chunk being acknowledged. ACK frames use frame ID `0x00`.

---

## STATUS Response

`STATUS` is the main capability handshake.

```json
{
  "ok": true,
  "uptime": 123456,
  "heap": 123456,
  "heap_total": 327680,
  "heap_min_free": 98765,
  "heap_max_alloc": 110592,
  "psram_total": 8388608,
  "psram_free": 8000000,
  "chip": "ESP32-S3",
  "chip_cores": 2,
  "cpu_mhz": 240,
  "temp_c": 48.6,
  "flash_size": 4194304,
  "sdk": "v5.5.0",
  "proto": 1,
  "proto_minor": 2,
  "fw": "1.0.0-beta.2",
  "device_id": "NR1A2B3C4D",
  "country": "US",
  "allowed_2ghz_channels": [1,2,3,4,5,6,7,8,9,10,11],
  "allowed_5ghz_channels": [36,40,44,48,52,56,60,64,100,104,108,112,116,120,124,128,132,136,140,144,149,153,157,161,165],
  "features": ["wifi", "sniff", "deauth", "beacon", "portal"],
  "sniffing": false,
  "client_detecting": false,
  "portal": false,
  "beacon": false,
  "deauth_detector": false,
  "hidden_ap": false,
  "ble_scanning": false,
  "ble_profiling": false
}
```

| Field | Type | Description |
|---|---|---|
| `ok` | bool | Always present |
| `uptime` | uint32 | Firmware uptime in milliseconds |
| `heap` | uint32 | Free heap in bytes |
| `heap_total` | uint32? | Total allocator heap size in bytes. Additive optional field |
| `heap_min_free` | uint32? | Minimum free heap observed since boot. Additive optional field |
| `heap_max_alloc` | uint32? | Largest currently allocatable heap block in bytes. Additive optional field |
| `psram_total` | uint32? | PSRAM size in bytes; `0` when PSRAM is absent. Additive optional field |
| `psram_free` | uint32? | Free PSRAM in bytes; `0` when PSRAM is absent. Additive optional field |
| `chip` | string | `ESP32`, `ESP32-C2`, `ESP32-S2`, `ESP32-S3`, `ESP32-C3`, `ESP32-C5`, or `ESP32-C6` |
| `chip_cores` | uint8? | Number of CPU cores. Additive optional field |
| `cpu_mhz` | uint16? | Current CPU frequency in MHz. Additive optional field |
| `temp_c` | float? | Internal chip/die temperature in Celsius. Additive optional field; omitted when the sensor is unavailable |
| `flash_size` | uint32? | Flash size in bytes. Additive optional field |
| `sdk` | string? | ESP-IDF/Arduino SDK version string. Additive optional field |
| `proto` | int | Protocol major version. Currently `1` |
| `proto_minor` | int | Protocol minor version. Omitted means `0`; mesh builds report `1`; pull-based scan result builds report `2` |
| `fw` | string | Firmware version |
| `device_id` | string | Persistent `NRxxxxxxxx` ID from NVS (10 characters total) |
| `country` | string | Active Wi-Fi regulatory country, e.g. `01`, `US`, `GB` |
| `allowed_2ghz_channels` | int[] | 2.4 GHz channels currently permitted by the active regulatory country |
| `allowed_5ghz_channels` | int[] | 5 GHz channels currently permitted; empty when 5 GHz is unavailable |

Device telemetry fields are additive and optional. Clients must tolerate their
absence when connected to older firmware. Values reported in `STATUS` are a
snapshot; clients that display live uptime/heap should re-request `STATUS`
periodically rather than extrapolating from the initial handshake.
| `features` | string[] | Compiled feature flags |
| `sniffing` | bool | Sniffer active |
| `client_detecting` | bool | Client detector active |
| `oversized_frames` | uint32 | Count of oversized frames observed by firmware |
| `channel` | int | Current sniffer channel, when sniffing |
| `portal` | bool | Captive portal active |
| `beacon` | bool | Beacon spam active |
| `deauth_detector` | bool | Deauth detector active |
| `hidden_ap` | bool | Hidden AP detector active |
| `ble_scanning` | bool | BLE scanner active |
| `ble_profiling` | bool | BLE GATT profiler active |
| `beacon_ssids` | int | Beacon SSID count, when active |
| `beacon_sent` | uint32 | Beacon frames sent, when active |
| `beacon_channel` | int | Beacon channel, when active |
| `deauth_detector_channel` | int | Deauth detector channel, when active |
| `deauth_detector_hopping` | bool | Deauth detector hopping mode |
| `deauth_detected` | uint32 | Deauth frames detected |
| `deauth_detector_sent` | uint32 | Events sent to app |
| `deauth_detector_dropped` | uint32 | Events dropped by firmware |
| `hidden_ap_channel` | int | Hidden AP detector channel |
| `hidden_ap_hopping` | bool | Hidden AP detector hopping mode |
| `hidden_ap_seen` | uint32 | Hidden APs seen |
| `hidden_ap_candidates` | uint32 | Candidate SSIDs seen |
| `hidden_ap_resolved` | uint32 | SSIDs resolved |
| `hidden_ap_sent` | uint32 | Events sent |
| `hidden_ap_dropped` | uint32 | Events dropped |

`HEAP` is an alias for `STATUS`.

### Feature flags

| Flag | Meaning |
|---|---|
| `wifi` | Wi-Fi scan |
| `sniff` | Packet sniffer |
| `client_detect` | Client/presence detector |
| `deauth` | Deauth injection |
| `deauth_multi` | Firmware-native multi-target deauth with per-target channel scheduling |
| `deauth_detect` | Deauth detector |
| `beacon` | Beacon spam |
| `portal` | Captive portal / Evil Twin AP |
| `portal_html_offset` | HTML chunks support offset-based upload; current portals are file-backed (FAT on S2/S3, LittleFS on C3/C5/classic) |
| `html_diag` | HTML upload diagnostic events |
| `stop_all` | `STOP_ALL` command |
| `wps` | WPS flag included in `scan_ap` |
| `scan_results_pull` | Firmware retains a bounded `SCAN_WIFI`/`WPS_LOCK_SCAN` snapshot and supports `SCAN_RESULTS` chunk retrieval with CRC32 verification |
| `wifi_2ghz` | 2.4 GHz Wi-Fi band is supported |
| `wifi_5ghz` | 5 GHz Wi-Fi band is enabled in this firmware build (advertised by C5 builds) |
| `psram` | Internal heap is accompanied by initialized PSRAM; `psram_total` and `psram_free` are meaningful |
| `temp_sensor` | Firmware can report internal chip/die temperature as optional `temp_c` |
| `hidden_ap` | Hidden AP revealer |
| `storage` | Mass storage/file operations |
| `ld2450` | HLK-LD2450 mmWave radar parser and events |
| `ble_hid` | BLE HID |
| `ble_scan` | BLE scanner |
| `ble_profile` | Read-only BLE GATT profiler |
| `ble_pin_bruteforce` | BLE HID PIN range/wordlist tester with live CDC control |
| `msc` | USB MSC mode |
| `msc_read_chunk` | Chunked `MSC_READ` |
| `badusb` | Native USB HID BadUSB |
| `pin_bruteforce` | Native USB HID PIN range/wordlist tester |
| `mesh_provision` | Mesh provisioning support is compiled in; advertised even before keys are stored |
| `mesh` | Mesh Foundation available; only advertised when valid derived keys exist |

### Pull-based scan results

Firmware that advertises `scan_results_pull` accepts
`SCAN_WIFI`/`WPS_LOCK_SCAN` with `pull_results:true`. The command response then
contains `scan_id`, `count`, `kind`, and (if applicable) `truncated`. The app
retrieves bounded chunks with:

```json
{"cmd":"SCAN_RESULTS","args":{"scan_id":42,"offset":0,"limit":4}}
```

```json
{
  "ok": true,
  "scan_id": 42,
  "kind": "wifi",
  "offset": 0,
  "count": 4,
  "total": 7,
  "next_offset": 4,
  "crc32": 123456789,
  "results": []
}
```

See [commands/wifi.md](./commands/wifi.md#pull-based-scan-result-chunks) for the
canonical CRC input and retry rules. Legacy firmware continues to emit
`scan_ap`/`wps_lock_ap` events when pull mode is not requested.

---

## Reference Index

Detailed command and event references are split by radio category:

- [Command Reference](./commands/README.md)
- [Event Reference](./events/README.md)
- [Version Compatibility](./COMPATIBILITY.md)

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Unknown command | RESPONSE `{ok:false,msg:"unknown command"}` |
| Missing command | RESPONSE `{ok:false,msg:"missing cmd"}` |
| Bad JSON | Frame dropped or RESPONSE `{ok:false,msg:"parse error"}` |
| Payload > 1024 bytes | App rejects before sending; firmware drops/resyncs |
| Unknown frame type | Decoder resynchronizes |
| Invalid length | Decoder skips byte(s) and resyncs |
| No matching command ID | RESPONSE discarded by app |
| Command timeout | App removes pending entry and returns null |

---

## Planned Extensions (future minor versions)

| Addition | Notes |
|---|---|
| FastPair model ID | BLE service-data mapping, app-side |
| Mesh foundation | Draft protocol 1.1. See [commands/mesh.md](./commands/mesh.md) and [events/mesh.md](./events/mesh.md) |
| Peripheral frame type | Reserved `0x07` for sub-GHz/nRF24/RFID data |
| Fragmentation envelope | `frag` / `frag_total` fields for logical messages over 1024 bytes |
