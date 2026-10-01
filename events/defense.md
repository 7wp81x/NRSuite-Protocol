# Defense Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `deauth_detected` | `subtype`, `subtype_code`, `bssid`, `source`, `client`, `destination`, `channel`, `rssi`, `reason`, `uptime_ms`, `ssid?` | Deauth/disassoc alert |
| `deauth_detector_hop` | `channel` | Deauth detector channel hop |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
