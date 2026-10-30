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
> On ESP32-C5, `SCAN_WIFI` keeps the radio in dual-band AUTO mode and restricts
> the scan with the 2.4/5 GHz channel bitmaps. This avoids the idle 2.4 GHz
> helper SoftAP blocking 5 GHz scans. Explicit 5 GHz scans use passive scan
> timing so DFS channels are not skipped by active-scan restrictions.
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
| `DEAUTH` | `{bssid,client,band?:"auto",channel,mode?:"burst"|"loop",count,duration,reason,deauth_interval_ms}` | Burst: final counts. Loop: `{ok:true,active:true,mode:"loop",duration,interval_ms}` | `deauth_stats` |
| `DEAUTH_STOP` | none | `{ok:true,sent_frames,failed_frames}` | Stops an active deauth loop |
| `DEAUTH_BURST` | `{bssid,client,band?:"auto",channel,count,reason,deauth_interval_ms}` | `{ok:true,mode:"burst",requested_frames,sent_frames,failed_frames}` | Capture-preserving burst; does not stop an active sniffer |
| `DEAUTH_CAPTURE` | Same as `DEAUTH` burst mode | `{ok:true}` | `deauth_stats`, then starts EAPOL capture |
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

### Deauth modes

`mode` makes count and duration mutually exclusive:

- `burst` uses `count` and sends a finite number of frames.
- `loop` uses `duration` in seconds and ignores `count`.
  - `duration:0` runs until `DEAUTH_STOP` or another radio command stops it.
  - `DEAUTH_STOP` is safe to call while the loop task is running.
  - The firmware emits periodic `deauth_stats` events with `status:"running"`
    and a final event with `status:"finished"`.

`DEAUTH_BURST` is the capture-assist variant. Android starts the sniffer first,
then sends `DEAUTH_BURST` immediately and retries it every configured interval
until the capture stops or a handshake is found. Unlike `DEAUTH`, it does not
call the firmware radio-idle path and therefore does not stop the sniffer.

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)


## WPS Lock Detector

`WPS_LOCK_SCAN` performs a passive WPS AP discovery scan. It listens for
beacons/probe responses on the selected band, parses each AP's WPS IE, and emits
one `wps_lock_ap` event per WPS-enabled AP. It does not attempt a WPS PIN or send
WPS M1-M4 messages. After the passive pass it may run a normal non-WPS active
scan only to resolve missing SSID names for the captured BSSIDs.

| Command | Args | Response | Events |
|---|---|---|---|
| `WPS_LOCK_SCAN` | `{band?:"auto"|"2g"|"5g",dwell_ms?:120}` | `{ok:true,count}` | `wps_lock_ap` |

`STATUS.features` advertises `wps_lock_detect` when this scan is available.

## WPS Pixie Dust

The live WPS Pixie Dust flow is PIN-first and uses the same registrar transaction
for either a successful PSK recovery or capture of Pixie Dust material after a
wrong-PIN rejection. The app owns PIN generation, the BSSID->PIN database, and
the offline Pixiewps search. Firmware executes one PIN attempt per command.

`STATUS.features` advertises `wps_pixie` on builds where raw WPS registrar
injection is supported (currently ESP32-S3 and ESP32-C5).

| Command | Args | Response | Events |
|---|---|---|---|
| `WPS_PIXIE_ATTEMPT` | `{bssid,ssid,channel,band,pin,pin_source,capture_only?,reuse_mac?,run_id?}` | `{ok:true,run_id}` | `wps_pixie_progress`, `wps_pixie_wrong_pin`, `wps_pixie_psk`, `wps_pixie_error` |
| `WPS_PIXIE_CONTINUE` | `{run_id,pin,pin_source?}` | `{ok:true}` | `wps_pixie_progress`, `wps_pixie_psk`, `wps_pixie_error` |
| `WPS_PIXIE_STOP` | `{run_id?}` | `{ok:true}` | `wps_pixie_error` with `code:"stopped"` |

`pin_source` is one of `stored`, `generated`, `pixie`, or `manual`.
`capture_only` defaults to `false`. `reuse_mac` defaults to `false`; set it
for the corrected-PIN retry so the same randomized STA MAC is reused within
the same target campaign. This avoids leaving the AP's WPS state machine tied
to the previous capture attempt's MAC.

When `capture_only:true`, firmware captures and validates M1/M2/M3, emits the
complete M1/M2/M3/AuthKey material via `wps_pixie_wrong_pin` with
`m3_only:true`, and keeps the existing WPS association/session alive without
sending M4. This avoids both a wrong-PIN validation and a risky AP WPS-session
restart. After the offline crack, the app sends `WPS_PIXIE_CONTINUE` with the
same `run_id` and recovered PIN; firmware builds M4 from the retained M3 state
and continues M5-M8 on the same session.

