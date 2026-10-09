# NRSuite Mesh Foundation

Status: implemented through Phase 3B for protocol `1.1`; Phase 3B hardware validation pending
Scope: ESP-NOW mesh membership, authentication, master election, heartbeat, channel management, and encrypted sensor-report transport

This document captures the accepted design constraints before firmware implementation begins.

---

## 1. Membership model

Every node that belongs to the operator's mesh is provisioned with the same passphrase over USB.

- The passphrase is the only membership credential.
- A node with no key, or the wrong key, does not initialise ESP-NOW mesh mode.
- A keyless node still runs its normal standalone NRSuite modules.
- The raw passphrase is never sent over the wire.
- The Android app derives two keys from the passphrase using HKDF-SHA256:
  - `auth_key` - USB identity challenge
  - `transport_key` - ESP-NOW AES-CCM transport
- Only these derived keys are stored in NVS under a dedicated `mesh` namespace.
- `MESH_PROVISION_KEY` provisions derived keys, not the raw passphrase.

Proposed HKDF labels for Phase 1:

```text
salt = "NRSuite Mesh v1"
auth_key = HKDF-SHA256(passphrase, salt, info="nrsuite-mesh-auth", length=32)
transport_key = HKDF-SHA256(passphrase, salt, info="nrsuite-mesh-transport", length=32)
```

A per-mesh random salt can be revisited in a later phase if key lifecycle requirements grow.

---

## 2. NVS layout

Use a dedicated NVS namespace, separate from the existing device ID namespace.

Suggested keys:

```text
mesh_init
mesh_auth_key
mesh_trans_key
mesh_key_id
mesh_node_id
```

> ESP-IDF NVS key names are limited to 15 characters. The names above
> deliberately stay under that limit.

`mesh_node_id` is the persistent device ID:

```text
NR + 8 hex digits = NRxxxxxxxx (10 characters total)
```

The mesh availability flag in `STATUS.features` is advertised only when `mesh_init` is true and both derived keys are present. A separate `mesh_provision` capability flag is advertised whenever the firmware includes mesh support, so the Android app can open the provisioning UI before any keys exist.

---

## 3. USB authentication challenge

The mesh auth handshake runs over USB.

1. App sends a random nonce.
2. Node signs the nonce with `auth_key`.
3. App verifies the signature against the same derived `auth_key`.
4. Failure means standalone mode, no mesh.
5. Success allows master election.

Protocol additions:

```text
MESH_AUTH_CHALLENGE
MESH_AUTH_RESPONSE
```

Suggested challenge payload:

```json
{
  "cmd": "MESH_AUTH_CHALLENGE",
  "args": {
    "nonce": "<base64>"
  }
}
```

Suggested response:

```json
{
  "ok": true,
  "node_id": "NR1A2B3C4D",
  "hmac": "<base64 HMAC-SHA256 over nonce using auth_key>"
}
```

The app verifies the HMAC using its derived `auth_key`.

---

## 4. Master election

There is no fixed master hardware.

A provisioned node becomes master when:

- it is USB-connected to the Android app
- USB authentication succeeds
- no other master session is active on the mesh

If authentication succeeds but another master is already broadcasting, the node joins as a client and locks to the existing session ID.

### Election decision tree

1. App sends nonce challenge.
2. Node signs with `auth_key`.
3. App verifies.
4. If verification fails: standalone, no mesh.
5. If verification passes, USB is connected, and master slot is free:
   - node becomes master
   - node generates a fresh random session ID for this plug-in session
   - node begins broadcasting heartbeat plus session ID over ESP-NOW
6. If verification passes but a master is already active:
   - node joins as client
   - node locks to the existing session ID

### Session ID

- Generated fresh by the master every time it is plugged in.
- Not tied to hardware.
- Broadcast in every heartbeat.
- Clients lock to the first valid session ID they receive.
- If two masters appear, use boot-millis or timestamp tiebreaker.
- Lowest timestamp wins; the earlier-plugged node keeps the master slot.

---

## 5. Transport key

- `transport_key` is derived once from the passphrase and stored in NVS.
- It is static for Phase 1.
- It does not rotate per session.
- It changes only when the user re-provisions the passphrase.
- Per-session key rotation is deferred.

---

## 6. Radio arbitration

Mesh is a radio module and must stop whenever another Wi-Fi module claims the radio.

Examples:

- sniffer
- beacon spam
- captive portal / Evil Twin
- deauth detector
- client detector
- hidden AP detector

Teardown hook:

```text
stopRadioModules()
```

not only

```text
stopAllModules()
```

`STOP_ALL` must also stop mesh, but normal radio-module transitions must use `stopRadioModules()` so mesh cannot keep the radio active while promiscuous mode is claimed.

---

## 7. Crypto implementation

Use mbedTLS AES-CCM:

- already linked in every build through ESP-IDF
- no new `lib_deps`
- works on ESP32-C3, ESP32-S3, ESP32-S2, and classic ESP32

Mesh packet authentication and replay protection should use:

- AES-CCM for confidentiality and integrity
- monotonic counter or nonce
- session ID binding
- optional timestamp window

---

## 8. C3 memory constraint

ESP32-C3 has 400 KB SRAM and runs NimBLE plus existing radio modules.

Before allowing BLE and mesh to run simultaneously on C3:

