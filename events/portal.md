# Portal Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `portal_client_seen` | `ip`, `mac`, `user_agent`, `request_type`, `timestamp` | Emitted for portal requests. `mac` is best-effort from the SoftAP station table and is `"unknown"` when unavailable. |
| `portal_viewed` | `client_ip` | Portal root page viewed |
| `portal_dns_hijack` | `client_ip`, `destination`, `count`, `free_heap`, `heap_min_free`, `heap_max_alloc` | Rate-limited diagnostic emitted when firmware answers a plaintext custom-resolver DNS query with the portal AP address. `destination` is the resolver IP the client attempted to use; heap fields report current free heap, minimum free heap, and largest allocatable block. |
| `captive_data` | `ip`, `user_agent`, `request_type`, `timestamp`, `data` | Submitted credential/form data from POST `/login`, GET `/login`, or credential-like GET query fields on `/` and `/continue` |
| `client_associated` | `client`, `bssid`, `rssi` | Association monitor event when that optional monitor is active |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
