# NRSuite Mesh Foundation

Status: design draft for protocol `1.1`
Scope: Phase 1 ESP-NOW mesh membership, authentication, master election, and heartbeat

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
mesh_initialized
mesh_auth_key
mesh_transport_key
mesh_key_id
mesh_node_id
```

`mesh_node_id` is the persistent device ID:

```text
NR + 8 hex digits = NRxxxxxxxx (10 characters total)
```

The mesh feature flag in `STATUS.features` is advertised only when `mesh_initialized` is true and both derived keys are present.

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
mesh_sensor_report
mesh_chat
mesh_route
```

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
