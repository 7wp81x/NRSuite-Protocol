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
| `kind` | string | `node_health` for Phase 3A; unknown kinds use `data_b64` |
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
