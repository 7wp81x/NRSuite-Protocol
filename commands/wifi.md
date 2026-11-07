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
Firmware advertises the capability as `nrugochi` in `STATUS.features`. ESP32-S2
builds intentionally omit this capability for release memory/profile reasons.
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
> Classic ESP32 uses a longer 500 ms channel dwell by default because short
> active scans can intermittently return very small AP lists. Newer targets
> default to 300 ms. Firmware advertising `scan_results_pull` stores a bounded
> snapshot and the app retrieves it with `SCAN_RESULTS`; legacy firmware is
> still supported through `scan_ap` events. The app compares the response count
> with the number of verified pulled records (or legacy events) to distinguish
> RF scan misses from USB/UART transport loss.
>
> On ESP32-C5, `SCAN_WIFI` keeps the radio in dual-band AUTO mode and restricts
> the scan with the 2.4/5 GHz channel bitmaps. This avoids the idle 2.4 GHz
> helper SoftAP blocking 5 GHz scans. Explicit 5 GHz scans use passive scan
> timing so DFS channels are not skipped by active-scan restrictions. As a
> final guard, firmware drops any returned AP whose channel does not match an
> explicit `2g` or `5g` request. `count` therefore reports emitted matching APs
> and `scanned` reports the raw scan-result count.
>
> `SET_COUNTRY` and the `allowed_*_channels` fields are authoritative for
> regulatory filtering. The firmware rejects fixed channels not permitted by
> the active country mask, and Android limits its channel steppers to those
> reported lists. The Android app exposes the country control only in Settings
> while an ESP32-C5 is connected. Do not hard-code a country such as `US`; the
> user must choose their actual location.

| Command | Args | Response | Events |
|---|---|---|---|
| `SCAN_WIFI` | `{band?:"auto"|"2g"|"5g",settle_ms?:number,dwell_ms?:number,pull_results?:bool}` | Legacy: `{ok:true,count:N,scanned:M,band,dwell_ms}`. Pull: `{ok:true,scan_id,count:N,scanned:M,band,dwell_ms,kind:"wifi",truncated}` | Legacy firmware emits `scan_ap` events. When `pull_results:true` (or the firmware advertises `scan_results_pull`), the app instead calls `SCAN_RESULTS` and the firmware does not emit the event burst. Firmware serializes scans, settles 250-5000 ms (default 900), uses a 200-1000 ms channel dwell (classic ESP32 defaults to 500 ms), and retries empty/low-result scans up to two times. `count` is the number of retrievable records; `truncated:true` means the bounded snapshot dropped excess APs. |
| `SCAN_RESULTS` | `{scan_id,offset,limit?}` | `{ok:true,scan_id,kind,offset,count,total,next_offset,crc32,results:[...]}` | Pull-based retrieval of the most recent `SCAN_WIFI` or `WPS_LOCK_SCAN` snapshot. `limit` is clamped to 1-8 (default 4). Each chunk is independently verifiable and may be retried with the same `scan_id`/`offset`. |
| `SET_COUNTRY` | `{country:"US"|"GB"|"CH"|"01"|...}` | `{ok:true,country,allowed_2ghz_channels,allowed_5ghz_channels}` | Persists regulatory country and refreshes channel mask. Blank firmware NVS defaults to `CH`; an existing saved country is preserved. |
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
| `DEAUTH_STOP` | none | `{ok:true,mode,sent_frames,failed_frames,targets?}` | Stops an active single- or multi-target deauth loop |
| `DEAUTH_MULTI` | `{targets:[{bssid,channel}],client,mode?:"burst"|"loop",count,duration,interval_ms,reason}` | Burst: final aggregate/per-target counts. Loop: `{ok:true,active:true,mode:"multi",targets,...}` | `deauth_stats` with `mode:"multi"` |
| `DEAUTH_BURST` | `{bssid,client,band?:"auto",channel,count,reason,deauth_interval_ms}` | `{ok:true,mode:"burst",requested_frames,sent_frames,failed_frames}` | Capture-preserving burst; does not stop an active sniffer |
| `DEAUTH_CAPTURE` | Same as `DEAUTH` burst mode | `{ok:true}` | `deauth_stats`, then starts EAPOL capture |
| `DEAUTH_CHANNEL_CAPTURE` | `{band,channel,targets:[{bssid}],count,deauth_interval_ms,reason,all_beacons}` | `{ok:true,requested_frames,sent_frames,failed_frames,targets,channel,band}` | starts all-EAPOL/all-beacon capture after multi-AP deauth |
| `START_BEACON` | `{ssids:"SSID1\nSSID2",band?:"auto",channel,interval_ms,random_bssid,hidden}` | `{ok:true,ssids,channel}` | |
| `STOP_BEACON` | none | `{ok:true,sent,ssids}` | |
| `BEACON_STATUS` | none | `{ok:true,active,ssids,sent,channel}` | |
| `START_PORTAL` | `{ssid,band?:"auto",channel,bssid?,show_notice?:bool=true,dns_hijack?:bool=true}` | `{ok:true}` or `{ok:false,error:"regulatory_channel_blocked"|"softap_start_failed",msg,channel,allowed_*_channels}` | `portal_client_seen`, `portal_viewed`, `portal_dns_hijack`, `captive_data`, `client_associated` |
| `STOP_PORTAL` | none | `{ok:true}` | |
| `RESET_HTML` | `{size}` | `{ok:true}` | `debug` events; creates/truncates the portal HTML file |
| `SET_HTML_CHUNK` | `{data:"<base64>",last:bool,offset?:number}` | `{ok:true}` | `debug` events; writes directly to portal storage |
| `PORTAL_STATUS` | none | `{ok:true,running,html_size,html_expected,html_complete}` | |