- profile free heap with mesh active
- profile heap with BLE HID active
- profile heap with BLE scanner active
- test mesh plus BLE under load
- add a build-time or runtime guard if heap headroom is insufficient

If memory is too tight, mesh and BLE may need to be mutually exclusive on C3.

---

## 9. Protocol versioning

`STATUS.proto` remains an integer major version:

```json
{
  "proto": 1,
  "proto_minor": 1
}
```

Do not change `proto` to a semver string.

Add `proto_minor` so the app can distinguish protocol `1.1` mesh builds from older `1.0` builds.

Feature flag:

```text
mesh
```

Only advertise `mesh` when the node has valid derived keys and mesh mode is available.

---

## 10. Phase 1 command/event set

Commands:

```text
MESH_PROVISION_KEY
MESH_CLEAR_KEY
MESH_AUTH_CHALLENGE
MESH_STATUS
MESH_ACTIVATE
MESH_DEACTIVATE
```

No `MESH_SET_ROLE` in Phase 1. Role is determined by election.

Events:

```text
mesh_status
mesh_heartbeat
mesh_node_joined
mesh_node_left
mesh_activation_result
mesh_error
```

Later phases:

```text
mesh_chat
mesh_route
```

Phase 3A adds the current USB-visible event:

```text
mesh_sensor_report
```

with `kind = "node_health"` and generic `data_b64` support for unknown
report kinds. Phase 3B extends the same event with `kind = "deauth"`.

### 10.1 Internal detector control packet (Phase 3B)

`PKT_DETECTOR_CONTROL = 6` is an encrypted ESP-NOW packet between mesh
members. It is not exposed over USB; Android still uses
`DEAUTH_DETECT_START` / `DEAUTH_DETECT_STOP` with a distributed/mesh flag.

Payload:

```text
byte 0      start (1) / stop (0)
byte 1      mode: 0 = same_channel, 1 = fixed, 2 = hop
byte 2      detector channel
byte 3..4   mesh window ms (little-endian u16)
byte 5..6   detector window ms (little-endian u16)
byte 7..8   detector hop dwell ms (little-endian u16)
```

Security and delivery rules:

- encrypted with the mesh transport key (same `PKT_*` AES-CCM envelope)
- accepted only when the sender role is `ROLE_MASTER`
- `sessionId == _sessionId`; stale sessions are ignored
- start/stop controls are retried a small number of times because clients may
  be temporarily off-channel in a detector window

Deauth observations are sent as `PKT_SENSOR_REPORT` with
`kind = 2 (deauth)`. Each observation has a stable `seq` assigned when queued;
retries reuse it so the Android app can deduplicate by `(node_id, seq)`.

### 10.2 Channel switch ACK handshake (Phase 3B)

`PKT_CHANNEL_SWITCH` now carries a small payload:

```text
byte 0      phase: 1 = request, 2 = commit
byte 1      target channel
byte 2..5   switch_id (little-endian u32)
```

`PKT_CHANNEL_SWITCH_ACK = 7` is sent by clients:

```text
byte 0      target channel
byte 1..4   switch_id (little-endian u32)
```

Master flow:

1. broadcast `request`
2. collect encrypted ACKs from online clients
3. when all online clients ACK, or after the ACK timeout, broadcast `commit`
4. switch to the target channel after a short commit delay
5. emit `mesh_channel_switch` USB events with `acked` and `pending` node lists

Client flow:

1. reply ACK to `request`
2. wait for `commit`
3. switch to the target channel without persisting it yet
4. stay on the target channel for 60 seconds, retrying join/reports
5. if a master heartbeat arrives, persist the channel through normal adoption
6. if no master arrives within 60 seconds, resume recovery hopping

Implementation note: a heartbeat arriving on the old channel during the commit
delay must not cancel a pending switch. The client preserves pending switch
state until the commit delay expires. This was hardware-validated on
ESP32-S3 + ESP32-S2.


### 10.3 Join ACK handshake (Phase 3B hardening)

`PKT_JOIN_ACK = 8` is an internal encrypted ESP-NOW packet. It confirms that
the master accepted a client's `PKT_JOIN` and that the client exists in the
master peer table.

Payload:

```text
byte 0      master channel
byte 1..4   target client node hash (little-endian u32)
```

Master flow:

1. receive and authenticate `PKT_JOIN`
2. add/update the client in the peer table
3. send `PKT_JOIN_ACK` addressed to that client

Client flow:

1. hear an authenticated master heartbeat
2. switch to that master channel as a candidate
3. send `PKT_JOIN` every 2 seconds
4. wait for a matching `PKT_JOIN_ACK`
5. only then persist the channel and enter fully joined/online state
6. if no ACK arrives within 6 seconds, return to idle and resume channel
   recovery hopping

This prevents a client from marking a master online and locking to its channel
when the master has not actually accepted the client.

---

## 11. Testing requirements

- Unit-test HKDF key derivation, HMAC verification, replay rejection, and packet auth.
- Two-board test:
  - provision both nodes
  - authenticate both
  - activate one as master
  - confirm the second self-demotes to client
- Disconnect/reconnect master test:
  - master session ID changes
  - clients re-lock to the new session
- Wrong-key test:
  - node remains standalone and never sends ESP-NOW mesh traffic
- Radio conflict test:
  - starting sniffer/beacon/portal stops mesh cleanly
- `STOP_ALL` test:
  - mesh stops and NVS keys remain intact
- C3 memory test:
  - mesh + BLE heap profile
