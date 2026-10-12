# Storage and HID Commands

## Storage and HID


| Command | Args | Response | Notes |
|---|---|---|---|
| `START_MSC` | none | `{ok:true}` | Reboots into USB MSC mode on S2/S3 |
| `MSC_LIST` | none | `{ok:true,files:[{name,size}],total,used,free}` | File list |
| `MSC_READ` | `{path,offset?,length?}` | `{ok:true,path,content,size,offset,total,eof}` | Chunked reads max 768 bytes |
| `MSC_WRITE` | `{path,content,append}` | `{ok:true}` | Writes/appends text |
| `MSC_DELETE` | `{path}` | `{ok:true}` | Deletes a file |
| `MSC_SPACE` | none | `{ok:true,total,used,free}` | Free-space query |
| `MSC_SETUP` | none | `{ok:true}` | Enters MSC mode directly |
| `SET_FILE_CHUNK` | `{filename,data:"<base64>",last}` | `{ok:true}` | Chunked file upload for DuckyScripts |
| `START_BADUSB` | `{filename,msc}` | `{ok:true}` | Arms native USB HID payload |
| `PIN_WORDLIST_RESET` | none | `{ok:true}` | Starts/clears a PIN wordlist upload buffer |
| `PIN_WORDLIST_CHUNK` | `{data:"<base64>",last}` | `{ok:true}` | Uploads PIN wordlist data; max 1000 lines, 16 KB total, 64 chars per line |
| `PIN_RANGE_START` | `{mode:"standalone_native_hid"|"external_ch9329_realtime",source:"range"|"wordlist",pin_length,start,end,charset?,custom_chars?,prefix?,suffix?,timeout_ms?,attempts_before_timeout?,inter_attempt_ms?,auto_resume?,session_key?,wordlist_file?}` | `{ok:true,state,...}` | Starts/arms a supervised HID PIN session |
| `PIN_RANGE_STOP` | none | `{ok:true,state,...}` | Pauses the active session and releases HID keys |
| `PIN_RANGE_STATUS` | none | `{ok:true,state,...}` | Returns the persisted/live session state |
| `PIN_RANGE_RESUME` | none | `{ok:true,state,...}` | Resumes a persisted paused/armed session |
| `PIN_RANGE_CLEAR` | `{wordlist?:bool}` | `{ok:true,state,...}` | Clears session state; optionally removes the wordlist |

> `external_ch9329_realtime` is reserved/deferred. Current Android UI exposes
> native HID only. Wordlists use `PIN_WORDLIST_*` and are stored on the device.
> HID cannot confirm target success; sessions are supervised only.

---

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
