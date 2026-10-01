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

---

> Core transport and framing: [PROTOCOL-SPEC.md](../PROTOCOL-SPEC.md)
