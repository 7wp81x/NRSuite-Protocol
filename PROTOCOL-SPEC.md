# NRSuite Wire Protocol Specification

**Version: 1.0**
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
  "chip": "ESP32-S3",
  "proto": 1,
  "fw": "1.0.0-beta.2",
  "device_id": "NR1A2B3C4D",
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
| `chip` | string | `ESP32`, `ESP32-S2`, `ESP32-S3`, or `ESP32-C3` |
| `proto` | int | Protocol major version. Currently `1` |
| `fw` | string | Firmware version |
| `device_id` | string | Persistent `NRxxxxxxx` ID from NVS |
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
| `deauth_detect` | Deauth detector |
| `beacon` | Beacon spam |
| `portal` | Captive portal / Evil Twin AP |
| `portal_html_offset` | HTML chunks support offset-based upload |
| `html_diag` | HTML upload diagnostic events |
| `stop_all` | `STOP_ALL` command |
| `wps` | WPS flag included in `scan_ap` |
| `hidden_ap` | Hidden AP revealer |
| `storage` | Mass storage/file operations |
| `ble_hid` | BLE HID |
| `ble_scan` | BLE scanner |
| `ble_profile` | Read-only BLE GATT profiler |
| `msc` | USB MSC mode |
| `msc_read_chunk` | Chunked `MSC_READ` |
| `badusb` | Native USB HID BadUSB |

---

## Command Reference

### System

| Command | Args | Response | Notes |
|---|---|---|---|
| `PING` | none | `{ok:true,msg:"pong"}` | Liveness check |
| `STATUS` | none | See STATUS Response | Device/feature handshake |
| `HEAP` | none | Same as `STATUS` | Alias |
| `STOP_ALL` | none | `{ok:true}` | Stops all radio/BLE/upload modules |
| `SET_CHANNEL` | `{channel:1..13}` | `{ok:true}` | Changes sniffer channel |

### Wi-Fi recon

| Command | Args | Response | Events |
|---|---|---|---|
| `SCAN_WIFI` | none | `{ok:true,count:N}` | `scan_ap` per network |
| `START_SNIFF` | `{mode:"fixed"|"hop",channel,interval_ms,eapol_only,bssid}` | `{ok:true}` | `PCAP` frames |
| `STOP_SNIFF` | none | `{ok:true,captured,sent,dropped}` | |
| `START_CLIENT_DETECT` | `{mode:"fixed"|"hop",channel,interval_ms}` | `{ok:true}` | `client_detected` |
| `STOP_CLIENT_DETECT` | none | `{ok:true,captured,sent,dropped}` | |
| `START_HIDDEN_AP` | `{mode:"fixed"|"hop",channel,interval_ms}` | `{ok:true}` | `hidden_ap`, `hidden_ssid_candidate`, `hidden_ssid_resolved`, `hidden_ap_hop` |
| `STOP_HIDDEN_AP` | none | `{ok:true,hidden,candidates,resolved,sent,dropped}` | |
| `HIDDEN_AP_FORCE_RECONNECT` | `{bssid,client,channel,count,interval_ms,reason}` | `{ok:true}` | Requires hidden AP detector active |

### Wi-Fi attack / portal

| Command | Args | Response | Events |
|---|---|---|---|
| `DEAUTH` | `{bssid,client,channel,count,reason,deauth_interval_ms}` | `{ok:true}` | `deauth_stats` |
| `DEAUTH_CAPTURE` | Same as `DEAUTH` | `{ok:true}` | `deauth_stats`, then starts EAPOL capture |
| `START_BEACON` | `{ssids:"SSID1\nSSID2",channel,interval_ms,random_bssid,hidden}` | `{ok:true,ssids,channel}` | |
| `STOP_BEACON` | none | `{ok:true,sent,ssids}` | |
| `BEACON_STATUS` | none | `{ok:true,active,ssids,sent,channel}` | |
| `START_PORTAL` | `{ssid,channel,bssid}` | `{ok:true}` | `portal_viewed`, `captive_data`, `client_associated` |
| `STOP_PORTAL` | none | `{ok:true}` | |
| `RESET_HTML` | `{size}` | `{ok:true}` | `debug` events |
| `SET_HTML_CHUNK` | `{data:"<base64>",last:bool,offset?:number}` | `{ok:true}` | `debug` events |
| `PORTAL_STATUS` | none | `{ok:true,running,html_size,html_expected,html_complete}` | |

### Defense

| Command | Args | Response | Events |
|---|---|---|---|
| `DEAUTH_DETECT_START` | `{mode:"fixed"|"hop",hop,channel,interval_ms,bssid,client,rssi_min}` | `{ok:true,channel,hopping}` | `deauth_detected`, `deauth_detector_hop` |
| `DEAUTH_DETECT_STOP` | none | `{ok:true,detected,sent,dropped}` | |
| `DEAUTH_DETECT_STATUS` | none | `{ok:true,active,hopping,channel,detected,sent,dropped}` | |

### BLE

