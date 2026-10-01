# System Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `heartbeat` | `uptime`, `heap` | Every 5 seconds |
| `debug` | varies | HTML reset/chunk/upload diagnostics |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
