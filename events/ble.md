# BLE Events

Every event includes `type` plus event-specific fields.

| Event type | Fields | Notes |
|---|---|---|
| `ble_device` | `address`, `address_type`, `rssi`, `connectable`, `tx_power`, `appearance`, `uptime_ms`, `name?`, `manufacturer_data?`, `raw_payload?`, `services?` | BLE scanner |
| `ble_profile` | `address`, `status` | `connecting`, `connected`, `done`, or `failed` |
| `ble_service` | `service_uuid` | GATT service |
| `ble_characteristic` | `service_uuid`, `uuid`, `properties` | `properties` has `read`, `write`, `write_no_response`, `notify`, `indicate`, `broadcast` |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
