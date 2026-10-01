# Defense Commands

## Defense


| Command | Args | Response | Events |
|---|---|---|---|
| `DEAUTH_DETECT_START` | `{mode:"fixed"|"hop",hop,channel,interval_ms,bssid,client,rssi_min}` | `{ok:true,channel,hopping}` | `deauth_detected`, `deauth_detector_hop` |
| `DEAUTH_DETECT_STOP` | none | `{ok:true,detected,sent,dropped}` | |
| `DEAUTH_DETECT_STATUS` | none | `{ok:true,active,hopping,channel,detected,sent,dropped}` | |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