With `capture_only:false`, a valid PIN runs M1 through M8. If the AP rejects the
PIN after M4, firmware emits `wps_pixie_wrong_pin` with `m3_only:false` and the
complete material so the app can run the offline cracker and retry once.

WPS lock and timeout handling:

- M2D, a NACK before M3, or configuration error `15` means the AP may be locked.
- The app must not automatically retry after a lockout event.
- Show a cooldown warning and let the user retry later.
- Before association, firmware passively checks fresh beacon/probe responses
  for the AP Setup Locked attribute (`0x1057`). A stale/absent attribute is not
  treated as proof that the AP is unlocked.
- If the lock flag is set, firmware waits up to 30 seconds for it to clear and
  emits `code:"wps_locked"` if it does not.
- M1 must arrive within 10 seconds after association/EAPOL-Start, otherwise the
  firmware emits `wps_pixie_error` with `code:"m1_timeout"`.
- M3 must arrive within 10 seconds after M2, otherwise the firmware emits
  `code:"m3_timeout"`.
- The overall attempt timeout is 35 seconds and emits `code:"timeout"`.
- The app must not automatically retry after an M1/M3/overall timeout. The user
  can start a fresh attempt after the radio has settled.
- A new `WPS_PIXIE_ATTEMPT` tears down the previous raw STA/SoftAP state before
  re-arming the registrar path.
- After the AP lock preflight and before raw authentication, firmware sends a
  raw Deauthentication and Disassociation using the campaign STA MAC to clear
  any stale AP association/WPS state from a prior attempt.
- The hidden helper SoftAP uses a randomized `NRSuite-WPS-xxxxxx` SSID and a
  random WPA2 password with zero intended clients. A hidden SoftAP is still
  detectable as a BSSID; it is not an invisible AP.
- Duplicate WSC requests replay the cached authenticated reply, including when
  the AP changes the EAP identifier. Fragmented EAP-WSC requests are reassembled
  and acknowledged with Frag-ACK.
- After M8, firmware waits for the enrollee's WSC_Done and replies with a
  registrar WSC_ACK containing Version, Message Type, Enrollee Nonce, Registrar
  Nonce, and the WFA extension. If WSC_Done is lost, firmware finalizes from the
  already validated M7 credentials after a 5-second grace period.


## Wi-Fi automation extensions

Implemented or planned extensions are tracked in
`../WIFI-AUTOMATION-ROADMAP.md`.

- Wifite-style Auto Audit is planned as an app-side orchestrator over existing
  `SCAN_WIFI`, `DEAUTH_BURST`/`DEAUTH`, `START_SNIFF`, `WPS_PIXIE_*`,
  `START_PORTAL`, and `STOP_ALL` commands.
- `deauth_stats` now includes `elapsed_ms` and `pps` telemetry.
- The Probe Request Monitor aggregates existing `client_detected` events with
  `subtype:"probe_request"`; no new command is required.
- PMKID capture commands/events are not defined yet.
- Captive Portal / Evil Twin template management reuses the existing
  `RESET_HTML` and `SET_HTML_CHUNK` flow.

## WPS Attempt Detector

The WPS Attempt Detector passively monitors 802.11 data frames for EAP-WSC
messages. It does not transmit or attempt WPS authentication. Firmware tracks
sessions by target BSSID + source client MAC and emits compact progress events
for Android-side vendor lookup and risk scoring.

| Command | Args | Response | Events |
|---|---|---|---|
| `WPS_ATTEMPT_DETECT_START` | `{mode?:"hop"|"fixed",band?:"auto"|"2g"|"5g",channels?:[int],targets?:[bssid],interval_ms?:300}` | `{ok:true,active,hopping,channel,channels,targets,interval_ms}` | `wps_attempt_session` |
| `WPS_ATTEMPT_DETECT_STOP` | none | `{ok:true,sessions,frames}` | |
| `WPS_ATTEMPT_DETECT_STATUS` | none | `{ok:true,active,channel,hopping,sessions,frames}` | |

`STATUS.features` advertises `wps_attempt_detect`.

- `targets` limits emitted attempts to the listed BSSIDs. Omit it to monitor all observed WPS attempts.
- `channels` restricts the monitor to those channels. One channel gives fixed monitoring; multiple channels hop only across that set.
- Omitting `channels` uses the allowed band channels: 2.4 GHz, or 2.4/5 GHz when the board supports 5 GHz and `band:"auto"`.
- Every requested channel is validated against the active regulatory mask.
