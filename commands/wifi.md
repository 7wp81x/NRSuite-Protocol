# Wi-Fi Commands

## Wi-Fi Recon


| Command | Args | Response | Events |
|---|---|---|---|
| `SCAN_WIFI` | none | `{ok:true,count:N}` | `scan_ap` per network |
| `START_SNIFF` | `{mode:"fixed"|"hop",channel,interval_ms,eapol_only,bssid}` | `{ok:true}` | `PCAP` frames |
| `STOP_SNIFF` | none | `{ok:true,captured,sent,dropped}` | |
| `START_CLIENT_DETECT` | `{mode:"fixed"|"hop",channel,interval_ms}` | `{ok:true}` | `client_detected` |
| `STOP_CLIENT_DETECT` | none | `{ok:true,captured,sent,dropped}` | |
| `START_HIDDEN_AP` | `{mode:"fixed"|"hop",channel,interval_ms}` | `{ok:true}` | `hidden_ap`, `hidden_ssid_candidate`, `hidden_ssid_resolved`, `hidden_ap_hop` |
| `STOP_HIDDEN_AP` | none | `{ok:true,hidden,candidates,resolved,sent,dropped}` | |
| `HIDDEN_AP_FORCE_RECONNECT` | `{bssid,client,channel,count,interval_ms,reason}` | `{ok:true}` | Requires hidden AP detector active |


## Wi-Fi Attacks and Portal


| Command | Args | Response | Events |
|---|---|---|---|
| `DEAUTH` | `{bssid,client,channel,count,reason,deauth_interval_ms}` | `{ok:true}` | `deauth_stats` |
| `DEAUTH_CAPTURE` | Same as `DEAUTH` | `{ok:true}` | `deauth_stats`, then starts EAPOL capture |
| `START_BEACON` | `{ssids:"SSID1\nSSID2",channel,interval_ms,random_bssid,hidden}` | `{ok:true,ssids,channel}` | |
| `STOP_BEACON` | none | `{ok:true,sent,ssids}` | |
| `BEACON_STATUS` | none | `{ok:true,active,ssids,sent,channel}` | |
| `START_PORTAL` | `{ssid,channel,bssid}` | `{ok:true}` | `portal_viewed`, `captive_data`, `client_associated` |
| `STOP_PORTAL` | none | `{ok:true}` | |
| `RESET_HTML` | `{size}` | `{ok:true}` | `debug` events |
| `SET_HTML_CHUNK` | `{data:"<base64>",last:bool,offset?:number}` | `{ok:true}` | `debug` events |
| `PORTAL_STATUS` | none | `{ok:true,running,html_size,html_expected,html_complete}` | |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
