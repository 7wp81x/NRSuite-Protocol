# Portal Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `portal_viewed` | `client_ip` | Portal root page viewed |
| `captive_data` | `ip`, `user_agent`, `timestamp`, `data` | Posted credential/form data |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