| Command | Args | Response | Events |
|---|---|---|---|
| `BLE_SCAN_START` | `{active,interval_ms,window_ms,min_emit_ms}` | `{ok:true}` | `ble_device` |
| `BLE_SCAN_STOP` | none | `{ok:true}` | |
| `BLE_PROFILE_START` | `{address,address_type}` | `{ok:true}` | `ble_profile`, `ble_service`, `ble_characteristic` |
| `BLE_PROFILE_STOP` | none | `{ok:true}` | `ble_profile` |
| `BLE_START` | `{name}` | `{ok:true}` | |
| `BLE_STATUS` | none | `{ok:true,connected,advertising,peer}` | |
| `BLE_STOP` | none | `{ok:true}` | |
| `BLE_RUN_SCRIPT` | `{script}` | `{ok:true,lines}` | |
| `BLE_STOP_SCRIPT` | none | `{ok:true}` | |
| `BLE_KEY_DOWN` | `{key}` | `{ok:true}` | |
| `BLE_KEY_UP` | `{key}` | `{ok:true}` | |
| `BLE_KEY_TAP` | `{key}` | `{ok:true}` | |
| `BLE_TYPE_TEXT` | `{text}` | `{ok:true}` | |
| `BLE_MOUSE_MOVE` | `{dx,dy}` | `{ok:true}` | |
| `BLE_MOUSE_SCROLL` | `{wheel}` | `{ok:true}` | |
| `BLE_MOUSE_BUTTON` | `{button,down}` | `{ok:true}` | |
| `BLE_MOUSE_RELEASE` | none | `{ok:true}` | |
| `BLE_RELEASE_ALL` | none | `{ok:true}` | |

### Storage / BadUSB

| Command | Args | Response | Notes |
|---|---|---|---|
| `START_MSC` | none | `{ok:true}` | Reboots into USB MSC mode on S2/S3 |
| `MSC_LIST` | none | `{ok:true,files:[{name,size}],total,used,free}` | File list |
| `MSC_READ` | `{path,offset?,length?}` | `{ok:true,path,content,size,offset,total,eof}` | Chunked reads max 768 bytes |
| `MSC_WRITE` | `{path,content,append}` | `{ok:true}` | Writes/appends text |
| `MSC_DELETE` | `{path}` | `{ok:true}` | Deletes a file |
| `MSC_SPACE` | none | `{ok:true,total,used,free}` | Free-space query |
| `MSC_SETUP` | none | `{ok:true}` | Enters MSC mode directly |
| `SET_FILE_CHUNK` | `{filename,data:"<base64>",last}` | `{ok:true}` | Chunked file upload for DuckyScripts |
| `START_BADUSB` | `{filename,msc}` | `{ok:true}` | Arms native USB HID payload |

---

## Event Reference

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `heartbeat` | `uptime`, `heap` | Every 5 seconds |
| `scan_ap` | `ssid`, `bssid`, `channel`, `rssi`, `security`, `wps` | Emitted by `SCAN_WIFI` |
| `deauth_stats` | `status`, `bssid`, `client`, `channel`, `count`, `interval_ms`, `reason`, `sent_frames` | After `DEAUTH` |
| `client_detected` | `client`, `bssid?`, `ssid?`, `subtype`, `rssi`, `channel` | Client detector |
| `client_associated` | `client`, `bssid`, `rssi` | Portal association monitor |
| `deauth_detected` | `subtype`, `subtype_code`, `bssid`, `source`, `client`, `destination`, `channel`, `rssi`, `reason`, `uptime_ms`, `ssid?` | Deauth/disassoc alert |
| `deauth_detector_hop` | `channel` | Deauth detector channel hop |
| `hidden_ap` | `bssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Hidden AP observed |
| `hidden_ssid_candidate` | `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Probe-request candidate |
| `hidden_ssid_resolved` | `bssid`, `client`, `ssid`, `channel`, `rssi`, `uptime_ms`, `subtype?` | Association-based resolution |
| `hidden_ap_hop` | `channel` | Hidden AP channel hop |
| `portal_viewed` | `client_ip` | Portal root page viewed |
| `captive_data` | `ip`, `user_agent`, `timestamp`, `data` | Posted credential/form data |
| `debug` | varies | HTML reset/chunk/upload diagnostics |
| `ble_device` | `address`, `address_type`, `rssi`, `connectable`, `tx_power`, `appearance`, `uptime_ms`, `name?`, `manufacturer_data?`, `raw_payload?`, `services?` | BLE scanner |
| `ble_profile` | `address`, `status` | `connecting`, `connected`, `done`, or `failed` |
| `ble_service` | `service_uuid` | GATT service |
| `ble_characteristic` | `service_uuid`, `uuid`, `properties` | `properties` has `read`, `write`, `write_no_response`, `notify`, `indicate`, `broadcast` |

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
| Mesh commands | ESP-NOW mesh activation/status, USB-serial control on master |
| Peripheral frame type | Reserved `0x07` for sub-GHz/nRF24/RFID data |
| Fragmentation envelope | `frag` / `frag_total` fields for logical messages over 1024 bytes |
