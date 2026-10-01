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

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