> Captive Portal and Evil Twin currently fail fast with a visible Android error;
> they do not silently change channels. Evil Twin must use the target AP channel
> for correctness, and Captive Portal keeps the same no-surprise policy until an
> explicit auto-fallback option is added.

Portal data capture:

- `captive_data` is emitted for POST `/login`, GET `/login`, and credential-like GET query parameters on `/` and `/continue`. `request_type` identifies the request form.
- `/` and `/continue` serve portal content, `/login` handles submissions, and unmatched paths are served the landing page directly. Firmware also advertises `192.168.4.1` as the DHCP DNS server and best-effort intercepts plaintext IPv4 UDP DNS sent to external resolvers. Set `dns_hijack:false` to disable only the custom-resolver interception; DHCP DNS, wildcard DNS, and forced routes remain active.

Portal HTML storage:

- `show_notice` defaults to `true`. When true, `/` serves the firmware test
  notice page and `/continue` serves the uploaded HTML. When false, `/` serves
  the uploaded HTML directly.
- S2/S3 store portal HTML on the existing FAT `msc_ffat` partition so USB MSC
  remains host-readable.
- C3/C5/classic ESP32 store portal HTML on the dedicated LittleFS `portal`
  partition.
- Android renders `#SSID#` into a temporary cache file and uploads it in
  chunks; the full page is not held in Android RAM.
- Firmware writes chunks to `/portal/index.html` and streams that file from the
  HTTP server. The full page is no longer retained in `_htmlBuffer`.
- The current maximum HTML size remains 24 KiB.

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

### Firmware-native multi-target deauth

`DEAUTH_MULTI` keeps the target/channel schedule in firmware and supports up to
32 targets. Each target is specified as `{bssid,channel}`. The command:

- validates every BSSID and channel, including the active regulatory mask;
- deduplicates/rejects repeated BSSIDs;
- switches channel per target;
- accepts `interval_ms` (canonical) and `deauth_interval_ms` (compatibility
  alias);
- supports burst mode and loop mode;
- treats `duration:0` in loop mode as run-until-`DEAUTH_STOP`;
- reports `requested_frames`, `sent_frames`, and `failed_frames` per target and
  in aggregate;
- is stopped by `DEAUTH_STOP` or `STOP_ALL`.

`STATUS.features` advertises `deauth_multi`. Android uses this capability only
for multi-target selections. Older firmware and selections above 32 targets
use the app-side repeated `DEAUTH_BURST` channel-hopping fallback.

Burst response and loop start response fields:

