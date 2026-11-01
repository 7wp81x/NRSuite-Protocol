# Portal Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `portal_client_seen` | `ip`, `mac`, `user_agent`, `request_type`, `timestamp` | Emitted for portal requests. `mac` is best-effort from the SoftAP station table and is `"unknown"` when unavailable. |
| `portal_viewed` | `client_ip` | Portal root page viewed |
| `captive_data` | `ip`, `user_agent`, `request_type`, `timestamp`, `data` | Submitted credential/form data from POST `/login`, GET `/login`, or credential-like GET query fields on `/` and `/continue` |
| `client_associated` | `client`, `bssid`, `rssi` | Association monitor event when that optional monitor is active |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
