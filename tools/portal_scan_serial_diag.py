#!/usr/bin/env python3
"""NRSuite portal/scan USB-serial diagnostic client.

Use this on a laptop when you want the firmware diagnostic lines that the
Android app cannot show in logcat. The Android app and this script cannot use
the same USB serial port at the same time; close/disconnect the app first.

The firmware writes both binary NRSuite protocol frames and human-readable
Serial.printf() diagnostics to the same USB serial stream. This script speaks
the protocol (PING, SCAN_WIFI, START_PORTAL, STOP_PORTAL) while also printing
the interleaved firmware text as [FW] lines.

Requirements:
    python3 -m pip install pyserial

Examples:
    # Linux/macOS
    python3 portal_scan_serial_diag.py /dev/ttyACM0 --mode both --cycles 5

    # Windows
    python3 portal_scan_serial_diag.py COM7 --mode both --cycles 5

    # Portal test with a manual Wi-Fi/HTTP check window
    python3 portal_scan_serial_diag.py /dev/ttyACM0 --mode portal --cycles 5 \\
        --http-check --http-hold 10

    # Scan-only test
    python3 portal_scan_serial_diag.py COM7 --mode scan --cycles 5

Portal HTTP check notes:
- Connect the laptop's Wi-Fi to the SSID printed by the script after each
  START_PORTAL. The HTTP check is optional and runs from the laptop, so it
  validates DHCP/DNS/HTTP reachability rather than only the command response.
- The USB serial connection stays open while you change Wi-Fi networks.

Authorized testing only. Use only networks and devices you own or have
explicit written permission to test.
"""

from __future__ import annotations

import argparse
import json
import queue
import re
import sys
import threading
import time
import urllib.error
import urllib.request

try:
    import serial
    from serial.tools import list_ports
except Exception as exc:  # pragma: no cover - dependency error path
    print(f"pyserial is required: {exc}", file=sys.stderr)
    print("Install it with: python3 -m pip install pyserial", file=sys.stderr)
    raise SystemExit(2)

MAGIC = b"\xAD\xDE"
HEADER_SIZE = 8
MAX_PAYLOAD = 1024
TYPE_COMMAND = 0x01
TYPE_RESPONSE = 0x02
TYPE_EVENT = 0x03
TYPE_PCAP = 0x04
TYPE_ACK = 0x05
TYPE_HTML = 0x06


def make_frame(msg_type: int, frame_id: int, payload: bytes) -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"payload too large: {len(payload)}")
    return (
        MAGIC
        + bytes([msg_type, frame_id])
        + len(payload).to_bytes(4, "little")
        + payload
    )


