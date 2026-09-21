# NRSuite Wire Protocol Specification

**Version: 1.0**
**Status: Stable (beta)**

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

The transport layer is byte-stream only. The protocol is responsible for its own framing and resynchronization -- there are no transport-level message boundaries.

---

## Frame Format

Every message between app and firmware is a frame with an 8-byte fixed header followed by a variable-length payload.

```
Offset  Size    Field
------  ----    -----
0       1       Magic byte 0 (0xAD)
1       1       Magic byte 1 (0xDE)
2       1       Frame type (see Frame Types)
3       1       Frame ID (0x01..0xFF, wraps at 0xFF back to 0x01)
4       4       Payload length in bytes, little-endian uint32
8       N       Payload (0..1024 bytes)
```

### Constants

| Name | Value |
|---|---|
| `MAGIC_0` | `0xAD` |
| `MAGIC_1` | `0xDE` |
| `HEADER_SIZE` | 8 bytes |
| `MAX_PAYLOAD_SIZE` | 1024 bytes |

### Frame ID

- Allocated by the sender (app or firmware) per message, starting at `0x01` and wrapping back to `0x01` after `0xFF`.
- Used to correlate COMMAND frames with their RESPONSE frames -- a RESPONSE carries the same ID as the COMMAND it answers.
- ID `0x00` is reserved for frames that do not require correlation (currently: ACK responses from the app to the firmware after a PCAP frame).

### Resynchronization

The decoder scans incoming bytes for the `0xAD 0xDE` magic sequence. If a byte sequence fails to parse as a valid frame (unknown type code, payload length exceeding `MAX_PAYLOAD_SIZE`, truncated data), the decoder discards one byte and resynchronizes by scanning forward for the next magic sequence. This allows recovery from transient corruption on the serial line without dropping the session.

---

## Frame Types

| Name | Code | Direction | Description |
|---|---|---|---|
| `COMMAND` | `0x01` | App -> Firmware | Carry a JSON command with optional arguments |
| `RESPONSE` | `0x02` | Firmware -> App | Reply to a specific COMMAND, same frame ID |
| `EVENT` | `0x03` | Firmware -> App | Async notification not tied to a specific command |
| `PCAP` | `0x04` | Firmware -> App | Raw pcap data chunk |
| `ACK` | `0x05` | App -> Firmware | Acknowledge receipt of a PCAP chunk |
| `HTML` | `0x06` | App -> Firmware | Upload HTML content to the firmware (e.g. captive portal page) |

---

## Session Lifecycle

```
App                                    Firmware
 |                                         |
 |-- COMMAND (id=1, cmd="PING") ---------> |
 |<- RESPONSE (id=1, {ok:true}) ---------- |
 |                                         |
 |-- COMMAND (id=2, cmd="STATUS") -------> |
 |<- RESPONSE (id=2, {chip, fw, features}) |
 |                                         |
 |   [ session now active ]                |
 |                                         |
 |-- COMMAND (id=3, cmd="...") ----------> |
 |<- RESPONSE (id=3, {...})  ------------- |
 |                                         |
 |<- EVENT ({event:"...", ...}) ---------- |  (async, any time)
 |                                         |
 |<- PCAP (id=N, raw bytes) -------------- |  (streaming during sniff)
 |-- ACK (id=0, {chunk:N}) ----------->   |
 |                                         |
```

### Connection establishment

1. App opens the USB serial port and starts the frame read loop.
2. App sends `PING` (timeout: 3 seconds). If no valid response, connection fails.
3. App sends `STATUS` (timeout: 5 seconds) to retrieve chip info, firmware version, and the feature set the firmware was compiled with.
4. Connection is considered established after a successful `STATUS` response.

### Disconnection

Either side may close the USB serial port at any time. A read/write error on the app side is treated as a clean disconnect (USB unplug) rather than a session error.

### Command timeout

