# NFC / RFID Commands

## PN532 ISO14443A reader (read-only)

The PN532 is a 13.56 MHz NFC controller connected to the ESP32 over I2C.
Milestone 1 exposes read-only ISO14443A identification only: UID, ATQA, SAK,
and an estimated tag family. Writes, locks, dumps, emulation, key recovery, and
APDU tooling are deliberately not part of this command set.

Capability flags advertised in `STATUS.features`:

- `nfc`
- `rfid`
- `pn532`

| Command | Args | Response | Notes |
|---|---|---|---|
| `RFID_STATUS` | none | `{ok:true, connected, configured, interface:"i2c", sda_gpio, scl_gpio, firmware_version, firmware_version_raw, scanning, tag_read_only:true, rfid_gpios:[...]}` | Returns PN532 status. If GPIOs are configured but the reader is not initialized, firmware retries detection. |
| `RFID_SET_CONFIG` | `{interface:"i2c", sda_gpio:int, scl_gpio:int}` | Status fields plus `{ok, config_saved, detection_ok, msg}` | Validates GPIOs, stops scanning, stores the pins in ESP32 NVS, reinitializes the I2C bus, and attempts PN532 detection. `ok`/`config_saved` report whether the configuration was accepted and persisted; `detection_ok` and `connected` report whether the reader responded. A saved configuration can therefore have `ok:true` and `detection_ok:false`. |
| `RFID_SCAN_START` | none | Status fields plus `{ok, msg}` | Starts ISO14443A passive polling. Fails if the PN532 is not configured or detected. |
| `RFID_SCAN_STOP` | none | Status fields plus `{ok, msg}` | Stops polling. Safe to call when already stopped. |

### GPIO rules

- SDA and SCL must be different.
- Only target-safe GPIOs advertised by `rfid_gpios` are accepted.
- Do not select flash, native USB, UART, PSRAM, or currently used peripheral pins.
- PN532 VCC is 3.3 V, GND must be common with the ESP32, and the module must be
  configured for I2C mode.
- IRQ and reset pins are not required for polling and are not configured in this
  milestone.

### Read-only guarantee

No command in this milestone writes tag memory, changes lock bits, formats a
tag, or performs cloning/emulation. `rfid_tag` events include `read_only:true`.

### Estimated tag families

These mappings are heuristics based on SAK/ATQA and must not be treated as a
memory-layout guarantee:

| ATQA | SAK | Estimate |
|---|---|---|
| `0004` | `08` | MIFARE Classic 1K |
| `0004` | `18` | MIFARE Classic 4K |
| `0004` | `09` | MIFARE Classic Mini |
| `0044` | `00` | NTAG / MIFARE Ultralight |
| SAK bit 5 set | `20`-class | ISO14443-4 |