class NRSClient:
    def __init__(self, port: str, baud: int = 115200, debug_raw: bool = False):
        self.port = port
        self.debug_raw = debug_raw
        self.ser = serial.Serial(
            port,
            baud,
            timeout=0.2,
            write_timeout=2.0,
        )
        self._rx_buffer = b""
        self._responses: dict[int, dict] = {}
        self._response_cond = threading.Condition()
        self._next_id = 1
        self.scan_ap_events = 0
        self._stop = threading.Event()
        self._reader = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader.start()

    def _emit_text(self, data: bytes) -> None:
        if not data:
            return
        text = data.decode("utf-8", errors="replace")
        if self.debug_raw:
            print(f"[RAW] {data.hex()}")
        for line in re.split(r"[\r\n]+", text):
            line = line.strip()
            if line:
                print(f"[FW] {line}")

    def _handle_frame(self, frame_type: int, frame_id: int, payload: bytes) -> None:
        if frame_type == TYPE_RESPONSE:
            try:
                doc = json.loads(payload.decode("utf-8"))
            except Exception:
                doc = {"_raw": payload.hex()}
            print(f"[RESP] id={frame_id} {json.dumps(doc, ensure_ascii=False)}")
            with self._response_cond:
                self._responses[frame_id] = doc
                self._response_cond.notify_all()
            return

        if frame_type == TYPE_EVENT:
            try:
                doc = json.loads(payload.decode("utf-8"))
            except Exception:
                doc = {"_raw": payload.hex()}
            if doc.get("type") == "scan_ap":
                self.scan_ap_events += 1
            print(f"[EVT] {json.dumps(doc, ensure_ascii=False)}")
            return

        if frame_type == TYPE_PCAP:
            print(f"[PCAP] id={frame_id} bytes={len(payload)}")
            return

        if frame_type == TYPE_ACK:
            try:
                doc = json.loads(payload.decode("utf-8"))
            except Exception:
                doc = {"_raw": payload.hex()}
            print(f"[ACK] id={frame_id} {json.dumps(doc, ensure_ascii=False)}")
            return

        if frame_type == TYPE_HTML:
            print(f"[HTML] id={frame_id} bytes={len(payload)}")
            return

        print(f"[FRAME] unknown type=0x{frame_type:02X} id={frame_id} bytes={len(payload)}")

    def _reader_loop(self) -> None:
        while not self._stop.is_set():
            try:
                chunk = self.ser.read(4096)
            except Exception as exc:
                if not self._stop.is_set():
                    print(f"[SERIAL] read error: {exc}", file=sys.stderr)
                return
            if not chunk:
                continue
            self._rx_buffer += chunk

            while True:
                idx = self._rx_buffer.find(MAGIC)
                if idx < 0:
                    # Preserve a possible split magic byte for the next read.
                    if len(self._rx_buffer) > 1:
                        self._emit_text(self._rx_buffer[:-1])
                        self._rx_buffer = self._rx_buffer[-1:]
                    break

                if idx > 0:
                    self._emit_text(self._rx_buffer[:idx])
                    self._rx_buffer = self._rx_buffer[idx:]

                if len(self._rx_buffer) < HEADER_SIZE:
                    break

                frame_type = self._rx_buffer[2]
                frame_id = self._rx_buffer[3]
                payload_len = int.from_bytes(self._rx_buffer[4:8], "little")
                if payload_len > MAX_PAYLOAD:
                    # False magic in firmware text; discard one byte and resync.
                    self._emit_text(self._rx_buffer[:1])
                    self._rx_buffer = self._rx_buffer[1:]
                    continue
                total = HEADER_SIZE + payload_len
                if len(self._rx_buffer) < total:
                    break

                payload = self._rx_buffer[HEADER_SIZE:total]
                self._rx_buffer = self._rx_buffer[total:]
                self._handle_frame(frame_type, frame_id, payload)

    def send_command(self, cmd: str, args: dict | None = None, timeout: float = 10.0) -> dict | None:
        with self._response_cond:
            frame_id = self._next_id
            self._next_id = 1 if self._next_id >= 255 else self._next_id + 1
            self._responses.pop(frame_id, None)

        payload = json.dumps({"cmd": cmd, "args": args or {}}).encode("utf-8")
        frame = make_frame(TYPE_COMMAND, frame_id, payload)
        print(f"[CMD] {cmd} {json.dumps(args or {}, ensure_ascii=False)}")
        self.ser.write(frame)
        self.ser.flush()

        deadline = time.time() + timeout
        with self._response_cond:
            while frame_id not in self._responses:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None
                self._response_cond.wait(timeout=min(remaining, 0.5))
            return self._responses.pop(frame_id)

    def ping(self, timeout: float = 2.0, attempts: int = 6) -> bool:
        for attempt in range(1, attempts + 1):
            response = self.send_command("PING", timeout=timeout)
            if response and response.get("ok"):
                return True
            print(f"[PING] attempt {attempt}/{attempts} failed")
            time.sleep(0.4)
        return False

    def close(self) -> None:
        self._stop.set()
        try:
            self.ser.close()
        except Exception:
            pass
        self._reader.join(timeout=1.0)


def http_check(url: str, timeout: float) -> None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(256)
            print(
                f"[HTTP] {url} -> HTTP {response.status}, "
                f"{len(body)} sampled byte(s)"
            )
    except urllib.error.URLError as exc:
        print(f"[HTTP] {url} -> FAILED: {exc}", file=sys.stderr)
    except Exception as exc:
        print(f"[HTTP] {url} -> FAILED: {exc}", file=sys.stderr)


def run_portal_cycles(client: NRSClient, args: argparse.Namespace) -> int:
    failures = 0
    print("\n=== Portal stop/start cycles ===")
    client.send_command("STOP_PORTAL", timeout=8)
    time.sleep(1.0)

    for cycle in range(1, args.cycles + 1):
        print(f"\n--- Portal cycle {cycle}/{args.cycles} ---")
        start = client.send_command(
            "START_PORTAL",
            {
                "ssid": args.ssid,
                "channel": args.channel,
                "bssid": "",
                "show_notice": True,
            },
            timeout=20,
        )
        if not start or not start.get("ok"):
            failures += 1
            print(f"[PORTAL] START failed: {start}", file=sys.stderr)
            time.sleep(1.0)
            continue

        print("[PORTAL] AP/server reported started")
        if args.http_check:
            if args.http_hold > 0:
                print(
                    f"[PORTAL] Connect laptop Wi-Fi to '{args.ssid}' now; "
                    f"HTTP check in {args.http_hold:.0f}s..."
                )
                time.sleep(args.http_hold)
            http_check(args.http_url, timeout=args.http_timeout)
        else:
            time.sleep(args.hold)

        stop = client.send_command("STOP_PORTAL", timeout=10)
        if not stop or not stop.get("ok"):
            failures += 1
            print(f"[PORTAL] STOP failed: {stop}", file=sys.stderr)
        else:
            print("[PORTAL] stopped")
        time.sleep(args.gap)

    return failures