Default command timeout is **8 seconds**. Some long-running commands (Wi-Fi scan, WPA crack) use extended timeouts specified per-command. If a RESPONSE is not received within the timeout, the pending correlation entry is removed and `null` is returned to the caller.

### Fire-and-forget commands

Latency-sensitive commands (e.g. HID key injection for BadUSB) may be sent without waiting for a RESPONSE using the `sendCommandNoWait` path. The firmware still sends a RESPONSE; the app simply does not block on it.

---

## JSON Payload Schema

All COMMAND, RESPONSE, EVENT, and ACK payloads are UTF-8 encoded JSON objects. PCAP and HTML payloads are raw bytes (not JSON).

### COMMAND frames

```json
{
  "cmd": "COMMAND_NAME",
  "args": {
    // command-specific arguments, may be empty object
  }
}
```

### RESPONSE frames

Every response includes at minimum:

```json
{
  "ok": true | false
}
```

Additional fields are command-specific (see Command Reference). On failure, a `"msg"` string field with a human-readable error description may be present:

```json
{
  "ok": false,
  "msg": "target not found"
}
```

### EVENT frames

Async notifications from firmware to app. Always include an `"event"` string identifying the event type:

```json
{
  "event": "EVENT_NAME",
  // event-specific fields
}
```

### PCAP frames

Raw binary pcap data (no JSON wrapper). The payload is a chunk of a standard pcap file (global header included in the first chunk only). The app reassembles chunks in received order and writes them to a `.pcap` file.

The firmware uses a small sliding window for flow control. The app sends an ACK after accepting each chunk.

### ACK frames

Sent by the app to the firmware after accepting a PCAP chunk. Frame ID is always `0x00`. Payload:

```json
{
  "chunk": <frame_id_of_the_pcap_frame_being_acknowledged>
}
```

### HTML frames

Raw UTF-8 HTML content, no JSON wrapper. Used to upload a custom captive portal page to the firmware. No ACK is required; the firmware sends a RESPONSE frame (type `0x02`) with `{"ok": true}` once the upload is complete.

---

## Command Reference

### PING

Liveness check. Sent as the first command after opening the serial port.

**Request args:** (none)

**Response:**
```json
{ "ok": true }
```

---

### STATUS

Retrieve device info and firmware feature set.

**Request args:** (none)

**Response:**
```json
{
  "ok": true,
  "chip": "ESP32",
  "fw": "1.0.0-beta",
  "features": ["wifi", "ble", "sniff", "deauth", "beacon", "evil_twin", "portal", "badusby", "wpa"]
}
```

| Field | Type | Description |
|---|---|---|
| `chip` | string | ESP32 chip model reported by firmware |
| `fw` | string | Firmware version string |
| `features` | string array | Feature flags indicating which modules are compiled in |

---

### SCAN_WIFI

Start a passive Wi-Fi scan. The firmware scans all channels and returns the count of discovered networks. Individual network details are delivered as `EVENT` frames with `"event": "ap"` during the scan.

**Request args:** (none)

**Response:**
```json
{
  "ok": true,
  "count": 12
}
```

**Events emitted during scan:**
```json
{
  "event": "ap",
  "ssid": "NetworkName",
  "bssid": "AA:BB:CC:DD:EE:FF",
  "channel": 6,
  "rssi": -65,
  "security": "WPA2"
}
```

---

### START_SNIFF

Start monitor-mode packet capture on the specified channel(s). Raw pcap data is delivered as a stream of `PCAP` frames.

**Request args:**

```json
{
  "fixed": true | false,
  "channel": 6,
  "interval_ms": 200,
  "deauth_before": false,
  "target_bssid": "AA:BB:CC:DD:EE:FF",
  "client": "FF:FF:FF:FF:FF:FF",
  "deauth_count": 0,
  "deauth_interval_ms": 80,
  "eapol_only": false,
  "target_only": false
}
```

