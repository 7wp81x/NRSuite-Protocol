# nrsuite-protocol

**Wire protocol specification for the NRSuite security research toolkit.**

This repo is the single source of truth for the frame format and JSON payload schema used between the NRSuite Android app and NRSuite ESP32 firmware. Both repos are versioned independently; this spec is what keeps them compatible.

If your change adds, removes, or modifies any command, response field, or frame type, update this spec and bump the version **before** merging either side's implementation.

---

## Versioning

This spec uses `MAJOR.MINOR` versioning:

- **MAJOR** bumped for breaking changes (removed fields, changed frame layout, renamed commands)
- **MINOR** bumped for additive changes (new commands, new optional response fields, new frame types)

App and firmware releases each declare which spec version they implement. See the [compatibility table](./COMPATIBILITY.md).

**Current version: `1.0`**

---

## Repository layout

- [PROTOCOL-SPEC.md](./PROTOCOL-SPEC.md) - core transport, frame format, session lifecycle, JSON envelope, STATUS response, and error handling
- [commands/](./commands/README.md) - command reference by radio category
- [events/](./events/README.md) - event reference by category
- [COMPATIBILITY.md](./COMPATIBILITY.md) - app/firmware/protocol compatibility matrix

### Core spec sections

- [Physical Transport](./PROTOCOL-SPEC.md#physical-transport)
- [Frame Format](./PROTOCOL-SPEC.md#frame-format)
- [Frame Types](./PROTOCOL-SPEC.md#frame-types)
- [Session Lifecycle](./PROTOCOL-SPEC.md#session-lifecycle)
- [JSON Payload Schema](./PROTOCOL-SPEC.md#json-payloads)
- [STATUS Response](./PROTOCOL-SPEC.md#status-response)
- [Error Handling](./PROTOCOL-SPEC.md#error-handling)
- [Planned Extensions](./PROTOCOL-SPEC.md#planned-extensions-future-minor-versions)
