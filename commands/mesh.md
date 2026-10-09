# Mesh Commands

Status: draft for protocol `1.1`

The core transport and framing are defined in [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md).

Mesh membership uses a shared passphrase provisioned over USB. The raw passphrase is never sent to the firmware. The Android app derives two keys with HKDF-SHA256 and provisions only the derived keys.

- `auth_key` - USB identity challenge
- `transport_key` - AES-CCM ESP-NOW transport

Derived keys are stored in NVS under a dedicated `mesh` namespace.

## Commands

| Command | Args | Response | Notes |
|---|---|---|---|
| `MESH_PROVISION_KEY` | `{auth_key:"<base64>",transport_key:"<base64>",key_id?,channel?}` | `{ok:true}` | Provisions derived keys and optional mesh channel (1-13); never sends the raw passphrase |
| `MESH_CLEAR_KEY` | none | `{ok:true}` | Removes mesh keys and disables mesh |
| `MESH_AUTH_CHALLENGE` | `{nonce:"<base64>"}` | `MESH_AUTH_RESPONSE`: `{ok:true,node_id,hmac:"<base64>"}` | Node HMACs the nonce with `auth_key`; app verifies |
| `MESH_STATUS` | none | `{ok:true,initialized,role,session_id,node_id,channel,radio_channel,scan_channel,join_ack_received,join_wait_ms,last_master_seen_ms,peer_count,peers?}` | Current mesh state. `channel` is the logical/adopted channel; `radio_channel` is read back from `esp_wifi_get_channel()`. `peers` is an optional authoritative snapshot with `node_id`, `chip?`, `role`, `session_id`, `online`, `rssi`, and `last_seen_ms` |
| `MESH_SET_CHANNEL` | `{channel:1..13}` | `{ok:true}` | Master starts the ACK/commit switch handshake and persists the target before the request is sent. The app must wait for `mesh_channel_switch phase="committed"` before treating the channel as applied. Stop/deactivate reloads the persisted target, so a same-boot restart preserves it even if the switch did not finish. Non-master nodes persist the channel for the next activation instead of leaving the current master |
| `MESH_ACTIVATE` | none | `{ok:true}` | Requests mesh start after successful USB auth |
| `MESH_DEACTIVATE` | none | `{ok:true}` | Stops mesh but keeps stored keys |

`MESH_SET_ROLE` is intentionally not part of Phase 1. Master/client role is determined by the election rules in [MESH-FOUNDATION.md](../MESH-FOUNDATION.md).

## Provisioning sequence

```text
App:
  1. Take operator passphrase.
  2. Derive auth_key and transport_key with HKDF-SHA256.
  3. Generate a key_id for UI/display if desired.

USB:
  4. Send MESH_PROVISION_KEY with derived keys only.

Firmware:
  5. Store derived keys in NVS mesh namespace.
  6. Advertise mesh_provision in STATUS.features whenever mesh support is compiled in.
  7. Advertise mesh in STATUS.features only when both derived keys are valid.
```

## Authentication sequence

```text
App -> MESH_AUTH_CHALLENGE {nonce}
Firmware -> RESPONSE {ok:true,node_id,hmac}
App verifies HMAC with auth_key
```

If verification fails, the node remains standalone and mesh mode is not enabled.

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
