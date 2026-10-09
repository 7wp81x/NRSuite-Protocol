# Mesh Events

Status: draft for protocol `1.1`

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `mesh_status` | `initialized`, `role`, `session_id?`, `node_id`, `peer_count` | Mesh state changed |
| `mesh_heartbeat` | `node_id`, `chip?`, `role`, `session_id`, `channel`, `uptime_ms`, `seq` | Master heartbeat forwarded over USB |
| `mesh_node_joined` | `node_id`, `chip?`, `session_id`, `channel`, `rssi?` | A client joined the active session |
| `mesh_node_left` | `node_id`, `session_id`, `reason?` | A client timed out or left |
| `mesh_activation_result` | `role`, `session_id?`, `ok`, `reason?` | Result of `MESH_ACTIVATE` |
| `mesh_sensor_report` | `node_id`, `chip?`, `role`, `session_id?`, `kind`, `seq`, `channel`, `rssi?`, plus report-specific fields | Master-forwarded encrypted sensor report |
| `mesh_channel_switch` | `phase`, `channel`, `switch_id`, `acked`, `pending`, `acked_count`, `pending_count`, `reason?` | Master-side channel switch request/ACK/commit status |
| `mesh_error` | `code`, `msg` | Mesh runtime or auth error |

## `mesh_sensor_report`

Phase 3A defines the generic report event and the first report kind,
`node_health`.

Common fields:

| Field | Type | Notes |
|---|---|---|
| `node_id` | string | Reporting node ID |
| `chip` | string? | Peer chip label if known |
| `role` | string | `master` or `client` |
| `session_id` | number? | Mesh session that received the report |
| `kind` | string | `node_health` (Phase 3A), `deauth` (Phase 3B); unknown kinds use `data_b64` |
| `seq` | number | Report sequence |
| `channel` | number | Channel reported by the node |
| `rssi` | number? | Master's receive RSSI for the report |

`node_health` fields:

| Field | Type | Notes |
|---|---|---|
| `uptime_ms` | number | Node uptime |
| `heap` | number | Free heap bytes |
| `role` | string | `master` or `client` |
| `channel` | number | Current mesh channel |

`deauth` fields (Phase 3B):

| Field | Type | Notes |
|---|---|---|
| `reason` | number | Deauth/disassoc reason code |
| `channel` | number | Channel where the frame was observed |
| `rssi` | number | RSSI observed by the reporting node |
| `source` | string | Source/BSSID address |
| `target` | string | Target/client address; `FF:FF:FF:FF:FF:FF` for broadcast |
| `seq` | number | Stable per-observation ID; retries reuse it for dedupe |

Phase 3B also adds the encrypted internal ESP-NOW packets
`PKT_DETECTOR_CONTROL = 6` for master-to-client start/stop control and
`PKT_JOIN_ACK = 8` for JOIN acceptance. They are not USB events and are
documented in [MESH-FOUNDATION.md](../MESH-FOUNDATION.md).

## `mesh_channel_switch`

Phase 3B adds an ACK-based channel switch handshake:

- master sends `request`
- clients reply with an encrypted ACK
- master sends `commit` after all online clients ACK or after the ACK timeout
- clients move to the target channel and hold there for 60 seconds
- if no master is seen during the hold, the client resumes recovery hopping

Fields:

| Field | Type | Notes |
|---|---|---|
| `phase` | string | `request`, `ack`, `commit`, or `committed` |
| `channel` | number | Target channel |
| `switch_id` | number | Random switch operation ID |
| `acked` | array[string] | Client node IDs that ACKed |
| `pending` | array[string] | Online clients that have not ACKed yet |
| `acked_count` | number | `acked.length` |
| `pending_count` | number | `pending.length` |
| `reason` | string? | `all_acked`, `ack_timeout`, or other detail |

`PKT_CHANNEL_SWITCH_ACK = 7` is an internal encrypted ESP-NOW packet and is
not exposed directly as a USB event.

Unknown report kinds carry:

| Field | Type | Notes |
|---|---|---|
| `data_b64` | string? | Base64 report payload |
| `data_len` | number? | Raw payload length |

Future Phase 3+ events:

| Event type | Notes |
|---|---|
| `mesh_chat` | Chat message payload |
| `mesh_route` | Multi-hop route update |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
