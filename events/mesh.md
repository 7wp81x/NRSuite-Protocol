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
| `mesh_error` | `code`, `msg` | Mesh runtime or auth error |

Future Phase 3 events:

| Event type | Notes |
|---|---|
| `mesh_sensor_report` | Distributed detector report |
| `mesh_chat` | Chat message payload |
| `mesh_route` | Multi-hop route update |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