```json
{
  "ok": true,
  "mode": "multi",
  "active": false,
  "target_count": 2,
  "count": 20,
  "duration": 0,
  "interval_ms": 100,
  "requested_frames": 40,
  "sent_frames": 39,
  "failed_frames": 1,
  "elapsed_ms": 1234,
  "pps": 31.6,
  "targets": [
    {
      "bssid": "AA:BB:CC:DD:EE:FF",
      "channel": 1,
      "requested_frames": 20,
      "sent_frames": 20,
      "failed_frames": 0
    }
  ]
}
```

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)


## WPS Lock Detector

`WPS_LOCK_SCAN` uses a hybrid discovery pass. A normal active Wi-Fi scan first
builds the authoritative candidate set from APs whose scan record advertises
WPS. A passive promiscuous pass then listens for beacons/probe responses on the
selected band and enriches those candidates with WPS IE metadata such as AP
Setup Locked, WPS version, configuration methods, and selected-registrar state.
The active-scan SSID, channel, security, and RSSI are retained when available;
passive-only WPS observations are still included. By default it emits one
`wps_lock_ap` event per WPS-enabled AP in legacy mode. With
`include_non_wps:true`, active-scan non-WPS APs are also returned as `scan_ap`
records for UI filtering. It does not attempt a WPS PIN or send WPS M1-M4
messages.

| Command | Args | Response | Events |
|---|---|---|---|
| `WPS_LOCK_SCAN` | `{band?:"auto"|"2g"|"5g",dwell_ms?:120,pull_results?:bool,include_non_wps?:bool}` | Legacy: `{ok:true,count}`. Pull: `{ok:true,scan_id,count,scanned,kind:"wps",include_non_wps,truncated}` | Default is WPS-only discovery. `include_non_wps:true` adds other active-scan APs with `wps:false`; pull results use `scan_ap` for those rows and `wps_lock_ap` for WPS rows. The WPS Pixie screen uses this to make its WPS-only toggle functional. |

`STATUS.features` advertises `wps_lock_detect` when this scan is available.


### Pull-based scan result chunks

The app requests chunks until `next_offset >= total`. On timeout, invalid JSON,
offset/count mismatch, CRC mismatch, or a non-progressing chunk, it retries the
same chunk up to three times before preserving any records already received.

`crc32` is the standard IEEE 802.3/zlib CRC-32 (polynomial `0xEDB88320`) over a
UTF-8 canonical string. For each result in chunk order:

```text
wifi|<ssid_byte_len>:<ssid>|<BSSID>|<channel>|<rssi>|
  <security_byte_len>:<security>|<wps 0/1>|<band>\n

wps|<ssid_byte_len>:<ssid>|<BSSID>|<channel>|<rssi>|
  <security_byte_len>:<security>|<wps 0/1>|<wps_parsed 0/1>|
  <lock_reported 0/1>|<ap_setup_locked 0/1>|<wps_version>|
  <config_methods>|<selected_registrar 0/1>|<last_seen_ms>\n
```

Lengths are UTF-8 byte lengths. The app computes the same canonical string from
the parsed `results` array. The snapshot is bounded to 32 records per scan;
`truncated` is set when the radio returned more results than the snapshot can
hold.

## WPS Pixie Dust

The live WPS Pixie Dust flow is PIN-first and uses the same registrar transaction
for either a successful PSK recovery or capture of Pixie Dust material after a
wrong-PIN rejection. The app owns PIN generation, the BSSID->PIN database, and
the offline Pixiewps search. Firmware executes one PIN attempt per command.

`STATUS.features` advertises `wps_pixie` on all ESP32 firmware builds where raw WPS registrar injection is supported.

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
  file-backed `RESET_HTML` and `SET_HTML_CHUNK` flow.

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
- `wps_attempt_session` preserves per-session evidence flags for M1-M8,
  M2D, and NACK. Earlier M1-M3 or M7-M8 evidence remains visible after a later
  NACK. Android raises High risk for same-session M1+M2+M3 (offline PIN
  cracking material) or M7+M8 (WPA PSK likely transferred); NACK alone is not
  sufficient.
