# Defense Commands

## Defense


| Command | Args | Response | Events |
|---|---|---|---|
| `DEAUTH_DETECT_START` | `{mode:"fixed"|"hop",hop,channel,interval_ms,bssid,client,rssi_min,mesh?,mesh_window_ms?,detector_window_ms?,detector_hop_dwell_ms?,hop_mask?}` | `{ok:true,channel,hopping,distributed?,mode?,mesh_window_ms?,detector_window_ms?,master_scanning?}` | `deauth_detected`, `deauth_detector_hop` |
| `DEAUTH_DETECT_STOP` | none | `{ok:true,detected,sent,dropped}` | |
| `DEAUTH_DETECT_STATUS` | none | `{ok:true,active,hopping,channel,detected,sent,dropped}` | |

> Distributed/mesh mode carries `bssid`, `client`, and `rssi_min` through
> `PKT_DETECTOR_CONTROL` so clients can filter matching deauth observations.
> Distributed HOP remains disabled. The selected target channel is applied as
> the mesh channel before monitoring starts.

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
