# BLE Commands

## BLE


| Command | Args | Response | Events |
|---|---|---|---|
| `BLE_SCAN_START` | `{active,interval_ms,window_ms,min_emit_ms}` | `{ok:true}` | `ble_device` |
| `BLE_SCAN_STOP` | none | `{ok:true}` | |
| `BLE_PROFILE_START` | `{address,address_type}` | `{ok:true}` | `ble_profile`, `ble_service`, `ble_characteristic` |
| `BLE_PROFILE_STOP` | none | `{ok:true}` | `ble_profile` |
| `BLE_START` | `{name}` | `{ok:true}` | |
| `BLE_STATUS` | none | `{ok:true,connected,advertising,peer}` | |
| `BLE_STOP` | none | `{ok:true}` | |
| `BLE_RUN_SCRIPT` | `{script}` | `{ok:true,lines}` | |
| `BLE_STOP_SCRIPT` | none | `{ok:true}` | |
| `BLE_KEY_DOWN` | `{key}` | `{ok:true}` | |
| `BLE_KEY_UP` | `{key}` | `{ok:true}` | |
| `BLE_KEY_TAP` | `{key}` | `{ok:true}` | |
| `BLE_TYPE_TEXT` | `{text}` | `{ok:true}` | |
| `BLE_MOUSE_MOVE` | `{dx,dy}` | `{ok:true}` | |
| `BLE_MOUSE_SCROLL` | `{wheel}` | `{ok:true}` | |
| `BLE_MOUSE_BUTTON` | `{button,down}` | `{ok:true}` | |
| `BLE_MOUSE_RELEASE` | none | `{ok:true}` | |
| `BLE_RELEASE_ALL` | none | `{ok:true}` | |
| `BLE_PIN_ADVERTISE_START` | `{name?,auto_reconnect?}` | `{ok:true}` | `ble_pin_connection`, `ble_pin_session_status` |
| `BLE_PIN_ADVERTISE_STOP` | none | `{ok:true}` | `ble_pin_connection`, `ble_pin_session_status` |
| `BLE_PIN_START` | `{mode:"ble_hid_live",source:"range"\|"wordlist",pin_length,start,end,timeout_ms?,max_attempts?,persist_every?,attempts_before_cooldown?,cooldown_ms?,inter_attempt_ms?,typing_delay_ms?,start_delay_ms?,auto_resume?,auto_start_on_connect?,pause_on_disconnect?,auto_reconnect?,session_key?,wordlist_file?}` | `{ok:true}` | `ble_pin_session_status`, `ble_pin_attempt`, `ble_pin_done` |
| `BLE_PIN_PAUSE` | none | `{ok:true}` | `ble_pin_session_status` |
| `BLE_PIN_RESUME` | none | `{ok:true}` | `ble_pin_session_status` |
| `BLE_PIN_STOP` | none | `{ok:true}` | `ble_pin_done`, `ble_pin_session_status` |
| `BLE_PIN_NEXT` | none | `{ok:true}` | `ble_pin_attempt`, `ble_pin_session_status` |
| `BLE_PIN_PREV` | none | `{ok:true}` | `ble_pin_session_status` |
| `BLE_PIN_CLEAR` | `{wordlist?:bool}` | `{ok:true}` | `ble_pin_session_status` |
| `BLE_PIN_STATUS` | none | `{ok:true,state,...}` | |
| `BLE_PIN_FORGET_BOND` | none | `{ok:true}` | `ble_pin_session_status` |
| `BLE_PIN_DISCONNECT` | none | `{ok:true}` | `ble_pin_connection`, `ble_pin_session_status` |
| `BLE_PIN_WORDLIST_RESET` | none | `{ok:true}` | |
| `BLE_PIN_WORDLIST_CHUNK` | `{data:"<base64>",offset,checksum,last}` | `{ok:true}` | |

> BLE HID PIN Bruteforce keeps the USB CDC bridge alive while the ESP32 types
> through a bonded BLE HID keyboard. Pair the host first, then start the session
> with live controls. `BLE_PIN_START` is a hard-capped supervised test.
> `BLE_PIN_NEXT` marks the next candidate as skipped and advances the sequence;
> `BLE_PIN_PREV` steps back one candidate and pauses a running session.
> `auto_start_on_connect` only auto-resumes a session that was paused by a BLE
> disconnect. `pause_on_disconnect` defaults to true. Wordlists use
> `/pin_wordlist.txt` and the same 1000-line / 16 KB validation as native HID.
> Bond storage and advertising restart are handled by the BLE HID stack.

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