| Field | Type | Description |
|---|---|---|
| `fixed` | bool | If true, stay on the specified channel; if false, hop channels using `interval_ms` |
| `channel` | int | Starting channel (1..13) |
| `interval_ms` | int | Channel hop interval in ms (ignored if `fixed` is true) |
| `deauth_before` | bool | Send deauth frames before capture to force handshake renegotiation |
| `target_bssid` | string | BSSID of the target AP (broadcast `FF:FF:FF:FF:FF:FF` to capture all) |
| `client` | string | Client MAC for targeted deauth; broadcast to deauth all clients |
| `deauth_count` | int | Number of deauth frames to send if `deauth_before` is true |
| `deauth_interval_ms` | int | Interval between deauth bursts in ms |
| `eapol_only` | bool | If true, only forward EAPOL frames (reduces pcap volume for WPA capture) |
| `target_only` | bool | If true, only capture frames involving `target_bssid` |

**Response:**
```json
{ "ok": true }
```

---

### STOP_SNIFF

Stop an active packet capture.

**Request args:** (none)

**Response:**
```json
{ "ok": true }
```

---

### DEAUTH

Send deauthentication frames.

**Request args:**

```json
{
  "bssid": "AA:BB:CC:DD:EE:FF",
  "client": "FF:FF:FF:FF:FF:FF",
  "count": 10,
  "interval_ms": 80
}
```

| Field | Type | Description |
|---|---|---|
| `bssid` | string | Target AP BSSID |
| `client` | string | Target client MAC; `FF:FF:FF:FF:FF:FF` for broadcast deauth |
| `count` | int | Number of deauth frames to send |
| `interval_ms` | int | Interval between frames in ms |

**Response:**
```json
{ "ok": true }
```

---

### START_BEACON

Start broadcasting fake beacon frames.

**Request args:**

```json
{
  "ssids": ["FakeAP1", "FakeAP2"],
  "channel": 6,
  "interval_ms": 100
}
```

**Response:**
```json
{ "ok": true }
```

---

### STOP_BEACON

Stop beacon broadcasting.

**Request args:** (none)

**Response:**
```json
{ "ok": true }
```

---

### BEACON_STATUS

Query whether beacon broadcast is currently active.

**Request args:** (none)

**Response:**
```json
{
  "ok": true,
  "running": true | false
}
```

---

### PORTAL_STATUS

Query whether the captive portal is currently active.

**Request args:** (none)

**Response:**
```json
{
  "ok": true,
  "running": true | false
}
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Unknown command string | Firmware responds `{"ok": false, "msg": "unknown command"}` |
| Malformed JSON payload | Firmware responds `{"ok": false, "msg": "parse error"}` or drops the frame |
| Payload exceeds 1024 bytes | App rejects before sending; firmware drops if received |
| Unknown frame type code | Decoder skips and resyncs |
| Invalid payload length (negative or > 1024) | Decoder skips one byte and resyncs |
| RESPONSE received with no matching pending command ID | Silently discarded by the app |
| Command timeout | App removes pending correlation entry, returns null to caller |

---

## Planned Extensions (v1.1+)

The following additions are planned for future minor versions. They are additive and will not break v1.0 implementations.

| Addition | Notes |
|---|---|
| `SCAN_BLE` command | BLE device scan, similar pattern to `SCAN_WIFI` with EVENT delivery |
| `START_EVIL_TWIN` / `STOP_EVIL_TWIN` | Evil twin AP control with portal integration |
| Defense module commands | `START_DEAUTH_DETECT`, `START_ROGUE_AP_DETECT`, `START_TRACKER_DETECT` |
| Mesh control commands | `MESH_ACTIVATE`, `MESH_HEARTBEAT`, `MESH_STATUS` -- carried over USB serial on the master node only; inter-node traffic travels over ESP-NOW separately |
| `PERIPHERAL` frame type | Reserved type code `0x07` for future sub-GHz/nRF24/RFID peripheral data that does not fit the JSON/pcap model |
| Fragmentation header | For payloads approaching 1024 bytes, a `frag`/`frag_total` field in the JSON envelope to allow logical messages larger than one frame |