def run_scan_cycles(client: NRSClient, args: argparse.Namespace) -> int:
    failures = 0
    print("\n=== Wi-Fi scan cycles ===")
    for cycle in range(1, args.cycles + 1):
        print(f"\n--- Scan cycle {cycle}/{args.cycles} ---")
        client.scan_ap_events = 0
        scan_args = {"band": args.band, "settle_ms": args.settle_ms}
        if args.dwell_ms is not None:
            scan_args["dwell_ms"] = args.dwell_ms
        response = client.send_command(
            "SCAN_WIFI",
            scan_args,
            timeout=args.scan_timeout,
        )
        events_seen = client.scan_ap_events
        if not response or not response.get("ok"):
            failures += 1
            print(f"[SCAN] failed/timeout: {response}", file=sys.stderr)
        else:
            reported = response.get("count")
            print(
                f"[SCAN] count={reported} scanned={response.get('scanned')} "
                f"band={response.get('band')} dwell_ms={response.get('dwell_ms')} "
                f"scan_ap_events={events_seen}"
            )
            if isinstance(reported, int) and reported != events_seen:
                failures += 1
                print(
                    f"[SCAN] WARNING: firmware reported {reported} AP(s) but "
                    f"{events_seen} scan_ap event(s) arrived; USB/UART transport "
                    "loss is possible.",
                    file=sys.stderr,
                )
        if cycle < args.cycles:
            time.sleep(args.gap)

    return failures


def list_serial_ports() -> None:
    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return
    for port in ports:
        print(f"{port.device}\t{port.description}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NRSuite USB-serial portal restart and Wi-Fi scan diagnostics",
    )
    parser.add_argument("port", nargs="?", help="Serial port, e.g. /dev/ttyACM0 or COM7")
    parser.add_argument("--list-ports", action="store_true", help="List serial ports and exit")
    parser.add_argument("--mode", choices=("portal", "scan", "both"), default="both")
    parser.add_argument("--cycles", type=int, default=5, help="Test cycles per mode (default: 5)")
    parser.add_argument("--ssid", default="NRSuite-Portal-Diag", help="Portal test SSID")
    parser.add_argument("--channel", type=int, default=6, help="Portal channel (default: 6)")
    parser.add_argument(
        "--country",
        help="Optionally set and persist the regulatory country before tests, e.g. PH",
    )
    parser.add_argument("--band", default="auto", choices=("auto", "2g", "5g"))
    parser.add_argument("--settle-ms", type=int, default=1000)
    parser.add_argument(
        "--dwell-ms",
        type=int,
        help="Optional scan channel dwell override, clamped by firmware to 200-1000 ms",
    )
    parser.add_argument("--scan-timeout", type=float, default=50.0)
    parser.add_argument("--hold", type=float, default=2.0, help="Seconds to keep each portal up")
    parser.add_argument("--gap", type=float, default=1.2, help="Seconds between cycles")
    parser.add_argument("--http-check", action="store_true", help="Fetch portal root after each start")
    parser.add_argument("--http-url", default="http://192.168.4.1/")
    parser.add_argument("--http-hold", type=float, default=10.0)
    parser.add_argument("--http-timeout", type=float, default=5.0)
    parser.add_argument("--raw", action="store_true", help="Also print raw serial byte chunks")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_ports:
        list_serial_ports()
        return 0
    if not args.port:
        print("A serial port is required. Use --list-ports to find it.", file=sys.stderr)
        return 2

    print(f"[SERIAL] Opening {args.port} at 115200 baud")
    print("[SERIAL] Close the Android app or any serial monitor using this port first.")
    try:
        client = NRSClient(args.port, debug_raw=args.raw)
    except Exception as exc:
        print(f"[SERIAL] Could not open {args.port}: {exc}", file=sys.stderr)
        return 2

    try:
        # Native USB CDC may reset the board when the port is opened.
        time.sleep(2.5)
        if not client.ping():
            print(
                "[SERIAL] PING failed. Check the port, firmware, and that the "
                "Android app is not holding it open.",
                file=sys.stderr,
            )
            return 3

        if args.country:
            country = args.country.strip().upper()
            response = client.send_command("SET_COUNTRY", {"country": country}, timeout=8)
            if not response or not response.get("ok"):
                print(f"[COUNTRY] Failed to set {country}: {response}", file=sys.stderr)
                return 4

        status = client.send_command("STATUS", timeout=8)
        if status:
            print("\n=== Device status ===")
            for key in (
                "chip",
                "fw",
                "country",
                "allowed_2ghz_channels",
                "allowed_5ghz_channels",
            ):
                if key in status:
                    print(f"[STATUS] {key}={status[key]}")
            features = status.get("features")
            if isinstance(features, list):
                print(f"[STATUS] features={','.join(str(item) for item in features)}")
        else:
            print("[STATUS] No response", file=sys.stderr)

        failures = 0
        if args.mode in ("scan", "both"):
            failures += run_scan_cycles(client, args)
        if args.mode in ("portal", "both"):
            failures += run_portal_cycles(client, args)

        print("\n=== Diagnostic summary ===")
        print(f"failures={failures}")
        print("Save this complete output, including [FW], [RESP], and [EVT] lines.")
        return 0 if failures == 0 else 1
    except KeyboardInterrupt:
        print("\nInterrupted; attempting to stop portal.", file=sys.stderr)
        try:
            client.send_command("STOP_PORTAL", timeout=8)
        except Exception:
            pass
        return 130
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
