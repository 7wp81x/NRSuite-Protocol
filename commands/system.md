# System Commands

## System


| Command | Args | Response | Notes |
|---|---|---|---|
| `PING` | none | `{ok:true,msg:"pong"}` | Liveness check |
| `STATUS` | none | See STATUS Response | Device/feature handshake |
| `HEAP` | none | Same as `STATUS` | Alias |
| `STOP_ALL` | none | `{ok:true}` | Stops all radio/BLE/upload modules |
| `SET_CHANNEL` | `{channel:1..13}` | `{ok:true}` | Changes sniffer channel |

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
