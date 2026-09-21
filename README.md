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

## Contents

- [Physical Transport](#physical-transport)
- [Frame Format](#frame-format)
- [Frame Types](#frame-types)
- [Session Lifecycle](#session-lifecycle)
- [JSON Payload Schema](#json-payload-schema)
  - [COMMAND frames](#command-frames)
  - [RESPONSE frames](#response-frames)
  - [EVENT frames](#event-frames)
  - [PCAP frames](#pcap-frames)
  - [ACK frames](#ack-frames)
  - [HTML frames](#html-frames)
- [Command Reference](#command-reference)
- [Error Handling](#error-handling)
- [Planned Extensions](#planned-extensions)
