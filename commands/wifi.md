# Wi-Fi Commands

## Nrugochi (pwnagotchi-style) capture

Android orchestrates the RECON -> INTERACT cycle. There is no ADVERTISE/Pwngrid
phase in this implementation.

1. `SCAN_WIFI` builds the AP list.
2. Channels are ranked by AP density, then APs within a channel by RSSI.
3. `DEAUTH_CHANNEL_CAPTURE` deauths multiple APs on one channel.
4. Firmware then starts all-EAPOL + all-beacon capture on that channel.
5. Android splits the PCAP stream per BSSID and writes `HS_<BSSID>.pcap`.
6. `STOP_SNIFF` / `STOP_ALL` clean up between channels and on stop.

`DEAUTH_CHANNEL_CAPTURE` args:
`{band, channel, targets:[{bssid}], count, deauth_interval_ms, reason, all_beacons}`.

`count` is sent **per target BSSID**. Android defaults NRuGochi to 8 frames per
AP at 50 ms intervals; a single frame is commonly ignored, especially on 5 GHz.
The response reports `requested_frames`, `sent_frames`, `failed_frames`, and
`targets`. Android logs the successful/requested count after each channel pass.

`START_SNIFF` also accepts `all_beacons:true` for passive channel capture.
Firmware advertises the capability as `nrugochi` in `STATUS.features`.
PMKID capture and Pwngrid advertising are out of scope.

## Wi-Fi Recon

> Band-aware Wi-Fi is capability-driven. `band:"auto"` is the default and
> enables 2.4 + 5 GHz operation on ESP32-C5 firmware advertising `wifi_5ghz`;
> other targets map it to 2.4 GHz only. Explicit `band:"2g"` and `band:"5g"`
> are supported where the hardware/firmware combination allows them. Channel
> numbers determine the band for targeted commands (`1–14` = 2.4 GHz,
> `36–177` = 5 GHz).
>
> The WiFi Scan screen's Auto/2.4/5 GHz filter is screen-local. Target-picker
> scans in Sniffer, Deauth, Client Detector, Deauth Detector, and Evil Twin
> always request firmware AUTO so the WiFi Scan filter cannot leak across
> modules. Hopping modules expose their own band selector.
>
> `SET_COUNTRY` and the `allowed_*_channels` fields are authoritative for
> regulatory filtering. The firmware rejects fixed channels not permitted by
> the active country mask, and Android limits its channel steppers to those
> reported lists. The Android app exposes the country control only in Settings
> while an ESP32-C5 is connected. Do not hard-code a country such as `US`; the
> user must choose their actual location.

| Command | Args | Response | Events |
|---|---|---|---|
| `SCAN_WIFI` | `{band?:"auto"|"2g"|"5g"}` | `{ok:true,count:N,band}` | `scan_ap` per network |
| `SET_COUNTRY` | `{country:"US"|"GB"|"01"|...}` | `{ok:true,country,allowed_2ghz_channels,allowed_5ghz_channels}` | Persists regulatory country and refreshes channel mask |
| `START_SNIFF` | `{mode:"fixed"|"hop",band?:"auto"|"2g"|"5g",channel,interval_ms,eapol_only,bssid,all_beacons}` | `{ok:true}` | `PCAP` frames |
| `STOP_SNIFF` | none | `{ok:true,captured,sent,dropped}` | |
| `START_CLIENT_DETECT` | `{mode:"fixed"|"hop",band?:"auto",channel,interval_ms}` | `{ok:true}` | `client_detected` |
| `STOP_CLIENT_DETECT` | none | `{ok:true,captured,sent,dropped}` | |
| `START_HIDDEN_AP` | `{mode:"fixed"|"hop",band?:"auto",channel,interval_ms}` | `{ok:true}` | `hidden_ap`, `hidden_ssid_candidate`, `hidden_ssid_resolved`, `hidden_ap_hop` |
| `STOP_HIDDEN_AP` | none | `{ok:true,hidden,candidates,resolved,sent,dropped}` | |
| `HIDDEN_AP_FORCE_RECONNECT` | `{bssid,client,channel,count,interval_ms,reason}` | `{ok:true}` | Requires hidden AP detector active |


## Wi-Fi Attacks and Portal


| Command | Args | Response | Events |
|---|---|---|---|
| `DEAUTH` | `{bssid,client,band?:"auto",channel,count,reason,deauth_interval_ms}` | `{ok:true}` | `deauth_stats` |
| `DEAUTH_CAPTURE` | Same as `DEAUTH` | `{ok:true}` | `deauth_stats`, then starts EAPOL capture |
| `DEAUTH_CHANNEL_CAPTURE` | `{band,channel,targets:[{bssid}],count,deauth_interval_ms,reason,all_beacons}` | `{ok:true,requested_frames,sent_frames,failed_frames,targets,channel,band}` | starts all-EAPOL/all-beacon capture after multi-AP deauth |
| `START_BEACON` | `{ssids:"SSID1\nSSID2",band?:"auto",channel,interval_ms,random_bssid,hidden}` | `{ok:true,ssids,channel}` | |
| `STOP_BEACON` | none | `{ok:true,sent,ssids}` | |
| `BEACON_STATUS` | none | `{ok:true,active,ssids,sent,channel}` | |
| `START_PORTAL` | `{ssid,band?:"auto",channel,bssid}` | `{ok:true}` or `{ok:false,error:"regulatory_channel_blocked"|"softap_start_failed",msg,channel,allowed_*_channels}` | `portal_viewed`, `captive_data`, `client_associated` |
| `STOP_PORTAL` | none | `{ok:true}` | |
| `RESET_HTML` | `{size}` | `{ok:true}` | `debug` events |
| `SET_HTML_CHUNK` | `{data:"<base64>",last:bool,offset?:number}` | `{ok:true}` | `debug` events |
| `PORTAL_STATUS` | none | `{ok:true,running,html_size,html_expected,html_complete}` | |

> Captive Portal and Evil Twin currently fail fast with a visible Android error;
> they do not silently change channels. Evil Twin must use the target AP channel
> for correctness, and Captive Portal keeps the same no-surprise policy until an
> explicit auto-fallback option is added.

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
